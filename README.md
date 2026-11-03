<div align="center">

# SSOT Skill

**Humans define the invariants. Agents evolve the code.**

[![CI](https://github.com/huangpufan/SSOT-SKILL/actions/workflows/ci.yml/badge.svg)](https://github.com/huangpufan/SSOT-SKILL/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE) [![Agents](https://img.shields.io/badge/agents-70%2B-purple)](#supported-agents) [![Stars](https://img.shields.io/github/stars/huangpufan/SSOT-SKILL?style=social)](https://github.com/huangpufan/SSOT-SKILL/stargazers)

[English](./README.md) · [中文](./README.zh.md) · [Install guide](./INSTALL.md) · [Protocol version](./VERSION) · [Changelog](./CHANGELOG.md)

</div>

We believe coding agents will evolve toward automating design, implementation, and code review. SSOT Skill explores and adapts to that paradigm shift: **humans define a project's invariants. When a change to those invariants is proposed, humans assess whether it is correct and appropriate, then decide whether to accept it.** Invariants are the promises an implementation must preserve: API compatibility, tenant isolation, or never charging twice on a retry.

Within those boundaries, agents do the work, supported by the **harness**: the tools, checks, and execution controls around them.

**SSOT Skill gives those invariants and decisions a durable home.** It maintains a version-controlled `SSOT/` directory, preserving the constraints and their rationale alongside architecture, decisions, and known pitfalls. Across sessions and agents, the work starts from the same explicit agreements.

**SSOT** means **Single Source of Truth**: each durable fact has one maintained home; other documents link to it. The bundle provides six skills, Markdown templates, and a local checker inside your existing coding agent. It maintains the shared knowledge; your harness and tests execute and verify the work.

## Quickstart

### 1. Install in the repository you want to document

Open that repository in your coding agent and paste:

```text
Read https://raw.githubusercontent.com/huangpufan/SSOT-SKILL/main/INSTALL.md and follow it.
```

The agent follows the [install guide](./INSTALL.md) to identify its installation target, install and verify all six skills, and merge lifecycle instructions into the repository's `AGENTS.md`, `CLAUDE.md`, or equivalent file. The default is **the current project only**, preserving an existing template language or choosing `en` / `zh` from your conversation. You can specify a different language or explicitly request a global installation in the same message.

<details> <summary>Prefer to install from a terminal?</summary>

You need **Bash 4+**, `git`, `curl`, and `python3`. On macOS, run `brew install bash` first and use `"$(brew --prefix)/bin/bash"` in place of `bash` below; the system Bash is too old.

Run this from the root of the repository you want to document:

```bash
set -o pipefail
curl -fsSL https://raw.githubusercontent.com/huangpufan/SSOT-SKILL/main/install.sh | bash -s -- --quickstart --scope project --lang en
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
- **During work:** notice facts that will outlive the task, such as a decision, a changed contract, a trap, or a rule you state.
- **Before finishing or committing a substantive batch:** record those facts where they belong and remove the statements they replace. When nothing durable changed, nothing is written.

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

## How the agent selects skills

The agent selects from four skills according to the task and repository state; two more names keep older prompts working. This table explains the routing for reference.

| Situation | Skill | Purpose |
|---|---|---|
| Starting a substantive repository task | [`ssot-preflight`](./skills/ssot-preflight/SKILL.md) | Read the relevant memory and the rules that bind the task |
| Creating, continuing, or migrating `SSOT/` | [`ssot-bootstrap`](./skills/ssot-bootstrap/SKILL.md) | Build the memory from the repository's code, history, and documents |
| Finishing a substantive change batch | [`ssot-closeout`](./skills/ssot-closeout/SKILL.md) | Record what changed for good, or write nothing |
| Checking health, reviewing, or catching up on commits | [`ssot-doctor`](./skills/ssot-doctor/SKILL.md) | Run the checker, review against the code, and report what was checked |
| Older prompts naming `$ssot-audit` or `$ssot-skill` | [`ssot-audit`](./skills/ssot-audit/SKILL.md), [`ssot-skill`](./skills/ssot-skill/SKILL.md) | Route to the skills above |

## What appears in your repository?

The installed skills are the instructions and tools. Your repository's `SSOT/` is the memory they maintain:

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

A file that grows large becomes a folder of the same name. Existing READMEs and design documents are input: their lasting facts move into `SSOT/`, and the originals point there, so each fact has one maintained home.

## What keeps the memory useful?

**It stores what the code cannot tell you.** Intent, how the parts fit together, decisions with their reasons, rejected options, and traps. It does not copy field lists, version numbers, or test logs, because those go stale fastest and the code already holds them.

**It is written for someone new.** Plain words, the situation before the mechanism, prose for reasons and tables only for lookups. A person who delegates work without reading code should be able to follow it; so can the next agent. The rules live in the [memory model](./skills/ssot-preflight/references/memory-model.md).

**People's rules stay people's decisions.** Rules you confirm are listed in `SSOT/README.md`. An agent may work within them but never changes them; a task that conflicts with one stops and asks you.

**Checks state their limits.** The [checker](./skills/ssot-doctor/assets/scripts/ssot-check.py) finds broken links, a malformed rules table, a confirmed rule changed without a dated approval, oversized files, and mentions of code files that git says were deleted or moved. It cannot tell whether a document is true or readable; Doctor reviews that against the code and says how far it looked.

**Maintenance follows the agent workflow.** Changes made outside that workflow are picked up when you ask for a catch-up. A long catch-up can take several sessions; each one continues from the last commit the previous one finished.

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
curl -fsSL https://raw.githubusercontent.com/huangpufan/SSOT-SKILL/main/install.sh | bash -s -- --list-agents
```

An installation path in the registry does not establish identical skill discovery or behavior across agent versions. Restart the agent after installation and verify that it can discover the skills.

## Update or uninstall

Ask your agent to handle updates through the same guide:

```text
Read https://raw.githubusercontent.com/huangpufan/SSOT-SKILL/main/INSTALL.md and update SSOT Skill for this agent in the current project. Preserve the template language.
```

Restart the agent afterward. Replacing the installed skills never changes `SSOT/` by itself. To uninstall, ask the agent to follow the guide's removal steps for the chosen scope, including checking for obsolete trigger instructions.

### Upgrading from 2.x

Version 3.0 keeps the memory and drops v2's certification machinery: area coverage labels, the `STATUS.md` and `HISTORY.md` ledgers, review archives, and catch-up audits after every release ([why](./DESIGN.md)). After upgrading, agents still read a v2 `SSOT/` but do not write to it until it is migrated. Repository scripts that call v2's `ssot-lint.sh` stop working until the migration repoints them. Migration is one agent-run commit with your agreement: ask "Migrate this repository's SSOT to v3." To stay on v2, install with `--ref v2-final`.

<details> <summary>Manual update and removal commands</summary>

For a project-local Codex installation, run from the consuming repository:

```bash
set -o pipefail
curl -fsSL https://raw.githubusercontent.com/huangpufan/SSOT-SKILL/main/install.sh | bash -s -- --upgrade --agent codex --scope project
```

To pin the frozen v2 protocol instead of the current release, add `--ref v2-final` to the install or upgrade command.

To remove it:

```bash
set -o pipefail
curl -fsSL https://raw.githubusercontent.com/huangpufan/SSOT-SKILL/main/install.sh | bash -s -- --uninstall --agent codex --scope project --yes
```

Choose the same key and scope used during installation. Agents sharing a skills directory also share the installed bundle, so removal affects that shared location. The command leaves your `SSOT/` documents and agent-instructions file in place; remove obsolete SSOT trigger instructions yourself if you stop using the bundle.

Bare `--upgrade` updates all detected installations in the current project and globally. Use the scoped form above when you want to update just one installation.

</details>

## Documentation and contributing

- [Install guide](./INSTALL.md) — agent-driven setup, instruction wiring, and network fallback.
- [Design](./DESIGN.md) — why the bundle is shaped this way, and what version 3 removed.
- [Changelog](./CHANGELOG.md) and [current protocol version](./VERSION) — what changed in the bundle.
- [Contributing](./CONTRIBUTING.md) — how to propose changes and run local checks.
- [AGENTS.md](./AGENTS.md) — instructions for agents maintaining **this bundle repository**.
- [Security policy](./SECURITY.md) — how to report a vulnerability.

## Star History

<a href="https://www.star-history.com/#huangpufan/SSOT-SKILL&Date"> <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=huangpufan/SSOT-SKILL&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=huangpufan/SSOT-SKILL&type=Date" /> <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=huangpufan/SSOT-SKILL&type=Date" /> </picture> </a>

## License

[MIT](./LICENSE) © [huangpufan](https://github.com/huangpufan)
