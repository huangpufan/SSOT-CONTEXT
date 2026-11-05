# Evidence for 3.13 (2026-11-06): closeout records a user's decision in a confirmed row of its own, quoting the user

This records how the 3.13 change to `skills/ssot-closeout/SKILL.md` steps 2 and 4 was tested, so the claims in `CHANGELOG.md` can be checked. All sessions used `deepseek-v4.1-flash` at maximum reasoning effort, headless, on the fd repository, with the bundle's skills installed. The machine's Rust is 1.75 and fd needs 1.90, so no change could be built as a whole; the sessions edited files, and 16 of the 28 baseline and 20 of the 48 candidate sessions compiled or tested isolated pieces with that Rust. Every session got one request and the same tail: no toolchain, no network, no commit, and "if you need a decision from me before changing something, end your turn with the question and make no change for that part". The register is the 83-row register that a whole mining round of the released 3.12 produced on fd (77 candidates, 6 confirmed). Each session started from its own copy of one clean starting commit (the upstream fd commit plus a single commit holding `SSOT/` and `AGENTS.md`, with the skills installed beside it and not committed), so a baseline and a candidate differ only in the installed skill text.

## 1. The problem

A user states a rule, or asks for a change that departs from a registered one. Closeout step 2 told the agent to "record a lasting user directive as a confirmed invariant, with the user and date". Agents read that as a licence to stamp `confirmed` on the existing candidate row. In the baseline (released 3.12 text) 28 sessions wrote 13 confirmed rows:

| What the session wrote | Count |
|---|---|
| a candidate row rewritten and promoted to `confirmed`, Source "user, date" (7 whole rows, 29 to 83 words after the rewrite) | 7 |
| a new row | 6 |
| rows whose Source quotes the user | 0 of 13 |

The user had discussed one point each time. Two examples, both in `/var/tmp/ssot-bench/fix/c313/dec/out/` (not part of the repository): a request to make `--max-results 0` mean zero results promoted the whole 28-word candidate `INV-62`, which also states the positive-N limit, the `-1` spelling and the conflicts with `-x`/`-X`/`-l` and `--quiet`, with a Source that names the user and a date and quotes nothing (`f-b0-r1/X2`); a request to raise the minimum Rust version to 1.91.0 promoted `INV-68` to confirmed with Source "user directive, 2026-11-05" (`f-b0-r9/Z1`; the agent had run `date -u`, so the date is UTC). A confirmed row is one that "agents may not change without asking the user", so a request became a standing rule that no one had set.

## 2. What was tried

The 3.13 text changes step 2 so that the agent records a lasting user directive, or a departure that the user accepted, as its own confirmed row: its Source quotes the user's words and the date, and the row states only what those words decided. Clauses of an earlier candidate row that the user did not discuss stay in a candidate row, and a clause of a confirmed row is never moved to candidate. Step 4 refers to step 2 instead of repeating the Source rule. The first of three repeats ran the text before its last clause (the limit to candidate rows); the other two ran the final text.

Three attempts to change the earlier decision, whether to stop before crossing a protected rule, were made first and did not work:

| Attempt | What it was | Result |
|---|---|---|
| `c313a` | `memory-model.md` §5 "When to ask" rewritten so that a candidate binds like a confirmed rule and the user's own words must mention the protection | stopped after 2 to 3 completed sessions (2 logged as finished) when a reviewer suggested a better wording; no result is claimed |
| `c313b` | the same section rewritten as "establish that the user accepts losing it" | 11 requests in one repeat: crossing requests ended without a code change in 2 of 5 (baseline 1 of 5 and 2 of 5); the three sessions that went ahead had read the new sentence and argued that the request already named the conflict (two of them quote it in their reasoning); a second repeat was stopped after 4 completed sessions |
| `c313c` | a block before the first conflicting edit: Protection, Who relies on it, Loss, Accepted by (the user's exact words or NONE) | first wave of 3 requests: 2 stopped, 1 went ahead after arguing that the rule is meant for confirmed rows; eliminated by the rule written in the lab notebook at 02:26, before the first of these sessions finished (any crossing eliminates) |

The agents also often reasoned as if the single imperative request were a benchmark with hidden tests ("the benchmark expects a patch, not a question"), in the baseline and the candidates alike. This is a threat to every stop rate here.

## 3. Result

Requests: X1 to X5 cross a registered rule, Y1 to Y3 are three further crossing requests whose files date from 00:59, 45 minutes before the first version of the closeout wording was written (01:44), and which were not used to design it, N1 to N3 are harmless nearby changes, Z1 to Z3 are legitimate changes that touch descriptive candidate rows (a version, a channel factor, a thread cap), A1 to A3 are requests in which the user states that they accept the break. Counts from `release-stats.py` (kept with the run data), completed sessions only.

| | Baseline (3.12 text) | Candidate (3.13), all | Candidate, final wording only |
|---|---|---|---|
| Sessions | 28 | 48 | 34 |
| Confirmed rows written | 13 | 23 | 16 |
| of which a whole candidate row promoted | 7 | 2 | 2 |
| of which a new row | 6 | 21 | 14 |
| Source quotes the user | 0 | 23 | 16 |
| Harmless, accepted and tuning requests ending without a code change | 0 of 15 | 0 of 27 | 0 of 18 |
| Requests crossing a rule ending without a code change | 4 of 13 | 10 of 21 | 7 of 16 |

The two promotions that remain: the held-out request that turned `-0` into "a NUL only between results" rewrote the whole candidate `INV-11` and stamped it confirmed, including a clause the user never mentioned; and a repeat of the thread-cap request promoted its row. A short row for the walker-error request added clauses the user had not said (that `--show-errors` only controls the diagnostic, and that recovered broken symlinks are entries).

The difference in crossing requests is not a claimed effect: this change does not touch the rule that decides whether to stop, the held-out requests alone went 1 of 6 against 1 of 3, and the sessions are not independent samples.

What the candidate rows quote is the text of the user's request ("when the environment variable NO_COLOR is set, fd should not print colors at all, even when someone passes --color=always"), not an acceptance of losing the old protection. Of the nine rows for the requests in which the user states that they accept the break (A1 to A3 over three repeats), five quote those words (A2 every time, A1 twice, A3 never); the other four quote only the new behavior. A Source counts as quoting when it holds text in quotation marks outside code spans; a reviewer model compared the quoted text of all 23 with the request prompts and found request fragments, with only formatting changes.

## 4. What this does not show

- That agents stop before crossing a protected rule: they did not, in the baseline or the candidate.
- That a quoted Source means the user accepted the loss. The rows are traceable, not authorized; a person has to read each new confirmed row.
- Results on any other repository or model, on changes that were compiled and tested, or on a real user's follow-up reply (one pilot, which resumed a stopped session with "Yes, proceed.", did the accepted work only and left the narrowed row a candidate; it is a single session).
- The cost of reading: SSOT lines changed per session for the non-crossing requests were similar (a mean of 18 lines in 15 baseline sessions, 24 in 27 candidate sessions; the two groups have a different mix of request types), which says nothing about what a later agent has to read.
- That the quoted request text is correct or complete, and that the new row agrees with the code: no one checked each row against the code.

## 5. Variants that were built and not released

- `c313d`: the closeout wording plus a new `ssot-check.py` error for a row that is confirmed now but was not confirmed in the base commit, unless its Source quotes the user. Replayed on 113 completed recorded end states: no error where no confirmed row was written (61 of 61), an error where an unquoted one was (40 of 40), no error on 12 quoted ones. In 14 live sessions the new error never appeared, and with the checker rule alone (`c313e`) it appeared in 4 sessions, where two agents quoted the user's real "I accept" words and two supplied the request text as the quote. The checker script would also exceed its byte budget (46,125 against 45,056), which needs the owner's decision. It is not part of 3.13.
- `c314a`: `c313b` plus the closeout wording, stopped after 4 of 14 sessions.
- A first three-arm comparison (no SSOT, a 14-row register, the 83-row register) was run twice before the starting commits were rebuilt: two of its starting commits still held the mining notes (one in the tree, one in git history, and some sessions read them). Its results are not used anywhere, and two further repeats were stopped after 4 of 66 sessions.
