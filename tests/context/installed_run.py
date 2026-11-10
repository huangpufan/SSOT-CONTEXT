#!/usr/bin/env python3
"""Candidate-only actual installation/discovery trial; ordinary user prompts."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

import cases
import oracle
import run
import source_cases
import source_oracle
import hybrid_case

FIRST = "请把 sources/initial.json 里的这次访谈导出接续整理到这个上下文空间既有的研究和创作笔记，保留各自原意及适用范围，并维护必要的简短入口。我同意在这个空间保存记忆；可信来源、范围及已授权owner见connector-setup.txt。以后还会追加导出，请保存各项完成和未完成进度，使换会话后能接续且不重复处理。原始导出保持原样，已经接受的方法继续有效，请报告实际范围和剩余事项。"
SECOND = "访谈来源新增 sources/followup.json，请按原授权把有限更正反映到相关既有笔记中，保留其他已接受约定、原始来源和历史。完成后说明当前保存和接入进度，不将计划描述为已经实现。"
ORDINARY = "请给一篇有关搬家的短篇写一个80字左右的开头，安静一点。"


def freeze(args):
    root = args.output.resolve()
    if root.exists() or not root.is_relative_to(Path("/tmp")):
        raise ValueError("Use a new /tmp output")
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
    for name in ("run.py", "cases.py"):
        shutil.copy2(Path(__file__).resolve().parent.parent / "benchmark" / name, harness / "benchmark" / name)
    for name in ("run-performance-trials.py", "continuity_cases.py"):
        shutil.copy2(Path(__file__).resolve().parent.parent / name, harness / name)
    fixture = root / "fixture"
    if args.hybrid:
        hybrid_case.build(fixture)
    elif args.ordinary_negative:
        fixture.mkdir()
    else:
        source_cases.build(fixture, cases.scenarios.write, native_entry=True)
        cases.scenarios.write(fixture, "SSOT/README.md", "---\nssot_format: 5\nlanguage: en\n---\n# Interview research and creative space\n\n[Research](../research/findings.md), [Creative material](../creation/notes.md), and [Authorized experiences](../memory/experiences.md) keep their own meaning and authority. Trusted source scope is in [Connector setup](../connector-setup.txt). Maintained by compatible SSOT-CONTEXT 5.0+ writers; older writers upgrade rather than downgrade.\n")
    command = ["bash", str(source / "install.sh"), "--quickstart", "--agent", "codex", "--scope", "project", "--lang", "zh"]
    installed = subprocess.run(command, cwd=fixture, env={**os.environ, "SOURCE_DIR": str(source)}, capture_output=True, text=True)
    run.save(root / "installation.json", {"command": command, "returncode": installed.returncode, "stdout": installed.stdout, "stderr": installed.stderr,
        "owned_source_copy_permissions": "owner-write restored to checkout-equivalent modes; source snapshot untouched",
        "mode_changes": modes, "source_content_hashes_identical": content_preserved})
    if installed.returncode:
        raise ValueError("Official local installer failed; retain evidence")
    adapter = (fixture / ".agents/skills/ssot-bootstrap/assets/templates/context-adapter.md").read_text()
    start, end = "<!-- SSOT-CONTEXT:BEGIN -->", "<!-- SSOT-CONTEXT:END -->"
    adapter = adapter[adapter.index(start):adapter.index(end) + len(end)].replace("ENTRY", "SSOT/README.md")
    if not args.ordinary_negative:
        (fixture / "AGENTS.md").write_text("# Workspace rules\n\nWork only in this isolated space. Do not commit, push, install dependencies, access other projects, invoke other models or use helpers.\n\n" + adapter + "\n")
    plan = {"schema": 1, "comparison_kind": "candidate actual installed discovery, no performance comparison", "model": args.model,
            "cap": args.cap, "reasoning": "medium", "concurrency": 1,
            "kind": "hybrid format5 parent and format4 child" if args.hybrid else "ordinary undeclared creative task" if args.ordinary_negative else "natural source workflow",
            "prompts": [hybrid_case.TASK] if args.hybrid else [ORDINARY] if args.ordinary_negative else [FIRST, SECOND],
            "source_manifest": run.manifest(source), "fixture_manifest": run.manifest(fixture), "harness_manifest": run.manifest(harness)}
    run.save(root / "plan.json", plan)
    print(f"Installed candidate and froze trial: {root}; no model calls")


def validate(root, plan):
    if Path(__file__).resolve().parent != root / "harness/context":
        raise ValueError("Run frozen installed harness")
    for name, expected in (("install-source", plan["source_manifest"]), ("fixture", plan["fixture_manifest"]), ("harness", plan["harness_manifest"])):
        if run.manifest(root / name) != expected:
            raise ValueError(f"Frozen {name} changed")


def execute(args):
    if os.environ.get("CI"):
        raise ValueError("Billable models disabled in CI")
    root = args.output.resolve()
    plan = json.loads((root / "plan.json").read_text())
    validate(root, plan)
    directory = root / "run"
    if directory.exists():
        raise ValueError("Do not overwrite an installed trial")
    directory.mkdir()
    repo = directory / "workspace"
    shutil.copytree(root / "fixture", repo)
    home = directory / "codex-home"
    sandbox = run.bench.isolated_command(repo, root / "install-source", home)
    # debug has no --ignore-user-config flag; its isolated home has no config.
    debug_command = sandbox + [shutil.which("codex"), "-m", plan["model"], "-C", str(repo), "debug", "prompt-input", plan["prompts"][0]]
    debug = subprocess.run(debug_command, env={**os.environ, "CODEX_HOME": str(home)}, capture_output=True, text=True, timeout=40)
    run.save(directory / "discovery-probe.json", {"command": debug_command, "returncode": debug.returncode, "stdout": debug.stdout, "stderr": debug.stderr})
    ordinary = plan.get("kind") == "ordinary undeclared creative task"
    hybrid = plan.get("kind") == "hybrid format5 parent and format4 child"
    if debug.returncode or "ssot-preflight" not in debug.stdout or (not ordinary and "SSOT-CONTEXT:BEGIN" not in debug.stdout):
        raise ValueError("Installed skill catalog/actual AGENTS not observed in zero-model prompt probe")
    if args.probe_only:
        print("Actual installed skill catalog and AGENTS observed; no model calls")
        return
    summaries = []
    original_files = oracle.snapshot(repo)
    for turn, prompt in enumerate(plan["prompts"], 1):
        if turn == 2:
            cases.scenarios.write(repo, "sources/followup.json", source_cases.export([source_cases.CORRECTION]))
        summary = run.bench.transport.execute_turn(root, directory, repo, prompt, turn, plan["cap"],
            sandbox_command=sandbox, codex_home=home, capture_checkpoints=True, model=plan["model"], allow_no_git=True, installed_mode=True)
        summaries.append(summary)
        if not summary["completed"] or summary["returncode"]:
            break
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
    if hybrid:
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
    verdict["actual_catalog_observed"] = True
    verdict["agents_wiring_expected"] = not ordinary
    verdict["agents_wiring_marker_observed"] = "SSOT-CONTEXT:BEGIN" in debug.stdout
    verdict["all_actual_models_match"] = all(summary.get("native_models") == [plan["model"]] for summary in summaries)
    verdict["native_expected_turns_completed"] = len(summaries) == len(plan["prompts"]) and all(summary["completed"] and not summary["returncode"] for summary in summaries)
    verdict["costs"] = [oracle.native_costs(summary, plan["model"]) for summary in summaries]
    run.save(directory / "verdict.json", verdict)
    validate(root, plan)
    print(json.dumps(verdict, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--prepare", action="store_true")
    modes.add_argument("--run-models", action="store_true")
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", help="Explicit currently authorized model, required for prepare")
    parser.add_argument("--cap", type=int, default=600)
    parser.add_argument("--probe-only", action="store_true", help="With run mode, stop after actual zero-model discovery probe")
    parser.add_argument("--ordinary-negative", action="store_true", help="Prepare installed skills without any declared space or AGENTS wiring")
    parser.add_argument("--hybrid", action="store_true", help="Prepare an installed mixed-format parent/child mono task")
    args = parser.parse_args()
    if args.prepare:
        if args.hybrid and args.ordinary_negative:
            parser.error("Choose one installed fixture mode")
        if not args.candidate or not args.model:
            parser.error("--candidate and explicit --model required")
        freeze(args)
    else:
        execute(args)


if __name__ == "__main__":
    main()
