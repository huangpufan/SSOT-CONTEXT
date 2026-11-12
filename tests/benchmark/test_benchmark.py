#!/usr/bin/env python3
"""Deterministic benchmark checks; never invokes a model."""
import json
from argparse import Namespace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import cases
import run


def solution(p, digital=True):
    return ('''def quote(zone, subtotal, weight, kind="physical", service="standard"):
''' + ('    if kind == "digital": return {"fee": 0, "days": 0}\n' if digital else '') + f'''
    if service == "standard": return {{"fee": 600, "days": 6}}
    if service != "express" or zone not in ("north", "south"): raise ValueError()
    base = {{"north": {p['north']}, "south": {p['south']}}}[zone]
    fee = base + max(weight - 1, 0) * {p['kg']}
    if zone == "north" and subtotal >= {p['threshold']}: fee = 0
    return {{"fee": fee, "days": 2 if zone == "north" else 4}}
''')


class BenchmarkTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir="/tmp")
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_fixtures_have_identical_facts_and_only_index_differs(self):
        for case in cases.CASES:
            a, b = self.root / (case + 'a'), self.root / (case + 'b')
            cases.build(a, case, True, 7)
            cases.build(b, case, True, 7)
            self.assertEqual(run.manifest(a), run.manifest(b))
        c = self.root / 'coarse'
        cases.build(c, 'routed', False, 7)
        a, b = run.manifest(self.root/'routeda'), run.manifest(c)
        self.assertEqual({k for k in a if a[k] != b[k]}, {'SSOT/README.md'})

    def test_oracle_accepts_solution_rejects_stub_boundary_loss_and_tampering(self):
        repo = self.root / 'repo'
        p = cases.build(repo, 'routed', True, 8)
        before = run.transport.snapshot(repo)
        self.assertFalse(cases.grade(repo, 'routed', p, before, before)['checks']['contract_and_boundaries'])
        (repo/'shipping.py').write_text(solution(p))
        self.assertTrue(cases.grade(repo, 'routed', p, before, run.transport.snapshot(repo))['passed'])
        (repo/'shipping.py').write_text(solution(p, digital=False))
        self.assertFalse(cases.grade(repo, 'routed', p, before, run.transport.snapshot(repo))['passed'])
        (repo/'shipping.py').write_text(solution(p))
        (repo/'test_shipping.py').write_text('print("pass")\n')
        self.assertFalse(cases.grade(repo, 'routed', p, before, run.transport.snapshot(repo))['passed'])

    def test_warm_requires_new_policy_with_same_head_and_untracked_owner(self):
        repo = self.root/'repo'
        p = cases.build(repo, 'warm', True, 9)
        run.init_git(repo)
        (repo/'shipping.py').write_text(solution(p))
        new = cases.update(repo, p)
        before = run.transport.snapshot(repo)
        stale = cases.grade(repo, 'warm', new, before, before)
        self.assertFalse(stale['checks']['contract_and_boundaries'])
        (repo/'shipping.py').write_text(solution(new))
        self.assertTrue(cases.grade(repo, 'warm', new, before, run.transport.snapshot(repo))['passed'])
        status = run.subprocess.check_output(['git', 'status', '--porcelain'], cwd=repo, text=True)
        self.assertIn('?? docs/promotions.md', status)
        self.assertIn(' M docs/shipping.md', status)

    def test_native_usage_is_mandatory_and_cumulative_fallback_is_rejected(self):
        summary = {'seconds': 3, 'tool_items': 2, 'tool_output_bytes': 9,
                   'requested_model': run.transport.MODEL,
                   'requested_reasoning': 'medium', 'native_reasoning': ['medium'], 'native_models': [run.transport.MODEL], 'usage': {'input_tokens': 9999}}
        self.assertIsNone(run.costs(summary))
        summary['native_turn_usage'] = {'input_tokens': 100, 'cached_input_tokens': 80, 'output_tokens': 12}
        self.assertEqual(run.costs(summary)['uncached_input_tokens'], 20)
        summary['native_models'] = ['different-model']
        self.assertIsNone(run.costs(summary))

    def test_resume_usage_is_selected_by_root_turn_not_last_cli_total(self):
        home = self.root/'home'
        sessions = home/'sessions'
        sessions.mkdir(parents=True)
        records = []
        for tid, amount in (('a', 50), ('b', 20), ('b', 30)):
            records += [{'type': 'turn_context', 'payload': {'root_turn_id': tid, 'model': run.transport.MODEL, 'effort': 'medium'}},
                        {'type': 'token_usage_record', 'payload': {'root_turn_id': tid, 'turn_id': tid,
                         'turn_token_usage': {'input_tokens': amount}}}]
        (sessions/'session-thread.jsonl').write_text('\n'.join(map(json.dumps, records)))
        summary = {'thread_id': 'thread'}
        run.transport.record_native(self.root, 2, summary, home)
        self.assertEqual(summary['native_turn_usage']['input_tokens'], 30)
        self.assertEqual(summary['native_turn_id'], 'b')

    def test_explicit_model_costs_require_matching_request_and_native_receipt(self):
        summary = {'seconds': 3, 'tool_items': 2, 'tool_output_bytes': 9,
                   'requested_model': 'gpt-6.1-sol', 'native_models': ['gpt-6.1-sol'], 'requested_reasoning': 'medium', 'native_reasoning': ['medium'],
                   'native_turn_usage': {'input_tokens': 100, 'cached_input_tokens': 80, 'output_tokens': 12}}
        self.assertIsNone(run.costs(summary))
        self.assertEqual(run.costs(summary, 'gpt-6.1-sol')['input_tokens'], 100)
        summary['requested_model'] = run.transport.MODEL
        self.assertIsNone(run.costs(summary, 'gpt-6.1-sol'))

    def test_explicit_model_is_frozen_and_cannot_change_at_execution(self):
        source = self.root/'source'
        (source/'skills').mkdir(parents=True)
        (source/'skills/example.md').write_text('frozen source\n')
        args = Namespace(output=self.root/'experiment', comparison='index', baseline=None, candidate=source,
                         repeats=1, documents=0, cap=30, seed=20261109, cases=['routed'], model='gpt-6.1-sol')
        run.prepare(args)
        self.assertEqual(json.loads((args.output/'plan.json').read_text())['model'], 'gpt-6.1-sol')
        # Exercise model identity separately from the independently tested CI
        # billing guard; stop before transport even if mismatch handling regresses.
        with patch.dict(run.os.environ, {'CI': ''}), \
                patch.object(run, 'validate_frozen', side_effect=AssertionError('must reject before execution')):
            with self.assertRaisesRegex(ValueError, 'Model differs'):
                run.run_models(Namespace(output=args.output, model=run.transport.MODEL))

    def test_report_keeps_failure_cost_and_excludes_failed_pairs(self):
        run.save(self.root/'plan.json', {'comparison': 'protocol', 'cases': ['routed'], 'pairs': [{'id': 'x', 'case': 'routed'}]})
        for arm, state in (('baseline', 'passed'), ('candidate', 'failed_quality')):
            directory = self.root/'runs'/'x'/arm
            directory.mkdir(parents=True)
            run.save(directory/'result.json', {'state': state, 'turns': [{'turn': 1, 'quality_passed': state == 'passed',
                      'usage_source': 'native', 'costs': {k: 2 for k in run.METRICS}}]})
        run.report(self.root)
        report = json.loads((self.root/'report.json').read_text())
        self.assertFalse(report['pairs'][0]['eligible'])
        self.assertEqual(report['attempts'][1]['seconds'], 2)
        self.assertIn('0/1 usable pairs; 1 excluded', (self.root/'report.md').read_text())

    def test_reading_observed_usage_survives_identity_failures_without_becoming_comparable(self):
        valid = {'seconds': 3, 'tool_items': 2, 'tool_output_bytes': 9,
                 'requested_model': run.transport.MODEL, 'native_models': [run.transport.MODEL],
                 'requested_reasoning': 'medium', 'native_reasoning': ['medium'],
                 'native_turn_usage': {'input_tokens': 100, 'cached_input_tokens': 80, 'output_tokens': 12}}
        variants = [({}, None), ({'native_reasoning': ['high']}, 'reasoning_mismatch'),
                    ({'native_models': ['other-model']}, 'model_mismatch'),
                    ({'native_reasoning': []}, 'observer_failure')]
        for changed, state in variants:
            with self.subTest(state=state):
                summary = {**valid, **changed}
                receipt = run.reading_turn_costs(summary, run.transport.MODEL)
                self.assertEqual(receipt['identity_state'], state)
                self.assertEqual(receipt['costs'] is not None, state is None)
                self.assertEqual(receipt['observed_costs']['input_tokens'], 100)
                self.assertEqual(receipt['observed_costs']['cached_input_tokens'], 80)
                self.assertEqual(receipt['observed_costs']['output_tokens'], 12)
                self.assertEqual(receipt['observed_costs']['uncached_input_tokens'], 20)
                self.assertEqual(receipt['usage_source'], 'native')
                self.assertEqual(run.costs(summary) is not None, state is None)
        unknown = run.reading_turn_costs({**valid, 'native_turn_usage': None}, run.transport.MODEL)
        self.assertIsNone(unknown['costs'])
        self.assertIsNone(unknown['observed_costs']['input_tokens'])
        self.assertEqual(unknown['observed_costs']['seconds'], 3)
        partial = run.reading_turn_costs({**valid, 'native_turn_usage': {'output_tokens': 12}}, run.transport.MODEL)
        self.assertIsNone(partial['costs'])
        self.assertIsNone(partial['observed_costs']['input_tokens'])
        self.assertEqual(partial['observed_costs']['output_tokens'], 12)

    def test_reading_report_recovers_native_spend_and_counts_reasoning_and_delivery_failures(self):
        plan = {'comparison': 'protocol', 'model': run.transport.MODEL, 'cases': ['routed'],
                'pairs': [{'id': name, 'case': 'routed'} for name in ('mismatch', 'valid', 'unknown')]}
        run.save(self.root / 'plan.json', plan)
        summary = {'seconds': 3, 'tool_items': 2, 'tool_output_bytes': 9,
                   'requested_model': run.transport.MODEL, 'native_models': [run.transport.MODEL],
                   'requested_reasoning': 'medium', 'native_reasoning': ['medium'],
                   'native_turn_usage': {'input_tokens': 100, 'cached_input_tokens': 80, 'output_tokens': 12}}
        for pair in plan['pairs']:
            for arm in ('baseline', 'candidate'):
                directory = self.root / 'runs' / pair['id'] / arm
                directory.mkdir(parents=True)
                state, actual = 'passed', dict(summary)
                if pair['id'] == 'mismatch' and arm == 'candidate':
                    state, actual['native_reasoning'] = 'reasoning_mismatch', ['high']
                elif pair['id'] == 'unknown':
                    if arm == 'baseline':
                        state, actual['native_turn_usage'] = 'observer_failure', None
                    else:
                        state = 'delivery_failure'
                run.save(directory / '1.summary.json', actual)
                # A historical result may lack observed_costs. Report derives
                # it from saved evidence without patching that old artifact.
                run.save(directory / 'result.json', {'state': state, 'turns': [{'turn': 1, 'costs': None}]})
        original = (self.root / 'runs/mismatch/candidate/result.json').read_bytes()
        run.report(self.root)
        report = json.loads((self.root / 'report.json').read_text())
        by_pair = {p['pair']: p for p in report['pairs']}
        self.assertFalse(by_pair['mismatch']['eligible'])
        self.assertTrue(by_pair['valid']['eligible'])
        self.assertFalse(by_pair['unknown']['eligible'])
        wrong = next(r for r in report['attempts'] if r['pair'] == 'mismatch' and r['arm'] == 'candidate')
        self.assertEqual(wrong['input_tokens'], 100)
        self.assertEqual(wrong['cached_input_tokens'], 80)
        self.assertEqual(wrong['output_tokens'], 12)
        self.assertFalse(wrong['cost_comparable'])
        self.assertEqual(wrong['identity_state'], 'reasoning_mismatch')
        missing = next(r for r in report['attempts'] if r['pair'] == 'unknown' and r['arm'] == 'baseline')
        self.assertIsNone(missing['input_tokens'])
        self.assertEqual(missing['seconds'], 3)
        markdown = (self.root / 'report.md').read_text()
        header = next(line for line in markdown.splitlines() if line.startswith('| Case | Arm |'))
        row = next(line for line in markdown.splitlines() if line.startswith('| routed | candidate |'))
        columns = [cell.strip() for cell in header.split('|')[1:-1]]
        counts = dict(zip(columns, [cell.strip() for cell in row.split('|')[1:-1]]))
        self.assertEqual(counts['Reasoning mismatch'], '1')
        self.assertEqual(counts['Delivery failure'], '1')
        self.assertEqual(sum(int(counts[key]) for key in columns[2:]), 3)
        self.assertIn('| mismatch | candidate | 1 | reasoning_mismatch | 3 | 100 | 12 | 80 | 20 | 2 | 9 |', markdown)
        self.assertIn('unknown', markdown)
        self.assertEqual((self.root / 'runs/mismatch/candidate/result.json').read_bytes(), original)

    def test_reading_missing_or_damaged_summary_retains_saved_spend_without_comparability(self):
        observed = {key: 2 for key in run.METRICS}
        turn = {'turn': 1, 'costs': observed}
        for saved in (None, b'{', b'[]', b'\xff'):
            with self.subTest(saved=saved):
                path = self.root / '1.summary.json'
                if saved is not None:
                    path.write_bytes(saved)
                elif path.exists():
                    path.unlink()
                receipt = run.reading_report_turn(self.root, turn, run.transport.MODEL)
                self.assertIsNone(receipt['costs'])
                self.assertEqual(receipt['observed_costs'], observed)
                self.assertEqual(receipt['identity_state'], 'observer_failure')
                self.assertIn('1.summary.json', receipt['report_error'])

    def test_reading_damaged_summary_isolates_its_attempt_and_keeps_good_neighbor(self):
        run.save(self.root / 'plan.json', {'comparison': 'protocol', 'model': run.transport.MODEL,
            'cases': ['routed'], 'pairs': [{'id': name, 'case': 'routed'} for name in ('good', 'damaged')]})
        summary = {'seconds': 3, 'tool_items': 2, 'tool_output_bytes': 9,
            'requested_model': run.transport.MODEL, 'native_models': [run.transport.MODEL],
            'requested_reasoning': 'medium', 'native_reasoning': ['medium'],
            'native_turn_usage': {'input_tokens': 100, 'cached_input_tokens': 80, 'output_tokens': 12}}
        for name in ('good', 'damaged'):
            for arm in ('baseline', 'candidate'):
                directory = self.root / 'runs' / name / arm
                directory.mkdir(parents=True)
                run.save(directory / '1.summary.json', summary)
                run.save(directory / 'result.json', {'state': 'passed', 'turns': [{'turn': 1,
                    'costs': run.costs(summary) if arm == 'baseline' else None}]})
        for bad in (b'{', b'[]', b'\xff'):
            with self.subTest(bad=bad):
                for arm in ('baseline', 'candidate'):
                    (self.root / 'runs/damaged' / arm / '1.summary.json').write_bytes(bad)
                run.report(self.root)
                report = json.loads((self.root / 'report.json').read_text())
                pairs = {pair['pair']: pair for pair in report['pairs']}
                self.assertTrue(pairs['good']['eligible'])
                self.assertFalse(pairs['damaged']['eligible'])
                rows = {row['arm']: row for row in report['attempts'] if row['pair'] == 'damaged'}
                self.assertEqual(rows['baseline']['state'], 'observer_failure')
                self.assertEqual(rows['baseline']['input_tokens'], 100)
                self.assertEqual(rows['candidate']['state'], 'observer_failure')
                self.assertIsNone(rows['candidate']['input_tokens'])

    def test_reading_result_errors_share_one_view_and_recover_spend_without_success(self):
        run.save(self.root / 'plan.json', {'comparison': 'protocol', 'model': run.transport.MODEL,
            'cases': ['routed'], 'pairs': [{'id': name, 'case': 'routed'} for name in ('good', 'damaged', 'empty')]})
        summary = {'seconds': 3, 'tool_items': 2, 'tool_output_bytes': 9,
            'requested_model': run.transport.MODEL, 'native_models': [run.transport.MODEL],
            'requested_reasoning': 'medium', 'native_reasoning': ['medium'],
            'native_turn_usage': {'input_tokens': 100, 'cached_input_tokens': 80, 'output_tokens': 12}}
        for name in ('good', 'damaged'):
            for arm in ('baseline', 'candidate'):
                directory = self.root / 'runs' / name / arm
                directory.mkdir(parents=True)
                run.save(directory / '1.summary.json', summary)
                run.save(directory / 'result.json', {'state': 'passed', 'turns': [{'turn': 1,
                    'costs': run.costs(summary), 'reading': {'contract_seen': True}}]})
                if name == 'damaged':
                    run.save(directory / '2.summary.json', {**summary, 'native_turn_usage': None})
        (self.root / 'runs/empty/candidate').mkdir(parents=True)
        invalid = (None, b'{', b'[]', b'\xff', b'{"state":"passed","turns":{}}',
                   b'{"state":"passed","turns":[null]}',
                   b'{"state":"passed","turns":[{"turn":1,"reading":[]}]}',
                   b'{"state":"passed","turns":[{"turn":1,"costs":[]}]}')
        read_text = Path.read_text
        for saved in invalid:
            with self.subTest(saved=saved):
                for arm in ('baseline', 'candidate'):
                    path = self.root / 'runs/damaged' / arm / 'result.json'
                    if saved is None:
                        path.unlink()
                    else:
                        path.write_bytes(saved)
                originals = {path: path.read_bytes() for path in (self.root / 'runs').rglob('*.json')}
                reads = {}
                def read_once(path, *args, **kwargs):
                    if path.name == 'result.json':
                        reads[path] = reads.get(path, 0) + 1
                    return read_text(path, *args, **kwargs)
                with patch.object(Path, 'read_text', autospec=True, side_effect=read_once):
                    run.report(self.root)
                self.assertTrue(all(count == 1 for count in reads.values()))
                self.assertEqual(originals, {path: path.read_bytes() for path in originals})
                report = json.loads((self.root / 'report.json').read_text())
                self.assertTrue(next(pair for pair in report['pairs'] if pair['pair'] == 'good')['eligible'])
                self.assertFalse(next(pair for pair in report['pairs'] if pair['pair'] == 'damaged')['eligible'])
                damaged = [row for row in report['attempts'] if row['pair'] == 'damaged']
                self.assertEqual(len(damaged), 4)
                for row in damaged:
                    self.assertEqual(row['state'], 'observer_failure')
                    self.assertFalse(row['cost_comparable'])
                    self.assertIn('result.json', row['report_error'])
                    self.assertEqual(row['input_tokens'], 100 if row['turn'] == 1 else None)
                empty = {row['arm']: row for row in report['attempts'] if row['pair'] == 'empty'}
                self.assertEqual(empty['baseline']['state'], 'unrun')
                self.assertIsNone(empty['baseline']['report_error'])
                self.assertEqual(empty['candidate']['state'], 'observer_failure')
                self.assertIn('FileNotFoundError', empty['candidate']['report_error'])
                self.assertIsNone(empty['candidate']['input_tokens'])
                markdown = (self.root / 'report.md').read_text()
                self.assertIn('| good | baseline | 1 | True |', markdown)
                self.assertIn('Evidence errors', markdown)
                self.assertIn('result.json', markdown)

    def test_plan_freezes_comparable_inputs_balances_order_and_refuses_overwrite(self):
        source = self.root/'source'
        (source/'skills').mkdir(parents=True)
        (source/'skills/example.md').write_text('frozen source\n')
        args = Namespace(output=self.root/'experiment', comparison='index', baseline=None, candidate=source,
                         repeats=2, documents=1, cap=30, seed=20261109, cases=['routed', 'warm'])
        run.prepare(args)
        plan = json.loads((args.output/'plan.json').read_text())
        first_arms = dict(plan['order'][::2])
        for case in args.cases:
            self.assertEqual(first_arms[case + '-r1'], 'baseline')
            self.assertEqual(first_arms[case + '-r2'], 'candidate')
        self.assertEqual(plan['bundles']['baseline']['manifest'], plan['bundles']['candidate']['manifest'])
        with self.assertRaisesRegex(ValueError, 'never overwritten'):
            run.prepare(args)

    def test_returned_reading_evidence_does_not_use_self_report(self):
        records = [
            {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'Physical express supports only north and south'}},
            {'type': 'item.completed', 'item': {'type': 'command_execution', 'aggregated_output': 'digital goods always return fee 0 and days 0\n# Returns workflow 1'}}]
        (self.root/'1.jsonl').write_text('\n'.join(map(json.dumps, records)))
        read = run.reading_observations(self.root, 1)
        self.assertFalse(read['contract_seen'])
        self.assertTrue(read['eligibility_seen'])
        self.assertEqual(read['distractor_documents_seen'], 1)

    def test_ci_rejects_billable_entrypoint_before_starting_any_process(self):
        with patch.dict(run.os.environ, {'CI': 'true'}), patch.object(run.subprocess, 'Popen') as start:
            with self.assertRaisesRegex(ValueError, 'disabled in CI'):
                run.run_models(Namespace(output=self.root/'does-not-exist'))
            start.assert_not_called()

    def test_generated_memory_is_clean_except_the_intentional_broken_route(self):
        checker = run.HERE.parents[1]/'skills/ssot-doctor/assets/scripts/ssot-check.py'
        for case in cases.CASES:
            repo = self.root/case
            p = cases.build(repo, case, True, 11, documents=1)
            run.init_git(repo)
            if case == 'warm':
                cases.update(repo, p)
            check = run.subprocess.run([run.sys.executable, str(checker), str(repo/'SSOT')],
                                       cwd=repo, capture_output=True, text=True)
            if case == 'stale':
                self.assertNotEqual(check.returncode, 0)
                self.assertIn('shipping-v0.md', check.stdout)
            else:
                self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
                self.assertNotIn('WARN', check.stdout)


if __name__ == '__main__':
    unittest.main()
