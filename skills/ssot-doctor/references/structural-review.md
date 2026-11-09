# Structural review with small models

Use this within the agreed Doctor or mining scope when lifecycle failures, disputed ownership or missing links between requirements and evidence need more than sentence-by-sentence review. Choose only the methods that can change the judgment; this is not a new review for every task. Existing miners and challengers do this work within their assigned scope.

## Establish the boundary and sources

State the entity or outcome, repository version, relevant owners and exclusions. Derive expected behavior from contracts and accepted decisions; separately read code, guards, callers and recovery paths to discover implemented cases. These sources establish the review's denominator, not test counts. Keep normative requirements, implementation observations and verified results distinct. Label proposals and unknowns; implementation alone establishes neither authorization nor a protected rule. Apply the shared [evidence](../../ssot-preflight/references/memory-model.md#3-current-planned-and-unknown) and [admission](../../ssot-preflight/references/memory-model.md#5-invariants) rules.

## Choose the useful model

- **Lifecycle.** Name meaningful states and events. For each transition, identify its guard (the condition allowing it), resulting state, effects and responsible owner. Keep independent state dimensions separate when combining them would confuse delivery, reading and business completion. Inspect normal, error, cancellation, retry, cold-recovery and duplicate paths where applicable. Select important continuous sequences across boundaries, not just isolated edges: success followed by late failure, lost receipt followed by restart and retry, or repeated reports of an unchanged fact. Avoid the full Cartesian product or arbitrary state-count limits.
- **Ownership graph.** Trace entry routes to fact owners and responsibility hand-offs. Look for unreachable owners, isolated facts, duplicate authorities and broken replacement chains. A link's existence does not establish that it routes a reader to the relevant rule.
- **Sets and mappings.** Map scoped requirements and decisions to owners, implementation and evidence, allowing many-to-many relationships. Examine unmatched items in both directions and missing sources. Derive reported counts from enumerated distinct members, not prose estimates. A pending proposal is not authorized work; an implementation without a matching decision is not automatically wrong. Report the unresolved relationship.
- **Constraints and counterexamples.** Test mutual exclusion, invariants, progress conditions and boundary cases against their actual authority. Look for conflicting guards, missing exits and effects with no responsible owner. Try a violating case and a nearby permitted one; discovering a desirable constraint does not establish that people accepted it.

## Match evidence to paths

Read what each test changes and observes. For example, a stable-notification-identity claim needs a sequence that repeats the same unresolved fact through the production event boundary; changing only a report fixture can miss a new stage event that resets identity and timing. Also check a genuinely new blocker so deduplication does not swallow new work. Inspect or run the necessary boundary and sequence checks, and distinguish static reasoning, simulation and actual runtime evidence. Untested paths and unknowns remain gaps.

Keep models and working matrices in scratch or existing verification records, not a new permanent ledger or schema. Put stable semantics in their existing owners. Report findings, checked paths and exclusions: coverage concerns only the explicit model and observed evidence, never all real requirements. Sampling does not justify an invented statistical confidence bound.
