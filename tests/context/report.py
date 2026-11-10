#!/usr/bin/env python3
"""Build a compact, auditable result inventory from preserved native evidence."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest_manifest(manifest):
    return hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def inventory(root):
    experiments, attempts, pre_model_failures = [], [], []
    for folder in sorted(root.iterdir()):
        plan_path = folder / "plan.json"
        if not plan_path.exists():
            failed_install = folder / "installation.json"
            if failed_install.exists():
                value = json.loads(failed_install.read_text())
                pre_model_failures.append({"experiment": folder.name, "stage": "installation before plan freeze", "returncode": value.get("returncode"),
                    "evidence": str(failed_install.relative_to(root)), "sha256": checksum(failed_install), "native_model_calls": 0,
                    "classification": "Read-only snapshot modes were inherited by the owned source copy; fixture producer was corrected to restore checkout-equivalent owner-write modes without changing content."})
            continue
        plan = json.loads(plan_path.read_text())
        if "harness_manifest" not in plan:
            continue
        candidate_path = folder / "candidate.json"
        candidate = json.loads(candidate_path.read_text()) if candidate_path.exists() else None
        entry = {"id": folder.name, "model": plan.get("model"), "reasoning": plan.get("reasoning"),
                 "cap_seconds": plan.get("cap"), "declared_concurrency": plan.get("concurrency"),
                 "plan_sha256": checksum(plan_path), "harness_manifest_sha256": digest_manifest(plan["harness_manifest"]),
                 "harness_manifest": plan["harness_manifest"],
                 "prepared_only": not (folder / "runs").exists() and not any((folder / "run").glob("[0-9].summary.json"))}
        baseline_manifest = plan.get("baseline_manifest", plan.get("bundles", {}).get("baseline", {}).get("manifest"))
        candidate_manifest = candidate.get("manifest") if candidate else plan.get("source_manifest", plan.get("bundles", {}).get("candidate", {}).get("manifest"))
        for arm, manifest in (("baseline", baseline_manifest), ("candidate", candidate_manifest)):
            if manifest:
                entry[f"{arm}_manifest"] = manifest
                entry[f"{arm}_manifest_sha256"] = digest_manifest(manifest)
        if candidate:
            entry["candidate_snapshot"] = Path(candidate["source"]).parent.name
        elif plan.get("bundles", {}).get("candidate", {}).get("source"):
            entry["candidate_snapshot"] = Path(plan["bundles"]["candidate"]["source"]).parent.name
        if plan.get("shared_tools_manifest"):
            entry["shared_tools_manifest"] = plan["shared_tools_manifest"]
        experiments.append(entry)
        run_root = folder / "runs"
        for directory in sorted(run_root.glob("*/*")):
            if not directory.is_dir():
                continue
            case, arm = directory.parent.name, directory.name
            pair = next((pair for pair in plan.get("pairs", []) if pair.get("id") == case), None)
            summaries = sorted(directory.glob("[0-9].summary.json")) + sorted(directory.glob("phase-*/[0-9].summary.json"))
            item = {"experiment": folder.name, "case": case, "arm": arm,
                    "evidence_directory": str(directory.relative_to(root)), "turns": []}
            if pair:
                item["case"], item["pair"], item["repeat"] = pair["case"], pair["id"], pair["repeat"]
            for path in summaries:
                summary = json.loads(path.read_text())
                native_path = path.with_name(path.name.replace("summary.json", "native.jsonl"))
                usage = summary.get("native_turn_usage")
                turn = {"summary": str(path.relative_to(root)), "summary_sha256": checksum(path),
                        "requested_model": summary.get("requested_model", summary.get("model_requested")),
                        "actual_models": summary.get("native_models"), "native_turn_id": summary.get("native_turn_id"),
                        "seconds": summary.get("seconds"), "returncode": summary.get("returncode"),
                        "completed": summary.get("completed"), "intentional_interruption": summary.get("intentional_interruption"),
                        "native_receipt_sha256": checksum(native_path) if native_path.exists() else None,
                        "usage_source": "native turn record" if usage else "missing", "usage": usage}
                turn["input_plus_output_tokens"] = usage["input_tokens"] + usage["output_tokens"] if usage else None
                item["turns"].append(turn)
            for path in sorted(set(directory.glob("verdict*.json")) | set(directory.glob("[0-9].verdict.json"))):
                item.setdefault("verdicts", []).append({"file": str(path.relative_to(root)), "sha256": checksum(path), "result": json.loads(path.read_text())})
            if (directory / "result.json").exists():
                item["benchmark_result"] = json.loads((directory / "result.json").read_text())
            for path in sorted(directory.glob("*observations.json")) + sorted(directory.glob("*classification.json")):
                item.setdefault("independent_observations", []).append({"file": str(path.relative_to(root)), "data": json.loads(path.read_text())})
            attempts.append(item)
        directory = folder / "run"
        summaries = sorted(directory.glob("[0-9].summary.json"))
        if summaries:
            turns = []
            for path in summaries:
                summary = json.loads(path.read_text())
                usage = summary.get("native_turn_usage")
                native = path.with_name(path.name.replace("summary.json", "native.jsonl"))
                turns.append({"summary": str(path.relative_to(root)), "summary_sha256": checksum(path),
                              "requested_model": summary.get("requested_model"), "actual_models": summary.get("native_models"),
                              "native_turn_id": summary.get("native_turn_id"), "seconds": summary.get("seconds"),
                              "returncode": summary.get("returncode"), "completed": summary.get("completed"), "usage": usage,
                              "usage_source": "native turn record" if usage else "missing",
                              "input_plus_output_tokens": usage["input_tokens"] + usage["output_tokens"] if usage else None,
                              "native_receipt_sha256": checksum(native) if native.exists() else None})
            installed_case = {"ordinary undeclared creative task": "installed-ordinary", "hybrid format5 parent and format4 child": "installed-hybrid"}.get(plan.get("kind"), "installed-source")
            attempts.append({"experiment": folder.name, "case": installed_case, "arm": "candidate", "turns": turns,
                             "evidence_directory": str(directory.relative_to(root)),
                             "verdicts": [{"file": str((directory / "verdict.json").relative_to(root)), "result": json.loads((directory / "verdict.json").read_text())}] if (directory / "verdict.json").exists() else []})
        for filename in ("installation.json", "run/discovery-probe.json"):
            path = folder / filename
            if path.exists():
                result = json.loads(path.read_text())
                entry.setdefault("installation_discovery", []).append({"file": str(path.relative_to(root)), "sha256": checksum(path),
                    "returncode": result.get("returncode"), "source_content_hashes_identical": result.get("source_content_hashes_identical"),
                    "model_calls": 0 if not summaries else "see native attempts"})
    turns = [turn for attempt in attempts for turn in attempt["turns"]]
    used = [turn["usage"] for turn in turns if turn.get("usage")]
    manifests = {}
    for experiment in experiments:
        for key in list(experiment):
            if key.endswith("_manifest") and isinstance(experiment[key], dict):
                manifest = experiment.pop(key)
                identity = digest_manifest(manifest)
                manifests.setdefault(identity, manifest)
                experiment[key + "_ref"] = identity
    result = {"schema": 2, "generated_at": datetime.now(timezone.utc).isoformat(),
            "status": "Scoped native evidence complete; see trials-5.0.md for semantic conclusions, failures and candidate applicability",
            "model_authorization": "gpt-6.1-sol was explicitly authorized for this task only; this result does not change repository model policy",
            "baseline_ref": "7c15dd8", "baseline_protocol": "4.5", "evidence_root": str(root),
            "experiments": experiments, "manifests": manifests, "attempts": attempts, "pre_model_failures": pre_model_failures,
            "observed_totals": {"native_turns_attempted": len(turns), "completed_turns": sum(bool(t["completed"]) for t in turns),
                "missing_native_usage_turns": sum(not bool(t.get("usage")) for t in turns),
                "intentional_interruption_turns": sum(bool(t.get("intentional_interruption")) for t in turns),
                "unexpected_incomplete_turns": sum(not t["completed"] and not t.get("intentional_interruption") for t in turns),
                "input_tokens": sum(u["input_tokens"] for u in used), "output_tokens": sum(u["output_tokens"] for u in used),
                "input_plus_output_tokens": sum(u["input_tokens"] + u["output_tokens"] for u in used),
                "sum_turn_elapsed_seconds": round(sum(t.get("seconds", 0) for t in turns), 3)},
            "limits": ["Interrupted usage is the observed native record at interruption, not an invented zero or guaranteed final provider bill.",
                       "Summed native elapsed durations can overlap; they are not whole-experiment wall time.",
                       "One observed path and mechanical checks do not establish general reliability or semantic completeness.",
                       "Original verdicts and corrected grader verdicts coexist; failures, prepared-only experiments and costs are retained."]}
    reading_audit = root / "reading-v2/reading-path-audit.json"
    if reading_audit.exists():
        result["reading_path_audit"] = json.loads(reading_audit.read_text())
    for arm in ("baseline", "candidate"):
        directory = root / "source-v4/runs/C07" / arm
        if not (directory / "interrupted-status.json").exists():
            continue
        interrupted = json.loads(json.loads((directory / "interrupted-status.json").read_text())["stdout"])
        final = json.loads(json.loads((directory / "oracle-status.json").read_text())["stdout"])
        stale = json.loads((directory / "stale-complete.json").read_text())
        def units(status):
            return [{"item": item["item_id"], "revision": item["revision"], "status": item["status"], "outcome": item.get("outcome"),
                     "targets": item.get("targets"), "receipt_count": len(item.get("receipts", [])), "reference_count": len(item.get("references", []))} for item in status.get("items", [])]
        result.setdefault("representative_continuous_paths", []).append({"case": "C07", "arm": arm,
            "interrupted_after_actual_two_owner_readback": units(interrupted), "stale_complete_returncode": stale["returncode"],
            "stale_complete_error": stale["stderr"].strip(), "fresh_session_final_units": units(final),
            "evidence_directory": str(directory.relative_to(root)),
            "limit": "Owned-process SIGTERM at a recorded event boundary; not power loss, mid-file-write atomicity or cross-machine recovery."})
    semantic = Path(__file__).resolve().parent / "trials-5.0.md"
    if semantic.exists():
        result["semantic_report"] = {"file": "tests/context/trials-5.0.md", "sha256": checksum(semantic)}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = inventory(args.evidence_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result["observed_totals"]))


if __name__ == "__main__":
    main()
