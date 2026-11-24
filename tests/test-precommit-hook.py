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


if __name__ == "__main__":
    unittest.main(verbosity=1)
