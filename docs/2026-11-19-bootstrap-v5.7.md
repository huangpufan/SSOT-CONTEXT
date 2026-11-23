# How much work does it take to set up useful repository memory?

A repository with a two-line scheduling function previously used six helpers to document one policy. The 5.5 handoff preserved the scheduling decision but left setup open, partly because there was no real example of an approved departure to exercise. Previous mining experiments also found that repeating a whole area added little coverage, while checking exact wording caught lost exceptions and corrections could introduce new errors. [Earlier setup](2026-11-19-context-checks-v5.6.md#how-early-was-bootstrap-useful) · [Coverage experiments](../tests/trials-3.7.md) · [Correction experiments](../tests/trials-3.10.md)

## What changed

For a bounded unit with a usable existing owner, the setup agent uses its first reads to draft the exact rule and its owner explanation. An independent reviewer derives outcomes from sources before opening the draft. That reviewer can then challenge the proposal and check the text in the same session. New clauses and repairs require independent review. A fresh reader exercises the actual entry. Only after the answers are saved does the reader receive the source sample. Rebuilding a usable guide from a public interface, lower-level code and tests gets its own distributed mining unit. The writer checks a worked example at the real entry, then the reader has to recover the action from the saved route. Large or disputed units also use distributed mining. The first inventory and the README-before-dispatch check apply on both paths. [Mining protocol](../skills/ssot-bootstrap/references/mining.md)

Claude Code Opus and Antigravity Gemini Neon independently discussed the existing workflow and then challenged the proposed change. Opus favored combining the challenge with the final text check. Neon stressed independent source discovery and rechecking repairs because writers and reviewers can share the same mistaken assumption. Both identified the risk of showing the reviewer draft conclusions too early. This led to a source-only first brief, a check of the exact saved passages and escalation of the affected scope when coverage cannot be established. Their suggested percentage targets were proposals. The comparison below measures whole setup work and checks what a new reader can do.

## Installed comparison

The baseline is 5.6 at `4377d49`. Each writer received one ordinary setup request, the same project files and fixed Git history, an actual project-local installation, an isolated Codex home and access to native helpers. The scheduling case is a small policy fixture. The file-operation case uses the real linking tool and its five tests from that commit, wrapped as a standalone repository. The model did not have access to sibling runs or the evaluation program. Codex 0.170.0 receipts identify GPT-6.1 Terra for the writers and helpers. Reasoning settings and native receipt hashes are recorded per session. Final-state file checks covered the application, tests and original decision owners. The independent reader received the resulting project without the writer’s conversation or scratch files.

| Repository | Installed version | Helpers | Model responses | Input + output tokens | Uncached input | Seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| shift | 5.6 | 6 | 85 | 2,521,056 | 100,585 | 285.8 |
| shift | 5.7 | 2 | 46 | 1,358,429 | 76,414 | 150.7 |
| links | 5.6 | 7 | 111 | 3,991,511 | 228,289 | 426.6 |
| links | 5.7 | 4 | 68 | 2,098,597 | 90,800 | 249.0 |

Responses count distinct model responses with native usage, including tool-call loops and helper sessions. Each writer had one user request. Tokens are input including cache hits, plus output. The separate external handoffs, discussion and development attempts are outside the writer table and recorded below. Elapsed times run from native launch through return. Concurrent runs shared the host. Two cases with one writer per version and case cannot establish a typical saving or a billing estimate. [Session counts, cached input and intermediate attempts](../tests/benchmark/results/bootstrap-5.7.json)

## What the handoffs exposed

- **Policy and implementation.** A failed handoff keeps the previous assignee. A rotation team may take over only on a weekend support shift with both parties’ confirmation. The canonical policy remained in place. The function takes one confirmation flag and has no known callers in the fixture. An earlier compact run split the policy into three rows and marked two parts as candidates. The revised instruction tells the writer to keep the conditions of a recorded decision together and to preserve genuine attribution uncertainty. An unavailable historical example of an approved departure is reported as untested.
- **Public commands and recovery.** The first compact run documented the five tested filesystem behaviors but dismissed CLI option spellings as implementation detail. That omitted promises in the actual help. A later version recorded the required backup argument and the empty-plan shortcut. Its cold reader still could not say which check happens first. Direct execution of the real CLI established that an empty plan with `--apply` and no `--backup-root` exits 2. Supplying the option returns `already-linked`. Adding the entry order to the compact review instructions still produced a guide from which one reader could not reconstruct how to select two bases. These trials led to the usable-owner condition and the requirement for a worked example on the reconstructed-guide path.
- **The test handoff itself.** Early document-only transfers dropped `AGENTS.md` to avoid loading startup instructions. A reader followed a valid project link and found it missing in the test copy. The corrected harness transfers the owner, disables automatic startup-instruction loading and withholds installed skills and private notes. Both baseline and candidate received this correction. Earlier transfers remain in the results. Application setup and repository-memory setup can also be read as different questions. The saved entry now identifies the scope finished and the product behavior still unverified.

In the final policy handoff the reader retained the approved conditions, distinguished recorded approval from the unavailable exchange and identified the completed documentation scope. It left live enforcement open. With the same intact transfer the 5.6 reader got the policy right but could not establish setup completion. In the file-operation handoff both versions explained alias handling, preservation of originals, stale plans, the tested rollback and the boundaries of human approval. The 5.7 writer worked across four helper sessions, including source mining, challenge and a cold read, and exercised the real CLI with temporary installations.

An additional operator request originally named directories without their locations. Both readers used paths relative to the checkout in example commands despite the requirement for external directories. We retained those replies and gave two fresh readers the same valid sibling locations. Each returned two commands. Running their exact arguments on separate disposable trees planned 12 links without a backup, applied all 12, and returned `already-linked` on a repeat. Both readers correctly said the empty plan still requires the backup option. This proves the specified command handoff when path prerequisites hold. The standalone fixture contains live tool and test code from the repository but supplies disposable skill trees for command execution.

## Development and evaluation cost

| Development variant | Shift, responses / tokens | Links, responses / tokens |
| --- | ---: | ---: |
| compact-draft | 46 / 1,240,106 | 48 / 1,357,792 |
| source-check | 25 / 722,037 | 45 / 1,329,838 |
| scope-handoff | 40 / 1,156,952 | 63 / 2,336,654 |
| entry-order | 37 / 955,509 | 53 / 1,640,399 |

The twelve setup runs across six variants used 20,708,880 recorded tokens. Separate reader probes used 1,403,038, including the earlier transfers, and three neighboring native controls used 635,461. Together those native trials used 22,747,379 tokens including cached input. Two Sonnet attempts returned no design response. Two successful Opus turns and those two unsuccessful attempts reported a combined list-price estimate of USD 0.60. Neon returned two substantive replies without comparable token or price telemetry. Coordinator work is unmetered here.

## Adjacent cases

A separate continuation had a missing entry, a stale instruction to publish a lowercase filename, and no independent reviewer. It restored a useful entry from the authoritative `Report.csv` decision, withheld the unsupported inference and kept the checkpoint. A plan-only repository with conflicting decisions from two authorities selected distributed review and changed no files. These checks ran on development snapshots of the new routing. An existing v3 migration-resume trial also preserved the original owners, register standing and review watermark, updated its wrapper, and passed its 15 checks. The trials do not cover a large repository, every escalation path, cross-machine recovery or a real approved-departure example.

## Reproduce

Use Linux with the [native benchmark prerequisites](../tests/benchmark/README.md#prepare-and-run). From a checkout containing the fixture commit, export the baseline and run the command for each bundle and case with a fresh output directory. Omitting `--run-models` prepares the fixtures without calling a model.

```bash
baseline_dir=$(mktemp -d)
git archive 4377d49 install.sh VERSION skills | tar -x -C "$baseline_dir"
python3 tests/benchmark/bootstrap.py --case shift --bundle "$baseline_dir" --output /tmp/ssot-shift-56 --run-models
python3 tests/benchmark/bootstrap.py --case shift --bundle . --output /tmp/ssot-shift-57 --run-models
```

Repeat with `--case links` and new directories. Each live invocation records native writer and reader receipts. The links case also gives a separate operator the valid directory layout. To inspect a saved phase, run `python3 tests/benchmark/bootstrap_usage.py /tmp/ssot-shift-57/writer`. The [counter](../tests/benchmark/bootstrap_usage.py) reconciles acknowledged helpers, unique response IDs, per-response sums and closing usage. Compare the actual README, owner passages and reader answers with the original sources before interpreting cost. A green checker and the number of rows cannot establish coverage of the decisions or public behavior.
