#!/usr/bin/env python3
"""Link explicitly selected local installations to a persistent source checkout."""
import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

CORE_SKILLS = ('ssot-preflight', 'ssot-bootstrap', 'ssot-closeout', 'ssot-doctor')
SHIM_SKILLS = ('ssot-audit', 'ssot-skill')
SKILLS = CORE_SKILLS + SHIM_SKILLS
GIT_ROUTING_ENV = {
    'GIT_DIR', 'GIT_WORK_TREE', 'GIT_COMMON_DIR', 'GIT_INDEX_FILE',
    'GIT_OBJECT_DIRECTORY', 'GIT_ALTERNATE_OBJECT_DIRECTORIES',
    'GIT_SHALLOW_FILE', 'GIT_PREFIX', 'GIT_IMPLICIT_WORK_TREE',
}


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


def is_dangling_ssot_link(target, name):
    return target.is_symlink() and not target.exists() and Path(os.readlink(target)).parts[-2:] == ('skills', name)


def check_no_installer_transaction(base):
    for journal in sorted(base.glob('.ssot-skill-install.*/.ssot-transaction')):
        if journal.is_file() or journal.is_symlink():
            raise ValueError(
                f'Refusing to link while unfinished installer transaction exists: {journal.parent}; '
                'recover the interrupted installation before linking'
            )


def check_no_installer_lock(base):
    lock = base / '.ssot-skill-lock'
    if lock.exists() or lock.is_symlink():
        raise ValueError(
            f'Refusing to link while installer lock exists: {lock}; '
            'wait for the active installer or recover the interrupted installation first'
        )
    check_no_installer_transaction(base)


@contextlib.contextmanager
def acquire_base_locks(bases, token):
    """Acquire install.sh-compatible .ssot-skill-lock files in sorted canonical order."""
    acquired = []
    try:
        for base in sorted({Path(b).resolve() for b in bases}):
            lock = base / '.ssot-skill-lock'
            try:
                fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError:
                raise ValueError(
                    f'Refusing to link while installer lock exists: {lock}; '
                    'wait for the active installer or recover the interrupted installation first'
                ) from None
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as handle:
                    handle.write(f'link-local.py PID: {os.getpid()}\n{token}\n')
            except BaseException:
                with contextlib.suppress(OSError):
                    lock.unlink()
                raise
            acquired.append(lock)
            check_no_installer_transaction(base)
        yield
    finally:
        release_errors = []
        for lock in reversed(acquired):
            try:
                if lock.is_file() and not lock.is_symlink():
                    lines = lock.read_text(encoding='utf-8').splitlines()
                    if len(lines) >= 2 and lines[1] == token:
                        lock.unlink()
            except OSError as exc:
                release_errors.append(f'{lock}: {exc}')
        if release_errors:
            raise OSError('Could not release installer lock(s): ' + '; '.join(release_errors))


def tracked_skill_directories(base, names):
    """Return sorted skill names under base that contain Git-tracked entries."""
    if not names:
        return []
    env = {k: v for k, v in os.environ.items() if k not in GIT_ROUTING_ENV}
    env.update(GIT_OPTIONAL_LOCKS='0', GIT_NO_LAZY_FETCH='1')
    try:
        res = subprocess.run(
            ['git', '-c', 'core.fsmonitor=false', '-c', 'core.quotepath=off',
             '-C', str(base), 'ls-files', '-z', '--', *names],
            env=env, capture_output=True, check=False,
        )
    except FileNotFoundError:
        return []
    if res.returncode != 0:
        return []
    tracked = set()
    for rec in res.stdout.decode('utf-8', 'surrogateescape').split('\0'):
        if rec:
            tracked.add(rec.split('/', 1)[0])
    return sorted(tracked)


def plan(source, bases, with_legacy_shims=False, allow_tracked=False, absolute=False):
    source = Path(source).resolve(strict=True)
    skills = source / 'skills'
    for name in SKILLS:
        if not (skills / name / 'SKILL.md').is_file():
            raise ValueError(f'Missing source skill: {name}')
    actions = []
    for base in sorted({Path(b).resolve(strict=True) for b in bases}):
        if base == skills or base in source.parents or source in base.parents:
            raise ValueError(f'Refusing to replace the source checkout: {base}')
        check_no_installer_lock(base)
        found = False
        planned_names = []
        active = list(CORE_SKILLS) + [
            name for name in SHIM_SKILLS
            if with_legacy_shims or (base / name).exists() or (base / name).is_symlink()
        ]
        for name in active:
            target = base / name
            if target.exists() or target.is_symlink():
                found = True
                if not is_dangling_ssot_link(target, name):
                    if not (target / 'SKILL.md').is_file():
                        raise ValueError(f'Unrecognised or broken installation: {target}')
                    if f'name: {name}' not in (target / 'SKILL.md').read_text(encoding='utf-8').splitlines():
                        raise ValueError(f'Unexpected skill owner: {target}')
            if target.is_symlink() and target.exists() and target.resolve() == skills / name:
                if not absolute or os.path.isabs(os.readlink(target)):
                    continue
            planned_names.append(name)
            actions.append({'path': str(target), 'source': str(skills / name),
                            'before': fingerprint(target)})
        if not found:
            raise ValueError(f'No existing SSOT installation: {base}')
        if not allow_tracked and planned_names:
            tracked = tracked_skill_directories(base, planned_names)
            if tracked:
                raise ValueError(
                    f'Refusing to replace git-tracked skill directories in {base} ({", ".join(tracked)}): '
                    'replacing tracked copies with local symlinks causes worktree skew and dirty git status; '
                    'use a global install (or untrack them first), or pass --allow-tracked to override'
                )
    return {'source': str(source), 'absolute': bool(absolute), 'actions': actions}


def apply(selected, backup_root):
    if not selected['actions']:
        return {'status': 'already-linked', 'actions': []}
    backup_root = Path(backup_root).resolve()
    source = Path(selected['source'])
    if backup_root == source or source in backup_root.parents:
        raise ValueError('Backups must be outside the source checkout')
    bases = sorted({Path(action['path']).parent.resolve() for action in selected['actions']})
    for base in bases:
        check_no_installer_lock(base)
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

    use_absolute = bool(selected.get('absolute', False))
    for i, action in enumerate(record['actions']):
        action['backup'] = str(archive / f'{i:04d}')
        action['link'] = action['source'] if use_absolute else os.path.relpath(action['source'], Path(action['path']).parent)
    save()
    touched = []
    with acquire_base_locks(bases, str(archive)):
        try:
            for action in record['actions']:
                target = Path(action['path'])
                check_no_installer_transaction(target.parent)
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
            conflicts = []
            for action in reversed(touched):
                target = Path(action['path'])
                backup = Path(action['backup'])
                if target.is_symlink() and os.readlink(target) == action['link']:
                    target.unlink()
                if target.exists() or target.is_symlink():
                    conflicts.append(str(target))
                    continue
                if backup.exists() or backup.is_symlink():
                    backup.rename(target)
            if conflicts:
                record['status'] = 'recovery-needed'
                record['rollback_conflicts'] = conflicts
                save()
                raise RuntimeError(
                    f'Concurrent replacement left intact ({", ".join(conflicts)}); recover from {manifest}'
                )
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
    parser.add_argument('--with-legacy-shims', action='store_true',
                        help='Also link ssot-audit and ssot-skill even when absent from target')
    parser.add_argument('--allow-tracked', action='store_true',
                        help='Allow replacing git-tracked skill directories with local symlinks')
    parser.add_argument('--absolute', action='store_true',
                        help='Create absolute symlinks instead of depth-relative ones (worktree-safe)')
    args = parser.parse_args()
    if args.apply and args.backup_root is None:
        parser.error('--apply requires --backup-root')
    selected = plan(
        args.source,
        args.base,
        with_legacy_shims=args.with_legacy_shims,
        allow_tracked=args.allow_tracked,
        absolute=args.absolute,
    )
    result = apply(selected, args.backup_root) if args.apply else selected
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
