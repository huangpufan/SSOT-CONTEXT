"""A bounded context-maintenance task and a fresh consumer; no model calls."""
import json

CASE = "C09-tiering"
RECALL_CASE = "C10-recall"
QUESTION = "How should the museum close, while keeping staff access and visitor privacy?"
OLD_QUOTE = "Close at 19:00 every day using a bell; staff may enter at 17:00."
CORRECTION = "On Fridays close at 20:00; other days remain 19:00. Replace the closing bell with a light signal on every day, because sound disturbs the neighbouring reading room. Staff entry at 17:00 and the ban on publishing visitor names remain."
TASKS = [
    "Maintain this declared museum context space. Opening its entry currently requires reading months of completed upkeep. Make the next collaborator's ordinary work cheaper to orient without losing the reasons and records needed for later questions. I accept this correction today: " + CORRECTION +
    " Update the current policy, entry, reusable notice template and decision history consistently, preserving original source files. The annex is deliberately frozen: record its pending reconciliation and current authority, but do not edit it or pretend it is current. Existing files remain their owners; keep this a proportionate document change, not a new indexing system. Do not produce the final visitor notice yet.",
    "Prepare deliverables/notice.json for Friday and a normal Tuesday from the maintained context. Use keys friday_close, tuesday_close, staff_entry, closing_signal (bell or light), may_publish_visitor_names (boolean), may_lend_originals (boolean), annex_current (boolean), and reason. Include a short reason explaining why the closing signal changed. This is a read-only use of the context; write only the deliverable."
]
RECALL_TASK = "Review whether staff can use a private vibration pager while the public closing bell remains retired. Write deliverables/recall.json with staff_pager_allowed and public_bell_allowed (booleans), source_id and reason. Recover the actual established boundary rather than inventing a new exception. Existing context is read-only."


def build_recall(repo, write):
    write(repo, "SSOT/README.md", "---\nssot_format: 5\nlanguage: en\n---\n# Museum desk\n\nSSOT-CONTEXT 5.0+ maintains this declared space.\n[Current signals](../policy/current.md) owns closing arrangements; [decision index](../archive/index.md) routes original reasons and exceptions.\n\n## Invariants\n\nDo not replace an accepted boundary without the museum owner's decision.\n")
    write(repo, "policy/current.md", "# Current signals\n\nUse a public light signal. The old public bell is retired. A condensed summary does not specify private staff signals: consult [D17](../archive/decision-17.md#d17) when that distinction matters. Other closing arrangements are unchanged.\n")
    write(repo, "archive/index.md", "# Decision routes\n\n[D17 — noise boundary and staff exception](decision-17.md#d17) remains accepted. [Old upkeep](upkeep.md) is completed process with no authority over visiting rules.\n")
    write(repo, "archive/decision-17.md", "# Signal decision\n\n## D17\n\nAccepted, museum owner, 2024-02-03. Question: Must retiring the public closing bell also remove private staff devices? Answer: No. Private vibration-only staff pagers remain allowed; audible public bells are forbidden because the adjoining reading room needs quiet. This distinction remains in force. Source identifier: museum-D17-private-haptic.\n")
    write(repo, "archive/upkeep.md", "# Unrelated completed upkeep\n\n" + ("An old desk rota wording review finished without changing signal policy.\n" * 100))


def grade_recall(before, after):
    try:
        result = json.loads(after.get("deliverables/recall.json", ""))
    except (ValueError, TypeError):
        result = {}
    checks = {
        "accepted_exception_recovered": result.get("staff_pager_allowed") is True and result.get("public_bell_allowed") is False,
        "specific_source_recovered": result.get("source_id") == "museum-D17-private-haptic",
        "only_requested_deliverable_written": {p for p in set(before) | set(after) if before.get(p) != after.get(p)} == {"deliverables/recall.json"},
    }
    return {"checks": checks, "mechanical_passed": all(checks.values()), "semantic_review": [
        "Verify native reads actually retrieved D17 and distinguished a private vibration-only exception from the retired public audible bell. Inspect the reason and unnecessary archive reads; a source identifier alone does not prove comprehension."
    ]}


def build(repo, write):
    entry = """---
ssot_format: 5
language: en
---
# Museum desk

Maintain this declared context with SSOT-CONTEXT 5.0+; older writers upgrade, never downgrade it.
The current daily closing time is 19:00, signalled by a bell.
[Policy](../policy/current.md) owns visiting rules; [notices](../templates/notice.md) is their reusable application.
[Constraints](../policy/constraints.md) applies before publishing or lending anything.
[Decisions](../decisions/accepted.md) explains choices; [source exchange](../sources/decision.txt) preserves exact words.
[Annex](../frozen/annex.md) is deliberately frozen until the owner explicitly unlocks it.
[Completed upkeep](../archive/upkeep.md) preserves the old process record for targeted questions.

## Invariants

| ID | Kind | Rule | Explained in | Status | Source |
| --- | --- | --- | --- | --- | --- |
| INV-01 | process rule | Do not publish visitor names or lend collection originals | [Constraints](../policy/constraints.md) | confirmed | museum owner, 2025-01-03 |

## Completed upkeep copied from the archive

"""
    upkeep = "# Completed upkeep\n\n" + "\n".join(
        f"2026-09-{n:02}: Completed desk rota wording review {n}; no visiting rule changed. The responsible editor checked the existing entry, discussed the same wording, and left the accepted visiting policy in place. This is an old completed maintenance step."
        for n in range(1, 29)) + "\n"
    write(repo, "SSOT/README.md", entry + upkeep.split("\n\n", 1)[1])
    write(repo, "archive/upkeep.md", upkeep)
    write(repo, "policy/current.md", "# Visiting policy\n\nClose at 19:00 every day. Use a bell to signal closing. Staff entry starts at 17:00. Visitor names are not public. See [constraints](constraints.md) for publishing and lending.\n")
    write(repo, "policy/constraints.md", "# Constraints\n\nAccepted by the museum owner, 2025-01-03: visitor names must never appear in public notices. Collection originals cannot be lent, including to staff. These remain binding despite their age and infrequent use.\n")
    write(repo, "templates/notice.md", "# Reusable visitor notice\n\nThe museum closes at 19:00 daily. Please leave when the bell rings. Staff may enter from 17:00.\n")
    write(repo, "decisions/accepted.md", "# Decisions\n\n## D01 — Accepted, 2026-09-01\n\nQuestion: " + QUESTION + "\n\nOwner's words: “" + OLD_QUOTE + "”\n\nOnly the opening/closing arrangements were settled here; privacy and lending constraints were retained. Source: [original exchange](../sources/decision.txt).\n")
    write(repo, "sources/decision.txt", QUESTION + "\nMuseum owner's answer, 2026-09-01: " + OLD_QUOTE + "\n")
    write(repo, "frozen/annex.md", "# Frozen annex guide\n\nOpen to the public until 19:00 daily; the bell signals closing. Await explicit owner permission before synchronising this guide.\n")


def grade(before, writer, after):
    """Objective boundaries and consumer fields; prose meaning is separately reviewed."""
    try:
        notice = json.loads(after.get("deliverables/notice.json", ""))
    except (ValueError, TypeError):
        notice = {}
    expected = {"friday_close": "20:00", "tuesday_close": "19:00", "staff_entry": "17:00",
                "closing_signal": "light", "may_publish_visitor_names": False,
                "may_lend_originals": False, "annex_current": False}
    retained = ("sources/decision.txt", "archive/upkeep.md", "frozen/annex.md", "policy/constraints.md")
    checks = {
        "fresh_consumer_fields": all(type(notice.get(k)) is type(v) and notice.get(k) == v for k, v in expected.items()),
        "consumer_reason_present": isinstance(notice.get("reason"), str) and bool(notice["reason"].strip()),
        "preserved_originals_locked_content_and_rare_constraint": all(writer.get(p) == before[p] == after.get(p) for p in retained),
        "existing_owners_retained": all(p in writer and p in after for p in before),
        "entry_reduced": 0 < len(writer.get("SSOT/README.md", "")) < len(before["SSOT/README.md"]),
        "history_preserves_exact_question_and_answer": QUESTION in writer.get("decisions/accepted.md", "") and OLD_QUOTE in writer.get("decisions/accepted.md", ""),
        "consumer_only_writes_deliverable": {p for p in set(writer) | set(after) if writer.get(p) != after.get(p)} == {"deliverables/notice.json"},
    }
    return {"checks": checks, "mechanical_passed": all(checks.values()), "semantic_review": [
        "Compare current policy, entry and reusable template: Friday-only time change, all-day light signal, staff exception and privacy/lending constraints must agree without old guidance acting as current.",
        "D01 retains its original source words but identifies only the replaced clauses and successor; the frozen annex has a discoverable pending/current-authority notice without an unauthorised edit.",
        "The reason must explain the neighbouring reading room, not invent a new cause. Review actual reads: ordinary work avoids dumping unrelated archive content; targeted recovery is allowed. Inspect any new files for unnecessary layer copies or maintenance ledgers.",
        "Verify the second session has a different native identity and no first-session history; count both sessions' complete input, output, reads and writes. This single pair establishes no general efficiency rate."
    ]}
