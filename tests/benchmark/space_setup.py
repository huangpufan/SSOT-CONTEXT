"""Prepare or run one installed format-5 handoff with neighboring spaces."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess

from bootstrap import phase
import run


HEADER = "---\nssot_format: 5\nlanguage: en\n---\n"
FIELD = ("# Field notes\n\nThis space guides shoreline sampling. Use the [field guide](field-guide.md) "
         "for fieldwork.\n\n## Invariants\n\nNone recorded.\n")
OWNED = ("# Field notes setup\n\nFor field-notes.md. The owner agreed to add the sampling time "
         "to field-guide.md from tide.txt; link and reread the owner, check the entry and finish this setup.\n")
FOREIGN = ("# Museum programme setup\n\nFor README.md only. The next unit is to obtain a loan "
           "schedule from the curator. The curator has not yet supplied it.\n")
REVIEW = ("Review the maintained field-notes space starting at field-notes.md. When should I collect the "
          "water sample? Does this space show any unfinished setup or cleanup work for us? Read only and report your evidence.")
RESUME = ("Please finish the already-agreed setup of the field-notes space, starting at field-notes.md. "
          "Use its existing source and owners, and tell me what was completed. Other projects are outside this assignment.")
PRIOR = " Our previous agreement is recorded in BOOTSTRAP.md."
FIELDWORK = "Using the maintained field notes, when should I collect the shoreline water sample? Work read-only."


def fixture(repo, case):
    files = {
        'field-notes.md': HEADER + FIELD,
        'field-guide.md': '# Field guide\n\nCollect the water sample before the boat leaves the pier.\n',
        'README.md': HEADER + '# Museum programme\n\nProgramme setup continues in [setup progress](BOOTSTRAP.md).\n\n## Invariants\n\nNone recorded.\n',
        'BOOTSTRAP.md': FOREIGN,
        'STATUS.md': '# Boat status\n\nMaintained independently by the harbour office.\n',
        'tide.txt': 'Field lead, 2026-11-09: Take the shoreline sample at low tide.\n',
    }
    if case in {'resume', 'legacy', 'mismatch'}:
        progress = 'field-progress.md' if case == 'resume' else 'BOOTSTRAP.md'
        files['field-notes.md'] += f'\nSetup continues in [field setup progress]({progress}).\n'
        if case != 'mismatch':
            files[progress] = OWNED
        if case == 'legacy':
            del files['README.md']
    elif case == 'agreed-legacy':
        del files['README.md']
        files['BOOTSTRAP.md'] = OWNED.replace('For field-notes.md. ', '')
    elif case == 'shared':
        files['field-notes.md'] += '\nSetup continues in [shared progress](BOOTSTRAP.md#field-notes-setup).\n'
        files['BOOTSTRAP.md'] = FOREIGN + '\n' + OWNED
    for name, content in files.items():
        (repo / name).write_text(content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=('review', 'fieldwork', 'resume', 'legacy', 'mismatch', 'unlinked',
                                           'agreed-legacy', 'shared'), required=True)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='New trial directory under /tmp or /var/tmp')
    parser.add_argument('--run-models', action='store_true', help='Make a billable native model call')
    args = parser.parse_args()
    if args.run_models and os.environ.get('CI'):
        parser.error('Native trials are disabled in CI')
    root = args.output.resolve()
    if root.exists() or not any(parent in root.parents for parent in (Path('/tmp').resolve(), Path('/var/tmp').resolve())):
        parser.error('Choose a new trial directory under /tmp or /var/tmp')
    root.mkdir(parents=True, mode=0o700)
    bundle = root / 'bundle'
    bundle.mkdir()
    for name in ('install.sh', 'VERSION'):
        shutil.copy2(args.bundle / name, bundle / name)
    shutil.copytree(args.bundle / 'skills', bundle / 'skills', ignore=shutil.ignore_patterns('__pycache__'))
    trial = root / args.case
    repo = trial / 'workspace'
    repo.mkdir(parents=True)
    subprocess.run(['bash', str(bundle / 'install.sh'), '--quickstart', '--scope', 'project', '--agent', 'codex',
                    '--lang', 'en'], cwd=repo, env={**os.environ, 'SOURCE_DIR': str(bundle)}, check=True,
                   stdout=subprocess.DEVNULL)
    adapter = (repo / '.agents/skills/ssot-bootstrap/assets/templates/context-adapter.md').read_text()
    (repo / 'AGENTS.md').write_text(adapter[adapter.index('<!-- SSOT-CONTEXT:BEGIN -->'):].replace('ENTRY', 'field-notes.md')
                                     + '\nWork only in this workspace. No helpers, external research or commits.\n')
    fixture(repo, args.case)
    run.init_git(repo)
    prompt = {'review': REVIEW, 'fieldwork': FIELDWORK}.get(args.case, RESUME)
    if args.case == 'agreed-legacy':
        prompt += PRIOR
    run.save(trial / 'task.json', {'case': args.case, 'prompt': prompt, 'entry': 'field-notes.md', 'bundle': run.manifest(bundle)})
    if args.run_models:
        phase(root, trial, repo, bundle, prompt, installed=True)


if __name__ == '__main__':
    main()
