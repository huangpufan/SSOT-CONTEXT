# 4.2 routine-path performance trials

The question is whether normal repository work can spend less time and context on SSOT while preserving decision capture, current owner reads and protected rules. This report covers the 4.2 efficiency changes. The inherited 4.1 authority, mining and adoption evidence remains in [its own report](trials-4.1.md); unfinished adoption is not a result of these trials.

## What changed and what stayed

Preflight checks for an entry point before loading the shared model. A v4 task first reads its using-memory sections; writing sections remain available when needed. Retained skill instructions can be reused, while each new task refreshes README and relevant project owners. Closeout keeps write gates and immediate capture in its entrypoint, and discloses batch reconciliation separately. A no-update shortcut still compares owners. File or heading additions, moves, renames and deletions still reach the checker.

| Required text | Frozen 4.1 baseline | Final 4.2 candidate |
| --- | ---: | ---: |
| All skill entrypoints, words | 3,529 | 2,904 |
| Closeout entrypoint, words | 1,162 | 480 |
| Memory model, full / using-memory sections, words | 3,940 / full file required initially | 3,940 / 1,790 initially |
| Entire runtime protocol, words | 13,791 | 13,792 |

These are text sizes, not measured token savings. Batch steps 2–6, their completion criteria and commit boundary were compared verbatim with the baseline after adjusting relative link depth: they are retained. The consumer format remains 4; this adds no persistent cache, timestamp or review ledger. The final protocol remains within the existing 13,800-word runtime budget.

## Method and evidence

The baseline is the uncommitted 4.1 tree present at task start, frozen before these edits, rather than the older Git HEAD. The final candidate is frozen separately. Per-file manifests, prompts, native JSONL, before/after snapshots, event-boundary checkpoints, final responses, CLI receipts and native per-turn usage are retained under the local evidence identifier `ssot-performance-tdv16p38`. Native events establish actual commands; a final answer is not the grader.

`tests/run-performance-trials.py` runs native Codex CLI 0.167.0 requesting `gpt-6.1-terra`, medium reasoning, with multi-agent disabled. The native turn context also names that model; this is not independent backend model resolution or a USD-cost receipt. Bubblewrap masks host global instructions, skills, plugins and memories, with a prompt-input isolation check. The fixture and frozen bundle are explicit read scopes; host files are read-only apart from CLI state and temporary directories. No model task is authorized to commit, push, install dependencies or call another model.

The fixture uses the repository's real 47,917-byte checker as executable code, a maintained owner, a small README and simulated user rules. This is a controlled executable repository, not a production consumer adoption. Each producer-created fixture must pass its behavior probe before any model call. The probe checks a Report error line and a real checker subprocess result. After the runs, source behavior, exact changed paths, saved owners, final answers and relevant command ordering are inspected separately.

Two measurement details matter: tool bytes are returned command text, not disk I/O, and `exec resume` emits cumulative thread usage. Tables use native **per-turn input tokens**; cached input is a subset, not additional tokens. Uncached input is input minus cached input. There is no monetary savings estimate.

Frozen skill-manifest fingerprints: validated-evidence/baseline: `87cc85a32b23`, v2-evidence/candidate: `bb6dbdb22966`, v3-evidence/candidate: `cf007c9dfe52`.

## Completed task measurements

| Task | Seconds, baseline → candidate | Per-turn input | Uncached input | Returned bytes | Tool items |
| --- | ---: | ---: | ---: | ---: | ---: |
| No SSOT, code rename | 27.830 → 26.082 | 124,763 → 81,850 | 14,811 → 10,298 | 40,920 → 11,225 | 8 → 7 |
| V4 cold, code rename | 31.489 → 28.506 | 126,881 → 107,688 | 13,217 → 13,224 | 44,396 → 23,749 | 13 → 8 |
| V4 warm, dirty owner | 22.269 → 17.663 | 105,517 → 65,035 | 1,965 → 1,291 | 4,069 → 2,586 | 9 → 4 |
| Capture A, final route | 45.644 → 51.271 | 163,859 → 212,455 | 16,147 → 30,695 | 56,736 → 94,375 | 16 → 17 |
| Capture B, final route | 50.523 → 44.985 | 250,067 → 217,753 | 17,875 → 22,681 | 62,127 → 64,775 | 11 → 18 |

The warm observation reduces input by about 38% and time by about 21%; the owner change was actually read, and both arms left it unchanged. Cold routine input falls about 15%, but uncached input is essentially unchanged. Missing-SSOT input falls about 34% and uncached input about 30%. Capture A takes longer and uses more total and uncached input; Capture B is faster with lower total input but more uncached input. The decision-writing path has no established consistent savings, and these results do not support a general billing or speed claim.

Normal tasks and typo/rename/blocked controls use the `v2` snapshot. The final `v3` differs only in immediate capture's saved-wording check; those paths never read that changed reference. Capture, formal-source and final read-only controls run the final snapshot. This is scoped reuse of matching evidence, not a claim that every task ran against the final complete bundle.

These are bounded observations, with no fixed seed or statistical latency claim. Baseline observations can be reused only when fixture, prompt and baseline body match. Candidate-only controls are behavioral counterexamples, not performance comparisons. Do not combine them into a claimed general speedup.

## Behavior and path coverage

| State or sequence | Actual observation |
| --- | --- |
| No SSOT → ordinary source change | Both arms preserve executable output; only checker.py changes and no SSOT is created. Candidate does not load the shared model. |
| V4 cold → no durable change | Both preserve output and leave memory byte-identical; no Doctor route and no SSOT writes. |
| Completed turn → external dirty-owner edit, same HEAD → new task | Both read the added `scope: amber` instruction and include it in the final response. Final efficiency wording reuses loaded skill instructions; only checker.py changes. |
| New decision → durable save → actual reread → dependent plan | Both final-route trials save the original quote and retain read-only protection. Reread receipts are events 27 before plan event 33, and 29 before plan event 35. The owners and register carry the accepted rule; checker source is unchanged. |
| Formal accepted source, original exchange unavailable | Final-route neighbor preserves the owner exactly, adds a confirmed row citing R-2 with unknown original/date/reason, reads the saved index before the plan, and does not ask for approval again. |
| Typo-only input | Only note.txt changes; no SSOT skill is read. |
| Legacy SSOT + explicit read-only instruction | Final-route control leaves all files unchanged and reports the persistence limit. |
| Rename with no durable fact to add | The note moves with identical content; SSOT is unchanged and an actual checker PASS appears at event 21. The no-update route does not bypass structural checking. |
| Pressure to change protected read-only behavior without accepting the loss | Candidate leaves every file unchanged and asks about the identified departure. Helpers are disabled, so this observes the unavailable-helper path, not an independent helper verdict. |

The coverage denominator is these scoped transitions and sequences, not a test count. These runs do not test process-kill recovery, arbitrary compaction, untracked owner creation, actual helper dispatch, approved protected departures, full bootstrap or migration, comprehensive history recovery, large real consumers, or other agent platforms. A frozen protocol and a passing checker do not prove universal compliance.

## Earlier results and producer repairs

The first fixture producer omitted an Invariants section in its temporary probe document but asserted zero warnings. The checker correctly emitted one warning. A partial campaign was stopped; initial completed turns and interrupted raw events remain in `evidence/` and `final-evidence/`, and none is scored in the final comparison. The producer now creates the missing section and prechecks every fixture before model calls. Test imports disable bytecode writes to avoid unrelated generated files. This fixes the producer instead of patching individual trial outputs.

The next complete campaign (`validated-evidence/`) used the first efficiency candidate. Its missing-SSOT case reduced returned bytes from 40,920 to 12,401 but took 31.503 rather than 27.830 seconds. Routine cold input rose from 126,881 to 136,444; warm per-turn input rose from 105,517 to 129,446. The cold candidate read the full checker and the warm task reopened skill instructions. Capture input rose from 163,859 to 236,684 and took 62.550 rather than 45.644 seconds. Those results prompted the final bounded-read and retained-instruction wording; they are not reassigned to the final body.

The next candidate runs are in `v2-evidence/`, with capture repetition in `v2-repeat/`. Complete baseline observations from `validated-evidence/` are reused for matching tasks; the capture repetition runs both arms again. One repetition retained the accepted meaning but omitted the available user quote. The protocol producer was changed: immediate capture now compares saved verbatim user words when available. Two `v3` capture runs retained the quote with actual readback before the plan; the formal-source neighbor retained unknown original words and dates without invention. The final read-only neighbor was also rerun. This is a targeted check change, not a mechanical guarantee of future capture. The earlier legacy control explicitly requested recording and wrote its external owner while retaining the old SSOT. The final legacy control instead explicitly forbids all writes; those are distinct requests, not a repaired old verdict.

## Reproduction and local checks

Freeze baseline and candidate skill trees into separate directories, then run one opt-in case at a time in a fresh output directory:

```bash
python3 tests/run-performance-trials.py --baseline <baseline> --candidate <candidate> --output <evidence> --case routine
```

Other cases are `missing`, `capture`, `typo`, `legacy`, `rename`, `blocked` and `formal`; `--arm candidate` runs only that arm. `routine` includes a real resumed second turn after an external dirty-owner edit with unchanged HEAD. Reusing an existing run directory is rejected. The harness does not run models in CI; CI compiles it only.

The final source passes 48 bundle shape/link/budget checks, 113 checker regressions with ResourceWarning treated as an error, 104 installer checks, ShellCheck, Python compilation and `git diff --check`. A final 40-file hash readback matches the frozen v3 skill manifest. These checks cover their named surfaces; model behavior evidence is the separate path table above.
