"""Replay the six-shift museum handoff with installed skills or plain project documents."""
import argparse
import json
import os
from pathlib import Path

import handoff
import run

FIXTURE = Path(__file__).parent / 'fixtures/six-shifts.json'
MODEL = 'gpt-6.1-terra'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    arm = parser.add_mutually_exclusive_group(required=True)
    arm.add_argument('--bundle', type=Path, help='Protocol checkout to install')
    arm.add_argument('--plain', action='store_true', help='Use the same project records without the skills')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--run-models', action='store_true', help='Run six billable shifts and a cold history question')
    args = parser.parse_args()
    root = args.output.resolve()
    if root.exists() or not any(base.resolve() in root.parents for base in (Path('/tmp'), Path('/var/tmp'))):
        parser.error('Choose a new directory under /tmp or /var/tmp')
    if args.run_models and os.environ.get('CI'):
        parser.error('Native trials are disabled in CI')
    case = json.loads(FIXTURE.read_text())
    repo = root / 'project'
    repo.mkdir(parents=True)
    for name, content in case['files'].items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    bundle = root / 'bundle'
    entry = case['entry']
    instructions = (f"Current project context starts at {entry}. Follow its owner and access rules. "
                    "Work locally. No commits, external effects or delegation.\n")
    if args.plain:
        bundle.mkdir()
    else:
        run.save(root / 'bundle.json', handoff.freeze_bundle(args.bundle.resolve(), bundle))
        instructions += handoff.installed_adapter(repo, bundle, root, case['format'], entry) + '\n'
    (repo / 'AGENTS.md').write_text(instructions)
    run.save(root / 'case.json', case)
    if not args.run_models:
        print('Prepared the starting project. No models were called.')
        return
    for index, prompt in enumerate(case['prompts']):
        for name, change in case['transitions'].get(str(index), {}).items():
            path = repo / name
            if isinstance(change, dict):
                original = path.read_text()
                if original.count(change['old']) != 1:
                    raise ValueError(f'Cannot apply the agreed heading change to {name}')
                change = original.replace(change['old'], change['new'])
            path.write_text(change)
        phase = root / f'phase-{index + 1}'
        phase.mkdir()
        home = phase / 'codex-home'
        sandbox = handoff.probe(repo, bundle, home, prompt, MODEL, phase, not args.plain)
        result = run.transport.execute_turn(root, phase, repo, prompt, 1, 240, sandbox_command=sandbox,
                                            codex_home=home, allow_no_git=True, installed_mode=True, model=MODEL)
        run.save(phase / 'artifacts.json', {n: (repo / n).read_text() for n in case['files'] if (repo / n).is_file()})
        if not result['completed'] or result['returncode']:
            raise SystemExit(f'Shift {index + 1} incomplete. Inspect the saved evidence.')
    print('Six shifts and the history question finished. Review the artifacts and traces against case.json.')


if __name__ == '__main__':
    main()
