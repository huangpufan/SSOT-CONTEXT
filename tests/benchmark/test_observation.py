"""Calibrate observation scope and real discovery without model calls."""
import json
import os
from pathlib import Path
import tempfile
import subprocess
import unittest
from unittest.mock import patch

import run

subprocess_popen = subprocess.Popen


class ObservationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir="/tmp")
        self.root = Path(self.temp.name).resolve()

    def fake_process(self, command, **kwargs):
        # The production timeout boundary is exercised by opt-in Linux trials.
        # These fixed local fakes also run in macOS CI without GNU timeout.
        self.assertEqual(command[:3], ["timeout", "--signal=TERM", "--kill-after=10"])
        return subprocess_popen(command[4:], **kwargs)

    def tearDown(self):
        self.temp.cleanup()

    def test_binary_mode_and_link_changes_are_not_text_equality(self):
        workspace = self.root / "workspace"
        workspace.mkdir()
        binary = workspace / "data.bin"
        binary.write_bytes(b"\x80")
        script = workspace / "script.sh"
        script.write_text("exit 0\n")
        outside = self.root / "outside.txt"
        outside.write_text("not authorized observation content")
        link = workspace / "link"
        link.symlink_to(outside)
        before = run.transport.tree_snapshot(workspace)
        text_before = run.transport.snapshot(workspace)
        self.assertNotIn("link", text_before)
        self.assertEqual(before["link"]["target"], str(outside))
        self.assertNotIn("sha256", before["link"])
        binary.write_bytes(b"\x81")
        script.chmod(script.stat().st_mode | 0o100)
        link.unlink()
        link.symlink_to("script.sh")
        after = run.transport.tree_snapshot(workspace)
        self.assertEqual(text_before["data.bin"], run.transport.snapshot(workspace)["data.bin"])
        self.assertEqual({p for p in before if before[p] != after[p]}, {"data.bin", "script.sh", "link"})

    def test_missing_workspace_and_special_file_are_incomplete(self):
        workspace = self.root / "workspace"
        self.assertEqual(run.transport.tree_snapshot(workspace)["."]["kind"], "unavailable")
        workspace.mkdir()
        os.mkfifo(workspace / "pipe")
        self.assertEqual(run.transport.tree_snapshot(workspace)["pipe"]["kind"], "unavailable")

    def test_launch_subdirectory_does_not_shrink_observed_workspace(self):
        workspace = self.root / "workspace"
        launch = workspace / "src"
        launch.mkdir(parents=True)
        owner = workspace / "owner.md"
        owner.write_text("before\n")
        evidence = self.root / "evidence"
        evidence.mkdir()
        fake = self.root / "fake-codex"
        fake.write_text("#!/usr/bin/env python3\nimport sys,json,pathlib\nsys.stdin.read()\n"
                        "cwd=pathlib.Path(sys.argv[sys.argv.index('-C')+1])\n"
                        "(cwd.parent/'owner.md').write_text('after\\n')\n"
                        "print(json.dumps({'type':'turn.completed'}))\n")
        fake.chmod(0o700)
        with patch.object(run.transport.shutil, "which", return_value=str(fake)), \
                patch.object(run.transport.subprocess, "Popen", side_effect=self.fake_process):
            summary = run.transport.execute_turn(self.root, evidence, workspace, "edit owner", 1, 10,
                sandbox_command=["env"], codex_home=self.root / "empty-home", launch_dir=launch)
        self.assertTrue(summary["native_completed"])
        self.assertFalse(summary["completed"])  # Fake transport has no native model receipt.
        self.assertFalse(summary["model_identity_verified"])
        self.assertTrue(summary["observation_complete"])
        self.assertEqual(summary["changed_paths"], ["owner.md"])
        self.assertEqual(summary["tree_changed_paths"], ["owner.md"])
        self.assertEqual(summary["launch_dir"], str(launch))
        self.assertEqual(json.loads((evidence / "1.after.json").read_text())["owner.md"], "after\n")
        with self.assertRaisesRegex(ValueError, "inside the observed workspace"):
            run.transport.execute_turn(self.root, evidence, workspace, "invalid", 1, 10, launch_dir=self.root)

    def test_corrupt_native_receipt_retains_parseable_usage_and_summary(self):
        home = self.root / 'home'
        sessions = home / 'sessions'
        sessions.mkdir(parents=True)
        records = [json.dumps({'type': 'turn_context', 'payload': {'root_turn_id': 'turn', 'model': run.transport.MODEL}}),
                   'broken record', json.dumps({'type': 'token_usage_record', 'payload': {'root_turn_id': 'turn',
                    'turn_token_usage': {'input_tokens': 12, 'cached_input_tokens': 0, 'output_tokens': 2}}})]
        (sessions / 'session-thread.jsonl').write_text('\n'.join(records))
        summary = {'thread_id': 'thread'}
        run.transport.record_native(self.root, 1, summary, home)
        self.assertEqual(summary['native_turn_usage']['input_tokens'], 12)
        self.assertEqual(len(summary['native_receipt_errors']), 1)
        self.assertTrue((self.root / '1.native.jsonl').exists())
        workspace = self.root / 'workspace'
        workspace.mkdir()
        evidence = self.root / 'evidence'
        evidence.mkdir()
        fake = self.root / 'fake-codex'
        fake.write_text('#!/usr/bin/env python3\nimport sys,json\nsys.stdin.read()\nprint(json.dumps({"type":"turn.completed"}))\n')
        fake.chmod(0o700)
        with patch.object(run.transport.shutil, 'which', return_value=str(fake)), \
                patch.object(run.transport.subprocess, 'Popen', side_effect=self.fake_process), \
                patch.object(run.transport, 'record_native', side_effect=ValueError('damaged receipt')):
            result = run.transport.execute_turn(self.root, evidence, workspace, 'task', 1, 10,
                sandbox_command=['env'], codex_home=home)
        self.assertFalse(result['observation_complete'])
        self.assertTrue(result['native_completed'])
        self.assertEqual(json.loads((evidence / '1.summary.json').read_text())['native_receipt_errors'], ['damaged receipt'])


    def test_quoted_names_are_not_a_discovered_catalog(self):
        project = {"role": "user", "content": [{"text": "# AGENTS.md instructions for /workspace\n"
                   "<!-- SSOT-CONTEXT:BEGIN --> Use $ssot-preflight."}]}
        observed = run.transport.discovery_observation(json.dumps([project]))
        self.assertEqual(observed["skills"], [])
        self.assertTrue(observed["instruction_blocks"][0]["ssot_wired"])
        catalog = {"role": "developer", "content": [{"text": "### Available skills\n"
                   "- ssot-preflight: Read context. (file: r1/ssot-preflight/SKILL.md)\n"}]}
        self.assertEqual(run.transport.discovery_observation(json.dumps([project, catalog]))["skills"], ["ssot-preflight"])
        with self.assertRaises(ValueError):
            run.transport.discovery_observation('{}')

    def test_malformed_stream_keeps_effects_raw_bytes_and_native_receipts(self):
        workspace = self.root / "workspace"
        workspace.mkdir()
        evidence = self.root / "evidence"
        evidence.mkdir()
        fake = self.root / "fake-codex"
        fake.write_text("#!/usr/bin/env python3\nimport sys,json,pathlib,time\nsys.stdin.read()\n"
                        "cwd=pathlib.Path(sys.argv[sys.argv.index('-C')+1])\n"
                        "sys.stdout.buffer.write(b'not JSON\\n\\xff\\n')\n"
                        "sys.stdout.buffer.flush()\n"
                        "time.sleep(0.05)\n(cwd/'effect.txt').write_text('one execution\\n')\n"
                        "print(json.dumps({'type':'item.completed','item':None}))\n"
                        "print(json.dumps({'type':'turn.completed'}))\n")
        fake.chmod(0o700)
        def receipt(_directory, _turn, summary, _home):
            summary["native_turn_usage"] = {"input_tokens": 100, "output_tokens": 10}
        with patch.object(run.transport.shutil, "which", return_value=str(fake)), \
                patch.object(run.transport, "record_native", side_effect=receipt), \
                patch.object(run.transport.subprocess, "Popen", side_effect=self.fake_process):
            summary = run.transport.execute_turn(self.root, evidence, workspace, "edit", 1, 10,
                sandbox_command=["env"], codex_home=self.root / "empty-home")
        self.assertEqual(summary["returncode"], 0)
        self.assertTrue(summary["native_completed"])
        self.assertFalse(summary["completed"])
        self.assertFalse(summary["observation_complete"])
        self.assertEqual(len(summary["observation_errors"]), 3)
        self.assertEqual(summary["native_turn_usage"]["input_tokens"], 100)
        self.assertEqual(summary["tree_changed_paths"], ["effect.txt"])
        self.assertTrue((evidence / "1.stdout.log").read_bytes().startswith(b'not JSON\n\xff\n'))
        self.assertEqual(json.loads((evidence / "1.jsonl").read_text()), {"type": "turn.completed"})


if __name__ == "__main__":
    unittest.main()
