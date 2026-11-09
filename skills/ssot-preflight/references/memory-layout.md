# Memory layout

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

`SSOT/README.md` is the entry point every task starts from, so keep it short, around 8,000 characters, not counting the rows of the invariants register ([section 5](memory-model.md#5-invariants)), which grows with the rules. It starts with front matter:

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

When a change adds a temporary workaround, a compatibility shim, or a `TODO`/`HACK` that future work must know about, note it in the owner of the affected part. Say why it exists and what established condition allows its removal. If no condition was decided, say so; [section 3](memory-model.md#3-current-planned-and-unknown) distinguishes a proposal from a decision. When you defer a known problem, record what was deferred, why, and what would trigger revisiting it. "Later" on its own is not a record.

### Existing task and evidence owners

Task progress, research originals and running databases keep their existing owners. Link to them rather than copying changing state into SSOT. Read them only when the task route calls for them. Before resuming across sessions, verify repository and task identity, the authoritative progress record, completed side effects and the next safe action; do not infer identity from the newest file or replay completed effects. SSOT records and routes knowledge; it does not schedule or execute work.

### Preserving content when reorganizing

Before moving, merging, compressing or deleting documentation, make a temporary content account: each decision, exception, rejection reason, unique asset and source context has a destination, remains in place, or is explicitly proposed for removal. Compare the final saved text against this account and the original before deleting anything. Unaccounted content stays. Keep historical decisions and their provenance as history, including partial supersessions. This account is task scratch, not a permanent review ledger; moving facts does not expand write or deletion authority.
