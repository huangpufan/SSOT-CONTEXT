---
name: ssot-doctor
description: Check, review or catch up maintained repository or general-space context against its domain evidence and supplied sources. Use for an explicit context health check, review or catch-up, or when another SSOT skill routes here. Runs mechanical checks plus an agent review of the requested scope and reports exactly what was checked.
---

# SSOT Doctor

For a review, report proposed corrections. For an authorized repair or catch-up, follow the requested scope. A request to fix one finding covers that finding; report other issues even when they share the same file.

For a withdrawal or restricted source, establish [permitted use](../ssot-preflight/references/source-retention.md#permitted-use) before reading related content. Inspect the explicit entry or default `SSOT/README.md`: 5 uses [general context spaces](../ssot-preflight/references/context-spaces.md), especially Doctor/catch-up. Format 4 uses the repository route below; known v2/v3 stays read-only pending agreed migration. Unknown/future formats stay read-only without downgrade. Explicit source processing uses the conditional [source contract](references/source-integration.md). Ordinary undeclared chat/research/creation skips this skill.

Find where `SSOT/` is wrong, missing, contradictory, or hard to use, and say exactly how far your check went. The model you check against is [`memory-model.md`](../ssot-preflight/references/memory-model.md).

## 1. Agree on the scope

For known v2/v3, review read-only and offer an agreed `$ssot-bootstrap` migration. Unknown/future formats remain read-only; identify their writer rather than proposing downgrade.

The scope includes named supplied decision sources (conversation excerpts, accepted proposals or decision history), not only git. Identify the available source set and gaps; without those sources, never claim complete decision coverage. Reconcile provided decisions through closeout’s [capture route](../ssot-closeout/references/decision-capture.md). The scope is the whole routed memory, one area or file, a catch-up from a given commit, or mining one area's protected rules (follow `../ssot-bootstrap/references/mining.md`, with separate agents). State it in your report. Findings, and any statement that something is healthy, cover only that scope.

## 2. Run the mechanical check

Use [selected checks](../ssot-preflight/references/source-retention.md#selected-mechanical-checks) for restricted or uncertain reads, including the first invocation. Otherwise run `python3 <this skill's directory>/assets/scripts/ssot-check.py SSOT` from the repository root. It reports errors (a missing entry point, broken links or heading anchors, a malformed invariants register, a confirmed invariant changed without a new dated source) and warnings (oversized files, v2 leftovers, and mentioned files that git says were removed or moved). It cannot tell whether a statement is true or readable. Exit code 3 means incomplete coverage or a crash; retain any findings. Errors outside your scope do not stop the review of your scope. Report them separately.

## 3. Review the scope

For lifecycle, ownership or requirement-to-evidence gaps, choose the relevant methods in [structural review](references/structural-review.md); use existing review roles rather than adding helpers by default.

For costly reading, history accumulation or requested tiering/compression, review [context tiers](../ssot-preflight/references/context-tiering.md) within the requested scope; measure use, preservation and affected guidance, not archive size alone.

- **Truth.** In each document, pick the statements a future task would act on, such as contracts, state ownership, commands, defaults, and "planned" labels, and check each against its domain evidence (memory-model §3); a fresh helper that did not write them checks best. Look hardest at two kinds: statements with "all", "only", "every", "never", or "always", which often miss an exception; and statements taken from a design document, an ADR, or a code comment, which may describe intent the code does not implement. Identify unsupported claims and distinguish unbuilt intent from current behavior. In a repair, correct the affected text. Start with areas that changed recently in `git log`.
- **Consistency.** Look for one fact stated two different ways, and for superseded decisions still presented as current.
- **Invariants.** Every row links to its canonical owner inside the repository. No rule changed meaning or status without a recorded user decision. Each candidate meets the admission rule in memory-model §5; candidates are not a backlog for the user to confirm.
- **What does not belong.** Flag restated code, proof of a single task, edit history, and status about the documents themselves.
- **Usefulness to a newcomer.** If you can start a helper with a fresh context, give it three to five real tasks for this repository. Include at least one normal path, one failure or recovery case, and one boundary judgment ("may I change X?"). The helper starts from `SSOT/README.md` and follows its repository-owner links. Then check its key answers against domain evidence and confirmed decisions: an answer that matches a wrong document is a finding about the document. Report which tasks you used. If no helper is available, say that this check was your own reading.

## 4. Catch up on past commits

Use this when commits landed without SSOT updates, or when the user asks for a catch-up.

1. Pin the requested start and end (normally `reviewed_through` and `HEAD`) to full commit SHAs. Honor an earlier or narrower requested range. If no start is known, suggest the commit that created `SSOT/` and ask. If either endpoint is unavailable or the start is not an ancestor of the end, ask before treating the range as continuous.
2. For whole-range catch-up, review the commits reachable from the end that the start excludes. Use `git log --reverse --topo-order --format=medium --name-status <start>..<end>` to read each message body, including merged branches and commits without file changes. Inspect relevant diffs and the merge result for lasting changes. Distinguish rejected proposals, accepted plans and shipped behavior at the pinned end. For long ranges, work in segments and keep temporary coverage and remaining commits in the protected [.ssot-work directory](../ssot-bootstrap/references/mining.md#1-declare-the-scope-before-mining).
3. Reconcile durable facts in their owners through closeout, verify against domain evidence at the pinned end, and read back the saved text. Continue independent facts when an owner is blocked.
4. Move `reviewed_through` last, only forward from the saved marker (or agreed initial start) to a descendant whose entire intervening range has been reviewed and reconciled. A later requested start leaves a gap. Preserve the marker for that gap, a path- or branch-limited review, unavailable history or an unfinished segment. Report actual coverage and the next uncovered range.

## 5. Catch up from conversations

For first or comprehensive decision recovery across AI products, or supplied conversation histories, follow [conversation catch-up](references/conversation-catchup.md). Git catch-up does not cover this source set.

## 6. Report

Report the scope, the checker result, and the findings ordered by impact, each with its file and evidence. Separate what you fixed from what remains, and list what you did not check.
