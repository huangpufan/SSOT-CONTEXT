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
    receipt_events, complete_events = [], []
    commands = []
    for log in source_logs:
        for number, line in enumerate(log.read_text().splitlines()):
            event = json.loads(line)
            item = event.get("item", {})
            command = item.get("command", "")
            if event.get("type") == "item.completed" and item.get("type") == "command_execution":
                commands.append(command)
                for value in source_execution.receipt_results(event):
                    receipt_events.append((log, number, value))
                if "complete" in command and item.get("exit_code") == 0:
                    complete_events.append((log, number, command))
    checks = {"public_status_available": result.returncode == 0}
    expected_method = "r2" if case in ("C06", "E2E-source") else "r1"
    method = records.get(("method", expected_method), {})
    method_ids = set(method.get("receipts", []))
    method_owners = {value.get("receipt", {}).get("owner") for _, _, value in receipt_events if value["receipt_id"] in method_ids}
    checks["multi_owner_method_completed"] = method.get("status") == "completed" and len(method_owners) >= 2
    checks["readback_receipts_precede_completion"] = bool(complete_events) and all(
        any(value["receipt_id"] == supplied and (log == complete_log and index < complete_index or str(log) < str(complete_log))
            for log, index, value in receipt_events)
        for complete_log, complete_index, command in complete_events
        for supplied in re.findall(r"--receipt[ =]+['\"]?([a-f0-9]+)", command))
    checks["actual_saved_text_returned"] = bool(receipt_events) and all(
        hashlib.sha256(value["saved_owner_text"].encode()).hexdigest() == value.get("receipt", {}).get("file_digest")
        for _, _, value in receipt_events)
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
    if case == "E2E-source":
        checks["formal_bundled_tool_called"] = any("/bundles/candidate/skills/ssot-doctor/assets/scripts/context-source.py" in command or ".agents/skills/ssot-doctor/assets/scripts/context-source.py" in command for command in commands)
    return {"checks": checks, "mechanical_passed": all(checks.values()),
            "entry_observed": bool(snapshot(repo).get("SSOT/README.md", "").strip()),
            "comparison_kind": "candidate formal skill entry end-to-end" if case == "E2E-source" else "protocol comparison under a shared frozen connector",
            "semantic_review": ["Compare saved owner prose to source question/answer, partial correction and uncertainty; accepted history must stay accepted, ordinary testimony/hypothesis must not become candidate protection.",
                                "Check duplicate capture, all declared/affected owner coverage, source scope mismatch and conflict handling; progress/readback linkage does not prove semantic interpretation.",
                                "Check withdrawal/use permissions versus physical deletion; inspect known owners, task state and host outputs as controlled copies, without all-copies or cross-owner ACID claims."]}
