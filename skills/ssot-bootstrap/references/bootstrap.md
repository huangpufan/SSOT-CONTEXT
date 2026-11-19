# Bootstrap: creating and migrating an SSOT

Templates for every file live in `../assets/templates/`. They are starting shapes, not forms to fill: delete any section that has nothing true to say.

## 1. Explore before writing

First make a preliminary inventory of existing canonical repository owners (section 4) and choose which knowledge each owns. Read enough to build a trustworthy initial README, answering from evidence:

- what the project is for and who uses it: READMEs, docs, product notes, issue templates;
- how it is built, tested, released, and deployed: build files, CI configuration, scripts, Dockerfiles, release notes;
- its main parts, where state lives, and how a typical request or command flows: entry points, directory structure, data stores, external services;
- the rules people already set: `AGENTS.md`, `CLAUDE.md`, contributing guides, ADRs, code review conventions;
- what history says: `git log` themes, large refactors, reverted changes, bug-fix commits that reveal traps;
- which outcomes users, clients, and integrations rely on staying the same: public promises, APIs, CLI behavior, saved data, import and export formats, and upgrades.

For first setup, discover relevant project conversation sources using [conversation catch-up](../../ssot-doctor/references/conversation-catchup.md). This initial inventory is not comprehensive reading and reconciliation: do those after saving section 2's README. Valid human-decision evidence already available may seed it. Report inaccessible sources as gaps; independent exploration continues.

Reuse this inventory in the [mining plan](mining.md). Save the entry before dispatch.

Note where the evidence is thin. That becomes an open question, not a guess. For a large repository, explore one part at a time and write as you go, so nothing depends on holding the whole repository in mind.

## 2. Write the README first

Start from `ssot-readme.md`. Set `ssot_format: 4` and the documentation language: the language the user asked for, or else the language of the repository's existing documentation. Write the project summary, the map, and task routes for the main kinds of work you saw in the history. Seed the invariants register like this:

- Classify human-established rules using [human-decision evidence](../../ssot-preflight/references/memory-model.md#human-decision-evidence), including accepted choices already recorded in canonical owners. Cite the evidence with its original-source limits; the explanation stays in its canonical repository owner (section 4).
- A rule you inferred from the code, the history, or a description of behavior in the user documentation is `candidate`, admitted through [`mining.md`](mining.md).

Save this entry point before comprehensive conversation recovery. Use verified project facts, owner routes and available human-decision evidence; mark unknowns. Say setup is in progress and which areas remain, linking `BOOTSTRAP.md` for ongoing work (section 5).

## 3. Fill only what has real content

Route to existing owners first. Fill only missing knowledge supported by evidence, updating an existing owner when authorized. Update README routes as each owner is saved. Create `product.md`, `architecture.md`, `process.md`, decision records or gotchas only where no suitable owner exists. When reconstructing an operating guide, save or link a worked example with the required inputs and prerequisites. Check it at the real entry point on safe inputs. Ask the cold reader for an executable action from the saved route, including a boundary case where order matters. Repair an unusable example and retry that request. Follow the memory model throughout: explain the system rather than restate the code, label anything planned as planned, and say what is unknown. Skip any file you cannot fill truthfully, and list it as an open question instead.

## 4. Keep existing owners and route to them

Inventory existing authoritative documentation before choosing new SSOT files. Preserve maintained repository owners, including design, memory, canon, control and decision-history documents. Link them from the README map, task routes and invariant explanations. Write new content there when authorized; create an SSOT owner only for knowledge without one. Leave generated, vendored, external-repository and runtime-owned material alone and link it where relevant.

If duplicated or obsolete documents need consolidation, propose the owner and exact changes first. Use the memory model’s preservation check before moving, compressing or removing anything. Agent startup rules remain in the instruction owner; project facts can remain in their established owner too. A source names the original file, section and date or commit so its authority remains traceable. Never delete a file without the user’s agreement; marker wiring in section 6 does not authorize edits outside the managed block.

## 5. Work across sessions

If setup will not finish in one session, keep `SSOT/BOOTSTRAP.md` from the `bootstrap-progress.md` template. As each area/source unit finishes, record its completed range, owner outputs, scratch checklist links and next action; keep detailed checklists in scratch. Record gaps and questions waiting for the user. Each session starts by reading it, verifying completed units and active writers, then resuming unfinished work rather than repeating completed units. Do not retry provider-blocked chunks merely on resume; continue independent units. Delete it when setup is complete.

## 6. Wire the instructions and finish

1. Add the block from `adapter-thin.md`, everything between `<!-- SSOT-CONTEXT:BEGIN -->` and `<!-- SSOT-CONTEXT:END -->`, to the repository's agent instruction file (`AGENTS.md`, `CLAUDE.md`, or the repository's equivalent). If the markers already exist, replace only the text between them. If legacy `SSOT-SKILL` markers exist instead, replace that entire block, including its markers, with the current block. This wiring step never edits outside the markers; moving project facts out of that file is section 4's job, done with the user's agreement.
2. Run `python3 ../ssot-doctor/assets/scripts/ssot-check.py SSOT`, with the path taken relative to this skill's directory. Fix every error. Where it warns that a mentioned file was removed or moved, correct each sentence that still describes current code.
3. Check what you wrote against domain evidence. Use mining’s [cold handoff](mining.md#check-the-result-with-a-fresh-reader) for the newcomer test and fix findings. A missing real example is a reported test gap. Unfinished mining or an unavailable independent reader stays in `BOOTSTRAP.md`.
4. Show the user every invariant you registered, the confirmed ones with their sources too (a rule found in an instruction file may have been written by an agent), plus the candidates and the open questions, and invite corrections. Do the same with the planned changes to documents outside `SSOT/` (section 4). Setup is complete once all of these have been put to the user; it does not stay open waiting for the answers. If some documents still repeat facts that SSOT now owns, add one open question to the README that names them; that question, not `BOOTSTRAP.md`, carries the pending work, and the exact edits are worked out once the user agrees. Answers that come later are recorded through `$ssot-closeout`. A candidate nobody answers stays a candidate; preflight asks about it when a task needs to depart from it.
5. Set `reviewed_through` in the README front matter to the commit whose code you explored. It marks where the next catch-up starts; it does not claim that you read every earlier commit. When the setup checks pass, replace the provisional notice with a short handoff identifying the completed setup scope and any unverified product behavior a newcomer could mistake for unfinished setup. Read back the sentence identifying the completed documentation scope before deleting `BOOTSTRAP.md` last.

## 7. Migrating a v2 layout to v4

Follow the [v2 migration](migration.md#7-migrating-a-v2-layout-to-v4).

## 8. Migrating v3 to v4

Follow the [v3 migration](migration.md#8-migrating-v3-to-v4).
