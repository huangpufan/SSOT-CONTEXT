# 4.3: bounded memory reading and measured limits

The goal is to reduce the time and context spent maintaining repository memory while preserving fresh owner reads, immediate decision capture and protected outcomes. This release bounds the memory text returned by a cold read and avoids repeating retained rules. Native whole-task measurements are mixed: routine turns are faster in the final observations, while decision capture is slower and total input does not consistently fall. This is not evidence of a general speed or billing improvement.

## The change

Preflight uses a read-only reader to return the project's README and v4 using-memory rules together. On a later task whose rules remain current in context, `--entry-only` refreshes the entry without repeating those rules. The reader follows no owner links: the agent still reads the relevant owners, including dirty and untracked content. There is no persistent cache. Updated instructions, changed scope, uncertain freshness or lost context still require the appropriate reread.

The shared model keeps its using-memory rules and routes longer branches to separate layout, writing and protected-departure references. Human-decision evidence loads when assessing acceptance or replacement. Writing rules load before writing, and departure review before changing protected behavior, including a newly admitted rule. These are routing instructions, not a mechanical barrier to every possible model mistake.

| Text size, including section headings | 4.2 baseline | 4.3 release |
| --- | ---: | ---: |
| Full shared model, words | 3,940 | 1,887 |
| Full shared model, UTF-8 bytes | 24,713 | 11,824 |
| Initial using-memory sections, words | 1,793 | 1,190 |
| Entire runtime protocol, words | 13,792 | 13,800 |

The moved layout, writing and departure bodies were compared with the frozen baseline: they are preserved after adjusting headings and cross-file links. The helper's quoted criterion, stop/failure behavior and already-accepted path are retained. The reader extracts the authoritative model instead of copying its rules into code. Consumer format, installer, checker and budgets are unchanged. Text size is not a token or latency measurement.

## Method and evidence

Baseline: clean main `e6ae79e`, frozen before this task. Native Codex CLI 0.167.0 requests only `gpt-6.1-terra`, medium reasoning, with helpers disabled. The recorder uses the executable checker fixture and probes its behavior before model calls. Bubblewrap hides global instructions, skills, plugins and memories. Startup logs include failures to install the hidden system skills; sessions still complete and these logs are retained. These are controlled executable repositories, not production consumer adoption.

Local evidence identifier: `ssot-performance-43-1s9gm1n5`. Each campaign keeps skill manifests, prompts, native JSONL and per-turn usage, CLI commands, before/after files and event-boundary checkpoints. Baseline observations from `evidence-release/` are reused: baseline skills, fixture producer for these tasks, user task and CLI settings match; working-directory and bundle-path prefixes differ. They are not fresh paired repetitions of the final reader.

Final routine and untracked-owner observations are in `evidence-final-reader/`; final capture is in `evidence-shipped/`. The latter frozen skills match the shipped tree except for a subsequently shortened layout H1. The former additionally predates shortening the departure H1; neither change alters a rule body or executable. Fresh-session controls in `evidence-reader/` predate the later `--entry-only` option and its routing sentence. Those controls cover their actual source snapshot, not every byte of the release.

Input below is native per-turn input, including cached input. Uncached input is input minus cached input, not a USD bill. Tool bytes are returned command text, not disk I/O. Resume's cumulative CLI usage is not treated as turn usage. A few development and final runs overlapped; there is no fixed seed, and provider/cache conditions vary. Timing includes the model, tools and recorder. These small samples do not establish a statistically reliable or causal percentage.

## Final observations

| Task | Seconds, baseline → candidate | Per-turn input | Uncached input | Returned bytes | Tool items |
| --- | ---: | ---: | ---: | ---: | ---: |
| Routine cold | 37.026 → 30.387 | 112,203 → 133,051 | 26,315 → 23,099 | 27,495 → 67,172 | 11 → 9 |
| Routine warm, dirty owner | 26.493 → 22.014 | 119,581 → 121,070 | 9,501 → 2,158 | 10,669 → 4,874 | 7 → 6 |
| Immediate decision capture | 52.166 → 70.780 | 189,499 → 228,700 | 24,891 → 18,012 | 91,332 → 49,057 | 19 → 16 |
| New-owner case, cold | 26.911 → 27.438 | 108,470 → 106,860 | 9,270 → 14,060 | 26,931 → 20,917 | 8 → 10 |
| New route and untracked owner | 21.713 → 22.911 | 118,065 → 116,299 | 3,633 → 4,555 | 9,496 → 15,304 | 6 → 7 |

The two routine turns take about 17% less time together, but about 10% more total input. Their uncached input falls by about 29%. The cold trace reads the full checker source early, so the smaller memory payload does not determine whole-task context cost. Warm native receipts show `--entry-only` actually used, and the externally changed `scope: amber` instruction is read and reported without modifying its owner.

The new-owner sequence takes slightly longer with slightly less input than its baseline. Both arms follow the changed README route, read the untracked owner and leave it untouched. The script therefore retains freshness in the tested sequence; it does not establish a general cache invalidation guarantee.

Final decision capture regresses from 52.166 to 70.780 seconds and from 189,499 to 228,700 input tokens. It preserves the original quote and rereads it before the dependent plan. The earlier reader capture took 53.131 seconds and 176,666 input tokens; it is retained as an earlier observation, not substituted for the less favorable final result. No consistent decision-path saving or overall token reduction is claimed.

## Development results, including regressions

| Snapshot and task | Seconds, baseline → candidate | Input tokens, baseline → candidate |
| --- | ---: | ---: |
| Wording/departure split, cold routine | 34.920 → 43.890 | 109,432 → 120,524 |
| Wording/departure split, warm routine | 29.439 → 36.772 | 96,345 → 107,603 |
| Wording/departure split, capture | 68.433 → 56.737 | 223,064 → 199,792 |
| Physical split before batching, cold routine | 30.923 → 35.655 | 153,939 → 134,692 |
| Physical split before batching, warm routine | 19.220 → 24.157 | 88,287 → 120,863 |
| Physical split before batching, capture | 105.505 → 50.915 | 189,941 → 192,046 |
| Physical split with batching, cold routine | 37.026 → 29.654 | 112,203 → 113,087 |
| Physical split with batching, warm routine | 26.493 → 20.592 | 119,581 → 93,430 |
| Physical split with batching, capture | 52.166 → 115.003 | 189,499 → 249,849 |
| Physical split with batching, new-owner cold | 26.911 → 70.244 | 108,470 → 113,959 |
| Physical split with batching, new-owner warm | 21.713 → 56.634 | 118,065 → 122,702 |
| First reader, cold routine | 37.026 → 26.928 | 112,203 → 109,131 |
| First reader, warm routine | 26.493 → 26.024 | 119,581 → 122,215 |
| First reader, capture | 52.166 → 53.131 | 189,499 → 176,666 |
| First reader, new-owner cold | 26.911 → 36.605 | 108,470 → 130,560 |
| First reader, new-owner warm | 21.713 → 30.066 | 118,065 → 127,844 |

`evidence-v2/` contains the wording/departure variant; `evidence-final/` contains the intermediate physical split; `evidence-release/` contains the subsequent batching candidate. The names predate the final reader and do not mean release acceptance. Each candidate and its output remain frozen separately.

The wording candidate still read the entire shared model. Physical separation bounds that failure; the reader then makes the intended section extraction executable. The first reader repeated its rules on a warm turn, prompting an entry-only option and a regression check. These are iterative development observations, not independent repeated confirmation of a performance gain. No earlier favorable result is reassigned to the final bundle.

## Behavior and path coverage

The denominator is these scoped states and sequences, not the test count. Saved files, actual tool receipts and independent executable probes are inspected separately from final answers.

| State or sequence | Source snapshot and actual observation |
| --- | --- |
| V4 cold task → content-only source rename | Final reader, both source-renaming cases: only checker.py changes; executable behavior is preserved, with no SSOT writes or Doctor review. |
| Completed turn → dirty owner, unchanged HEAD → next task | Final reader: entry-only refresh is used, the external instruction is read and reported, and only checker.py changes. |
| Completed turn → changed route and new untracked owner, unchanged HEAD → next task | Final reader: new route and owner are actually read; `scope: amber` is reported and the owner's bytes are retained. |
| New decision → save → reread → dependent plan | Final capture: original quote and read-only rule remain; native readback receipts precede the first checkpoint containing implementation-plan.md. |
| Request crosses a protection without accepting its loss | Earlier reader: departure reference is read, no files change, and the response asks about the identified loss. Helpers are disabled, so this covers the unavailable-helper route. |
| Formal accepted source without original exchange | Earlier reader: owner stays unchanged; the confirmed index row links to its accepted record, and unknown original words/date/reason remain unknown. Saved memory is read before the plan. |
| File rename without a durable fact | Earlier reader: note.txt moves byte-identically, memory is unchanged and the real checker runs. |
| No SSOT → source rename | Earlier reader: no shared model is read, no SSOT is created and executable behavior is preserved. |
| Typo-only input | Earlier reader: only note.txt changes; no SSOT skill is read. |
| Legacy memory with an explicit no-write instruction | Earlier reader: every file stays unchanged and the response discloses that the decision was not persisted. |

Real helper dispatch, approved protected departures, process-kill recovery, full bootstrap/migration, large production repositories and other models/platforms were not tested. Textual preservation does not prove those unrun behaviors.

An initial independent inspection assertion required the formal decision ID and the word “unknown” to be duplicated in the index. Inspection showed that its link instead reaches the unchanged accepted owner carrying both. The inspection producer was corrected to check the canonical route and preserved source limits; no model output was patched or rerun to satisfy that mistaken assertion.

## Reproduction and local checks

Freeze baseline and candidate skills, then run a case in a new evidence directory:

```bash
python3 tests/run-performance-trials.py --baseline <baseline> --candidate <candidate> --output <evidence> --case routine
```

`routine` resumes after a dirty-owner edit. `untracked` resumes after changing the README route and creating an untracked owner; both keep HEAD unchanged. Other cases: `capture`, `blocked`, `formal`, `rename`, `missing`, `typo`, `legacy`. `--arm candidate` runs only that arm. Billable models are opt-in; CI compiles the recorder without running them.

Local checks pass: 48 bundle shape/link/budget checks, 114 checker regressions, 8 reader command tests, 108 installer checks, ShellCheck and Python syntax. Reader tests cover bounded v4 rules, quoted/commented and malformed markers, legacy/unmarked text, body-only markers, missing-entry failure, fresh route reads and entry-only output. Installer checks execute the installed reader and compare all three moved references byte-for-byte. These checks cover their named surfaces; native behavior evidence is the separate path table above.
