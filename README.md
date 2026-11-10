<div align="center">

# SSOT-CONTEXT

The project was previously named SSOT-SKILL. Existing skill names remain compatible; see [rename compatibility](./INSTALL.md#project-rename-compatibility).

**Maintained context. Protected human choices.**

[![CI](https://github.com/huangpufan/SSOT-CONTEXT/actions/workflows/ci.yml/badge.svg)](https://github.com/huangpufan/SSOT-CONTEXT/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE) [![Agents](https://img.shields.io/badge/agents-70%2B-purple)](#supported-agents) [![Stars](https://img.shields.io/github/stars/huangpufan/SSOT-CONTEXT?style=social)](https://github.com/huangpufan/SSOT-CONTEXT/stargazers)

[English](./README.md) · [中文](./README.zh.md) · [Install guide](./INSTALL.md) · [Protocol version](./VERSION) · [Changelog](./CHANGELOG.md)

</div>

SSOT-CONTEXT helps agents maintain long-term context for development repositories and explicitly declared research, creative, personal or organizational spaces. **Each fact or record has one maintained owner; human decisions keep their scope and authority.** An entry routes the next task to relevant owners rather than requiring each session to reconstruct the history.

It began with a development promise: people define invariants, and agents evolve code within them. API compatibility, tenant isolation and never charging twice on a retry stay protected. That workflow remains available under consumer format 4; a bundle upgrade does not require migration.

General spaces use consumer format 5 and an explicitly wired entry, retaining existing owners and directories without requiring Git or a unified root. The agent distinguishes facts, hypotheses, accepted choices, preferences, experiences and changing state. An authorized experience record can be preserved for its own sake; a personality inference or research hypothesis does not become a protective candidate rule.

**SSOT** means **Single Source of Truth**: each maintained item has one owner; other documents link to it. The bundle provides four primary skills, two compatibility names, templates, a mechanical checker and an optional source-progress CLI. Your agent/host supplies execution, access and scheduling; skills do not collect unseen material in the background or guarantee erasure of every copy.

## Quickstart

### 1. Install in the repository you want to document

Open that repository in your coding agent and paste:

```text
Read https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/INSTALL.md and follow it.
```

The agent follows the [install guide](./INSTALL.md) to identify its installation target, install and verify all six skills, and merge lifecycle instructions into the repository's `AGENTS.md`, `CLAUDE.md`, or equivalent file. The default is **the current project only**, preserving an existing template language or choosing `en` / `zh` from your conversation. You can specify a different language or explicitly request a global installation in the same message.

<details> <summary>Prefer to install from a terminal?</summary>

You need **Bash 4+**, `git`, `curl`, and `python3`. On macOS, run `brew install bash` first and use `"$(brew --prefix)/bin/bash"` in place of `bash` below; the system Bash is too old.

Run this from the root of the repository you want to document:

```bash
set -o pipefail
curl -fsSL https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/install.sh | bash -s -- --quickstart --scope project --lang en
```

Use `--lang zh` for Chinese templates. `--quickstart` detects the agent and skips interactive prompts. If detection is ambiguous or you want to choose explicitly, append `--agent codex`, `--agent claude-code`, or another [supported key](#supported-agents).

The script installs the skills and prints a suggested instruction block. **It does not edit your agent-instructions file or create `SSOT/`.** Merge the block using [install guide step 4](./INSTALL.md#4-wire-the-skills-into-the-repos-agent-instructions-file), updating any existing SSOT block instead of duplicating it. Then continue below.

</details>

### 2. Restart the agent, then work as usual

Restart the agent session so it loads the installed skills and repository instructions. **Describe your task as usual; the agent applies the SSOT workflow automatically.** For example:

```text
Investigate and fix the login timeout, and verify the fix.
```

The repository instructions tell the agent when to act:

- **Before substantive work:** read `SSOT/README.md` and the few documents the task touches, check the rules people decided, and surface open questions that affect the task. If the repository has no `SSOT/` yet, the agent offers to create one; nothing is created without your agreement.
- **During work:** save a durable confirmation, correction, rejection, or scope decision when it is accepted, and read back the saved passage. Keep the question it answered and distinguish the accepted decision from what is implemented; batch closeout reconciles the remaining durable facts.
- **Before finishing or committing a substantive batch:** record those facts where they belong and remove the statements they replace. When nothing durable changed, nothing is written.

**Read Markdown directly, using its routes.** Preflight uses ordinary file tools such as `cat`, `rg` and `sed`; no dedicated reader is required. Task routes link to owner sections, say what question they answer and when to follow related constraints. Missing or stale routes fall back to the product and architecture entries and owner search. Layout, writing and protected-departure rules remain separate references, reached when needed. Retained instructions can be reused; each new task refreshes the entry and relevant owners, including uncommitted content. The opt-in [reading benchmark](./tests/benchmark/README.md) compares complete tasks, correctness and native token usage; fewer words alone do not establish a speedup.

You do not need to select or invoke a skill at every step. Creating the memory for a large repository may take more than one session; progress is saved in `SSOT/BOOTSTRAP.md` until setup is done. Then read the result at `SSOT/README.md`.

<details> <summary>Optional: request setup or a focused check directly</summary>

You can ask in ordinary language:

```text
Create an SSOT for this repository from its code and existing documentation.
Check the health of this repository's SSOT.
Catch SSOT up with the recent commits.
```

Naming a skill explicitly is also available, for example `Use $ssot-doctor to check this repository's SSOT.` This can help when diagnosing a missed trigger. It is an agent chat prompt; invocation syntax varies by agent.

</details>

## General context spaces

Install the same bundle, then explicitly name the subject and workspace to maintain. For example:

```text
Use this folder as the context space for this research project. Preserve the existing source files and findings owner; create only a useful entry and genuinely missing context.
```

With your agreement, Bootstrap uses format 5 and wires the actual entry through the selected-language `context-adapter.md`. Existing canonical owners remain in place. Top-level spaces can own cross-domain priorities and tradeoffs; child details, original materials, live state and task progress retain their owners. Routing never grants access or writes to another space. Ordinary undeclared chat, research answers and creative writing skip the workflow.

Known format-5 writers need bundle 5.0+. Older writers must discover a read-only entry and upgrade their bundle; do not downgrade data to satisfy an older checker. Existing development format 4 and independently authorized owner-recording workflows keep their normal rules. See the [space model](./skills/ssot-preflight/references/context-spaces.md) for ownership, authorized records and withdrawal/deletion distinctions.

For repeatable exports, the optional POSIX/Python [source contract and CLI](./skills/ssot-doctor/references/source-integration.md) tracks stable item/revision identity, declared owners and conflicts. Updates require saved-owner readback before acknowledgement; considered no-update outcomes need a reason. The agent interprets sources and updates owners; state retains metadata/locators rather than source prose. It can stop use and locate registered effects, including unfinished captures, without claiming every downstream copy. Single requested records need only normal owner write/readback. [Context trials](./tests/context/README.md) distinguish controlled behavior, installed discovery and source integration evidence.

The [native validation report](./tests/context/trials-5.0.md) retains actual outcomes, failures, frozen identities and costs. Observed developer token costs increased in the small paired sample; no performance improvement is claimed. Later metadata/checker fixes have separate mechanical evidence, and the report states remaining scope and writing-quality limits.

## How the agent selects skills

The agent selects from four skills according to the task and repository state; two more names keep older prompts working. This table explains the routing for reference.

| Situation | Skill | Purpose |
|---|---|---|
| Starting substantive repository or declared-space work | [`ssot-preflight`](./skills/ssot-preflight/SKILL.md) | Read relevant context and protected rules |
| Agreed setup, continuation or migration | [`ssot-bootstrap`](./skills/ssot-bootstrap/SKILL.md) | Build from the subject's evidence and existing owners |
| Accepting a durable decision, or finishing a substantive change batch | [`ssot-closeout`](./skills/ssot-closeout/SKILL.md) | Record what changed for good, or write nothing |
| Checking health, reviewing, or catching up on commits and conversation sources | [`ssot-doctor`](./skills/ssot-doctor/SKILL.md) | Run the checker, review against domain evidence, and report what was checked |
| Older prompts naming `$ssot-audit` or `$ssot-skill` | [`ssot-audit`](./skills/ssot-audit/SKILL.md), [`ssot-skill`](./skills/ssot-skill/SKILL.md) | Route to the skills above |

## What appears in your repository?

The installed skills are the instructions and tools. Your repository's `SSOT/README.md` is the entry to the memory they maintain:

```text
Your task → agent reads SSOT → does the work → updates SSOT if something durable changed
```

Only the entry file is required; the others appear when there is something true to put in them:

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

A new SSOT-owned document that grows large can become a folder of the same name; existing owners follow their local maintenance conventions rather than being split automatically. Existing maintained READMEs, design documents, and domain contracts can remain the owners, linked from `SSOT/README.md`. Reorganization preserves meaningful content and its reasons before replacing a source with a pointer. Research originals, task artifacts, and runtime state retain their appropriate owners.

## What keeps the memory useful?

**It stores what the code cannot tell you.** Intent, how the parts fit together, decisions with their reasons, rejected options, and traps. It does not copy field lists, version numbers, or test logs, because those go stale fastest and the code already holds them.

**It is written for someone new.** Plain words, the situation before the mechanism, prose for reasons and tables only for lookups. A person who delegates work without reading code should be able to follow it; so can the next agent. The rules live in the [memory model](./skills/ssot-preflight/references/memory-model.md).

**People's rules stay people's decisions.** Rules you confirm are listed in `SSOT/README.md`. An agent may work within them but never changes them; a task that conflicts with one stops and asks you.

**Checks state their limits.** The [checker](./skills/ssot-doctor/assets/scripts/ssot-check.py) finds broken links, a malformed rules table, a confirmed rule changed without a new dated source, oversized files, and mentions of code files that git says were deleted or moved. It cannot establish truth, readability or authorization. Doctor reviews the relevant [domain evidence](./skills/ssot-preflight/references/memory-model.md#3-current-planned-and-unknown), checks readability, and says how far it looked.

**Choose models for the question.** Doctor and mining can use [structural review](./skills/ssot-doctor/references/structural-review.md): states and paths, ownership graphs, mappings from requirements and decisions to implementation and evidence, and constraints with counterexamples. Methods are selected by scope and risk. Coverage concerns the explicit model and observed evidence. Missing sources, untested paths and unknowns remain gaps; model coverage does not prove all real needs were covered. This is neither full modeling for every task nor an automatic model checker.

**Maintenance follows the agent workflow.** Changes made outside that workflow are picked up when you ask for a catch-up. A long catch-up can take several sessions; each one continues from the last commit the previous one finished.

**Conversation recovery has a stated scope.** The agent running setup or catch-up discovers project-related conversation sources across AI products, recovers the original question, answer and later corrections, and revisits new content appended to old threads. Raw private conversations stay outside the repository. Source gaps remain explicit; a commit watermark does not establish conversation coverage. These skills do not run an automatic background collector or guarantee that every decision is captured.

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

Restart the agent afterward. Replacing the installed skills never changes `SSOT/` by itself. To uninstall, ask the agent to follow the guide's removal steps for the chosen scope, including checking for obsolete trigger instructions.

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

Choose the same key and scope used during installation. Agents sharing a skills directory also share the installed bundle, so removal affects that shared location. The command leaves your `SSOT/` documents and agent-instructions file in place; remove obsolete SSOT trigger instructions yourself if you stop using the bundle.

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
