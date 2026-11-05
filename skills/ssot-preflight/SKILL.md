---
name: ssot-preflight
description: Read the repository's SSOT before substantive work. Use this before code, config, documentation, review, debugging, refactoring, or planning work in a repository, to find the invariants and documents that bear on the task and to surface open questions that affect it. Skip it for non-repository chat, pure command runs, and typo or formatting edits that cannot change meaning.
metadata:
  protocol_version: "3.13"
  bundle: "SSOT Skill"
---

# SSOT Preflight

Before substantive work, find out what the repository's memory says about the task. Read [`references/memory-model.md`](references/memory-model.md), which explains what `SSOT/` holds and what the invariants register means, the first time you use SSOT in a session.

## 1. Find the entry point

- **No `SSOT/` directory.** Tell the user the repository has no SSOT and offer to create one with `$ssot-bootstrap`. Setup writes a documentation tree and can take more than one session, so it needs the user's yes. If they decline or defer, do the task without the SSOT steps, and do not offer again this session.
- **`SSOT/BOOTSTRAP.md` exists.** Setup is unfinished. Offer to continue it, and meanwhile use what is already written.
- **`SSOT/README.md` has no `ssot_format: 3`.** This SSOT predates v3: usually the v2 layout with `SSOT/STATUS.md`, sometimes a hand-written one. Read it as knowledge. Its coverage labels and review records are historical, but its adjudications, user constraints, limits, and open questions that bear on the task still bind you. Do not write to it. Tell the user once that `$ssot-bootstrap` can migrate it or set it up in the v3 format.

## 2. Read what this task needs

Read `SSOT/README.md`, then:

1. **Invariants.** Find the rows whose rule this task could affect, and read the explanation each one links to. Section 3 says what to do when the change could break one.
2. **Open questions.** If one blocks the path this task needs, say so. Only the work that depends on the answer waits; unrelated work goes ahead.
3. **Known traps and limits.** Read the gotchas and the known gaps that touch the parts you will change, and handle each one: fix it, work around it deliberately, or say why it does not apply.
4. **Routes.** Read the files the task routes point to. If no route fits, read the product and architecture entry documents. Do not read the whole tree.
5. **What you rely on.** When an SSOT statement decides how you will implement something, check it against the code first. If they disagree, the code is the current behavior. Note the mismatch so closeout fixes the document, or so you can report the violation.

## 3. Find what the change must preserve

Before you settle on an implementation, identify the behaviors and boundaries the change could affect: their SSOT owners, the tests that assert them, boundary checks and guards, and the fix or revert history of the code involved. Follow callers and shared state where effects cross files. Tell a protected outcome from an incidental detail with the admission and departure rules in [memory-model.md §5](references/memory-model.md#5-invariants).

Before implementation details, state each affected rule, registered or newly admitted: "Must preserve: [outcome and conditions] — [evidence]." Compare the request with these rules. For a concrete conflict, propose a preserving design that meets the request, or pause and ask whether to change the protection, naming who relies on it and the consequence. A request naming the new behavior is not approval; the user may not know the protection exists. Approval counts only when the user's words accept giving up that protection, previously or now. Continue independent work. Record missing rules as candidates through closeout.

## 4. Before your first change, and while you work

If the user has stated a lasting rule ("from now on", "never", "always"), or settled a decision whose reason exists only in the conversation, write it to its owner before you change anything else, and again whenever the user settles one later. Follow closeout's rules for where and whether SSOT may be written, and label what the code does not do yet as planned. These do not wait for closeout: an interrupted or compacted session loses them, and the code never shows them. An idea still under discussion is not settled.

Watch for the other facts that will outlive the task: decisions, changed contracts or behavior that users rely on, traps you hit, changed commands, and temporary workarounds. Note them as they come up; `$ssot-closeout` records them before you finish, and you may update an obvious owner right away.

## Where to go next

| Situation | Skill |
|---|---|
| No SSOT yet, setup unfinished, or a v2 layout to migrate | `$ssot-bootstrap` |
| Finishing a substantive batch, before the final response or commit | `$ssot-closeout` |
| Health check, a review, or catching up on past commits | `$ssot-doctor` |
