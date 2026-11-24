# Contributing to SSOT-CONTEXT

Thanks for your interest in improving the SSOT-CONTEXT bundle. Read [DESIGN.md](./DESIGN.md) first: it explains why the bundle is small and what it deliberately does not do.

## What lives where

| Area | Files | Review weight |
|---|---|---|
| Protocol | `skills/*/SKILL.md`, `skills/*/references/*.md`, templates | Protocol review (below) |
| Engineering | `install.sh`, `skills/*/assets/scripts/`, `tests/`, `.github/workflows/` | Standard review |
| Docs | `README*`, `INSTALL.md`, `DESIGN.md`, `CHANGELOG.md`, `docs/` | Standard review |

`skills/ssot-preflight/references/memory-model.md` owns what a consumer's `SSOT/` contains and how it is written. The `SKILL.md` files link to it rather than restating it.

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
| Hot-path runtime protocol (`SKILL.md` + daily core references) | 9,200 words |
| Conditional/cold runtime branches (setup, migration, spaces, source, review) | 10,400 words |
| Templates, per language | 16 KiB |
| Runtime assets (`skills/` excluding Python scripts) | 160 KiB |
| `ssot-check.py` | 64 KiB |
| All bundle scripts (`skills/*/assets/scripts/*.py`) | 96 KiB |
| All of `skills/` | 248 KiB |

Version 4.0 raises entrypoints to 3,600 words, runtime protocol to 13,000 words, and the checker to 48 KiB for immediate decision capture, accessible conversation-source recovery, external-owner routes, preservation-aware migration, and checks on those routes. Measured template and whole-bundle sizes fit their existing limits, which remain unchanged.

Version 4.1 raises only the runtime limit to 13,800 words. Real adoption and behavior trials exposed boundaries between formal acceptance, original-source verification and capture dates, plus mixed-task Doctor routing. A notification lifecycle counterexample also requires a scoped structural-review reference: contracts and code define the cases, while evidence must observe the relevant transitions and sequences. Keep the necessary context rather than cutting unrelated authorization or recovery rules; all other limits remain unchanged.

Version 4.4 raises the runtime limit to 14,000 words for native reading, stale-route recovery and conditional section navigation. The changed routing adds 82 words; no unrelated authorization, recovery or writing rules were shortened. The benchmark measures this reading policy independently from index changes; its evidence and limits are recorded with the release. Other budgets remain unchanged.

Version 5.0 sets 17,000 runtime words and 220 KiB of skills for a conditional general-space model and source-state/readback reference adapter. Existing development format 4, protection and recovery text remains; general spaces use format 5 so old writers that discover them take their read-only branch. Added references are reached only for relevant tasks. The coordinator accepted the observed bounded cost tradeoff for this release after native quality/reading review; this is not a user statement accepting higher costs or a performance-improvement claim. See the [native result account](tests/context/results/context-evolution-5.0-2026-11-10.json) and [implementation report](tests/trials-5.0.md). Entrypoint, template and checker limits remain unchanged; a size pass alone is never a behavioral release gate.

Version 5.4 allows 18,000 runtime words for conditional context tiering and shared reconciliation of changed guidance across formats 4 and 5. It replaces the development-only supersession recipe rather than duplicating it, keeps consolidation off ordinary task paths, and retains existing authorization/recovery text. Other budgets and consumer formats stay unchanged. Whole-task trials and their cost limits are recorded in [the 5.4 report](tests/context/trials-5.4.md); the ceiling is not a performance claim.

Version 5.9 allows 52 KiB for the checker and 223 KiB for the bundle. The former limits left 77 and 70 bytes respectively. A real checker run opened a withdrawn Markdown original through a retained link. The additional code bounds document and anchor reads to an explicit selection and reports its coverage. The agent reading budgets stay fixed. See the [checks and tradeoffs](docs/2026-11-20-catchup-v5.9.md).

Version 5.10 allows 18,500 runtime words, 53 KiB for the checker and 227 KiB for the bundle. The runtime additions route goal and preference capture, task handoff and selected checks in both formats. The checker adds selected format-4 owners within its existing repository boundary. These are distribution ceilings. The [release evidence](docs/2026-11-20-context-lifecycle-v5.10.md) describes what the agent actually used and the limits of the cost comparison.

Version 5.12 allows 18,700 runtime words and 232 KiB for the bundle. Version 5.11 had 139 words and 55 bytes of headroom. Conditional decision use, recovery of premise-dependent progress and metadata-only withdrawal use existing owners. The connector also protects a restricted withdrawal from older readers. The [release study](docs/2026-11-20-conditional-context-v5.12.md) accounts for behaviour and cost on both changed and ordinary tasks.

On 2026-11-24, following the [Stage 5 real-session audit](docs/2026-11-24-real-session-stage5-audit.md), the CI budget ruler was decoupled in two steps: first separating always-loaded surfaces (768 B full catalog, 1,600 B per managed adapter block), model-read runtime assets (160 KiB), and executable scripts (`ssot-check.py` 64 KiB, all scripts 96 KiB, overall `skills/` 248 KiB); then separating the flat 18,700-word cliff (99.6% full after 5.17, with 4,178 words in low-frequency `migration.md`, `area-mining.md`, and `source-integration.md`) into explicit hot-path (9,200 words, covering all `SKILL.md` entrypoints plus daily preflight/departure/closeout references) and conditional/cold-branch (10,400 words) ceilings alongside a 600 B cap on the default core-4 skill discovery catalog. The total runtime-assets byte cap (160 KiB) stays unchanged, and an exhaustive partition check prevents any new reference file from bypassing the word caps.

A budget is a reason to rethink responsibilities, never a reason to cut a recovery or authorization branch to fit, and never a reason to rewrite unrelated rule text to make room: such edits are untested changes. In 3.5 the owner raised the limits from 3,000 and 8,000 words, with room left on purpose, after a trial branch had tightened about 40 unrelated sentences to fit new rules into the old limits; in 3.7 the owner raised the runtime limit from 9,500 to 10,000 words for the mining changes, instead of cutting other rules; in 3.9 the owner raised the checker limit from 40 to 44 KiB for the check on confirmed invariants; in 3.10 the owner raised the runtime limit from 10,000 to 11,000 words for the row-fixing step in mining. A v2 word cap once rejected a complete entrypoint for being complete. Raising a limit requires the same evidence as adding a rule. Record the reason in `CHANGELOG.md`.

## Versions

`VERSION` and `metadata.protocol_version` in `skills/ssot-preflight/SKILL.md` must match; CI checks this. Bump the minor version for protocol changes and add a `CHANGELOG.md` entry. The consumer data format (`ssot_format` in `SSOT/README.md`) changes only when existing SSOTs would otherwise be misread. That needs a major version and a migration path in `ssot-bootstrap`.

## Templates

Templates under `skills/ssot-bootstrap/assets/templates/{en,zh}/` are copied into consumer repositories. Keep both languages in file-name parity. They are prompts for prose, not forms: avoid tables that invite one-word cells, and in Mermaid diagrams use `%%` comments, never HTML comments.

## README reconciliation

Before completing or committing any repository change, compare the resulting behavior with `README.md` and `README.zh.md` without waiting for a user reminder. Update both in the same change when it affects the bundle's purpose or capabilities, normal usage, installation, upgrade, uninstall, migration, recovery, prerequisites, compatibility or material limitations. Keep `README.md` and `README.zh.md` readable for a newcomer: summarize the current workflow and primary boundaries on the front page, and keep release-specific edge cases, CLI flags, and trial numbers in their authoritative reference documents and `CHANGELOG.md` instead of appending footnotes to the opening paragraphs.

This check is complete when both READMEs describe the verified current behavior, agree in meaning, and their affected links and commands match the authoritative guides. Internal refactors, test-only changes and typo fixes can leave them untouched when the existing user-facing description remains accurate.

## Local verification

```bash
bash tests/test-bundle-shape.sh        # shape, links, budgets
python3 tests/test-ssot-check.py       # checker regression tests
python3 -m unittest discover -s tests/benchmark -p 'test_*.py' # outcome, observer and handoff calibration; no model calls
python3 tests/test-migration-trials.py # migration fixtures, oracle and CI billing guard; no model calls
python3 tests/test-context-source.py  # POSIX source/owner/readback contract; no model calls
python3 tests/context/test_context.py # general-context fixtures/oracles; no model calls
python3 tests/context/test_source_contract.py # independent source CLI contracts; no model calls
python3 tests/context/test_continuation.py # continuation oracle; no model calls
python3 tests/context/test_register.py # large-register outcomes; no model calls
python3 tests/context/test_source_oracle.py # public source-state oracle; no model calls
bash tests/test-installer-e2e.sh       # installer end to end
python3 tests/test-installer-recovery.py # replacement faults, cancellation, locking and recovery
shellcheck -S warning -e SC2034 install.sh tests/*.sh
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
