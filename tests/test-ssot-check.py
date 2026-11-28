#!/usr/bin/env python3
"""Regression tests for skills/ssot-doctor/assets/scripts/ssot-check.py.

Each test builds a small SSOT/ tree in a temporary directory, runs the real
checker as a subprocess, and asserts on its exit code and output. Run:
    python3 tests/test-ssot-check.py
"""

import ast
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
    def test_regression_names_are_unique(self):
        with open(__file__, encoding="utf-8") as handle:
            tree = ast.parse(handle.read())
        duplicates = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            seen = set()
            for method in node.body:
                if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)) and method.name.startswith("test_"):
                    if method.name in seen:
                        duplicates.append(f"{node.name}.{method.name}:{method.lineno}")
                    seen.add(method.name)
        self.assertFalse(duplicates, "duplicate regression methods are silently overwritten: " + ", ".join(duplicates))

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

    def run_checker(self, *args, env=None):
        before = tree_digest(self.repo)
        result = subprocess.run([sys.executable, CHECKER, *(args or [self.ssot])],
                                capture_output=True, text=True, cwd=self.repo, env=env)
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

    def test_format5_without_git_checks_only_selected_entry_and_direct_owners(self):
        self.valid()
        self.write("README.md", README.replace("ssot_format: 4", "ssot_format: 5"))
        self.write("private-unrouted.md", "# Unrelated\n\n[Broken](missing-original.md)\n")
        out = self.assert_clean()
        self.assertIn("selected entry and direct local owners", out)
        self.assertNotIn("missing-original", out)
        self.assertFalse(os.path.exists(os.path.join(self.repo, ".git")))
        self.write("architecture.md", ARCHITECTURE + "\n[Broken](missing-owner.md)\n")
        self.assert_error("broken link: missing-owner.md")

    def test_named_space_and_directory_report_the_entry_actually_checked(self):
        self.valid()
        entry = README.replace("ssot_format: 4", "ssot_format: 5")
        self.write("README.md", entry)
        named = self.write("field-notes.md", entry + "\n[Guide](missing-guide.md)\n")
        code, default = self.run_checker(self.ssot)
        self.assertEqual(code, 0, default)
        self.assertIn(os.path.join(self.ssot, "README.md"), default.splitlines()[-1])
        code, selected = self.run_checker(named)
        self.assertEqual(code, 1, selected)
        self.assertIn("broken link: missing-guide.md", selected)
        self.assertIn(named, selected.splitlines()[-1])
        os.remove(os.path.join(self.ssot, "README.md"))
        self.write("field-notes.md", entry)
        code, selected = self.run_checker(named)
        self.assertEqual(code, 0, selected)
        self.assertIn(named, selected.splitlines()[-1])

    def test_format5_external_owner_is_a_reported_route_without_implicit_read(self):
        self.valid()
        self.write("README.md", README.replace("ssot_format: 4", "ssot_format: 5").replace(
            "architecture.md#failure-and-recovery", "../external.md#failure-and-recovery"))
        with open(os.path.join(self.repo, "external.md"), "w") as handle:
            handle.write("# External\n\n[Broken](not-accessed.md)\n")
        out = self.assert_clean()
        self.assertIn("external explanation not checked", out)
        self.assertIn("external-space route not read", out)
        self.assertNotIn("not-accessed", out)
        os.remove(os.path.join(self.repo, "external.md"))
        self.assert_error("missing external-space target")

    def test_general_space_uses_its_routes_for_setup_and_history(self):
        entry = README.replace("ssot_format: 4", "ssot_format: 5")
        self.valid()
        self.write("README.md", entry)
        named = self.write("field-notes.md", entry + "\n[Setup progress](field-progress.md)\n")
        self.write("BOOTSTRAP.md", "# Museum setup\n")
        self.write("HISTORY.md", "# Oral history\n")
        self.write("STATUS.md", "# Boat status\n")
        for path, expected in ((self.ssot, 0), (named, 1)):
            code, out = self.run_checker(path)
            self.assertEqual(code, expected, out)
            for unrelated in ("BOOTSTRAP.md", "HISTORY.md", "STATUS.md"):
                self.assertNotIn(unrelated, out)
        self.assertIn("broken link: field-progress.md", out)
        self.write("field-progress.md", "# Field setup\n\n[Source](missing-field-log.md)\n")
        code, out = self.run_checker(named)
        self.assertEqual(code, 1, out)
        self.assertIn("broken link: missing-field-log.md", out)

    def test_selected_general_owners_limit_actual_content_reads(self):
        self.valid()
        entry = self.write("entry.md", README.replace("ssot_format: 4", "ssot_format: 5") +
                           "\n[Retained locator](original.md#source)\n")
        original = self.write("original.md", "# Source\n\n[Private plate](missing-plate.png)\n")
        self.write("architecture.md", ARCHITECTURE +
                   "\n[Earlier wording](original.md#L1) and [current wording](#missing-heading).\n")
        # Observe opens inside the CLI. A clean report alone could hide an anchor read.
        observer = textwrap.dedent("""
            import os, runpy, sys
            watched, checker, *args = sys.argv[1:]
            def audit(event, arguments):
                if event == "open" and arguments[0] == watched:
                    print("OPENED ORIGINAL", file=sys.stderr)
            sys.addaudithook(audit)
            sys.argv = [checker, *args]
            runpy.run_path(checker, run_name="__main__")
        """)
        def observe(*args):
            return subprocess.run([sys.executable, "-c", observer, original, CHECKER, entry, *args],
                                  cwd=self.repo, text=True, capture_output=True)
        full = observe()
        self.assertEqual(full.returncode, 1, full.stdout)
        self.assertIn("OPENED ORIGINAL", full.stderr)
        self.assertIn("missing-plate.png", full.stdout)
        scoped = observe("--owners", "architecture.md")
        self.assertEqual(scoped.returncode, 1, scoped.stdout)
        self.assertIn("missing heading anchor", scoped.stdout)
        self.assertIn("selected files only", scoped.stdout.splitlines()[-1])
        self.assertNotIn("OPENED ORIGINAL", scoped.stderr)
        self.assertNotIn("missing-plate.png", scoped.stdout)
        entry_only = observe("--owners")
        self.assertEqual(entry_only.returncode, 0, entry_only.stdout)
        self.assertNotIn("OPENED ORIGINAL", entry_only.stderr)
        self.assertIn("Git history excluded", entry_only.stdout)

    def test_selected_task_reached_through_a_permitted_index(self):
        for version, name in (("4", "README.md"), ("5", "space.md")):
            with self.subTest(version=version):
                entry = self.write(name, f"---\nssot_format: {version}\nlanguage: en\n---\n"
                                   "# Study\n[Board](board.md)\n\n## Invariants\nNone registered.\n")
                board = self.write("board.md", "# Board\n[Pilot](work/pilot.md) and [minutes](original.md#L1).\n")
                pilot = self.write("work/pilot.md", "# Pilot\n[Board](../board.md) and [result](#old-result).\n")
                original = self.write("original.md", "# Minutes\n")
                observer = textwrap.dedent("""
                    import runpy, sys
                    watched = set(sys.argv[1:4])
                    def audit(event, args):
                        if event == "open" and args[0] in watched:
                            print("READ", args[0], file=sys.stderr)
                    sys.addaudithook(audit)
                    sys.argv = sys.argv[4:]
                    runpy.run_path(sys.argv[0], run_name="__main__")
                """)
                def observe(*selection):
                    return subprocess.run([sys.executable, "-c", observer, board, pilot, original, CHECKER,
                                           entry, "--owners", *selection], cwd=self.repo,
                                          capture_output=True, text=True)

                checked = observe("work/pilot.md", "board.md")
                self.assertEqual(checked.returncode, 1, checked.stdout)
                self.assertIn("missing heading anchor: #old-result", checked.stdout)
                self.assertIn("READ " + board, checked.stderr)
                self.assertIn("READ " + pilot, checked.stderr)
                self.assertNotIn("READ " + original, checked.stderr)
                missing_index = observe("work/pilot.md")
                self.assertEqual(missing_index.returncode, 1, missing_index.stdout)
                self.assertNotIn("READ ", missing_index.stderr)
                self.write("work/pilot.md", "# Pilot\n[Board](../board.md)\n")
                self.assertEqual(observe("board.md", "work/pilot.md").returncode, 0)

    def test_named_space_with_sibling_owners_uses_only_its_explicit_selection(self):
        entry = self.write("desk/entry.md", "---\nssot_format: 5\nlanguage: en\n---\n"
                           "# Estuary\n[Guide](../field/guide.md)\n\n## Invariants\nNone registered.\n")
        self.write("field/guide.md", "# Guide\n[Decision](notes.md#old) and [source](original.md#voice)\n")
        self.write("field/notes.md", "# Current\n")
        original = self.write("field/original.md", "# Voice\n")
        args = [entry, "--space-root", self.ssot, "--owners", "../field/guide.md", "../field/notes.md"]
        self.assertEqual(self.run_checker(entry, "--owners", "../field/guide.md")[0], 2)
        # Fail on any attempt to open the excluded original, including an anchor lookup.
        observer = textwrap.dedent("""
            import runpy, sys
            original = sys.argv.pop(1)
            def audit(event, args):
                if event == "open" and args[0] == original:
                    raise RuntimeError("opened excluded source")
            sys.addaudithook(audit)
            sys.argv = sys.argv[1:]
            runpy.run_path(sys.argv[0], run_name="__main__")
        """)
        def observe():
            return subprocess.run([sys.executable, "-c", observer, original, CHECKER, *args],
                                  cwd=self.repo, capture_output=True, text=True)
        broken = observe()
        self.assertEqual(broken.returncode, 1, broken.stdout + broken.stderr)
        self.assertIn("missing heading anchor: notes.md#old", broken.stdout)
        self.write("field/notes.md", "# Old\n")
        self.assertEqual(observe().returncode, 0)
        self.assertEqual(self.run_checker(entry, "--space-root", self.ssot, "--owners", "../field/notes.md")[0], 1)
        os.makedirs(os.path.join(self.ssot, "field", ".git"))
        self.assertNotEqual(observe().returncode, 0)
        self.assertEqual(self.run_checker(entry, "--space-root", os.path.dirname(original), "--owners")[0], 2)
        self.assertEqual(self.run_checker(entry, "--space-root", self.ssot)[0], 2)
        self.valid()
        self.assertEqual(self.run_checker(os.path.join(self.ssot, "README.md"), "--space-root", self.repo, "--owners")[0], 2)

    def test_selected_owners_require_local_files_and_explicit_entry(self):
        self.valid()
        entry = self.write("entry.md", README.replace("ssot_format: 4", "ssot_format: 5"))
        self.write("unrouted.md", "# Other\n\n[Private plate](missing-plate.png)\n")
        code, out = self.run_checker(entry, "--owners", "unrouted.md", "absent.md")
        self.assertEqual(code, 1, out)
        for name in ("unrouted.md", "absent.md"):
            self.assertIn(name, out)
        self.assertNotIn("missing-plate.png", out)
        os.symlink("unrouted.md", os.path.join(self.ssot, "alias.md"))
        for args in ((entry, "--owners", "alias.md"), (entry, "--owners", "../other.md"),
                     (self.ssot, "--owners"), (entry, "--owners", "--since", "HEAD")):
            code, out = self.run_checker(*args)
            self.assertEqual(code, 2, out)
        code, out = self.run_checker(os.path.join(self.ssot, "README.md"), "--owners")
        self.assertEqual(code, 0, out)
        self.assertIn("Git history excluded", out)

    def test_selected_development_owners_skip_withdrawn_and_unrouted_bodies(self):
        self.valid()
        allowed = os.path.join(self.repo, "guide.md")
        original = self.write("original.md", "# Source\n\n[Old reference](private-missing.png)\n")
        other = self.write("another.md", "# Other\n\n[Another reference](other-missing.png)\n")
        entry = self.write("README.md", README +
                           "\n[Retained source](original.md#source) and [Guide](../guide.md).\n")
        with open(allowed, "w", encoding="utf-8") as handle:
            handle.write("# Guide\n\n[Source locator](SSOT/original.md#L1) and [broken](#missing-heading).\n")
        observer = textwrap.dedent("""
            import runpy, sys
            source, other, checker, *args = sys.argv[1:]
            def audit(event, arguments):
                if event == "open" and arguments[0] in (source, other):
                    print("OPENED EXCLUDED BODY", file=sys.stderr)
            sys.addaudithook(audit)
            sys.argv = [checker, *args]
            runpy.run_path(checker, run_name="__main__")
        """)
        def observe(*args):
            return subprocess.run([sys.executable, "-c", observer, original, other, CHECKER, *args],
                                  cwd=self.repo, text=True, capture_output=True)
        full = observe(self.ssot)
        self.assertEqual(full.returncode, 1, full.stdout)
        self.assertIn("OPENED EXCLUDED BODY", full.stderr)
        self.assertIn("private-missing.png", full.stdout)
        self.assertIn("other-missing.png", full.stdout)
        scoped = observe(entry, "--owners", "../guide.md")
        self.assertEqual(scoped.returncode, 1, scoped.stdout)
        self.assertNotIn("OPENED EXCLUDED BODY", scoped.stderr)
        self.assertIn("missing heading anchor: #missing-heading", scoped.stdout)
        self.assertNotIn("private-missing.png", scoped.stdout)
        self.assertNotIn("other-missing.png", scoped.stdout)
        self.assertIn("Git history excluded", scoped.stdout)
        self.assertIn("selected files only", scoped.stdout.splitlines()[-1])
        rejected = observe(entry, "--owners", "another.md")
        self.assertEqual(rejected.returncode, 1, rejected.stdout)
        self.assertNotIn("OPENED EXCLUDED BODY", rejected.stderr)
        self.assertIn("reachable through the selection", rejected.stdout)

    def test_unrecognized_named_entry_does_not_select_the_enclosing_directory(self):
        self.valid()
        self.write("other-space.md", "[Broken](unrelated-missing.md)\n")
        self.write("BOOTSTRAP.md", "# Other project\n")
        for marker in ("", "ssot_format: 4", "ssot_format: 99"):
            named = self.write("field-notes.md", f"---\n{marker}\nlanguage: en\n---\n# Notes\n")
            code, out = self.run_checker(named)
            self.assertEqual(code, 1, out)
            self.assertIn("a named entry file requires", out)
            self.assertNotIn("unrelated-missing", out)
            self.assertNotIn("BOOTSTRAP", out)
            self.assertIn(named, out.splitlines()[-1])

    def test_format5_named_entry_retains_confirmed_history_guard(self):
        self.valid()
        self.write("context.md", README.replace("ssot_format: 4", "ssot_format: 5"))
        os.remove(os.path.join(self.ssot, "README.md"))
        self.git("init", "-q")
        self.commit()
        self.write("context.md", README.replace("ssot_format: 4", "ssot_format: 5").replace(
            "A retry never charges twice", "A retry may charge twice"))
        code, out = self.run_checker(os.path.join(self.ssot, "context.md"))
        self.assertEqual(code, 1, out)
        self.assertIn("confirmed invariant INV-01 changed its rule", out)

    def test_format5_absolute_external_target_is_statted_without_crawling(self):
        self.valid()
        external = os.path.join(self.repo, "external-owner.md")
        with open(external, "w") as handle:
            handle.write("# External owner\n\n[Uncrawled](private-missing.md)\n")
        link = f"\n[External owner]({external})\n"
        self.write("README.md", README.replace("ssot_format: 4", "ssot_format: 5") + link)
        out = self.assert_clean()
        self.assertIn("absolute link path is machine-specific", out)
        self.assertIn("external-space route not read", out)
        self.assertNotIn("private-missing", out)
        os.remove(external)
        self.assert_error("missing external-space target")
        self.write("README.md", README + link)
        out = self.assert_clean()  # existing format-4 absolute-link warning stays compatible
        self.assertNotIn("missing external-space target", out)

    def test_format5_absolute_local_owner_is_checked_as_a_direct_owner(self):
        self.valid()
        owner = self.write("absolute-owner.md", "# Local owner\n\n[Broken](missing-local.md)\n")
        self.write("README.md", README.replace("ssot_format: 4", "ssot_format: 5") + f"\n[Owner]({owner})\n")
        self.assert_error("broken link: missing-local.md")

    def test_protected_rules_heading_checks_the_same_register_and_history(self):
        self.valid()
        translated = README.replace("## Invariants", "## 保护规则")
        self.write("README.md", translated)
        self.assertNotIn("no Invariants section", self.assert_clean())
        self.write("README.md", translated.replace("| confirmed |", "| merely-observed |"))
        self.assert_error("must be confirmed, candidate, or retired")
        self.write("README.md", translated)
        self.git("init", "-q");self.commit()
        self.write("README.md", translated.replace("A retry never charges twice", "A retry may charge twice"))
        self.assert_error("confirmed invariant INV-01 changed its rule")

    def test_v3_fixture_is_legacy_not_format4_pass(self):
        self.write("README.md", README_V3)
        self.write("architecture.md", ARCHITECTURE)
        code, out = self.run_checker()
        self.assertEqual(code, 3, out)
        self.assertIn("v3 layout", out)
        self.assertNotIn("ssot-check: PASS", out)

    def test_explicit_unknown_format_is_not_overridden_by_legacy_files(self):
        for version in ("6", "vendor-next"):
            with self.subTest(version=version):
                self.write("README.md", f"---\nssot_format: {version}\nlanguage: en\n---\n# Future space\n")
                self.write("STATUS.md", "# Retained history\n")
                out = self.assert_error("ssot_format")
                self.assertNotIn("migrate to format 4", out)
                self.assertNotIn("legacy SSOT requires migration", out)

    def test_markerless_legacy_files_still_identify_v2(self):
        self.write("README.md", "# Historical space\n")
        self.write("STATUS.md", "# Old progress ledger\n")
        code, out = self.run_checker()
        self.assertEqual(code, 3, out)
        self.assertIn("v2 layout", out)

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

    def test_existing_large_external_owner_emits_info_while_ssot_doc_warns(self):
        self.external_owner(ARCHITECTURE + "\n" + "Canonical context. " * 1000 + "\n")
        owner = os.path.join(self.repo, "docs", "owner.md")
        with open(owner, "rb") as handle:
            before = hashlib.sha256(handle.read()).hexdigest()
        out = self.assert_clean()
        self.assertIn("INFO  ../docs/owner.md", out)
        self.assertIn("16000-character reading budget", out)
        self.assertNotIn("WARN", out)
        with open(owner, "rb") as handle:
            self.assertEqual(hashlib.sha256(handle.read()).hexdigest(), before)
        # An oversized document owned inside SSOT/ still warns.
        self.write("architecture.md", ARCHITECTURE + "\n" + "SSOT detail. " * 1400 + "\n")
        out_ssot = self.assert_clean()
        self.assertIn("WARN  architecture.md", out_ssot)
        self.assertIn("16000-character reading budget", out_ssot)

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

    def test_system_path_alias_before_repository_keeps_identity(self):
        self.valid()
        self.git("init", "-q")
        with tempfile.TemporaryDirectory() as aliases, tempfile.TemporaryDirectory() as foreign:
            alias = os.path.join(aliases, "system-root")
            os.symlink(os.path.dirname(self.repo), alias)
            requested = os.path.join(alias, os.path.basename(self.repo))
            code, out = self.run_checker(os.path.join(requested, "SSOT"))
            self.assertEqual(code, 0, out)

            # The preceding system alias must not hide a later cross-repo link.
            subprocess.run(["git", "init", "-q", foreign], check=True)
            target = os.path.join(foreign, "SSOT")
            os.makedirs(target)
            for name, content in (("README.md", README), ("architecture.md", ARCHITECTURE)):
                with open(os.path.join(target, name), "w") as handle:
                    handle.write(content)
            link = os.path.join(self.repo, "linked")
            os.symlink(target, link)
            try:
                code, out = self.run_checker(os.path.join(requested, "linked"))
                self.assertEqual(code, 1, out)
                self.assertIn("README must belong to the same repository", out)
            finally:
                os.unlink(link)

    def test_physical_worktree_path_keeps_requested_alias(self):
        self.valid()
        self.git("init", "-q")
        with tempfile.TemporaryDirectory() as aliases:
            # macOS TMPDIR and a linked /tmp reach the same place by another name; git
            # reports the physical path, which must not split the worktree in two.
            alias = os.path.join(aliases, "system-root")
            os.symlink(os.path.dirname(self.repo), alias)
            code, out = self.run_checker(os.path.join(alias, os.path.basename(self.repo), "SSOT"))
            self.assertEqual(code, 0, out)
            # The same SSOT under the physical spelling is clean too.
            code, out = self.run_checker(self.ssot)
            self.assertEqual(code, 0, out)

    def test_physical_path_through_another_repository_stays_foreign(self):
        self.valid()
        self.git("init", "-q")
        with tempfile.TemporaryDirectory() as aliases, tempfile.TemporaryDirectory() as foreign:
            subprocess.run(["git", "init", "-q", foreign], check=True)
            target = os.path.join(foreign, "SSOT")
            os.makedirs(target)
            for name, content in (("README.md", README), ("architecture.md", ARCHITECTURE)):
                with open(os.path.join(target, name), "w") as handle:
                    handle.write(content)
            alias = os.path.join(aliases, "system-root")
            os.symlink(os.path.dirname(foreign), alias)
            code, out = self.run_checker(os.path.join(alias, os.path.basename(foreign), "SSOT"))
            self.assertEqual(code, 0, out)
            code, out = self.run_checker(target)
            self.assertEqual(code, 0, out)
            link = os.path.join(self.repo, "linked")
            os.symlink(target, link)
            try:
                # The requested repository stays the outer one even when git names the
                # physical path of the repository behind the link.
                code, out = self.run_checker(os.path.join(alias, os.path.basename(self.repo), "linked"))
                self.assertEqual(code, 1, out)
                self.assertIn("README must belong to the same repository", out)
            finally:
                os.unlink(link)

    def test_shared_first_file_does_not_make_ssot_the_worktree_root(self):
        # Sharing a file inode does not make its containing directories identical.
        # Build README first so it can be the first entry in both directories.
        with tempfile.TemporaryDirectory() as repo:
            readme = os.path.join(repo, "README.md")
            with open(readme, "w") as handle:
                handle.write(README.replace("architecture.md", "../docs/owner.md"))
            ssot = os.path.join(repo, "SSOT")
            os.makedirs(ssot)
            os.link(readme, os.path.join(ssot, "README.md"))
            os.makedirs(os.path.join(repo, "docs"))
            with open(os.path.join(repo, "docs", "owner.md"), "w") as handle:
                handle.write(ARCHITECTURE)
            subprocess.run(["git", "init", "-q", repo], check=True)
            # Directory iteration order is unspecified. Exercise an allowed order
            # that puts the genuinely shared file first, without faking its inode.
            import contextlib
            import runpy
            from unittest.mock import patch
            repository_root = runpy.run_path(CHECKER)["repository_root"]
            real_scandir = os.scandir

            @contextlib.contextmanager
            def readme_first(path):
                with real_scandir(path) as entries:
                    ordered = sorted(entries, key=lambda entry: entry.name != "README.md")
                yield iter(ordered)

            with patch.object(os, "scandir", readme_first):
                self.assertEqual(repository_root(ssot), os.path.realpath(repo))
            code, out = self.run_checker(ssot)
            self.assertEqual(code, 0, out)

    def test_inherited_git_routing_cannot_select_a_foreign_repository(self):
        self.repo_with()
        with tempfile.TemporaryDirectory() as foreign:
            subprocess.run(["git", "init", "-q", foreign], check=True)
            environments = (
                {"GIT_DIR": os.path.join(foreign, ".git")},
                {"GIT_WORK_TREE": foreign},
                {"GIT_DIR": os.path.join(foreign, ".git"), "GIT_WORK_TREE": foreign},
                {"GIT_COMMON_DIR": os.path.join(foreign, ".git")},
                {"GIT_INDEX_FILE": os.path.join(foreign, ".git", "index")},
                {"GIT_OBJECT_DIRECTORY": os.path.join(foreign, ".git", "objects")},
                {"GIT_SHALLOW_FILE": os.path.join(foreign, "missing-shallow")},
            )
            for routing in environments:
                with self.subTest(routing=routing):
                    self.edit_confirmed(self.CONFIRMED)
                    env = dict(os.environ, **routing)
                    code, out = self.run_checker(env=env)
                    self.assertEqual(code, 0, out)
                    self.edit_confirmed(self.CONFIRMED.replace("never charges twice", "may charge twice"))
                    code, out = self.run_checker(env=env)
                    self.assertEqual(code, 1, out)
                    self.assertIn("confirmed invariant INV-01 changed its rule", out)
                    self.edit_confirmed(self.CONFIRMED)

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

    def test_since_requires_available_committed_git_history(self):
        self.valid()
        self.write("README.md", README.replace("ssot_format: 4", "ssot_format: 5"))
        for label, env in (("no repository", None),
                           ("git unavailable", dict(os.environ, PATH=""))):
            with self.subTest(label=label):
                code, out = self.run_checker(self.ssot, "--since", "HEAD", env=env)
                self.assertEqual(code, 3, out)
                self.assertIn("UNCHECKED", out)
        self.git("init", "-q")
        code, out = self.run_checker(self.ssot, "--since", "HEAD")
        self.assertEqual(code, 3, out)
        self.assertIn("UNCHECKED", out)
        self.write("README.md", README.replace("ssot_format: 4", "ssot_format: 5") + "\n[Broken](missing.md)\n")
        code, out = self.run_checker(self.ssot, "--since", "HEAD")
        self.assertEqual(code, 3, out)
        self.assertIn("broken link: missing.md", out)

    def test_since_accepts_commit_before_entry_exists(self):
        self.git("init", "-q")
        self.write("seed.txt", "seed\n")
        base = self.commit("before SSOT entry")
        self.valid()
        code, out = self.run_checker(self.ssot, "--since", base)
        self.assertEqual(code, 0, out)

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

    def test_confirmed_rule_preserves_exact_names_and_literal_spacing(self):
        self.repo_with()
        rule = "Write Report.csv with `--Exact` and the label `A  B`"
        row = self.CONFIRMED.replace("A retry never charges twice", rule)
        self.edit_confirmed(row)
        self.commit()
        for old, new in (("Report.csv", "report.csv"), ("--Exact", "--exact"), ("A  B", "A B")):
            with self.subTest(new=new):
                self.edit_confirmed(row.replace(old, new))
                self.assert_error("confirmed invariant INV-01 changed its rule")
        self.edit_confirmed(row.replace("Write Report", "Write  Report").replace("confirmed", "CONFIRMED"))
        self.assert_clean()
        self.edit_confirmed(row.replace("Report.csv", "report.csv").replace("2026-05-02", "2026-05-02, user 2026-11-19"))
        self.assertIn("with a newly dated Source", self.assert_clean())

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

    def test_accepted_change_with_unknown_approval_date_needs_source_repair(self):
        self.repo_with()
        self.write("architecture.md", ARCHITECTURE + "\n## Refund exception\n\n"
                   "Recorded as accepted by the payments lead: refund retries may charge again; "
                   "the promise still covers all other retries. Approval date unknown. "
                   "The original exchange is unavailable.\n")
        self.commit("record accepted refund exception")
        self.code_file("src/payments.py", "def may_charge_again(is_refund):\n    return is_refund\n")
        changed = self.CONFIRMED.replace("A retry never charges twice", "A retry never charges twice, except for refunds")
        self.edit_confirmed(changed)
        # An accepted owner and matching code do not bypass the Source guard.
        out = self.assert_error("confirmed invariant INV-01 changed its rule")
        self.assertIn("With matching acceptance, keep only the authorized change and repair Source", out)
        self.assertIn("Without acceptance, restore the protection and ask the user", out)
        self.assertIn("Do not revert only the register", out)
        self.edit_confirmed(changed.replace("user, 2026-05-02 |",
            "user, 2026-05-02; payments lead, recorded as accepted in "
            "[Refund exception](architecture.md#refund-exception); approval date unknown; "
            "original exchange unavailable; record captured 2026-11-06 |"))
        # Structural success records a real source, not proof of authorization.
        self.assertIn("with a newly dated Source", self.assert_clean())

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

    def test_stray_ancestor_dotgit_directory_does_not_break_system_alias(self):
        self.valid()
        self.git("init", "-q")
        with tempfile.TemporaryDirectory() as outer, tempfile.TemporaryDirectory() as foreign:
            # A non-repository .git directory above an alias must not mark the path as inside a repo.
            os.makedirs(os.path.join(outer, ".git"))
            alias = os.path.join(outer, "sub", "system-root")
            os.makedirs(os.path.dirname(alias))
            os.symlink(os.path.dirname(self.repo), alias)
            requested = os.path.join(alias, os.path.basename(self.repo))
            code, out = self.run_checker(os.path.join(requested, "SSOT"))
            self.assertEqual(code, 0, out)

            # Once inside the actual repository, a cross-repo symlink is still rejected.
            subprocess.run(["git", "init", "-q", foreign], check=True)
            target = os.path.join(foreign, "SSOT")
            os.makedirs(target)
            for name, content in (("README.md", README), ("architecture.md", ARCHITECTURE)):
                with open(os.path.join(target, name), "w") as handle:
                    handle.write(content)
            link = os.path.join(self.repo, "linked")
            os.symlink(target, link)
            try:
                code, out = self.run_checker(os.path.join(requested, "linked"))
                self.assertEqual(code, 1, out)
                self.assertIn("README must belong to the same repository", out)
            finally:
                os.unlink(link)

    def test_uppercase_markdown_extension_is_walked_and_anchor_checked(self):
        self.valid()
        self.write("NOTES.MD", "# Existing Heading\n\nSee [missing](architecture.md#nope).\n")
        self.write("architecture.md", ARCHITECTURE + "\nSee [notes](NOTES.MD#missing-section).\n")
        code, out = self.run_checker(self.ssot)
        self.assertEqual(code, 1, out)
        self.assertIn("NOTES.MD:3  missing heading anchor: architecture.md#nope", out)
        self.assertIn("missing heading anchor: NOTES.MD#missing-section", out)

    def test_removals_skips_rev_list_without_matches_and_orders_repeated_removals(self):
        self.repo_with("src/old.py")
        first_commit = self.git("rev-parse", "HEAD")
        # Mention only a runtime path never tracked in Git: rev-list need not run.
        self.write("architecture.md", ARCHITECTURE + "\nRuntime cache: `var/runtime.tmp`.\n")
        self.commit("mention runtime path")
        probe = textwrap.dedent("""
            import importlib.util, sys
            spec = importlib.util.spec_from_file_location("checker", sys.argv[1])
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            orig = mod.git_output
            calls = []
            def spy(directory, *args):
                calls.append(args)
                return orig(directory, *args)
            mod.git_output = spy
            code = mod.main([sys.argv[1], sys.argv[2], "--since", sys.argv[3]])
            assert code == 0, code
            assert not any(a and a[0] == "rev-list" for a in calls), calls
        """)
        result = subprocess.run([sys.executable, "-B", "-c", probe, CHECKER, self.ssot, first_commit],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        # Two separate removals of the same path still report the newest commit first.
        os.remove(os.path.join(self.repo, "src/old.py"))
        first_drop = self.commit("first drop")
        self.code_file("src/old.py", "v2\n")
        self.commit("restore old")
        os.remove(os.path.join(self.repo, "src/old.py"))
        second_drop = self.commit("second drop")
        self.write("architecture.md", ARCHITECTURE + "\nLegacy: `src/old.py`.\n")
        code, out = self.run_checker(self.ssot)
        self.assertEqual(code, 0, out)
        self.assertIn(second_drop[:10], out)
        self.assertNotIn(first_drop[:10], out)

    # --- optional topic-sharded invariants register -----------------------
    def sharded_setup(self, readme_invariants=None, shipping_rows=None, webhooks_rows=None):
        self.write("architecture.md", ARCHITECTURE)
        inv_block = readme_invariants if readme_invariants is not None else textwrap.dedent("""\
            | ID | Kind | Rule | Explained in | Status | Source |
            |---|---|---|---|---|---|
            | INV-01 | product promise | A retry never charges twice | [Retries](architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |

            Topic shards:
            - [Shipping invariants](invariants/shipping.md) (`SHP-01`..`SHP-02`)
            - [Webhooks invariants](invariants/webhooks.md) (`WHK-01`)
            """)
        readme = README.split("## Invariants\n")[0] + "## Invariants\n\n" + inv_block.strip() + "\n\n## Open questions\n\nNone yet.\n"
        self.write("README.md", readme)
        ship = shipping_rows if shipping_rows is not None else (
            "| SHP-01 | architecture invariant | Never drop parcel manifests | [Retries](../architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |\n"
        )
        self.write("invariants/shipping.md",
                   "# Shipping invariants\n\n| ID | Kind | Rule | Explained in | Status | Source |\n|---|---|---|---|---|---|\n" + ship)
        whk = webhooks_rows if webhooks_rows is not None else (
            "| WHK-01 | process rule | Cap webhook retries at 10 seconds | [Retries](../architecture.md#failure-and-recovery) | confirmed | user, 2026-05-03 |\n"
        )
        self.write("invariants/webhooks.md",
                   "# Webhooks invariants\n\n| ID | 类型 | 规则 | 解释位置 | 状态 | 来源 |\n|---|---|---|---|---|---|\n" + whk)

    def test_sharded_invariants_valid_passes(self):
        self.sharded_setup()
        out = self.assert_clean()
        self.assertNotIn("WARN", out)

    def test_sharded_only_invariants_without_inline_table_passes(self):
        self.sharded_setup(readme_invariants="- [Shipping invariants](invariants/shipping.md) covers SHP-01\n- [Webhooks invariants](invariants/webhooks.md) covers WHK-01\n")
        out = self.assert_clean()
        self.assertNotIn("WARN", out)

    def test_sharded_duplicate_id_between_readme_and_shard_fails(self):
        self.sharded_setup(shipping_rows="| INV-01 | process rule | Duplicate rule | [Retries](../architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |\n")
        out = self.assert_error("duplicate invariant ID INV-01")
        self.assertIn("invariants/shipping.md", out)
        self.assertIn("README.md:", out)

    def test_sharded_duplicate_id_across_two_shards_fails(self):
        self.sharded_setup(webhooks_rows="| SHP-01 | process rule | Duplicate across shards | [Retries](../architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |\n")
        out = self.assert_error("duplicate invariant ID SHP-01")
        self.assertIn("invariants/webhooks.md", out)
        self.assertIn("invariants/shipping.md:", out)

    def test_sharded_bad_table_columns_and_invalid_status_fail(self):
        self.sharded_setup(shipping_rows="| SHP-01 | process rule | Rule | [Ext](https://example.com) | bogus | user |\n")
        out = self.assert_error("status 'bogus' must be confirmed, candidate, or retired")
        self.assertIn("invariants/shipping.md", out)
        self.assertIn("needs a Markdown explanation in the same repository", out)

    def test_sharded_non_table_prose_rule_fails(self):
        self.sharded_setup()
        self.write("invariants/shipping.md", "# Shipping invariants\n\n- SHP-01: never drop parcel manifests.\n")
        out = self.assert_error("invariants must be written as a table")
        self.assertIn("invariants/shipping.md", out)

    def test_sharded_broken_explanation_anchor_relative_to_shard_fails(self):
        self.sharded_setup(shipping_rows="| SHP-01 | process rule | Rule | [Missing](../architecture.md#missing-anchor) | confirmed | user, 2026-05-02 |\n")
        out = self.assert_error("missing heading anchor: ../architecture.md#missing-anchor")
        self.assertIn("invariants/shipping.md", out)

    def test_unlinked_invariants_subdir_shard_fails(self):
        self.sharded_setup()
        self.write("invariants/orphan.md",
                   "# Orphan\n\n| ID | Kind | Rule | Explained in | Status | Source |\n|---|---|---|---|---|---|\n"
                   "| ORP-01 | process rule | Unreachable rule | [R](../architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |\n")
        out = self.assert_error("unlinked invariants shard")
        self.assertIn("invariants/orphan.md", out)

    def test_unlinked_frontmatter_register_shard_fails(self):
        self.valid()
        self.write("README.md", README.replace("- [Architecture](architecture.md)",
                                               "- [Architecture](architecture.md)\n- [Extra rules](extra-rules.md)"))
        self.write("extra-rules.md",
                   "---\nssot_register: shard\n---\n\n# Extra rules\n\n| ID | Kind | Rule | Explained in | Status | Source |\n|---|---|---|---|---|---|\n"
                   "| EXT-01 | process rule | Rule | [R](architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |\n")
        out = self.assert_error("unlinked invariants shard")
        self.assertIn("extra-rules.md", out)

    def test_ordinary_link_under_invariants_is_not_treated_as_shard(self):
        self.write("architecture.md", ARCHITECTURE + "\n| ColA | ColB |\n|---|---|\n| a | b |\n")
        self.write("README.md", README.replace("## Open questions",
                                               "Background: [Architecture](architecture.md).\n\n## Open questions"))
        out = self.assert_clean()
        self.assertNotIn("WARN", out)

    def test_large_invariants_shard_is_not_a_warning(self):
        rows = "\n".join(f"| SHP-{n:03d} | product promise | Rule {n} for shipping | [R](../architecture.md#failure-and-recovery) | candidate | tests |"
                         for n in range(1, 151)) + "\n"
        self.sharded_setup(shipping_rows=rows)
        self.assertNotIn("WARN", self.assert_clean())
        self.write("invariants/shipping.md",
                   "# Shipping invariants\n\n" + ("prose " * 2800) + "\n\n| ID | Kind | Rule | Explained in | Status | Source |\n|---|---|---|---|---|---|\n" + rows)
        self.assertIn("reading budget (invariant rows not counted)", self.assert_clean())

    def test_confirmed_invariant_moved_from_readme_to_shard_passes(self):
        self.write("architecture.md", ARCHITECTURE)
        mono = README.replace(
            "| INV-01 | product promise | A retry never charges twice | [Retries](architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |",
            "| INV-01 | product promise | A retry never charges twice | [Retries](architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |\n"
            "| SHP-01 | architecture invariant | Never drop parcel manifests | [Retries](architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |"
        )
        self.write("README.md", mono)
        self.git("init", "-q")
        base = self.commit("monolithic register")
        self.sharded_setup()
        out = self.assert_clean()
        self.assertNotIn("WARN", out)
        code, since_out = self.run_checker(self.ssot, "--since", base)
        self.assertEqual(code, 0, since_out)

    def test_confirmed_invariant_altered_during_move_to_shard_fails(self):
        self.write("architecture.md", ARCHITECTURE)
        mono = README.replace(
            "| INV-01 | product promise | A retry never charges twice | [Retries](architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |",
            "| INV-01 | product promise | A retry never charges twice | [Retries](architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |\n"
            "| SHP-01 | architecture invariant | Never drop parcel manifests | [Retries](architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |"
        )
        self.write("README.md", mono)
        self.git("init", "-q")
        self.commit("monolithic register")
        self.sharded_setup(shipping_rows="| SHP-01 | architecture invariant | Drop parcel manifests after 1 day | [Retries](../architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |\n")
        out = self.assert_error("confirmed invariant SHP-01 changed its rule")
        self.assertIn("invariants/shipping.md", out)

    def test_confirmed_invariant_edited_or_removed_inside_shard_fails(self):
        self.sharded_setup()
        self.git("init", "-q")
        self.commit("sharded baseline")
        # Silent edit without new date fails.
        self.write("invariants/shipping.md",
                   "# Shipping invariants\n\n| ID | Kind | Rule | Explained in | Status | Source |\n|---|---|---|---|---|---|\n"
                   "| SHP-01 | architecture invariant | Drop manifests freely | [Retries](../architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |\n")
        self.assert_error("confirmed invariant SHP-01 changed its rule")
        # Removal fails.
        self.write("invariants/shipping.md",
                   "# Shipping invariants\n\n| ID | Kind | Rule | Explained in | Status | Source |\n|---|---|---|---|---|---|\n")
        self.assert_error("confirmed invariant SHP-01 was removed")
        # Approved update with new date passes and reports approval INFO.
        self.write("invariants/shipping.md",
                   "# Shipping invariants\n\n| ID | Kind | Rule | Explained in | Status | Source |\n|---|---|---|---|---|---|\n"
                   "| SHP-01 | architecture invariant | Archive manifests after 30 days | [Retries](../architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02; updated 2026-06-01 |\n")
        self.assertIn("SHP-01", self.assert_clean())

    def test_confirmed_invariant_fails_when_shard_unlinked_or_deleted(self):
        self.sharded_setup()
        self.git("init", "-q")
        self.commit("sharded baseline")
        # Unlinking the shard drops SHP-01 from active register and leaves an orphan shard.
        self.write("README.md", README)
        out = self.assert_error("confirmed invariant SHP-01 was removed")
        self.assertIn("unlinked invariants shard", out)
        # Deleting the shard from disk still reports the removed confirmed invariant from git history.
        os.remove(os.path.join(self.ssot, "invariants/shipping.md"))
        out = self.assert_error("confirmed invariant SHP-01 was removed")
        self.assertIn("invariants/shipping.md", out)

    def test_confirmed_invariant_fails_when_shard_replaced_with_escaping_symlink(self):
        self.sharded_setup()
        self.git("init", "-q")
        self.commit("sharded baseline")
        with tempfile.TemporaryDirectory() as outside:
            ext = os.path.join(outside, "evil.md")
            with open(ext, "w", encoding="utf-8") as handle:
                handle.write("# Evil\n")
            target = os.path.join(self.ssot, "invariants/shipping.md")
            os.remove(target)
            os.symlink(ext, target)
            try:
                out = self.assert_error("confirmed invariant SHP-01 was removed")
                self.assertIn("leaves the repository", out)
            finally:
                os.unlink(target)

    def test_format5_general_space_supports_register_shard_and_catches_map_only_shard(self):
        space = os.path.join(self.repo, "space")
        os.makedirs(space)
        def write_space(name, content):
            path = os.path.join(space, name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(textwrap.dedent(content))
            return path
        write_space("owner.md", "# Owner\n\n## Rules\n\nKeep receipts.\n")
        write_space("finance-rules.md",
                    "---\nssot_register: shard\n---\n\n# Finance rules\n\n"
                    "| ID | Kind | Rule | Explained in | Status | Source |\n|---|---|---|---|---|---|\n"
                    "| FIN-01 | process rule | Keep tax receipts 7 years | [Rules](owner.md#rules) | confirmed | user, 2026-05-02 |\n")
        entry = write_space("CONTEXT.md", """\
            ---
            ssot_format: 5
            language: en
            ---

            # Space

            ## Map

            - [Owner](owner.md)

            ## Invariants

            - [Finance rules](finance-rules.md) (`FIN-01`)
            """)
        self.git("init", "-q")
        self.commit("format 5 sharded")
        code, out = self.run_checker(entry)
        self.assertEqual(code, 0, out)
        # Linking the shard only under ## Map (not ## Invariants) must fail.
        write_space("CONTEXT.md", """\
            ---
            ssot_format: 5
            language: en
            ---

            # Space

            ## Map

            - [Owner](owner.md)
            - [Finance rules](finance-rules.md)

            ## Invariants

            None yet.
            """)
        code, out = self.run_checker(entry)
        self.assertEqual(code, 1, out)
        self.assertIn("unlinked invariants shard", out)
        self.assertIn("confirmed invariant FIN-01 was removed", out)

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root can read unreadable files")
    def test_scoped_owners_does_not_open_unselected_shard(self):
        self.sharded_setup(readme_invariants=(
            "- [Shipping invariants](invariants/shipping.md) (`SHP-01`)\n"
            "- [Webhooks invariants](invariants/webhooks.md) (`WHK-01`)\n"
        ))
        secret = os.path.join(self.ssot, "invariants/webhooks.md")
        os.chmod(secret, 0)
        try:
            code, out = self.run_checker(os.path.join(self.ssot, "README.md"),
                                         "--owners", "invariants/shipping.md", "architecture.md")
        finally:
            os.chmod(secret, 0o644)
        self.assertEqual(code, 0, out)
        self.assertNotIn("ERROR", out)
        self.assertNotIn("UNCHECKED", out)

    def test_gitignored_link_warns_while_tracked_ignored_pattern_passes(self):
        self.valid()
        self.git("init", "-q")
        with open(os.path.join(self.repo, ".gitignore"), "w", encoding="utf-8") as handle:
            handle.write("tmp/\n*.log\n")
        os.makedirs(os.path.join(self.repo, "tmp"))
        with open(os.path.join(self.repo, "tmp/verify.md"), "w", encoding="utf-8") as handle:
            handle.write("# Ephemeral\n")
        with open(os.path.join(self.repo, "tracked.log"), "w", encoding="utf-8") as handle:
            handle.write("kept\n")
        self.git("add", "-f", "tracked.log")
        self.write("architecture.md", ARCHITECTURE
                   + "\nSee [ephemeral](../tmp/verify.md), [dir](../tmp), and [tracked](../tracked.log).\n")
        self.commit("baseline")
        out = self.assert_clean()
        self.assertIn("link targets gitignored path", out)
        self.assertIn("../tmp/verify.md", out)
        self.assertIn("../tmp", out)
        self.assertNotIn("../tracked.log", out)
        # --owners scoped mode excludes git checks and stays clean without gitignore warnings.
        code, scoped_out = self.run_checker(os.path.join(self.ssot, "README.md"), "--owners", "architecture.md")
        self.assertEqual(code, 0, scoped_out)
        self.assertNotIn("gitignored", scoped_out)

    def test_large_inline_register_emits_nonblocking_shard_info_without_warn(self):
        rows = "\n".join(f"| INV-{n:03d} | product promise | Rule {n} | [R](architecture.md#failure-and-recovery) | candidate | tests |"
                         for n in range(1, 56))
        self.invariant_row(rows)
        out = self.assert_clean()
        self.assertIn("INFO", out)
        self.assertIn("optional topic shards", out)
        self.assertNotIn("WARN", out)

    def test_shard_with_invariants_heading_allows_helper_table_above(self):
        self.sharded_setup()
        self.write("invariants/shipping.md", textwrap.dedent("""\
            # Shipping invariants

            | Scope | Owner |
            |---|---|
            | Parcel pricing | `shipping.py` |

            ## Invariants

            | ID | Kind | Rule | Explained in | Status | Source |
            |---|---|---|---|---|---|
            | SHP-01 | product promise | Express keeps standard intact | [Retries](../architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |
            """))
        self.git("init", "-q")
        self.commit("shard with helper table")
        out = self.assert_clean()
        self.assertNotIn("WARN", out)
        # Mutating the confirmed rule under ## Invariants must still fail.
        self.write("invariants/shipping.md", textwrap.dedent("""\
            # Shipping invariants

            | Scope | Owner |
            |---|---|
            | Parcel pricing | `shipping.py` |

            ## Invariants

            | ID | Kind | Rule | Explained in | Status | Source |
            |---|---|---|---|---|---|
            | SHP-01 | product promise | Express weakens standard | [Retries](../architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |
            """))
        self.assert_error("confirmed invariant SHP-01 changed its rule")

    def test_drifted_instruction_block_emits_nonblocking_info_and_current_stays_quiet(self):
        self.valid()
        agents_path = os.path.join(self.repo, "AGENTS.md")
        claude_path = os.path.join(self.repo, "CLAUDE.md")
        with open(agents_path, "w", encoding="utf-8") as handle:
            handle.write("# Repo\n\n<!-- SSOT-SKILL:BEGIN -->\nOld stale instructions.\n<!-- SSOT-SKILL:END -->\n")
        os.symlink("AGENTS.md", claude_path)
        out = self.assert_clean()
        self.assertEqual(out.count("managed block differs from installed templates"), 1, out)
        self.assertIn("(legacy SSOT-SKILL markers)", out)
        self.assertNotIn("WARN", out)
        # Syncing to current template silences the INFO completely.
        tpl = os.path.join(os.path.dirname(CHECKER), "../../../ssot-bootstrap/assets/templates/en/adapter-thin.md")
        with open(tpl, encoding="utf-8") as handle:
            tpl_text = handle.read()
        begin = tpl_text.index("<!-- SSOT-CONTEXT:BEGIN -->")
        end = tpl_text.index("<!-- SSOT-CONTEXT:END -->") + len("<!-- SSOT-CONTEXT:END -->")
        with open(agents_path, "w", encoding="utf-8") as handle:
            handle.write("# Repo\n\n" + tpl_text[begin:end] + "\n")
        out = self.assert_clean()
        self.assertNotIn("managed block differs", out)
        # --owners mode must not read AGENTS.md at all.
        with open(agents_path, "w", encoding="utf-8") as handle:
            handle.write("<!-- SSOT-CONTEXT:BEGIN -->\nStale.\n<!-- SSOT-CONTEXT:END -->\n")
        code, scoped_out = self.run_checker(os.path.join(self.ssot, "README.md"), "--owners")
        self.assertEqual(code, 0, scoped_out)
        self.assertNotIn("managed block differs", scoped_out)

    def test_symlinked_nongit_format5_passes_while_escaping_symlinks_fail(self):
        with tempfile.TemporaryDirectory() as outer:
            vault = os.path.join(outer, "target", "space")
            os.makedirs(vault)
            with open(os.path.join(vault, "topic.md"), "w", encoding="utf-8") as handle:
                handle.write("# Topic\n\nLocal notes.\n")
            with open(os.path.join(vault, "INDEX.md"), "w", encoding="utf-8") as handle:
                handle.write(textwrap.dedent("""\
                    ---
                    ssot_format: 5
                    language: en
                    ---

                    # Personal Space

                    - [Topic](topic.md)

                    ## Invariants

                    None yet.
                    """))
            home = os.path.join(outer, "home")
            os.makedirs(home)
            alias = os.path.join(home, "notes")
            os.symlink(vault, alias)
            # Symlinked non-git Format-5 directory succeeds (absolute and relative).
            code, out = self.run_checker(os.path.join(alias, "INDEX.md"))
            self.assertEqual(code, 0, out)
            self.assertNotIn("ERROR", out)
            rel_proc = subprocess.run(
                [sys.executable, CHECKER, "notes/INDEX.md"],
                cwd=home, capture_output=True, text=True, check=False,
            )
            self.assertEqual(rel_proc.returncode, 0, rel_proc.stdout + rel_proc.stderr)

            # Escaping Format-5 file symlink pointing outside the space must fail.
            outside_f5 = os.path.join(outer, "outside_f5.md")
            with open(outside_f5, "w", encoding="utf-8") as handle:
                handle.write("---\nssot_format: 5\nlanguage: en\n---\n# Outside\n\n## Invariants\n\nNone.\n")
            os.symlink(outside_f5, os.path.join(vault, "ESCAPE.md"))
            code, out = self.run_checker(os.path.join(vault, "ESCAPE.md"))
            self.assertEqual(code, 1, out)
            self.assertIn("README must belong to the same repository", out)

            # Non-git Format-4 escaping directory symlink must still be rejected.
            ext_ssot = os.path.join(outer, "external_ssot")
            os.makedirs(ext_ssot)
            with open(os.path.join(ext_ssot, "README.md"), "w", encoding="utf-8") as handle:
                handle.write(README)
            proj = os.path.join(outer, "proj")
            os.makedirs(proj)
            os.symlink(ext_ssot, os.path.join(proj, "SSOT"))
            code, out = self.run_checker(os.path.join(proj, "SSOT"))
            self.assertEqual(code, 1, out)
            self.assertIn("README must belong to the same repository", out)

    def test_format5_gitignored_space_skips_noise_while_tracked_format5_warns(self):
        self.git("init", "-q")
        with open(os.path.join(self.repo, ".gitignore"), "w", encoding="utf-8") as handle:
            handle.write("private-space/\ntmp/\n")
        # 1. Untracked Format-5 space inside a gitignored folder gets 0 gitignore warnings.
        priv = os.path.join(self.repo, "private-space")
        os.makedirs(priv)
        with open(os.path.join(priv, "topic.md"), "w", encoding="utf-8") as handle:
            handle.write("# Topic\n\nPrivate note.\n")
        priv_entry = os.path.join(priv, "INDEX.md")
        with open(priv_entry, "w", encoding="utf-8") as handle:
            handle.write("---\nssot_format: 5\nlanguage: en\n---\n# Private\n\n- [Topic](topic.md)\n\n## Invariants\n\nNone.\n")
        # 2. Tracked Format-5 space inside the same Git repo linking to a gitignored file still warns.
        tracked = os.path.join(self.repo, "tracked-space")
        os.makedirs(os.path.join(tracked, "tmp"))
        with open(os.path.join(tracked, "tmp", "scratch.md"), "w", encoding="utf-8") as handle:
            handle.write("# Scratch\n")
        tracked_entry = os.path.join(tracked, "INDEX.md")
        with open(tracked_entry, "w", encoding="utf-8") as handle:
            handle.write("---\nssot_format: 5\nlanguage: en\n---\n# Tracked\n\n- [Scratch](tmp/scratch.md)\n\n## Invariants\n\nNone.\n")
        self.valid()
        self.commit("baseline")

        code, priv_out = self.run_checker(priv_entry)
        self.assertEqual(code, 0, priv_out)
        self.assertNotIn("gitignored", priv_out)

        code, tracked_out = self.run_checker(tracked_entry)
        self.assertEqual(code, 0, tracked_out)
        self.assertIn("link targets gitignored path", tracked_out)
        self.assertIn("tmp/scratch.md", tracked_out)

    def test_bold_invariant_ids_excluded_from_budget_and_inline_code_ref_ignored(self):
        rows = "\n".join(
            f"| **INV-{n:03d}** | product promise | {'Long contract text ' * 7} | [R](architecture.md#failure-and-recovery) | candidate | tests |"
            for n in range(1, 70)
        )
        self.invariant_row(rows)
        out = self.assert_clean()
        self.assertNotIn("reading budget", out)
        # Backticked reference-link syntax inside Explained in must not satisfy link requirement.
        self.invariant_row(
            "| INV-01 | product promise | Rule | `[fake][r]` | candidate | tests |\n\n[r]: architecture.md#failure-and-recovery"
        )
        self.assert_error("invariant INV-01 needs a link to where it is explained")

    def test_instruction_block_crlf_and_zh_ascii_parens_format5_parity(self):
        self.valid()
        agents_path = os.path.join(self.repo, "AGENTS.md")
        # 1. CRLF stale block emits updated installer guidance (not bare ./install.sh).
        with open(agents_path, "wb") as handle:
            handle.write(b"# Repo\r\n\r\n<!-- SSOT-CONTEXT:BEGIN -->\r\n## SSOT workflow\r\nStale.\r\n<!-- SSOT-CONTEXT:END -->\r\n")
        out = self.assert_clean()
        self.assertIn("managed block differs from installed templates", out)
        self.assertIn("SSOT-CONTEXT installer with --check-block / --sync-block", out)

        # 2. Synced CRLF block stays quiet.
        tpl = os.path.join(os.path.dirname(CHECKER), "../../../ssot-bootstrap/assets/templates/en/adapter-thin.md")
        with open(tpl, encoding="utf-8") as handle:
            tpl_text = handle.read()
        begin = tpl_text.index("<!-- SSOT-CONTEXT:BEGIN -->")
        end = tpl_text.index("<!-- SSOT-CONTEXT:END -->") + len("<!-- SSOT-CONTEXT:END -->")
        crlf_block = tpl_text[begin:end].replace("\n", "\r\n")
        with open(agents_path, "wb") as handle:
            handle.write(("# Repo\r\n\r\n" + crlf_block + "\r\n").encode("utf-8"))
        out = self.assert_clean()
        self.assertNotIn("managed block differs", out)

        # 3. ZH Format-5 block using ASCII parens around `ssot_format: 5` detects drift when stale and passes when synced.
        with open(agents_path, "w", encoding="utf-8") as handle:
            handle.write("<!-- SSOT-CONTEXT:BEGIN -->\n## 长期 context\n\n本空间通过 INDEX.md(`ssot_format: 5`) 管理。\n<!-- SSOT-CONTEXT:END -->\n")
        out = self.assert_clean()
        self.assertIn("managed block differs from installed templates", out)
        zh_f5 = os.path.join(os.path.dirname(CHECKER), "../../../ssot-bootstrap/assets/templates/zh/context-adapter.md")
        with open(zh_f5, encoding="utf-8") as handle:
            zh_text = handle.read()
        zb = zh_text.index("<!-- SSOT-CONTEXT:BEGIN -->")
        ze = zh_text.index("<!-- SSOT-CONTEXT:END -->") + len("<!-- SSOT-CONTEXT:END -->")
        with open(agents_path, "w", encoding="utf-8") as handle:
            handle.write(zh_text[zb:ze].replace("ENTRY", "INDEX.md") + "\n")
        out = self.assert_clean()
        self.assertNotIn("managed block differs", out)

    def test_inline_triple_backtick_at_line_start_does_not_swallow_following_markdown(self):
        self.valid()
        # Inline ```token``` at start of line in an area doc must not hide a broken link below it.
        self.write("architecture.md", ARCHITECTURE + "\n```--strict``` enables strict mode.\n\nSee [Missing](nope.md).\n")
        self.assert_error("broken link: nope.md")
        # Same in README.md.
        self.valid()
        self.write("README.md", README + "\n```--strict``` enables strict mode.\n\nSee [Missing](nope.md).\n")
        self.assert_error("broken link: nope.md")
        # Tilde fence with backticks in info string still opens a real fence per CommonMark §4.5.
        self.valid()
        self.write("architecture.md", ARCHITECTURE + "\n~~~foo ```bar```\n[ignored](nope.md)\n~~~\n")
        self.assert_clean()

    def test_pipe_in_invariants_bullet_and_shard_context_table_preserve_confirmed_guard(self):
        self.sharded_setup(
            readme_invariants="- [Shipping invariants](invariants/shipping.md) — checkout | refunds | idempotency\n"
                              "- [Webhooks invariants](invariants/webhooks.md) — signing | retries\n",
        )
        # Put a 2-col helper context table (even using a common header word like Status)
        # before the 6-col invariants table in a shard without ## Invariants heading.
        self.write("invariants/shipping.md", textwrap.dedent("""\
            # Shipping invariants

            | Service | Status |
            |---|---|
            | Parcel pricing | active |

            | ID | Kind | Rule | Explained in | Status | Source |
            |---|---|---|---|---|---|
            | SHP-01 | architecture invariant | Never drop parcel manifests | [Retries](../architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |
            """))
        self.git("init", "-q")
        self.commit("sharded bullets with pipes and shard helper table")
        out = self.assert_clean()
        self.assertNotIn("WARN", out)

        # Mutating confirmed SHP-01 inside the shard linked by a pipe-containing bullet must still fail.
        self.write("invariants/shipping.md", textwrap.dedent("""\
            # Shipping invariants

            | Service | Owner |
            |---|---|
            | Parcel pricing | `shipping.py` |

            | ID | Kind | Rule | Explained in | Status | Source |
            |---|---|---|---|---|---|
            | SHP-01 | architecture invariant | Drop manifests freely | [Retries](../architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |
            """))
        self.assert_error("confirmed invariant SHP-01 changed its rule")

        # Malformed 5-col invariants table after the helper table must still fail.
        self.write("invariants/shipping.md", textwrap.dedent("""\
            # Shipping invariants

            | Service | Owner |
            |---|---|
            | Parcel pricing | `shipping.py` |

            | ID | Kind | Rule | Status | Source |
            |---|---|---|---|---|
            | SHP-01 | architecture invariant | Never drop parcel manifests | confirmed | user, 2026-05-02 |
            """))
        self.assert_error("needs 6 columns")

    def test_symlinked_repo_path_still_warns_on_relative_removed_path_mentions(self):
        self.valid()
        os.makedirs(os.path.join(self.repo, "src"))
        with open(os.path.join(self.repo, "src", "old.py"), "w", encoding="utf-8") as handle:
            handle.write("x = 1\n")
        self.write("architecture.md", ARCHITECTURE + "\nUses `../src/old.py`.\n")
        self.git("init", "-q")
        self.commit("add old.py")
        self.git("rm", "-q", "src/old.py")
        self.commit("remove old.py")
        with tempfile.TemporaryDirectory() as outer:
            alias = os.path.join(outer, "repo-alias")
            os.symlink(self.repo, alias)
            code, out = self.run_checker(os.path.join(alias, "SSOT"))
            self.assertEqual(code, 0, out)
            self.assertIn("`src/old.py` was removed", out)

    def test_gitignored_symlink_to_tracked_file_warns(self):
        self.valid()
        with open(os.path.join(self.repo, ".gitignore"), "w", encoding="utf-8") as handle:
            handle.write("ignored_link.md\nignored_dir\n")
        with open(os.path.join(self.repo, "real_tracked.md"), "w", encoding="utf-8") as handle:
            handle.write("# Tracked\n")
        os.makedirs(os.path.join(self.repo, "real_docs"))
        with open(os.path.join(self.repo, "real_docs", "guide.md"), "w", encoding="utf-8") as handle:
            handle.write("# Guide\n")
        os.symlink("real_tracked.md", os.path.join(self.repo, "ignored_link.md"))
        os.symlink("real_docs", os.path.join(self.repo, "ignored_dir"))
        self.write("README.md", README + "\n- [Ignored symlink](../ignored_link.md)\n- [Ignored dir symlink](../ignored_dir/guide.md)\n")
        self.git("init", "-q")
        self.git("add", ".gitignore", "real_tracked.md", "real_docs", "SSOT")
        self.git("commit", "-q", "-m", "baseline")
        out = self.assert_clean()
        self.assertEqual(out.count("link targets gitignored path"), 2, out)
        self.assertIn("../ignored_link.md", out)
        self.assertIn("../ignored_dir/guide.md", out)

    def test_instruction_block_drift_covers_cursor_windsurf_copilot_and_flattened_lang_mismatch(self):
        self.valid()
        stale = "<!-- SSOT-CONTEXT:BEGIN -->\n## SSOT workflow\nStale.\n<!-- SSOT-CONTEXT:END -->\n"
        for rel in (".cursor/rules/ssot.mdc", ".windsurf/rules/ssot.md", ".github/copilot-instructions.md"):
            full = os.path.join(self.repo, rel)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "w", encoding="utf-8") as handle:
                handle.write(stale)
        out = self.assert_clean()
        self.assertEqual(out.count("managed block differs from installed templates"), 3, out)
        for rel in (".cursor/rules/ssot.mdc", ".windsurf/rules/ssot.md", ".github/copilot-instructions.md"):
            self.assertIn(rel, out)

        # Flattened single-language EN install inspecting a ZH managed block emits a clear INFO note.
        import shutil
        with tempfile.TemporaryDirectory() as inst:
            chk_dst = os.path.join(inst, "ssot-doctor/assets/scripts/ssot-check.py")
            tpl_dst = os.path.join(inst, "ssot-bootstrap/assets/templates/adapter-thin.md")
            os.makedirs(os.path.dirname(chk_dst), exist_ok=True)
            os.makedirs(os.path.dirname(tpl_dst), exist_ok=True)
            shutil.copy2(CHECKER, chk_dst)
            shutil.copy2(os.path.join(os.path.dirname(CHECKER), "../../../ssot-bootstrap/assets/templates/en/adapter-thin.md"), tpl_dst)
            with open(os.path.join(self.repo, "AGENTS.md"), "w", encoding="utf-8") as handle:
                handle.write("<!-- SSOT-CONTEXT:BEGIN -->\n## SSOT 工作流\n旧版保护规则。\n<!-- SSOT-CONTEXT:END -->\n")
            proc = subprocess.run([sys.executable, chk_dst, self.ssot], capture_output=True, text=True, check=False)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("managed block is zh while installed templates are en", proc.stdout)

    def test_sharded_external_owner_linked_only_from_shard_is_checked_and_owners_stays_scoped(self):
        self.sharded_setup(
            shipping_rows="| SHP-01 | architecture invariant | Never drop parcel manifests | [Spec](../../docs/shard-only.md#details) | confirmed | user, 2026-05-02 |\n",
        )
        os.makedirs(os.path.join(self.repo, "src"))
        os.makedirs(os.path.join(self.repo, "tmp"))
        with open(os.path.join(self.repo, ".gitignore"), "w", encoding="utf-8") as handle:
            handle.write("tmp/\n")
        with open(os.path.join(self.repo, "src", "old.py"), "w", encoding="utf-8") as handle:
            handle.write("x = 1\n")
        with open(os.path.join(self.repo, "tmp", "proof.txt"), "w", encoding="utf-8") as handle:
            handle.write("ok\n")
        self.write("../docs/shard-only.md", textwrap.dedent("""\
            # Shard Only Spec

            ## Details

            Mentions `src/old.py`, [Proof](../tmp/proof.txt), and [Dead](missing.md).
            """))
        self.git("init", "-q")
        self.commit("baseline")
        self.git("rm", "-q", "src/old.py")
        self.commit("remove old.py")
        # Full run must scan docs/shard-only.md (1-hop from shard) and surface all three findings.
        out = self.assert_error("broken link: missing.md")
        self.assertIn("docs/shard-only.md", out)
        self.assertIn("`src/old.py` was removed", out)
        self.assertIn("link targets gitignored path", out)
        # --owners mode must stay strictly scoped and never open unselected shard-only external owners.
        shard_owner = os.path.join(self.repo, "docs", "shard-only.md")
        observer = textwrap.dedent("""
            import runpy, sys
            watched, checker, *args = sys.argv[1:]
            def audit(event, arguments):
                if event == "open" and arguments[0] == watched:
                    print("OPENED UNSELECTED", file=sys.stderr)
            sys.addaudithook(audit)
            sys.argv = [checker, *args]
            runpy.run_path(checker, run_name="__main__")
        """)
        scoped = subprocess.run(
            [sys.executable, "-c", observer, shard_owner, CHECKER,
             os.path.join(self.ssot, "README.md"), "--owners", "invariants/shipping.md"],
            cwd=self.repo, text=True, capture_output=True, check=False,
        )
        self.assertEqual(scoped.returncode, 0, scoped.stdout + scoped.stderr)
        self.assertNotIn("OPENED UNSELECTED", scoped.stderr)
        # Format 5 shard-only local owner is also scanned 1-hop in non-scoped mode.
        space = os.path.join(self.repo, "f5space")
        os.makedirs(space)
        with open(os.path.join(space, "shard-only.md"), "w", encoding="utf-8") as handle:
            handle.write("# Spec\n\n## Rules\n\n[Dead](nope.md)\n")
        with open(os.path.join(space, "rules.md"), "w", encoding="utf-8") as handle:
            handle.write("---\nssot_register: shard\n---\n\n# Rules\n\n"
                         "| ID | Kind | Rule | Explained in | Status | Source |\n|---|---|---|---|---|---|\n"
                         "| F5-01 | process rule | Keep receipts | [Rules](shard-only.md#rules) | confirmed | user, 2026-05-02 |\n")
        entry = os.path.join(space, "CONTEXT.md")
        with open(entry, "w", encoding="utf-8") as handle:
            handle.write("---\nssot_format: 5\nlanguage: en\n---\n\n# Space\n\n## Invariants\n\n- [Rules](rules.md)\n")
        code, f5_out = self.run_checker(entry)
        self.assertEqual(code, 1, f5_out)
        self.assertIn("broken link: nope.md", f5_out)

    def test_multi_section_shard_validates_and_protects_every_section(self):
        self.sharded_setup()
        multi_ok = textwrap.dedent("""\
            # Dispatch & Execution

            | Scope | Owner |
            |---|---|
            | Dispatch | `host/dispatch.js` |

            ## Invariants: Admission

            | ID | Kind | Rule | Explained in | Status | Source |
            |---|---|---|---|---|---|
            | DISP-01 | architecture invariant | Never drop admission | [Retries](../architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |

            ## Invariants: Concurrency

            | ID | Kind | Rule | Explained in | Status | Source |
            |---|---|---|---|---|---|
            | DISP-02 | architecture invariant | Never double-run | [Retries](../architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |

            ## 并发与恢复

            | ID | 类型 | 规则 | 解释位置 | 状态 | 来源 |
            |---|---|---|---|---|---|
            | DISP-03 | 架构不变量 | 恢复不丢进度 | [Retries](../architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |
            """)
        self.write("invariants/shipping.md", multi_ok)
        self.git("init", "-q")
        self.commit("multi-section shard baseline")
        out = self.assert_clean()
        self.assertNotIn("WARN", out)
        # Tampering confirmed row under second ## Invariants section must fail.
        self.write("invariants/shipping.md", multi_ok.replace("Never double-run", "Allow double-run"))
        self.assert_error("confirmed invariant DISP-02 changed its rule")
        # Tampering confirmed row under later non-Invariants ## section must also fail.
        self.write("invariants/shipping.md", multi_ok.replace("恢复不丢进度", "允许丢进度"))
        self.assert_error("confirmed invariant DISP-03 changed its rule")
        # Structural errors under later section must also be caught.
        self.write("invariants/shipping.md", multi_ok.replace(
            "| [Retries](../architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |",
            "| no-link | bogus |  |",
        ))
        err_out = self.assert_error("status 'bogus' must be confirmed, candidate, or retired")
        self.assertIn("needs a link", err_out)

    def test_missing_gitignored_link_reports_worktree_diagnostic_and_existing_warns(self):
        self.valid()
        self.git("init", "-q")
        with open(os.path.join(self.repo, ".gitignore"), "w", encoding="utf-8") as handle:
            handle.write("verification/\nprivate-space/\n")
        self.write("architecture.md", ARCHITECTURE
                   + "\nSee [proof](../verification/run1/proof.json) and [real-missing](../docs/missing.md).\n")
        self.commit("baseline")
        # Missing gitignored target (as in a fresh worktree/clone) gets worktree-aware ERROR;
        # genuinely missing non-ignored target stays plain broken link ERROR.
        out = self.assert_error("broken link to gitignored path (absent in worktree/clone")
        self.assertIn("../verification/run1/proof.json", out)
        self.assertIn("ERROR architecture.md:7  broken link: ../docs/missing.md", out)
        # Once the gitignored file exists locally and the real missing link is removed, WARN mentions worktrees/clones.
        os.makedirs(os.path.join(self.repo, "verification", "run1"))
        with open(os.path.join(self.repo, "verification", "run1", "proof.json"), "w", encoding="utf-8") as handle:
            handle.write("{}\n")
        self.write("architecture.md", ARCHITECTURE + "\nSee [proof](../verification/run1/proof.json).\n")
        clean_out = self.assert_clean()
        self.assertIn("link targets gitignored path (breaks in worktrees/clones or after cleanup)", clean_out)
        # Inside an entirely gitignored Format-5 space, missing links stay plain broken link (not worktree noise).
        priv = os.path.join(self.repo, "private-space")
        os.makedirs(priv)
        entry = os.path.join(priv, "INDEX.md")
        with open(entry, "w", encoding="utf-8") as handle:
            handle.write("---\nssot_format: 5\nlanguage: en\n---\n\n# Private\n\n[Dead](nope.md)\n\n## Invariants\n\nNone.\n")
        code, priv_out = self.run_checker(entry)
        self.assertEqual(code, 1, priv_out)
        self.assertIn("broken link: nope.md", priv_out)
        self.assertNotIn("absent in worktree/clone", priv_out)

    def test_truncation_producer_info_signals_for_entry_shard_and_long_rows(self):
        # 1. Total README > 16,000 chars (prose < 8,000) + single row > 500 chars -> INFO only, zero WARN.
        long_rule = "Preserve exact ordering and idempotency across retries " * 9
        rows = [f"| INV-001 | product promise | {long_rule} | [R](architecture.md#failure-and-recovery) | candidate | tests |"]
        rows.extend(
            f"| INV-{n:03d} | product promise | Concise invariant constraint number {n:03d} with context | [R](architecture.md#failure-and-recovery) | candidate | tests |"
            for n in range(2, 130)
        )
        self.invariant_row("\n".join(rows))
        out = self.assert_clean()
        self.assertNotIn("WARN", out)
        self.assertIn("total README.md size is", out)
        self.assertIn("exceed 500 characters (longest: INV-001", out)
        # 2. Oversized shard (> 50 rows and > 16,000 chars) + long row -> INFO only, zero WARN.
        shard_rows = [f"| SHP-001 | product promise | {long_rule} | [R](../architecture.md#failure-and-recovery) | candidate | tests |"]
        shard_rows.extend(
            f"| SHP-{n:03d} | product promise | Concise shipping invariant number {n:03d} for checkout | [R](../architecture.md#failure-and-recovery) | candidate | tests |"
            for n in range(2, 55)
        )
        self.sharded_setup(shipping_rows="\n".join(shard_rows) + "\n")
        out_shard = self.assert_clean()
        self.assertNotIn("WARN", out_shard)
        self.assertIn("invariants/shipping.md  invariants shard is", out_shard)
        self.assertIn("exceed 500 characters (longest: SHP-001", out_shard)

    def test_reviewed_through_lag_info_respects_threshold_since_and_shallow(self):
        self.valid()
        self.git("init", "-q")
        base = self.commit("initial")
        self.write("README.md", README.replace("language: en\n", f"language: en\nreviewed_through: {base}\n"))
        self.commit("set reviewed_through")
        for n in range(9):
            self.git("commit", "--allow-empty", "-q", "-m", f"step {n}")
        # 10 commits behind (< 100) stays quiet.
        out_small = self.assert_clean()
        self.assertNotIn("commits behind HEAD", out_small)
        for n in range(90):
            self.git("commit", "--allow-empty", "-q", "-m", f"more {n}")
        # 100 commits behind emits non-blocking INFO without WARN.
        out_lag = self.assert_clean()
        self.assertIn(f"INFO  README.md:1  reviewed_through {base} is 100 commits behind HEAD", out_lag)
        self.assertNotIn("WARN", out_lag)
        # Suppressed when --since is given.
        code, out_since = self.run_checker(self.ssot, "--since", "HEAD")
        self.assertEqual(code, 0, out_since)
        self.assertNotIn("commits behind HEAD", out_since)
        # Skipped safely on shallow clones even when reviewed_through is present.
        with tempfile.TemporaryDirectory() as outer:
            shallow_clone = os.path.join(outer, "shallow")
            subprocess.run(["git", "clone", "-q", "--depth", "101", f"file://{self.repo}", shallow_clone], check=True)
            proc = subprocess.run([sys.executable, CHECKER, os.path.join(shallow_clone, "SSOT")],
                                  capture_output=True, text=True, check=False)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertNotIn("commits behind HEAD", proc.stdout)

    def test_format5_english_block_with_cjk_entry_path_and_line_anchor_bounds(self):
        self.valid()
        en_f5 = os.path.join(os.path.dirname(CHECKER), "../../../ssot-bootstrap/assets/templates/en/context-adapter.md")
        with open(en_f5, encoding="utf-8") as handle:
            tpl = handle.read()
        begin = tpl.index("<!-- SSOT-CONTEXT:BEGIN -->")
        end = tpl.index("<!-- SSOT-CONTEXT:END -->") + len("<!-- SSOT-CONTEXT:END -->")
        block = tpl[begin:end].replace("ENTRY", "个人空间/README.md")
        with open(os.path.join(self.repo, "AGENTS.md"), "w", encoding="utf-8") as handle:
            handle.write("# Space\n\n" + block + "\n")
        # Must classify as English (not Chinese because of '空间' inside ENTRY path) and stay quiet.
        out = self.assert_clean()
        self.assertNotIn("managed block differs", out)
        # Line anchor bounds: #L0, reversed range #L4-L2, and past-EOF end line #L1-L999 must all ERROR.
        self.write("notes.md", "# Notes\n\n[zero](architecture.md#L0) [rev](architecture.md#L4-L2) "
                   "[past](architecture.md#L1-L999) [ok](architecture.md#L1-L3)\n")
        err_out = self.assert_error("line anchor past end of file: architecture.md#L1-L999")
        self.assertIn("invalid line anchor: architecture.md#L0", err_out)
        self.assertIn("invalid line anchor: architecture.md#L4-L2", err_out)
        self.assertIn("line anchors drift when the file changes; link a heading: architecture.md#L1-L3", err_out)

    def test_dated_history_pileup_and_inline_retired_info_and_cold_retired_shard_protection(self):
        # 1. Oversized owner with >=5 dated headings gets enriched chronological-consolidation hint;
        #    small owner with >=5 dated headings stays quiet; oversized owner with <5 keeps standard hint.
        self.valid()
        dated_small = "# Design\n\n" + "\n\n".join(f"## 2026-10-{d:02d} Note {d}\n\nShort note {d}." for d in range(1, 7)) + "\n"
        dated_big = "# Design\n\n" + "\n\n".join(
            f"## 2026-10-{d:02d} Revision {d}\n\n" + ("Superseded narrative detail for revision history. " * 70)
            for d in range(1, 7)
        ) + "\n"
        plain_big = "# Spec\n\n## Overview\n\n" + ("Current architecture explanation without dated pileup. " * 340) + "\n"
        self.write("README.md", README.replace(
            "- [Architecture](architecture.md)",
            "- [Architecture](architecture.md)\n- [SmallDated](small-dated.md)\n- [BigDated](../docs/big-dated.md)\n- [PlainBig](../docs/plain-big.md)",
        ))
        self.write("small-dated.md", dated_small)
        self.write("../docs/big-dated.md", dated_big)
        self.write("../docs/plain-big.md", plain_big)
        out_hist = self.assert_clean()
        self.assertNotIn("small-dated.md", out_hist)
        self.assertIn("big-dated.md", out_hist)
        self.assertIn("and has 6 dated headings; consolidate current behavior and move superseded history to a cold archive", out_hist)
        self.assertIn("plain-big.md", out_hist)
        self.assertIn("plain-big.md  ", out_hist)
        self.assertNotIn("plain-big.md  1", out_hist.split("dated headings")[0][-40:])

        # 2. Active register with >=3 inline retired rows emits non-blocking INFO; <3 stays quiet.
        self.valid()
        rows_2 = "\n".join([
            "| INV-01 | product promise | A retry never charges twice | [Retries](architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |",
            "| INV-02 | product promise | Old rule 2 | [Retries](architecture.md#failure-and-recovery) | retired | user, 2026-06-01 |",
            "| INV-03 | product promise | Old rule 3 | [Retries](architecture.md#failure-and-recovery) | retired | user, 2026-06-02 |",
        ])
        self.invariant_row(rows_2)
        self.assertNotIn("retired invariant row(s) inline", self.assert_clean())
        rows_3 = rows_2 + "\n| INV-04 | product promise | Old rule 4 | [Retries](architecture.md#failure-and-recovery) | retired | user, 2026-06-03 |"
        self.invariant_row(rows_3)
        out_ret = self.assert_clean()
        self.assertIn("3 retired invariant row(s) inline in README.md", out_ret)
        self.assertNotIn("WARN", out_ret)

        # 3. Cold invariants/retired.md shard stays quiet on inline-retired INFO and preserves Git confirmed tamper checks.
        self.valid()
        base_rows = "\n".join([
            "| INV-01 | product promise | A retry never charges twice | [Retries](architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |",
            "| INV-02 | product promise | Keep legacy CSV export | [Retries](architecture.md#failure-and-recovery) | confirmed | user, 2026-05-03 |",
            "| INV-03 | product promise | Old rule 3 | [Retries](architecture.md#failure-and-recovery) | retired | user, 2026-06-01 |",
        ])
        self.invariant_row(base_rows)
        self.git("init", "-q")
        self.commit("base before retiring to cold shard")
        # Retiring INV-02 with a new dated source AND moving both INV-02 and INV-03 to invariants/retired.md passes cleanly.
        self.write("README.md", README.replace(
            "| INV-01 | product promise | A retry never charges twice | [Retries](architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |",
            "| INV-01 | product promise | A retry never charges twice | [Retries](architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |\n\n- [Retired invariants](invariants/retired.md)",
        ))
        retired_shard = textwrap.dedent("""\
            # Retired Invariants

            | ID | Kind | Rule | Explained in | Status | Source |
            |---|---|---|---|---|---|
            | INV-02 | product promise | Keep legacy CSV export | [Retries](../architecture.md#failure-and-recovery) | retired | user, 2026-05-03; retired 2026-11-26 |
            | INV-03 | product promise | Old rule 3 | [Retries](../architecture.md#failure-and-recovery) | retired | user, 2026-06-01 |
            | INV-04 | product promise | Old rule 4 | [Retries](../architecture.md#failure-and-recovery) | retired | user, 2026-06-02 |
            | INV-05 | product promise | Old rule 5 | [Retries](../architecture.md#failure-and-recovery) | retired | user, 2026-06-03 |
            """)
        self.write("invariants/retired.md", retired_shard)
        out_ok = self.assert_clean()
        self.assertIn("confirmed invariant(s) INV-02 changed", out_ok)
        self.assertNotIn("retired invariant row(s) inline", out_ok)
        # Moving confirmed INV-02 to retired.md as retired WITHOUT a newly dated source MUST FAIL.
        self.write("invariants/retired.md", retired_shard.replace("user, 2026-05-03; retired 2026-11-26", "user, 2026-05-03"))
        self.assert_error("confirmed invariant INV-02 changed its status")
        # Duplicate ID between README.md and invariants/retired.md MUST FAIL.
        self.write("invariants/retired.md", retired_shard + "| INV-01 | product promise | Dup | [Retries](../architecture.md#failure-and-recovery) | retired | user, 2026-11-26 |\n")
        self.assert_error("duplicate invariant ID INV-01")

    def test_cold_archive_and_retired_shard_exemptions_and_64k_truncation(self):
        # 1. Legitimate cold archives (>16k chars, >=5 dated headings) must emit zero warm-bloat WARN/INFO
        #    and zero compaction candidates, while still catching broken links inside cold archives.
        self.valid()
        big_history = "# Archived History\n\n" + "\n\n".join(
            f"## 2026-08-{d:02d} Revision {d}\n\n" + ("Preserved superseded rationale and verbatim quote. " * 70)
            for d in range(1, 8)
        ) + "\n"
        self.write("decisions/0002-ui-history.md", big_history)
        self.write("research/bench-notes.md", big_history)
        self.write("archive/2025.md", big_history)
        self.write("auth-history.md", big_history)
        self.write("custom-cold.md", "---\nssot_tier: cold\n---\n\n" + big_history)
        out = self.assert_clean()
        self.assertNotIn("WARN", out)
        self.assertNotIn("reading budget", out)
        self.assertNotIn("compaction candidates", out)
        # Broken link inside a cold archive must still fail.
        self.write("decisions/0002-ui-history.md", big_history + "\nSee [Broken](missing.md).\n")
        self.assert_error("broken link: missing.md")
        self.write("decisions/0002-ui-history.md", big_history)

        # 2. Cold retired shards (>50 rows, >16k chars, >500-char rows) stay exempt from active shard nags,
        #    and emit pure truncation INFO only past 64,000 chars.
        long_rule = "Preserved historical invariant wording for archived reference " * 9
        retired_rows = "\n".join(
            f"| RET-{n:03d} | product promise | {long_rule} | [R](../architecture.md#failure-and-recovery) | retired | user, 2026-01-01 |"
            for n in range(1, 56)
        ) + "\n"
        self.sharded_setup(
            readme_invariants="- [Shipping](invariants/shipping.md)\n- [Webhooks](invariants/webhooks.md)\n- [Retired](invariants/retired.md)\n- [Old custom](invariants/old-custom.md)\n",
        )
        self.write("invariants/retired.md",
                   "# Retired Invariants\n\n| ID | Kind | Rule | Explained in | Status | Source |\n|---|---|---|---|---|---|\n" + retired_rows)
        self.write("invariants/old-custom.md",
                   "---\nssot_tier: cold\n---\n\n# Old Custom\n\n| ID | Kind | Rule | Explained in | Status | Source |\n|---|---|---|---|---|---|\n"
                   + retired_rows.replace("RET-", "OLD-"))
        out_cold_shards = self.assert_clean()
        self.assertNotIn("WARN", out_cold_shards)
        self.assertNotIn("exceed 500 characters", out_cold_shards)
        self.assertNotIn("retired invariant row(s) inline", out_cold_shards)
        self.assertNotIn("invariants shard is", out_cold_shards)
        self.assertNotIn("compaction candidates", out_cold_shards)
        # Pushing a cold retired shard past 64,000 chars triggers pure truncation INFO.
        huge_retired = "\n".join(
            f"| RET-{n:03d} | product promise | {long_rule} | [R](../architecture.md#failure-and-recovery) | retired | user, 2026-01-01 |"
            for n in range(1, 130)
        ) + "\n"
        self.write("invariants/retired.md",
                   "# Retired Invariants\n\n| ID | Kind | Rule | Explained in | Status | Source |\n|---|---|---|---|---|---|\n" + huge_retired)
        out_huge = self.assert_clean()
        self.assertNotIn("WARN", out_huge)
        self.assertIn("cold retired shard is", out_huge)
        self.assertIn("compaction candidates (1): invariants/retired.md", out_huge)

        # 3. Entry README with 3/3 retired rows is NOT misclassified as a cold shard.
        import shutil
        shutil.rmtree(os.path.join(self.ssot, "invariants"))
        self.valid()
        only_retired = "\n".join(
            f"| INV-{n:02d} | product promise | Old rule {n} | [R](architecture.md#failure-and-recovery) | retired | user, 2026-06-0{n} |"
            for n in range(1, 4)
        )
        self.invariant_row(only_retired)
        out_entry_ret = self.assert_clean()
        self.assertIn("3 retired invariant row(s) inline in README.md", out_entry_ret)

    def test_intra_file_cold_tail_exemptions_inverted_layering_and_32k_offload(self):
        # 1. Valid trailing cold tails (EN heading, ZH heading with ASCII/full-width parens, HTML marker)
        #    keep warm_chars/dated/checkboxes above the boundary clean while checking links below.
        cold_body = "\n\n".join(
            f"### 2026-09-{d:02d} Superseded trial {d}\n\n" + ("Superseded log detail preserved for traceability. " * 70)
            + "\n\n- [x] Old done task A\n- [x] Old done task B\n"
            for d in range(1, 7)
        )
        for label, boundary in (
            ("en-heading", "## History (cold)"),
            ("en-archive", "## archive (cold)"),
            ("zh-full", "## 历史记录（冷读）"),
            ("zh-ascii", "## 历史归档(冷读)"),
            ("html-marker", "<!-- ssot:cold -->\n\n## Superseded Experiments"),
        ):
            with self.subTest(boundary=label):
                self.valid()
                doc_text = "# Policy\n\n## Current behavior\n\nActive governing rule stays concise.\n\n" + boundary + "\n\n" + cold_body + "\n"
                self.write("policy.md", doc_text)
                out = self.assert_clean()
                self.assertNotIn("WARN", out)
                self.assertNotIn("reading budget", out)
                self.assertNotIn("completed checklist", out)
                self.assertNotIn("compaction candidates", out)
        # Broken link inside the cold tail MUST still ERROR.
        self.valid()
        self.write("policy.md", "# Policy\n\n## Current\n\nShort.\n\n## History (cold)\n\nSee [Missing](nope.md).\n")
        self.assert_error("broken link: nope.md")
        # <!-- ssot:cold --> inside a fenced code block or inline code span must NOT exempt bloated warm text below it.
        self.valid()
        self.write("policy.md",
                   "# Policy\n\n```md\n<!-- ssot:cold -->\n```\n\nAlso `<!-- ssot:cold -->` inline.\n\n"
                   + ("Warm active prose that should still count toward budget. " * 320) + "\n")
        out_fenced = self.assert_clean()
        self.assertIn("WARN  policy.md", out_fenced)
        self.assertIn("16000-character reading budget", out_fenced)

        # 2. Inverted layering (>1,000 chars of non-cold ## sections below cold boundary) triggers INFO.
        for label, body in (
            ("heading", "# Policy\n\n## History (cold)\n\n### 2026-01-01 Old\n\nOld text.\n\n## Current behavior\n\n" + ("Active rule detail. " * 70) + "\n"),
            ("marker", "# Policy\n\n<!-- ssot:cold -->\n\n## Old trials\n\nOld text.\n\n## Current behavior\n\n" + ("Active rule detail. " * 70) + "\n"),
        ):
            with self.subTest(inverted=label):
                self.valid()
                self.write("policy.md", body)
                out_inv = self.assert_clean()
                self.assertNotIn("WARN", out_inv)
                self.assertIn("cold section starts above", out_inv)
                self.assertIn("compaction candidates (1): policy.md", out_inv)

        # 3. Valid cold tail whose total file size exceeds 32,000 chars emits offload INFO.
        self.valid()
        huge_tail = "# Policy\n\n## Current\n\nShort active spec.\n\n## History (cold)\n\n" + ("Archived verbatim quote and trial context. " * 800) + "\n"
        self.write("policy.md", huge_tail)
        out_32k = self.assert_clean()
        self.assertNotIn("WARN", out_32k)
        self.assertIn("including its cold tail (>32000)", out_32k)
        self.assertIn("compaction candidates (1): policy.md", out_32k)

    def test_html_comments_stripped_from_budget_and_entry_section_bloat(self):
        # 1. HTML comments (such as <!-- ssot-source:... -->) do not inflate warm budget; fenced code still counts.
        self.valid()
        comments = "\n".join(f"<!-- ssot-source:thread-{n:03d} sha256=deadbeef -->" for n in range(150))
        self.write("architecture.md", ARCHITECTURE + "\n" + comments + "\n" + ("Warm prose. " * 900) + "\n")
        out_comments = self.assert_clean()
        self.assertNotIn("WARN", out_comments)
        self.assertNotIn("reading budget", out_comments)
        self.write("architecture.md", ARCHITECTURE + "\n```python\n" + ("x = 'code dump inside fence'\n" * 650) + "```\n")
        out_fence_dump = self.assert_clean()
        self.assertIn("WARN  architecture.md", out_fence_dump)
        self.assertIn("16000-character reading budget", out_fence_dump)

        # 2. Entry prose >8k with >=5 dated headings emits dated-consolidation WARN and names largest non-Invariants section.
        self.valid()
        dated_entry = README + "\n\n## Activity log\n\n" + "\n\n".join(
            f"### 2026-10-{d:02d} Update {d}\n\n" + ("Chronological log pasted into entry README. " * 40)
            for d in range(1, 7)
        ) + "\n"
        self.write("README.md", dated_entry)
        out_dated_entry = self.assert_clean()
        self.assertIn("WARN  README.md", out_dated_entry)
        self.assertIn("and has 6 dated headings; largest section: ## Activity log", out_dated_entry)
        self.assertIn("entry section '## Activity log' is", out_dated_entry)

        # 3. Entry <=8k total with a single >4k non-core section emits INFO; >4k core section (## Task routes) stays quiet.
        self.valid()
        self.write("README.md", README.replace(
            "None yet.",
            "Open item detail requiring follow-up decision. " * 95,
        ))
        out_oq = self.assert_clean()
        self.assertNotIn("WARN", out_oq)
        self.assertIn("entry section '## Open questions' is", out_oq)
        self.assertIn("compaction candidates (1): README.md", out_oq)
        self.valid()
        self.write("README.md", README.replace(
            "## Map",
            "## Task routes\n\n" + ("Route signal detail pointing to architecture owner. " * 85) + "\n\n## Map",
        ))
        out_routes = self.assert_clean()
        self.assertNotIn("WARN", out_routes)
        self.assertNotIn("entry section", out_routes)
        self.assertNotIn("compaction candidates", out_routes)

    def test_early_chronological_warm_doc_mega_doc_h2_and_format5_shard_hint(self):
        # 1. Warm doc 8k..16k with >=5 dated headings emits non-blocking INFO; <8k stays quiet.
        self.valid()
        mid_dated = "# Sync Engine\n\n" + "\n\n".join(
            f"## 2026-11-{d:02d} Decision {d}\n\n" + ("Chronological update piling up in warm owner. " * 38)
            for d in range(1, 7)
        ) + "\n"
        self.assertGreater(len(mid_dated), 8000)
        self.assertLess(len(mid_dated), 16000)
        self.write("sync.md", mid_dated)
        out_mid = self.assert_clean()
        self.assertNotIn("WARN", out_mid)
        self.assertIn("INFO  sync.md", out_mid)
        self.assertIn("with 6 dated headings; consolidate current state", out_mid)
        self.assertIn("compaction candidates (1): sync.md", out_mid)

        # 2. Multi-concern mega-doc (>16k chars, >=6 H2 sections, <5 dated headings) notes level-2 sections.
        self.valid()
        os.remove(os.path.join(self.ssot, "sync.md"))
        mega_doc = "# System Architecture\n\n## Failure and recovery\n\nRetries are idempotent.\n\n" + "\n\n".join(
            f"## Subsystem {n}\n\n" + ("Independent concern architecture specification and state ownership. " * 45)
            for n in range(1, 7)
        ) + "\n"
        self.write("architecture.md", mega_doc)
        out_mega = self.assert_clean()
        self.assertIn("WARN  architecture.md", out_mega)
        self.assertIn("across 7 level-2 sections is past the 16000-character reading budget; consider splitting by topic", out_mega)

        # 3. Format-5 entry with >=50 inline rows suggests entry-relative invariants/<topic>.md, not SSOT/invariants/.
        space = os.path.join(self.repo, "f5space")
        os.makedirs(space)
        with open(os.path.join(space, "rules.md"), "w", encoding="utf-8") as handle:
            handle.write("# Rules\n\n## Core\n\nExplained.\n")
        f5_rows = "\n".join(
            f"| F5-{n:03d} | process rule | Concise space rule {n:03d} | [Core](rules.md#core) | confirmed | owner, 2026-05-02 |"
            for n in range(1, 53)
        )
        entry = os.path.join(space, "CONTEXT.md")
        with open(entry, "w", encoding="utf-8") as handle:
            handle.write("---\nssot_format: 5\nlanguage: en\n---\n\n# Space\n\n## Invariants\n\n"
                         "| ID | Kind | Rule | Explained in | Status | Source |\n|---|---|---|---|---|---|\n" + f5_rows + "\n")
        code, f5_out = self.run_checker(entry)
        self.assertEqual(code, 0, f5_out)
        self.assertIn("invariants/<topic>.md (relative to entry dir)", f5_out)
        self.assertNotIn("SSOT/invariants/<topic>.md", f5_out)

    def test_cold_index_bloat_and_completed_checkboxes(self):
        # 1. Clean concise decisions/README.md stays quiet; >8k emits INFO; >16k SSOT-owned emits WARN;
        #    >=3 rows >250 chars or 1 row >350 chars emits rolled-up INFO.
        self.valid()
        self.write("decisions/0001-a.md", "# 0001\n\nAccepted.\n")
        clean_idx = "# Decisions\n\n| ID | Date | Status | Topic | File |\n|---|---|---|---|---|\n" \
                    "| 0001 | 2026-05-02 | accepted | Token bucket | [0001](0001-a.md) |\n"
        self.write("decisions/README.md", clean_idx)
        out_clean = self.assert_clean()
        self.assertNotIn("WARN", out_clean)
        self.assertNotIn("cold index", out_clean)
        self.assertNotIn("compaction candidates", out_clean)

        # Single row >350 chars triggers verbose-row INFO without size WARN.
        verbose_idx = clean_idx + "| 0002 | 2026-05-03 | accepted | " + ("Full archive summary replayed inside index cell. " * 8) + " | [0001](0001-a.md) |\n"
        self.write("decisions/README.md", verbose_idx)
        out_row = self.assert_clean()
        self.assertNotIn("WARN", out_row)
        self.assertIn("cold-index table row(s) exceed 250 characters", out_row)
        self.assertIn("compaction candidates (1): decisions/README.md", out_row)

        # >=3 rows in (250, 350] chars also triggers rolled-up INFO.
        soft_row = "| 0003 | 2026-05-04 | accepted | " + ("Verbose summary cell text. " * 9) + " | [0001](0001-a.md) |\n"
        self.write("decisions/README.md", clean_idx + soft_row * 3)
        out_soft = self.assert_clean()
        self.assertIn("3 cold-index table row(s) exceed 250 characters", out_soft)

        # Size >8k -> INFO; >16k SSOT-owned -> WARN.
        self.write("decisions/README.md", clean_idx + ("| 0004 | 2026-05-05 | accepted | Short topic | [0001](0001-a.md) |\n" * 130))
        out_8k = self.assert_clean()
        self.assertNotIn("WARN", out_8k)
        self.assertIn("INFO  decisions/README.md  cold index is", out_8k)
        self.write("decisions/README.md", clean_idx + ("| 0004 | 2026-05-05 | accepted | Short topic | [0001](0001-a.md) |\n" * 260))
        out_16k = self.assert_clean()
        self.assertIn("WARN  decisions/README.md  cold index is", out_16k)

        # 2. Completed checkboxes: >=5 in task/workaround/entry triggers INFO; <5 stays quiet;
        #    active warm doc requires >=8 AND >=50%; fenced code checkboxes ignored.
        self.valid()
        os.remove(os.path.join(self.ssot, "decisions", "README.md"))
        self.write("workarounds.md", "# Workarounds\n\n" + "\n".join(f"- [x] Fixed shim {n}" for n in range(1, 5)) + "\n")
        self.assertNotIn("completed checklist", self.assert_clean())
        self.write("workarounds.md", "# Workarounds\n\n" + "\n".join(f"- [x] Fixed shim {n}" for n in range(1, 6)) + "\n")
        out_wa = self.assert_clean()
        self.assertIn("5 completed checklist item(s) (`- [x]`) out of 5", out_wa)
        self.assertNotIn("WARN", out_wa)
        # Warm doc: 8 checked out of 20 (<50%) stays quiet; 8 checked out of 12 (>=50%) triggers INFO.
        os.remove(os.path.join(self.ssot, "workarounds.md"))
        self.valid()
        self.write("architecture.md", ARCHITECTURE + "\n"
                   + "\n".join(f"- [x] Done {n}" for n in range(8)) + "\n"
                   + "\n".join(f"- [ ] Open {n}" for n in range(12)) + "\n")
        self.assertNotIn("completed checklist", self.assert_clean())
        self.write("architecture.md", ARCHITECTURE + "\n"
                   + "\n".join(f"- [x] Done {n}" for n in range(8)) + "\n"
                   + "\n".join(f"- [ ] Open {n}" for n in range(4)) + "\n")
        self.assertIn("8 completed checklist item(s) (`- [x]`) out of 12", self.assert_clean())
        # Fenced checkboxes do not count.
        self.valid()
        self.write("tasks.md", "# Tasks\n\n```md\n" + "\n".join(f"- [x] Example {n}" for n in range(10)) + "\n```\n")
        self.assertNotIn("completed checklist", self.assert_clean())

    def test_compaction_rollup_capping_clean_zero_noise_and_owners_scoping(self):
        # 1. Clean repo emits zero compaction rollup lines.
        self.valid()
        self.assertNotIn("compaction candidates", self.assert_clean())

        # 2. Six distinct bloated files emit ONE capped rollup line right before the verdict.
        for n in range(1, 7):
            self.write(f"tasks-{n}.md", f"# Tasks {n}\n\n" + "\n".join(f"- [x] Finished item {i}" for i in range(6)) + "\n")
        out_cap = self.assert_clean()
        self.assertEqual(out_cap.count("compaction candidates"), 1, out_cap)
        self.assertIn("INFO  .  compaction candidates (6):", out_cap)
        self.assertIn(", and 1 more", out_cap)
        lines = [ln for ln in out_cap.splitlines() if ln.strip()]
        self.assertIn("compaction candidates (6):", lines[-2])
        self.assertTrue(lines[-1].startswith("ssot-check: PASS"))

        # 3. --owners only checks selected files and never opens unselected bloated files.
        unselected = os.path.join(self.ssot, "tasks-2.md")
        observer = textwrap.dedent("""
            import runpy, sys
            watched, checker, *args = sys.argv[1:]
            def audit(event, arguments):
                if event == "open" and arguments[0] == watched:
                    print("OPENED UNSELECTED", file=sys.stderr)
            sys.addaudithook(audit)
            sys.argv = [checker, *args]
            runpy.run_path(checker, run_name="__main__")
        """)
        self.write("README.md", README + "\n- [Tasks 1](tasks-1.md)\n- [Tasks 2](tasks-2.md)\n")
        proc = subprocess.run(
            [sys.executable, "-c", observer, unselected, CHECKER,
             os.path.join(self.ssot, "README.md"), "--owners", "tasks-1.md"],
            cwd=self.repo, text=True, capture_output=True, check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertNotIn("OPENED UNSELECTED", proc.stderr)
        self.assertIn("compaction candidates (1): tasks-1.md", proc.stdout)
        self.assertNotIn("tasks-2.md", proc.stdout)

    def test_verifier_regressions_cold_shards_zh_core_research_markers_and_cold_paths(self):
        import shutil
        # 1. Active confirmed row inside invariants/retired.md warns and does not get cold exemptions;
        #    active feature shard invariants/chat-history.md with 55 confirmed rows is not exempted.
        long_rule = "Preserve exact ordering and auditability across retries " * 9
        self.sharded_setup(
            readme_invariants="- [Shipping](invariants/shipping.md)\n- [Webhooks](invariants/webhooks.md)\n"
                              "- [Retired](invariants/retired.md)\n- [Chat history](invariants/chat-history.md)\n",
        )
        self.write("invariants/retired.md", textwrap.dedent(f"""\
            # Retired Invariants

            | ID | Kind | Rule | Explained in | Status | Source |
            |---|---|---|---|---|---|
            | RET-01 | product promise | {long_rule} | [Retries](../architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |
            """))
        chat_rows = "\n".join(
            f"| CHT-{n:03d} | product promise | Preserve chat history message {n:03d} | [Retries](../architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |"
            for n in range(1, 56)
        )
        self.write("invariants/chat-history.md",
                   "# Chat History Invariants\n\n| ID | Kind | Rule | Explained in | Status | Source |\n|---|---|---|---|---|---|\n" + chat_rows + "\n")
        out_shards = self.assert_clean()
        self.assertIn("WARN  invariants/retired.md:5  1 active (confirmed/candidate) invariant row(s) in cold shard retired.md", out_shards)
        self.assertIn("INFO  invariants/retired.md:5  1 register row(s) exceed 500 characters", out_shards)
        self.assertIn("INFO  invariants/chat-history.md  invariants shard is", out_shards)
        self.assertNotIn("WARN  invariants/chat-history.md", out_shards)

        # 2. Shipped ZH core headings (## 文件地图 in F4, ## 权威文档与任务路由 in F5) stay quiet at 4.5k chars (<8k total).
        shutil.rmtree(os.path.join(self.ssot, "invariants"))
        self.valid()
        zh_f4 = textwrap.dedent("""\
            ---
            ssot_format: 4
            language: zh-CN
            ---

            # 示例

            ## 文件地图

            - [架构](architecture.md)：""" + ("说明核心文档路径与职责。" * 380) + """

            ## 不变量

            | ID | 类型 | 规则 | 解释位置 | 状态 | 来源 |
            |---|---|---|---|---|---|
            | INV-01 | 产品承诺 | 重试不重复扣款 | [架构](architecture.md#failure-and-recovery) | confirmed | 用户，2026-05-02 |
            """)
        self.write("README.md", zh_f4)
        out_zh_f4 = self.assert_clean()
        self.assertNotIn("WARN", out_zh_f4)
        self.assertNotIn("entry section", out_zh_f4)
        self.assertNotIn("compaction candidates", out_zh_f4)

        space = os.path.join(self.repo, "f5zh")
        os.makedirs(space)
        with open(os.path.join(space, "guide.md"), "w", encoding="utf-8") as handle:
            handle.write("# 指南\n")
        zh_f5_entry = os.path.join(space, "CONTEXT.md")
        with open(zh_f5_entry, "w", encoding="utf-8") as handle:
            handle.write("---\nssot_format: 5\nlanguage: zh-CN\n---\n\n# 空间\n\n## 权威文档与任务路由\n\n- [指南](guide.md)："
                         + ("说明现行规则文档位置与适用范围。" * 270) + "\n\n## 不变量\n\n暂无。\n")
        code, out_zh_f5 = self.run_checker(zh_f5_entry)
        self.assertEqual(code, 0, out_zh_f5)
        self.assertNotIn("WARN", out_zh_f5)
        self.assertNotIn("entry section", out_zh_f5)
        self.assertNotIn("compaction candidates", out_zh_f5)

        # 3. Active research/ (- Status: active / - 状态：active), ssot_tier: warm opt-out, and Format-5 bare history.md/archive.md.
        self.valid()
        big_body = ("Detailed active research evidence and findings. " * 380) + "\n"
        self.write("research/active-en.md", "# Study EN\n\n- Date: 2026-11-26\n- Status: active <!-- WIP -->\n\n" + big_body)
        self.write("research/active-zh.md", "# Study ZH\n\n- 日期：2026-11-26\n- 状态：active\n\n" + big_body)
        self.write("research/concluded.md", "# Done Study\n\n- Status: concluded — see 0004\n\n" + big_body)
        self.write("research/warm-override.md", "---\nssot_tier: warm\n---\n\n# Warm Override\n\n" + big_body)
        self.write("history.md", "---\nssot_tier: warm\n---\n\n# Active History\n\n" + big_body)
        out_res = self.assert_clean()
        self.assertIn("WARN  research/active-en.md", out_res)
        self.assertIn("WARN  research/active-zh.md", out_res)
        self.assertIn("WARN  research/warm-override.md", out_res)
        self.assertIn("WARN  history.md", out_res)
        self.assertNotIn("concluded.md", out_res)

        f5_hist = os.path.join(self.repo, "f5hist")
        os.makedirs(f5_hist)
        with open(os.path.join(f5_hist, "history.md"), "w", encoding="utf-8") as handle:
            handle.write("# World History\n\n" + big_body)
        with open(os.path.join(f5_hist, "archive.md"), "w", encoding="utf-8") as handle:
            handle.write("# World Archive\n\n" + big_body)
        with open(os.path.join(f5_hist, "old-history.md"), "w", encoding="utf-8") as handle:
            handle.write("# Superseded Notes\n\n" + big_body)
        f5_entry = os.path.join(f5_hist, "CONTEXT.md")
        with open(f5_entry, "w", encoding="utf-8") as handle:
            handle.write("---\nssot_format: 5\nlanguage: en\n---\n\n# Space\n\n"
                         "- [History](history.md)\n- [Archive](archive.md)\n- [Old](old-history.md)\n\n## Invariants\n\nNone.\n")
        code, out_f5h = self.run_checker(f5_entry)
        self.assertEqual(code, 0, out_f5h)
        self.assertIn("INFO  history.md", out_f5h)
        self.assertIn("INFO  archive.md", out_f5h)
        self.assertNotIn("old-history.md", out_f5h)

        # 4. Cold-marker comment state machine & <!-- /ssot:cold --> bypass prevention.
        shutil.rmtree(os.path.join(self.ssot, "research"))
        os.remove(os.path.join(self.ssot, "history.md"))
        self.valid()
        # (a) Nested-looking text inside an outer single-line comment must NOT trigger cold tail.
        self.write("outer-comment.md",
                   "# Spec\n\n<!-- hint: use <!-- ssot:cold --> before heading -->\n\n" + big_body)
        out_outer = self.assert_clean()
        self.assertIn("WARN  outer-comment.md", out_outer)
        os.remove(os.path.join(self.ssot, "outer-comment.md"))
        # (b) Real <!-- ssot:cold --> on the same line after a multiline comment close MUST trigger cold tail.
        self.write("after-close.md",
                   "# Spec\n\n## Active\n\nShort.\n\n<!-- multiline\ncomment --> <!-- ssot:cold -->\n\n" + big_body)
        out_after = self.assert_clean()
        self.assertNotIn("WARN", out_after)
        self.assertNotIn("after-close.md", out_after)
        os.remove(os.path.join(self.ssot, "after-close.md"))
        # (c) <!-- /ssot:cold --> followed by headingless 18k prose MUST trigger BOTH 16k WARN and inverted INFO.
        self.write("closed-bypass.md",
                   "# Spec\n\n<!-- ssot:cold -->\nOld.\n<!-- /ssot:cold -->\n\n" + big_body)
        out_bypass = self.assert_clean()
        self.assertIn("WARN  closed-bypass.md", out_bypass)
        self.assertIn("cold section starts above", out_bypass)
        os.remove(os.path.join(self.ssot, "closed-bypass.md"))

        # 5. path_mentions() skips cold archives and intra-file cold tails, while still warning above cold boundary.
        self.valid()
        os.makedirs(os.path.join(self.repo, "src"))
        with open(os.path.join(self.repo, "src", "old.py"), "w", encoding="utf-8") as handle:
            handle.write("x = 1\n")
        self.write("archive/v1.md", "# Archived\n\nUsed `src/old.py`.\n")
        self.write("auth-history.md", "# Auth History\n\nUsed `src/old.py`.\n")
        self.write("architecture.md", ARCHITECTURE + "\n## History (cold)\n\nReplaced `src/old.py`.\n")
        self.git("init", "-q")
        self.commit("baseline with old.py")
        self.git("rm", "-q", "src/old.py")
        self.commit("remove old.py")
        out_paths_cold = self.assert_clean()
        self.assertNotIn("`src/old.py` was removed", out_paths_cold)
        # Mentioning src/old.py ABOVE ## History (cold) still warns.
        self.write("architecture.md", ARCHITECTURE + "\nActive code in `src/old.py`.\n\n## History (cold)\n\nReplaced `src/old.py`.\n")
        out_paths_warm = self.assert_clean()
        self.assertIn("WARN  architecture.md:7  `src/old.py` was removed", out_paths_warm)
        self.assertNotIn("also line", out_paths_warm)

    def test_v2_f4_vs_f5_cold_offload_external_owner_and_concrete_shard_rollup(self):
        # 1. F4 SSOT-owned dated warm doc (both 8k-16k early INFO and >16k WARN) suggests separate cold archive
        #    (decisions/ or *-history.md), NEVER trailing ## History (cold) / cold tail.
        self.valid()
        mid_dated = "# Alert Policy\n\n" + "\n\n".join(
            f"## 2026-11-{d:02d} Change {d}\n\n" + ("Superseded revision log detail. " * 46)
            for d in range(1, 7)
        ) + "\n"
        self.write("alerts.md", mid_dated)
        out_f4_mid = self.assert_clean()
        self.assertIn("move superseded history to a cold archive (decisions/ or *-history.md)", out_f4_mid)
        self.assertNotIn("trailing ## History (cold)", out_f4_mid)
        self.assertIn("alerts.md (", out_f4_mid)
        self.assertIn("consolidate + offload history to cold archive)", out_f4_mid)
        self.assertNotIn("cold tail", out_f4_mid)

        big_dated = "# Alert Policy\n\n" + "\n\n".join(
            f"## 2026-11-{d:02d} Change {d}\n\n" + ("Superseded revision log detail. " * 90)
            for d in range(1, 7)
        ) + "\n"
        self.write("alerts.md", big_dated)
        out_f4_big = self.assert_clean()
        self.assertIn("WARN  alerts.md", out_f4_big)
        self.assertIn("move superseded history to a cold archive (decisions/ or *-history.md)", out_f4_big)
        self.assertNotIn("trailing ## History (cold)", out_f4_big)
        self.assertIn("consolidate + offload history to cold archive)", out_f4_big)
        os.remove(os.path.join(self.ssot, "alerts.md"))

        # 2. Format-5 chronological doc keeps (or trailing ## History (cold) if layout is fixed).
        space = os.path.join(self.repo, "f5log")
        os.makedirs(space)
        with open(os.path.join(space, "decisions.md"), "w", encoding="utf-8") as handle:
            handle.write(mid_dated)
        entry = os.path.join(space, "CONTEXT.md")
        with open(entry, "w", encoding="utf-8") as handle:
            handle.write("---\nssot_format: 5\nlanguage: en\n---\n\n# Space\n\n- [Decisions](decisions.md)\n\n## Invariants\n\nNone.\n")
        code, out_f5_log = self.run_checker(entry)
        self.assertEqual(code, 0, out_f5_log)
        self.assertIn("or trailing ## History (cold) if layout is fixed", out_f5_log)
        self.assertIn("decisions.md (", out_f5_log)
        self.assertIn("or ## History (cold) if layout fixed)", out_f5_log)

        # 3. External canonical owner in Format 4 is explicitly tagged `external owner` in compaction rollup
        #    so closeout can relay a 1-line proposal without opening untouched external files.
        self.valid()
        ext_mega = "# External Spec\n\n" + "\n\n".join(
            f"## Concern {n}\n\n" + ("External specification owned outside SSOT directory. " * 60)
            for n in range(1, 8)
        ) + "\n"
        self.write("../docs/spec.md", ext_mega)
        self.write("README.md", README + "\n- [Spec](../docs/spec.md)\n")
        out_ext = self.assert_clean()
        self.assertNotIn("WARN", out_ext)
        self.assertIn("INFO  ../docs/spec.md", out_ext)
        self.assertIn("compaction candidates (1): ../docs/spec.md (external owner,", out_ext)
        self.assertIn("7 sections -> propose split/consolidation)", out_ext)

        # 4. Concrete entry sharding + retired offload rollup in Format 4 and Format 5.
        self.valid()
        f4_rows = [
            f"| INV-{n:03d} | product promise | Active rule {n:03d} | [R](architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |"
            for n in range(1, 51)
        ] + [
            f"| INV-{n:03d} | product promise | Retired rule {n:03d} | [R](architecture.md#failure-and-recovery) | retired | user, 2026-06-01 |"
            for n in range(51, 55)
        ]
        self.invariant_row("\n".join(f4_rows))
        out_t3_f4 = self.assert_clean()
        self.assertIn("compaction candidates (1): README.md (54 inline; 4 retired -> propose sharding into SSOT/invariants/<topic>.md + SSOT/invariants/retired.md)", out_t3_f4)

        f5_t3 = os.path.join(self.repo, "f5t3")
        os.makedirs(f5_t3)
        with open(os.path.join(f5_t3, "rules.md"), "w", encoding="utf-8") as handle:
            handle.write("# Rules\n\n## Core\n\nExplained.\n")
        f5_rows = [
            f"| F5-{n:03d} | process rule | Active rule {n:03d} | [Core](rules.md#core) | confirmed | owner, 2026-05-02 |"
            for n in range(1, 51)
        ] + [
            f"| F5-{n:03d} | process rule | Old rule {n:03d} | [Core](rules.md#core) | retired | owner, 2026-06-01 |"
            for n in range(51, 55)
        ]
        f5_entry = os.path.join(f5_t3, "CONTEXT.md")
        with open(f5_entry, "w", encoding="utf-8") as handle:
            handle.write("---\nssot_format: 5\nlanguage: en\n---\n\n# Space\n\n## Invariants\n\n"
                         "| ID | Kind | Rule | Explained in | Status | Source |\n|---|---|---|---|---|---|\n" + "\n".join(f5_rows) + "\n")
        code, out_t3_f5 = self.run_checker(f5_entry)
        self.assertEqual(code, 0, out_t3_f5)
        self.assertIn("compaction candidates (1): CONTEXT.md (54 inline; 4 retired -> propose sharding into invariants/<topic>.md + invariants/retired.md)", out_t3_f5)

    def test_submodule_links_validate_populated_targets_and_handle_unpopulated_cleanly(self):
        self.valid()
        # 1. Populated nested git repo / submodule inside repo root: valid file + heading anchor -> 0 warnings.
        sub_dir = os.path.join(self.repo, "plugins", "child-mod")
        os.makedirs(sub_dir)
        subprocess.run(["git", "init", "-q", sub_dir], check=True)
        with open(os.path.join(sub_dir, "README.md"), "w", encoding="utf-8") as handle:
            handle.write("# Child Plugin\n\n## Runtime Contract\n\nDetails.\n")
        self.write(
            "notes.md",
            "# Notes\n\n"
            "- [Root](../plugins/child-mod)\n"
            "- [Doc](../plugins/child-mod/README.md)\n"
            "- [Section](../plugins/child-mod/README.md#runtime-contract)\n",
        )
        out_ok = self.assert_clean()
        self.assertIn("0 error(s), 0 warning(s)", out_ok)
        self.assertNotIn("link leaves the repository", out_ok)

        # 2. Broken file inside populated submodule -> ERROR.
        self.write("notes.md", "# Notes\n\n- [Missing](../plugins/child-mod/absent.md)\n")
        self.assert_error("broken link (in nested repository): ../plugins/child-mod/absent.md")

        # 3. Broken heading anchor inside populated submodule -> ERROR.
        self.write("notes.md", "# Notes\n\n- [BadAnchor](../plugins/child-mod/README.md#no-such-heading)\n")
        self.assert_error("missing heading anchor: ../plugins/child-mod/README.md#no-such-heading")

        # 4. Unpopulated submodule declared in .gitmodules (empty dir, no .git) -> INFO, 0 errors, 0 warnings.
        empty_sub = os.path.join(self.repo, "services", "uninit-svc")
        os.makedirs(empty_sub)
        with open(os.path.join(self.repo, ".gitmodules"), "w", encoding="utf-8") as handle:
            handle.write('[submodule "services/uninit-svc"]\n\tpath = services/uninit-svc\n\turl = https://example.test/uninit.git\n')
        self.write("notes.md", "# Notes\n\n- [Uninit](../services/uninit-svc/README.md#api)\n")
        out_uninit = self.assert_clean()
        self.assertIn("0 error(s), 0 warning(s)", out_uninit)
        self.assertIn("nested repository/submodule is not populated here", out_uninit)
        self.assertNotIn("link leaves the repository", out_uninit)

        # 5. Unpopulated stub containing only .git (like pre-commit snapshot) -> INFO, 0 errors, 0 warnings.
        stub_sub = os.path.join(self.repo, "plugins", "stub-mod")
        os.makedirs(os.path.join(stub_sub, ".git"))
        self.write("notes.md", "# Notes\n\n- [Stub](../plugins/stub-mod/README.md)\n")
        out_stub = self.assert_clean()
        self.assertIn("0 error(s), 0 warning(s)", out_stub)
        self.assertIn("nested repository/submodule is not populated here", out_stub)

        # 6. Link truly leaving the repository still emits WARN.
        self.write("notes.md", "# Notes\n\n- [Sibling](../../other-repo/README.md)\n")
        out_leave = self.assert_clean()
        self.assertIn("link leaves the repository", out_leave)

        # 7. Invariant Explained in pointing into a submodule is still rejected as ERROR.
        self.write("notes.md", "# Notes\n\nClean.\n")
        self.invariant_row("| INV-02 | architecture invariant | Rule | [Sub](../plugins/child-mod/README.md#runtime-contract) | confirmed | user, 2026-06-01 |")
        self.assert_error("needs a Markdown explanation in the same repository")

    def test_cjk_utf8_byte_thresholds_and_chinese_cold_classification(self):
        self.valid()
        # 1. Healthy CJK warm doc (~6,400 chars / ~19,200 bytes) stays clean.
        self.write("healthy-zh.md", "# 中文模块\n\n" + ("中文说明段落用于验证健康长度不会误报。" * 320) + "\n")
        out_healthy = self.assert_clean()
        self.assertIn("0 error(s), 0 warning(s)", out_healthy)
        self.assertNotIn("compaction candidates", out_healthy)

        # 2. Oversized CJK warm doc (~9,000 chars / ~27,000 bytes, under 16k chars but over 24k UTF-8 bytes)
        #    surfaces as INFO + compaction candidate across 6 H2 sections.
        sections = "\n\n".join(f"## 主题{i}\n\n" + ("这是超过两万四千字节的中文说明。" * 100) for i in range(1, 7))
        self.write("big-zh.md", "# 中文巨型文档\n\n" + sections + "\n")
        out_big = self.assert_clean()
        self.assertIn("0 error(s), 0 warning(s)", out_big)
        self.assertIn("past the UTF-8 reading budget", out_big)
        self.assertIn("compaction candidates (1): big-zh.md", out_big)
        self.assertIn("6 sections -> split by topic", out_big)
        os.remove(os.path.join(self.ssot, "big-zh.md"))

        # 3. CJK invariant row >900 bytes (<500 chars) and mixed char+byte rows.
        zh_rule = "这是用来测试中文单行不变量字节上限的规则描述" * 16  # 352 chars, 1,056 bytes
        self.invariant_row(f"| INV-02 | 流程规则 | {zh_rule} | [架构](architecture.md#failure-and-recovery) | confirmed | 用户，2026-06-01 |")
        out_row = self.assert_clean()
        self.assertIn("exceed 900 bytes", out_row)
        self.assertIn("compaction candidates (1): README.md (1 long rows >900 bytes -> trim rows)", out_row)

        long_ascii = "x" * 520
        self.invariant_row(
            f"| INV-02 | 流程规则 | {zh_rule} | [架构](architecture.md#failure-and-recovery) | confirmed | 用户，2026-06-01 |\n"
            f"| INV-03 | process rule | {long_ascii} | [Arch](architecture.md#failure-and-recovery) | confirmed | user, 2026-06-01 |"
        )
        out_mixed = self.assert_clean()
        self.assertIn("exceed 500 characters or 900 bytes", out_mixed)
        self.assertIn("INV-02", out_mixed)
        self.assertIn("INV-03", out_mixed)

        # 4. CJK cold tail >32,000 bytes (<32,000 chars) triggers offload INFO.
        self.valid()
        cold_tail_zh = "# 策略\n\n现行规则很短。\n\n## 历史记录（冷读）\n\n" + ("这是旧版本历史归档记录。" * 1000) + "\n"
        self.write("policy-zh.md", cold_tail_zh)
        out_tail = self.assert_clean()
        self.assertIn("0 error(s), 0 warning(s)", out_tail)
        self.assertIn("including its cold tail; >32000 bytes)", out_tail)
        self.assertIn("offload cold tail", out_tail)
        os.remove(os.path.join(self.ssot, "policy-zh.md"))

        # 5. Chinese cold archive dir (04_设计决策历史/) is exempt from reading budget while still checking links;
        #    Chinese cold index (04_设计决策历史/00_索引.md) catches bloated summary rows (>500 bytes).
        self.write("04_设计决策历史/2026-11.md", "# 历史决策\n\n" + ("这是一份很长的中文历史决策归档文档。" * 600) + "\n")
        self.write("topic-历史.md", "# 专题历史\n\n" + ("这是专题历史归档。" * 1200) + "\n")
        out_cold_zh = self.assert_clean()
        self.assertIn("0 error(s), 0 warning(s)", out_cold_zh)
        self.assertNotIn("compaction candidates", out_cold_zh)

        self.write(
            "04_设计决策历史/00_索引.md",
            "# 决策索引\n\n| 编号 | 摘要 | 链接 |\n|---|---|---|\n"
            + "".join(
                f"| D-0{i} | {'把历史讨论和原话全塞进索引单元格导致膨胀' * 10} | [归档](2026-11.md) |\n"
                for i in range(1, 4)
            ),
        )
        out_cidx = self.assert_clean()
        self.assertIn("cold-index table row(s) exceed 500 bytes", out_cidx)
        self.assertIn("04_设计决策历史/00_索引.md", out_cidx)

        # 6. Format-5 CJK doc >24,000 bytes uses propose split/consolidation (not auto-split).
        f5_dir = os.path.join(self.repo, "f5zh")
        os.makedirs(f5_dir)
        with open(os.path.join(f5_dir, "guide.md"), "w", encoding="utf-8") as handle:
            handle.write("# 指南\n\n" + ("中文通用空间正文内容超过两万四千字节。" * 500) + "\n")
        f5_entry = os.path.join(f5_dir, "README.md")
        with open(f5_entry, "w", encoding="utf-8") as handle:
            handle.write("---\nssot_format: 5\nlanguage: zh-CN\n---\n\n# 空间\n\n- [指南](guide.md)\n\n## 不变量\n\n暂无。\n")
        code, out_f5 = self.run_checker(f5_entry)
        self.assertEqual(code, 0, out_f5)
        self.assertIn("compaction candidates (1): guide.md (", out_f5)
        self.assertIn("bytes -> propose split/consolidation)", out_f5)

    def test_codex_instruction_chain_byte_budget_and_git_boundaries(self):
        import shutil
        # 1. Non-git directory graceful handling: <28 KB stays clean (0 warnings, no UNCHECKED),
        #    and >32 KB warns accurately without ascending above the workspace.
        self.valid()
        root_agents = os.path.join(self.repo, "AGENTS.md")
        with open(root_agents, "w", encoding="utf-8") as handle:
            handle.write("# Agents\n\n" + ("中" * 9000) + "\n")  # 27,011 UTF-8 bytes (<28,672)
        out_nogit_ok = self.assert_clean()
        self.assertIn("0 error(s), 0 warning(s)", out_nogit_ok)
        self.assertNotIn("Codex instruction chain", out_nogit_ok)

        with open(root_agents, "w", encoding="utf-8") as handle:
            handle.write("# Agents\n\n" + ("a" * 33000) + "\n")
        out_nogit_over = self.assert_clean()
        self.assertIn("WARN  ../AGENTS.md  Codex instruction chain is 33011 bytes (1 file(s); exceeds 32768-byte project_doc_max_bytes cliff", out_nogit_over)
        self.assertIn("mid-UTF-8", out_nogit_over)

        # 2. Git repo: 28-32 KB warning band, >32 KB root+subdir cumulative cliff,
        #    and AGENTS.override.md precedence in both directions.
        with open(root_agents, "w", encoding="utf-8") as handle:
            handle.write("r" * 20000)
        self.git("init", "-q")
        self.commit("init with 20k root AGENTS")
        out_under = self.assert_clean()
        self.assertNotIn("Codex instruction chain", out_under)

        sub_dir = os.path.join(self.repo, "packages", "client")
        os.makedirs(sub_dir)
        sub_agents = os.path.join(sub_dir, "AGENTS.md")
        with open(sub_agents, "w", encoding="utf-8") as handle:
            handle.write("s" * 9500)  # cumulative 29,500 B in [28,672, 32,768]
        out_warn = self.assert_clean()
        self.assertIn("WARN  ../packages/client/AGENTS.md  Codex instruction chain is 29500 bytes (2 file(s); >=28672 bytes, approaching 32768-byte project_doc_max_bytes limit)", out_warn)
        self.assertNotIn("WARN  ../AGENTS.md", out_warn)

        with open(sub_agents, "w", encoding="utf-8") as handle:
            handle.write("s" * 15000)  # cumulative 35,000 B > 32,768
        out_cliff = self.assert_clean()
        self.assertIn("WARN  ../packages/client/AGENTS.md  Codex instruction chain is 35000 bytes (2 file(s); exceeds 32768-byte project_doc_max_bytes cliff", out_cliff)

        # Small AGENTS.override.md replaces oversized AGENTS.md in the same directory.
        sub_override = os.path.join(sub_dir, "AGENTS.override.md")
        with open(sub_override, "w", encoding="utf-8") as handle:
            handle.write("# Short override\n")  # cumulative 20,017 B < 28,672
        out_ovr_small = self.assert_clean()
        self.assertNotIn("Codex instruction chain", out_ovr_small)

        # Conversely, oversized AGENTS.override.md over tiny AGENTS.md triggers cliff.
        with open(sub_agents, "w", encoding="utf-8") as handle:
            handle.write("# Small base\n")
        with open(sub_override, "w", encoding="utf-8") as handle:
            handle.write("o" * 15000)  # cumulative 35,000 B > 32,768
        out_ovr_big = self.assert_clean()
        self.assertIn("WARN  ../packages/client/AGENTS.override.md  Codex instruction chain is 35000 bytes (2 file(s); exceeds 32768-byte project_doc_max_bytes cliff", out_ovr_big)

        # 3. --owners scoped mode skips Codex chain scanning completely.
        code, out_scoped = self.run_checker(os.path.join(self.ssot, "README.md"), "--owners")
        self.assertEqual(code, 0, out_scoped)
        self.assertNotIn("Codex instruction chain", out_scoped)
        shutil.rmtree(os.path.join(self.repo, "packages"))

        # 4. Nested .git boundary stops chain propagation in BOTH directions (zero cross-repo bleed).
        nested = os.path.join(self.repo, "child-repo")
        os.makedirs(os.path.join(nested, "SSOT"))
        subprocess.run(["git", "init", "-q", nested], check=True)
        with open(os.path.join(nested, "AGENTS.md"), "w", encoding="utf-8") as handle:
            handle.write("n" * 20000)  # 20k outer + 20k nested would be 40k if wrongly combined
        with open(os.path.join(nested, "SSOT", "README.md"), "w", encoding="utf-8") as handle:
            handle.write(README)
        with open(os.path.join(nested, "SSOT", "architecture.md"), "w", encoding="utf-8") as handle:
            handle.write(ARCHITECTURE)
        out_outer = self.assert_clean()
        self.assertNotIn("Codex instruction chain", out_outer)
        code, out_inner = self.run_checker(os.path.join(nested, "SSOT"))
        self.assertEqual(code, 0, out_inner)
        self.assertNotIn("Codex instruction chain", out_inner)

        # 5. Gitignored runtime/snapshot directories do not spam Codex chain warnings.
        with open(os.path.join(self.repo, ".gitignore"), "w", encoding="utf-8") as handle:
            handle.write(".runtime/\n")
        ign_dir = os.path.join(self.repo, ".runtime", "snap")
        os.makedirs(ign_dir)
        with open(os.path.join(ign_dir, "AGENTS.md"), "w", encoding="utf-8") as handle:
            handle.write("x" * 20000)
        out_ign = self.assert_clean()
        self.assertNotIn("Codex instruction chain", out_ign)

        # 6. Format-5 space inside a git subdirectory inherits repo-root -> space ancestor bytes
        #    while stopping at the nearest .git root.
        f5_sub = os.path.join(self.repo, "spaces", "notes")
        os.makedirs(f5_sub)
        with open(os.path.join(f5_sub, "CONTEXT.md"), "w", encoding="utf-8") as handle:
            handle.write("---\nssot_format: 5\nlanguage: en\n---\n\n# Notes\n\n## Invariants\n\nNone.\n")
        with open(os.path.join(f5_sub, "AGENTS.md"), "w", encoding="utf-8") as handle:
            handle.write("f" * 14000)  # 20k repo root + 14k space = 34k > 32,768
        code, out_f5 = self.run_checker(os.path.join(f5_sub, "CONTEXT.md"))
        self.assertEqual(code, 0, out_f5)
        self.assertIn("WARN  AGENTS.md  Codex instruction chain is 34000 bytes (2 file(s); exceeds 32768-byte project_doc_max_bytes cliff", out_f5)


if __name__ == "__main__":
    unittest.main(verbosity=1)
