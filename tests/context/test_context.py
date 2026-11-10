#!/usr/bin/env python3
"""Offline oracle/fixture checks. Never invokes a model."""
import json
from pathlib import Path
import tempfile
import unittest

import cases
import oracle
import run


class ContextChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ssot-context-offline-", dir="/tmp")
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def solution(self, repo):
        (repo / "SSOT").mkdir()
        links = "\n".join(f"[{name}](../{name})" for name in cases.MATERIAL)
        (repo / "SSOT/README.md").write_text("# 生活空间\n\n" + links + "\n")

    def test_non_git_fixture_requires_real_entry_and_preserved_owners(self):
        repo = self.root / "repo"
        cases.build(repo, "C01")
        before = oracle.snapshot(repo)
        self.assertFalse(oracle.grade(repo, "C01", before, None)["mechanical_passed"])
        self.solution(repo)
        verdict = oracle.grade(repo, "C01", before, None)
        self.assertTrue(verdict["mechanical_passed"])
        self.assertTrue(verdict["semantic_review"])
        (repo / "SPACE.md").write_text("Only projects matter now.\n")
        self.assertFalse(oracle.grade(repo, "C01", before, None)["mechanical_passed"])

    def test_forced_git_and_development_scaffold_are_rejected(self):
        repo = self.root / "repo"
        cases.build(repo, "C01")
        before = oracle.snapshot(repo)
        self.solution(repo)
        (repo / ".git").mkdir()
        (repo / "package.json").write_text("{}")
        checks = oracle.grade(repo, "C01", before, None)["checks"]
        self.assertFalse(checks["no_git_created"])
        self.assertFalse(checks["no_software_scaffold"])

    def test_partial_fixture_is_valid_and_unchanged_is_not_success(self):
        repo = self.root / "repo"
        watermark = cases.build(repo, "D03")
        before = oracle.snapshot(repo)
        skills = repo / ".agents/skills"
        skills.parent.mkdir()
        skills.symlink_to(Path(__file__).resolve().parents[2] / "skills", target_is_directory=True)
        verdict = oracle.grade(repo, "D03", before, watermark)
        self.assertTrue(verdict["checks"]["checker_passes"])
        self.assertFalse(verdict["mechanical_passed"])
        self.assertEqual(len(cases.tasks("D03")), 2)

    def test_native_usage_requires_actual_expected_model_and_per_turn_record(self):
        summary = {"seconds": 2, "native_models": ["gpt-6.1-sol"],
                   "usage": {"input_tokens": 999999}}
        self.assertIsNone(oracle.native_costs(summary, "gpt-6.1-sol"))
        summary["native_turn_usage"] = {"input_tokens": 100, "cached_input_tokens": 40, "output_tokens": 8}
        self.assertEqual(oracle.native_costs(summary, "gpt-6.1-sol")["total_input_output_tokens"], 108)
        summary["native_models"] = ["gpt-6.1-terra"]
        self.assertIsNone(oracle.native_costs(summary, "gpt-6.1-sol"))

    def test_manifest_detects_fixture_and_oracle_changes(self):
        folder = self.root / "frozen"
        folder.mkdir()
        (folder / "oracle.py").write_text("original")
        frozen = run.manifest(folder)
        (folder / "oracle.py").write_text("changed")
        self.assertNotEqual(frozen, run.manifest(folder))

    def test_all_additional_fixtures_build_without_model_calls(self):
        for case in cases.scenarios.CASES:
            repo = self.root / case
            cases.build(repo, case)
            self.assertTrue(oracle.snapshot(repo), case)
            self.assertTrue(cases.tasks(case), case)
        self.assertFalse((self.root / "C02/.git").exists())
        self.assertFalse((self.root / "C03/SSOT").exists())

    def test_candidate_protection_detects_departure_and_allows_local_rename(self):
        repo = self.root / "repo"
        cases.build(repo, "D02")
        before = oracle.snapshot(repo)
        p = repo / "payment.py"
        p.write_text(p.read_text().replace("result", "receipt"))
        (repo / "note.txt").write_text("maintenance\n")
        good = oracle.grade(repo, "D02", before, None)
        self.assertTrue(good["mechanical_passed"])
        p.write_text('def retry(payment_id):\n    receipt = {"payment_id": "new"}\n    return receipt\n')
        self.assertFalse(oracle.grade(repo, "D02", before, None)["checks"]["payment_identity_preserved"])

    def test_raw_source_and_canon_changes_cannot_pass(self):
        for case, name, check in (("C03", "sources/A.txt", "original_sources_preserved"),
                                  ("C04", "creation/canon.md", "canon_draft_narrator_unchanged")):
            repo = self.root / case
            cases.build(repo, case)
            before = oracle.snapshot(repo)
            (repo / name).write_text("Changed to suit the summary.\n")
            self.assertFalse(oracle.grade(repo, case, before, None)["checks"][check])

    def test_authorized_personal_entry_is_not_rejected_for_its_path(self):
        repo = self.root / "repo"
        cases.build(repo, "C05")
        before = oracle.snapshot(repo)
        (repo / "personal/preferences.md").write_text("# 偏好\n\n本月喜欢早晨写作。\n")
        (repo / "personal/README.md").write_text("# 个人空间入口\n\n[写作偏好](preferences.md)\n")
        path = repo / "company/README.md"
        path.write_text(path.read_text().replace("maintenence", "maintenance"))
        self.assertTrue(oracle.grade(repo, "C05", before, None)["mechanical_passed"])
        (repo / "company/policy.md").write_text("All data is public now.\n")
        self.assertFalse(oracle.grade(repo, "C05", before, None)["mechanical_passed"])

    def test_context_read_classifier_distinguishes_enumeration_and_exclusions(self):
        safe = ["/bin/bash -lc 'rg --files -g AGENTS.md -g note.txt -g \"!SSOT/**\"'",
                "rg --files SSOT", "find SSOT -type f", "cat note.txt", "rg SSOT note.txt",
                "rg -n spelling . -g '!SSOT/**'", "cat > SSOT/README.md <<EOF"]
        actual = ["cat SSOT/README.md", "sed -n '1,120p' SSOT/README.md",
                  "rg -n 'accepted' SSOT", "cat .agents/skills/ssot-preflight/SKILL.md",
                  "rg -n spelling .", "/bin/bash -lc 'cat note.txt; cat SSOT/README.md'"]
        for command in safe:
            self.assertFalse(oracle.reads_memory_content(command), command)
        for command in actual:
            self.assertTrue(oracle.reads_memory_content(command), command)

    def test_source_names_and_capture_date_do_not_prove_correction_processed(self):
        repo = self.root / "repo"
        cases.build(repo, "C03")
        before = oracle.snapshot(repo)
        path = repo / "research/review.md"
        path.write_text(path.read_text() + "\nsource-A and source-B reviewed on 2026-11-10.\n")
        checks = oracle.grade(repo, "C03", before, None)["checks"]
        self.assertFalse(checks["sources_and_correction_traceable"])
        self.assertFalse(checks["new_correction_original_preserved"])


if __name__ == "__main__":
    unittest.main()
