---
name: ssot-preflight
description: Read SSOT before substantive work in a repository or declared space. Follow its bounded lookup and edit routes. Skip pure commands and cosmetic edits.
metadata:
  protocol_version: "5.23"
  bundle: "SSOT-CONTEXT"
---

# SSOT Preflight

Find the entry point before loading the [memory model](references/memory-model.md). For a withdrawal or restricted source, establish [permitted use](references/source-retention.md#permitted-use) before opening related owners or evidence.

When the workflow says placing content in a destination can trigger delivery, publication or execution, check who may cause that effect before writing or moving anything there. If only the choice is delegated, leave the live destination untouched and use an authorized draft or handoff. If release is delegated, use the designated destination.

Read the explicit entry or default `SSOT/README.md` by header and headings first (you may read it in the same step as this `SKILL.md`, before opening any linked owner or source). Check its applicable ownership, permissions and protections before following a route. Explicit SSOT checks, reviews and catch-up use `$ssot-doctor` even alongside implementation; ordinary code reviews do not.

In formats 4 and 5, answer a lookup from its current authorized owner when that owner settles the question. For one settled prose change confined to that owner, use `$ssot-closeout` directly. Follow owner-specific requirements. If the answer depends on other evidence or decisions, follow their authorized routes. Restricted sources require the permission result before any dependent read, including a search.

Otherwise format 5 and agreed general-space setup use [general context spaces](references/context-spaces.md); format 4 uses the steps below. Known v2/v3 stays read-only pending agreed migration (`$ssot-bootstrap`); unknown/future formats stay read-only pending a compatible writer (never offer migration or downgrade). Undeclared non-repository chat, research or creation skips this skill.

## 1. Find the entry point

- **No `SSOT/` directory.** Tell the user the repository has no SSOT and offer to create one with `$ssot-bootstrap`. Setup writes a documentation tree and can take more than one session, so it needs the user's yes. If they decline or defer, do the task without the SSOT steps, and do not offer again this session.
- **`SSOT/BOOTSTRAP.md` exists.** Setup is unfinished. Offer to continue it, and meanwhile use what is already written.
- **Known v2/v3 layout.** Read it as knowledge: coverage labels and review records are historical, while relevant adjudications, user constraints, limits and open questions still bind. Offer preservation-aware migration via `$ssot-bootstrap`.

## 2. Read what this task needs

Read the orientation, task routes and relevant open questions using the section locations above. A compact entry can fit in one pass. For a large entry, use bounded ranges and search the invariants register in place. Recover any needed text cut off by tool output before relying on it. Load [memory-model](references/memory-model.md) sections 1, 3 and 5; reuse them while current in context. Use [decision evidence](references/memory-model.md#human-decision-evidence) for acceptance or replacement; [writing rules](references/writing-memory.md) when writing. Then:

1. **Invariants.** Search the register for affected outcomes, including general rules and related topics. When `## Invariants` links [topic shards](references/memory-model.md#5-invariants), read the cross-cutting rows in the entry and open only matching shards, skipping cold retired shards (`invariants/retired.md` or `ssot_tier: cold`) on routine tasks. Use route terms, user-facing behavior and dependencies to find matches. If headings or terms are unclear, widen to related shards and product or architecture owners. Read each matching row and its linked explanation with conditions and exceptions intact. Section 3 says what to do when the change could break one.
2. **Open questions.** If one blocks the path this task needs, say so. Only the work that depends on the answer waits; unrelated work goes ahead.
3. **Known traps and limits.** Read the gotchas and the known gaps that touch the parts you will change, and handle each one: fix it, work around it deliberately, or say why it does not apply.
4. **Routes.** Follow matching task routes to owner sections and their stated expansion conditions. If no route fits or a link is stale, use the product and architecture entries, then search for the current owner. Read related constraints across owners before changing shared behavior; a route is a starting point, not the task boundary. Skip cold targets on routine tasks—cold archives (`decisions/`, `archive/`, `history/`, `*-history.md`, `*-archive.md`, `ssot_tier: cold`), concluded `research/`, and trailing intra-file cold sections (`## History (cold)`, `## Archive (cold)`, `## 历史记录（冷读）`, `## 历史归档（冷读）`, or `<!-- ssot:cold -->`)—and open them only when tracing reasons, rejected options, research evidence, or conflicts. Avoid whole-tree reads.
5. **What you rely on.** When an SSOT statement decides how you will implement something, check the evidence appropriate to its domain first (memory-model §3). Code shows implementation, not whether a human decision was accepted. Note the mismatch so closeout fixes the document, or so you can report the violation.

Reuse retained instructions and model sections until updates or context loss. Each new task refreshes the relevant entry sections and owners, including dirty and untracked content; unchanged `HEAD` is insufficient. Within a task, reuse unchanged passages; reread after edits, scope changes or uncertain freshness. Batch independent reads and bound excerpts.

For oversized entries, repeated reconstruction from history, or requested tiering/compression, use [context tiers](references/context-tiering.md#when-reading-has-become-costly). Ordinary reading keeps the routes above.

## 3. Find what the change must preserve

Skip this section for read-only review or investigation (still note observed violations). Before you settle on an implementation, identify the behaviors and boundaries the change could affect: their canonical owners and the domain evidence that establishes them. For software, inspect the tests, boundary checks and guards, and fix or revert history; follow callers and shared state where effects cross files. For creative, research or human-decision work, use the relevant canon, original materials or accepted source exchange rather than requiring code evidence. Tell a protected outcome from an incidental detail with the admission and departure rules in [memory-model.md §5](references/memory-model.md#5-invariants).

Before implementation details, state each affected rule, registered or newly admitted: "Must preserve: [outcome and conditions] — [evidence]." Compare the request with these rules. For a concrete conflict, propose a preserving design that meets the request, or follow "When to ask" in memory-model §5. Continue independent work. Record missing rules through closeout using [human-decision evidence](references/memory-model.md#human-decision-evidence): preserve recorded acceptance; only inferred rules are candidates.

## 4. Before your first change, and while you work

When resuming paused or interrupted work, follow [task continuation](references/task-continuation.md) before planning from its saved state.

Invoke `$ssot-closeout` immediately when the user settles or revises a durable choice (even in discussion), before dependent work. Update obvious owners as you work, and run `$ssot-closeout` before replying or committing if this batch edited files, requested a handoff, or surfaced a lasting finding or wrong/missing SSOT statement; pure read-only review or investigation with none of those finishes directly without loading `$ssot-closeout` (if it hit severe entry/doc truncation or a bloated chronological startup log, optionally add a one-line `$ssot-doctor` compaction note in the reply without extra reads).
