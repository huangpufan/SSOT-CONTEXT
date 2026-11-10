# Generic-context native trials

These opt-in trials compare observable user outcomes against frozen inputs and a host-side oracle. They include the initial C01 non-Git space and D03 immediate decision capture/partial correction smoke cases, cross-domain owner scenarios, and reused development reading cases. A mechanically passing result still requires the listed independent semantic review; the subject's final answer is never its own oracle.

The completed experiment and its limits are in [the native report](trials-5.0.md) and [versioned machine inventory](results/context-evolution-5.0-2026-11-10.json). The report owns semantic conclusions; the inventory owns attempt usage, elapsed durations, manifests and receipt hashes. Both retain failed and interrupted observations.

Run offline checks without models:

```bash
python3 tests/context/test_context.py
python3 tests/context/test_source_contract.py
```

Prepare from an exported baseline. Preparation freezes tasks, fixtures, oracle, harness and baseline bundle before billable calls. It refuses existing output directories and requires an explicit authorized model. The November context-evolution experiment fixes `gpt-6.1-sol` under that task's user authorization; this does not change the repository's standing model policy. Both arms use the frozen model and medium reasoning, and record actual native model/usage receipts. CI refuses billable calls.

```bash
python3 tests/context/run.py --prepare --baseline /tmp/exported-4.5 --model gpt-6.1-sol --cases C01 D03 --output /tmp/context-smoke
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
