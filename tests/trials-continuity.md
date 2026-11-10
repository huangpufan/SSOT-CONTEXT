# V2 knowledge preservation and decision continuity

These trials complete the next bundle-local verification slice identified by the [evolution review](../docs/evolution-review-2026-11-10.md). They run the unchanged 4.5 skill bundle from `590977a`. No agent protocol or consumer format changes are made on the strength of these observations. They are scoped behavior evidence, not certification of all repositories or histories.

## Requirements and cases

The migration and capture protocols already require content preservation, original authority, continuation from a saved record, and partial rather than wholesale replacement of decisions. The fixture and independent host-side checks derive from those requirements, not from the subject's final answer. [continuity_cases.py](continuity_cases.py) supplies the cases through the existing [native runner](run-migration-trials.py).

| Case | Transition and observed surface |
| --- | --- |
| `v2` | Committed v2 memory → agreed migration → existing owners, current entry and executable check. Unique facts begin in STATUS, HISTORY, a bootstrap review and a manifest. |
| `mixed-writers` | Migration requested while an enabled writer remains on 2.86 → refuse migration without changing repository contents. |
| `partial` | Existing accepted rule → accepted report-format replacement → later correction of only unattended reports. Two actual native turns share a session; each must save and return the updated owner text before writing the dependent plan. |
| `capture-readonly` | An accepted choice arrives together with a strict read-only restriction → keep the choice operative in the response and report the recording gap without changing files. |
| `v2-interrupt` | Agreed migration starts → checkpoint plus changed memory → signal the recorder's own live child → new session/home reads the persisted checkpoint and actual tree → finishes preservation and verification. |

The v2 fixture carries confirmed and candidate rows, two historical apex-maxim placement states with different human evidence, an accepted but unimplemented offline-export directive, a one-time pilot choice, a rejected publication proposal, an open adjudication and a platform-verification gap. Its old decision metadata distinguishes accepted/superseded from implementation status. Migration must retain these meanings in their owners after removing the bookkeeping, keep existing owner paths and shared instruction identity, repair inbound links/tooling, and leave the review watermark unchanged. A new version alone does not authorize a history catch-up.

The correction fixture has a canonical owner outside SSOT. The accepted plain-text report choice changes to allow Markdown, then only the unattended portion changes back. Read-only checking, checked-scope reporting, interactive Markdown permission and the product-notification exclusion stay intact. Original questions, all three source IDs and exact user words must remain. The final plan is still planned work; there is no product implementation in this fixture.

## What ran

All live turns request `gpt-6.1-terra` with medium reasoning through Codex CLI 0.167.0 on Linux. The runner freezes the bundle, fixture, prompt and harness, prechecks the starting memory with the actual checker, and hides host histories, unrelated projects and the oracle. Current adapter instructions are supplied to these new cases. Helpers are unavailable; no new mining is requested, and newcomer review is the subject's own. Live calls require `--run-models`; CI runs only deterministic fixture/oracle/recorder checks.

```bash
python3 tests/test-migration-trials.py
# Preparation only; a new directory is required for every attempt.
python3 tests/run-migration-trials.py --bundle . \
  --output /tmp/ssot-v2-precheck --case v2
# Opt-in native execution. Replace the case for the other rows above.
python3 tests/run-migration-trials.py --bundle . \
  --output /tmp/ssot-v2-live --case v2 --run-models
```

Five experiments use seven native turns: six finish and one is deliberately interrupted. V2 conversion preserves the original rule authority, including unknown human authorship as candidate, and registers the recovered offline directive as confirmed. Pilot decisions retain accepted/superseded and unbuilt states without becoming extra invariant rows. Ledger facts move to existing owners, question/gap IDs remain, both instruction entries still share their owner, and the repaired wrapper actually reports a checker PASS. Direct inspection confirms the timeout/late-receipt rationale, offline scope, audit-tail completion condition, platform limit and rejected proposal remain in context.

The partial-correction experiment preserves both unaffected rule rows exactly and keeps all source words in the existing owner. Returned tool output contains each newly saved quote before the corresponding plan change appears in event-boundary snapshots. The final register retires the original universal plain-text row and carries interactive Markdown and unattended plain text in confirmed successor rows. The saved plan reflects both modes and explicitly remains unimplemented.

Both refusal controls leave all non-Git repository content unchanged. Their final answers disclose, respectively, the incompatible writer and the uncaptured read-only decision. This shows current-agent refusal in these scenarios, not control over an independently running old agent.

The interruption experiment observes SIGTERM of the owned child at native event 19, return code -15 and no completed turn. The saved state contains BOOTSTRAP, converted owners and removed ledgers; it is a post-rewrite, pre-finish interruption, not a power-loss simulation halfway through a filesystem write. A fresh native session and home receive only the checkpoint location, continued authorization and normal task boundaries, not the killed agent's reasoning or a coordinator-authored completion list. It examines the saved tree, verifies both record/implementation states and links, repairs incomplete text, runs the real checker wrapper and removes BOOTSTRAP. Final host-side checks pass. The interrupted receipt has observed token usage; it is retained as an interrupted attempt rather than relabelled a completed success or zero cost.

## Oracle repairs and evidence limits

The first v2 verdict was false because the host parser recognized only fixture-specific `INV-*`, `CLAUDE-MAXIM-*` and `CORE-RULE-*` rows, overlooking the legal `CAP-1` row. The first partial verdict assumed the changed row had to stay confirmed under its original ID, overlooking the permitted retired-row/successor representation. Neither constraint follows from the protocol or user requirement. The parser now accepts the documented ID grammar, and format checking selects current confirmed format rules while requiring original IDs/history and untouched clauses to remain. Counterexamples cover both repairs.

Original verdict files remain unchanged. Separate `verdict-oracle-repair.json` files record the corrected judgments and grader digest against the same saved artifacts; no model rerun was used to seek a better answer. The [machine-readable observations](continuity-results.json) retain original and repaired verdicts, frozen source/harness digests, native receipt hashes, per-turn usage and interruption metadata.

Fifteen offline self-tests cover original migration cases, legacy fixture validity, good conversions and missing knowledge, unknown-authority promotion, legal ID prefixes and successor rows, changed unaffected rules, capture ordering, incompatible-writer/read-only mutations, the interruption trigger, recorder ownership and the CI billing guard. The recorder's optional interrupt callback is unset for ordinary trials; the existing reading-benchmark self-tests still run without models.

Local Linux checks pass: 48 bundle checks, 118 checker regressions, 108 installer checks, fifteen migration/continuity self-tests, ten reading-benchmark self-tests, ShellCheck, Python compilation and changed-document link/anchor checks. Platform CI is a separate observation on the pushed commit.

Automatic checks of prose are bounded: keyword presence does not prove a complete causal explanation or clause admission. The concrete saved owners and plans were also read against the original fixture. They do not establish source completeness, behavior across models, unknown old-agent behavior, side-effect replay protection, SIGKILL/power-loss recovery, every migration interleaving, general cost improvement or real consumer adoption. Native setup/rule mining and host integrations retain their own evidence boundaries. The separate installer replacement defect remains open until its restricted edit scope is settled; these successful document trials do not close it.
