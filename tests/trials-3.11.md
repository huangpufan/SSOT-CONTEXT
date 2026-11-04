# Evidence for 3.11 (2026-11-05): a mining round keeps unchecked register rows out of the register

This records how the 3.11 change to `skills/ssot-bootstrap/references/mining.md` §4 was tested, so the claims in `CHANGELOG.md` can be checked. All runs used `deepseek-v4.1-flash` on fd's output area, copied under `/var/tmp`; nothing touched a real repository.

## 1. The problem

A mining round must not admit a register row before a fresh helper has checked it against the code. The 3.10 text says "add its checked rows to the register then, not at the end", but the same paragraph says the writer writes "directly into that area's owner in `SSOT/`, not into a draft for you to merge". The lead can read the second sentence as covering the register rows too.

In a real single-area mining run of the shipped 3.10 text (`r1`), the lead told the writer to put the new rows into `SSOT/README.md`. The run hit its 60-minute cap before the row check returned. It ended with 25 register rows, 11 of them new and never checked. `ssot-check` passed, because it cannot tell whether a row was checked. A second run of the same text (`r2`) drafted the rows in a working file instead and ended with no new rows in the register. The text allowed both readings.

## 2. What was tried

Both candidates replay r1 from its state just before the writer ran, so the same miners, challenge, and admission decisions feed the lead, which writes its own writer brief. The only difference between candidates is the text of §4.

| Candidate | Change to §4 |
|---|---|
| `c311` | The writer drafts each register row "in its own working file, not in the register". |
| `c311b` | `c311` plus "add only its checked rows to the register then, not at the end; an unchecked row stays in the working file". This is what 3.11 ships. |

Replay limit: 40 minutes each, two replays per candidate, one at a time on the same slots. The question for each replay was whether any new row was in the register before the row check had returned.

## 3. Result

| Run | Text | New rows in the register before the first row check returned | Finished |
|---|---|---|---|
| `r1` | 3.10 | 11, written there by the writer | no (60-minute cap) |
| `r2` | 3.10 | 0 | no (60-minute cap) |
| `pw1` | `c311` | 11, merged by the lead at step 513 while the row check was still running | yes, 39 minutes |
| `pw2` | `c311` | 11, written at step 165, before any row check started | yes, 35 minutes |
| `pv1` | `c311b` | 0 | no (40-minute cap) |
| `pv2` | `c311b` | 0 | no (40-minute cap) |

In `pv1` and `pv2` the register stayed at the starting 14 rows through the writer, the first row check, the fixer, and the re-check, and `ssot-check` passed with no errors and no warnings. Both writer briefs asked for the draft rows in `.ssot-work/writer-rows.md`; the `pv1` brief also says the lead adds the register rows after the row check. Both leads' notes say they will insert the rows once the re-check passes, and both runs reached the cap while the re-check was running.

The drafting sentence alone (`c311`) did not hold in either replay: the lead merged the draft into the register early, once while the row check was still running and once before any row check had started. With the added "checked rows only" clause, the rows stayed out in both replays. Two replays per text is a small sample, and the reason a lead merged early was not examined.

## What this does not show

- A finished run of `c311b`. Both replays hit the cap during the re-check, so the register had no new rows when they stopped. That includes rows the first check had passed: under the 3.10 reading all of them would have been in the register, unchecked. Whether a finished run adds the checked rows is not observed for `c311b`; the leads' notes say it will.
- Run-to-run spread. Two replays per candidate, from one starting state. `c311` finished in 35 and 39 minutes and `c311b` did not finish in 40; four runs cannot separate that from noise.
- Other models, other repositories, other areas. fd's output area only, flash only; the leads and the helpers are the same model.
- That the rows are better. This tests where unchecked rows go, not how accurate they are.

## Side observation for 3.10

Two replays of the released 3.10 text (`rp1`, `rp2`) started from r1's state with the rows already written and checked, fixed, and reported. In both, the lead's own fixer brief carried the 3.10 wording ("never drop" a part, put the exception into the row). 3.10's evidence had only scripted prompts, so this is the first time a lead followed the wording unaided. Their claim scores were graded once each and are not comparable with the majority-of-three scores in `tests/trials-3.10.md`, so none are reported here.
