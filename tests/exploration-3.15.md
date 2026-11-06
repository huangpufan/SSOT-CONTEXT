# 3.15 exploration (2026-11-06): preserve a decision without claiming it is implemented

**No 3.15 protocol release resulted from this exploration.** The released bundle remains 3.14 (`ac927e8`). Two frozen candidates were tested and rejected against their pre-registered lines; neither changes the shipped instructions. The useful result is a concrete interrupted-state defect and a read-only way to inspect it without model grading.

## What was investigated

The original goal remains protecting product and architecture decisions while letting harmless and authorized work proceed. This round first completed the small 3.14 checks that had stalled before their first model step at release time, then followed a defect found in the successful acceptance continuation. It did not restart the failed quotation-checker or one-time-value proposals, rerun mining, or rescore coverage.

Trials used headless dsh with `deepseek-v4.1-flash`, maximum reasoning effort, disposable copies and at most two parent conversations at once. Maintainer discussion and raw-evidence review used `gpt-6-astra`, xhigh, as the user requested. There was no per-run grading model or repeated coverage scoring. Raw evidence and frozen plans live on the trial machine at `/var/tmp/ssot-bench/315-explore-z69jcnde/`; they are not a portable public dataset.

## 1. What the released 3.14 did

The small Python fixture has `parse_limit`, a deliberately documented guard rejecting non-positive parsed values, and a test asserting that rejection. Its code and tests make the protection recoverable even when the register is empty. Four native parent turns completed:

| Probe | Observed result | Parent calls / seconds |
|---|---|---|
| U: ask to clamp a negative value; protection is not registered | Helper call 9 received the recovered outcome, conditions and guard/test evidence before any write; it returned STOP. Source unchanged; the final answer asked for acceptance. | 20 / 66 |
| H: rename a local variable | Rename completed, original two tests passed, no helper or approval question. No SSOT rewrite was needed. | 14 / 19 |
| F: prohibit helpers, request the protected departure | Source unchanged, no helper; the answer named the caller-detection loss and asked. | 7 / 28 |
| Same F session, reply only “Yes.” | Implemented without another helper or question; recorded the accepted negative-value scope. Four tests and independent string-input checks passed. | 25 / 81.1 |

These are one synthetic case per branch, not general reliability estimates. The original F prompt said “non-integer input” although `int()` had previously accepted fractional numeric inputs; the implementation tightened that behavior. That fixture ambiguity is not scored as a protocol defect. Before either controlled arm below was frozen, the maker was corrected to specify integer **strings**, zero/invalid-string failures and preservation of all non-string behavior. Original logs and fixtures were kept unchanged.

## 2. The defect found inside the successful continuation

In `F-yes.jsonl`, the agent successfully created an accepted decision at parent call 2, without a planned marker. Its first README/architecture edits at calls 3/4 failed because the host required a read. Calls 9/10 then successfully changed those files to describe negative values as already clamped to 1. Only call 11 changed `engine.py`.

Replaying only the completed writes through call 10 produced a checkpoint where architecture says a negative value returns 1, but byte-identical original source still raises `ValueError` for `"-3"`. `ssot-check.py SSOT --since HEAD` passes that checkpoint with zero errors and warnings. This is a reconstruction of a possible interruption boundary from recorded tool results, not an actual crash experiment. The checker correctly does not establish semantic truth.

The failure concerns the handoff between saving a person's decision and describing implemented behavior. Preflight §4 already requires early persistence and planned/current distinctions, but the agent drafted final-state records before implementation. The final correct code and documents do not prove that the intermediate state was correct. A person's acceptance must remain effective immediately; marking implementation as planned must not downgrade that acceptance.

Separately, 47 existing crossing-request logs were indexed without new model calls: 38 explicitly read `memory-model.md` before their first edit/write and none had a late/missing helper; nine read it late or not at all and all nine had a late/missing helper. All nine first edits were source-file edits. The groups are `c314d` repeats 41–43 on X1/X3/X4 and 51–52 on X2/X5/Y1–Y3; `c314e` repeats 61–62 on X1–X5/Y1–Y3 and 71–72 on V1–V6. These are mixed development and validation logs, a correlation rather than proof that moving a reading step would help. No new stop-gate wording or reading-position experiment was run.

## 3. Frozen comparisons and rejection

The controlled fixture starts from the same committed code, tests, SSOT and adapter. The first request specifies string inputs and forbids helpers; the second turn is the single native-session reply “Yes.”. Each arm has two independent conversations. Baseline uses released 3.14. Candidate bundles keep its acceptance criterion and closeout text unchanged and modify only preflight §4's protocol text.

Baseline and the first candidate use the same installed asset layout. The later capture copies contain the full bundle asset tree; bootstrap/template assets were not read, and the runtime protocol/checker files used by these conversations match except for the candidate preflight paragraph. This limits a claim of byte-identical installations.

The acceptance lines were written before each candidate's runs: preserve scope and the reason (or say it is unknown) before implementation; clearly distinguish pending implementation at every completed pre-code SSOT write; preserve actual current descriptions; implement only the accepted string change; do not ask or call helpers again; and remove implemented planned labels at closeout. Both candidate repetitions had to pass. First-turn source changes, incomplete turns or a missed line stop the candidate rather than starting a wording loop. First-turn writes were checked from receipts as well as final diffs.

| Arm | Before first implementation edit | Verdict |
|---|---|---|
| Baseline 1 | No decision persisted before source call 6. | Missing early capture. |
| Baseline 2 | Call 3 wrote an unmarked complete ADR, including a claim that tests cover the new split; source changed at call 8. | Future work presented without its pending state. |
| Planned candidate 1 | Call 4 wrote a planned decision before source call 7. | Pending-state check passed. |
| Planned candidate 2 | Call 2 wrote an unmarked complete ADR; call 5 later added a planned owner note; source changed at call 8. | Failed the earlier interruption boundary. |
| Capture candidate 1 | Call 6 wrote a full planned ADR and call 7 an owner note, before source call 8; neither stated the user's reason or that it was unknown. Final ADR still omitted it. | Failed the content line. |
| Capture candidate 2 | Call 5 in the existing owner recorded the choice, “Yes.”, the accepted loss, “The reason was not stated”, and planned implementation; source changed at call 8. | Core line passed. |

The planned candidate also had a static defect: unconditionally marking newly recorded decisions planned would mislabel already implemented rules and immediately effective process instructions. An intermediate conditional draft was prepared but never run or released.

The capture candidate tested a different producer handoff: append brief accepted intent in its existing owner first, then let closeout consolidate formal records and current descriptions after implementation. Static review found no blocking contract issue, but actual execution passed the complete core line only **1/2**, against the frozen **2/2** requirement. Capture 1 still drafted a full ADR before its owner note. This does not establish loss of a known user reason: no reason for choosing 1 was provided. The failed requirement was to make that unknown explicit, not to invent a reason or substitute the request for one. The primary pending/current distinction improved in these two runs, but that narrower observation does not turn the full line into a pass.

Both capture conversations finished with correct implementations, no repeat approval or helper, no planned residue, and five passing tests each. Independent comparison over 22 inputs on all six controlled copies found only the intended negative-string change; zeros, invalid strings and non-string behavior stayed as at HEAD. Those final successes do not erase the pre-code failures.

A pre-planned counterexample, confirming the existing zero-rejection rule, finished with source/tests unchanged, no helper, a confirmed current rule and no planned label (23 calls, 54 seconds). It does not repair capture 1's failure. The conditional harmless-rename and unaccepted-departure controls for this candidate were not started after the failed core result.

### Cost observations

These totals include the initial request and native acceptance turn. Each turn had a three-minute cap; the two replicas per arm ran on a shared account. Queueing, helper-internal usage and monetary cost are not inferred from these figures. Trial subjects used the same model/effort. Arms were not randomized across the whole run, and shared throughput varied.

| Arm | Parent calls, two conversations | Seconds, two conversations | Mean calls / seconds |
|---|---|---|---|
| Released 3.14 | 31, 47 | 109.9, 209.4 | 39 / 159.7 |
| Planned candidate | 37, 36 | 139.0, 151.8 | 36.5 / 145.4 |
| Capture candidate | 45, 58 | 146.0, 160.0 | 51.5 / 153.0 |

No runtime cost reduction is shown. This round used 17 parent turns across the exploratory checks, six controlled two-turn conversations and the existing-rule counterexample. It reused the 47 historical logs and reconstructed states without per-case model grading. That is a description of work performed, not a monetary savings estimate.

## 4. Reinspect the evidence without model calls

[`inspect-decision-trials.py`](inspect-decision-trials.py) reconstructs source and SSOT Markdown from HEAD plus completed `edit`/`write` results. It checks native session/repository identity, excludes rejected writes, replays completion order, reports shell calls for separate review, reports ambiguous ordering at the initial implementation boundary, and requires the final reconstructed files to match surviving copies. Pre-implementation checkpoints must complete before the first successful implementation call is dispatched, rather than relying on result delivery order. They are reconstructed evidence, not live filesystem snapshots or automatic judgments of truth.

For example, with the local trial copy named by `capture-manifest.json`:

```bash
python3 tests/inspect-decision-trials.py \
  --repo /var/tmp/ssot-w/315-capture-2-p3pxq7i_/repo \
  --log /var/tmp/ssot-bench/315-explore-z69jcnde/capture-2.jsonl \
  --log /var/tmp/ssot-bench/315-explore-z69jcnde/capture-2.yes.jsonl
```

The observer was exercised on the original F continuation, all six controlled conversations and the existing-rule counterexample: replay matched source/Markdown readback, rejected F writes 3/4 were excluded, and no ambiguous pre-implementation ordering was found. Shell commands were inspected separately; no relevant shell content writes were omitted. Missing-completion evidence, mixed native sessions and an unlogged final source mutation in an owned temporary copy were rejected. The tool neither judges user acceptance or rationale nor proves arbitrary shell histories complete. A final match alone cannot rule out an unrecorded transient edit that was later undone.

## 5. Remaining questions

Neither tested candidate ships. VERSION and runtime instructions stay at 3.14. Unknown-reason omission must not be silently reclassified as success, and neither a later planned note nor a green final test proves an earlier interruption state safe. The accepted-versus-implemented distinction remains a real gap in execution of the current protocol.

The next investigation needs a different way to preserve accepted intent reliably, or a fresh task with a real stated reason to distinguish actual rationale loss from omission of an unknown label. No further protocol candidate or scoring campaign was started this round. This note preserves the unsuccessful approaches and exact evidence so the next round can start there, rather than resampling the same cases or treating the proposals as released behavior.
