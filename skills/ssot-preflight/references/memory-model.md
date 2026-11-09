# SSOT Memory Model

This file owns what a repository's `SSOT/` contains, where each kind of knowledge lives, and how it is written. The other SSOT skills link here.

## 1. What SSOT is for

`SSOT/` is the repository's long-term memory. A new agent, or a person who delegates work to agents, should be able to read it and know what the project is for, how it works, which rules must not be broken, why things are the way they are, and where the traps are. With that, they can plan a change without first reconstructing the whole codebase. Its most important job is the rules: the architecture boundaries and product behaviors that only a person may change. Other changes still follow the repository’s authorization and ownership rules, including human-approved canon or domain facts maintained outside the invariant register and decision records.

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
- **How to work here.** The commands and checks for building, testing, releasing, and deploying, and the environment quirks they depend on.

Leave out:

- **Restated code.** Field lists, schema version numbers, function signatures, configuration values, and file inventories. Name the file that holds them instead. This content changes fastest, and a stale copy misleads more than a missing one.
- **Proof of one task.** Test output, exit codes, hashes, screenshots, and "verified on <date>" diaries. Keep a one-line pointer only when a long-term conclusion depends on that evidence. For example: "Rejected polling after the 2026-03 load test showed 40% CPU idle burn (see PR #812)."
- **History of edits.** Git already records who changed what and when.
- **Status about the documentation itself.** No coverage labels, review ledgers, or "last checked" stamps. A note on where a fact came from ("seen on the production server, 2026-09") is different: that is the fact's source, and it may stay.

## 3. Current, planned, and unknown

Readers act on what you write, so never present something planned as if it exists. Use plain labels near the claim:

- Describe current behavior in the present tense.
- Mark anything decided but not built, for example: "Planned, not built yet:… (see decision 0012)". Remove the label when it ships, or rewrite the text if the plan changes.
- Mark an agent's inferred follow-up, revisit or removal condition "Proposed, not decided", separate from the accepted choice. A reason for a decision does not establish a later action.
- Say what is unknown. "We have not verified this on macOS" is useful. Silence is not.

Use evidence appropriate to the claim: code, tests and runtime for software behavior; canonical material and the actual text for creative continuity; original sources, data and methods for research; human-decision evidence below for accepted choices. Code describes current implementation, not authorization to replace a person's rule. When a document and the code disagree, distinguish a stale description, a violation of an intended rule, and intent not yet implemented. Correct the stale description or report the implementation gap; preserve the rule unless human-decision evidence establishes its replacement, and then replace only the authorized part.

A claim about verification must say how far the verification went. "Unit tests pass" does not support "works end to end", and evidence from one platform does not cover another. A performance number says how and when it was measured. Keep four things apart: what was decided, what the code does, what one run showed, and what is guaranteed in general.

### Human-decision evidence

A visible user exchange or supplied export establishes acceptance through the person's words together with the question or proposal they answer; a bare “yes” without that context establishes no scope. An existing formal decision in a canonical owner can also establish that a choice was recorded as human-established or accepted under that owner's recording protocol. Preserve that recorded standing, including `confirmed` for a lasting rule. Cite it as “recorded as accepted in <owner/section>”; distinguish this from original words checked in this task. If the original exchange is unavailable or unchecked, say so without downgrading or reopening the decision solely for that reason.

Judge the record by the owner's role and surrounding acceptance context. Missing dates or per-item signatures leave those fields unknown; they do not by themselves undo recorded acceptance. A filename such as `AGENTS.md`, a role label, an arbitrary AI summary, a behavior description, or a pending proposal alone establishes no accepted decision. An agent-written formal record may carry an established decision, but agent authorship cannot manufacture acceptance. If evidence conflicts about acceptance or replacement, keep the existing protection and report the conflict rather than settling it from current code.

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

A rule belongs here when it is a lasting constraint on future work, set by a person ("never add pop-up notifications", "a retry never charges twice", "no public release without approval", "every UI change gets a native screenshot") or recovered from evidence that people protect it (below). A one-time choice, such as a retention period or which library to use, is a decision: record it in `decisions/` or its owner, where it still binds and still needs the person to change it. Keep each row to one line; the register is read before every task.

- **confirmed.** A person established it, either by a direct instruction or by accepting a decision. Agents may change code, tests, and docs within the rule, but never its meaning, scope, or status. If a task conflicts with it, stop and ask the user. If reality already violates it, report the violation instead of rewriting the rule to match the code.
- **candidate.** An agent inferred the rule from evidence that people protect it. Follow it by default. When a task needs to depart from it, or its meaning is unclear in a way that matters, ask the user to confirm or drop it and record the answer; silence confirms nothing. That the code already behaves this way does not make it confirmed, and candidates are not put to the user one by one: each is settled when a task needs to depart from it.
- **retired.** It no longer applies. Keep the row so the history stays readable, and link the decision that retired it.

When a user states a lasting rule ("never X", "always Y", "from now on"), record it as a confirmed invariant with the user and date as its source. The explanation lives in the owner the row links to, inside the repository, including existing owners outside `SSOT/`.

**Recovering a rule from the code.** Many protected rules were never written down. Admit one as a candidate only when you can name the outcome it protects, the conditions under which it holds, and evidence that people protect it on purpose: a test that asserts the outcome for its own sake, a fix or revert commit that restored it, a guard whose comment or history says why, a promise in the user documentation, or a compatibility shim or migration that exists to keep it. A test's existence alone is not enough; it may pin an incidental detail, which a change may update. State the supported exceptions, if any. Exceptions and exclusions mark where this rule does not apply; their behavior is protected only with independent evidence meeting this section's admission rules. Give one concrete change that would violate the rule and one nearby change it permits. Search for evidence that contradicts its scope, and tell a legitimate exception from an existing violation. "No known exception" is acceptable, but it does not prove the rule holds everywhere. A rule people stated stays protected even where the code violates it; report the violation instead of rewriting the rule.

**When to ask.** Before changing protected behavior, read [departure review](protection-departure.md), including for newly admitted rules.

## 6. Writing for a cold reader

Read [writing rules](writing-memory.md) before writing.

## 7. The format marker and older layouts

`ssot_format: 4` in the README's front matter marks this model. The bundle's own version number can change without changing the format, and a new bundle release never obliges a repository to "catch up".

A repository whose `SSOT/README.md` lacks `ssot_format: 4` uses an older or unrecognized model, including v2 and v3. Read its decisions, constraints, limits and open questions as knowledge; they still bind. Keep it read-only until the user explicitly agrees to migration through `$ssot-bootstrap`. V3 needs owner-preserving marker and wiring updates, not v2 ledger removal.
