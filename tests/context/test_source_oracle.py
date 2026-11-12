#!/usr/bin/env python3
"""Calibrate C06 oracle against actual CLI progress and an unsafe status counterexample."""
import json
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import oracle
import source_cases as cases
import source_oracle
import source_execution

SCRIPT = Path(__file__).resolve().parents[2] / 'skills/ssot-doctor/assets/scripts/context-source.py'


class C06Oracle(unittest.TestCase):
    def test_original_completion_then_conflict_blocks_successor(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / 'repo'
            cases.build(repo, lambda root, name, data: self.write(root / name, data))
            (repo / '.tools').mkdir()
            shutil.copy2(SCRIPT, repo / '.tools/context-source.py')
            run = Path(tmp) / 'run'
            run.mkdir()
            state = repo / 'run/source-state.json'
            events = []

            def cli(*args, expected=0):
                command = [sys.executable, str(repo / '.tools/context-source.py'), *args, '--state', str(state)]
                result = subprocess.run(command, text=True, capture_output=True)
                self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                events.append({'type': 'item.completed', 'item': {'type': 'command_execution', 'exit_code': result.returncode,
                    'command': ' '.join(command), 'aggregated_output': result.stdout}})
                return json.loads(result.stdout) if result.stdout.strip() else {}

            source_args = ('--source-id', cases.SOURCE_ID, '--scope', cases.SCOPE)
            cli('import', str(repo / 'sources/initial.json'), *source_args, '--owner', f'findings={repo}/research/findings.md')
            cli('bind', '--owner', f'creation={repo}/creation/notes.md')
            cli('bind', '--owner', f'experience={repo}/memory/experiences.md')

            def capture(item, rev, aliases):
                info = cli('inspect', '--item', item, '--revision', rev)
                target_args = sum((['--owner', a] for a in aliases), [])
                cli('targets', '--item', item, '--revision', rev, *target_args)
                paths = {'findings': 'research/findings.md', 'creation': 'creation/notes.md', 'experience': 'memory/experiences.md'}
                for alias in aliases:
                    with (repo / paths[alias]).open('a') as f:
                        f.write('\n' + info['marker'] + '\n白鹭 retained source material\n')
                receipts = [cli('readback', '--item', item, '--revision', rev, '--owner', a)['receipt_id'] for a in aliases]
                if item == 'method' and rev == 'r1':
                    with (repo / paths[aliases[0]]).open('a') as f:
                        f.write('Authorized edit after readback.\n')
                    cli('complete', '--item', item, '--revision', rev,
                        *sum((['--receipt', r] for r in receipts), []), expected=2)
                    cli('inspect', '--item', item, '--revision', rev, '--retry')
                    receipts = [cli('readback', '--item', item, '--revision', rev, '--owner', a)['receipt_id'] for a in aliases]
                cli('complete', '--item', item, '--revision', rev, *sum((['--receipt', r] for r in receipts), []))

            capture('method', 'r1', ['findings', 'creation'])
            capture('experience', 'r1', ['experience'])
            cli('inspect', '--item', 'routine', '--revision', 'r1')
            cli('no-update', '--item', 'routine', '--revision', 'r1', '--reason', 'encoding only')
            followup = repo / 'sources/followup.json'
            followup.write_text(cases.export([cases.METHOD, cases.CONFLICT, cases.CORRECTION, cases.EXPERIENCE]))
            cli('import', str(followup), *source_args, expected=1)
            cli('inspect', '--item', 'method', '--revision', 'r2')
            cli('targets', '--item', 'method', '--revision', 'r2', '--owner', 'findings', '--owner', 'creation', expected=2)
            cli('no-update', '--item', 'method', '--revision', 'r2', '--reason', 'not needed', expected=2)
            withdrawal = repo / 'sources/withdrawal.json'
            withdrawal.write_text(cases.export([cases.WITHDRAWAL]))
            cli('import', str(withdrawal), *source_args)
            capture('experience', 'r2', ['experience'])
            unknown = repo / 'sources/unknown-target.json'
            unknown.write_text(cases.export([cases.UNKNOWN_TARGET]))
            cli('import', str(unknown), *source_args, expected=1)
            cli('withdraw-source', '--reason', 'future use revoked')
            (run / '1.jsonl').write_text(''.join(json.dumps(e) + '\n' for e in events))
            before = oracle.snapshot(repo)
            (run / '1.before.json').write_text(json.dumps(before))
            (run / '1.after.json').write_text(json.dumps(before))
            result = source_oracle.grade(repo, 'C06', run, oracle.snapshot)
            self.assertTrue(result['mechanical_passed'], result['checks'])
            self.assertEqual(result['formal_tool_observation']['subject_execution'], 'unknown')
            # Inspecting a blocked successor is not a prerequisite for leaving
            # its active owners untouched. Real no-inspect CLI calibration is
            # retained separately; this removes only that unnecessary event.
            no_inspect = [e for e in events if not ('inspect' in e['item']['command'] and '--item method --revision r2' in e['item']['command'])]
            (run / '1.jsonl').write_text(''.join(json.dumps(e) + '\n' for e in no_inspect))
            self.assertTrue(source_oracle.grade(repo, 'C06', run, oracle.snapshot)['mechanical_passed'])

            # Two successful completions in one shell event include three receipts;
            # each output object must be matched to its own references.
            method_event = next(e for e in events if e['item']['exit_code'] == 0 and 'complete' in e['item']['command'] and '--item method --revision r1' in e['item']['command'])
            experience_event = next(e for e in events if e['item']['exit_code'] == 0 and 'complete' in e['item']['command'] and '--item experience --revision r1' in e['item']['command'])
            completed_method = json.loads(method_event['item']['aggregated_output'])
            readbacks = [e for e in events if any(value.get('receipt') in completed_method['references']
                for value in source_execution.receipt_results(e))]
            self.assertEqual({value['receipt']['owner'] for event in readbacks
                for value in source_execution.receipt_results(event)}, {'findings', 'creation'})
            same_batch = json.loads(json.dumps(method_event))
            same_batch['item']['command'] = 'bash source-driver.sh'  # A real wrapper need not name its subcommands.
            same_batch['item']['aggregated_output'] = '\n'.join(e['item']['aggregated_output'] for e in [*readbacks, method_event])
            same_events = [same_batch if e is method_event else e for e in events if all(e is not old for old in readbacks)]
            (run / '1.jsonl').write_text(''.join(json.dumps(e) + '\n' for e in same_events))
            self.assertTrue(source_oracle.grade(repo, 'C06', run, oracle.snapshot)['mechanical_passed'])
            # References have set semantics, while observable output order is
            # meaningful: completion cannot borrow a later readback.
            reverse_refs = {**completed_method, 'references': list(reversed(completed_method['references']))}
            same_batch['item']['aggregated_output'] = '\n'.join(e['item']['aggregated_output'] for e in readbacks) + '\n' + json.dumps(reverse_refs)
            (run / '1.jsonl').write_text(''.join(json.dumps(e) + '\n' for e in same_events))
            self.assertTrue(source_oracle.grade(repo, 'C06', run, oracle.snapshot)['mechanical_passed'])
            for invalid_output in (
                '\n'.join(e['item']['aggregated_output'] for e in [method_event, *readbacks]),
                '\n'.join(e['item']['aggregated_output'] for e in [readbacks[0], method_event]),
            ):
                same_batch['item']['aggregated_output'] = invalid_output
                (run / '1.jsonl').write_text(''.join(json.dumps(e) + '\n' for e in same_events))
                rejected = source_oracle.grade(repo, 'C06', run, oracle.snapshot)
                self.assertFalse(rejected['checks']['multi_owner_method_completed'])
                self.assertFalse(rejected['checks']['readback_receipts_precede_completion'])
            batch = json.loads(json.dumps(method_event))
            batch['item']['command'] += "\n" + experience_event['item']['command']
            batch['item']['aggregated_output'] += "\n" + experience_event['item']['aggregated_output']
            grouped = [batch if e is method_event else e for e in events if e is not experience_event]
            (run / '1.jsonl').write_text(''.join(json.dumps(e) + '\n' for e in grouped))
            self.assertTrue(source_oracle.grade(repo, 'C06', run, oracle.snapshot)['checks']['multi_owner_method_completed'])
            broken = json.loads(json.dumps(grouped))
            method_result = json.loads(method_event['item']['aggregated_output'])
            missing = method_result['references'][0]
            for e in broken:
                if 'readback' in e['item']['command'] and e['item']['exit_code'] == 0:
                    value = json.loads(e['item']['aggregated_output'])
                    if value.get('receipt') == missing:
                        e['item']['aggregated_output'] = '{}'
            (run / '1.jsonl').write_text(''.join(json.dumps(e) + '\n' for e in broken))
            self.assertFalse(source_oracle.grade(repo, 'C06', run, oracle.snapshot)['checks']['multi_owner_method_completed'])
            (run / '1.jsonl').write_text(''.join(json.dumps(e) + '\n' for e in events))
            marker = next(json.loads(e['item']['aggregated_output'])['marker'] for e in events
                          if 'inspect' in e['item']['command'] and '--item method --revision r2' in e['item']['command'])
            owner = repo / 'creation/notes.md'
            prior = owner.read_text()
            owner.write_text(prior + "\n" + marker + "\nunauthorized correction\n")
            self.assertFalse(source_oracle.grade(repo, 'C06', run, oracle.snapshot)['checks']['unadmitted_successor_marker_absent'])
            owner.write_text(prior)
            owner.write_text(prior + '\nOnly support evidence remains.\n')
            no_marker = source_oracle.grade(repo, 'C06', run, oracle.snapshot)
            self.assertIn('creation/notes.md', no_marker['conflicted_owner_changes_for_semantic_review'])
            self.assertTrue(any('without a marker' in text for text in no_marker['semantic_review']))
            owner.write_text(prior)
            checkpoint = run / '2.checkpoints.json'
            checkpoint.write_text(json.dumps([{'files': {'creation/notes.md': prior + marker}}]))
            self.assertFalse(source_oracle.grade(repo, 'C06', run, oracle.snapshot)['checks']['unadmitted_successor_marker_absent'])
            checkpoint.unlink()

            # A forged public status represents the previously possible unsafe state;
            # all actual CLI evidence is unchanged, so the oracle must reject it.
            real_run = subprocess.run
            def unsafe(*args, **kwargs):
                response = real_run(*args, **kwargs)
                status = json.loads(response.stdout)
                original = next(x for x in status['items'] if x['item_id'] == 'method' and x['revision'] == 'r1')
                successor = next(x for x in status['items'] if x['item_id'] == 'method' and x['revision'] == 'r2')
                successor['status'] = 'completed'
                successor['receipts'] = original['receipts']  # Deliberately forged historical-looking public status.
                self.assertGreaterEqual(len(successor['receipts']), 2)
                response.stdout = json.dumps(status)
                return response
            with patch.object(source_oracle.subprocess, 'run', side_effect=unsafe):
                bad = source_oracle.grade(repo, 'C06', run, oracle.snapshot)
            self.assertFalse(bad['checks']['conflicted_method_successor_not_completed'])
            self.assertFalse(bad['mechanical_passed'])
            # Failed successor completion followed by successful status in one
            # shell event remains a valid blocked outcome.
            status = subprocess.run([sys.executable, str(repo / '.tools/context-source.py'),
                'status', '--state', str(state)], capture_output=True, text=True, check=True).stdout
            batch_status = {'type': 'item.completed', 'item': {'type': 'command_execution', 'exit_code': 0,
                'command': 'connector complete --item method --revision r2; connector status',
                'aggregated_output': 'ancestor conflict\n' + status}}
            (run / '1.jsonl').write_text(''.join(json.dumps(e) + '\n' for e in [*events, batch_status]))
            self.assertTrue(source_oracle.grade(repo, 'C06', run, oracle.snapshot)['checks']['conflicted_method_successor_not_completed'])
            # A public completed view cannot be hidden by a later conflicted state.
            completed = {'item_id': 'method', 'revision': 'r2', 'status': 'completed'}
            batch_status['item']['aggregated_output'] = json.dumps(completed) + '\n' + status
            (run / '1.jsonl').write_text(''.join(json.dumps(e) + '\n' for e in [*events, batch_status]))
            self.assertFalse(source_oracle.grade(repo, 'C06', run, oracle.snapshot)['checks']['conflicted_method_successor_not_completed'])
            # A missing original completion or incomplete receipt coverage cannot pass.
            (run / '1.jsonl').write_text(''.join(json.dumps(e) + '\n' for e in events if not ('complete' in e['item']['command'] and '--item method --revision r1' in e['item']['command'])))
            self.assertFalse(source_oracle.grade(repo, 'C06', run, oracle.snapshot)['checks']['multi_owner_method_completed'])

    @staticmethod
    def write(path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data)

    def test_cold_chain_stops_unverified_interruption_before_recovery_side_effects(self):
        spec = importlib.util.spec_from_file_location('native_transport_for_source_test', SCRIPT.parents[4] / 'tests/run-performance-trials.py')
        transport = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(transport)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / 'repo'
            cases.build(repo, lambda r, n, d: self.write(r / n, d), interrupted=True)
            self.write(repo / '.tools/context-source.py', SCRIPT.read_text())
            state = repo / 'run/source-state.json'
            def cli(*args):
                response = subprocess.run([sys.executable, str(repo / '.tools/context-source.py'), *args,
                    '--state', str(state)], capture_output=True, text=True, check=True)
                return json.loads(response.stdout)
            cli('import', str(repo / 'sources/initial.json'), '--source-id', cases.SOURCE_ID, '--scope', cases.SCOPE,
                '--owner', f'findings={repo}/research/findings.md', '--owner', f'creation={repo}/creation/notes.md')
            info = cli('inspect', '--item', 'method', '--revision', 'r1')
            cli('targets', '--item', 'method', '--revision', 'r1', '--owner', 'findings', '--owner', 'creation')
            for path in ('research/findings.md', 'creation/notes.md'):
                with (repo / path).open('a') as handle:
                    handle.write('\n' + info['marker'] + '\nRetained actual source.\n')
            receipts = [cli('readback', '--item', 'method', '--revision', 'r1', '--owner', alias)
                        for alias in ('findings', 'creation')]
            event = {'type': 'item.completed', 'item': {'type': 'command_execution', 'command': 'bash wrapper.sh',
                'exit_code': 0, 'aggregated_output': '\n'.join(json.dumps(value) for value in receipts)}}
            valid = {'intentional_interruption': {'event': 1, 'signal': 'SIGTERM'}, 'completed': False,
                'native_completed': False, 'observation_complete': True, 'returncode': -15,
                'requested_model': transport.MODEL, 'native_models': [transport.MODEL],
                'requested_reasoning': 'medium', 'native_reasoning': ['medium'],
                'native_identity_state': None, 'native_turn_usage': {'input_tokens': 100}}
            owner = repo / 'research/findings.md'
            original = owner.read_bytes()
            variants = [('observer', {'observation_complete': False}),
                ('wrong-model', {'native_models': ['other-model']}),
                ('wrong-effort', {'native_reasoning': ['high']}),
                ('unknown-effort', {'native_reasoning': None})]
            def save(path, data):
                path.write_text(json.dumps(data))
            for name, changed in variants:
                directory = root / name
                directory.mkdir()
                def execute(*args, **kwargs):
                    self.assertTrue(kwargs['interrupt_when']({}, event))
                    summary = {**valid, **changed}
                    if name == 'unknown-effort':
                        summary.pop('native_reasoning')
                    return summary
                with patch.object(transport, 'execute_turn', side_effect=execute) as executed, \
                        patch.object(source_execution.subprocess, 'run') as native_cli:
                    result = source_execution.cold_chain(root, directory, repo, root, {'model': transport.MODEL, 'cap': 5},
                        ['first', 'resume'], transport, lambda home: [], lambda text: text, save)
                self.assertEqual(executed.call_count, 1)
                native_cli.assert_not_called()
                self.assertEqual(owner.read_bytes(), original)
                self.assertTrue((directory / 'interruption-invalid.json').exists())
                self.assertEqual(result[0]['native_turn_usage']['input_tokens'], 100)
            directory = root / 'valid'
            directory.mkdir()
            def execute_valid(*args, **kwargs):
                if 'interrupt_when' in kwargs:
                    self.assertTrue(kwargs['interrupt_when']({}, event))
                    return dict(valid)
                return {**valid, 'completed': True, 'native_completed': True, 'returncode': 0}
            with patch.object(transport, 'execute_turn', side_effect=execute_valid) as executed:
                result = source_execution.cold_chain(root, directory, repo, root, {'model': transport.MODEL, 'cap': 5},
                    ['first', 'resume'], transport, lambda home: [], lambda text: text, save)
            self.assertEqual(executed.call_count, 2)
            self.assertEqual(len(result), 2)
            self.assertEqual(json.loads((directory / 'stale-complete.json').read_text())['returncode'], 2)


if __name__ == '__main__':
    unittest.main()
