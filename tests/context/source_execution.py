"""Observed connector receipts and owned-process interruption, without oracle answers."""
import json
from pathlib import Path
import subprocess
import sys


def object_entries(text):
    decoder, offset = json.JSONDecoder(), 0
    while offset < len(text):
        starts = [position for position in (text.find("{", offset), text.find("[", offset)) if position >= 0]
        if not starts:
            return
        offset = min(starts)
        start = offset
        try:
            value, offset = decoder.raw_decode(text, offset)
        except ValueError:
            offset += 1
            continue
        yield start, value


def objects(text):
    for _, value in object_entries(text):
        yield value


def receipt_entries(event):
    """Returned candidates, not proof of invocation or successful persistence.

    A wrapper need not name readback, and a later failed shell command must not
    erase an earlier returned receipt. Consumers verify public progress/digests.
    """
    item = event.get("item", {})
    if event.get("type") != "item.completed" or item.get("type") != "command_execution":
        return []
    return [(offset, value) for offset, value in object_entries(item.get("aggregated_output", ""))
            if isinstance(value, dict) and isinstance(value.get("receipt_id"), str)
            and isinstance(value.get("saved_owner_text"), str)]


def receipt_results(event):
    return [value for _, value in receipt_entries(event)]


def cold_chain(root, directory, repo, bundle, plan, tasks, transport, sandbox_for, prompt_for, save):
    receipts = {}

    def interrupt(files, event):
        for value in receipt_results(event):
            receipt = value.get("receipt", {})
            if receipt.get("owner"):
                receipts[receipt["owner"]] = value
        return len(receipts) >= 2

    first = directory / "phase-1"
    first.mkdir()
    home = first / "codex-home"
    summary = transport.execute_turn(root, first, repo, prompt_for(tasks[0]), 1, plan["cap"],
        sandbox_command=sandbox_for(home), codex_home=home, capture_checkpoints=True,
        interrupt_when=interrupt, model=plan["model"], allow_no_git=True)
    summary["evidence_directory"] = "phase-1"
    save(directory / "interruption-receipts.json", list(receipts.values()))
    summaries = [summary]
    identity = transport.native_identity_state(summary, plan["model"])
    if not summary.get("observation_complete") or identity:
        save(directory / "interruption-invalid.json", {
            "reason": "Observation or native identity is unverified; dependent recovery stopped",
            "observation_complete": summary.get("observation_complete"), "native_identity_state": identity})
        return summaries
    if not summary.get("intentional_interruption") or len(receipts) < 2:
        save(directory / "interruption-invalid.json", {"reason": "No observed two-owner readback interruption before completion"})
        return summaries
    script = repo / ".tools/context-source.py"
    state = repo / "run/source-state.json"
    result = subprocess.run([sys.executable, str(script), "status", "--state", str(state)], capture_output=True, text=True)
    save(directory / "interrupted-status.json", {"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
    try:
        method = next(item for item in json.loads(result.stdout)["items"] if item["item_id"] == "method" and item["revision"] == "r1")
    except (ValueError, KeyError, StopIteration):
        method = {}
    if method.get("status") != "readback-ready" or not {value["receipt_id"] for value in receipts.values()} <= set(method.get("receipts", [])):
        save(directory / "interruption-invalid.json", {"reason": "Actual source progress was not readback-ready at interruption", "observed": method})
        return summaries
    first_receipt = next(iter(receipts.values()))["receipt"]
    owner = Path(first_receipt["path"])
    if not owner.resolve().is_relative_to(repo.resolve()):
        raise ValueError("Receipt owner escaped controlled trial workspace")
    with owner.open("a") as handle:
        handle.write("\n外部维护注：本段于中断期间追加，不改变任何既有用户决定。\n")
    command = [sys.executable, str(script), "complete", "--state", str(state), "--item", "method", "--revision", "r1"]
    for value in receipts.values():
        command += ["--receipt", value["receipt_id"]]
    result = subprocess.run(command, capture_output=True, text=True)
    save(directory / "stale-complete.json", {"command": command, "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
    second = directory / "phase-2"
    second.mkdir()
    home = second / "codex-home"
    summary = transport.execute_turn(root, second, repo, prompt_for(tasks[1]), 1, plan["cap"],
        sandbox_command=sandbox_for(home), codex_home=home, capture_checkpoints=True,
        model=plan["model"], allow_no_git=True)
    summary["evidence_directory"] = "phase-2"
    summaries.append(summary)
    return summaries
