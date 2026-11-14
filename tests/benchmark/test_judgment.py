"""Prose cannot receive a useful-content verdict from a file/keyword oracle."""
import argparse
import json
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys
from unittest.mock import patch

import handoff as h
import handoff_cases as cases
import judgment_cases as j


class JudgmentTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir='/tmp')
        self.root = Path(self.temp.name)
        self.c = cases.contract('judgment', 0)

    def tearDown(self):
        self.temp.cleanup()

    def test_artifact_observation_never_decides_usefulness(self):
        repo = self.root / 'workspace'
        cases.build(repo, self.c, 'ceiling')
        for text in ('', '# 完整通过\n作者已认所有人放弃愿望。', '另一种完全合法的布局，需要实际评审。'):
            (repo / self.c['output']).write_text(text)
            result = cases.output_grade(repo, self.c)
            self.assertTrue(result['deliverable_readable'])
            self.assertTrue(result['present'])
            self.assertNotIn('policy_matches', result)
            self.assertEqual(result['text'], text)
        (repo / self.c['output']).unlink()
        self.assertFalse(cases.output_grade(repo, self.c)['present'])
        (repo / self.c['output']).symlink_to(repo / self.c['owner'])
        self.assertFalse(cases.output_grade(repo, self.c)['deliverable_readable'])

    def test_protected_files_and_exact_writer_scope(self):
        repo = self.root / 'workspace'
        cases.build(repo, self.c)
        before = h.T.tree_snapshot(repo)
        (repo / self.c['owner']).write_text('A different but permitted narrative.\n')
        self.assertTrue(all(cases.writer_checks(repo, self.c, before, h.T.tree_snapshot(repo))[0].values()))
        (repo / 'creation/extra.md').write_text('Unrequested new ledger')
        checks, paths = cases.writer_checks(repo, self.c, before, h.T.tree_snapshot(repo))
        self.assertFalse(checks['write_scope_preserved'])
        self.assertIn('creation/extra.md', paths)
        (repo / 'archive/old-programme.md').write_text('Erased')
        self.assertFalse(cases.writer_checks(repo, self.c, before, h.T.tree_snapshot(repo))[0]['protected_paths_preserved'])

    def seal(self, arm='baseline'):
        d = self.root / 'runs/judgment' / arm
        d.mkdir(parents=True)
        h.save(d / 'mechanical.json', {'state': 'calibration_pending' if arm in ('floor', 'stale') else 'semantic_pending',
            'checks': {'deliverable_readable': True}, 'evaluation': 'prose',
            'semantic_obligations': [*h.SEMANTIC, *j.SEMANTIC], 'turns': []})
        identity = h.evidence_identity(d)
        h.save(d / 'result.json', {'state': 'semantic_pending', 'evidence': identity, 'turns': []})
        return d, identity

    def test_old_three_obligation_review_cannot_accept_prose(self):
        d, identity = self.seal()
        record = {'reviewer': 'offline calibration', 'evidence': identity,
                  'checks': {k: {'passed': True, 'reason': 'Preserved files'} for k in h.SEMANTIC}}
        review = self.root / 'review.json'
        h.save(review, record)
        with patch.object(h, 'validate'), self.assertRaisesRegex(ValueError, 'semantic obligations'):
            h.review(argparse.Namespace(case='judgment', arm='baseline', review=review), self.root, {})
        self.assertFalse((d / 'review.json').exists())

    def test_semantic_content_failure_and_negative_control_cannot_be_averaged_away(self):
        for arm, fail in [('baseline', 'reasoned_judgment'), ('stale', 'expected_control_behavior')]:
            d, identity = self.seal(arm)
            record = {'reviewer': 'offline calibration', 'evidence': identity,
                'checks': {k: {'passed': k != fail, 'reason': 'Read actual artifact and source; this is a plumbing calibration.'}
                           for k in (*h.SEMANTIC, *j.SEMANTIC)}}
            review = self.root / f'{arm}.json'
            h.save(review, record)
            with patch.object(h, 'validate'):
                h.review(argparse.Namespace(case='judgment', arm=arm, review=review), self.root, {})
            self.assertEqual(h.verified_result(d, arm)['state'], 'failed_quality')

    def test_consumer_does_not_supply_the_unique_value_judgment(self):
        consumer = cases.consumer_prompt(self.c)
        self.assertNotIn('各人的小成败', consumer)
        self.assertNotIn('不同人物主动愿望', consumer)
        self.assertNotIn('找合奏伙伴', consumer)
        self.assertEqual(len(cases.prompts(self.c, 'explicit')), 2)

    def test_old_automatic_cli_prepare_does_not_admit_unrequested_prose(self):
        output = self.root / 'automatic'
        cli = Path(__file__).parent / 'handoff.py'
        result = subprocess.run([sys.executable, '-B', str(cli), '--prepare', '--baseline', str(cli.parents[2]),
            '--model', 'gpt-6.1-sol', '--capture-goal', 'automatic', '--confirmation', 'none', '--output', str(output)],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = h.load(output / 'plan.json')
        self.assertEqual(set(plan['cases']), {'reporting', 'editorial', 'museum'})
        self.assertEqual(plan['capture_goal'], 'automatic')

    def test_source_transfer_is_explicit_and_cannot_escape(self):
        c = cases.contract('judgment-sources', 0)
        repo = self.root / 'sources'
        cases.build(repo, c)
        self.assertNotIn('research/source-room3.md', cases.handoff_files(repo))
        transfer = cases.handoff_files(repo, c)
        self.assertEqual(transfer['research/source-room3.md'], (repo / 'research/source-room3.md').read_text())
        with self.assertRaisesRegex(ValueError, 'escapes'):
            cases.handoff_files(repo, {**c, 'transfer_roots': ['../outside']})

    def test_writer_lock_and_consumer_path_allowance_are_separate(self):
        c = cases.contract('judgment-partial-unlock', 0)
        repo = self.root / 'partial'
        cases.build(repo, c)
        before = h.T.tree_snapshot(repo)
        (repo / 'creation/roster.md').write_text('Changed too early')
        checks, _ = cases.writer_checks(repo, c, before, h.T.tree_snapshot(repo))
        self.assertFalse(checks['protected_paths_preserved'])
        h.setup(repo, self.root, c, False, self.root, consumer=True)
        instructions = (repo / 'AGENTS.md').read_text()
        self.assertIn('creation/roster.md, action-note.md', instructions)
        self.assertNotIn('creation/schedule.md', instructions)
        self.assertNotIn('creation/poster.md', instructions)
        self.assertIn('does not unlock a frozen file', instructions)

    def test_partial_unlock_requires_actual_action_without_unlocking_poster(self):
        c = cases.contract('judgment-partial-unlock', 0)
        repo = self.root / 'actions'
        cases.build(repo, c, 'ceiling')
        before = h.T.tree_snapshot(repo)
        (repo / c['output']).write_text('I updated the roster.')
        checks = cases.consumer_change_checks(c, before, h.T.tree_snapshot(repo), 'baseline')
        self.assertFalse(checks['required_actions_observed'])
        self.assertTrue(checks['consumer_preserved_handoff'])
        self.assertNotIn('required_actions_observed', cases.consumer_change_checks(c, before, h.T.tree_snapshot(repo), 'stale'))
        (repo / 'creation/roster.md').write_text('A changed roster still needs semantic verification.')
        self.assertTrue(all(cases.consumer_change_checks(c, before, h.T.tree_snapshot(repo), 'baseline').values()))
        self.assertFalse(cases.consumer_change_checks(c, before, h.T.tree_snapshot(repo), 'stale')['consumer_preserved_handoff'])
        self.assertFalse(cases.consumer_change_checks(c, before, h.T.tree_snapshot(repo), 'floor')['consumer_preserved_handoff'])
        (repo / 'creation/poster.md').write_text('Unauthorized sync')
        self.assertFalse(cases.consumer_change_checks(c, before, h.T.tree_snapshot(repo), 'baseline')['consumer_preserved_handoff'])

    def test_confirmation_mechanical_adapter_preserves_original_task_and_criteria(self):
        import hashlib
        c = cases.contract('confirmation-community-repair', 0)
        repo = self.root / 'confirmation'
        cases.build(repo, c)
        self.assertIn(c['owner'], cases.handoff_files(repo, c))
        value = j.fixture(c['case'])
        adapter = value.pop('mechanical_adapter')
        for name in ('case', 'allowed_writer_paths', 'transfer_roots', 'comparison_supported'):
            value['contract'].pop(name)
        reconstructed = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
        self.assertEqual(hashlib.sha256(reconstructed).hexdigest(), adapter['original_sha256'])

    def test_canonical_temp_alias_is_accepted_and_real_outside_rejected(self):
        # Reproduce macOS /tmp -> /private/tmp without rewriting the host's /tmp.
        original = Path.resolve
        def aliases(path, *a, **kw):
            if str(path) == '/tmp' or str(path).startswith('/tmp/'):
                return Path('/private') / str(path).lstrip('/')
            return original(path, *a, **kw)
        args = argparse.Namespace(output=Path('/tmp/ssot-symlink-contract'), baseline=Path.cwd(),
                                  model='gpt-6.1-sol', cap=1)
        with patch.object(Path, 'resolve', aliases), patch.object(Path, 'mkdir', side_effect=RuntimeError('accepted-root')):
            with self.assertRaisesRegex(RuntimeError, 'accepted-root'):
                h.prepare(args)
            args.output = Path('/opt/ssot-outside-contract')
            with self.assertRaisesRegex(ValueError, 'new output'):
                h.prepare(args)

    def test_open_variant_stale_can_update_both_but_not_schedule(self):
        c = cases.contract('judgment-partial-unlock-open', 0)
        repo = self.root / 'open-stale'
        cases.build(repo, c, 'stale')
        before = h.T.tree_snapshot(repo)
        for name in ('creation/roster.md', 'creation/poster.md'):
            (repo / name).write_text((repo / name).read_text().replace('18:40', '19:35'))
        checks = cases.consumer_change_checks(c, before, h.T.tree_snapshot(repo), 'stale')
        self.assertTrue(checks['consumer_preserved_handoff'])
        self.assertEqual(set(cases.consumer_paths(c, 'stale')), {'creation/roster.md', 'creation/poster.md', 'action-note.md'})
        (repo / 'creation/schedule.md').write_text('Unauthorized edit')
        self.assertFalse(cases.consumer_change_checks(c, before, h.T.tree_snapshot(repo), 'stale')['consumer_preserved_handoff'])


if __name__ == '__main__':
    unittest.main()
