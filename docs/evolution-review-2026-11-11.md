# Evolution review: preserve trust across continued work

SSOT-CONTEXT helps someone resume work without losing the subject's purpose, its people's choices or the reasons behind them. Its value depends on three things holding together: the right context is reachable, its meaning and authority survive updates, and keeping it useful costs less than reconstructing it. Adding more stored material or more rules is not, by itself, progress.

This review covers the direction from `6b05fe1` to `cae20ad`, with a clean starting worktree and matching remote main. It examines the current protocol routes, source adapter, template checks and published evidence, rather than claiming an exhaustive audit of every historical patch or consumer. [DESIGN](../DESIGN.md) owns the architecture; the [previous review](evolution-review-2026-11-10.md) and [5.0 report](../tests/context/trials-5.0.md) retain their original evidence boundaries.

## Direction and priorities

Versions 4.4–4.5 replaced the special reader with native Markdown navigation, measured whole tasks, and completed scoped migration and interruption paths. The installer then gained recoverable replacement. Version 5.0 extended the same ownership and human-authority model to explicitly declared general spaces, with a conditional source adapter. Recent installation and README changes made that broader purpose discoverable. Existing development format 4 remains supported without migration.

The strongest next step is to make these existing promises hold across successive operations. A correction can arrive after readback; a cold caller can present the same receipts in a different order; a valid development template says nothing about its general-space counterpart. These are reachable continuations of shipped behavior, not reasons to introduce another subsystem.

| Priority | Finding and consequence | Decision for this batch |
| --- | --- | --- |
| First | A conflicting source identity did not block its descendants. A later correction could be marked complete despite an unresolved predecessor. | Repair the source adapter's ancestor guard and exercise continuations through the public CLI. |
| First | Retrying completion with the same receipts in another order failed. Recovery depended on argument order rather than the saved evidence. | Compare receipt membership after all existing validity checks, preserving the original completed record. |
| Next | Bundle checks covered only development templates. Broken general instruction blocks and the wrong general format marker could pass CI. | Apply shared checks to both template families and languages, with negative cases. |
| Next | The README's universal knowledge-extraction wording omitted authorized records of experience and exact words. | Reconcile both READMEs with the existing general-space admission rule. |
| Later | Small synthetic tasks do not establish sustained usefulness, and large protection registers have not been measured here. | Collect representative longitudinal and large-register evidence before changing reading policy. |

The **Standards** pass found one confirmed coverage gap: `tests/test-bundle-shape.sh` omitted the general template family even though both families ship under the same template contract. Existing budget increases are documented release decisions, not an unapproved weakening found in this batch.

The **Spec** pass found three confirmed mismatches: the two source CLI behaviors contradict the existing [source contract](../skills/ssot-doctor/references/source-integration.md), and the README admission wording omits the existing [authorized-record boundary](../skills/ssot-preflight/references/context-spaces.md#what-the-material-means). The ancestor-conflict bypass is the highest-impact finding. Sustained consumer usefulness and large-register costs remain unmeasured opportunities, not additional confirmed defects.

## Discussion with Claude Code Fable

The user explicitly requested Claude Code Fable for this discussion. The recorded model was `claude-fable-5-1`; this task-specific choice does not change the repository's standing model policy. The initial read phase was interrupted by the coordinator to bound scope and duration, then resumed to produce findings. A subsequent exchange considered the coordinator's executable counterexamples and challenged the first recommendations. Fable's agreement is discussion evidence, not independent execution of those counterexamples.

Fable initially proposed adding format-5 exceptions beside development-only closeout commands and repeating skip conditions in the general adapter. The coordinator checked the actual branch routing: the skills already send format 5 to the general-space workflow, and the adapter requests substantive work while preflight defines the skip cases. Fable withdrew both proposals. No observed behavior failure justified repeating those rules or releasing 5.1 for them.

Both participants agreed on the four repairs above. The template gap came from Fable's review and was confirmed against the test script. The two source failures were reproduced by the coordinator. No additional default reading duty, template wording, format, installer behavior or consumer migration is introduced. The review does not upgrade a model recommendation into a new human-confirmed invariant.

## Implementation and evidence

The source adapter formerly checked a fixed list of relationship-conflict kinds on ancestors. Content-identity conflicts have a different representation and escaped that list. The guard now rejects any unresolved conflict on the selected ancestor chain and names the blocking revision. It does not reject unrelated items or legitimate selected branches merely because unselected sibling history remains present.

Completion formerly compared receipt lists by position. It now compares their membership only after checking source identity, current owner bindings, marker and file bytes, and coverage of affected owners. A successful replay returns the existing record without reordering its references. Changed bytes and new receipts cannot rewrite completed history.

| Transition or counterexample | Executed observation |
| --- | --- |
| Conflicting original → withdrawal successor, before inspection | A source with no captured owners still cannot use `no-update` to complete past the conflict. |
| Readback on a second-generation correction → original identity conflict | Targets, readback, completion and no-update refuse progress; the owner bytes remain unchanged. |
| Selected fork with a byte conflict → continuation | Selecting the branch does not clear its identity conflict or let a descendant dismiss it. |
| Conflict on one item → independent item | The unrelated item can still complete a legitimate no-update outcome. |
| Completed two-owner capture → reversed receipt order | Retry succeeds with the original saved record and owner bytes unchanged. |
| Completed capture → owner edit → old or renewed receipt | Stale evidence is rejected, and renewed evidence cannot replace the completed historical references. |
| Broken general templates in English and Chinese | Missing/reversed markers, a lifecycle route moved outside the managed block, and format 4 in a general entry all passed the old shape script and fail the new one. |

The source regressions ran against the released helper before repair: four affected test methods produced seven failing assertions/subtests, not seven distinct bugs. After repair, all 18 source contract tests and 12 independent source CLI tests pass. The earlier fork, successor, withdrawal and recovery cases remain active. The tests invoke separate real CLI processes with synthetic local files and check that source originals are unchanged.

The shape suite passes 56 checks. Its adapter validator checks exactly one ordered marker pair and all four lifecycle routes inside that block for both families and languages; both README template formats and language fields are checked. Eight isolated whole-bundle mutations compare the old and new scripts, so a passing helper test alone is not the evidence that general templates are covered. No budget was raised; runtime protocol remains 16,593 words. ShellCheck and whitespace checks pass. The unchanged checker passes 125 tests, and benchmark, migration and context self-tests pass 12, 16 and 11 tests respectively without model calls.

The README change explains the existing admission exception and links its owner; it adds no agent protocol rule. No new native behavior or performance trial was run for this batch, and no improvement in model compliance, latency or token cost is claimed. Local results observe Linux; publication and Linux/macOS CI must be checked on the pushed commit rather than inferred from these results.

## Work that remains valuable

A useful next experiment is sustained work in one explicitly authorized general space: resume an interrupted task, correct a source, replace only part of a decision, retrieve context after unrelated edits, and observe whether the next session reaches the right owner without inventing acceptance or repeatedly storing the same fact. Measure resulting owner quality and retrieval errors alongside reading and upkeep cost. Existing synthetic trials are a starting point, not a substitute for that observation. This batch does not modify another consumer or create a collection service.

Large invariant registers are another measurement target. The reading budget deliberately excludes their rows so important protections are not dropped to satisfy a size cap. Before changing routing, compare baseline and candidate on representative large registers, including a relevant rule far from the task's apparent area. A lower token count is useful only if the same protected outcomes remain visible. No new index or selective-rule policy is justified by this review alone.

Provider connectors, background collection, cross-machine recovery and deletion of inaccessible copies remain separate host responsibilities. Source progress and receipts prove known identity and saved linkage; they do not prove semantic truth, complete discovery, authority or external-owner transactions. The high-value direction is better evidence and reliable continuation within these boundaries.
