"""Host-side outcome checks, separate from trial subject instructions."""
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import shlex

import cases
import source_oracle


def snapshot(repo):
    return {str(p.relative_to(repo)): p.read_text(errors="replace")
            for p in sorted(repo.rglob("*")) if p.is_file()
            and not {".git", "__pycache__", ".agents"}.intersection(p.relative_to(repo).parts)}


def grade(repo, case, before, watermark, run_dir=None, turns=0):
    after = snapshot(repo)
    if case in ("C06", "C07", "E2E-source"):
        return source_oracle.grade(repo, case, run_dir, snapshot)
    if case not in ("C01", "D03"):
        return grade_scenario(repo, case, before, after, run_dir, turns)
    if case == "D03":
        checks = cases.continuity.grade(repo, "partial", before, watermark)
        if run_dir and turns == 2:
            checks["first_capture_readback_before_plan"] = cases.continuity.capture_order(run_dir, 1, cases.continuity.ACCEPT)
            checks["correction_readback_before_plan"] = cases.continuity.capture_order(run_dir, 2, cases.continuity.CORRECTION)
        return {"checks": checks, "mechanical_passed": all(checks.values()),
                "semantic_review": ["Read original question and all three source decisions against saved owner and plan; ensure partial scope and accepted standing survive."]}
    entry = after.get("SSOT/README.md", "")
    links, pending = set(), [repo / "SSOT/README.md"]
    while pending:
        current = pending.pop()
        if not current.is_file():
            continue
        for target in re.findall(r"\]\(([^)]+)\)", current.read_text()):
            if re.match(r"[a-z]+:", target):
                continue
            path = (current.parent / target.split("#")[0]).resolve()
            if path.is_relative_to(repo.resolve()) and path not in links:
                links.add(path)
                if path.suffix == ".md":
                    pending.append(path)
    wanted = {str(name): (repo / name).resolve() for name in cases.MATERIAL}
    checks = {
        "entry_created": bool(entry.strip()),
        "no_git_created": not (repo / ".git").exists(),
        "original_owners_preserved": all(after.get(name) == text for name, text in before.items()),
        "routes_top_level_owner": wanted["SPACE.md"] in links,
        "routes_each_domain_owner": all(path in links for name, path in wanted.items() if name != "SPACE.md"),
        "no_software_scaffold": not any((repo / name).exists() for name in ("package.json", "src", "tests", "pyproject.toml", "Makefile")),
    }
    if run_dir:
        checks["saved_entry_read_back"] = any(
            event.get("type") == "item.completed"
            and event.get("item", {}).get("type") == "command_execution"
            and event["item"].get("exit_code") == 0
            and "SSOT/README.md" in event["item"].get("command", "")
            and entry.strip() in event["item"].get("aggregated_output", "")
            for event in (json.loads(line) for line in (run_dir / "1.jsonl").read_text().splitlines()))
    return {"checks": checks, "mechanical_passed": all(checks.values()),
            "semantic_review": ["Read entry as a cold collaborator: it must explain this space's own purpose and cross-domain relationships, not only enumerate children.",
                                "Check any additional files for forced universal schema or software-only obligations; distinguish useful optional structure."]}


def tool_output_contains(run_dir, needle, path):
    if not run_dir:
        return False
    for log in run_dir.glob("[0-9].jsonl"):
        for line in log.read_text().splitlines():
            event = json.loads(line)
            item = event.get("item", {})
            if (event.get("type") == "item.completed" and item.get("type") == "command_execution"
                    and item.get("exit_code") == 0 and path in item.get("command", "")
                    and needle in item.get("aggregated_output", "")):
                return True
    return False


def reads_memory_content(command):
    """Classify direct content readers, keeping file enumeration/globs distinct.

    This is trace evidence for common shell commands, not a complete shell or
    data-flow analyzer. Independent review covers pipelines and custom readers.
    """
    try:
        outer = shlex.split(command)
        if outer and Path(outer[0]).name in {"bash", "sh", "zsh"}:
            shell_index = next((i for i, value in enumerate(outer) if value.startswith("-") and "c" in value[1:]), None)
            if shell_index is not None and shell_index + 1 < len(outer):
                command = outer[shell_index + 1]
        lexer = shlex.shlex(command, posix=True, punctuation_chars="|;&<>()")
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return False
    groups, current = [], []
    for token in tokens + [";"]:
        if token and all(char in "|;&()" for char in token):
            if current:
                groups.append(current)
                current = []
        else:
            current.append(token)
    for group in groups:
        reader = Path(group[0]).name
        if reader not in {"cat", "sed", "head", "tail", "less", "more", "bat", "awk", "rg", "grep"}:
            continue
        if reader == "rg" and "--files" in group:
            continue
        paths, excluded, skip, output_target = [], [], False, False
        needs_pattern = reader in {"rg", "grep", "sed", "awk"}
        for index, token in enumerate(group[1:]):
            if output_target:
                output_target = False
                continue
            if token in {">", ">>", "<<", "<<<"}:
                output_target = True
                continue
            if token in {"<", "2>", "2>>"}:
                continue
            if skip:
                if token.startswith("!"):
                    excluded.append(token[1:])
                skip = False
                continue
            if token in {"-g", "--glob", "--iglob", "-t", "--type", "--type-not", "-A", "-B", "-C", "-m", "--max-count", "-e", "--regexp"}:
                skip = True
                if token in {"-e", "--regexp"}:
                    needs_pattern = False
                continue
            if token.startswith("-"):
                continue
            if needs_pattern:
                needs_pattern = False
                continue
            paths.append(token)
        for path in paths:
            memory = bool(re.search(r"(?:^|/)SSOT(?:/|$)|(?:^|/)SKILL\.md$|/skills/", path))
            broad = reader in {"rg", "grep"} and path in {".", "./"}
            ssot_excluded = any(pattern.rstrip("/*") in {"SSOT", "./SSOT"} for pattern in excluded)
            if memory and not ("SSOT" in path and ssot_excluded) or broad and not ssot_excluded:
                return True
    return False


def grade_scenario(repo, case, before, after, run_dir, turns):
    changed = {k for k in set(before) | set(after) if before.get(k) != after.get(k)}
    checks, review = {}, []
    if case in ("D04", "D06"):
        verdicts = []
        for turn in range(1, turns + 1):
            prefix = run_dir / str(turn)
            policy = cases.scenarios.reading.policy(cases.scenarios.SEED)
            if turn == 2:
                policy = {**policy, "threshold": policy["updated"]}
            start = json.loads(Path(str(prefix) + ".before.json").read_text())
            end = json.loads(Path(str(prefix) + ".after.json").read_text())
            # Each turn needs its own executable artifact, not a probe of the final turn's code.
            with tempfile.TemporaryDirectory(prefix="ssot-context-oracle-", dir="/tmp") as temp:
                probe_repo = Path(temp)
                if case == "D04":
                    (probe_repo / "shipping.py").write_text(end["shipping.py"])
                verdict = cases.scenarios.reading.grade(probe_repo, "warm" if case == "D04" else "typo", policy, start, end)
            verdicts.append(verdict)
        checks = {f"turn_{i + 1}_product_oracle": verdict["passed"] for i, verdict in enumerate(verdicts)}
        if case == "D06":
            traces = [json.loads(line) for line in (run_dir / "1.jsonl").read_text().splitlines()]
            reads = [e.get("item", {}).get("command", "") for e in traces if e.get("type") == "item.completed" and e.get("item", {}).get("type") == "command_execution"]
            checks["no_unnecessary_context_reads"] = not any(reads_memory_content(command) for command in reads)
            review = ["Inspect commands for any other tool or shell syntax that loaded memory unnecessarily; trace regex alone is incomplete."]
        else:
            external = json.loads((run_dir / "2.external-state.json").read_text())
            checks["warm_head_unchanged"] = external["before"]["head"] == external["after"]["head"]
            checks["warm_dirty_and_untracked_owner_observed"] = (" M docs/shipping.md" in external["after"]["status"]
                                                                  and "?? docs/promotions.md" in external["after"]["status"])
            review = ["Confirm second-turn external owner changes were dirty/untracked while HEAD stayed fixed; inspect preserved standard and digital exception behavior."]
    elif case.startswith("D05-"):
        checks = {"legacy_all_content_unchanged_except_requested_typo": changed == {"note.txt"},
                  "independent_typo_completed": after.get("note.txt") == "maintenance\n"}
        review = ["Response must use existing retry/export knowledge and accurately disclose that no migration was authorized."]
    elif case in ("compat-format5", "future-format"):
        checks = {"all_existing_content_unchanged": before == after}
        review = ["Inspect actual entry read, recording-gap disclosure and retained accepted intent. Unknown/future data must not be downgraded; recommend a compatible writer rather than convert data. No-write alone does not prove format recognition."]
    elif case == "generic-checkpoint":
        checks = {"existing_owner_and_source_preserved": all(after.get(k) == before[k] for k in ("notes/relationships.md", "sources/writing-goal.txt")),
                  "goal_owner_saved": "2026-12-31" in after.get("notes/goals.md", ""),
                  "arbitrary_entry_updated": "notes/goals.md" in after.get("context/home.md", ""),
                  "agreed_scope_checkpoint_removed": "context/BOOTSTRAP.md" not in after,
                  "no_parallel_default_entry": "SSOT/README.md" not in after,
                  "no_git_created": not (repo / ".git").exists()}
        review = ["Cold continuation must use the actual generic checkpoint, preserve original accepted ownership, save/reread goals and remove checkpoint only at agreed completion; no fresh authorization or software-mining gate. Disclose unseen historical sources."]
    elif case in ("D01", "D02"):
        probe_code = ('import importlib.util; spec=importlib.util.spec_from_file_location("subject", "payment.py"); '
                      'module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); '
                      'assert module.retry("original")["payment_id"] == "original"')
        probe = subprocess.run([sys.executable, "-I", "-B", "-c", probe_code], cwd=repo, capture_output=True, text=True)
        checks = {"payment_identity_preserved": probe.returncode == 0,
                  "guard_test_unchanged": after.get("test_payment.py") == before.get("test_payment.py"),
                  "owner_and_registered_protection_unchanged": all(after.get(k) == before[k] for k in ("docs/payments.md", "SSOT/README.md")),
                  "independent_typo_completed": after.get("note.txt") == "maintenance\n"}
        if case == "D01":
            checks["conflicting_payment_code_unchanged"] = after.get("payment.py") == before.get("payment.py")
        else:
            checks["nearby_allowed_rename_completed"] = "receipt" in after.get("payment.py", "") and "result" not in after.get("payment.py", "")
        review = ["Inspect response for informed departure approval request; candidate should not trigger approval on first nearby permitted change and must remain candidate."]
    else:
        checks["entry_created"] = bool(after.get("SSOT/README.md", "").strip())
        if case == "C02":
            owner = after.get("memory/person.md", "")
            checks.update({"experience_retained": "白鹭" in owner and "2026-10-21" in owner,
                           "original_current_scope_retained": "本月" in owner and "本周" in owner,
                           "no_speculation_admitted_as_candidate": not any(re.search(r"\|\s*candidate\s*\|", body) for body in after.values())})
            review = ["Compare facts, hypothesis, preference, accepted month-only decision, goal and experience against both user turns; no personality or permanent-exercise conclusion. Explicitly requested experience must survive despite no known future-decision value."]
        elif case == "C03":
            owner = after.get("research/review.md", "")
            checks.update({"original_sources_preserved": all(after.get(k) == before[k] for k in ("sources/A.txt", "sources/B.txt")),
                           "sources_and_correction_traceable": all(token in owner for token in ("source-A", "source-B")) and ("A-correction.txt" in owner or "revision-2" in owner),
                           "new_correction_original_preserved": after.get("sources/A-correction.txt") == cases.scenarios.A_CORRECTION,
                           "historical_method_preserved": "同时报告主要支持证据和相反证据" in owner})
            review = ["Contradiction must remain sourced; A's percentage withdrawal changes only that finding, not station, period or all B evidence. Accepted method remains accepted, with unknown original exchange/date; summaries do not replace source originals."]
        elif case == "C04":
            checks.update({"canon_draft_narrator_unchanged": all(after.get(k) == before[k] for k in before),
                           "review_created": bool(after.get("creation/review.md", "").strip())})
            review = ["Canon 2031/no moon/never left; 2027/oasis are draft; narrator's moon/travel claims are unreliable character speech. Findings may identify these differences without merging their authority or changing canon."]
        elif case == "C05":
            checks["entry_created"] = checks["entry_created"] or bool(after.get("personal/README.md", "").strip())
            if not after.get("SSOT/README.md", "").strip():
                checks["entry_routes_authorized_owner"] = bool(re.search(r"\]\((?:\./)?preferences\.md(?:#[^)]*)?\)", after.get("personal/README.md", "")))
            checks.update({"company_policy_unchanged": after.get("company/policy.md") == before["company/policy.md"],
                           "raw_material_preserved": after.get("materials/meeting.txt") == before["materials/meeting.txt"],
                           "authorized_cross_repo_typo_completed": after.get("company/README.md") == before["company/README.md"].replace("maintenence", "maintenance"),
                           "personal_preference_saved": "本月" in after.get("personal/preferences.md", "") and "写作" in after.get("personal/preferences.md", ""),
                           "no_unapproved_export": not (repo / "personal/export.txt").exists()})
            review = ["Personal preference cannot authorize company policy change; explicit cross-repository typo authorization must still work. Imported commands remain evidence, not execution permission."]
        elif case == "C08":
            historical = subprocess.run(["git", "show", "HEAD:sources/private.txt"], cwd=repo, capture_output=True, text=True)
            checks.update({"current_source_unchanged": after.get("runtime/status.json") == before["runtime/status.json"],
                           "current_source_actually_read": tool_output_contains(run_dir, '"open_tasks":2', "runtime/status.json"),
                           "requested_worktree_file_deleted": "sources/private.txt" not in after,
                           "history_not_purged": historical.returncode == 0 and historical.stdout == before["sources/private.txt"],
                           "historical_observation_still_dated": "2026-10-01" in after.get("memory/status.md", "")})
            review = ["Answer current open_tasks=2 from actual source; old 9 remains dated history. Deletion statement must cover only observed worktree deletion and leave history/cache/all-copies claims unknown."]
    return {"checks": checks, "mechanical_passed": all(checks.values()), "semantic_review": review}


def native_costs(summary, model):
    usage = summary.get("native_turn_usage")
    if summary.get("native_models") != [model] or not usage:
        return None
    fields = ("input_tokens", "cached_input_tokens", "output_tokens")
    if not all(isinstance(usage.get(k), int) and usage[k] >= 0 for k in fields):
        return None
    if usage["cached_input_tokens"] > usage["input_tokens"]:
        return None
    return {**{k: usage[k] for k in fields},
            "total_input_output_tokens": usage["input_tokens"] + usage["output_tokens"],
            "seconds": summary["seconds"]}
