# Evidence for 3.8 (2026-11-01): mining no longer comes back empty

This records how the 3.8 mining changes were tested, so the claims in `CHANGELOG.md` can be checked. It uses the repositories, answer keys, and measures of `tests/trials-3.7.md`: fd (202 claims) to develop the text, click (169 claims) held out, coverage as the share of claims `SSOT/` states, and precision as the share of added register rows a terra audit judged correct. Mining ran as a Doctor scope over the whole repository, on copies of the same starting SSOT (the one a 3.6 setup produced with terra), and the judges never saw the working files.

Every run here used a clean environment. After the 3.7 release the maintainer found that terra runs had loaded the maintainer's personal codex configuration (`tests/trials-3.7.md` section 6). Codex now runs with an isolated home, and dsh with a settings patch that loads no personal instructions. A run of 3.7 in the clean environment is the baseline for every comparison below, so 3.7's own published numbers are not used.

## 1. A mining run that wrote nothing

Three flash mining runs of fd with the 3.7 text stated 83% and 91% of the claims; the third wrote no rules. The dsh session store shows why. The lead started too many helpers through a workflow tool and was refused by the runtime's limit of eight active helpers, but it recovered within 20 seconds. The loss came from the plan it then followed: it told every writer to draft into `.ssot-work/` and not to touch `SSOT/`, so that it could merge the drafts at the end. When the run reached the trial's 150-minute cap, three areas' drafts existed (47, 32, and 20 KB) and nothing had been merged. Two other runs first wrote to `SSOT/` after 90 and 140 minutes of running time for the same reason.

3.8 makes three changes for this. Each area's writer writes directly into its owner in `SSOT/`. Each area goes through challenge, writing, and the row check as soon as its own miners finish, and its rows join the register then, so a round that stops early keeps the areas it finished. The lead keeps at most eight helpers running and starts the next when one finishes; a workflow counts against the same limit.

The first version of these changes (three runs, three at a time like the 3.7 runs) put every area's outcomes into `SSOT/` but still registered rows in only one of three runs. Two causes showed in the logs: leads still registered all rows at the end, and one lead cut the register from 61 rows to 48 to keep the README under its 8,000-character target, which the checker had never applied to register rows. Memory model §4 now says the target does not count those rows.

With that text, flash runs one at a time (the owner's decision, since users run one mining at a time) all wrote and registered rules:

| Run | Version | Claims stated | New rows judged | Precision | Ended |
|---|---|---|---|---|---|
| 1 | 3.7 | 83% | 77 | 53/77 | at the cap |
| 2 | 3.7 | 91% | 68 | 46/68 | at the cap |
| 3 | 3.7 | 0% | 0 | | at the cap |
| 4 | 3.8 before the checker change | 92% | 84 | 59/84 | on its own, 105 min |
| 5 | 3.8 before the checker change | 96% | 92 | 54/92 | at the cap, during the row check |
| 6 | 3.8 before the checker change | 95% | 56 | 41/56 | on its own, 116 min |
| 7 | 3.8 | 91% | 54 | 34/54 | on its own, 95 min |

The 3.7 runs ran three at a time and the 3.8 runs one at a time, so this table does not separate the text from the running conditions. Run 6 met the helper limit nine times and recovered each time by waiting or by stopping a helper that had already written its file; no task was narrowed and no area dropped. Run 5 hit the cap with its rows already registered.

## 2. Where a flash run's time goes

All six flash runs of the 3.7 round hit the 150-minute cap. The session stores show that wall time is the number of successful model steps divided by the account's throughput. A mining run of fd needs 2,100 to 3,300 steps. The account completes 18 to 30 steps per minute in total, whether one run is active or three, and rate-limit retries outnumber successful steps (3,256 retries against 2,659 steps in run 6). So one run takes 95 to 157 minutes, and three concurrent runs share the same throughput. Steps are spread over every role (in run 6: miners 770, writers 617, challengers 411, row checkers 368, lead 320), so no phase can be dropped without losing coverage or precision.

What 3.8 saves is the work that was thrown away: the end-of-round merge, and refused helper starts. What it cannot save is the rate limit, which belongs to the account, not the protocol. The 150-minute cap is the trial's safety stop, not a property of the procedure.

## 3. A checker warning that worked as a cap

`ssot-check.py` warned when the register passed 60 rows ("N invariants are read before every task"). Run 6's lead wrote about 127 rows, then, to stay under the warning, had a helper cut the register to 59, moving the rest into the owners' prose: 191 claims were stated, but only 144 through the register. Terra leads met the same warning after each checker run (on fd, 61 to 90 rows). Mining has no target count, and a rule that is only described is not kept the way a registered one is, so 3.8 removes the warning; a checker test now asserts that 150 rows draw no warning.

Run 7, the one flash run with the final text, still merged related rows by itself because the register "is read every task", but nothing was lost to it: the register states 181 of the 184 claims the run stated, against 144 of 191 in run 6.

## 4. Terra, fd

One mining round per copy with terra, clean environment, four runs per version:

| Version | Claims stated | Mean | Precision of added rows | Run length |
|---|---|---|---|---|
| 3.7 | 69%, 26%, 56%, 55% | 52% | 171/181 = 94% | 4 to 8 min |
| 3.8 before the checker change | 60%, 64%, 64%, 48% | 59% | 163/171 = 95% | 5 to 8 min |

Two intermediate drafts were dropped on this evidence. One told the lead that the round ends only when every checklist item is marked; it stated 40% and 45%, lower than either version, and added only 30 and 34 rows. Short rows of at most about 25 words, tried in three flash runs to raise flash precision, were judged 64% correct against 68% for 3.7 and stated 4 points fewer claims.

## 5. Held-out repository: click

The maintainer did not read click's answer key while changing the text, and the final text was tried on click only once it was fixed. One mining round per copy with terra from the same starting click SSOT, clean environment, four runs per version, run in interleaved groups of four:

| Version | Claims stated | Mean | Rows added | Precision | Run length |
|---|---|---|---|---|---|
| 3.7 | 44%, 40%, 29%, 56% | 42% | 64, 83, 22, 135 | 282/304 = 93% | 4 to 12 min |
| 3.8 | 59%, 41%, 57%, 62% | 55% | 105, 75, 141, 125 | 412/448 = 92% | 8 to 13 min |

3.8 states more in all four pairings, and its lowest run is close to 3.7's mean; with four runs each, a one-sided rank test gives p of about 0.06. 3.7's earlier click run (44%, with the personal configuration loaded) matches its clean mean.

## What this does not show

- Coverage near complete. Every terra mining round in this trial, in both versions, stopped after 4 to 13 minutes and called itself unfinished, and coverage tracks how long the lead keeps going: on fd, runs that added 14 to 17 rows stated 26% to 28%, runs that added 81 stated 72%.
- Precision near complete with flash. Its runs state 91% to 96% of fd's claims, but only 59% to 73% of its added rows are judged correct; most of the rest are too broad, missing one override, empty input, platform, or early exit. The flash row checker catches many (in run 6 one area's checker flagged 13 of 15 rows, and all passed after two rounds of fixes) and passes others the terra judge rejects.
- That 3.8 beats 3.7 on fd with terra: 59% against 52% is within the spread of one version's runs.
- Full setups with the 3.8 text, flash on click, large repositories, and whether more rows change what agents do.
- That the answer keys are complete: they are terra's selection of each area's most important rules.
