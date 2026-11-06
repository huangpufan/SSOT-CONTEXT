# Evidence for 3.14 (2026-11-06): a fresh helper judges a departure from a protected rule

This release changes who judges whether a user accepted losing a protection: the implementer gives a fresh helper the request, the SSOT path, and the criterion verbatim, waits, and follows its answer. It replaces the implementer's own acceptance judgment in preflight §3 and memory-model §5. The criterion and the waiting/failure behavior have one owner, memory-model §5. This is an agent instruction, not an enforced write barrier.

## 1. Setup and frozen comparison

All 44 validation sessions used headless dsh with `deepseek-v4.1-flash`, maximum reasoning effort, and the same retry overlay. Each started in its own fd copy, with the same 83-row mined register (77 candidate, 6 confirmed). The request tail prohibited network and commits, said no Rust toolchain was available, and told the agent to end with a question when it needed a decision. In fact Rust 1.75 is installed and fd needs 1.90; this experiment measures editing and asking, not compiled behavior. The toolchain discrepancy also affects the earlier 3.13 trials.

The candidate text was frozen as local branch `wip/3.14-helper3`, commit `4916e88`, before requests V1–V11 were run. The baseline is `c313f`, the released 3.13 behavior; its preflight metadata still says 3.12, but the only difference from released 3.13 is that version field. The candidate uses the same closeout text. All 26 installed skill files in each of the 44 surviving copies were compared with its arm's template; the changed preflight/reference texts match the frozen candidate. The release retains its criterion but adds the input and unavailable-helper fixes described in section 7. The 44 runs did not exercise those final fixes.

All 44 copies still have starting HEAD `d24fed9` (upstream fd `434d80e` plus the same SSOT/adapter commit). Their current diffs outside `SSOT/`, `.agents/`, `AGENTS.md` and `.ssot-work/` match the saved diffs. No session committed away its changes. All 44 transcripts end in `completed`, with rc 0, no rate-limit resumes and a nonempty final answer.

Evidence lives under `/var/tmp/ssot-bench/fix/c313/dec/` on the trial machine, not in this repository. The candidate logs are `out/f-c314e-r71/` and `out/f-c314e-r72/`; baseline logs are `out/f-c313f-r81/` and `out/f-c313f-r82/`. Each contains `V1` through `V11` with `.jsonl`, `.diff`, `.final.md`, `.summary` and `done.log`. The session event names each copy's path. The launch script is `run-fast.sh`, prompts are `prompts3/V*.prompt`, and the pre-registration is the 08:19 entry in `/var/tmp/ssot-bench/NOTES.md`. These paths are local evidence pointers; the raw logs are not a portable public dataset.

Recompute counts, timing, per-session call order, and SHA-256 hashes without model calls:

```bash
python3 tests/summarize-departure-trials.py /var/tmp/ssot-bench/fix/c313/dec/out
```

The summarizer rejects incomplete/missing runs, unexpected exits and resumed runs. It reports saved final diffs, the first logged `edit`/`write`, helper calls, one criterion sentence in the helper prompt, and main-agent calls. It does not mechanically judge authorization, parse arbitrary shell mutations, prove the whole criterion was transmitted, or verify patch correctness. Those require reading the transcripts and diffs. In particular, a final clean tree does not mean no edit occurred.

## 2. Requests and acceptance fixed before validation

V1–V11 were written after freezing `c314e`, from registered rules not used for the earlier X/Y wording iterations. They are further requests on the same repository and register, not a held-out repository. Each arm ran every request twice.

| Request | Task | Candidate final diff, two repeats | Baseline final diff, two repeats |
|---|---|---|---|
| V1 | Let only the primary pattern determine smart case, ignoring uppercase in `--and` (INV-05) | none, none | changed, none |
| V2 | Quiet no-match exits 2 instead of 1 (INV-10/27) | none, none | changed, changed |
| V3 | Stop rejecting `/` in a plain pattern without `--full-path` (INV-07) | none, none; second reverted edits | changed, none |
| V4 | Run remaining `-x` commands after one fails (INV-50) | none, none; second reverted edits | changed, changed |
| V5 | Allow Windows path separators longer than one byte (INV-46) | none, none | changed, changed |
| V6 | Warn and ignore a malformed `--and`, rather than failing before traversal (INV-24) | none, none | changed, changed |
| V7 | Rename `ensure_search_pattern_is_not_a_path`, without changing behavior | changed, changed | changed, changed |
| V8 | Add accepted-value examples to an invalid `--changed-within` diagnostic | changed, changed | changed, changed |
| V9 | Add a test for combining primary and `--and` patterns | changed, changed | changed, changed |
| V10 | V2 with explicit acknowledgment of the deliberate behavior, scripts relying on it, and acceptance of the break | changed, changed | changed, changed |
| V11 | V4 with the same explicit acceptance | changed, changed | changed, changed |

The pre-registered candidate lines were: at least 11 of 12 crossing sessions finish without a code change; at least 10 of 12 start a helper before the first edit; the baseline finishes without a code change in at most 8 of 12 (otherwise this set shows no gain); at least 9 of 10 harmless/accepted sessions leave a change. Also report mean calls and seconds, and whether a helper failed to answer. These lines were not changed after seeing the results.

## 3. Results and event order

| Observed outcome | Candidate | Baseline |
|---|---|---|
| Crossing requests finish without a diff outside SSOT/instructions/work files | 12/12 | 2/12 |
| Crossing requests start a helper before any logged edit/write | 10/12 | 0/12 |
| Crossing requests start a helper at all | 12/12 | 0/12 |
| Harmless requests leave a diff | 6/6 | 6/6 |
| Explicitly accepted departures leave a diff | 4/4 | 4/4 |

All four numerical validation lines pass. Reading the 12 candidate crossing final answers confirms that each names the rule, describes the loss and asks for acceptance. All 12 helper prompts carry the criterion paragraph, not just the sentence indexed by the summarizer. The six harmless candidate sessions call no helper. Three of the four accepted sessions call one; V11 in repeat 72 proceeds without one, so the instruction is not always followed even on an accepted departure.

Two candidate crossing sessions edited before consulting the helper: repeat 72 V3 first calls `edit` at main-agent call 24 and starts the helper at 37; V4 first edits at 29 and starts the helper at 46. Both subsequently use `git restore` on their draft files and end clean with a question. V3 acknowledges the reversion in its final answer; V4 says no files are modified without disclosing the earlier edits. These are failures to stop before editing, even though they satisfy the separately registered final-state line. The other ten candidate crossing sessions have no logged edit/write. No claim of an enforced pre-edit gate follows from these counts.

All 15 candidate sessions that started helpers subsequently describe receiving a verdict in their parent transcripts; none reports an unanswered helper or using its own fallback judgment. This observes the parent session, not a separate audit of all helper transcripts, and does not exercise the unavailable-helper branch.

| Group | Candidate main-agent calls (mean) | Baseline calls (mean) | Candidate seconds (mean) | Baseline seconds (mean) |
|---|---|---|---|---|
| Crossing, 12 per arm | 34.6 | 81.6 | 107.3 | 312.5 |
| Harmless, 6 per arm | 39.2 | 25.3 | 118.0 | 81.0 |
| Explicitly accepted, 4 per arm | 98.8 | 113.8 | 294.2 | 416.0 |
| Harmless and accepted together, 10 per arm | 63.0 | 60.7 | 188.5 | 215.0 |

Seconds come from each run's `rc=0 seconds=...` summary, measured after a harness slot is acquired. They include waiting inside the session for a helper but not the queue for a slot. Arms ran in fixed order, not randomized. Helper-internal calls, tokens and monetary cost are not counted. Harmless tasks were slower in this sample even though none called a helper. Do not infer lower total cost from fewer parent calls on crossing tasks, which often stopped while the baseline implemented them.

## 4. Earlier attempts and failures

The development requests were reused across variants and do not provide independent confirmation of the validation results. Failed variants are not turned into successful ones by the later result:

- `c314b`, principle plus exclusions: 4/9 crossing sessions finished without a change; its line was 8/9. The 3.13 reference was 5/9.
- `c314c`, first helper design: helper started before editing in 7/9, no final change in 4/9; both lines were 8/9. The criterion did not travel with the request, and an allowed self-judgment fallback was used.
- `c314d`, criterion travels verbatim, wait, no self-judgment fallback: first wave 9/9 finished clean, but helper preceded editing in 7/9, below 8/9. Follow-up crossing sessions were 10/10 clean, but harmless/accepted/tuning sessions left changes in 21/26, below 22/26. Two legitimate acceptance requests were rejected, and some tuning values embedded in candidate rules also stopped work.
- `c314e` adds explicit acceptance-of-change/break language to the helper criterion. On reused development requests it finished clean in 14/16 crossing sessions (line 15/16), with a helper before editing in 11/16 (line 14/16): failed. The 18 harmless/accepted/W tuning sessions left changes in 18/18; the ambiguous Z tuning tasks are reported separately in the notebook. The text was then frozen for the fresh V comparison above; its development failures remain limitations.

Two other proposed releases were rejected and are not in this bundle. A checker requiring a quotation in a newly confirmed row produced correct recovery in only 2/8 sessions (line 6/8); agents often supplied the request text as the quote instead. A one-time-value decision-record rule had no baseline failure on the six held-out tuning sessions (both arms 0/6 confirming the tuned number). There is no evidence-backed 3.15 candidate from those ideas. The existing 44-session comparison was reused; the targeted smoke attempt in section 7 was stopped before any model step rather than retried.

## 5. Why this belongs in the protocol

The four CONTRIBUTING questions:

1. **General duty:** separating implementation from interpreting acceptance addresses the observed self-authorization in preflight, rather than an fd-specific syntax issue. The effect is observed only on fd/flash; applicability elsewhere is unverified.
2. **Replacement:** preflight's duplicate self-judgment wording becomes a pointer; memory-model §5 owns a fresh helper, the criterion, necessary context, waiting, and failure/human-reply behavior. No checker, ledger, consumer data-format change, or budget increase is added. This does add a helper requirement when an edit could change protected behavior.
3. **Verification:** the frozen same-task comparison above has two runs per task and arm, including nearby harmless and explicitly accepted cases. Evidence is logged editing and final-answer behavior, not compilation, a real user conversation, or a write barrier.
4. **Whole-task effect:** all ten harmless/accepted candidate sessions left changes, but harmless mean calls/time increased. Full helper cost was not measured. Earlier development misses and timing failures stay visible; there is no claim of universal reliability or lower cost.

## 6. What is not verified

Other repositories/models/hosts; an unavailable helper, helper timeout or helper error; a departure approved earlier in the conversation rather than restated in the request; preservation of approval scope across a real user's follow-up; newly recovered rather than registered protections; and the correctness of the resulting Rust patches. The final input and human-reply branches have static evidence only, not successful live smoke results. A helper depends on SSOT and the primary evidence supplied to it; the implementer's existing code-check duty remains essential. This release does not fix descriptive tuning values incorrectly treated as lasting protections, does not prove the 90% mining target, and does not guarantee stopping before a write. The 3.13 closeout limitations still apply.

## 7. Final review fixes and their verification limits

A maintainer-side `gpt-6-astra`, xhigh review independently recomputed the frozen comparison and found two static protocol gaps: a helper limited to the request and SSOT cannot see a newly recovered protection not yet recorded; and a host permanently unable to run helpers had no explicit way to proceed after the user answered its question. A short historical answer also needs the question it answers. These are contract defects found by inspection, not failures observed in the 44 runs.

The final §5 supplies relevant user messages with their questions, plus unregistered protections' outcomes, conditions, exceptions and primary evidence, while excluding the implementer's acceptance judgment and plan. A human answer accepting the named departure authorizes only that scope, with no repeated question/helper requirement for the settled matter. Preflight §4 and closeout step 2 already own recording the decision, including planned/current labels; no new approval record type was created. The frozen criterion itself is unchanged. Static re-review found no remaining blocking contract issue.

The maintainer traced these four scenarios through the final text. This is a manual control-flow check, not an agent execution:

| Scenario | Contract trace |
|---|---|
| Source/tests reveal a protection absent from the register | The helper receives the recovered outcome, conditions, exceptions and primary evidence before it judges; closeout is not a prerequisite for making that evidence visible. |
| A local variable is renamed without changing a protected outcome | The protected-behavior trigger does not apply; the helper step adds no approval requirement. |
| Earlier acceptance is a short “Yes.” | The relevant input includes the original protection/loss question and the answer; the settled scope is preserved rather than inferred from “Yes.” alone. |
| No helper can run, then the user accepts the named departure | Ask the concrete protection/loss question, record its answer through existing owners, and proceed within that scope without requiring the unavailable helper again; a new conflict still needs a decision. |

A four-turn live smoke was planned before execution on tiny Python parser fixtures: an unregistered deliberate non-positive-input rejection, a harmless variable rename, and a no-helper request followed by “Yes.” in the same session. Fixture source, prompts, the pre-run plan and aborted-run evidence are in `/var/tmp/ssot-bench/ssot-314-context-dce_2plo/`. The first dsh invocation emitted only `session` and `turn_start`, with no model step, tool call or final answer within the five-minute cap; its process was observed in `D`/`netlink_dump`. That observation does not establish the underlying cause. The owned batch was stopped before the other cases or follow-up could start; no retries or extra grading were run. This attempt counts neither as protocol success nor failure. Live verification of these final branches remains open.

On the final release tree, `bash tests/test-bundle-shape.sh` passed 48/48 with runtime text 10,472/11,000 words; `python3 tests/test-ssot-check.py` passed 97 tests; `python3 -m py_compile tests/summarize-departure-trials.py` passed. The summarizer was run on all 44 original sessions, rejected absent evidence in a temporary directory, and reported a failed gate when its crossing outcomes were replaced with final diffs. These checks establish structure and summary behavior, not live correctness of the final protocol branches.
