---
name: ssot-closeout
description: Update the repository's SSOT at the end of a substantive change batch, before the final response or commit. Records decisions, changed contracts or behavior, new traps, changed commands, temporary workarounds, and lasting user directives in their single owner, and removes the statements they supersede. Writes nothing when no durable fact changed. Do not use for typo or formatting edits or at the start of a task.
---

# SSOT Closeout

Bring `SSOT/` in line with what this batch changed: the diff, the decisions made in the conversation, and what you observed while working. What to store, where it lives, and how to write it are defined in [`memory-model.md`](../ssot-preflight/references/memory-model.md).

## Before you start

- **No `SSOT/` directory.** Nothing to do, unless the user asked to create one (that is `$ssot-bootstrap`).
- **Not v3** (`SSOT/README.md` has no `ssot_format: 3`, usually a v2 layout with `STATUS.md`). Do not write. List the durable facts from this batch for the user, explain that SSOT stays read-only until it is migrated, and offer the migration with `$ssot-bootstrap`.
- **Setup unfinished** (`SSOT/BOOTSTRAP.md` exists). Update documents that already exist. Note anything else in `BOOTSTRAP.md` so setup picks it up.

The batch is the work done in this task. If other people's changes are in the tree, or `HEAD` moved underneath you, do not record facts from them that you have not verified. Tell the user, and leave them to a `$ssot-doctor` catch-up.

## Steps

1. **List the candidates.** Go through the batch and look for:
   - decisions made, and alternatives the user rejected;
   - contracts, APIs, data formats, or behavior that users rely on and that changed;
   - traps you hit, with their cause;
   - build, test, release, or deploy commands that changed;
   - temporary workarounds added, with any established removal condition;
   - lasting directives from the user;
   - findings that will keep guiding work: a failed approach, an unexplained observation, a research result;
   - SSOT statements this work proved wrong;
   - protected rules found during the work that SSOT lacks (preflight section 3), as candidates.

   Before you decide there is nothing, open the owners that describe the parts this batch touched, plus any related problems preflight surfaced, and compare them with what is now true. A statement that is now wrong must be fixed or removed, even if the fact behind it could be recovered from the code. "Could be recovered from the code" only decides what to add, never what to leave wrong. If the owners still hold, write nothing: no logs, no timestamps, no "checked" markers. Say so in your report. If you already updated the owners during the work, that counts.
2. **Write each one in its single owner.** Use the README's routes and the model's layout. Update in place, in the present tense. Preserve accurate unaffected prose. Describe an accepted exception within its scope, retaining the rest of the rule and its status. Add a decision record for a consequential choice. Record a lasting user directive, or a departure from a protected rule that the user accepted, as its own confirmed row: its Source quotes the user's words and the date, and the row states only what those words decided. Clauses of an earlier candidate row that the user did not discuss stay in a candidate row; never move a clause of a confirmed row to candidate. Put the explanation in the owner the row links to. A one-time choice the user made goes to a decision record instead. Label anything decided but not built as planned.
3. **Remove what it supersedes.** Search `SSOT/` and the agent instruction files (`AGENTS.md`, `CLAUDE.md`) for older statements of the same fact (names, numbers, the old behavior) that still act as current guidance, and fix or delete them. A rule kept short in an instruction file and explained in `SSOT/` changes in both places. If you renamed or split a file or heading, fix the links to it across the repository. History keeps its meaning: in a past decision or research note, leave the old behavior as written, set a replaced decision's status to `superseded by NNNN`, and link the successor.
4. **Protect people's rules.** Change a confirmed invariant, or an accepted decision a person made, only on an explicit user decision. A decision in this conversation counts, and so does an earlier one that is already recorded and applies. Record it with its date. Without one, pause only the work that depends on the change, and ask. Record a departure from a protected rule as decided only when the approval rule in memory-model §5 is met, as step 2 says; otherwise report the conflict to the user, and do not record the new behavior as the truth.
5. **Check.** Check new or broader behavior claims, including final summaries, with the memory model's [claim check](../ssot-preflight/references/memory-model.md#checking-behavior-claims). The checker below checks structure, not truth. Unless this batch only edited the contents of files outside `SSOT/` (no file or heading added, moved, renamed, or deleted), run the checker that ships with `ssot-doctor`, passing the commit the batch started from (`HEAD` if nothing is committed yet): `python3 <ssot-doctor skill directory>/assets/scripts/ssot-check.py SSOT --since <commit>`. Fix the errors this batch introduced, plus any that affect what you wrote. A warning that a file this batch removed or moved is still mentioned points at a sentence that may now describe code that is gone: correct it if it does. Report other errors without fixing them, and do not present a scoped check as a clean bill for the whole SSOT. Then reread each changed passage as a newcomer would.
6. **Report.** Carry the checked input conditions into the final response. In your final response, name the SSOT files you changed and why. If you changed nothing, name the owners you compared and say why nothing in them became wrong or missing.

Put SSOT edits in the same commit as the change they describe, if the project's commit rules allow it. Committing and pushing follow the project's existing rules; this skill grants no extra authority.

You are done when every candidate is written to its owner or explicitly judged not durable, changed behavior claims agree with the evidence you checked, and, if step 5 ran the checker, it reports no errors in what this batch wrote. Errors elsewhere are reported, not fixed.
