#!/usr/bin/env python3
"""Calibrate observable outcomes with valid and independently damaged artifacts."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys

import cases
import oracle
import tiering_case as case


class TieringChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ssot-tiering-offline-")
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        cases.build(self.repo, case.CASE)
        self.before = oracle.snapshot(self.repo)
        self.writer = copy.deepcopy(self.before)
        self.writer["SSOT/README.md"] = self.before["SSOT/README.md"].split("## Completed upkeep copied")[0]
        self.writer["policy/current.md"] = case.CORRECTION
        self.writer["templates/notice.md"] = case.CORRECTION
        self.writer["decisions/accepted.md"] += "\nD01 closing time and signal superseded by D02; staff access remains.\nD02: " + case.CORRECTION
        self.notice = {"friday_close": "20:00", "tuesday_close": "19:00", "staff_entry": "17:00",
                       "closing_signal": "light", "may_publish_visitor_names": False,
                       "may_lend_originals": False, "annex_current": False,
                       "reason": "Keep the neighbouring reading room quiet."}

    def result(self, writer=None, notice=None):
        writer = self.writer if writer is None else writer
        after = {**writer, "deliverables/notice.json": json.dumps(self.notice if notice is None else notice)}
        return case.grade(self.before, writer, after)

    def test_valid_fields_still_require_semantic_review_of_warm_owners(self):
        result = self.result()
        self.assertTrue(result["mechanical_passed"])
        self.assertTrue(result["semantic_review"])
        # Presence of all expected fields is not a semantic oracle for Markdown.
        self.writer["policy/current.md"] = "Contradictory prose requires human semantic review."
        self.assertTrue(self.result()["semantic_review"])

    def test_revival_exception_loss_and_low_frequency_rule_loss_fail(self):
        for key, bad in (("closing_signal", "bell"), ("tuesday_close", "20:00"),
                         ("staff_entry", "20:00"), ("may_lend_originals", True),
                         ("may_publish_visitor_names", True), ("annex_current", True)):
            with self.subTest(key=key):
                self.assertFalse(self.result(notice={**self.notice, key: bad})["mechanical_passed"])

    def test_deleting_originals_or_rewriting_locked_asset_fails(self):
        for path in ("sources/decision.txt", "archive/upkeep.md", "frozen/annex.md", "policy/constraints.md"):
            with self.subTest(path=path):
                writer = {**self.writer, path: "rewritten"}
                self.assertFalse(self.result(writer=writer)["mechanical_passed"])

    def test_history_original_words_and_entry_reduction_are_observed(self):
        writer = {**self.writer, "decisions/accepted.md": "The old choice was superseded."}
        self.assertFalse(self.result(writer=writer)["mechanical_passed"])
        self.assertFalse(self.result(writer=self.before)["mechanical_passed"])
        # Shorter does not mean deletion: original upkeep remains byte-identical.
        self.assertEqual(self.writer["archive/upkeep.md"], self.before["archive/upkeep.md"])

    def test_fresh_consumer_cannot_silently_change_context(self):
        after = {**self.writer, "deliverables/notice.json": json.dumps(self.notice), "policy/current.md": "edited by consumer"}
        self.assertFalse(case.grade(self.before, self.writer, after)["mechanical_passed"])

    def test_reporting_survives_the_cli_run_module_name_collision(self):
        context = Path(__file__).resolve().parent
        code = "import sys, types; sys.path.insert(0, sys.argv[1]); import oracle; sys.modules['run'] = types.ModuleType('run'); result = oracle.native_observation({}, 'gpt-6.1-terra'); assert result['costs'] is None; assert result['identity_state']"
        subprocess.run([sys.executable, "-B", "-c", code, str(context)], check=True)

    def test_cold_recall_distinguishes_exception_from_reactivating_old_rule(self):
        result = {"staff_pager_allowed": True, "public_bell_allowed": False, "source_id": "museum-D17-private-haptic", "reason": "Private vibration does not disturb readers."}
        before = {"policy/current.md": "retained"}
        after = {**before, "deliverables/recall.json": json.dumps(result)}
        self.assertTrue(case.grade_recall(before, after)["mechanical_passed"])
        for key, value in (("public_bell_allowed", True), ("staff_pager_allowed", False), ("source_id", "guessed")):
            after["deliverables/recall.json"] = json.dumps({**result, key: value})
            self.assertFalse(case.grade_recall(before, after)["mechanical_passed"])

    def test_case_registration_and_unchanged_fixture_fail(self):
        self.assertIn(case.CASE, cases.CASES)
        self.assertEqual(len(cases.tasks(case.CASE)), 2)
        cases.before_turn(self.repo, case.CASE, 2)
        self.assertEqual(oracle.snapshot(self.repo), self.before)
        self.assertFalse(oracle.grade(self.repo, case.CASE, self.before, None)["mechanical_passed"])


if __name__ == "__main__":
    unittest.main()
