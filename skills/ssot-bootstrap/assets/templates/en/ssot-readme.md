---
ssot_format: 4
language: en
reviewed_through: <commit you explored>
---

# <Project name>

<!-- Remove instructional comments when filling. In a few plain sentences: who this is for, what it does, and what it deliberately does not do. -->

## Map

<!-- Route to existing canonical repository owners (including outside SSOT/) and remove unused fallbacks. Mark cold history so routine tasks skip it; never route routine startup to an unbounded chronological log. -->

- [Product](product.md): who uses it, what it promises, and what it does not do.
- [Architecture](architecture.md): parts, state ownership, key flows, and failure handling.
- [Process](process.md): how to build, test, release, and deploy.
- [Decisions](decisions/): cold history of choices, superseded rules, and rejected options (skip on routine tasks unless tracing reasons or conflicts).
- [Gotchas](gotchas.md): traps and temporary workarounds that have already cost time.
- [Glossary](glossary.md): project terms a newcomer would misread.

## Task routes

<!-- Map recurring tasks to direct owner sections, the question answered, and expansion triggers; replace the example and keep facts in their owners. If routes grow long, use compact one-line bullets instead of a wide table. -->

| When the task… | Read first and why | Expand when… |
|---|---|---|
| changes payment retries | [Failure and recovery](architecture.md#failure-and-recovery): what survives a retry | shared state or side effects change: follow related owners and [INV-01](#invariants) |

## Open questions

<!-- Unresolved decisions and known gaps blocking work: one line each (what is open, what it blocks, where details live). Delete once resolved—never leave `[RESOLVED]` or strikethrough tombstones. If none, say so. -->

## Invariants

Confirmed rules bind until a person changes them; candidate rules are inferred protections to follow by default and settle only when a task needs to depart (see `memory-model.md` in SSOT-CONTEXT).

| ID | Kind | Rule | Explained in | Status | Source |
|---|---|---|---|---|---|

<!-- Example row:
| INV-01 | product promise | A retry never charges twice | [Retries](architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |
Kind: product promise, architecture invariant, or process rule. Status: confirmed / candidate / retired (link retiring decision). If none yet, keep the empty table and say so. Keep each row to one concise line (1 canonical owner link; compact dated source—never verbatim quotes or readback logs in Source). At ~50+ rows, keep cross-cutting rules here and link `invariants/<topic>.md` shards (and optional `invariants/retired.md` for retired rows) from a bullet list, never a table. -->
