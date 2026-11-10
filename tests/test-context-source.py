#!/usr/bin/env python3
"""Exercise the POSIX reference CLI's acquisition, capture and recovery boundaries."""
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

CLI = Path(__file__).resolve().parents[1] / "skills/ssot-doctor/assets/scripts/context-source.py"


class SourceContract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.state = self.root / "state.json"
        self.one, self.two = self.root / "one.md", self.root / "two.md"
        self.originals = {}

    def call(self, command, *args, code=0):
        result = subprocess.run([sys.executable, str(CLI), command, "--state", str(self.state),
                                 *map(str, args)], capture_output=True, text=True)
        self.assertEqual(result.returncode, code, (result.stdout, result.stderr))
        # The adapter never mutates or deletes original exports.
        for path, expected in self.originals.items():
            self.assertEqual(path.read_bytes(), expected)
        return json.loads(result.stdout or result.stderr)

    def export(self, name, items, scope="approved synthetic scope"):
        path = self.root / name
        path.write_text(json.dumps({"source_id": "example", "scope": scope, "items": items}))
        self.originals[path] = path.read_bytes()
        return path

    def item(self, ident="a", revision="1", **kwargs):
        return {"item_id": ident, "revision": revision, "operation": "upsert",
                "source_ref": "example-export#" + ident, "content": "SYNTHETIC_PRIVATE_ACCOUNT", **kwargs}

    def acquire(self, path, *bindings, code=0):
        return self.call("import", path, "--source-id", "example", "--scope", "approved synthetic scope",
                         *sum((["--owner", binding] for binding in bindings), []), code=code)

    def action(self, command, ident="a", revision="1", *extra, code=0):
        return self.call(command, "--item", ident, "--revision", revision, *extra, code=code)

    def inspect(self, ident="a", revision="1", retry=False, code=0):
        return self.action("inspect", ident, revision, *(["--retry"] if retry else []), code=code)

    def targets(self, aliases, ident="a", revision="1"):
        return self.action("targets", ident, revision, *sum((["--owner", alias] for alias in aliases), []))

    def readback(self, alias="one", ident="a", revision="1"):
        result = self.action("readback", ident, revision, "--owner", alias)
        self.assertEqual(result["saved_owner_text"], {"one": self.one, "two": self.two}[alias].read_text())
        return result["receipt_id"]

    def complete(self, receipts, ident="a", revision="1", code=0):
        return self.action("complete", ident, revision,
                           *sum((["--receipt", receipt] for receipt in receipts), []), code=code)

    def status(self, ident="a", revision="1"):
        return next(i for i in self.call("status")["items"]
                    if i["item_id"] == ident and i["revision"] == revision)

    def seed_capture(self, aliases=("one",)):
        path = self.export("original.json", [self.item()])
        self.acquire(path, f"one={self.one}", f"two={self.two}")
        item = self.inspect()
        self.targets(aliases)
        for alias in aliases:
            {"one": self.one, "two": self.two}[alias].write_text("# Account\n\nAttributed account.\n" + item["marker"])
        receipts = [self.readback(alias) for alias in aliases]
        self.complete(receipts)
        return path, item, receipts

    def test_trusted_scope_original_locator_and_no_source_payload_cache(self):
        path = self.export("original.json", [self.item(artifact="unopened-audio.wav")])
        self.call("import", path, "--source-id", "example", "--scope", "self-authorized scope", code=2)
        self.assertFalse(self.state.exists())
        self.acquire(path, f"one={self.one}")
        self.assertNotIn("SYNTHETIC_PRIVATE_ACCOUNT", self.state.read_text())
        item = self.inspect()
        self.assertEqual(item["untrusted_source"]["content"], "SYNTHETIC_PRIVATE_ACCOUNT")
        self.assertIn("not opened or hashed", item["artifact_verification"])
        path.rename(self.root / "temporarily-unavailable.json")
        self.originals.pop(path)
        self.inspect(code=2)
        self.assertEqual(self.status()["status"], "failed")
        self.assertNotIn("SYNTHETIC_PRIVATE_ACCOUNT", self.state.read_text())

    def test_all_declared_owners_read_back_before_progress_and_replay_reuses_capture(self):
        path = self.export("original.json", [self.item()])
        self.acquire(path, f"one={self.one}", f"two={self.two}")
        self.complete(["invented"], code=2)
        item = self.inspect(retry=True)
        self.targets(["one", "two"])
        for owner in (self.one, self.two):
            owner.write_text("# Account\n\nRetained account.\n" + item["marker"])
        first = self.readback()
        self.assertEqual(self.status()["status"], "readback-ready")
        # A fresh CLI process after the interruption sees existing owner captures.
        self.acquire(path)
        captures = self.inspect()["existing_captures"]
        self.assertEqual(sum(c.get("marker_count", 0) for c in captures), 2)
        self.complete([first], code=2)
        self.inspect(retry=True)
        receipts = [self.readback("one"), self.readback("two")]
        self.complete(receipts)
        before = self.one.read_bytes(), self.two.read_bytes()
        self.acquire(path)
        self.complete(receipts)
        self.assertEqual(before, (self.one.read_bytes(), self.two.read_bytes()))
        self.assertEqual(self.status()["outcome"], "recorded")

    def test_stale_receipt_recovery_and_explicit_binding_move(self):
        path = self.export("original.json", [self.item()])
        self.acquire(path, f"one={self.one}")
        item = self.inspect();self.targets(["one"])
        self.one.write_text("# Account\n" + item["marker"])
        stale = self.readback()
        self.one.write_text(self.one.read_text() + "\nLater unrelated edit.\n")
        self.complete([stale], code=2)
        self.assertEqual(self.status()["status"], "failed")
        self.inspect(retry=True);receipt = self.readback();self.complete([receipt])
        moved = self.root / "moved.md";moved.write_bytes(self.one.read_bytes())
        self.call("bind", "--owner", f"one={moved}", code=2)
        self.call("bind", "--owner", f"one={moved}", "--reason", "authorized owner move")
        self.complete([receipt], code=2)
        self.assertEqual(self.call("status")["owners"]["one"], str(moved))

    def test_conflicts_do_not_block_unrelated_processing_and_unknown_target_is_visible(self):
        self.seed_capture()
        conflicting = self.export("conflict.json", [self.item(content="Different bytes, same revision")])
        self.acquire(conflicting, code=1)
        unknown = self.export("unknown.json", [self.item("missing", "2", operation="withdrawal", replaces="1")])
        self.acquire(unknown, code=1)
        self.assertEqual(self.status("missing", "2")["status"], "conflict")
        unrelated = self.export("unrelated.json", [self.item("b")])
        self.acquire(unrelated)
        item = self.inspect("b");self.targets(["one"], "b")
        self.one.write_text(self.one.read_text() + "\nSecond account.\n" + item["marker"])
        self.complete([self.readback("one", "b")], "b")
        self.assertEqual(self.status("a")["status"], "conflict")
        missing = self.export("missing.json", [self.item("missing")])
        self.acquire(missing)
        self.assertEqual(self.status("missing", "2")["status"], "pending")

    def test_correction_requires_prior_owners_and_source_withdrawal_stops_processing(self):
        self.seed_capture(("one", "two"))
        changed = self.export("corrected.json", [self.item(revision="2", operation="correction", replaces="1")])
        self.acquire(changed)
        item = self.inspect(revision="2");self.targets(["one"], revision="2")
        for owner in (self.one, self.two):
            owner.write_text(owner.read_text() + "\nCorrected account; unaffected context remains.\n" + item["marker"])
        first = self.readback(revision="2")
        self.complete([first], revision="2", code=2)
        self.inspect(revision="2", retry=True)
        self.action("targets", "a", "2", "--owner", "one", "--owner", "two", "--reason", "all affected owners")
        receipts = [self.readback(alias, revision="2") for alias in ("one", "two")]
        self.complete(receipts, revision="2")
        self.action("no-update", "a", "2", "--reason", "attempted dismissal", code=2)
        withdrawn = self.call("withdraw-source", "--reason", "user withdrew further use")
        self.assertEqual(len(withdrawn["known_references"]), 4)
        self.acquire(changed, code=2);self.inspect(revision="2", code=2)
        self.assertEqual(self.call("status")["source_status"], "withdrawn")
        self.assertNotIn("SYNTHETIC_PRIVATE_ACCOUNT", self.state.read_text())

    def test_human_and_operational_blockers_remain_visible_and_no_update_needs_a_reason(self):
        path = self.export("original.json", [self.item()]);self.acquire(path)
        self.inspect();self.action("defer", "a", "1", "--reason", "holder must decide")
        self.action("readback", "a", "1", "--owner", "unbound", code=2)
        self.assertEqual(self.status()["status"], "needs-decision")
        self.inspect(retry=True)
        self.action("fail", "a", "1", "--reason", "source temporarily unavailable")
        self.assertEqual(self.status()["status"], "failed")
        self.inspect(retry=True)
        self.action("no-update", "a", "1", "--reason", "unrequested transient content, no durable extraction")
        self.assertEqual(self.status()["outcome"], "no-update")
        self.assertFalse(self.one.exists())

    def test_state_lock_excludes_concurrent_operation_without_losing_progress(self):
        path = self.export("original.json", [self.item()]);self.acquire(path)
        before = self.state.read_bytes()
        with open(str(self.state) + ".lock", "a") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.call("inspect", "--item", "a", "--revision", "1", code=2)
        self.assertEqual(before, self.state.read_bytes())
        self.inspect()
        self.assertEqual(self.status()["status"], "inspected")

    def test_no_update_cannot_discard_a_capture_before_completion(self):
        path = self.export("original.json", [self.item()]);self.acquire(path, f"one={self.one}")
        item = self.inspect();self.targets(["one"])
        self.one.write_text("# Captured but not acknowledged\n" + item["marker"])
        self.action("no-update", "a", "1", "--reason", "attempt to skip readback", code=2)
        self.assertNotEqual(self.status()["status"], "completed")
        self.inspect(retry=True);self.readback()
        self.action("no-update", "a", "1", "--reason", "attempt to skip completion", code=2)
        self.assertNotEqual(self.status()["status"], "completed")
        self.assertIn(item["marker"], self.one.read_text())

    def test_rebinding_cannot_hide_capture_written_before_readback(self):
        path = self.export("original.json", [self.item()]);self.acquire(path, f"one={self.one}")
        item = self.inspect();self.targets(["one"])
        self.one.write_text("# In-flight capture\n" + item["marker"])
        replacement = self.root / "replacement.md";replacement.write_text("# Empty destination\n")
        self.call("bind", "--owner", f"one={replacement}", "--reason", "owner move", code=2)
        self.assertEqual(self.call("status")["owners"]["one"], str(self.one))
        self.action("no-update", "a", "1", "--reason", "attempted dismissal", code=2)
        self.assertNotEqual(self.status()["status"], "completed")

    def test_narrowed_targets_cannot_hide_capture_but_actual_reversal_can_finish(self):
        path = self.export("original.json", [self.item()]);self.acquire(path, f"one={self.one}", f"two={self.two}")
        item = self.inspect();self.targets(["one", "two"])
        original_owner = b"# Maintained owner A\nExisting terms stay.\n"
        self.one.write_bytes(original_owner + ("\nNew account.\n" + item["marker"]).encode())
        self.action("targets", "a", "1", "--owner", "two", "--reason", "narrow final targets")
        self.two.write_text("# Account B\n" + item["marker"])
        only_second = self.readback("two")
        self.complete([only_second], code=2)
        self.assertNotEqual(self.status()["status"], "completed")
        # Genuine reversal of the unacknowledged first write leaves no capture to skip.
        self.one.write_bytes(original_owner)
        self.inspect(retry=True)
        self.complete([self.readback("two")])
        self.assertEqual(self.status()["status"], "completed")
        self.assertEqual(self.one.read_bytes(), original_owner)

    def test_source_withdrawal_keeps_inflight_impacts_and_gates_before_source_access(self):
        path = self.export("original.json", [self.item()]);self.acquire(path, f"one={self.one}")
        item = self.inspect();self.targets(["one"])
        self.one.write_text("# Unconfirmed output\n" + item["marker"])
        self.readback()
        impacts = self.call("withdraw-source", "--reason", "withdraw all further use")["known_references"]
        self.assertEqual(impacts[0]["path"], str(self.one))
        self.assertIn("readback", impacts[0]["evidence"])
        self.assertIn("located-capture", impacts[0]["evidence"])
        self.assertEqual(self.call("status")["known_impacts"], impacts)
        # A nonexistent source would fail differently if import tried to read it first.
        error = self.acquire(self.root / "missing-source.json", code=2)
        self.assertIn("withdrawn", error["error"])
        self.assertNotIn("No such file", error["error"])

    def test_successor_blocks_old_input_replay_but_allows_readonly_history(self):
        path = self.export("original.json", [self.item()]);self.acquire(path, f"one={self.one}")
        changed = self.export("changed.json", [self.item(revision="2", operation="correction", replaces="1")])
        self.acquire(changed)
        self.inspect(code=2)
        historical = self.action("inspect", "a", "1", "--history")
        self.assertTrue(historical["read_only_history"])
        item = self.inspect(revision="2");self.targets(["one"], revision="2")
        self.one.write_text("# Correction; unaffected clauses remain in their owner\n" + item["marker"])
        self.complete([self.readback(revision="2")], revision="2")
        self.acquire(path)
        self.inspect(code=2);self.complete(["invented"], code=2)
        self.assertEqual(self.status()["successors"], [{"revision": "2", "status": "completed", "operation": "correction"}])
        ambiguous = self.export("ambiguous.json", [self.item(revision="3")])
        self.acquire(ambiguous, code=1)
        self.assertEqual(self.status(revision="3")["status"], "conflict")

    def test_successor_reconciles_actual_effects_before_predecessor_completion(self):
        path = self.export("original.json", [self.item()]);self.acquire(path, f"one={self.one}", f"two={self.two}")
        old = self.inspect();self.targets(["one", "two"])
        for owner in (self.one, self.two):
            owner.write_text("# Retained unaffected clause\nOld attributed account.\n" + old["marker"])
        self.readback("one")  # second owner has a real capture but no readback/completion
        changed = self.export("changed.json", [self.item(revision="2", operation="correction", replaces="1")])
        self.acquire(changed)
        item = self.inspect(revision="2");self.targets(["one"], revision="2")
        self.one.write_text(self.one.read_text() + "\nPartial correction.\n" + item["marker"])
        self.complete([self.readback(revision="2")], revision="2", code=2)
        self.assertNotEqual(self.status(revision="2")["status"], "completed")
        self.inspect(revision="2", retry=True)
        self.action("targets", "a", "2", "--owner", "one", "--owner", "two", "--reason", "include unfinished prior capture")
        self.two.write_text(self.two.read_text() + "\nPartial correction.\n" + item["marker"])
        self.complete([self.readback(alias, revision="2") for alias in ("one", "two")], revision="2")
        self.assertIn("Retained unaffected clause", self.one.read_text())
        self.assertIn("Retained unaffected clause", self.two.read_text())

    def test_sibling_conflict_resolution_is_scoped_to_known_set_and_preserves_effects(self):
        self.seed_capture(("one", "two"))
        siblings = self.export("siblings.json", [
            self.item(revision=revision, operation="correction", replaces="1") for revision in ("2", "3")])
        self.acquire(siblings, code=1)
        self.inspect(revision="2", code=1)
        self.action("targets", "a", "2", "--owner", "one", code=2)
        self.action("resolve-fork", "a", "3", "--reason", "source owner selected revision 3")
        self.assertEqual(self.status(revision="2")["status"], "conflict")
        item = self.inspect(revision="3");self.targets(["one", "two"], revision="3")
        for owner in (self.one, self.two):
            owner.write_text(owner.read_text() + "\nSelected partial correction; original unaffected terms remain.\n" + item["marker"])
        self.complete([self.readback(alias, revision="3") for alias in ("one", "two")], revision="3")
        continuation = self.export("continuation.json", [self.item(revision="4", operation="correction", replaces="3")])
        self.acquire(continuation)
        self.assertEqual(self.inspect(revision="4")["status"], "inspected")
        later = self.export("new-sibling.json", [self.item(revision="5", operation="correction", replaces="1")])
        self.acquire(later, code=1)
        self.assertEqual(self.status(revision="3")["status"], "conflict")
        self.action("targets", "a", "4", "--owner", "one", code=2)
        self.action("resolve-fork", "a", "3", "--reason", "source owner considered the new sibling set")
        self.inspect(revision="4", retry=True)
        self.assertEqual(self.status(revision="3")["status"], "completed")

    def test_fork_resolution_cannot_clear_byte_conflict_or_withdrawal(self):
        original = self.export("original.json", [self.item()]);self.acquire(original)
        siblings = self.export("siblings.json", [
            self.item(revision=revision, operation="correction", replaces="1") for revision in ("2", "3")])
        self.acquire(siblings, code=1)
        changed = self.export("changed-same-revision.json", [self.item(revision="3", operation="correction", replaces="1", content="different bytes")])
        self.acquire(changed, code=1)
        self.action("resolve-fork", "a", "3", "--reason", "selection cannot fix conflicting version identity")
        self.inspect(revision="3", code=1)
        self.action("targets", "a", "3", "--owner", "one", code=2)
        self.call("withdraw-source", "--reason", "withdraw source")
        self.action("resolve-fork", "a", "2", "--reason", "cannot reopen withdrawn source", code=2)


if __name__ == "__main__":
    unittest.main()
