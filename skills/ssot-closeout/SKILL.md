---
name: ssot-closeout
description: Capture durable user decisions immediately, including discussion-only confirmations, corrections, rejections and scope limits. Reconcile lasting decisions, behavior, traps, commands and workarounds in their single owner before a substantive batch's final response or commit. Write nothing when no durable fact changed; skip typo and formatting edits without durable decisions.
---

# SSOT Closeout

Reconcile durable changes in their single owner. The [memory model](../ssot-preflight/references/memory-model.md) defines what belongs there; read its relevant sections when needed, reusing material still current in context.

## Before you start

- **No `SSOT/` directory.** Do not create one without agreement (`$ssot-bootstrap`). Existing project-authorized owner recording can still use the immediate route.
- **Not v4** (`SSOT/README.md` has no `ssot_format: 4`, including v2 or v3). Do not write the older SSOT or migrate it. List the durable facts from this batch for the user, explain that SSOT stays read-only until it is migrated, and offer the migration with `$ssot-bootstrap`.
- **Existing project workflow.** The gates above restrict SSOT protocol writes, not an existing recording process with explicit prior write authorization or the current user’s direct request to record in that owner. Follow that owner’s rules; this exception does not authorize changing an older SSOT format, reorganizing it, or inferring wider permission. A user’s read-only restriction still forbids writing; report an uncaptured decision without claiming persistence.
- **Setup unfinished** (`SSOT/BOOTSTRAP.md` exists). Update documents that already exist. Note anything else in `BOOTSTRAP.md` so setup picks it up.

The batch is the work done in this task. If other people's changes are in the tree, or `HEAD` moved underneath you, do not record facts from them that you have not verified. Tell the user, and leave them to a `$ssot-doctor` catch-up.

## Choose the route

- **Decision just settled:** follow [immediate decision capture](references/decision-capture.md) now. Batch reconciliation waits until the batch ends.
- **Batch end:** compare this task's diff, conversation and observations with the relevant owners. Include decisions and rejected alternatives, changed contracts or behavior, traps and causes, commands, workarounds and removal conditions, lasting directives, lasting findings, wrong SSOT statements and missing protected rules. Use [what to store](../ssot-preflight/references/memory-model.md#2-what-to-store-and-what-to-leave-out) if durability is unclear.

Before deciding nothing changed, open the owners for the touched areas and problems preflight surfaced. Reuse unchanged passages only under [preflight's reuse rule](../ssot-preflight/SKILL.md#2-read-what-this-task-needs). Fix or remove statements now wrong even when code could tell the fact; recoverability decides what to add, not what to leave wrong. Updates already made count. If the owners still hold and nothing durable is missing, write nothing: no logs, timestamps or checked markers. Report the owners compared and why no update was needed. Stop here only for content-only changes outside `SSOT/` and its routed owners, with no added, moved, renamed or deleted files or headings; otherwise follow batch step 5 even if updates are complete.

For remaining durable changes, follow [batch reconciliation](references/batch-closeout.md), starting at step 2. Committing and pushing follow the project's rules.
