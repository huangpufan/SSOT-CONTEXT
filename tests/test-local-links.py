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


if __name__ == '__main__':
    unittest.main()
