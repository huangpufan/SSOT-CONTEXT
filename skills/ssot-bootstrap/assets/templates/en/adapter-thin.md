# SSOT instruction block

Add the block below to the repository's agent instruction file (`AGENTS.md`, `CLAUDE.md`, or the equivalent). If a block with these markers already exists, replace only the text between them.

<!-- SSOT-SKILL:BEGIN -->
## SSOT workflow

This repository routes its long-term memory through `SSOT/README.md` to canonical repository owners. Use the SSOT skills automatically; users describe tasks normally.

- **Start:** before substantive work (code, configuration, documentation, review, debugging, or planning), use `$ssot-preflight`.
- **Decision now:** when the user confirms, corrects, rejects, or limits a durable choice, use `$ssot-closeout` immediately, including discussion-only work; save and reread the decision before dependent work.
- **Finish:** before the final response or commit of a substantive change batch, use `$ssot-closeout`. It writes nothing when no durable fact changed.
- **Create or migrate:** use `$ssot-bootstrap`, only with the user's agreement.
- **Check or catch up:** use `$ssot-doctor` when asked, or when another SSOT skill routes there.

Skip these for non-repository chat, pure command runs, and typo or formatting edits. Before planning or changing behavior or architecture, use `$ssot-preflight` to identify protected outcomes, and preserve active registered invariants and protections admitted from evidence unless the user explicitly approves the identified departure. Use domain evidence: code and runtime for software behavior, canon and text for creative work, original sources for research, and the user’s words for decisions. Automatic upkeep depends on loaded skills and visible input; it cannot guarantee lossless capture. Commits and pushes follow this repository's existing rules. If an SSOT skill cannot be loaded, say so instead of guessing its steps.
<!-- SSOT-SKILL:END -->
