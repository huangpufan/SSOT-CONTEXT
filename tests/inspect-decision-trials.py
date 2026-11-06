#!/usr/bin/env python3
"""Replay successful trial writes to inspect SSOT before implementation.

Read-only: --repo is a surviving trial copy, --log is repeatable for its
native conversation turns. Replays completed edit/write tools, not shell mutations;
inspect the reported shell calls separately. Final source and Markdown must
match readback. Concurrent writes need manual review. These reconstructed
checkpoints are evidence to review, not live snapshots or semantic pass/fail.
"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def inspect(repo, logs, sources):
    repo = repo.resolve()
    paths = subprocess.check_output(
        ["git", "-C", str(repo), "ls-tree", "-r", "--name-only", "HEAD", "--", "SSOT", *sources], text=True
    ).splitlines()
    state = {p: subprocess.check_output(["git", "-C", str(repo), "show", "HEAD:" + p]).decode()
             for p in paths if p.endswith(".md") or p in sources}
    checkpoints, failures, writes, shell_calls, overlaps, first = [], [], [], [], [], None
    session_id = None
    for log in logs:
        events = [json.loads(line) for line in log.read_text().splitlines()]
        endings = [e for e in events if e["type"] == "status" and e.get("phase") == "turn_end"]
        if not endings or endings[-1].get("reason", {}).get("kind") != "completed":
            raise ValueError(f"Incomplete turn: {log}")
        sessions = [e for e in events if e["type"] == "session"]
        if not sessions:
            raise ValueError(f"Missing session identity: {log}")
        for e in sessions:
            if Path(e["cwd"]).resolve() != repo:
                raise ValueError(f"Wrong session repository: {log}")
            if not e.get("sessionId") or (session_id is not None and e["sessionId"] != session_id):
                raise ValueError(f"Missing or mixed native session identity: {log}")
            session_id = e["sessionId"]
        results = {e["callId"]: e for e in events if e["type"] == "tool_result"}
        call_events = {e["callId"]: i for i, e in enumerate(events) if e["type"] == "tool_call"}
        result_events = {e["callId"]: i for i, e in enumerate(events) if e["type"] == "tool_result"}
        calls = [e for e in events if e["type"] == "tool_call"]
        source_calls = []
        for call in calls:
            if call["tool"] in ("edit", "write") and results.get(call["callId"], {}).get("status") == "completed":
                path = Path(call["input"]["file_path"])
                relative = str((path if path.is_absolute() else repo / path).resolve().relative_to(repo))
                if relative in sources:
                    source_calls.append(call_events[call["callId"]])
        first_source_call = min(source_calls, default=len(events))
        ordered = sorted(enumerate(calls, 1), key=lambda item: result_events.get(item[1]["callId"], len(events)))
        for number, call in ordered:
            if call["tool"] == "bash":
                shell_calls.append({"log": log.name, "call": number, "input": call["input"]})
            if call["tool"] not in ("edit", "write"):
                continue
            data = call["input"]
            path = Path(data["file_path"])
            relative = str((path if path.is_absolute() else repo / path).resolve().relative_to(repo))
            if relative not in sources and not (relative.startswith("SSOT/") and relative.endswith(".md")):
                continue
            position = {"log": log.name, "call": number, "path": relative,
                        "call_event": call_events[call["callId"]] + 1,
                        "result_event": result_events.get(call["callId"], -1) + 1}
            result = results.get(call["callId"])
            if not result:
                raise ValueError(f"Missing write result: {position}")
            if result["status"] != "completed":
                failures.append(position)
                continue
            if call["tool"] == "write":
                state[relative] = data["content"]
            else:
                current, old = state[relative], data["old_string"]
                if not old or old not in current:
                    raise ValueError(f"Cannot reconstruct edit: {position}")
                state[relative] = current.replace(old, data["new_string"], -1 if data.get("replace_all") else 1)
            writes.append(position)
            if relative in sources and first is None:
                first = position
            if first is None and relative.startswith("SSOT/"):
                if result_events[call["callId"]] >= first_source_call:
                    overlaps.append(position)
                    continue
                checkpoints.append({
                    **position,
                    "ssot": {p: s for p, s in state.items() if p.startswith("SSOT/")},
                    "source_sha256": {p: hashlib.sha256(state[p].encode()).hexdigest() for p in sources},
                })
    actual = {str(p.relative_to(repo)): p.read_text() for p in (repo / "SSOT").rglob("*.md")}
    actual.update({p: (repo / p).read_text() for p in sources})
    if actual != state:
        raise ValueError("Readback differs from replay; inspect shell writes, commits, or later changes")
    return {
        "base_head": subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip(),
        "session_id": session_id, "completed_logs": len(logs),
        "successful_writes": writes, "failed_writes": failures,
        "shell_calls_for_review": shell_calls,
        "overlapping_writes_for_review": overlaps,
        "first_implementation_edit": first, "pre_implementation_checkpoints": checkpoints,
        "final_ssot": {p: s for p, s in state.items() if p.startswith("SSOT/")},
        "readback_matches": True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--log", required=True, action="append", type=Path)
    parser.add_argument("--source", action="append", help="Implementation path; default engine.py and test_engine.py")
    args = parser.parse_args()
    print(json.dumps(inspect(args.repo, args.log, args.source or ["engine.py", "test_engine.py"]), indent=2))


if __name__ == "__main__":
    main()
