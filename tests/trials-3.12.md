# Evidence for 3.12 (2026-11-05): an over-budget owner file is split by topic, not shortened

This records how the 3.12 change to `skills/ssot-bootstrap/references/mining.md` §4 was tested, so the claims in `CHANGELOG.md` can be checked. All runs used `deepseek-v4.1-flash` on fd's output area, copied under `/var/tmp`; nothing touched a real repository.

## 1. The problem

A reader reads a topic file in `SSOT/` before working. `ssot-check` warns when one passes about 16,000 characters, and the memory model (§4) already says what to do: turn it into a folder with one file per subtopic. `mining.md` did not say it, so a lead who had a writer produce an owner file that was too long had only the warning and its own brief to go by.

Six runs of the 3.10 and 3.11 texts on fd's output area (two real runs and four replays from just before the writer) ended with these owner files for the output rules:

| Run | Owner file at the end |
|---|---|
| `r1` | `output.md`, 16,000 characters |
| `r2` | `output.md`, 13,436 |
| `pw1` | `output.md`, 18,741, with the checker's warning left in place |
| `pw2` | a folder of 7 files, largest 7,751 |
| `pv1` | `output.md`, 15,998 |
| `pv2` | `output.md`, 15,908 |

Three of the six sit just under the line. The writer's report in `r1` says why: "to stay under the 16,000-character reading budget I tightened prose and dropped or shortened only secondary admission notes". One of the notes it dropped was that an explicit root spelled `-` is outside the leading-dash guard. When the 3.10 text was replayed from `r1`'s state (`rp1`), a row checker flagged exactly that missing exception on the INV-16 row and cited the writer's note that it had been dropped. The `pv1` writer says it trimmed redundant prose and kept every condition; I found nothing about it in `pv2`'s working files.

## 2. What was tried

Candidate `c312` is 3.11 plus one sentence in §4: when the checker warns that an owner file is past the reading budget, split it by topic (memory model §4), and never shorten it by dropping a condition, exception, alias, or piece of evidence.

It was replayed twice (`pq1`, `pq2`) from the same state as `pv1` and `pv2`: `r1`'s working files up to the admission decisions, with nothing written to `SSOT/` yet, so the lead writes its own writer brief. The cap was 90 minutes, not 40.

## 3. Result

| Run | Size of `output.md` when the lead first saw it | What happened | Finished | `ssot-check` |
|---|---|---|---|---|
| `pq1` | 20,270 characters | the lead wrote that it would tell the writer to split it by topic "per memory model §4"; the writer did, and the new files totalled about 17,200 (the old file was 16,654 at that point); after the row fixes the folder held 5 files, 18,521 in all, largest 4,640 | yes, 39 minutes | 0 errors, 0 warnings |
| `pq2` | 17,755 characters; the writer's report says three tightening passes left 16,967 | the lead split it itself into a folder of 4 files (18,834 in all, largest 7,062), although its own brief to the writer said "Do not create a folder/split" | yes, 53 minutes | 0 errors, 0 warnings |

The `pq2` writer reports that three tightening passes left it at 16,967 and that going lower would have meant dropping a named condition, exception, alias, test name, or commit hash, so it stopped there. The `pq1` writer's report was not read for this. In both runs the new register rows entered the register only after the row check had passed (this is the 3.11 behaviour). In `pq1` the re-check was started at step 721, the lead wrote "All 13 rows are admitted" at step 785, and the rows were written at step 791. In `pq2` the second check reported 13 of 13 protected as written at step 629 and the rows were merged at step 640; at step 624 the lead had considered inserting them early and wrote "better wait".

Without the sentence, one of six runs ended with a folder. With it, two of two did. That difference is small: if three of eight runs had split by chance, both splits landing in the two-run group has a probability of about 0.11.

## What this does not show

- That the sentence is what made the leads split. The `pq1` lead cited memory model §4, which the sentence names, and the `pq2` lead split against its own brief; both fit the sentence, but two runs cannot separate that from the lead reading the checker's warning, which every run saw.
- That the split lost nothing. In `pq1` the writer's files fell from 20,270 characters to about 17,200 when it split, and the pre-split file was deleted, so I cannot compare the two word for word. What exists is indirect: the row checks ran after the split and compared each row with the admission text and the folder; the first found one dropped condition (INV-15, the followed-symlink case), the fixer restored it, and the re-check reported no condition dropped. That is as far as those checkers could see. In `pq2` the lead's script found every rule paragraph word for word after the split, but the writer had already tightened the file from 17,755 to 16,967 before that.
- That a file under the budget stays whole. No replay had an owner file under 16,000 with the sentence; the sentence applies only to a warning, so it should not trigger, but this was not run.
- That a reader gets the same from a folder. `ssot-check` found no broken link, and the single grading below read both folders; nothing more was tested.
- Other repositories, areas, or models. fd's output area, flash only, two replays from one starting state.
- A whole mining round. The replays start after the miners and the challenge.

## Reading the folder

One grading of `pq1` and `pq2` with the unchanged graders, to see that a folder owner is read at all. One grading varies by 6 to 16 claims, so it supports no comparison.

| Run | Owner | Output claims found in `SSOT/` (of 44) | Claims backed by an accepted row (one grading, of 44) | Words in the 14 new or changed rows |
|---|---|---|---|---|
| `pq1` | folder, 5 files | 44 | 31 | 814 |
| `pq2` | folder, 4 files | 42 | 20 | 530 |
| `pw1`, `pw2` (3.11, single file) | one file | 44, 42 | 29, 36 | 430, 395 |
| `rp1`, `rp2` (3.10) | one file | 42, 42 | 22, 13 | 335, 339 |

The folder was read: the graders found 44 and 42 of the 44 claims in it, as many as for a single file. The scores in the fourth column range from 13 to 36 across these six runs, so no difference between them is claimed.

The last column is a separate observation. The 14 rows changed in `pq1` and `pq2` are longer than in the earlier replays (58 and 38 words a row, against 24 to 31). The 3.12 sentence does not touch row length, so this is not attributed to it; it is one run each, and it adds to the open question of what an agent pays to read longer rows at preflight.
