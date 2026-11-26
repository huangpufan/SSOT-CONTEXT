# Memory layout

```text
SSOT/
├── README.md        required: entry point, task routes, invariants, open questions
├── invariants/      optional: topic shards linked from README.md ## Invariants
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

`reviewed_through` marks where the next catch-up starts. Setup sets it to the commit whose code it explored, and [Doctor](../../ssot-doctor/SKILL.md#4-catch-up-on-past-commits) advances it only across contiguous reviewed history, including merges. It is a starting point, not a certificate: it does not say that every earlier fact was recorded or that SSOT is correct. Ordinary closeouts leave it alone, because they cover only their own batch, and commits made outside that workflow may still hold unrecorded facts.

Then, in this order (existing entries using another section order remain valid):

1. **What this project is.** A few sentences of plain prose: who it is for, what it does, and what it deliberately does not do.
2. **Map.** Which owner answers which question; link directly to it, tagging cold history so routine tasks skip it.
3. **Task routes.** Map recurring task signals to owner sections, the question each answers, and when to follow related constraints or another owner. Use a compact 3-column table or one-line bullets as routes grow, with searchable headings and direct section links; keep facts in their owners and never route routine startup to an unbounded chronological log. Add routes when they save discovery, not for every file. A long owner may have a local contents list; avoid chains of indexes. Keep routes current when owners move.
4. **Open questions.** Unresolved decisions and known gaps that affect work, written as concise one-line bullets naming what is open, what work it blocks, and where details live. Delete an entry as soon as it is resolved—never leave `[RESOLVED]` or strikethrough tombstones.
5. **Invariants.** The register in section 5.

### Decisions

Write a decision record when a choice is consequential: costly to reverse, affecting more than one part, overturning an earlier decision, or likely to be questioned later. This applies to product and process choices as well as technical ones. Routine edits do not need one, and neither does a choice whose reasons already live in another owner.

Explain the situation, choice, alternatives and why they lost, consequences, date and who decided. Keep the history so readers can recover rejected paths. Use `accepted`, `superseded by NNNN` (name its replacement), or `retired` (no successor required). An accepted choice binds until a person with authority over it revises or retires it. On handover check the [decision authority](memory-model.md#human-decision-evidence) and preserve the original attribution.

**Cold indexes.** When a cold directory (`decisions/`, `archive/`, `history/`, or concluded `research/`) keeps an index such as `decisions/README.md`, keep it lookup-only: one-line table rows (`ID/Date | Topic | Status | Link`) or compact one-line bullets (`<=120` characters) with no summary, rationale, or quote columns. Full explanations and excerpts stay in the linked cold files.

### Research

A research note records an investigation whose result still guides work. Keep `Status:` (`active`, `concluded — see NNNN`, or `superseded`) alongside the date, question, how it was investigated, what was found (including approaches that failed), and what was not checked. A bare conclusion cannot be re-judged when circumstances change. Put the conclusion that a decision relies on in that decision or topic owner, link the note for the method, and treat concluded or superseded notes as cold history.

### Temporary workarounds and deferrals

When a change adds a temporary workaround, a compatibility shim, or a `TODO`/`HACK` that future work must know about, note it in the owner of the affected part under `### Temporary workarounds` or labeled inline as `**Workaround (remove when <condition>).**`. Say why it exists and what established condition allows its removal, so it can be spotted and deleted once verified. If no condition was decided, say so; [section 3](memory-model.md#3-current-planned-and-unknown) distinguishes a proposal from a decision. When you defer a known problem, record what was deferred, why, and what would trigger revisiting it. "Later" on its own is not a record.

### Existing task and evidence owners

See [task continuation](task-continuation.md).

### Preserving content when reorganizing

Before moving, merging, compressing or deleting documentation, make a temporary content account: each decision, exception, rejection reason, unique asset and source context has a destination, remains in place, or is explicitly proposed for removal. Compare the final saved text against this account and the original before deleting anything. Unaccounted content stays. Keep historical decisions and their provenance as history, including partial supersessions, and keep cold targets recognizable under [context tiers](context-tiering.md#when-reading-has-become-costly). Preserve `<!-- ssot-source:... -->` provenance markers during compaction unless reconciling through `context-source.py`. This account is task scratch, not a permanent review ledger; moving facts does not expand write or deletion authority.
