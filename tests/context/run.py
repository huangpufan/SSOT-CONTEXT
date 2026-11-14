#!/usr/bin/env python3
"""Freeze independent context trials, run opt-in native arms, retain all evidence."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import cases
import oracle
import source_execution

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("benchmark_transport", HERE.parent / "benchmark/run.py")
sys.path.insert(0, str(HERE.parent / "benchmark"))
# The benchmark has its own module named cases; its transport does not need its fixture here.
saved_cases = sys.modules.pop("cases", None)
BENCH_CASE_SPEC = importlib.util.spec_from_file_location("cases", HERE.parent / "benchmark/cases.py")
bench_cases = importlib.util.module_from_spec(BENCH_CASE_SPEC)
BENCH_CASE_SPEC.loader.exec_module(bench_cases)
sys.modules["cases"] = bench_cases
bench = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bench)
sys.modules["cases"] = saved_cases


def handoff_tools():
    """Reuse sealed-review primitives with their benchmark module dependency."""
    name = "context_handoff_tools"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, HERE.parent / "benchmark/handoff.py")
        module = importlib.util.module_from_spec(spec)
        previous = sys.modules.get("run")
        try:
            sys.modules["run"] = bench
            spec.loader.exec_module(module)
        finally:
            if previous is None:
                sys.modules.pop("run", None)
            else:
                sys.modules["run"] = previous
        sys.modules[name] = module
    return sys.modules[name]


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def manifest(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()
            and not {".git", "__pycache__"}.intersection(p.relative_to(root).parts)}


def git_observation(repo):
    if not (repo / ".git").exists():
        return None
    return {"head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip(),
            "status": subprocess.check_output(["git", "status", "--porcelain"], cwd=repo, text=True)}


def prepare(args):
    root = args.output.resolve()
    if root.exists() or not any(root.is_relative_to(Path(p).resolve()) for p in ("/tmp", "/var/tmp")):
        raise ValueError("Use a new output directory under /tmp or /var/tmp")
    root.mkdir(parents=True)
    harness = root / "harness"
    shutil.copytree(HERE, harness / "context", ignore=shutil.ignore_patterns("__pycache__"))
    (harness / "benchmark").mkdir()
    for name in ("run.py", "cases.py", "handoff.py", "handoff_cases.py", "judgment_cases.py"):
        shutil.copy2(HERE.parent / "benchmark" / name, harness / "benchmark" / name)
    for name in ("run-performance-trials.py", "continuity_cases.py"):
        shutil.copy2(HERE.parent / name, harness / name)
    bundle = root / "bundles/baseline"
    shutil.copytree(args.baseline / "skills", bundle / "skills", ignore=shutil.ignore_patterns("__pycache__"))
    fixture_data = {}
    for case in args.cases:
        repo = root / "fixtures" / case
        watermark = cases.build(repo, case)
        fixture_data[case] = {"manifest": manifest(repo), "watermark": watermark, "tasks": cases.tasks(case),
                              "before": oracle.snapshot(repo)}
    model = bench.transport.requested_model(args.model)
    plan = {"schema": 2, "model": model, "reasoning": "medium", "cap": args.cap,
            "baseline_ref": args.baseline_ref, "harness_manifest": manifest(harness),
            "baseline_manifest": manifest(bundle), "cases": fixture_data,
            "concurrency": args.concurrency, "source": str(args.baseline.resolve())}
    if args.connector:
        shared = root / "shared-tools"
        shared.mkdir()
        shutil.copy2(args.connector, shared / "context-source.py")
        plan["shared_tools_manifest"] = manifest(shared)
    elif any(case in ("C06", "C07") for case in args.cases):
        raise ValueError("C06/C07 require an explicitly frozen --connector")
    save(root / "plan.json", plan)
    print(f"Prepared frozen trials: {root}; no model calls")


def validate(root, plan):
    if HERE != root / "harness/context":
        raise ValueError(f"Run frozen harness: python3 {root}/harness/context/run.py --output {root} ...")
    for path, expected in ((root / "harness", plan["harness_manifest"]),
                           (root / "bundles/baseline", plan["baseline_manifest"])):
        if manifest(path) != expected:
            raise ValueError(f"Frozen artifact changed: {path}")
    for case, data in plan["cases"].items():
        if manifest(root / "fixtures" / case) != data["manifest"]:
            raise ValueError(f"Frozen fixture changed: {case}")
    if plan.get("shared_tools_manifest") and manifest(root / "shared-tools") != plan["shared_tools_manifest"]:
        raise ValueError("Frozen shared connector changed")


def attach(root, plan, source):
    validate(root, plan)
    if (root / "candidate.json").exists():
        raise ValueError("Candidate already frozen")
    bundle = root / "bundles/candidate"
    shutil.copytree(source / "skills", bundle / "skills", ignore=shutil.ignore_patterns("__pycache__"))
    save(root / "candidate.json", {"source": str(source.resolve()), "manifest": manifest(bundle)})


def run_arm(args, root, plan):
    if os.environ.get("CI"):
        raise ValueError("Billable models disabled in CI")
    validate(root, plan)
    model = plan["model"]
    bundle = root / "bundles" / args.arm
    if args.arm == "candidate":
        expected = json.loads((root / "candidate.json").read_text())["manifest"]
        if manifest(bundle) != expected:
            raise ValueError("Candidate bundle changed")
    environment = {"codex": subprocess.check_output(["codex", "--version"], text=True).strip(),
                   "python": sys.version, "platform": sys.platform, "model": model,
                   "reasoning": "medium", "PATH": os.environ["PATH"], "concurrency": plan["concurrency"]}
    env_path = root / "environment.json"
    if env_path.exists() and json.loads(env_path.read_text()) != environment:
        raise ValueError("Environment changed")
    if not env_path.exists():
        save(env_path, environment)
    for case in args.cases:
        directory = root / "runs" / case / args.arm
        if directory.exists():
            raise ValueError(f"Refusing to overwrite attempt: {directory}")
        directory.mkdir(parents=True)
        repo = directory / "repo"
        shutil.copytree(root / "fixtures" / case, repo)
        skills = repo / ".agents/skills"
        skills.parent.mkdir(parents=True)
        skills.symlink_to(bundle / "skills", target_is_directory=True)
        if case in ("C06", "C07"):
            (repo / ".tools").symlink_to(root / "shared-tools", target_is_directory=True)
        home = directory / "codex-home"
        def sandbox_for(session_home):
            command = bench.isolated_command(repo, bundle, session_home)
            if case in ("C06", "C07"):
                command = command[:-1] + ["--ro-bind", str(root / "shared-tools"), str(root / "shared-tools"), "--"]
            return command
        sandbox = sandbox_for(home)
        subprocess.run(sandbox + [shutil.which("codex"), "--version"], check=True, capture_output=True, timeout=20)
        adapter = (bundle / "skills/ssot-bootstrap/assets/templates/en/adapter-thin.md").read_text()
        start, end = "<!-- SSOT-CONTEXT:BEGIN -->", "<!-- SSOT-CONTEXT:END -->"
        adapter = adapter[adapter.index(start):adapter.index(end) + len(end)]
        data = plan["cases"][case]
        summaries = []
        def prompt_for(task):
            return (f"Work only in the current isolated workspace. Skills are at {bundle / 'skills'}; read SKILL.md directly when routed. "
                    "Do not commit, push, install dependencies, access other projects or invoke other models. Helpers are unavailable.\n"
                    + adapter + "\nUser task:\n" + task)
        try:
            tasks_to_run = data["tasks"]
            if case == "C07":
                summaries = source_execution.cold_chain(root, directory, repo, bundle, plan, data["tasks"],
                    bench.transport, sandbox_for, prompt_for, save)
                tasks_to_run = []
            for turn, task in enumerate(tasks_to_run, 1):
                before_external = git_observation(repo)
                cases.before_turn(repo, case, turn)
                if turn > 1:
                    save(directory / f"{turn}.external-state.json", {"before": before_external, "after": git_observation(repo)})
                prompt = task
                if turn == 1:
                    prompt = prompt_for(task)
                summary = bench.transport.execute_turn(root, directory, repo, prompt, turn, plan["cap"],
                    sandbox_command=sandbox, codex_home=home, capture_checkpoints=True, model=model,
                    allow_no_git=not (repo / ".git").exists())
                summaries.append(summary)
                if summary["returncode"] or not summary["completed"]:
                    break
            verdict = oracle.grade(repo, case, data["before"], data["watermark"], directory, len(summaries))
            verdict["native_model_matches"] = all(s.get("native_models") == [model] for s in summaries)
            verdict["native_identity_states"] = [bench.transport.native_identity_state(s, model) for s in summaries]
            verdict["native_identities_verified"] = bool(summaries) and not any(verdict["native_identity_states"])
            verdict["native_completed"] = len(summaries) == len(data["tasks"]) and all(s["completed"] and not s["returncode"] for s in summaries)
            if case == "C07":
                verdict["native_completed"] = (len(summaries) == 2 and bool(summaries[0].get("intentional_interruption"))
                                                and summaries[1]["completed"] and summaries[1]["returncode"] == 0)
            verdict["native_observations"] = [oracle.native_observation(s, model,
                directory / s.get('evidence_directory', '') / ('1.native.jsonl' if s.get('evidence_directory') else f'{number}.native.jsonl'))
                for number, s in enumerate(summaries, 1)]
            verdict["costs"] = [value["costs"] for value in verdict["native_observations"]]
            observed_turns = summaries
            if case == "C07" and len(summaries) == 2 and summaries[0].get("intentional_interruption"):
                first = summaries[0]
                initial_failure = bench.transport.native_identity_state(first, model)
                if not first.get("observation_complete"):
                    initial_failure = initial_failure or "observer_failure"
                observed_turns = summaries[1:]
            else:
                initial_failure = None
            failure = initial_failure or bench.transport.completion_state(observed_turns, 1 if case == "C07" else len(data["tasks"]), model)
            verdict["state"] = failure or ("awaiting_semantic_review" if verdict["mechanical_passed"] and verdict["native_completed"] else "failed_quality")
            save(directory / "verdict.json", verdict)
            print(json.dumps({"case": case, "arm": args.arm, **verdict}, ensure_ascii=False), flush=True)
        except Exception as exc:
            save(directory / "infrastructure-error.json", {"type": type(exc).__name__, "message": str(exc)})
            raise
    validate(root, plan)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--prepare", action="store_true")
    modes.add_argument("--run-models", action="store_true")
    modes.add_argument("--attach-candidate", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--model", help="Required when preparing; explicit choice must have the caller's current authorization")
    parser.add_argument("--connector", type=Path, help="Freeze an explicitly supplied external connector for shared-tool comparisons")
    parser.add_argument("--baseline-ref", default="7c15dd8")
    parser.add_argument("--arm", choices=("baseline", "candidate"), default="baseline")
    parser.add_argument("--cases", choices=cases.CASES, nargs="+", default=["C01", "D03"])
    parser.add_argument("--cap", type=int, default=300)
    parser.add_argument("--concurrency", type=int, default=1)
    args = parser.parse_args()
    if args.prepare:
        if not args.baseline:
            parser.error("--baseline required for preparation")
        if not args.model:
            parser.error("--model required for preparation; the runner does not establish model authorization")
        prepare(args)
    else:
        root = args.output.resolve()
        plan = json.loads((root / "plan.json").read_text())
        if args.attach_candidate:
            attach(root, plan, args.attach_candidate)
        else:
            run_arm(args, root, plan)


if __name__ == "__main__":
    main()
