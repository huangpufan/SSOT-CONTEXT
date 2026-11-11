<div align="center">

# SSOT-CONTEXT

The project was previously named SSOT-SKILL. Existing skill names remain compatible; see [rename compatibility](./INSTALL.md#project-rename-compatibility).

**Maintained context. Protected human choices.**

[![CI](https://github.com/huangpufan/SSOT-CONTEXT/actions/workflows/ci.yml/badge.svg)](https://github.com/huangpufan/SSOT-CONTEXT/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE) [![Agents](https://img.shields.io/badge/agents-70%2B-purple)](#supported-agents) [![Stars](https://img.shields.io/github/stars/huangpufan/SSOT-CONTEXT?style=social)](https://github.com/huangpufan/SSOT-CONTEXT/stargazers)

[English](./README.md) · [中文](./README.zh.md) · [Install guide](./INSTALL.md) · [Protocol version](./VERSION) · [Changelog](./CHANGELOG.md)

</div>

A new agent session usually starts without the history of the work: what the subject is for, which choices people already made and why, and where the traps are. SSOT-CONTEXT gives that history a maintained home. A small entry document routes each task to the few documents that own the relevant facts, and the agent keeps those documents current as the work changes them.

It maintains two kinds of subject:

- **Development repositories**, the original use. People define the invariants, the rules or outcomes that must keep holding, such as API compatibility, tenant isolation or never charging twice on a retry. Agents change the code within them.
- **General context spaces** that you explicitly declare: a research project, a creative work, a personal life domain or an organization. Git and a single root folder are optional; existing folders and documents stay where they are.

**SSOT** means **Single Source of Truth**: each fact or record has one maintained owner, the document responsible for keeping it correct, and other documents link to it. Decisions people made keep their scope and authority. An agent works within them and asks before departing from one.

The bundle is a set of agent skills: four primary skills, two compatibility names, templates, a mechanical checker and an optional source-progress CLI. Your agent or host supplies execution, file access and scheduling. The skills act only when the agent loads them; they do not collect material in the background and cannot guarantee deletion of every copy.

## Two kinds of space

| | Development repository | General space |
|---|---|---|
| Entry | `SSOT/README.md` | The entry you name, usually a README in the space's folder |
| Format marker | `ssot_format: 4` | `ssot_format: 5` |
| Git | Used for history checks and catch-up | Optional |
| What it holds | Product promises, architecture, process, decisions, traps | Links to existing owners, plus facts, hypotheses, decisions, preferences, experiences and live-state pointers kept distinct |
| When it applies | Substantive work in the repository | Work in a space you declared; ordinary chat, research answers and creative writing do not trigger setup |

Existing development repositories keep format 4 and need no migration when the bundle upgrades. Writing to a format-5 space requires bundle 5.0 or newer. Upgrade every known writer; until then, a 4.5 bundle that discovers the entry treats it as read-only, but older wiring may not discover an entry at an arbitrary location, so an unknown installation remains a gap to report. Never convert the data back to format 4 to satisfy an older bundle.

## Quickstart

### 1. Install where the context should live

Open the repository, or the folder of the space you want to maintain, in your agent and paste:

```text
Read https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/INSTALL.md and follow it.
```

The agent follows the [install guide](./INSTALL.md) to identify its installation target, install and verify all six skills, and, for a repository, merge lifecycle instructions into its `AGENTS.md`, `CLAUDE.md`, or equivalent file. A general space is wired later, in step 3, once you have declared it. The default is **the current project only**, preserving an existing template language or choosing `en` / `zh` from your conversation. You can specify a different language or explicitly request a global installation in the same message.

<details> <summary>Prefer to install from a terminal?</summary>

You need **Bash 4+**, `git`, `curl`, and `python3`. On macOS, run `brew install bash` first and use `"$(brew --prefix)/bin/bash"` in place of `bash` below; the system Bash is too old. These are installer prerequisites; a general space itself does not need to be a Git repository.

Run this from the root of the project you want to maintain:

```bash
set -o pipefail
curl -fsSL https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/install.sh | bash -s -- --quickstart --scope project --lang en
```

Use `--lang zh` for Chinese templates. `--quickstart` detects the agent and skips interactive prompts. If detection is ambiguous or you want to choose explicitly, append `--agent codex`, `--agent claude-code`, or another [supported key](#supported-agents).

The script installs the skills and prints a suggested instruction block. **It does not edit your agent-instructions file or create any context documents.** That block is for development repositories: merge it using [install guide step 4](./INSTALL.md#4-wire-the-skills-into-the-repos-agent-instructions-file), updating any existing SSOT block instead of duplicating it. For a general space, skip it and continue with step 3.

</details>

### 2. Restart the agent, then work as usual

Restart the agent session so it loads the installed skills and project instructions. **Describe your task as usual; the agent applies the workflow automatically.** For example, in a repository:

```text
Investigate and fix the login timeout, and verify the fix.
```

The project instructions tell the agent when to act:

- **Before substantive work:** read the entry and the few documents the task touches, check the rules people decided, and surface open questions that affect the task. If the repository has no `SSOT/` yet, the agent offers to create one; nothing is created without your agreement.
- **During work:** save a durable confirmation, correction, rejection, or scope decision when it is accepted, and read back the saved passage. Keep the question it answered and distinguish the accepted decision from what is implemented; batch closeout reconciles the remaining durable facts.
- **Before finishing or committing a substantive batch:** record those facts where they belong and remove the statements they replace. When nothing durable changed, nothing is written.

You do not need to select or invoke a skill at every step. Creating the context for a large subject may take more than one session; progress is saved in `BOOTSTRAP.md` next to the entry until setup is done.

### 3. For a general space, declare it first

A folder is not treated as a context space until you say so. Name the subject and the location, for example:

```text
Use this folder as the context space for this research project. Preserve the existing source files and findings owner; create only a useful entry and genuinely missing context.
```

With your agreement, Bootstrap creates a format-5 entry, links the documents that already own each topic, and wires that entry into the agreed instruction file using the selected-language `context-adapter.md` template. Non-software setup does not require source-code mining or a Git repository, and originals are linked rather than copied into a new archive. Restart the agent after this wiring. From then on, work in that space follows the same before/during/finish steps as above.

<details> <summary>Optional: request setup or a focused check directly</summary>

You can ask in ordinary language:

```text
Create an SSOT for this repository from its code and existing documentation.
Check the health of this repository's SSOT.
Catch SSOT up with the recent commits.
```

Naming a skill explicitly is also available, for example `Use $ssot-doctor to check this repository's SSOT.` This can help when diagnosing a missed trigger. It is an agent chat prompt; invocation syntax varies by agent.

</details>

## How the agent selects skills

The agent selects from four skills according to the task and the state of the entry; two more names keep older prompts working. This table explains the routing for reference.

| Situation | Skill | Purpose |
|---|---|---|
| Starting substantive work in a repository or declared space | [`ssot-preflight`](./skills/ssot-preflight/SKILL.md) | Read the relevant context and the rules that bind the task |
| Agreed setup, continuation or migration | [`ssot-bootstrap`](./skills/ssot-bootstrap/SKILL.md) | Build from the subject's evidence and existing owners |
| Accepting a durable decision, or finishing a substantive change batch | [`ssot-closeout`](./skills/ssot-closeout/SKILL.md) | Record what changed for good, or write nothing |
| Checking health, reviewing, or catching up on commits, conversations and source exports | [`ssot-doctor`](./skills/ssot-doctor/SKILL.md) | Run the checker, review against domain evidence, and report what was checked |
| Older prompts naming `$ssot-audit` or `$ssot-skill` | [`ssot-audit`](./skills/ssot-audit/SKILL.md), [`ssot-skill`](./skills/ssot-skill/SKILL.md) | Route to the skills above |

**Reading uses plain Markdown and its routes.** Preflight uses ordinary file tools such as `cat`, `rg` and `sed`; no dedicated reader is required. Task routes link to owner sections, say what question they answer and when to follow related constraints. Missing or stale routes fall back to the main entries and an owner search within the authorized scope. Each new task refreshes the entry and relevant owners, including uncommitted content. The opt-in [reading benchmark](./tests/benchmark/README.md) compares complete tasks, correctness and native token usage; fewer words alone do not establish a speedup.

## What appears in your project?

The installed skills are the instructions and tools. The entry document is where the context they maintain begins:

```text
Your task → agent reads the entry and relevant owners → does the work → updates owners if something durable changed
```

In a development repository, only `SSOT/README.md` is required; the others appear when there is something true to put in them:

```text
 your-repo/SSOT/
 ├── README.md        What the project is, where to look for each task, the rules people decided, open questions
 ├── product.md       Who uses it, what it promises, what it does not do
 ├── architecture.md  The parts, who owns which state, key flows, failure and recovery
 ├── process.md       How to build, test, release, and deploy
 ├── decisions/       Why things are the way they are, including rejected options
 ├── gotchas.md       Traps that have already cost time
 ├── glossary.md      Project terms a newcomer would misread
 └── research/        Investigations whose conclusions still guide decisions
```

Existing maintained READMEs, design documents, and domain contracts can remain the owners, linked from `SSOT/README.md`. A new SSOT-owned document that grows large can become a folder of the same name; existing owners follow their local conventions rather than being split automatically. Reorganization preserves meaningful content and its reasons before replacing a source with a pointer.

A general space has no fixed folder layout. Its entry explains the space's purpose, scope and sensitive boundaries, links each existing owner and the question it answers, lists protected rules (or says none are known) and records open questions. Other files are created only for content that has no owner yet. A top-level space, such as one spanning several life domains or an organization's projects, owns its cross-domain goals and tradeoffs; details stay with each child. Original materials, live state and task progress keep their own owners.

## What keeps the context useful?

**By default it stores what the material cannot tell you.** Intent, how the parts fit together, decisions with their reasons, rejected options, and traps. It does not copy field lists, version numbers or test logs, because those go stale fastest and their originals already hold them. Original documents, private transcripts and assets stay with their owners and are linked rather than copied into a new archive. Records you authorize, described below, are the exception.

**It is written for someone new.** Plain words, the situation before the mechanism, prose for reasons and tables only for lookups. A person who delegates work without reading code should be able to follow it; so can the next agent. The rules live in the [memory model](./skills/ssot-preflight/references/memory-model.md) and the [writing guide](./skills/ssot-preflight/references/writing-memory.md).

**People's rules stay people's decisions.** Rules you confirm are listed in the entry. An agent may work within them but never changes them; a task that conflicts with one stops and asks you. A *candidate* rule is one the agent inferred from evidence that people protect an outcome; it is followed by default until you decide otherwise.

**Different kinds of material keep their meaning.** In a general space the agent keeps facts, hypotheses, accepted decisions, preferences and goals, experiences, and changing state apart. A research hypothesis or a guess about someone's personality never becomes a protected rule. A record you authorized, such as a journal entry kept for its own sake, can be preserved even when it does not guide a future decision, in your exact wording when you ask for that. Current values stay in their live source; the context links to it and says how to check it.

**Routes are not permissions.** Following a link to another space or repository lets the agent read within the scope you allowed; it does not grant write access there. Imported source text is evidence to interpret, never instructions to execute.

**Forgetting has distinct operations.** Stopping use, marking guidance as superseded, withdrawing permission, and physically deleting a file are different requests, handled separately. The agent can locate the references it registered; it does not promise deletion of backups, provider logs or copies it cannot reach. See the [space model](./skills/ssot-preflight/references/context-spaces.md#stop-using-supersede-withdraw-or-delete).

**Checks state their limits.** The [checker](./skills/ssot-doctor/assets/scripts/ssot-check.py) finds broken links, a malformed rules table, a confirmed rule changed without a new dated source, oversized files, and mentions of code files that git says were deleted or moved. For a format-5 space it checks the entry and the local owners it links directly. It cannot establish truth, readability or authorization. Doctor reviews the relevant [domain evidence](./skills/ssot-preflight/references/memory-model.md#3-current-planned-and-unknown), checks readability, and says how far it looked.

**Choose models for the question.** Doctor and mining can use [structural review](./skills/ssot-doctor/references/structural-review.md): states and paths, ownership graphs, mappings from requirements and decisions to implementation and evidence, and constraints with counterexamples. Methods are selected by scope and risk. Coverage concerns the explicit model and observed evidence; missing sources, untested paths and unknowns remain gaps. This is neither full modeling for every task nor an automatic model checker.

**Maintenance follows the agent workflow.** Changes made outside that workflow are picked up when you ask for a catch-up. A long catch-up can take several sessions; in a repository each one continues from the last commit the previous one finished.

**Conversation recovery has a stated scope.** The agent running setup or catch-up discovers related conversation sources across AI products, recovers the original question, answer and later corrections, and revisits new content appended to old threads. Raw private conversations stay outside the context. Source gaps remain explicit; a commit watermark does not establish conversation coverage.

**Repeatable source exports have an optional tracker.** For sources you export more than once, such as a notes app or chat archive, the optional POSIX/Python [source contract and CLI](./skills/ssot-doctor/references/source-integration.md) tracks each item's identity and revision, the owners it should update, and conflicts. An update is acknowledged only after the saved owner is read back. After an interruption, the agent re-inspects the item and reuses captures already written or receipts still valid, so finished work need not be repeated; an owner edited in between needs a new readback, and conflicts stay visible for reconciliation. The agent interprets the source and writes the owners; the tool stores metadata and locators, not source text. A single record you ask for needs no tool.

## Evidence and limits

The [5.0 native report](./tests/context/trials-5.0.md) records what actually ran for general spaces: research, creative, personal and mixed-authority cases, development protections, source interruption and recovery, and an undeclared creative task that correctly caused no setup or file change. It keeps failures, frozen versions and costs. In its small paired sample, developer token use on warm tasks increased by about 5–13%; no performance improvement is claimed. [Context trials](./tests/context/README.md) explain how the controlled, installed-discovery and source-integration evidence differ. These are small synthetic tasks, not proof of universal reliability, automatic background ingestion or discovery of every unlinked entry by old bundles.

## Supported agents

The installer contains installation paths for **70+ agents**, including Claude Code, Codex, Cursor, Windsurf, Gemini CLI, GitHub Copilot, OpenCode, and Cline. Examples of project-local locations:

| Agent | Installer key | Project skills directory |
|---|---|---|
| Claude Code | `claude-code` | `.claude/skills/` |
| Codex | `codex` | `.agents/skills/` |
| Cursor | `cursor` | `.agents/skills/` |
| Windsurf | `windsurf` | `.windsurf/skills/` |
| Gemini CLI | `gemini-cli` | `.agents/skills/` |

List all keys and installation paths without installing anything:

```bash
set -o pipefail
curl -fsSL https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/install.sh | bash -s -- --list-agents
```

An installation path in the registry does not establish identical skill discovery or behavior across agent versions. Restart the agent after installation and verify that it can discover the skills.

## Update or uninstall

Ask your agent to handle updates through the same guide:

```text
Read https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/INSTALL.md and update SSOT-CONTEXT for this agent in the current project. Preserve the template language.
```

Restart the agent afterward. Replacing the installed skills never changes `SSOT/` or a general space's documents by itself. To uninstall, ask the agent to follow the guide's removal steps for the chosen scope, including checking for obsolete trigger instructions.

Installation and upgrade keep previous entries as backups until replacement succeeds. Errors during replacement and INT/TERM cancellation trigger rollback per installation location; a lock prevents competing install, upgrade or uninstall operations there. Incomplete rollback or SIGKILL leaves recovery state that blocks reruns. Follow the [recovery instructions](./INSTALL.md#failed-or-interrupted-replacement) to inspect retained backups and distinguish incomplete replacement from a completed installation whose cleanup failed.

Use the guide's [upgrade transition checks](./INSTALL.md#check-the-transition-not-only-the-new-installation) for old instruction/tooling remnants, including custom calls to the retired 4.3 reader. A same-format bundle upgrade does not require rewriting project memory.

### Upgrading from 2.x or 3.x

Version 4.0 uses `ssot_format: 4` so maintained repository-local documents can remain authoritative outside `SSOT/`. Agents read v2 and v3 memory but do not update it until you agree to a preservation-aware migration: ask "Migrate this repository's SSOT to v4." All installations that write this repository must use v4 before migration.

Both migration routes reconcile old instructions (including unmarked directives), inbound links and retired tool calls. The v3 route keeps existing knowledge, owner paths and the record of the last reviewed commit; it does not run v2 ledger deletion. The v2 route extracts durable content before removing those ledgers. An interrupted agreed migration resumes from `SSOT/BOOTSTRAP.md`, checked against the actual tree. Migration needs your agreement and is one commit. To stay on v2, install with `--ref v2-final`; to retain v3, choose a v3 release with `--ref`.

<details> <summary>Manual update and removal commands</summary>

For a project-local Codex installation, run from the consuming repository:

```bash
set -o pipefail
curl -fsSL https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/install.sh | bash -s -- --upgrade --agent codex --scope project
```

To pin the frozen v2 protocol instead of the current release, add `--ref v2-final` to the install or upgrade command.

To remove it:

```bash
set -o pipefail
curl -fsSL https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/install.sh | bash -s -- --uninstall --agent codex --scope project --yes
```

Choose the same key and scope used during installation. Agents sharing a skills directory also share the installed bundle, so removal affects that shared location. The command leaves your context documents and agent-instructions file in place; remove obsolete SSOT trigger instructions yourself if you stop using the bundle.

Bare `--upgrade` updates all detected installations in the current project and globally. Use the scoped form above when you want to update just one installation.

</details>

## Documentation and contributing

- [Install guide](./INSTALL.md) — agent-driven setup, instruction wiring, and network fallback.
- [Design](./DESIGN.md) — why the bundle is shaped this way, and what version 3 removed.
- [Changelog](./CHANGELOG.md) and [current protocol version](./VERSION) — what changed in the bundle.
- [Migration trials](./tests/trials-4.5.md), [decision and interruption continuity](./tests/trials-continuity.md), and [installer recovery evidence](./tests/installer-recovery.md) — reproducible scenarios, observations and explicit limits, rather than a guarantee for every repository or failure.
- [Contributing](./CONTRIBUTING.md) — how to propose changes and run local checks.
- [AGENTS.md](./AGENTS.md) — instructions for agents maintaining **this bundle repository**.
- [Security policy](./SECURITY.md) — how to report a vulnerability.

## Star History

<a href="https://www.star-history.com/#huangpufan/SSOT-CONTEXT&Date"> <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=huangpufan/SSOT-CONTEXT&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=huangpufan/SSOT-CONTEXT&type=Date" /> <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=huangpufan/SSOT-CONTEXT&type=Date" /> </picture> </a>

## License

[MIT](./LICENSE) © [huangpufan](https://github.com/huangpufan)
