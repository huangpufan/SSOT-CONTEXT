---
name: ssot-preflight
description: Read relevant maintained context before substantive repository work or work in a declared context space. Find protected rules, owners and blocking questions for code, configuration, documentation, review, debugging or planning. Use for an explicit request to maintain non-repository context; ordinary chat, research answers or creative writing without a declared space do not trigger setup. Skip pure commands and meaning-preserving typo or formatting edits.
metadata:
  protocol_version: "5.1"
  bundle: "SSOT-CONTEXT"
---

# SSOT Preflight

Find the entry point before loading the [memory model](references/memory-model.md).

Inspect the explicit entry or default `SSOT/README.md` first. Format 5 uses [general context spaces](references/context-spaces.md); format 4 uses the repository steps below. Known v2/v3 uses the legacy read-only route. Unknown/future markers stay read-only: identify/upgrade the writer, never downgrade the data. Explicit new general-space setup also uses the general branch. Ordinary undeclared non-repository chat, research or creation skips this skill.

Explicit SSOT checks, reviews or catch-up require `$ssot-doctor` for that scope, including alongside implementation; preflight cannot replace it. Ordinary code reviews do not trigger Doctor.

## 1. Find the entry point

- **No `SSOT/` directory.** Tell the user the repository has no SSOT and offer to create one with `$ssot-bootstrap`. Setup writes a documentation tree and can take more than one session, so it needs the user's yes. If they decline or defer, do the task without the SSOT steps, and do not offer again this session.
- **`SSOT/BOOTSTRAP.md` exists.** Setup is unfinished. Offer to continue it, and meanwhile use what is already written.
- **Known v2/v3 layout.** Read it as knowledge. Its coverage labels and review records are historical, but relevant adjudications, user constraints, limits and open questions still bind. Keep it read-only and offer the agreed preservation-aware migration through `$ssot-bootstrap`; do not apply that offer to unknown/future formats.

## 2. Read what this task needs

Read `SSOT/README.md` with normal file tools (`cat`, `rg`, `sed`, or equivalents). For v4, load [memory-model](references/memory-model.md) sections 1, 3 and 5; reuse them while current in context. Search headings to locate sections, then read their conditions and exceptions together. Use [decision evidence](references/memory-model.md#human-decision-evidence) for acceptance or replacement; [writing rules](references/writing-memory.md) when writing. Then:

1. **Invariants.** Find the rows whose rule this task could affect, and read the explanation each one links to. Section 3 says what to do when the change could break one.
2. **Open questions.** If one blocks the path this task needs, say so. Only the work that depends on the answer waits; unrelated work goes ahead.
3. **Known traps and limits.** Read the gotchas and the known gaps that touch the parts you will change, and handle each one: fix it, work around it deliberately, or say why it does not apply.
4. **Routes.** Follow matching task routes to owner sections and their stated expansion conditions. If no route fits or a link is stale, use the product and architecture entries, then search for the current owner. Read related constraints across owners before changing shared behavior; a route is a starting point, not the task boundary. Avoid whole-tree reads.
5. **What you rely on.** When an SSOT statement decides how you will implement something, check the evidence appropriate to its domain first (memory-model §3). Code shows implementation, not whether a human decision was accepted. Note the mismatch so closeout fixes the document, or so you can report the violation.

Reuse retained instructions and model sections until updates or context loss. Each new task rereads README and relevant owners, including dirty and untracked content; unchanged `HEAD` is insufficient. Within a task, reuse unchanged passages; reread after edits, scope changes or uncertain freshness. Batch independent reads and bound excerpts.

## 3. Find what the change must preserve

Before you settle on an implementation, identify the behaviors and boundaries the change could affect: their canonical owners and the domain evidence that establishes them. For software, inspect the tests, boundary checks and guards, and fix or revert history; follow callers and shared state where effects cross files. For creative, research or human-decision work, use the relevant canon, original materials or accepted source exchange rather than requiring code evidence. Tell a protected outcome from an incidental detail with the admission and departure rules in [memory-model.md §5](references/memory-model.md#5-invariants).

Before implementation details, state each affected rule, registered or newly admitted: "Must preserve: [outcome and conditions] — [evidence]." Compare the request with these rules. For a concrete conflict, propose a preserving design that meets the request, or follow "When to ask" in memory-model §5. Continue independent work. Record missing rules through closeout using [human-decision evidence](references/memory-model.md#human-decision-evidence): preserve recorded acceptance; only inferred rules are candidates.

## 4. Before your first change, and while you work

When the user confirms, corrects, rejects, or limits a durable decision, invoke `$ssot-closeout` immediately, including during discussion-only work. Its [decision capture route](../ssot-closeout/references/decision-capture.md) records and rereads the decision before dependent work continues; do not wait for the batch to end.

Watch for the other facts that will outlive the task: decisions, changed contracts or behavior that users rely on, traps you hit, changed commands, and temporary workarounds. Note them as they come up; `$ssot-closeout` records them before you finish, and you may update an obvious owner right away.

## Where to go next

| Situation | Skill |
|---|---|
| No SSOT yet, setup unfinished, or an older layout to migrate | `$ssot-bootstrap` |
| Finishing a substantive batch, before the final response or commit | `$ssot-closeout` |
