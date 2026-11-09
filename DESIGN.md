# Design: why SSOT Skill is shaped this way

This file records the design inherited from version 3 and the ownership changes in version 4, so that later changes do not quietly rebuild what it removed. How to change the protocol is in [CONTRIBUTING.md](./CONTRIBUTING.md#changing-the-protocol). What a consumer's `SSOT/` contains is in [memory-model.md](./skills/ssot-preflight/references/memory-model.md).

## The job

A coding agent starts every session without the history of the project. SSOT Skill gives each repository a small, maintained memory: what the project is for, how it works, which rules people decided, why things are the way they are, and where the traps are. The next agent reads it before working and updates it when something durable changes. The bundle's value is that this reading and updating cost less than the mistakes they prevent.

## What happened in v2

Version 2 grew from 0.8 MB of skills (2.50, June 2026) to 1.9 MB (2.86, October 2026), and its lint script grew from 50 KB to 400 KB of Bash. There were 36 protocol versions in four months. Most later commits reconciled clauses that earlier fixes had made inconsistent.

The repositories that used it showed the cost:

- None of the five repositories ever reached the protocol's own finish line (`converged`). One had 406 SSOT commits, and all 17 of its areas were still marked `gap` or `stale`.
- Status ledgers, histories, review records, and manifests made up 15–38% of the SSOT bytes. One `STATUS.md`, which agents had to read before every task, had grown to 213 KB.
- About a third of all commits in the heavy users changed only SSOT files.
- The governance did not keep the facts fresh. One product document still gave a schema version that the code had passed several migrations earlier.
- Documents meant for people filled up with the protocol's bookkeeping vocabulary, and readers said they could not follow them.

The cause was in how the protocol changed, not in any one rule. Each observed agent mistake became a new clause, a lint check, a template field, a version bump, and a catch-up task for every consumer. Each fix was tested on its own case. Nothing asked whether the duty belonged in a general protocol at all, or whether the whole still paid for itself.

## Principles retained in v4

1. **Memory, not verification.** SSOT keeps what helps the next task. Proof that one task works stays in its commit, pull request, or test run.
2. **Store only what the code cannot tell you.** Don't restate fields, versions, or configuration values. Explain intent, system relationships, decisions, rejected options, and traps.
3. **One required file.** `SSOT/README.md` is the entry point; every other file exists only when it has real content.
4. **People's rules are the one strongly governed thing.** Confirmed invariants cannot be changed by an agent, and every invariant links to its single explanation, inside `SSOT/` or another maintained repository-local owner. Since 3.5 this also covers rules an agent recovers from evidence that people protect them (a guarding test, a restoring fix): they bind until a person settles them, and a request that merely names the new behavior is not that person's approval, because the requester may not know the protection exists.
5. **Releases never create work for consumers.** The data format (`ssot_format`) changes only when old SSOTs would be misread. A new bundle version alone never asks a repository to catch up.
6. **Machines check only what machines can decide.** Links, anchors, the register's shape, sizes, and file paths that git says were deleted or moved. Truth and readability are reviewed by an agent, and the review says how far it went.

## Accepted direction: preserve uncertainty

On 2026-11-06 the user confirmed this project's design direction: “承认模糊，承认不确定，模糊的正确比坚决的错误要好得多。” Keep what is known, inferred, undecided, and unverified distinct, and state how far the evidence reaches. Do not invent confirmation or rationale to make a record look complete. Uncertainty blocks only the work that depends on resolving it; independent work continues. This accepted direction preserves honest limits and does not lower verification requirements.

## Why v4 changes the format

Repositories already have maintained design documents, machine-checked contracts, research, and follow-up systems. Moving all their durable facts into `SSOT/` can create duplicate authorities or discard the context that explains a decision. Format 4 makes `SSOT/README.md` the entry point and records the owner routes; a maintained document elsewhere in the same repository can remain the authority. Raw conversations, task artifacts, and runtime state keep their appropriate owners rather than becoming a second SSOT archive.

A user's confirmation, correction, rejection, or scope limitation can matter before implementation finishes. Closeout therefore also captures accepted durable decisions immediately and reads the saved passage back; batch closeout still reconciles the final behavior. The capture keeps the question answered, the source and words, the accepted scope, implementation state, and any unknown rationale. A later decision replaces only the part it actually changes.

Code history cannot recover all of that intent. Bootstrap and catch-up inventory accessible project-related AI conversation sources, recover the relevant question and answer with later corrections, and revisit appended portions of existing threads. Private raw transcripts stay out of the repository. A commit watermark covers commits, not chats; inaccessible sources and unexamined ranges remain explicit gaps. This is an agent workflow, not an autonomous background collector or a guarantee of zero omissions.

The format change makes old v3 installations unsafe writers of external-owner routes. Old v2 and v3 memory stays readable but read-only until an agreed, preservation-aware bootstrap migration. Reorganization must account for meaningful content before replacing its source with a pointer; structural success alone cannot prove that nothing was lost.

## Routine reading and branch costs

A routine task should pay for the knowledge it uses. Preflight checks for an entry point before loading the shared model and reads its using-memory sections first. Writing rules remain in that same model and are reached when writing is needed. Closeout keeps write gates and route selection in its entrypoint; batch reconciliation is disclosed separately so each immediate decision need not load it. A no-update closeout still compares relevant owners, and structural changes still require the checker. Retained skill instructions are reused until an observed update or context loss; each new task refreshes the project entry and relevant owners, including dirty content. This introduces no persistent cache or review ledger. These choices reduce required reading on some paths without deleting the longer paths. Whole-task measurements and counterexamples belong in [the performance trial report](./tests/trials-4.2.md).

## What was removed, and what it would take to bring it back

The following left the bundle in 3.0. The full v2 implementation is frozen at the `v2-final` tag and installable with `install.sh --ref v2-final`:

- per-area coverage states, completeness checklists, the Q01–Q21 matrix, and `converged` certification;
- the `STATUS.md` and `HISTORY.md` ledgers, review archives under `.bootstrap/`, and `_manifest.md` inventories;
- tracking baselines advanced after review, and the obligation to audit after every protocol release;
- the 400 KB lint script and its prose-pattern checks.

Bringing any of these back needs what v2 never had: a failure seen in real use that v3 cannot handle, a trial that shows the addition helps on whole tasks, and a place in the [budget](./CONTRIBUTING.md#protocol-budgets).
