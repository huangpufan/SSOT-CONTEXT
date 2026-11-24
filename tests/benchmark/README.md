# SSOT evaluation and reading benchmark

Use the [evaluation method](METHOD.md) to choose evidence for a protocol decision. The suite combines the reading lane below with [cold handoff and plain-docs controls](HANDOFF.md) and the existing capture, protection, source, continuation, installation and migration trials. It has no combined score: correct action, useful handoff, preservation and honest evidence come before conditional cost comparisons.

This opt-in benchmark asks a native agent to finish a small executable task whose accepted behavior lives in repository Markdown. It measures whole-task cost and independently checks the resulting code. A shorter or faster run that loses a rule is a quality failure, not an optimization.

Use it to compare a protocol change or to test whether better task routes help. These are separate experiments: mixing both changes cannot tell you which caused a difference. The benchmark is development tooling; it is not installed in consumer repositories and adds no required reader, cache or index format.

For the cost and quality of **creating** repository memory, use the [bootstrap comparison](../../docs/2026-11-19-bootstrap-v5.7.md). Its isolated writer and document-only reader exercise a recorded policy and a real file-operation tool. The measurements include the writer’s helpers.

For general spaces in a shared directory, the [setup and recovery trial](space_setup.py) prepares ordinary reading, review, continuation and disputed-checkpoint cases. The [5.8 report](../../docs/2026-11-19-context-maintenance-v5.8.md) includes the prompts' outcomes, a cold handoff and source withdrawal checks.

[Catch-up trials](catchup.py) exercise retained archive links, withdrawal followed by cold recovery, merged Git history and gaps before a requested range. The [5.9 review](../../docs/2026-11-20-catchup-v5.9.md) records the old and new outcomes and reproduction commands.

The [six-shift trial](six_shifts.py) follows an editorial and research project across independent sessions, then asks a fresh reader to recover the reason for a superseded preference. The [5.13 study](../../docs/2026-11-20-context-stewardship-v5.13.md) includes the plain-documents control, original evidence loss and reproduction commands.

For routine software, research and creative queries, the [direct-lookup study](../../docs/2026-11-20-read-trigger-study.md) compares input costs and follows a five-shift handoff. Its [receipts](results/read-trigger-study.json) record both correct answers and unwanted reads or writes.

For a single rule change, the [ordered-lookup study](../../docs/2026-11-20-ordered-lookup-cost.md) measures what a fresh reader recovered. Its [file-open records](results/ordered-lookup-cost.json) show when the agent requested a source before learning its permissions. These small trials leave broader savings and access reliability open.

For mixed tasks that combine one approved prose edit with a read-only lookup in another owner, the [mixed-edit study](../../docs/2026-11-24-mixed-edit-study.md) pairs 5.15 against an isolated decoupling candidate on Codex across format 4 and format 5, with plain-docs controls, cold readers and kernel `inotify` file-open witnesses. Protocol 5.15 was kept after premature Closeout backtracking and API round-trip variance raised aggregate input by 7.4%; see its [frozen results](results/mixed-edit-study.json).

For hot-path reference splitting (`memory-model.md` and `context-spaces.md`) plus the `ssot-closeout/SKILL.md` format-5 `Otherwise` guard, the [hot-path split study](../../docs/2026-11-24-hotpath-split-study.md) runs 38 completed native Codex sessions across Parcel desk coding, warm refresh, protected rules, preference capture, undocumented code-protection recovery and format-5 tasks. Splitting cross-referenced §3/§5 sections caused deterministic +1 API-turn hops on `dev4_protected`; restricting the split to non-preflight §2 and cold format-5 setup passed 24/24 runs with zero extra hops, while 12-pair aggregate input stayed flat (+0.36%) because single-turn API batching variance dwarfs ~3 KB file reductions. Protocol 5.15 remains unchanged; see [frozen results](results/hotpath-split-study.json).

For delegated subagent preflight/closeout skipping motivated by the [Stage 5 real-session audit](../../docs/2026-11-24-real-session-stage5-audit.md), the [delegated subagent study](../../docs/2026-11-24-delegated-subagent-study.md) pairs 5.16 against a candidate adding explicit delegated-worker skip clauses across 12 frozen Codex pairs (6 primary delegated tasks with 80–90 invariant rows, 4 safety counterexamples, and 2 top-level controls). All 24 sessions passed behavioral checks, but baseline 5.16 already skipped redundant protocol reads on 6/6 well-briefed primary tasks (`proto=[]`), while the candidate raised primary input by +7.46%, raised top-level control input by +25.41%, and skipped `ssot-closeout` / `source-retention.md` on a format-5 space-owner edit next to a withdrawn source. Protocol 5.16 remains unchanged; see [frozen results](results/delegated-subagent-study.json).

For permission-safe batching and same-step on-disk readback, the [5.16 release study](../../docs/2026-11-24-batching-readback-v5.16.md) evaluates 16 clean matched Codex pairs (12 main + 4 unseen confirmation pairs covering `warm`, `stale`, `typo`, and format-5 setup recovery, plus 4 cold readers and kernel `inotify` file-open witnesses). All 36 clean sessions passed with zero permission or readback regressions, total input dropped 14.70% (1,832,077 to 1,562,792) and API round-trips dropped 14.89% (94 to 80; 10 fewer, 6 tied, 0 more); protocol 5.16 was released with zero new files or budget increases. See [frozen results](results/batching-readback-5.16.json).

For optional topic-sharded invariants registers (`SSOT/invariants/<topic>.md` or `ssot_register: shard`) addressing the 251 KB monolithic entry truncation bottleneck identified in the Stage 5 audit, the [5.17 release study](../../docs/2026-11-24-register-sharding-v5.17.md) pairs 5.16 against 5.17 across 8 frozen counterbalanced Codex pairs (16 `gpt-6.1-terra` `medium` sessions: 6 large 360-invariant coding, protected-rule, cross-topic widening, and sharded closeout pairs plus 2 byte-identical unsharded controls). All 16 sessions passed quality and safety checks; on the 6 large pairs, initial `SSOT/README.md` read truncations dropped from 6/6 to 0/6 (total truncated tool calls 13 to 4), aggregate native input dropped 21.60% (1,178,239 to 923,693, lower on all 6/6 pairs), uncached input dropped 16.92%, and unsharded controls showed no regression (input -5.95%). Protocol 5.17 was released with +18 checker unit tests and zero budget ceiling raises; see [frozen results](results/register-sharding-5.17.json).

For narrowing the `ssot-closeout` checker trigger (removing false-positive `added` checks on pure external file additions while keeping checks for `SSOT/`/routed edits and external moves/renames/deletions) and routing immediate decision capture (`decision-capture.md`) into topic shards, the [5.18 release study](../../docs/2026-11-24-closeout-sharding-v5.18.md) pairs 5.17 against 5.18 across 6 frozen counterbalanced Codex pairs (12 `gpt-6.1-terra` `medium` sessions: 3 pure external file-addition pairs, 2 sharded immediate-capture pairs, and 1 deleted-file safety counterexample). All 12 sessions passed quality and safety checks: on the 3 pure addition pairs, unnecessary `ssot-check.py` executions fell from 3/3 to 0/3 and aggregate input fell 12.26% (437,703 to 384,054, lower on 3/3; API turns 21 to 19); 2/2 sharded immediate-capture runs placed new topic rules in `SSOT/invariants/webhooks.md` (input -2.85%); and the deleted-file counterexample still ran `ssot-check.py` and cleared stale references (input -10.32%; overall 6-pair input -9.27%, turns -7.50%). Protocol 5.18 was released with +19 hot-path runtime words and zero adapter/catalog growth; see [frozen results](results/closeout-sharding-5.18.json).

For inlining the restricted-first `ssot-check.py` invocation in `decision-capture.md` (F4, accepted) and testing sharded-register hints on the `SKILL.md` bounded-lookup/edit fast paths (F3, falsified and withdrawn), the [5.19 release study](../../docs/2026-11-25-bounded-shard-and-capture-v5.19.md) runs 10 frozen counterbalanced Codex pairs (20 `gpt-6.1-terra` `medium` sessions). On F4 (6 pairs: 3 format-4 sharded discussion-only captures, 1 format-5 no-Git capture, and 2 format-5 restricted-source counterexamples with kernel `inotify`), all 6/6 pairs passed task and safety checks, redundant format-4 `batch-closeout.md` loads fell from 3/3 to 0/3 while `ssot-check.py` stayed 6/6 (with `--owners` and zero unauthorized opens on restricted sources), and aggregate native input fell 5.71% (683,152 to 644,158; -10.70% on format-4 capture). On F3 (4 pairs), baseline 5.18 already opened the matching topic shards 3/3 and passed 4/4 while F3 regressed to 3/4 on a protected prose conflict, so F3 was withdrawn. Protocol 5.19 was released with +15 hot-path words and zero entrypoint/catalog/adapter byte growth; see [frozen results](results/bounded-shard-and-capture-5.19.json).

## What it runs

The synthetic Parcel desk repository has a quotation module, compatibility tests, accepted delivery and eligibility owners, a superseded proposal, product/architecture entries and 24 adjacent operational documents by default. Arbitrary contract values vary deterministically by repetition and stay identical between paired arms. The agent implements express delivery while preserving standard quotes and the cross-service digital-goods exception. Policy files and supplied tests must remain unchanged. This explicit write scope keeps the experiment about reading and implementation; decision capture and documentation upkeep need separate trials.

| Case | Reading problem | Independently checked outcome |
| --- | --- | --- |
| `routed` | A matching route points to the contract and related eligibility owner | Express prices, threshold boundaries, regions, timing, error handling, standard compatibility and digital exceptions |
| `unrouted` | No matching task route | Same contract, found through project entries and owner links |
| `stale` | Route points to a missing file; an obsolete proposal also exists | Current accepted behavior, not the rejected flat price |
| `warm` | After the first task, another writer changes a tracked owner and adds a routed untracked owner without moving HEAD | Second turn in the same session applies the new threshold and preserves everything else |
| `typo` | A one-word edit needs no SSOT reading | Only the requested correction; traces expose unnecessary preflight reading |

The oracle probes 144 combinations per code task, including exact threshold edges and an unknown service. It rejects the unchanged stub, missing digital exceptions, stale thresholds and edits to tests or policy. These are scoped executable outcomes, not proof that the agent understands every document. Source-phrase matches in returned command output record observed contract, eligibility, promotion and distractor reads. A missing phrase is unknown: a smaller excerpt or another tool may omit it. The agent's own claim that it read a document is not evidence.

## Prepare and run

Requirements for live runs: Linux, `bwrap`, `timeout`, Git, Python 3.10+ and an authenticated `codex` CLI with access to the selected model (default `gpt-6.1-terra`). The tested CLI version is recorded in each experiment. Preparation, reporting and self-tests make no model calls. Live execution requires `--run-models` and refuses to run when `CI` is set. An authorized experiment can select `--model MODEL` during preparation; model and medium reasoning are frozen in the plan and checked against native receipts. Execution cannot change that model. A model parameter does not grant authorization under the repository's model policy.

Supply two repository directories containing `skills/`. For a historical baseline, export its commit into a temporary directory, then prepare the plan. Replace `BASELINE_REF` with the commit or tag you want to compare.

```bash
baseline_dir=$(mktemp -d)
git archive BASELINE_REF | tar -x -C "$baseline_dir"
python3 tests/benchmark/run.py --prepare \
  --baseline "$baseline_dir" --candidate . \
  --output /tmp/ssot-reading-protocol --model gpt-6.1-terra --repeats 3
python3 /tmp/ssot-reading-protocol/harness/benchmark/run.py \
  --output /tmp/ssot-reading-protocol --run-models
python3 /tmp/ssot-reading-protocol/harness/benchmark/run.py \
  --output /tmp/ssot-reading-protocol --report
```

The prepared output must be new. Preparation freezes both skill bundles, fixture trees, harness code, seed and execution order before any model calls. Run the frozen harness printed by the prepare command; it checks manifests before and after execution. The runner alternates arm order within each case's repetitions, shuffles the pairs and executes serially. Three repetitions of the default suite mean 30 attempts and 36 model turns, because `warm` has two turns. Use `--cases routed --repeats 1` for a two-attempt pipeline smoke test; this is not a performance conclusion.

To measure only the index, use the same candidate bundle in both arms. The coarse arm routes through product/architecture; the targeted arm links directly to the contract and states the related reading condition. Preparation rejects fixture differences outside `SSOT/README.md`. Both arms contain identical owner text and code.

```bash
python3 tests/benchmark/run.py --prepare --comparison index --candidate . \
  --cases routed warm --model gpt-6.1-terra --repeats 3 --output /tmp/ssot-reading-index
python3 /tmp/ssot-reading-index/harness/benchmark/run.py \
  --output /tmp/ssot-reading-index --run-models
```

An existing result, including failure, is retained when execution resumes. An interrupted attempt without a result blocks resume rather than silently restarting a partially changed repository; preserve that experiment and use a new output directory. There are no automatic retries or best-of selection. Use a new experiment for changed fixtures, harness code, source or environment. Do not overwrite a failed run after fixing its cause.

## Evidence and interpretation

Judge correctness first, then task completion time and total input/output tokens. Cache and tool statistics are diagnostic: they help explain variability and reading patterns, but do not decide efficiency or billing by themselves.

Each attempt gets an isolated writable repository and Codex home, a read-only skill bundle and necessary system/runtime files. Host projects, historical sessions, sibling attempts and fixture/oracle sources under the hidden home/temp roots are unavailable. Authentication is mounted for the CLI without copying it into the artifact. This controls accidental experiment contamination; it is not a sandbox for malicious code. Keep experiments under `/tmp` or `/var/tmp` so that the hidden-root boundary applies.

`plan.json` records hashes, inputs and order; `environment.json` records CLI/Python versions. Every turn retains its prompt, command/event stream, stderr, native session receipt, final answer, before/after files, summary and separate oracle verdict. The benchmark disables the historical recorder's per-event repository snapshots so observer work does not grow with every tool event. The separate [historical recorder](../run-performance-trials.py) still supports decision-order investigations that need those snapshots.

`report.md`, `report.json` and `report.csv` can be regenerated offline. They show all attempts, including quality failures, timeouts, observer failures, wrong-model execution, infrastructure failures and unrun entries. Costs from failed turns remain in the data. These are observed native phase costs; preparation, semantic review, human interventions and rework need separate accounting, with unmeasured human minutes left unknown. Only pairs that both pass and have valid native per-turn usage enter the descriptive cost comparison; every excluded pair remains visible. This conditional comparison can still be biased when quality differs, so inspect quality counts first. Fewer than three usable pairs are pipeline observations only. Medians, ranges and paired changes do not establish significance or a general percentage gain.

| Metric | Meaning |
| --- | --- |
| Seconds | Full native turn, including model, tools and event recording; excludes preparation and post-run oracle |
| Input tokens | Native per-turn input, including cached input |
| Cached / uncached input | Cached input is reported separately; uncached is input minus cached |
| Output tokens | Native per-turn output, separate from input; not added into a synthetic score |
| Tool items | Completed command, file-change and MCP items exposed by the CLI |
| Tool output bytes | UTF-8 command text returned by the CLI; not disk reads, token counts or guaranteed untruncated output |

Resume's cumulative CLI usage is never substituted for native turn usage. Missing native records, unknown reasoning effort, or an unexpected model/effort exclude the cost comparison; they are not treated as zero. Cache/provider conditions remain uncontrolled, and cost is not converted to money. Inspection of final code and saved tool receipts complements the automatic oracle: passing code does not establish that every protocol branch was followed.

The fixture is deliberately small and synthetic, with one code domain and an adapter injected into the prompt. It does not measure installed-skill discovery, large production repositories, bootstrap/migration, decision capture, actual protected-departure approval, unrelated dirty-state costs, other models or statistical reliability. Repeated tuning against these cases risks overfitting; add independent project-shaped tasks before making broad claims. The [4.4 report](../trials-4.4.md) records the experiments actually run and their limits.

## Check the benchmark itself

```bash
python3 -m unittest discover -s tests/benchmark -p 'test_*.py'
```

CI checks deterministic fixture parity, mechanical documentation validity (except the deliberate broken route), positive and negative oracle cases, warm-state freshness, per-turn usage attribution and reports that retain failures. It never runs billable models. Preserve original evidence if the oracle is wrong; a changed oracle or harness is a new version, not permission to replace old results silently.

## Replay the cross-domain maintenance tasks

Use `stewardship_paths.py` for software, research, creative work, compatible and conflicting editorial decisions, format-specific lookups, protected changes and unrelated copyedits. A fresh directory is required for each arm and lane. Preparation makes no model calls. The opt-in runner installs the requested bundle into the test project, verifies native discovery and records one fresh Terra session per phase. The seven-stage history question uses the existing six-shift runner. Run both for the full 22-phase workload. The [architecture study](../../docs/2026-11-20-context-paths-study.md) also records a separate DSH host comparison. Apply [the archived runtime patch](fixtures/context-paths-candidate.patch.gz) to a disposable checkout of the study baseline to reproduce the candidate.

```sh
python3 tests/benchmark/stewardship_paths.py --plain --lane research --output /tmp/ssot-plain-research
python3 tests/benchmark/stewardship_paths.py --bundle . --lane research --output /tmp/ssot-new-research --run-models
python3 tests/benchmark/six_shifts.py --bundle . --output /tmp/ssot-new-history --run-models
```
