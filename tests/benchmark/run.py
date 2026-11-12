#!/usr/bin/env python3
"""Prepare, run explicitly billable native reading trials, or report saved evidence."""

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import random
import re
import shutil
import statistics
import subprocess
import sys
import traceback

import cases

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("transport", HERE.parent / "run-performance-trials.py")
transport = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(transport)
PRIMARY_METRICS = ("seconds", "input_tokens", "output_tokens")
DIAGNOSTIC_METRICS = ("cached_input_tokens", "uncached_input_tokens", "tool_items", "tool_output_bytes")
METRICS = PRIMARY_METRICS + DIAGNOSTIC_METRICS


def save(path, value):
    transport.save(path, value)


def manifest(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()
            and not {".git", "__pycache__"}.intersection(p.relative_to(root).parts)}


def init_git(repo):
    env = {**os.environ, "GIT_AUTHOR_DATE": "2026-11-09T00:00:00Z", "GIT_COMMITTER_DATE": "2026-11-09T00:00:00Z"}
    for args in (("init", "-q"), ("add", "."), ("-c", "user.name=Benchmark", "-c", "user.email=benchmark@example.invalid",
                 "-c", "maintenance.auto=false", "commit", "-qm", "fixture")):
        subprocess.run(["git", "-C", str(repo), *args], check=True, env=env, capture_output=True)


def prepare(args):
    root = args.output.resolve()
    if not any(root.is_relative_to(p.resolve()) for p in (Path("/tmp"), Path("/var/tmp"))):
        raise ValueError("Use an output under /tmp or /var/tmp; isolation hides these roots")
    if root.exists():
        raise ValueError("Use a new output directory; plans and evidence are never overwritten")
    if args.comparison == "protocol" and not args.baseline:
        raise ValueError("protocol comparison needs --baseline")
    if args.comparison == "index" and any(c not in ("routed", "warm") for c in args.cases):
        raise ValueError("index comparison supports routed,warm; fallback/typo routes do not differ")
    if args.repeats < 1 or args.documents < 0 or args.cap < 1:
        raise ValueError("repeats/cap must be positive and documents nonnegative")
    if len(set(args.cases)) != len(args.cases):
        raise ValueError("Choose each case once; use --repeats for repetitions")
    root.mkdir(parents=True)
    harness = root / "harness"
    (harness / "benchmark").mkdir(parents=True)
    for name in ("run.py", "cases.py"):
        shutil.copy2(HERE / name, harness / "benchmark" / name)
    shutil.copy2(HERE.parent / "run-performance-trials.py", harness / "run-performance-trials.py")
    plan = {"schema": 1, "comparison": args.comparison,
            "model": transport.requested_model(getattr(args, "model", None)), "reasoning": "medium",
            "seed": args.seed, "repeats": args.repeats, "documents": args.documents, "cap": args.cap,
            "cases": args.cases, "harness_manifest": manifest(harness), "bundles": {}, "pairs": [], "order": []}
    for arm in ("baseline", "candidate"):
        source = (args.baseline if arm == "baseline" and args.comparison == "protocol" else args.candidate).resolve()
        target = root / "bundles" / arm
        shutil.copytree(source / "skills", target / "skills", ignore=shutil.ignore_patterns("__pycache__"))
        plan["bundles"][arm] = {"source": str(source), "manifest": manifest(target)}
    rng = random.Random(args.seed)
    schedule = [(repeat, case) for repeat in range(args.repeats) for case in args.cases]
    rng.shuffle(schedule)
    for repeat, case in schedule:
        pair_id = f"{case}-r{repeat + 1}"
        fixture_seed = args.seed + repeat
        pair = {"id": pair_id, "case": case, "repeat": repeat + 1, "seed": fixture_seed, "fixtures": {}}
        for arm in ("baseline", "candidate"):
            repo = root / "fixtures" / pair_id / arm
            indexed = args.comparison == "protocol" or arm == "candidate"
            p = cases.build(repo, case, indexed, fixture_seed, args.documents)
            # A supplied stub passes compatibility but must fail the target contract.
            public = subprocess.run([sys.executable, "-B", "test_shipping.py"], cwd=repo, capture_output=True)
            if public.returncode:
                raise ValueError("fixture compatibility precheck failed")
            before = transport.snapshot(repo)
            verdict = cases.grade(repo, case, p, before, before)
            if case != "typo" and verdict["checks"]["contract_and_boundaries"]:
                raise ValueError("unmodified fixture incorrectly passes task oracle")
            pair["fixtures"][arm] = manifest(repo)
        a, b = pair["fixtures"].values()
        difference = {k for k in set(a) | set(b) if a.get(k) != b.get(k)}
        expected = {"SSOT/README.md"} if args.comparison == "index" else set()
        if difference != expected:
            raise ValueError(f"non-comparable fixture pair: {difference}")
        plan["pairs"].append(pair)
        # Balance within each case, regardless of the shuffled global position.
        for arm in (("baseline", "candidate") if repeat % 2 == 0 else ("candidate", "baseline")):
            plan["order"].append([pair_id, arm])
    save(root / "plan.json", plan)
    print(f"Prepared {len(plan['order'])} attempts in {root}; no models called")


def isolated_command(repo, bundle, home):
    """Hide sibling runs, host projects, history and answer sources from the subject."""
    home.mkdir(exist_ok=True)
    command = ["bwrap", "--die-with-parent", "--unshare-pid", "--ro-bind", "/", "/",
               "--tmpfs", "/home", "--tmpfs", "/root", "--tmpfs", "/var/tmp", "--tmpfs", "/tmp",
               "--proc", "/proc", "--dev", "/dev", "--bind", str(repo), str(repo),
               "--ro-bind", str(bundle), str(bundle), "--bind", str(home), str(home)]
    host_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    auth = host_home / "auth.json"
    if auth.exists():
        command += ["--ro-bind", str(auth), str(home / "auth.json")]
    # Support npm installs and local proxy launchers without exposing the rest of HOME.
    mounted = set()
    for directory in os.environ["PATH"].split(os.pathsep):
        executable = Path(directory) / "codex"
        if not executable.is_file():
            continue
        actual = executable.resolve()
        if actual.parts[1] in ("home", "root", "tmp") or actual.is_relative_to(Path("/var") / "tmp"):
            package = next((p for p in actual.parents if p.parent.name == "node_modules"), actual)
            if package not in mounted:
                command += ["--ro-bind", str(package), str(package)]
                mounted.add(package)
            if executable != actual:
                command += ["--symlink", str(actual), str(executable)]
    return command + ["--chdir", str(repo), "--"]


def prompt(bundle, case):
    adapter = (bundle / "skills/ssot-bootstrap/assets/templates/en/adapter-thin.md").read_text()
    block = adapter[adapter.index("<!-- SSOT-CONTEXT:BEGIN -->"):adapter.index("<!-- SSOT-CONTEXT:END -->")]
    task = "Only correct maintenence to maintenance in note.txt." if case == "typo" else cases.TASK
    return (f"Work only in the current isolated repository. Skills are available at {bundle / 'skills'}. "
            "Read their SKILL.md directly when routed; no dedicated skill tool is needed. "
            "Do not commit, push, install dependencies, access other projects or invoke other models. "
            "Helpers are unavailable.\n" + block + "\nUser task:\n" + task)


def costs(summary, expected_model=None):
    usage = summary.get("native_turn_usage")
    expected_model = transport.requested_model(expected_model)
    if not usage or transport.native_identity_state(summary, expected_model):
        return None
    fields = ("input_tokens", "cached_input_tokens", "output_tokens")
    if any(not isinstance(usage.get(k), int) or usage[k] < 0 for k in fields):
        return None
    if usage["cached_input_tokens"] > usage["input_tokens"]:
        return None
    return {**{k: summary[k] for k in ("seconds", "tool_items", "tool_output_bytes")},
            **{k: usage[k] for k in fields},
            "uncached_input_tokens": usage["input_tokens"] - usage["cached_input_tokens"]}


def observed_reading_costs(summary):
    """Observed spend survives wrong/unknown identity; missing usage stays unknown."""
    usage = summary.get("native_turn_usage")
    usage = usage if isinstance(usage, dict) else {}
    observed = {key: None for key in METRICS}
    for key in ("seconds", "tool_items", "tool_output_bytes"):
        value = summary.get(key)
        types = (int, float) if key == "seconds" else (int,)
        if type(value) in types and math.isfinite(value) and value >= 0:
            observed[key] = value
    for key in ("input_tokens", "cached_input_tokens", "output_tokens"):
        value = usage.get(key)
        if type(value) is int and value >= 0:
            observed[key] = value
    actual_input, cached = observed["input_tokens"], observed["cached_input_tokens"]
    if actual_input is not None and cached is not None:
        if cached <= actual_input:
            observed["uncached_input_tokens"] = actual_input - cached
        else:
            observed["cached_input_tokens"] = None
    return observed


def reading_turn_costs(summary, model):
    """Reading-only receipt: measurement and comparison eligibility are separate."""
    observed = observed_reading_costs(summary)
    comparable = costs(summary, model) if all(observed[key] is not None for key in METRICS) else None
    return {"costs": comparable, "observed_costs": observed,
            "identity_state": transport.native_identity_state(summary, model),
            "usage_source": "native" if all(observed[k] is not None for k in
                ("input_tokens", "cached_input_tokens", "output_tokens")) else "missing_or_partial_native_usage"}


def reading_report_turn(directory, turn, model):
    """Re-read saved evidence without editing an attempt or inventing its identity."""
    summary = directory / f'{turn["turn"]}.summary.json'
    try:
        saved = json.loads(summary.read_text())
        if not isinstance(saved, dict):
            raise ValueError("native summary is not an object")
        return {**turn, **reading_turn_costs(saved, model)}
    except (OSError, ValueError) as exc:
        error = f"{summary}: {type(exc).__name__}: {exc}"
    # Old receipts can still show recorded spend. Without the native summary
    # they cannot establish that model and effort met this experiment's request.
    observed = turn.get("observed_costs") or turn.get("costs") or {}
    return {**turn, "costs": None, "identity_state": "observer_failure",
            "report_error": error,
            "observed_costs": {key: observed.get(key) for key in METRICS}}


def reading_report_attempt(directory, model):
    """One protected view supplies spend, state and reading diagnostics alike."""
    try:
        if not directory.exists():
            return {"state": "unrun", "turns": [], "report_error": None}
    except OSError as exc:
        return {"state": "observer_failure", "turns": [],
                "report_error": f"{directory}: {type(exc).__name__}: {exc}"}
    result = directory / "result.json"
    errors, turns, state = [], {}, "observer_failure"
    try:
        saved = json.loads(result.read_text())
        if not isinstance(saved, dict) or not isinstance(saved.get("state"), str):
            raise ValueError("result must be an object with a state string")
        if not isinstance(saved.get("turns"), list):
            raise ValueError("result turns must be a list")
        state = saved["state"]
        if state == "passed" and not saved["turns"]:
            errors.append(f"{result}: passed result has no turns")
        for index, turn in enumerate(saved["turns"]):
            if (not isinstance(turn, dict) or type(turn.get("turn")) is not int or turn["turn"] < 1
                    or turn["turn"] in turns):
                errors.append(f"{result}: invalid or duplicate turn at index {index}")
                continue
            turn = dict(turn)
            for field in ("costs", "observed_costs", "reading"):
                if turn.get(field) is not None and not isinstance(turn[field], dict):
                    errors.append(f"{result}: turn {turn['turn']} {field} must be an object or null")
                    turn[field] = None
            turns[turn["turn"]] = turn
    except (OSError, ValueError) as exc:
        errors.append(f"{result}: {type(exc).__name__}: {exc}")
    try:
        for summary in sorted(directory.glob("*.summary.json")):
            match = re.fullmatch(r"([1-9][0-9]*)\.summary\.json", summary.name)
            if not match:
                errors.append(f"{summary}: invalid native turn filename")
                continue
            number = int(match[1])
            if number not in turns:
                turns[number] = {"turn": number}
                errors.append(f"{result}: turn {number} absent from result; retained summary observation")
    except OSError as exc:
        errors.append(f"{directory}: {type(exc).__name__}: {exc}")
    observed = [reading_report_turn(directory, turn, model) for _, turn in sorted(turns.items())]
    errors.extend(turn["report_error"] for turn in observed if turn.get("report_error"))
    if errors:
        state = "observer_failure"
    elif state == "passed":
        for failure in ("model_mismatch", "reasoning_mismatch", "observer_failure"):
            if any(turn.get("identity_state") == failure for turn in observed):
                state = failure
                break
    return {"state": state, "turns": observed, "report_error": "; ".join(errors) or None}


def reading_observations(run_dir, turn):
    """Diagnostic evidence from returned command text, never agent self-report."""
    returned = []
    for line in (run_dir / f"{turn}.jsonl").read_text().splitlines():
        event = json.loads(line)
        if event.get("type") == "item.completed":
            returned.append(event.get("item", {}).get("aggregated_output", ""))
    text = "\n".join(returned)
    return {"contract_seen": "Physical express supports only north and south" in text,
            "eligibility_seen": "digital goods always return fee 0 and days 0" in text,
            "updated_promotion_seen": "superseding only the previous threshold" in text,
            "distractor_documents_seen": len(set(re.findall(r"# (\w+ workflow \d+)", text))),
            "preflight_seen": "# SSOT Preflight" in text}


def validate_frozen(root, plan):
    if manifest(root / "harness") != plan["harness_manifest"]:
        raise ValueError("frozen harness changed")
    # Execute exactly the prepared harness, even if the checkout has since changed.
    if HERE != root / "harness/benchmark":
        raise ValueError(f"Run the frozen harness: python3 {root}/harness/benchmark/run.py --output {root} --run-models")
    for arm, entry in plan["bundles"].items():
        if manifest(root / "bundles" / arm) != entry["manifest"]:
            raise ValueError(f"frozen {arm} bundle changed")
    for pair in plan["pairs"]:
        for arm, expected in pair["fixtures"].items():
            if manifest(root / "fixtures" / pair["id"] / arm) != expected:
                raise ValueError("frozen fixture changed")


def run_models(args):
    if os.environ.get("CI"):
        raise ValueError("Billable model runs are disabled in CI")
    root = args.output.resolve()
    plan = json.loads((root / "plan.json").read_text())
    if getattr(args, "model", None) is not None and args.model != plan["model"]:
        raise ValueError("Model differs from the frozen plan; prepare a new experiment")
    validate_frozen(root, plan)
    for name in ("codex", "bwrap", "timeout", "git"):
        if not shutil.which(name):
            raise ValueError(f"Required executable unavailable: {name}")
    environment = {"codex": subprocess.check_output(["codex", "--version"], text=True).strip(),
                   "python": sys.version, "platform": sys.platform}
    env_file = root / "environment.json"
    if env_file.exists() and json.loads(env_file.read_text()) != environment:
        raise ValueError("environment changed; prepare a new experiment")
    save(env_file, environment)
    pairs = {p["id"]: p for p in plan["pairs"]}
    for pair_id, arm in plan["order"]:
        run_dir = root / "runs" / pair_id / arm
        if (run_dir / "result.json").exists():
            continue  # Preserve all attempts, including failures; never silently retry them.
        if run_dir.exists():
            raise ValueError(f"Interrupted attempt in {run_dir}; preserve it and use a new experiment")
        run_dir.mkdir(parents=True)
        pair = pairs[pair_id]
        repo, bundle = run_dir / "repo", root / "bundles" / arm
        shutil.copytree(root / "fixtures" / pair_id / arm, repo)
        init_git(repo)
        p = cases.policy(pair["seed"])
        result = {"pair": pair_id, "case": pair["case"], "arm": arm, "state": "infra", "turns": []}
        try:
            home = run_dir / "codex-home"
            sandbox = isolated_command(repo, bundle, home)
            # This also probes the actual CLI and mount layout before a billable call.
            subprocess.run(sandbox + [shutil.which("codex"), "--version"], check=True, capture_output=True, timeout=20)
            turns = 2 if pair["case"] == "warm" else 1
            summaries = []
            for turn in range(1, turns + 1):
                if turn == 2:
                    old_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo)
                    p = cases.update(repo, p)
                    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo) == old_head
                text = prompt(bundle, pair["case"]) if turn == 1 else cases.WARM_TASK
                head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo)
                summary = transport.execute_turn(root, run_dir, repo, text, turn, plan["cap"],
                                                 sandbox_command=sandbox, codex_home=home,
                                                 capture_checkpoints=False, model=plan["model"])
                summaries.append(summary)
                before = json.loads((run_dir / f"{turn}.before.json").read_text())
                after = json.loads((run_dir / f"{turn}.after.json").read_text())
                verdict = cases.grade(repo, pair["case"], p, before, after)
                allowed = "note.txt" if pair["case"] == "typo" else "shipping.py"
                verdict["checks"]["byte_type_and_mode_scope"] = summary["tree_changed_paths"] == [allowed]
                verdict["checks"]["head_unchanged"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo) == head
                verdict["passed"] = all(verdict["checks"].values())
                save(run_dir / f"{turn}.verdict.json", verdict)
                result["turns"].append({"turn": turn, "completed": summary["completed"] and summary["returncode"] == 0,
                                        "observation_complete": summary["observation_complete"],
                                        "model_matches": summary.get("native_models") == [plan["model"]],
                                        "reasoning_matches": summary.get("native_reasoning") == [plan["reasoning"]],
                                        "quality_passed": verdict["passed"], **reading_turn_costs(summary, plan["model"]),
                                        "reading": reading_observations(run_dir, turn)})
                if transport.completion_state([summary], 1, plan["model"]):
                    break
            failure = transport.completion_state(summaries, turns, plan["model"])
            result["state"] = failure or ("passed" if all(t["quality_passed"] for t in result["turns"]) else "failed_quality")
        except Exception:
            result["error"] = traceback.format_exc()
            if result["turns"] or (run_dir / "1.jsonl").exists():
                result["state"] = "incomplete"
        save(run_dir / "result.json", result)
        print(json.dumps({"pair": pair_id, "arm": arm, "state": result["state"]}), flush=True)
        report(root)
    validate_frozen(root, plan)


def aggregate(result):
    turns = result.get("turns", [])
    if result["state"] != "passed" or not turns or any(t["costs"] is None for t in turns):
        return None
    return {k: sum(t["costs"][k] for t in turns) for k in METRICS}


def report(root):
    plan = json.loads((root / "plan.json").read_text())
    rows, comparisons, attempts = [], [], []
    for pair in plan["pairs"]:
        values = {}
        for arm in ("baseline", "candidate"):
            directory = root / "runs" / pair["id"] / arm
            value = reading_report_attempt(directory, plan.get("model", transport.MODEL))
            attempts.append({"pair": pair["id"], "arm": arm, **value})
            values[arm] = aggregate(value)
            # All attempted turns retain their cost, including quality failures/timeouts.
            for t in value["turns"] or [{"turn": 0, "costs": None}]:
                rows.append({"pair": pair["id"], "case": pair["case"], "arm": arm, "state": value["state"],
                             "turn": t["turn"], "quality_passed": t.get("quality_passed"),
                             "usage_source": t.get("usage_source", "missing"),
                             "identity_state": t.get("identity_state", "observer_failure"),
                             "report_error": value["report_error"],
                             "cost_comparable": value["state"] == "passed" and t["costs"] is not None,
                             **{key: (t.get("observed_costs") or {}).get(key) for key in METRICS}})
        comparisons.append({"pair": pair["id"], "case": pair["case"], "eligible": all(values.values()), **values})
    save(root / "report.json", {"comparison": plan["comparison"], "attempts": rows, "pairs": comparisons})
    with (root / "report.csv").open("w") as f:
        writer = csv.DictWriter(f, fieldnames=("pair", "case", "arm", "state", "turn", "quality_passed", "usage_source",
                                               "identity_state", "report_error", "cost_comparable", *METRICS))
        writer.writeheader(); writer.writerows(rows)
    lines = [f"# Reading benchmark: {plan['comparison']}", "", "Descriptive observations, not statistical or billing claims. Costs cover whole tasks; warm includes both turns.",
             "Failed, incomplete, infra and unrun attempts retain observed spend; missing usage stays unknown. Only paired passes with verified model, reasoning and native usage enter cost comparisons.", ""]
    state_labels = {"passed": "Pass", "failed_quality": "Quality fail", "incomplete": "Incomplete",
                    "observer_failure": "Observer failure", "model_mismatch": "Model mismatch",
                    "reasoning_mismatch": "Reasoning mismatch", "delivery_failure": "Delivery failure",
                    "infra": "Infra", "unrun": "Unrun"}
    for state in sorted({row["state"] for row in rows} - state_labels.keys()):
        state_labels[state] = state
    lines += ["| Case | Arm | " + " | ".join(state_labels.values()) + " |",
              "| --- | --- | " + " | ".join("---:" for _ in state_labels) + " |"]
    for case in plan["cases"]:
        for arm in ("baseline", "candidate"):
            states = {r["pair"]: r["state"] for r in rows if r["case"] == case and r["arm"] == arm}
            counts = [list(states.values()).count(s) for s in state_labels]
            lines.append(f"| {case} | {arm} | " + " | ".join(map(str, counts)) + " |")
    lines += ["", "## Observed attempt spend", "",
              "These observations include failed and mismatched executions. They are not comparable costs; unknown is not zero.", "",
              "| Pair | Arm | Turn | State | " + " | ".join(METRICS) + " |",
              "| --- | --- | ---: | --- | " + " | ".join("---:" for _ in METRICS) + " |"]
    for row in rows:
        lines.append(f'| {row["pair"]} | {row["arm"]} | {row["turn"]} | {row["state"]} | '
                     + " | ".join(str(row[key]) if row[key] is not None else "unknown" for key in METRICS) + " |")
    if any(attempt["report_error"] for attempt in attempts):
        lines += ["", "## Evidence errors", ""]
        lines += [f'- {attempt["pair"]}/{attempt["arm"]}: {attempt["report_error"]}'
                  for attempt in attempts if attempt["report_error"]]
    for case in plan["cases"]:
        selected = [p for p in comparisons if p["case"] == case and p["eligible"]]
        total = sum(p["case"] == case for p in comparisons)
        lines += ["", f"## {case}: {len(selected)}/{total} usable pairs; {total - len(selected)} excluded", "",
                  "Fewer than three pairs are pipeline observations only; even three do not establish a general gain."]
        for title, metrics in (("Primary: completion time and total input/output", PRIMARY_METRICS),
                               ("Diagnostics: cache and tools; these do not decide efficiency alone", DIAGNOSTIC_METRICS)):
            lines += ["", title, "", "| Metric | Baseline median [min, max] | Candidate median [min, max] | Median paired change |",
                      "| --- | ---: | ---: | ---: |"]
            for metric in metrics:
                if not selected:
                    continue
                a = [p["baseline"][metric] for p in selected]
                b = [p["candidate"][metric] for p in selected]
                fmt = lambda x: f"{statistics.median(x):.3f} [{min(x):.3f}, {max(x):.3f}]"
                lines.append(f"| {metric} | {fmt(a)} | {fmt(b)} | {statistics.median([y-x for x,y in zip(a,b)]):+.3f} |")
    lines += ["", "Native input includes cached input. Uncached = input minus cached. Output is separate; tool bytes are returned text, not disk I/O or tokens.",
              "Inspect saved prompts, commands, native receipts, before/after files and verdicts. The synthetic fixture and injected adapter do not measure skill discovery, production scale, or other models."]
    lines += ["", "## Returned reading evidence", "", "Exact source phrases observed in command output; absence is unknown, not proof a document was unread. These diagnostics do not grade correctness.", "",
              "| Pair | Arm | Turn | Contract | Eligibility | Updated promotion | Distractors | Preflight |",
              "| --- | --- | ---: | --- | --- | --- | ---: | --- |"]
    for attempt in attempts:
        for turn in attempt["turns"]:
            observed = turn.get("reading") or {}
            keys = ("contract_seen", "eligibility_seen", "updated_promotion_seen", "distractor_documents_seen", "preflight_seen")
            lines.append(f"| {attempt['pair']} | {attempt['arm']} | {turn['turn']} | " + " | ".join(str(observed.get(k, "unknown")) for k in keys) + " |")
    (root / "report.md").write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--run-models", action="store_true", help="explicitly authorize billable native runs; disabled in CI")
    mode.add_argument("--report", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--comparison", choices=("protocol", "index"), default="protocol")
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--candidate", type=Path, default=HERE.parents[1])
    parser.add_argument("--cases", nargs="+", choices=cases.CASES, default=list(cases.CASES))
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--documents", type=int, default=24)
    parser.add_argument("--seed", type=int, default=20261109)
    parser.add_argument("--cap", type=int, default=240)
    parser.add_argument("--model", help="authorized model for preparation; execution uses the frozen plan")
    args = parser.parse_args()
    if args.prepare:
        prepare(args)
    elif args.run_models:
        run_models(args)
    else:
        report(args.output.resolve())


if __name__ == "__main__":
    main()
