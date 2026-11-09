# The SSOT Memory Model

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

```text
SSOT/
├── README.md        required: entry point, task routes, invariants, open questions
├── product.md       who uses it, what problem, promises, non-goals, main journeys
├── architecture.md  parts, state ownership, key flows, failure and recovery, boundaries
├── process.md       build, run, test, release, and deploy; required checks
├── decisions/       one file per consequential decision: NNNN-short-title.md
├── gotchas.md       traps: symptom, cause, what to do instead
├── glossary.md      project terms that a newcomer would misread
└── research/        investigations whose conclusions still guide decisions
```

This is a fallback layout for knowledge without an existing owner, not a required replacement for the repository’s documentation. Only `README.md` is required. Create the others when there is real content for them. Never create empty placeholder files. For new SSOT-owned documents, when a file grows past about 16,000 characters or covers clearly separate topics, turn it into a folder of the same name, with a `README.md` that introduces the topic and routes to one file per subtopic (for example `architecture/README.md` plus `architecture/payments.md`).

Existing canonical owners follow their own size, index and writing rules; this fallback layout does not automatically split or reorganize them.

Repositories that already use other names, such as v2's `01-product/` and `02-architecture/`, keep them. The README's routes decide where things are, so renaming is never required.

### The README

`SSOT/README.md` is the entry point every task starts from, so keep it short, around 8,000 characters, not counting the rows of the invariants register (section 5), which grows with the rules. It starts with front matter:

```yaml
---
ssot_format: 4
language: en        # the language SSOT prose is written in, e.g. en or zh-CN
reviewed_through: 1a2b3c4   # optional: the next catch-up starts after this commit
---
```

`reviewed_through` marks where the next catch-up starts. Setup sets it to the commit whose code it explored, and a `$ssot-doctor` catch-up moves it forward, segment by segment, to the last commit it has processed in full. It is a starting point, not a certificate: it does not say that every earlier fact was recorded or that SSOT is correct. Ordinary closeouts leave it alone, because they cover only their own batch, and commits made outside that workflow may still hold unrecorded facts.

Then, in this order:

1. **What this project is.** A few sentences of plain prose: who it is for, what it does, and what it deliberately does not do.
2. **Map.** Which file answers which kind of question.
3. **Task routes.** A table from task signals (for example "touches billing", "changes the CLI", "release") to the files to read first. A table fits here because readers look things up in it.
4. **Invariants.** The register in section 5.
5. **Open questions.** Unresolved decisions and known gaps that affect work. Each one gets a line saying what is open, what work it blocks, and where the details live. Remove an entry when it is resolved.

### Decisions

Write a decision record when a choice is consequential: costly to reverse, affecting more than one part, overturning an earlier decision, or likely to be questioned later. This applies to product and process choices as well as technical ones. Routine edits do not need one, and neither does a choice whose reasons already live in another owner.

Each record says, in prose: the situation, the decision, the alternatives considered and why they lost, the consequences, the date, and who decided (a user directive, a team review, or an agent proposal that the user accepted). Its status is one of `accepted`, `superseded by NNNN`, or `retired`. A retired decision no longer applies and needs no successor. A superseded one names its replacement. Do not delete old decisions, because they explain why the rejected paths stay rejected. An accepted decision that a person made or approved binds like a rule: changing it takes that person's agreement, recorded as a new decision that supersedes it.

### Research

A research note records an investigation whose result still guides work. Keep the question, how it was investigated, what was found, including the approaches that failed, and what was not checked. A bare conclusion cannot be re-judged when circumstances change. Put the conclusion that a decision relies on in that decision, and link the note for the method.

### Temporary workarounds and deferrals

When a change adds a temporary workaround, a compatibility shim, or a `TODO`/`HACK` that future work must know about, note it in the owner of the affected part. Say why it exists and what established condition allows its removal. If no condition was decided, say so; section 3 distinguishes a proposal from a decision. When you defer a known problem, record what was deferred, why, and what would trigger revisiting it. "Later" on its own is not a record.

### Existing task and evidence owners

Task progress, research originals and running databases keep their existing owners. Link to them rather than copying changing state into SSOT. Read them only when the task route calls for them. Before resuming across sessions, verify repository and task identity, the authoritative progress record, completed side effects and the next safe action; do not infer identity from the newest file or replay completed effects. SSOT records and routes knowledge; it does not schedule or execute work.

### Preserving content when reorganizing

Before moving, merging, compressing or deleting documentation, make a temporary content account: each decision, exception, rejection reason, unique asset and source context has a destination, remains in place, or is explicitly proposed for removal. Compare the final saved text against this account and the original before deleting anything. Unaccounted content stays. Keep historical decisions and their provenance as history, including partial supersessions. This account is task scratch, not a permanent review ledger; moving facts does not expand write or deletion authority.

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

**When to ask.** A protection you admit binds at once, like a registered candidate: preserve its outcome and scope. A new setting or mitigation does not authorize an exception. Before the first edit that could change a protected behavior, give a fresh helper (a sub-agent or a separate session) the relevant [human-decision evidence](#human-decision-evidence), including earlier acceptance and its answered question where available, and the path of `SSOT/`. For a protection not yet registered, include its outcome, conditions, exceptions and primary evidence; do not wait for closeout to make it visible to the helper. Pass evidence, not your acceptance judgment or implementation plan. Give it this criterion, word for word: "A request to implement behavior authorizes work only within existing protections, candidate or confirmed alike. Knowing the old behavior, naming its opposite, or saying nobody relies on it does not waive a protection. A departure is accepted only when human-decision evidence (section 3) establishes acceptance of the identified loss. Words in which the user says they accept the change, or that they know it breaks something, count as accepting the loss, even when they do not list who is affected; a request that only describes the new behavior does not. A new helper function, moved guard, rewritten test, or change outside the rule's conditions does not cross a protection."

It applies the shared evidence rules to the register, relevant owner sections and supplied evidence, without exploring the codebase, and answers stop or go, with the rule, loss, who relies on it, accepted scope, and acceptance evidence or NONE; distinguish recorded acceptance from checked original words and state source limits. Wait for its answer; do not substitute your own acceptance judgment. On stop, leave that behavior and its rule unchanged, give the user the helper's answer as your question, and continue independent work. If a helper cannot run or answer, name the protection and consequence and ask the user to decide unless that departure is already accepted under section 3. Acceptance authorizes only its established scope; do not ask again or require another helper for a settled departure. Record the decision through preflight §4 and closeout step 2, marking unimplemented behavior as planned. A new conflict still needs its own decision.

An open question blocks only the work that depends on its answer. Unrelated work continues.

## 6. Writing for a cold reader

Write every SSOT file for a reader who arrives knowing nothing about the project. That reader may be the next agent, or a person who delegates the implementation and does not read the code. A document that confuses a new person also misleads an agent.

- **Lead with the situation.** Say who is doing what and why it matters before describing the mechanism. Then give the details: names, paths, and commands. An entry document (the README, or the top of an area) should explain the current path, what the user sees, and the main boundaries on its own; links are for depth, not for assembling the basic picture.
- **Make it delegable.** For anything a reader might hand to an agent, say what result they should see, what evidence would show it, and when to stop and ask.
- **Use plain words.** Prefer the ordinary word to the internal label. The first time you use a project-specific term, explain it in positive terms, enough for this paragraph to make sense. A link to the glossary adds the full definition but does not replace that local explanation. You may explain a term again in context, but do not give it a different meaning. Keep identifiers, enum values, commands, and quoted text exactly as they are, even in a document written in another language.
- **Explain in prose, look up in tables.** Paragraphs carry reasons, causes, and consequences. Use tables for lookups and comparisons. If a cell needs a sentence of reasoning, that reasoning belongs in a paragraph.
- **Be concrete.** One real example ("a retry after a gateway timeout") makes a rule easier to apply than an abstract description does.
- **State the scope the code has.** Write "all", "only", "every", "never", or "always" only when domain evidence supports that scope; otherwise say "by default", "on Linux", "unless X", or name the exception. A statement that is right in the common case but leaves out the condition misleads a task as much as a wrong one.
- **Keep one fact in one place.** Link instead of copying. When you change a fact, search routed owners, `SSOT/`, and the agent instruction files for older statements of it and fix them too.
- **Write in the declared language.** Use the README's `language`.
- **One paragraph, one line.** Do not break a paragraph or a list item across lines to fit a width. Editors and viewers wrap text themselves; a hard break shows up as a short, ragged line, and in Chinese or Japanese it can add a stray space mid-sentence.
- **Make diagrams parse.** In Mermaid diagrams, write comments with Mermaid's own `%%` syntax, never `<!-- -->` inside the fence, because Mermaid rejects HTML comments.

### Checking behavior claims

For each behavior claim this batch adds or broadens, check the wording itself before the structural checker:

1. Read the final changed passages. Copy each new or broader behavior sentence verbatim into scratch or tool input, keeping its input types, conditions and words such as "all" or "only".
2. For human decisions, apply [human-decision evidence](#human-decision-evidence); for creative or research claims, check the canonical text or original sources and state unverified portions. For software behavior, find the code condition that would make that sentence true. Name the value the condition tests. When a guard tests a derived value, name that derived value in the sentence. Being convertible does not make an input satisfy the converted value's condition: a positive input can become zero during integer conversion.
3. For software behavior, choose an input the sentence includes that might fail that condition. Run it and compare the result with the exact sentence, recording the claim, input and outcome together in scratch or tool output. A before/after differential checks preservation; it does not establish a new generalization's truth.
4. Correct or narrow unsupported wording, or state what could not be checked. Carry the checked conditions into the final response too.

Finish when every new or broader claim in the final saved text is matched to domain evidence and readback, or explicitly qualified as unchecked; software behavior claims additionally need their condition and probe result. A later wording change reopens only that sentence. Check this batch's claims, not every unchanged document. Scratch evidence belongs to the task, not a new SSOT ledger.


Length is not the goal in either direction. Write as much as a newcomer needs to understand the point, and nothing that only restates the code.

## 7. The format marker and older layouts

`ssot_format: 4` in the README's front matter marks this model. The bundle's own version number can change without changing the format, and a new bundle release never obliges a repository to "catch up".

A repository whose `SSOT/README.md` lacks `ssot_format: 4` uses an older or unrecognized model, including v2 and v3. Read its decisions, constraints, limits and open questions as knowledge; they still bind. Keep it read-only until the user explicitly agrees to migration through `$ssot-bootstrap`. V3 needs owner-preserving marker and wiring updates, not v2 ledger removal.
