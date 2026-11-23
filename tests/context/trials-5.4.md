# 5.4 context tiering and installed discovery

Status: the checked paired scenarios and actual Calliope installation checks passed. This establishes the observed paths, not a general performance or reliability improvement.

The scope and protocol decisions are in [the design account](../../docs/2026-11-16-context-tiering-design.md). Baseline 5.3 and candidate 5.4 use `gpt-6.1-terra` with medium reasoning. C09 tests context consolidation, partial replacement, a frozen dependency and a fresh consumer; C10 tests necessary historical retrieval; D03 and D06 retain development correction and typo controls.

The first C09 baseline completed both native sessions. Reporting then failed because the context oracle imported a different module also named `run` when launched as a CLI. Original attempts are preserved. The cost helper now resolves by file path and has a subprocess regression check; this repair changes reporting, not those model actions. The corrected report reuses original native records instead of replaying completed calls. Subsequent execution uses a new frozen harness; fixture and bundle equality are checked before comparing this retained baseline.

## Outcomes and evidence

The [machine inventory](results/context-tiering-5.4-2026-11-16.json) binds frozen plans, fixtures, bundles, native receipts and the independent semantic review. Original raw records, failed reporting and separate reanalysis are retained in the private evidence archive `tiering-20261116-ejppf66v`. Raw native session data is not published. Every baseline/candidate subject receipt identifies `gpt-6.1-terra`, medium reasoning, with complete closing usage. C09 uses distinct native writer and consumer sessions in both arms.

| Scenario | Baseline 5.3 and candidate 5.4 result |
| --- | --- |
| C09, format 5 consolidation | Both fresh consumers use Friday 20:00, other days 19:00, daily light signal and the retained 17:00 staff exception. Privacy and lending constraints remain. Current policy and reusable notice agree; exact original source words and frozen annex bytes survive. The entry identifies the annex's obsolete guidance, current authority and reopening condition. Neither consumer dumps the completed upkeep archive. |
| C10, necessary cold recall | Both actually read `archive/decision-17.md`, identify its source, permit private vibration-only staff pagers and reject the public bell for the quiet-room reason. Only the requested deliverable changes. |
| D03, format 4 correction | Both preserve original human-10/11/12 wording and the limited replacement. Public traces show capture, readback, then the dependent plan. Unattended output remains plain text; interactive Markdown permission does not extend to product notifications. No implementation is claimed. |
| D06, unrelated typo | Both change only `note.txt`; no SSOT read is observed. |

The independent reviewer inspected frozen tasks, before/after artifacts, deliverables and public tool traces. Mechanical verdicts alone remain `awaiting_semantic_review` in the original attempts; this report and inventory add the reviewed outcome without rewriting them. C09's entry fell from 7,953 characters to 1,148 in baseline and 1,222 in candidate. Those sizes are descriptive, not the success criterion: the consumer's retained conditions, explanation and boundaries matter.

## Observed cost and limits

Input is the sum of every native request's full input, including cached input. It is not unique document size or a price estimate. C09 includes both writer and fresh consumer; D03 includes both turns. Seconds cover native turns, excluding setup, external review and installation.

| Case | Full input, baseline → candidate | Cached input, baseline → candidate | Output, baseline → candidate | Native seconds, baseline → candidate |
| --- | ---: | ---: | ---: | ---: |
| C09 | 359,133 → 310,142 | 320,896 → 277,632 | 2,485 → 2,377 | 133.788 → 114.861 |
| C10 | 108,829 → 109,002 | 93,440 → 97,664 | 561 → 531 | 48.686 → 45.782 |
| D03 | 441,788 → 438,935 | 370,688 → 411,264 | 3,488 → 3,864 | 142.713 → 133.521 |
| D06 | 80,503 → 60,277 | 71,936 → 51,840 | 228 → 181 | 43.046 → 36.917 |
| Total | 990,253 → 918,356 | 856,960 → 838,400 | 6,762 → 6,953 | 368.233 → 331.081 |

Both arms passed; no quality advantage was demonstrated. Total input is 7.3% lower in this sample, but C10 input increased and D03 candidate used more tool items and output bytes. There is one observation per case/arm, fixed execution order, no repeated or randomized comparison, no long-term workload, and no complete project-task or monetary cost measurement. C09/C10 validate format 5 tiering and retrieval. D03/D06 provide format 4 regression coverage, **not** an equivalent full format 4 consolidation/frozen-dependency trial. Compression does not evict previously loaded host context.

Runtime protocol text grew from 16,868 to 17,595 words; the ceiling is now 18,000. The new shared authority replaces the old development-only supersession recipe, and consolidation is conditional. This measured maintenance tradeoff is accepted for the scoped design; it does not prove lower runtime cost for every task.

## Actual installation and discovery

Calliope was clean at `9d286859` before the project-only upgrade (full identity in the inventory). The local-source installer ran with `--upgrade --agent codex,agy --scope project`. All 39 installed files matched the source with the Chinese templates selected. `.agents/skills` and `.claude/skills` still point to the single `.codex/skills` owner. Only the marked SSOT instruction block changed in `AGENTS.md`; its surrounding text, unrelated tracked files and frozen project content were preserved.

An actual Codex catalog probe listed all six skills. A fresh native Codex session (`gpt-6.1-terra`, medium, confirmed by its turn context) and a fresh Antigravity session both fully read the installed preflight/doctor instructions and new tiering reference, then performed a bounded read-only review. Both observed preflight protocol 5.4 and ran the installed checker successfully. Antigravity requested `gemini-4-carbon-medium`; its response receipt identifies `gemini-4-carbon`, without independently echoed effort. Discovery, actual file reads and subsequent use are separately recorded in the inventory.

The earlier Antigravity discussion had already read the existing 5.3 skill successfully. Thus the user's unavailable-skill symptom was not reproduced in these fresh project sessions; this is evidence of current availability, not a claim that an unknown old-session defect was repaired. The installer now has an explicit App key (`antigravity-app`, alias `agy`) for the documented shared global path. Existing IDE/CLI keys keep their legacy installation ownership. Global path behavior was checked in isolated installer homes; no real global installation was changed. See [the installation guide](../../INSTALL.md) for the official App/CLI/IDE distinctions and refresh instructions.

The actual reviews also found remaining **Calliope content** work: Antigravity identified an oversized frozen-area follow-up table that repeats replacement details; Codex identified tension between a README route allowing relevant reference reads and a control-page restriction on reading locked areas. Those are bounded review findings, not a completed audit of the whole novel. This installation did not rewrite those owners or frozen canon.

## Local checks

Bundle shape: 57 passed. Installer end-to-end: 120 passed, including shared project symlinks, unrelated skills, App shared-global ownership and legacy scoped uninstall. Offline checks: tiering 8, context 11, orchestration 19, benchmark 65, source oracle 2 and continuation 1 passed. Shellcheck and whitespace checks passed. Calliope `make check` passed before and after installation; after installation it reported 0/32,262 broken links/anchors, no context-health or installed checker errors/warnings, and no active forbidden-term hits. These checks do not substitute for the native semantic and discovery observations above.
