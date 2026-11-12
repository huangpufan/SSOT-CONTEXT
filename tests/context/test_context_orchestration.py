#!/usr/bin/env python3
"""Offline attempt/discovery/cost calibration for installed context orchestration."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import subprocess
import unittest
from unittest.mock import patch

import installed_run as installed
import longchain_case
import oracle
import run


class ContextOrchestrationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir='/tmp')
        self.root = Path(self.temp.name)
        (self.root / 'fixture').mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def summary(self, **changed):
        return {'requested_model': 'gpt-6.1-sol', 'native_models': ['gpt-6.1-sol'],
                'requested_reasoning': 'medium', 'native_reasoning': ['medium'],
                'observation_complete': True, 'completed': True, 'native_completed': True, 'returncode': 0,
                'native_discovery': {'skills': ['ssot-preflight'], 'instruction_blocks': []},
                'thread_id': 'offline-thread', 'seconds': 3, 'tool_items': 1, 'tool_output_bytes': 4,
                'native_turn_usage': {'input_tokens': 11, 'cached_input_tokens': 1, 'output_tokens': 2}, **changed}

    def native_receipt(self, path, summary, closing=True, later_output=False):
        turn = 'offline-native-turn'
        rows = [{'type': 'turn_context', 'payload': {'root_turn_id': turn}},
                {'type': 'response_item', 'payload': {'type': 'message', 'role': 'assistant'}},
                {'type': 'token_usage_record', 'payload': {'root_turn_id': turn, 'turn_token_usage': summary.get('native_turn_usage')}}]
        if later_output:
            rows.append({'type': 'response_item', 'payload': {'type': 'custom_tool_call'}})
        if closing:
            rows.append({'type': 'event_msg', 'payload': {'type': 'task_complete', 'root_turn_id': turn}})
        path.write_text('\n'.join(json.dumps(row) for row in rows) + '\n')
        return path

    def plan(self):
        value = {'schema': 2, 'kind': 'ordinary undeclared creative task', 'model': 'gpt-6.1-sol',
                 'cap': 10, 'prompts': ['An ordinary creative task.'], 'fixture_manifest': run.manifest(self.root / 'fixture')}
        run.save(self.root / 'plan.json', value)
        return value

    def test_comparable_cost_requires_actual_model_and_reasoning(self):
        good = self.summary()
        native = self.native_receipt(self.root / 'good.native.jsonl', good)
        self.assertEqual(oracle.native_costs(good, 'gpt-6.1-sol', native)['total_input_output_tokens'], 13)
        for change in ({'native_reasoning': ['high']}, {'native_models': ['other']}, {'native_reasoning': []}):
            with self.subTest(change=change):
                self.assertIsNone(oracle.native_costs({**good, **change}, 'gpt-6.1-sol', native))

    def test_usage_requires_native_closing_coverage_not_summary_completion(self):
        good = self.summary()
        for closing, later, expected in ((True, False, 'complete'), (True, True, 'lower_bound'), (False, True, 'lower_bound'), (False, False, 'lower_bound')):
            with self.subTest(closing=closing, later=later):
                native = self.native_receipt(self.root / 'usage.native.jsonl', good, closing, later)
                observation = oracle.native_observation(good, 'gpt-6.1-sol', native)
                self.assertEqual(observation['usage_status'], expected)
                self.assertEqual(observation['cost_comparable'], expected == 'complete')
                self.assertEqual(observation['observed_costs']['input_tokens'], 11)
                self.assertEqual(observation['complete_costs']['seconds'], 3)
                self.assertEqual(observation['complete_costs']['input_tokens'], 11 if expected == 'complete' else None)
        self.assertFalse(oracle.native_observation(good, 'gpt-6.1-sol')['cost_comparable'])
        absent = self.summary(native_turn_usage=None)
        native = self.native_receipt(self.root / 'missing-usage.native.jsonl', absent)
        observation = oracle.native_observation(absent, 'gpt-6.1-sol', native)
        self.assertEqual(observation['usage_status'], 'unknown')
        self.assertIsNone(observation['observed_costs']['input_tokens'])
        self.assertEqual(observation['observed_costs']['seconds'], 3)

    def test_missing_usage_does_not_erase_time_and_wrong_identity_keeps_spend(self):
        observation = oracle.native_observation(self.summary(native_turn_usage=None), 'gpt-6.1-sol')
        self.assertIsNone(observation['costs'])
        self.assertEqual(observation['observed_costs']['seconds'], 3)
        self.assertIsNone(observation['observed_costs']['input_tokens'])
        observation = oracle.native_observation(self.summary(native_reasoning=['high']), 'gpt-6.1-sol')
        self.assertEqual(observation['identity_state'], 'reasoning_mismatch')
        self.assertEqual(observation['observed_costs']['input_tokens'], 11)
        self.assertFalse(observation['cost_comparable'])

    def test_setup_failure_retains_attempt_before_native_dispatch(self):
        self.plan()
        args = argparse.Namespace(output=self.root, probe_only=False)
        with patch.object(installed, 'validate'), patch.object(run.bench, 'isolated_command', side_effect=OSError('offline sandbox unavailable')), \
                patch.object(run.bench.transport, 'execute_turn') as dispatch, patch.dict(installed.os.environ, {'CI': ''}):
            installed.execute(args)
        dispatch.assert_not_called()
        result = json.loads((self.root / 'run/result.json').read_text())
        self.assertEqual(result['state'], 'infra')
        self.assertEqual(result['turns'], [])
        self.assertEqual(result['phase'], 'setup')
        timing = json.loads((self.root / 'execution-timing.json').read_text())
        self.assertGreaterEqual(timing['elapsed_seconds'], 0)
        self.assertEqual(timing['mechanical_sha256'], hashlib.sha256((self.root / 'run/mechanical.json').read_bytes()).hexdigest())

    def test_probe_only_timing_and_rejected_replay_preserve_existing_attempt(self):
        self.plan()
        with patch.object(installed, 'validate'), patch.object(installed, 'probe'), \
                patch.object(installed.time, 'monotonic', side_effect=[100.0, 112.75]), \
                patch.object(run.bench, 'isolated_command', return_value=['offline-sandbox', '--']), \
                patch.object(run.bench.transport, 'execute_turn') as dispatch, patch.dict(installed.os.environ, {'CI': ''}):
            installed.execute(argparse.Namespace(output=self.root, probe_only=True))
        dispatch.assert_not_called()
        timing = json.loads((self.root / 'execution-timing.json').read_text())
        self.assertEqual(timing['elapsed_seconds'], 12.75)
        self.assertIn('zero-model probes', timing['boundary'])
        original = {str(path.relative_to(self.root)): path.read_bytes() for path in self.root.rglob('*') if path.is_file()}
        with self.assertRaises(ValueError):
            installed.execute(argparse.Namespace(output=self.root, probe_only=True))
        self.assertEqual(original, {str(path.relative_to(self.root)): path.read_bytes() for path in self.root.rglob('*') if path.is_file()})
        # Historical attempts may have no timing receipt. Refusing replay must
        # leave that absence intact rather than retroactively timing a refusal.
        (self.root / 'execution-timing.json').unlink()
        original.pop('execution-timing.json')
        with patch.object(installed, 'validate'), self.assertRaises(ValueError):
            installed.execute(argparse.Namespace(output=self.root, probe_only=True))
        self.assertFalse((self.root / 'execution-timing.json').exists())
        self.assertEqual(original, {str(path.relative_to(self.root)): path.read_bytes() for path in self.root.rglob('*') if path.is_file()})

    def test_setup_timeout_retains_terminal_receipt_and_partial_observation(self):
        self.plan()
        error = subprocess.TimeoutExpired(['offline-probe'], 40, output=b'partial setup stdout', stderr=b'partial setup stderr')
        with patch.object(installed, 'validate'), patch.object(installed, 'probe', side_effect=error), \
                patch.object(run.bench, 'isolated_command', return_value=['offline-sandbox', '--']), \
                patch.object(run.bench.transport, 'execute_turn') as dispatch, patch.dict(installed.os.environ, {'CI': ''}):
            installed.execute(argparse.Namespace(output=self.root, probe_only=False))
        dispatch.assert_not_called()
        result = json.loads((self.root / 'run/result.json').read_text())
        self.assertEqual(result['state'], 'infra')
        self.assertEqual(result['turns'], [])
        error = json.loads((self.root / 'run/infrastructure-error.json').read_text())
        self.assertEqual(error['type'], 'TimeoutExpired')
        self.assertEqual(error['timeout_seconds'], 40)
        self.assertEqual((self.root / 'run/setup-timeout.stdout').read_bytes(), b'partial setup stdout')
        self.assertEqual((self.root / 'run/setup-timeout.stderr').read_bytes(), b'partial setup stderr')

    def test_metadata_authorization_is_explicit_and_catches_observed_write_then_removal(self):
        for kind, allowed in (('development', True), ('confirmation', False)):
            with self.subTest(kind=kind):
                c = longchain_case.definition(kind=kind)
                c['metadata_roots'] = ['run'] if allowed else []
                repo = self.root / ('metadata-' + kind)
                longchain_case.build(repo, installed.cases.scenarios.write, c)
                before = run.bench.transport.snapshot(repo)
                tree = run.bench.transport.tree_snapshot(repo)
                path = repo / 'run/task-state.json'
                path.parent.mkdir()
                path.write_text('Observed metadata write')
                phase = self.root / ('phase-' + kind)
                phase.mkdir()
                run.save(phase / '1.checkpoints.json', [{'event': 1, 'files': run.bench.transport.snapshot(repo)}])
                path.unlink()
                path.parent.rmdir()
                self.assertTrue(installed.workspace_checks(tree, run.bench.transport.tree_snapshot(repo), c)['authorized_workspace_tree_changes'])
                observed = installed.checkpoint_checks(phase, 1, before, c)
                self.assertTrue(observed['checkpoint_observation_complete'])
                self.assertEqual(observed['observed_text_checkpoint_scope_preserved'], allowed)

    def test_each_native_phase_checks_actual_catalog_wiring_and_identity(self):
        good = self.summary(native_discovery={'skills': ['ssot-preflight'], 'instruction_blocks': [{'ssot_wired': True}]})
        self.assertIsNone(installed.phase_state(good, 'gpt-6.1-sol', True, True))
        cases = [({'native_discovery': {}}, 'observer_failure'),
                 ({'native_discovery': {'skills': [], 'instruction_blocks': [{'ssot_wired': False}]}}, 'delivery_failure'),
                 ({'native_reasoning': ['high']}, 'reasoning_mismatch'),
                 ({'observation_complete': False}, 'observer_failure')]
        for change, state in cases:
            with self.subTest(change=change):
                self.assertEqual(installed.phase_state({**good, **change}, 'gpt-6.1-sol', True, True), state)
        stopped = {**good, 'completed': False, 'native_completed': False, 'returncode': -15,
                   'intentional_interruption': {'event': 3, 'signal': 'SIGTERM'}}
        self.assertIsNone(installed.phase_state(stopped, 'gpt-6.1-sol', True, True, interrupted=True))
        self.assertEqual(installed.phase_state(good, 'gpt-6.1-sol', True, True, interrupted=True), 'delivery_failure')
        consumer = self.summary(native_discovery={'skills': [], 'instruction_blocks': [{'ssot_wired': False}]})
        self.assertIsNone(installed.phase_state(consumer, 'gpt-6.1-sol', False, False))
        self.assertEqual(installed.phase_state(good, 'gpt-6.1-sol', False, False), 'delivery_failure')

    def test_tree_guard_observes_binary_permissions_and_links_outside_authorized_owners(self):
        c = longchain_case.definition()
        repo = self.root / 'tree'
        longchain_case.build(repo, installed.cases.scenarios.write, c)
        (repo / 'binary.bin').write_bytes(b'\x80\x00')
        (repo / 'link').symlink_to('scratch/unrelated.txt')
        before = run.bench.transport.tree_snapshot(repo)
        owner = repo / c['owners']['primary']
        owner.write_text(owner.read_text() + '\nAccepted owner update.\n')
        self.assertTrue(all(installed.workspace_checks(before, run.bench.transport.tree_snapshot(repo), c).values()))
        (repo / 'binary.bin').write_bytes(b'\x81\x00')
        self.assertFalse(installed.workspace_checks(before, run.bench.transport.tree_snapshot(repo), c)['authorized_workspace_tree_changes'])
        (repo / 'binary.bin').write_bytes(b'\x80\x00')
        protected = repo / 'scratch/unrelated.txt'
        protected.chmod(0o700)
        self.assertFalse(installed.workspace_checks(before, run.bench.transport.tree_snapshot(repo), c)['authorized_workspace_tree_changes'])
        protected.chmod(before['scratch/unrelated.txt']['mode'])
        (repo / 'link').unlink()
        (repo / 'link').symlink_to(c['owners']['primary'])
        self.assertFalse(installed.workspace_checks(before, run.bench.transport.tree_snapshot(repo), c)['authorized_workspace_tree_changes'])

    def test_observed_git_commit_is_rejected_before_another_phase(self):
        (self.root / 'fixture').rmdir()
        c = longchain_case.definition(kind='confirmation')
        longchain_case.build(self.root / 'fixture', installed.cases.scenarios.write, c)
        plan = self.plan()
        plan.update(kind='installed longchain', longchain=c, phases=longchain_case.phases(c))
        run.save(self.root / 'plan.json', plan)
        observed = {}
        def subject(_root, evidence, repo, _prompt, turn, *_args, **_kwargs):
            if observed:
                raise ValueError('Protected Git edit improperly advanced to another phase')
            before = run.bench.transport.tree_snapshot(repo)
            observed['head_before'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip()
            owner = repo / c['owners']['primary']
            owner.write_text(owner.read_text() + '\nAuthorized document content update.\n')
            subprocess.run(['git', 'add', '--', c['owners']['primary']], cwd=repo, check=True, capture_output=True)
            subprocess.run(['git', '-c', 'user.name=Benchmark', '-c', 'user.email=benchmark@example.invalid',
                            'commit', '--quiet', '-m', 'unauthorized model-side commit'],
                           cwd=repo, check=True, capture_output=True)
            observed['head_after'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip()
            observed['old_tree_guard'] = installed.workspace_checks(before, run.bench.transport.tree_snapshot(repo), c)['authorized_workspace_tree_changes']
            run.save(evidence / '1.checkpoints.json', [{'event': 1, 'files': run.bench.transport.snapshot(repo)}])
            summary = self.summary(native_discovery={'skills': ['ssot-preflight'], 'instruction_blocks': [{'ssot_wired': True}]})
            run.save(evidence / '1.summary.json', summary)
            return summary
        with patch.object(installed, 'validate'), patch.object(installed, 'probe'), \
                patch.object(longchain_case, 'phase_grade', return_value={'checks': {'sample_outcome': True}, 'mechanical_passed': True}) as grader, \
                patch.object(run.bench, 'isolated_command', return_value=['offline-sandbox', '--']), \
                patch.object(run.bench.transport, 'execute_turn', side_effect=subject) as dispatch, \
                patch.dict(installed.os.environ, {'CI': ''}):
            installed.execute(argparse.Namespace(output=self.root, probe_only=False))
        self.assertNotEqual(observed['head_before'], observed['head_after'])
        self.assertTrue(observed['old_tree_guard'])  # Calibrate why byte/type snapshots alone missed this.
        self.assertEqual(dispatch.call_count, 1)
        grader.assert_not_called()
        result = json.loads((self.root / 'run/result.json').read_text())
        self.assertEqual(result['state'], 'failed_quality')
        checked = json.loads((self.root / 'run/phase-1/phase-verdict.json').read_text())
        self.assertFalse(checked['checks']['git_history_identity_preserved'])

    def test_git_guard_allows_owner_staging_and_retains_changed_index_observation(self):
        repo = self.root / 'git-index'
        c = longchain_case.definition(kind='confirmation')
        longchain_case.build(repo, installed.cases.scenarios.write, c)
        before = installed.git_identity(repo)
        owner = repo / c['owners']['primary']
        owner.write_text(owner.read_text() + '\nAuthorized unstaged owner update.\n')
        subprocess.run(['git', 'status', '--porcelain'], cwd=repo, check=True, capture_output=True)
        self.assertEqual(installed.git_identity(repo), before)
        subprocess.run(['git', 'add', '--', c['owners']['primary']], cwd=repo, check=True, capture_output=True)
        after = installed.git_identity(repo)
        self.assertEqual(after['head'], before['head'])
        self.assertEqual(after['refs'], before['refs'])
        self.assertNotEqual(after['index_entries'], before['index_entries'])
        self.assertNotEqual(after, before)
        self.assertTrue(installed.same_git_history(before, after))

    def test_native_catalog_gap_stops_later_prompts_despite_good_setup_probe(self):
        plan = self.plan()
        plan.update(kind='natural source workflow', prompts=['Capture initial source.', 'Apply correction.'])
        run.save(self.root / 'plan.json', plan)
        summary = self.summary(native_discovery={'skills': [], 'instruction_blocks': [{'ssot_wired': False}]})
        def subject(_root, evidence, _repo, _prompt, turn, *_args, **_kwargs):
            run.save(evidence / f'{turn}.summary.json', summary)
            return summary
        with patch.object(installed, 'validate'), patch.object(installed, 'probe', return_value={'skills': ['ssot-preflight']}), \
                patch.object(run.bench, 'isolated_command', return_value=['offline-sandbox', '--']), \
                patch.object(run.bench.transport, 'execute_turn', side_effect=subject) as dispatch, \
                patch.dict(installed.os.environ, {'CI': ''}):
            installed.execute(argparse.Namespace(output=self.root, probe_only=False))
        self.assertEqual(dispatch.call_count, 1)
        result = json.loads((self.root / 'run/result.json').read_text())
        self.assertEqual(result['state'], 'delivery_failure')
        self.assertEqual(len(result['turns']), 1)
        self.assertFalse((self.root / 'run/workspace/sources/followup.json').exists())

    def test_skills_free_consumer_receives_only_declared_documents_and_cannot_edit_them(self):
        base = self.root
        for tamper in ('none', 'handoff', 'checkpoint', 'observation-gap', 'aggregate-gap', 'infrastructure-gap', 'aggregate-infrastructure-gap'):
            with self.subTest(tamper=tamper):
                self.root = base / str(tamper)
                contract = longchain_case.definition(control='ceiling')
                longchain_case.build(self.root / 'fixture', installed.cases.scenarios.write, contract)
                plan = self.plan()
                plan.update(kind='installed longchain', longchain=contract, phases=longchain_case.phases(contract))
                run.save(self.root / 'plan.json', plan)
                consumer = self.root / 'run/consumer/workspace'
                def subject(_root, evidence, repo, _prompt, turn, *_args, **kwargs):
                    self.assertEqual(repo, consumer)
                    self.assertTrue(kwargs['installed_mode'])  # Observe the real empty catalog rather than suppressing discovery.
                    self.assertFalse((repo / '.agents').exists())
                    self.assertFalse((repo / 'sources').exists())
                    self.assertFalse((repo / contract['state_path']).exists())
                    installed.cases.scenarios.write(repo, contract['consumer']['output'], json.dumps(contract['current_policy']))
                    if tamper == 'handoff':
                        (repo / contract['entry']).write_text('Rewritten handoff')
                    checkpoints = []
                    if tamper == 'checkpoint':
                        temporary = repo / 'outside-authorized-output.txt'
                        temporary.write_text('Observed forbidden write, later removed.')
                        checkpoints.append({'event': 1, 'files': run.bench.transport.snapshot(repo)})
                        temporary.unlink()
                    checkpoints.append({'event': 2, 'files': run.bench.transport.snapshot(repo)})
                    run.save(evidence / f'{turn}.checkpoints.json', checkpoints)
                    summary = self.summary(native_discovery={'skills': [], 'instruction_blocks': [{'ssot_wired': False}]})
                    run.save(evidence / f'{turn}.summary.json', summary)
                    return summary
                actual_grade = longchain_case.consumer_grade
                aggregate_grade = longchain_case.grade
                def grade(*args, **kwargs):
                    if tamper in ('observation-gap', 'infrastructure-gap'):
                        return {'checks': {'phase_snapshot_present': False}, 'mechanical_passed': False,
                                'state': 'infra' if tamper == 'infrastructure-gap' else 'observer_failure', 'observation_errors': ['Missing output observation']}
                    return actual_grade(*args, **kwargs)
                def aggregate(*args, **kwargs):
                    if tamper in ('aggregate-gap', 'aggregate-infrastructure-gap'):
                        return {'checks': {'shape_present': True}, 'mechanical_passed': False,
                                'state': 'infra' if tamper == 'aggregate-infrastructure-gap' else 'observer_failure', 'observation_failed': True}
                    return aggregate_grade(*args, **kwargs)
                with patch.object(installed, 'validate'), patch.object(installed, 'probe') as probe, \
                        patch.object(longchain_case, 'consumer_grade', side_effect=grade), \
                        patch.object(longchain_case, 'grade', side_effect=aggregate), \
                        patch.object(run.bench, 'isolated_command', return_value=['offline-sandbox', '--']), \
                        patch.object(run.bench.transport, 'execute_turn', side_effect=subject), \
                        patch.dict(installed.os.environ, {'CI': ''}):
                    installed.execute(argparse.Namespace(output=self.root, probe_only=False))
                self.assertEqual(probe.call_args.args[-2:], (False, False))
                result = json.loads((self.root / 'run/result.json').read_text())
                timing = json.loads((self.root / 'execution-timing.json').read_text())
                self.assertGreaterEqual(timing['elapsed_seconds'], 0)
                expected = 'semantic_pending' if tamper == 'none' else 'infra' if tamper in ('infrastructure-gap', 'aggregate-infrastructure-gap') else 'observer_failure' if tamper in ('observation-gap', 'aggregate-gap') else 'failed_quality'
                self.assertEqual(result['state'], expected)
        self.root = base

    def sealed_attempt(self):
        self.plan()
        d = self.root / 'run'
        (d / 'phase-1').mkdir(parents=True)
        run.save(d / 'phase-1/1.summary.json', self.summary())
        native = self.native_receipt(d / 'phase-1/1.native.jsonl', self.summary())
        result = {'state': 'semantic_pending', 'phase': 'finished', 'turns': [{'phase': 'one', 'summary': 'phase-1/1.summary.json',
                  **oracle.native_observation(self.summary(), 'gpt-6.1-sol', native)}]}
        installed.seal(d, result, {'checks': {'retained_scoped_outcome': True}, 'mechanical_passed': True})
        return d

    def test_artifact_bound_review_replay_and_mutation_keep_observed_spend(self):
        d = self.sealed_attempt()
        result = json.loads((d / 'result.json').read_text())
        record = {'reviewer': 'offline calibration', 'evidence': result['evidence'],
                  'checks': {key: {'passed': True, 'reason': 'Reviewed retained phase evidence'} for key in run.handoff_tools().SEMANTIC}}
        review = self.root / 'external-review.json'
        run.save(review, record)
        with patch.object(installed, 'validate'):
            installed.review(self.root, review)
            installed.review(self.root, review)
            report = installed.report(self.root)
            self.assertEqual(report['state'], 'passed')
            self.assertEqual(report['observed_totals']['input_tokens'], 11)
            self.assertTrue(report['cost_comparable'])
            (d / 'phase-1/1.summary.json').write_text('{')
            report = installed.report(self.root)
        self.assertEqual(report['state'], 'observer_failure')
        self.assertEqual(report['observed_totals']['input_tokens'], 11)
        self.assertFalse(report['cost_comparable'])

    def test_cost_reanalysis_writes_only_new_external_output_and_rejects_overwrite(self):
        self.sealed_attempt()
        original = {str(path.relative_to(self.root)): path.read_bytes() for path in self.root.rglob('*') if path.is_file()}
        with tempfile.TemporaryDirectory(dir='/tmp') as outside:
            target = Path(outside) / 'analysis'
            with patch.object(installed, 'validate') as validate:
                report = installed.report(self.root, target)
                self.assertFalse(validate.call_args.kwargs['require_frozen_reporter'])
                with self.assertRaises(ValueError):
                    installed.report(self.root, target)
                with self.assertRaises(ValueError):
                    installed.report(self.root, self.root / 'inside-source')
            self.assertEqual(report['provenance']['mode'], 'read-only cost reanalysis')
            self.assertTrue((target / 'report.md').is_file())
            self.assertFalse((self.root / 'report.json').exists())
        self.assertEqual(original, {str(path.relative_to(self.root)): path.read_bytes() for path in self.root.rglob('*') if path.is_file()})

    def test_missing_result_recovers_spend_but_not_acceptance_and_started_stays_started(self):
        d = self.sealed_attempt()
        (d / 'result.json').unlink()
        with patch.object(installed, 'validate'):
            report = installed.report(self.root)
            self.assertEqual(report['state'], 'observer_failure')
            self.assertEqual(report['observed_totals']['seconds'], 3)
            run.save(d / 'result.json', {'state': 'started', 'phase': 'one', 'turns': []})
            (d / 'mechanical.json').unlink()
            report = installed.report(self.root)
        self.assertEqual(report['state'], 'started')
        self.assertEqual(report['observed_totals']['seconds'], 3)
        self.assertFalse(report['cost_comparable'])

    def test_old_unsealed_schema_cannot_be_relabelled_as_verified(self):
        d = self.sealed_attempt()
        old = self.plan()
        old['schema'] = 1
        run.save(self.root / 'plan.json', old)
        with patch.object(installed, 'validate'):
            report = installed.report(self.root)
        self.assertEqual(report['state'], 'legacy_unsealed')
        self.assertEqual(report['observed_totals']['seconds'], 3)
        self.assertFalse(report['cost_comparable'])

    def test_seal_failure_records_unknown_identity_instead_of_started(self):
        self.plan()
        tools = run.handoff_tools()
        with patch.object(installed, 'validate'), patch.object(run.bench, 'isolated_command', side_effect=OSError('offline setup unavailable')), \
                patch.object(tools, 'evidence_identity', side_effect=PermissionError('offline unreadable evidence')), \
                patch.dict(installed.os.environ, {'CI': ''}):
            installed.execute(argparse.Namespace(output=self.root, probe_only=False))
        result = json.loads((self.root / 'run/result.json').read_text())
        self.assertEqual(result['state'], 'observer_failure')
        self.assertIsNone(result['evidence'])
        self.assertIn('unreadable', result['evidence_error'])


if __name__ == '__main__':
    unittest.main()
