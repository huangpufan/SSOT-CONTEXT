#!/usr/bin/env python3
"""Run frozen native Codex memory trials in disposable copies.

This is an evidence recorder, not a semantic grader. Bubblewrap masks host
instructions and skill discovery without changing CODEX_HOME or host files.
Snapshots observe event boundaries, not every possible intermediate filesystem
state. Review native tool receipts for ordering and shell writes separately.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time


def snapshot(repo):
    return {str(p.relative_to(repo)): p.read_text(errors='replace')
            for p in sorted(repo.rglob('*')) if p.is_file()
            and '.git' not in p.relative_to(repo).parts}


def sandbox(root, cwd):
    empty = root / 'empty'
    empty.mkdir(exist_ok=True)
    home = Path.home()
    codex_home = home / '.codex'
    blank = root / 'empty-instructions'
    blank.write_text('')
    args = ['bwrap', '--ro-bind', '/', '/', '--dev', '/dev',
            '--bind', '/tmp', '/tmp', '--bind', str(root if cwd == root else cwd.parent),
            str(root if cwd == root else cwd.parent),
            '--bind', str(codex_home), str(codex_home)]
    global_instruction = (codex_home / 'AGENTS.md').resolve()
    if global_instruction.exists():
        args += ['--ro-bind', str(blank), str(global_instruction)]
    for name in (home / '.codex/skills', home / '.agents/skills', home / '.codex/plugins'):
        if Path(name).exists():
            args += ['--ro-bind', str(empty), str(name)]
    return args + ['--chdir', str(cwd), '--']


def isolation(root):
    command = sandbox(root, root) + [str(Path.home() / '.local/bin/codex'), '-c',
        'project_doc_max_bytes=0', 'debug', 'prompt-input', 'ISOLATION_ONLY']
    p = subprocess.run(command, capture_output=True, text=True, timeout=30)
    (root / 'isolation.json').write_text(p.stdout)
    (root / 'isolation.stderr').write_text(p.stderr)
    if p.returncode:
        raise RuntimeError('Cannot inspect isolated prompt input')
    forbidden = ('全局开发工作纪律', '<skills_instructions>',
                 str(Path(__file__).resolve().parents[1]), 'MEMORY_SUMMARY')
    if any(s in p.stdout for s in forbidden):
        raise RuntimeError('Host instruction or skill contamination in prompt input')
    return {'command': command, 'forbidden_absent': list(forbidden)}


def run(root, arm, case, turn, cap):
    if case == 'chat' and not (root / 'chat-final.ready').exists():
        raise RuntimeError('Awaiting final conversation protocol freeze')
    run_dir = root / 'runs' / arm / case
    run_dir.mkdir(parents=True, exist_ok=True)
    repo = run_dir / 'repo'
    if turn == 1:
        if repo.exists():
            raise RuntimeError('Refusing to overwrite an existing run')
        shutil.copytree(root / 'fixtures' / arm / case, repo)
    elif not repo.exists():
        raise RuntimeError('Missing native session fixture')
    prompt_path = root / 'prompts' / f'{case}.{turn}.txt'
    prompt = prompt_path.read_text()
    bundle = root / 'bundles' / ('candidate-final' if arm == 'candidate'
                                  and case in ('chat', 'chat-origin-positive', 'newcomer') else arm)
    if turn == 1:
        adapter = (bundle / 'skills/ssot-bootstrap/assets/templates/zh/adapter-thin.md').read_text()
        start = adapter.index('<!-- SSOT-CONTEXT:BEGIN -->')
        end = adapter.index('<!-- SSOT-CONTEXT:END -->') + len('<!-- SSOT-CONTEXT:END -->')
        prompt = ('这是隔离的真实项目摘录试验；只读写当前工作目录，禁止联网、提交、推送、调用其他模型或读取其他项目。'
                  '当前未提供的项目文件不代表不存在，不声称覆盖完整项目。'
                  'SSOT技能只从以下冻结目录按需读取，不使用宿主其他技能：\n' + str(bundle / 'skills') + '\n'
                  + adapter[start:end] + '\n\n本轮用户任务：\n' + prompt)
    command = sandbox(root, repo) + [str(Path.home() / '.local/agent-proxy-bin/codex'), 'exec']
    if turn > 1:
        prior = json.loads((run_dir / '1.summary.json').read_text())
        command += ['resume']
    command += ['--ignore-user-config', '--ignore-rules', '-m', 'gpt-6.1-sol',
                '-c', 'project_doc_max_bytes=0', '-c', 'model_reasoning_effort="high"',
                '-c', 'approval_policy="never"', '-c', 'sandbox_mode="danger-full-access"', '--json',
                '-o', str(run_dir / f'{turn}.final.md')]
    if turn == 1:
        command += ['-s', 'danger-full-access', '-C', str(repo)]
    else:
        command += [prior['session_id']]
    command += ['-']
    (run_dir / f'{turn}.prompt.txt').write_text(prompt)
    before = snapshot(repo)
    (run_dir / f'{turn}.before.json').write_text(json.dumps(before, ensure_ascii=False, indent=2))
    env = dict(os.environ)
    env['PATH'] = os.pathsep.join([str(Path.home() / '.local/agent-proxy-bin'),
                                     str(Path.home() / '.local/bin'), env.get('PATH', '')])
    started = time.monotonic()
    # External timeout bounds the CLI; nonzero/incomplete turns remain failures.
    with (run_dir / f'{turn}.stderr').open('w') as err, (run_dir / f'{turn}.jsonl').open('w') as out:
        p = subprocess.Popen(['timeout', '--signal=TERM', '--kill-after=10', str(cap)] + command,
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=err,
                             text=True, env=env)
        p.stdin.write(prompt)
        p.stdin.close()
        events, checkpoints, session_id = [], [], None
        for line in p.stdout:
            out.write(line)
            out.flush()
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            events.append(event)
            session_id = event.get('thread_id', session_id)
            current = snapshot(repo)
            if current != before:
                checkpoints.append({'event_index': len(events), 'event': event, 'files': current})
                before = current
        returncode = p.wait()
    final = snapshot(repo)
    (run_dir / f'{turn}.checkpoints.json').write_text(json.dumps(checkpoints, ensure_ascii=False, indent=2))
    (run_dir / f'{turn}.after.json').write_text(json.dumps(final, ensure_ascii=False, indent=2))
    completed = any(e.get('type') == 'turn.completed' for e in events)
    summary = {'model_requested': 'gpt-6.1-sol', 'session_id': session_id,
               'seconds': round(time.monotonic() - started, 2), 'returncode': returncode,
               'completed': completed, 'command': command, 'events': len(events),
               'usage': next((e.get('usage') for e in reversed(events)
                              if e.get('type') == 'turn.completed'), None),
               'tool_items': sum(e.get('type') == 'item.completed' and e.get('item', {}).get('type')
                                 in ('command_execution', 'file_change', 'mcp_tool_call') for e in events),
               'changed_paths': sorted(set(final) ^ set(json.loads((run_dir / f'{turn}.before.json').read_text()))
                   | {k for k in final if final.get(k) != json.loads((run_dir / f'{turn}.before.json').read_text()).get(k)})}
    if session_id:
        candidates = list((Path.home() / '.codex/sessions').rglob(f'*{session_id}*.jsonl'))
        for native in candidates:
            shutil.copy2(native, run_dir / f'{turn}.native.jsonl')
            native_events = [json.loads(line) for line in native.read_text().splitlines()]
            starts = [i for i, e in enumerate(native_events)
                      if e.get('payload', {}).get('type') == 'task_started']
            this_turn = native_events[starts[-1]:] if starts else native_events
            usage_records = [e.get('payload', {}) for e in this_turn
                             if e.get('type') == 'token_usage_record']
            summary['native_turn_usage'] = (usage_records[-1].get('turn_token_usage')
                                            if usage_records else None)
            summary['native_tool_calls'] = sum(
                e.get('payload', {}).get('type') in ('function_call', 'custom_tool_call')
                for e in this_turn)
            summary['native_models'] = sorted({e.get('payload', {}).get('model')
                for e in native_events if e.get('type') == 'turn_context'
                and e.get('payload', {}).get('model')})
    (run_dir / f'{turn}.summary.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary))
    return returncode == 0 and completed


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('root', type=Path)
    ap.add_argument('--isolation', action='store_true')
    ap.add_argument('--arm', choices=('baseline', 'candidate'))
    ap.add_argument('--case')
    ap.add_argument('--turn', type=int, default=1)
    ap.add_argument('--cap', type=int, default=240)
    a = ap.parse_args()
    root = a.root.resolve()
    if a.isolation:
        print(json.dumps(isolation(root), indent=2))
    elif not a.arm or not a.case:
        ap.error('--arm and --case are required for model runs')
    elif not run(root, a.arm, a.case, a.turn, a.cap):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
