"""Synthetic multi-session continuation: host fixture, prompts and conservative oracle."""
import json
import re

import source_cases

PROMPTS = [
    "请将 sources/initial.json 的访谈整理到这个已授权空间的既有研究和创作笔记中，保留已接受的方法及来源原文，不要将未验证的猜测写成结论。请维护必要入口。",
    "新增 sources/followup.json。请把其中有限更正反映到相关既有笔记，其他已接受约定继续有效，原始来源保留原样。",
    "请把 scratch/message.txt 中的拼写错误 teh 改成 the。",
    "请为下一次访谈准备一份简短执行清单，写入 deliverables/interview-checklist.md。根据这个空间已经接受的研究和创作约定，以及仍未验证的内容，给出具体做法。",
]
OWNERS = ("research/findings.md", "creation/notes.md", "memory/experiences.md", "SSOT/README.md")


def structure(files):
    """Observed context paths, headings and Markdown destinations, not prose truth."""
    return {name: (re.findall(r"^#{1,6} .*", text, re.M), re.findall(r"\]\(([^)]+)\)", text))
            for name, text in files.items() if name in OWNERS or name.startswith("SSOT/")}


def build(repo, write):
    source_cases.build(repo, write, native_entry=True)
    write(repo, "SSOT/README.md", "---\nssot_format: 5\nlanguage: en\n---\n# Interview space\n\n[Research](../research/findings.md) and [creative notes](../creation/notes.md) own their respective material. [Source scope](../connector-setup.txt).\n")
    write(repo, "scratch/message.txt", "Please review teh draft.\n")


def before_turn(repo, turn, write):
    if turn == 2:
        write(repo, "sources/followup.json", source_cases.export([source_cases.CORRECTION]))


def grade(repo, phases):
    def snap(n, side):
        path = phases / f"phase-{n}" / f"1.{side}.json"
        return json.loads(path.read_text()) if path.exists() else {}
    snapshots = [(snap(n, "before"), snap(n, "after")) for n in range(1, 5)]
    checked_phases = []
    for n, (before, after) in enumerate(snapshots, 1):
        log = phases / f"phase-{n}/1.jsonl"
        events = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
        path = phases / f"phase-{n}/1.checkpoints.json"
        checkpoints = json.loads(path.read_text()) if path.exists() else []
        previous, last_change = structure(before), 0
        for checkpoint in checkpoints:
            current = structure(checkpoint["files"])
            if current != previous:
                last_change = checkpoint["event"]
            previous = current
        if previous != structure(after):
            last_change = len(events) + 1  # Final change was not observed before a check.
        if not last_change:
            continue
        passed = any(index >= last_change and event.get("type") == "item.completed"
                     and item.get("type") == "command_execution" and item.get("exit_code") == 0
                     and "ssot-check.py" in item.get("command", "") and "--since" not in item.get("command", "")
                     and "ssot-check: PASS" in item.get("aggregated_output", "")
                     for index, event in enumerate(events, 1) for item in [event.get("item", {})])
        checked_phases.append(passed)
    checks = {
        "all_four_snapshots_present": all(a and b for a, b in snapshots),
        "observed_context_structure_checked_after_changes": all(checked_phases),
        "source_originals_preserved_each_turn": all(all(b.get(k) == v for k, v in a.items() if k.startswith("sources/")) for a, b in snapshots),
        "installed_instructions_preserved_each_turn": all(all(a.get(k) == b.get(k) for k in set(a) | set(b) if k == "AGENTS.md" or k.startswith(".agents/")) for a, b in snapshots),
        "existing_owners_retained": all((repo / name).is_file() for name in OWNERS),
        "unrelated_edit_did_not_change_context": bool(snapshots[2][0]) and all(snapshots[2][0].get(k) == snapshots[2][1].get(k) for k in set(snapshots[2][0]) | set(snapshots[2][1]) if k != "scratch/message.txt"),
        "typo_fixed": (repo / "scratch/message.txt").is_file() and (repo / "scratch/message.txt").read_text() == "Please review the draft.\n",
        "final_deliverable_exists": (repo / "deliverables/interview-checklist.md").is_file() and bool((repo / "deliverables/interview-checklist.md").read_text().strip()),
    }
    return {"checks": checks, "mechanical_passed": all(checks.values()),
            "comparison_kind": "synthetic four-session continuation, not observed longitudinal use",
            "semantic_review": [
                "Compare both owner files and the final checklist with both original source exports: research retains supporting and opposing evidence; creative use is limited to non-identifying atmosphere, without interviewee identity; testimony is not automatically canon.",
                "Confirm the original accepted standing and unchanged decision portions survive the partial correction, without invented acceptance or duplicate records; the light/sleep hypothesis remains unverified.",
                "Inspect each phase's actual owner changes and final checklist: the final cold session retrieved and applied maintained context, and no unrelated durable record was added for the typo.",
                "Check command order and scope when writes and checks share one shell event. Event snapshots cannot exclude writes undone within one tool call; structural matching covers context paths, headings and Markdown links, not every possible format or semantic change.",
            ]}
