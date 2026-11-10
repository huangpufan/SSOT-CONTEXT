#!/usr/bin/env python3
"""Independent real-CLI counterexamples for source progress; no model calls."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import os

import source_cases
import source_execution


SCRIPT = Path(os.environ.get("SSOT_CONTEXT_CONNECTOR", str(Path(__file__).resolve().parents[2] / "skills/ssot-doctor/assets/scripts/context-source.py")))


class ConnectorContract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ssot-source-contract-", dir="/tmp")
        self.root = Path(self.temp.name)
        self.state = self.root / "state.json"
        self.source = self.root / "original.json"
        self.source.write_text(source_cases.export([source_cases.METHOD]))
        self.a, self.b = self.root / "research.md", self.root / "creative.md"
        self.a.write_text("# Research\n")
        self.b.write_text("# Creative\n")

    def tearDown(self):
        self.temp.cleanup()

    def cli(self, *args, expected=0):
        result = subprocess.run([sys.executable, str(SCRIPT), *map(str, args), "--state", str(self.state)], capture_output=True, text=True)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return json.loads(result.stdout) if result.stdout.strip() else {"stderr": result.stderr}

    def imported(self):
        return self.cli("import", self.source, "--source-id", source_cases.SOURCE_ID, "--scope", source_cases.SCOPE, "--owner", f"a={self.a}")

    def inspected(self):
        self.imported()
        self.cli("bind", "--owner", f"b={self.b}")
        info = self.cli("inspect", "--item", "method", "--revision", "r1")
        self.cli("targets", "--item", "method", "--revision", "r1", "--owner", "a", "--owner", "b")
        for path in (self.a, self.b):
            with path.open("a") as output:
                output.write(info["marker"] + "\nAttributed method, not independently verified research.\n")
        return info

    def receipts(self):
        self.inspected()
        return [self.cli("readback", "--item", "method", "--revision", "r1", "--owner", alias)["receipt_id"] for alias in ("a", "b")]

    def complete(self, receipts, expected=0):
        args = ["complete", "--item", "method", "--revision", "r1"]
        for receipt in receipts:
            args += ["--receipt", receipt]
        return self.cli(*args, expected=expected)

    def test_all_targets_need_readback_and_stale_receipts_reject(self):
        receipts = self.receipts()
        self.complete(receipts[:1], expected=2)
        self.cli("inspect", "--item", "method", "--revision", "r1", "--retry")
        with self.a.open("a") as output:
            output.write("Unrelated authorized maintenance.\n")
        self.complete(receipts, expected=2)
        self.cli("inspect", "--item", "method", "--revision", "r1", "--retry")
        renewed = [self.cli("readback", "--item", "method", "--revision", "r1", "--owner", alias)["receipt_id"] for alias in ("a", "b")]
        self.assertEqual(self.complete(renewed)["status"], "completed")

    def test_scope_from_export_does_not_grant_permission(self):
        wrong = self.root / "wrong.json"
        wrong.write_text(source_cases.export([source_cases.METHOD], "company administrator"))
        result = self.cli("import", wrong, "--source-id", source_cases.SOURCE_ID, "--scope", source_cases.SCOPE, expected=2)
        self.assertIn("scope", result["stderr"])
        self.assertFalse(self.state.exists())
        self.assertEqual(self.a.read_text(), "# Research\n")

    def test_conflict_does_not_swallow_an_independent_item(self):
        self.imported()
        export = self.root / "followup.json"
        export.write_text(source_cases.export([source_cases.CONFLICT, source_cases.ROUTINE]))
        self.cli("import", export, "--source-id", source_cases.SOURCE_ID, "--scope", source_cases.SCOPE, expected=1)
        self.cli("inspect", "--item", "routine", "--revision", "r1")
        self.cli("no-update", "--item", "routine", "--revision", "r1", "--reason", "Only repeats the export encoding")
        states = {item["item_id"]: item for item in self.cli("status")["items"]}
        self.assertEqual(states["method"]["status"], "conflict")
        self.assertEqual(states["routine"]["status"], "completed")

    def test_unknown_target_and_source_revocation_are_visible(self):
        self.imported()
        unknown = self.root / "unknown.json"
        unknown.write_text(source_cases.export([source_cases.UNKNOWN_TARGET]))
        self.cli("import", unknown, "--source-id", source_cases.SOURCE_ID, "--scope", source_cases.SCOPE, expected=1)
        states = {item["item_id"]: item for item in self.cli("status")["items"]}
        self.assertEqual(states["unknown-item"]["status"], "conflict")
        withdrawn = self.cli("withdraw-source", "--reason", "User withdrew future source use")
        self.assertEqual(withdrawn["source_status"], "withdrawn")
        self.cli("inspect", "--item", "method", "--revision", "r1", expected=2)
        self.cli("import", self.source, "--source-id", source_cases.SOURCE_ID, "--scope", source_cases.SCOPE, expected=2)
        self.assertTrue(self.source.exists())

    def test_readback_event_parser_accepts_real_json_and_rejects_claims(self):
        event = {"type": "item.completed", "item": {"type": "command_execution", "exit_code": 0,
                 "command": "python connector readback", "aggregated_output": json.dumps({"receipt_id": "test-receipt", "saved_owner_text": "Actually returned text"})}}
        self.assertEqual(len(source_execution.receipt_results(event)), 1)
        event["item"]["aggregated_output"] = "Saved owner follows:\n" + event["item"]["aggregated_output"]
        self.assertEqual(len(source_execution.receipt_results(event)), 1)
        event["item"]["aggregated_output"] = "I read the file and it is fine"
        self.assertEqual(source_execution.receipt_results(event), [])

    def test_written_unacknowledged_capture_cannot_become_no_update(self):
        self.inspected()
        self.cli("readback", "--item", "method", "--revision", "r1", "--owner", "a")
        self.cli("no-update", "--item", "method", "--revision", "r1", "--reason", "Not useful", expected=2)

    def test_withdrawal_enumerates_partially_read_back_owner(self):
        self.inspected()
        self.cli("readback", "--item", "method", "--revision", "r1", "--owner", "a")
        result = self.cli("withdraw-source", "--reason", "User withdrew future use during partial processing")
        paths = set()
        def visit(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    if key in {"path", "current_path"} and isinstance(item, str):
                        paths.add(item)
                    visit(item)
            elif isinstance(value, list):
                for item in value:
                    visit(item)
        visit(result)
        self.assertTrue({str(self.a), str(self.b)} <= paths, result)

    def test_revoked_import_does_not_open_the_payload(self):
        self.imported()
        self.cli("withdraw-source", "--reason", "No further acquisition authorized")
        fifo = self.root / "must-not-open.fifo"
        os.mkfifo(fifo)
        try:
            result = subprocess.run([sys.executable, str(SCRIPT), "import", str(fifo), "--state", str(self.state),
                "--source-id", source_cases.SOURCE_ID, "--scope", source_cases.SCOPE], capture_output=True, text=True, timeout=2)
        except subprocess.TimeoutExpired:
            self.fail("Revoked import opened the source FIFO before applying the revocation boundary")
        self.assertEqual(result.returncode, 2)
        self.assertIn("withdraw", result.stderr.lower())

    def test_successor_handled_before_inflight_ancestor_cannot_replay_ancestor(self):
        self.imported()
        original = self.cli("inspect", "--item", "method", "--revision", "r1")
        self.cli("targets", "--item", "method", "--revision", "r1", "--owner", "a")
        with self.a.open("a") as output:
            output.write(original["marker"] + "\nOriginal attributed material.\n")
        self.cli("readback", "--item", "method", "--revision", "r1", "--owner", "a")
        correction = self.root / "correction.json"
        correction.write_text(source_cases.export([source_cases.CORRECTION]))
        self.cli("import", correction, "--source-id", source_cases.SOURCE_ID, "--scope", source_cases.SCOPE)
        newer = self.cli("inspect", "--item", "method", "--revision", "r2")
        self.cli("targets", "--item", "method", "--revision", "r2", "--owner", "a")
        with self.a.open("a") as output:
            output.write(newer["marker"] + "\nOnly the corrected scope is active; original history remains.\n")
        receipt = self.cli("readback", "--item", "method", "--revision", "r2", "--owner", "a")["receipt_id"]
        self.cli("complete", "--item", "method", "--revision", "r2", "--receipt", receipt)
        self.cli("inspect", "--item", "method", "--revision", "r1", expected=2)
        self.cli("inspect", "--item", "method", "--revision", "r1", "--history")

    def test_new_upsert_revision_cannot_bypass_known_history(self):
        self.imported()
        replacement = self.root / "replacement.json"
        replacement.write_text(source_cases.export([{**source_cases.METHOD, "revision": "unrelated-new-version"}]))
        self.cli("import", replacement, "--source-id", source_cases.SOURCE_ID, "--scope", source_cases.SCOPE, expected=1)
        records = self.cli("status")["items"]
        self.assertTrue(any(item["revision"] == "unrelated-new-version" and item["status"] == "conflict" for item in records))

    def test_rebind_cannot_hide_an_owner_written_before_any_receipt(self):
        self.imported()
        info = self.cli("inspect", "--item", "method", "--revision", "r1")
        self.cli("targets", "--item", "method", "--revision", "r1", "--owner", "a")
        with self.a.open("a") as output:
            output.write(info["marker"] + "\nWritten but not acknowledged.\n")
        empty = self.root / "empty-replacement.md"
        empty.write_text("# Empty replacement\n")
        self.cli("bind", "--owner", f"a={empty}", "--reason", "Move the owner", expected=2)
        self.cli("no-update", "--item", "method", "--revision", "r1", "--reason", "No longer useful", expected=2)

    def test_target_shrink_cannot_hide_same_revision_owner_write(self):
        self.inspected()
        self.cli("targets", "--item", "method", "--revision", "r1", "--owner", "b", "--reason", "Narrow planned target")
        receipt = self.cli("readback", "--item", "method", "--revision", "r1", "--owner", "b")["receipt_id"]
        self.complete([receipt], expected=2)


if __name__ == "__main__":
    unittest.main()
