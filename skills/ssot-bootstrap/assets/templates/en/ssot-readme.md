---
ssot_format: 4
language: en
reviewed_through: <commit you explored>
---

# <Project name>

<!-- In a few sentences of plain prose: who this is for, what it does for them, and what it deliberately does not do. After this paragraph a newcomer should be able to explain the project to someone else. -->

## Map

<!-- Route to existing canonical repository owners, including files outside SSOT/. The links below are fallback examples: replace them with real owners and remove unused entries. -->

- [Product](product.md): who uses it, what it promises, and what it does not do.
- [Architecture](architecture.md): the parts, who owns which state, the key flows, and failure handling.
- [Process](process.md): how to build, test, release, and deploy.
- [Decisions](decisions/): cold history of choices, superseded rules, and rejected options (skip on routine tasks unless tracing reasons or conflicts).
- [Gotchas](gotchas.md): traps that have already cost time.
- [Glossary](glossary.md): project terms a newcomer would misread.

## Task routes

<!-- Use recurring tasks, direct owner sections, the question answered, and when to expand. Replace the example; keep facts in their owners. -->

| When the task… | Read first and why | Expand when… |
|---|---|---|
| changes payment retries | [Failure and recovery](architecture.md#failure-and-recovery): what survives a retry | shared state or side effects change: follow related owners and [INV-01](#invariants) |

## Invariants

These are rules people decided and the implementation must preserve. An agent never changes a rule's meaning, scope, or status on its own: a task that conflicts with a confirmed rule stops and asks the user. A candidate rule was inferred from protection evidence; follow it by default, and settle it with the user only when a task needs to depart from it.

| ID | Kind | Rule | Explained in | Status | Source |
|---|---|---|---|---|---|

<!-- Example row:
| INV-01 | product promise | A retry never charges twice | [Retries](architecture.md#failure-and-recovery) | confirmed | user, 2026-05-02 |
Kind: product promise, architecture invariant, or process rule. Status: confirmed = set by a person; candidate = inferred protection, binds until a task needs to depart from it; retired = no longer applies (link the decision). If there are none yet, keep the empty table and say so in one sentence. Keep rows concise (quotes/history belong in the linked owner or cold decisions). When large (~50+ rows), keep cross-cutting rules here and move topic groups into `invariants/<topic>.md` shards (optionally retired rows into `invariants/retired.md`) linked from a bullet list (never a table). -->

## Open questions

<!-- Unresolved decisions and known gaps that affect work. For each: what is open, which work it blocks, and where the details live. Delete an entry once it is resolved. If there are none, say so. -->
