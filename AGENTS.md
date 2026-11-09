# AGENTS.md

> AGENTS.md should fit in the reader's working memory; if a section grows past comfortable reading, consolidate or demote before adding.

## What This Repo Is

SSOT-SKILL is a skill bundle that gives a project repository a small, maintained memory entered through `SSOT/README.md`, with repository-local knowledge owners: what the project is for, how it works, the rules people decided, why things are the way they are, and the traps. [DESIGN.md](./DESIGN.md) explains why it is shaped this way, including what version 3 removed. The bundle contains six skills:

| Skill | Role |
|-------|------|
| `ssot-preflight` | Read the relevant memory before substantive work |
| `ssot-bootstrap` | Create, continue, or migrate a repository's SSOT (with the user's agreement) |
| `ssot-closeout` | Capture accepted decisions immediately; reconcile durable changes at batch end |
| `ssot-doctor` | Check, review, or catch up SSOT |
| `ssot-audit` | Compatibility name; routes to Doctor's catch-up |
| `ssot-skill` | Compatibility name; routes to the four above |

## Install

When a user asks you to install or reinstall this bundle, follow [`INSTALL.md`](./INSTALL.md). The short form:

```bash
curl -fsSL https://raw.githubusercontent.com/huangpufan/SSOT-SKILL/main/install.sh | bash -s -- --quickstart
```

For upgrade or uninstall, see `bash install.sh --help`.

## Usage

In consuming repositories, complete the instruction wiring in [`INSTALL.md`](./INSTALL.md), then restart the agent session. Users describe tasks normally; the agent selects the matching skills automatically.

The consumer instruction block lives in the bootstrap adapter template ([English](./skills/ssot-bootstrap/assets/templates/en/adapter-thin.md), [中文](./skills/ssot-bootstrap/assets/templates/zh/adapter-thin.md)), between the `SSOT-SKILL:BEGIN` / `SSOT-SKILL:END` markers. The installer prints that same block; maintain its wording there. Each skill's `SKILL.md` owns the detailed protocol.

## Language

- Skill protocol text (`SKILL.md`, `references/`) is in English for routing accuracy.
- Bootstrap templates ship in both `en/` and `zh/`; the installer copies one language based on `--lang`.
- Consumer-facing `SSOT/` documentation follows the `language` in the consumer's `SSOT/README.md` front matter.

## Repo Boundaries

- `install.sh` is the installer entrypoint; change it only for the skill list, the agent registry, or how sources are fetched (`--ref`).
- `skills/*/SKILL.md` is the protocol authority for each skill; `skills/ssot-preflight/references/memory-model.md` owns the consumer memory model they share.
- Protocol changes follow [CONTRIBUTING.md](./CONTRIBUTING.md#changing-the-protocol), including the budgets CI enforces.
- `skills/ssot-bootstrap/assets/templates/{en,zh}/` contains template files; keep `en/` and `zh/` in file-name parity.
- `skills/*/agents/openai.yaml` must stay in sync with each skill.
- `VERSION` and `skills/ssot-preflight/SKILL.md` `metadata.protocol_version` must match (CI enforces).
- `CHANGELOG.md` follows Keep a Changelog format.

## Commit Discipline (Global)

This section applies to **maintainers operating against `origin/main` directly**. External contributors follow [`CONTRIBUTING.md`](./CONTRIBUTING.md) — that is the single entry point for community PRs.

Every modification to this repository — code, templates, docs, installer, tests — MUST end with `git commit && git push` to `origin/main` as the final step of the task. Do not leave changes in the working tree at the end of a turn.

- Direct commits to `main` are the established pattern for maintainers on this repo; external contributors go through `CONTRIBUTING.md` (branch + PR).
- Group related edits into a single commit per task; do not split into per-file commits.
- Commit message follows the `<type>: <subject>` form used in `git log` (e.g. `docs:`, `feat(protocol):`, `fix:`, `vX.YY (low|medium|high):` for protocol bumps).
- Run any relevant local check before committing (`bash tests/test-bundle-shape.sh` for shape, links, and budgets; `python3 tests/test-ssot-check.py` for checker changes; `bash tests/test-installer-e2e.sh` for installer changes); a failing check is a blocker, not a footnote.
- If the user explicitly says "don't push" or "stage only", that overrides this rule for that turn only — it does not change the default.

## Models for Development and Trials

Every model run that develops or tests SSOT Skill uses a cheap model: setup and migration runs, trial subjects, judges, reviewers, and helper agents. Claude models (the `claude` CLI, Claude subagents) and other expensive model tiers are not allowed for this work. The user named two that are allowed: `deepseek-v4.1-flash` through dsh, and `gpt-6.1-terra` through codex. Ask the user before using any other model whose cost is unclear. The maintainer session that coordinates the runs and judges their results is not covered by this rule (user directive, 2026-10-27).

## Writing Style (Global)

KISS is the permanent SSOT design principle: choose the shortest **reliable path to understanding**, not the fewest words. Keep one fact in one owner and make tables serve prose rather than replace it; never compress away the context, causal story, boundary, current path, failure behavior, or current-versus-planned distinction a cold reader needs. Every SSOT document the bundle generates is first written for the stranger who lands tonight knowing nothing. That reader may be the next agent, or a person who delegates implementation without reading code: lead with the situation, the decision, the result they should see and the evidence that shows it, then when to stop and ask; explain unavoidable terms before exact tokens, commands, paths, or codes. Tables, codes and tags the reader cannot interpret are not paragraphs. The same rules apply to this repository's own docs. [`writing-memory.md`](./skills/ssot-preflight/references/writing-memory.md) is the unique owner of the writing rules the bundle ships; templates and skills link to it rather than restating it.

## Key Files

| File | Purpose |
|------|---------|
| `DESIGN.md` | Why the bundle is shaped this way; what v3 removed and why |
| `install.sh` | Bundle installer (70+ agents; `--ref` selects a branch or tag) |
| `VERSION` | Bundle protocol version |
| `CHANGELOG.md` | Version history |
| `skills/*/SKILL.md` | Skill protocol and instructions |
| `skills/ssot-preflight/references/memory-model.md` | What consumer memory holds, its owners, and how it is written |
| `skills/ssot-bootstrap/references/bootstrap.md` | Creating an SSOT and preserving v2/v3 knowledge during migration |
| `skills/*/agents/openai.yaml` | Agent metadata for each skill |
| `skills/ssot-bootstrap/assets/templates/{en,zh}/` | Bootstrap templates |
| `skills/ssot-preflight/assets/scripts/read-context.py` | Read-only entry and using-memory reader |
| `skills/ssot-doctor/assets/scripts/ssot-check.py` | Read-only mechanical checker |
| `tests/` | Bundle shape and budgets, checker, installer, and diagram tests |
| `.github/workflows/ci.yml` | CI pipeline |
