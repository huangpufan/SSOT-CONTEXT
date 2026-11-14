# Cold handoff benchmark

A writer receives a lasting decision and a scoped correction. A new consumer receives only the maintained Markdown and must implement the current policy. Its fresh session has neither the original conversation nor SSOT skills. This tests whether the recorded knowledge works for someone who was not present.

`reporting` produces a Python policy function for interactive and unattended reports. `editorial` uses a named format-5 entry and produces publishing configuration for narration and quotation. `museum` is an independently authored format-5 confirmation about gallery labels and inventory records; it varies domain and authorship while retaining the two-mode JSON task shape. All preserve an independent boundary and an arbitrary exact required field (seeded for reporting/editorial, independently fixed for museum); the correction changes only one mode. Neither writer may implement the consumer's deliverable or retain the explicitly excluded diagnostic token. Unrelated binary/text work remains untouched. Markdown wording and layout are not prescribed; the existing owner and usable entry must survive.

## Open judgment in prose

The opt-in `judgment` case asks a fresh theatre collaborator to evaluate a concrete proposal and produce usable alternatives after two writer turns record an accepted direction and a limited correction. Its public synthetic material preserves reasons, unselected examples and permission to propose improvements; it copies no private creative work. The consumer task does not disclose the current corrected goal or the particular reason that should guide the judgment. This case is development evidence, not an untouched confirmation.

Prepare with `--cases judgment --confirmation none --capture-goal explicit`, an authorized `--model`, a baseline and a new output root. The default prepared cases remain reporting, editorial and museum, including the existing automatic-capture preparation path. Run individual arms with the existing `--case judgment --arm ARM` interface.

Mechanical observation checks readable artifacts, exact write scope, owner retention, protected paths and native execution. It never sets `consumer_policy_matches` for prose. A readable but useless or mistaken document reaches only `semantic_pending`; no content-length, keyword or field-presence rule establishes understanding. Review requires the original three obligations plus `usable_deliverable`, `reasoned_judgment`, `source_and_scope_application` and `expected_control_behavior`. Read the frozen fixture's rubric, actual maintained text, writer turns and consumer output, and explain each decision with artifact evidence. One failed obligation rejects the attempt; subjective appeal or human preference remains separate.

For ceiling, review whether complete maintained knowledge supports a concrete, correctly scoped deliverable. Floor lacks an adopted choice: it must expose that gap and can still offer conditional useful work; guessing a current choice is not valid calibration. Stale retains the initial choice: its observed use must differ from current correctness for the intended reason, not an unrelated failure. These controls stay `calibration_pending` until the additional review establishes the expected behavior. Calibrate actual good, bad and legitimately different prose before interpreting comparisons; unit tests of the review interface do not establish semantic discrimination. The same immutable evidence/review rules apply to these additional obligations.

For floor and stale, `source_and_scope_application` evaluates the knowledge that particular consumer actually received. `expected_control_behavior` then checks whether the missing or old choice has the intended observable effect compared with the current contract. Faithfully using a stale accepted goal can pass negative-control calibration while failing current-task correctness; inventing the current goal, an unrelated error or a false acceptance claim cannot. Do not require a negative control to implement the current goal and do not label its intended stale response an ordinary quality failure. In all arms, `usable_deliverable` concerns work feasible under the supplied knowledge, including explicitly conditional useful progress when a choice is missing.

For multi-artifact review, check each judgment against the actual path and a short passage from that artifact; matching a verdict to the wrong file is a review failure, not a product result.

Other opt-in prose cases use the same interface:

- `judgment-sources` retains explicitly scoped research originals and tests applying known source limits, mechanism-based rejection and a same-name exception to useful guidance. It does not establish discovery of a hidden defect or the independent contribution of the second correction. Cost comparisons are disabled because stale knowledge can recover from original evidence.
- `judgment-partial-unlock` records a freeze followed by limited release in two installed writer turns; its fresh consumer must actually edit the released roster and preserve the poster. The `judgment-partial-unlock-open` adjacent variant explicitly releases both, requiring both edits. Floor/stale allow only the action note; their known unauthorized roster edits are mechanically rejected. Open is a path check with cost comparisons disabled.
- `confirmation-community-repair` is independently authored and was frozen before development outputs. It changes the task to an executable-by-people operations proposal. Its mechanical adapter retains the original task/rubric and explicitly transfers its operations owner; only baseline was selected, with no cost comparison. Independent authorship is not a model-unseen generalization guarantee.

Select these with `--cases CASE --case CASE --confirmation none` as appropriate to preparation/execution; use `--confirmation confirmation-community-repair` when preparing that confirmation. Each new experiment uses a new root, explicit authorized model and the same existing freeze/receipt/review rules. Live native execution remains Linux-only. Preparation canonicalizes both temporary output paths and allowed root aliases; offline preparation and tests do not make the Linux sandbox portable.

| Arm | Writer | Consumer input |
| --- | --- | --- |
| `plain` | The same SSOT-shaped factual entry and ordinary project rules; no bundle, catalog or workflow block | Writer's maintained Markdown |
| `baseline` / `candidate` | Same initial facts; official project installation and actual SSOT wiring | Writer's maintained Markdown |
| `ceiling` | No writer call | Hand-authored complete current policy |
| `floor` | No writer call | Initial owner with choices still unsettled |
| `stale` | No writer call | Initial accepted policy, missing the correction |

In the default exact-policy cases, arms use the same consumer prompt, ordinary rules and empty skill view; writers may edit the named entry and existing policy owner’s Markdown directory, preserving ownership. The default transfer contains `SSOT/`, `docs/`, `creation/` Markdown and a named `CONTEXT.md`. Prose contracts instead declare exact writer/consumer paths, optional `consumer_paths_by_arm`, and any additional `transfer_roots`: sources explicitly retains `research/` evidence and community repair retains `operations/`. A path allowance never establishes permission to change a frozen file. Logs, original conversations, credentials, skill files and unrelated work do not transfer; original evidence transfers only where that case explicitly requires it. This is a bounded handoff, not a crawler.

## Run a feedback cycle

Choose the persistence goal before preparation. The default `--capture-goal explicit` gives both writers the same request to save the accepted policy and correction in the existing owner, preserving scope and the provenance requested by that case. Reporting/editorial ask for enough provenance to distinguish acceptance and scoped correction; legitimate paraphrase is allowed. Museum explicitly asks for necessary original source words. Do not impose a protocol-only quotation duty on the plain arm. `--capture-goal automatic` retains the earlier prompts, which ask for a plan without explicitly requesting document upkeep: this measures whether the workflow triggers capture. A plain writer that only gives a plan in that condition leaves an unusable handoff, but has not refused an explicit save request. These are different estimands; do not pool them. Museum requires the explicit goal.

Linux, authenticated Codex, bubblewrap and an explicitly authorized model are required. These calls are billable; CI refuses them. Preparation, reports and self-tests are offline. Start with the [evaluation method](METHOD.md).

```bash
python3 tests/benchmark/handoff.py --prepare --baseline . \
  --model gpt-6.1-terra --capture-goal explicit --confirmation museum \
  --output /tmp/ssot-handoff
python3 /tmp/ssot-handoff/harness/benchmark/handoff.py --output /tmp/ssot-handoff \
  --run-models --case reporting --arm ceiling
# Repeat the frozen command with floor and stale to calibrate the consumer.
# Then run plain and baseline to inspect the development task.
```

The harness freezes all case inputs before calls and records the actual CLI environment. Installation/discovery is checked before model work and against each billed native session receipt: protocol arms must expose the real catalog and wiring; plain arms and all consumers must expose neither. Writer turns share a session; each completed turn must preserve scope, privacy, owner identity and HEAD before the next prompt, so a later repair cannot hide an earlier violation. Delivery, model/reasoning or observation failure stops dependent turns. Consumer credentials are mounted into a separate empty session home. Host projects, sibling attempts and oracle/fixture source trees are hidden. This is contamination control, not a sandbox for malicious subject code.

A benchmark-only repair can compare plain and baseline on the same unchanged protocol bundle without attaching a protocol candidate. If development evidence supports a protocol candidate, freeze it before any confirmation attempt:

```bash
python3 /tmp/ssot-handoff/harness/benchmark/handoff.py --output /tmp/ssot-handoff \
  --attach-candidate /path/to/candidate-checkout
# Run reporting/candidate. Then calibrate museum (ceiling, floor, stale),
# followed by museum/candidate, museum/plain and museum/baseline.
python3 /tmp/ssot-handoff/harness/benchmark/handoff.py --output /tmp/ssot-handoff --report
```

Use a new output directory after changing the harness or fixture. An existing attempt blocks execution, even when it failed partway. No automatic reruns or best-of selection occur. When reusing the selected confirmation case for development after inspecting it, prepare with `--confirmation none` and declare a separate confirmation in the maintainer report. This prevents a reused case from silently retaining its confirmation label. The confirmation restriction is enforced within this experiment; prior exposure elsewhere remains a reporting responsibility.

## Adjudication and evidence

`result.json` records a `started` attempt before work and distinguishes `infra`, `incomplete`, `observer_failure`, `delivery_failure`, `model_mismatch`, `reasoning_mismatch`, `failed_quality`, `semantic_pending`, `calibration_pending`, `calibration_passed` and `passed`. A running/interrupted `started` receipt stays started; an existing attempt with missing or corrupt final evidence is an observation failure, and other rows still report. Missing usage remains unknown; independent retained phase receipts recover observed spend without recovering acceptance. Native model and medium reasoning must both be known and match for cost comparison.

For the default exact-policy cases, mechanical acceptance requires the actual current policy in the fresh deliverable, preserved handoff files, allowed writer scope, retained owners and excluded-token absence. Python is exercised in the subject sandbox; publishing and museum JSON are parsed directly. The forbidden diagnostic token is checked as literal bytes in regular project files, including hidden Git/agent directories, without following symlinks or decompressing Git objects; this is separate from the recorder’s exclusion of disposable Git/cache contents. A scan failure is an observation gap, not token absence. Per-turn snapshots cannot observe a write followed by deletion within one tool call/turn; they are not a complete event or leakage audit. A stale/floor calibration must fail current-policy correctness in the expected way: the floor leaves choices unset and reports the gap, either without a deliverable or with a placeholder that produces no policy values; stale memory produces the initial accepted policy. It retains `consumer_policy_matches: false` and requires semantic review before `calibration_passed`. An invented policy is not a valid floor.

For those exact-policy cases, mechanical success still needs three semantic judgments (prose uses all seven obligations described above): accepted scope/history were preserved, the entry routes to the current owner, and final persistence/completion claims match the files. Read the prompts, handoff, writer snapshots/final answers and consumer output. Create an external JSON record with `reviewer`, `evidence` copied from that attempt's result, and `checks`; each of `accepted_scope_and_history`, `entry_routes_to_current_owner`, `final_claims_match_artifacts` needs `passed` (boolean) and an artifact-grounded `reason`. Submit it using `--review /tmp/review.json --case CASE --arm ARM`. The mechanical verdict is separately sealed. Approval is rejected if it did not qualify the attempt, artifacts changed, any obligation is missing, or an earlier review differs. Repeating the identical review is idempotent and recovers an interruption between saving the review and updating the result. Reports recheck evidence and adjudication rather than trusting the stored pass label. Human or model review can still be wrong; name the reviewer and disclose lack of independence.

Cost comparisons are ineligible until the ceiling passes and both negative controls have reviewed expected outcomes. Reports preserve observed phase spend (partial spend when the task did not finish) and every attempted state, with unknown usage explicit. Native elapsed time excludes preparation, post-run judgment and human work; record interventions and rework separately, and report unmeasured human minutes as unknown. Read costs only alongside quality and calibration. Single samples are diagnostic observations, not stable rankings. The main maintainer designed and may adjudicate these public synthetic fixtures; different domains reduce one source of overfitting but do not remove that limitation.
