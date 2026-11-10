# Reading benchmark

This opt-in benchmark asks a native agent to finish a small executable task whose accepted behavior lives in repository Markdown. It measures whole-task cost and independently checks the resulting code. A shorter or faster run that loses a rule is a quality failure, not an optimization.

Use it to compare a protocol change or to test whether better task routes help. These are separate experiments: mixing both changes cannot tell you which caused a difference. The benchmark is development tooling; it is not installed in consumer repositories and adds no required reader, cache or index format.

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
  --output /tmp/ssot-reading-protocol --repeats 3
python3 /tmp/ssot-reading-protocol/harness/benchmark/run.py \
  --output /tmp/ssot-reading-protocol --run-models
python3 /tmp/ssot-reading-protocol/harness/benchmark/run.py \
  --output /tmp/ssot-reading-protocol --report
```

The prepared output must be new. Preparation freezes both skill bundles, fixture trees, harness code, seed and execution order before any model calls. Run the frozen harness printed by the prepare command; it checks manifests before and after execution. The runner alternates arm order within each case's repetitions, shuffles the pairs and executes serially. Three repetitions of the default suite mean 30 attempts and 36 model turns, because `warm` has two turns. Use `--cases routed --repeats 1` for a two-attempt pipeline smoke test; this is not a performance conclusion.

To measure only the index, use the same candidate bundle in both arms. The coarse arm routes through product/architecture; the targeted arm links directly to the contract and states the related reading condition. Preparation rejects fixture differences outside `SSOT/README.md`. Both arms contain identical owner text and code.

```bash
python3 tests/benchmark/run.py --prepare --comparison index --candidate . \
  --cases routed warm --repeats 3 --output /tmp/ssot-reading-index
python3 /tmp/ssot-reading-index/harness/benchmark/run.py \
  --output /tmp/ssot-reading-index --run-models
```

An existing result, including failure, is retained when execution resumes. An interrupted attempt without a result blocks resume rather than silently restarting a partially changed repository; preserve that experiment and use a new output directory. There are no automatic retries or best-of selection. Use a new experiment for changed fixtures, harness code, source or environment. Do not overwrite a failed run after fixing its cause.

## Evidence and interpretation

Judge correctness first, then task completion time and total input/output tokens. Cache and tool statistics are diagnostic: they help explain variability and reading patterns, but do not decide efficiency or billing by themselves.

Each attempt gets an isolated writable repository and Codex home, a read-only skill bundle and necessary system/runtime files. Host projects, historical sessions, sibling attempts and fixture/oracle sources under the hidden home/temp roots are unavailable. Authentication is mounted for the CLI without copying it into the artifact. This controls accidental experiment contamination; it is not a sandbox for malicious code. Keep experiments under `/tmp` or `/var/tmp` so that the hidden-root boundary applies.

`plan.json` records hashes, inputs and order; `environment.json` records CLI/Python versions. Every turn retains its prompt, command/event stream, stderr, native session receipt, final answer, before/after files, summary and separate oracle verdict. The benchmark disables the historical recorder's per-event repository snapshots so observer work does not grow with every tool event. The separate [historical recorder](../run-performance-trials.py) still supports decision-order investigations that need those snapshots.

`report.md`, `report.json` and `report.csv` can be regenerated offline. They show all attempts, including quality failures, timeouts, infrastructure failures and unrun entries. Costs from failed turns remain in the data. Only pairs that both pass and have valid native per-turn usage enter the descriptive cost comparison; every excluded pair remains visible. This conditional comparison can still be biased when quality differs, so inspect quality counts first. Fewer than three usable pairs are pipeline observations only. Medians, ranges and paired changes do not establish significance or a general percentage gain.

| Metric | Meaning |
| --- | --- |
| Seconds | Full native turn, including model, tools and event recording; excludes preparation and post-run oracle |
| Input tokens | Native per-turn input, including cached input |
| Cached / uncached input | Cached input is reported separately; uncached is input minus cached |
| Output tokens | Native per-turn output, separate from input; not added into a synthetic score |
| Tool items | Completed command, file-change and MCP items exposed by the CLI |
| Tool output bytes | UTF-8 command text returned by the CLI; not disk reads, token counts or guaranteed untruncated output |

Resume's cumulative CLI usage is never substituted for native turn usage. Missing native records or an unexpected model exclude the cost comparison; they are not treated as zero. Cache/provider conditions remain uncontrolled, and cost is not converted to money. Inspection of final code and saved tool receipts complements the automatic oracle: passing code does not establish that every protocol branch was followed.

The fixture is deliberately small and synthetic, with one code domain and an adapter injected into the prompt. It does not measure installed-skill discovery, large production repositories, bootstrap/migration, decision capture, actual protected-departure approval, unrelated dirty-state costs, other models or statistical reliability. Repeated tuning against these cases risks overfitting; add independent project-shaped tasks before making broad claims. The [4.4 report](../trials-4.4.md) records the experiments actually run and their limits.

## Check the benchmark itself

```bash
python3 tests/benchmark/test_benchmark.py
```

CI checks deterministic fixture parity, mechanical documentation validity (except the deliberate broken route), positive and negative oracle cases, warm-state freshness, per-turn usage attribution and reports that retain failures. It never runs billable models. Preserve original evidence if the oracle is wrong; a changed oracle or harness is a new version, not permission to replace old results silently.
