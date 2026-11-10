#!/usr/bin/env python3
"""Fixture and migration-oracle checks; never invokes a model."""
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

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
        block = template[template.index("<!-- SSOT-SKILL:BEGIN -->"):template.index("<!-- SSOT-SKILL:END -->")]
        (self.repo / "AGENTS.md").write_text("# Project instructions\n\nNever publish payment credentials.\n\n"
                                              + block + "<!-- SSOT-SKILL:END -->\n")
        (self.repo / "check-memory.sh").write_text("#!/bin/sh\npython3 .agents/skills/ssot-doctor/assets/scripts/ssot-check.py SSOT\n")
        (self.repo / "SSOT/BOOTSTRAP.md").unlink()

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


if __name__ == "__main__":
    unittest.main()
