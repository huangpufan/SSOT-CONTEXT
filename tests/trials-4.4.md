# 4.4: native Markdown reading and a reusable benchmark

This change removes the dedicated preflight reader, retains the separate layout/writing/departure references, and strengthens existing task routes. Agents use ordinary file tools to read owner sections and related constraints, with product/architecture discovery when routes are absent or stale. Consumer format remains 4. No consumer migration, installed cache or new index file is required.

The user approved this direction and requested a reusable reading benchmark. A design discussion through Claude Code explicitly selected `sonnet`; the native response identified `claude-sonnet-5-5`. This was design critique, not behavior evidence. Its findings led to independent task fixtures, isolated sessions, complete executable tasks, separate quality verdicts, counterbalanced attempts and native per-turn accounting. Live benchmark subjects use only `gpt-6.1-terra` with medium reasoning.

## Protocol scope

The change belongs in the general reading path: Markdown owners remain usable with ordinary tools, while routes identify the relevant question and expansion condition. It replaces the reader command and its special refresh option. Layout and template changes refine the existing task-route table instead of adding another catalog. Invariant, source-evidence, immediate capture and protected-departure procedures retain their owners and semantics. The runtime budget rises from 13,800 to 14,000 words for 82 added routing words; unrelated rules were not compressed. Total installed skill bytes fall when the reader is removed.

Verification separates the protocol comparison from an index-only comparison, as described in the [benchmark guide](benchmark/README.md). Source hashes, task trees, prompts, runner, execution order and raw native receipts are frozen per experiment. No favorable earlier run substitutes for a final result.

## Experiments

Baseline: `6b05fe1` (4.3). The release candidate uses the staged task files with the original checker; a concurrent checker task is excluded. The local evidence directory is `/var/tmp/ssot-benchmark-44-4u7knkfy`. Native Codex CLI 0.167.0 runs serially with medium reasoning and an isolated home per attempt. Correct task outcomes, completion time and total input/output are the primary measures; cache and tool statistics are auxiliary diagnostics. Costs below are native per-turn values; warm rows sum both turns. Cached input is included in total input, and uncached input is reported separately. None of these numbers is a financial bill.

### Protocol comparison

Both arms receive identical task documents and indexes. Each of five cases has two repetitions: 20 attempts, 24 turns, all passing the independent code/file-scope oracle. The table shows each arm's per-case median. Two observations per case are pipeline evidence, not a statistical estimate.

| Case | Seconds, 4.3 → 4.4 | Input tokens | Uncached input | Tool items |
| --- | ---: | ---: | ---: | ---: |
| Matching route | 42.462 → 41.638 | 146,633.5 → 158,742.5 | 15,945.5 → 24,150.5 | 9.5 → 14 |
| No matching route | 38.010 → 51.437 | 142,447 → 149,850 | 12,079 → 16,538 | 9 → 14 |
| Stale route | 44.446 → 50.166 | 159,090.5 → 141,163.5 | 19,186.5 → 18,987.5 | 11 → 15.5 |
| Same-session policy update, both turns | 89.826 → 72.769 | 305,957 → 278,441.5 | 19,429 → 26,089.5 | 18 → 22 |
| Typo only | 11.648 → 10.634 | 45,457 → 45,481 | 4,753 → 4,649 | 2 → 2 |

Across the observed tasks, total time is 452.783 → 453.287 seconds; total input is 1,599,170 → 1,547,357; uncached input is 142,786 → 180,829. Time is effectively unchanged in this sample, total input falls about 3.2%, and uncached input rises about 26.6%. Native reads use more tool calls on substantive tasks. Removing the reader simplifies the interface; these observations do not show a general speed or billing improvement.

This campaign alternated the arms globally after shuffling pairs, which did not balance first-arm order within each task class. The producer was corrected to alternate by repetition within each case, with a multi-case regression test. The completed protocol observations remain recorded with that ordering limitation; they were not rerun to seek more favorable numbers. The separate index campaign uses the corrected schedule.

### Index-only comparison

Both arms use byte-identical 4.4 skills and owner content, differing only in README task routes. Three repetitions produce six passing attempts. Arm order alternates within the case. All three paired observations have lower elapsed time and total input with direct section routes; the medians below are descriptive.

| Metric | Coarse routes | Direct section routes |
| --- | ---: | ---: |
| Seconds | 41.365 | 38.472 |
| Input tokens | 142,783 | 136,546 |
| Uncached input | 15,024 | 12,316 |
| Output tokens | 1,409 | 1,540 |
| Tool items | 9 | 14 |
| Returned tool bytes | 30,451 | 30,541 |

The paired time reductions are 5.060, 2.893 and 0.555 seconds. Total input over the three tasks falls from 435,800 to 416,018. Uncached input is uneven: its total rises from 42,456 to 45,714 even though its median falls. More tool calls coexist with lower elapsed time, so call count alone is not a speed measure. These observations support further testing of useful direct routes; they do not establish that more indexes generally improve performance or reduce billing.

[Machine-readable observations](benchmark/results-4.4.json) retain all 26 release attempts, 30 turns, per-turn costs, quality checks, reading observations, source/runner digests and native receipt hashes. Every substantive turn has a successful supplied-test receipt; candidate traces contain no dedicated-reader command. The complete raw records remain in the local evidence directory. Reproduce with the commands in the benchmark guide; provider variation means a new run need not reproduce these exact numbers.

## Behavior and limits

| State or sequence | Observation in the protocol campaign |
| --- | --- |
| Matching route → contract and related eligibility owner → implementation | All four runs preserve standard behavior, regional prices, threshold edges, digital exceptions and invalid-service handling. |
| No matching route → entry documents and owner discovery | All four runs reach the accepted contract and pass the same independent checks. |
| Missing route target, with an obsolete proposal also present | All four runs implement current accepted behavior; policy files remain unchanged as requested. |
| Completed task → dirty tracked owner plus new routed untracked owner, same HEAD → resumed task | Both arms in both repetitions apply the new threshold and preserve the other rules. Native returned text contains the new promotion passage. |
| Typo-only task | All four runs change only the requested word; no preflight text is observed in returned command output. |

The fixture uses one synthetic code domain and an injected adapter. It does not test installed-skill discovery, production-scale repositories, bootstrap/migration, new-decision capture, actual protected-departure approval, unrelated dirty-state costs or other models. The shared memory model, writing reference and protected-departure body are byte-identical to 4.3; textual preservation is not a new behavior trial of those unrun branches. Cache/provider variation and the small samples limit performance conclusions.

A preliminary two-attempt smoke test is retained separately. Another campaign was stopped after its candidate snapshot was found to include the parallel task's unstaged checker changes; its traces and exclusion reason remain in `protocol/`. Release observations use the isolated staged snapshot in `protocol-final/`. No frozen source or failed/interrupted output was overwritten.

Local validation of this task's isolated candidate passed 48 bundle checks, 114 checker regressions, 107 installer checks and ShellCheck. The benchmark's ten deterministic self-tests cover fixture parity, correct/incorrect implementations, stale warm policy, native usage attribution, failure reporting, per-case ordering, returned-text evidence, generated-document validity and the CI billing guard. CI runs those self-tests without invoking a model.

After native measurements, a mechanical check found that the fixture map used three plain lines where the documentation convention requires list items or one paragraph. The generator now adds list markers to those same three links. A regression runs the real checker against every generated case, including the warm update: ordinary cases have no warnings, while the intentionally stale route still fails for its missing target. The native numbers above retain the preceding formatting snapshot; the formatting-only correction was mechanically checked rather than rerunning models. The protocol skill files are unchanged by this correction.

The final offline report separates primary timing/token measures from cache and tool diagnostics following the user’s question about uncached input. This presentation change does not change raw measurements or grading.
