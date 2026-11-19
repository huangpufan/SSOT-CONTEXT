# SSOT instruction block

Add the block below to the repository's agent instruction file (`AGENTS.md`, `CLAUDE.md`, or the equivalent). If a block with these markers already exists, replace only the text between them.

<!-- SSOT-CONTEXT:BEGIN -->
## SSOT workflow

Use the SSOT skills automatically for this repository. Users describe tasks normally.

- **Start:** for substantive work (code, configuration, documentation, review, debugging, or planning), load `$ssot-preflight` before opening `SSOT/README.md`. Start the entry with its header and headings.
- **Decision now:** when the user settles or revises a durable goal, preference, or decision, use `$ssot-closeout` immediately, including discussion-only work; save and reread the decision before dependent work.
- **Finish or hand off:** use `$ssot-closeout` for an authorized task handoff or before the final response or commit of a substantive change batch. Routine no-change closeouts write nothing.
- **Create or migrate:** use `$ssot-bootstrap`, only with the user's agreement.
- **Check or catch up:** use `$ssot-doctor` when asked, or when another SSOT skill routes there.

Skip these for non-repository chat, pure command runs, and typo or formatting edits. Before planning or changing behavior or architecture, use `$ssot-preflight` to identify protected outcomes, and preserve active registered invariants and protections admitted from evidence unless the user explicitly approves the identified departure. Use domain evidence: code and runtime for software behavior, canon and text for creative work, original sources for research, and the user’s words for decisions. Automatic upkeep depends on loaded skills and visible input; it cannot guarantee lossless capture. Commits and pushes follow this repository's existing rules. If an SSOT skill cannot be loaded, say so instead of guessing its steps.
<!-- SSOT-CONTEXT:END -->
