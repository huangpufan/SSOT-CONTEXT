#!/usr/bin/env python3
"""Frozen writer -> portable memory -> fresh consumer experiments with plain-docs controls."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import traceback

sys.dont_write_bytecode = True

import run
import handoff_cases as cases

HERE = Path(__file__).resolve().parent
T = run.transport
save = run.save
load = lambda p: json.loads(p.read_text())
ARMS = ('plain', 'baseline', 'candidate', 'ceiling', 'floor', 'stale')
SEMANTIC = ('accepted_scope_and_history', 'entry_routes_to_current_owner', 'final_claims_match_artifacts')


def freeze_bundle(source, target):
    target.mkdir(parents=True)
    for name in ('VERSION', 'install.sh'):
        shutil.copy2(source / name, target / name)
    shutil.copytree(source / 'skills', target / 'skills', ignore=shutil.ignore_patterns('__pycache__'))
    return T.tree_snapshot(target)


def prepare(args):
    root = args.output.resolve()
    if root.exists() or not any(root.is_relative_to(Path(p)) for p in ('/tmp', '/var/tmp')):
        raise ValueError('Use a new output under /tmp or /var/tmp')
    if not args.baseline or not args.model or args.cap < 1:
        raise ValueError('Preparation requires baseline, authorized model and positive cap')
    root.mkdir(parents=True)
    harness = root / 'harness/benchmark'
    harness.mkdir(parents=True)
    for name in ('run.py', 'cases.py', 'handoff.py', 'handoff_cases.py'):
        shutil.copy2(HERE / name, harness / name)
    if (HERE / 'fixtures').is_dir():
        shutil.copytree(HERE / 'fixtures', harness / 'fixtures')
    shutil.copy2(HERE.parent / 'run-performance-trials.py', root / 'harness/run-performance-trials.py')
    capture_goal = getattr(args, 'capture_goal', 'explicit')
    plan = {'schema': 1, 'model': T.requested_model(args.model), 'reasoning': 'medium', 'cap': args.cap,
            'capture_goal': capture_goal,
            'seed': args.seed, 'concurrency': 1, 'cases': {}, 'harness': T.tree_snapshot(root / 'harness'),
            'baseline': freeze_bundle(args.baseline.resolve(), root / 'bundles/baseline'),
            'semantics': list(SEMANTIC), 'confirmation': None if args.confirmation == 'none' else args.confirmation,
            'limits': 'Public synthetic contracts; no population estimate. Main author also reviews semantics.'}
    for case in cases.CASES:
        c = cases.contract(case, args.seed)
        for kind in ('initial', 'ceiling', 'stale'):
            cases.build(root / 'fixtures' / case / kind, c, kind)
        plan['cases'][case] = {'contract': c, 'prompts': cases.prompts(c, capture_goal), 'consumer': cases.consumer_prompt(c),
                               'fixtures': T.tree_snapshot(root / 'fixtures' / case)}
    save(root / 'plan.json', plan)
    (root / 'plan.sha256').write_text(hashlib.sha256((root / 'plan.json').read_bytes()).hexdigest() + '\n')
    print(f'Prepared {root}; no model calls. Run its frozen harness.')


def validate(root, plan):
    if hashlib.sha256((root / 'plan.json').read_bytes()).hexdigest() != (root / 'plan.sha256').read_text().strip():
        raise ValueError('Frozen plan changed')
    if HERE != root / 'harness/benchmark':
        raise ValueError('Run the frozen handoff.py harness')
    items = [(root / 'harness', plan['harness']), (root / 'bundles/baseline', plan['baseline'])]
    items += [(root / 'fixtures' / case, d['fixtures']) for case, d in plan['cases'].items()]
    if (root / 'candidate.json').exists():
        items += [(root / 'bundles/candidate', load(root / 'candidate.json')['manifest'])]
    for path, expected in items:
        if T.tree_snapshot(path) != expected:
            raise ValueError(f'Frozen artifact changed: {path}')


def attach(root, plan, source):
    validate(root, plan)
    if (root / 'candidate.json').exists() or (plan.get('confirmation') and (root / 'runs' / plan['confirmation']).exists()):
        raise ValueError('Freeze candidate once, before any confirmation attempt; examined cases are development evidence')
    save(root / 'candidate.json', {'source': str(source.resolve()),
         'manifest': freeze_bundle(source.resolve(), root / 'bundles/candidate')})


def setup(repo, bundle, c, protocol, directory):
    instructions = (f'# Workspace rules\n\nMaintained context starts at {c["entry"]}; {c["owner"]} owns the policy and its accepted changes.\n'
        f'Authorized documentation edits: {c["entry"]} and Markdown beneath {str(Path(c["owner"]).parent)}/; preserve the existing policy owner. Other files, including AGENTS.md, stay unchanged.\n'
        'Work only here. Do not commit, push, install dependencies, access other projects, invoke other models or delegate.\n')
    if protocol:
        command = ['bash', str(bundle / 'install.sh'), '--quickstart', '--agent', 'codex', '--scope', 'project', '--lang', 'en']
        installed = subprocess.run(command, cwd=repo, env={**os.environ, 'SOURCE_DIR': str(bundle)}, capture_output=True, text=True, timeout=40)
        save(directory / 'installation.json', {'command': command, 'returncode': installed.returncode,
                                             'stdout': installed.stdout, 'stderr': installed.stderr})
        if installed.returncode:
            raise ValueError('Official local installation failed')
        template = 'adapter-thin.md' if c['format'] == 4 else 'context-adapter.md'
        adapter = (repo / '.agents/skills/ssot-bootstrap/assets/templates' / template).read_text()
        start, end = '<!-- SSOT-CONTEXT:BEGIN -->', '<!-- SSOT-CONTEXT:END -->'
        instructions += '\n' + adapter[adapter.index(start):adapter.index(end)+len(end)].replace('ENTRY', c['entry']) + '\n'
    (repo / 'AGENTS.md').write_text(instructions)


def probe(repo, bundle, home, prompt, model, directory, protocol):
    sandbox = run.isolated_command(repo, bundle, home)
    command = sandbox + [shutil.which('codex'), '-m', model, '-C', str(repo), 'debug', 'prompt-input', prompt]
    subprocess.run(sandbox + ['python3', '--version'], check=True, capture_output=True, timeout=20)
    result = subprocess.run(command, env={**os.environ, 'CODEX_HOME': str(home)}, capture_output=True, text=True, timeout=40)
    save(directory / 'discovery.json', {'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
    observed = T.discovery_observation(result.stdout) if not result.returncode else {}
    present = bool(observed.get('skills'))
    wired = any(p['ssot_wired'] for p in observed.get('instruction_blocks', []))
    if result.returncode or present != protocol or wired != protocol or (protocol and 'ssot-preflight' not in observed['skills']):
        raise ValueError('Actual discovery does not match the treatment')
    return sandbox


turn_state = T.completion_state


def evidence_identity(directory):
    # Include byte, mode and symlink identities, without reading session homes.
    excluded = {'codex-home', '.git', '__pycache__'}
    identity = {p: value for p, value in T.tree_snapshot(directory, exclude_dirs=excluded).items()
                if not excluded.intersection(Path(p).parts) and p not in ('result.json', 'review.json')}
    unavailable = [p for p, value in identity.items() if value.get('kind') == 'unavailable']
    if unavailable:
        raise ValueError('Evidence unavailable: ' + ', '.join(unavailable))
    return identity



def execute(args, root, plan):
    if os.environ.get('CI'):
        raise ValueError('Billable models disabled in CI')
    validate(root, plan)
    if args.case == 'museum' and plan.get('capture_goal', 'automatic') != 'explicit':
        raise ValueError('Museum confirmation requires an explicitly frozen persistence goal')
    if args.arm == 'candidate' and not (root / 'candidate.json').exists():
        raise ValueError('Attach candidate before execution')
    directory = root / 'runs' / args.case / args.arm
    if directory.exists():
        raise ValueError('Attempt already exists; never replay partial work or overwrite evidence')
    directory.mkdir(parents=True)
    c = plan['cases'][args.case]['contract']
    bundle = root / 'bundles' / ('candidate' if args.arm == 'candidate' else 'baseline')
    # Plain controls never mount the protocol bundle into their subject sandbox.
    empty = directory / 'empty-tools'
    result = {'case': args.case, 'arm': args.arm, 'state': 'started', 'turns': [], 'checks': {}, 'phase': 'setup'}
    save(directory / 'result.json', result)
    try:
        empty.mkdir()
        environment = {'codex': subprocess.check_output(['codex', '--version'], text=True).strip(),
                       'python': sys.version, 'platform': sys.platform}
        ep = root / 'environment.json'
        if ep.exists() and load(ep) != environment:
            raise ValueError('Environment changed')
        save(ep, environment)
        writer = directory / 'writer'
        writer.mkdir()
        repo = writer / 'workspace'
        kind = args.arm if args.arm in ('ceiling', 'stale') else 'initial'
        shutil.copytree(root / 'fixtures' / args.case / kind, repo)
        protocol = args.arm in ('baseline', 'candidate')
        setup(repo, bundle, c, protocol, writer)
        if c["format"] == 4:
            run.init_git(repo)
        writer_head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo) if c['format'] == 4 else None
        initial = T.tree_snapshot(repo)
        fixture_tree = T.tree_snapshot(root / 'fixtures' / args.case / kind)
        if any(initial.get(p) != value for p, value in fixture_tree.items()):
            raise ValueError('Installation/setup changed shared fixture facts')
        summaries = []
        result['writer_turn_checks'] = []
        if args.arm in ('plain', 'baseline', 'candidate'):
            prompts = plan['cases'][args.case]['prompts']
            home = writer / 'codex-home'
            sandbox = probe(repo, bundle if protocol else empty, home, prompts[0], plan['model'], writer, protocol)
            for number, prompt in enumerate(prompts, 1):
                result['phase'] = f'writer-{number}'
                save(directory / 'result.json', result)
                s = T.execute_turn(root, writer, repo, prompt, number, plan['cap'], sandbox_command=sandbox,
                    codex_home=home, model=plan['model'], allow_no_git=True, installed_mode=True, capture_checkpoints=False)
                discovery = s.get('native_discovery', {})
                wired = any(b['ssot_wired'] for b in discovery.get('instruction_blocks', []))
                if s.get('completed') and (not discovery.get('instruction_blocks') or bool(discovery.get('skills')) != protocol or wired != protocol):
                    s['observation_complete'] = bool(discovery.get('instruction_blocks'))
                    s['discovery_mismatch'] = bool(discovery.get('instruction_blocks'))
                    save(writer / f'{number}.summary.json', s)
                summaries.append(s)
                result['turns'].append({'phase': result['phase'], 'costs': run.costs(s, plan['model'])})
                if turn_state([s], 1, plan['model']):
                    break
                turn_checks, unauthorized = cases.writer_checks(repo, c, initial, T.tree_snapshot(repo))
                turn_checks['head_preserved'] = writer_head is None or subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo) == writer_head
                result['writer_turn_checks'].append({'turn': number, 'checks': turn_checks, 'unauthorized_changes': unauthorized})
                if not all(turn_checks.values()):
                    result['checks'] = turn_checks
                    result['state'] = 'observer_failure' if turn_checks.get('private_scan_complete') is False else 'failed_quality'
                    return
            failure = turn_state(summaries, 2, plan['model'])
            if failure:
                result['state'] = failure
                return
        result['checks'], result['unauthorized_changes'] = cases.writer_checks(repo, c, initial, T.tree_snapshot(repo))
        if result['checks'].get('private_scan_complete') is False:
            result['state'] = 'observer_failure'
            return
        if not result['checks']['owner_transfer_valid']:
            result['state'] = 'failed_quality'
            return
        result['checks']['writer_head_preserved'] = writer_head is None or subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo) == writer_head
        transferred = cases.handoff_files(repo)
        save(directory / 'handoff.json', transferred)
        consumer = directory / 'consumer'
        consumer.mkdir()
        fresh = consumer / 'workspace'
        fresh.mkdir()
        for name, content in transferred.items():
            cases.write(fresh, name, content)
        setup(fresh, bundle, c, False, consumer)
        if c["format"] == 4:
            run.init_git(fresh)
        prompt = plan['cases'][args.case]['consumer']
        home = consumer / 'codex-home'
        result['phase'] = 'consumer-discovery'
        save(directory / 'result.json', result)
        sandbox = probe(fresh, empty, home, prompt, plan['model'], consumer, False)
        consumer_head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=fresh) if c['format'] == 4 else None
        before = T.tree_snapshot(fresh)
        result['phase'] = 'consumer'
        save(directory / 'result.json', result)
        s = T.execute_turn(root, consumer, fresh, prompt, 1, plan['cap'], sandbox_command=sandbox,
            codex_home=home, model=plan['model'], allow_no_git=True, installed_mode=True, capture_checkpoints=False)
        result['turns'].append({'phase': 'consumer', 'costs': run.costs(s, plan['model'])})
        discovery = s.get('native_discovery', {})
        if s.get('completed') and (not discovery.get('instruction_blocks') or discovery.get('skills') or any(b['ssot_wired'] for b in discovery.get('instruction_blocks', []))):
            s['observation_complete'] = bool(discovery.get('instruction_blocks'))
            s['discovery_mismatch'] = bool(discovery.get('instruction_blocks'))
            save(consumer / '1.summary.json', s)
        failure = turn_state([s], 1, plan['model'])
        native_after = T.tree_snapshot(fresh)
        verdict = cases.output_grade(fresh, c, sandbox)
        after = T.tree_snapshot(fresh)
        result['probe_changed_paths'] = sorted(p for p in native_after.keys() | after.keys() if native_after.get(p) != after.get(p))
        result['checks']['deliverable_preserves_handoff_when_exercised'] = not result['probe_changed_paths']
        changes = {p for p in before.keys() | native_after.keys() if before.get(p) != native_after.get(p)}
        result['checks']['consumer_preserved_handoff'] = changes <= {c['output'], '__pycache__'}
        result['checks']['consumer_head_preserved'] = consumer_head is None or subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=fresh) == consumer_head
        result['output'] = verdict
        result['checks']['consumer_policy_matches'] = verdict['policy_matches']
        result['phase'] = 'adjudication'
        if args.arm in ('floor', 'stale'):
            placeholder = verdict.get('observed') == {} and (c['format'] == 5 or set(verdict.get('mode_errors', {})) == set(c['modes']))
            negative = (not (fresh / c['output']).exists() or placeholder) if args.arm == 'floor' else (
                json.dumps(verdict.get('observed'), sort_keys=True) == json.dumps(cases.expected(c, stale=True), sort_keys=True)
                and verdict.get('unknown_mode_rejected'))
            result['calibration_expected_outcome'] = bool(negative) and not verdict['policy_matches']
            accepted = result['calibration_expected_outcome'] and all(v for k, v in result['checks'].items() if k != 'consumer_policy_matches')
            result['state'] = failure or ('calibration_pending' if accepted else 'failed_quality')
        else:
            result['state'] = failure or ('semantic_pending' if all(result['checks'].values()) else 'failed_quality')
    except Exception:
        result['state'] = 'infra'
        result['error'] = traceback.format_exc()
    finally:
        try:
            validate(root, plan)
        except ValueError as exc:
            result['state'] = 'observer_failure'
            result['frozen_artifact_error'] = str(exc)
        save(directory / 'mechanical.json', {k: result[k] for k in ('state', 'phase', 'checks', 'turns')} |
             {k: result[k] for k in ('output', 'calibration_expected_outcome', 'writer_turn_checks') if k in result})
        try:
            result['evidence'] = evidence_identity(directory)
        except (ValueError, OSError) as exc:
            result['state'] = 'observer_failure'
            result['evidence'] = None
            result['evidence_error'] = str(exc)
            mechanical = load(directory / 'mechanical.json')
            save(directory / 'mechanical.json', {**mechanical, 'state': 'observer_failure'})
        save(directory / 'result.json', result)
        print(json.dumps({k: result[k] for k in ('case', 'arm', 'state', 'phase', 'checks')}), flush=True)


def review_admissible(directory, arm):
    verdict = load(directory / 'mechanical.json')
    checks = verdict['checks']
    if arm in ('floor', 'stale'):
        return (verdict['state'] == 'calibration_pending' and verdict.get('calibration_expected_outcome') is True
                and checks.get('consumer_policy_matches') is False
                and all(v is True for k, v in checks.items() if k != 'consumer_policy_matches'))
    return (verdict['state'] == 'semantic_pending' and checks.get('consumer_policy_matches') is True
            and all(v is True for v in checks.values()))


def checked_review(record, evidence):
    if (not isinstance(record, dict) or record.get('evidence') != evidence
            or not isinstance(record.get('reviewer'), str) or not record['reviewer'].strip()
            or not isinstance(record.get('checks'), dict) or set(record['checks']) != set(SEMANTIC)):
        raise ValueError('Review must identify reviewer, bind exact evidence and cover semantic obligations')
    if any(not isinstance(v, dict) or type(v.get('passed')) is not bool
           or not isinstance(v.get('reason'), str) or not v['reason'].strip() for v in record['checks'].values()):
        raise ValueError('Each review obligation needs a boolean and artifact-grounded reason')


def review_state(record, arm):
    if not all(v['passed'] for v in record['checks'].values()):
        return 'failed_quality'
    return 'calibration_passed' if arm in ('floor', 'stale') else 'passed'


def review(args, root, plan):
    validate(root, plan)
    directory = root / 'runs' / args.case / args.arm
    result = load(directory / 'result.json')
    existing = directory / 'review.json'
    record = load(args.review)
    if existing.exists():
        if load(existing) != record:
            raise ValueError('Cannot replace an existing review; retain the original evidence')
    elif result['state'] not in ('semantic_pending', 'calibration_pending'):
        raise ValueError('Review only mechanically accepted outcomes')
    if evidence_identity(directory) != result['evidence']:
        raise ValueError('Evidence changed after adjudication')
    if not review_admissible(directory, args.arm):
        raise ValueError('Sealed mechanical verdict does not permit acceptance')
    checked_review(record, result['evidence'])
    if not existing.exists():
        save(existing, record)
    # Idempotent recovery if the reviewer stopped after review.json was saved.
    result['state'] = review_state(record, args.arm)
    save(directory / 'result.json', result)


def report_record(path):
    value = load(path)
    if not isinstance(value, dict):
        raise ValueError(f'{path.name} must contain an object')
    return value


def verified_result(directory, arm):
    # Read independent receipts before checking integrity: a broken artifact
    # invalidates acceptance, but does not erase already observed phase spend.
    errors, receipt, mechanical = [], {}, {}
    for name in ('result.json', 'mechanical.json'):
        if name == 'mechanical.json' and receipt.get('state') == 'started' and not (directory / name).exists():
            continue  # A running attempt has no final mechanical verdict yet.
        try:
            record = report_record(directory / name)
            if name == 'result.json':
                receipt = record
            else:
                mechanical = record
            if not isinstance(record.get('state'), str) or not record['state']:
                raise ValueError(f'{name} has no valid state')
            if 'turns' in record and not isinstance(record['turns'], list):
                raise ValueError(f'{name} has invalid turns')
            if name == 'mechanical.json' and not isinstance(record.get('checks'), dict):
                raise ValueError('mechanical.json has invalid checks')
        except (ValueError, OSError) as exc:
            errors.append(f'{name}: {exc}')
    result = {**receipt, **mechanical}
    result['turns'] = mechanical.get('turns') if isinstance(mechanical.get('turns'), list) else receipt.get('turns', [])
    if not isinstance(result['turns'], list):
        result['turns'] = []
    result.setdefault('phase', 'before receipt')
    try:
        if errors:
            raise ValueError('; '.join(errors))
        if receipt['state'] == 'started':
            # A final receipt has not sealed the artifacts. A leftover verdict
            # or review cannot promote an in-flight attempt to completion.
            return {**result, 'state': 'started'}
        if receipt.get('evidence') != evidence_identity(directory):
            raise ValueError('Evidence missing or changed after attempt')
        review_path = directory / 'review.json'
        if review_path.exists():
            record = report_record(review_path)
            checked_review(record, receipt['evidence'])
            if not review_admissible(directory, arm):
                raise ValueError('Sealed mechanical verdict does not permit acceptance')
            return {**result, 'state': review_state(record, arm)}
        if receipt['state'] in ('passed', 'calibration_passed'):
            raise ValueError('Acceptance has no artifact-bound review')
        return result
    except (ValueError, OSError, KeyError) as exc:
        return {**result, 'state': 'observer_failure', 'report_error': str(exc)}


def known_costs(value):
    if not isinstance(value, dict):
        return {}
    return {key: value[key] for key in run.METRICS if type(value.get(key)) in ((int, float) if key == 'seconds' else (int,))
            and (type(value[key]) is int or math.isfinite(value[key])) and value[key] >= 0}


def observed_turns(directory, turns, model):
    """Recover cost observations, never acceptance, from retained native receipts."""
    observed, errors = {}, []
    for number, turn in enumerate(turns):
        if not isinstance(turn, dict) or not isinstance(turn.get('phase'), str):
            errors.append(f'Invalid phase observation at turn {number + 1}')
            continue
        phase = turn['phase']
        if phase in observed:
            errors.append(f'Duplicate phase observation: {phase}')
            continue
        observed[phase] = {**turn, 'costs': known_costs(turn.get('costs')) or None, 'native_identity_verified': False}
    for role in ('writer', 'consumer'):
        for path in sorted((directory / role).glob('*.summary.json')):
            number = path.name.split('.')[0]
            if not number.isdigit():
                continue
            phase = f'writer-{number}' if role == 'writer' else 'consumer'
            try:
                summary = report_record(path)
                cost = known_costs({key: summary.get(key) for key in ('seconds', 'tool_items', 'tool_output_bytes')})
                usage = summary.get('native_turn_usage')
                identity_verified = bool(model) and T.native_identity_state(summary, model) is None
                # Mismatched execution still consumed resources. Native identity
                # governs comparison, not whether observed usage is retained.
                if isinstance(usage, dict):
                    cost.update(known_costs({key: usage.get(key) for key in ('input_tokens', 'cached_input_tokens', 'output_tokens')}))
                    if all(key in cost for key in ('input_tokens', 'cached_input_tokens')):
                        if cost['cached_input_tokens'] <= cost['input_tokens']:
                            cost['uncached_input_tokens'] = cost['input_tokens'] - cost['cached_input_tokens']
                        else:
                            cost.pop('cached_input_tokens')
                retained = observed.setdefault(phase, {'phase': phase, 'costs': None})
                retained['costs'] = {**cost, **(retained['costs'] or {})} or None
                retained['native_identity_verified'] = identity_verified
            except (ValueError, OSError) as exc:
                errors.append(f'{role}/{path.name}: {exc}')
                observed.setdefault(phase, {'phase': phase, 'costs': None, 'native_identity_verified': False})
    ordered = sorted(observed.values(), key=lambda turn: (turn['phase'] == 'consumer',
                     int(turn['phase'][7:]) if turn['phase'].startswith('writer-') and turn['phase'][7:].isdigit() else 0))
    return ordered, errors


def cost_totals(turns):
    if not turns:
        return None, None, False
    costs = [turn['costs'] or {} for turn in turns]
    observed = {key: sum(cost[key] for cost in costs if key in cost) for key in run.METRICS if any(key in cost for cost in costs)}
    total = {key: observed[key] if all(key in cost for cost in costs) else None for key in run.METRICS}
    complete = all(value is not None for value in total.values()) and all(turn.get('native_identity_verified') for turn in turns)
    return (total if observed else None), (observed or None), complete


def report(root):
    plan = load(root / 'plan.json')
    frozen_error = None
    try:
        validate(root, plan)
    except (ValueError, OSError) as exc:
        frozen_error = f'Frozen experiment cannot be verified: {exc}'
    rows = []
    for case in cases.CASES:
        for arm in ARMS:
            directory = root / 'runs' / case / arm
            result = verified_result(directory, arm) if directory.exists() else {'state': 'unrun', 'turns': []}
            turns, errors = observed_turns(directory, result['turns'], plan.get('model'))
            if frozen_error and result['state'] != 'unrun':
                errors.append(frozen_error)
            if errors:
                result = {**result, 'state': 'observer_failure', 'report_error': '; '.join(str(error) for error in [result.get('report_error'), *errors] if error)}
            total, observed, complete = cost_totals(turns)
            rows.append({'case': case, 'arm': arm, 'state': result['state'], 'phase': result.get('phase'),
                         'turns': turns, 'costs': total, 'observed_costs': observed, 'costs_complete': complete,
                         'report_error': result.get('report_error')})
    calibration = {}
    for case in cases.CASES:
        states = {r['arm']: r['state'] for r in rows if r['case'] == case}
        calibration[case] = states['ceiling'] == 'passed' and all(states[a] == 'calibration_passed' for a in ('floor', 'stale'))
    comparisons = [{'case': case, 'pair': [left, right],
                    'eligible': calibration[case] and all(any(r['case'] == case and r['arm'] == arm and r['state'] == 'passed' and r['costs_complete'] for r in rows) for arm in (left, right))}
                   for case in cases.CASES for left, right in (('plain', 'baseline'), ('baseline', 'candidate'))]
    capture_goal = plan.get('capture_goal', 'automatic')  # Plans predating this field used automatic capture.
    save(root / 'report.json', {'limits': plan['limits'], 'confirmation': plan.get('confirmation'),
         'capture_goal': capture_goal, 'report_error': frozen_error,
         'calibration_valid': calibration, 'comparisons': comparisons, 'attempts': rows})
    lines = ['# Cold handoff results', '', 'All attempts retained. Unknown cost is not zero. Quality precedes cost; no combined score.', '',
             'Capture goal: ' + capture_goal + '.', '',
             '| Task | Arm | State | Last phase | Seconds | Input | Output |', '| --- | --- | --- | --- | ---: | ---: | ---: |']
    for r in rows:
        cost = r['costs'] or {}
        def display(key):
            if cost.get(key) is not None:
                return str(cost[key])
            observed = (r['observed_costs'] or {}).get(key)
            return f'unknown ({observed} observed)' if observed is not None else 'unknown'
        lines.append(f"| {r['case']} | {r['arm']} | {r['state']} | {r['phase'] or '—'} | {display('seconds')} | {display('input_tokens')} | {display('output_tokens')} |")
    if frozen_error:
        lines += ['', frozen_error]
    lines += ['', 'Calibration valid (ceiling plus reviewed absent/stale controls): ' + json.dumps(calibration),
              'Prior exposure and earlier experiment roots belong in the accompanying maintainer report; this report does not track them automatically.',
              'Cost comparisons require valid calibration and both accepted tasks with native usage. Failed controls invalidate comparison, not the retained observations.']
    (root / 'report.md').write_text('\n'.join(lines) + '\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare', action='store_true')
    mode.add_argument('--run-models', action='store_true')
    mode.add_argument('--attach-candidate', type=Path)
    mode.add_argument('--review', type=Path)
    mode.add_argument('--report', action='store_true')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--baseline', type=Path)
    p.add_argument('--model')
    p.add_argument('--cap', type=int, default=300)
    p.add_argument('--seed', type=int, default=20261112)
    p.add_argument('--capture-goal', choices=('automatic', 'explicit'), default='explicit',
                   help='Explicit gives all writers the same persistence goal; automatic probes unprompted capture')
    p.add_argument('--confirmation', choices=(*cases.CASES, 'none'), default='editorial',
                   help='Untouched confirmation in this experiment; use none for previously exposed development cases and declare separate confirmation in the maintainer report')
    p.add_argument('--case', choices=cases.CASES, default='reporting')
    p.add_argument('--arm', choices=ARMS, default='baseline')
    args = p.parse_args()
    if args.prepare:
        prepare(args)
        return
    root = args.output.resolve()
    plan = load(root / 'plan.json')
    if args.model is not None and args.model != plan['model']:
        raise ValueError('Model differs from the frozen plan; prepare a new experiment')
    if args.attach_candidate:
        attach(root, plan, args.attach_candidate)
    elif args.review:
        review(args, root, plan)
    elif args.report:
        report(root)
    else:
        execute(args, root, plan)


if __name__ == '__main__':
    main()
