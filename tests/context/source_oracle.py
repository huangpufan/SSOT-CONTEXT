"""Check public connector progress and saved artifacts; no internal-state schema oracle."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import re

import source_execution
import source_cases


def grade(repo, case, run_dir, snapshot, state_path=None):
    script = repo / ".tools/context-source.py"
    if case == "E2E-source":
        script = repo / ".agents/skills/ssot-doctor/assets/scripts/context-source.py"
    state = state_path or repo / "run/source-state.json"
    result = subprocess.run([sys.executable, str(script), "status", "--state", str(state)], capture_output=True, text=True)
    (run_dir / "oracle-status.json").write_text(json.dumps({"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}, ensure_ascii=False, indent=2))
    try:
        status = json.loads(result.stdout)
    except ValueError:
        status = {}
    records = {(item.get("item_id"), item.get("revision")): item for item in status.get("items", [])}
    source_logs = sorted(run_dir.glob("[0-9].jsonl")) if case != "C07" else sorted(run_dir.glob("phase-*/*.jsonl"))
    source_logs = [p for p in source_logs if not p.name.endswith(".native.jsonl")]
    receipt_events, complete_events, public_views = [], [], []
    commands = []
    r2_markers = set()
    for log_index, log in enumerate(source_logs):
        for number, line in enumerate(log.read_text().splitlines()):
            event = json.loads(line)
            item = event.get("item", {})
            command = item.get("command", "")
            if event.get("type") == "item.completed" and item.get("type") == "command_execution":
                commands.append(command)
                for offset, obj in source_execution.object_entries(item.get("aggregated_output", "")):
                    position = (log_index, number, offset)
                    public_views.append((position, obj))
                    if (isinstance(obj, dict) and obj.get("item_id") == "method"
                            and obj.get("revision") == "r2" and isinstance(obj.get("marker"), str)):
                        r2_markers.add(obj["marker"])
                    if isinstance(obj, dict) and obj.get("status") == "completed" and obj.get("references"):
                        complete_events.append((position, obj))
                for offset, value in source_execution.receipt_entries(event):
                    receipt_events.append(((log_index, number, offset), value))
    checks = {"public_status_available": result.returncode == 0}
    expected_method = "r2" if case == "E2E-source" else "r1"
    method = records.get(("method", expected_method), {})
    method_ids = set(method.get("receipts", []))
    method_owners = {value["receipt"].get("owner") for _, value in receipt_events
                     if value["receipt_id"] in method_ids and isinstance(value.get("receipt"), dict)}
    def reference_set(refs):
        return {json.dumps(ref, sort_keys=True) for ref in refs} if isinstance(refs, list) and all(isinstance(ref, dict) for ref in refs) else set()
    def proves_completion(position, value):
        refs = value.get("references", [])
        known = records.get((value.get("item_id"), value.get("revision")), {}).get("references", [])
        return bool(reference_set(refs)) and reference_set(refs) == reference_set(known) and all(
            any(receipt.get("receipt") == ref and receipt_position < position
                for receipt_position, receipt in receipt_events) for ref in refs)
    if case == "C06":
        # The original remains conflicted after a conflicting same-revision import.
        # Its historical completion must be observed in the event stream, not inferred
        # from its now-conflicted public status or from the successor's receipts.
        required_paths = {str((repo / name).resolve()) for name in ("research/findings.md", "creation/notes.md")}
        checks["multi_owner_method_completed"] = any(
            value.get("item_id") == "method" and value.get("revision") == "r1"
            and proves_completion(position, value)
            and {ref.get("path") for ref in value["references"]} >= required_paths
            for position, value in complete_events)
        # A failed targets operation does not prevent a shell batch from writing
        # afterward. Check observed owner bytes, including intermediate snapshots.
        owner_paths = ("research/findings.md", "creation/notes.md")
        owner_observations = [{name: (repo / name).read_text() for name in owner_paths}]
        original_positions = [position for position, value in complete_events
            if value.get("item_id") == "method" and value.get("revision") == "r1" and proves_completion(position, value)]
        first_completion = min(original_positions) if original_positions else None
        for log_index, log in enumerate(source_logs):
            path = log.with_name(log.stem + ".after.json")
            if path.exists() and (first_completion is None or log_index >= first_completion[0]):
                owner_observations.append(json.loads(path.read_text()))
            path = log.with_name(log.stem + ".checkpoints.json")
            if path.exists():
                owner_observations.extend(checkpoint.get("files", {}) for checkpoint in json.loads(path.read_text())
                    if first_completion is None or (log_index, checkpoint.get("event", 0) - 1) >= first_completion[:2])
        # An interrupted later turn may have checkpoints before a final log is
        # retained. Keep those explicit observations as well.
        known_checkpoints = {log.with_name(log.stem + ".checkpoints.json") for log in source_logs}
        for path in sorted(set(run_dir.glob("[0-9].checkpoints.json")) - known_checkpoints):
            owner_observations.extend(checkpoint.get("files", {}) for checkpoint in json.loads(path.read_text()))
        # This fixture has no other admitted item targeting these two owners
        # after method r1. Compare to its actual completed readback, rather than
        # requiring a subject to inspect a successor already known conflicted.
        original_text = {ref.get("path"): value["saved_owner_text"]
            for ref in method.get("references", []) for _, value in receipt_events
            if value.get("receipt") == ref}
        marker_pattern = r"<!--\s*ssot-source:[^>]+-->"
        checks["unadmitted_successor_marker_absent"] = all(
            str((repo / name).resolve()) in original_text and
            set(re.findall(marker_pattern, observation.get(name, ""))) <= set(re.findall(
                marker_pattern, original_text[str((repo / name).resolve())])) and
            not any(marker in observation.get(name, "") for marker in r2_markers)
            for observation in owner_observations for name in owner_paths)
        successor = records.get(("method", "r2"), {})
        def contains_completed_successor(value):
            if isinstance(value, dict):
                if value.get("item_id") == "method" and value.get("revision") == "r2" and value.get("status") == "completed":
                    return True
                return any(contains_completed_successor(child) for child in value.values())
            if isinstance(value, list):
                return any(contains_completed_successor(child) for child in value)
            return False
        checks["conflicted_method_successor_not_completed"] = bool(successor) and not contains_completed_successor(successor) and not any(
            contains_completed_successor(value) for _, value in public_views)
    else:
        checks["multi_owner_method_completed"] = method.get("status") == "completed" and len(method_owners) >= 2
    checks["readback_receipts_precede_completion"] = any(
        value.get("item_id") == "method" and value.get("revision") == expected_method
        for _, value in complete_events) and all(proves_completion(*event) for event in complete_events)
    checks["actual_saved_text_returned"] = bool(receipt_events) and all(
        isinstance(value.get("receipt"), dict) and
        hashlib.sha256(value["saved_owner_text"].encode()).hexdigest() == value["receipt"].get("file_digest")
        for _, value in receipt_events)
    checks["all_source_originals_preserved"] = True
    phase_dirs = [run_dir] if case != "C07" else [run_dir / "phase-1", run_dir / "phase-2"]
    for phase in phase_dirs:
        for before_path in phase.glob("[0-9].before.json"):
            after_path = before_path.with_name(before_path.name.replace("before", "after"))
            before, after = json.loads(before_path.read_text()), json.loads(after_path.read_text())
            checks["all_source_originals_preserved"] &= all(after.get(name) == text for name, text in before.items() if name.startswith("sources/"))
    allowed = {str((repo / name).resolve()) for name in ("research/findings.md", "creation/notes.md", "memory/experiences.md")}
    checks["only_authorized_owner_bindings"] = bool(status.get("owners")) and set(status.get("owners", {}).values()) <= allowed
    checks["trusted_source_and_scope_retained"] = status.get("source_id") == source_cases.SOURCE_ID and status.get("scope") == source_cases.SCOPE
    if case == "C06":
        checks.update({"same_revision_conflict_visible": records.get(("method", "r1"), {}).get("status") == "conflict",
                       "unknown_target_conflict_visible": records.get(("unknown-item", "r2"), {}).get("status") == "conflict",
                       "explicit_experience_recorded": records.get(("experience", "r1"), {}).get("outcome") == "recorded" and "白鹭" in (repo / "memory/experiences.md").read_text(),
                       "legitimate_no_update_terminal": records.get(("routine", "r1"), {}).get("status") == "completed" and records.get(("routine", "r1"), {}).get("outcome") == "no-update",
                       "limited_withdrawal_completed": records.get(("experience", "r2"), {}).get("status") == "completed",
                       "source_revoked": status.get("source_status") == "withdrawn"})
    if case == "C07":
        stale = json.loads((run_dir / "stale-complete.json").read_text()) if (run_dir / "stale-complete.json").exists() else {}
        checks["stale_receipt_rejected"] = stale.get("returncode") == 2 and "changed" in stale.get("stderr", "").lower()
        checks["actual_interruption_boundary_valid"] = not (run_dir / "interruption-invalid.json").exists() and (run_dir / "interruption-receipts.json").exists()
        first = json.loads((run_dir / "phase-1/1.summary.json").read_text())
        second_path = run_dir / "phase-2/1.summary.json"
        second = json.loads(second_path.read_text()) if second_path.exists() else {}
        checks["fresh_native_session"] = bool(second.get("thread_id")) and first.get("thread_id") != second.get("thread_id")
    tool_observation = {"subject_execution": "unknown", "script_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
        "public_status_via_this_script": result.returncode == 0,
        "command_path_mentioned": any("/bundles/candidate/skills/ssot-doctor/assets/scripts/context-source.py" in command or
            ".agents/skills/ssot-doctor/assets/scripts/context-source.py" in command for command in commands),
        "evidence_limit": "Installed bytes and oracle public status do not independently attest which executable a subject or wrapper invoked."}
    owner_changes = []
    if case == "C06":
        owner_changes = [name for name in owner_paths if str((repo / name).resolve()) in original_text and any(
            observation.get(name, "") != original_text[str((repo / name).resolve())] for observation in owner_observations)]
    return {"checks": checks, "mechanical_passed": all(checks.values()),
            "formal_tool_observation": tool_observation, "conflicted_owner_changes_for_semantic_review": owner_changes,
            "entry_observed": bool(snapshot(repo).get("SSOT/README.md", "").strip()),
            "comparison_kind": "candidate formal skill entry end-to-end" if case == "E2E-source" else "protocol comparison under a shared frozen connector",
            "semantic_review": ["Compare saved owner prose to source question/answer, partial correction and uncertainty; accepted history must stay accepted, ordinary testimony/hypothesis must not become candidate protection.",
                                "Check duplicate capture, all declared/affected owner coverage, source scope mismatch and conflict handling; r2 not completed alone is insufficient: inspect active owner prose for corrections applied without admission, including writes without a marker. Event-boundary snapshots cannot observe writes and reversions within one tool call; absence of observed writes does not prove no transient write. Progress/readback linkage does not prove semantic interpretation.",
                                "Check withdrawal/use permissions versus physical deletion; inspect known owners, task state and host outputs as controlled copies, without all-copies or cross-owner ACID claims."]}
