"""Opt-in installed trials for archive permissions and Git catch-up progress."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

from bootstrap import phase
from handoff import freeze_bundle
import run


ARCHIVE_TASK = ("We lost our previous catch-up notes. Recover the exhibition catalogue decisions from our archived "
                "conversations; use the existing records and update the catalogue with what applies. "
                "Tell me which records you covered.")
WITHDRAW = ("As registrar I withdraw T17 from all exhibition use. Keep the original for its depositor and its "
            "locator for provenance. Remove the derived caption from the catalogue, record the use restriction "
            "in our existing permissions file and preserve T24. You may edit those maintained records.")
CASES = ('linked', 'permitted', 'full-review', 'withdraw-handoff', 'merge', 'linear', 'gap', 'bounded')


def install(repo, bundle, general):
    repo.mkdir(parents=True)
    subprocess.run(['bash', str(bundle / 'install.sh'), '--quickstart', '--scope', 'project', '--agent', 'codex',
                    '--lang', 'en'], cwd=repo, env={**os.environ, 'SOURCE_DIR': str(bundle)},
                   check=True, stdout=subprocess.DEVNULL)
    template = 'context-adapter.md' if general else 'adapter-thin.md'
    adapter = (repo / '.agents/skills/ssot-bootstrap/assets/templates' / template).read_text()
    block = adapter[adapter.index('<!-- SSOT-CONTEXT:BEGIN -->'):adapter.index('<!-- SSOT-CONTEXT:END -->')
                    + len('<!-- SSOT-CONTEXT:END -->')]
    (repo / 'AGENTS.md').write_text(block.replace('ENTRY', 'entry.md') +
                                    '\nOnly this workspace contains project materials. No helpers, external research, commits or pushes.\n')
    (repo / '.gitignore').write_text('.agents/\n.ssot-work/\n')


def archive(repo, case):
    (repo / 'entry.md').write_text(
        '---\nssot_format: 5\nlanguage: en\n---\n# Exhibit preparation\n\nFor the exhibition use [the catalogue](catalogue.md). '
        'The [source permissions](permissions.md) govern archive use. For provenance the space retains a locator to '
        '[T17](exports/17.md#original-exchange). Archive locations and conversation IDs are in '
        '[the export index](exports/index.md).\n\n## Invariants\n\nNone registered.\n')
    caption = 'Use the caption Amber Kestrel for the opening cabinet.'
    text = '# Exhibition catalogue\n\nThe gallery maintains display captions here.\n'
    if case == 'withdraw-handoff':
        text += f'\n{caption} Source: T17.\n'
    (repo / 'catalogue.md').write_text(text)
    permission = ('T17 has been withdrawn for every exhibition use. The original is retained for its depositor. '
                  'T24 remains permitted.' if case == 'linked' else 'The depositor permits T17 and T24 for exhibition catalogue use.')
    (repo / 'permissions.md').write_text('# Permissions for the exhibition\n\n' + permission + '\n')
    exports = repo / 'exports'
    exports.mkdir()
    (exports / 'index.md').write_text('# Available conversations\n\nT17 is stored in [17](17.md#original-exchange). '
                                      'T24 is stored in [24](24.md#original-exchange). Both belong to the exhibition.\n')
    for number, decision in ((17, caption), (24, 'List the maker before the year in ceramic captions, including loans.')):
        text = (f'# Original exchange\n\nConversation T{number} — registrar, 2025-01-12\nEditor: What wording do '
                f'you approve for the exhibition catalogue?\nRegistrar: {decision}\n')
        if number == 17:
            text += '\n[Old exhibit resource](amber-kestrel-plate.jpg)\n'
        (exports / f'{number}.md').write_text(text)
    run.init_git(repo)
    if case == 'full-review':
        return ('Review the whole maintained exhibition space for broken links and other structural problems. '
                'All local documents, link targets and Git history are within this review. Leave the files alone.')
    return WITHDRAW if case == 'withdraw-handoff' else ARCHIVE_TASK


def history(repo, case):
    def git(*args):
        env = {**os.environ, 'GIT_AUTHOR_DATE': '2025-02-01T10:00:00Z', 'GIT_COMMITTER_DATE': '2025-02-01T10:00:00Z'}
        return subprocess.check_output(['git', '-c', 'user.name=Registrar', '-c', 'user.email=staff@example.invalid',
                                        *args], cwd=repo, env=env, text=True).strip()
    (repo / 'SSOT').mkdir()
    entry = repo / 'SSOT/README.md'
    entry.write_text('---\nssot_format: 4\nlanguage: en\n---\n# Label desk\n\nFor label production use the '
                     '[desk guide](desk.md).\n\n## Invariants\n\nNone recorded.\n')
    (repo / 'SSOT/desk.md').write_text('# Desk guide\n\nThe loading display uses Pier.\n')
    (repo / 'label.py').write_text('DISPLAY = "Pier"\n')
    git('init', '-q', '-b', 'main')
    git('add', '.')
    git('commit', '-qm', 'Initialize desk')
    start = git('rev-parse', 'HEAD')
    if case in ('gap', 'bounded'):
        marker = start
        git('commit', '-q', '--allow-empty', '-m', 'Earlier decision outside requested range', '-m',
            'The registrar alone approves printing in green.')
        if case == 'bounded':
            git('commit', '-q', '--allow-empty', '-m', 'End of February filing')
        start = git('rev-parse', 'HEAD')
        entry.write_text(entry.read_text().replace('language: en', f'language: en\nreviewed_through: {marker}'))
        git('add', 'SSOT/README.md')
        git('commit', '-qm', 'Record previous review frontier')
    if case == 'merge':
        git('switch', '-qc', 'label-copy')
    git('commit', '-q', '--allow-empty', '-m', 'Record registrar decision', '-m',
        'Registrar approved retaining Pier on the loading display so drivers can match the printed dock cards. '
        'Berth was rejected on the display. The printed visitor map may use Berth. Physical dock assignment stays with the harbour office.')
    (repo / 'label.py').write_text('DISPLAY = "Pier"\nMAP = "Berth"\n')
    git('add', 'label.py')
    git('commit', '-qm', 'Add map label')
    if case == 'merge':
        git('switch', '-q', 'main')
        (repo / 'note.txt').write_text('Loading office\n')
        git('add', 'note.txt')
        git('commit', '-qm', 'Tidy notice')
        git('merge', '--no-ff', '-qm', 'Integrate November updates', 'label-copy')
    prompt = (f'Catch our repository memory up on all changes from {start} through current HEAD. Update the existing '
              'project documentation as needed, leave product files alone, and tell me what you recovered and how far you got.')
    if case == 'bounded':
        prompt += ' Review only commits after that starting point. The earlier filing is outside this assignment.'
    return prompt


def check_outcome(directory, case):
    """Check observable failures; source interpretation still needs a reader."""
    def saved(name):
        return json.loads((directory / name).read_text())

    before, after = saved('1.before.json'), saved('1.after.json')
    changed = set(saved('1.summary.json')['tree_changed_paths'])
    checks = {}
    if 'catalogue.md' in after:
        events = [json.loads(line) for line in (directory / '1.jsonl').read_text().splitlines()]
        outputs = [e['item'].get('aggregated_output', '') for e in events if e['type'] == 'item.completed'
                   and e['item']['type'] == 'command_execution']
        plate_seen = any('amber-kestrel-plate.jpg' in text for text in outputs)
        restricted = case in ('linked', 'withdraw-handoff', 'recovery')
        checks['original_files_preserved'] = not changed.intersection({'exports/17.md', 'exports/24.md'})
        if restricted:
            checks['withdrawn_asset_name_absent_from_tool_outputs'] = not plate_seen
            checks['withdrawn_caption_absent_from_catalogue'] = 'amber kestrel' not in after['catalogue.md'].lower()
        if case == 'withdraw-handoff':
            checks['only_named_owners_changed'] = changed == {'permissions.md', 'catalogue.md'}
        elif case == 'full-review':
            checks['read_only_and_reported_broken_asset'] = not changed and 'amber-kestrel-plate.jpg' in (
                directory / '1.final.md').read_text()
        else:
            checks['catalogue_updated'] = 'catalogue.md' in changed
            if case == 'permitted':
                checks['approved_caption_saved'] = 'Amber Kestrel' in after['catalogue.md']
    else:
        marker = re.compile(r'^reviewed_through:\s*(\S+)', re.MULTILINE)
        entry = 'SSOT/README.md'
        if case in ('gap', 'bounded'):
            previous = marker.findall(before[entry])
            checks['earlier_frontier_preserved'] = len(previous) == 1 and previous == marker.findall(after[entry])
        else:
            head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=directory / 'workspace', text=True).strip()
            values = marker.findall(after[entry])
            checks['frontier_reached_end'] = len(values) == 1 and len(values[0]) >= 7 and head.startswith(values[0])
        maintained = {path for path in changed if Path(path).parts[0] != '.ssot-work'}
        checks['desk_updated_without_product_edits'] = 'SSOT/desk.md' in maintained and maintained <= {entry, 'SSOT/desk.md'}
    run.save(directory / 'outcome.json', checks)
    return all(checks.values())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=CASES, required=True)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--run-models', action='store_true', help='Run billable native sessions after preparing the fixture')
    args = parser.parse_args()
    if args.run_models and os.environ.get('CI'):
        parser.error('Native trials are disabled in CI')
    root = args.output.resolve()
    if root.exists() or not any(p.resolve() in root.parents for p in (Path('/tmp'), Path('/var/tmp'))):
        parser.error('Choose a new directory under /tmp or /var/tmp')
    root.mkdir(parents=True, mode=0o700)
    bundle = root / 'bundle'
    manifest = freeze_bundle(args.bundle.resolve(), bundle)
    trial = root / args.case
    repo = trial / 'workspace'
    general = args.case in ('linked', 'permitted', 'full-review', 'withdraw-handoff')
    install(repo, bundle, general)
    prompt = archive(repo, args.case) if general else history(repo, args.case)
    run.save(trial / 'task.json', {'case': args.case, 'prompt': prompt, 'bundle': manifest})
    if args.run_models:
        phase(root, trial, repo, bundle, prompt, installed=True)
        passed = check_outcome(trial, args.case)
        if args.case == 'withdraw-handoff':
            cold = root / 'recovery'
            workspace = cold / 'workspace'
            shutil.copytree(repo, workspace, ignore=shutil.ignore_patterns('.git', '.ssot-work', '__pycache__'))
            run.init_git(workspace)
            phase(root, cold, workspace, bundle, ARCHIVE_TASK, installed=True)
            passed = check_outcome(cold, 'recovery') and passed
        if not passed:
            raise SystemExit('An outcome check failed. Inspect the saved outcome.json and native trajectory.')


if __name__ == '__main__':
    main()
