<div align="center">

# SSOT-CONTEXT

**Maintained context. Protected human choices.**

[![CI](https://github.com/huangpufan/SSOT-CONTEXT/actions/workflows/ci.yml/badge.svg)](https://github.com/huangpufan/SSOT-CONTEXT/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE) [![Agents](https://img.shields.io/badge/agents-70%2B-purple)](#supported-agents) [![Stars](https://img.shields.io/github/stars/huangpufan/SSOT-CONTEXT?style=social)](https://github.com/huangpufan/SSOT-CONTEXT/stargazers)

[English](./README.md) · [中文](./README.zh.md) · [Install guide](./INSTALL.md) · [Protocol version](./VERSION) · [Changelog](./CHANGELOG.md)

</div>

A new agent session arrives knowing nothing about your project's history, rules, or past mistakes. SSOT-CONTEXT gives durable project knowledge a small, maintained home: one concise entry routes each task to the documents that own it, while protecting confirmed human decisions so agents work within them instead of quietly overwriting them. When you pause or hand off work, the agent updates the authorized task record so the next session can verify what actually happened before acting.

It works in two kinds of place:

- **Development repositories.** People define invariants—outcomes that must keep holding, such as API compatibility or never charging twice on a retry—and agents change code within them. The entry is `SSOT/README.md` (`ssot_format: 4`).
- **General context spaces you explicitly declare:** a research project, creative work, personal life domain, or organization. Git is optional, and existing folders and documents stay where they are. The entry is the document you name (`ssot_format: 5`).

The project was previously named SSOT-SKILL; fresh installs ship the four core lifecycle skills, while existing upgrades preserve the old compatibility shims (`--with-legacy-shims` for fresh opt-in; [details](./INSTALL.md#project-rename-compatibility)).

## Principles

- **One fact, one owner.** SSOT means Single Source of Truth: each durable fact has one maintained document responsible for keeping it accurate, and other documents link to it.
- **People's rules stay people's decisions.** Confirmed rules are listed in the entry. Agents work within them, never alter them on their own, and stop to ask when a task conflicts with one.
- **Keep daily reading small and history recoverable.** Hot task context, maintained topic owners, and cold historical records have different access costs; [tiering and reconciliation](./skills/ssot-preflight/references/context-tiering.md) handle consolidation and partial replacements without creating duplicate stores.
- **Keep kinds of material apart.** Facts, hypotheses, confirmed decisions, scoped [goals and preferences](./skills/ssot-preflight/references/memory-model.md#goals-and-preferences), authorized [experience records](./skills/ssot-preflight/references/context-spaces.md#what-the-material-means), and live state stay distinct.
- **Write for someone new.** Plain words, situation before mechanism, and explicit scope so the next agent or a non-coding decision maker can act on it ([writing guide](./skills/ssot-preflight/references/writing-memory.md)).
- **Routes are not permissions.** Agents check authorization before opening linked sources; actual file access is enforced by the host, and imported text is evidence rather than executable instructions.
- **Say what was checked.** The read-only [checker](./skills/ssot-doctor/assets/scripts/ssot-check.py) verifies structure (links, anchors, register shape, confirmed-rule edits, and optional `--owners` restricted subsets), never truth. Reviews state findings, coverage, and gaps.
- **Evolve from real context needs.** Improvements start from recurring long-term context needs and whole-task evidence rather than rule accumulation ([design direction](./DESIGN.md#accepted-direction-evolve-from-context-needs)).

## Quickstart

### 1. Install

Open the repository, or the folder of the space you want to maintain, in your agent and paste:

```text
Read https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/INSTALL.md and follow it.
```

The agent installs and verifies the skills in the current project and wires them into `AGENTS.md`, `CLAUDE.md` or the equivalent file. If the folder does not look like a code repository, it asks you once which mode to use. You can ask for another template language (`en` / `zh`) or a global installation in the same message.

<details> <summary>Install from a terminal instead</summary>

Requires **Bash 4+**, `git`, `curl` and `python3` (on macOS, `brew install bash` and use `"$(brew --prefix)/bin/bash"`). From the project root:

```bash
set -o pipefail
curl -fsSL https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/install.sh | bash -s -- --quickstart --scope project --lang en
```

The script installs the skills and prints an instruction block, but does not edit your instruction files or create context. Merge the block as described in [install guide step 4](./INSTALL.md#4-wire-the-skills-into-the-repos-agent-instructions-file), which also covers general spaces.

</details>

### 2. Restart the agent, then work as usual

Describe tasks normally. Four skills handle the workflow automatically:

- [`ssot-preflight`](./skills/ssot-preflight/SKILL.md) reads the routes, applicable constraints and relevant owners before substantive work. Long development entries are read by section.
- [`ssot-bootstrap`](./skills/ssot-bootstrap/SKILL.md) creates or migrates the context with your agreement. During repository setup, a writer and an independent reviewer can cover a bounded area with a usable existing guide, followed by a fresh reader. Areas that require reconstructing a guide across sources, and large or disputed areas, use distributed mining.
- [`ssot-closeout`](./skills/ssot-closeout/SKILL.md) saves settled goals, preferences and decisions as they happen. It uses the task record for requested handoffs and updates durable knowledge at batch end when something changed.
- [`ssot-doctor`](./skills/ssot-doctor/SKILL.md) checks health and catches the context up with work done outside this workflow.

You can also ask directly, for example "Check the health of this repository's SSOT" or "Catch SSOT up with the recent commits."

### 3. For a general space, declare it first

A folder is not treated as a context space until you say so:

```text
Use this folder as the context space for this research project. Preserve the existing files; create only a useful entry and genuinely missing context.
```

Ordinary chat, research answers and creative writing never trigger setup on their own.

## What appears in your project

In a development repository only `SSOT/README.md` is required; the other files appear when there is something true to put in them:

```text
 your-repo/SSOT/
 ├── README.md        What the project is, where to look for each task, the rules people decided, open questions
 ├── invariants/      Optional topic shards when the invariants register grows large
 ├── product.md       Who uses it, what it promises, what it does not do
 ├── architecture.md  The parts, who owns which state, key flows, failure and recovery
 ├── process.md       How to build, test, release, and deploy
 ├── decisions/       Why things are the way they are, including rejected options
 ├── gotchas.md       Traps that have already cost time
 ├── glossary.md      Project terms a newcomer would misread
 └── research/        Investigations whose conclusions still guide decisions
```

Existing maintained documents can stay the owners and are linked from the entry. A general space has no fixed layout: its entry states purpose, scope and protected rules, and links the documents that already own each topic. An unfinished general space links its own setup record. Several spaces can share a directory. Details are in the [memory model](./skills/ssot-preflight/references/memory-model.md) and the [space model](./skills/ssot-preflight/references/context-spaces.md).

A reader can answer a bounded lookup from the current authorized owner, update a single approved prose rule in place with on-disk readback, and split a large invariants register into optional topic shards (`SSOT/invariants/<topic>.md` or `ssot_register: shard`) checked across files by `ssot-check.py`. For deterministic commit-time checks across every agent without spending model tokens, see the opt-in [`tools/ssot-precommit.sh`](./tools/ssot-precommit.sh) guard ([setup](./docs/2026-11-24-install-maintenance.md#optional-zero-token-git-pre-commit-guard)).

## Limits

- **No background collection or host enforcement.** The skills act only when the agent loads them and sees the input; they cannot delete copies they cannot reach (Git history, backups, provider logs) or override host file permissions.
- **Decision authority, restricted sources, and selected checks.** Handovers follow the project's decision authority while preserving prior attribution and rationale ([decision evidence](./skills/ssot-preflight/references/memory-model.md#human-decision-evidence)). Restricted sources support metadata-only withdrawal ([source integration](./skills/ssot-doctor/references/source-integration.md#correction-and-withdrawal)) and scoped structural checks with `--owners` ([selected checks](./skills/ssot-preflight/references/source-retention.md#selected-mechanical-checks)).
- **Measured real-world gaps.** A 15-day audit of 386 real consumer sessions confirmed consistent preflight on code edits and 20 real catches of unauthorized confirmed-invariant edits, while exposing stale instruction blocks across upgraded workspaces, truncation on 200+ KB entries, and repeated preflight in spawned subagents ([Stage 5 real-session audit](./docs/2026-11-24-real-session-stage5-audit.md)).

## Supported agents

For Antigravity App, use `--agent agy`; project installation shares `.agents/skills` with Codex. The [maintenance guide](./docs/2026-11-24-install-maintenance.md#when-a-skill-appears-unavailable) covers App/CLI/IDE locations, child-repository discovery, and local symlink setup (`tools/link-local.py`).

The installer knows the installation paths for **70+ agents**, including Claude Code, Codex, Cursor, Windsurf, Gemini CLI, GitHub Copilot, OpenCode, and Cline. A known path does not prove identical behavior, so after installing, restart the agent and confirm it discovers the skills. To list every key and path:

```bash
set -o pipefail
curl -fsSL https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/install.sh | bash -s -- --list-agents
```

## Update or uninstall

```text
Read https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/INSTALL.md and update SSOT-CONTEXT for this agent in the current project. Preserve the template language.
```

After updating the skill files (or pulling a symlinked checkout), check and refresh the repository's managed instruction block via `curl -fsSL https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/install.sh | bash -s -- --check-block <AGENTS.md|CLAUDE.md>` and `--sync-block <file>` (or run `bash install.sh ...` from a local checkout), then restart the agent. Updating never rewrites your context documents or forces format-4 repositories to convert to format 5. Manual commands, uninstalling, interrupted-install recovery, and 2.x/3.x migration are in [the maintenance guide](./INSTALL.md#update-or-remove-an-existing-installation).

## Documentation

- [Install guide](./INSTALL.md) and [maintenance/recovery reference](./docs/2026-11-24-install-maintenance.md): fresh setup, block sync, upgrade, removal, symlinks, and recovery.
- [Design](./DESIGN.md): why the bundle is shaped this way and what v3 removed.
- [Stage 5 real-session audit](./docs/2026-11-24-real-session-stage5-audit.md) and [long-term route review](./docs/2026-11-20-context-evolution-route.md): 386 real consumer sessions, current stage, and next priorities.
- [5.19 immediate capture](./docs/2026-11-25-bounded-shard-and-capture-v5.19.md), [5.18 closeout & sharding](./docs/2026-11-24-closeout-sharding-v5.18.md), [5.17 sharded register](./docs/2026-11-24-register-sharding-v5.17.md), [5.16 batching & readback](./docs/2026-11-24-batching-readback-v5.16.md), [cross-domain architecture study](./docs/2026-11-20-context-paths-study.md), and [everyday lookup/edit costs](./docs/2026-11-20-ordered-lookup-cost.md): paired native experiments and whole-task costs.
- [Evolving research and creative projects](./docs/2026-11-14-evolving-research-and-creative-projects.md) (Chinese guide): practical examples for format-5 spaces.
- [Evaluation](./tests/benchmark/README.md): task outcomes, cold handoff, plain-docs controls, and evidence limits.
- [Changelog](./CHANGELOG.md), [Contributing](./CONTRIBUTING.md), [AGENTS.md](./AGENTS.md), and [Security policy](./SECURITY.md).

## Star History

<a href="https://www.star-history.com/#huangpufan/SSOT-CONTEXT&Date"> <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=huangpufan/SSOT-CONTEXT&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=huangpufan/SSOT-CONTEXT&type=Date" /> <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=huangpufan/SSOT-CONTEXT&type=Date" /> </picture> </a>

## License

[MIT](./LICENSE) © [huangpufan](https://github.com/huangpufan)
