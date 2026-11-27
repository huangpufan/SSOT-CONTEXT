#!/usr/bin/env python3
"""Comprehensive regression tests for tools/ssot-backlinks.py."""
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "ssot-backlinks.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("ssot_backlinks", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestSSOTBacklinks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        (self.root / "SSOT").mkdir()
        (self.root / "docs" / "guides").mkdir(parents=True)
        (self.root / "src" / "payments").mkdir(parents=True)
        (self.root / "src" / "other").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args, cwd=None):
        return subprocess.run(
            [sys.executable, "-B", str(TOOL), *args],
            cwd=cwd or self.root,
            capture_output=True,
            text=True,
        )

    def test_relative_links_fragments_refdefs_and_same_basenames(self):
        (self.root / "SSOT" / "README.md").write_text(
            "---\nssot_format: 4\nlanguage: en\n---\n\n"
            "# Entry\n\n"
            "## Routes\n\n"
            "- Payments logic -> [retry](../src/payments/index.py#L10)\n"
            "- Other index -> [other](../src/other/index.py)\n"
            "- Ref link: [ref][payref]\n\n"
            "[payref]: ../src/payments/index.py\n"
            "[^fn1]: ../src/payments/index.py\n",
            encoding="utf-8",
        )
        (self.root / "docs" / "guides" / "flow.md").write_text(
            "Flow Overview\n"
            "Part Two\n"
            "=============\n\n"
            "See [payments](../../src/payments/index.py?raw=1#retries).\n",
            encoding="utf-8",
        )
        res = self.run_cli(
            "--json",
            "--source", "SSOT/README.md",
            "--source", "SSOT/README.md",  # duplicate source deduplicated
            "--source", "docs/guides/flow.md",
            "--", "src/payments/index.py", "src/payments/index.py",
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        data = json.loads(res.stdout)
        self.assertFalse(data["incomplete_coverage"])
        self.assertIn("working-tree", data["scope"])
        hits = data["results"]["src/payments/index.py"]
        self.assertEqual(len(hits), 3)
        self.assertEqual(
            [(h["source"], h["line"], h["heading"], h["kind"], h["fragment"]) for h in hits],
            [
                ("SSOT/README.md", 10, "Routes", "inline_link", "L10"),
                ("SSOT/README.md", 14, "Routes", "reference_definition", ""),
                ("docs/guides/flow.md", 5, "Flow Overview Part Two", "inline_link", "retries"),
            ],
        )

    def test_markdown_edge_cases_comments_fences_code_titles_images_and_headings(self):
        (self.root / "SSOT" / "edge.md").write_text(
            "\ufeff# C#\r\n\r\n"
            "<!-- multiline comment with fence inside\r\n"
            "```\r\n"
            "still inside comment -->\r\n"
            "Real after comment: [after-comment](../src/payments/a.py)\r\n\r\n"
            "Comment split must not merge: [fake]<!-- split -->(../src/payments/a.py)\r\n\r\n"
            "Escaped bracket: \\[escaped](../src/payments/a.py)\r\n\r\n"
            "Title with link text: [title-link](../src/other/x.py \"see [t](../src/payments/a.py) \\\"q\\\"\")\r\n\r\n"
            "Linked image: [![alt](../src/other/img.png)](../src/payments/a.py)\r\n\r\n"
            "    [indented-code](../src/payments/a.py)\r\n\r\n"
            "> ```\r\n"
            "> [blockquoted-fence](../src/payments/a.py)\r\n"
            "> ```\r\n\r\n"
            "Multiline code span ``start\r\n"
            "[in-multiline-code](../src/payments/a.py)\r\n"
            "end`` then [two](../src/payments/a.py) and [two2](../src/payments/a.py)\r\n\r\n"
            "Paragraph before fence\r\n"
            "```\r\n"
            "code\r\n"
            "```\r\n"
            "---\r\n"
            "After rule: [still-csharp](../src/payments/a.py)\r\n",
            encoding="utf-8",
        )
        res = self.run_cli("--json", "--source", "SSOT/edge.md", "--", "src/payments/a.py")
        self.assertEqual(res.returncode, 0, res.stderr)
        hits = json.loads(res.stdout)["results"]["src/payments/a.py"]
        # Expect: line 6 (after-comment), line 14 (linked image outer), line 24 (two + two2), line 31 (still-csharp)
        self.assertEqual([h["line"] for h in hits], [6, 14, 24, 24, 31])
        self.assertTrue(all(h["heading"] == "C#" for h in hits))

    def test_git_working_tree_beats_committed_and_staged_versions(self):
        env = {**os.environ, "GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@e",
               "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@e"}
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=self.root, check=True, env=env)
        doc = self.root / "SSOT" / "README.md"
        doc.write_text("# V1\n\n[old](../src/payments/old.py)\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.root, check=True, env=env)
        subprocess.run(["git", "commit", "-q", "-m", "v1"], cwd=self.root, check=True, env=env)
        doc.write_text("# V2\n\n[staged](../src/payments/staged.py)\n", encoding="utf-8")
        subprocess.run(["git", "add", "SSOT/README.md"], cwd=self.root, check=True, env=env)
        doc.write_text("# V3\n\n[dirty](../src/payments/dirty.py)\n", encoding="utf-8")

        res = self.run_cli(
            "--json", "--source", "SSOT/README.md", "--",
            "src/payments/old.py", "src/payments/staged.py", "src/payments/dirty.py",
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        results = json.loads(res.stdout)["results"]
        self.assertEqual(len(results["src/payments/old.py"]), 0)
        self.assertEqual(len(results["src/payments/staged.py"]), 0)
        self.assertEqual(len(results["src/payments/dirty.py"]), 1)
        self.assertEqual(results["src/payments/dirty.py"][0]["heading"], "V3")

    def test_zero_target_io_proved_and_directory_or_self_links(self):
        mod = load_tool()
        (self.root / "SSOT" / "README.md").write_text(
            "# Self\n\n"
            "Self anchor: [here](#self)\n"
            "Dir link: [docs](../docs/)\n"
            "Escaped frag: [ef](../src/payments/p.py#a\\#b)\n",
            encoding="utf-8",
        )
        # Prove find_backlinks never stats/opens target paths
        real_stat = os.stat
        touched = []

        def spy_stat(path, *a, **kw):
            touched.append(str(path))
            return real_stat(path, *a, **kw)

        with mock.patch("os.stat", side_effect=spy_stat):
            data, rc, _ = mod.find_backlinks(
                self.root, ["SSOT/README.md"],
                ["SSOT/README.md", "docs", "docs/README.md", "src/payments/p.py"],
            )
        self.assertEqual(rc, 0)
        self.assertEqual(len(data["results"]["SSOT/README.md"]), 1)
        self.assertEqual(len(data["results"]["docs"]), 1)
        self.assertEqual(len(data["results"]["docs/README.md"]), 0)
        self.assertEqual(len(data["results"]["src/payments/p.py"]), 1)
        self.assertFalse(any("payments/p.py" in p for p in touched))

        # Verify text output prints escaped fragment once (not doubled)
        res = self.run_cli("--source", "SSOT/README.md", "--", "src/payments/p.py")
        self.assertEqual(res.returncode, 0)
        self.assertIn("-> ../src/payments/p.py#a\\#b\n", res.stdout)

    def test_symlink_source_and_parent_symlink_rejected_with_exit_3(self):
        outside = tempfile.TemporaryDirectory()
        try:
            secret = Path(outside.name) / "secret.md"
            secret.write_text("# Secret\n\n[a](../src/payments/a.py)\n", encoding="utf-8")
            os.symlink(secret, self.root / "SSOT" / "leaf-sym.md")
            real_sub = self.root / "SSOT" / "realdir"
            real_sub.mkdir()
            (real_sub / "in.md").write_text("# In\n\n[a](../../src/payments/a.py)\n", encoding="utf-8")
            os.symlink(real_sub, self.root / "SSOT" / "symdir")
            (self.root / "SSOT" / "ok.md").write_text("# OK\n\n[a](../src/payments/a.py)\n", encoding="utf-8")

            res = self.run_cli(
                "--json",
                "--source", "SSOT/leaf-sym.md",
                "--source", "SSOT/symdir/in.md",
                "--source", "SSOT/ok.md",
                "--", "src/payments/a.py",
            )
            self.assertEqual(res.returncode, 3)
            data = json.loads(res.stdout)
            self.assertTrue(data["incomplete_coverage"])
            self.assertEqual(data["sources_scanned"], ["SSOT/ok.md"])
            self.assertEqual(len(data["failed_sources"]), 2)
            self.assertEqual(len(data["results"]["src/payments/a.py"]), 1)
        finally:
            outside.cleanup()

    def test_incomplete_coverage_never_prints_false_negative_and_decode_names_source(self):
        (self.root / "SSOT" / "badutf8.md").write_bytes(b"\xff\xfe invalid utf8")
        res = self.run_cli("--source", "SSOT/badutf8.md", "--source", "SSOT/missing.md", "--", "src/payments/a.py")
        self.assertEqual(res.returncode, 3)
        self.assertIn("SSOT/badutf8.md", res.stderr)
        self.assertIn("no match in successfully scanned sources (incomplete coverage", res.stdout)
        self.assertNotIn("no explicit link in the selected sources", res.stdout)

    def test_invalid_only_targets_exit_2_without_scanning_and_root_from_other_cwd(self):
        (self.root / "SSOT" / "ok.md").write_text("# OK\n\n[a](../src/payments/a.py)\n", encoding="utf-8")
        res = self.run_cli("--json", "--source", "SSOT/ok.md", "--", "../escape.py", ".")
        self.assertEqual(res.returncode, 2)
        data = json.loads(res.stdout)
        self.assertEqual(data["sources_scanned"], [])
        self.assertEqual(len(data["invalid_targets"]), 2)

        # Invoke from a separate cwd using a symlink alias for --root and absolute --source under that alias
        other_tmp = tempfile.TemporaryDirectory()
        try:
            alias = Path(other_tmp.name) / "repo-alias"
            os.symlink(self.root, alias)
            res2 = self.run_cli(
                "--root", str(alias),
                "--source", str(alias / "SSOT/ok.md"),
                "--", "src/payments/a.py",
                cwd=Path(other_tmp.name),
            )
            self.assertEqual(res2.returncode, 0, res2.stderr)
            self.assertIn("SSOT/ok.md:3 [OK]", res2.stdout)
        finally:
            other_tmp.cleanup()

    def test_control_chars_escaped_and_zero_match_complete_message(self):
        (self.root / "SSOT" / "ctrl.md").write_text("# Evil\x1b[31mRed\n\n[x](../src/payments/x.py)\n", encoding="utf-8")
        res = self.run_cli("--source", "SSOT/ctrl.md", "--", "src/payments/x.py", "src/payments/none.py")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertNotIn("\x1b", res.stdout)
        self.assertIn("\\x1b[31mRed", res.stdout)
        self.assertIn("no explicit link in the selected sources", res.stdout)
        self.assertNotIn("no constraints", res.stdout.lower())

    def test_fence_html_comment_multiline_refdef_unmatched_ticks_fifo_and_surrogates(self):
        # 1) HTML comment opener inside fenced code block must NOT hide links after fence
        # 2) Refdef-shaped line inside multiline code span closing later on same line must NOT match
        # 3) Unmatched single backtick must NOT swallow a later valid double-backtick span
        (self.root / "SSOT" / "hard.md").write_text(
            "# Hard Cases\n\n"
            "```\n"
            "<!-- literal comment opener inside fence\n"
            "```\n"
            "After fence: [ok-after-fence](../src/payments/a.py)\n\n"
            "Start multiline ``code\n"
            "[fake-ref]: ../src/payments/a.py `` and [real-after-close](../src/payments/a.py)\n\n"
            "Unmatched single ` then valid ``[in-code](../src/payments/a.py)`` then [after-unmatched](../src/payments/a.py)\n",
            encoding="utf-8",
        )
        res = self.run_cli("--json", "--source", "SSOT/hard.md", "--", "src/payments/a.py")
        self.assertEqual(res.returncode, 0, res.stderr)
        hits = json.loads(res.stdout)["results"]["src/payments/a.py"]
        self.assertEqual(
            [(h["line"], h["kind"]) for h in hits],
            [(6, "inline_link"), (9, "inline_link"), (11, "inline_link")],
        )

        # 4) Selected FIFO must fail fast with exit 3 (never block)
        fifo = self.root / "SSOT" / "pipe.md"
        os.mkfifo(fifo)
        res_fifo = subprocess.run(
            [sys.executable, "-B", str(TOOL), "--json", "--source", "SSOT/pipe.md", "--", "src/payments/a.py"],
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        self.assertEqual(res_fifo.returncode, 3)
        self.assertTrue(json.loads(res_fifo.stdout)["incomplete_coverage"])

        # 5) Non-UTF-8 POSIX target argv bytes must return exit 2 with valid UTF-8 JSON stdout
        res_bad_utf8 = subprocess.run(
            [sys.executable.encode(), b"-B", str(TOOL).encode(), b"--json",
             b"--source", b"SSOT/hard.md", b"--", b"src/payments/bad\xff.py"],
            cwd=self.root,
            capture_output=True,
        )
        self.assertEqual(res_bad_utf8.returncode, 2)
        parsed = json.loads(res_bad_utf8.stdout.decode("utf-8"))
        self.assertEqual(len(parsed["invalid_targets"]), 1)

    def test_unreadable_file_permission_denied(self):
        if os.geteuid() == 0:
            self.skipTest("running as root ignores chmod 000")
        locked = self.root / "SSOT" / "locked.md"
        locked.write_text("# Locked\n", encoding="utf-8")
        locked.chmod(0)
        try:
            res = self.run_cli("--source", "SSOT/locked.md", "--", "src/payments/a.py")
            self.assertEqual(res.returncode, 3)
            self.assertIn("SSOT/locked.md", res.stderr)
        finally:
            locked.chmod(stat.S_IRUSR | stat.S_IWUSR)


if __name__ == "__main__":
    unittest.main()
