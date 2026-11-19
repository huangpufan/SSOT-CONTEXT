"""Reconcile native setup usage across the coordinator and its isolated helper sessions."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "context"))
from oracle import native_usage_boundary


FIELDS = ("input_tokens", "cached_input_tokens", "output_tokens")


def summarize(directory):
    summary = json.loads((directory / "1.summary.json").read_text())
    sessions = []
    responses = set()
    requested_helpers = Counter()
    observed_helpers = Counter()
    totals = Counter()
    issues = []
    root_seen = False
    for path in sorted((directory / "codex-home/sessions").rglob("*.jsonl")):
        raw = path.read_bytes()
        records = [json.loads(line) for line in raw.splitlines()]
        meta = next(r["payload"] for r in records if r["type"] == "session_meta")
        role = "coordinator"
        if isinstance(meta["source"], dict):
            role = meta["source"]["subagent"]["thread_spawn"]["agent_path"]
            observed_helpers[role] += 1
        else:
            root_seen |= meta["id"] == summary["thread_id"]
        calls = {r["payload"]["call_id"] for r in records if r["type"] == "response_item"
                 and r["payload"].get("name") == "spawn_agent"}
        for r in records:
            p = r["payload"]
            if p.get("type") == "function_call_output" and p.get("call_id") in calls:
                try:
                    reply = json.loads(p["output"])
                except (TypeError, ValueError):
                    continue  # A failed tool call may return plain text.
                if isinstance(reply, dict) and reply.get("task_name"):
                    requested_helpers[reply["task_name"]] += 1
        contexts = [r["payload"] for r in records if r["type"] == "turn_context"]
        turns = {p.get("root_turn_id") or p.get("turn_id") for p in contexts}
        usage = [r["payload"] for r in records if r["type"] == "token_usage_record"]
        models = {p.get("model") for p in contexts}
        efforts = {p.get("effort") for p in contexts}
        if models != {"gpt-6.1-terra"} or None in efforts or (role == "coordinator" and efforts != {"medium"}):
            issues.append(f"{role}: model or reasoning mismatch")
        for turn in turns:
            boundary, _ = native_usage_boundary({"native_turn_id": turn}, path)
            if boundary["status"] != "complete":
                issues.append(f"{role}: {boundary['reason']}")
        local = Counter()
        for receipt in usage:
            response = receipt.get("response_id")
            if not response or response in responses:
                issues.append(f"{role}: missing or repeated response ID")
                continue
            responses.add(response)
            local.update({k: receipt["usage"][k] for k in FIELDS})
        if not usage or any(local[k] != usage[-1]["thread_token_usage"][k] for k in FIELDS):
            issues.append(f"{role}: response sum differs from final thread usage or usage is missing")
        totals.update(local)
        sessions.append({"role": role, "models": sorted(models, key=str), "efforts": sorted(efforts, key=str),
                         "responses": len(usage), "turns": len(turns), **local,
                         "sha256": hashlib.sha256(raw).hexdigest()})
    if not root_seen or requested_helpers != observed_helpers:
        issues.append("Coordinator or acknowledged helper inventory does not match session receipts")
    return {"sessions": sessions, "sessions_count": len(sessions), "responses": len(responses),
            "observed_tokens": totals["input_tokens"] + totals["output_tokens"], **totals,
            "seconds": summary["seconds"], "native_completed": summary["native_completed"],
            "returncode": summary["returncode"], "observation_issues": issues}


if __name__ == "__main__":
    print(json.dumps(summarize(Path(sys.argv[1])), indent=2))
