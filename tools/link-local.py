#!/usr/bin/env python3
"""Link explicitly selected local installations to a persistent source checkout."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile

SKILLS = ('ssot-preflight', 'ssot-bootstrap', 'ssot-closeout',
          'ssot-doctor', 'ssot-audit', 'ssot-skill')


def fingerprint(path):
    if path.is_symlink():
        return {'link': os.readlink(path)}
    if not path.exists():
        return None
    if not path.is_dir():
        raise ValueError(f'Expected skill directory: {path}')
    result = {}
    for base, dirs, files in os.walk(path, followlinks=False):
        for name in sorted(dirs + files):
            child = Path(base) / name
            key = str(child.relative_to(path))
            if child.is_symlink():
                result[key] = {'link': os.readlink(child)}
            elif child.is_file():
                result[key] = {'sha256': hashlib.sha256(child.read_bytes()).hexdigest(),
                               'mode': child.stat().st_mode}
            elif child.is_dir():
                result[key] = {'directory': True, 'mode': child.stat().st_mode}
            else:
                raise ValueError(f'Unsupported special file: {child}')
    return result


def plan(source, bases):
    source = Path(source).resolve(strict=True)
    skills = source / 'skills'
    for name in SKILLS:
        if not (skills / name / 'SKILL.md').is_file():
            raise ValueError(f'Missing source skill: {name}')
    actions = []
    for base in sorted({Path(b).resolve(strict=True) for b in bases}):
        if base == skills or base in source.parents or source in base.parents:
            raise ValueError(f'Refusing to replace the source checkout: {base}')
        found = False
        for name in SKILLS:
            target = base / name
            if target.exists() or target.is_symlink():
                found = True
                if not (target / 'SKILL.md').is_file():
                    raise ValueError(f'Unrecognised or broken installation: {target}')
                if f'name: {name}' not in (target / 'SKILL.md').read_text(encoding='utf-8').splitlines():
                    raise ValueError(f'Unexpected skill owner: {target}')
            if target.is_symlink() and target.resolve() == skills / name:
                continue
            actions.append({'path': str(target), 'source': str(skills / name),
                            'before': fingerprint(target)})
        if not found:
            raise ValueError(f'No existing SSOT installation: {base}')
    return {'source': str(source), 'actions': actions}


def apply(selected, backup_root):
    if not selected['actions']:
        return {'status': 'already-linked', 'actions': []}
    backup_root = Path(backup_root).resolve()
    source = Path(selected['source'])
    if backup_root == source or source in backup_root.parents:
        raise ValueError('Backups must be outside the source checkout')
    for action in selected['actions']:
        target = Path(action['path'])
        if target == backup_root or target in backup_root.parents:
            raise ValueError('Backups must be outside installed skills')
        if fingerprint(target) != action['before']:
            raise ValueError(f'Installation changed after planning: {target}')
    backup_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Moving originals preserves bytes, modes and links. Refuse cross-device moves.
    for action in selected['actions']:
        if Path(action['path']).parent.stat().st_dev != backup_root.stat().st_dev:
            raise ValueError('Backup root and installations must share a filesystem')
    archive = Path(tempfile.mkdtemp(prefix='link-', dir=backup_root))
    record = {**selected, 'status': 'applying', 'backup_directory': str(archive)}
    manifest = archive / 'manifest.json'

    def save():
        temporary = archive / 'manifest.tmp'
        temporary.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
        temporary.replace(manifest)

    for i, action in enumerate(record['actions']):
        action['backup'] = str(archive / f'{i:04d}')
        action['link'] = os.path.relpath(action['source'], Path(action['path']).parent)
    save()
    touched = []
    try:
        for action in record['actions']:
            target = Path(action['path'])
            if fingerprint(target) != action['before']:
                raise ValueError(f'Installation changed during application: {target}')
            if action['before'] is not None:
                target.rename(action['backup'])
            touched.append(action)
            target.symlink_to(action['link'], target_is_directory=True)
            action['linked'] = True
            save()
        record['status'] = 'linked'
        save()
    except BaseException:
        for action in reversed(touched):
            target = Path(action['path'])
            backup = Path(action['backup'])
            if target.is_symlink() and os.readlink(target) == action['link']:
                target.unlink()
            if target.exists() or target.is_symlink():
                record['status'] = 'recovery-needed'
                save()
                raise RuntimeError(f'Concurrent replacement left intact; recover from {manifest}')
            if backup.exists() or backup.is_symlink():
                backup.rename(target)
        record['status'] = 'rolled-back'
        save()
        raise
    return {'status': record['status'], 'manifest': str(manifest),
            'linked_skills': len(record['actions'])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--base', type=Path, action='append', required=True,
                        help='Existing agent skills directory; repeat for multiple installations')
    parser.add_argument('--apply', action='store_true', help='Otherwise print a read-only plan')
    parser.add_argument('--backup-root', type=Path,
                        help='Required for apply; originals and manifest remain here')
    args = parser.parse_args()
    if args.apply and args.backup_root is None:
        parser.error('--apply requires --backup-root')
    selected = plan(args.source, args.base)
    result = apply(selected, args.backup_root) if args.apply else selected
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
