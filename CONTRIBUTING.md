# Contributing to SSOT-CONTEXT

Thanks for your interest in improving the SSOT-CONTEXT bundle. Read [DESIGN.md](./DESIGN.md) first: it explains why the bundle is small and what it deliberately does not do.

## What lives where

| Area | Files | Review weight |
|---|---|---|
| Protocol | `skills/*/SKILL.md`, `skills/*/references/*.md`, templates | Protocol review (below) |
| Engineering | `install.sh`, `skills/*/assets/scripts/`, `tools/`, `tests/`, `.github/workflows/` | Standard review |
| Docs | `README*`, `INSTALL.md`, `DESIGN.md`, `CHANGELOG.md`, `docs/` | Standard review |

`skills/ssot-preflight/references/memory-model.md` owns development format 4 (`SSOT/`), `skills/ssot-preflight/references/context-spaces.md` owns general-space format 5, and `skills/ssot-preflight/references/writing-memory.md` owns the writing rules the bundle ships. The `SKILL.md` files and templates link to those owners rather than restating them.

### Naming files in `docs/`

Start each filename with the date it first enters the repository (`YYYY-MM-DD`), then a short lowercase English topic with words separated by hyphens. To identify a release, append the version before the extension, as in `2026-11-21-skill-discovery-cost-v5.15.md`. For a second report on the same topic that day, add a qualifier such as `round-2`. Use a lowercase file extension and keep the original date when revising a document so its links stay stable.

## Changing the protocol

Every protocol change answers four questions in its pull request:

1. **Does this belong in a general protocol?** A rule specific to one project belongs in that project. A problem caused by a template is fixed in the template, and a tool bug is fixed in the tool. Do not turn one mistake into a new duty for every repository.
2. **What does it replace?** Name the duty it adds, merges, or removes. Adding is allowed when nothing existing can carry it. Explain why, and keep within the budgets.
3. **How was it verified, at the level of its impact?** A wording fix needs the structural tests. A local rule needs a scenario where it should apply and a nearby one where it should not. A change to what agents read or write by default needs a baseline/candidate trial on real tasks that records wrong decisions, false triggers, reading, and writing.
4. **What is the net effect on whole tasks?** Fixing one case while making every unrelated task read or write more is not an improvement.

Do not claim more than you ran. A structural test does not show that agents behave better.

### Writing a SKILL.md

An entrypoint lets an agent pick the right branch, find its instructions, respect its boundaries, and know when it is done. Keep:

- the purpose and the condition for being done;
- routing, with links that say when to read them;
- ordered steps where the order affects safety or correctness;
- permission, ownership, and recovery rules the agent needs before choosing a route.

Detailed shared material belongs in a reference, read at the point of use. `SKILL.md` and `references/` are in English, the language skill routing is tuned for.

### Protocol budgets

`tests/test-bundle-shape.sh` enforces these limits in CI, separating the always-loaded prompt surface, model-read protocol text, and executable scripts:

| What | Limit |
|---|---|
| Always-loaded core-4 skill catalog (`SKILL.md` frontmatter `name + description`) | 600 bytes |
| Always-loaded full-6 skill catalog (including legacy compatibility shims) | 768 bytes |
| Managed instruction block (`en`/`zh`, format 4/5, between markers) | 1,600 bytes each |
| All `SKILL.md` files together | 3,600 words |
| Hot-path runtime protocol (core-4 `SKILL.md` + daily references) | 10,200 words |
| Conditional/cold runtime branches (setup, migration, spaces, source, review, legacy shims) | 11,600 words |
| Templates, per language | 16 KiB |
| Runtime assets (`skills/` excluding Python scripts) | 184 KiB |
| `ssot-check.py` | 96 KiB |
| All bundle scripts (`skills/*/assets/scripts/*.py`) | 128 KiB |
| All of `skills/` | 312 KiB |

Following the [Stage 5 real-session audit](docs/2026-11-24-real-session-stage5-audit.md), the CI budget ruler separates always-loaded prompt surfaces (core-4/full-6 discovery catalogs and managed adapter blocks), model-read protocol text (exhaustively partitioned into hot-path core-4 + daily references and conditional/cold branches including opt-in legacy shims, plus runtime assets), and non-model-read executable scripts. Models run `ssot-check.py` and `context-source.py` via CLI rather than loading their source into context, so the executable script ceilings were decoupled to 96 KiB / 128 KiB while keeping v3's anti-400KB-linter boundary. In `5.23`, the hot-path (`10,200` words), conditional/cold (`11,600` words), runtime-asset (`184 KiB`), and disjoint `skills/` total (`312 KiB = 184 KiB + 128 KiB`) ceilings were dynamically adjusted based on two-round frozen counterbalanced paired trial evidence ([5.23 auto-compaction and layering study](docs/2026-11-26-auto-compaction-layering-v5.23.md) and [CHANGELOG.md](./CHANGELOG.md)), while always-loaded prompt surfaces (catalogs, managed blocks), `SKILL.md` entrypoints, templates, and executable script caps remained unchanged.

A budget is a reason to rethink responsibilities, never a reason to cut a recovery or authorization branch to fit, and never a reason to rewrite unrelated rule text to make room: such edits are untested changes. A v2 word cap once rejected a complete entrypoint for being complete. Raising a limit requires the same evidence as adding a rule; record the reason in `CHANGELOG.md`.

## Versions

`VERSION` and `metadata.protocol_version` in `skills/ssot-preflight/SKILL.md` must match; CI checks this. Bump the minor version for protocol changes and add a `CHANGELOG.md` entry. The consumer data format (`ssot_format` in `SSOT/README.md`) changes only when existing SSOTs would otherwise be misread. That needs a major version and a migration path in `ssot-bootstrap`.

## Templates

Templates under `skills/ssot-bootstrap/assets/templates/{en,zh}/` are copied into consumer repositories. Keep both languages in file-name parity. They are prompts for prose, not forms: avoid tables that invite one-word cells, and in Mermaid diagrams use `%%` comments, never HTML comments.

## README reconciliation

Before completing or committing any repository change, compare the resulting behavior with `README.md` and `README.zh.md` without waiting for a user reminder. Update both in the same change when it affects the bundle's purpose or capabilities, normal usage, installation, upgrade, uninstall, migration, recovery, prerequisites, compatibility or material limitations. Keep `README.md` and `README.zh.md` readable for a newcomer: summarize the current workflow and primary boundaries on the front page, and keep release-specific edge cases, CLI flags, and trial numbers in their authoritative reference documents and `CHANGELOG.md` instead of appending footnotes to the opening paragraphs.

This check is complete when both READMEs describe the verified current behavior, agree in meaning, and their affected links and commands match the authoritative guides. Internal refactors, test-only changes and typo fixes can leave them untouched when the existing user-facing description remains accurate.

## Local verification

```bash
bash tests/test-bundle-shape.sh        # shape, links/anchors, hygiene, budgets
python3 tests/test-ssot-check.py       # checker regression tests
python3 -m unittest discover -s tests/benchmark -p 'test_*.py' # outcome, observer and handoff calibration; no model calls
python3 tests/test-migration-trials.py # migration fixtures, oracle and CI billing guard; no model calls
python3 tests/test-context-source.py   # POSIX source/owner/readback contract; no model calls
python3 -m unittest discover -s tests/context -p 'test_*.py' # general-context, source CLI, continuation, register, tiering and longchain tests; no model calls
python3 tests/test-local-links.py      # tools/link-local.py symlink plan, backup and rollback tests
python3 tests/test-precommit-hook.py   # tools/ssot-precommit.sh zero-token Git pre-commit guard tests
bash tests/test-installer-e2e.sh       # installer end to end
python3 tests/test-installer-recovery.py # replacement faults, cancellation, locking and recovery
shellcheck -S warning -e SC2034 install.sh tests/*.sh tools/*.sh
```

The recovery tests invoke Bash 4+ from `PATH`; on macOS, set `SSOT_TEST_BASH="$(brew --prefix)/bin/bash"` when the default `bash` is older.

For opt-in native evaluation and feedback cycles, use [the benchmark guide](./tests/benchmark/README.md), including its outcome coverage map, reading comparisons and cold handoff with plain-docs controls. It runs billable models only when explicitly invoked; CI compiles it without running trials.

For old-format migration and read-only behavior, [the 4.5 trial guide](./tests/trials-4.5.md) documents the separate opt-in native scenarios. [Continuity trials](./tests/trials-continuity.md) add v2 extraction, incompatible-writer refusal, partial decision correction and an observed process interruption. They check transitions, not performance.

For diagram changes, install `mermaid@11.12.0` and `jsdom@26.1.0` into an isolated npm prefix, then run `node tests/test-mermaid-templates.mjs <prefix>/node_modules`.

## Pull request checklist

- [ ] The four protocol questions are answered (protocol changes only)
- [ ] Local verification passes, including budgets
- [ ] `VERSION` and `CHANGELOG.md` updated for protocol changes
- [ ] `en/` and `zh/` templates updated together
- [ ] [README reconciliation](#readme-reconciliation) assessed; required updates included

## Code of conduct

Be kind. Surface disagreements with evidence and proposed alternatives, not broad rejection.
