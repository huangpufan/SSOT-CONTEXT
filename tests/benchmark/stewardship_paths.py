"""Replay independent whole tasks using the public 5.13 evidence and the installed transport."""
import argparse
import json
import os
from pathlib import Path
import re

import cases
import handoff
import run

HERE = Path(__file__).resolve().parent
MODEL = 'gpt-6.1-terra'
LANES = ('software', 'research', 'creative', 'merge', 'conflict', 'lookup4', 'lookup5', 'departure', 'typo4', 'typo5')


def write(repo, name, content):
    path = repo / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def setup(repo, lane):
    if lane in ('software', 'lookup4', 'departure', 'typo4'):
        policy = cases.build(repo, 'routed', True, 514)
        prompts = [cases.TASK, cases.WARM_TASK] if lane == 'software' else ['Only correct maintenence to maintenance in note.txt.']
        if lane == 'lookup4':
            prompts = ['A merchant asks what a physical express parcel to the south would cost at 3 kg, and whether the quote creates an order. Answer from the accepted contract and distinguish whether express is available today. Read only.']
        if lane == 'departure':
            prompts = ['Make digital express orders to remote zones return ValueError, like physical ones. Only shipping.py may be edited.']
        return 4, 'SSOT/README.md', prompts, policy
    repo.mkdir(parents=True)
    if lane == 'creative':
        data = json.loads((HERE / 'fixtures/judgment.json').read_text())
        for name, content in data['fixtures']['initial'].items():
            write(repo, name, content)
        return 5, 'CONTEXT.md', [*data['prompts'], data['consumer']], None
    if lane == 'lookup5':
        data = json.loads((HERE / 'fixtures/judgment.json').read_text())
        for name, content in data['fixtures']['ceiling'].items():
            write(repo, name, content)
        return 5, 'CONTEXT.md', ['根据作者已经接受的节目方向，修琴人现在想要什么，与旧师傅的关系和北门茶摊分别是什么地位？答给来接班的编辑，只读。'], None
    if lane == 'research':
        data = json.loads((HERE / 'results/context-stewardship-5.13.json').read_text())
        for arm in ('plain', '5.13'):
            turns = data['families']['six-shifts']['arms'][arm]
            run.save(repo / f'{arm}.json', [{key: t[key] for key in ('phase', 'native_turn_id', 'input', 'cached_input', 'output', 'answer')} for t in turns])
        history = (HERE.parents[1] / 'CHANGELOG.md').read_text()
        sections = re.split(r'(?m)(?=^## \[)', history)
        selected = [s for s in sections if re.match(r'^## \[(5\.([0-9]|1[0-3])|4\.[0-5]|3\.1[2-5]|2\.55|2\.50)\]', s)]
        if len(selected) != 26:
            raise ValueError('Unexpected historical editions')
        write(repo, 'release-history.md', '# Historical releases\n\n' + '\n'.join(selected))
        write(repo, 'entry.md', '---\nssot_format: 5\nlanguage: en\n---\n# Evaluation notebook\nAssess whether maintained context pays its cost. The [plain](plain.json) and [installed](5.13.json) transcripts are receipts for one project. Use [release history](release-history.md) for earlier design decisions.\n\n## Invariants\nNone registered.\n')
        return 5, 'entry.md', ['Write finding.md for our research lead. Did the installed workflow halve total input on the seven shifts? Calculate each total from the phase receipts, distinguish cached input from total, and give the tradeoff on the final history question. A colleague proposes bringing back the dedicated reader. Find when and why it left, and say what new comparison would justify that decision. Only finding.md may change.'], None
    write(repo, 'entry.md', '---\nssot_format: 5\nlanguage: en\n---\n# Score archive\n[Edition notes](guide.md) own the current terms. The two editors have equal authority in their editions.\n\n## Invariants\nNone registered.\n')
    if lane == 'typo5':
        write(repo, 'note.txt', 'maintenence\n')
        write(repo, 'guide.md', '# Catalogue\nThe title remains Score archive.\n')
        return 5, 'entry.md', ['Only correct maintenence to maintenance in note.txt.'], None
    common = 'Studio copies use cream covers. Touring copies use grey covers. Corrections go on loose slips.'
    current = common.replace('grey', 'blue') if lane == 'merge' else common.replace('cream', 'blue')
    write(repo, 'guide.md', '# Edition notes\n' + current + '\nMo adopted blue for quick identification at the depot.\n')
    prompt = (f'You are integrating the two editors’ decisions. Both worked from the same edition: “{common}” '
              'The current owner has Mo’s accepted edit. On the other branch, Eli accepted amber for studio copies because the studio lamp washes out pale stock. '
              'Neither editor can overrule the other on an overlapping choice; the board has not decided a conflict. '
              'Reconcile guide.md in place where settled. Leave a usable handoff about any overlap and the unaffected requirements. '
              'Edit only guide.md; preserve the attribution and reasons each successor will need.')
    return 5, 'entry.md', [prompt, 'Use the maintained guide to tell the printer what cover can be ordered for each edition now, what is unresolved and who chose the changes and why. Include how corrections travel. No file edits or actual orders.'], None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--bundle', type=Path)
    mode.add_argument('--plain', action='store_true')
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--lane', choices=LANES, required=True)
    parser.add_argument('--run-models', action='store_true')
    args = parser.parse_args()
    root = args.output.resolve()
    if root.exists() or not any(path in root.parents for path in (Path('/tmp').resolve(), Path('/var/tmp').resolve())):
        parser.error('Use a new isolated output directory under /tmp or /var/tmp')
    if args.run_models and os.environ.get('CI'):
        parser.error('No native calls in CI')
    root.mkdir(parents=True)
    repo, bundle = root / 'project', root / 'bundle'
    version, entry, prompts, policy = setup(repo, args.lane)
    instructions = f'Maintained context starts at {entry}. Respect its current owners. Work locally; no commits, external actions or delegation.\n'
    if args.plain:
        bundle.mkdir()
    else:
        run.save(root / 'bundle.json', handoff.freeze_bundle(args.bundle.resolve(), bundle))
        instructions += handoff.installed_adapter(repo, bundle, root, version, entry) + '\n'
    write(repo, 'AGENTS.md', instructions)
    if version == 4:
        run.init_git(repo)
    run.save(root / 'prompts.json', prompts)
    if not args.run_models:
        return
    for n, prompt in enumerate(prompts, 1):
        if args.lane == 'software' and n == 2:
            policy = cases.update(repo, policy)
        phase = root / f'phase-{n}'
        phase.mkdir()
        home = phase / 'codex-home'
        command = handoff.probe(repo, bundle, home, prompt, MODEL, phase, not args.plain)
        summary = run.transport.execute_turn(root, phase, repo, prompt, 1, 300, sandbox_command=command,
                                             codex_home=home, allow_no_git=True, installed_mode=True, model=MODEL)
        state = run.transport.completion_state([summary], 1, MODEL)
        if state:
            raise RuntimeError(f'Incomplete phase {n}: {state}')
        if args.lane in ('software', 'typo4', 'typo5'):
            before, after = [json.loads((phase / f'1.{s}.json').read_text()) for s in ('before', 'after')]
            result = cases.grade(repo, 'routed' if args.lane == 'software' else 'typo', policy, before, after)
            run.save(phase / 'outcome.json', result)


if __name__ == '__main__':
    main()
