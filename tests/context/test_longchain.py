"""Real public-CLI states and outcome mutations; no native model calls."""
import copy
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import longchain_case as case
import run

SCRIPT = Path(__file__).resolve().parents[2] / 'skills/ssot-doctor/assets/scripts/context-source.py'


def write(repo, name, text):
    p = Path(repo) / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


class LongChain(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repo = self.root / 'workspace'
        self.c = case.calibrate_contract(SCRIPT, self.root / 'private-oracle', case.definition())
        case.build(self.repo, write, self.c)
        p = self.repo / case.TOOL
        p.parent.mkdir(parents=True)
        shutil.copy2(SCRIPT, p)
        self.directory = self.root / 'run'
        self.directory.mkdir()
        self.cli('import', 'sources/initial.json', '--source-id', self.c['source_id'], '--scope', self.c['scope'],
                 '--owner', 'findings=research/findings.md', '--owner', 'creative=creation/notes.md', '--owner', 'personal=memory/experiences.md')

    def tearDown(self):
        self.temp.cleanup()

    def cli(self, *args, code=0):
        p = subprocess.run([sys.executable, '-B', str(SCRIPT), *args, '--state', str(self.repo / self.c['state_path'])],
                           cwd=self.repo, text=True, capture_output=True)
        self.assertEqual(p.returncode, code, p.stdout + p.stderr)
        return json.loads(p.stdout) if p.returncode in (0, 1) else p.stderr

    def capture(self, item, revision, owners, content):
        inspected = self.cli('inspect', '--item', item, '--revision', revision)
        self.cli('targets', '--item', item, '--revision', revision, *[x for owner in owners for x in ('--owner', owner)])
        mapping = {'findings': 'primary', 'creative': 'secondary', 'personal': 'personal'}
        for alias in owners:
            p = self.repo / self.c['owners'][mapping[alias]]
            p.write_text(p.read_text() + '\n' + content + '\n' + inspected['marker'] + '\n')
        receipts = [self.cli('readback', '--item', item, '--revision', revision, '--owner', owner)['receipt_id'] for owner in owners]
        self.cli('complete', '--item', item, '--revision', revision, *[x for receipt in receipts for x in ('--receipt', receipt)])
        return receipts

    def grade_phase(self, number, before):
        p = self.directory / f'phase-{number}'
        p.mkdir(exist_ok=True)
        (p / '1.after.json').write_text(json.dumps(run.bench.transport.snapshot(self.repo)))
        result = case.phase_grade(self.repo, number, p, before, self.c)
        (p / 'phase-verdict.json').write_text(json.dumps(result))
        return result

    def initial(self):
        before = run.bench.transport.snapshot(self.repo)
        self.capture('method', 'r1', ['findings', 'creative'], self.c['items']['method']['content'])
        self.capture('experience', 'r1', ['personal'], self.c['items']['experience']['content'])
        self.assertTrue(self.grade_phase(1, before)['mechanical_passed'])

    def partial(self):
        case.before_phase(self.repo, 2, write, self.c)
        before = run.bench.transport.snapshot(self.repo)
        self.cli('import', 'sources/correction.json', '--source-id', self.c['source_id'], '--scope', self.c['scope'])
        data = self.cli('inspect', '--item', 'method', '--revision', 'r2')
        self.cli('targets', '--item', 'method', '--revision', 'r2', '--owner', 'findings', '--owner', 'creative')
        p = self.repo / self.c['owners']['primary']
        p.write_text(p.read_text() + '\n' + self.c['items']['correction']['content'] + '\n' + data['marker'] + '\n')
        return before

    def test_definition_freezes_finite_paths_without_processing_native_fixture(self):
        self.assertEqual(len(case.phases(self.c)), 6)
        self.assertEqual(case.phases(self.c)[1]['readonly_fault_paths'], ['creation/notes.md'])
        self.assertFalse((self.repo / 'sources/correction.json').exists())
        self.assertNotIn(self.c['expected_r2_marker'], (self.repo / 'research/findings.md').read_text())
        for control in ('ceiling', 'floor', 'stale'):
            c = case.definition(control=control)
            self.assertEqual(len(case.phases(c)), 1)
            self.assertTrue(case.phases(c)[0]['consumer'])

    def test_initial_and_ceiling_portable_routes_are_closed_without_writer_config(self):
        def broken_links(root, contract):
            portable = set(case.transfer_paths(contract))
            broken = []
            for name in portable:
                for link in re.findall(r'\]\(([^)#]+)(?:#[^)]*)?\)', (root / name).read_text()):
                    target = (root / name).parent / link
                    relative = str(target.resolve().relative_to(root.resolve()))
                    if relative not in portable or not target.is_file():
                        broken.append((name, link))
            return broken
        for control in (None, 'ceiling'):
            c = case.definition(control=control)
            root = self.root / ('portable-' + str(control))
            case.build(root, write, c)
            self.assertTrue((root / 'connector-setup.txt').is_file())
            self.assertNotIn('connector-setup.txt', case.transfer_paths(c))
            self.assertEqual(broken_links(root, c), [])
            entry = root / c['entry']
            entry.write_text(entry.read_text() + '\n[Writer-only setup](../connector-setup.txt)\n')
            self.assertTrue(broken_links(root, c))

    def test_real_partial_capture_passes_but_second_write_and_early_readback_fail(self):
        self.initial()
        before = self.partial()
        after = run.bench.transport.snapshot(self.repo)
        tracker = case.interrupt_tracker(before, self.c)
        self.assertTrue(tracker(after, {'type': 'item.completed', 'item': {'type': 'file_change'}}))
        self.assertEqual(tracker.observed['kind'], 'partial-owner-capture')
        self.assertTrue(self.grade_phase(2, before)['mechanical_passed'])
        secondary = self.repo / self.c['owners']['secondary']
        secondary.write_text(secondary.read_text() + '\nchanged too early\n')
        self.assertFalse(case.interrupt_predicate(run.bench.transport.snapshot(self.repo), {}, before, self.c))
        self.assertFalse(self.grade_phase(2, before)['mechanical_passed'])
        secondary.write_text(before[self.c['owners']['secondary']])
        self.cli('readback', '--item', 'method', '--revision', 'r2', '--owner', 'findings')
        self.assertFalse(self.grade_phase(2, before)['checks']['no_premature_r2_readback_or_completion'])

    def test_real_recovery_preserves_identity_history_note_and_rejects_old_receipt(self):
        self.initial()
        initial = self.cli('status')
        old = next(x for x in initial['items'] if x['item_id'] == 'method')['receipts'][0]
        self.partial()
        self.cli('complete', '--item', 'method', '--revision', 'r2', '--receipt', old, code=2)
        self.cli('inspect', '--retry', '--item', 'method', '--revision', 'r2')
        case.before_phase(self.repo, 3, write, self.c)
        before = run.bench.transport.snapshot(self.repo)
        # Consolidating old linkage syntax is allowed: the necessary original
        # words and immutable completed history remain, while current linkage is exact.
        primary = self.repo / self.c['owners']['primary']
        old_markers = [m for m in re.findall(r'<!-- ssot-source:[a-f0-9]+ -->', primary.read_text()) if m != self.c['expected_r2_marker']]
        for old_marker in old_markers:
            primary.write_text(primary.read_text().replace(old_marker, ''))
        secondary = self.repo / self.c['owners']['secondary']
        text = secondary.read_text()
        for old_marker in old_markers:
            text = text.replace(old_marker, '')
        secondary.write_text(text + '\n' + self.c['items']['correction']['content'] + '\n' + self.c['expected_r2_marker'] + '\n')
        receipts = [self.cli('readback', '--item', 'method', '--revision', 'r2', '--owner', owner)['receipt_id'] for owner in ('findings', 'creative')]
        self.cli('complete', '--item', 'method', '--revision', 'r2', *[x for receipt in receipts for x in ('--receipt', receipt)])
        self.assertTrue(self.grade_phase(3, before)['mechanical_passed'])
        primary = self.repo / self.c['owners']['primary']
        primary.write_text(primary.read_text() + self.c['expected_r2_marker'])
        self.assertFalse(self.grade_phase(3, before)['mechanical_passed'])

    def test_conflict_does_not_block_new_item_but_conflicted_capture_fails(self):
        self.initial()
        self.partial()
        secondary = self.repo / self.c['owners']['secondary']
        secondary.write_text(secondary.read_text() + '\n' + self.c['expected_r2_marker'] + '\n')
        receipts = [self.cli('readback', '--item', 'method', '--revision', 'r2', '--owner', owner)['receipt_id'] for owner in ('findings', 'creative')]
        self.cli('complete', '--item', 'method', '--revision', 'r2', *[x for receipt in receipts for x in ('--receipt', receipt)])
        case.before_phase(self.repo, 4, write, self.c)
        before = run.bench.transport.snapshot(self.repo)
        self.cli('import', 'sources/repeated-and-new.json', '--source-id', self.c['source_id'], '--scope', self.c['scope'], code=1)
        self.assertFalse(self.grade_phase(4, before)['checks']['independent_new_item_completed'])
        self.capture('followup-window', 'r1', ['personal'], self.c['items']['independent']['content'])
        self.assertTrue(self.grade_phase(4, before)['mechanical_passed'])
        p = self.repo / self.c['owners']['primary']
        p.write_text(p.read_text() + '\n' + self.c['expected_conflict_marker'] + '\n')
        self.assertFalse(self.grade_phase(4, before)['checks']['no_conflicted_capture_marker'])

    def test_exact_current_initial_floor_and_meaningful_mutations(self):
        output = self.repo / self.c['consumer']['output']
        output.parent.mkdir(parents=True)
        output.write_text(json.dumps(self.c['current_policy']))
        self.assertTrue(case.consumer_grade(self.repo, self.root, self.c)['mechanical_passed'])
        for key, old in self.c['initial_policy'].items():
            if old == self.c['current_policy'][key]:
                continue
            value = {**self.c['current_policy'], key: old}
            output.write_text(json.dumps(value))
            self.assertFalse(case.consumer_grade(self.repo, self.root, self.c)['mechanical_passed'], key)
        value = {**self.c['current_policy'], 'testimony_is_canon': 0}
        output.write_text(json.dumps(value))
        self.assertFalse(case.consumer_grade(self.repo, self.root, self.c)['mechanical_passed'])
        c = case.definition(control='stale')
        output.write_text(json.dumps(c['initial_policy']))
        self.assertTrue(case.consumer_grade(self.repo, self.root, c)['mechanical_passed'])
        self.assertFalse(case.consumer_grade(self.repo, self.root, c)['checks']['consumer_current_policy_matches'])
        c = case.definition(control='floor')
        output.unlink()
        self.assertTrue(case.consumer_grade(self.repo, self.root, c)['mechanical_passed'])
        output.write_text(json.dumps({'error': 'Accepted policy choices are missing; not implemented.'}))
        self.assertTrue(case.consumer_grade(self.repo, self.root, c)['gap_candidate'])
        output.write_text(json.dumps({'requires_supporting_evidence': True}))
        self.assertFalse(case.consumer_grade(self.repo, self.root, c)['mechanical_passed'])
        output.write_text('{')
        self.assertFalse(case.consumer_grade(self.repo, self.root, c)['mechanical_passed'])

    def test_limited_withdrawal_preserves_record_and_independent_progress(self):
        self.initial()
        self.partial()
        secondary = self.repo / self.c['owners']['secondary']
        secondary.write_text(secondary.read_text() + '\n' + self.c['expected_r2_marker'] + '\n')
        receipts = [self.cli('readback', '--item', 'method', '--revision', 'r2', '--owner', owner)['receipt_id'] for owner in ('findings', 'creative')]
        self.cli('complete', '--item', 'method', '--revision', 'r2', *[x for receipt in receipts for x in ('--receipt', receipt)])
        case.before_phase(self.repo, 4, write, self.c)
        self.cli('import', 'sources/repeated-and-new.json', '--source-id', self.c['source_id'], '--scope', self.c['scope'], code=1)
        self.capture('followup-window', 'r1', ['personal'], self.c['items']['independent']['content'])
        case.before_phase(self.repo, 5, write, self.c)
        before = run.bench.transport.snapshot(self.repo)
        self.cli('import', 'sources/withdrawal.json', '--source-id', self.c['source_id'], '--scope', self.c['scope'])
        self.capture('experience', 'r2', ['personal'], self.c['items']['withdrawal']['content'])
        self.assertTrue(self.grade_phase(5, before)['mechanical_passed'])
        personal = self.repo / self.c['owners']['personal']
        personal.write_text('All personal material removed.\n')
        self.assertFalse(self.grade_phase(5, before)['checks']['personal_record_retained'])

    def test_missing_corrupt_or_wrong_shape_snapshot_is_observation_failure(self):
        phase = self.directory / 'phase-1'
        phase.mkdir()
        for raw in (None, '{', '[]', '{}', '{"owner": 7}'):
            p = phase / '1.after.json'
            if raw is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_text(raw)
            value = case.phase_grade(self.repo, 1, phase, {}, self.c)
            self.assertEqual(value['state'], 'observer_failure')
            self.assertFalse(value['mechanical_passed'])
            self.assertTrue(value['observation_errors'])

    def test_extra_public_owner_binding_is_rejected_without_any_owner_file_edit(self):
        self.initial()
        before = run.bench.transport.snapshot(self.repo)
        untouched = (self.repo / 'scratch/unrelated.txt').read_bytes()
        self.cli('bind', '--owner', 'outside=scratch/unrelated.txt')
        result = self.grade_phase(1, before)
        self.assertFalse(result['mechanical_passed'])
        self.assertFalse(result['checks']['only_authorized_owner_bindings'])
        self.assertEqual((self.repo / 'scratch/unrelated.txt').read_bytes(), untouched)

    def test_public_status_failure_or_corruption_is_observation_failure(self):
        self.initial()
        before = run.bench.transport.snapshot(self.repo)
        phase = self.directory / 'phase-1'
        for code, text in ((2, ''), (0, '{'), (0, '[]'), (0, '{}')):
            with patch.object(case.subprocess, 'run', return_value=SimpleNamespace(returncode=code, stdout=text, stderr='calibrated status observation gap')):
                value = case.phase_grade(self.repo, 1, phase, before, self.c)
            self.assertEqual(value['state'], 'observer_failure')
            self.assertFalse(value['mechanical_passed'])
            self.assertTrue(value['observation_errors'])


if __name__ == '__main__':
    unittest.main()
