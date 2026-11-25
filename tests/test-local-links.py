#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('local_links', Path(__file__).resolve().parents[1] / 'tools/link-local.py')
links = importlib.util.module_from_spec(spec)
spec.loader.exec_module(links)


class LocalLinks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.base = self.root / 'consumer/skills'
        self.backups = self.root / 'backups'
        for name in links.SKILLS:
            for parent in [self.source / 'skills', self.base]:
                (parent / name).mkdir(parents=True)
                (parent / name / 'SKILL.md').write_text(f'---\nname: {name}\n---\n')
        (self.base / 'unrelated.txt').write_text('keep')

    def test_links_preserve_originals_and_follow_new_source_files(self):
        selected = links.plan(self.source, [self.base])
        original = links.fingerprint(self.base / 'ssot-preflight')
        result = links.apply(selected, self.backups)
        self.assertEqual(result['linked_skills'], 6)
        self.assertEqual((self.base / 'unrelated.txt').read_text(), 'keep')
        for name in links.SKILLS:
            self.assertTrue((self.base / name).is_symlink())
        new = self.source / 'skills/ssot-bootstrap/assets/templates/zh/new.md'
        new.parent.mkdir(parents=True)
        new.write_text('new source file')
        self.assertEqual((self.base / 'ssot-bootstrap/assets/templates/zh/new.md').read_text(), 'new source file')
        self.assertEqual(links.fingerprint(Path(result['manifest']).parent / '0000'), original)
        self.assertEqual(links.plan(self.source, [self.base])['actions'], [])

    def test_shared_base_is_deduplicated(self):
        alias = self.root / 'alias'
        alias.symlink_to(self.base, target_is_directory=True)
        self.assertEqual(len(links.plan(self.source, [self.base, alias])['actions']), 6)

    def test_source_and_unrecognised_targets_refused(self):
        with self.assertRaises(ValueError):
            links.plan(self.source, [self.source / 'skills'])
        (self.base / 'ssot-doctor/SKILL.md').write_text('name: unrelated\n')
        with self.assertRaises(ValueError):
            links.plan(self.source, [self.base])

    def test_changed_installation_is_not_overwritten(self):
        selected = links.plan(self.source, [self.base])
        (self.base / 'ssot-preflight/SKILL.md').write_text('a concurrent edit')
        with self.assertRaises(ValueError):
            links.apply(selected, self.backups)
        self.assertFalse(self.base.joinpath('ssot-preflight').is_symlink())

    def test_failure_restores_earlier_and_current_originals(self):
        original = {name: links.fingerprint(self.base / name) for name in links.SKILLS}
        symlink = Path.symlink_to
        count = 0

        def fail_second(path, *args, **kwargs):
            nonlocal count
            count += 1
            if count == 2:
                raise OSError('injected link failure')
            return symlink(path, *args, **kwargs)

        with patch.object(Path, 'symlink_to', fail_second), self.assertRaises(OSError):
            links.apply(links.plan(self.source, [self.base]), self.backups)
        self.assertEqual({name: links.fingerprint(self.base / name) for name in links.SKILLS}, original)

    def test_utf8_skill_files_work_under_ascii_locale(self):
        import os, subprocess, sys
        (self.base / 'ssot-preflight/SKILL.md').write_text('---\nname: ssot-preflight\n---\n中文说明\n', encoding='utf-8')
        env = {**os.environ, 'LC_ALL': 'C', 'LANG': 'C', 'PYTHONCOERCECLOCALE': '0'}
        tool = Path(__file__).resolve().parents[1] / 'tools/link-local.py'
        proc = subprocess.run(
            [sys.executable, str(tool), '--source', str(self.source), '--base', str(self.base),
             '--apply', '--backup-root', str(self.backups)],
            capture_output=True, text=True, env=env,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue((self.base / 'ssot-preflight').is_symlink())

    def test_four_skill_install_links_only_core_unless_opt_in(self):
        four = self.root / 'consumer4/skills'
        for name in links.CORE_SKILLS:
            (four / name).mkdir(parents=True)
            (four / name / 'SKILL.md').write_text(f'---\nname: {name}\n---\n')
        selected = links.plan(self.source, [four])
        self.assertEqual(len(selected['actions']), 4)
        res = links.apply(selected, self.backups)
        self.assertEqual(res['linked_skills'], 4)
        for shim in links.SHIM_SKILLS:
            self.assertFalse((four / shim).exists() or (four / shim).is_symlink())
        opt_in = links.plan(self.source, [four], with_legacy_shims=True)
        self.assertEqual(len(opt_in['actions']), 2)

    def test_repoints_dangling_ssot_symlinks_after_source_checkout_moves(self):
        import json, os
        first = links.apply(links.plan(self.source, [self.base]), self.backups)
        self.assertEqual(first['linked_skills'], 6)
        old_targets = {name: os.readlink(self.base / name) for name in links.SKILLS}
        moved = self.root / 'moved-source'
        self.source.rename(moved)
        for name in links.SKILLS:
            self.assertTrue((self.base / name).is_symlink())
            self.assertFalse((self.base / name).exists())

        repoint_plan = links.plan(moved, [self.base])
        self.assertEqual(len(repoint_plan['actions']), 6)
        res = links.apply(repoint_plan, self.backups)
        self.assertEqual(res['linked_skills'], 6)
        manifest = json.loads(Path(res['manifest']).read_text(encoding='utf-8'))
        for action in manifest['actions']:
            name = Path(action['path']).name
            self.assertEqual(action['before'], {'link': old_targets[name]})
            self.assertTrue((self.base / name).is_symlink())
            self.assertEqual((self.base / name).resolve(), (moved / 'skills' / name).resolve())
            self.assertTrue(Path(action['backup']).is_symlink())
            self.assertEqual(os.readlink(action['backup']), old_targets[name])

    def test_refuses_arbitrary_non_ssot_dangling_symlinks(self):
        import shutil
        missing = self.root / 'missing'
        for idx, bad_target in enumerate((missing / 'unrelated', missing / 'other/ssot-doctor', missing / 'skills/wrong-skill')):
            base = self.root / f'bad-{idx}/skills'
            for name in links.CORE_SKILLS:
                (base / name).mkdir(parents=True)
                (base / name / 'SKILL.md').write_text(f'---\nname: {name}\n---\n')
            shutil.rmtree(base / 'ssot-doctor')
            (base / 'ssot-doctor').symlink_to(bad_target)
            with self.assertRaisesRegex(ValueError, 'Unrecognised or broken installation'):
                links.plan(self.source, [base])

    def test_refuses_plan_and_apply_when_installer_lock_or_transaction_exists(self):
        # 1. Active .ssot-skill-lock refuses plan().
        lock = self.base / '.ssot-skill-lock'
        lock.write_text('Installer PID: 99999\n/tmp/stage\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'installer lock'):
            links.plan(self.source, [self.base])
        lock.unlink()

        # 2. Unfinished .ssot-skill-install.*/.ssot-transaction refuses plan().
        tx_dir = self.base / '.ssot-skill-install.CRASH1'
        tx_dir.mkdir()
        (tx_dir / '.ssot-transaction').write_text('SSOT-CONTEXT installation transaction\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'unfinished installer transaction'):
            links.plan(self.source, [self.base])
        (tx_dir / '.ssot-transaction').unlink()
        tx_dir.rmdir()

        # 3. Lock appearing between plan() and apply() refuses apply() without touching skills.
        selected = links.plan(self.source, [self.base])
        lock.write_text('Installer PID: 99999\n/tmp/stage\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'installer lock'):
            links.apply(selected, self.backups)
        self.assertFalse((self.base / 'ssot-preflight').is_symlink())

    def test_apply_acquires_installer_lock_blocks_concurrent_installer_and_releases_on_exit(self):
        import os, subprocess
        installer = Path(__file__).resolve().parents[1] / 'install.sh'
        proj = self.root / 'locked-proj'
        base = proj / '.agents/skills'
        for name in links.CORE_SKILLS:
            (base / name).mkdir(parents=True)
            (base / name / 'SKILL.md').write_text(f'---\nname: {name}\n---\n', encoding='utf-8')
        lock_file = base / '.ssot-skill-lock'
        orig_symlink = Path.symlink_to
        checked_concurrent = False

        def intercept_first(path, *args, **kwargs):
            nonlocal checked_concurrent
            if not checked_concurrent and path.parent == base:
                checked_concurrent = True
                self.assertTrue(lock_file.is_file(), '.ssot-skill-lock must be held during apply()')
                # Concurrent install.sh on the same base must be rejected by the lock.
                proc = subprocess.run(
                    ['bash', str(installer), '--non-interactive', '--agent', 'codex', '--scope', 'project', '--lang', 'en', '--yes'],
                    cwd=proj,
                    env={**os.environ, 'HOME': str(self.root / 'home'), 'SOURCE_DIR': str(Path(__file__).resolve().parents[1])},
                    capture_output=True, text=True,
                )
                self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                self.assertIn('locked', proc.stderr)
            return orig_symlink(path, *args, **kwargs)

        with patch.object(Path, 'symlink_to', intercept_first):
            res = links.apply(links.plan(self.source, [base]), self.backups)
        self.assertTrue(checked_concurrent)
        self.assertEqual(res['linked_skills'], 4)
        self.assertFalse(lock_file.exists(), '.ssot-skill-lock must be released after apply()')

    def test_rollback_continues_restoring_earlier_slots_after_concurrent_conflict(self):
        import json
        first_orig = links.fingerprint(self.base / 'ssot-preflight')
        orig_symlink = Path.symlink_to
        count = 0

        def fail_third_with_conflict(path, *args, **kwargs):
            nonlocal count
            count += 1
            if count == 3:
                # Replace slot 2 (ssot-bootstrap) concurrently so rollback hits a conflict on slot 2,
                # yet must still proceed to restore slot 1 (ssot-preflight) from backup.
                second = self.base / 'ssot-bootstrap'
                second.unlink()
                second.mkdir()
                (second / 'FOREIGN.txt').write_text('foreign', encoding='utf-8')
                raise OSError('injected failure on third slot')
            return orig_symlink(path, *args, **kwargs)

        with patch.object(Path, 'symlink_to', fail_third_with_conflict):
            with self.assertRaisesRegex(RuntimeError, 'Concurrent replacement left intact'):
                links.apply(links.plan(self.source, [self.base]), self.backups)

        # Slot 1 (ssot-preflight) must be restored despite conflict on slot 2 (ssot-bootstrap).
        self.assertFalse((self.base / 'ssot-preflight').is_symlink())
        self.assertEqual(links.fingerprint(self.base / 'ssot-preflight'), first_orig)
        self.assertTrue((self.base / 'ssot-bootstrap/FOREIGN.txt').is_file())
        self.assertFalse((self.base / '.ssot-skill-lock').exists(), 'lock must be released after rollback')
        manifests = list(self.backups.glob('link-*/manifest.json'))
        self.assertEqual(len(manifests), 1)
        data = json.loads(manifests[0].read_text(encoding='utf-8'))
        self.assertEqual(data['status'], 'recovery-needed')
        self.assertEqual(len(data['rollback_conflicts']), 1)

    def test_refuses_git_tracked_skill_dirs_unless_allow_tracked(self):
        import os, subprocess
        repo = self.root / 'tracked-repo'
        base = repo / '.agents/skills'
        for name in links.CORE_SKILLS:
            (base / name).mkdir(parents=True)
            (base / name / 'SKILL.md').write_text(f'---\nname: {name}\n---\n', encoding='utf-8')
        git_env = {
            **os.environ,
            'GIT_AUTHOR_NAME': 'Test', 'GIT_AUTHOR_EMAIL': 't@example.test',
            'GIT_COMMITTER_NAME': 'Test', 'GIT_COMMITTER_EMAIL': 't@example.test',
        }
        subprocess.run(['git', 'init', '-q'], cwd=repo, env=git_env, check=True)
        subprocess.run(['git', 'add', '.'], cwd=repo, env=git_env, check=True)
        subprocess.run(['git', 'commit', '-qm', 'track skills'], cwd=repo, env=git_env, check=True)

        with self.assertRaisesRegex(ValueError, 'git-tracked skill directories'):
            links.plan(self.source, [base])

        selected = links.plan(self.source, [base], allow_tracked=True)
        self.assertEqual(len(selected['actions']), 4)
        res = links.apply(selected, self.backups)
        self.assertEqual(res['linked_skills'], 4)
        self.assertTrue((base / 'ssot-preflight').is_symlink())

    def test_absolute_flag_creates_absolute_symlinks_and_upgrades_relative_links(self):
        import os, subprocess, sys
        tool = Path(__file__).resolve().parents[1] / 'tools/link-local.py'
        # 1. Start with default relative links.
        links.apply(links.plan(self.source, [self.base]), self.backups)
        for name in links.SKILLS:
            self.assertFalse(os.path.isabs(os.readlink(self.base / name)))

        # 2. Running with --absolute via CLI upgrades existing relative links to absolute ones.
        proc = subprocess.run(
            [sys.executable, str(tool), '--source', str(self.source), '--base', str(self.base),
             '--apply', '--backup-root', str(self.backups), '--absolute'],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        for name in links.SKILLS:
            raw_target = os.readlink(self.base / name)
            self.assertTrue(os.path.isabs(raw_target), f'expected absolute link for {name}, got {raw_target}')
            self.assertEqual(Path(raw_target), (self.source / 'skills' / name).resolve())

        # 3. Second --absolute plan is a no-op (already-linked).
        self.assertEqual(links.plan(self.source, [self.base], absolute=True)['actions'], [])


if __name__ == '__main__':
    unittest.main()
