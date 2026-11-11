#!/usr/bin/env python3
"""Calibrate C06 oracle against actual CLI progress and an unsafe status counterexample."""
import json
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

            # Two successful completions in one shell event include three receipts;
            # each output object must be matched to its own references.
            method_event = next(e for e in events if e['item']['exit_code'] == 0 and 'complete' in e['item']['command'] and '--item method --revision r1' in e['item']['command'])
            experience_event = next(e for e in events if e['item']['exit_code'] == 0 and 'complete' in e['item']['command'] and '--item experience --revision r1' in e['item']['command'])
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


if __name__ == '__main__':
    unittest.main()
