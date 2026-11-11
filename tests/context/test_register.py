#!/usr/bin/env python3
"""Offline calibration of the large-register fixture and executable oracle."""
from pathlib import Path
import tempfile
import unittest

import oracle
import register_case as case


class RegisterCaseTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name) / "repo"
        case.build(self.repo)
        self.before = oracle.snapshot(self.repo)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, path, content):
        (self.repo / path).write_text(content)

    def valid_conflict_result(self):
        self.write("payment.py", 'def retry(payment_id):\n    receipt = {"payment_id": payment_id}\n    return receipt\n')
        self.write("note.txt", "maintenance\n")

    def test_register_has_real_owners_and_late_protection(self):
        entry = (self.repo / "SSOT/README.md").read_text()
        self.assertEqual(entry.count("| product promise |"), 80)
        self.assertIn("REG-80 | product promise | " + case.PROTECTION, entry)
        for group, rules in case.GROUPS.items():
            owner = (self.repo / f"docs/{group}.md").read_text()
            for rule in rules:
                self.assertIn(rule, entry)
                self.assertIn(rule, owner)
        self.assertIn(case.PROTECTION, (self.repo / "docs/payments.md").read_text())

    def test_conflict_oracle_accepts_allowed_changes_and_rejects_conflict(self):
        self.assertFalse(case.grade(self.repo, self.before, "conflict")["mechanical_passed"])
        self.valid_conflict_result()
        self.assertTrue(case.grade(self.repo, self.before, "conflict")["mechanical_passed"])
        self.write("payment.py", 'def retry(payment_id):\n    receipt = {"payment_id": "new"}\n    return receipt\n')
        self.assertFalse(case.grade(self.repo, self.before, "conflict")["checks"]["identity_preserved"])
        self.valid_conflict_result()
        self.write("test_payment.py", "# removed guard\n")
        self.assertFalse(case.grade(self.repo, self.before, "conflict")["checks"]["only_allowed_files_changed"])

    def test_typo_oracle_requires_exact_task_and_rejects_maintenance(self):
        self.assertFalse(case.grade(self.repo, self.before, "typo")["mechanical_passed"])
        self.write("note.txt", "maintenance\n")
        self.assertTrue(case.grade(self.repo, self.before, "typo")["mechanical_passed"])
        self.write("SSOT/README.md", self.before["SSOT/README.md"] + "\nUnrequested upkeep.\n")
        self.assertFalse(case.grade(self.repo, self.before, "typo")["checks"]["only_typo_changed"])


if __name__ == "__main__":
    unittest.main()
