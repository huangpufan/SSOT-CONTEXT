"""Offline good/bad calibration for retaining attempts despite damaged evidence."""
import argparse
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import handoff as h


class ReportIntegrityTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir='/tmp')
        self.root = Path(self.temp.name)
        h.save(self.root / 'plan.json', {'limits': 'offline calibration', 'model': 'gpt-6.1-terra'})

    def tearDown(self):
        self.temp.cleanup()

    def attempt(self, arm='baseline', turns=None, native_identity=True):
        d = self.root / 'runs/reporting' / arm
        d.mkdir(parents=True)
        h.save(d / 'handoff.json', {'docs/policy.md': 'Accepted scoped policy; prose/layout is unrestricted.'})
        turns = turns if turns is not None else [{'phase': 'consumer', 'costs': {key: 7 for key in h.run.METRICS} | {'cached_input_tokens': 0}}]
        (d / 'consumer').mkdir()
        summary = {'seconds': 7, 'tool_items': 7, 'tool_output_bytes': 7,
                   'requested_model': 'gpt-6.1-terra', 'native_models': ['gpt-6.1-terra'],
                   'requested_reasoning': 'medium', 'native_reasoning': ['medium'],
                   'native_turn_usage': {'input_tokens': 7, 'cached_input_tokens': 0, 'output_tokens': 7}}
        if not native_identity:
            summary.pop('native_reasoning')
        h.save(d / 'consumer/1.summary.json', summary)
        negative = arm in ('floor', 'stale')
        mechanical = {'state': 'calibration_pending' if negative else 'semantic_pending', 'phase': 'adjudication',
                      'checks': {'consumer_policy_matches': not negative}, 'turns': turns}
        if negative:
            mechanical['calibration_expected_outcome'] = True
        h.save(d / 'mechanical.json', mechanical)
        identity = h.evidence_identity(d)
        h.save(d / 'result.json', {**mechanical, 'state': 'calibration_passed' if negative else 'passed', 'evidence': identity})
        h.save(d / 'review.json', {'reviewer': 'offline calibration', 'evidence': identity,
            'checks': {key: {'passed': True, 'reason': 'Read retained artifacts'} for key in h.SEMANTIC}})
        return d

    def report(self):
        with patch.object(h, 'validate'):
            h.report(self.root)
        return h.load(self.root / 'report.json')

    def row(self, report, arm='baseline'):
        return next(row for row in report['attempts'] if row['case'] == 'reporting' and row['arm'] == arm)

    def test_valid_artifact_bound_review_and_alternate_prose_still_pass(self):
        self.attempt()
        row = self.row(self.report())
        self.assertEqual(row['state'], 'passed')
        self.assertEqual(row['costs'], {key: 7 for key in h.run.METRICS} | {'cached_input_tokens': 0})

    def test_each_missing_or_malformed_record_keeps_other_attempts_and_cost(self):
        # Reset each bad sample independently; a second valid arm must survive it.
        for name in ('result.json', 'review.json', 'mechanical.json'):
            for damage in ('missing', 'invalid-json', 'wrong-shape', 'invalid-encoding'):
                with self.subTest(record=name, damage=damage):
                    with tempfile.TemporaryDirectory(dir='/tmp') as parent:
                        old_root, self.root = self.root, Path(parent)
                        try:
                            h.save(self.root / 'plan.json', {'limits': 'offline calibration', 'model': 'gpt-6.1-terra'})
                            d = self.attempt()
                            self.attempt('plain')
                            target = d / name
                            if damage == 'missing':
                                target.unlink()
                            elif damage == 'invalid-json':
                                target.write_text('{')
                            elif damage == 'wrong-shape':
                                h.save(target, [])
                            else:
                                target.write_bytes(b'\xff')
                            report = self.report()
                            row = self.row(report)
                            self.assertEqual(len(report['attempts']), len(h.cases.CASES) * len(h.ARMS))
                            self.assertEqual(row['state'], 'observer_failure')
                            self.assertTrue(row['report_error'])
                            self.assertEqual(row['costs']['input_tokens'], 7)
                            self.assertEqual(self.row(report, 'plain')['state'], 'passed')
                            self.assertFalse(any(pair['eligible'] for pair in report['comparisons']))
                        finally:
                            self.root = old_root

    def test_unreadable_snapshot_cannot_be_accepted_even_if_identity_repeats(self):
        d = self.attempt()
        real_read = Path.read_bytes
        def unreadable(path):
            if path == d / 'handoff.json':
                raise PermissionError('offline unreadable artifact')
            return real_read(path)
        with patch.object(Path, 'read_bytes', unreadable):
            # Existing recorder returns an unavailable marker. Repeating that marker
            # must not turn unavailable evidence into an accepted identity.
            unavailable = h.T.tree_snapshot(d)
            unavailable = {key: value for key, value in unavailable.items() if key not in ('result.json', 'review.json')}
            result = h.load(d / 'result.json')
            result['evidence'] = unavailable
            h.save(d / 'result.json', result)
            review = h.load(d / 'review.json')
            review['evidence'] = unavailable
            h.save(d / 'review.json', review)
            row = self.row(self.report())
        self.assertEqual(row['state'], 'observer_failure')
        self.assertIn('unavailable', row['report_error'].lower())
        self.assertEqual(row['costs']['input_tokens'], 7)

    def test_snapshot_exception_isolated_to_its_attempt(self):
        d = self.attempt()
        self.attempt('plain')
        real_identity = h.evidence_identity
        def snapshot(where):
            if where == d:
                raise OSError('offline snapshot failure')
            return real_identity(where)
        with patch.object(h, 'evidence_identity', side_effect=snapshot):
            report = self.report()
        self.assertEqual(self.row(report)['state'], 'observer_failure')
        self.assertEqual(self.row(report, 'plain')['state'], 'passed')
        self.assertEqual(self.row(report)['costs']['input_tokens'], 7)

    def test_started_receipt_and_pre_receipt_directory_never_become_completed(self):
        d = self.root / 'runs/reporting/baseline'
        d.mkdir(parents=True)
        h.save(d / 'result.json', {'state': 'started', 'phase': 'writer-2', 'turns': []})
        # Even a leftover mechanical verdict cannot establish completion without
        # the final receipt binding it to the observed artifacts.
        h.save(d / 'mechanical.json', {'state': 'semantic_pending', 'checks': {'consumer_policy_matches': True}, 'turns': []})
        report = self.report()
        self.assertEqual(self.row(report)['state'], 'started')
        (d / 'result.json').unlink()
        self.assertEqual(self.row(self.report())['state'], 'observer_failure')
        self.assertEqual(self.row(report, 'candidate')['state'], 'unrun')

    def test_summary_recovers_observed_spend_without_inventing_usage_or_acceptance(self):
        d = self.root / 'runs/reporting/baseline'
        (d / 'writer').mkdir(parents=True)
        h.save(d / 'result.json', {'state': 'started', 'phase': 'writer-2',
            'turns': [{'phase': 'writer-1', 'costs': {key: 7 for key in h.run.METRICS}}]})
        h.save(d / 'writer/2.summary.json', {'seconds': 3, 'tool_items': 2, 'tool_output_bytes': 12,
            'requested_model': 'gpt-6.1-terra', 'native_models': ['gpt-6.1-terra'],
            'requested_reasoning': 'medium', 'native_reasoning': ['medium'], 'completed': False})
        row = self.row(self.report())
        self.assertEqual(row['state'], 'started')
        self.assertEqual([turn['phase'] for turn in row['turns']], ['writer-1', 'writer-2'])
        self.assertEqual(row['costs']['seconds'], 10)
        self.assertIsNone(row['costs']['input_tokens'])
        self.assertEqual(row['observed_costs']['input_tokens'], 7)
        self.assertFalse(row['costs_complete'])
        text = (self.root / 'report.md').read_text()
        self.assertIn('unknown', text)
        self.assertIn('observed', text)

    def test_missing_receipt_recovers_summary_and_missing_usage_is_unknown(self):
        d = self.root / 'runs/reporting/baseline'
        (d / 'consumer').mkdir(parents=True)
        h.save(d / 'consumer/1.summary.json', {'seconds': 4, 'tool_items': 0, 'tool_output_bytes': 0,
            'requested_model': 'gpt-6.1-terra', 'native_models': ['gpt-6.1-terra'],
            'requested_reasoning': 'medium', 'native_reasoning': ['medium'],
            'native_turn_usage': {'input_tokens': 11, 'cached_input_tokens': 1, 'output_tokens': 2}})
        row = self.row(self.report())
        self.assertEqual(row['state'], 'observer_failure')
        self.assertEqual(row['costs']['input_tokens'], 11)
        self.assertEqual(row['costs']['seconds'], 4)
        (d / 'consumer/1.summary.json').write_text('{')
        row = self.row(self.report())
        self.assertEqual(row['state'], 'observer_failure')
        self.assertIsNone(row['costs'])
        self.assertIsNone(row['observed_costs'])

    def test_frozen_snapshot_failure_retains_attempts_but_invalidates_acceptance(self):
        self.attempt()
        with patch.object(h, 'validate', side_effect=OSError('offline frozen snapshot unreadable')):
            h.report(self.root)
        report = h.load(self.root / 'report.json')
        self.assertEqual(self.row(report)['state'], 'observer_failure')
        self.assertEqual(self.row(report)['costs']['seconds'], 7)
        self.assertEqual(self.row(report, 'candidate')['state'], 'unrun')
        self.assertIn('Frozen experiment', report['report_error'])

    def test_valid_calibration_does_not_make_unknown_native_cost_comparable(self):
        for arm in ('plain', 'baseline', 'ceiling', 'floor', 'stale'):
            self.attempt(arm, native_identity=False)
        # The complete legacy cost dict alone cannot verify native model/effort.
        report = self.report()
        self.assertTrue(report['calibration_valid']['reporting'])
        self.assertFalse(any(pair['eligible'] for pair in report['comparisons']))
        d = self.root / 'runs/reporting/baseline'
        (d / 'review.json').unlink()
        receipt = h.load(d / 'result.json')
        receipt['state'] = 'semantic_pending'
        h.save(d / 'result.json', receipt)
        self.assertEqual(self.row(self.report())['state'], 'semantic_pending')

    def test_complete_native_receipts_with_valid_controls_allow_comparison(self):
        for arm in ('plain', 'baseline', 'ceiling', 'floor', 'stale'):
            self.attempt(arm)
        report = self.report()
        self.assertTrue(report['calibration_valid']['reporting'])
        self.assertTrue(self.row(report)['costs_complete'])
        self.assertTrue(next(pair for pair in report['comparisons']
                             if pair['case'] == 'reporting' and pair['pair'] == ['plain', 'baseline'])['eligible'])

    def test_observed_usage_survives_wrong_or_unknown_native_identity(self):
        for models, efforts in ((['other-model'], ['medium']), (['gpt-6.1-terra'], ['high']), ([], [])):
            with self.subTest(models=models, efforts=efforts):
                d = self.root / 'runs/reporting/baseline'
                (d / 'consumer').mkdir(parents=True, exist_ok=True)
                h.save(d / 'consumer/1.summary.json', {'seconds': 4, 'tool_items': 0, 'tool_output_bytes': 0,
                    'requested_model': 'gpt-6.1-terra', 'native_models': models,
                    'requested_reasoning': 'medium', 'native_reasoning': efforts,
                    'native_turn_usage': {'input_tokens': 11, 'cached_input_tokens': 1, 'output_tokens': 2}})
                row = self.row(self.report())
                self.assertEqual(row['state'], 'observer_failure')  # missing receipt
                self.assertEqual(row['costs']['input_tokens'], 11)
                self.assertEqual(row['costs']['seconds'], 4)
                self.assertFalse(row['costs_complete'])
                self.assertFalse(row['turns'][0]['native_identity_verified'])

    def test_incomplete_privacy_scan_stops_writer_and_control_as_observer_failure(self):
        spec = h.cases.contract('editorial', 44)
        plan = {'model': 'gpt-6.1-terra', 'cap': 10, 'cases': {'editorial': {
            'contract': spec, 'prompts': h.cases.prompts(spec), 'consumer': h.cases.consumer_prompt(spec)}}}
        checks = {'owner_transfer_valid': True, 'write_scope_preserved': True,
                  'private_token_not_retained': True, 'private_scan_complete': False, 'canonical_owner_retained': True}
        summary = {'observation_complete': True, 'requested_model': plan['model'], 'native_models': [plan['model']],
                   'requested_reasoning': 'medium', 'native_reasoning': ['medium'],
                   'native_discovery': {'skills': [], 'instruction_blocks': [{'ssot_wired': False}]},
                   'completed': True, 'returncode': 0, 'seconds': 1, 'tool_items': 1, 'tool_output_bytes': 3,
                   'native_turn_usage': {'input_tokens': 10, 'cached_input_tokens': 0, 'output_tokens': 2}}
        for arm, kind in (('plain', 'initial'), ('ceiling', 'ceiling')):
            with self.subTest(arm=arm):
                root = self.root / arm
                h.cases.build(root / 'fixtures/editorial' / kind, spec, kind)
                with patch.object(h, 'validate'), patch.object(h, 'probe', return_value=[]), \
                        patch.object(h.T, 'execute_turn', return_value=summary) as dispatch, \
                        patch.object(h.cases, 'writer_checks', return_value=(checks, [])), \
                        patch.object(h.subprocess, 'check_output', return_value='offline codex'), \
                        patch.dict(h.os.environ, {'CI': ''}):
                    h.execute(argparse.Namespace(case='editorial', arm=arm), root, plan)
                result = h.load(root / 'runs/editorial' / arm / 'result.json')
                self.assertEqual(result['state'], 'observer_failure')
                self.assertEqual(dispatch.call_count, 1 if arm == 'plain' else 0)
                self.assertFalse((root / 'runs/editorial' / arm / 'consumer').exists())

    def test_snapshot_seal_failure_records_observer_failure_instead_of_started(self):
        spec = h.cases.contract('editorial', 44)
        args = argparse.Namespace(case='editorial', arm='plain')
        with patch.object(h, 'validate'), patch.object(h.subprocess, 'check_output', side_effect=OSError('offline setup unavailable')), \
                patch.object(h, 'evidence_identity', side_effect=ValueError('Evidence unavailable: unreadable-artifact')), \
                patch.object(h.T, 'execute_turn') as dispatch, patch.dict(h.os.environ, {'CI': ''}):
            h.execute(args, self.root, {'cases': {'editorial': {'contract': spec}}})
        dispatch.assert_not_called()
        d = self.root / 'runs/editorial/plain'
        receipt = h.load(d / 'result.json')
        self.assertEqual(receipt['state'], 'observer_failure')
        self.assertIsNone(receipt['evidence'])
        self.assertIn('unreadable-artifact', receipt['evidence_error'])
        self.assertEqual(h.load(d / 'mechanical.json')['state'], 'observer_failure')
        self.assertEqual(h.verified_result(d, 'plain')['state'], 'observer_failure')


if __name__ == '__main__':
    unittest.main()
