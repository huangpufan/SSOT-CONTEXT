#!/usr/bin/env python3
"""Regression tests for skills/ssot-doctor/assets/scripts/ssot-check.py.

Each test builds a small SSOT/ tree in a temporary directory, runs the real
checker as a subprocess, and asserts on its exit code and output. Run:
    python3 tests/test-ssot-check.py
"""

import hashlib
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Fixture repositories must not change on their own while a test compares their
# contents before and after a checker run. `git commit` can start background
# maintenance (seen on macOS runners), which creates and deletes lock files
# under .git; turn it off for every git process the tests start.
_GIT_FIXTURE_CONFIG = (("maintenance.auto", "false"), ("gc.auto", "0"), ("gc.autoDetach", "false"))
os.environ["GIT_CONFIG_COUNT"] = str(len(_GIT_FIXTURE_CONFIG))
for _index, (_key, _value) in enumerate(_GIT_FIXTURE_CONFIG):
    os.environ[f"GIT_CONFIG_KEY_{_index}"] = _key
    os.environ[f"GIT_CONFIG_VALUE_{_index}"] = _value
CHECKER = os.path.join(ROOT, "skills", "ssot-doctor", "assets", "scripts", "ssot-check.py")

README_V3 = """\
---
ssot_format: 3
language: en
---

# Demo

Demo is a tiny service.

## Map

- [Architecture](architecture.md)

## Invariants

| ID | Kind | Rule | Explained in | Status | Source |
|---|---|---|---|---|---|
| INV-01 | product promise | A retry never charges twice | [Retries](architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |

## Open questions

None yet.
"""

# Keep the original format-3 fixture for explicit migration coverage.
README = README_V3.replace("ssot_format: 3", "ssot_format: 4")

ARCHITECTURE = """\
# Architecture

## Failure and recovery

Retries are idempotent.
"""


def tree_digest(path):
    digest = hashlib.sha256()
    for directory, subdirs, files in sorted(os.walk(path)):
        subdirs.sort()
        for name in sorted(files):
            full = os.path.join(directory, name)
            digest.update(full.encode())
            try:
                with open(full, "rb") as handle:
                    digest.update(handle.read())
            except PermissionError:  # unreadable fixture: size and mtime still reveal writes
                info = os.stat(full)
                digest.update(f"{info.st_size}:{info.st_mtime_ns}".encode())
        digest.update(directory.encode())
    return digest.hexdigest()


class CheckerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = os.path.realpath(self.tmp.name)
        self.ssot = os.path.join(self.repo, "SSOT")
        os.makedirs(self.ssot)

    def tearDown(self):
        for directory, _, files in os.walk(self.repo):
            for name in files:
                os.chmod(os.path.join(directory, name), 0o644)
        self.tmp.cleanup()

    def write(self, relative, content, mode="w", encoding="utf-8"):
        path = os.path.join(self.ssot, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if mode == "wb":
            with open(path, "wb") as handle:
                handle.write(content)
        else:
            with open(path, "w", encoding=encoding) as handle:
                handle.write(textwrap.dedent(content))
        return path

    def valid(self):
        self.write("README.md", README)
        self.write("architecture.md", ARCHITECTURE)

    def run_checker(self, *args):
        before = tree_digest(self.repo)
        result = subprocess.run([sys.executable, CHECKER, *(args or [self.ssot])],
                                capture_output=True, text=True, cwd=self.repo)
        self.assertEqual(before, tree_digest(self.repo), "checker must never write")
        return result.returncode, result.stdout + result.stderr

    def assert_clean(self):
        code, out = self.run_checker()
        self.assertEqual(code, 0, out)
        self.assertNotIn("ERROR", out)
        return out

    def assert_error(self, fragment):
        code, out = self.run_checker()
        self.assertEqual(code, 1, out)
        self.assertIn(fragment, out)
        self.assertIn("ssot-check: FAIL - ", out)
        return out

    # --- entry point and format marker ---------------------------------
    def test_valid_tree_passes(self):
        self.valid()
        out = self.assert_clean()
        self.assertIn("ssot-check: PASS - 0 error(s), 0 warning(s)", out)

    def test_v3_fixture_is_legacy_not_format4_pass(self):
        self.write("README.md", README_V3)
        self.write("architecture.md", ARCHITECTURE)
        code, out = self.run_checker()
        self.assertEqual(code, 3, out)
        self.assertIn("v3 layout", out)
        self.assertNotIn("ssot-check: PASS", out)

    def external_owner(self, content):
        self.valid()
        self.write("../docs/owner.md", content)
        self.write("README.md", README.replace("architecture.md", "../docs/owner.md"))

    def test_external_owner_links_and_anchors_are_checked(self):
        self.external_owner(ARCHITECTURE + "\n[Missing](missing.md)\n")
        self.assert_error("broken link: missing.md")
        self.external_owner(ARCHITECTURE + "\n[Missing](#absent)\n")
        self.assert_error("missing heading anchor: #absent")

    def test_owner_scope_does_not_crawl_unrelated_or_nested_documents(self):
        self.external_owner(ARCHITECTURE + "\n[Detail](detail.md)\n")
        self.write("../docs/detail.md", "# Detail\n[Broken](absent.md)\n")
        self.write("../unrelated.md", "[Broken](absent.md)\n")
        self.assert_clean()

    def test_chinese_repository_owner_filename_heading_and_explicit_id(self):
        self.valid()
        self.write("../docs/创作设定.md", '# 创作设定\n\n## 人物关系与边界\n\n<a id="设定修改与决策记录"></a>\n')
        self.write("README.md", README + "\n[人物](../docs/创作设定.md#人物关系与边界)\n"
                   "[修改](../docs/创作设定.md#设定修改与决策记录)\n")
        self.assert_clean()
        self.write("../docs/创作设定.md", '# 创作设定\n\n## 人物关系与边界\n')
        self.assert_error("missing heading anchor: ../docs/创作设定.md#设定修改与决策记录")

    def test_non_markdown_route_is_valid_but_not_invariant_explanation(self):
        self.valid()
        self.write("../docs/settings.json", '{"mode": "draft"}\n')
        self.write("README.md", README + "\n[Settings](../docs/settings.json)\n")
        self.assert_clean()
        self.invariant_row("| INV-01 | process rule | Rule | [R](../docs/settings.json) | confirmed | user |")
        self.assert_error("needs a Markdown explanation in the same repository")

    def test_existing_large_external_owner_warns_without_rewriting(self):
        self.external_owner(ARCHITECTURE + "\n" + "Canonical context. " * 1000 + "\n")
        owner = os.path.join(self.repo, "docs", "owner.md")
        with open(owner, "rb") as handle:
            before = hashlib.sha256(handle.read()).hexdigest()
        out = self.assert_clean()
        self.assertIn("WARN  ../docs/owner.md", out)
        self.assertIn("16000-character reading budget", out)
        with open(owner, "rb") as handle:
            self.assertEqual(hashlib.sha256(handle.read()).hexdigest(), before)

    def test_external_owner_missing_file_is_error(self):
        self.valid()
        self.write("README.md", README.replace("architecture.md", "../docs/missing.md"))
        self.assert_error("broken link")

    def test_url_and_non_markdown_are_not_invariant_explanations(self):
        for target in ("https://example.com/rules.md", "../rules.txt"):
            self.invariant_row(f"| INV-01 | process rule | Rule | [R]({target}) | confirmed | user |")
            self.assert_error("needs a Markdown explanation in the same repository")

    def test_symlink_escape_is_not_an_owner(self):
        with tempfile.TemporaryDirectory() as outside:
            owner = os.path.join(outside, "owner.md")
            with open(owner, "w") as handle:
                handle.write("# Owner\n")
            os.symlink(owner, os.path.join(self.ssot, "escape.md"))
            self.invariant_row("| INV-01 | process rule | Rule | [R](escape.md) | confirmed | user |")
            self.assert_error("needs a Markdown explanation in the same repository")
            os.unlink(os.path.join(self.ssot, "escape.md"))

    def test_nested_git_repository_is_not_an_owner(self):
        self.external_owner(ARCHITECTURE)
        subprocess.run(["git", "init", "-q", os.path.join(self.repo, "docs")], check=True)
        self.assert_error("needs a Markdown explanation in the same repository")

    def test_ssot_below_repository_root_can_use_sibling_owner(self):
        subprocess.run(["git", "init", "-q", self.repo], check=True)
        self.ssot = os.path.join(self.repo, "project", "SSOT")
        os.makedirs(self.ssot)
        self.valid()
        self.write("../../docs/owner.md", ARCHITECTURE)
        self.write("README.md", README.replace("architecture.md", "../../docs/owner.md"))
        self.assert_clean()

    def test_requested_ssot_symlink_cannot_change_repository_identity(self):
        self.valid()
        self.git("init", "-q")
        for indirect in (False, True):
            with self.subTest(ancestor_symlink=indirect), tempfile.TemporaryDirectory() as target:
                subprocess.run(["git", "init", "-q", target], check=True)
                target_ssot = os.path.join(target, "SSOT")
                os.makedirs(target_ssot)
                for name, content in (("README.md", README), ("architecture.md", ARCHITECTURE)):
                    with open(os.path.join(target_ssot, name), "w") as handle:
                        handle.write(content)
                link = os.path.join(self.repo, "linked")
                os.symlink(target if indirect else target_ssot, link)
                try:
                    requested = os.path.join(link, "SSOT") if indirect else link
                    code, out = self.run_checker(requested)
                    self.assertEqual(code, 1, out)
                    self.assertIn("README must belong to the same repository", out)
                    # An explicit real path to another repo remains a legitimate request.
                    code, out = self.run_checker(target_ssot)
                    self.assertEqual(code, 0, out)
                finally:
                    os.unlink(link)

    def test_requested_ssot_symlink_within_same_repository_is_allowed(self):
        self.valid()
        self.git("init", "-q")
        link = os.path.join(self.repo, "linked")
        os.symlink(self.ssot, link)
        code, out = self.run_checker(link)
        self.assertEqual(code, 0, out)

    def test_format3_to_format4_migration_keeps_confirmed_rule_guard(self):
        self.valid()
        self.write("README.md", README_V3)
        self.git("init", "-q")
        self.commit()
        self.write("README.md", README.replace("A retry never charges twice", "A retry may charge twice"))
        self.assert_error("confirmed invariant INV-01 changed its rule")

    def test_external_owner_removed_code_mentions_are_checked(self):
        self.repo_with("src/gone.py")
        os.remove(os.path.join(self.repo, "src/gone.py"))
        self.commit()
        self.external_owner(ARCHITECTURE + "\nSee `src/gone.py`.\n")
        self.assertIn("`src/gone.py` was removed", self.assert_clean())

    def test_missing_readme(self):
        self.write("architecture.md", ARCHITECTURE)
        self.assert_error("missing SSOT/README.md")

    def test_missing_format_marker(self):
        self.write("README.md", "# Demo\n")
        self.assert_error("ssot_format: 4")

    def test_missing_language(self):
        self.write("README.md", README.replace("language: en\n", ""))
        self.write("architecture.md", ARCHITECTURE)
        self.assert_error("language:")

    def test_v2_layout_requires_migration(self):
        self.write("README.md", "# Old\n")
        self.write("STATUS.md", "# Status\n")
        code, out = self.run_checker()
        self.assertEqual(code, 3, out)
        self.assertIn("v2 layout", out)
        self.assertIn("requires migration", out)

    def test_v2_ledger_left_after_migration_warns(self):
        self.valid()
        self.write("HISTORY.md", "# History\n")
        out = self.assert_clean()
        self.assertIn("v2 ledger left after migration", out)

    def test_bootstrap_progress_is_reported(self):
        self.valid()
        self.write("BOOTSTRAP.md", "# SSOT setup in progress\n")
        self.assertIn("bootstrap is unfinished", self.assert_clean())

    def test_help_and_usage_errors(self):
        code, out = self.run_checker("--help")
        self.assertEqual(code, 0, out)
        self.assertIn("Usage", out)
        code, out = self.run_checker("a", "b")
        self.assertEqual(code, 2, out)

    def test_missing_directory_is_usage_error(self):
        code, out = self.run_checker(os.path.join(self.repo, "nope"))
        self.assertEqual(code, 2, out)

    # --- links and anchors ------------------------------------------------
    def test_broken_file_link(self):
        self.valid()
        self.write("gotchas.md", "# Gotchas\n\nSee [the guide](missing.md).\n")
        self.assert_error("broken link: missing.md")

    def test_broken_anchor(self):
        self.valid()
        self.write("gotchas.md", "# Gotchas\n\nSee [retries](architecture.md#no-such-heading).\n")
        self.assert_error("missing heading anchor")

    def test_github_slugs_for_cjk_punctuation_and_duplicates(self):
        self.valid()
        self.write("zh.md", """\
            # 中文

            ## GOT-0015：Codex 正文 text chunk 不是 Markdown 段落

            ## Current / 当前存在

            ## Notes

            ## Notes
            """)
        self.write("links.md", """\
            # Links

            [a](zh.md#got-0015codex-正文-text-chunk-不是-markdown-段落)
            [b](zh.md#current--当前存在)
            [c](zh.md#notes-1)
            [d](zh.md#%E4%B8%AD%E6%96%87)
            """)
        self.assert_clean()

    def test_truncated_cjk_anchor_is_caught(self):
        self.valid()
        self.write("zh.md", "# 中文\n\n## 不是 Markdown 段落或完整消息\n")
        self.write("links.md", "# Links\n\n[a](zh.md#不是-markdown-段落)\n")
        self.assert_error("missing heading anchor")

    def test_link_forms(self):
        self.valid()
        os.makedirs(os.path.join(self.ssot, "notes"))
        self.write("notes/a(b).md", "# A\n")
        self.write("forms.md", """\
            # Forms

            [parens](notes/a(b).md) [dq](architecture.md "title") [angle](<architecture.md>)
            """)
        self.assert_clean()
        self.write("forms.md", "# Forms\n\n[sq](missing.md 'title')\n")
        self.assert_error("broken link: missing.md")

    def test_link_after_a_multiline_comment_is_checked(self):
        self.valid()
        self.write("notes.md", "# Notes\n\n<!-- start\nhidden [x](ignored.md)\n--> [y](missing.md)\n")
        out = self.assert_error("broken link: missing.md")
        self.assertNotIn("ignored.md", out)

    def test_heading_anchors_ignore_comments_and_include_setext(self):
        self.valid()
        self.write("target.md", "# Target\n\n<!--\n# Hidden\n-->\n\nSetext Title\n============\n\n| a | b |\n|---|---|\n")
        self.write("links.md", "# Links\n\n[ok](target.md#setext-title)\n")
        self.assert_clean()
        self.write("links.md", "# Links\n\n[bad](target.md#hidden)\n")
        self.assert_error("missing heading anchor")

    def test_backslash_escapes_in_links(self):
        self.valid()
        self.write("notes.md", "# Notes\n\n[arch](architecture\\.md)\n")
        self.assert_clean()

    def test_reviewed_through_outside_git_is_incomplete(self):
        self.valid()
        self.write("README.md", README.replace("language: en\n", "language: en\nreviewed_through: abcdef1\n"))
        code, out = self.run_checker()
        self.assertEqual(code, 3, out)
        self.assertIn("not inside a git work tree", out)

    def test_comment_opener_inside_inline_code_is_text(self):
        self.valid()
        self.write("gotchas.md", "# Gotchas\n\nMermaid rejects `<!--` comments.\n\n[missing](does-not-exist.md)\n")
        self.assert_error("broken link: does-not-exist.md")

    def test_footnotes_are_not_links(self):
        self.valid()
        self.write("research.md", "# Research\n\nSee the test.[^1]\n\n[^1]: See the 2026 load test in PR 812.\n")
        self.assert_clean()

    def test_bom_and_emphasis_in_headings(self):
        self.write("README.md", "\ufeff" + README)
        self.write("architecture.md", ARCHITECTURE + "\n## The _important_ part\n")
        self.write("links.md", "# L\n\n[x](architecture.md#the-important-part)\n")
        self.assert_clean()

    def test_link_leaving_the_repository_warns(self):
        self.valid()
        self.write("notes.md", "# Notes\n\n[sibling](../../other-repo/WORK.md)\n")
        self.assertIn("link leaves the repository", self.assert_clean())

    def test_links_in_code_are_ignored(self):
        self.valid()
        self.write("notes.md", "# Notes\n\n`[x](missing.md)`\n\n```\n[y](missing.md)\n```\n")
        self.assert_clean()

    def test_external_and_repo_links(self):
        self.valid()
        os.makedirs(os.path.join(self.repo, "src"))
        with open(os.path.join(self.repo, "src", "app.py"), "w") as handle:
            handle.write("print(1)\n")
        self.write("notes.md", "# Notes\n\n[site](https://example.com) [code](../src/app.py)\n")
        self.assert_clean()

    def test_line_anchor_warns_or_fails_past_end(self):
        self.valid()
        self.write("notes.md", "# Notes\n\n[ok](architecture.md#L3) [bad](architecture.md#L99)\n")
        out = self.assert_error("line anchor past end of file")
        self.assertIn("line anchors drift", out)

    # --- invariants register ----------------------------------------------
    def invariant_row(self, row):
        self.write("README.md", README.replace(
            "| INV-01 | product promise | A retry never charges twice | [Retries](architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |",
            row))
        self.write("architecture.md", ARCHITECTURE)

    def test_bad_invariant_status(self):
        self.invariant_row("| INV-01 | process rule | Rule | [R](architecture.md) | approved | user |")
        self.assert_error("must be confirmed, candidate, or retired")

    def test_duplicate_invariant_id(self):
        self.invariant_row("| INV-01 | process rule | A | [R](architecture.md) | confirmed | user |\n"
                           "| INV-01 | process rule | B | [R](architecture.md) | candidate | inferred |")
        self.assert_error("duplicate invariant ID INV-01")

    def test_invariant_needs_link_and_source(self):
        self.invariant_row("| INV-02 |  | Rule | see code | confirmed |  |")
        out = self.assert_error("needs a link")
        self.assertIn("needs a source", out)
        self.assertIn("needs a kind", out)

    def test_invariant_explained_in_repository_owner_passes(self):
        with open(os.path.join(self.repo, "AGENTS.md"), "w") as handle:
            handle.write("# Agents\n")
        self.invariant_row("| INV-01 | process rule | Rule | [AGENTS](../AGENTS.md) | confirmed | user |")
        self.assert_clean()

    def test_invariant_anchor_in_readme_is_inside_ssot(self):
        self.invariant_row("| INV-01 | process rule | Rule | [Below](#open-questions) | confirmed | user |")
        self.assert_clean()

    def test_escaped_pipe_in_cell(self):
        self.invariant_row(r"| INV-01 | process rule | Use a \| b only | [R](architecture.md) | confirmed | user |")
        self.assert_clean()

    def test_commented_example_rows_are_ignored(self):
        self.invariant_row("<!-- | INV-9 | example | x | maybe | |  -->")
        self.assert_clean()

    def test_wrong_column_count_is_rejected(self):
        self.write("README.md", README.replace(
            "| ID | Kind | Rule | Explained in | Status | Source |\n|---|---|---|---|---|---|",
            "| ID | Kind | Rule | Explained in | Status | Source | Extra |\n|---|---|---|---|---|---|---|"))
        self.write("architecture.md", ARCHITECTURE)
        self.assert_error("needs 6 columns")

    def test_backticked_id_and_status_are_valid(self):
        self.invariant_row("| `INV-01` | process rule | Rule | [R](architecture.md) | `confirmed` | user |")
        self.assert_clean()

    def test_missing_separator_row_is_an_error(self):
        self.write("README.md", README.replace("|---|---|---|---|---|---|\n", ""))
        self.write("architecture.md", ARCHITECTURE)
        self.assert_error("needs a separator row")

    def test_four_backtick_fence_hides_inner_fences(self):
        self.valid()
        self.write("notes.md", "# Notes\n\n````markdown\n```\n[x](missing.md)\n```\n[y](missing.md)\n````\n")
        self.assert_clean()

    def test_invariant_table_under_a_subheading_is_checked(self):
        self.write("README.md", README.replace(
            "| ID | Kind | Rule |", "### Delivery\n\n| ID | Kind | Rule |").replace("| confirmed | user, 2026-05-02 |",
                                                                          "| maybe | user, 2026-05-02 |"))
        self.write("architecture.md", ARCHITECTURE)
        self.assert_error("must be confirmed, candidate, or retired")

    def test_invariant_explanation_via_symlink_to_repository_owner_passes(self):
        outside = os.path.join(self.repo, "outside")
        os.makedirs(outside)
        with open(os.path.join(outside, "rules.md"), "w") as handle:
            handle.write("# Rules\n")
        os.symlink(outside, os.path.join(self.ssot, "linked"))
        self.invariant_row("| INV-01 | process rule | Rule | [R](linked/rules.md) | confirmed | user |")
        self.assert_clean()

    def test_invariant_table_without_outer_pipes_is_checked(self):
        self.write("README.md", README.replace(
            "| ID | Kind | Rule | Explained in | Status | Source |\n|---|---|---|---|---|---|\n"
            "| INV-01 | product promise | A retry never charges twice | [Retries](architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |",
            "ID | Kind | Rule | Explained in | Status | Source\n---|---|---|---|---|---\n"
            "INV-01 | process rule | R | [R](architecture.md) | nonsense | user"))
        self.write("architecture.md", ARCHITECTURE)
        self.assert_error("must be confirmed, candidate, or retired")

    def test_separator_must_match_header_width(self):
        self.write("README.md", README.replace("|---|---|---|---|---|---|", "|---|---|"))
        self.write("architecture.md", ARCHITECTURE)
        self.assert_error("needs a separator row")

    def test_numbered_invariants_heading_is_still_checked(self):
        self.write("README.md", README.replace("## Invariants", "## 4. Invariants").replace(
            "| confirmed | user, 2026-05-02 |", "| approved-by-bot | user, 2026-05-02 |"))
        self.write("architecture.md", ARCHITECTURE)
        self.assert_error("must be confirmed, candidate, or retired")

    def test_list_shaped_register_is_an_error(self):
        self.write("README.md", README.split("## Invariants")[0] +
                   "## Invariants\n\n- INV-01 (approved by bot): see [AGENTS](architecture.md)\n")
        self.write("architecture.md", ARCHITECTURE)
        self.assert_error("must be written as a table")

    def test_reference_style_explanation_link(self):
        self.invariant_row("| INV-01 | process rule | Rule | [R][arch] | confirmed | user |")
        with open(os.path.join(self.ssot, "README.md"), encoding="utf-8") as handle:
            readme = handle.read()
        self.write("README.md", readme + "\n[arch]: architecture.md\n")
        self.assert_clean()

    def test_missing_invariants_section_warns(self):
        self.write("README.md", README.split("## Invariants")[0])
        self.write("architecture.md", ARCHITECTURE)
        self.assertIn("no Invariants section", self.assert_clean())

    # --- reviewed_through --------------------------------------------------
    def test_reviewed_through_placeholder_warns(self):
        self.valid()
        self.write("README.md", README.replace("language: en\n", "language: en\nreviewed_through: <commit>\n"))
        self.assertIn("template placeholder", self.assert_clean())

    def test_reviewed_through_must_exist(self):
        self.valid()
        subprocess.run(["git", "init", "-q", self.repo], check=True)
        subprocess.run(["git", "-C", self.repo, "-c", "user.name=t", "-c", "user.email=t@t", "add", "-A"], check=True)
        subprocess.run(["git", "-C", self.repo, "-c", "user.name=t", "-c", "user.email=t@t",
                        "commit", "-q", "-m", "init"], check=True)
        head = subprocess.run(["git", "-C", self.repo, "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
        self.write("README.md", README.replace("language: en\n", f"language: en\nreviewed_through: {head}\n"))
        self.assertNotIn("reviewed_through", self.assert_clean())
        self.write("README.md", README.replace("language: en\n", "language: en\nreviewed_through: deadbeef\n"))
        self.assertIn("is not a commit in this repository", self.assert_clean())

    def test_reviewed_through_rejects_moving_refs_and_strips_comments(self):
        self.valid()
        self.write("README.md", README.replace("language: en\n", "language: en\nreviewed_through: HEAD\n"))
        self.assert_error("must be a commit SHA")
        self.write("README.md", README.replace("language: en\n", "language: en\nreviewed_through: <commit>  # optional\n"))
        self.assertIn("template placeholder", self.assert_clean())

    def test_reviewed_through_off_the_current_history_warns(self):
        self.valid()
        run = lambda *a: subprocess.run(["git", "-C", self.repo, "-c", "user.name=t", "-c", "user.email=t@t", *a],
                                        capture_output=True, text=True, check=True).stdout.strip()
        run("init", "-q")
        run("add", "-A")
        run("commit", "-q", "-m", "one")
        run("checkout", "-q", "-b", "side")
        self.write("gotchas.md", "# Gotchas\n")
        run("add", "-A")
        run("commit", "-q", "-m", "side")
        side = run("rev-parse", "--short", "HEAD")
        run("checkout", "-q", "-")
        self.write("README.md", README.replace("language: en\n", f"language: en\nreviewed_through: {side}\n"))
        self.assertIn("not an ancestor of HEAD", self.assert_clean())

    # --- budgets, encoding, and tool failures -----------------------------
    def test_budget_counts_characters_not_bytes(self):
        self.valid()
        self.write("README.md", README.replace("Demo is a tiny service.", "中" * 3000))
        self.assertNotIn("reading budget", self.assert_clean())
        self.write("README.md", README.replace("Demo is a tiny service.", "中" * 9000))
        self.assertIn("reading budget", self.assert_clean())

    def test_readme_budget_does_not_count_invariant_rows(self):
        rows = "\n".join(f"| INV-{n:02d} | process rule | {'规则说明' * 40} | [R](architecture.md) | confirmed | user |"
                         for n in range(1, 60))
        self.invariant_row(rows)
        self.assertNotIn("reading budget", self.assert_clean())

    def test_large_register_is_not_a_warning(self):
        # mining has no target row count; a size warning made leads cut admitted rules to stay under it
        rows = "\n".join(f"| INV-{n:03d} | product promise | Rule {n} | [R](architecture.md) | candidate | tests |"
                         for n in range(1, 151))
        self.invariant_row(rows)
        self.assertNotIn("WARN", self.assert_clean())

    def test_undecodable_file_warns_without_crashing(self):
        self.valid()
        self.write("latin.md", "# Caf\xe9\n".encode("latin-1"), mode="wb")
        self.assertIn("not valid UTF-8", self.assert_clean())

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root can read unreadable directories")
    def test_unreadable_directory_is_not_a_pass(self):
        self.valid()
        self.write("private/notes.md", "# Notes\n\n[x](missing.md)\n")
        os.chmod(os.path.join(self.ssot, "private"), 0)
        try:
            code, out = self.run_checker()
        finally:
            os.chmod(os.path.join(self.ssot, "private"), 0o755)
        self.assertEqual(code, 3, out)
        self.assertIn("UNCHECKED", out)
        self.assertIn("ssot-check: INCOMPLETE - ", out)
        self.assertNotIn("ssot-check: PASS", out)

    def test_multi_part_invariant_ids_are_valid(self):
        self.invariant_row("| CLAUDE-MAXIM-1 | process rule | Rule | [R](architecture.md) | confirmed | user |\n"
                           "| CORE-RULE-2 | process rule | Rule | [R](architecture.md) | confirmed | user |")
        self.assert_clean()

    def test_invariant_columns_must_be_in_order(self):
        self.write("README.md", README.replace("| ID | Kind | Rule | Explained in | Status | Source |",
                                               "| ID | Kind | Rule | Explained in | Source | Status |"))
        self.write("architecture.md", ARCHITECTURE)
        self.assert_error("columns must be, in order")

    def test_chinese_invariant_headers_are_accepted(self):
        self.write("README.md", README.replace("| ID | Kind | Rule | Explained in | Status | Source |",
                                               "| ID | 类型 | 规则 | 解释位置 | 状态 | 来源 |"))
        self.write("architecture.md", ARCHITECTURE)
        self.assert_clean()

    def test_git_failure_is_not_reported_as_a_missing_commit(self):
        self.valid()
        subprocess.run(["git", "init", "-q", self.repo], check=True)
        self.write("README.md", README.replace("language: en\n", "language: en\nreviewed_through: deadbeef\n"))
        broken = os.path.join(self.repo, "broken-gitconfig")
        with open(broken, "w") as handle:
            handle.write("[core\n")
        before = tree_digest(self.repo)
        result = subprocess.run([sys.executable, CHECKER, self.ssot], capture_output=True, text=True,
                                env=dict(os.environ, GIT_CONFIG_GLOBAL=broken))
        self.assertEqual(before, tree_digest(self.repo))
        self.assertNotIn("is not a commit", result.stdout)
        self.assertEqual(result.returncode, 3, result.stdout)

    def test_query_string_is_not_part_of_the_path(self):
        self.valid()
        self.write("notes.md", "# Notes\n\n[raw](architecture.md?plain=1#failure-and-recovery)\n")
        self.assert_clean()

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root can read unreadable files")
    def test_tool_failure_has_its_own_exit_code(self):
        self.valid()
        path = self.write("locked.md", "# Locked\n")
        os.chmod(path, 0)
        code, out = self.run_checker()
        self.assertEqual(code, 3, out)
        self.assertIn("ssot-check: INCOMPLETE - ", out)

    # --- mentions of files that no longer exist ---------------------------
    def git(self, *args):
        return subprocess.run(["git", "-C", self.repo, "-c", "user.name=t", "-c", "user.email=t@t", *args],
                              capture_output=True, text=True, check=True).stdout.strip()

    def code_file(self, relative, content=None):
        seed = hashlib.sha256(relative.encode()).hexdigest()
        content = content or "".join(f"{relative} {seed[n:n + 8]} = {n}\n" for n in range(24))
        path = os.path.join(self.repo, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)

    def repo_with(self, *files):
        """A git repository holding a valid SSOT and the given code files, committed."""
        self.valid()
        for relative in files:
            self.code_file(relative)
        self.git("init", "-q")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "start")

    def commit(self, message="change"):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD")

    def test_mention_of_a_removed_file_warns_with_the_commit(self):
        self.repo_with("src/app/old.py", "src/app/live.py")
        os.remove(os.path.join(self.repo, "src/app/old.py"))
        sha = self.commit("remove old")
        self.write("architecture.md", ARCHITECTURE + "\nThe worker lives in `src/app/old.py` and `src/app/live.py`.\n")
        self.commit()
        out = self.assert_clean()
        self.assertIn(f"architecture.md:7  `src/app/old.py` was removed in {sha[:10]}", out)
        self.assertNotIn("live.py", out)
        self.assertIn("1 mention(s) of files that no longer exist", out)

    def test_moved_file_names_its_new_place(self):
        self.repo_with("src/a.py")
        self.git("mv", "src/a.py", "src/b.py")
        sha = self.commit("move")
        self.write("architecture.md", ARCHITECTURE + "\nSee `src/a.py:12`.\n")
        self.assertIn(f"`src/a.py` was moved to `src/b.py` in {sha[:10]}", self.assert_clean())

    def test_uncommitted_removal_and_move_are_reported(self):
        self.repo_with("src/gone.py", "src/staged.py", "src/moved.py")
        self.write("architecture.md", ARCHITECTURE + "\n`src/gone.py`, `src/staged.py`, `src/moved.py`\n")
        self.commit()
        os.remove(os.path.join(self.repo, "src/gone.py"))
        self.git("rm", "-q", "src/staged.py")
        self.git("mv", "src/moved.py", "src/new.py")
        out = self.assert_clean()
        self.assertIn("`src/gone.py` was removed in uncommitted changes", out)
        self.assertIn("`src/staged.py` was removed in uncommitted changes", out)
        self.assertIn("`src/moved.py` was moved to `src/new.py` in uncommitted changes", out)

    def test_abbreviated_paths_match_by_suffix(self):
        self.repo_with("src/app/web/routes.py", "src/app/web/views.py")
        os.remove(os.path.join(self.repo, "src/app/web/routes.py"))
        self.commit()
        self.write("architecture.md", ARCHITECTURE + "\n`web/routes.py` and `web/views.py`\n")
        out = self.assert_clean()
        self.assertIn("`web/routes.py` (`src/app/web/routes.py`) was removed", out)
        self.assertNotIn("views.py", out)

    def test_paths_git_never_knew_are_not_reported(self):
        self.repo_with("src/app.py")
        self.write("architecture.md", ARCHITECTURE + "\nPlanned: `src/billing/retry.py`. Runtime: `~/.app/config.json`, "
                                                     "`userData/state.json`. Folder: `src/`.\n")
        out = self.assert_clean()
        self.assertNotIn("no longer exist", out)
        self.assertNotIn("INFO", out)

    def test_records_of_the_past_are_not_checked(self):
        self.repo_with("src/old.py")
        os.remove(os.path.join(self.repo, "src/old.py"))
        self.commit()
        self.write("decisions/0001-drop-old.md", "# 0001\n\nWe removed `src/old.py`.\n")
        self.write("research/old-path.md", "# Research\n\n`src/old.py` was slow.\n")
        self.assertNotIn("old.py", self.assert_clean())

    def test_line_naming_the_removing_commit_is_history(self):
        self.repo_with("src/old.py")
        os.remove(os.path.join(self.repo, "src/old.py"))
        sha = self.commit()
        self.write("gotchas.md", f"# Gotchas\n\nDo not revive `src/old.py` (removed in {sha[:7]}).\n\n"
                                 "Unrelated commit deadbeef12 does not excuse `src/old.py`.\n")
        out = self.assert_clean()
        self.assertIn("gotchas.md:5  `src/old.py` was removed", out)
        self.assertNotIn("gotchas.md:3", out)

    def test_readded_file_is_not_reported(self):
        self.repo_with("src/back.py")
        os.remove(os.path.join(self.repo, "src/back.py"))
        self.commit()
        self.code_file("src/back.py")
        self.commit()
        self.write("architecture.md", ARCHITECTURE + "\n`src/back.py`\n")
        self.assertNotIn("back.py", self.assert_clean())

    def test_relative_mentions_resolve_from_the_document(self):
        self.repo_with("src/old.py")
        os.remove(os.path.join(self.repo, "src/old.py"))
        self.commit()
        self.write("architecture.md", ARCHITECTURE + "\n`../src/old.py`\n")
        self.assertIn("`src/old.py` was removed", self.assert_clean())

    def test_sparse_checkout_is_not_a_removal(self):
        self.repo_with("src/far.py")
        self.write("architecture.md", ARCHITECTURE + "\n`src/far.py`\n")
        self.commit()
        self.git("update-index", "--skip-worktree", "src/far.py")
        os.remove(os.path.join(self.repo, "src/far.py"))
        self.assertNotIn("far.py", self.assert_clean())

    def test_only_whole_path_spans_outside_code_blocks_are_checked(self):
        self.repo_with("tests/test_old.py")
        os.remove(os.path.join(self.repo, "tests/test_old.py"))
        self.commit()
        self.write("process.md", "# Process\n\nRun `pytest tests/test_old.py`.\n\n```\ntests/test_old.py\n```\n\n"
                                 "Node: `tests/test_old.py::test_x`.\n")
        out = self.assert_clean()
        self.assertIn("process.md:9  `tests/test_old.py` was removed", out)
        self.assertNotIn("process.md:3", out)

    def test_dot_folders_and_non_ascii_names_are_checked(self):
        self.repo_with(".github/workflows/old.yml", "文档/旧说明.md")
        os.remove(os.path.join(self.repo, ".github/workflows/old.yml"))
        os.remove(os.path.join(self.repo, "文档/旧说明.md"))
        self.commit()
        self.write("process.md", "# Process\n\nCI: `.github/workflows/old.yml`. Notes: `文档/旧说明.md`.\n")
        out = self.assert_clean()
        self.assertIn("`.github/workflows/old.yml` was removed", out)
        self.assertIn("`文档/旧说明.md` was removed", out)

    def test_link_labels_are_left_to_the_link_check(self):
        self.repo_with("docs/old.md")
        self.git("mv", "docs/old.md", "docs/new.md")
        self.commit()
        self.write("architecture.md", ARCHITECTURE + "\nSee [`docs/old.md`](../docs/new.md).\n")
        self.assertNotIn("old.md", self.assert_clean())

    def test_reference_style_labels_are_left_to_the_link_check(self):
        self.repo_with("docs/old.md")
        self.git("mv", "docs/old.md", "docs/new.md")
        self.commit()
        self.write("architecture.md", ARCHITECTURE + "\n[`docs/old.md`][new] and [`docs/old.md`][]\n\n"
                                                     "[new]: ../docs/new.md\n[`docs/old.md`]: ../docs/new.md\n")
        self.assertNotIn("old.md` was", self.assert_clean())

    def test_explicit_relative_path_is_not_matched_by_suffix(self):
        self.repo_with("poc/skeleton/plugin.js")
        os.remove(os.path.join(self.repo, "poc/skeleton/plugin.js"))
        self.commit()
        self.write("architecture.md", ARCHITECTURE + "\n`../skeleton/plugin.js` and `skeleton/plugin.js`\n")
        out = self.assert_clean()
        self.assertNotIn("../skeleton", out)
        self.assertIn("`skeleton/plugin.js` (`poc/skeleton/plugin.js`) was removed", out)

    def test_removed_folder_is_reported(self):
        self.repo_with("src/legacy/a.py", "src/legacy/b.py", "src/live/c.py")
        self.git("rm", "-q", "-r", "src/legacy")
        sha = self.commit()
        self.write("architecture.md", ARCHITECTURE + "\n`src/legacy/` and `src/live` and `legacy/b.py`\n")
        out = self.assert_clean()
        self.assertIn(f"`src/legacy` (a folder) was removed in {sha[:10]}", out)
        self.assertIn("`legacy/b.py` (`src/legacy/b.py`) was removed", out)
        self.assertNotIn("src/live", out)

    def test_removal_while_resolving_a_merge_is_found(self):
        self.repo_with("src/keep.py", "src/drop.py")
        main = self.git("rev-parse", "--abbrev-ref", "HEAD")
        self.git("checkout", "-q", "-b", "side")
        self.code_file("src/side.py")
        self.commit("side")
        self.git("checkout", "-q", main)
        self.code_file("src/main.py")
        self.commit("main")
        self.git("merge", "-q", "--no-commit", "side")
        self.git("rm", "-q", "src/drop.py")
        merge = self.commit("merge and drop")
        self.write("architecture.md", ARCHITECTURE + "\n`src/drop.py`\n")
        self.assertIn(f"`src/drop.py` was removed in {merge[:10]}", self.assert_clean())

    def test_removal_on_a_merged_branch_names_the_branch_commit(self):
        self.repo_with("src/old.py")
        main = self.git("rev-parse", "--abbrev-ref", "HEAD")
        self.git("checkout", "-q", "-b", "side")
        os.remove(os.path.join(self.repo, "src/old.py"))
        removed = self.commit("remove on side")
        self.git("checkout", "-q", main)
        self.code_file("src/main.py")
        self.commit("main")
        self.git("merge", "-q", "--no-edit", "side")
        self.write("architecture.md", ARCHITECTURE + "\n`src/old.py`\n")
        self.assertIn(f"`src/old.py` was removed in {removed[:10]}", self.assert_clean())

    def test_since_lists_only_later_removals(self):
        self.repo_with("src/early.py", "src/late.py")
        os.remove(os.path.join(self.repo, "src/early.py"))
        start = self.commit("early")
        os.remove(os.path.join(self.repo, "src/late.py"))
        self.commit("late")
        self.write("architecture.md", ARCHITECTURE + "\n`src/early.py` `src/late.py`\n")
        code, out = self.run_checker(self.ssot, "--since", start[:8])
        self.assertEqual(code, 0, out)
        self.assertIn("`src/late.py` was removed", out)
        self.assertNotIn("`src/early.py` was", out)
        self.assertIn(f"1 mention(s) of files removed before {start[:8]} are not listed", out)
        code, out = self.run_checker(self.ssot, "--since", "nosuchref")
        self.assertEqual(code, 3, out)
        self.assertIn("--since nosuchref is not a commit", out)
        self.assertEqual(self.run_checker(self.ssot, "--since")[0], 2)

    def test_git_hooks_and_monitors_never_run(self):
        self.repo_with("src/old.py")
        os.remove(os.path.join(self.repo, "src/old.py"))
        self.commit()
        self.write("architecture.md", ARCHITECTURE + "\n`src/old.py`\n")
        marker = os.path.join(self.tmp.name + "-fsmonitor-ran")
        hook = os.path.join(self.repo, ".git", "fsmonitor-hook")
        with open(hook, "w") as handle:
            handle.write(f"#!/bin/sh\ntouch '{marker}'\nexit 1\n")
        os.chmod(hook, 0o755)
        self.git("config", "core.fsmonitor", hook)
        self.assertIn("`src/old.py` was removed", self.assert_clean())
        self.assertFalse(os.path.exists(marker), "the checker must not run core.fsmonitor")

    def test_clean_filters_never_run(self):
        self.repo_with("src/old.py", "src/live.py", "src/gone.py")
        os.remove(os.path.join(self.repo, "src/old.py"))
        self.commit()
        marker = self.tmp.name + "-clean-filter-ran"
        with open(os.path.join(self.repo, ".gitattributes"), "w") as handle:
            handle.write("*.py filter=spy\n")
        self.commit("attributes")
        self.git("config", "filter.spy.clean", f"sh -c 'touch {marker}; cat'")
        self.code_file("src/live.py", "changed\n")
        os.remove(os.path.join(self.repo, "src/gone.py"))
        self.write("architecture.md", ARCHITECTURE + "\n`src/old.py` `src/live.py` `src/gone.py`\n")
        out = self.assert_clean()
        self.assertIn("`src/old.py` was removed", out)
        self.assertIn("`src/gone.py` was removed in uncommitted changes", out)
        self.assertFalse(os.path.exists(marker), "the checker must not run clean filters")

    def test_removed_again_by_a_merge_after_being_restored(self):
        self.repo_with("src/old.py")
        main = self.git("rev-parse", "--abbrev-ref", "HEAD")
        os.remove(os.path.join(self.repo, "src/old.py"))
        self.commit("first removal")
        self.code_file("src/old.py")
        restored = self.commit("restore")
        self.git("checkout", "-q", "-b", "side")
        self.code_file("src/side.py")
        self.commit("side")
        self.git("checkout", "-q", main)
        self.code_file("src/main.py")
        self.commit("main")
        self.git("merge", "-q", "--no-commit", "side")
        self.git("rm", "-q", "src/old.py")
        merge = self.commit("merge and remove again")
        self.write("architecture.md", ARCHITECTURE + "\n`src/old.py`\n")
        code, out = self.run_checker(self.ssot, "--since", restored)
        self.assertIn(f"`src/old.py` was removed in {merge[:10]}", out)

    def test_since_is_validated_even_without_mentions(self):
        self.repo_with()
        code, out = self.run_checker(self.ssot, "--since", "nosuchref")
        self.assertEqual(code, 3, out)

    def test_file_names_that_look_like_headers(self):
        self.repo_with("\x01a", "\x01b", "src/old.py")
        for name in ("\x01a", "\x01b", "src/old.py"):
            os.remove(os.path.join(self.repo, name))
        self.commit()
        self.write("architecture.md", ARCHITECTURE + "\n`src/old.py`\n")
        self.assertIn("`src/old.py` was removed", self.assert_clean())

    def test_git_failure_while_reading_history_is_incomplete(self):
        self.repo_with("src/old.py")
        os.remove(os.path.join(self.repo, "src/old.py"))
        self.commit()
        self.write("architecture.md", ARCHITECTURE + "\n`src/old.py`\n")
        fake = os.path.join(self.tmp.name + "-bin")
        os.makedirs(fake, exist_ok=True)
        real = subprocess.run(["sh", "-c", "command -v git"], capture_output=True, text=True).stdout.strip()
        for failing in ("log", "diff-tree"):
            with open(os.path.join(fake, "git"), "w") as handle:
                handle.write(f'#!/bin/sh\nfor a in "$@"; do [ "$a" = {failing} ] && exit 7; done\n'
                             f'exec {real} "$@"\n')
            os.chmod(os.path.join(fake, "git"), 0o755)
            result = subprocess.run([sys.executable, CHECKER, self.ssot], capture_output=True, text=True,
                                    env=dict(os.environ, PATH=fake + os.pathsep + os.environ["PATH"]))
            self.assertEqual(result.returncode, 3, f"{failing}: {result.stdout}")
            self.assertIn("mentions of removed files: git failed", result.stdout)

    def test_unusual_file_names_do_not_crash(self):
        self.repo_with("src/a\u2028b.py", "src/tab\there.py", "src/old.py")
        for name in ("src/a\u2028b.py", "src/tab\there.py", "src/old.py"):
            os.remove(os.path.join(self.repo, name))
        self.commit()
        self.write("architecture.md", ARCHITECTURE + "\n`src/old.py`\n")
        self.assertIn("`src/old.py` was removed", self.assert_clean())

    def test_hard_wrapped_paragraphs_warn(self):
        self.valid()
        self.write("product.md", "# Product\n\nThis paragraph was written for a\nnarrow terminal and broken by\nhand every few words.\n\n"
                                 "- a list item that was also\n  wrapped across three short\n  source lines\n")
        out = self.assert_clean()
        self.assertIn("product.md:3  2 paragraph(s) are broken across short lines (lines 3, 7)", out)

    def test_one_line_paragraphs_lists_tables_and_code_do_not_warn(self):
        self.valid()
        long_line = "这一段写成一行。" * 30
        self.write("product.md", f"# 产品\n\n{long_line}\n\n- 一\n- 二\n- 三\n- 四\n\n| a | b |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |\n\n"
                                 "```\nline one\nline two\nline three\n```\n\n<!-- a comment\nover three\nlines -->\n\n"
                                 "Two short\nlines only.\n\nLine break kept on purpose  \nwith two spaces  \nat each end.\n")
        self.assertNotIn("broken across", self.assert_clean())

    def test_outside_git_or_before_the_first_commit(self):
        self.valid()
        self.write("architecture.md", ARCHITECTURE + "\n`src/old.py`\n")
        self.assertIn("not in a git work tree, so mentions of removed files were not checked", self.assert_clean())
        self.git("init", "-q")
        self.assertNotIn("INFO", self.assert_clean())

    # --- confirmed invariants changed without the user ---------------------
    CONFIRMED = "| INV-01 | product promise | A retry never charges twice | [Retries](architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |"

    def edit_confirmed(self, row, extra=""):
        self.write("README.md", README.replace(self.CONFIRMED, row + extra))

    def test_changed_confirmed_rule_is_an_error(self):
        self.repo_with()
        for row, what in (
                ("| INV-01 | product promise | A retry never charges twice, except for refunds | [Retries](architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |", "rule"),
                ("| INV-01 | process rule | A retry never charges twice | [Retries](architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |", "kind"),
                ("| INV-01 | product promise | A retry never charges twice | [Retries](architecture.md#failure-and-recovery) | candidate | user, 2026-05-02 |", "status"),
                ("| INV-01 | product promise | Retries are a request, not a gate | [Retries](architecture.md) | confirmed | `user`, 2026-05-02 |", "rule")):
            self.edit_confirmed(row)
            out = self.assert_error(f"confirmed invariant INV-01 changed its {what} since the last commit")
            self.assertIn("README.md:18", out)

    def test_removed_confirmed_rule_is_an_error(self):
        self.repo_with()
        self.edit_confirmed("| INV-02 | product promise | Refunds go to the original card | [Retries](architecture.md) | candidate | inferred |")
        self.assert_error("confirmed invariant INV-01 was removed since the last commit")

    def test_moved_link_reworded_source_and_other_rows_are_not_reported(self):
        self.repo_with()
        self.edit_confirmed("|  INV-01 | product promise |  A retry  never charges twice | [Retries](architecture.md) | `confirmed` | user (payments lead), 2026-05-02 |",
                            "\n| INV-02 | product promise | Refunds go to the original card | [Retries](architecture.md) | confirmed | `docs/refunds.md` |")
        self.assertNotIn("confirmed invariant", self.assert_clean())
        self.commit()
        self.edit_confirmed(self.CONFIRMED, "\n| INV-02 | product promise | Refunds go to the card | [Retries](architecture.md) | candidate | inferred |")
        self.assertNotIn("INV-01", self.assert_error("confirmed invariant INV-02 changed its rule and status"))

    def test_candidate_rules_may_change(self):
        self.repo_with()
        self.edit_confirmed(self.CONFIRMED, "\n| INV-02 | product promise | Refunds go to the original card | [Retries](architecture.md) | candidate | inferred |")
        self.commit()
        self.edit_confirmed(self.CONFIRMED)
        self.assertNotIn("invariant", self.assert_clean())

    def test_change_with_a_newly_dated_source_is_reported_for_review(self):
        self.repo_with()
        self.edit_confirmed("| INV-01 | product promise | A retry never charges twice, except for refunds | [Retries](architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02; narrowed by the user, 2026-11-02 |")
        out = self.assert_clean()
        self.assertIn("confirmed invariant(s) INV-01 changed since the last commit with a newly dated Source", out)
        self.edit_confirmed("| INV-01 | product promise | A retry never charges twice, except for refunds | [Retries](architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02; narrowed by the user, 2026-05-02 |")
        self.assertIn("with a newly dated Source", self.assert_clean())  # approved on the day it was set
        self.edit_confirmed("| INV-01 | product promise | A retry never charges twice, except for refunds | [Retries](architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 (narrowed) |")
        self.assert_error("confirmed invariant INV-01 changed its rule")

    def test_since_compares_with_the_named_commit(self):
        self.repo_with()
        start = self.git("rev-parse", "HEAD")
        self.edit_confirmed("| INV-01 | product promise | A retry rarely charges twice | [Retries](architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |")
        self.commit()
        self.assertNotIn("confirmed invariant", self.assert_clean())
        code, out = self.run_checker(self.ssot, "--since", start)
        self.assertEqual(code, 1, out)
        self.assertIn(f"confirmed invariant INV-01 changed its rule since {start}", out)

    def test_migration_from_a_v2_readme_is_not_compared(self):
        self.write("README.md", "# Old\n\n## Invariants\n\n| ID | Kind | Rule | Explained in | Status | Source |\n|---|---|---|---|---|---|\n"
                                "| INV-01 | product promise | Old wording | [R](architecture.md) | confirmed | user |\n")
        self.write("architecture.md", ARCHITECTURE)
        self.git("init", "-q")
        self.commit()
        self.write("README.md", README)
        self.assertNotIn("confirmed invariant", self.assert_clean())

    def test_confirmed_check_needs_a_committed_readme(self):
        self.valid()
        self.git("init", "-q")
        self.edit_confirmed("| INV-01 | product promise | Anything | [Retries](architecture.md) | confirmed | user |")
        self.assertNotIn("INFO", self.assert_clean())
        self.write("notes.md", "# Notes\n")
        self.git("add", "SSOT/notes.md")
        self.commit()
        self.assertNotIn("INFO", self.assert_clean())

    def test_shallow_history_is_disclosed(self):
        self.repo_with("src/old.py")
        os.remove(os.path.join(self.repo, "src/old.py"))
        self.commit()
        self.write("architecture.md", ARCHITECTURE + "\n`src/old.py`\n")
        self.commit()
        clone = os.path.join(self.repo, "shallow")
        subprocess.run(["git", "clone", "-q", "--depth", "1", f"file://{self.repo}", clone], check=True)
        result = subprocess.run([sys.executable, CHECKER, os.path.join(clone, "SSOT")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("shallow history", result.stdout)
        self.assertNotIn("was removed", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=1)
