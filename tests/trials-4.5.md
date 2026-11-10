# 4.5: upgrading an existing repository

An installed new bundle and a correctly migrated consumer are different outcomes. This release closes a documentation gap between the v2 and v3 migration routes and makes upgrade boundaries executable. It does not promise automatic migration or introduce a release-triggered memory review.

## What changed and why

The v2 route searches all agent instructions and tool callers. The v3 route previously said only to replace the managed adapter block, without routing to those cleanup steps. It now shares section 7's instruction, inbound-link and tooling reconciliation, while explicitly excluding v2 ledger removal. The existing authorization and content-preservation rules still apply. A progress template can now name v3 migration rather than offering only v2.

The retired-tool step also distinguishes operations. A v2 mechanical check can move to the current checker while preserving its blocking behavior; a migration operation follows the migration protocol. The 4.3 `read-context.py` reader, removed in 4.4, instead moves to ordinary Markdown reading. Substituting `ssot-check.py` for every removed executable would be the wrong operation. The installation guide now distinguishes bundle upgrade, memory migration, same-format upgrades and retired-reader integrations.

These are existing upgrade responsibilities made reachable from the relevant branch, replacing the v3 route's managed-block-only wording and the overly broad retired-script replacement instruction. They belong in the general migration protocol because old workflow entries and tool callers can exist in any consumer. No ordinary preflight/closeout step is added. Runtime text grows by 33 words to 13,915 of the existing 14,000-word budget; consumer format stays 4. Agent behavior outside the migration branch was not retested as a whole.

## Portable scenarios

[run-migration-trials.py](run-migration-trials.py) builds a small v3 consumer with one confirmed rule, one candidate, an owner explaining the reason and exception, an open question, a fixed review watermark, unmarked v2 instruction remnants and an obsolete checker wrapper. `resume` adds an explicitly authorized migration checkpoint; this is a synthetic cold continuation, not a process-kill recovery trial. `migrate` starts with committed legacy memory and explicit migration agreement. `readonly` asks only for review and forbids every write.

Preparation makes no model calls. It freezes the bundle, fixture, prompt and recorder; checks that the starting memory is recognized as well-formed v3; and refuses an existing output directory. Live execution reuses the reading benchmark's isolated native transport: `gpt-6.1-terra`, medium reasoning, Codex CLI 0.167.0 on Linux, read-only source tools and an isolated session home. Helpers are unavailable; these are migration scenarios without new rule mining, and the newcomer review is not independent. CI refuses live model calls.

```bash
python3 tests/test-migration-trials.py
python3 tests/run-migration-trials.py --bundle . \
  --output /tmp/ssot-migration-precheck --case resume
# Use a different, new output directory for each billable observation.
python3 tests/run-migration-trials.py --bundle . \
  --output /tmp/ssot-migration-live --case resume --run-models
```

The output retains `plan.json`, frozen harness and bundle, native receipts, tool events, before/after files, checkpoints, model usage and `verdict.json`. Use `--case migrate` or `--case readonly` for the other scenarios. Evidence directories contain synthetic project data but native session streams are kept local rather than copied into the repository. Preparation and each live attempt use new directories; failures are never overwritten or silently retried.

The oracle checks owner bytes, both rule rows including sources/statuses, review watermark, the export question, unrelated credential policy, the exact current marked block, removal of legacy instructions, a genuinely running replacement wrapper, the real checker, final checkpoint absence and the allowed write set. Read-only uses complete non-Git before/after file equality. Seven self-tests reject unchanged stubs, changed authority/scope, stale instructions/checkpoints, moved watermarks, missing memory and unrelated writes, and test the CI billing guard. This is not a semantic judge of every possible paraphrase or proof that all migration branches were followed.

## Observations and limits

The first exploratory baseline already completed the mixed-remnant migration correctly under 4.4. The documentation gap is real, but that observation contradicts any claim that the old wording inevitably leaves remnants. A final frozen-harness baseline comparison and candidate scenarios are recorded separately; no statistical, speed or token-efficiency claim is intended.

| Final observation | Result | Seconds | Native input / output tokens |
| --- | --- | ---: | ---: |
| 4.4 baseline, cold continuation | All scoped oracle checks pass | 73.604 | 292,258 / 2,571 |
| 4.5 candidate, cold continuation | All scoped oracle checks pass | 74.674 | 308,185 / 2,790 |
| 4.5 candidate, agreed migration from committed v3 | All scoped oracle checks pass | 65.400 | 283,990 / 2,175 |
| 4.5 candidate, read-only review | All files unchanged | 55.504 | 153,974 / 2,000 |

The paired continuation fixtures are byte-identical before execution; only the bundle and its prompt path differ. The baseline bundle digest is `b4b41c93564f`, candidate `9995caa2e3b9`. [Machine-readable observations](migration-results-4.5.json) retain the full digests, every attempt including the excluded malformed fixture and exploratory baseline, native usage, receipt hashes and oracle results. The final four attempts complete using the requested model and preserve their frozen source manifests. Receipts show a successful checker-wrapper run before checkpoint removal and another check afterward in both candidate migrations. The subject's own report is not used as the oracle.

An early generated candidate fixture accidentally indented Markdown delimiters and headings. Its native run completed but failed owner/rule/write-scope checks while repairing that malformed input. Preserve that attempt as a fixture-producer failure, not a clean migration comparison. The generator now normalizes multiline literals before committing them, prechecks actual v3 recognition before model calls, and has a regression that requires two real register rows. The corrected fixture uses a new output directory; the original artifact and verdict remain unchanged.

Installer scenario 25 separately performs a scoped old-bundle upgrade. It verifies byte equality of existing memory, an unfinished migration checkpoint, a decision owner, instructions and a retired-reader caller; the shared instruction symlink survives, while the retired executable is removed from the replaced skill. This proves the installer does not silently rewrite consumer state. The preserved caller still needs the separately authorized integration reconciliation described above.

Local Linux validation passes 48 bundle checks, 118 checker regressions, 108 installer checks, ten reading-benchmark self-tests, seven migration self-tests, ShellCheck, Python compilation and diff whitespace checks. Exact-commit platform CI remains a separate release observation.

Full v2 ledger extraction, real process termination during migration, mixed writers that have not upgraded, source-conversation recovery, actual protected departures, cross-machine recovery, production consumer adoption and general task costs are not established by these scenarios. The [evolution review](../docs/evolution-review-2026-11-10.md) retains remaining goal work rather than relabelling these checks as complete migration coverage.
