# Contributing to SSOT-CONTEXT

Thanks for your interest in improving the SSOT-CONTEXT bundle. Read [DESIGN.md](./DESIGN.md) first: it explains why the bundle is small and what it deliberately does not do.

## What lives where

| Area | Files | Review weight |
|---|---|---|
| Protocol | `skills/*/SKILL.md`, `skills/*/references/*.md`, templates | Protocol review (below) |
| Engineering | `install.sh`, `skills/*/assets/scripts/`, `tests/`, `.github/workflows/` | Standard review |
| Docs | `README*`, `INSTALL.md`, `DESIGN.md`, `CHANGELOG.md` | Standard review |

`skills/ssot-preflight/references/memory-model.md` owns what a consumer's `SSOT/` contains and how it is written. The `SKILL.md` files link to it rather than restating it.

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

`tests/test-bundle-shape.sh` enforces these limits in CI:

| What | Limit |
|---|---|
| All `SKILL.md` files together | 3,600 words |
| Everything an agent may read at runtime (`SKILL.md` + `references/`) | 14,000 words |
| Templates, per language | 16 KiB |
| `ssot-check.py` | 50 KiB |
| All of `skills/` | 160 KiB |

Version 4.0 raises entrypoints to 3,600 words, runtime protocol to 13,000 words, and the checker to 48 KiB for immediate decision capture, accessible conversation-source recovery, external-owner routes, preservation-aware migration, and checks on those routes. Measured template and whole-bundle sizes fit their existing limits, which remain unchanged.

Version 4.1 raises only the runtime limit to 13,800 words. Real adoption and behavior trials exposed boundaries between formal acceptance, original-source verification and capture dates, plus mixed-task Doctor routing. A notification lifecycle counterexample also requires a scoped structural-review reference: contracts and code define the cases, while evidence must observe the relevant transitions and sequences. Keep the necessary context rather than cutting unrelated authorization or recovery rules; all other limits remain unchanged.

Version 4.4 raises the runtime limit to 14,000 words for native reading, stale-route recovery and conditional section navigation. The changed routing adds 82 words; no unrelated authorization, recovery or writing rules were shortened. The benchmark measures this reading policy independently from index changes; its evidence and limits are recorded with the release. Other budgets remain unchanged.

A budget is a reason to rethink responsibilities, never a reason to cut a recovery or authorization branch to fit, and never a reason to rewrite unrelated rule text to make room: such edits are untested changes. In 3.5 the owner raised the limits from 3,000 and 8,000 words, with room left on purpose, after a trial branch had tightened about 40 unrelated sentences to fit new rules into the old limits; in 3.7 the owner raised the runtime limit from 9,500 to 10,000 words for the mining changes, instead of cutting other rules; in 3.9 the owner raised the checker limit from 40 to 44 KiB for the check on confirmed invariants; in 3.10 the owner raised the runtime limit from 10,000 to 11,000 words for the row-fixing step in mining. A v2 word cap once rejected a complete entrypoint for being complete. Raising a limit requires the same evidence as adding a rule. Record the reason in `CHANGELOG.md`.

## Versions

`VERSION` and `metadata.protocol_version` in `skills/ssot-preflight/SKILL.md` must match; CI checks this. Bump the minor version for protocol changes and add a `CHANGELOG.md` entry. The consumer data format (`ssot_format` in `SSOT/README.md`) changes only when existing SSOTs would otherwise be misread. That needs a major version and a migration path in `ssot-bootstrap`.

## Templates

Templates under `skills/ssot-bootstrap/assets/templates/{en,zh}/` are copied into consumer repositories. Keep both languages in file-name parity. They are prompts for prose, not forms: avoid tables that invite one-word cells, and in Mermaid diagrams use `%%` comments, never HTML comments.

## README reconciliation

Before completing or committing any repository change, compare the resulting behavior with `README.md` and `README.zh.md` without waiting for a user reminder. Update both in the same change when it affects the bundle's purpose or capabilities, normal usage, installation, upgrade, uninstall, migration, recovery, prerequisites, compatibility or material limitations. Keep detailed procedures and evidence in their existing owners and link to them from the READMEs.

This check is complete when both READMEs describe the verified current behavior, agree in meaning, and their affected links and commands match the authoritative guides. Internal refactors, test-only changes and typo fixes can leave them untouched when the existing user-facing description remains accurate.

## Local verification

```bash
bash tests/test-bundle-shape.sh        # shape, links, budgets
python3 tests/test-ssot-check.py       # checker regression tests
python3 tests/benchmark/test_benchmark.py # benchmark oracle and accounting; no model calls
python3 tests/test-migration-trials.py # migration fixtures, oracle and CI billing guard; no model calls
bash tests/test-installer-e2e.sh       # installer end to end
python3 tests/test-installer-recovery.py # replacement faults, cancellation, locking and recovery
shellcheck -S warning -e SC2034 install.sh tests/*.sh
```

The recovery tests invoke Bash 4+ from `PATH`; on macOS, set `SSOT_TEST_BASH="$(brew --prefix)/bin/bash"` when the default `bash` is older.

For opt-in native performance comparisons, use [the reading benchmark](./tests/benchmark/README.md). It runs billable models only when explicitly invoked; CI compiles it without running trials.

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
