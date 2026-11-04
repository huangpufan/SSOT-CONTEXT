# Evidence for 3.10 (2026-11-04): flagged rows are fixed by naming the case in the row

This records how the 3.10 change to the row check in `skills/ssot-bootstrap/references/mining.md` was tested, so the claims in `CHANGELOG.md` can be checked. It uses the fd answer key and measures of `tests/trials-3.7.md`.

## 1. The problem

A mining round writes register rows, and a fresh helper checks them against the code. Before 3.10 the text said to fix a flagged row "by narrowing, moving it to its owner as plain description, or dropping it". On fd with `deepseek-v4.1-flash`, rows that came out of that step were often still rejected by the graders (19 of 27 accepted in one run, 8 of 15 in the other): a row said "always" where its own explanation named an exception, or it left out an override. Two earlier attempts to fix this by changing how rows are written (a rewrite step in 3.10 candidate `c310b`, a "list the cases first" paragraph in `c310a`) could not be told apart from noise, because the same finished SSOT graded 6 to 16 claims apart from one grading to the next.

## 2. What was tried

The experiment keeps the mining run as it was and changes only what happens to its new rows afterwards. Two finished 3.9 mining runs of fd's output area were copied (27 and 15 new rows). On each copy:

- Fresh adversarial reviewers (seven review prompts in all) checked every new row against the code, the row's own explanation, and the history, and for each flagged row listed the case, its `path:line` or commit, and the smallest change to the row's words that makes it true.
- One fresh fixer then went through the flagged rows. It checked each case itself, then edited the row so it holds in every verified case by naming the case or narrowing the universal word, never dropping a part, and fixed the explanation where it disagreed with the new wording. It was told not to touch confirmed rows, ids, kinds, statuses, or links.

The shipped text in `mining.md` §4 is a condensed version of these two prompts. The measure was the same one used for the earlier attempts: the 44 claims of fd's output area, each judged by the unchanged graders (coverage, a code-reading row grader, and a row-consistency grader), three gradings per copy, majority of the three.

## 3. Result

| Copy | Rows flagged | Rows changed | Output claims safe | New rows accepted | Words in new rows |
|---|---|---|---|---|---|
| Run A before | | | 29 | 19/27 | 418 |
| Run A after | 18/27 | 17 | 39 | 22/27 | 812 |
| Run B before | | | 27 | 8/15 | 198 |
| Run B after | 14/15 | 14 | 39 | 14/15 | 554 |

Confirmed rows changed: 0 in both. Nothing outside `SSOT/` changed. Cost: reviewers about 18 minutes of wall time for 7 prompts on 4 judge slots; the fixer 8 and 11 minutes (86 and 111 tool calls); no more grading than the three gradings above.

A single grading of one SSOT varies by 6 to 16 claims, so a gain of 10 or 12 claims is within that spread for one grading. Here each figure is the majority of three gradings and both copies moved the same way, which makes the direction credible but not the size.

## 4. Do the lengthened rows hold in the code?

The graders and the fixer are the same model, so a higher score could come from rows that are longer and agree with themselves. As a check, fresh judges broke each of the 31 rows the fixer changed into clauses and judged every clause true, false, or unverified against the code alone, treating `SSOT/` text as a claim and not as evidence. The same was done for the same rows before the fix.

| | Before | After |
|---|---|---|
| Rows (of 31) with a false clause | 15 | 5 |
| False clauses | 18 of 95 | 6 of 169 |

Thirteen rows lost their false clause, two kept one, and three rows were clean before and had one after: the fixer added a new condition that is wrong. I read the code behind four of the five rows that still have a false clause, and the judges' reading held in all four, though one is minor: for example one row says a leading-dash root without `./` is unguarded, while `src/cli.rs` turns the root `-` into `./-`; another says diagnostics are outside the escaping rule, while `src/error.rs` escapes them. This is why the text keeps the existing instruction to check fixed rows again, once.

## What this does not show

- A whole mining round that follows the shipped text. The reviewers and fixer here ran from scripted prompts that `mining.md` §4 now summarizes; no lead has yet followed the new wording unaided.
- A second pass. The re-check of fixed rows was not run, so it is unknown whether check and fix converge to no false clauses or trade old errors for new ones.
- Independence. The reviewers, fixer, and graders are all `deepseek-v4.1-flash`. The code-reading check in section 4 uses a different prompt and a clause-level method, but the same model, and ran once per row. I read the cited code for four of the six remaining false clauses and did not read the 18 before-fix ones.
- Other repositories. Two mining runs of one area of one repository, paired on the same content, so run-to-run mining noise is not covered. Click was not used.
- Reading cost. The changed rows grew from about 16 and 14 words to about 39 (up to 64). What an agent reading the register at preflight pays for that is not measured.
- The fixer also edited explanation sections, so part of the row-to-explanation agreement may come from harmonized wording.
