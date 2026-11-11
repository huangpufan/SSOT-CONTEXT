"""Calibrate outcomes, treatment parity, attempt state and artifact-bound adjudication."""
import argparse
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import handoff as h
import handoff_cases as c


class HandoffTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir='/tmp')
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_contract_mutants_and_both_output_shapes(self):
        for case in c.CASES:
            spec = c.contract(case, 17)
            repo = self.root / case
            c.build(repo, spec, 'ceiling')
            self.assertFalse(c.output_grade(repo, spec)['policy_matches'])
            expected = c.expected(spec)
            def put(values):
                if case == 'reporting':
                    text = f'RULES = {values!r}\ndef report_policy(mode):\n    if mode not in RULES: raise ValueError(mode)\n    return RULES[mode]\n'
                else:
                    text = json.dumps(values)
                c.write(repo, spec['output'], text)
            put(expected)
            self.assertTrue(c.output_grade(repo, spec)['policy_matches'])
            put(c.expected(spec, stale=True))
            self.assertFalse(c.output_grade(repo, spec)['policy_matches'])
            altered = c.expected(spec)
            altered[spec['modes'][0]][spec['boundary']] = not spec['value']
            put(altered)
            self.assertFalse(c.output_grade(repo, spec)['policy_matches'])
            altered = c.expected(spec)
            altered[spec['modes'][0]][spec['boundary']] = int(spec['value'])
            put(altered)
            self.assertFalse(c.output_grade(repo, spec)['policy_matches'])
            put(expected)
            if case == 'reporting':
                (repo / 'policy.py').write_text('print(' + repr(json.dumps({'result': expected, 'unknown': True})) + ')\nraise SystemExit(0)\n')
                self.assertFalse(c.output_grade(repo, spec)['policy_matches'])
            if case == 'reporting':
                (repo / 'policy.py').write_text("def report_policy(mode): raise NotImplementedError('policy unsettled')\n")
                placeholder = c.output_grade(repo, spec)
                self.assertFalse(placeholder['policy_matches'])
                self.assertEqual(placeholder['observed'], {})
                self.assertEqual(set(placeholder['mode_errors']), set(spec['modes']))
            self.assertNotEqual(c.contract(case, 18)['field'], spec['field'])

    def test_writer_scope_privacy_and_alternative_layout(self):
        spec = c.contract('reporting', 2)
        repo = self.root / 'repo'
        c.build(repo, spec)
        before = h.T.tree_snapshot(repo)
        c.write(repo, spec['owner'], '# Policy\n\nA prose narrative is permitted.\n')
        c.write(repo, 'docs/detail.md', 'A linked additional explanation.\n')
        checks, violations = c.writer_checks(repo, spec, before, h.T.tree_snapshot(repo))
        self.assertTrue(all(checks.values()))
        self.assertFalse(violations)
        (repo / 'scratch.bin').write_bytes(b'\x81private-local-work\x00')
        checks, violations = c.writer_checks(repo, spec, before, h.T.tree_snapshot(repo))
        self.assertFalse(checks['write_scope_preserved'])
        self.assertIn('scratch.bin', violations)
        c.write(repo, spec['owner'], spec['private'])
        self.assertFalse(c.writer_checks(repo, spec, before, h.T.tree_snapshot(repo))[0]['private_token_not_retained'])
        external = self.root / 'external.md'
        external.write_text('Outside authorized transfer')
        (repo / 'docs/link.md').symlink_to(external)
        with self.assertRaises(ValueError):
            c.handoff_files(repo)

    def test_native_state_never_turns_observer_gap_into_quality(self):
        good = {'observation_complete': True, 'native_models': ['gpt-6.1-terra'], 'completed': True, 'returncode': 0}
        self.assertIsNone(h.turn_state([good], 1, 'gpt-6.1-terra'))
        self.assertEqual(h.turn_state([good], 2, 'gpt-6.1-terra'), 'incomplete')
        self.assertEqual(h.turn_state([{**good, 'observation_complete': False}], 1, 'gpt-6.1-terra'), 'observer_failure')
        self.assertEqual(h.turn_state([good], 1, 'different'), 'model_mismatch')
        self.assertEqual(h.turn_state([{**good, 'native_models': [], 'returncode': 124, 'completed': False}], 1, 'gpt-6.1-terra'), 'incomplete')
        self.assertEqual(h.turn_state([{**good, 'native_models': []}], 1, 'gpt-6.1-terra'), 'observer_failure')
        self.assertEqual(h.turn_state([{**good, 'returncode': 124, 'observation_complete': False}], 1, 'gpt-6.1-terra'), 'incomplete')
        self.assertEqual(h.turn_state([{**good, 'discovery_mismatch': True}], 1, 'gpt-6.1-terra'), 'delivery_failure')

    def test_review_requires_actual_artifact_identity_and_all_obligations(self):
        d = self.root / 'runs/reporting/baseline'
        d.mkdir(parents=True)
        (d / 'handoff.json').write_text('{}')
        h.save(d / 'mechanical.json', {'state': 'semantic_pending', 'checks': {'consumer_policy_matches': True}})
        original_mode = (d / 'handoff.json').stat().st_mode & 0o777
        identity = h.evidence_identity(d)
        h.save(d / 'result.json', {'state': 'semantic_pending', 'evidence': identity})
        record = {'reviewer': 'calibration', 'evidence': identity,
                  'checks': {name: {'passed': True, 'reason': 'calibration evidence'} for name in h.SEMANTIC}}
        review = self.root / 'review-input.json'
        h.save(review, record)
        args = argparse.Namespace(case='reporting', arm='baseline', review=review)
        with patch.object(h, 'validate'):
            (d / 'handoff.json').write_text('{"changed":true}')
            with self.assertRaisesRegex(ValueError, 'Evidence changed'):
                h.review(args, self.root, {})
            (d / 'handoff.json').write_text('{}')
            (d / 'handoff.json').chmod(0o700)
            with self.assertRaisesRegex(ValueError, 'Evidence changed'):
                h.review(args, self.root, {})
            (d / 'handoff.json').chmod(original_mode)
            h.review(args, self.root, {})
            self.assertEqual(h.load(d / 'result.json')['state'], 'passed')
            h.review(args, self.root, {})  # identical replay recovers the review/result crash window
            self.assertEqual(h.verified_result(d, 'baseline')['state'], 'passed')
            result = h.load(d / 'result.json')
            result['state'] = 'semantic_pending'
            h.save(d / 'result.json', result)
            self.assertEqual(h.verified_result(d, 'baseline')['state'], 'passed')
            (d / 'handoff.json').write_text('changed after approval')
            self.assertEqual(h.verified_result(d, 'baseline')['state'], 'observer_failure')

    def test_failed_sealed_mechanical_verdict_cannot_be_reviewed_into_a_pass(self):
        d = self.root / 'runs/reporting/baseline'
        d.mkdir(parents=True)
        h.save(d / 'mechanical.json', {'state': 'failed_quality', 'checks': {'consumer_policy_matches': False}, 'turns': []})
        identity = h.evidence_identity(d)
        h.save(d / 'result.json', {'state': 'semantic_pending', 'evidence': identity, 'turns': []})
        record = {'reviewer': 'calibration', 'evidence': identity,
                  'checks': {name: {'passed': True, 'reason': 'invalid optimistic review'} for name in h.SEMANTIC}}
        review = self.root / 'review-input.json'
        h.save(review, record)
        args = argparse.Namespace(case='reporting', arm='baseline', review=review)
        with patch.object(h, 'validate'), self.assertRaisesRegex(ValueError, 'mechanical verdict'):
            h.review(args, self.root, {})
        h.save(d / 'review.json', record)
        self.assertEqual(h.verified_result(d, 'baseline')['state'], 'observer_failure')


    def test_full_handoff_and_subject_owner_violation(self):
        spec = c.contract('editorial', 44)
        plan = {'model': 'gpt-6.1-terra', 'cap': 10, 'cases': {'editorial': {
            'contract': spec, 'prompts': c.prompts(spec), 'consumer': c.consumer_prompt(spec)}}}
        for label, bad_owner in (('valid', False), ('invalid-owner', True)):
            root = self.root / label
            c.build(root / 'fixtures/editorial/initial', spec)
            calls = []
            def subject(_root, where, repo, prompt, turn, *_args, **_kwargs):
                calls.append(where.name)
                if where.name == 'writer':
                    target = repo / spec['owner']
                    if bad_owner:
                        target.unlink()
                        target.symlink_to('/outside/owner.md')
                    else:
                        target.write_text('Accepted policy with a scoped correction.\n')
                else:
                    self.assertFalse((repo / 'scratch.bin').exists())
                    self.assertFalse((repo / '.agents').exists())
                    c.write(repo, spec['output'], json.dumps(c.expected(spec)))
                summary = {'observation_complete': True, 'native_models': [plan['model']],
                    'native_discovery': {'skills': [], 'instruction_blocks': [{'ssot_wired': False}]},
                    'completed': True, 'returncode': 0, 'seconds': 1, 'tool_items': 1, 'tool_output_bytes': 3,
                    'native_turn_usage': {'input_tokens': 10, 'cached_input_tokens': 0, 'output_tokens': 2}}
                h.save(where / f'{turn}.summary.json', summary)
                return summary
            args = argparse.Namespace(case='editorial', arm='plain')
            with patch.object(h, 'validate'), patch.object(h, 'probe', return_value=[]), \
                    patch.object(h.T, 'execute_turn', side_effect=subject), \
                    patch.object(h.subprocess, 'check_output', return_value='fixture codex'), \
                    patch.dict(h.os.environ, {'CI': ''}):
                h.execute(args, root, plan)
            result = h.load(root / 'runs/editorial/plain/result.json')
            self.assertEqual(result['state'], 'failed_quality' if bad_owner else 'semantic_pending')
            self.assertEqual(calls, ['writer', 'writer'] if bad_owner else ['writer', 'writer', 'consumer'])
            self.assertTrue(result['evidence'])
            self.assertEqual(len(result['turns']), len(calls))

    def test_setup_failure_is_retained_before_any_native_dispatch(self):
        spec = c.contract('editorial', 44)
        plan = {'cases': {'editorial': {'contract': spec}}}
        args = argparse.Namespace(case='editorial', arm='plain')
        with patch.object(h, 'validate'), patch.object(h.subprocess, 'check_output', side_effect=OSError('codex unavailable')), \
                patch.object(h.T, 'execute_turn') as dispatch, patch.dict(h.os.environ, {'CI': ''}):
            h.execute(args, self.root, plan)
            dispatch.assert_not_called()
        d = self.root / 'runs/editorial/plain'
        result = h.verified_result(d, 'plain')
        self.assertEqual(result['state'], 'infra')
        self.assertEqual(result['phase'], 'setup')
        self.assertEqual(result['turns'], [])
        with patch.object(h, 'validate'), patch.dict(h.os.environ, {'CI': ''}), self.assertRaisesRegex(ValueError, 'Attempt already exists'):
            h.execute(args, self.root, plan)


    def test_report_does_not_promote_uncalibrated_or_unreviewed_success(self):
        h.save(self.root / 'plan.json', {'limits': 'calibration test'})
        d = self.root / 'runs/reporting/baseline'
        d.mkdir(parents=True)
        h.save(d / 'result.json', {'state': 'passed', 'turns': [], 'evidence': {}})
        with patch.object(h, 'validate'):
            h.report(self.root)
        report = h.load(self.root / 'report.json')
        self.assertFalse(any(report['calibration_valid'].values()))
        self.assertFalse(any(p['eligible'] for p in report['comparisons']))
        self.assertEqual(next(r for r in report['attempts'] if r['case'] == 'reporting' and r['arm'] == 'baseline')['state'], 'observer_failure')


    def test_freeze_has_equal_facts_and_confirmation_before_candidate(self):
        for kind in ('initial', 'ceiling', 'stale'):
            spec = c.contract('editorial', 9)
            repo = self.root / kind
            c.build(repo, spec, kind)
        self.assertNotIn(spec['field'], '\n'.join(c.handoff_files(self.root / 'initial').values()))
        self.assertIn(spec['field'], '\n'.join(c.handoff_files(self.root / 'ceiling').values()))
        for kind in ('initial', 'ceiling', 'stale'):
            self.assertNotIn(spec['private'], '\n'.join(c.handoff_files(self.root / kind).values()))
        (self.root / 'runs/editorial').mkdir(parents=True)
        with patch.object(h, 'validate'), self.assertRaisesRegex(ValueError, 'before any confirmation'):
            h.attach(self.root, {'confirmation': 'editorial'}, self.root / 'bundle')


if __name__ == '__main__':
    unittest.main()
