---
name: ssot-bootstrap
description: Create, continue or migrate maintained context with the user's agreement. Use for a repository's missing or unfinished SSOT, an agreed legacy migration, or explicit setup of a bounded general context space. Retain canonical owners and current development format 4; ordinary non-repository conversation does not trigger setup. Do not use for normal preflight or closeout.
---

# SSOT Bootstrap

Inspect the explicit entry or default `SSOT/README.md`: 5 uses [general context spaces](../ssot-preflight/references/context-spaces.md), especially Bootstrap; 4 keeps the repository route below; known v2/v3 keeps its agreed migration route. Unknown/future formats stay read-only without downgrade. Explicit new general-space setup uses the general branch without Git or non-software mining requirements. Ordinary undeclared chat/research/creation skips this skill; a bundle upgrade never requires format conversion.

Build the repository’s memory from domain evidence, existing canonical documents, history and available user decisions. A filled template is not knowledge. What to store and how to write it is defined in [`memory-model.md`](../ssot-preflight/references/memory-model.md).

Setup writes a documentation tree and may edit existing documents, so it needs the user's agreement first. Tell them what you will create and which existing files you expect to change.

For new or unfinished repository setup, follow the [setup guide](references/bootstrap.md), starting from any saved `BOOTSTRAP.md`. Its [mining plan and dispatch gate](references/mining.md#1-declare-the-scope-before-mining) use compact review for bounded units with an existing usable owner. Use distributed mining when a usable guide must be reconstructed across sources, the scope is larger or authority is disputed.

For an agreed [v2 or v3 migration](references/migration.md), follow the matching section, including when the progress file identifies an unfinished migration.

You are done when all of these hold:

- the saved README identifies the completed setup scope and routes the repository's main tasks to usable owners;
- the mining report accounts for the sources, independently checked rules, cold handoff and remaining scope;
- every document you wrote matches its domain evidence (memory-model §3);
- durable facts have one maintained owner, reachable from `SSOT/`, with existing canonical owners retained;
- the candidate invariants, the open questions, and the planned changes outside `SSOT/` have been put to the user;
- the checker reports no errors;
- `SSOT/BOOTSTRAP.md` has been removed.

If you have to stop earlier, `BOOTSTRAP.md` must say what is done and what comes next.
