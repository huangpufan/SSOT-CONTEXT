#!/usr/bin/env python3
"""Exercise the reader's command boundary, without calling a model."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
READER = ROOT / "skills/ssot-preflight/assets/scripts/read-context.py"


class ContextTests(unittest.TestCase):
    def run_reader(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            readme = Path(tmp) / "README.md"
            readme.write_text(text, encoding="utf-8")
            result = subprocess.run([sys.executable, str(READER), str(readme)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(readme.read_text(encoding="utf-8"), text)
            self.assertEqual(list(Path(tmp).iterdir()), [readme])
            return result.stdout

    def test_v4_returns_entry_and_preservation_rules(self):
        text = "---\nssot_format: 4\nlanguage: en\n---\n# Project\nA local rule.\n"
        output = self.run_reader(text)
        self.assertIn(text, output)
        self.assertIn("## 1. What SSOT is for", output)
        self.assertIn("## 3. Current, planned, and unknown", output)
        self.assertIn("## 5. Invariants", output)
        self.assertIn("**confirmed.**", output)
        self.assertIn("**candidate.**", output)
        self.assertIn("**Recovering a rule from the code.**", output)
        self.assertIn("protection-departure.md", output)
        self.assertNotIn("### Human-decision evidence", output)
        self.assertNotIn("## 2. What to store", output)
        self.assertNotIn("## 4. Layout", output)
        self.assertNotIn("## 6. Writing", output)
        self.assertNotIn("Give it this criterion, word for word", output)

    def test_legacy_and_unmarked_entries_remain_available(self):
        for marker in ("ssot_format: 3", "ssot_format: 2", "ssot_format: 5", "language: en"):
            with self.subTest(marker=marker):
                text = f"---\n{marker}\n---\n# Old rules\nKeep this protection.\n"
                output = self.run_reader(text)
                self.assertIn(text, output)
                self.assertNotIn("## 1. What SSOT is for", output)

    def test_body_text_cannot_select_v4_rules(self):
        output = self.run_reader("# Notes\nssot_format: 4\n")
        self.assertNotIn("## 1. What SSOT is for", output)

    def test_quoted_and_commented_v4_markers(self):
        for value in ('"4"', "'4'", "4 # current format"):
            with self.subTest(value=value):
                output = self.run_reader(f"---\nssot_format: {value}\n---\n# Project\n")
                self.assertIn("## 5. Invariants", output)

    def test_ambiguous_or_malformed_marker_does_not_select_v4(self):
        for fields in ("ssot_format: 3\nssot_format: 4", "ssot_format: '4\"",
                       "ssot_format:\n4"):
            with self.subTest(fields=fields):
                output = self.run_reader(f"---\n{fields}\n---\n# Project\n")
                self.assertNotIn("## 1. What SSOT is for", output)

    def test_new_read_observes_dirty_entry_and_untracked_route(self):
        with tempfile.TemporaryDirectory() as tmp:
            readme = Path(tmp) / "README.md"
            readme.write_text("---\nssot_format: 4\n---\n# Project\n", encoding="utf-8")
            command = [sys.executable, str(READER), str(readme)]
            first = subprocess.run(command, capture_output=True, text=True, check=True).stdout
            owner = Path(tmp) / "new-owner.md"
            owner.write_text("Owner contents are read by task scope.\n", encoding="utf-8")
            readme.write_text(readme.read_text() + "[New route](new-owner.md)\n", encoding="utf-8")
            second = subprocess.run(command, capture_output=True, text=True, check=True).stdout
            self.assertNotIn("New route", first)
            self.assertIn("[New route](new-owner.md)", second)
            self.assertNotIn(owner.read_text(), second)

    def test_missing_entry_is_a_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            readme = Path(tmp) / "missing.md"
            result = subprocess.run([sys.executable, str(READER), str(readme)],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertFalse(readme.exists())

    def test_entry_only_refreshes_entry_without_repeating_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            readme = Path(tmp) / "README.md"
            readme.write_text("---\nssot_format: 4\n---\n# Fresh route\n", encoding="utf-8")
            result = subprocess.run([sys.executable, str(READER), str(readme), "--entry-only"],
                                    capture_output=True, text=True, check=True)
            self.assertIn(readme.read_text(), result.stdout)
            self.assertNotIn("## 1. What SSOT is for", result.stdout)


if __name__ == "__main__":
    unittest.main()
