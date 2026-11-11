#!/usr/bin/env python3
"""Fixture and migration-oracle checks; never invokes a model."""
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("migration", HERE / "run-migration-trials.py")
migration = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(migration)


class MigrationTrialsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.watermark = migration.fixture(self.repo, "resume")
        (self.repo / ".agents").mkdir()
        (self.repo / ".agents/skills").symlink_to(HERE.parent / "skills", target_is_directory=True)
        self.before = migration.bench.transport.snapshot(self.repo)

    def tearDown(self):
        self.tmp.cleanup()

    def grade(self, case="resume"):
        return migration.grade(self.repo, case, self.before, self.watermark)

    def complete(self):
        index = self.repo / "SSOT/README.md"
        index.write_text(index.read_text().replace("ssot_format: 3", "ssot_format: 4"))
        template = (HERE.parent / "skills/ssot-bootstrap/assets/templates/en/adapter-thin.md").read_text()
        block = template[template.index("<!-- SSOT-CONTEXT:BEGIN -->"):template.index("<!-- SSOT-CONTEXT:END -->")]
        (self.repo / "AGENTS.md").write_text("# Project instructions\n\nNever publish payment credentials.\n\n"
                                              + block + "<!-- SSOT-CONTEXT:END -->\n")
        (self.repo / "check-memory.sh").write_text("#!/bin/sh\npython3 .agents/skills/ssot-doctor/assets/scripts/ssot-check.py SSOT\n")
        (self.repo / "SSOT/BOOTSTRAP.md").unlink()

    def test_current_block_does_not_allow_leftover_legacy_marker_block(self):
        self.complete()
        instructions = self.repo / "AGENTS.md"
        instructions.write_text(instructions.read_text() + "\n<!-- SSOT-SKILL:BEGIN -->\nOld workflow\n<!-- SSOT-SKILL:END -->\n")
        self.assertFalse(self.grade()["one_current_instruction_block"])

    def test_fixture_is_valid_legacy_memory_not_malformed_markdown(self):
        checker = self.repo / ".agents/skills/ssot-doctor/assets/scripts/ssot-check.py"
        result = subprocess.run(["python3", "-B", str(checker), str(self.repo / "SSOT")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 3, result.stdout)
        self.assertIn("v3 layout", result.stdout)
        self.assertNotIn("ERROR", result.stdout)
        self.assertEqual(len([line for line in self.before["SSOT/README.md"].splitlines() if line.startswith("| INV-")]), 2)

    def test_unmodified_fixture_fails_migration_but_passes_readonly(self):
        self.assertFalse(all(self.grade().values()))
        self.assertTrue(all(self.grade("readonly").values()))

    def test_complete_migration_passes_and_violates_readonly(self):
        self.complete()
        self.assertTrue(all(self.grade().values()), self.grade())
        self.assertFalse(all(self.grade("readonly").values()))

    def test_lost_scope_or_authority_is_rejected(self):
        self.complete()
        original = (self.repo / "SSOT/README.md").read_text()
        for text in (original.replace("| confirmed |", "| candidate |"),
                     original.replace("| candidate |", "| confirmed |"),
                     original.replace("original payment identity", "new payment identity")):
            (self.repo / "SSOT/README.md").write_text(text)
            self.assertFalse(self.grade()["rules_sources_statuses_preserved"])

    def test_stale_integration_checkpoint_or_watermark_is_rejected(self):
        self.complete()
        (self.repo / "AGENTS.md").write_text((self.repo / "AGENTS.md").read_text() + "\nRead SSOT/STATUS.md first.\n")
        self.assertFalse(self.grade()["legacy_instructions_removed"])
        (self.repo / "SSOT/BOOTSTRAP.md").write_text("# Still unfinished\n")
        self.assertFalse(self.grade()["checkpoint_removed_last_state"])
        index = self.repo / "SSOT/README.md"
        index.write_text(index.read_text().replace(self.watermark, "HEAD"))
        self.assertFalse(self.grade()["review_watermark_preserved"])

    def test_deleted_entry_and_unrelated_write_are_not_hidden(self):
        self.complete()
        (self.repo / "SSOT/README.md").unlink()
        (self.repo / "unrelated.txt").write_text("unexpected")
        checks = self.grade()
        self.assertFalse(checks["format4"])
        self.assertFalse(checks["rules_sources_statuses_preserved"])
        self.assertFalse(checks["write_scope"])

    def test_ci_refuses_billable_runs_before_preparation(self):
        output = Path(self.tmp.name) / "forbidden-run"
        result = subprocess.run(["python3", str(HERE / "run-migration-trials.py"),
                                 "--bundle", str(HERE.parent), "--output", str(output), "--run-models"],
                                env={**os.environ, "CI": "1"}, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("Model calls are forbidden in CI", result.stderr)
        self.assertFalse(output.exists())


class ContinuityTrialsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"

    def tearDown(self):
        self.tmp.cleanup()

    def build(self, case):
        self.watermark = migration.fixture(self.repo, case)
        (self.repo / ".agents").mkdir()
        (self.repo / ".agents/skills").symlink_to(HERE.parent / "skills", target_is_directory=True)
        self.before = migration.bench.transport.snapshot(self.repo)

    def complete_v2(self):
        c = migration.continuity_cases
        register = c.rows(self.before["SSOT/README.md"])
        table = []
        for key, row in register.items():
            status = "candidate" if key == "CLAUDE-MAXIM-1" else "confirmed" if key == "CORE-RULE-1" else row[5]
            table.append("| " + " | ".join((key, "process rule", row[2], row[3], status, row[4])) + " |")
        table.append('| INV-03 | product promise | Manual exports must work offline | [Offline](02-architecture/README.md#offline) | confirmed | user, 2026-10-03, human-offline |')
        c.write(self.repo, "SSOT/README.md", f'''---
            ssot_format: 4
            language: en
            reviewed_through: {self.watermark}
            ---
            # Parcel Desk

            ## Map

            [Architecture](02-architecture/README.md), [Guide](../docs/guide.md), [Pilot](04-records/decisions/0002-local-queue.md).

            ## Invariants

            | ID | Kind | Rule | Explained in | Status | Source |
            | --- | --- | --- | --- | --- | --- |
        ''')
        path = self.repo / "SSOT/README.md"
        path.write_text(path.read_text() + "\n".join(table) + "\n\n## Open questions\n\nADJ-7: Should manual export retain expired quotes? GAP-12: macOS offline export is unverified.\n")
        owner = self.repo / "SSOT/02-architecture/README.md"
        owner.write_text(owner.read_text().split("---", 2)[2].lstrip() + "\n## Offline\n\n"
                         + "\n\n".join(c.FACTS.values()) + "\n\nThe user rejected publishing debug payloads.\n")
        for name, status in (("0001-remote-queue.md", "superseded by 0002-local-queue.md; never built"),
                             ("0002-local-queue.md", "accepted; planned, not implemented")):
            path = self.repo / "SSOT/04-records/decisions" / name
            path.write_text("Status: " + status + "\n\n" + path.read_text().split("---", 2)[2].lstrip())
        for name in ("SSOT/STATUS.md", "SSOT/HISTORY.md", "SSOT/02-architecture/_manifest.md", "SSOT/.bootstrap/review.md"):
            (self.repo / name).unlink()
        (self.repo / "SSOT/.bootstrap").rmdir()
        c.write(self.repo, "docs/guide.md", "# Guide\n\n[Questions](../SSOT/README.md#open-questions) affect export work.")
        adapter = (HERE.parent / "skills/ssot-bootstrap/assets/templates/en/adapter-thin.md").read_text()
        block = adapter[adapter.index("<!-- SSOT-CONTEXT:BEGIN -->"):adapter.index("<!-- SSOT-CONTEXT:END -->")]
        c.write(self.repo, "AGENTS.md", "# Project instructions\n\nNever publish payment credentials.\n\n" + block + "<!-- SSOT-CONTEXT:END -->")
        c.write(self.repo, "check-memory.sh", "#!/bin/sh\npython3 .agents/skills/ssot-doctor/assets/scripts/ssot-check.py SSOT")

    def test_v2_fixture_is_readable_legacy_and_mixed_writer_guard_checks_changes(self):
        self.build("v2")
        checker = self.repo / ".agents/skills/ssot-doctor/assets/scripts/ssot-check.py"
        result = subprocess.run(["python3", "-B", str(checker), str(self.repo / "SSOT")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 3, result.stdout)
        self.assertNotIn("ERROR", result.stdout)
        self.assertFalse(all(migration.grade(self.repo, "v2", self.before, self.watermark).values()))
        self.assertTrue(all(migration.grade(self.repo, "mixed-writers", self.before, self.watermark).values()))
        (self.repo / "SSOT/BOOTSTRAP.md").write_text("premature migration")
        self.assertFalse(all(migration.grade(self.repo, "mixed-writers", self.before, self.watermark).values()))

    def test_v2_complete_conversion_passes(self):
        self.build("v2")
        self.complete_v2()
        verdict = migration.grade(self.repo, "v2", self.before, self.watermark)
        self.assertTrue(all(verdict.values()), verdict)

    def test_v2_promotion_and_ledger_knowledge_loss_are_rejected(self):
        self.build("v2")
        self.complete_v2()
        path = self.repo / "SSOT/README.md"
        path.write_text(path.read_text().replace("| candidate |", "| confirmed |"))
        self.assertFalse(migration.grade(self.repo, "v2", self.before, self.watermark)["existing_rule_authority_preserved"])
        owner = self.repo / "SSOT/02-architecture/README.md"
        owner.write_text(owner.read_text().replace("audit-tail", "tail"))
        self.assertFalse(migration.grade(self.repo, "v2", self.before, self.watermark)["unique_ledger_knowledge_preserved"])

    def test_accepted_capture_ids_are_not_limited_to_inv(self):
        self.build("v2")
        self.complete_v2()
        path = self.repo / "SSOT/README.md"
        path.write_text(path.read_text().replace("| INV-03 |", "| CAP-OFFLINE-1 |"))
        verdict = migration.grade(self.repo, "v2", self.before, self.watermark)
        self.assertTrue(all(verdict.values()), verdict)

    def test_partial_correction_preserves_other_rules_and_provenance(self):
        self.build("partial")
        c = migration.continuity_cases
        owner = self.repo / "docs/decisions.md"
        owner.write_text(owner.read_text() + f'\nHistorical source human-11: "{c.ACCEPT}"\n\nCurrent partial replacement, human-12: "{c.CORRECTION}"\n')
        path = self.repo / "SSOT/README.md"
        path.write_text(path.read_text().replace("Maintenance reports are plain text", "Interactive maintenance reports may use Markdown; unattended reports remain plain text")
                        .replace("| user, 2026-11-01, human-10 |\n\n## Open", '| user, 2026-11-10, human-12 "' + c.CORRECTION + '" |\n\n## Open'))
        c.write(self.repo, "implementation-plan.md", "Use Markdown for interactive reports; keep unattended reports plain text. Preserve read-only checks and state checked scope.")
        verdict = migration.grade(self.repo, "partial", self.before, self.watermark)
        self.assertTrue(all(verdict.values()), verdict)
        # A historical row may retire while a successor carries the scoped rule.
        text = path.read_text()
        current = next(line for line in text.splitlines() if line.startswith("| INV-03"))
        successor = current.replace("| INV-03 |", "| REPORT-MODE-1 |")
        retired = current.replace("| confirmed |", "| retired |")
        path.write_text(text.replace(current, retired + "\n" + successor))
        self.assertTrue(all(migration.grade(self.repo, "partial", self.before, self.watermark).values()))
        self.assertFalse(all(migration.grade(self.repo, "capture-readonly", self.before, self.watermark).values()))
        path.write_text(path.read_text().replace("Read-only checks never write", "Read-only checks may write"))
        self.assertFalse(migration.grade(self.repo, "partial", self.before, self.watermark)["unaffected_rules_identical"])

    def test_capture_order_requires_returned_saved_owner_before_plan(self):
        root = Path(self.tmp.name)
        save = lambda name, value: (root / name).write_text(json.dumps(value))
        save("1.before.json", {})
        save("1.checkpoints.json", [{"event": 1, "files": {"docs/decisions.md": "decision"}},
                                     {"event": 3, "files": {"implementation-plan.md": "plan"}}])
        events = [{}, {"type": "item.completed", "item": {"type": "command_execution", "exit_code": 0,
                   "command": "cat docs/decisions.md", "aggregated_output": "decision"}}, {}]
        (root / "1.jsonl").write_text("\n".join(json.dumps(event) for event in events))
        self.assertTrue(migration.continuity_cases.capture_order(root, 1, "decision"))
        save("1.checkpoints.json", [{"event": 1, "files": {"docs/decisions.md": "decision", "implementation-plan.md": "plan"}}])
        self.assertFalse(migration.continuity_cases.capture_order(root, 1, "decision"))

    def test_interruption_guard_requires_checkpoint_and_a_real_document_change(self):
        c = migration.continuity_cases
        before = {"SSOT/README.md": "original"}
        self.assertFalse(c.migration_in_flight(before, before))
        self.assertFalse(c.migration_in_flight(before, {**before, "SSOT/BOOTSTRAP.md": "started"}))
        self.assertFalse(c.migration_in_flight(before, {"SSOT/README.md": "changed"}))
        self.assertTrue(c.migration_in_flight(before, {"SSOT/README.md": "changed", "SSOT/BOOTSTRAP.md": "started"}))

    def test_recorder_retains_interrupted_turn_and_only_signals_its_child(self):
        self.build("v2")
        run_dir = Path(self.tmp.name) / "run"
        run_dir.mkdir()
        signalled = []
        commands = []

        class NativeProcess:
            def __init__(process, *args, **kwargs):
                commands.append(args[0])
                process.stdin = io.BytesIO()
                process.stdout = io.BytesIO(b'{"type":"item.completed","item":{}}\n')
                (self.repo / "SSOT/BOOTSTRAP.md").write_text("started")
                (self.repo / "SSOT/README.md").write_text("changed")

            def poll(process):
                return None

            def terminate(process):
                signalled.append(process)

            def wait(process):
                return 143

        with patch.object(migration.bench.transport.subprocess, "Popen", NativeProcess):
            result = migration.bench.transport.execute_turn(Path(self.tmp.name), run_dir, self.repo,
                     "task", 1, 10, sandbox_command=["isolated"],
                     interrupt_when=lambda current, event: migration.continuity_cases.migration_in_flight(self.before, current),
                     model="gpt-6.1-sol", allow_no_git=True, installed_mode=True)
        self.assertEqual(commands[0][commands[0].index("-m") + 1], "gpt-6.1-sol")
        self.assertIn("--skip-git-repo-check", commands[0])
        self.assertNotIn("project_doc_max_bytes=0", commands[0])
        self.assertTrue(result["installed_mode"])
        self.assertEqual(result["requested_model"], "gpt-6.1-sol")
        self.assertEqual(len(signalled), 1)
        self.assertEqual(result["returncode"], 143)
        self.assertFalse(result["completed"])
        self.assertEqual(result["intentional_interruption"]["signal"], "SIGTERM")
        after = json.loads((run_dir / "1.after.json").read_text())
        self.assertIn("SSOT/BOOTSTRAP.md", after)
        self.assertTrue((run_dir / "1.summary.json").exists())


if __name__ == "__main__":
    unittest.main()
