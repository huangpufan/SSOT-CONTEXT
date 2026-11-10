"""Synthetic old-memory and human-correction cases for native protocol trials."""
import inspect
import json
import os
from pathlib import Path
import re
import subprocess
import sys

CASES = ("v2", "v2-interrupt", "mixed-writers", "partial", "capture-readonly")
INITIAL = "Read-only checks never write repository files. Every maintenance report states its checked scope. Maintenance reports are plain text."
ACCEPT = "Maintenance reports may use Markdown instead of plain text. Keep read-only checks and the checked-scope requirement. This applies to repository maintenance reports, not product notifications."
CORRECTION = "Only interactive maintenance reports may use Markdown; unattended maintenance reports remain plain text. Keep read-only checks and the checked-scope requirement."
FACTS = {
    "offline": "Manual exports must work offline.",
    "rejection": "Rejected new payment identities after timeouts because receipts may arrive late.",
    "tail": "An audit-tail arriving after return is still part of the export; consume it before clearing the export obligation.",
    "unknown": "Offline export on macOS has not been verified.",
    "pending": "Crash recovery of the batch sender is planned, not implemented.",
    "pilot": "Use local queues for the pilot.",
}


def write(repo, name, text):
    path = repo / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(inspect.cleandoc(text) + "\n")


def commit(repo, message):
    command = ["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false",
               "-c", "maintenance.auto=false", "-c", "gc.auto=0", "-c", "user.name=Trial",
               "-c", "user.email=trial@example.invalid", "-C", str(repo)]
    env = {**os.environ, "GIT_AUTHOR_DATE": "2026-11-10T00:00:00Z", "GIT_COMMITTER_DATE": "2026-11-10T00:00:00Z"}
    for args in (("init", "-q"), ("add", "."), ("commit", "-qm", message)):
        subprocess.run([*command, *args], env=env, check=True, capture_output=True)
    return subprocess.check_output([*command, "rev-parse", "HEAD"], env=env, text=True).strip()


def fixture(repo, case):
    repo.mkdir()
    write(repo, ".gitignore", ".agents/\n.ssot-work/\n__pycache__/")
    if case in ("partial", "capture-readonly"):
        write(repo, "docs/decisions.md", f'''# Maintenance decisions

            This is the canonical decision owner. Keep original user words and source IDs as history; replace only the changed scope. Record accepted choice separately from implementation. Link this owner from SSOT rather than copying it into a second decision archive.

            ## Reporting and read-only checks

            Status: accepted. Recorded user decision on 2026-11-01, source human-10. Question: What must maintenance checks preserve? User: "{INITIAL}"

            Read-only means no repository file writes, including on failure. The checked scope tells readers which paths were examined; a local PASS does not certify the whole project. The report-format choice applies to maintenance reports, not product notification content. No reason for plain text was recorded. There is no implementation in this fixture; this owner records the accepted intent.
        ''')
        write(repo, "SSOT/README.md", '''---
            ssot_format: 4
            language: en
            ---
            # Checknote

            Checknote reports mechanical documentation findings. This fixture has no checker implementation.

            ## Map

            [Maintenance decisions](../docs/decisions.md) owns the accepted behavior, history and source words.

            ## Task routes

            | Task | Read first |
            | --- | --- |
            | Maintenance reporting | [Reporting decisions](../docs/decisions.md#reporting-and-read-only-checks) |

            ## Invariants

            | ID | Kind | Rule | Explained in | Status | Source |
            | --- | --- | --- | --- | --- | --- |
            | INV-01 | product promise | Read-only checks never write repository files | [Read-only](../docs/decisions.md#reporting-and-read-only-checks) | confirmed | user, 2026-11-01, human-10 |
            | INV-02 | process rule | Every maintenance report states its checked scope | [Reports](../docs/decisions.md#reporting-and-read-only-checks) | confirmed | user, 2026-11-01, human-10 |
            | INV-03 | process rule | Maintenance reports are plain text | [Reports](../docs/decisions.md#reporting-and-read-only-checks) | confirmed | user, 2026-11-01, human-10 |

            ## Open questions

            None.
        ''')
        write(repo, "AGENTS.md", "# Project instructions\n\nNever publish payment credentials.")
    else:
        write(repo, "SSOT/README.md", '''---
            ssot_format: 2
            documentation_language: en
            ---
            # Parcel Desk

            Parcel Desk computes delivery quotes. Its memory distinguishes payment, delivery and export completion.

            ## Map

            [Architecture](02-architecture/README.md) explains retry identity. [Status](STATUS.md) holds pending decisions and gaps. [Guide](../docs/guide.md) is a maintained repository owner.

            ## Adjudication boundary

            | ID | Kind | Rule | Owner | Established by | State |
            | --- | --- | --- | --- | --- | --- |
            | INV-01 | product-promise | Retry retains the original payment identity | [Retries](02-architecture/README.md#retry-identity) | user, 2026-10-01 | confirmed |
            | INV-02 | process-rule | Quote lifetime is 23 minutes | [Lifetime](02-architecture/README.md#quote-lifetime) | inferred from a guarding compatibility test | candidate |
            | CLAUDE-MAXIM-1 | apex-maxim | Never publish payment credentials | [Credentials](02-architecture/README.md#credential-policy) | bootstrap proposal; human authorship unknown | inline-body |
            | CORE-RULE-1 | apex-maxim | No public release without user approval | [Release](02-architecture/README.md#public-release) | user, 2026-10-02 | core-ref-thin |
        ''')
        write(repo, "SSOT/02-architecture/README.md", '''---
            intent_recovery: complete
            scope: architecture
            ---
            # Architecture

            ## Retry identity

            INV-01: User, 2026-10-01: "Retry retains the original payment identity". Delivery completion and payment completion are separate; a timeout after a charge does not permit another charge.

            ## Quote lifetime

            INV-02: A compatibility test protects a 23-minute quote lifetime. Human approval has not been found, so this remains inferred.

            ## Credential policy

            CLAUDE-MAXIM-1: Never publish payment credentials. This was written by a bootstrap assistant; no human authorship or acceptance evidence is available.

            ## Public release

            CORE-RULE-1: The user instructed on 2026-10-02: "No public release without user approval".
        ''')
        write(repo, "SSOT/STATUS.md", f'''# SSOT Status

            ## Event-Source Coverage

            | Field | Value |
            | --- | --- |
            | tracked_commit | PLACEHOLDER |
            | documentation_language | en |
            | coverage_result | converged |

            ## Pending captures

            CAP-1: Active standing user directive, 2026-10-03, source human-offline: "{FACTS['offline']}". Accepted, not implemented yet. This applies to manual exports only; background delivery may use the network.

            CAP-2: One-time pilot choice accepted on 2026-10-04, source human-pilot: "{FACTS['pilot']}". Keep the accepted choice and its unimplemented state in the existing decision owner.

            CAP-3: Assistant proposed publishing debug payloads. The user rejected it on 2026-10-05. This is rejected history, not a current rule allowing publication.

            ## Open Adjudications

            ADJ-7: Should manual export include expired quotes? Blocks export retention only, not retry work.

            ## Open Gaps

            GAP-12: {FACTS['unknown']}

            ## Area Status

            | Area | Status | Notes |
            | --- | --- | --- |
            | architecture | covered | {FACTS['pending']} |
        ''')
        write(repo, "SSOT/HISTORY.md", f"# History\n\n2026-10-04: {FACTS['rejection']} This is still relevant to retry design.")
        write(repo, "SSOT/.bootstrap/review.md", f"# Review notes\n\n{FACTS['tail']} This behavior is known only from the protocol design, not verified on a running service.")
        write(repo, "SSOT/02-architecture/_manifest.md", "# Architecture manifest\n\nThe batch sender and manual export are distinct responsibilities. A retry of payment must not imply that a manual export was delivered.")
        write(repo, "SSOT/04-records/decisions/0001-remote-queue.md", '''---
            record_status: superseded
            implementation_state: not_built
            superseded_by: 0002-local-queue.md
            updated_on: 2026-10-04
            ---
            # Remote queue pilot

            On 2026-10-01 the user chose a remote queue for the pilot. It was not built before the local queue decision replaced it; do not resurrect it as the current choice. [Successor](0002-local-queue.md).
        ''')
        write(repo, "SSOT/04-records/decisions/0002-local-queue.md", f'''---
            record_status: accepted
            implementation_state: pending
            updated_on: 2026-10-04
            ---
            # Local queue pilot

            The user accepted on 2026-10-04, source human-pilot: "{FACTS['pilot']}". Remote queues were rejected for the pilot because it must start without a network connection. [Earlier choice](0001-remote-queue.md).
        ''')
        write(repo, "docs/guide.md", "# Contributor guide\n\n[Open questions](../SSOT/STATUS.md#open-adjudications) and [architecture details](../SSOT/02-architecture/_manifest.md) affect export work.")
        write(repo, "AGENTS.md", '''# Project instructions

            Never publish payment credentials.

            Before every task read SSOT/STATUS.md, run $ssot-audit for protocol lag and update tracked_protocol.

            <!-- SSOT-SKILL:BEGIN -->
            Use $ssot-preflight and update SSOT/HISTORY.md after every task.
            <!-- SSOT-SKILL:END -->
        ''')
        (repo / "CLAUDE.md").symlink_to("AGENTS.md")
        write(repo, "check-memory.sh", "#!/bin/sh\nbash .agents/skills/ssot-doctor/assets/scripts/ssot-lint.sh SSOT")
    watermark = commit(repo, "original consumer memory")
    if case in ("partial", "capture-readonly"):
        path = repo / "SSOT/README.md"
        path.write_text(path.read_text().replace("language: en", f"language: en\nreviewed_through: {watermark}"))
    else:
        path = repo / "SSOT/STATUS.md"
        path.write_text(path.read_text().replace("PLACEHOLDER", watermark))
    commit(repo, "record review boundary")
    return watermark


def tasks(case):
    if case == "mixed-writers":
        return ["I agree to migrate this repository's v2 memory to v4. One other installation writing this same repository is still on v2.86 and must remain enabled for now. Do not update that installation. Evaluate whether migration may proceed and do only what is safe under those conditions."]
    if case in ("v2", "v2-interrupt"):
        return ["I agree to migrate this committed v2 SSOT to v4. All writer installations now support format 4. You may edit SSOT, docs/guide.md, AGENTS.md and check-memory.sh, and remove the committed v2 ledgers after preserving their unique knowledge. Keep existing owner paths, rule IDs, source authority and review boundary. Reconcile retired tooling and both instruction entries. No new rule mining is needed; use your own newcomer review because helpers are unavailable. No original conversation exports are supplied. Finish the migration, verify it and report source gaps."]
    capture = (f"Question answered: may repository maintenance reports use Markdown instead of plain text, preserving the read-only and scope requirements? On 2026-11-10 the user decides (source human-11): \"{ACCEPT}\" Reason given: links should be navigable. Capture this accepted decision now, then write implementation-plan.md describing how to implement it. Do not implement product behavior; this is decision recording and planning only.")
    if case == "capture-readonly":
        return [capture + " This task is strictly read-only: do not create or edit any file, including the decision owner and implementation-plan.md. Report the uncaptured decision and the next safe action instead."]
    return [capture, f"Correction on 2026-11-10, source human-12: \"{CORRECTION}\" This changes only the unattended-report portion of human-11; keep its interactive-report permission, product-notification exclusion and the other accepted constraints. No additional reason was given. Save and reread the partial correction, then update implementation-plan.md. Do not implement product behavior."]


def rows(text):
    result = {}
    for line in text.splitlines():
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if len(cells) == 6 and re.fullmatch(r"[A-Z][A-Z0-9]*(?:-[A-Z][A-Z0-9]*)*-\d+", cells[0]):
            result[cells[0]] = cells
    return result


def grade(repo, case, before, watermark):
    files = {str(p.relative_to(repo)): p.read_text() for p in repo.rglob("*")
             if p.is_file() and ".git" not in p.relative_to(repo).parts}
    if case in ("mixed-writers", "capture-readonly"):
        return {"repository_content_unchanged": files == before}
    readme = files.get("SSOT/README.md", "")
    register = rows(readme)
    checker = repo / ".agents/skills/ssot-doctor/assets/scripts/ssot-check.py"
    checked = subprocess.run([sys.executable, "-B", str(checker), str(repo / "SSOT")], capture_output=True, text=True)
    common = {"checker_passes": checked.returncode == 0 and "ssot-check: PASS" in checked.stdout,
              "watermark_preserved": f"reviewed_through: {watermark}" in readme,
              "unrelated_instruction_preserved": "Never publish payment credentials." in files.get("AGENTS.md", "")}
    if case == "partial":
        owner = files.get("docs/decisions.md", "")
        plan = files.get("implementation-plan.md", "")
        original = rows(before["SSOT/README.md"])
        current_format = [row for row in register.values() if row[4] == "confirmed"
                          and "report" in row[2].lower()
                          and any(word in row[2].lower() for word in ("markdown", "plain text"))]
        format_rules = " ".join(row[2].lower() for row in current_format)
        common.update({
            "unaffected_rules_identical": all(register.get(key) == original[key] for key in ("INV-01", "INV-02")),
            "history_and_source_words_preserved": all(value in owner for value in (INITIAL, ACCEPT, CORRECTION, "human-10", "human-11", "human-12")),
            "format_rule_remains_confirmed": bool(current_format) and all(key in register for key in original),
            "partial_scope_in_current_rule": all(word in format_rules for word in ("interactive", "unattended", "markdown", "plain text")),
            "plan_obeys_partial_scope": all(word in plan.lower() for word in ("interactive", "unattended", "markdown", "plain text", "scope", "read-only")),
            "single_owner": not any(name.startswith("SSOT/decisions/") for name in files),
            "write_scope": {k for k in set(files) | set(before) if files.get(k) != before.get(k)} <= {"SSOT/README.md", "docs/decisions.md", "implementation-plan.md"},
        })
        return common
    corpus = "\n".join(text for name, text in files.items() if name.startswith("SSOT/") and name.endswith(".md"))
    retired = ("SSOT/STATUS.md", "SSOT/HISTORY.md", "SSOT/02-architecture/_manifest.md", "SSOT/.bootstrap/review.md")
    wrapper = subprocess.run(["sh", "check-memory.sh"], cwd=repo, capture_output=True, text=True)
    statuses = {key: value[4] for key, value in register.items()}
    old = files.get("SSOT/04-records/decisions/0001-remote-queue.md", "")
    active = files.get("SSOT/04-records/decisions/0002-local-queue.md", "")
    common.update({
        "format4": "ssot_format: 4" in readme,
        "old_owners_and_shared_entry_preserved": all(name in files for name in ("SSOT/02-architecture/README.md", "SSOT/04-records/decisions/0001-remote-queue.md", "SSOT/04-records/decisions/0002-local-queue.md")) and (repo / "CLAUDE.md").is_symlink() and os.readlink(repo / "CLAUDE.md") == "AGENTS.md",
        "existing_rule_authority_preserved": statuses.get("INV-01") == "confirmed" and statuses.get("INV-02") == "candidate" and statuses.get("CLAUDE-MAXIM-1") == "candidate" and statuses.get("CORE-RULE-1") == "confirmed",
        "offline_directive_is_confirmed": any(row[4] == "confirmed" and "offline" in row[2].lower() and "manual" in row[2].lower() for row in register.values()),
        "gaps_and_questions_preserved": "ADJ-7" in readme and "GAP-12" in readme,
        "unique_ledger_knowledge_preserved": all(word in corpus.lower() for word in ("receipts", "late", "audit-tail", "obligation", "macos", "not implemented")),
        "human_words_preserved": FACTS["offline"] in corpus and FACTS["pilot"] in corpus,
        "subject_status_retained_in_prose": "supersed" in old.lower() and "0002-local-queue" in old and "accepted" in active.lower() and bool(re.search(r"not (?:yet )?(?:implemented|built)|unimplemented|planned|pending", active, re.I)),
        "subject_frontmatter_removed": not any(re.search(r"^(record_status|implementation_state|intent_recovery|promotion_targets|updated_on):", text, re.M) for text in (old, active, files.get("SSOT/02-architecture/README.md", ""))),
        "ledgers_and_checkpoint_removed": not any(name in files for name in (*retired, "SSOT/BOOTSTRAP.md")) and not (repo / "SSOT/.bootstrap").exists(),
        "old_instruction_workflow_removed": all(word not in files.get("AGENTS.md", "") for word in ("tracked_protocol", "protocol lag", "SSOT/STATUS.md", "SSOT/HISTORY.md")),
        "wrapper_runs": wrapper.returncode == 0 and "ssot-check: PASS" in wrapper.stdout,
        "inbound_links_repaired": all(name not in files.get("docs/guide.md", "") for name in ("STATUS.md", "_manifest.md")),
        "one_time_pilot_not_promoted": not any("pilot" in row[2].lower() for row in register.values()),
        "rejected_proposal_not_promoted": "debug" in corpus.lower() and "reject" in corpus.lower() and not any("debug" in row[2].lower() for row in register.values()),
    })
    return common


def capture_order(run_dir, turn, quote):
    """Require saved owner → returned owner text → changed dependent plan."""
    before = json.loads((run_dir / f"{turn}.before.json").read_text())
    checkpoints = json.loads((run_dir / f"{turn}.checkpoints.json").read_text())
    owner_saved = next((c["event"] for c in checkpoints if quote in c["files"].get("docs/decisions.md", "")), None)
    plan_written = next((c["event"] for c in checkpoints if c["files"].get("implementation-plan.md") != before.get("implementation-plan.md")), None)
    if owner_saved is None or plan_written is None or owner_saved >= plan_written:
        return False
    for number, line in enumerate((run_dir / f"{turn}.jsonl").read_text().splitlines(), 1):
        event = json.loads(line)
        item = event.get("item", {})
        if (owner_saved <= number < plan_written and event.get("type") == "item.completed"
                and item.get("type") == "command_execution" and item.get("exit_code") == 0
                and "docs/decisions.md" in item.get("command", "")
                and quote in item.get("aggregated_output", "")):
            return True
    return False


def migration_in_flight(before, current):
    return ("SSOT/BOOTSTRAP.md" in current
            and any(name.startswith("SSOT/") and name != "SSOT/BOOTSTRAP.md"
                    and before.get(name) != text for name, text in current.items()))
