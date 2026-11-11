#!/usr/bin/env python3
"""Offline calibration; no model invocation."""
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest

import cases
import continuation_case as case
import oracle


class ContinuationOracle(unittest.TestCase):
    def test_positive_and_negative_samples(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, phases = root / 'workspace', root / 'run'
            case.build(repo, cases.scenarios.write)
            for n in range(1, 5):
                case.before_turn(repo, n, cases.scenarios.write)
                phase = phases / f'phase-{n}'
                phase.mkdir(parents=True)
                before = oracle.snapshot(repo)
                if n == 1:
                    with (repo / 'research/findings.md').open('a') as handle:
                        handle.write('\n## New evidence\n')
                if n == 3:
                    (repo / 'scratch/message.txt').write_text('Please review the draft.\n')
                if n == 4:
                    (repo / 'deliverables').mkdir()
                    (repo / 'deliverables/interview-checklist.md').write_text('Checklist\n')
                if n == 1:
                    (phase / '1.checkpoints.json').write_text(json.dumps([{'event': 1, 'files': oracle.snapshot(repo)}]))
                for name, value in [('before', before), ('after', oracle.snapshot(repo))]:
                    (phase / f'1.{name}.json').write_text(json.dumps(value))
            self.assertFalse(case.grade(repo, phases)['checks']['observed_context_structure_checked_after_changes'])
            # No structural change needs no structural checker run.
            first_after = phases / 'phase-1/1.after.json'
            saved_after = first_after.read_text()
            checkpoints = phases / 'phase-1/1.checkpoints.json'
            saved_checkpoints = checkpoints.read_text()
            first_after.write_text((phases / 'phase-1/1.before.json').read_text())
            checkpoints.write_text('[]')
            self.assertTrue(case.grade(repo, phases)['checks']['observed_context_structure_checked_after_changes'])
            first_after.write_text(saved_after)
            checkpoints.write_text(saved_checkpoints)
            script = Path(__file__).resolve().parents[2] / 'skills/ssot-doctor/assets/scripts/ssot-check.py'
            checked = subprocess.run([sys.executable, str(script), str(repo / 'SSOT')], capture_output=True, text=True)
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
            event = {'type': 'item.completed', 'item': {'type': 'command_execution', 'exit_code': 0,
                     'command': 'python3 .agents/skills/ssot-doctor/assets/scripts/ssot-check.py SSOT/README.md',
                     'aggregated_output': checked.stdout}}
            (phases / 'phase-1/1.jsonl').write_text(json.dumps(event) + '\n')
            self.assertTrue(case.grade(repo, phases)['mechanical_passed'])
            # A later observed structural edit invalidates an earlier passing check.
            checkpoints = phases / 'phase-1/1.checkpoints.json'
            saved = json.loads(checkpoints.read_text())
            saved[0]['event'] = 2
            checkpoints.write_text(json.dumps(saved))
            self.assertFalse(case.grade(repo, phases)['checks']['observed_context_structure_checked_after_changes'])
            saved[0]['event'] = 1
            checkpoints.write_text(json.dumps(saved))
            second = phases / 'phase-2/1.after.json'
            unchanged = json.loads(second.read_text())
            changed = dict(unchanged)
            changed['creation/notes.md'] += '\n## New owner section\n'
            second.write_text(json.dumps(changed))
            self.assertFalse(case.grade(repo, phases)['checks']['observed_context_structure_checked_after_changes'])
            second.write_text(json.dumps(unchanged))
            event['item']['command'] += ' --since HEAD'
            event['item']['exit_code'] = 3
            (phases / 'phase-1/1.jsonl').write_text(json.dumps(event) + '\n')
            self.assertFalse(case.grade(repo, phases)['checks']['observed_context_structure_checked_after_changes'])
            after_path = phases / 'phase-3/1.after.json'
            after = json.loads(after_path.read_text())
            after['research/findings.md'] += 'unrelated record'
            after_path.write_text(json.dumps(after))
            self.assertFalse(case.grade(repo, phases)['checks']['unrelated_edit_did_not_change_context'])
            after = json.loads((phases / 'phase-1/1.after.json').read_text())
            after['sources/initial.json'] = 'changed'
            (phases / 'phase-1/1.after.json').write_text(json.dumps(after))
            self.assertFalse(case.grade(repo, phases)['checks']['source_originals_preserved_each_turn'])
            (repo / 'deliverables/interview-checklist.md').unlink()
            self.assertFalse(case.grade(repo, phases)['checks']['final_deliverable_exists'])


if __name__ == '__main__':
    unittest.main()
