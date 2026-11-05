# Changelog

All notable changes to the SSOT Skill bundle protocol.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to a simple `MAJOR.MINOR` versioning scheme tied to the bundle protocol. The single source of truth for the current version is `metadata.protocol_version` in `skills/ssot-preflight/SKILL.md`; the `VERSION` file at the repository root is the physical mirror enforced by `tests/test-bundle-shape.sh`.

Entries up to 2.86 were derived from the v2 protocol-upgrade ledger, which is preserved with the rest of v2 at the `v2-final` tag.

## [Unreleased]

## [3.13] - 2026-11-06

Closeout now asks the agent to record a user's decision as a confirmed row of its own, with the user's words in its Source, instead of stamping `confirmed` on an existing candidate row. In 28 recorded edit sessions of the released 3.12 text on fd, the sessions wrote 13 confirmed rows. Seven of them were whole candidate rows that the agent rewrote and promoted with a Source of "user, date", and none of the 13 quoted the user. A plain tuning request (raise the minimum Rust version) also turned its row into a confirmed rule that later agents would have to ask a person to change. With this wording, 48 sessions wrote 23 confirmed rows: 2 promotions, 21 new short rows, and all 23 carry a quotation in their Source.

### Changed
- `skills/ssot-closeout/SKILL.md` step 2: a lasting user directive, or a departure from a protected rule that the user accepted, becomes its own confirmed row. Its Source quotes the user's words and the date, and the row states only what those words decided. Clauses of an earlier candidate row that the user did not discuss stay in a candidate row, and a clause of a confirmed row is never moved to candidate. Step 4 now points to step 2 for how to record a departure instead of repeating it. About 47 words added; the runtime protocol is 10,234 of 11,000 words.

### Evidence
- `tests/trials-3.13.md`: edit sessions of `deepseek-v4.1-flash` (maximum reasoning effort) on fd with its 83-row mined register, one request per session, from the same clean starting commit for baseline and candidate. Baseline: the released 3.12 text, 28 sessions. Candidate: 48 sessions (14 with an earlier version of the wording, 34 with the final one). The failed variants and the sessions that were stopped are listed there.
- Confirmed rows written, whole-row promotions of a candidate, and rows with a quotation in the Source: baseline 13, 7, 0 of 13; candidate 23, 2, 23 of 23. The two remaining promotions were a held-out request that rewrote a whole row and stamped it, and a tuning request.
- No over-asking showed up in the one signal that was measured, a session that ended without a code change: none of the 27 harmless, user-accepted, and tuning sessions under the candidate did (0 of 15 under the baseline). A session that changed the code and also asked would not show in this signal.
- The shape tests pass (48 of 48) and the checker tests pass (99 of 99) on the release tree; the checker script is unchanged.

### Not verified
- That agents stop before crossing a protected rule. This change does not touch that rule, and the sessions that proceeded kept proceeding: requests crossing a rule ended without a code change in 10 of 21 candidate sessions and 4 of 13 baseline sessions, which is not a claimed effect (the held-out requests alone went 1 of 6 against 1 of 3). Three rewordings or redesigns of the asking rule were tried, and none changed it reliably; one was stopped after 2 completed sessions and another after 3, and all three are listed in the trials file.
- That a quoted Source means the user accepted losing the old protection. The quotes are the text of the user's request: of the nine rows for requests in which the user states that they accept the break, five quote those words and four quote only the new behavior. The row is traceable, not authorized, and a person still has to read each new confirmed row.
- That a new row states only what the user decided: in one session a short row added clauses the user never said (that `--show-errors` only controls the diagnostic, and that recovered broken symlinks are entries). A new short row can also fix a one-time tuning choice into a confirmed rule; one candidate session did. The last sentence added, that a clause of a confirmed row is never moved to candidate, has no scenario in the data that exercises it.
- Other repositories, other models, and changes that were built and tested as a whole: the machine's Rust is 1.75 and fd needs 1.90, so no change was built as a whole, although 16 of the 28 baseline and 20 of the 48 candidate sessions compiled or tested isolated pieces. No reading cost was measured. The first of three repeats used the wording before its last clause (the limit to candidate rows); the other two used the final text. The agents often reasoned as if they were in a benchmark with hidden tests, in baseline and candidate alike.

## [3.12] - 2026-11-05

A mining round now splits an owner file that passes the reading budget instead of shortening it. `ssot-check` already warns at about 16,000 characters and the memory model already says to turn the file into a folder, but `mining.md` did not say it. In six earlier runs on fd's output area, three owner files ended between 15,908 and 16,000 characters, and in one the writer's report says it dropped secondary notes to get there, among them an exception a later row check flagged as missing. The consumer data format is unchanged (`ssot_format: 3`); nothing needs to catch up. Evidence and limits: `tests/trials-3.12.md`.

### Changed
- `references/mining.md` §4: when the checker warns that an owner file is past the reading budget, split it by topic (memory model §4), and never shorten it by dropping a condition, exception, alias, or piece of evidence. About 33 words; the runtime budget is 10,187 of 11,000.

### Evidence
- Two replays of a real fd output-area run from just before the writer, with a 90-minute cap: both finished, both split the owner file into a folder (5 and 4 files; 20,270 and 17,755 characters when the lead first saw them), and the new register rows entered the register only after the row check had passed. Without the sentence, one of six runs ended with a folder (`tests/trials-3.12.md`).

### Not verified
- That the sentence caused the split: the difference is two of two against one of six, and every run saw the checker's warning. That a file under the budget stays whole. That a split loses nothing: in one replay the files shrank by about 3,000 characters when the writer split, the pre-split file was deleted, and only the later row checks (one dropped condition found and restored) and a link check speak for it. Other repositories, areas, and models; a whole mining round.

## [3.11] - 2026-11-05

A mining round now keeps a register row out of the register until a fresh helper has checked it. Under 3.10 the same paragraph said both "add its checked rows to the register" and "write directly into the owner, not a draft", and in one real run the lead had the writer put 11 new rows straight into `SSOT/README.md`; the run then hit its time cap before the row check returned, and those rows stayed in the register unchecked. The consumer data format is unchanged (`ssot_format: 3`); nothing needs to catch up. Evidence and limits: `tests/trials-3.11.md`.

### Changed
- `references/mining.md` §4: the writer drafts each register row in its own working file, not in the register, and the lead adds only checked rows; an unchecked row stays in the working file. This replaces "add its checked rows to the register then" with the same duty stated so that "directly into the owner" cannot be read as covering the register.

### Evidence
- Replaying the real fd output-area run from just before the writer, twice per text: the drafting sentence alone left 11 unchecked rows in the register in both replays (the lead merged early); with "add only its checked rows" the register had no new row before the row check in both replays, and `ssot-check` passed (`tests/trials-3.11.md`).

### Not verified
- A finished run of the shipped text: both replays reached their 40-minute cap during the re-check, so no new rows were in the register when they stopped, including rows the first check had passed. Two replays per text from one starting state, one repository, and one model.

## [3.10] - 2026-11-04

A mining round now fixes a flagged register row by putting the case into the row, instead of narrowing it however the fixer likes or dropping it. On fd with `deepseek-v4.1-flash`, rows written in a mining round were often still rejected by the graders because a row said "always" or "only" where its own explanation named an exception, or left out an override (19 of 27 new rows accepted in one run, 8 of 15 in another). The consumer data format is unchanged (`ssot_format: 3`); nothing needs to catch up. Evidence and limits: `tests/trials-3.10.md`.

### Changed
- `references/mining.md` §4: the row check adds a "contradicted" verdict (the row's own explanation names a case that makes its words false) and lists every case with its evidence and the smallest change; a fresh helper then verifies each case itself and edits the row so it holds in every verified case, naming the case or narrowing the universal word or condition, never dropping a part, fixing the explanation where it disagrees, and leaving `confirmed` rows alone. This replaces "fix every row it flags, by narrowing, moving it, or dropping it".
- Runtime budget raised from 10,000 to 11,000 words (owner direction, 2026-11-03: budgets may be loosened); the new text brings it to about 10,140.

### Evidence
- On two finished 3.9 mining runs of fd's output area, reviewers plus one fixer raised the claims judged safe from 29 to 39 and from 27 to 39 of 44 (majority of three gradings), and the new rows accepted from 19/27 to 22/27 and from 8/15 to 14/15; no confirmed row changed. A clause-by-clause check of the 31 changed rows against the code found a false clause in 5 rows instead of 15, and 6 of 169 clauses false instead of 18 of 95 (`tests/trials-3.10.md`).

### Not verified
- A whole mining round that follows the new wording; the experiment ran scripted prompts the text condenses. A second check of the fixed rows (three rows gained a wrong clause from the fix itself). Models other than flash, repositories other than fd, and the cost of rows that grew from about 15 to about 39 words for an agent reading the register at preflight.

## [3.9] - 2026-11-03

The checker now reports a confirmed invariant that an agent changed, and a mining lead that sees the error puts the rule back. Three of four 3.8 mining runs with `deepseek-v4.1-flash` on fd rewrote the text of three of the four confirmed rules while tidying the register: one added "documentation typos are exempt", one dropped "take responsibility for contribution rights", one turned "open an issue first" into "a request, not an enforced gate". Memory model §5 already forbade this; nothing detected it, and the precision grading looked only at candidate rows. The consumer data format is unchanged (`ssot_format: 3`); nothing needs to catch up. Evidence and limits: `tests/trials-3.9.md`.

### Changed
- `ssot-check.py`: compares each confirmed row of the base commit (`HEAD`, or the `--since` commit) with the working tree. A changed kind, rule, or status, or a removed row, is an error, unless the row's Source gained a date: that is how a change the user decided is recorded, and the checker then lists the row for the user to see. A moved link or a reworded source is not reported. Replayed on the 14 existing flash mining copies of fd, it reports exactly the rows a separate script found changed (0 to 3 per run) and nothing in the runs that only moved links.
- Checker budget raised from 40 to 44 KiB (owner approval, 2026-11-02) for this check; the alternative, a second script, would need its own wiring into every skill that runs the checker.

### Evidence
- Five end-of-round replays with flash, each starting from the saved end state of a real mining run (`tests/trials-3.9.md`): in the three that held rewritten confirmed rules, the lead ran the checker, restored all of them word for word, and added no date; with no confirmed change, nothing was reported or changed; when the user approved a change in the request, the lead made it and dated the Source with the user. The same start state with the 3.8 checker restored none of the three, and its report said the confirmed rows were unchanged.

### Not verified
- A whole mining run with this checker, closeout's `--since` path, and other models. A lead could add a date without the user's approval; none of the five did, which is too few runs to rule it out, and a dated change is still listed for the user.

## [3.8] - 2026-11-01

Mining no longer comes back empty, and it records more of a repository's protected rules. In 3.7, one of three mining runs with `deepseek-v4.1-flash` on fd wrote no rules at all: the lead had its writers draft into working files for one merge at the end, and the run ended before the merge. Now writers write into `SSOT/` directly, each area is challenged, written, checked, and registered as soon as its own miners finish, and the lead keeps at most eight helpers running instead of starting more and having them refused. In a clean environment, one mining round with `gpt-6.1-terra` from the same starting SSOT stated 55% of click's claims against 42% for 3.7 (four runs each; click was held out while the text was written) and, with the text before the checker change, 59% of fd's against 52%; 92% to 95% of the added rows were correct in both versions. The consumer data format is unchanged (`ssot_format: 3`); nothing needs to catch up. Evidence and limits: `tests/trials-3.8.md`.

### Changed
- `mining.md` §2: helpers run from a queue, at most eight at a time or fewer if the runtime allows fewer; a workflow or batch tool that starts helpers counts against the same limit; after a limit error, wait for a running helper to finish and start again.
- `mining.md` §4: each area's writer writes directly into its owner in `SSOT/`, not into a draft for the lead to merge. Each area goes through challenge, writing, and the row check as soon as its miners finish, and its checked rows join the register then, so a round that stops early keeps every area it finished.
- `mining.md` §1 and §4: the checklist lists each documented option with every spelling; writers carry every condition, exception, alias, and exact value from the proposal and the challenge; the row checker also compares each row with its proposal for dropped details.
- Memory model §4: the README's target of about 8,000 characters does not count the rows of the invariants register, which grows with the rules. The checker already excluded them.
- `ssot-check.py`: no longer warns when the register passes 60 rows. Leads read the warning as a cap and moved admitted rules out of the register to stay under it.

### Evidence
- click, held out (169 claims), clean environment, one terra mining round from the same starting SSOT: 3.7 44%, 40%, 29%, 56% (mean 42%); 3.8 59%, 41%, 57%, 62% (mean 55%). Precision of added rows: 93% and 92%.
- fd (202 claims), same arrangement: 3.7 69%, 26%, 56%, 55% (mean 52%); the 3.8 text before the checker change 60%, 64%, 64%, 48% (mean 59%). Precision: 94% and 95%.
- fd with flash: 3.7 83%, 91%, and one run with no rules written; 3.8 92%, 96%, 95% (before the checker change) and 91%, none empty. Precision of added rows: 68% (3.7) and 66% (3.8).
- A flash mining run of fd takes 95 to 157 minutes, set by the account's rate limit: 2,100 to 3,300 model steps at 18 to 30 steps per minute for the whole account, whether one run or several are active.

### Not verified
- Coverage near complete. Every clean terra mining round, in both versions, stopped after 4 to 13 minutes and called itself unfinished; on fd the spread between runs of one version (26% to 69% for 3.7) is larger than the difference between versions.
- Precision with flash: a third of its added rows still miss a condition or exception, and the flash row checker passes rows the terra judge rejects.
- Full setups with 3.8, large repositories, and flash on click.
- Equal conditions for the flash comparison: the 3.7 runs ran three at a time, the 3.8 runs one at a time, as users run them (owner decision, 2026-10-31).
- 3.7's own numbers (fd 64%, click 50%) were measured with the maintainer's personal codex configuration loaded; in a clean environment 3.7 states 52% and 42%.

## [3.7] - 2026-10-30

Mining now finds most of the protected rules of a small or medium repository, not about a third. On fd, a Rust command-line tool, the share of protected behaviors that SSOT states after one mining round with `gpt-6.1-terra` rose from 33% to 64% on average over five runs, with 90% to 100% of the added rows correct; on click, a Python library held out while the text was written, from 35% to 50% over three runs. The largest gain came from removing a bottleneck: in 3.6 the lead agent decided and rechecked every proposal itself and stopped with most of them undecided; now one helper per area writes every outcome the challenge left standing into `SSOT/`, and the lead decides only disputes. The owner raised the runtime word budget from 9,500 to 10,000 for these changes. The consumer data format is unchanged (`ssot_format: 3`); nothing needs to catch up. Evidence and limits: `tests/trials-3.7.md`.

### Changed
- `mining.md` §1: setup mines every main area; a small or medium repository is mined whole in one round, every area getting a first pass before any gets a second. Each area's sources are listed item by item (tests, fix and revert commits, changelog fixes, documented behaviors, guards) and split among the miners.
- `mining.md` §2: user documentation (manual, README, help text, API reference) is a mining source; a documented behavior the code still has is a candidate, never `confirmed`. Each miner marks every checklist item, with no target count.
- `mining.md` §4: miners apply the challenger's findings; the lead decides only disputes; one helper per area, each owning its files, writes every standing outcome into its owner and drafts its rows. Rules state the behavior a user or caller sees (or, for architecture, the property and boundary), not a test fixture, one outcome per row, and the explanation names triggers with aliases, the default, the exact outcome, precedence, and exclusions. A fresh helper checks the new rows, hunting exceptions first; a violated protection stays and is reported; a row still disputed after one recheck stays out of the register and goes in the report.
- `mining.md` §5: after every area's first pass, a fresh helper samples checklist items for outcomes missing from `SSOT/`; misses are mined once more, then reported.
- Memory model §5 and bootstrap §2: a promise in the user documentation is evidence for a candidate.
- `CONTRIBUTING.md` and `tests/test-bundle-shape.sh`: runtime budget 10,000 words.

### Evidence
- fd, claims SSOT states (202 claims split from 53 rules derived and checked by terra), one terra mining round from the same starting SSOT: 3.6 36%, 30%, 32%; 3.7 text 65%, 64%, 66%, 55%, 70%. Precision of added rows: 3.6 88% to 100%, 3.7 90% to 100%.
- click, held out (169 claims): 3.6 34%, 36%; 3.7 before the review fixes 49%, 58%, and the shipped text 44% (one run, finished after release); precision 87% to 98%.
- A second mining round on a finished copy added at most 2 points: what remained was missing detail, which the explanation list now names.
- 3.6's open question: on jellyfin, mined SSOTs drew 2 needless questions in 24 ordinary requests, the unmined one 1 in 12.

### Not verified
- Coverage near complete; the best runs state about two thirds of fd's claims and about half of click's.
- Precision with `deepseek-v4.1-flash`: its fd setups state 73% to 87% of the claims, but its candidate rows were judged correct 80% and 67% of the time with 3.6 and 58% in the one setup with the 3.7 text.
- Large repositories; full setups with terra, which often ended sessions with setup unfinished; whether more rows change what agents do.
- A clean environment: every terra run, builders and judges, loaded the maintainer's personal codex instructions, skills, and memories (found after release; `tests/trials-3.7.md` section 6).

## [3.6] - 2026-10-30

Setup and Doctor can now find the architecture and product rules a repository protects but never wrote down, so that 3.5's rule (keep a protected rule unless the user gives it up) has rules to protect. Before, setup registered almost none of them: about 1% of the protected rules sampled from three areas per repository. The procedure is never one agent in one pass: helper agents with fresh contexts mine from tests, history, and guards, a fresh challenger looks for exceptions and missed rules, the miners revise, the lead admits each rule by the admission rule, and a fresh reader checks the result. The owner released it on 2026-10-30 after the first results, with the next goal of raising coverage and precision toward complete. The consumer data format is unchanged (`ssot_format: 3`); nothing needs to catch up; a Doctor area scope mines an existing SSOT. Evidence and limits: `tests/trials-3.6.md`.

### Added
- `ssot-bootstrap/references/mining.md`: declare the scope; at least two miners per area from different sources; a challenger; a revision round; admission; a fresh-reader check; a per-area report. If helpers cannot be started, stop and tell the user instead of mining alone. After a helper's rate-limit error, retry with fewer at a time rather than a narrower task.
- Bootstrap: a question about which outcomes users, clients, and integrations rely on staying the same, and setup is done only when the rules were mined this way and the report was given to the user.
- Doctor: a scope for mining one area's protected rules.

### Changed
- Memory model §5: admitting a rule now also states its supported exceptions, one change that would violate it and one nearby change it permits, and a search for evidence against its scope; "no known exception" is allowed but proves nothing.
- Mining and Doctor's catch-up keep working files in `.ssot-work/` at the repository root, with its own `.gitignore`, instead of outside the repository, where sandboxed agents often cannot write.

### Evidence
- Coverage of 134 protected rules in nine areas declared in advance: 3.4 setup 1 of 134; mined with the cheap model 43% to 57% per repository (three builds on jellyfin and n8n), with `gpt-6.1-terra` 28% to 39% (three repositories).
- Precision of added rows: cheap model 44% to 67%, terra 82% to 88%; most other rows were right in substance but missed a condition or exception.
- jellyfin, 12 change requests that break a sampled rule: plans protected 2 against the unmined SSOT and 9 against a mined one.

### Not verified
- Whether overbroad mined rules make agents ask about ordinary work; that test was still running at release.
- 1Panel with the cheap model, more builds, and other models; precision near 90% with the cheap model.
- Doctor's catch-up with working files in `.ssot-work/`, beyond a sandbox check that the directory is writable and stays out of git.

## [3.5] - 2026-10-30

An agent now keeps the architecture boundaries and product behaviors a repository protects, even when the user's request would break one, unless the user gives that protection up. Before, an agent that found the guarding test or the fix that established a behavior usually treated the request as permission and went ahead. The owner ruled on 2026-10-29 that a request which names the new behavior is not approval, because the requester may not know the protection exists: the agent points out the protection, its evidence, who relies on it, and the consequence, and asks. The consumer data format is unchanged (`ssot_format: 3`); nothing needs to catch up. Repositories wired before 3.5 keep working. The measured result used the new startup block as well as the new skills, and upgrading the skills does not edit instruction files, so to get the full effect replace the text between the `SSOT-SKILL` markers in the repository's agent instruction file with the 3.5 block (the installer prints it). Evidence and limits: `tests/trials-3.5.md`.

### Changed
- Preflight section 3 (new): before settling on an implementation, find the behaviors and boundaries the change could affect, in SSOT and in the tests, guards, and fix history of the code involved; state each affected rule ("Must preserve: ..."); for a conflict, propose a design that keeps it or ask, naming who relies on it. The former section 3 is now section 4.
- Memory model §5: what an invariant is (an architecture boundary, or a product behavior users, clients, or integrations rely on; changing one takes a person, other work needs nobody's approval); how to recover a rule from the code as a candidate (the protected outcome, its conditions, evidence that people protect it on purpose, a change that would break it); when to ask, including the approval rule above. Candidates are settled when a task needs to depart from one, not put to the user one by one.
- Closeout records protected rules found during the work as candidates, and records a departure from a protected rule as decided only when the approval rule is met, citing the user's words; otherwise it reports the conflict. Doctor checks candidates against the admission rule instead of listing them for confirmation.
- The startup block (`adapter-thin.md`, both languages) tells every agent to identify protected outcomes before changing behavior or architecture and to keep them unless the user approves the specific departure.
- Word limits rise from 3,000 to 3,300 for all `SKILL.md` files and from 8,000 to 9,500 for everything read at runtime, by the owner's decision on 2026-10-30. A trial branch had tightened about forty unrelated sentences to fit new rules into the old limits; those edits were reverted, and `CONTRIBUTING.md` now forbids rewriting unrelated rule text to make room.

### Evidence
- Held-out test on jellyfin, 1Panel, and n8n, 36 protected rules not used during design, same SSOT copies in every arm: plans that silently broke the rule fell from 58% with 3.4 skills to 33% with 3.5 (−25 points, 95% interval −42 to −8), and from 58% without SSOT. Cost per plan did not rise (1,259k input tokens against 1,337k with 3.4).
- Ordinary work in the same areas drew 3 needless questions in 36 with 3.5, against 2 with 3.4 and 0 without SSOT. That missed the 5-point limit set before the test; the owner accepted the trade.

### Not verified
- That the agent proceeds without asking again when the user's words do give up the protection, under the 3.5 wording.
- That closeout catches a crossing in a finished diff; an earlier test found no gain, and its redesign was not rerun.
- What the "Must preserve" line adds by itself, other models, more runs, and SSOTs built by a 3.5 setup.
- Mining protected rules at setup with several agents raised coverage in early runs but wrote too many overbroad rules; it is not in 3.5.

## [3.4] - 2026-10-28

Setup and catch-up now check what they write against the code. An audit of finished SSOTs on large repositories found that about 5% of the statements a task would act on were wrong and about 40% were right only in part, mostly because a statement was made too broad or a design intention was written as if it were built. The consumer data format is unchanged (`ssot_format: 3`); nothing needs to catch up. Evidence and limits: `tests/trials-3.3.md` section 6.

### Changed
- Bootstrap step 6.3: check what you wrote against the code (Doctor's Truth review) as well as running the newcomer test, and fix what they expose.
- Doctor's Truth review covers each document and names the two kinds of statement most often wrong: those with "all", "only", "every", "never", or "always", and those taken from a design document, an ADR, or a code comment. Unbuilt intent is labeled as planned.
- Doctor catch-up checks each statement it writes or changes against the code at the end of its range.
- Memory model §6: use "all", "only", "every", "never", and "always" only when the code enforces them; otherwise state the condition or the exception.

### Evidence
- On jellyfin and 1Panel, four setups per arm from the same commit, audited by a different cheap model: wrong statements fell from 7% to 2% of 272; statements with absolute words that were not correct fell from 60% to 44%. The share of fully correct statements rose from 51% to 56%, which is within the judge's own variation.

### Not verified
- Whether the documents are more complete: partly-right statements stayed at about 40%.
- More repositories, more runs, and other models.

## [3.3] - 2026-10-28

Tested on two large repositories, n8n (about 2.5 million lines of TypeScript, 26,000 commits) and zed (about 1.8 million lines of Rust, 40,000 commits), with a cheap model (`deepseek-v4.1-flash`) doing the work. Setup and everyday reading held up at this size: SSOT grew by splitting files into folders, and a task read 3 to 9 of its files, never the whole tree. Two things broke: a catch-up after a long gap could not resume, and setup could stay unfinished for good. The consumer data format is unchanged (`ssot_format: 3`); nothing needs to catch up. Evidence and limits: `tests/trials-3.3.md`.

### Changed
- Doctor catch-up works oldest first along the main line of history, a few dozen commits per segment, and says what reviewing a commit means: read every commit message, and the diff where the message or the files it touches suggest a durable fact. `reviewed_through` moves to the end of each segment once that segment's facts are written, so an interrupted catch-up resumes instead of starting over. Before, it moved only after the whole range; on a 2,007-commit gap, a 60-minute session left no progress behind. With 3.3, sessions capped at 8 minutes carried the marker to commit 500, 843, and 1,300 of 2,001.
- The marker moves last. Both 3.2 catch-ups that moved it did so before writing anything, so a session interrupted at that point would have made the next one skip facts never written.
- A catch-up keeps its working files (commit lists, scripts) outside the repository. An interrupted session had left 3.3 MB of them at the repository root.
- Setup is complete once the invariants, the open questions, and the planned changes to documents outside `SSOT/` have been put to the user; it no longer stays open waiting for the answers. Documents that still repeat SSOT's facts become one open question in the README. From a setup state that 3.2 kept unfinished for three sessions, 3.3 finished setup in 3 of 4 completed runs (2 of 2 with the final wording), 3.2 in 0 of 2.

### Not verified
- Whether SSOT makes tasks in these repositories better or cheaper. Both already ship long agent instruction files; plans with and without SSOT were similar, and token use was not lower with it.
- Whether a person finds the generated documents readable.
- Migration of a large v2 SSOT, and several people or agents writing SSOT at once.

## [3.2] - 2026-10-27

The user found that SSOT documents broke lines early: every paragraph was cut into short lines of about 70 characters. In an editor that reads as ragged text, and in Chinese a line break inside a sentence can show up as a stray space. The cause was the bundle itself. Its templates and skill files were hard-wrapped, agents copied that shape, and nothing said otherwise. All three real consumer SSOTs show it.

### Changed
- Memory model §6: write each paragraph and list item as one line, and let the editor wrap it.
- All templates (`en`, `zh`) and all of this repository's own Markdown are rewritten with one line per paragraph. The text is unchanged apart from line breaks; this was checked file by file.
- Decision and research templates list their fields (status, date, decided by) as a bulleted list, so each field stays on its own line.

### Added
- `ssot-check.py` warns when a paragraph or list item runs over three or more short lines (100 characters or fewer each), naming the lines. Lists, tables, code, comments, and deliberate line breaks (two trailing spaces) are not affected.
- `tests/test-bundle-shape.sh` fails if any Markdown file in this repository has such a paragraph, so the bundle cannot teach the old shape again.

### How 3.2 was checked
- A fresh agent set up a Chinese SSOT with 3.2 on a copy of a small repository (a 4,500-line Rust tool). Every paragraph came out as one line (prose lines average 118 characters), and the checker reported no errors and no warnings. The setup took 12 minutes.
- On two earlier SSOTs of the same repository, the new warning found 11 and 55 broken paragraphs. Joining their lines cleared every warning and changed no text.
- Checker regression tests and bundle shape tests pass; a probe file with a broken paragraph makes the bundle test fail.

## [3.1] - 2026-10-27

Two gaps found by looking at three repositories that have used SSOT for months, and at what an interrupted session loses. The consumer data format is unchanged (`ssot_format: 3`); nothing needs to catch up. Evidence and limits: `tests/trials-3.1.md`.

### Added
- `ssot-check.py` warns when a document mentions, in inline code, a file or folder that git says was deleted or moved, naming the commit and, for a move, the new path. `decisions/` and `research/` are records of the past and are not checked, and a line that names the removing commit counts as deliberate history. On three real SSOTs it found 0, 158, and 36 such mentions. In a blind sample, about 44% were current guidance pointing at code that no longer exists; the rest were deliberate history or records. The check reads only git's index and object store, so it does not run a repository's clean filters or filesystem monitor. A git failure makes the run INCOMPLETE rather than a pass. Tests cover both.
- `ssot-check.py --since <commit>` lists only removals after that commit. Closeout uses it to see what its own batch removed.

### Changed
- Preflight: a lasting rule the user states, or a settled decision whose reason exists only in the conversation, is written to its owner before the first code change, with anything not built yet labeled as planned. In a trial that interrupted the session at its first code edit, 3.0 lost such a rule in 2 of 2 runs. 3.1 had written it down, marked as planned, in 2 of 2.
- Candidate invariants are followed by default. The user is asked only when a task needs to depart from one or its meaning matters here. Setup shows the rules once and invites corrections, instead of asking for a verdict on each.
- Closeout runs the checker only when the batch changed `SSOT/` or added, moved, renamed, or deleted files or headings.
- Migration keeps `SSOT/BOOTSTRAP.md` from its first write until it is verified, so an interrupted migration reads as unfinished. A resumed migration accounts for each uncommitted change before continuing. The migration also absorbs outside documents (section 4) and runs the newcomer test, as setup does.
- `reviewed_through` is described as where the next catch-up starts, not as proof that SSOT matched the repository.
- Runtime protocol text: 6,990 to about 7,300 words, with some redundant passages removed to offset the additions.

### Not verified
- Migration beyond one small repository. One run there was interrupted and resumed, and it passed every item in its answer key (`tests/trials-3.1.md` section 3). The migrated SSOT kept nearly all of its v2 size.
- Whether the checker changes closeout behaviour: in the two trial tasks that moved files, agents on 3.0 and 3.1 both fixed every mention without it.
- Native Windows, submodules, and grafted histories in the checker.

## [3.0] - 2026-10-26

A redesign around one job: keep a repository memory that helps the next task. [DESIGN.md](./DESIGN.md) explains the evidence and the reasoning. v2 is frozen at the `v2-final` tag.

### Changed (breaking)
- The consumer `SSOT/` has one required file, `SSOT/README.md`, with `ssot_format: 3` and `language` in its front matter. It holds the project summary, a map, task routes, the invariants register, and open questions. `product.md`, `architecture.md`, `process.md`, `decisions/`, `gotchas.md`, `glossary.md`, and `research/` exist only when they have real content. Existing v2 paths such as `01-product/` remain valid.
- One shared memory model (`skills/ssot-preflight/references/memory-model.md`) defines what to store, what to leave out (restated code, single-task proofs, edit history, status about the docs), current versus planned, invariants, and the writing rules.
- Closeout writes nothing when no durable fact changed: no history rows, timestamps, or markers.
- Every invariant must be explained inside `SSOT/`, and the checker enforces this.
- Catch-up on past commits moved into `ssot-doctor`. It starts from the optional `reviewed_through` front-matter field, and only a catch-up or a setup moves that field.
- `ssot-audit` and `ssot-skill` are compatibility names that route to the four lifecycle skills.
- A v2 `SSOT/` is read but not written until it is migrated with `$ssot-bootstrap` (one commit, with the user's agreement). Until then, closeout lists what should be recorded instead of writing it.
- Repository scripts, hooks, CI, or tests that call v2 bundle files (`ssot-lint.sh`, `ssot-migrate.py`, `run-tests.sh`) fail after the upgrade. The migration repoints them to `ssot-check.py`.
- The invariants register holds the lasting rules people set ("never X", "always Y"). One-time choices are decision records. Both need the user's agreement to change.

### Removed
- Per-area coverage states, completeness checklists, the Q01–Q21 matrix, and `converged` certification.
- `STATUS.md`, `HISTORY.md`, `.bootstrap/` review archives, `_manifest.md` inventories, tracking baselines, and catch-up audits after each protocol release.
- The 400 KB `ssot-lint.sh`, its migration helpers, and their tests.
- `skills/SKILL_STYLE.md`, which is now part of `CONTRIBUTING.md`. The installer removes the copy it installed earlier.

### Added
- `ssot-check.py`: a read-only Python checker for the entry file, links and GitHub heading anchors (including CJK), and the invariants register. It counts reading budgets in characters. Its last line always states PASS, FAIL, or INCOMPLETE; exit code 3 (INCOMPLETE) means it crashed or could not examine part of the tree, and is never a pass.
- `install.sh --ref <branch|tag>` (or `SSOT_REF`). `--ref v2-final` installs the frozen v2 protocol.
- CI budgets for everything agents load at runtime (8,000 words), the entrypoints (3,000 words), templates, the checker, and `skills/`. Before 3.0 these were about 110,000 words and 1.9 MB.
- `DESIGN.md`, and protocol change rules in `CONTRIBUTING.md`.

### How 3.0 was checked
Method, per-question scores, and limits are in `tests/trials-3.0.md`.

- **Behavior trials, run on copies of one real consumer repository (a desktop application):**
  - Six real maintainer tasks were answered by fresh agents in three set-ups: v2.86 with the original SSOT, v3 after an agent-run migration, and no SSOT at all. The migration used an earlier draft of the migration procedure. The final procedure added steps (keeping `GAP-` IDs, handling `apex-maxim` rows, sorting before deletion, repointing tooling), and of those only the tooling step was run against the trial copy. A blind judge scored every answer against an answer key built from the code.
  - Must-have points: v3 94%, v2 97%, no SSOT 84%.
  - Answers that pushed unrelated documentation chores onto the user: v2 had 14 such items, mostly protocol catch-up and audits. v3 had 6, all from one migration gap (tooling still calling `ssot-lint.sh`); that gap is now covered by a migration step.
  - After that migration step was applied, two of the tasks were re-run and re-judged blind. v3 scored full marks with no noise and the highest usefulness (9 and 9, against v2's 7 and 8). The other four tasks were not re-run.
  - Token use was the same in all three set-ups. 3.0 does not make reading cheaper.
- **Closeout trials:**
  - An internal refactor wrote nothing to SSOT.
  - A user decision (a shorter retention period) was recorded in the right owner and a new decision record, with the old decision kept as history.
- **Conflict trial:** asked to add a pop-up that a confirmed rule forbids, both v2 and v3 agents stopped and asked. v3 used about a third fewer tokens.
- **Setup from scratch** on a second, smaller repository (a web application with its own agent instruction file): 7 documents, about 50 KB. An independent newcomer test answered 5 real tasks correctly, and the procedure gaps the run reported were fixed. Its findings included two real bugs in that application, which the documents now record as open questions.
- **Local suites:** checker regression tests, bundle shape with budgets, installer end to end (including `--ref`), Mermaid parsing of the template diagrams, and ShellCheck.
- **Not verified:**
  - The final migration procedure end to end. The trial used an earlier draft, and only one of the later steps was run.
  - Migration of a second consumer repository, including the larger ones.
  - Long-term maintenance over many batches.
  - Other agent harnesses.
  - Diagram rendering.
  - macOS or Windows runners beyond CI.

## [2.56–2.86] - 2026-07 to 2026-10 (frozen as `v2-final`)

### Added
- Adjudication boundary register (v2.64): `SSOT/README.md` gains a canonical `## 裁决边界` / `## Adjudication boundary` section registering the rules whose meaning an agent must not change unaided —`arch-invariant` / `product-promise` / `process-rule` rows (`INV-NN`) and `apex-maxim` rows (`CLAUDE-MAXIM-N` / `CORE-RULE-N`). Rows are pointer-sized (one-line name, one resolving owner anchor, `Established by`, closed `State` enum); agents may change what a rule governs but not the rule itself — meaning/scope/state changes require a `decisions/` entry or explicit user directive, and reality-vs-rule conflicts file `ADJ-` instead of silently rewriting. Agents register `candidate` rows; only human authority confirms. Confirmed/core-ref owner bodies carry the registry ID at the rule anchor; the standalone apex-maxim registry (`intent-ownership.md §1.1`) folds into the unified table at ≥2.64. Enforced by preflight's boundary gate, closeout's promotion duty (`update-routing.md §1.7`), and doctor rows `[INV-REGISTRY]` (16E) / `[INV-BODY]` (16F); bootstrap seeds the register from the root constraint file, binding decisions, and user-confirmed product promises.
- Append-only batch write log (v2.63): `SSOT/HISTORY.md` is a sibling register of `STATUS.md` — STATUS owns coverage claims, HISTORY owns write provenance. Every substantive batch that runs a writing skill (bootstrap/closeout/audit/doctor) appends exactly one row `| Date | Commit | Actor | Result | Touched | Note |`; a substantive `no-op` still logs, distinguishing "checked, nothing durable" from "never checked". Rows are append-only (correct by appending), carry pointers only (never restated facts), and are schema-checked by the version-gated `[HISTORY-LOG]` lint. Bootstrap creates the file header-only and appends its first `wrote: skeleton` row on completion; audit reads rows as reconciliation evidence and logs one row per completed segment; `ssot-migrate.py` creates the header for upgrading consumers.
- Bound claims (v2.62): the two coverage ledgers can no longer contradict —`[LEDGER-CONSISTENCY]` fails a file stamped `intent_recovery: covered` under a `gap`/`stale`/`unknown`/`conflict` area row (partial under a weak area warns), and `[GAP-BLOCK]` turns an Open Gaps Blocking/retrigger cell into a machine-readable contract so an open row blocking `converged`/`covered`/ `tracked_*` forbids that claim while open.
- Reviewed baselines and artifacts (v2.62): `[BASELINE-REVIEW]` warns when a live `tracked_commit`/`tracked_session`/`tracked_skill_version` has no Stop Review Gate row naming it; `[SKILL-VERSION-BINDING]` fails a `tracked_skill_version` that outruns every installed/pinned artifact a fresh checkout would see; `[RECONFIRM-TOKEN]` requires dated, on-branch `re-confirmed at` tokens.
- Reference, evidence, and lifecycle integrity (v2.62): `[REF-RESOLVE]` warns on unresolvable inline-code repo paths and `path::symbol` pins (`retired:`/`historical:`/`deleted:` markers exempt real history); `[EPHEMERAL-EVIDENCE]` warns on `/tmp`/cache evidence pointers; `[GIT-TRACKED]` warns on git-ignored or untracked SSOT files (canonical `release/` collides with common ignore rules); `[SUPERSEDE-LINK]` warns on superseded records naming no successor. Large failure/warning sets now end with a per-check `[DIGEST]` count.
- Verification layer and worktree boundary (v2.62, closeout): `update-routing.md §1.5` requires classifying each user-visible claim as `user-path`/`proxy`/`unexercised` and routing unexercised paths to a durable owner — install + unit tests + screenshot is not a user-journey proof — and requires ending a substantive batch committed or with a visible named reason, since a dirty worktree is the next batch's contamination.
- `ssot-migrate.py` (v2.62): migrates legacy lean STATUS tables to the canonical Appendix-A schemas in place (keyword column remap, generated `GAP-`/`ADJ-`/`CAP-` stable IDs, owner↔route dual-fill) and backfills missing record frontmatter keys; `--dry-run` previews the rewrite.
- Source references must resolve (v2.62): reader-quality.md §2 floor item 6 requires inline-code source pins to resolve in the current tree or carry an explicit `historical:`/`retired:`/`deleted:` marker, preferring `path::symbol` over drifting line numbers — a page teaching a deleted runtime is worse than an honest gap.

### Fixed
- v2.86: Scope the protocol-version gate to SSOT writes instead of stopping all work, and give closeout its own entry check (missing SSOT, active bootstrap, protocol behind) so it never writes into a vacuum or an unaudited STATUS.
- v2.85: Remove author-environment assumptions: stale-install check no longer names a private checkout path; surface/symbol/failure anchors fit libraries, CLIs and jobs, not only web apps; the unfounded Playwright doctor claim is gone; version-binding lint finds any agent's install and compares against the newest artifact instead of the oldest.
- v2.84: Define an independent reviewer once and give a no-deadlock path when none is available; bootstrap, area-model, Doctor and session templates now defer to status-protocol §6 instead of demanding independence in more places than it does.
- v2.83: Make bootstrap an offered, user-authorised step when SSOT is missing, so an unrelated task is not blocked behind a multi-session setup; adapter blocks and entry scenarios carry the decline path.
- v2.82: Preserve consequential product, process, and operating decisions even when reversible or local, while keeping routine edits out of the decision register.
- v2.81: Distinguish retirement without replacement from supersession; preserve history and validate real successor routes across nested record collections.
- v2.80: Reconcile scoped coverage and single-level architecture rules; validate scope owners, exact reviews, and non-applicable roll-ups without inventing directories.
- v2.79: Preserve useful contextual vocabulary explanations without duplicating authority; consolidate their writing rule in reader-quality instead of sentence and word limits.
- v2.78: Generate native Mermaid comments, reject invalid HTML markers inside diagram fences, and parse every bilingual template diagram in CI.
- v2.77: Retain bootstrap review evidence and referenced exploration records; determine unfinished setup from active phases and completion evidence rather than directory presence.
- v2.76: Bound adapter diagnostics to the managed block while preserving handwritten startup rules and legacy generated-file checks.
- v2.75: Make the documented single-owner architecture layout usable without fabricated domain/view directories, preserving complete inventories and reader review.
- v2.74: Make bilingual architecture and research templates emit canonical state and registry tokens instead of translated or unrelated confidence scales.
- v2.73: Allow research evidence retention, supported-claim promotion, and unresolved-claim preservation together, with one authority per conclusion.
- v2.72: Diagnose actual SSOT consumption across harnesses, separate missing observations from proven misses, and honor existing scoped repair authorization.
- v2.71: Replace arbitrary entrypoint word/table limits with task-complete skill guidance and preserve necessary procedures, knowledge, and recovery routes.
- v2.70: Use the canonical Pending Captures schema and lifecycle everywhere while preserving frozen historical capture records.
- v2.69: Bind audit baselines to fixed, fully reviewed ranges; preserve unread sessions, resumed content, merged history, and reverted events.
- v2.68: Allow scoped Doctor diagnostics despite unrelated structural debt while preserving every relevant pass and coverage gate.
- v2.67: Match knowledge confidence to authorized intent, static structure, observed execution, and external contracts instead of a code-only evidence hierarchy.
- v2.66: Scope adjudication blockers to decision-dependent actions, preserving independent work, existing human decisions, and confirmed constraints.
- v2.65: Unify audit reviewer selection with the scoped review policy; ordinary catch-up no longer imposes a second independent-review requirement.
- Faceted-layout migration checks destinations that become occupied after a parent directory moves, preventing existing owner documents or domain indexes from being overwritten. Domain numbering reserves prefixes in both layouts.
- Legacy STATUS migration preserves column meanings, escaped pipes, and existing stable IDs; rewrites table separators; avoids duplicate generated IDs; and leaves other sections and fenced examples untouched. Named capture IDs no longer crash migration, and exhausted ID space fails before writing.
- Bundle link checks now return failure for missing files instead of printing an error followed by a passing summary, including script links and links with fragments or queries. Migration regressions run in CI.
- Consumer agent instructions now share one marked routing block between the installer and bilingual bootstrap templates. The entry distinguishes substantive work from trivial tasks, preserves conditional audit/Doctor routing and review requirements, and reports unavailable skills explicitly. Installation rejects a missing or malformed block before replacing files.
- Open Gaps actionability now reads the canonical columns — Responsible owner from column 6, Blocking/retrigger from 7, Resolving route from 8 — and emits real file line numbers. The previous mapping read the Question column as the owner and the Blocking column as the route, failing every real row (55 false FAILs observed across two consumers).
- Schema migration is a first-class route: per-row Open Gaps actionability runs only against the canonical 8-column table; a legacy lean table produces one migration WARN pointing at `ssot-migrate.py` instead of dozens of misleading per-row FAILs restating one schema debt.
- `COVERED-PLACEHOLDER` no longer strips inline code before judging table-cell emptiness: code-only cells and legitimate reader-substitution notation (`` `path/<segment>` ``) are content, not placeholder residue.
- `META-LEAKAGE` no longer treats protocol machinery as leakage when the machinery is the subject — records directories get the base token set only, and inline-code operational mentions (`$ssot-preflight` invocations) are stripped before matching.
- `tracked_*` baseline fields are extracted from their own STATUS rows instead of the first backtick-hex in the file, so an earlier table's hex value can no longer be mistaken for the commit baseline.
- Lint test assertions can no longer pass vacuously: `assert_no_fail_tag` / `assert_has_fail_tag` scope to the `[FAIL] N` section instead of grepping for the impossible adjacent string `[FAIL] [TAG]` — the hole that let the column-mapping bug ship. Fifteen assertions across both test files fixed.
- Removed a gawk regex-escape warning emitted on every lint invocation.
- Project upgrades now recognize the pre-marker `SKILL_STYLE.md` shipped by older complete SSOT bundles, adopt it safely, and still refuse unrelated shared-root files with the same name. The installed Doctor self-test now recognizes the selected-language flattened template layout instead of reporting the absent source-only `en/` and `zh/` directories as failures.

### Added
- Graduated coverage: `partial` is now a first-class Area Status value — honest partial credit between `gap` and `covered` (owner README + writing floor + Doctor L1 clean + a scoped self-review), requiring no cold review. The v2.60 review blockers now gate `covered` only, so consumers with strong content can bank incremental wins instead of stalling at all-`gap`.
- Freshness floor: a conditional gate binds `covered`/`partial`/`converged` claims to a fresh `tracked_commit` baseline; a stale claim without a same-task scoped re-confirmation demotes to `stale`, and lint FAILs a `converged` STATUS whose baseline is behind `HEAD` (WARN below). The re-confirmation exemption is machine-checkable: a Stop Review Gate row noting `re-confirmed at <HEAD-sha|worktree>` exempts a below-`converged` claim (worktree counts uncommitted content as fresh), closing the "infinitely-renewed `partial`" loophole; the check parses the gate tolerantly so a leaner consumer table still qualifies.
- Large-repo coverage (opt-in): the Area Status table accepts scoped `<area>/<scope>` rows and an optional `Coverage depth` column, with the 17-row baseline kept as the honest computed roll-up (weak child blocks the parent; `[STATUS-AGGREGATE]` on over-claim). Single-tenant repos are unchanged.

### Changed
- Single-owner applied to the protocol itself: the CAP-row 8-column schema is owned solely by `status-protocol.md §8 Appendix A` (`promotion-rationale.md` keeps only move semantics); `architecture.md §3` is the sole normative owner of "what a domain owns", with `reader-quality.md §4` and `area-model.md §2.2` deriving instead of restating. Doctor's stop condition is now self-evaluable and non-circular.

### Changed
- Lifecycle `SKILL.md` bodies are distilled back to activation prompts (60 words or fewer outside the preflight router), while the detailed v2.60 procedures remain in on-demand references. The active bundle and generated reader surfaces now use one STATUS term, `tracking baseline` / `追踪基线`, instead of forking that concept across coverage and waterline synonyms.
- A cross-layer `Q01`-`Q21` quality, risk, and governance profile now prevents silent omissions across accessibility, locale, usability, performance/cost, concurrency/consistency, continuity, compatibility/migration, data recovery, isolation, threats/abuse, supply chain, offline delivery, compliance, privacy/data governance, safety/harm, human oversight, fairness/transparency, maintainability, environmental impact, output validity, and commercial/financial/entitlement integrity. `STATUS.md` keeps the pointer-sized disposition register; product, architecture, process/evidence, and record owners keep the facts. Doctor rejects missing rows, unresolved applicable layers, and misuse of `not_applicable` for unimplemented behaviour.
- The reader contract now explicitly serves an implementation delegator who may not read source code. Common, process, record, glossary, root, STATUS, and product profiles gain the missing plain-language scene, delegated action, retry/concurrency, affected-scope, exposure, naming, acceptance-route, disposition, and non-page-surface questions. The `LA` family is renamed `Plain-language clarity` to avoid confusing prose readability with product accessibility.
- Process, records, glossary, the SSOT root, and STATUS now have exact lightweight review profiles of 46, 46, 38, 37, and 32 items. A passing artifact gives every exact row a plain answer and preserves a finite target matrix for every real process child, record collection and entry/anchor, glossary term owner, root, or STATUS target. Current scope, Area Status, and Q fingerprints, complete target coverage, fitting evidence, and stated limits prevent row counts or resolving links from creating a false-green `covered` claim.
- Durable records now keep two independent state axes: whether the knowledge record itself is current, and whether the decision, research adoption, bug, hazard, or debt it describes is still active. Collection indexes mirror both axes and route every ID exactly once to its unique entry owner, including stable anchors for topic-aggregated gotchas.
- Bug failure truth now includes `open` beside `fixed` and `recurred`, so a confirmed unresolved defect keeps an honest failure owner instead of being mislabeled as technical debt.
- Process owners now explain the method, nearest rejected alternative, invariants, rationale, and accepted trade-offs before commands. They also keep a finite eight-field inventory of stable assets they create, read, change, verify, hand off, or retire. The glossary uses one six-family inventory with exact entry routing instead of overlapping hard-coded lists.
- The seventh architecture view is now wired through preflight structure, bootstrap creation/fill order, template inventory, and Doctor rather than existing only in the view template and covered-scope lint.
- A real consumer cold read exposed a STATUS false-green: a gap could be named without telling a non-coding reader whether their task was affected, when it became blocking, or where ownership lived. The STATUS profile now includes `S08`; the exact bilingual Open Gaps schema records affected scope/task, blocking or retrigger condition, responsible owner, and resolving route; and Doctor enforces `[STATUS-GAP-ACTIONABILITY]` for real v2.60 gap rows while preserving empty starter rows. Owner and route must be clickable Markdown links or explicit `$ssot-*` routes; a bare record ID is not actionable.
- `STATUS.md` now follows one exact `S01`-`S11` register contract. It records the tracking baseline, all 17 area states, source absorption, reviewed startup references, stop authorisations, actionable adjudications and gaps, `Q01`-`Q21`, pending captures, and deliberate source exclusions. Cells remain pointer-sized; passing process, records, and glossary rows link exactly one current scope artifact, while convergence additionally requires matching root and STATUS artifacts.
- The same consumer run exposed four over-broad generic heuristics. STATUS Notes-ledger detection now reads only the `Notes/备注` cell, not an explicit Date column; aggregate contradictions read only declared stop/summary surfaces, not Open Gaps rows; and README derived-state detection distinguishes explicit latest-verification mirrors from narrative use of a literal image tag such as `latest`. Generic KISS table-density warnings now exclude protocol-owned `_manifest.md` registers, which remain governed by their dedicated completeness and inventory checks.
- Reader-quality protocol v2.60 closes the false-`covered` path exposed by real consumer regeneration: product maturity/evidence semantics now have one live owner, cold review uses six exact tasks, 16 scored leaves, five cold proofs, and exact completeness profiles (>=29/32 plus family and implementation-delegator floors). A failed reader surface must be repaired bottom-up and re-reviewed until source, installed bundle, manifests, prose, and consumer tracking baseline agree. Protocol version `2.59` -> `2.60`.
- Covered product roots now carry a finite, stable-ID inventory across twelve classes: pages, navigation, entry modes, controls, settings, diagnostics, external channels, commands, public interfaces, output artifacts, notifications, and help/onboarding. Covered architecture roots classify every direct owner, register unique technical surfaces, bridge product surfaces to runtime owners, and include deployment/observability in the default cross-owner route.
- Document-quality lint no longer accepts a linked file merely because it contains `no-more-required-changes`. When `tracked_skill_version` is `2.60`, it validates the review scope/version/probes/score/verdict and body evidence, plus product `[SURFACE-INVENTORY]` and architecture `[OWNER-INVENTORY]` completeness. Review artifacts now carry a separate normalized STATUS-Q fingerprint, so a Q disposition change expires both product and architecture reviews while an unrelated STATUS tracking-baseline edit does not. Architecture kind dispositions must name the exact registered surfaces of that kind; unknown, wrong-kind, duplicate, and omitted IDs are rejected.
- Product/architecture review evidence is now path-bound and authority-bound: exact frontmatter identifies the reviewer and authorised area, every target and evidence link stays inside consumer SSOT and outside review artifacts, visible verdict and required changes agree, and one matching STATUS stop row closes a passing covered claim. Absolute, missing, symlinked, self-referential, comment-only, or fenced-code evidence cannot produce a pass.
- Product and architecture documentation now follow a v2.59 reader-quality contract: KISS means the shortest reliable path to understanding, narrative explanation precedes reference tables, product intent precedes architecture, and exact scaffold-heading checklists are replaced by semantic cold-reader questions. Protocol version `2.58` -> `2.59`.
- The universal product/architecture manifest template is replaced by five location-specific archetypes (`product-root`, `product-collection`, `architecture-root`, `architecture-views`, `architecture-domain`). Covered claims now fail on placeholder/empty manifests, heading-only narrative, missing default reader surfaces, or missing first-screen domain diagrams.
- Product completeness now includes real surface inventory, user/object lifecycle, choice/control/recovery/diagnosis journeys, trust/privacy posture, and separate product-maturity versus evidence-fidelity axes. Architecture completeness now includes state/data, contracts/trust, and failure/recovery views in addition to operating model, critical journeys, and current-target-gap.
- The v2.57 faceted-layout contract is now end-to-end: bootstrap templates and current references use numbered physical paths, Doctor resolves and enforces canonical facets at the v2.57 waterline, and the migration helper is idempotent and path-boundary-safe on real canonical trees.
- Research-record lint now accepts valid YAML block-list `promotion_targets` while preserving empty-value failures; Bootstrap and Doctor also share the four independent-review exceptions owned by `status-protocol.md`.
- `ssot-closeout` / `ssot-audit` now force a durable disposition for user-visible bug-fix, hotfix, regression-fix, and caveat-heavy batches: closeout must adjudicate bug packetization, fix-commit disposition, caveat extraction, and overdue waterlines instead of leaving the outcome only in closeout prose, walkthroughs, plans, or git history. Protocol version `2.57` -> `2.58`.
- `ssot-doctor` guidance and `ssot-lint.sh` now flag placeholder debt / follow-up wording more aggressively, especially when owner files or STATUS summaries still say `TODO debt`, `Pending action`, or equivalent without a durable owner / trigger / guard.
- `install.sh` now installs ownership-marked bundle-level companion files such as `skills/SKILL_STYLE.md` into the target skills root, refuses to overwrite unowned collisions, and removes only bundle-owned copies.
- `ssot-preflight` area model now makes the v2.57 numbered faceted layout the canonical physical SSOT layout: `01-product/`, `02-architecture/`, `03-process/*`, and `04-records/*`. Legacy unnumbered paths remain readable compatibility input, but concrete protocol paths, links, template targets, CORE-REF examples, and upgrade targets use numbered paths. Protocol version `2.56` -> `2.57`.
- `ssot-preflight` gate floor narrowed (v2.56): the mandatory read is now `SSOT/STATUS.md` plus `SSOT/README.md` as the project-specific router. `product/README.md` and `architecture/README.md` are read only when the task-entry map routes the task to them, with a thin-router fallback to both trunks when the map is missing or does not route the task. The open-risk scan narrows to routed owners plus `STATUS.md ## Open Gaps`; full `tech-debt/` / `bugs/` / `gotchas/` directory scans become agent self-decision. `area-model.md §4` becomes the single owner of trunk-read routing. Protocol version `2.55` -> `2.56`.
- Scrubbed origin-project references from shipped skill assets: replaced cold-agent-sim cycle transcripts with one synthetic example using a fictional project; replaced origin-project implementation paths in `ssot-preflight/references/` and `ssot-audit/references/` with synthetic placeholders; replaced real commit SHAs in audit history with `<commit>`.
- AGENTS.md commit discipline now explicitly scopes to maintainers and points external contributors at `CONTRIBUTING.md`.
- SKILL_STYLE.md now records the `ssot-preflight` gate/router exception alongside the bundle-wide anti-patterns.

### Added
- Conditional bilingual `03-process/operations/` and `03-process/security-and-compliance/` templates separate day-two service operation and recurring security/compliance evidence from deployment and architecture mechanism owners. Small repositories must record a named non-applicability disposition instead of silently omitting either concern.
- Ten dedicated English/Chinese process, deployment, records, glossary, gotcha, bug, and technical-debt templates. They lead with the implementation-delegator's decision and next action, keep protocol guidance in author-only comments, preserve table-independent narrative, and route indexes to unique entry owners. Phase 1 now creates the complete `03-process/`, `04-records/`, and `glossary/` root/index skeleton while deferring record and term entries until concrete evidence exists.
- Paired English/Chinese deployment-and-observability view and structured cold-reader review templates, with regression fixtures for forged verdicts, scope drift, below-threshold scores, and missing owner/surface inventories.
- Paired English/Chinese exact-scope review templates for process, records, glossary, root, and STATUS, including current-content fingerprints, exact completeness rows, semantic truth samples, required-change accounting, and claim-specific STATUS authorisation.
- `ssot-preflight/references/reader-quality.md`, document-quality lint mode, source/rendered template contract tests, and task-based product/architecture comprehension gates: six exact tasks, sixteen scored leaves, five hard proofs, a score of at least 29/32, family and implementation-delegator floors, no critical truth error, and no unresolved required change.
- `ssot-audit/assets/scripts/migrate-faceted-layout.py`, installed with the audit skill, migrates legacy consumer `SSOT/` trees to the v2.57 faceted layout, rewrites Markdown links/literal paths, preserves legacy domain indexes, and exits explicitly on source/target conflicts.
- `tests/test-faceted-layout-migration.sh` plus CI wiring cover dry-run, successful migration, conflict handling, and helper syntax.
- `What is SSOT?` section in `README.md` / `README.zh.md` that explicitly defines "Single Source of Truth", explains how the principle maps to `SSOT/` in this skill, and reiterates that code/schema/tests remain the truth for current implementation (bilingual parity preserved).
- `Requirements` and `Uninstall` sections in `README.md` / `README.zh.md` (bilingual parity preserved).
- OSS hygiene files: `SECURITY.md`, `CODE_OF_CONDUCT.md`, `.github/ISSUE_TEMPLATE/bug_report.md`, `.github/ISSUE_TEMPLATE/feature_request.md`, `.github/PULL_REQUEST_TEMPLATE.md`.
- `install.sh` bash-4+ guard with a macOS-specific `brew install bash` hint, plus `SSOT_SKILL_REPO_URL` env override for forks.
- `tests/test-bundle-shape.sh` now resolves links via portable `python3 os.path.realpath` instead of GNU `readlink -f`.
- `.github/workflows/ci.yml` runs `bash-syntax`, `bundle-shape`, and `installer-e2e` jobs on `ubuntu-latest` and `macos-latest`.

### Removed
- Obsolete `workflows/intent-recoverability-loop.workflow.js` (and the now-empty `workflows/` directory).

## [2.55] - 2026-07-03

`semantic_impact: medium` -- adds **benchmark** as an independent engineering process owner under `03-process/benchmark/`. Benchmark now owns current suites, canonical workloads, metrics, environments, runner commands, floors, comparison rules, trend interpretation, known gaps, and links to product / architecture / release decisions. `testing/` stays focused on correctness checks and gates; `04-records/research/` keeps one-off benchmark studies until stable rules are promoted.

### Changed
- **`VERSION`** -> `2.55`.
- **`skills/ssot-preflight/SKILL.md`** `metadata.protocol_version` -> `2.55`.
- **`area-model.md`**, source-material routing, closeout, commit-audit, and conversation-audit now distinguish correctness testing, stable benchmark policy, and research evidence packets.
- **`ssot-doctor`** documents `[BENCHMARK-OWNER]` and `[BENCHMARK-LEDGER]` semantics so benchmark facts are not hidden in `testing/` and benchmark owners do not become chronological run logs.

### Added
- `benchmark-readme.md` bootstrap template in both `en/` and `zh/`.
- Root `SSOT/README.md`, `STATUS.md`, bootstrap manifest, recon, and template index support for the benchmark process area.
- `ssot-lint.sh` `[BENCHMARK-OWNER]` checks for missing faceted benchmark owner and obvious benchmark floor / trend facts hidden in `testing/`, plus `[BENCHMARK-LEDGER]` WARN heuristics for dated benchmark run logs.
- Lint smoke tests for missing benchmark owner, valid benchmark owner, benchmark facts hidden in `testing/`, and benchmark run-log warnings.

## [2.54] - 2026-06-30

`semantic_impact: medium` — adds **research / POC records** as a first-class records area under `04-records/research/`. Research records preserve questions, methods, environment, evidence, negative findings, boundaries, reusable claim rows, and promotion targets as structured evidence packets. Product, architecture, decisions, and other owners only absorb claims after promotion; raw source material remains governed by the source-material lifecycle rules.

### Changed
- **`VERSION`** -> `2.54`.
- **`skills/ssot-preflight/SKILL.md`** `metadata.protocol_version` -> `2.54`.
- **`ssot-preflight` / `ssot-closeout`** now distinguish research records from authority mirrors and require explicit disposition when a task produces research or POC evidence.
- **`ssot-doctor`** documents mechanical research-record checks rather than semantic judgement of research quality.

### Added
- `research-readme.md` and `research-entry.md` bootstrap templates in both `en/` and `zh/`.
- Bootstrap skeleton support for `SSOT/04-records/research/README.md` without creating sample research entries.
- `ssot-lint.sh` `[RESEARCH-RECORD]` checks for canonical location, `NNNN-<slug>.md` numbering, required frontmatter, promotion/recheck fields, and mechanical boundary / `do_not_use_for` signals.
- Lint smoke tests for valid research records, missing required fields, top-level `SSOT/research/`, and unnumbered entry names.

## [2.53] - 2026-06-30

`semantic_impact: medium` — adds the **active recommendation / non-silent deferral floor**. Preflight now classifies task-overlapping open risks as `fix-now`, `recommend-now`, `defer-visible`, or `ignore-for-scope`; closeout must carry each recommendation to a visible disposition. Deferrals must keep an owner or owner record, reason, closure condition, revisit signal, verification guard, and next concrete action. Lint adds `[SILENT-DEFERRAL]` for obvious future-work wording without owner/reference or retrigger signals.

### Changed
- **`VERSION`** -> `2.53`.
- **`skills/ssot-preflight/SKILL.md`** `metadata.protocol_version` -> `2.53`.
- **`ssot-preflight` / `ssot-closeout`** now require classification and closeout disposition of task-relevant risk recommendations.
- **`area-model.md`** `tech-debt/` rules now state active debt is not passive backlog and active entries should expose next action / must-handle triggers on the first screen.
- **`doctor.md`** documents the new `[SILENT-DEFERRAL]` tag and extends the open-risk deterministic summary.

### Added
- `ssot-lint.sh` check for `[SILENT-DEFERRAL]`, scoped to obvious "later / someday / future work" wording and locked-language equivalents that lack owner/reference or retrigger signals.
- Lint smoke tests for silent deferral failure and owner-backed deferral pass.

## [2.52] - 2026-06-30

`semantic_impact: medium` — adds the **open-risk and temporary-surface floor**. Preflight now surfaces task-relevant active debt and gotchas, open or recurred bugs, and open gaps; closeout must either close, defer with owner/trigger/guard, or create a next action. Temporary fallback, compat shim, later-remove, TODO/FIXME/HACK, and waiver surfaces must be registered with owner, reason, closure condition, revisit signal, and verification guard. Lint adds deterministic checks for markdown fence balance, ADR/debt closure fields, covered-area placeholder residue, STATUS aggregate contradictions, unowned gap rows, and pending-action text hidden inside resolved capture sections. Bundle-shape adds public hygiene guards for local paths, origin-project names, real commit SHAs, and unclosed Markdown fences.

### Changed
- **`VERSION`** -> `2.52`.
- **`skills/ssot-preflight/SKILL.md`** `metadata.protocol_version` -> `2.52`.
- **`ssot-preflight` / `ssot-closeout`** now require task-relevant open-risk recommendations and closeout disposition.
- **`area-model.md`** `tech-debt/` rules now define temporary-surface registration fields.
- **`architecture.md` §16** now uses one owner per Capability -> Surface registry row plus link-only mirrors instead of duplicate product / architecture registry rows.

### Added
- `ssot-lint.sh` checks for `[MARKDOWN-FENCE]`, `[ADR-CLOSURE]`, `[DEBT-CLOSURE]`, `[TEMP-SURFACE]`, `[COVERED-PLACEHOLDER]`, `[STATUS-AGGREGATE]`, `[GAP-OWNER]`, and `[CAPTURE-LIFECYCLE]`.
- Lint smoke tests for the new deterministic checks.
- Bundle-shape checks for unclosed Markdown fences and public OSS leakage patterns.

## [2.51] - 2026-06-23

`semantic_impact: medium` — adds the **reader-scaffolds floor**. The v2.47–v2.50 floors all subtracted (cut shadow ledgers, table-only intent, language-drift H1s, missing directory maps); v2.51 adds the additive complement: four owner-template structural slots a cold agent uses to orient itself after routing — `## Walkthrough`, `## Easily confused with`, `## Out of scope`, `## See also` — plus a new `glossary-entry.md` per-term template, diagram-typing comments in architecture Mermaid blocks, and a KISS mini-card permitted form for first-mention canonical vocabulary that does not violate `15F [VOCAB-PROSE-FORK]`. Self-reviewable per `status-protocol.md §7.1`; no doctor stop-review required.

### Added
- **Owner-template structural slots** — every owner-archetype template in `skills/ssot-bootstrap/assets/templates/{en,zh}/` (`ssot-readme.md`, `architecture-readme.md`, `architecture-domain-readme.md`, `product-readme.md`, `dir-readme-map.md`) now carries `## Walkthrough`, `## Easily confused with`, `## Out of scope`, `## See also` H2 slots.
- **`glossary-entry.md` template** (en + zh) — per-term glossary entry skeleton: one-sentence positive definition, `Used in` inverse index, `Not to be confused with` boundary list, source pin.
- **`architecture-domain-readme.md`** gains a `### Walkthrough (canonical flow)` H3 above the Runtime Flows table (required when the table is non-empty).
- **`product-readme.md`** gains a `## Capabilities ↔ Journeys diagram` mermaid block.
- **Diagram-typing comments** — first mermaid block in each architecture template carries `<!-- diagram_type: component -->`; templates surface the one-type-per-block rule via an inline notice.
- **KISS mini-card permitted form** (`SKILL_STYLE.md` reader-scaffolds section): first-mention canonical vocabulary may appear inline as `**Term** (def: <≤ 15-word clause> → [CORE-REF: glossary/<term>.md])` without violating `15F [VOCAB-PROSE-FORK]`.
- **Doctor rows** `15R [WALKTHROUGH]`, `15S [BOUNDARY-DISAMBIG]`, `15T [OUT-OF-SCOPE-LINK]`, `15U [DIAGRAM-TYPE-TAG]`, `15V [DIAGRAM-FIRST]` appended to `skills/ssot-doctor/references/doctor.md` §2.2. All five ship WARN-only; `15R` graduates to FAIL next cycle.
- **`ssot-lint.sh` checks 18–22** mirror the five new doctor rows (structural grep only — heading presence, mermaid fence inspection, first-screen line-count check). No NLP.
- **Audit ledger entry** `### v2.51` added to `skills/ssot-audit/references/current-upgrade.md` with the semantic-impact-medium checklist.

### Changed
- **`VERSION`** -> `2.51`.
- **`skills/ssot-preflight/SKILL.md`** `metadata.protocol_version` -> `2.51`.
- **`skills/ssot-bootstrap/references/bootstrap.md`** §3.7: added `**Reader scaffolds (v2.51).**` subsection (four slots, per-archetype minimum scaffold set, additive-vs-subtractive framing).
- **`skills/SKILL_STYLE.md`**: added `## Reader scaffolds (v2.51)` section (six-slot summary, why no `archetype:` frontmatter, diagram typing, KISS mini-card permitted form).
- **`skills/ssot-preflight/references/area-model.md`** §2.0: required-answer list extended from five questions to six (added "Where can I go next, and what does this owner explicitly NOT answer").
- **`skills/ssot-preflight/references/area-model.md`** §2.3: added `**v2.51 entry template.**` note pointing new glossary entries at `glossary-entry.md`; pre-v2.51 entries grandfather in until next touched.
- **All five owner-archetype templates**: writing-style banner upgraded from one-line `> Writing style: ...` to multi-line form that names the reader-scaffold slots and links both `bootstrap.md §3.7` and `SKILL_STYLE.md` reader-scaffolds section.
- **`skills/ssot-bootstrap/references/templates-index.md`**: added `glossary-entry.md` row.

### Compatibility
- `semantic_impact: medium` — self-reviewable; consumers bump `tracked_skill_version` to `2.51` without an external reviewer.
- All five new lint checks ship as WARN-only in this cycle so existing converged SSOTs do not regress on the upgrade itself.
- `15R [WALKTHROUGH]` graduates to FAIL in the next cycle's protocol entry; the other four stay WARN until consumer-adoption signal justifies promotion.
- The KISS mini-card permitted form is opt-in; existing `[CORE-REF: ...]` links remain valid.

## [2.50] - 2026-06

`semantic_impact: medium` — adds the **information-architecture (IA) self-display floor**: a cold reader's first touch is `ls` / `tree`, not `cat`. Directory names, file-name prefixes, and the README directory-map annotations must carry routing weight; prose is the fallback when the name alone cannot disambiguate. New `bootstrap.md` §3.7 sub-rules A1.1–A1.4, new Doctor rows `15N` / `15O` / `15P` / `15Q`, new `ssot-lint.sh` `[DIR-MAP-MISSING]` check, new `cold-agent-sim.md §1.8 dir-tree-only` probe, and a new `dir-readme-map.md` template (en/zh).

### Changed
- **`VERSION`** -> `2.50`.
- **`skills/ssot-preflight/SKILL.md`** `metadata.protocol_version` -> `2.50`.
- **`skills/ssot-bootstrap/references/bootstrap.md`** §3.7: added "Information-architecture self-display (v2.50)" block introducing sub-rules A1.1 (directory README = directory map), A1.2 (numeric prefix for read-ordered directories), A1.3 (file names spoken in plain words), A1.4 (meta files routed explicitly).
- **`skills/ssot-doctor/references/doctor.md`** §2.1 L1 checklist and §4 output-tag list: added rows `15N [DIR-MAP]`, `15O [READ-ORDER]`, `15P [META-FILE-ROUTING]`, `15Q [JARGON-MAP-NOTE]` plus §3 coverage hard-blocker entries for each.
- **`skills/ssot-doctor/references/cold-agent-sim.md`** §1.8: added the `dir-tree-only` routing probe with mandatory question pool and `navigation-gap` / `boundary-gap` / `meta-routing-gap` / `read-order-gap` miss classes.
- **`skills/ssot-doctor/assets/scripts/ssot-lint.sh`**: added check 17 `[DIR-MAP-MISSING]` (15N) verifying that every directory README's first 60 lines carries an ASCII tree (├── / └── glyphs). Made checks 9 and 10 (intent-truth-narrative + product skeleton) resolve the product / architecture trunk path at runtime so consumers can facet the top level (e.g. `SSOT/01-product/`, `SSOT/02-architecture/`) without breaking the skeleton check.
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/dir-readme-map.md`**: new template — H1 + one-sentence purpose + ASCII tree with plain-language annotation rows + recommended-reading-order line + one-paragraph "why this split".

### Compatibility
- Existing consumers that use the canonical un-faceted shape (`SSOT/product/`, `SSOT/architecture/`) continue to pass the v2.50 lint unchanged.
- Consumers that previously had directory READMEs without an ASCII tree must add one. The `[DIR-MAP-MISSING]` check is a FAIL.
- The `[PRODUCT]` skeleton check now also accepts `SSOT/01-product/` when that directory exists; the canonical `SSOT/product/` is still the default fall-through.

## [2.49] - 2026-06

`semantic_impact: low` — codifies SSOT document naming, frontmatter uniformity, and H1 language conventions in a single reference (`skills/ssot-bootstrap/references/formatting-conventions.md`) and gives `ssot-lint.sh` four new deterministic checks plus matching Doctor L2 rows so the conventions can be enforced mechanically.

### Changed
- **`VERSION`** -> `2.49`.
- **`skills/ssot-preflight/SKILL.md`** `metadata.protocol_version` -> `2.49`.
- **`skills/ssot-bootstrap/references/formatting-conventions.md`**: new file— naming (`NN-` ordered prefix vs `NNNN-` ledger prefix vs unordered kebab-case), same-directory frontmatter uniformity, the `intent_recovery:` propagation rule under `product/` and `architecture/`, and the H1-leads-with-locked-language rule.
- **`skills/ssot-bootstrap/references/bootstrap.md`**: adds §3.8 pointing at the new formatting-conventions reference.
- **`skills/ssot-doctor/references/doctor.md`**: adds rows `15J [PEER-FRONTMATTER]`, `15K [NUMBERED-PREFIX]`, `15L [H1-LANGUAGE]`, `15M [INTENT-RECOVERY-UNIFORM]`; adds matching hard-blocker bullets (15J / 15K / 15M block `covered`, 15L WARN-only) and output tag entries.
- **`skills/ssot-doctor/assets/scripts/ssot-lint.sh`**: adds checks 13–16 (15J–15M) — sibling frontmatter key-set uniformity, ordered-directory numbering, pure-English H1 detection under `documentation_language: zh`, and `intent_recovery:` presence on `product/` and `architecture/` prose.

## [2.48] - 2026-06

`semantic_impact: medium` — separates SSOT self-maintenance machinery from product / architecture prose. Doctor / lint / cold-agent-sim machinery introduced by v2.43–v2.47 (Core recovery manifest, Core completeness argument, Apex / Maxim → Owner index, Capability → Surface registry mirror rows, intent-recovery pillar matrix, `intent_recovery_evidence` strings, README-self failure-mode sections, adoption-cycle version labels) now lives in a sibling `_manifest.md` per covered area. Prose owners (`product/*.md`, `product/{capabilities,journeys}/*.md`, `architecture/*.md`, `architecture/*/*.md`, `architecture/views/*.md` — excluding `_manifest.md`) carry only the product / design narrative plus inline `[CORE-REF: ...]` anchors. Doctor gains hard row `15I [META-LEAKAGE]`; `ssot-lint.sh` gains a deterministic grep check (always run as part of normal lint) plus a standalone `--check-meta-leakage` flag.

### Changed
- **`VERSION`** -> `2.48`.
- **`skills/ssot-preflight/SKILL.md`** `metadata.protocol_version` -> `2.48`.
- **`skills/ssot-preflight/references/area-model.md`**: adds §2.0.5 Manifest separation defining the prose/manifest split and the v2.48 forbidden-token list for covered prose files.
- **`skills/ssot-doctor/references/doctor.md`**: adds `15I [META-LEAKAGE]` row, tag entry, and hard-blocker bullet; extends the L1 automation prefix.
- **`skills/ssot-doctor/assets/scripts/ssot-lint.sh`**: adds always-on `15I` grep (FAIL on hit) plus standalone `--check-meta-leakage [DIR ...]` mode for targeted invocation against `SSOT/01-product/` and `SSOT/02-architecture/`.
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/_manifest.md`**: new template for area-level `_manifest.md` (Core recovery manifest + Apex / Maxim mirror + Capability surface registry + README-self failure modes + intent-recovery evidence + adoption-cycle log).
- **`skills/ssot-audit/references/current-upgrade.md`**: adds v2.48 ledger entry with impact checklist and no-op criteria.

### Migration
- Run `ssot-lint.sh --check-meta-leakage SSOT/01-product/ SSOT/02-architecture/` to enumerate current `15I` hits.
- For each covered area, create `<area>/_manifest.md` from the new template and move Core recovery manifest, Apex / Maxim mirror, Capability surface registry rows, intent-recovery evidence, README-self failure-mode sections, and adoption-cycle labels into it. Frontmatter on prose files reduces to `intent_recovery: covered|partial|gap`.
- Re-run the targeted lint; `FAIL=0` is the v2.48 acceptance bar.

## [2.47] - 2026-06

`semantic_impact: medium` — adds an intent/truth narrative gate for product and architecture trunks. Covered product / architecture areas must explain product intent + product truth or design intent + design truth in compact prose before Core recovery manifests or dense owner maps; the manifest remains a narrow recovery index. Doctor gains `15H [INTENT-TRUTH-NARRATIVE]`, and `ssot-lint.sh` adds a WARN-only heuristic for covered trunks that have a Core recovery manifest but no obvious intent/truth narrative heading.

### Changed
- **`VERSION`** -> `2.47`.
- **`skills/ssot-preflight/SKILL.md`** `metadata.protocol_version` -> `2.47`.
- **`skills/ssot-preflight/references/area-model.md`**: adds §2.0.3 intent/truth narrative before manifests.
- **`skills/ssot-preflight/references/architecture.md`** and **`skills/ssot-bootstrap/references/bootstrap.md`**: require prose-first product/design intent and truth before dense tables.
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/{product-readme.md,architecture-readme.md}`**: add product/design intent-truth sections.
- **`skills/ssot-doctor/references/doctor.md`**: adds `15H [INTENT-TRUTH-NARRATIVE]`.
- **`skills/ssot-doctor/assets/scripts/ssot-lint.sh`** and its test runner: add the WARN-only intent/truth narrative heuristic.
- **`skills/ssot-audit/references/current-upgrade.md`**: prepends the v2.47 medium-impact upgrade entry.

## [2.46] - 2026-06

`semantic_impact: medium` — tightens the Core recovery manifest into a first-principles completeness check. Product and architecture trunks that claim `covered` must now explain why their finite core set is complete, which product-model / operating-model classes are included, which near-miss items are excluded, and what wrong conclusion an omitted class would cause. Doctor `15G [CORE-COVERAGE-MAP]` now covers missing completeness arguments, omitted product posture/model or architecture operating-model/CTG rows, unmapped state labels such as `current`, and spine-owned rows that lack a same-granularity anchor.

### Changed
- **`VERSION`** -> `2.46`.
- **`skills/ssot-preflight/SKILL.md`** `metadata.protocol_version` -> `2.46`.
- **`skills/ssot-preflight/references/area-model.md`**: extends the Core recovery manifest with the Core completeness argument and spine-row anchor rule.
- **`skills/ssot-preflight/references/knowledge-integrity.md`**: binds `intent_recovery: covered` to the completeness argument as well as manifest row coverage.
- **`skills/ssot-doctor/references/cold-agent-sim.md`**: adds the completeness probe and omission-risk prompt dimension to manifest sweeps.
- **`skills/ssot-doctor/references/doctor.md`**: broadens `15G [CORE-COVERAGE-MAP]`.
- **`skills/ssot-audit/references/current-upgrade.md`**: prepends the standalone v2.46 medium-impact upgrade entry.

## [2.45] - 2026-06

`semantic_impact: medium` — adds a finite Core recovery manifest requirement for product and architecture recoverability. Consumers that mark `product` or `architecture` as `covered` must enumerate the core capabilities, journeys, runtime owners, and cross-owner views whose product/design intent and truth must be recoverable; each row names required pillars, current truth state, owner, and closure/evidence owner. `mixed` is the explicit state for a row that combines shipped contract truth with unresolved design/debt/out truth. Cold-agent-sim now performs owner-directed manifest trials for core rows not touched by recent commits, and Doctor gains `15G [CORE-COVERAGE-MAP]`.

### Changed
- **`VERSION`** -> `2.45`.
- **`skills/ssot-preflight/SKILL.md`** `metadata.protocol_version` -> `2.45` and explicitly reports stale runtime-installed skill copies when a project source checkout is newer.
- **`skills/ssot-preflight/references/area-model.md`**: adds the Core recovery manifest rule for product and architecture trunks.
- **`skills/ssot-preflight/references/knowledge-integrity.md`**: binds `intent_recovery: covered` to complete manifest coverage.
- **`skills/ssot-doctor/references/cold-agent-sim.md`**: adds manifest sweep scheduling, synthetic owner-directed trials, result reporting, and cycle-gate criteria.
- **`skills/ssot-doctor/references/doctor.md`**: adds `15G [CORE-COVERAGE-MAP]`.
- **`skills/ssot-audit/references/current-upgrade.md`**: prepend the standalone v2.45 medium-impact upgrade entry.

## [2.44] - 2026-06

`semantic_impact: medium` — tightens the intent-recoverability model for current product truth. A product `product_truth` trial no longer treats "no contract-level browser surface exists yet" as automatically equivalent to unrecoverable truth when the product owner explicitly marks the row as `state: design`, `state: debt`, `Out`, or `not_applicable` and gives the current user-visible behavior plus a falsifiable gap / decision / debt anchor. This prevents the harness from forcing product files to pretend a planned or negative surface is a shipped contract just to satisfy `[SURFACE-PIN]`.

### Changed
- **`VERSION`** -> `2.44`.
- **`skills/ssot-preflight/SKILL.md`** `metadata.protocol_version` -> `2.44`.
- **`skills/ssot-preflight/references/area-model.md`**: `product/` capability owners must carry current-truth anchors for contract, design/debt, Out, and not-applicable rows.
- **`skills/ssot-preflight/references/knowledge-integrity.md`**: `product_truth` intent recovery explicitly accepts state-tagged negative / design current-truth anchors when the current behavior and closure owner are recoverable.
- **`skills/ssot-doctor/references/cold-agent-sim.md`**: `product_truth` pillar, output schema, grading rubric, and miss-class taxonomy gain `truth-state-gap`.
- **`skills/ssot-doctor/references/doctor.md`**: `[SURFACE-PIN]` (14T) and `[INTENT-RECOVERY]` (14Y) distinguish contract surface anchors from state-tagged current-truth anchors.
- **`skills/ssot-audit/references/current-upgrade.md`**: prepend the standalone v2.44 medium-impact upgrade entry.

## [2.43] - 2026-06

`semantic_impact: medium` — opens the intent-recoverability cycle. Adds an apex-maxim → SSOT-owner mapping protocol (new `skills/ssot-preflight/references/intent-ownership.md`), an architecture domain README intent triad (`## Why` / `## 失败模式` / `## 关闭条件`), a canonical-vocabulary hard list for `glossary/`, falsifiable `closure_condition` + `revisit_signal` fields for ADRs and tech-debt entries, and an `intent_recovery: covered | partial | gap` axis on `knowledge-integrity.md` that binds `STATUS.md` `covered` to passing cold-agent-sim trials. The cold-agent simulation harness now scores per 4 pillars (`design_intent` / `product_intent` / `design_truth` / `product_truth`) with a `≥ 5/8` floor per pillar plus `≥ 24/32` aggregate gate, and every FAIL trial records a closed-set `miss_class` of `missing-owner` / `prose-fork` / `broken-ref` / `glossary-gap`. Doctor gains seven new rows: `14W [INTENT-OWNER]`, `14X [MAXIM-OWNER]`, `14Y [INTENT-RECOVERY]`, `14Z [CORE-REF-PROSE]`, `15A [WORKFLOW-STATE-VOCAB]`, `15B [ADR-CLOSURE]`, `15C [DEBT-CLOSURE]`; the legacy `[FORK]` and `[FIRST-DAY]` rows are renumbered to `15D` and `15E` respectively to free the 14W/14X slots.

### Changed
- **`VERSION`** -> `2.43`.
- **`skills/ssot-preflight/SKILL.md`** `metadata.protocol_version` -> `2.43`.
- **NEW `skills/ssot-preflight/references/intent-ownership.md`**: apex-maxim → SSOT-owner mapping; repo-wide invariant single-owner rule; `[CORE-REF: <owner_path#anchor>]` syntax definition.
- **`skills/ssot-preflight/references/area-model.md`**: §2.0.1 apex invariants and CORE-REF prose ownership; §2.2 architecture domain README intent triad; §2.3 canonical-vocabulary hard list (workflow result codes, lifecycle states, agent-tier semantics, altitude vocabulary); §2.4 cite intent-ownership.md for apex-maxim DISC ownership; §2.8 ADR `closure_condition` + `revisit_signal` required for pending/partial/diverged; §2.11 tech-debt `closure_condition` + `revisit_signal` required for active entries.
- **`skills/ssot-preflight/references/architecture.md`**: §3 Domains apex-maxim and apex-invariant single-owner rule; §4 Owner Anchors apex-maxim row + apex-maxim indexing subsection.
- **`skills/ssot-preflight/references/knowledge-integrity.md`**: §1.1 intent-recovery axis; §4 binding rule that `intent_recovery: gap` blocks `covered` even when `confidence: verified`.
- **`skills/ssot-doctor/references/cold-agent-sim.md`**: §2 trial schema gains `pillar` + `miss_class` fields; §2.1 pillar assignment subsection; §3 grading rubric switches to per-pillar `≥ 5/8` floor + aggregate `≥ 24/32` gate; §3.1 closed-set `miss_class` taxonomy.
- **`skills/ssot-doctor/references/doctor.md`**: append rows `14W [INTENT-OWNER]`, `14X [MAXIM-OWNER]`, `14Y [INTENT-RECOVERY]`, `14Z [CORE-REF-PROSE]`, `15A [WORKFLOW-STATE-VOCAB]`, `15B [ADR-CLOSURE]`, `15C [DEBT-CLOSURE]`; renumber legacy `14W [FORK]` → `15D` and `14X [FIRST-DAY]` → `15E`; §3 hard-blocker bullets and §4 output-tag examples + tag-semantics list updated.
- **`skills/ssot-audit/references/current-upgrade.md`**: prepend the standalone v2.43 medium-impact upgrade entry.

### Cycle-2 deltas (in-place, no version bump)

- **`skills/ssot-doctor/references/doctor.md`**: row `14Z [CORE-REF-PROSE]` scope broadened to include `glossary/`, `decisions/` (excluding the establishing ADR), `tech-debt/`, `bugs/`, `gotchas/`, `release/`, `testing/` and gains a `Worked example — legal vs. illegal restatement` block; row `15A [WORKFLOW-STATE-VOCAB]` extended to require the apex-behavior-maxim umbrella term + numbered-rule→owner table when the consumer's root constraint file enumerates `*-MAXIM-N` / `*-RULE-N` rules; new row `15F [VOCAB-PROSE-FORK]` enforces the canonical-vocabulary single-prose-owner rule across non-glossary owners; §3 hard-blocker bullets and §4 output tags + tag-semantics list updated for both 15A scope and 15F.
- **`skills/ssot-preflight/references/area-model.md`**: §2.0.1 mirrors the broadened CORE-REF-PROSE location set, adds the legal-vs-illegal restatement worked example and the legal-vs-illegal glossary cell shape; §2.3 hard list gains the 5th category (apex behavior maxim term) and a single-prose-owner rule paragraph; new §2.3.1 ships the recommended `glossary/README.md` skeleton (Owner block + H2-per-category + 3-column table).
- **`skills/ssot-doctor/references/cold-agent-sim.md`**: §2.1 adds the 48-trial-per-cycle budget cap with priority-order skip rules; §3 cycle gate restated as ratio + absolute floor (`pillar_score ≥ 0.625`, absolute passing-cell count ≥ 4); §4 fail-row schema retires `missing_evidence_kind` and adds `(pillar, miss_class)` consecutive-cycle escalation; §5 Results template rewritten to per-cell rows + per-pillar / miss-class distribution; §5 cycle-gate line and §6 Termination drop the superseded flat-75% rule.
- **`skills/ssot-preflight/references/knowledge-integrity.md`**: §1.1 adds the multi-pillar rule for `intent_recovery: covered` (every declared pillar must PASS).
- **`skills/ssot-audit/references/current-upgrade.md`**: append cycle-2 deltas sub-section under the v2.43 entry.

### Cycle-3 deltas (in-place, no version bump)

- **`skills/ssot-preflight/references/intent-ownership.md`**: new §1.1 **Apex maxim registry (consumer side)** subsection — consumers must ship a single positive-existence registry table at `glossary/README.md` (preferred), `development/discipline.md` head matter, or `architecture/README.md` invariants section, with one row per apex maxim including `not_yet_owned` rows. Registry shape (Apex maxim | Slug | SSOT owner | Root-file link state) is the canonical 14X read anchor.
- **`skills/ssot-preflight/references/area-model.md`**: §2.0.1 gains a third **Illegal — `本域落地形态` / domain-form fork** worked example covering the wrapper pattern (`本域 contract 一句摘要` / `具体到本域的落地形态` / `domain-form restatement` / `本域如何承接`) that survived cycle-2 closure on backend-runtime line 91; mechanical-test paragraph now states explicitly that wrappers do not exempt trailing verb clauses. §2.3 hard list gains 6th category **Concurrency-control vocabulary** for named scheduling/concurrency identifiers used as nouns in apex docs (e.g. `workspace_path`, `project_limit`).
- **`skills/ssot-preflight/references/architecture.md`**: §4 Apex maxim indexing subsection now ends with a one-line cross-reference pointing 14X readers at `intent-ownership.md §1.1` for the consumer-side registry.
- **`skills/ssot-preflight/references/knowledge-integrity.md`**: §1.1 gains **Lag-deferral clause (v2.43.1)** allowing one cycle of deferral when `tracked_skill_version < 2.43`; multi-pillar `partial` rule extended to recognise `pillar-not-applicable-to-cycle` deferrals from the new §1.5 owner-pillar coverage matrix.
- **`skills/ssot-doctor/references/cold-agent-sim.md`**: §2.1 gains **Pillar-roundtrip enforcement** — harness embeds `pillar_assigned` in trial prompts and records `pillar-mismatch` for any mismatch (skill-fail when ≥10% of cycle trials drift). New §1.5 **Owner-pillar coverage requirement** computes the (owner, declared_pillar) coverage matrix before sample finalisation; new §1.6 **Canonical-vocab spot-check** adds 2 deterministic synthetic trials per cycle drawn from `glossary/README.md` plus apex-doc nouns absent from glossary, scored as a fifth `glossary_vocab` pillar with `2/2` floor as gate condition 7. §3 cycle-gate restated as ratio formulation `ceil(0.625·denom)` per pillar plus aggregate `total_score / sum(denom) ≥ 0.75`, dropping the conflicting `absolute passing-cell count ≥ 4` clauses. New §3.2 **Authoritative-owner check** downgrades any `verdict=PASS` whose resolved file would be flagged by `15D [FORK]` or `14Z [CORE-REF-PROSE]` to `verdict=FAIL` with `miss_class=prose-fork`. §3.1 miss-class table gains `pillar-mismatch` row and `prose-fork` Trial-signature column extended for §3.2. §6 termination conditions restated in ratio form and gain `glossary_vocab = 2/2` clause.
- **`skills/ssot-doctor/references/doctor.md`**: row `14X [MAXIM-OWNER]` body rewritten to enumerate the three firing cases (missing owner, missing/incomplete Apex maxim registry, non-owner body recopy) and explicitly disclaim root-constraint-file inline body as `[CORE-REF-PROSE]` (14Z) territory; example block expanded from one to three demarcated examples (registry missing, non-owner DISC body recopy, root-file no-owner registered). Row `14Y [INTENT-RECOVERY]` body rewritten to make demotion mandatory ("MUST be auto-demoted") rather than conditional ("If ... demote"), and explicitly cites the lag-deferral clause as the only legitimate exception (capped at one cycle); example refreshed.

## [2.38] - 2026-06

`semantic_impact: medium` - adds source-document lifecycle governance and the Runtime Owner Map architecture IA. Root public Markdown and `docs/**/*.md` now need lifecycle inventory, an in-file header, or an audited exclusion once a consumer advances to v2.38. Working, historical, external, and public-thin docs carry authority/downgrade fields so thick docs can exist without pretending to be current SSOT. Product owns intent; architecture owns implementation response. Architecture templates default to runtime owners rather than a universal section checklist.

### Changed
- **`VERSION`** -> `2.38`.
- **`skills/ssot-preflight/SKILL.md`** `metadata.protocol_version` -> `2.38`; `semantic_impact: medium`.
- **`skills/ssot-preflight/references/source-material.md`**: adds lifecycle classes, downgrade fields, audited exclusions, and public-thin owner requirements.
- **`skills/ssot-preflight/references/area-model.md`** and **`architecture.md`**: sharpen product intent vs architecture implementation response, and define Runtime Owner Map as the default architecture IA.
- **`skills/ssot-closeout/references/{update-routing.md,inline-update-guide.md}`**: route systemic consumer docs/IA problems through SSOT-SKILL first and then consumer migration.
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/{status.md,recon-report.md,bootstrap-session.md,architecture-readme.md,architecture-domain-readme.md}`**: add lifecycle inventory fields and replace checklist-heavy architecture templates with owner-map templates.
- **`skills/ssot-doctor/references/doctor.md`**, **`skills/ssot-doctor/assets/scripts/ssot-lint.sh`**, and **`run-tests.sh`**: add v2.38 source lifecycle checks and Runtime Owner Map drift heuristics.
- **`skills/ssot-audit/references/current-upgrade.md`** and **`archive/index.md`**: add the standalone v2.38 medium-impact upgrade entry.

## [2.37] - 2026-06

`semantic_impact: medium` - applies the v2.36 KISS principle to SSOT-SKILL's own protocol surfaces. STATUS and closeout routing now lead with prose decision paths and keep wide tables as appendices; bootstrap STATUS/manifest/recon templates default to thin registers; architecture protocol requires a mental model, owner boundary, and evidence direction before optional matrices; protocol upgrade history is split into a small router, `current-upgrade.md`, and archive range files so ordinary audits no longer load the whole historical ledger.

### Changed
- **`VERSION`** -> `2.37`.
- **`skills/ssot-preflight/SKILL.md`** `metadata.protocol_version` -> `2.37`; `semantic_impact: medium`.
- **`skills/ssot-preflight/references/status-protocol.md`**: rewritten around five STATUS registers and a STATUS decision path; table schemas and detailed product/architecture coverage rules moved to appendices.
- **`skills/ssot-closeout/references/update-routing.md`**: rewritten around five routing questions, frequent routes, and targeted cascade checks; full mapping tables moved to appendices.
- **`skills/ssot-preflight/references/architecture.md`**: reframed architecture as mental model + owner boundary + evidence direction; domain/diagram/appendix requirements now trigger from real complexity instead of empty mandatory sections.
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/{status.md,bootstrap-manifest.md,recon-report.md}`**: thinner default registers and optional appendix blocks for wide details.
- **`skills/ssot-audit/references/protocol-upgrades.md`**, **`current-upgrade.md`**, and **`archive/`**: protocol upgrade ledger split into router/current/archive layers; previously CHANGELOG-only v2.20 and v2.25-v2.31 coverage is explicit in the archive.
- **`tests/test-bundle-shape.sh`** and **`tests/test-installer-e2e.sh`**: assert the new audit ledger shape and installed archive/current files.

## [2.36] - 2026-06

`semantic_impact: medium` - makes KISS the permanent SSOT design principle. SSOT owners must give the mental model in prose and use tables only for routing, comparison, state registers, or evidence lookup. `STATUS.md`, bootstrap manifests, promotion metadata, and protocol ledgers remain allowed registers, but their cells must stay pointer-sized; paragraph reasoning, command output, copied checklists, and proof-of-work transcripts move to the authoritative owner or evidence artifact. Doctor gains semantic tag `[KISS]`; `ssot-lint.sh` adds a WARN-only `[KISS-TABLE-DENSITY]` heuristic; STATUS and architecture-domain templates now make the register/prose boundary explicit.

### Changed
- **`VERSION`** -> `2.36`.
- **`skills/ssot-preflight/SKILL.md`** `metadata.protocol_version` -> `2.36`; `semantic_impact: medium`.
- **`AGENTS.md`**: declares KISS as the permanent SSOT design principle and extends readability discipline to register-only cells.
- **`skills/SKILL_STYLE.md`**: adds a KISS bridge so references/templates cannot reverse-incentivize table-first documents.
- **`skills/ssot-bootstrap/references/bootstrap.md`** and **`skills/ssot-preflight/references/area-model.md`**: add the KISS rule and register-only row budget.
- **`skills/ssot-preflight/references/status-protocol.md`**, **`skills/ssot-closeout/references/inline-update-guide.md`**, and **`promotion-rationale.md`**: make STATUS and PLTL metadata pointer-sized registers.
- **`skills/ssot-doctor/references/doctor.md`**: adds `[KISS]` / `[KISS-TABLE-DENSITY]` review language.
- **`skills/ssot-doctor/assets/scripts/ssot-lint.sh`** and **`run-tests.sh`**: add WARN-only table-density smoke coverage.
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/status.md`**: adds register-only KISS notes for STATUS rows, stop-review evidence, and CAP rows.
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/architecture-domain-readme.md`**: adds prose-first placeholders to table-heavy sections and fixes optional-block wording that conflicted with deleting unused blocks.
- **`skills/ssot-audit/references/protocol-upgrades.md`**: adds the standalone v2.36 medium-impact review entry.

## [2.35] - 2026-06

`semantic_impact: medium` - adds an agent-actionability layer on top of the existing cold-reader readability and owner-boundary rules. SSOT entries must help a future agent decide what to do next: why to read the entry, what current truth it owns, where to inspect first, what not to do, and what minimal verification/evidence closes the loop. High-risk `bugs/` and `tech-debt/` entries gain an "agent quick entry" expectation. `STATUS.md` stop-review fields must stay pointers and conclusions, not full batch transcripts. Doctor gains semantic tag `[ACTIONABILITY]`; `ssot-lint.sh` adds WARN-only heuristics for overlong lines, stop-review ledger bloat, and missing quick-entry surfaces on numbered bug/debt entries.

### Changed
- **`VERSION`** -> `2.35`.
- **`skills/ssot-preflight/SKILL.md`** `metadata.protocol_version` -> `2.35`; `semantic_impact: medium`.
- **`skills/ssot-preflight/references/area-model.md`**: adds the agent-actionability posture and explicit quick-entry expectations for `bugs/` and `tech-debt/`.
- **`skills/ssot-closeout/references/update-routing.md`** and **`inline-update-guide.md`**: route SSOT-quality / protocol-gap signals through "fix the protocol first when the repository owns it, then repair local SSOT" and require actionability checks before writing.
- **`skills/ssot-doctor/references/doctor.md`**: adds `[ACTIONABILITY]`, `[ENTRY-ACTIONABILITY]`, `[STATUS-STOP-REVIEW-LEDGER]`, and `[READABILITY-LONG-LINE]` review language.
- **`skills/ssot-doctor/assets/scripts/ssot-lint.sh`**: adds WARN-only deterministic heuristics for the new tags.
- **`skills/ssot-doctor/assets/scripts/test/run-tests.sh`**: adds smoke scenarios for the new WARN checks.
- **`skills/ssot-audit/references/protocol-upgrades.md`**: adds the standalone v2.35 medium-impact review entry.

## [2.34] - 2026-06

`semantic_impact: medium` — generalizes the v2.33 testing-ledger boundary into a broader owner/index/ledger boundary. `STATUS.md` Notes are now project-level coverage pointers, not child-entry status, recent validation, or run-history ledgers. README/index/Reader Map files may route readers and expose protocol-authorized minimal index fields, but must not mirror child body facts, generated counts, latest activity, or non-authoritative lifecycle state. Doctor gains semantic tags `STATUS-NOTES-LEDGER`, `INDEX-DERIVED-STATE`, and `SHADOW-LEDGER`; `ssot-lint.sh` adds WARN-only heuristics for these patterns so projects see owner-boundary drift without hard-failing normal maintenance.

### Changed
- **`VERSION`** -> `2.34`.
- **`skills/ssot-preflight/SKILL.md`** `metadata.protocol_version` -> `2.34`; `semantic_impact: medium`.
- **`skills/ssot-preflight/references/status-protocol.md`**: expands Notes-column guidance into `STATUS-NOTES-LEDGER`, covering derived child state, latest validation, and run-history bloat.
- **`skills/ssot-preflight/references/area-model.md`**: adds general README/index and non-owner shadow-ledger boundaries.
- **`skills/ssot-doctor/references/doctor.md`**: adds Doctor checks/tags and coverage hard blockers for STATUS notes ledgers, index-derived state, and shadow ledgers.
- **`skills/ssot-doctor/assets/scripts/ssot-lint.sh`**: adds WARN-only deterministic heuristics for the three new tags.
- **`skills/ssot-doctor/assets/scripts/test/run-tests.sh`**: adds smoke scenarios for the new WARN checks.
- **`skills/ssot-audit/references/protocol-upgrades.md`**: adds the standalone v2.34 medium-impact review entry.

## [2.33] - 2026-06

`semantic_impact: medium` — clarifies the boundary between stable testing facts and verification run evidence. `testing/` now owns test strategy, selection matrix, quality gates, fixtures/test data, current baselines, known gaps, and defensive-test mappings; it must not become a chronological validation ledger. Closeout and audit now explicitly treat command pass/fail output as evidence for the final answer, commit/release notes, bug entries, or stop-review evidence unless that output changes durable testing policy. Doctor gains semantic check/tag `TESTING-LEDGER`; bootstrap testing templates now include Test Selection Matrix, Quality Gates, Current Baseline, and a "not a verification ledger" guard. Existing projects: audit `testing/` and split/remove recent-run tables or command transcripts, keeping only current baseline/gap/map facts with evidence pointers.

### Changed
- **`VERSION`** -> `2.33`.
- **`skills/ssot-preflight/SKILL.md`** `metadata.protocol_version` -> `2.33`; `semantic_impact: medium`.
- **`skills/ssot-preflight/references/status-protocol.md`**: defines `semantic_impact=medium` as self-reviewed but standalone in the protocol upgrade ledger.
- **`skills/ssot-audit/references/protocol-upgrades.md`**: adds v2.33 testing-ledger review guidance and backfills the v2.32 identity-removal review entry under the new medium-impact rule.
- **`skills/ssot-audit/SKILL.md`**: aligns waterline advancement review wording with `status-protocol.md §7.1` so medium-impact protocol upgrades can be self-reviewed with a checklist while high-impact exceptions still route to `$ssot-doctor`.
- **`skills/ssot-closeout/SKILL.md`** and **`skills/ssot-closeout/references/inline-update-guide.md`**: align closeout waterline wording with the same §7.1 review split.
- **`skills/ssot-preflight/references/area-model.md`** `testing/`: defines the stable owner set and forbids batch-by-batch command transcripts, dates, green/red summaries, and recent validation rows unless they change a durable testing fact.
- **`skills/ssot-closeout/SKILL.md`**: states that test command output is evidence, not automatically a `testing/` fact.
- **`skills/ssot-closeout/references/update-routing.md`** and **`skills/ssot-audit/references/{commit-audit,conversation-audit}.md`**: require agents to ask whether a test change/result changes future test selection before updating `testing/`.
- **`skills/ssot-doctor/references/doctor.md`**: adds semantic check/tag `TESTING-LEDGER` and includes testing-ledger bloat in coverage hard blockers.
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/testing-readme.md`**: adds Test Selection Matrix, Quality Gates, Current Baseline, and a verification-ledger exclusion section.

## [2.32] - 2026-06

`semantic_impact: medium` — removes `identity/` as a top-level SSOT area. The four facts it carried are absorbed by existing owners that already held the same content: the one-sentence repository positioning moves to the opening line of `SSOT/README.md` (right after the writing-style note); tech stack, runtime form and repository type fold into `architecture/README.md` as part of the design brief; primary capabilities stay where they already lived, in `product/prd.md`'s capability map. Rationale: identity duplicated content already owned by `product/`, `architecture/` and the SSOT root entry — three places to keep in sync for one fact each, the exact anti-pattern the protocol bans elsewhere. The remaining unique role (a short, citable cover-sheet for thin adapters) is served better by the README opening line, which the adapter template already wants as its first source. Doctor `14I` and the readability hard blocker drop `identity/` from their scope lists; thin-adapter `SSOT-source` switches from `identity/README.md` to `README.md`; the `<identity-one-liner>` placeholder renames to `<repo-positioning-one-liner>`. Status/manifest/recon templates drop the identity row. Existing projects: identity content is already either in or one paragraph from its new home; the audit pass needs only to lift the positioning line into `SSOT/README.md`, confirm `architecture/README.md` covers tech stack/repository type, and delete `SSOT/identity/`.

### Changed
- **`VERSION`** → `2.32`.
- **`skills/ssot-preflight/SKILL.md`** `metadata.protocol_version` → `2.32`; `semantic_impact: medium`.
- **`skills/ssot-preflight/references/area-model.md`**: deletes §2.3 `identity/`; renumbers §2.4–§2.12 → §2.3–§2.11; removes `identity/` from the structural-model tree, "Context areas" line, and §5 always-applicable list; adds a paragraph after the product-required paragraph requiring `SSOT/README.md` to open with a one-sentence repository positioning and stating where tech stack / repository type / primary capabilities live; updates the `architecture/README.md` tree comment to note the design brief carries tech stack and repository type; updates two `(see §2.5)` internal cross-references to `(see §2.4)`.
- **`skills/ssot-bootstrap/references/bootstrap.md`**: replaces the Tier 1 `identity` row with an `SSOT/README.md` row noting the one-sentence positioning opening line; removes the `identity` row from the evidence-source map; drops `identity/` from §3.7 scope; updates the S/M sharding example to drop `identity`; expands the Phase 1 Output #2 description to require `SSOT/README.md` to open with the one-sentence positioning.
- **`skills/ssot-preflight/references/status-protocol.md`** §3 coverage state table: drops the `identity` row.
- **`skills/ssot-doctor/references/adapter-strategy.md`** §2: `Project identity` source changes from `SSOT/identity/` to "the opening line of `SSOT/README.md`".
- **`skills/ssot-doctor/references/doctor.md`**: drops `identity/` from `14I` scope and from the hard-blocker scope.
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/adapter-thin.md`**: `SSOT-source` first source changes from `SSOT/identity/README.md` to `SSOT/README.md`; `<identity-one-liner>` placeholder renames to `<repo-positioning-one-liner>`.
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/ssot-readme.md`**: adds a `## What this repo is` / `## 仓库定位` section with the one-sentence positioning placeholder and a one-line pointer to `architecture/README.md` (tech stack/runtime/type) and `product/prd.md` (capabilities); drops the `Repository identity` / `仓库身份` row from the Area Index.
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/status.md`**: drops the `identity` row from the Area Status table.
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/bootstrap-manifest.md`**: drops the `identity` row from both the Assignment and Workflow tables; the Tier-order footnote drops `identity` from Tier 1.
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/recon-report.md`**: source-material example row example areas list drops `identity`.
- **`AGENTS.md`** writing-style scope sentence drops `identity/`.

## [2.31] - 2026-06

`semantic_impact: medium` — extends `decisions/` entries with required lifecycle fields (`created_on`, `updated_on`, `introduced_in`, `updated_in`) so ADRs carry their own temporal and git anchors; adds bilingual `decision-entry.md` and `decisions-readme.md` bootstrap templates for single-decision files and the decisions area index; adds doctor check `11` (check 21 reference) to validate frontmatter completeness on all `decisions/NNNN-<slug>.md` entries, exempting bootstrap-archaeology archives; updates bootstrap archive phase to apply the new `decision-entry.md` template for `0000-bootstrap-recon.md`.

### Added
- **`skills/ssot-preflight/references/area-model.md`** §2.9 `decisions/`: `created_on`, `updated_on`, `introduced_in`, `updated_in` fields. Explains each field's purpose — date anchor for temporal context, commit anchor for git provenance. Historic/imported ADR carveout (`introduced_in` = the commit that brought the file into `SSOT/04-records/decisions/`; `created_on` falls back to import date).
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/decision-entry.md`** — new single-decision template. YAML frontmatter with all lifecycle fields plus body sections: Background, Decision (with options-considered table), Consequences, Scope of Impact.
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/decisions-readme.md`** — new decisions area index template. Table with ID, Title, Status, Implementation state, Date, Owner / reviewer columns.
- **`skills/ssot-doctor/assets/scripts/ssot-lint.sh`** check 11: scans `decisions/NNNN-<slug>.md` for required frontmatter fields (`status`, `implementation_state`, `created_on`, `introduced_in`); exempts `bootstrap-archaeology` type entries.
- **`skills/ssot-doctor/references/doctor.md`** L1 check 21 row documenting the new doctor check.
- **`skills/ssot-doctor/assets/scripts/test/run-tests.sh`** S11, S12, S13: decision missing-field FAIL, complete decision PASS, bootstrap-archaeology exemption.

### Changed
- **`VERSION`** → `2.31`.
- **`skills/ssot-preflight/SKILL.md`** `metadata.protocol_version` → `2.31`.

## [2.30] - 2026-06

`semantic_impact: medium` — extends the cold-reader readability floor SSOT-wide, and replaces v2.29's five-rule blockquote-on-every-template scaffolding with one posture sentence + three guardrails + a one-line pointer per template. The scope is now every SSOT area the bundle generates (`product/`, `architecture/` root/views/domains, `development/`, `testing/`, `release/`, deployment, `decisions/`, `gotchas/`, `bugs/`, `tech-debt/`, `identity/`, `glossary/`, root `SSOT/README.md`) except infra files (`STATUS.md`, `.bootstrap/`, thin adapters). Single posture sentence: "Every section is first written for the stranger who lands tonight knowing nothing; tables, codes and tags they cannot read are not paragraphs." Three guardrails: prose before tables; define every term positively on first use; a cell is not a paragraph. v2.29's per-template multi-sentence `[MUST]` blockquotes are intentionally retired in favour of a single-line pointer — this is a deliberate course-correction, not a regression. The manual-style blockquote anti-pattern was teaching the model what its defaults already know once the posture loads; the pointer is the activator, not the rule. Doctor `14I` globalizes (renamed `Product readability` → `SSOT readability`); the `[PRODUCT-READABILITY]` tag merges into `[READABILITY]`; the product-specific hard blocker collapses into one general readability blocker.

### Changed
- **`skills/ssot-bootstrap/references/bootstrap.md`** §3.7 retitled `Product docs must be readable cold` → `SSOT docs must be readable cold`; opening prose replaced with scope sentence + posture sentence + "trust your defaults on everything else"; five rules collapse to three guardrails; closing "shared readability floor for product/ + architecture/views/" paragraph removed (subsumed by the new scope sentence).
- **`skills/ssot-doctor/references/doctor.md`** `14I` row renamed `Product readability (v2.29)` → `SSOT readability (v2.30)`; question column rewritten as three short checks aligned with the three guardrails, applied to every user-facing SSOT body file. Hard-blocker list: the v2.29 product-specific readability bullet becomes one general bullet covering all user-facing SSOT body files; the standalone scene-anchor blocker is removed (subsumed by the posture). `[PRODUCT-READABILITY]` tag retired; its semantics merged into `[READABILITY]`.
- **`skills/ssot-preflight/references/area-model.md`** new §2.0 prelude before `## 2. Area responsibilities` content: quotes the posture, names the three guardrails by phrase, links to `ssot-bootstrap` §3.7. §2.1 `product/` Writing-style block pruned to one line referencing §2.0. No per-area Writing-style subsections added elsewhere — the §2.0 prelude is enough.
- **`AGENTS.md`** `## Writing Style (Global)` shrunk to three sentences: posture, scope, pointer. Defensive prose ("long-running self-check phase", "immediate target is product and architecture", "tighten as needed, loosen only when …") removed.
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/product-readme.md`**, **`product-prd.md`**, **`product-model.md`**, **`product-roadmap-and-acceptance.md`**, **`product-capabilities-readme.md`**, **`product-journeys-readme.md`**, **`product-capability-entry.md`**, **`product-journey-entry.md`** — the v2.29 multi-sentence cold-reader blockquote and the v2.29 in-body `[MUST]` explanatory paragraphs (e.g. product-prd.md's "Do not satisfy this section by rearranging …" paragraph) are removed; replaced by the single-line pointer `> Writing style: any cold reader. See \`ssot-bootstrap\` §3.7.` (zh: `> 行文风格：写给任何冷读者。详见 \`ssot-bootstrap\` §3.7。`) immediately under the title.
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/architecture-readme.md`**, **`architecture-views-readme.md`**, **`architecture-view-operating-model.md`**, **`architecture-view-critical-journeys.md`**, **`architecture-view-current-target-gap.md`**, **`development-readme.md`**, **`testing-readme.md`**, **`release-readme.md`**, **`ssot-readme.md`** — same one-line pointer added immediately under the title.
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/architecture-domain-readme.md`** — same one-line pointer added under the title; the existing Readable Authority intro paragraph is preserved.
- **`VERSION`** → `2.30`.
- **`skills/ssot-preflight/SKILL.md`** `metadata.protocol_version` → `2.30`.

## [2.29] - 2026-06

`semantic_impact: medium` — introduces a cold-reader readability floor for `product/`. The primary reader of SSOT is still the next agent; the framing matters because what is unreadable to a person who does not know the system is also unreadable to an agent that does not — plain language, prose before tables, positive term definitions and concrete scenes are the conditions under which any cold reader (agent or human) can attach meaning to the identifiers, references and constraints. Five product spine / capability / journey templates now require an opening prose section ([MUST]) before any table, plus a concrete usage scene; `ssot-bootstrap` §3.7 documents the rules; Doctor gains check `14I Product readability`, a new hard blocker covering the same surface, and the `[PRODUCT-READABILITY]` tag. `14B` Readable Authority extends from `root/view/domain` to `root/view/domain/product`. `area-model.md` §2.1 absorbs the rules so preflight readers see the constraint too. Top-level `AGENTS.md` gains a `Writing Style (Global)` posture for the long-running readability self-check phase.

### Added
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/product-prd.md`** — `## What this product is [MUST]` and `## What this phase ships, and what it does not [MUST]` opening prose sections; non-goals must explain why-not and revisit conditions.
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/product-model.md`** — `## Users and the world they live in [MUST]` and `## What we promise and what we do not [MUST]` opening prose sections; positive-first term definitions required.
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/product-roadmap-and-acceptance.md`** — `## The story from this phase to the next [MUST]` and `## What acceptance means here [MUST]` opening prose sections.
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/product-capability-entry.md`** — `## Tell this capability in one breath [MUST]` three-layer structure (one-sentence summary / concrete scene / why independent owner) replaces the weaker "1-3 paragraphs" hint.
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/product-journey-entry.md`** — `## A real user from A to B [MUST]` walks the journey as a real user experiences it; `## Why this journey is separate [MUST]` names each split reason explicitly.
- **`skills/ssot-bootstrap/references/bootstrap.md`** new `### 3.7 Product docs are written for humans` with the five rules (prose-before-tables, plain language, cell-is-not-paragraph, prefer-one-extra-sentence, always-anchor-on-a-concrete-scene). Shared readability floor for `product/` and `architecture/views/`.
- **`skills/ssot-doctor/references/doctor.md`** new L2 check `14I Product readability`; new hard-blocker bullet for product readability; new `[PRODUCT-READABILITY]` output tag with semantics.
- **`AGENTS.md`** new `## Writing Style (Global)` section: declares the long-running readability self-check posture for any template/protocol/Doctor change.

### Changed
- **`skills/ssot-preflight/references/area-model.md`** §2.1 `product/` adds a `**Writing style**:` subsection summarizing the five rules and pointing to `ssot-bootstrap` §3.7 so preflight readers see the constraint.
- **`skills/ssot-doctor/references/doctor.md`** `14B` Readable Authority extends scope from `root/view/domain body` to `root/view/domain/product body` — single readability authority across `architecture/` and `product/`.
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/product-readme.md`**, **`product-capabilities-readme.md`**, **`product-journeys-readme.md`** — added the helper line "this file only routes the reader; the body (written for humans in plain language) lives in the linked owner files", with a pointer to `ssot-bootstrap` §3.7.

## [2.28] - 2026-06

`semantic_impact: low` — introduces PLTL v3, the Promotable Long-Term Lessons mechanism. Collapses prior rank distinctions into three altitudes (Apex / Authority / Inbox) and replaces threshold-based promotion with explicit agent judgement fed by two evidence streams (repo + conversation reality; user interactive directives). Promotion or demotion across any altitude is a single move; `$ssot-doctor` stop-review is required only on moves that touch apex. No lint check, no new STATUS field, no new top-level SSOT area, no new Doctor label. Per v2.22 §8.1, low-impact entries are not promoted to a standalone `protocol-upgrades.md` section; this CHANGELOG entry is the only version-level record (the new `## Bundle Captures` section in `protocol-upgrades.md` is the inbox surface, not a version entry).

### Added
- **`skills/ssot-closeout/references/promotion-rationale.md`** (new): semantic owner of PLTL v3. Defines the three altitudes, the two evidence streams, the five self-check questions, the `rule` / `move` / `CAP-` schemas, the doctor stop-review trigger, the migration rule for pre-v2.28 rules, and worked promote/demote examples.
- **`skills/ssot-preflight/SKILL.md`** `## Park user-directive signals`: capture-side hook letting preflight park a `CAP-` row in `STATUS.md ## Pending Captures` with `signal_source: user-directive` when the user's prompt names a constraint. Preflight does not promote — it files the signal for closeout or audit to act on.
- **`skills/ssot-closeout/SKILL.md`** `## Distill & promote`: small-window two-stream scan over rules touched or cited in the current batch; emits zero or more `move` blocks. Apex moves are routed to `$ssot-doctor` stop-review; non-apex moves land directly.
- **`skills/ssot-audit/SKILL.md`** `## Scan the wide window`: large-window two-stream scan where cross-batch concentration and apex/authority drift become visible. New drift-signal row in `## Load on demand` routes bundle-side inbox lookups to `references/protocol-upgrades.md ## Bundle Captures`.
- **`skills/ssot-doctor/SKILL.md`** `## Reviewing promotion rationale`: stop-review posture for `move` blocks. Doctor never writes content; it confirms `stream_a` and `stream_b` anchors resolve and actually support the direction of the move, returning `no-more-required-changes` or `needs-fix` per the existing verdict schema.
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/status.md`** `## Pending Captures` (zh: `## 待捕获项`): inbox section with the `CAP-` row schema and a single `>` footnote routing to `$ssot-closeout references/promotion-rationale.md` for enum definitions.
- **`skills/ssot-audit/references/protocol-upgrades.md`** `## Bundle Captures`: bundle-side inbox mirror. The bundle does not dogfood; consumer-staged `deferred-export` rows are relayed here during the audit protocol-upgrades cadence.
- **`AGENTS.md`** top-of-file blockquote: `> AGENTS.md should fit in the reader's working memory; if a section grows past comfortable reading, consolidate or demote before adding.` Sits above `## What This Repo Is` so every reader hits it before any section grows.

### Changed
- **`skills/ssot-preflight/SKILL.md`** `metadata.protocol_version`: `2.27` → `2.28`.
- **`VERSION`**: `2.27` → `2.28` (physical mirror enforced by `tests/test-bundle-shape.sh`).

### Not required
- No change to `ssot-lint.sh`. PLTL v3 is enforced by skill discipline plus doctor stop-review on apex moves; there is no lint-time check for altitude transitions, evidence anchors, or `move` block schema.
- No change to `skills/ssot-bootstrap/`. Bootstrap continues to instantiate the existing template set; the new `## Pending Captures` section is the only template-side change and it lives under `assets/templates/`, not in the bootstrap workflow.
- No new top-level SSOT area, owner field, STATUS field, JSON/YAML state file, or Doctor label.

## [2.27] - 2026-06

`semantic_impact: low` — third pass of `assets/templates/` ceremony reduction: condition-marker convention for legacy-mode and optional sections, plus wide-table splits. No new SSOT area, owner field, STATUS field, or stop-review trigger.

### Changed
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/architecture-readme.md`**: wrapped the five legacy-only sections (`Design Brief`, `System Principles / Operating Model`, `Primary User / Operating Journeys`, `Core Invariants`, `Current / Target / Gap Summary`) in three separate `<!-- LEGACY-ONLY-START / END -->` blocks. The three blocks split around the two always-required Reader Map / View Index / Domain Index sections so deleting the legacy blocks in views+domains mode leaves the views-mode spine intact. The intro blockquote was rewritten to make views+domains the explicit default and to document the three-block convention. Per `references/architecture.md` §2.1.
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/architecture-domain-readme.md`**: wrapped six conditional sections (`### External Diagram Candidates`, `### Conditional Current Diagrams`, `### Target Diagrams`, `## Configuration / Variability Model`, `## Lifecycle / Concurrency / Scheduling Model`, `## Evolution / Migration Ledger`) in independent `<!-- OPTIONAL-START / END -->` blocks. Each marker carries a specific trigger condition and an explicit instruction: delete the entire block when not applicable; do not leave it as `not_applicable` boilerplate. Required sections (Boundary, Design Intent, Design Constraints, decomposition_basis, Runtime Flows, State/Data/Resources, Cross-Boundary Contracts, Invariants and Constraints, Failure and Recovery, Verification, Current/Target/Gap, Diagram Index, and the three current-mode Mermaid blocks) stay unwrapped. Per SKILL_STYLE.md anti-pattern "Filling empty-shell documents".
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/status.md`** `## Core Reference Document Review`: split the 10-column table into two narrower joined tables (`### Facts` with 5 columns and `### Review` with 6 columns, sharing the `Document` key column). The intro blockquote explicitly cites `status-protocol.md` §4.1 as still treating them as one logical 10-field ledger; the split is a rendering choice only.
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/bootstrap-manifest.md`** `## Area Status`: split the 9-column table into `### Assignment` (Area | Status | Assignment | Confidence) and `### Workflow` (Area | Covered scope | Remaining scope | Stop reviewer | Stop result | Remaining changes) tables. All 12 areas appear in identical order in both. Trailing prose notes (status enum, Tier ordering, etc.) preserved.
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/bootstrap-session.md`** `## Architecture Diagram Handling`: split the 7-column table into `### Diagram Index` (Diagram ID | Architecture path | Status | Coverage) and `### Diagram Trace` (Diagram ID | Evidence | Linked table rows | Outcome) tables.

### Not required
- No new SSOT top-level area, STATUS field, JSON/YAML state file, schema, command, skill, Doctor label, or `ssot-lint.sh` check.
- No new requirement on consumer projects. `tracked_skill_version` may advance to `2.27` as a no-op; previously-instantiated SSOT files continue to function — the new markers and table splits only affect future template instantiations.

## [2.26] - 2026-06

`semantic_impact: low` — second pass of `assets/templates/` ceremony reduction. No new SSOT area, owner field, STATUS field, or stop-review trigger. Per v2.22 §8.1, low-impact entries are not promoted to a standalone `protocol-upgrades.md` section; this CHANGELOG entry is the only record.

### Changed
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/status.md`**: collapsed seven dense inline blockquote paragraphs (~150 words each) into nine one-line pointers into `$ssot-preflight references/status-protocol.md` (§2.1 / §7.1 / §3.1 / §3 / §3.0 / §4 / §4.1 / §7 / §5.1 / §6). The blockquotes had been duplicating protocol prose owned by `status-protocol.md`; per `SKILL_STYLE.md` the body should name *when to load* the reference, not what it contains. Column headers and intra-cell enum hints are preserved.
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/bootstrap-manifest.md`**: added an explicit orthogonality blockquote between the existing Write rule and the Repository Overview section, stating that manifest tracks the *work-progress* axis (`pending` / `active` / `done` / `blocked`) while `STATUS.md` tracks the *content-quality* axis (`covered` / `gap` / `stale` / `unknown` / `not_applicable` / `conflict`), and that Phase 4 cleanup must set each area's final STATUS from its own stop-review evidence rather than auto-mapping manifest `done` to STATUS `covered`. The two common mappings (manifest `done` + scope-empty → STATUS `not_applicable`; manifest `done` + stop-review-passed + content-complete → STATUS `covered`) are spelled out inline. This was implicit in `status-protocol.md` §1 but absent from the template.
- **Reader Map column schema unified across 8 templates** (en+zh): `ssot-readme.md`, `architecture-readme.md`, `architecture-views-readme.md`, `architecture-domain-readme.md`, `product-readme.md` (already canonical, untouched), `development-readme.md`, `testing-readme.md`, `release-readme.md`. Canonical 5 columns: `Reader question | First stop | Authoritative owner | Evidence direction | Stop condition / risk`. Where the original used 6 columns (architecture-readme split Stop condition vs Risk; architecture-domain had separate Subtopic / One-line answer / Authoritative location / Evidence links / Why-or-risk columns) the data was merged or reshaped preserving row intent; the `One-line answer` and `Subtopic` columns were dropped per SKILL_STYLE (Reader Map rows route, they don't carry independent answers). In `ssot-readme.md` the legacy `Core` / `Reference` prioritization signal was folded into `Stop condition / risk` as the leading hint.

### Not required
- No new SSOT top-level area, STATUS field, JSON/YAML state file, schema, command, skill, Doctor label, or `ssot-lint.sh` check.
- No new requirement on consumer projects. `tracked_skill_version` may advance to `2.26` as a no-op; previously-instantiated STATUS.md files in consumer SSOTs continue to function — the removed blockquotes were always redundant restatements of `status-protocol.md`.

## [2.25] - 2026-06

`semantic_impact: low` — first pass of `assets/templates/` ceremony reduction. No new SSOT area, owner field, STATUS field, or stop-review trigger. Per v2.22 §8.1, low-impact entries are not promoted to a standalone `protocol-upgrades.md` section; this CHANGELOG entry is the only record.

### Changed
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/*.md`**: removed 40 redundant "Template instantiation note" HTML comments (20 EN + 20 ZH) that duplicated the same language-discipline rule on every template. The rule is now owned by a single new subsection in `references/bootstrap.md` (see Added).
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/adapter-thin.md`**: new merged adapter template. Replaces the two near-identical `adapter-agents-md.md` and `adapter-claude-md.md` files (the difference was a single `## Key Reminders` section). The new template wraps `Key Reminders` with an `<!-- OPTIONAL: keep when ... drop for ... -->` marker so a single template covers both AGENTS.md (drop the section) and CLAUDE.md / GEMINI.md (keep it) targets. Placeholders also normalized from `{PROJECT_NAME}` / `{INVARIANT_1}` / `{DATE}` style to the bundle-standard `<project-name>` / `<invariant-1>` / `<date>` form, eliminating the only remaining `{FOO}`-style placeholders in the bundle.
- **`skills/ssot-bootstrap/assets/templates/en/bootstrap-manifest.md`**: added missing `| Tier 0 | | | pending | | |` row in the Convergence Checks table (the ZH counterpart already had it; this restores en/zh structural parity).
- **`skills/ssot-bootstrap/references/bootstrap.md`**: rewrote item 9 of Phase 1 Outputs to point at the new single `adapter-thin.md` and explain the optional `Key Reminders` toggle.

### Added
- **`skills/ssot-bootstrap/references/bootstrap.md` §2 → "Language discipline when instantiating templates"**: new subsection owning the language-translation rule that was previously duplicated 40 times in templates. Covers both rendered SSOT files and bootstrap-only files (`recon.md`, `manifest.md`, session logs) before they are archived or deleted at Phase 4.
- **`skills/ssot-bootstrap/references/templates-index.md`**: maintainer index of all 23 templates under `assets/templates/{en,zh}/`, with columns `Template / Purpose / Default destination / Section in bootstrap.md`. Adds a single place to update when templates are added or removed, removing the requirement to hand-edit each path reference in `bootstrap.md`.

### Removed
- **`skills/ssot-bootstrap/assets/templates/{en,zh}/adapter-agents-md.md`** and **`adapter-claude-md.md`** (4 files total): replaced by the single `adapter-thin.md` (see Changed).

### Not required
- No new SSOT top-level area, STATUS field, JSON/YAML state file, schema, command, skill, Doctor label, or `ssot-lint.sh` check.
- No new requirement on consumer projects. `tracked_skill_version` may advance to `2.25` as a no-op; templates that have already been instantiated into a consumer's `SSOT/` are not affected (the removed comments are merely no longer added to *new* instantiations).

## [2.24] - 2026-06

`semantic_impact: low` — second pass of `SKILL.md` body distillation against `SKILL_STYLE.md`; no new area, owner field, or stop-review trigger. Per v2.22 §8.1, low-impact entries are not promoted to a standalone `protocol-upgrades.md` section; this CHANGELOG entry plus the collapsed bullet under v2.22 are the only record.

### Changed
- **`skills/ssot-bootstrap/SKILL.md`**: body distilled from 19 lines / ~140 words to 22 lines / ~150 words (line count unchanged, register replaced). Removed "Use this skill only…" description echo and "protocol version is owned by `$ssot-preflight`" lifecycle restatement. Replaced the 6-step workflow with a second-person posture ("you are creating a repository's first authoritative SSOT…") that reframes bootstrap as evidence absorption rather than template-filling, an explicit `assets/templates/` anti-pattern guardrail, an outcome-conditioned self-certification ban, and a 4-row Load-on-demand table.
- **`skills/ssot-closeout/SKILL.md`**: body distilled from 22 lines / ~280 words to 25 lines / ~210 words. Removed description echoes and the 9-step workflow. Replaced with a "reconcile what just happened against `SSOT/`" posture sentence (covering diff / tests / user confirmations / preflight deltas — not just file changes), a folded no-op clause, an explicit "do not invoke full `$ssot-doctor` here" guardrail, and an outcome-conditioned ban on self-certifying waterline / `covered/converged` / language-lock / bootstrap `passed`.
- **`skills/ssot-audit/SKILL.md`**: body distilled from 27 lines / ~250 words to 19 lines / ~160 words. Removed description echoes, the duplicate "Route" vs "Rules" structure, and the lifecycle restatement. Replaced with a "you have been routed here, not to do new work" posture sentence, an explicit "segment large diffs and long transcripts" anti-pattern (the failure mode this skill exists to prevent), an outcome-conditioned self-certification ban on `tracked_commit / tracked_session / tracked_skill_version`, and a 5-row Load-on-demand table that doubles as the drift-signal router.
- **`skills/ssot-doctor/SKILL.md`**: body distilled from 23 lines / ~220 words to 22 lines / ~190 words. Removed description echoes and the 5-step workflow. Replaced with a "you are the independent check on SSOT credibility" posture sentence (also reframing doctor as *not* an editor and *not* an audit catch-up), an explicit "run `ssot-lint.sh` before subjective review" guardrail, the stop-reviewer signature scope as the only signature that may advance a waterline / claim `converged` / set bootstrap `passed` / change a language lock, and an outcome-conditioned return rule (`no-more-required-changes` only when reviewed scope has zero remaining required fixes; otherwise `needs-fix` with concrete items — never a soft "looks fine"). Removed the `assets/scripts/test/run-tests.sh` line from the load table (maintainer-only, not loaded during a doctor pass).

### Engineering bucket (no protocol bump on its own)
- **`.github/workflows/ci.yml`**: `shellcheck` invocation upgraded from `-e SC2034` to `-S warning -e SC2034` so `shellcheck 0.9`'s elevated `SC2016` (info: expansions in single quotes) no longer fails CI on intentional literal patterns in `ssot-lint.sh`. Real warnings still fail.

### Not required
- No new SSOT top-level area, STATUS field, JSON/YAML state file, schema, command, skill, Doctor label, or `ssot-lint.sh` check.
- No new requirement on consumer projects. `tracked_skill_version` may advance to `2.24` as a no-op once it is confirmed no project-local material quoted the prior SKILL.md wording verbatim.

## [2.23] - 2026-06

`semantic_impact: low` — SKILL.md body distillation; no new area, owner field, or stop-review trigger. Per v2.22 §8.1, low-impact entries are not promoted to a standalone `protocol-upgrades.md` section; this CHANGELOG entry is the only record.

### Added
- **`skills/SKILL_STYLE.md`**: contributor-facing acceptance standard for `SKILL.md` prose bodies, reverse-engineered from Anthropic's `grill-me` skill. Five criteria (mode-switch / outcome-condition / structural metaphor / single anti-pattern guardrail / second-person imperative) plus a bundle-specific anti-pattern list. Includes a PR review procedure requiring per-sentence criterion annotation.

### Changed
- **`skills/ssot-skill/SKILL.md`** (compatibility shim): body distilled from 22 lines / ~230 words to 11 lines / ~60 words. Removed duplicated routing list; kept the single trigger-to-skill mapping. Posture sentence rewritten as second-person imperative. No semantic change; same five lifecycle routes.
- **`skills/ssot-preflight/SKILL.md`**: body distilled from 94 lines / ~1100 words to ~45 lines / ~470 words. Replaced the 8-step preflight checklist with a posture sentence plus three outcome-conditioned dimensions (adjudications / language / version). Folded the 14-row routing table into default-on rules plus pointer to `SSOT/README.md` task-entry map and `references/area-model.md` (full mapping unchanged, just delegated). Folded the durable-fact bullet list into a single comma-list; the `Rule / Trigger / Why / Evidence / Failure-mode` discipline schema now lives only in `references/area-model.md §2.5`, which the body explicitly points to. Frontmatter `semantic_impact: low` (introduced by v2.22) retained.
- **`skills/ssot-doctor/assets/scripts/ssot-lint.sh`** and **`run-tests.sh`** (engineering bucket): all script output and comments translated from Chinese to English; test fixture content (which exercises `documentation_language: 中文` semantics) intentionally retained in Chinese.

### Not required
- No new SSOT top-level area, STATUS field, JSON/YAML state file, schema, command, skill, Doctor label, or `ssot-lint.sh` check.
- No new requirement on consumer projects. `tracked_skill_version` may advance to `2.23` as a no-op once it is confirmed no project-local material quoted the prior SKILL.md wording verbatim.

## [2.22] - 2026-06

### Changed (preview)
- **Self-review 减负（v2.22 优化方案系列）**: 削减 B 类仪式性流程（自审计/账本/归零检查），保留 A 类长期记忆骨架（决策/Bug/Gotcha/Discipline/Architecture）。
  - STATUS.md 分层：停载 batch closeout blockquote、验证账本全表、stop-review 全表；目标 ~70 行。
  - `ssot-lint.sh` check#2 `converged` + drift 冲突从 FAIL 降为 WARN（`self-reference` 闭环）。
  - `status-protocol.md §7` 改为默认 self-reviewed + 4 个硬性独立 reviewer 例外。
  - `SKILL.md` frontmatter 新增 `semantic_impact` 字段（`none | low | high`），协议升级税按 impact 分级。
  - `protocol-upgrades.md` 按 high-impact 列条目，none/low 归入下一个 high entry 的 collapsed list。
  - `ssot-lint.sh` 移除副本一致性检查（`diff -qr` 永远 PASS）。
  - `SKILL.md §1.3` `[MUST]/[SHOULD]/[MAY]` 三级分类删除。
  - DEC 锚点规则收紧：`src/**` 或 `tests/**` 中 `# DEC-NNNN` 注释机械引用为充要条件。
- 详情见 v2.22 最终决议各 Phase 实现。

## [2.21] - 2026-06

### Added
- **Agent operation discipline routing**: `area-model.md §2.5` now defines `development/` discipline as the owner of cross-task imperative rules (`Rule / Trigger / Why / Evidence / Failure mode`), with a recommended `development/discipline.md` sub-file carrying `DISC-NNNN` entries. Discipline is task-pattern-scoped; `gotchas/` remains file/module-scoped.
- `area-model.md §4.1 Default fallback for unrouted durable knowledge`: imperative rule → `development/`; file-scoped trap → `gotchas/`; trade-off → `decisions/`; bug instance takeaway → `bugs/<entry>.md`. Explicitly forbids creating new top-level areas to absorb unrouted knowledge.
- `update-routing.md §2` new file-type row for external SDK / third-party API integration code (`*sdk*`, `*adapter*`, `integrations/`, manifest version bumps of an external SDK / LLM client / remote-service client) routed to architecture/, `development/` discipline, and bugs/ when applicable.
- `update-routing.md §3` four new conversation-signal rows for: long-term lesson / "from now on always X", mock-only-passed-real-service-differed, hotfix-of-hotfix on the same external behaviour, and the meta-question "where should this lesson live?" (which dispatches to §4.1 fallback).
- `update-routing.md §4` cascade row for discovery of long-term agent-operation discipline, requiring sync to `development/`, originating bug/decision and optionally `testing/` for the enforcement test.
- `ssot-preflight/SKILL.md §3` in-task write trigger for user-confirmed cross-task agent operation discipline.

### Changed
- `area-model.md §2.10 gotchas/` upgrades the `Trigger` field from `(recommended)` to `[SHOULD]` and adds an explicit boundary note: cross-task procedural rules belong in `development/` discipline, not in `gotchas/`.

### Not required
- No new SSOT top-level area, STATUS field, JSON/YAML state file, schema, command or skill.
- No new Doctor label; reuse `[CONSUMPTION]` and `[OWNER-ANCHOR]` when discipline entries are unreferenced or duplicate a bug takeaway without a clear owner.
- No `ssot-lint.sh` or `test-bundle-shape.sh` changes; v2.21 is a semantic protocol extension (same posture as v2.18).
- No mechanical migration of historical `gotchas/` entries; only the trigger field convention is reaffirmed.

## [2.20] - 2026-06

### Added
- **Installer agent registry expanded from 4 to 70 agents** to align with the Vercel `vercel-labs/skills` (skills.sh) ecosystem. Newly supported agents include Gemini CLI, GitHub Copilot, OpenCode, Cline, Roo Code, Continue, Augment, Zed, Goose, Aider, Junie, Trae (+CN), Crush, Warp, OpenHands, Replit, Devin, Droid, Qwen Code, Lingma, Kilo, ForgeCode, Tabnine CLI, Amp, Antigravity (+CLI), AstrBot, Autohand, IBM Bob, CodeArts, CodeBuddy, Codemaker, Code Studio, Command Code, Cortex, Deep Agents, Dexto, Firebender, Hermes, iFlow, inference.sh, Jazz, Kimi Code CLI, Kiro CLI, Kode, Loaf, MCPJam, Mistral Vibe, Moxby, Mux, Neovate, OpenClaw, Ona, Pi, Pochi, PromptScript, Qoder (+CN), Reasonix, Rovo Dev, Terramind, Tinycloud, Zencoder, Zenflow, AdaL, and a `universal` target writing to `.agents/skills`.
- `--list-agents` flag prints `KEY / NAME / DETECT / GLOBAL PATH` for every registered agent plus a detection summary for the current system.
- Legacy short keys (`claude`, `codeium`, `copilot`, `gemini`, `aider`, `tabnine`, `iflow`, `kimi`, `kiro`, `autohand`, `hermes`, `codearts`) are preserved as aliases that resolve to canonical Vercel keys (`claude-code`, `windsurf`, `github-copilot`, `gemini-cli`, `aider-desk`, `tabnine-cli`, `iflow-cli`, `kimi-code-cli`, `kiro-cli`, `autohand-code`, `hermes-agent`, `codearts-agent`). Existing CLI invocations and CI scripts keep working unchanged.

### Changed
- The interactive multi-select widget is now paginated and searchable. With 70 supported agents the previous full-list redraw would overflow most terminals; the new widget shows a scrolling viewport with `/` filter, PageUp/PageDown, toggle-all-visible (`a`), and deselect-all (`q`) keys. Detected agents are still pre-selected.
- Multiple agents sharing the same physical install path (for example `cline`, `dexto`, and `loaf` all writing to `.agents/skills`) are now deduplicated with a single warning; the bundle is copied once.
- Project-only agents (currently `promptscript`) with no global install location now fail loudly under `--scope global` instead of silently installing to an empty path.
- Installer detection respects `$XDG_CONFIG_HOME`, `$CLAUDE_CONFIG_DIR`, `$CODEX_HOME`, `$VIBE_HOME`, `$HERMES_HOME`, `$AUTOHAND_HOME`, `$APPDATA`, and `$FLATPAK_XDG_CONFIG_HOME` where the corresponding agent uses them, matching `vercel-labs/skills` behaviour.

### Notes
- The SSOT protocol semantics, lifecycle skills, references, and templates are unchanged from 2.19 — only the installer's packaging surface and agent coverage move. The `VERSION` bump exists because `tests/test-bundle-shape.sh` enforces VERSION == `metadata.protocol_version` and because the installer surface is part of the publicly observed bundle.

## [2.19] - 2026-06

### Added
- **`SSOT/01-product/` as a mandatory top-level area** — the product trunk now owns the PRD, product promise, users / operators, product boundary, capabilities, journeys, roadmap, and product acceptance. Architecture only records technical implementation, runtime execution, failure / recovery, observability, and implementation gap, and links back to the product owner.
- Product bootstrap templates: `product-readme.md`, `product-prd.md`, `product-model.md`, `product-roadmap-and-acceptance.md`, `product-capabilities-readme.md`, `product-capability-entry.md`, `product-journeys-readme.md`, `product-journey-entry.md`.
- Doctor semantic labels: `[PRODUCT]`, `[PRODUCT-OWNER]`, `[PRODUCT-ARCH-DRIFT]`.
- `ssot-lint.sh` deterministic checks for the required product skeleton and for the `product` row in the `STATUS.md` coverage table.

### Changed
- Source material routing: PRD, product promise, users / operators, capability, journey, roadmap, and product acceptance now default to the product owner. This supersedes the v2.8 / v2.9 routing that absorbed PRD content into `architecture/views/`.
- `STATUS.md` coverage table MUST include a `product` row.
- Architecture views and domains MUST link to the product owner instead of re-defining product promise, product non-goals, user journeys, or product acceptance. Implementation gap links back to the product owner.

## [2.18] - 2026-06

### Added
- Architecture evidence-guided decomposition: `decomposition_basis` must record entrypoints, call/dependency edges, shared state, runtime flow, failure boundaries, contract surface, tests, configs, scripts and ADR material, including rejected axes and false friends.
- Bottom-up writing order for architecture: `domain evidence -> view synthesis -> root Reader Map`. Root/view claims must trace back to domain evidence or be marked `gap` / `unknown`.
- Reader Map as a reader route (intent, first stop, authoritative owner, evidence direction, stop condition, risk); it must not host independent long-lived facts.
- Authoritative owner anchor: each long-lived claim has exactly one owner (domain, view, engineering area, decision or other existing authority); non-owner sites only link.
- Architecture rubric in Doctor output: 1-minute mental model, view raison d'etre, domain why-separate, owner/evidence/why/risk/constraint, required diagrams, and current/target/gap separation.
- Doctor labels `[DECOMPOSITION]`, `[SYNTHESIS]`, `[OWNER-ANCHOR]`; existing `[READER-MAP]`, `[READABILITY]`, `[DIAGRAM]`, `[ARCH-ROOT]`, `[ARCH-VIEWS]`, `[ARCH-DOMAINS]` continue to apply.

### Changed
- Architecture rubric tightened; root README must not carry independent long-lived facts and must not pre-write global conclusions without domain-level evidence.

### Not required
- No new SSOT top-level area, STATUS field, JSON/YAML state file, schema, command or skill.
- No mechanical migration of legacy projects to the latest `views/ + domains/` template; only authority, evidence and reader-routing scope is touched.
- No Tree-sitter, LSP, automatic dependency graph, code indexer or generator.
- No `ssot-lint.sh` changes; these are L2 semantic checks.

## [2.17] - 2026

### Added
- SSOT Skill bundle: formal entry skill `ssot-preflight`; process skills `ssot-bootstrap`, `ssot-closeout`, `ssot-audit`, `ssot-doctor`; legacy `ssot-skill` retained only as a lightweight compatibility shim.
- Open adjudication parser: canonical heading `## 开放裁决项`, with backward compatibility for `## 待裁决项`.
- Doctor label `[SKILL-SPLIT]` for bundles missing the formal entry, a process skill, the shim, the protocol owner or process trigger descriptions.

### Changed
- Entry skill renamed: task start now triggers `$ssot-preflight` instead of `$ssot-skill`.
- Protocol-version owner migrated to `skills/ssot-preflight/SKILL.md` (`metadata.protocol_version`); `tracked_skill_version` now refers to the bundle protocol version rather than the old `ssot-skill/SKILL.md`.
- Adapter / core-ref boundary clarified: the 50-line size cap and SSOT-source hash apply only to files carrying the SSOT-generated marker. Handwritten or mixed startup files are no longer flagged `[ADAPTER]` for missing the marker; missing SSOT routing reports as `[CONSUMPTION]`, factual drift as `[CORE-REF]`.

### Not required
- No new SSOT top-level area, JSON/YAML state file or product-grade Web/API truth.
- No per-skill separate installation; phase 1 installs the bundle together.
- No mechanical renaming of historical text; only triggers, protocol watermark and runtime prompts in authoritative positions are updated.

## [2.16] - 2026

### Removed
- All naming entries, source-material classifications and special routes for legacy externally generated repository-knowledge surfaces. Reader Map, claim-to-evidence, script/tool inventories and diagram-candidate governance are now native protocol capabilities, not external imports.

### Changed
- Source material scope limited to README / docs / ADR / PRD / runbook / design docs / subsystem README / user-provided external material; external auto-summaries are accepted only as ordinary candidate material.
- Reader Map provenance: generated from `decomposition_basis`, reader questions, authoritative positions and evidence; never borrowed from external topic trees.
- External generated diagrams, screenshots, IDE dependency graphs and auto dependency graphs are candidates only; they must be rewritten as maintainable Mermaid with Diagram ID, Status, Covers, evidence and owner before counting as authoritative.

### Added
- Doctor label `[LEGACY-SURFACE]` for residual parallel generated knowledge surfaces, legacy-named entries, dedicated source-material categories, or external topic trees being treated as authority.

### Not required
- No migration scripts; the protocol-upgrade audit is sufficient.
- No mechanical rewrite of all existing SSOT files to the latest template.
- No active fetching of external generated material.
- No new SSOT area, STATUS field, schema or generator.

## [2.15] - 2026

### Added
- `[CORE-REF]` review slice: `AGENTS.md`, `CLAUDE.md`, `.cursor/rules/*`, `.windsurf/rules/*`, `GEMINI.md` and equivalent startup-time / agent-rules files are now first-class source material. New `STATUS.md` 核心参考文档审查 table; new Doctor `[CORE-REF]` L1/L2 checks.
- Reader Map / 快速理解地图 protocol for entry routing: entries only link to authoritative positions and must not host independent long-lived facts.
- Readable Authority / 可读权威正文: prose body must establish a mental model via short narrative, claim, evidence, why, risk and constraint; tables and lists alone are insufficient.
- Claim-to-evidence writing as standard for key assertions in architecture views/domains and engineering operating areas.
- Engineering script/tool inventory fields under `development/`, `testing/`, `release/` and deployment areas.
- Diagram-candidate governance: external generated diagrams, screenshots and dependency graphs accepted only as candidates; authoritative diagrams must be Mermaid fenced blocks with metadata, evidence, status and current/target separation.
- Doctor labels `[CORE-REF]`, `[READER-MAP]`, `[READABILITY]`; extended `[DIAGRAM]` for misuse of external generated diagrams as authoritative.

### Changed
- L2 semantic checks scoped: `ssot-lint.sh` remains deterministic and is not asked to judge command, workflow or architecture-fact semantics; those remain with the Doctor reviewer.
- `[ADAPTER]` continues to cover thin-adapter file shape only; `[CONSUMPTION]` continues to cover SSOT trigger linkage; `[CORE-REF]` covers factual correctness of startup-time references.

### Not required
- No new `SSOT/core-reference/` or other top-level area.
- No mechanical replacement of user-authored `AGENTS.md` / `CLAUDE.md`; default output is specific recommendations only.
- No `[CORE-REF]` automation inside `ssot-lint.sh`.
- No new top-level parallel knowledge area, schema, STATUS field or generator.

## [2.14] - 2026

### Added
- L4 behaviour-layer trigger / consumption-side audit: new `skills/ssot-doctor/references/consumption-audit.md` as the semantic owner for verifying whether SSOT was actually triggered and consumed in real transcripts. Honours the L4 probe promise outstanding since v2.13.
- Near-field trigger probe during session self-check (zero-cost, always on).
- Far-field consumption audit available on demand (`[MAY]`) when the user names it or near-field signals are insufficient.

### Changed
- `[CONSUMPTION]` Doctor label scope extended: L1 static link breaks continue to use it; L4 behaviour-layer attribution and trigger-side optimisation flow through the consumption audit without a new label.

### Not required
- No mandatory far-field transcript analysis every session.
- No automatic rewriting of trigger-side files; recommendations only by default.
- No new SSOT area, STATUS field or required-to-create files.

## [2.13] - 2026

### Added
- Pre-write conflict / negation scan in SKILL.md §3.1.
- Evidence pointer symbol anchor (`path#symbol`) preferred over `path:line` to survive code movement; legacy line pointers are not mechanically migrated.
- Gotcha executable contract: high-risk active gotchas must give a "don't do / do instead" pair.
- Optional SSOT-source hash line on SSOT-generated thin adapters for drift detection (`SSOT-source: <path>@<hash>`).
- SSOT consumption link check (`[CONSUMPTION]` Doctor label): adapter must carry SSOT read instruction and route to SSOT; `SSOT/README.md` navigation entry must exist.
- `ssot-lint.sh` L1 automation extended to checks #6 (confidence: hypothesis in `architecture/`), #7 (SSOT-generated thin adapter <=50 lines and optional source hash) and the consumption link check.

### Not required
- No mechanical migration of existing `path:line` evidence pointers.
- No requirement to fill executable contracts for all gotchas (high-risk first).
- Source hash on thin adapters is `[MAY]`, not required.
- No new SSOT area, STATUS field or required-to-create files.

## [2.12] - 2026

### Added
- Protocol layering with `[MUST]` / `[SHOULD]` / `[MAY]` markers in SKILL.md to lower Agent execution friction under high task load.
- `self-reviewed` downgrade path in the STATUS independent stop-review gate: medium-impact updaters may self-review with explicit recording.
- Legacy direct-child-domain compensation: when no `architecture/views/` exists, root `architecture/README.md` MUST carry `设计简报`, `核心不变量`, `Current / Target / Gap 摘要` sections.
- `decomposition_basis` template for architecture splits.
- Architecture migration trigger when the domain count is >= 4 or a journey crosses >= 3 domains (see `architecture.md`).
- Bootstrap recon archive path: `recon.md` is archived as `decisions/0000-bootstrap-recon.md` rather than deleted during Phase 4 cleanup; manifest and session logs are still cleaned up.
- `ssot-lint.sh` script available as `[MAY]` CI / Doctor pre-gate; can be invoked directly from the skill path without copying into the project.

### Changed
- `STATUS.md` coverage tables (`区域 / 状态 / 备注`) must not maintain derivable information (entry counts, sub-directory entry status, recent test results); the 备注 column becomes a pointer to sub-directory README, carrying only unique semantics.

### Not required
- No traversal of historical stop-review entries to back-fill `self-reviewed`.
- No new SSOT files or directories.
- No new required-to-create file or area.

---

[Unreleased]: https://github.com/huangpufan/SSOT-SKILL/compare/v2.21...HEAD
[2.21]: https://github.com/huangpufan/SSOT-SKILL/releases/tag/v2.21
[2.19]: https://github.com/huangpufan/SSOT-SKILL/releases/tag/v2.19
[2.18]: https://github.com/huangpufan/SSOT-SKILL/releases/tag/v2.18
[2.17]: https://github.com/huangpufan/SSOT-SKILL/releases/tag/v2.17
[2.16]: https://github.com/huangpufan/SSOT-SKILL/releases/tag/v2.16
[2.15]: https://github.com/huangpufan/SSOT-SKILL/releases/tag/v2.15
[2.14]: https://github.com/huangpufan/SSOT-SKILL/releases/tag/v2.14
[2.13]: https://github.com/huangpufan/SSOT-SKILL/releases/tag/v2.13
[2.12]: https://github.com/huangpufan/SSOT-SKILL/releases/tag/v2.12
