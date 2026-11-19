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
        self.root = Path(self.temp.name).resolve()
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

    def test_missing_owner_is_reported_without_blocking_source_withdrawal(self):
        self.complete(self.receipts())
        moved = self.root / "moved-research.md"
        self.a.rename(moved)  # An external move has not repaired the binding.
        result = self.cli("withdraw-source", "--reason", "Permission withdrawn")
        self.assertEqual(result["source_status"], "withdrawn")
        gap = result["unavailable_owners"][0]
        self.assertEqual((gap["owner"], gap["path"], gap["missing"]), ("a", str(self.a), True))
        self.assertIn(str(self.a), {r["path"] for r in result["known_references"]})
        self.assertNotIn(str(moved), {r["path"] for r in result["known_references"]})
        self.assertEqual(self.cli("status")["unavailable_owners"], result["unavailable_owners"])
        self.cli("inspect", "--item", "method", "--revision", "r1", expected=2)
        self.assertTrue(moved.exists())

    def test_repeated_withdrawal_keeps_original_reason_and_refreshes_gaps(self):
        self.imported()
        first = self.cli("withdraw-source", "--reason", "User revoked research use")
        self.assertEqual(first["unavailable_owners"], [])
        self.a.unlink()
        repeated = self.cli("withdraw-source", "--reason", "Retry after interruption")
        self.assertEqual(repeated["reason"], first["reason"])
        self.assertTrue(repeated["unavailable_owners"][0]["missing"])
        self.assertEqual(self.cli("status")["withdrawal_reason"], first["reason"])

    def withdraw_with_fault(self, event, path, fault):
        # A fresh CLI runs the normal transaction up to the selected filesystem event.
        inject = """
import os, runpy, sys
event_name, path, fault = sys.argv[1:4]
del sys.argv[1:4]
sys.argv = sys.argv[1:]
def inject(event, args):
    if event != event_name or path not in args[:2]:
        return
    if fault == "exit":
        os._exit(75)
    raise ValueError("injected filesystem failure")
sys.addaudithook(inject)
runpy.run_path(sys.argv[0], run_name="__main__")
"""
        return subprocess.run([sys.executable, "-c", inject, event, str(path), fault, str(SCRIPT),
                               "withdraw-source", "--state", str(self.state), "--reason", "Owner withdrew use"],
                              capture_output=True, text=True, timeout=10)

    def test_withdrawal_survives_interruption_during_owner_inventory(self):
        self.inspected()
        result = self.withdraw_with_fault("open", self.a, "exit")
        self.assertEqual(result.returncode, 75, result.stderr)
        status = self.cli("status")
        self.assertEqual(status["source_status"], "withdrawn")
        self.assertEqual(status["withdrawal_reason"], "Owner withdrew use")
        self.cli("inspect", "--item", "method", "--revision", "r1", expected=2)
        self.b.unlink()
        repeated = self.cli("withdraw-source", "--reason", "Recover impact report")
        self.assertEqual(repeated["reason"], "Owner withdrew use")
        self.assertEqual([gap["owner"] for gap in repeated["unavailable_owners"]], ["b"])
        self.assertEqual({ref["owner"] for ref in repeated["known_references"]}, {"a", "b"})

    def test_withdrawal_errors_distinguish_failed_save_and_failed_report(self):
        self.imported()
        before = self.state.read_bytes()
        unsaved = self.withdraw_with_fault("os.rename", self.state, "error")
        self.assertEqual(unsaved.returncode, 2, unsaved.stderr)
        self.assertEqual(self.state.read_bytes(), before)
        report = self.withdraw_with_fault("open", self.a, "error")
        self.assertEqual(report.returncode, 2, report.stderr)
        self.assertIn("impact report incomplete", report.stderr)
        self.assertEqual(self.cli("status")["source_status"], "withdrawn")

    def test_inventory_reads_each_binding_once_and_preserves_aliases_and_receipts(self):
        receipts = self.receipts()
        self.complete(receipts)
        note = self.cli("inspect", "--item", "method", "--revision", "r1")
        with self.a.open("a") as handle:
            handle.write(note["marker"] + "<!-- ssot-source:incomplete -->")
        moved = self.root / "new-creative.md"
        self.b.rename(moved)
        self.cli("bind", "--owner", f"b={moved}", "--reason", "Creative owner moved")
        gap = self.root / "missing.md"
        self.cli("bind", "--owner", f"alias={self.a}", "--owner", f"gap={gap}")
        bulk = self.root / "additional.json"
        bulk.write_text(source_cases.export([{**source_cases.METHOD, "item_id": f"other-{n}"} for n in range(127)]))
        self.cli("import", bulk, "--source-id", source_cases.SOURCE_ID, "--scope", source_cases.SCOPE)
        count_opens = """
import json, runpy, sys
counts = dict.fromkeys(json.loads(sys.argv.pop(1)), 0)
sys.argv = sys.argv[1:]
def count(event, args):
    if event == "open" and args[0] in counts:
        counts[args[0]] += 1
sys.addaudithook(count)
try:
    runpy.run_path(sys.argv[0], run_name="__main__")
finally:
    print(json.dumps(counts), file=sys.stderr)
"""
        observed = []
        expected = {str(self.a): 2, str(moved): 1, str(gap): 1}
        for args, field in ((["status"], "known_impacts"), (["withdraw-source", "--reason", "Stop"], "known_references")):
            result = subprocess.run([sys.executable, "-c", count_opens, json.dumps(list(expected)),
                                     str(SCRIPT), *args, "--state", str(self.state)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stderr), expected)
            report = json.loads(result.stdout)
            self.assertEqual([item["owner"] for item in report["unavailable_owners"]], ["gap"])
            observed.append(report[field])
        self.assertEqual(*observed)
        captures = {item["owner"]: item["marker_count"] for item in observed[0] if "located-capture" in item["evidence"]}
        self.assertEqual(captures, {"a": 2, "alias": 2, "b": 1})
        saved = {item["receipt_id"] for item in observed[0] if "readback" in item["evidence"]}
        self.assertEqual(saved, set(receipts))

    def test_missing_unused_target_does_not_prevent_no_update(self):
        self.imported()
        self.a.unlink()
        self.cli("inspect", "--item", "method", "--revision", "r1")
        self.cli("targets", "--item", "method", "--revision", "r1", "--owner", "a")
        result = self.cli("no-update", "--item", "method", "--revision", "r1", "--reason", "No derived record was needed")
        self.assertEqual(result["outcome"], "no-update")
        self.assertTrue(self.cli("status")["unavailable_owners"][0]["missing"])

    def test_unreadable_binding_does_not_become_an_empty_success(self):
        self.imported()
        self.a.unlink()
        self.a.mkdir()  # Reading a directory fails even in a privileged test process.
        self.cli("inspect", "--item", "method", "--revision", "r1")
        self.cli("targets", "--item", "method", "--revision", "r1", "--owner", "a")
        self.cli("no-update", "--item", "method", "--revision", "r1", "--reason", "Nothing found", expected=2)
        result = self.cli("withdraw-source", "--reason", "Permission withdrawn")
        self.assertFalse(result["unavailable_owners"][0]["missing"])
        self.assertEqual(result["source_status"], "withdrawn")

    def test_repaired_move_is_not_reported_as_an_unavailable_current_owner(self):
        self.complete(self.receipts())
        moved = self.root / "moved-research.md"
        self.a.rename(moved)
        self.cli("bind", "--owner", f"a={moved}", "--reason", "Authorized owner move")
        result = self.cli("withdraw-source", "--reason", "Permission withdrawn")
        self.assertEqual(result["unavailable_owners"], [])
        self.assertIn(str(moved), {r["path"] for r in result["known_references"]})
        self.assertIn(str(self.a), {r["path"] for r in result["known_references"]})

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
