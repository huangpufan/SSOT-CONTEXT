# Evidence for 3.9 (2026-11-03): a changed confirmed rule is reported and put back

This records how the 3.9 checker change was tested, so the claims in `CHANGELOG.md` can be checked. A confirmed invariant is a rule a person set; memory model §5 says an agent never changes its meaning, scope, or status. 3.8 had no check for that, and mining runs broke it.

## 1. The problem

Mining runs with `deepseek-v4.1-flash` on fd start from an SSOT whose register holds four confirmed process rules taken from fd's `CONTRIBUTING.md` and `SECURITY.md`. Three of the four 3.8 runs rewrote three of them while tidying the register, for example adding "documentation typos are exempt" to the changelog rule and dropping "take responsibility for contribution rights" from the AI-contribution rule. The leads ran the checker 15 to 24 times after those edits, and it passed every time. The precision grading looked only at candidate rows, so the trials never counted it either.

## 2. The mechanical check

The checker now compares each confirmed row of the base commit with the working tree. On the 14 existing flash mining copies of fd it reports exactly the rows a separate grading script finds changed: three rows in each of the three 3.8 runs above, none in the runs that only moved a link. Unit tests cover a changed rule, kind, or status, a removed row, a moved link, a reworded source, a same-day dated approval, and a v2 base README.

## 3. What a lead does with the error

A whole mining run takes about two and a half hours with flash, so this was tested by replaying only the end of a round. Each replay copies the saved end state of a real mining run (its register, owner files, and working files, with the confirmed rows exactly as that run left them), installs the skills under test, and asks a fresh flash lead to finish the round: run the checker, settle what it reports, and report, without starting helpers. Each replay took three to five minutes. A script graded the final register against the base commit.

| Start state | Checker | Expected | Result |
|---|---|---|---|
| Run that rewrote three confirmed rules | 3.9 | the three restored word for word, no date added | restored, twice in two replays |
| Another run that rewrote three | 3.9 | the same | restored |
| Run that changed no confirmed rule | 3.9 | nothing reported, nothing changed | as expected |
| Same, and the request says the user decided today to exempt typo fixes from the changelog rule | 3.9 | that rule changes and its Source names the user and the date; nothing else changes | as expected |
| First start state again | 3.8 | (control) | none restored; the report said the confirmed rows were unchanged |

The control shows that the restoring comes from the error: with the old checker, the same lead from the same state did not notice the rewritten rules.

## What this does not show

- A whole mining run with the 3.9 checker. The replays start where a round ends; a lead in a full round might weigh the error differently after hours of work.
- Closeout's `--since` path, Doctor catch-ups, and models other than flash.
- That no lead forges an approval. The approval path is a date in the Source column, and an agent can write one. None of the five replays did, which is too few to rule it out; a dated change is listed for the user to see rather than passing silently.
