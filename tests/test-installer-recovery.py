#!/usr/bin/env python3
"""Exercise replacement failure through the real installer, in owned locations."""
import hashlib
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parent.parent
INSTALLER = Path(os.environ.get("SSOT_TEST_INSTALLER", ROOT / "install.sh"))
BASH = os.environ.get("SSOT_TEST_BASH", "bash")
SKILLS = ("ssot-preflight", "ssot-bootstrap", "ssot-closeout", "ssot-audit", "ssot-doctor", "ssot-skill")
MARKER = '<!-- SSOT-SKILL bundle companion; owned by install.sh -->'


def digest(root):
    result = {}
    if root.exists():
        for path in sorted(root.rglob("*")):
            name = str(path.relative_to(root))
            if path.is_symlink():
                result[name] = ("link", os.readlink(path))
            elif path.is_file():
                result[name] = ("file", path.stat().st_mode & 0o777, hashlib.sha256(path.read_bytes()).hexdigest())
            elif path.is_dir():
                result[name] = ("directory", path.stat().st_mode & 0o777)
    return result


class RecoveryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.project = self.root / "project [copy]"
        self.project.mkdir()
        self.base = self.project / ".agents/skills"
        self.home = self.root / "home"
        self.home.mkdir()
        self.sources = {}
        for generation in ("old", "new"):
            source = self.root / generation
            source.mkdir()
            shutil.copytree(ROOT / "skills", source / "skills", ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copy2(ROOT / "VERSION", source / "VERSION")
            for skill in SKILLS:
                (source / "skills" / skill / "generation.txt").write_text(generation)
            self.sources[generation] = source
        self.injected = self.root / "injected"
        self.release = self.root / "release"
        self.fakebin = self.root / "tools"
        self.fakebin.mkdir()
        self.write_fault_tools()
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        (self.base / "unrelated-skill").mkdir()
        (self.base / "unrelated-skill/data").write_text("keep")
        (self.base / "SKILL_STYLE.md").write_text("another owner's shared-root file\n")
        self.old = digest(self.base)

    def tearDown(self):
        self.tmp.cleanup()

    def write_fault_tools(self):
        real_mv, real_rm = shutil.which("mv"), shutil.which("rm")
        script = f'''#!{sys.executable}
import os, pathlib, signal, sys, time
args = sys.argv[1:]
tool = pathlib.Path(sys.argv[0]).name
src = pathlib.Path(args[-2]) if len(args) > 1 else pathlib.Path('.')
dst = pathlib.Path(args[-1])
mode = os.environ.get('FAULT_MODE', '')
target = os.environ.get('FAIL_NAME', 'ssot-closeout')
injected = pathlib.Path(os.environ['INJECTED'])
restore = '.backup' in src.parts
promote = any(p.startswith('.ssot-skill-install.') for p in src.parts) and not restore and dst.name == target
if tool == 'rm' and mode == 'commit' and dst.name == '.ssot-transaction' and not injected.exists():
    injected.write_text('commit'); sys.exit(71)
if tool == 'rm' and mode == 'cleanup' and dst.name.startswith('.ssot-skill-install.'):
    injected.write_text('cleanup'); sys.exit(73)
if tool == 'rm' and mode == 'unlock' and dst.name == '.ssot-skill-lock':
    injected.write_text('unlock'); sys.exit(73)
if tool == 'rm' and mode == 'rollback-remove' and dst.name == 'ssot-bootstrap':
    injected.write_text('rollback-remove'); sys.exit(73)
if tool == 'mv' and mode == 'backup' and '.backup' in dst.parts and src.name == target:
    injected.write_text('backup'); sys.exit(71)
if tool == 'mv' and mode == 'rollback' and restore and dst.name == 'ssot-preflight':
    injected.write_text('rollback'); sys.exit(72)
if tool == 'mv' and promote and mode in ('promotion', 'rollback', 'rollback-remove', 'pause', 'term', 'int', 'kill'):
    injected.write_text('promotion')
    if mode == 'pause':
        release = pathlib.Path(os.environ['RELEASE'])
        limit = time.monotonic() + 10
        while not release.exists() and time.monotonic() < limit: time.sleep(0.02)
        if not release.exists(): sys.exit(74)
    elif mode in ('term', 'int', 'kill'):
        sig = {{'term': signal.SIGTERM, 'int': signal.SIGINT, 'kill': signal.SIGKILL}}[mode]
        os.kill(os.getppid(), sig); time.sleep(0.03); sys.exit(128 + sig)
    else:
        sys.exit(71)
os.execv({real_mv!r} if tool == 'mv' else {real_rm!r}, [tool, *args])
'''
        for name in ("mv", "rm"):
            path = self.fakebin / name
            path.write_text(script)
            path.chmod(0o755)

    def command(self, action="install"):
        flags = ["--upgrade"] if action == "upgrade" else ["--uninstall"] if action == "uninstall" else ["--quickstart", "--lang", "zh"]
        return [BASH, str(INSTALLER), *flags, "--non-interactive", "--agent", "codex", "--scope", "project", "--yes"]

    def environment(self, generation="old", fault="", name="ssot-closeout"):
        return {**os.environ, "HOME": str(self.home), "SOURCE_DIR": str(self.sources[generation]), "SSOT_UI_LANG": "en",
                "PATH": str(self.fakebin) + os.pathsep + os.environ["PATH"], "FAULT_MODE": fault, "FAIL_NAME": name,
                "INJECTED": str(self.injected), "RELEASE": str(self.release)}

    def run_installer(self, generation="old", fault="", name="ssot-closeout", action="install"):
        return subprocess.run(self.command(action), cwd=self.project, env=self.environment(generation, fault, name),
                              capture_output=True, text=True, timeout=20)

    def assert_rolled_back(self, fault, name="ssot-closeout"):
        result = self.run_installer("new", fault, name)
        self.assertTrue(self.injected.exists(), "fault did not run")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.old, digest(self.base), "a failed replacement must restore the previous installation")
        retry = self.run_installer("new")
        self.assertEqual(retry.returncode, 0, retry.stdout + retry.stderr)
        self.assert_new_generation()

    def assert_bundle_bytes(self):
        for skill in SKILLS:
            self.assertEqual((self.base / skill / "generation.txt").read_text(), "new")
            expected = digest(self.sources["new"] / "skills" / skill)
            if skill == "ssot-bootstrap":
                # Installation's public layout contract selects and flattens zh.
                prefix = "assets/templates/"
                expected = {(prefix + name[len(prefix + "zh/"):] if name.startswith(prefix + "zh/") else name): value
                            for name, value in expected.items()
                            if not name.startswith(prefix) or name.startswith(prefix + "zh/")}
            # Recreated directories follow the caller's umask. New file bytes,
            # file modes and layout must match; rollback checks directory modes too.
            layout = lambda tree: {name: (value[:1] if value[0] == "directory" else value) for name, value in tree.items()}
            self.assertEqual(layout(expected), layout(digest(self.base / skill)), skill + " must contain the complete selected source")

    def assert_new_generation(self):
        self.assert_bundle_bytes()
        self.assertIn("SSOT", (self.base / "ssot-bootstrap/assets/templates/ssot-readme.md").read_text())
        self.assertIn("language: zh-CN", (self.base / "ssot-bootstrap/assets/templates/ssot-readme.md").read_text())
        self.assertFalse((self.base / "ssot-bootstrap/assets/templates/en").exists())
        self.assertEqual((self.base / "unrelated-skill/data").read_text(), "keep")
        self.assertFalse(list(self.base.glob(".ssot-skill-install.*")))
        self.assertFalse(os.path.lexists(self.base / ".ssot-skill-lock"))

    def recover_retained_attempt(self, stage):
        # The installation guide's recovery procedure, only after our own child
        # is known to have terminated. Preserve partial new entries and metadata.
        self.assertTrue((stage / ".ssot-transaction").is_file())
        rescue = self.base / ".ssot-skill-recovered"
        rescue.mkdir()
        for name in (*SKILLS, "SKILL_STYLE.md"):
            target = self.base / name
            backup = stage / ".backup" / name
            if backup.exists() or backup.is_symlink():
                if target.exists() or target.is_symlink():
                    target.rename(rescue / name)
                backup.rename(target)
            elif (stage / ".touched" / name).exists() and not (stage / ".had-old" / name).exists():
                if target.exists() or target.is_symlink():
                    target.rename(rescue / name)
        lock = self.base / ".ssot-skill-lock"
        own_lock = lock.is_file() and lock.read_text().partition("\n")[2].rstrip("\n") == str(stage)
        stage.rename(rescue / "transaction")
        if own_lock:
            lock.unlink()
        restored = {name: value for name, value in digest(self.base).items()
                    if name != rescue.name and not name.startswith(rescue.name + "/")}
        self.assertEqual(self.old, restored)

    def test_first_promotion_failure_restores_every_previous_file(self):
        self.assert_rolled_back("promotion", "ssot-preflight")

    def test_later_promotion_failure_restores_already_replaced_skills(self):
        self.assert_rolled_back("promotion")

    def test_term_rolls_back_with_cancellation_exit(self):
        result = self.run_installer("new", "term")
        self.assertTrue(self.injected.exists())
        self.assertEqual(result.returncode, 143, result.stdout + result.stderr)
        self.assertEqual(self.old, digest(self.base))

    def test_int_rolls_back_with_cancellation_exit(self):
        result = self.run_installer("new", "int")
        self.assertTrue(self.injected.exists())
        self.assertEqual(result.returncode, 130, result.stdout + result.stderr)
        self.assertEqual(self.old, digest(self.base))

    def test_failed_rollback_retains_backup_and_refuses_rerun(self):
        result = self.run_installer("new", "rollback")
        self.assertNotEqual(result.returncode, 0)
        stages = list(self.base.glob(".ssot-skill-install.*"))
        self.assertEqual(len(stages), 1, result.stdout + result.stderr)
        self.assertEqual((stages[0] / ".backup/ssot-preflight/generation.txt").read_text(), "old")
        self.assertIn(str(stages[0]), result.stderr)
        saved = digest(self.base)
        for action in ("upgrade", "uninstall"):
            retry = self.run_installer("new", action=action)
            self.assertNotEqual(retry.returncode, 0, retry.stdout + retry.stderr)
            self.assertIn(str(stages[0]), retry.stderr)
            self.assertEqual(saved, digest(self.base), "rerun must not overwrite pending recovery state")
        self.recover_retained_attempt(stages[0])
        retry = self.run_installer("new", action="upgrade")
        self.assertEqual(retry.returncode, 0, retry.stdout + retry.stderr)
        self.assert_new_generation()

    def test_kill_retains_recovery_state_and_refuses_rerun(self):
        result = self.run_installer("new", "kill", "ssot-preflight")
        self.assertEqual(result.returncode, -signal.SIGKILL)
        stages = list(self.base.glob(".ssot-skill-install.*"))
        self.assertEqual(len(stages), 1)
        self.assertEqual((stages[0] / ".backup/ssot-preflight/generation.txt").read_text(), "old")
        saved = digest(self.base)
        retry = self.run_installer("new", action="upgrade")
        self.assertNotEqual(retry.returncode, 0)
        self.assertEqual(saved, digest(self.base))
        self.assertIn(str(stages[0]), retry.stderr)
        self.recover_retained_attempt(stages[0])
        retry = self.run_installer("new", action="upgrade")
        self.assertEqual(retry.returncode, 0, retry.stdout + retry.stderr)
        self.assert_new_generation()

    def test_failed_new_install_leaves_no_partial_bundle(self):
        for skill in SKILLS:
            shutil.rmtree(self.base / skill)
        self.old = digest(self.base)
        result = self.run_installer("new", "promotion")
        self.assertTrue(self.injected.exists())
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.old, digest(self.base))

    def test_owned_companion_failure_restores_skills_and_companion(self):
        for generation in ("old", "new"):
            (self.sources[generation] / "skills/SKILL_STYLE.md").write_text(MARKER + "\n" + generation)
        (self.base / "SKILL_STYLE.md").write_text(MARKER + "\nold")
        self.old = digest(self.base)
        self.assert_rolled_back("promotion", "SKILL_STYLE.md")
        self.assertEqual((self.base / "SKILL_STYLE.md").read_text(), MARKER + "\nnew")

    def test_directory_symlink_is_restored_without_touching_its_target(self):
        external = self.root / "external-skill"
        (self.base / "ssot-doctor").rename(external)
        (self.base / "ssot-doctor").symlink_to(external, target_is_directory=True)
        external_before = digest(external)
        self.old = digest(self.base)
        self.assert_rolled_back("promotion", "ssot-skill")
        self.assertEqual(external_before, digest(external))

    def test_backup_rename_failure_keeps_original_entry(self):
        result = self.run_installer("new", "backup")
        self.assertEqual(self.injected.read_text(), "backup")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.old, digest(self.base))

    def test_retired_companion_returns_when_commit_fails(self):
        (self.base / "SKILL_STYLE.md").write_text(MARKER + "\nold")
        self.old = digest(self.base)
        result = self.run_installer("new", "commit")
        self.assertEqual(self.injected.read_text(), "commit")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.old, digest(self.base))
        retry = self.run_installer("new", action="upgrade")
        self.assertEqual(retry.returncode, 0, retry.stdout + retry.stderr)
        self.assert_new_generation()
        self.assertFalse((self.base / "SKILL_STYLE.md").exists())

    def test_postcommit_cleanup_failure_keeps_complete_new_generation(self):
        result = self.run_installer("new", "cleanup")
        self.assertEqual(self.injected.read_text(), "cleanup")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("changes completed", result.stderr)
        self.assert_bundle_bytes()
        stages = list(self.base.glob(".ssot-skill-install.*"))
        self.assertEqual(len(stages), 1)
        self.assertFalse((stages[0] / ".ssot-transaction").exists())
        self.assertFalse((self.base / ".ssot-skill-lock").exists())
        retry = self.run_installer("new", action="upgrade")
        self.assertEqual(retry.returncode, 0, retry.stdout + retry.stderr)
        self.assertTrue(stages[0].exists(), "a rerun does not discard another attempt's backup")

    def assert_concurrent_operation_rejected(self, action):
        process = subprocess.Popen(self.command(), cwd=self.project, env=self.environment("new", "pause"),
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 5
            while not self.injected.exists() and process.poll() is None and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue(self.injected.exists(), "installer did not reach the controlled pause")
            self.assertIsNone(process.poll(), "paused installer must still be live")
            before = digest(self.base)
            result = self.run_installer("new", action=action)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("locked", result.stderr)
            self.assertEqual(before, digest(self.base))
        finally:
            self.release.write_text("continue")
            out, err = process.communicate(timeout=20)
        self.assertEqual(process.returncode, 0, out + err)
        self.assert_new_generation()

    def test_another_installer_cannot_replace_an_active_location(self):
        self.assert_concurrent_operation_rejected("install")

    def test_uninstall_cannot_remove_an_active_location(self):
        self.assert_concurrent_operation_rejected("uninstall")

    def test_successful_upgrade_preserves_language_and_shared_root_file(self):
        result = self.run_installer("new", action="upgrade")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assert_new_generation()
        self.assertEqual((self.base / "SKILL_STYLE.md").read_text(), "another owner's shared-root file\n")

    def test_unowned_dangling_companion_link_is_never_replaced(self):
        (self.sources["new"] / "skills/SKILL_STYLE.md").write_text(MARKER + "\nnew")
        (self.base / "SKILL_STYLE.md").unlink()
        (self.base / "SKILL_STYLE.md").symlink_to(self.root / "unavailable-owner")
        before = digest(self.base)
        result = self.run_installer("new")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("unowned bundle companion", result.stderr)
        self.assertEqual(before, digest(self.base))

    def test_failed_removal_during_rollback_keeps_both_generations(self):
        result = self.run_installer("new", "rollback-remove")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.injected.read_text(), "rollback-remove")
        stages = list(self.base.glob(".ssot-skill-install.*"))
        self.assertEqual(len(stages), 1)
        self.assertEqual((stages[0] / ".backup/ssot-bootstrap/generation.txt").read_text(), "old")
        self.assertEqual((self.base / "ssot-bootstrap/generation.txt").read_text(), "new")
        self.recover_retained_attempt(stages[0])

    def test_lock_cleanup_failure_keeps_owner_and_committed_bundle(self):
        result = self.run_installer("new", "unlock")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.injected.read_text(), "unlock")
        self.assertIn("changes completed", result.stderr)
        lock = self.base / ".ssot-skill-lock"
        self.assertIn("Installer PID:", lock.read_text())
        self.assert_bundle_bytes()
        self.assertFalse(list(self.base.glob(".ssot-skill-install.*")))
        saved = digest(self.base)
        retry = self.run_installer("new", action="upgrade")
        self.assertNotEqual(retry.returncode, 0)
        self.assertIn("locked", retry.stderr)
        self.assertEqual(saved, digest(self.base))
        lock.unlink()  # its owning child is known to have returned above
        retry = self.run_installer("new", action="upgrade")
        self.assertEqual(retry.returncode, 0, retry.stdout + retry.stderr)
        self.assert_new_generation()


if __name__ == "__main__":
    unittest.main()
