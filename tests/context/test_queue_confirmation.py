"""Offline calibration of the independent frozen queue confirmation contract."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import queue_confirmation_case as queue
import run


BWRAP = shutil.which('bwrap')
try:
    CAN_PROBE = bool(BWRAP) and subprocess.run([BWRAP, '--ro-bind', '/', '/', '--unshare-net', '--',
        sys.executable, '-B', '-c', 'pass'], capture_output=True, timeout=5).returncode == 0
except (OSError, subprocess.TimeoutExpired):
    CAN_PROBE = False
requires_probe = unittest.skipUnless(CAN_PROBE, 'bubblewrap network namespaces unavailable; native probe not claimed')


def implementation(capacity=5, first=True, dependencies=True, paused=True, external=True, mutate=False):
    """Known fixture implementation; never supplied to a native consumer."""
    return f'''def plan_jobs(jobs):
    records = {{}}
    for position, job in enumerate(jobs):
        if {first!r} and job["id"] in records:
            continue
        records[job["id"]] = (position, job)
    remaining = list(records.values())
    chosen = []
    capacity = {capacity}
    while True:
        eligible = [(position, job) for position, job in remaining
                    if job["ready"] and (not {paused!r} or not job["paused"])
                    and (not {external!r} or not job["external_slot"])
                    and (not {dependencies!r} or all(dep in chosen for dep in job["depends_on"]))]
        if not eligible:
            break
        position, job = min(eligible, key=lambda pair: (not pair[1]["urgent"], pair[0]))
        remaining.remove((position, job))
        if job["cost"] <= capacity:
            chosen.append(job["id"])
            capacity -= job["cost"]
    if {mutate!r} and jobs:
        jobs.append(jobs[0])
    return chosen
'''


ALTERNATE = '''def plan_jobs(jobs):
    unique = {}
    for index, job in enumerate(jobs):
        unique.setdefault(job['id'], (index, job))
    usable = {key for key, (_, job) in unique.items()
              if job['ready'] and not job['paused'] and not job['external_slot']}
    while True:
        reduced = {key for key in usable if set(unique[key][1]['depends_on']) <= usable}
        if reduced == usable:
            break
        usable = reduced
    selected, budget = [], 5
    while usable:
        candidates = [key for key in usable if set(unique[key][1]['depends_on']) <= set(selected)
                      and unique[key][1]['cost'] <= budget]
        if not candidates:
            break
        key = min(candidates, key=lambda k: (not unique[k][1]['urgent'], unique[k][0]))
        selected.append(key)
        budget -= unique[key][1]['cost']
        usable.remove(key)
    return selected
'''


class QueueConfirmationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir='/tmp')
        self.root = Path(self.temp.name)
        self.repo = self.root / 'consumer'
        self.repo.mkdir()
        self.phase = self.root / 'phase'
        self.phase.mkdir()
        self.contract = queue.definition()

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def write(root, name, text):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def probe(self, text, control=None):
        self.write(self.repo, 'src/queue_plan.py', text)
        return queue.consumer_grade(self.repo, self.phase, queue.definition(control), sandbox=self.sandbox())

    def sandbox(self):
        return [BWRAP, '--ro-bind', '/', '/', '--bind', str(self.repo), str(self.repo), '--chdir', str(self.repo), '--']

    @requires_probe
    def test_reference_and_equivalent_implementation_pass_hand_derived_vectors(self):
        self.assertEqual(len(queue.vectors()), 8)
        for code in (implementation(), ALTERNATE):
            with self.subTest(code=code[:30]):
                result = self.probe(code)
                self.assertTrue(result['mechanical_passed'], result)
                self.assertTrue(result['checks']['consumer_current_policy_matches'])
                self.assertTrue(all(row['input_unchanged'] and row['repeat_equal'] for row in result['observed']))

    @requires_probe
    def test_each_declared_mutation_is_rejected(self):
        mutants = {'capacity-still-seven': implementation(capacity=7),
                   'last-id-overwrites-first': implementation(first=False),
                   'urgent-ignores-dependencies': implementation(dependencies=False),
                   'paused-not-applied': implementation(paused=False),
                   'withdrawn-slot-still-eligible': implementation(external=False),
                   'all-ordinary-jobs-deleted': 'def plan_jobs(jobs):\n    return []\n',
                   'input-mutated': implementation(mutate=True)}
        for name, code in mutants.items():
            with self.subTest(name=name):
                result = self.probe(code)
                self.assertFalse(result['mechanical_passed'], result)
        mutation = self.probe(implementation(mutate=True))
        self.assertTrue(any(row['output'] == expected and not row['input_unchanged']
            for row, (_, _, expected, _) in zip(mutation['observed'], queue.vectors())))

    @requires_probe
    def test_floor_is_a_real_gap_and_stale_is_complete_initial_behavior(self):
        floor = self.probe(queue.STUB, 'floor')
        self.assertTrue(floor['mechanical_passed'])
        self.assertFalse(floor['checks']['consumer_current_policy_matches'])
        self.assertTrue(all(row['error'] == 'NotImplementedError' for row in floor['observed']))
        self.assertEqual(floor['calibration_state'], 'gap_candidate')
        self.assertIsNone(floor['checks']['expected_consumer_outcome'])
        self.assertFalse(self.probe(queue.STUB)['mechanical_passed'])
        stale_code = implementation(capacity=7, paused=False, external=False)
        stale = self.probe(stale_code, 'stale')
        self.assertTrue(stale['mechanical_passed'], stale)
        self.assertFalse(stale['checks']['consumer_current_policy_matches'])
        self.assertFalse(self.probe(stale_code)['mechanical_passed'])
        self.assertFalse(self.probe('def plan_jobs(:\n', 'stale')['mechanical_passed'])
        explicit = self.probe('def plan_jobs(jobs):\n    raise RuntimeError("policy undecided")\n', 'floor')
        self.assertEqual(explicit['calibration_state'], 'gap_candidate')
        self.assertIsNone(explicit['floor_semantic_acceptance'])
        bug = self.probe('def plan_jobs(jobs):\n    return missing_name\n', 'floor')
        self.assertEqual(bug['calibration_state'], 'gap_candidate')
        self.assertIsNone(bug['checks']['expected_consumer_outcome'])
        self.assertIsNone(bug['floor_semantic_acceptance'])
        self.assertTrue(any('NameError' in item for item in bug['semantic_review']))
        self.assertTrue(self.probe(implementation(), 'ceiling')['mechanical_passed'])

    @requires_probe
    def test_probe_runs_only_through_supplied_subprocess_boundary(self):
        self.write(self.repo, 'src/queue_plan.py', implementation())
        for boundary in (None, ['env']):
            unavailable = queue.consumer_grade(self.repo, self.phase, self.contract, sandbox=boundary)
            self.assertFalse(unavailable['mechanical_passed'])
            self.assertEqual(unavailable['state'], 'infra')
        actual = subprocess.run
        calls = []
        def execute(command, **kwargs):
            calls.append(command)
            return actual(command, **kwargs)
        with patch.object(queue.subprocess, 'run', side_effect=execute):
            result = queue.consumer_grade(self.repo, self.phase, self.contract, sandbox=self.sandbox())
        self.assertTrue(result['mechanical_passed'])
        self.assertEqual(calls[0][0], BWRAP)
        self.assertIn('--unshare-net', calls[0])
        self.assertIn(['--ro-bind', str(self.repo), str(self.repo)], [calls[0][n:n+3] for n in range(len(calls[0]) - 2)])
        self.assertNotIn('src.queue_plan', sys.modules)
        self.assertTrue(result['execution_observation']['probe_network_namespace_isolated'])
        record = json.loads((self.phase / 'consumer-probe.json').read_text())
        self.assertEqual(record['command'], calls[0])
        self.assertEqual(record['returncode'], 0)
        self.assertTrue(record['stdout'])

    @requires_probe
    def test_probe_launch_and_timeout_are_infra_not_function_quality(self):
        self.write(self.repo, 'src/queue_plan.py', implementation())
        for kind in ('launch', 'timeout'):
            with self.subTest(kind=kind):
                def unavailable(command, **kwargs):
                    if kind == 'launch':
                        raise OSError('controlled executable unavailable')
                    raise subprocess.TimeoutExpired(command, 0.05, output=b'known partial stdout', stderr=b'known partial stderr')
                with patch.object(queue.subprocess, 'run', side_effect=unavailable) as executed:
                    result = queue.consumer_grade(self.repo, self.phase, self.contract, sandbox=self.sandbox())
                self.assertEqual(executed.call_count, 1)
                self.assertEqual(result['state'], 'infra')
                self.assertTrue(result['observation_failed'])
                self.assertFalse(result['mechanical_passed'])
                self.assertIsNone(result['calibration_state'])
                receipt = json.loads((self.phase / 'consumer-probe.json').read_text())
                self.assertEqual(receipt['state'], 'infra')
                self.assertIsNone(receipt['returncode'])
                if kind == 'timeout':
                    self.assertEqual((self.phase / 'consumer-probe.stdout.raw').read_bytes(), b'known partial stdout')
                    self.assertEqual((self.phase / 'consumer-probe.stderr.raw').read_bytes(), b'known partial stderr')
                    self.assertEqual(receipt['execution_completion'], 'unknown')

    @requires_probe
    def test_missing_or_damaged_probe_output_is_observer_failure_but_function_errors_are_quality(self):
        self.write(self.repo, 'src/queue_plan.py', implementation())
        for kind in ('missing', 'corrupt', 'wrong-schema', 'partial', 'nonzero'):
            with self.subTest(kind=kind):
                def damaged(command, **kwargs):
                    prefix = re.search(r'queue-probe-[a-f0-9]+:', command[-1]).group().encode()
                    data = {'missing': b'', 'corrupt': prefix + b'{', 'wrong-schema': prefix + b'[]',
                        'partial': prefix + b'{"rows":[],"violations":[],"import_error":null}', 'nonzero': b'failed to start isolated interpreter'}[kind]
                    return subprocess.CompletedProcess(command, 2 if kind == 'nonzero' else 0, stdout=data, stderr=b'')
                with patch.object(queue.subprocess, 'run', side_effect=damaged) as executed:
                    result = queue.consumer_grade(self.repo, self.phase, self.contract, sandbox=self.sandbox())
                self.assertEqual(executed.call_count, 1)
                self.assertEqual(result['state'], 'observer_failure')
                self.assertTrue(result['observation_failed'])
                self.assertFalse(result['mechanical_passed'])
                self.assertTrue(result['detail'])
        for code in ('def plan_jobs(jobs):\n    return missing_name\n', 'def plan_jobs(:\n'):
            quality = self.probe(code)
            self.assertIsNone(quality['state'])
            self.assertFalse(quality['observation_failed'])
            self.assertFalse(quality['mechanical_passed'])
        for code, actual_type in (('def plan_jobs(jobs):\n    return {"N"}\n', 'set'),
                                  ('def plan_jobs(jobs):\n    return [object()]\n', 'list')):
            quality = self.probe(code)
            self.assertIsNone(quality['state'])
            self.assertFalse(quality['observation_failed'])
            self.assertFalse(quality['mechanical_passed'])
            self.assertTrue(all(not row['return_contract'] and row['return_type'] == actual_type for row in quality['observed']))
        target = self.repo / 'src/queue_plan.py'
        target.unlink()
        missing_deliverable = queue.consumer_grade(self.repo, self.phase, self.contract, sandbox=self.sandbox())
        self.assertIsNone(missing_deliverable['state'])
        self.assertFalse(missing_deliverable['observation_failed'])

    @requires_probe
    def test_probe_evidence_missing_or_corrupted_on_save_is_observer_failure(self):
        self.write(self.repo, 'src/queue_plan.py', implementation())
        write_bytes = Path.write_bytes
        for corrupt in (False, True):
            with self.subTest(corrupt=corrupt):
                path = self.phase / 'consumer-probe.json'
                if path.exists():
                    path.unlink()
                def broken_save(path, data):
                    if path.name == 'consumer-probe.json':
                        return write_bytes(path, b'{') if corrupt else 0
                    return write_bytes(path, data)
                with patch.object(Path, 'write_bytes', autospec=True, side_effect=broken_save):
                    result = queue.consumer_grade(self.repo, self.phase, self.contract, sandbox=self.sandbox())
                self.assertEqual(result['state'], 'observer_failure')
                self.assertTrue(result['observation_failed'])
                self.assertTrue(result['checks']['consumer_current_policy_matches'])
                self.assertFalse(result['mechanical_passed'])

    @requires_probe
    def test_correct_outputs_cannot_hide_writes_transient_writes_or_network(self):
        self.write(self.repo, 'spec/queue-policy.md', 'Keep this policy.\n')
        effects = [
            "open('spec/queue-policy.md','w').write('unauthorized')",
            "p=__import__('pathlib').Path('temporary-write'); p.write_text('transient'); p.unlink()",
            "__import__('socket').socket()",
        ]
        for effect in effects:
            with self.subTest(effect=effect):
                code = implementation().replace('    return chosen',
                    '    try:\n        ' + effect + '\n    except Exception:\n        pass\n    return chosen')
                result = self.probe(code)
                self.assertTrue(result['checks']['consumer_current_policy_matches'])
                self.assertTrue(result['checks']['probe_preserved_workspace'])
                self.assertFalse(result['checks']['probe_no_forbidden_effects'])
                self.assertFalse(result['mechanical_passed'])
                self.assertTrue(result['execution_observation']['audit_violations'])
                self.assertEqual((self.repo / 'spec/queue-policy.md').read_text(), 'Keep this policy.\n')
                self.assertFalse((self.repo / 'temporary-write').exists())

    @requires_probe
    def test_unavailable_probe_snapshot_is_observer_failure_not_quality_or_zero(self):
        self.write(self.repo, 'src/queue_plan.py', implementation())
        unknown = {'.': {'kind': 'unavailable', 'error': 'fixture observation unavailable'}}
        with patch.object(run.bench.transport, 'tree_snapshot', return_value=unknown), \
                patch.object(queue.subprocess, 'run') as executed:
            result = queue.consumer_grade(self.repo, self.phase, self.contract, sandbox=self.sandbox())
        executed.assert_not_called()
        self.assertTrue(result['observation_failed'])
        self.assertEqual(result['state'], 'observer_failure')
        self.assertFalse(result['mechanical_passed'])
        self.assertIsNone(json.loads((self.phase / 'consumer-probe.json').read_text())['returncode'])

    def test_missing_damaged_or_wrong_schema_phase_snapshot_is_observer_failure(self):
        path = self.phase / '1.after.json'
        for raw in (None, b'{', b'[]', b'\xff', b'{"spec/queue-policy.md":{}}'):
            with self.subTest(raw=raw):
                if raw is not None:
                    path.write_bytes(raw)
                elif path.exists():
                    path.unlink()
                result = queue.phase_grade(self.repo, 1, self.phase, {}, self.contract)
                self.assertTrue(result['observation_failed'])
                self.assertEqual(result['state'], 'observer_failure')
                self.assertFalse(result['mechanical_passed'])
                self.assertIn('1.after.json', result['detail'])

    def test_five_phase_contract_retains_frozen_rules_and_handoff_scope(self):
        c = self.contract
        self.assertEqual(c['specification_sha256'], queue.SPEC_SHA256)
        self.assertEqual(c['format'], 4)
        self.assertEqual(c['metadata_roots'], [])
        specs = queue.phases(c)
        self.assertEqual(len(specs), 5)
        self.assertEqual([spec['consumer'] for spec in specs], [False, False, False, False, True])
        self.assertTrue(all(spec['expected'] == 'completed' and not spec['readonly_fault_paths'] for spec in specs))
        self.assertEqual(queue.consumer_prompt(c), queue.consumer_prompt(queue.definition('floor')))
        for control in ('ceiling', 'floor', 'stale'):
            self.assertEqual(len(queue.phases(queue.definition(control))), 1)
            self.assertEqual(queue.consumer_seed_files(queue.definition(control)), {'src/queue_plan.py': queue.STUB})
        self.assertEqual(set(queue.transfer_paths(c)), {'SSOT/README.md', 'spec/queue-policy.md', 'spec/source-use.md', 'PROJECT.md'})
        self.assertFalse(any(name.startswith(('sources/', 'run/', '.agents/')) for name in queue.transfer_paths(c)))

    def test_actual_git_fixture_sources_repeat_and_writer_boundaries(self):
        repo = self.root / 'writer'
        c = self.contract
        queue.build(repo, self.write, c)
        initial_head = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'])
        queue.before_phase(repo, 2, self.write, c)
        queue.before_phase(repo, 3, self.write, c)
        self.assertEqual((repo / 'sources/correction.txt').read_bytes(), (repo / 'sources/repeated-correction.txt').read_bytes())
        self.assertEqual((repo / 'sources/discussion-a.txt').read_text().splitlines()[0],
                         (repo / 'sources/discussion-b.txt').read_text().splitlines()[0])
        self.assertIn('用户独立明确接受', (repo / 'sources/paused.txt').read_text())
        before = run.bench.transport.snapshot(repo)
        self.write(repo, c['owners']['primary'], queue._policy(False))
        self.write(repo, c['owners']['secondary'], '# Current accepted use\n\n初始允许external_slot作为普通候选，仍不授权真实操作。\n')
        (self.phase / '1.after.json').write_text(json.dumps(run.bench.transport.snapshot(repo)))
        valid = queue.phase_grade(repo, 1, self.phase, before, c)
        self.assertTrue(valid['mechanical_passed'], valid)
        self.write(repo, c['consumer']['output'], implementation())
        (self.phase / '1.after.json').write_text(json.dumps(run.bench.transport.snapshot(repo)))
        bad = queue.phase_grade(repo, 1, self.phase, before, c)
        self.assertFalse(bad['checks']['writer_left_consumer_code_untouched'])
        self.assertFalse(bad['checks']['only_authorized_changes'])
        self.write(repo, c['consumer']['output'], queue.STUB)
        self.write(repo, 'sources/accepted.txt', 'rewritten original')
        (self.phase / '1.after.json').write_text(json.dumps(run.bench.transport.snapshot(repo)))
        self.assertFalse(queue.phase_grade(repo, 1, self.phase, before, c)['checks']['source_originals_preserved'])
        self.assertEqual(subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD']), initial_head)

    def test_aggregate_requires_each_phase_and_keeps_semantic_obligations(self):
        c = self.contract
        for number in range(1, 6):
            phase = self.root / f'phase-{number}'
            phase.mkdir()
            (phase / 'phase-verdict.json').write_text(json.dumps({'mechanical_passed': True, 'semantic_review': ['Review authority and scope.']}))
        self.assertTrue(queue.grade(self.repo, self.root, c)['mechanical_passed'])
        (self.root / 'phase-3/phase-verdict.json').write_text('{')
        result = queue.grade(self.repo, self.root, c)
        self.assertFalse(result['mechanical_passed'])
        self.assertFalse(result['checks']['phase_3_passed'])
        self.assertTrue(result['semantic_review'])


if __name__ == '__main__':
    unittest.main()
