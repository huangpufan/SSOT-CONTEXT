# Generic-context native trials

These opt-in trials compare observable user outcomes against frozen inputs and a host-side oracle. They include the initial C01 non-Git space and D03 immediate decision capture/partial correction smoke cases, cross-domain owner scenarios, and reused development reading cases. A mechanically passing result still requires the listed independent semantic review; the subject's final answer is never its own oracle.

The completed experiment and its limits are in [the native report](trials-5.0.md) and [versioned machine inventory](results/context-evolution-5.0-2026-11-10.json). The report owns semantic conclusions; the inventory owns attempt usage, elapsed durations, manifests and receipt hashes. Both retain failed and interrupted observations.

Run offline checks without models:

```bash
python3 tests/context/test_context.py
python3 tests/context/test_source_contract.py
```

Prepare from an exported baseline. Preparation freezes tasks, fixtures, oracle, harness and baseline bundle before billable calls. It refuses existing output directories and requires an explicit authorized model. The commands below use the standing authorized `gpt-6.1-terra` model. The historical November 10 experiment used `gpt-6.1-sol` under its separate task authorization; that exception does not apply to new runs. Both arms use the frozen model and medium reasoning, and record actual native model/usage receipts. CI refuses billable calls.

```bash
python3 tests/context/run.py --prepare --baseline /tmp/exported-4.5 --model gpt-6.1-terra --cases C01 D03 --output /tmp/context-smoke
python3 /tmp/context-smoke/harness/context/run.py --output /tmp/context-smoke --run-models --arm baseline
python3 /tmp/context-smoke/harness/context/run.py --output /tmp/context-smoke --attach-candidate /path/to/frozen-candidate
python3 /tmp/context-smoke/harness/context/run.py --output /tmp/context-smoke --run-models --arm candidate
```

Candidate attachment is a new immutable manifest; it does not rewrite the original baseline plan. Both arms use the same already frozen harness, tasks and fixtures. A changed harness or oracle requires a new experiment, retaining old attempts and their invalidation reason. Failures and interrupted attempts cannot be overwritten or silently retried. Cost records require native per-turn usage and the expected actual model; cumulative CLI totals are insufficient. One attempt per arm provides scoped path evidence and no general performance or reliability conclusion.

The runner reuses the reading benchmark's isolated writable workspace/home and read-only skill mount. It hides host histories, unrelated projects, sibling attempts and oracle sources. Authentication is mounted read-only without copying it into artifacts. Do not use the weaker historical memory runner's whole-home/whole-temp mounts for these comparisons. Event-boundary snapshots and tool receipts observe capture/readback ordering; they do not establish every intermediate filesystem state.

`C06`/`C07` require `--connector PATH` at preparation. This freezes one external reference connector for both arms and tests protocol behavior under that shared condition. It does not establish that the historical baseline shipped the connector. C07 interrupts only an owned child after actual two-owner readback, changes an owned fixture to invalidate its receipts, then uses a fresh native session/home. Independent CLI counterexamples cover progress/authority combinations without calling models; `SSOT_CONTEXT_CONNECTOR` can select an immutable historical script for a before/after check.

Use `installed_run.py` separately for actual installed discovery. It runs the official local-source installer in an owned fixture, wires the real project AGENTS, verifies the actual catalog/instructions with a zero-model probe, and sends ordinary user requests without injecting skill names, script paths or adapter instructions. `--ordinary-negative` installs skills without declaring a space or adding AGENTS; `--hybrid` builds the real mixed format-5 parent/format-4 child task. These are candidate-only behavior checks, not performance comparisons. Preparation requires an explicit model and immutable candidate path; use a new output directory for every observation. A probe-only run is retained separately and cannot silently become a model run.

The installed setup follows official [skill discovery](https://learn.chatgpt.com/docs/build-skills) and [AGENTS discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md), but the actual CLI probe and native receipts establish what happened in this experiment. The normal comparison transport suppresses project-document injection and supplies an adapter; installed mode intentionally retains actual AGENTS discovery. Keep those evidence levels distinct.

`report.py --evidence-root PATH --output PATH` regenerates the compact inventory from retained evidence, including corrected grader files without overwriting original verdicts. It deduplicates manifests and includes the semantic report's hash when present. It never runs models.

Use `installed_run.py --prepare --candidate PATH --model gpt-6.1-terra --continuation --output /tmp/NEW-RUN` for four fresh sessions sharing one installed general space: capture, limited correction, an unrelated typo and cold retrieval for a concrete deliverable. Run its frozen `harness/context/installed_run.py --output /tmp/NEW-RUN --run-models`. `--large-register conflict` and `--large-register typo` instead install a development fixture with 80 protected rules. Each mode requires a separate new output directory. Offline calibration is in `test_continuation.py`, `test_register.py` and `test_source_oracle.py`; semantic content and actual reading still require direct review. These are candidate observations, not performance comparisons or real longitudinal use.

C06 now requires the original method's successful two-owner completion to remain observable, and prevents its correction from completing while the original identity is conflicted. It checks the actual completed references against submitted readback receipts, allowing old invalidated receipts to remain in history. The historical 5.0 report used its frozen helper/oracle; its r2-completed result does not validate today's ancestor-conflict contract.

The [5.1 continuation and source handoff report](trials-5.1.md) retains failed and prepared-only attempts, calibrated oracle changes and installed development controls. Its [inventory](results/context-evolution-5.1-2026-11-12.json) records actual Terra versions, frozen identities and costs.

The [5.2 discovery report](trials-5.2.md) retains child-start and named-entry observations, including two rejected path-resolution clauses and a zero-model discovery failure. Its whole-workspace snapshots expose a launch-directory limitation in the inherited recorder; do not interpret that recorder's empty `changed_paths` as no edits outside the launch subdirectory.

## Connected maintenance and an executable cold handoff

Use the installed long-chain mode when the decision concerns connected maintenance rather than isolated capture. The development case keeps one source task across accepted multi-owner capture, a limited correction interrupted after one owner write, cold completion, duplicate input plus a genuinely new independent item alongside conflict, limited use withdrawal and a fresh executable-data consumer. The confirmation case is a format-4 queue implementation with capacity, identity, dependencies, an independent paused rule and external-use withdrawal; it changes task shape and does not claim to reproduce the interruption. The [current work record](../../docs/benchmark-deepening-2026-11-12.md) distinguishes proposed, calibrated and actually observed paths.

Prepare a new root for every attempt, with an explicitly authorized model. Preparation uses the official local-source installation and freezes the fixture, contract, private public-CLI calibration, harness and bundle before any model call:

```bash
python3 tests/context/installed_run.py --prepare --candidate /path/to/frozen-S0 \
  --model gpt-6.1-terra --longchain --longchain-kind development --cap 300 \
  --output /tmp/NEW-CONTINUITY
python3 /tmp/NEW-CONTINUITY/harness/context/installed_run.py \
  --output /tmp/NEW-CONTINUITY --run-models
```

`--longchain-kind confirmation` selects the independently authored queue shape. `--longchain-control ceiling`, `floor` or `stale` prepares only that shape's fresh consumer and requires a separate new root. Use the same consumer prompt and empty skill/state/source-export view as the real handoff. Ceiling must implement the current accepted policy; stale must actually implement the initial accepted policy, not fail from an unrelated bug. Floor may explicitly report missing choices and leave a stub or refuse to implement; a mechanical gap candidate is not a passed control. Its artifact-bound semantic review must name the missing accepted choices, verify explicit nonimplementation and rule out accidental syntax/name errors or a false completion claim.

The development partial-write fault temporarily read-only binds the existing second owner, and the observer terminates only its owned child after an actual first-owner capture with the other owner unchanged. Recovery uses a new session/home without that fault, preserves the existing operation identity and external note, finishes all owner writes, then reads back and completes. This is a declared experiment window, not a new product ordering requirement. A missed window or broken observation is retained as invalid; no automatic retry occurs. The separate C07 path continues to test the later two-owner-readback/stale-receipt boundary.

Each phase has actual prompts, native identity/discovery/usage, byte/type/mode/link evidence and public connector observations where applicable. Reports preserve known failed/interrupted spend; missing usage stays unknown. Original source records, prior sessions, connector state, writer final answers and skills do not transfer to the consumer. The queue consumer receives only maintained documents and its frozen initial code stub. Executable output does not establish that earlier owner standing or source/use history was correct; inspect the phase artifacts before submitting the standard three-obligation evidence-bound review:

```bash
python3 /tmp/NEW-CONTINUITY/harness/context/installed_run.py \
  --output /tmp/NEW-CONTINUITY --review /path/to/artifact-review.json
python3 /tmp/NEW-CONTINUITY/harness/context/installed_run.py \
  --output /tmp/NEW-CONTINUITY --report
```

Native phase time excludes preparation, adjudication and human work. Intentional interruption may leave token cost unknown; counts of completed sessions cannot replace the capture/recovery/authority path denominator. Event-boundary snapshots do not observe arbitrary write-and-delete sequences within one tool call, arbitrary concurrency or unknown external side-effect outcomes. Keep those limits separate from the specific observed controlled failure and recovery.

A native usage snapshot is not automatically the complete cost of an interrupted turn. Complete tokens require the same turn's closing usage to cover its final model output; a snapshot followed by more reasoning or tool calls is only an observed lower bound. Keep elapsed time and known tokens, leave complete token totals unknown and exclude complete-cost comparisons. This dependency also applies when reusing historical interruption evidence: saved-state/quality observations can remain useful while old cost completeness is unverified. Do not silently rewrite historical reports or assume their costs have been rejudged.

For a new read-only cost interpretation of an existing frozen attempt, use the current reporter with a new external output directory:

```bash
python3 tests/context/installed_run.py --report --output /tmp/FROZEN-ATTEMPT \
  --report-output /var/tmp/NEW-COST-ANALYSIS
```

The separate report identifies its reporter, frozen plan and native/sealed evidence hashes, retains observed lower bounds, and lists invalidated historical complete-cost fields. It does not rerun models, change the original frozen harness or alter a quality verdict. Preserve the original versioned report alongside this new interpretation; exact offline reconstruction and whether its old cost claim remains valid are different questions.

Future installed executions also save `execution-timing.json`: execute entry through executor return or exception after terminal sealing, including setup, zero-model discovery probes, native phases, host transitions and mechanical checks. It excludes preparation, external semantic review and persistence of the timing receipt itself. The receipt binds the frozen plan and final mechanical record. Historical attempts without it retain unknown executor wall time; reanalysis cannot reconstruct that duration from file timestamps or native-only time. This executor interval still does not measure the complete user task.
