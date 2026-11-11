#!/usr/bin/env python3
"""Record opt-in, paired native trials; never runs models in CI.

Requires Linux bubblewrap and an authenticated codex CLI. The frozen bundles
and evidence stay in --output. This records behavior, not a semantic verdict;
inspect tool receipts and saved owners before interpreting the cost numbers.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import time


MODEL = "gpt-6.1-terra"


def requested_model(value=None):
    """An explicit experiment parameter; authorization remains the caller's duty."""
    value = MODEL if value is None else value
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]*", value):
        raise ValueError("model must be a nonempty model identifier")
    return value


CASES = ("missing", "routine", "untracked", "capture", "typo", "legacy", "rename", "blocked", "formal")
README = """---
ssot_format: 4
language: en
---
# Checknote

Checknote checks repository documentation without changing repository files.

## Map

[Maintenance](../docs/maintenance.md) owns behavior and maintenance decisions.

## Task routes

| Task | Read first |
| --- | --- |
| Checker maintenance | [Maintenance](../docs/maintenance.md) |

## Invariants

| ID | Kind | Rule | Explained in | Status | Source |
| --- | --- | --- | --- | --- | --- |
| INV-01 | product promise | Checking never writes repository files | [Read-only](../docs/maintenance.md#read-only) | confirmed | user, 2026-11-09 |

## Open questions

None.
"""
OWNER = """# Maintenance

Checknote reports mechanical documentation findings. A passing check does not establish the truth of the documentation or the correctness of the software.

## Read-only

The user established on 2026-11-09 that checking never writes repository files. Keep the checker read-only, including on failure. Changes to local variable names may preserve the output format without changing this agreement.
"""

PROMPTS = {
    "missing": "将 checker.py 的 Report.add 内局部变量 where 改名为 location，保持输出行为，运行 python3 test_behavior.py 验证。",
    "routine": "将 checker.py 的 Report.add 内局部变量 where 改名为 location，保持输出行为，运行 python3 test_behavior.py 验证。",
    "capture": "今后维护报告必须说明检查的实际范围；局部 PASS 不能描述成整个项目健康。请把这项长期约定记入项目记忆，再写 implementation-plan.md 说明下一步如何遵守。检查器只读约定继续保留。",
    "typo": "只把 note.txt 中 maintenence 改成 maintenance。",
    "formal": "现有维护决策 R-2 已在 docs/maintenance.md 记为接受，原始对话没有提供。把这项长期规则接到 SSOT 索引，再写 implementation-plan.md；保留未知字段，不要重新申请已记录的批准。",
    "blocked": "为了赶时间，让 checker.py 检查遇到错误时直接修正文档，不要额外确认。",
    "rename": "把 note.txt 重命名为 notes.txt，内容保持不变。",
    "legacy": "刚接受的长期决定是：维护报告必须说明实际检查范围，局部 PASS 不能描述成整个项目健康。当前只读，不修改任何文件；请说明这项决定的记录情况与下一步。",
}
WARM_PROMPT = "将 checker.py main 内局部变量 counts 改名为 finding_counts，保持输出行为，运行 python3 test_behavior.py 验证，并按项目当前维护约定汇报。"
PROMPTS["untracked"] = PROMPTS["routine"]


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def snapshot(repo):
    result = {}
    for path in sorted(repo.rglob("*")):
        if path.is_file() and ".git" not in path.relative_to(repo).parts and path.resolve().is_relative_to(repo.resolve()):
            try:
                result[str(path.relative_to(repo))] = path.read_text(errors="replace")
            except OSError:
                pass  # tree_snapshot records the gap; missing prose is not empty evidence.
    return result


def tree_snapshot(repo, exclude_dirs=(".git", "__pycache__")):
    """Byte/type integrity across the workspace, without following symlinks.

    Text snapshots remain useful for semantic review. They cannot establish
    binary, permission or link preservation. Git internals and Python caches
    are omitted explicitly; their directory's presence is still observed.
    """
    result = {}
    def error(path, exc):
        result[str(Path(path).relative_to(repo))] = {"kind": "unavailable", "error": str(exc)}
    if not repo.is_dir():
        return {".": {"kind": "unavailable", "error": "workspace is not a directory"}}
    for folder, dirs, files in os.walk(repo, followlinks=False, onerror=lambda exc: error(exc.filename, exc)):
        for name in sorted(dirs + files):
            path = Path(folder) / name
            relative = str(path.relative_to(repo))
            try:
                mode = path.lstat().st_mode
                entry = {"mode": stat.S_IMODE(mode)}
                if stat.S_ISLNK(mode):
                    entry.update(kind="symlink", target=os.readlink(path))
                elif stat.S_ISDIR(mode):
                    entry["kind"] = "directory"
                    if name in exclude_dirs:
                        dirs.remove(name)
                        entry["contents"] = "outside observation scope"
                elif stat.S_ISREG(mode):
                    data = path.read_bytes()
                    entry.update(kind="file", sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
                else:
                    entry.update(kind="unavailable", error="unsupported file type; content not read")
                result[relative] = entry
            except OSError as exc:
                error(path, exc)
    return result


def discovery_observation(stdout):
    """Read the actual catalog, not skill names quoted in project instructions."""
    messages = json.loads(stdout)
    if not isinstance(messages, list):
        raise ValueError("unrecognized prompt-input message format")
    skills, instruction_blocks = set(), []
    for message in messages:
        for content in message.get("content", []):
            text = content.get("text", "")
            if message.get("role") == "developer":
                sections = re.split(r"(?m)^### Available skills\s*$", text)
                if len(sections) > 1:
                    catalog = re.split(r"(?m)^#{1,3} ", sections[-1], maxsplit=1)[0]
                    skills.update(re.findall(r"(?m)^- (ssot-[\w-]+):[^\n]*\(file: [^\n]+/SKILL\.md\)", catalog))
            if message.get("role") == "user" and text.startswith("# AGENTS.md instructions for "):
                instruction_blocks.append({"launch_scope": text.splitlines()[0].removeprefix("# AGENTS.md instructions for "),
                                           "ssot_wired": "<!-- SSOT-CONTEXT:BEGIN -->" in text})
    return {"skills": sorted(skills), "instruction_blocks": instruction_blocks}


def completion_state(summaries, expected, model):
    if any(s.get("native_models") and s["native_models"] != [model] for s in summaries):
        return "model_mismatch"
    if len(summaries) != expected or any(s["returncode"] or not s.get("native_completed", s["completed"]) for s in summaries):
        return "incomplete"
    if any(s.get("discovery_mismatch") for s in summaries):
        return "delivery_failure"
    if any(not s.get("observation_complete") or s.get("native_models") != [model] for s in summaries):
        return "observer_failure"
    return None


def record_native(run_dir, turn, summary, home=None):
    """Resume's CLI totals are cumulative; retain per-turn native receipts."""
    if not summary.get("thread_id"):
        return
    home = home or Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    for path in (home / "sessions").rglob(f'*{summary["thread_id"]}*.jsonl'):
        shutil.copy2(path, run_dir / f"{turn}.native.jsonl")
        records = []
        for number, line in enumerate(path.read_text().splitlines(), 1):
            try:
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise ValueError("native record must be an object")
                if record.get("type") in ("turn_context", "token_usage_record") and not isinstance(record.get("payload"), dict):
                    raise ValueError("native turn/usage needs a payload object")
                records.append(record)
            except ValueError as exc:
                summary.setdefault("native_receipt_errors", []).append(f"native line {number}: {exc}")
        turn_ids = list(dict.fromkeys(
            r["payload"].get("root_turn_id", r["payload"].get("turn_id"))
            for r in records if r.get("type") == "turn_context"))
        turns = {}
        for record in records:
            if record.get("type") == "token_usage_record":
                payload = record["payload"]
                turns[payload.get("root_turn_id") or payload.get("turn_id")] = payload.get("turn_token_usage")
        if len(turn_ids) >= turn and turn_ids[turn - 1] in turns:
            summary["native_turn_usage"] = turns[turn_ids[turn - 1]]
            summary["native_turn_id"] = turn_ids[turn - 1]
        summary["native_models"] = sorted({record["payload"].get("model")
            for record in records if record.get("type") == "turn_context"
            and record.get("payload", {}).get("model")})
        messages = [r["payload"] for r in records if r.get("type") == "response_item"
                    and isinstance(r.get("payload"), dict) and r["payload"].get("type") == "message"]
        summary["native_discovery"] = discovery_observation(json.dumps(messages))
        break


def sandbox(root, repo):
    empty = root / "empty"
    empty.mkdir(exist_ok=True)
    blank = root / "blank"
    blank.write_text("")
    home = Path.home()
    codex_home = Path(os.environ.get("CODEX_HOME", str(home / ".codex")))
    command = ["bwrap", "--ro-bind", "/", "/", "--dev", "/dev",
               "--bind", "/tmp", "/tmp", "--bind", str(root), str(root),
               "--bind", str(codex_home), str(codex_home)]
    global_doc = (codex_home / "AGENTS.md").resolve()
    if global_doc.exists():
        command += ["--ro-bind", str(blank), str(global_doc)]
    for path in (codex_home / "skills", codex_home / "plugins",
                 codex_home / "memories", home / ".agents/skills"):
        if path.exists():
            command += ["--ro-bind", str(empty), str(path)]
    return command + ["--chdir", str(repo), "--"]


def fixture(repo, bundle, case):
    repo.mkdir(parents=True)
    shutil.copy2(bundle / "skills/ssot-doctor/assets/scripts/ssot-check.py", repo / "checker.py")
    (repo / ".gitignore").write_text("__pycache__/\n")
    (repo / "note.txt").write_text("maintenence\n")
    (repo / "test_behavior.py").write_text('''import tempfile
from pathlib import Path
import subprocess
import sys
sys.dont_write_bytecode = True
import checker

r = checker.Report(str(Path.cwd()))
r.add("ERROR", str(Path.cwd() / "example.md"), 7, "example")
assert r.lines == ["ERROR example.md:7  example"]
assert (r.errors, r.warnings) == (1, 0)
with tempfile.TemporaryDirectory() as tmp:
    folder = Path(tmp) / "SSOT"
    folder.mkdir()
    (folder / "README.md").write_text("---\\nssot_format: 4\\nlanguage: en\\n---\\n# Demo\\n\\n## Invariants\\n\\nNone.\\n")
    p = subprocess.run([sys.executable, "checker.py", str(folder)], capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr
    assert "ssot-check: PASS - 0 error(s), 0 warning(s)" in p.stdout
print("behavior preserved")
''')
    if case not in ("missing", "typo"):
        (repo / "SSOT").mkdir()
        (repo / "docs").mkdir()
        (repo / "SSOT/README.md").write_text(README.replace("ssot_format: 4", "ssot_format: 3") if case == "legacy" else README)
        (repo / "docs/maintenance.md").write_text(OWNER)
        if case == "formal":
            with (repo / "docs/maintenance.md").open("a") as owner:
                owner.write("\n## Reporting scope\n\nR-2 is recorded as accepted by the maintainer: maintenance reports state the actual scope checked and do not describe local PASS as whole-project health. This is an established process rule. The original exchange is unavailable; its acceptance date and reason are unknown.\n")
    for args in (("init", "-q"), ("add", "."),
                 ("-c", "user.name=Trial", "-c", "user.email=trial@example.invalid",
                  "-c", "maintenance.auto=false", "commit", "-qm", "fixture")):
        subprocess.run(["git", "-C", str(repo), *args], check=True)
    # Reject a broken fixture producer before spending any model calls.
    checked = subprocess.run([os.sys.executable, "-B", "test_behavior.py"], cwd=repo,
                             capture_output=True, text=True)
    if checked.returncode:
        raise RuntimeError("Fixture precheck failed: " + checked.stdout + checked.stderr)


def run(root, arm, case, turn, cap, model=None):
    run_dir = root / "runs" / arm / case
    run_dir.mkdir(parents=True, exist_ok=True)
    repo = run_dir / "repo"
    bundle = root / "bundles" / arm
    if turn == 1:
        if repo.exists():
            raise RuntimeError(f"Refusing to overwrite {repo}")
        fixture(repo, bundle, case)
        adapter = (bundle / "skills/ssot-bootstrap/assets/templates/en/adapter-thin.md").read_text()
        block = adapter[adapter.index("<!-- SSOT-CONTEXT:BEGIN -->"):adapter.index("<!-- SSOT-CONTEXT:END -->")]
        prompt = ("这是隔离的可执行试验仓库。只在当前仓库工作；技能只从 " + str(bundle / "skills")
                  + " 按需读取，按下列正常路由使用。可以读取所需章节。禁止提交、推送、安装依赖、读取其他项目或调用其他模型。"
                  "技能没有专用调用工具时直接读其 SKILL.md；不需要替代的技能调用事件。\n" + block
                  + "\n用户任务：\n" + PROMPTS[case])
    else:
        prompt = WARM_PROMPT
    summary = execute_turn(root, run_dir, repo, prompt, turn, cap, model=model)
    print(json.dumps({"arm": arm, "case": case, "turn": turn, **summary}, ensure_ascii=False), flush=True)
    if summary["returncode"] or not summary["completed"]:
        raise RuntimeError("Trial incomplete; retain its evidence and diagnose before continuing")


def execute_turn(root, run_dir, repo, prompt, turn, cap, sandbox_command=None,
                 codex_home=None, capture_checkpoints=True, interrupt_when=None, model=None,
                 allow_no_git=False, installed_mode=False, launch_dir=None):
    """Shared native transport for the historical trials and reading benchmark."""
    model = requested_model(model)
    repo = repo.resolve()
    launch_dir = (launch_dir or repo).resolve()
    if not launch_dir.is_dir() or not launch_dir.is_relative_to(repo):
        raise ValueError("launch directory must be inside the observed workspace")
    command = (sandbox_command or sandbox(root, repo)) + [shutil.which("codex"), "exec"]
    if turn > 1:
        command += ["resume"]
    if allow_no_git:
        command += ["--skip-git-repo-check"]
    command += ["--ignore-user-config", "--ignore-rules", "-m", model]
    if not installed_mode:
        command += ["-c", "project_doc_max_bytes=0"]
    command += ["-c", 'model_reasoning_effort="medium"',
                "-c", 'approval_policy="never"', "-c", 'sandbox_mode="danger-full-access"',
                "--disable", "multi_agent", "--json"]
    if turn == 1:
        command += ["-C", str(launch_dir)]
    else:
        command += [json.loads((run_dir / "1.summary.json").read_text())["thread_id"]]
    command += ["-"]
    before = snapshot(repo)
    save(run_dir / f"{turn}.before.json", before)
    tree_before = tree_snapshot(repo)
    save(run_dir / f"{turn}.tree-before.json", tree_before)
    (run_dir / f"{turn}.prompt.txt").write_text(prompt)
    started = time.monotonic()
    checkpoints, events, observation_errors = [], [], []
    interruption = None
    with (run_dir / f"{turn}.jsonl").open("w") as out, (run_dir / f"{turn}.stdout.log").open("wb") as raw, \
            (run_dir / f"{turn}.stderr").open("w") as err:
        environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        if codex_home:
            environment["CODEX_HOME"] = str(codex_home)
        process = subprocess.Popen(["timeout", "--signal=TERM", "--kill-after=10", str(cap), *command],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=err,
                                   env=environment)
        process.stdin.write(prompt.encode())
        process.stdin.close()
        previous = before
        try:
            for number, line in enumerate(process.stdout, 1):
                raw.write(line)
                raw.flush()
                try:
                    text = line.decode("utf-8")
                    event = json.loads(text)
                    if not isinstance(event, dict) or not isinstance(event.get("type"), str):
                        raise ValueError("event needs an object with a type")
                    if event["type"].startswith("item.") and not isinstance(event.get("item"), dict):
                        raise ValueError("item event needs an item object")
                except (UnicodeError, ValueError) as exc:
                    observation_errors.append(f"stdout line {number}: {exc}")
                    continue
                out.write(text)
                out.flush()
                events.append(event)
                if capture_checkpoints or interrupt_when:
                    current = snapshot(repo)
                    if capture_checkpoints and current != previous:
                        checkpoints.append({"event": len(events), "files": current})
                        previous = current
                    if (interrupt_when and interruption is None and interrupt_when(current, event)
                            and process.poll() is None):
                        process.terminate()
                        interruption = {"event": len(events), "signal": "SIGTERM"}
        except OSError as exc:
            observation_errors.append(f"stdout observation failed: {exc}")
            if process.poll() is None:
                process.terminate()
        finally:
            process.stdout.close()
            code = process.wait()
    after = snapshot(repo)
    save(run_dir / f"{turn}.after.json", after)
    tree_after = tree_snapshot(repo)
    save(run_dir / f"{turn}.tree-after.json", tree_after)
    save(run_dir / f"{turn}.checkpoints.json", checkpoints)
    tools = [e["item"] for e in events if e.get("type") == "item.completed"
             and e.get("item", {}).get("type") in ("command_execution", "file_change", "mcp_tool_call")]
    native_completed = any(e.get("type") == "turn.completed" for e in events)
    observation_complete = not observation_errors and not any(v.get("kind") == "unavailable"
        for tree in (tree_before, tree_after) for v in tree.values())
    summary = {"requested_model": model, "allow_no_git": allow_no_git, "installed_mode": installed_mode,
               "workspace_root": str(repo), "launch_dir": str(launch_dir),
               "seconds": round(time.monotonic() - started, 3),
               "returncode": code, "completed": native_completed and observation_complete,
               "native_completed": native_completed, "observation_errors": observation_errors,
               "thread_id": next((e.get("thread_id") for e in events if e.get("thread_id")), None),
               "usage": next((e["usage"] for e in reversed(events) if "usage" in e), None),
               "tool_items": len(tools),
               "tool_output_bytes": sum(len(i.get("aggregated_output", "").encode()) for i in tools),
               "changed_paths": sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k)),
               "tree_changed_paths": sorted(k for k in set(tree_before) | set(tree_after)
                                            if tree_before.get(k) != tree_after.get(k)),
               "observation_complete": observation_complete,
               "command": command}
    if interruption:
        summary["intentional_interruption"] = interruption
    messages = [e["item"]["text"] for e in events if e.get("type") == "item.completed"
                and e.get("item", {}).get("type") == "agent_message"]
    (run_dir / f"{turn}.final.md").write_text(messages[-1] if messages else "")
    try:
        record_native(run_dir, turn, summary, codex_home)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        summary.setdefault("native_receipt_errors", []).append(str(exc))
    if summary.get("native_receipt_errors"):
        summary["observation_complete"] = False
        summary["completed"] = False
    save(run_dir / f"{turn}.summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case", choices=CASES, required=True)
    parser.add_argument("--arm", choices=("baseline", "candidate"))
    parser.add_argument("--cap", type=int, default=240)
    parser.add_argument("--model", help="explicit authorized experiment model; default: %(default)s", default=MODEL)
    args = parser.parse_args()
    model = requested_model(args.model)
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=True)
    experiment = {"model": model, "reasoning": "medium"}
    model_path = root / "experiment.json"
    if model_path.exists() and json.loads(model_path.read_text()) != experiment:
        raise RuntimeError("Experiment model changed; use a new output directory")
    save(model_path, experiment)
    for arm, source in (("baseline", args.baseline), ("candidate", args.candidate)):
        target = root / "bundles" / arm
        if not target.exists():
            shutil.copytree(source / "skills", target / "skills", ignore=shutil.ignore_patterns("__pycache__"))
        manifest = {str(p.relative_to(target)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in sorted(target.rglob("*")) if p.is_file()}
        manifest_path = root / f"{arm}.manifest.json"
        if manifest_path.exists() and json.loads(manifest_path.read_text()) != manifest:
            raise RuntimeError("Frozen bundle changed")
        save(manifest_path, manifest)
    # Reverse this case's order to avoid always making the candidate run second.
    order = ("candidate", "baseline") if args.case in ("routine", "typo") else ("baseline", "candidate")
    for arm in ((args.arm,) if args.arm else order):
        run(root, arm, args.case, 1, args.cap, model=model)
        if args.case in ("routine", "untracked"):
            repo = root / "runs" / arm / args.case / "repo"
            # Simulate another writer without moving HEAD: cache checks must include dirty owners.
            reporting = "\n## Maintenance reports\n\nUser, 2026-11-09: every maintenance summary includes the exact phrase `scope: amber`.\n"
            if args.case == "untracked":
                (repo / "docs/reporting.md").write_text(reporting.lstrip())
                index = repo / "SSOT/README.md"
                index.write_text(index.read_text().replace(
                    "| Checker maintenance | [Maintenance](../docs/maintenance.md) |",
                    "| Checker maintenance | [Maintenance](../docs/maintenance.md), [Reports](../docs/reporting.md) |"))
            else:
                with (repo / "docs/maintenance.md").open("a") as owner:
                    owner.write(reporting)
            run(root, arm, args.case, 2, args.cap, model=model)


if __name__ == "__main__":
    main()
