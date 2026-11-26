#!/usr/bin/env python3
"""Integration tests for tools/ssot-precommit.sh (zero-token opt-in Git pre-commit guard)."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "tools/ssot-precommit.sh"
CHECKER = ROOT / "skills/ssot-doctor/assets/scripts/ssot-check.py"


class PrecommitHookTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        self.home = Path(self.tmp.name) / "empty-home"
        self.home.mkdir()
        self.env = {
            **os.environ,
            "HOME": str(self.home),
            "GIT_AUTHOR_NAME": "Test",
            "GIT_AUTHOR_EMAIL": "t@example.test",
            "GIT_COMMITTER_NAME": "Test",
            "GIT_COMMITTER_EMAIL": "t@example.test",
        }
        for key in ("SSOT_CHECKER", "SSOT_DIR", "SSOT_PRECOMMIT_STRICT", "SSOT_PRECOMMIT_ALWAYS",
                    "CODEX_HOME", "CLAUDE_CONFIG_DIR"):
            self.env.pop(key, None)
        self.git("init", "-q")
        # Install hook in .git/hooks/pre-commit referencing a copied standalone script
        # (so it does not accidentally resolve ROOT/skills via script_dir unless configured).
        self.standalone = Path(self.tmp.name) / "standalone-precommit.sh"
        shutil.copy2(HOOK, self.standalone)
        self.standalone.chmod(0o755)
        hook_dst = self.repo / ".git/hooks/pre-commit"
        hook_dst.write_text(f'#!/usr/bin/env bash\nexec "{self.standalone}" "$@"\n', encoding="utf-8")
        hook_dst.chmod(0o755)

        # Install checker into repo-local .agents/skills to test normal auto-discovery.
        local_chk = self.repo / ".agents/skills/ssot-doctor/assets/scripts/ssot-check.py"
        local_chk.parent.mkdir(parents=True)
        shutil.copy2(CHECKER, local_chk)

        # Seed valid format-4 SSOT + routed external doc + source file.
        (self.repo / "SSOT/invariants").mkdir(parents=True)
        (self.repo / "docs").mkdir()
        (self.repo / "src").mkdir()
        (self.repo / "docs/api.md").write_text("# API\n\n## Retries\n\nIdempotent retry behavior.\n", encoding="utf-8")
        (self.repo / "src/app.py").write_text("x = 1\n", encoding="utf-8")
        (self.repo / "src/legacy.py").write_text("old = True\n", encoding="utf-8")
        (self.repo / "SSOT/architecture.md").write_text(
            "# Architecture\n\nActive code is in `src/app.py`; fallback is in `src/legacy.py`.\n",
            encoding="utf-8",
        )
        (self.repo / "SSOT/invariants/shipping.md").write_text(textwrap.dedent("""\
            # Shipping invariants

            | ID | Kind | Rule | Explained in | Status | Source |
            |---|---|---|---|---|---|
            | SHP-01 | product promise | Express keeps standard intact | [Retries](../../docs/api.md#retries) | confirmed | user, 2026-05-02 |
            """), encoding="utf-8")
        (self.repo / "SSOT/README.md").write_text(textwrap.dedent("""\
            ---
            ssot_format: 4
            language: en
            ---

            # Demo

            Demo service.

            ## Map

            - [Architecture](architecture.md)
            - [API](../docs/api.md)

            ## Invariants

            - [Shipping](invariants/shipping.md) (`SHP-01`)

            | ID | Kind | Rule | Explained in | Status | Source |
            |---|---|---|---|---|---|
            | INV-01 | product promise | Never charge twice | [Retries](../docs/api.md#retries) | confirmed | user, 2026-05-02 |

            ## Open questions

            None.
            """), encoding="utf-8")
        self.git("add", ".")
        res = self.git("commit", "-m", "initial")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)

    def git(self, *args, env=None):
        return subprocess.run(["git", *args], cwd=self.repo, env=env or self.env, capture_output=True, text=True)

    def test_fast_path_skips_checker_for_external_code_add_and_edit(self):
        marker = Path(self.tmp.name) / "checker-ran"
        sentinel = Path(self.tmp.name) / "sentinel-checker.py"
        sentinel.write_text(f"import pathlib, sys\npathlib.Path({str(marker)!r}).write_text('ran')\nsys.exit(0)\n", encoding="utf-8")
        env = {**self.env, "SSOT_CHECKER": str(sentinel)}

        (self.repo / "src/new_helper.py").write_text("def ok(): return True\n", encoding="utf-8")
        (self.repo / "src/app.py").write_text("x = 2\n", encoding="utf-8")
        self.git("add", "src/new_helper.py", "src/app.py")
        res = self.git("commit", "-m", "code only", env=env)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertFalse(marker.exists(), "fast-path should skip launching ssot-check.py for non-SSOT code adds/edits")

    def test_blocks_unauthorized_confirmed_invariant_edit_in_readme_and_shard(self):
        # 1. Tampering confirmed invariant in README without new dated source is blocked.
        readme = self.repo / "SSOT/README.md"
        orig = readme.read_text(encoding="utf-8")
        readme.write_text(orig.replace("Never charge twice", "May charge twice on timeout"), encoding="utf-8")
        self.git("add", "SSOT/README.md")
        res = self.git("commit", "-m", "sneaky readme edit")
        self.assertEqual(res.returncode, 1, res.stdout + res.stderr)
        self.assertIn("confirmed invariant INV-01 changed its rule", res.stdout + res.stderr)
        readme.write_text(orig, encoding="utf-8")
        self.git("reset", "-q", "HEAD", "SSOT/README.md")

        # 2. Tampering confirmed invariant inside a 5.17 topic shard is also blocked.
        shard = self.repo / "SSOT/invariants/shipping.md"
        shard_orig = shard.read_text(encoding="utf-8")
        shard.write_text(shard_orig.replace("Express keeps standard intact", "Express overrides standard"), encoding="utf-8")
        self.git("add", "SSOT/invariants/shipping.md")
        res = self.git("commit", "-m", "sneaky shard edit")
        self.assertEqual(res.returncode, 1, res.stdout + res.stderr)
        self.assertIn("confirmed invariant SHP-01 changed its rule", res.stdout + res.stderr)
        shard.write_text(shard_orig, encoding="utf-8")

    def test_blocks_broken_heading_anchor_in_external_routed_markdown(self):
        api = self.repo / "docs/api.md"
        api.write_text("# API\n\n## Renamed Section\n\nIdempotent retry behavior.\n", encoding="utf-8")
        self.git("add", "docs/api.md")
        res = self.git("commit", "-m", "rename heading")
        self.assertEqual(res.returncode, 1, res.stdout + res.stderr)
        self.assertIn("missing heading anchor", res.stdout + res.stderr)

    def test_triggers_on_deleted_source_file_mentioned_in_ssot(self):
        self.git("rm", "-q", "src/legacy.py")
        res = self.git("commit", "-m", "remove legacy")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("`src/legacy.py` was removed", res.stdout + res.stderr)

    def test_missing_checker_soft_skips_by_default_and_fails_when_strict(self):
        shutil.rmtree(self.repo / ".agents")
        (self.repo / "SSOT/architecture.md").write_text("# Architecture\n\nUpdated note.\n", encoding="utf-8")
        self.git("add", "SSOT/architecture.md")
        res_strict = self.git("commit", "-m", "strict check", env={**self.env, "SSOT_PRECOMMIT_STRICT": "1"})
        self.assertNotEqual(res_strict.returncode, 0, res_strict.stdout + res_strict.stderr)
        self.assertIn("ssot-check.py not found", res_strict.stderr)
        direct_strict = subprocess.run([str(self.standalone)], cwd=self.repo,
                                       env={**self.env, "SSOT_PRECOMMIT_STRICT": "1"}, capture_output=True, text=True)
        self.assertEqual(direct_strict.returncode, 2, direct_strict.stdout + direct_strict.stderr)
        res_soft = self.git("commit", "-m", "soft skip")
        self.assertEqual(res_soft.returncode, 0, res_soft.stdout + res_soft.stderr)
        self.assertIn("skipping", res_soft.stderr)

    def test_symlinked_hook_discovers_checkout_and_global_codex_checker(self):
        shutil.rmtree(self.repo / ".agents")
        hook_dst = self.repo / ".git/hooks/pre-commit"
        hook_dst.unlink()
        # 1. Documented `ln -sf <checkout>/tools/ssot-precommit.sh .git/hooks/pre-commit`
        # resolves symlinks back to ROOT/skills without any local or global install.
        hook_dst.symlink_to(HOOK)
        readme = self.repo / "SSOT/README.md"
        orig = readme.read_text(encoding="utf-8")
        readme.write_text(orig.replace("Never charge twice", "May charge twice"), encoding="utf-8")
        self.git("add", "SSOT/README.md")
        res = self.git("commit", "-m", "tamper via checkout symlink")
        self.assertEqual(res.returncode, 1, res.stdout + res.stderr)
        self.assertIn("confirmed invariant INV-01 changed its rule", res.stdout + res.stderr)

        # 2. Symlink to standalone hook (no adjacent skills/) finds global ~/.codex/skills.
        hook_dst.unlink()
        hook_dst.symlink_to(self.standalone)
        codex_chk = self.home / ".codex/skills/ssot-doctor/assets/scripts/ssot-check.py"
        codex_chk.parent.mkdir(parents=True)
        shutil.copy2(CHECKER, codex_chk)
        res_global = self.git("commit", "-m", "tamper via global codex checker")
        self.assertEqual(res_global.returncode, 1, res_global.stdout + res_global.stderr)
        self.assertIn("confirmed invariant INV-01 changed its rule", res_global.stdout + res_global.stderr)
        readme.write_text(orig, encoding="utf-8")
        self.git("reset", "-q", "HEAD", "SSOT/README.md")

    def test_staged_tamper_blocked_even_when_working_tree_reverted(self):
        readme = self.repo / "SSOT/README.md"
        orig = readme.read_text(encoding="utf-8")
        readme.write_text(orig.replace("Never charge twice", "May charge twice"), encoding="utf-8")
        self.git("add", "SSOT/README.md")
        # Revert working tree without unstaging: index still carries the tampered invariant.
        readme.write_text(orig, encoding="utf-8")
        res = self.git("commit", "-m", "staged tamper clean wt")
        self.assertEqual(res.returncode, 1, res.stdout + res.stderr)
        self.assertIn("confirmed invariant INV-01 changed its rule", res.stdout + res.stderr)
        self.assertIn("Never charge twice", self.git("show", "HEAD:SSOT/README.md").stdout)

    def test_clean_staged_doc_passes_despite_dirty_unstaged_ssot(self):
        readme = self.repo / "SSOT/README.md"
        orig = readme.read_text(encoding="utf-8")
        readme.write_text(orig.replace("Never charge twice", "Unstaged WIP edit"), encoding="utf-8")
        api = self.repo / "docs/api.md"
        api.write_text("# API\n\n## Retries\n\nIdempotent retry behavior with backoff.\n", encoding="utf-8")
        self.git("add", "docs/api.md")
        res = self.git("commit", "-m", "clean staged doc")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        # Unstaged WIP in working tree remains untouched.
        self.assertIn("Unstaged WIP edit", readme.read_text(encoding="utf-8"))

    def test_commit_only_and_custom_git_index_file_check_staged_index(self):
        readme = self.repo / "SSOT/README.md"
        orig = readme.read_text(encoding="utf-8")
        # Dirty staged SSOT in default index, but `git commit --only docs/api.md` commits only docs/api.md.
        readme.write_text(orig.replace("Never charge twice", "Dirty staged edit"), encoding="utf-8")
        self.git("add", "SSOT/README.md")
        api = self.repo / "docs/api.md"
        api.write_text("# API\n\n## Retries\n\nClarified retry wording.\n", encoding="utf-8")
        res_only = self.git("commit", "--only", "docs/api.md", "-m", "only api doc")
        self.assertEqual(res_only.returncode, 0, res_only.stdout + res_only.stderr)

        # Custom GIT_INDEX_FILE holding a tampered SSOT while default index and WT are clean must block.
        readme.write_text(orig, encoding="utf-8")
        self.git("reset", "-q", "HEAD", "SSOT/README.md")
        custom_idx = Path(self.tmp.name) / "custom.index"
        shutil.copy2(self.repo / ".git/index", custom_idx)
        custom_env = {**self.env, "GIT_INDEX_FILE": str(custom_idx)}
        readme.write_text(orig.replace("Never charge twice", "Custom index tamper"), encoding="utf-8")
        self.git("add", "SSOT/README.md", env=custom_env)
        readme.write_text(orig, encoding="utf-8")
        direct = subprocess.run([str(self.standalone)], cwd=self.repo, env=custom_env, capture_output=True, text=True)
        self.assertEqual(direct.returncode, 1, direct.stdout + direct.stderr)
        self.assertIn("confirmed invariant INV-01 changed its rule", direct.stdout + direct.stderr)

    def test_linked_worktree_diffs_against_worktree_head_not_main_head(self):
        wt = Path(self.tmp.name) / "linked-wt"
        res_add = self.git("worktree", "add", "-q", "-b", "feature", str(wt))
        self.assertEqual(res_add.returncode, 0, res_add.stdout + res_add.stderr)
        # Copy repo-local checker into the linked worktree (since .agents was committed in repo).
        wt_readme = wt / "SSOT/README.md"
        # Legitimately update INV-01 in worktree HEAD with a new dated Source so worktree HEAD != main HEAD.
        wt_text = wt_readme.read_text(encoding="utf-8").replace(
            "Never charge twice | [Retries](../docs/api.md#retries) | confirmed | user, 2026-05-02",
            "Never charge twice; refund in 24h | [Retries](../docs/api.md#retries) | confirmed | user, 2026-05-02; revised 2026-11-25",
        )
        wt_readme.write_text(wt_text, encoding="utf-8")
        r_add = subprocess.run(["git", "add", "SSOT/README.md"], cwd=wt, env=self.env, capture_output=True, text=True)
        self.assertEqual(r_add.returncode, 0, r_add.stderr)
        r_com = subprocess.run(["git", "commit", "-m", "approved wt update"], cwd=wt, env=self.env, capture_output=True, text=True)
        self.assertEqual(r_com.returncode, 0, r_com.stdout + r_com.stderr)

        # 1. Dirty unstaged SSOT/README.md + clean staged docs/api.md triggers snapshot mode.
        # Comparing against main HEAD would falsely fail on INV-01; comparing against worktree HEAD passes.
        wt_readme.write_text(wt_text.replace("refund in 24h", "dirty unstaged"), encoding="utf-8")
        (wt / "docs/api.md").write_text("# API\n\n## Retries\n\nWorktree doc update.\n", encoding="utf-8")
        subprocess.run(["git", "add", "docs/api.md"], cwd=wt, env=self.env, check=True)
        r_clean = subprocess.run(["git", "commit", "-m", "clean wt doc"], cwd=wt, env=self.env, capture_output=True, text=True)
        self.assertEqual(r_clean.returncode, 0, r_clean.stdout + r_clean.stderr)

        # 2. Staged tamper relative to worktree HEAD with reverted WT must block.
        wt_readme.write_text(wt_text.replace("refund in 24h", "unauthorized tamper"), encoding="utf-8")
        subprocess.run(["git", "add", "SSOT/README.md"], cwd=wt, env=self.env, check=True)
        wt_readme.write_text(wt_text, encoding="utf-8")
        r_tamper = subprocess.run(["git", "commit", "-m", "tamper wt"], cwd=wt, env=self.env, capture_output=True, text=True)
        self.assertEqual(r_tamper.returncode, 1, r_tamper.stdout + r_tamper.stderr)
        self.assertIn("confirmed invariant INV-01 changed its rule", r_tamper.stdout + r_tamper.stderr)

    def test_blocks_whole_ssot_deletion_format4_cached_and_format5(self):
        # 1. `git rm -r --cached SSOT` (still on disk) must be blocked.
        self.git("rm", "-rq", "--cached", "SSOT")
        res_cached = self.git("commit", "-m", "untrack whole SSOT")
        self.assertEqual(res_cached.returncode, 1, res_cached.stdout + res_cached.stderr)
        self.assertIn("removes tracked SSOT target 'SSOT'", res_cached.stderr)
        self.git("reset", "-q", "HEAD", "SSOT")

        # 2. `git rm -r SSOT` (deleted from index and disk) must be blocked.
        self.git("rm", "-rq", "SSOT")
        res_rm = self.git("commit", "-m", "delete whole SSOT")
        self.assertEqual(res_rm.returncode, 1, res_rm.stdout + res_rm.stderr)
        self.assertIn("removes tracked SSOT target 'SSOT'", res_rm.stderr)
        self.assertIn("--no-verify", res_rm.stderr)
        self.git("checkout", "HEAD", "--", "SSOT")

        # 3. Format-5 single-file entry deletion (`SSOT_DIR=docs/context.md`) must be blocked.
        f5 = self.repo / "docs/context.md"
        f5.write_text(textwrap.dedent("""\
            ---
            ssot_format: 5
            language: en
            ---
            # Space

            ## Invariants

            | ID | Kind | Rule | Explained in | Status | Source |
            |---|---|---|---|---|---|
            | F5-01 | product promise | Keep history | [Space](context.md#space) | confirmed | user, 2026-05-02 |
            """), encoding="utf-8")
        self.git("add", "docs/context.md")
        env_f5 = {**self.env, "SSOT_DIR": "docs/context.md"}
        res_init = self.git("commit", "-m", "add f5 space", env=env_f5)
        self.assertEqual(res_init.returncode, 0, res_init.stdout + res_init.stderr)
        self.git("rm", "-q", "docs/context.md")
        res_f5_rm = self.git("commit", "-m", "delete f5 space", env=env_f5)
        self.assertEqual(res_f5_rm.returncode, 1, res_f5_rm.stdout + res_f5_rm.stderr)
        self.assertIn("removes tracked SSOT target 'docs/context.md'", res_f5_rm.stderr)

    def test_ssot_dir_trailing_slash_triggers_on_non_markdown_inside_ssot(self):
        marker = Path(self.tmp.name) / "slash-ran"
        sentinel = Path(self.tmp.name) / "slash-sentinel.py"
        sentinel.write_text(f"import pathlib, sys\npathlib.Path({str(marker)!r}).write_text('ran')\nsys.exit(0)\n", encoding="utf-8")
        (self.repo / "SSOT/data.txt").write_text("metadata\n", encoding="utf-8")
        self.git("add", "SSOT/data.txt")
        env = {**self.env, "SSOT_DIR": "SSOT/", "SSOT_CHECKER": str(sentinel)}
        res = self.git("commit", "-m", "add non-md in SSOT", env=env)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertTrue(marker.exists(), "SSOT_DIR with trailing slash should still trigger on files inside SSOT/")

    def test_missing_python3_respects_strict_flag(self):
        # Build a minimal PATH directory with git/bash/coreutils but NO python3.
        no_py_bin = Path(self.tmp.name) / "no-python-bin"
        no_py_bin.mkdir()
        for tool in ("bash", "git", "env", "dirname", "basename", "readlink", "mktemp", "rm", "tr"):
            found = shutil.which(tool)
            if found:
                (no_py_bin / tool).symlink_to(found)
        (self.repo / "SSOT/architecture.md").write_text("# Architecture\n\nNo-python test.\n", encoding="utf-8")
        self.git("add", "SSOT/architecture.md")
        base_no_py = {**self.env, "PATH": str(no_py_bin)}

        # STRICT=1 exits 2 with clear python3 error (not 127 blaming ssot-check.py).
        strict_direct = subprocess.run([str(self.standalone)], cwd=self.repo,
                                       env={**base_no_py, "SSOT_PRECOMMIT_STRICT": "1"}, capture_output=True, text=True)
        self.assertEqual(strict_direct.returncode, 2, strict_direct.stdout + strict_direct.stderr)
        self.assertIn("python3 not found", strict_direct.stderr)
        self.assertNotIn("blocked by ssot-check.py", strict_direct.stderr)

        # STRICT=0 soft-skips with exit 0 and clear message.
        soft_commit = self.git("commit", "-m", "commit without python3", env=base_no_py)
        self.assertEqual(soft_commit.returncode, 0, soft_commit.stdout + soft_commit.stderr)
        self.assertIn("python3 not found; skipping", soft_commit.stderr)

    def test_clean_commit_uses_direct_path_and_unborn_head_uses_snapshot(self):
        # 1. Clean staged SSOT edit + unrelated dirty non-.md code file keeps direct fast path (argv[1] == 'SSOT').
        arg_log = Path(self.tmp.name) / "checker-arg"
        recorder = Path(self.tmp.name) / "record-checker.py"
        recorder.write_text(
            f"import pathlib, sys\npathlib.Path({str(arg_log)!r}).write_text(sys.argv[1])\nsys.exit(0)\n",
            encoding="utf-8",
        )
        (self.repo / "src/app.py").write_text("x = 999\n", encoding="utf-8")  # unstaged non-.md edit
        (self.repo / "SSOT/architecture.md").write_text("# Architecture\n\nClean direct check.\n", encoding="utf-8")
        self.git("add", "SSOT/architecture.md")
        res = self.git("commit", "-m", "direct check", env={**self.env, "SSOT_CHECKER": str(recorder)})
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertEqual(arg_log.read_text(encoding="utf-8"), "SSOT")

        # 2. Unborn HEAD with staged broken link + fixed WT catches the staged broken link via snapshot.
        fresh = Path(self.tmp.name) / "unborn-repo"
        fresh.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=fresh, env=self.env, check=True)
        (fresh / ".git/hooks/pre-commit").symlink_to(HOOK)
        (fresh / "SSOT").mkdir()
        broken = "---\nssot_format: 4\nlanguage: en\n---\n# Demo\n\n- [Missing](missing.md)\n\n## Invariants\n\nNone.\n"
        fixed = "---\nssot_format: 4\nlanguage: en\n---\n# Demo\n\n## Invariants\n\nNone.\n"
        (fresh / "SSOT/README.md").write_text(broken, encoding="utf-8")
        subprocess.run(["git", "add", "SSOT/README.md"], cwd=fresh, env=self.env, check=True)
        (fresh / "SSOT/README.md").write_text(fixed, encoding="utf-8")
        r_unborn = subprocess.run(["git", "commit", "-m", "initial broken"], cwd=fresh, env=self.env, capture_output=True, text=True)
        self.assertEqual(r_unborn.returncode, 1, r_unborn.stdout + r_unborn.stderr)
        self.assertIn("broken link: missing.md", r_unborn.stdout + r_unborn.stderr)

    def test_blocks_staged_link_to_untracked_external_owner_and_non_md_file(self):
        # 1. Untracked Format-4 external owner linked from staged SSOT/README.md must fail before commit.
        (self.repo / "docs/new-owner.md").write_text("# New Owner\n\n## Details\n\nBody.\n", encoding="utf-8")
        readme = self.repo / "SSOT/README.md"
        orig = readme.read_text(encoding="utf-8")
        readme.write_text(orig + "\n- [New Owner](../docs/new-owner.md#details)\n", encoding="utf-8")
        self.git("add", "SSOT/README.md")
        res_md = self.git("commit", "-m", "link untracked owner")
        self.assertEqual(res_md.returncode, 1, res_md.stdout + res_md.stderr)
        self.assertIn("broken link: ../docs/new-owner.md#details", res_md.stdout + res_md.stderr)

        # 2. Untracked non-Markdown file linked from staged SSOT/README.md must also fail.
        (self.repo / "src/new_helper.txt").write_text("helper\n", encoding="utf-8")
        readme.write_text(orig + "\n- [Helper](../src/new_helper.txt)\n", encoding="utf-8")
        self.git("add", "SSOT/README.md")
        res_txt = self.git("commit", "-m", "link untracked non-md")
        self.assertEqual(res_txt.returncode, 1, res_txt.stdout + res_txt.stderr)
        self.assertIn("broken link: ../src/new_helper.txt", res_txt.stdout + res_txt.stderr)

        # 3. Once both targets are staged, targeted snapshot checks them out and commit succeeds.
        readme.write_text(orig + "\n- [New Owner](../docs/new-owner.md#details)\n- [Helper](../src/new_helper.txt)\n", encoding="utf-8")
        self.git("add", "SSOT/README.md", "docs/new-owner.md", "src/new_helper.txt")
        res_ok = self.git("commit", "-m", "commit owner and helper together")
        self.assertEqual(res_ok.returncode, 0, res_ok.stdout + res_ok.stderr)

    def test_canonicalizes_absolute_ssot_dir_handles_format4_readme_and_rejects_outside(self):
        readme = self.repo / "SSOT/README.md"
        orig = readme.read_text(encoding="utf-8")
        readme.write_text(orig.replace("Never charge twice", "Tampered via abs SSOT_DIR"), encoding="utf-8")
        self.git("add", "SSOT/README.md")
        # Force snapshot mode via an unstaged edit to docs/api.md.
        (self.repo / "docs/api.md").write_text("# API\n\n## Retries\n\nUnstaged.\n", encoding="utf-8")

        # 1. Absolute SSOT_DIR inside repo must block tampered confirmed invariant (never silent exit 0).
        res_abs = self.git("commit", "-m", "abs ssot dir", env={**self.env, "SSOT_DIR": str(self.repo / "SSOT")})
        self.assertEqual(res_abs.returncode, 1, res_abs.stdout + res_abs.stderr)
        self.assertIn("confirmed invariant INV-01 changed its rule", res_abs.stdout + res_abs.stderr)

        # 2. Format-4 SSOT_DIR=SSOT/README.md resolves to its containing SSOT directory and blocks tamper.
        res_f4_file = self.git("commit", "-m", "f4 readme file", env={**self.env, "SSOT_DIR": "SSOT/README.md"})
        self.assertEqual(res_f4_file.returncode, 1, res_f4_file.stdout + res_f4_file.stderr)
        self.assertIn("confirmed invariant INV-01 changed its rule", res_f4_file.stdout + res_f4_file.stderr)

        # 3. SSOT_DIR outside repo fails loudly with exit 2.
        direct_out = subprocess.run([str(self.standalone)], cwd=self.repo,
                                    env={**self.env, "SSOT_DIR": str(self.home)}, capture_output=True, text=True)
        self.assertEqual(direct_out.returncode, 2, direct_out.stdout + direct_out.stderr)
        self.assertIn("outside repository root", direct_out.stderr)

        # 4. Clean edit with SSOT_DIR=SSOT/README.md passes.
        readme.write_text(orig + "\nExtra note.\n", encoding="utf-8")
        self.git("add", "SSOT/README.md")
        res_clean = self.git("commit", "-m", "clean f4 readme", env={**self.env, "SSOT_DIR": "SSOT/README.md"})
        self.assertEqual(res_clean.returncode, 0, res_clean.stdout + res_clean.stderr)

    def test_triggers_on_mixed_case_markdown_extension(self):
        (self.repo / "docs/Guide.Md").write_text("# Guide\n\n## Sec\n\nText.\n", encoding="utf-8")
        readme = self.repo / "SSOT/README.md"
        readme.write_text(readme.read_text(encoding="utf-8") + "\n- [Guide](../docs/Guide.Md#sec)\n", encoding="utf-8")
        self.git("add", "docs/Guide.Md", "SSOT/README.md")
        self.assertEqual(self.git("commit", "-m", "add Guide.Md").returncode, 0)

        (self.repo / "docs/Guide.Md").write_text("# Guide\n\n## Renamed\n\nText.\n", encoding="utf-8")
        self.git("add", "docs/Guide.Md")
        res = self.git("commit", "-m", "break mixed-case md anchor")
        self.assertEqual(res.returncode, 1, res.stdout + res.stderr)
        self.assertIn("missing heading anchor: ../docs/Guide.Md#sec", res.stdout + res.stderr)

    def test_targeted_snapshot_preserves_linked_non_md_symlinks_and_skip_worktree_mentions(self):
        # Link a non-md file with line anchor, a symlink to a non-md file, and keep a non-linked file mentioned in backticks.
        (self.repo / "docs/app-link.py").symlink_to("../src/app.py")
        readme = self.repo / "SSOT/README.md"
        orig = readme.read_text(encoding="utf-8")
        readme.write_text(orig + "\n- [App](../src/app.py#L1)\n- [Link](../docs/app-link.py)\n", encoding="utf-8")
        self.git("add", "docs/app-link.py", "SSOT/README.md")
        # Force snapshot mode with an unstaged edit to docs/api.md.
        (self.repo / "docs/api.md").write_text("# API\n\n## Retries\n\nUnstaged.\n", encoding="utf-8")
        res_ok = self.git("commit", "-m", "linked non-md and symlink in snapshot")
        self.assertEqual(res_ok.returncode, 0, res_ok.stdout + res_ok.stderr)
        self.assertNotIn("`src/app.py` was removed", res_ok.stdout + res_ok.stderr)
        self.assertNotIn("`src/legacy.py` was removed", res_ok.stdout + res_ok.stderr)

        # Line anchor past EOF in non-md file must still be caught in targeted snapshot mode.
        readme.write_text(orig + "\n- [App](../src/app.py#L999)\n", encoding="utf-8")
        self.git("add", "SSOT/README.md")
        res_bad = self.git("commit", "-m", "bad line anchor in snapshot")
        self.assertEqual(res_bad.returncode, 1, res_bad.stdout + res_bad.stderr)
        self.assertIn("line anchor past end of file", res_bad.stdout + res_bad.stderr)

    def test_custom_sentinel_checker_with_module_level_exit_falls_back_in_snapshot_mode(self):
        # A custom SSOT_CHECKER calling sys.exit(0) at module level must not execute during
        # stage_targeted_snapshot import; hook must fall back to full checkout-index -a and run it once.
        log_file = Path(self.tmp.name) / "sentinel-calls.log"
        sentinel = Path(self.tmp.name) / "exit-sentinel.py"
        sentinel.write_text(
            f"import os, pathlib, sys\n"
            f"p = pathlib.Path({str(log_file)!r})\n"
            f"target = sys.argv[1] if len(sys.argv) > 1 else ''\n"
            f"p.open('a', encoding='utf-8').write(f'{{target}}|{{os.path.isdir(target)}}\\n')\n"
            f"sys.exit(0)\n",
            encoding="utf-8",
        )
        (self.repo / "untracked.txt").write_text("forces snapshot mode\n", encoding="utf-8")
        (self.repo / "SSOT/architecture.md").write_text("# Architecture\n\nSentinel snapshot check.\n", encoding="utf-8")
        self.git("add", "SSOT/architecture.md")
        res = self.git("commit", "-m", "sentinel in snapshot mode", env={**self.env, "SSOT_CHECKER": str(sentinel)})
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        calls = log_file.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(calls), 1, f"expected checker to execute once, got: {calls}")
        self.assertTrue(calls[0].endswith("/SSOT|True"), calls[0])

    def test_format4_readme_ssot_dir_in_snapshot_mode_preserves_non_md_ssot_files(self):
        # Tracked non-.md files inside SSOT/ (e.g. .bootstrap/state.json) must still be materialized
        # in targeted snapshot mode when SSOT_DIR=SSOT/README.md.
        (self.repo / "SSOT/.bootstrap").mkdir()
        (self.repo / "SSOT/.bootstrap/state.json").write_text('{"legacy": true}\n', encoding="utf-8")
        self.git("add", "SSOT/.bootstrap/state.json")
        (self.repo / "untracked.txt").write_text("forces snapshot mode\n", encoding="utf-8")
        res = self.git("commit", "-m", "f4 readme snapshot preserves non-md ssot files",
                       env={**self.env, "SSOT_DIR": "SSOT/README.md"})
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("v2 ledger left after migration", res.stdout + res.stderr)

    def test_shallow_clone_snapshot_mode_succeeds_and_still_blocks_tamper(self):
        # Create a second commit so a depth-1 clone has a real shallow graft boundary.
        (self.repo / "src/extra.py").write_text("y = 2\n", encoding="utf-8")
        self.git("add", "src/extra.py")
        self.assertEqual(self.git("commit", "-m", "second commit").returncode, 0)

        shallow = Path(self.tmp.name) / "shallow-clone"
        subprocess.run(
            ["git", "clone", "-q", "--depth", "1", f"file://{self.repo}", str(shallow)],
            env=self.env, check=True,
        )
        hook_dst = shallow / ".git/hooks/pre-commit"
        hook_dst.write_text(f'#!/usr/bin/env bash\nexec "{self.standalone}" "$@"\n', encoding="utf-8")
        hook_dst.chmod(0o755)
        # Force snapshot mode with an unstaged edit to docs/api.md.
        (shallow / "docs/api.md").write_text("# API\n\n## Retries\n\nUnstaged local note.\n", encoding="utf-8")
        (shallow / "SSOT/architecture.md").write_text(
            "# Architecture\n\nActive code is in `src/app.py`; `src/extra.py` is helper.\n", encoding="utf-8"
        )
        subprocess.run(["git", "add", "SSOT/architecture.md"], cwd=shallow, env=self.env, check=True)
        res_ok = subprocess.run(
            ["git", "commit", "-m", "shallow snapshot clean"],
            cwd=shallow, env=self.env, capture_output=True, text=True,
        )
        self.assertEqual(res_ok.returncode, 0, res_ok.stdout + res_ok.stderr)
        self.assertNotIn("INCOMPLETE", res_ok.stdout + res_ok.stderr)

        # Tampered confirmed invariant in shallow snapshot mode must still be blocked (exit 1, not 3).
        readme = shallow / "SSOT/README.md"
        readme.write_text(
            readme.read_text(encoding="utf-8").replace("Never charge twice", "Shallow tamper"),
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "SSOT/README.md"], cwd=shallow, env=self.env, check=True)
        res_bad = subprocess.run(
            ["git", "commit", "-m", "shallow snapshot tamper"],
            cwd=shallow, env=self.env, capture_output=True, text=True,
        )
        self.assertEqual(res_bad.returncode, 1, res_bad.stdout + res_bad.stderr)
        self.assertIn("confirmed invariant INV-01 changed its rule", res_bad.stdout + res_bad.stderr)

    def test_submodule_160000_link_matches_direct_mode_in_targeted_and_fallback_snapshots(self):
        sub_origin = Path(self.tmp.name) / "sub-origin"
        sub_origin.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=sub_origin, env=self.env, check=True)
        (sub_origin / "README.md").write_text("# Submodule\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=sub_origin, env=self.env, check=True)
        subprocess.run(["git", "commit", "-qm", "sub init"], cwd=sub_origin, env=self.env, check=True)

        res_sub = self.git("-c", "protocol.file.allow=always", "submodule", "add", "-q", str(sub_origin), "plugins/sub")
        self.assertEqual(res_sub.returncode, 0, res_sub.stdout + res_sub.stderr)
        readme = self.repo / "SSOT/README.md"
        readme.write_text(
            readme.read_text(encoding="utf-8") + "\n- [Sub](../plugins/sub/README.md)\n",
            encoding="utf-8",
        )
        self.git("add", ".gitmodules", "plugins/sub", "SSOT/README.md")
        # Force targeted snapshot mode with an unstaged edit to docs/api.md.
        (self.repo / "docs/api.md").write_text("# API\n\n## Retries\n\nUnstaged.\n", encoding="utf-8")
        res_snap = self.git("commit", "-m", "link submodule in snapshot")
        self.assertEqual(res_snap.returncode, 0, res_snap.stdout + res_snap.stderr)
        self.assertIn("nested repository/submodule is not populated here", res_snap.stdout + res_snap.stderr)
        self.assertNotIn("link leaves the repository", res_snap.stdout + res_snap.stderr)
        self.assertNotIn("broken link", res_snap.stdout + res_snap.stderr)
        self.assertFalse(
            (self.repo / ".agents/skills/ssot-doctor/assets/scripts/__pycache__").exists(),
            "targeted snapshot must invoke python3 -B and never write __pycache__ into the consumer repo",
        )

        # Also test the fallback checkout-index -a snapshot path by wrapping ssot-check.py in a non-importable shim.
        wrapper = Path(self.tmp.name) / "wrap-checker.py"
        wrapper.write_text(
            f"import subprocess, sys\nraise SystemExit(subprocess.call([sys.executable, {str(CHECKER)!r}, *sys.argv[1:]]))\n",
            encoding="utf-8",
        )
        (self.repo / "SSOT/architecture.md").write_text("# Architecture\n\nFallback submodule test.\n", encoding="utf-8")
        self.git("add", "SSOT/architecture.md")
        res_fb = self.git("commit", "-m", "submodule fallback snapshot", env={**self.env, "SSOT_CHECKER": str(wrapper)})
        self.assertEqual(res_fb.returncode, 0, res_fb.stdout + res_fb.stderr)
        self.assertIn("nested repository/submodule is not populated here", res_fb.stdout + res_fb.stderr)
        self.assertNotIn("link leaves the repository", res_fb.stdout + res_fb.stderr)
        self.assertNotIn("broken link", res_fb.stdout + res_fb.stderr)

        # Clean direct-mode commit with a valid populated submodule link passes with 0 warnings,
        # while a broken heading anchor inside the populated submodule is blocked.
        self.git("checkout", "--", "docs/api.md")
        readme.write_text(
            readme.read_text(encoding="utf-8") + "- [Sub Heading](../plugins/sub/README.md#submodule)\n",
            encoding="utf-8",
        )
        self.git("add", "SSOT/README.md")
        res_direct = self.git("commit", "-m", "valid populated submodule anchor")
        self.assertEqual(res_direct.returncode, 0, res_direct.stdout + res_direct.stderr)
        self.assertIn("0 error(s), 0 warning(s)", res_direct.stdout + res_direct.stderr)

        readme.write_text(
            readme.read_text(encoding="utf-8") + "- [Bad Sub Anchor](../plugins/sub/README.md#missing-anchor)\n",
            encoding="utf-8",
        )
        self.git("add", "SSOT/README.md")
        res_bad_anchor = self.git("commit", "-m", "broken populated submodule anchor")
        self.assertEqual(res_bad_anchor.returncode, 1, res_bad_anchor.stdout + res_bad_anchor.stderr)
        self.assertIn("missing heading anchor", res_bad_anchor.stdout + res_bad_anchor.stderr)

    def test_split_git_dir_and_work_tree_runs_cleanly_and_blocks_tamper(self):
        git_dir = Path(self.tmp.name) / "split.git"
        work_tree = Path(self.tmp.name) / "split-wt"
        work_tree.mkdir()
        split_base = ["git", f"--git-dir={git_dir}", f"--work-tree={work_tree}"]
        subprocess.run([*split_base, "init", "-q"], env=self.env, check=True)
        hook_dst = git_dir / "hooks/pre-commit"
        hook_dst.write_text(f'#!/usr/bin/env bash\nexec "{self.standalone}" "$@"\n', encoding="utf-8")
        hook_dst.chmod(0o755)
        (work_tree / "SSOT").mkdir()
        (work_tree / "SSOT/arch.md").write_text("# Arch\n\nDetails.\n", encoding="utf-8")
        readme_text = textwrap.dedent("""\
            ---
            ssot_format: 4
            language: en
            ---
            # Split

            ## Map

            - [Arch](arch.md)

            ## Invariants

            | ID | Kind | Rule | Explained in | Status | Source |
            |---|---|---|---|---|---|
            | SPL-01 | product promise | Stay intact | [Arch](arch.md) | confirmed | user, 2026-05-02 |
            """)
        (work_tree / "SSOT/README.md").write_text(readme_text, encoding="utf-8")
        local_chk = work_tree / ".agents/skills/ssot-doctor/assets/scripts/ssot-check.py"
        local_chk.parent.mkdir(parents=True)
        shutil.copy2(CHECKER, local_chk)
        subprocess.run([*split_base, "add", "."], env=self.env, check=True)
        res_init = subprocess.run([*split_base, "commit", "-m", "initial split"], env=self.env, capture_output=True, text=True)
        self.assertEqual(res_init.returncode, 0, res_init.stdout + res_init.stderr)

        # Clean follow-up commit must succeed (no exit 128 from git_clean).
        (work_tree / "SSOT/arch.md").write_text("# Arch\n\nUpdated details.\n", encoding="utf-8")
        subprocess.run([*split_base, "add", "SSOT/arch.md"], env=self.env, check=True)
        res_clean = subprocess.run([*split_base, "commit", "-m", "clean split update"], env=self.env, capture_output=True, text=True)
        self.assertEqual(res_clean.returncode, 0, res_clean.stdout + res_clean.stderr)

        # Tampered confirmed invariant must be blocked with exit 1.
        (work_tree / "SSOT/README.md").write_text(readme_text.replace("Stay intact", "Tampered"), encoding="utf-8")
        subprocess.run([*split_base, "add", "SSOT/README.md"], env=self.env, check=True)
        res_bad = subprocess.run([*split_base, "commit", "-m", "tamper split"], env=self.env, capture_output=True, text=True)
        self.assertEqual(res_bad.returncode, 1, res_bad.stdout + res_bad.stderr)
        self.assertIn("confirmed invariant SPL-01 changed its rule", res_bad.stdout + res_bad.stderr)

    def test_staged_mdc_cursorrules_and_windsurfrules_trigger_hook(self):
        for idx, rel in enumerate((".cursor/rules/ssot.mdc", ".cursorrules", ".windsurfrules")):
            marker = Path(self.tmp.name) / f"instr-ran-{idx}"
            sentinel = Path(self.tmp.name) / f"instr-sentinel-{idx}.py"
            sentinel.write_text(
                f"import pathlib, sys\npathlib.Path({str(marker)!r}).write_text('ran')\nsys.exit(0)\n",
                encoding="utf-8",
            )
            target = self.repo / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f"# rule {idx}\n", encoding="utf-8")
            self.git("add", rel)
            res = self.git("commit", "-m", f"add {rel}", env={**self.env, "SSOT_CHECKER": str(sentinel)})
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
            self.assertTrue(marker.exists(), f"staging {rel} should trigger the pre-commit guard")

    def test_find_checker_discovers_copilot_opencode_amp_antigravity_cli_and_dsh(self):
        shutil.rmtree(self.repo / ".agents")
        hook_dst = self.repo / ".git/hooks/pre-commit"
        hook_dst.unlink()
        hook_dst.symlink_to(self.standalone)

        readme = self.repo / "SSOT/README.md"
        orig = readme.read_text(encoding="utf-8")
        readme.write_text(orig.replace("Never charge twice", "Global discovery tamper"), encoding="utf-8")
        self.git("add", "SSOT/README.md")

        rel = Path("ssot-doctor/assets/scripts/ssot-check.py")
        cases = [
            ("copilot", self.home / ".copilot/skills" / rel, {}),
            ("opencode", Path(self.tmp.name) / "xdg/opencode/skills" / rel, {"XDG_CONFIG_HOME": str(Path(self.tmp.name) / "xdg")}),
            ("amp", Path(self.tmp.name) / "xdg2/agents/skills" / rel, {"XDG_CONFIG_HOME": str(Path(self.tmp.name) / "xdg2")}),
            ("antigravity-cli", self.home / ".gemini/antigravity-cli/skills" / rel, {}),
            ("dsh-home", Path(self.tmp.name) / "custom-dsh/skills" / rel, {"DSH_HOME": str(Path(self.tmp.name) / "custom-dsh")}),
            ("dsh-default", self.home / ".dsh/skills" / rel, {}),
        ]
        for label, chk_path, extra_env in cases:
            with self.subTest(agent=label):
                chk_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(CHECKER, chk_path)
                try:
                    env = {**self.env, **extra_env}
                    env.pop("DSH_HOME", None)
                    env.pop("XDG_CONFIG_HOME", None)
                    env.update(extra_env)
                    res = self.git("commit", "-m", f"tamper via {label}", env=env)
                    self.assertEqual(res.returncode, 1, res.stdout + res.stderr)
                    self.assertIn("confirmed invariant INV-01 changed its rule", res.stdout + res.stderr)
                finally:
                    chk_path.unlink()
        readme.write_text(orig, encoding="utf-8")
        self.git("reset", "-q", "HEAD", "SSOT/README.md")

    def test_hook_works_inside_git_submodule_where_dotgit_is_file(self):
        parent = Path(self.tmp.name) / "parent-repo"
        parent.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=parent, env=self.env, check=True)
        res_add = subprocess.run(
            ["git", "-c", "protocol.file.allow=always", "submodule", "add", "-q", str(self.repo), "plugins/child"],
            cwd=parent, env=self.env, capture_output=True, text=True,
        )
        self.assertEqual(res_add.returncode, 0, res_add.stdout + res_add.stderr)
        child = parent / "plugins/child"
        self.assertTrue((child / ".git").is_file(), "submodule .git must be a regular file")

        common_dir = subprocess.check_output(
            ["git", "rev-parse", "--git-common-dir"], cwd=child, env=self.env, text=True
        ).strip()
        common_path = (child / common_dir).resolve()
        hook_dst = common_path / "hooks/pre-commit"
        hook_dst.parent.mkdir(parents=True, exist_ok=True)
        hook_dst.write_text(f'#!/usr/bin/env bash\nexec "{self.standalone}" "$@"\n', encoding="utf-8")
        hook_dst.chmod(0o755)

        # 1. Clean commit inside submodule passes.
        (child / "SSOT/architecture.md").write_text("# Architecture\n\nSubmodule clean edit.\n", encoding="utf-8")
        subprocess.run(["git", "add", "SSOT/architecture.md"], cwd=child, env=self.env, check=True)
        r_clean = subprocess.run(["git", "commit", "-m", "sub clean"], cwd=child, env=self.env, capture_output=True, text=True)
        self.assertEqual(r_clean.returncode, 0, r_clean.stdout + r_clean.stderr)

        # 2. Tampered shard invariant inside submodule (snapshot mode with reverted WT) is blocked.
        shard = child / "SSOT/invariants/shipping.md"
        shard_orig = shard.read_text(encoding="utf-8")
        shard.write_text(shard_orig.replace("Express keeps standard intact", "Submodule tamper"), encoding="utf-8")
        subprocess.run(["git", "add", "SSOT/invariants/shipping.md"], cwd=child, env=self.env, check=True)
        shard.write_text(shard_orig, encoding="utf-8")
        r_bad = subprocess.run(["git", "commit", "-m", "sub tamper"], cwd=child, env=self.env, capture_output=True, text=True)
        self.assertEqual(r_bad.returncode, 1, r_bad.stdout + r_bad.stderr)
        self.assertIn("confirmed invariant SHP-01 changed its rule", r_bad.stdout + r_bad.stderr)

    def test_ast_import_safe_targeted_snapshot_and_nonblocking_compaction_info(self):
        # 1. Verify ssot-check.py still satisfies tools/ssot-precommit.sh's AST import-safety whitelist
        #    so snapshot mode never silently degrades to full checkout-index -a fallback.
        hook_text = HOOK.read_text(encoding="utf-8")
        marker_start = hook_text.index("def is_import_safe_checker(path):")
        marker_end = hook_text.index("\ntry:\n    if not is_import_safe_checker(checker):")
        ns = {}
        exec("import ast\n" + hook_text[marker_start:marker_end], ns)
        self.assertTrue(
            ns["is_import_safe_checker"](str(CHECKER)),
            "ssot-check.py violated tools/ssot-precommit.sh is_import_safe_checker() AST whitelist",
        )

        # 2. Verify compaction INFO + rollup emitted in snapshot mode (triggered by an untracked file)
        #    are strictly non-blocking (commit exits 0) and surface the rollup hint cleanly.
        (self.repo / "untracked-note.txt").write_text("forces snapshot mode\n", encoding="utf-8")
        mid_dated = "# Sync Log\n\n" + "\n\n".join(
            f"## 2026-11-{d:02d} Change {d}\n\n" + ("Chronological entry accumulating in warm owner. " * 38)
            for d in range(1, 7)
        ) + "\n"
        (self.repo / "SSOT/sync.md").write_text(mid_dated, encoding="utf-8")
        (self.repo / "SSOT/workarounds.md").write_text(
            "# Workarounds\n\n" + "\n".join(f"- [x] Fixed shim {i}" for i in range(1, 6)) + "\n",
            encoding="utf-8",
        )
        self.git("add", "SSOT/sync.md", "SSOT/workarounds.md")
        res = self.git("commit", "-m", "add bloated docs with compaction info")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        combined = res.stdout + res.stderr
        self.assertIn("compaction candidates (2):", combined)
        self.assertIn("sync.md", combined)
        self.assertIn("workarounds.md", combined)
        self.assertIn("ssot-check: PASS", combined)


if __name__ == "__main__":
    unittest.main(verbosity=1)
