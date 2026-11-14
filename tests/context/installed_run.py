#!/usr/bin/env python3
"""Candidate-only actual installation/discovery trial; ordinary user prompts."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

import cases
import oracle
import run
import source_cases
import source_oracle
import hybrid_case
import continuation_case
import register_case

FIRST = "请把 sources/initial.json 里的这次访谈导出接续整理到这个上下文空间既有的研究和创作笔记，保留各自原意及适用范围，并维护必要的简短入口。我同意在这个空间保存记忆；可信来源、范围及已授权owner见connector-setup.txt。以后还会追加导出，请保存各项完成和未完成进度，使换会话后能接续且不重复处理。原始导出保持原样，已经接受的方法继续有效，请报告实际范围和剩余事项。"
SECOND = "访谈来源新增 sources/followup.json，请按原授权把有限更正反映到相关既有笔记中，保留其他已接受约定、原始来源和历史。完成后说明当前保存和接入进度，不将计划描述为已经实现。"
ORDINARY = "请给一篇有关搬家的短篇写一个80字左右的开头，安静一点。"


def freeze(args):
    root = args.output.resolve()
    if root.exists() or not any(root.is_relative_to(Path(base).resolve()) for base in ("/tmp", "/var/tmp")):
        raise ValueError("Use a new /tmp or /var/tmp output")
    root.mkdir(parents=True)
    source = root / "install-source"
    source.mkdir()
    for name in ("install.sh", "VERSION"):
        shutil.copy2(args.candidate / name, source / name)
    shutil.copytree(args.candidate / "skills", source / "skills")
    # Coordinator snapshots are read-only; an owned checkout-equivalent copy
    # must retain ordinary owner-write permissions for installer staging.
    modes = []
    for path in (source, *source.rglob("*")):
        before = path.stat().st_mode & 0o777
        path.chmod(path.stat().st_mode | 0o200)
        if before != path.stat().st_mode & 0o777:
            modes.append({"path": str(path.relative_to(source)), "before": oct(before), "after": oct(path.stat().st_mode & 0o777)})
    original_manifest = run.manifest(args.candidate)
    content_preserved = all(original_manifest.get(name) == value for name, value in run.manifest(source).items())
    if not content_preserved:
        raise ValueError("Owned install source differs in content from candidate snapshot")
    harness = root / "harness"
    shutil.copytree(Path(__file__).resolve().parent, harness / "context", ignore=shutil.ignore_patterns("__pycache__"))
    (harness / "benchmark").mkdir()
    for name in ("run.py", "cases.py", "handoff.py", "handoff_cases.py", "judgment_cases.py"):
        shutil.copy2(Path(__file__).resolve().parent.parent / "benchmark" / name, harness / "benchmark" / name)
    for name in ("run-performance-trials.py", "continuity_cases.py"):
        shutil.copy2(Path(__file__).resolve().parent.parent / name, harness / name)
    fixture = root / "fixture"
    longchain = None
    if getattr(args, "longchain", False):
        import longchain_case
        definition = getattr(args, "longchain_contract", None)
        longchain = json.loads(definition.read_text()) if definition else longchain_case.definition(
            kind=getattr(args, 'longchain_kind', 'development'), control=getattr(args, 'longchain_control', None))
        longchain = longchain_case.calibrate_contract(source / 'skills/ssot-doctor/assets/scripts/context-source.py', root / 'oracle', longchain)
        longchain_case.build(fixture, cases.scenarios.write, longchain)
        kind, prompts = "installed longchain", [phase["prompt"] for phase in longchain_case.phases(longchain)]
    elif args.large_register:
        register_case.build(fixture)
        kind, prompts = "large-register " + args.large_register, [register_case.TYPO_TASK if args.large_register == "typo" else register_case.CONFLICT_TASK]
    elif args.continuation:
        continuation_case.build(fixture, cases.scenarios.write)
        kind, prompts = "synthetic four-session continuation", continuation_case.PROMPTS
    elif args.hybrid:
        hybrid_case.build(fixture)
        kind, prompts = "hybrid format5 parent and format4 child", [hybrid_case.TASK]
    elif args.ordinary_negative:
        fixture.mkdir()
        kind, prompts = "ordinary undeclared creative task", [ORDINARY]
    else:
        source_cases.build(fixture, cases.scenarios.write, native_entry=True)
        cases.scenarios.write(fixture, "SSOT/README.md", "---\nssot_format: 5\nlanguage: en\n---\n# Interview research and creative space\n\n[Research](../research/findings.md), [Creative material](../creation/notes.md), and [Authorized experiences](../memory/experiences.md) keep their own meaning and authority. Trusted source scope is in [Connector setup](../connector-setup.txt). Maintained by compatible SSOT-CONTEXT 5.0+ writers; older writers upgrade rather than downgrade.\n")
        kind, prompts = "natural source workflow", [FIRST, SECOND]
    command = ["bash", str(source / "install.sh"), "--quickstart", "--agent", "codex", "--scope", "project", "--lang", "zh"]
    installed = subprocess.run(command, cwd=fixture, env={**os.environ, "SOURCE_DIR": str(source)}, capture_output=True, text=True)
    run.save(root / "installation.json", {"command": command, "returncode": installed.returncode, "stdout": installed.stdout, "stderr": installed.stderr,
        "owned_source_copy_permissions": "owner-write restored to checkout-equivalent modes; source snapshot untouched",
        "mode_changes": modes, "source_content_hashes_identical": content_preserved})
    if installed.returncode:
        raise ValueError("Official local installer failed; retain evidence")
    template = "adapter-thin.md" if args.large_register or (longchain and longchain['format'] == 4) else "context-adapter.md"
    adapter = (fixture / ".agents/skills/ssot-bootstrap/assets/templates" / template).read_text()
    start, end = "<!-- SSOT-CONTEXT:BEGIN -->", "<!-- SSOT-CONTEXT:END -->"
    adapter = adapter[adapter.index(start):adapter.index(end) + len(end)].replace("ENTRY", longchain["entry"] if longchain else "SSOT/README.md")
    if not args.ordinary_negative:
        (fixture / "AGENTS.md").write_text("# Workspace rules\n\nWork only in this isolated space. Do not commit, push, install dependencies, access other projects, invoke other models or delegate to other agents.\n\n" + adapter + "\n")
    plan = {"schema": 2, "comparison_kind": "candidate actual installed discovery, no performance comparison", "model": run.bench.transport.requested_model(args.model),
            "cap": args.cap, "reasoning": "medium", "concurrency": 1,
            "kind": kind, "prompts": prompts,
            "source_manifest": run.manifest(source), "fixture_manifest": run.manifest(fixture), "harness_manifest": run.manifest(harness)}
    if longchain:
        plan["longchain"] = longchain
        plan["phases"] = longchain_case.phases(longchain)
        if (root / 'oracle').exists():
            plan['oracle_manifest'] = run.manifest(root / 'oracle')
    plan["tree_manifests"] = {name: run.bench.transport.tree_snapshot(root / name) for name in ("install-source", "fixture", "harness")}
    plan['fixture_git_identity'] = git_identity(fixture)
    run.save(root / "plan.json", plan)
    (root / "plan.sha256").write_text(hashlib.sha256((root / "plan.json").read_bytes()).hexdigest() + "\n")
    print(f"Installed candidate and froze trial: {root}; no model calls")


def validate(root, plan, require_frozen_reporter=True):
    if require_frozen_reporter and Path(__file__).resolve().parent != root / "harness/context":
        raise ValueError("Run frozen installed harness")
    if plan.get("schema", 1) >= 2 and hashlib.sha256((root / "plan.json").read_bytes()).hexdigest() != (root / "plan.sha256").read_text().strip():
        raise ValueError("Frozen plan changed")
    for name, expected in (("install-source", plan["source_manifest"]), ("fixture", plan["fixture_manifest"]), ("harness", plan["harness_manifest"])):
        if run.manifest(root / name) != expected:
            raise ValueError(f"Frozen {name} changed")
    for name, expected in plan.get("tree_manifests", {}).items():
        actual = run.bench.transport.tree_snapshot(root / name)
        if actual != expected or any(value.get("kind") == "unavailable" for value in actual.values()):
            raise ValueError(f"Frozen {name} type/mode/content unavailable or changed")
    if 'oracle_manifest' in plan and run.manifest(root / 'oracle') != plan['oracle_manifest']:
        raise ValueError('Frozen private oracle changed')
    if 'fixture_git_identity' in plan and git_identity(root / 'fixture') != plan['fixture_git_identity']:
        raise ValueError('Frozen fixture Git history changed')


def discovery_state(discovery, installed, wired):
    if not isinstance(discovery, dict) or not all(key in discovery for key in ('skills', 'instruction_blocks')):
        return 'observer_failure'
    observed_wiring = any(block.get('ssot_wired') for block in discovery['instruction_blocks'])
    if (('ssot-preflight' in discovery['skills']) if installed else not discovery['skills']) and observed_wiring == wired:
        return None
    return 'delivery_failure'


def probe(directory, repo, home, sandbox, prompt, model, installed, wired):
    command = sandbox + [shutil.which('codex'), '-m', model, '-C', str(repo), 'debug', 'prompt-input', prompt]
    result = subprocess.run(command, env={**os.environ, 'CODEX_HOME': str(home)}, capture_output=True, text=True, timeout=40)
    run.save(directory / 'discovery-probe.json', {'command': command, 'returncode': result.returncode,
             'stdout': result.stdout, 'stderr': result.stderr})
    observation = run.bench.transport.discovery_observation(result.stdout) if not result.returncode else {}
    failure = discovery_state(observation, installed, wired)
    if result.returncode or failure:
        raise ValueError('Actual zero-model catalog/wiring probe failed: ' + (failure or 'infra'))
    return observation


def phase_state(summary, model, installed, wired, interrupted=False):
    failure = run.bench.transport.native_identity_state(summary, model)
    if failure:
        return failure
    if not summary.get('observation_complete'):
        return 'observer_failure'
    failure = discovery_state(summary.get('native_discovery'), installed, wired)
    if failure:
        return failure
    if interrupted:
        if not summary.get('intentional_interruption') or summary.get('native_completed'):
            return 'delivery_failure'
        return None
    return run.bench.transport.completion_state([summary], 1, model)


def workspace_checks(before, after, contract, consumer=False):
    allowed = {contract['consumer']['output']} if consumer else {contract['entry'], *contract['owners'].values()}
    ancestors = {str(parent) for name in allowed for parent in Path(name).parents if str(parent) != '.'}
    changed = {name for name in before.keys() | after.keys() if before.get(name) != after.get(name)}
    def authorized(name):
        current, prior = after.get(name, {}), before.get(name)
        if name in allowed:
            return current.get('kind') == 'file' and (not prior or current.get('mode') == prior.get('mode'))
        if not consumer and any(name.startswith(root.rstrip('/') + '/') or (
                name == root.rstrip('/') and current.get('kind') == 'directory') for root in contract.get('metadata_roots', [])):
            return True
        return name in ancestors and not prior and current.get('kind') == 'directory'
    return {'tree_observation_complete': all(value.get('kind') != 'unavailable' for tree in (before, after) for value in tree.values()),
            'authorized_workspace_tree_changes': all(authorized(name) for name in changed)}


def git_identity(repo):
    if not (repo / '.git').exists():
        return None
    if (repo / '.git').is_symlink() or not (repo / '.git').is_dir():
        raise ValueError('Git metadata is not the owned fixture directory')
    try:
        observed = subprocess.check_output(['git', 'rev-parse', '--show-toplevel', 'HEAD'], cwd=repo, text=True).splitlines()
        refs = subprocess.check_output(['git', 'for-each-ref', '--format=%(refname) %(objectname)'], cwd=repo, text=True)
        index = subprocess.check_output(['git', 'ls-files', '--stage'], cwd=repo, text=True)
    except subprocess.CalledProcessError as exc:
        raise ValueError('Owned Git identity could not be observed') from exc
    if len(observed) != 2 or Path(observed[0]).resolve() != repo.resolve():
        raise ValueError('Git observation is not the owned repository')
    return {'head': observed[1], 'refs': refs.splitlines(), 'index_entries': index.splitlines()}


def same_git_history(before, after):
    if before is None or after is None:
        return before is after
    return all(before[key] == after[key] for key in ('head', 'refs'))


def checkpoint_checks(directory, turn, before, contract, consumer=False):
    try:
        values = json.loads((directory / f'{turn}.checkpoints.json').read_text())
        if not isinstance(values, list):
            raise ValueError('Checkpoints must be a list')
        allowed = {contract['consumer']['output']} if consumer else {contract['entry'], *contract['owners'].values()}
        preserved = True
        for value in values:
            files = value.get('files') if isinstance(value, dict) else None
            if not isinstance(files, dict) or any(not isinstance(name, str) or not isinstance(text, str) for name, text in files.items()):
                raise ValueError('Invalid checkpoint text snapshot')
            changed = {name for name in before.keys() | files.keys() if before.get(name) != files.get(name)}
            preserved = preserved and all(name in allowed or (not consumer and any(
                name.startswith(root.rstrip('/') + '/') for root in contract.get('metadata_roots', []))) for name in changed)
        return {'checkpoint_observation_complete': True, 'observed_text_checkpoint_scope_preserved': preserved}
    except (OSError, ValueError):
        return {'checkpoint_observation_complete': False, 'observed_text_checkpoint_scope_preserved': False}


def seal(directory, result, verdict):
    tools = run.handoff_tools()
    mechanical = {**verdict, 'state': result['state'], 'phase': result['phase'], 'turns': result['turns']}
    run.save(directory / 'verdict.json', mechanical)
    run.save(directory / 'mechanical.json', mechanical)
    try:
        result['evidence'] = tools.evidence_identity(directory)
    except (ValueError, OSError) as exc:
        result.update(state='observer_failure', evidence=None, evidence_error=str(exc))
        mechanical['state'] = result['state']
        run.save(directory / 'mechanical.json', mechanical)
        run.save(directory / 'verdict.json', mechanical)
    run.save(directory / 'result.json', result)


def adjudication_failure(verdict):
    if verdict.get('state') in ('infra', 'observer_failure'):
        return verdict['state']
    return 'observer_failure' if verdict.get('observation_failed') else 'failed_quality'


def verified_attempt(directory):
    tools = run.handoff_tools()
    records, errors = {}, []
    for name in ('result.json', 'mechanical.json'):
        if name == 'mechanical.json' and records.get('result.json', {}).get('state') == 'started' and not (directory / name).exists():
            continue
        try:
            records[name] = tools.report_record(directory / name)
        except (ValueError, OSError) as exc:
            errors.append(f'{name}: {exc}')
    receipt, mechanical = records.get('result.json', {}), records.get('mechanical.json', {})
    result = {**receipt, **mechanical}
    result['turns'] = mechanical.get('turns', receipt.get('turns', []))
    if not isinstance(result['turns'], list):
        result['turns'] = []
        errors.append('Invalid phase receipt list')
    try:
        if receipt.get('state') == 'started' and not errors:
            return {**result, 'state': 'started'}
        if errors:
            raise ValueError('; '.join(errors))
        if not isinstance(mechanical.get('state'), str) or not isinstance(mechanical.get('checks', {}), dict):
            raise ValueError('Invalid mechanical record')
        if receipt.get('evidence') != tools.evidence_identity(directory):
            raise ValueError('Attempt evidence missing or changed')
        review_path = directory / 'review.json'
        if review_path.exists():
            record = tools.report_record(review_path)
            tools.checked_review(record, receipt['evidence'])
            if mechanical['state'] not in ('semantic_pending', 'calibration_pending') or not mechanical.get('mechanical_passed') or not all(value is True for value in mechanical['checks'].values()):
                raise ValueError('Sealed mechanical verdict does not permit acceptance')
            return {**result, 'state': tools.review_state(record, receipt.get('control') or 'baseline')}
        if receipt.get('state') in ('passed', 'calibration_passed'):
            raise ValueError('Acceptance has no artifact-bound review')
        return result
    except (ValueError, OSError, KeyError) as exc:
        return {**result, 'state': 'observer_failure', 'report_error': str(exc)}


def report(root, report_output=None):
    plan = json.loads((root / 'plan.json').read_text())
    directory, errors = root / 'run', []
    destination = Path(report_output).resolve() if report_output else root
    if report_output and (destination.exists() or destination.is_relative_to(root.resolve())):
        raise ValueError('Cost reanalysis requires a new output outside the frozen evidence root')
    try:
        validate(root, plan, require_frozen_reporter=not bool(report_output))
    except (OSError, ValueError) as exc:
        errors.append(str(exc))
    if not directory.exists():
        result = {'state': 'unrun', 'turns': []}
    elif plan.get('schema', 1) < 2:
        result = {'state': 'legacy_unsealed', 'turns': []}
        errors.append('Historical schema has no sealed attempt receipt; observation is not retrospective acceptance')
    else:
        result = verified_attempt(directory)
    turns = {}
    for turn in result['turns']:
        if isinstance(turn, dict) and isinstance(turn.get('summary'), str):
            turns[turn['summary']] = turn
        else:
            errors.append('Malformed phase observation')
    for path in sorted(directory.glob('*.summary.json')) + sorted(directory.glob('phase-*/*.summary.json')):
        turns.setdefault(str(path.relative_to(directory)), {'summary': str(path.relative_to(directory))})
    rows, invalidated = [], []
    for relative, turn in turns.items():
        path = directory / relative
        try:
            if not path.resolve().is_relative_to(directory.resolve()):
                raise ValueError('Summary escaped attempt')
            summary = run.handoff_tools().report_record(path)
            observation = oracle.native_observation(summary, plan['model'], path.with_name(path.name.replace('.summary.json', '.native.jsonl')))
        except (ValueError, OSError) as exc:
            errors.append(f'{relative}: {exc}')
            saved = turn.get('observed_costs') or turn.get('costs')
            saved = saved if isinstance(saved, dict) else {}
            observed = oracle.observed_native_costs({**saved, 'native_turn_usage': saved})
            observation = {'costs': None, 'observed_costs': observed,
                           'complete_costs': {'seconds': observed['seconds']}, 'usage_status': 'unknown',
                           'usage_boundary': {'status': 'unknown', 'reason': 'Native summary unavailable'},
                           'identity_state': 'observer_failure', 'cost_comparable': False}
        if observation['costs'] is None and (turn.get('costs') is not None or turn.get('cost_comparable')):
            invalidated.append({'summary': relative, 'legacy_costs': turn.get('costs'),
                                'legacy_cost_comparable': turn.get('cost_comparable'),
                                'reason': observation['usage_boundary']['reason']})
        rows.append({**turn, **observation})
    if errors and result['state'] not in ('unrun', 'legacy_unsealed'):
        result['state'] = 'observer_failure'
    values = [row.get('observed_costs') or {} for row in rows]
    keys = ('seconds', 'input_tokens', 'cached_input_tokens', 'output_tokens', 'total_input_output_tokens')
    totals = {key: sum(value[key] for value in values if value.get(key) is not None) if any(value.get(key) is not None for value in values) else None for key in keys}
    complete = [row.get('complete_costs') or {} for row in rows]
    complete_totals = {key: sum(value[key] for value in complete) if complete and all(value.get(key) is not None for value in complete) else None for key in keys}
    execution_timing, timing_error, timing_hash = None, None, None
    timing_path = root / 'execution-timing.json'
    if timing_path.exists():
        try:
            timing_hash = hashlib.sha256(timing_path.read_bytes()).hexdigest()
            timing = run.handoff_tools().report_record(timing_path)
            elapsed = timing.get('elapsed_seconds')
            if any(not isinstance(timing.get(key), str) or not timing[key] for key in ('started_at_utc', 'finished_at_utc', 'boundary')):
                raise ValueError('Execution timing lacks observed endpoints or boundary')
            for key in ('started_at_utc', 'finished_at_utc'):
                if datetime.fromisoformat(timing[key]).tzinfo is None:
                    raise ValueError('Execution timing endpoint has no timezone')
            if (timing.get('plan_sha256') != hashlib.sha256((root / 'plan.json').read_bytes()).hexdigest()
                    or timing.get('mechanical_sha256') != hashlib.sha256((directory / 'mechanical.json').read_bytes()).hexdigest()
                    or timing.get('clock') != 'time.monotonic' or type(elapsed) not in (int, float)
                    or not math.isfinite(elapsed) or elapsed < 0):
                raise ValueError('Execution timing is not bound to this plan/mechanical result')
            execution_timing = timing
        except (OSError, ValueError) as exc:
            timing_error = str(exc)
    output = {'schema': 2, 'kind': plan.get('kind'), 'control': plan.get('longchain', {}).get('control'), 'state': result['state'], 'phase': result.get('phase'),
              'phases': rows, 'observed_totals': totals,
              'observed_totals_scope': 'Sum of observed samples only; token amounts are lower bounds when any phase is not complete. Missing usage is never an observed zero.',
              'complete_totals': complete_totals, 'invalidated_legacy_cost_fields': invalidated,
              'execution_timing': execution_timing, 'execution_timing_error': timing_error,
              'cost_comparable': result['state'] == 'passed' and bool(rows) and all(row['cost_comparable'] for row in rows),
              'report_error': '; '.join(filter(None, [result.get('report_error'), *errors])) or None,
              'limits': 'Native phase costs exclude preparation, semantic review and human effort. A usage sample without a same-turn native closing boundary covering later model output is a lower bound; full token totals stay unknown. Phase-boundary trees observe bytes, modes and links; saved intermediate checkpoints observe text only. Git HEAD/refs protect history at phase boundaries; index entries are diagnostic. Writes undone within one tool call and intermediate binary/mode/link/Git changes are not audited.'}
    here = Path(__file__).resolve().parent
    reporter_files = [Path(__file__), here / 'oracle.py', here / 'run.py', here.parent / 'benchmark/run.py',
                      here.parent / 'benchmark/handoff.py', here.parent / 'run-performance-trials.py']
    output['provenance'] = {'mode': 'read-only cost reanalysis' if report_output else 'frozen report',
        'source_plan_sha256': hashlib.sha256((root / 'plan.json').read_bytes()).hexdigest(),
        'source_harness_manifest_sha256': hashlib.sha256(json.dumps(plan.get('harness_manifest', {}), sort_keys=True).encode()).hexdigest(),
        'source_execution_timing_sha256': timing_hash,
        'source_sealed_record_sha256': {name: hashlib.sha256((directory / name).read_bytes()).hexdigest()
                                       for name in ('result.json', 'mechanical.json', 'review.json') if (directory / name).is_file()},
        'reporter_sha256': {str(path.relative_to(here.parent)): hashlib.sha256(path.read_bytes()).hexdigest() for path in reporter_files},
        'source_native_sha256': {row['summary'].replace('.summary.json', '.native.jsonl'): row.get('usage_boundary', {}).get('native_sha256') for row in rows},
        'behavior_adjudication': 'Original sealed artifacts and artifact-bound reviews are read unchanged; only cost completeness is reassessed.'}
    if report_output:
        destination.mkdir(parents=True)
    run.save(destination / 'report.json', output)
    lines = ['# Installed context attempt', '', 'State: ' + output['state'], '', output['limits'], '',
             '| Phase evidence | Identity | Seconds | Input | Output |', '| --- | --- | ---: | ---: | ---: |']
    for row in rows:
        costs = row.get('observed_costs') or {}
        def show(key):
            if costs.get(key) is None:
                return 'unknown'
            return str(costs[key]) if key == 'seconds' or row['usage_status'] == 'complete' else f'>= {costs[key]} (total unknown)'
        lines.append(f"| {row['summary']} | {row['identity_state'] or 'verified'} | {show('seconds')} | {show('input_tokens')} | {show('output_tokens')} |")
    if output['report_error']:
        lines += ['', 'Evidence gap: ' + output['report_error']]
    lines += ['', 'Complete executor elapsed seconds: ' + (str(execution_timing['elapsed_seconds']) if execution_timing else 'unknown (not observed for this attempt)')]
    (destination / 'report.md').write_text('\n'.join(lines) + '\n')
    return output


def review(root, record_path):
    plan = json.loads((root / 'plan.json').read_text())
    validate(root, plan)
    if plan.get('schema', 1) < 2:
        raise ValueError('Historical unsealed attempts cannot acquire retrospective acceptance')
    tools, directory = run.handoff_tools(), root / 'run'
    receipt = tools.report_record(directory / 'result.json')
    record = tools.report_record(record_path)
    existing = directory / 'review.json'
    if existing.exists() and tools.report_record(existing) != record:
        raise ValueError('Cannot replace an existing review')
    if receipt.get('evidence') != tools.evidence_identity(directory):
        raise ValueError('Attempt evidence changed before review')
    mechanical = tools.report_record(directory / 'mechanical.json')
    if mechanical.get('state') not in ('semantic_pending', 'calibration_pending') or not mechanical.get('mechanical_passed') or not all(value is True for value in mechanical.get('checks', {}).values()):
        raise ValueError('Sealed mechanical verdict does not permit acceptance')
    tools.checked_review(record, receipt['evidence'])
    if not existing.exists():
        run.save(existing, record)
    receipt['state'] = tools.review_state(record, receipt.get('control') or 'baseline')
    run.save(directory / 'result.json', receipt)


def grade_existing(repo, directory, plan, original_files, summaries):
    ordinary = plan.get('kind') == 'ordinary undeclared creative task'
    hybrid = plan.get('kind') == 'hybrid format5 parent and format4 child'
    continuation = plan.get('kind') == 'synthetic four-session continuation'
    state_path = None
    for log in sorted(directory.glob("[0-9].jsonl")):
        for line in log.read_text().splitlines():
            event = json.loads(line)
            command = event.get("item", {}).get("command", "")
            if "context-source.py" in command:
                found = re.search(r"--state\s+['\"]?([^\s'\";]+)", command)
                if found:
                    target = Path(found.group(1))
                    target = target if target.is_absolute() else repo / target
                    if target.resolve().is_relative_to(repo.resolve()) and target.is_file():
                        state_path = target
    if plan["kind"].startswith("large-register "):
        verdict = register_case.grade(repo, original_files, plan["kind"].split()[1])
    elif continuation:
        verdict = continuation_case.grade(repo, directory)
        threads = [s.get("thread_id") for s in summaries]
        verdict["checks"]["fresh_native_sessions"] = len(threads) == 4 and all(threads) and len(set(threads)) == 4
        verdict["mechanical_passed"] = all(verdict["checks"].values())
    elif hybrid:
        verdict = hybrid_case.grade(repo, directory, original_files)
    elif ordinary:
        commands = [json.loads(line).get("item", {}).get("command", "") for line in (directory / "1.jsonl").read_text().splitlines()]
        verdict = {"checks": {"no_workspace_changes": oracle.snapshot(repo) == original_files,
                              "installed_files_also_unchanged": run.manifest(repo) == plan["fixture_manifest"],
                              "no_context_model_loaded": not any("memory-model.md" in command or "context-spaces.md" in command for command in commands)},
                   "skill_body_read_observed": any("SKILL.md" in command for command in commands),
                   "semantic_review": ["Read final creative response: it must answer the ordinary task without offering/asking to initialize a context space."]}
        verdict["mechanical_passed"] = all(verdict["checks"].values())
    else:
        verdict = source_oracle.grade(repo, "E2E-source", directory, oracle.snapshot, state_path=state_path)
    return verdict


def execute(args):
    root = args.output.resolve()
    if (root / 'execution-timing.json').exists():
        raise ValueError('Do not overwrite an existing execution timing receipt')
    started_at = datetime.now(timezone.utc).isoformat()
    started = time.monotonic()
    owned = []
    try:
        return _execute_attempt(args, owned)
    finally:
        finished_at = datetime.now(timezone.utc).isoformat()
        elapsed = time.monotonic() - started
        if owned:
            mechanical = root / 'run/mechanical.json'
            receipt = {'started_at_utc': started_at, 'finished_at_utc': finished_at,
                       'elapsed_seconds': round(elapsed, 6), 'clock': 'time.monotonic',
                       'plan_sha256': hashlib.sha256((root / 'plan.json').read_bytes()).hexdigest(),
                       'mechanical_sha256': hashlib.sha256(mechanical.read_bytes()).hexdigest() if mechanical.is_file() else None,
                       'boundary': 'execute entry through executor return/exception after terminal sealing; includes setup, zero-model probes, native phases, host transitions and mechanical checks; excludes prepare, external semantic review and construction/persistence of this timing receipt'}
            with (root / 'execution-timing.json').open('x') as output:
                output.write(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')


def _execute_attempt(args, owned):
    if os.environ.get('CI'):
        raise ValueError('Billable models disabled in CI')
    root = args.output.resolve()
    plan = json.loads((root / 'plan.json').read_text())
    validate(root, plan)
    directory = root / 'run'
    if directory.exists():
        raise ValueError('Do not overwrite an installed trial')
    directory.mkdir()
    owned.append(directory)  # Successful atomic mkdir assigns this invocation alone ownership of the attempt.
    result = {'state': 'started', 'phase': 'setup', 'turns': [], 'control': plan.get('longchain', {}).get('control')}
    verdict = {'checks': {}, 'mechanical_passed': False}
    run.save(directory / 'result.json', result)
    summaries = []
    try:
        repo = directory / 'workspace'
        shutil.copytree(root / 'fixture', repo)
        ordinary = plan.get('kind') == 'ordinary undeclared creative task'
        continuation = plan.get('kind') == 'synthetic four-session continuation'
        longchain = plan.get('longchain')
        if longchain:
            import longchain_case
        home = directory / 'codex-home'
        sandbox = run.bench.isolated_command(repo, root / 'install-source', home)
        probe(directory, repo, home, sandbox, plan['prompts'][0], plan['model'], True, not ordinary)
        if args.probe_only:
            result['state'] = 'probe_only'
            return
        original_files = oracle.snapshot(repo)
        phases = plan.get('phases') or [{'id': f'turn-{number}', 'prompt': prompt, 'expected': 'completed', 'consumer': False}
                                        for number, prompt in enumerate(plan['prompts'], 1)]
        for number, spec in enumerate(phases, 1):
            validate(root, plan)
            result['phase'] = spec['id']
            run.save(directory / 'result.json', result)
            fresh = bool(longchain or continuation)
            phase = directory / f'phase-{number}' if fresh else directory
            if fresh:
                phase.mkdir()
            current_repo, tracker = repo, None
            if longchain:
                event = longchain_case.before_phase(repo, number, cases.scenarios.write, longchain)
                run.save(phase / 'host-event.json', event)
            elif continuation:
                continuation_case.before_turn(repo, number, cases.scenarios.write)
            elif number == 2:
                cases.scenarios.write(repo, 'sources/followup.json', source_cases.export([source_cases.CORRECTION]))
            consumer = spec.get('consumer', False)
            if consumer:
                current_repo = directory / 'consumer/workspace'
                current_repo.mkdir(parents=True)
                transfer = {}
                for name in longchain_case.transfer_paths(longchain):
                    target = repo / name
                    if not name.endswith('.md') or target.is_symlink() or not target.resolve().is_relative_to(repo.resolve()):
                        raise ValueError('Invalid portable Markdown owner: ' + name)
                    transfer[name] = target.read_text()
                    cases.scenarios.write(current_repo, name, transfer[name])
                run.save(directory / 'handoff.json', transfer)
                for name, content in longchain_case.consumer_seed_files(longchain).items():
                    target = current_repo / name
                    if not target.resolve().is_relative_to(current_repo.resolve()) or name in transfer:
                        raise ValueError('Invalid frozen consumer seed: ' + name)
                    cases.scenarios.write(current_repo, name, content)
                output = longchain['consumer']['output']
                (current_repo / 'AGENTS.md').write_text(f'# Workspace rules\n\nUse the maintained documents for the task. Edit only {output}; preserve all other files. Do not commit, access outside projects or invoke other models.\n')
            before = run.bench.transport.snapshot(current_repo)
            before_tree = run.bench.transport.tree_snapshot(current_repo)
            before_git = git_identity(current_repo) if longchain else None
            if longchain:
                run.save(phase / 'git-before.json', before_git)
            if fresh:
                phase_home = phase / 'codex-home'
                tools_root = root / 'install-source'
                if consumer:
                    tools_root = directory / 'empty-tools'
                    tools_root.mkdir()
                phase_sandbox = run.bench.isolated_command(current_repo, tools_root, phase_home)
            else:
                phase_home, phase_sandbox = home, sandbox
            for name in spec.get('readonly_fault_paths', []):
                target = current_repo / name
                if target.is_symlink() or not target.is_file() or not target.resolve().is_relative_to(current_repo.resolve()):
                    raise ValueError('Invalid controlled read-only owner: ' + name)
                phase_sandbox = phase_sandbox[:-1] + ['--ro-bind', str(target), str(target), '--']
            run.save(phase / f'{1 if fresh else number}.phase-setup.json', {'readonly_fault_paths': spec.get('readonly_fault_paths', []),
                     'consumer': consumer, 'fresh_session': fresh})
            if spec.get('expected') == 'intentional_interruption':
                tracker = longchain_case.interrupt_tracker(before, longchain)
            if consumer:
                probe(phase, current_repo, phase_home, phase_sandbox, spec['prompt'], plan['model'], False, False)
            turn = 1 if fresh else number
            summary = run.bench.transport.execute_turn(root, phase, current_repo, spec['prompt'], turn, plan['cap'],
                sandbox_command=phase_sandbox, codex_home=phase_home, capture_checkpoints=True,
                interrupt_when=tracker, model=plan['model'], allow_no_git=True, installed_mode=True)
            summaries.append(summary)
            if tracker:
                run.save(phase / 'interruption-observation.json', tracker.observed)
            observation = oracle.native_observation(summary, plan['model'], phase / f'{turn}.native.jsonl')
            result['turns'].append({'phase': spec['id'], 'summary': str((phase / f'{turn}.summary.json').relative_to(directory)), **observation})
            failure = phase_state(summary, plan['model'], not consumer, not ordinary and not consumer,
                                  interrupted=spec.get('expected') == 'intentional_interruption')
            if failure:
                result['state'] = failure
                break
            if longchain:
                tree_checks = workspace_checks(before_tree, run.bench.transport.tree_snapshot(current_repo), longchain, consumer)
                tree_checks.update(checkpoint_checks(phase, turn, before, longchain, consumer))
                try:
                    after_git = git_identity(current_repo)
                    run.save(phase / 'git-after.json', after_git)
                    tree_checks.update(git_history_observation_complete=True, git_history_identity_preserved=same_git_history(before_git, after_git))
                except (OSError, ValueError) as exc:
                    tree_checks.update(git_history_observation_complete=False, git_history_identity_preserved=False)
                if not all(tree_checks.values()):
                    verdict = {'checks': tree_checks, 'mechanical_passed': False}
                    complete = all(tree_checks[key] for key in ('tree_observation_complete', 'checkpoint_observation_complete', 'git_history_observation_complete'))
                    result['state'] = 'failed_quality' if complete else 'observer_failure'
                    run.save(phase / 'phase-verdict.json', verdict)
                    break
                try:
                    if consumer:
                        checked = longchain_case.consumer_grade(current_repo, phase, longchain, phase_sandbox)
                    else:
                        checked = longchain_case.phase_grade(repo, number, phase, before, longchain)
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    result.update(state='observer_failure', observation_error=f'{type(exc).__name__}: {exc}')
                    break
                checked['checks'].update(tree_checks)
                checked['mechanical_passed'] = checked['mechanical_passed'] and all(tree_checks.values())
                run.save(phase / 'phase-verdict.json', checked)
                if not checked['mechanical_passed']:
                    verdict = checked
                    result['state'] = adjudication_failure(checked)
                    break
            run.save(directory / 'result.json', result)
        else:
            try:
                verdict = longchain_case.grade(repo, directory, longchain) if longchain else grade_existing(repo, directory, plan, original_files, summaries)
            except (OSError, ValueError, KeyError, TypeError) as exc:
                result.update(state='observer_failure', observation_error=f'{type(exc).__name__}: {exc}')
                return
            if longchain:
                threads = [summary.get('thread_id') for summary in summaries]
                verdict['checks']['fresh_native_sessions'] = len(threads) == len(phases) and all(threads) and len(set(threads)) == len(threads)
                verdict['mechanical_passed'] = verdict['mechanical_passed'] and all(value is True for value in verdict['checks'].values())
            if verdict['mechanical_passed']:
                result['state'] = 'calibration_pending' if result['control'] in ('floor', 'stale') else 'semantic_pending'
            else:
                result['state'] = adjudication_failure(verdict)
        verdict.update(actual_catalog_observed=True, agents_wiring_expected=not ordinary,
            all_native_identities_verified=all(run.bench.transport.native_identity_state(summary, plan['model']) is None for summary in summaries),
            native_observations=[{key: value for key, value in turn.items() if key not in ('phase', 'summary')} for turn in result['turns']],
            costs=[turn['costs'] for turn in result['turns']])
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        result.update(state='infra', error=f'{type(exc).__name__}: {exc}')
        failure = {'type': type(exc).__name__, 'message': str(exc), 'phase': result['phase']}
        if isinstance(exc, subprocess.TimeoutExpired):
            failure.update(timeout_seconds=exc.timeout, command=exc.cmd)
            prefix = 'setup-timeout' if result['phase'] == 'setup' else 'phase-timeout'
            for stream in ('stdout', 'stderr'):
                data = getattr(exc, stream, None)
                if data is not None:
                    path = directory / f'{prefix}.{stream}'
                    path.write_bytes(data.encode() if isinstance(data, str) else data)
                    failure[stream + '_file'] = path.name
        run.save(directory / 'infrastructure-error.json', failure)
    finally:
        try:
            validate(root, plan)
        except (OSError, ValueError) as exc:
            result.update(state='observer_failure', frozen_artifact_error=str(exc))
        seal(directory, result, verdict)
        print(json.dumps({'state': result['state'], 'phase': result['phase'], 'native_phases': len(summaries)}), flush=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--prepare", action="store_true")
    modes.add_argument("--run-models", action="store_true")
    modes.add_argument("--report", action="store_true")
    modes.add_argument("--review", type=Path)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report-output", type=Path, help="Read frozen evidence and write cost reanalysis to a new external directory; never rewrite the original report")
    parser.add_argument("--model", help="Explicit currently authorized model, required for prepare")
    parser.add_argument("--cap", type=int, default=600)
    parser.add_argument("--probe-only", action="store_true", help="With run mode, stop after actual zero-model discovery probe")
    parser.add_argument("--ordinary-negative", action="store_true", help="Prepare installed skills without any declared space or AGENTS wiring")
    parser.add_argument("--hybrid", action="store_true", help="Prepare an installed mixed-format parent/child mono task")
    parser.add_argument("--continuation", action="store_true", help="Prepare synthetic four-session continuation")
    parser.add_argument("--large-register", choices=("conflict", "typo"), help="Prepare an 80-rule development register task")
    parser.add_argument("--longchain", action="store_true", help="Prepare a bounded multi-owner interruption and cold handoff")
    parser.add_argument("--longchain-kind", choices=("development", "confirmation"), default="development")
    parser.add_argument("--longchain-control", choices=("ceiling", "floor", "stale"))
    parser.add_argument("--longchain-contract", type=Path, help="Freeze an explicitly supplied independent case contract")
    args = parser.parse_args()
    if args.report_output and not args.report:
        parser.error('--report-output requires --report')
    if args.prepare:
        if sum((args.hybrid, args.ordinary_negative, args.continuation, bool(args.large_register), args.longchain)) > 1:
            parser.error("Choose one installed fixture mode")
        if not args.candidate or not args.model:
            parser.error("--candidate and explicit --model required")
        if not args.longchain and (args.longchain_contract or args.longchain_control or args.longchain_kind != 'development'):
            parser.error("Longchain contract, kind and control require --longchain")
        freeze(args)
    elif args.report:
        report(args.output.resolve(), args.report_output)
    elif args.review:
        review(args.output.resolve(), args.review)
    else:
        execute(args)


if __name__ == "__main__":
    main()
