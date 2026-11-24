---
name: ssot-closeout
description: Capture settled durable choices immediately, record requested handoffs and reconcile lasting changes before batch end.
---

# SSOT Closeout

A task used as a source stays under its executor. Report discrepancies in the requested output. Changing the source task’s state needs separate authority.

For withdrawals or restricted sources, establish [permitted use](../ssot-preflight/references/source-retention.md#permitted-use) before reading related evidence. Check the explicit entry or default `SSOT/README.md`, its format, setup state, applicable protections and owner rules (you may read the entry header/headings in the same step as this `SKILL.md`, before opening linked owners). Once entry permissions and protections are verified, batch independent authorized reads and reuse current passages.

**One settled edit (formats 4 and 5).** When setup is complete, verify that one accepted decision changes only existing prose in its authorized owner. Check the approvers, effective scope and dependencies. Changes to protections, document structure, routes or another live use take the full route. With all approvals present, update the passage in place. Record the accepted words and their source, scope, stated reason and effective point as the owner requires. Keep unaffected terms and the only retained account of who chose the previous rule and why, within retention permissions. Reopen the saved passage from disk (you may read it back in the same tool step right after saving) and check the new terms, source, scope and history. A proposal or missing approval leaves the current rule in force. For an authorized prose-only edit, readback finishes closeout; stop here, and run additional checks only when the project requires them. For broader changes check each affected owner.

For a bounded handoff, name the writable owners and supply only authorized evidence. Restrict actual access through the host when needed. Otherwise, format 5 continues with [general context spaces](../ssot-preflight/references/context-spaces.md#use-and-maintain-a-space), including lifecycle and handoff.

## Development repositories

- Without `SSOT/`, creation needs agreement (`$ssot-bootstrap`). While `SSOT/BOOTSTRAP.md` exists, update existing documents and leave remaining setup there.
- Known v2/v3 stays read-only pending agreed migration. List uncaptured durable facts and offer agreed migration. Unknown/future formats stay read-only without downgrade. Separate project workflows retain their explicit write authority, subject to the user's limits; they cannot rewrite an older SSOT or grant wider permission.
- Ordinary undeclared non-repository work skips closeout unless a record is requested. For format 4, reconcile this batch's verified changes in their single owner. Leave unverified concurrent changes for `$ssot-doctor` catch-up and tell the user. Read only needed [model](../ssot-preflight/references/memory-model.md) sections.

## Choose the route

- **Durable choice just settled:** follow [immediate decision capture](references/decision-capture.md) now. Batch reconciliation waits until the batch ends.
- **Pause, checkpoint or handoff requested:** follow [task continuation](../ssot-preflight/references/memory-layout.md#existing-task-and-evidence-owners) in the authorized task owner.
- **Batch end:** compare this task's diff, conversation and observations with the relevant owners. Include decisions and rejected alternatives, changed contracts or behavior, traps and causes, commands, workarounds and removal conditions, lasting directives, lasting findings, wrong SSOT statements and missing protected rules. Use [what to store](../ssot-preflight/references/memory-model.md#2-what-to-store-and-what-to-leave-out) if durability is unclear.

Before deciding nothing changed, open the owners for the touched areas and problems preflight surfaced. Reuse unchanged passages only under [preflight's reuse rule](../ssot-preflight/SKILL.md#2-read-what-this-task-needs). Correct stale guidance in scope even when recoverable from code. Updates already made count. If the owners still hold and nothing durable is missing, write nothing: no logs, timestamps or checked markers. Report the owners compared and why no update was needed. Stop here only for content-only changes outside `SSOT/` and its routed owners, with no added, moved, renamed or deleted files or headings; otherwise follow batch step 5 even if updates are complete.

For remaining durable changes, follow [batch reconciliation](references/batch-closeout.md), starting at step 2. Committing and pushing follow the project's rules.
