# 3.15: verify the claims closeout adds

3.15 updates the rules for final SSOT reconciliation. They require preserving accurate unaffected prose and rule scope/status, and using a shared check that compares an exact new claim with its code condition and a potentially contradicting input. The shared memory model distinguishes inferred follow-up conditions from approved decisions and permits an honestly undecided removal condition. Checked input conditions also carry into the final response. Closeout's completion criterion includes agreement with checked evidence alongside the structural checker. It does not ship any of this round's unsuccessful early-decision-capture routes.

The observed defect was concrete: in whole-task trials, agents correctly preserved the original non-string parser path but newly described positive non-string inputs as returning their integer. The actual unchanged `parse_limit(0.5)` raises `ValueError`, because `int(0.5)` is zero and the guard rejects it. A structural checker PASS did not establish the truth of that description. Another produced sentence instructed a future agent to remove a migration exception on a condition the user had not approved. Both are record-generation problems, not reasons to patch the generated example documents by hand.

## Scope, method and acceptance

The release candidate starts from 3.14 at `99f3440` and changes closeout plus the shared memory model's writing guidance. Preflight behavior, triggers, agent metadata, acceptance criteria, helper rules, checker, installer, templates, budgets and `ssot_format: 3` are unchanged. The release version marker is a separate mechanical change. The exact trial closeout SHA-256 starts with `0c6919be6fb3`; the local frozen manifest retains the full digest.

N asks negative integer strings to select the migration importer's minimum limit of 1; Z asks zero-parsing strings to return the scheduler's inheritance marker `None`. The committed starting code rejects every converted value below 1. For each matched pair the maker prepares an identical, already implemented source/test diff, leaves the original SSOT to reconcile, and supplies the same explicit user acceptance of the caller-detection loss and its stated reason. This isolates final closeout from the unsuccessful pre-implementation work. It cannot demonstrate that an initial unaccepted request stops, that conversational intent survives interruption, or that real recovery works.

The model is `deepseek-v4.1-flash` with maximum reasoning effort through headless dsh. Matched arms use the same complete asset layout and identical initial code/SSOT/adapter and agreed implementation/test hashes; only the two candidate protocol files differ. Trial subjects use no network or helper. No separate automated model-grading pass is launched for each trial. Maintainer design and independent evidence review use `gpt-6-astra`, xhigh, under the user's separate request. At most two parent sessions run at once. Baseline and the first rejected closeout variant have three-minute caps; the final frozen candidate has a five-minute resource cap. Calls and observed time are reported without treating the cap change as a quality result.

The frozen release bar requires both N/Z candidates to complete and satisfy the agreed function scope, truthful final prose and final report, retained reasons and unaffected protection status, no invented approved retirement condition, stale guidance or repeat approval, and no unrelated writes. It then requires fresh R (bytes-only zero inheritance), H (harmless variable rename, no SSOT rewrite), D (confirm an already implemented zero-rejection rule, no planned label), and S (text casefold after trimming, retaining the post-trim-empty guard). An actual claim/input/outcome trace is also required when a new behavior claim is written. No trace is needed on H when no new claim is written. No wording changes follow those controls. Earlier capture bars remain failed.

## Observed outcomes

| Case | Observed final result | Scope of the evidence |
|---|---|---|
| N: negative integer strings select 1 | Agreed source unchanged, reason/acceptance retained, existing rule stays candidate, no decided removal condition invented. | Final prose/report agree with the code; semantic claim/result correspondence exists. |
| Z: zero strings mean inheritance | Agreed source unchanged; final non-string paragraph uses **positive converted value**; `0.5/-0.5` still raise; inferred revisit is proposed. | Final prose/report agree with the code; semantic claim/result correspondence exists. |
| R: bytes-only zero inheritance | Source unchanged; string/bytearray behavior retained, reason preserved, no decided removal condition invented. Added tests restore the old negative-string assertion and cover byte boundaries. | Five tests plus 45 independent inputs; the failed combined script is excluded as a whole. |
| H: local variable rename | Only the three variable occurrences change; no helper/approval or SSOT rewrite. | Original two tests and 45 independent inputs. |
| D: confirm the current zero rule | Source/tests unchanged; zero rule confirmed and negative protection candidate; no planned label or extra approval. | Correct current state; exact existing row reused, rather than the general separate-row recording instruction. |
| S: casefold after trimming | Source/tests unchanged; whitespace-only text still fails after normalization; non-text failures/messages preserved; old protection stays candidate. | Three tests, 17 independent inputs and actual Unicode/whitespace probes; no importer integration exists here. |

The result gate and the operating procedure are reported separately. Independent review found both core final artifacts truthful with actual condition/input/result correspondence. The transcript combines final literal readback, reasoning about the guard and actual probe outcomes. It does **not** show every full sentence recopied verbatim into a probe script: that strict operational target received only partial adherence. This is not counted as “all frozen requirements passed” or a clean procedural win. Before controls, that deviation was explicitly retained and the result gate was recorded as final truth/scope plus semantic evidence correspondence. D also reused the exact candidate row for the confirmed zero directive. The release ships the clarified writing requirement with these execution limits visible; it does not claim complete protocol obedience or an enforced semantic gate.

R's call 35 printed successful individual claim checks but then stopped in an uncaught old-function exception inside its differential scaffolding. It is not counted as an overall pass. Call 37 replaced that scaffolding with exception capture and completed the 32-input differential; the independent 45-input check is separate evidence. A tool result with status “completed” alone does not establish the shell program succeeded.

The new source-complete baseline N/Z tasks also produced accurate final descriptions. This matched comparison therefore shows candidate conformance, not an error-rate improvement. The earlier whole-task baseline failures establish that the false generalizations occur; those different starting conditions must not be pooled with this pair to claim a causal improvement.

An independent matrix covers 45 inputs per parser case: signed and padded strings, signed zero, invalid strings, integers, fractional values including `0.5` and `-0.5`, booleans, `None`, bytes, bytearrays, decimals, infinity and NaN. S separately checks 17 text/non-text inputs, including whitespace-only nonempty inputs, Unicode names, and unchanged non-text failures. Expected results derive from the committed original function plus only the explicitly accepted type-specific exception or casefold transform; exception types and messages are compared too. Prepared source hashes, actual diffs, SSOT passages and tool receipts are checked separately. Functional checks cannot prove prose accurate, so the prose/source/scope audit is manual and independently reviewed. Model assertions and the structural checker are not semantic verdicts.

SSOT writes are replayed from their original committed Markdown using the existing read-only observer API with no implementation paths selected: these tasks deliberately start with an uncommitted completed implementation. Initial/final implementation hashes and the functional matrix check that separate boundary. Replay must match surviving Markdown; shell calls are inspected separately. This is final-state readback, not an actual crash experiment.

## Cost observations and failed exploration

| Arm / case | Parent calls | Seconds | Read calls | Completed SSOT writes |
|---|---:|---:|---:|---:|
| base-close-N | 33 | 164 | 5 | 4 |
| base-close-Z | 28 | 108 | 9 | 5 |
| wording-close-N | 28 | 124 | 8 | 5 |
| wording-close-Z | 32 | 180 | 8 | 4 |
| wording-control-R | 42 | 216 | 11 | 6 |
| wording-control-H | 14 | 20 | 7 | 0 |
| wording-control-D | 27 | 89 | 8 | 2 |
| wording-control-S | 34 | 114 | 9 | 6 |

The units are parent tool calls and wall seconds, not price or total model usage. Caps differ, scheduling is shared, and arms are not randomized. No runtime or monetary saving is established. Maintainer/release-review model usage is excluded from this table. Evaluation avoided full mining, repeated register scoring and a separate automated model-grading pass for each trial; it reused the frozen baseline and deterministic readback when the candidate changed.

This round also ran the following unsuccessful development branches before isolating the release slice. They do not enter the shipped protocol:

| Branch | Preserved reason for rejection |
|---|---|
| Reused prior early-capture proposal on fresh N/Z | N recorded the actual accepting reply only after implementation; Z newly generalized non-string behavior incorrectly. |
| Decision-source paragraph plus claim reminder | N made no early SSOT capture; Z still produced the fractional-input contradiction. |
| Re-entry description plus boundary check | Neither session re-entered preflight after acceptance; both loaded closeout first. Better outputs did not satisfy the declared routing hypothesis. |
| Writer with separate capture/batch routes | N captured the actual exchange; Z omitted the actual approval question and drafted a full ADR with unbuilt test claims before code. Its OpenAI metadata also lagged its new role. |
| More concrete capture note | N implemented in the initial request without the required acceptance. Z's subsequent completion does not offset that failure. No conditional controls were started. |
| First per-claim trace | Z's trace tested positive integers but its final architecture still said a convertible positive value returns its parsed integer. The broader sentence was not checked; core failed despite trace presence. |
| Carrying checked conditions into the final report | N passed; Z's report improved but its final architecture still generalized positive non-strings incorrectly, and its inferred revisit conditions were unlabelled. No controls started. |
| Scope-preserving closeout follow-up | N passed. Z completed, but both its final architecture and final response still generalized positive inputs as returning a converted integer. Its matrix/checker passes did not correct that prose. No conditional controls started. |
| First closeout-only claim-check | N hit the resource cap incomplete: 36 calls, 188 seconds including termination. Its saved architecture also issued an unapproved removal instruction. Z completed with correct source and accurate converted-value prose; the candidate still failed. |

The final variant replaces the missed generic matrix-to-prose link with an explicit exact-claim/code-condition/counterexample/result comparison in the shared writing owner. It moves proposal labeling to that same model and clarifies the shared workaround rule so an unknown removal condition need not be invented. The final adjustment reads the saved changed wording, explicitly names derived values rather than convertibility, and requires later wording edits to be checked again for that sentence. The integer-conversion illustration is learned development evidence, not an undisclosed holdout. S is a fresh different-domain control without a paired baseline. Closeout dispatches that procedure and carries checked input conditions into the final response. This is a change in the writer that produces the mistaken guidance, not a manual repair of one trial. The no-reason omission from the previous [exploration](exploration-3.15.md) remains a known failure; the original sample and its 1/2 result are not reclassified. Previous exploration is a dated record of what was not released at that time.

The current exploration used 39 parent turns: 38 completed and one incomplete (`claim-close-N`). This count includes the failed variants, the two reused source-complete baselines and the six final candidate cases; it excludes the earlier report's 17 turns. No omitted or incomplete trial is treated as a success. R exposed a fixture-preparation defect: the maker had dropped a prior negative-string assertion. The agent restored it. A future fixture maker now starts from HEAD tests and changes only the accepted case; three new generated N/Z/R suites pass, and R retains its original negative/zero loop. Historical trial copies and their initial hashes remain unchanged. Metrics were recomputed after fixing receipt counting for relative `SSOT/` paths.

Local raw evidence is `/var/tmp/ssot-bench/315-release-hh_28q35/`: `WORDING-PREGISTRATION.md`, `S-PREGISTRATION.md`, `wording-manifest.json`, native `wording-*.jsonl`, `wording-*.ssot-replay.json`, external test outputs and `wording-verification.json`. Earlier manifests and failure logs remain alongside them. Full file digests and initial commit/source/test identities live in those local manifests; the shared model's frozen SHA-256 starts with `796bf8419a09`. Raw evidence is not a portable public dataset. Replay uses [the committed observer](inspect-decision-trials.py) without a separate automated grading pass for each trial.

## Why this belongs in the protocol

1. **General responsibility:** preserving unaffected contracts and separating observed facts from inferred instructions apply to any repository's SSOT. The parser and importer details stay in the trial, not the shipped rule.
2. **Existing owner:** closeout already writes and verifies these records. The change refines that writer and its completion criterion, with the shared writing model owning the detailed check and proposal distinction; it introduces no ledger, lifecycle route, schema or approval owner.
3. **Evidence level:** real headless model runs produce the actual Markdown being judged, paired with code boundary checks, raw receipts and readback. Structural tests validate packaging, not the meaning of the model's output.
4. **Whole-task effect:** the no-rewrite and current-rule controls check nearby non-trigger cases. The checked scope stays new/broader claims rather than a new full-repository review. The current samples do not establish reduced error rate or lower total cost.

## Limits and release verification

No universal reliability, real crash/restart recovery, initial authorization improvement, unknown-reason repair, large real-repository generalization, other trial model, or total cost reduction is demonstrated. Bootstrap, doctor and migration were not behaviorally rerun with the shared writing change; their new guidance has static review, not end-to-end evidence. All failed early-capture variants stay outside the release. This is an instruction change with bounded conformance evidence, not a trusted approval or semantic enforcement barrier.

On the integrated release candidate, `bash tests/test-bundle-shape.sh` passes 48/48, with entrypoints 3,279/3,300 words and runtime protocol 10,804/11,000; no budget is raised. `python3 -W error::ResourceWarning tests/test-ssot-check.py` passes 97/97 after closing an existing fixture's README reader that had emitted a `ResourceWarning`. `bash tests/test-installer-e2e.sh` also passes 100/100, including a real temporary install reporting 3.15. The checker itself is unchanged. Before commit, source-body equality with the frozen runtime and the exact staged diff are checked separately. CI on the published commit supplies cross-platform packaging checks; it cannot establish model behavior.
