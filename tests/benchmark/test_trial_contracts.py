"""Calibrate native identities, persistence goals and whole-project privacy offline."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import handoff_cases as cases
import run


class TrialContractsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir='/tmp')
        self.root = Path(self.temp.name)
        self.home = self.root / 'home'
        (self.home / 'sessions').mkdir(parents=True)

    def tearDown(self):
        self.temp.cleanup()

    def receipt(self, records, turn=1):
        path = self.home / 'sessions/session-thread.jsonl'
        path.write_text('\n'.join(map(json.dumps, records)))
        summary = {'thread_id': 'thread', 'requested_model': run.transport.MODEL,
                   'requested_reasoning': 'medium'}
        run.transport.record_native(self.root, turn, summary, self.home)
        return summary

    def context(self, effort='medium', turn_id='first', model=None):
        return {'type': 'turn_context', 'payload': {'root_turn_id': turn_id,
                'model': model or run.transport.MODEL, 'effort': effort}}

    def test_native_reasoning_valid_missing_and_mismatched_are_distinct(self):
        for effort, state in (('medium', None), (None, 'observer_failure'), ('high', 'reasoning_mismatch')):
            with self.subTest(effort=effort):
                record = self.context(effort)
                if effort is None:
                    del record['payload']['effort']
                summary = self.receipt([record])
                self.assertEqual(summary['native_reasoning'], [effort])
                self.assertEqual(run.transport.native_identity_state(summary, run.transport.MODEL), state)
                summary.update(returncode=0, native_completed=True, completed=state is None, observation_complete=True)
                self.assertEqual(run.transport.completion_state([summary], 1, run.transport.MODEL), state)

    def test_resume_selects_current_turn_identity_and_keeps_missing_context(self):
        summary = self.receipt([self.context('high'), self.context('medium', 'second')], turn=2)
        self.assertEqual(summary['native_reasoning'], ['medium'])
        self.assertIsNone(run.transport.native_identity_state(summary, run.transport.MODEL))
        summary = self.receipt([self.context('medium'), self.context(None)])
        self.assertCountEqual(summary['native_reasoning'], [None, 'medium'])
        self.assertEqual(run.transport.native_identity_state(summary, run.transport.MODEL), 'observer_failure')

    def test_saved_historical_summary_cannot_invent_verified_effort(self):
        summary = {'native_models': [run.transport.MODEL], 'requested_model': run.transport.MODEL,
                   'native_turn_usage': {'input_tokens': 12, 'cached_input_tokens': 0, 'output_tokens': 2},
                   'seconds': 1, 'tool_items': 0, 'tool_output_bytes': 0}
        self.assertEqual(run.transport.native_identity_state(summary, run.transport.MODEL), 'observer_failure')
        self.assertIsNone(run.costs(summary))
        summary['requested_reasoning'] = 'medium'
        self.assertIsNone(run.costs(summary))  # Requested medium is not native evidence.
        summary['native_reasoning'] = ['high']
        self.assertIsNone(run.costs(summary))
        summary['native_reasoning'] = ['medium']
        self.assertEqual(run.costs(summary)['input_tokens'], 12)
        summary['requested_model'] = 'different'
        self.assertIsNone(run.costs(summary))

    def test_real_transport_stops_on_unverified_or_wrong_native_reasoning(self):
        # A local CLI fake emits the real event envelope; it never calls a model.
        fake = self.root / 'fake-codex'
        fake.write_text('#!/usr/bin/env python3\nimport sys,json\nsys.stdin.read()\n'
                        'print(json.dumps({"type":"thread.started","thread_id":"thread"}))\n'
                        'print(json.dumps({"type":"turn.completed"}))\n')
        fake.chmod(0o700)
        popen = subprocess.Popen
        def process(command, **kwargs):
            self.assertEqual(command[:3], ['timeout', '--signal=TERM', '--kill-after=10'])
            return popen(command[4:], **kwargs)
        for effort, state in (('medium', None), (None, 'observer_failure'), ('high', 'reasoning_mismatch')):
            with self.subTest(effort=effort):
                self.receipt([self.context(effort)])
                workspace = self.root / ('workspace-' + str(effort))
                workspace.mkdir()
                evidence = self.root / ('evidence-' + str(effort))
                evidence.mkdir()
                with patch.object(run.transport.shutil, 'which', return_value=str(fake)), \
                        patch.object(run.transport.subprocess, 'Popen', side_effect=process):
                    summary = run.transport.execute_turn(self.root, evidence, workspace, 'task', 1, 10,
                        sandbox_command=['env'], codex_home=self.home)
                self.assertTrue(summary['native_completed'])
                self.assertTrue(summary['observation_complete'])
                self.assertEqual(summary['requested_reasoning'], 'medium')
                self.assertEqual(summary['native_identity_state'], state)
                self.assertEqual(summary['completed'], state is None)
                self.assertIn('model_reasoning_effort="medium"', summary['command'])

    def test_privacy_includes_git_and_agent_files_without_following_symlinks(self):
        spec = cases.contract('reporting', 7)
        repo = self.root / 'repo'
        cases.build(repo, spec)
        (repo / '.git').mkdir()
        (repo / '.agents').mkdir()
        before = run.transport.tree_snapshot(repo)
        outside = self.root / 'outside'
        outside.mkdir()
        (outside / 'secret').write_text(spec['private'])
        (repo / '.git/external-directory').symlink_to(outside, target_is_directory=True)
        (repo / '.git/external-file').symlink_to(outside / 'secret')
        self.assertEqual(cases.private_scan(repo, spec['private'].encode()), (False, True))
        for name in ('.git/diagnostic-note', '.agents/diagnostic-note'):
            with self.subTest(name=name):
                path = repo / name
                path.write_text(spec['private'])
                checks, _ = cases.writer_checks(repo, spec, before, run.transport.tree_snapshot(repo))
                self.assertFalse(checks['private_token_not_retained'])
                self.assertTrue(checks['private_scan_complete'])
                path.unlink()

    def test_privacy_observation_gap_is_not_success_and_chunks_preserve_matches(self):
        repo = self.root / 'repo'
        repo.mkdir()
        (repo / 'large').write_bytes(b'x' * 65534 + b'diagnostic-unique')
        self.assertEqual(cases.private_scan(repo, b'diagnostic-unique'), (True, True))
        with patch.object(cases.os, 'open', side_effect=PermissionError('unreadable')):
            self.assertEqual(cases.private_scan(repo, b'diagnostic-unique'), (False, False))

    def test_explicit_goal_changes_only_persistence_instruction_for_both_turns(self):
        legacy = {'reporting': 'f3b99ae8815bbcf583ada8167058e93c3905b9f0c6cbf52ce1df3446aff68e8d',
                  'editorial': '66aef96e1ec6d8885ea6671278e280006df94b53f2256792cee6f54e1293d9d3'}
        for case, digest in legacy.items():
            spec = cases.contract(case, 7)
            automatic = cases.prompts(spec)
            self.assertEqual(automatic, cases.prompts(spec, 'automatic'))
            self.assertEqual(hashlib.sha256(json.dumps(automatic, sort_keys=True).encode()).hexdigest(), digest)
            explicit = cases.prompts(spec, 'explicit')
            goals = [new.removeprefix(old) for old, new in zip(automatic, explicit)]
            self.assertEqual(goals[0], goals[1])
            self.assertIn('Save the accepted policy', goals[0])
            self.assertIn('existing document owners', goals[0])
            self.assertNotIn('SSOT', goals[0])
            self.assertEqual(len(explicit), 2)
            for old, new in zip(automatic, explicit):
                self.assertTrue(new.startswith(old))
                self.assertIn('do not implement', new)
            with self.assertRaises(ValueError):
                cases.prompts(spec, 'unspecified')

    def test_independent_museum_source_is_verbatim_seed_invariant_and_uses_generic_oracle(self):
        fixture = cases.museum_fixture()
        self.assertEqual(fixture['source_sha256'], 'e083cf12c7a84a554a1d6cebb1ef1b1ba092f89fda101ca354dd5969712cdf69')
        spec = cases.contract('museum', 7)
        self.assertEqual(spec, cases.contract('museum', 99))
        self.assertEqual(cases.prompts(spec, 'explicit'), fixture['prompts'])
        self.assertEqual(cases.consumer_prompt(spec), fixture['consumer'])
        self.assertNotIn('expected', fixture)
        self.assertEqual(spec['field'], 'object_key_7c91e2b4')
        repo = self.root / 'museum'
        cases.build(repo, spec, 'ceiling')
        cases.write(repo, spec['output'], json.dumps(cases.expected(spec)))
        self.assertTrue(cases.output_grade(repo, spec)['policy_matches'])
        cases.write(repo, spec['output'], json.dumps(cases.expected(spec, stale=True)))
        self.assertFalse(cases.output_grade(repo, spec)['policy_matches'])


if __name__ == '__main__':
    unittest.main()
