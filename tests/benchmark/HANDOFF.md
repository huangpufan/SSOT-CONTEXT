# Cold handoff benchmark

A writer receives a lasting decision and a scoped correction. A new consumer receives only the maintained Markdown and must implement the current policy. Its fresh session has neither the original conversation nor SSOT skills. This tests whether the recorded knowledge works for someone who was not present.

`reporting` produces a Python policy function for interactive and unattended reports. `editorial` uses a named format-5 entry and produces publishing configuration for narration and quotation. `museum` is an independently authored format-5 confirmation about gallery labels and inventory records; it varies domain and authorship while retaining the two-mode JSON task shape. All preserve an independent boundary and an arbitrary exact required field (seeded for reporting/editorial, independently fixed for museum); the correction changes only one mode. Neither writer may implement the consumer's deliverable or retain the explicitly excluded diagnostic token. Unrelated binary/text work remains untouched. Markdown wording and layout are not prescribed; the existing owner and usable entry must survive.

| Arm | Writer | Consumer input |
| --- | --- | --- |
| `plain` | The same SSOT-shaped factual entry and ordinary project rules; no bundle, catalog or workflow block | Writer's maintained Markdown |
| `baseline` / `candidate` | Same initial facts; official project installation and actual SSOT wiring | Writer's maintained Markdown |
| `ceiling` | No writer call | Hand-authored complete current policy |
| `floor` | No writer call | Initial owner with choices still unsettled |
| `stale` | No writer call | Initial accepted policy, missing the correction |

All consumers use the same ordinary rules, prompt and empty skill view. The fixture grants writes to its named entry and the existing policy owner’s Markdown directory; it does not authorize relocating ownership. The transfer includes `SSOT/`, `docs/`, `creation/` Markdown and a named `CONTEXT.md`; logs, original conversations, raw sources, credentials, skill files and unrelated local work do not transfer. This is a declared portable handoff boundary, not a general crawler. A new task with other owners needs an explicit boundary.

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

Mechanical acceptance requires the actual current policy in the fresh deliverable, preserved handoff files, allowed writer scope, retained owners and excluded-token absence. Python is exercised in the subject sandbox; publishing and museum JSON are parsed directly. The forbidden diagnostic token is checked as literal bytes in regular project files, including hidden Git/agent directories, without following symlinks or decompressing Git objects; this is separate from the recorder’s exclusion of disposable Git/cache contents. A scan failure is an observation gap, not token absence. Per-turn snapshots cannot observe a write followed by deletion within one tool call/turn; they are not a complete event or leakage audit. A stale/floor calibration must fail current-policy correctness in the expected way: the floor leaves choices unset and reports the gap, either without a deliverable or with a placeholder that produces no policy values; stale memory produces the initial accepted policy. It retains `consumer_policy_matches: false` and requires semantic review before `calibration_passed`. An invented policy is not a valid floor.

Mechanical success still needs three semantic judgments: accepted scope/history were preserved, the entry routes to the current owner, and final persistence/completion claims match the files. Read the prompts, handoff, writer snapshots/final answers and consumer output. Create an external JSON record with `reviewer`, `evidence` copied from that attempt's result, and `checks`; each of `accepted_scope_and_history`, `entry_routes_to_current_owner`, `final_claims_match_artifacts` needs `passed` (boolean) and an artifact-grounded `reason`. Submit it using `--review /tmp/review.json --case CASE --arm ARM`. The mechanical verdict is separately sealed. Approval is rejected if it did not qualify the attempt, artifacts changed, any obligation is missing, or an earlier review differs. Repeating the identical review is idempotent and recovers an interruption between saving the review and updating the result. Reports recheck evidence and adjudication rather than trusting the stored pass label. Human or model review can still be wrong; name the reviewer and disclose lack of independence.

Cost comparisons are ineligible until the ceiling passes and both negative controls have reviewed expected outcomes. Reports preserve observed phase spend (partial spend when the task did not finish) and every attempted state, with unknown usage explicit. Native elapsed time excludes preparation, post-run judgment and human work; record interventions and rework separately, and report unmeasured human minutes as unknown. Read costs only alongside quality and calibration. Single samples are diagnostic observations, not stable rankings. The main maintainer designed and may adjudicate these public synthetic fixtures; different domains reduce one source of overfitting but do not remove that limitation.
