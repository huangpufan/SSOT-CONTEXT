# SSOT Memory Model

This is the development format-4 model, which remains supported for normal reading and writing. Declared general format-5 spaces use the conditional [space model](context-spaces.md); the shared decision-evidence and protective-rule definitions below retain their meaning.

This file owns what a repository's `SSOT/` contains, where each kind of knowledge lives, and how it is written. The other SSOT skills link here.

## 1. What SSOT is for

`SSOT/` is the repository's long-term memory. A newcomer should be able to find the project's goal, understand how the parts work, and decide what to do next from the relevant method, progress, preferences and decisions. The task owner keeps execution progress. Topic owners explain what still applies, why choices were made and where earlier attempts went wrong. Human-protected architecture boundaries and product behaviors bind every change in their scope. Other changes still follow the repository’s authorization and ownership rules, including human-approved canon or domain facts maintained outside the invariant register and decision records.

SSOT is memory, not a verification system. Domain evidence (section 3) remains authoritative for factual claims. Proof that one task works belongs in that task's commit, pull request, or test run, not in SSOT.

"Single source of truth" means one maintained **owner** for each fact. `SSOT/README.md` is the entry point and routes to owners; an owner may stay elsewhere inside the repository. Keep established canonical documents (for example `DESIGN.md`, `MEMORY.md`, a creative canon, control document or decision history) in place and link them instead of creating parallel SSOT copies. New knowledge goes to the existing relevant owner, or a new owner only where none fits. Routing does not grant write permission: external repositories, reference material and runtime stores are linked, not edited by this workflow.

Automatic upkeep depends on the agent loading these instructions and seeing the relevant input. It cannot recover unseen conversations or promise zero loss.

## 2. What to store, and what to leave out

Store a fact when all three hold:

1. The domain’s primary evidence and history cannot cheaply tell a reader this.
2. It would change a future decision or prevent a mistake.
3. It changes more slowly than people will maintain it.

Typical durable knowledge:

- **Intent.** Who the product serves, the problem it solves, its promises and non-goals.
- **System understanding.** The parts of the system and what each owns, which part holds which state, how a request flows, how failures are contained and recovered, and which boundaries must not be crossed. A reader only gets this by studying many files, so writing it down saves real work.
- **Rules and decisions.** Invariants set by people, decisions with their reasons, and the alternatives that were rejected and why. A rejected path is worth recording so nobody revives it by accident.
- **Traps.** Problems that cost real time, with their cause and the right approach.
- **How to work here.** Reusable methods, commands and checks. Explain when a method applies, how to tell it worked, and any reason or limitation a successor would need to reconsider it.

Leave out:

- **Restated code.** Field lists, schema version numbers, function signatures, configuration values, and file inventories. Name the file that holds them instead. This content changes fastest, and a stale copy misleads more than a missing one.
- **Proof of one task.** Test output, exit codes, hashes, screenshots, and "verified on <date>" diaries. Keep a one-line pointer only when a long-term conclusion depends on that evidence. For example: "Rejected polling after the 2026-03 load test showed 40% CPU idle burn (see PR #812)."
- **History of edits.** Git already records who changed what and when.
- **Status about the documentation itself.** No coverage labels, review ledgers, or "last checked" stamps. A note on where a fact came from ("seen on the production server, 2026-09") is different: that is the fact's source, and it may stay.

### Goals and preferences

Keep an enduring goal with the outcome it serves, its scope and any agreed success or stopping condition. A task-specific goal belongs with the task. Distinguish proposed goals and methods from accepted ones. For an authorized trial, keep its bounds and what would justify revisiting it.

A preference is an attributed default within a stated scope, including exceptions. A specific authorized choice for this task takes precedence without rewriting the default. Save an established preference in the authorized owner for that audience and scope. The invariant register is for binding rules. A one-off request or account of usual behaviour establishes no enduring preference by itself. Look for whose future choice the person actually settled. When defaults overlap, follow the agreed priority or exercise delegated judgment within scope. Preserve each holder's preference. A choice reserved to the holders remains open until they settle it. When preferences change, update only the applicable scope. Existing confirmed rules keep their standing until an authorized correction. Past experiences still describe what happened.

## 3. Current, planned, and unknown

Readers act on what you write, so never present something planned as if it exists. Use plain labels near the claim:

- Describe observed behavior in its actual scope. During a partial rollout, say which parts have changed when that affects the task.
- Mark anything decided but not built, for example: "Planned, not built yet:… (see decision 0012)". Remove the label when it ships, or rewrite the text if the plan changes.
- Mark an agent's inferred follow-up, revisit or removal condition "Proposed, not decided", separate from the accepted choice. A reason for a decision does not establish a later action.
- Say what is unknown. "We have not verified this on macOS" is useful. Silence is not.

When a choice takes effect or ends on a condition, put the condition and its agreed consequence where people choose the method or act on the preference. Record what governs in the meantime. At use, check the evidence for the affected scope. If the same receipt identifies incompatible subjects or outcomes, resolve its identity before relying on it. A review date opens a review; continuation follows the agreement. Deployment alone settles no policy. If the trigger or interim authority is uncertain, proceed with work valid in either case and leave the dependent choice open.

Use evidence appropriate to the claim: code, tests and runtime for software behavior; canonical material and the actual text for creative continuity; original sources, data and methods for research; human-decision evidence below for accepted choices. Code describes current implementation, not authorization to replace a person's rule. When a document and the code disagree, distinguish a stale description, a violation of an intended rule, and intent not yet implemented. Correct the stale description or report the implementation gap; preserve the rule unless human-decision evidence establishes its replacement, and then replace only the authorized part.

A claim about verification must say how far the verification went. "Unit tests pass" does not support "works end to end", and evidence from one platform does not cover another. A performance number says how and when it was measured. Keep four things apart: what was decided, what the code does, what one run showed, and what is guaranteed in general.

### Human-decision evidence

Use the person's own words and the question or proposal they answer. A self-contained statement can establish its own scope. A bare “yes” requires the question. An existing formal decision in a canonical owner can also establish that a choice was recorded as human-established or accepted under that owner's recording protocol. Preserve that recorded standing, including `confirmed` for a lasting rule. Cite it as “recorded as accepted in <owner/section>”; distinguish this from original words checked in this task. If the original exchange is unavailable or unchecked, say so without downgrading or reopening the decision solely for that reason.

Judge the record by its owner's role and the context of acceptance. Missing dates or signatures leave those details unknown. A filename, title, AI summary, observed behavior or proposal alone cannot establish acceptance. An agent can record a decision someone made. On handover, verify who can revise this choice, within which scope and from when. Execution duties alone confer no decision right. Credit each decision to its maker. If acceptance or replacement is disputed, preserve the protection and report the conflict. Current code cannot settle it.

When needed for that source record, you may separately label its actual capture or verification date, leaving an unknown acceptance date unknown. This date establishes source handling, not approval, authorization or supersession order; it is not a per-task timestamp requirement.

## 4. Layout

See [layout rules](memory-layout.md).

## 5. Invariants

An invariant is a rule that people decided and that the implementation must preserve: an architecture boundary, or a product behavior that users, clients, or integrations rely on. Changing one takes a person; work that keeps every invariant needs nobody's approval. The register in the README lists them:

```markdown
| ID | Kind | Rule | Explained in | Status | Source |
|---|---|---|---|---|---|
| INV-01 | product promise | A retry never charges twice | [Payments](architecture.md#retries) | confirmed | user, 2026-05-02 |
| INV-02 | process rule | The CLI keeps backward-compatible flags | [Process](process.md#compatibility) | candidate | inferred from the release notes |
```

**Kind** says what the rule protects. A *product promise* is something users rely on, an *architecture invariant* is a property the system must keep, and a *process rule* governs how people and agents work in the repository.

A rule belongs here when it is a lasting constraint on future work, set by a person ("never add pop-up notifications", "a retry never charges twice", "no public release without approval", "every UI change gets a native screenshot") or recovered from evidence that people protect it (below). A one-time choice, such as a retention period or which library to use, is a decision: record it in `decisions/` or its owner, where it still binds and still needs the person to change it. Keep each row to one concise line: `Rule` states one governing constraint plus its primary scope (full alias tables, flag matrices, rollout history, and rationale live in `Explained in`); `Explained in` holds one canonical owner section link; `Source` holds compact attribution, latest date, and optional short ref (e.g., `user, 2026-05-02; ADR-0014`)—never verbatim quotes or readback diaries, which belong in `Explained in` or cold history. Group a growing register by topic under searchable headings, and keep rules that span topics visible near the start of the register.

**Optional topic shards.** When an inline register makes the entry heavy to read (roughly 50+ rows), keep cross-cutting rules in `## Invariants` and move topic groups into `SSOT/invariants/<topic>.md` (or files with `ssot_register: shard` in front matter). Link each shard directly from a bullet list placed above cross-cutting rows under `## Invariants` with its topic scope (never a Markdown shard-index table—tables under `## Invariants` are parsed as the 6-column register and trigger orphan-shard errors); every `.md` file under `SSOT/invariants/` is treated as a shard, so do not place a folder `README.md` there. If a shard includes helper tables, place its register under an explicit `## Invariants` heading. Keep IDs unique across entry and shards, update relative `Explained in` links, and follow [preserving content](memory-layout.md#preserving-content-when-reorganizing). When an active shard itself grows past roughly 50 rows or 16,000 characters, split it by sub-topic or trim bloated `Source` cells to prevent tool truncation. Sharding is optional and keeps the same format.

- **confirmed.** A person established it, either by a direct instruction or by accepting a decision. Agents may change code, tests, and docs within the rule, but never its meaning, scope, or status. If a task conflicts with it, stop and ask the user. If reality already violates it, report the violation instead of rewriting the rule to match the code.
- **candidate.** An agent inferred the rule from evidence that people protect it. Follow it by default. When a task needs to depart from it, or its meaning is unclear in a way that matters, ask the user to confirm or drop it and record the answer; silence confirms nothing. That the code already behaves this way does not make it confirmed, and candidates are not put to the user one by one: each is settled when a task needs to depart from it.
- **retired.** It no longer applies. Keep the row with a link to the retiring decision (never delete it); retired rows may move to a linked cold shard (such as `invariants/retired.md` or a shard marked `ssot_tier: cold`) skipped on routine reads so active tables stay concise (follow [compaction boundaries](context-tiering.md#compaction-boundaries) before creating a cold shard for the first time).

When a user sets a lasting requirement ("never X", "always Y"), record it as a confirmed invariant with the user and date as its source. The explanation lives in the owner the row links to, inside the repository, including existing owners outside `SSOT/`.

**Recovering a rule from the code.** Many protected rules were never written down. Admit one as a candidate only when you can name the outcome it protects, the conditions under which it holds, and evidence that people protect it on purpose: a test that asserts the outcome for its own sake, a fix or revert commit that restored it, a guard whose comment or history says why, a promise in the user documentation, or a compatibility shim or migration that exists to keep it. A test's existence alone is not enough; it may pin an incidental detail, which a change may update. State the supported exceptions, if any. Exceptions and exclusions mark where this rule does not apply; their behavior is protected only with independent evidence meeting this section's admission rules. Give one concrete change that would violate the rule and one nearby change it permits. Search for evidence that contradicts its scope, and tell a legitimate exception from an existing violation. "No known exception" is acceptable, but it does not prove the rule holds everywhere. A rule people stated stays protected even where the code violates it; report the violation instead of rewriting the rule.

**When to ask.** Before changing protected behavior, read [departure review](protection-departure.md), including for newly admitted rules.

## 6. Writing for a cold reader

Read [writing rules](writing-memory.md) before writing.

## 7. The format marker and older layouts

`ssot_format: 4` in the README's front matter marks this model. The bundle's own version number can change without changing the format, and a new bundle release never obliges a repository to "catch up".

An entry with `ssot_format: 5` follows the [general space model](context-spaces.md). A known older v2 or v3 `SSOT/README.md` still binds through its decisions, constraints, limits and open questions; keep it read-only until the user explicitly agrees to migration through `$ssot-bootstrap` (v3 needs owner-preserving marker and wiring updates, not v2 ledger removal). Unknown or future formats stay read-only pending a compatible writer; do not offer a downgrade migration.
