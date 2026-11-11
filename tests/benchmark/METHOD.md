# Choosing evidence for a protocol decision

SSOT helps a new collaborator act from maintained knowledge without losing its authority, scope or history. The evaluation asks whether that collaborator finishes the right task, preserves the boundaries and leaves usable knowledge for the next person. Reading fewer words is useful only when those outcomes hold.

The suite has several lanes because they answer different questions. It has no overall score. Select the relevant paths before changing the protocol, including a nearby path that must stay unaffected. Keep the full acceptance contract even when an early attempt fails.

| Decision | Existing evidence lane | What it can establish | Important limit |
| --- | --- | --- | --- |
| Does routed knowledge lead to correct implementation? | [Reading benchmark](README.md): routed, unrouted, stale | Executable behavior and preservation across policy boundaries | Small synthetic delivery domain; injected instructions |
| Does a reader notice changed knowledge in a warm session? | Reading `warm`; context D04 | Dirty and untracked changes without moving HEAD affect the next action | One external writer; not a concurrency stress test |
| Does maintained memory let a stranger continue? | [Cold handoff](HANDOFF.md): reporting and editorial | Actual fresh consumer deliverable after a decision and scoped correction | Public synthetic tasks; semantic review remains necessary |
| Does a protocol add value beyond the documents themselves? | Cold handoff `plain` versus `baseline`/`candidate` | Same initial facts and ordinary entry pointer, with or without workflow/skills | Estimates the protocol on maintained documents, not all memory's value |
| Are protected outcomes preserved while unrelated work proceeds? | [Context trials](../context/README.md): D01/D02, hybrid and large-register conflict | Allowed progress alongside an identified protected conflict | A tie on a few cases cannot justify removing a safety boundary |
| Does the protocol stay out of unrelated work? | Reading `typo`; installed ordinary and large-register typo | Requested edit/creative result, mutation scope and observed extra reading | A command's potential search scope is not proof it returned memory |
| Can writing, setup and recovery continue correctly? | Context continuation/source trials; [migration](../trials-4.5.md), [continuity](../trials-continuity.md) | Owner preservation, partial success, process interruption, source identity and incompatible writers | Keep host, connector and protocol failures separate |
| Can the host actually discover what is installed? | Installed prompt probes and native installed trials | Actual skill catalog and instruction wiring at the launch root | A skill name quoted in AGENTS is not discovery; CLI behavior can change |

## Before the experiment

Write the user outcome, the decision this result can change and a counterexample. Separate the candidate mechanism from fixture or indexing changes. Freeze the task, fixture, expected behavior, harness, bundle and model before calls. Arbitrary policy values reduce guessing; they do not make public fixtures secret.

Choose a development task and an independent confirmation task before tuning. Confirmation should vary domain or task shape, not just reseed a number. Freeze the candidate before running confirmation. Once an outcome has been examined to change the design, that case is development evidence; a new frozen experiment does not erase this history. Reports must disclose earlier exposure and author/judge overlap. Neither model consensus nor a fixed percentage threshold decides adoption.

Calibrate the measurement before a matrix: a known-valid artifact must pass, a meaningful mutation must fail, and legitimate alternate prose/layout must remain valid. The cold-handoff lane also uses native ceiling, absent-decision and stale-decision consumers. If a floor consumer invents the right answer, the fixture does not discriminate memory use. Preserve calibration failures; fix their cause before interpreting product results.

## During the experiment

The common recorder observes the whole authorized workspace independently of its launch directory. It retains text for review plus byte hashes, file types, modes and symlink targets. It does not follow outside symlinks. Git internals and Python cache contents are excluded explicitly; repository identity requires a separate Git readback where relevant. Missing/unreadable evidence is not an empty successful snapshot.

Record requests, raw output, validated events, native session/model/usage, actual changes and final answers. A malformed event stream is an observer failure even when the process later completes. The recorder continues draining the already running process under its original timeout and waits for exit before the final snapshot; it does not silently replay or leave that process writing after reporting. Known native completion and complete observation remain separate facts.

Attempt transitions are: frozen inputs → new attempt → discovery → writer/native task → transferred artifacts → fresh consumer when applicable → mechanical adjudication → semantic review when required. Infrastructure failure, native incompletion, observer failure and wrong-model execution are separate from quality failure. A `started` receipt without final evidence means running or interrupted, not a completed infrastructure verdict. An existing attempt, including partial side effects, is never overwritten or automatically retried. New attempts need a reason and retain the old evidence. A semantic approval is bound to exact observations and artifacts; it cannot survive an artifact edit, including when regenerating the report. Identical review replay recovers a review/result write interruption; a changed review cannot replace the original.

## Make the next decision

Review actual task output first. Use exact executable contracts where possible; use artifact-grounded semantic review for standing, scope, meaningful history, routing and honest completion claims. Do not require a semantic ritual where the executable contract fully decides the result. A reported read is diagnostic; the final action is the outcome.

Retain failures and incomplete spend. Missing usage stays unknown. Compare cost only for correctly completed, comparable tasks with matching native model receipts. Show writer and consumer phases as well as the whole task, including failed attempts. Input includes cached tokens; time includes tool execution and observation. Neither is a billing claim. Do not turn a conditional cost improvement among survivors into a general improvement when quality changed.

For each finding, identify the first broken boundary: missing knowledge, undiscoverable owner, incorrect authority/scope, wrong action, lost handoff, host discovery, or defective observation. Change its owner, not the symptom. Run the thin path again, relevant counterexamples, then the predeclared confirmation. If the candidate adds cost or fails to change the observed problem, withdraw it. Keep rejected approaches and their evidence so the next maintainer does not repeat the same intervention.

These fixtures do not establish production reliability, every domain, every model, arbitrary interruption/concurrency or statistical superiority. New real incidents should add a discriminating case to the appropriate lane only when the current suite cannot distinguish the failure. Existing focused tests remain useful; more cases alone are not better coverage.
