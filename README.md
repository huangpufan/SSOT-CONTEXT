<div align="center">

# SSOT-CONTEXT

**Maintained context. Protected human choices.**

[![CI](https://github.com/huangpufan/SSOT-CONTEXT/actions/workflows/ci.yml/badge.svg)](https://github.com/huangpufan/SSOT-CONTEXT/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE) [![Agents](https://img.shields.io/badge/agents-70%2B-purple)](#supported-agents) [![Stars](https://img.shields.io/github/stars/huangpufan/SSOT-CONTEXT?style=social)](https://github.com/huangpufan/SSOT-CONTEXT/stargazers)

[English](./README.md) · [中文](./README.zh.md) · [Install guide](./INSTALL.md) · [Protocol version](./VERSION) · [Changelog](./CHANGELOG.md)

</div>

A new agent session starts without the history of the work: what the subject is for, which choices people already made and why, and where the traps are. SSOT-CONTEXT gives that history a maintained home. A small entry document routes each task to the few documents that own the relevant facts, and the agent keeps those documents current as the work changes them.

It works in two kinds of place:

- **Development repositories.** People define the invariants, the outcomes that must keep holding, such as API compatibility or never charging twice on a retry. Agents change the code within them. The entry is `SSOT/README.md` (`ssot_format: 4`).
- **General context spaces you explicitly declare:** a research project, a creative work, a personal life domain or an organization. Git is optional, and existing folders and documents stay where they are. The entry is the document you name (`ssot_format: 5`).

The project was previously named SSOT-SKILL; old skill names still work ([details](./INSTALL.md#project-rename-compatibility)).

## Principles

- **One fact, one owner.** SSOT means Single Source of Truth: each fact has one document responsible for keeping it correct, and other documents link to it.
- **People's rules stay people's decisions.** Rules you confirm are listed in the entry. The agent works within them, never changes them, and stops to ask when a task conflicts with one.
- **Extract knowledge selectively; preserve records you authorize.** Keep intent, how the parts fit together, decisions and their reasons, rejected options and traps. Field lists, version numbers and logs stay in their originals; link to original documents and private conversations. In a general space, experiences and exact words you ask to preserve can stay with their authorized owner even without future decision value; see the [space model](./skills/ssot-preflight/references/context-spaces.md#what-the-material-means).
- **Keep kinds of material apart.** Facts, hypotheses, decisions, preferences and changing state are kept distinct. A research hypothesis or a guess about a person never becomes a protected rule.
- **Write for someone new.** Plain words and the situation before the mechanism, so the next agent, or a person who delegates work without reading code, can follow it. See the [writing guide](./skills/ssot-preflight/references/writing-memory.md).
- **Routes are not permissions.** Following a link lets the agent read only within the scope you allowed. Imported text is evidence to interpret, never instructions to execute.
- **Say what was checked.** The [checker](./skills/ssot-doctor/assets/scripts/ssot-check.py) finds mechanical problems such as broken links; it cannot establish truth. Reviews state how far they looked and keep gaps visible.

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

- [`ssot-preflight`](./skills/ssot-preflight/SKILL.md) reads the entry and the relevant owners before substantive work.
- [`ssot-bootstrap`](./skills/ssot-bootstrap/SKILL.md) creates or migrates the context, only with your agreement.
- [`ssot-closeout`](./skills/ssot-closeout/SKILL.md) saves accepted decisions as they happen and records durable changes when a batch finishes. When nothing durable changed, it writes nothing.
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
 ├── product.md       Who uses it, what it promises, what it does not do
 ├── architecture.md  The parts, who owns which state, key flows, failure and recovery
 ├── process.md       How to build, test, release, and deploy
 ├── decisions/       Why things are the way they are, including rejected options
 ├── gotchas.md       Traps that have already cost time
 ├── glossary.md      Project terms a newcomer would misread
 └── research/        Investigations whose conclusions still guide decisions
```

Existing maintained documents can stay the owners and are linked from the entry. A general space has no fixed layout: its entry states purpose, scope and protected rules, and links the documents that already own each topic. Details are in the [memory model](./skills/ssot-preflight/references/memory-model.md) and the [space model](./skills/ssot-preflight/references/context-spaces.md).

## Limits

The skills act only when the agent loads them. They do not collect material in the background, and they cannot delete copies they cannot reach, such as backups or provider logs. The [5.1 trials](./tests/context/trials-5.1.md) cover cold-session continuation, source admission and a large protection register. This is small synthetic evidence, not proof of universal reliability; in the [5.0 report](./tests/context/trials-5.0.md), token use on warm development tasks rose about 5–13%.

## Supported agents

The installer knows the installation paths for **70+ agents**, including Claude Code, Codex, Cursor, Windsurf, Gemini CLI, GitHub Copilot, OpenCode and Cline. A known path does not prove identical behavior, so after installing, restart the agent and confirm it finds the skills. To list every key and path:

```bash
set -o pipefail
curl -fsSL https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/install.sh | bash -s -- --list-agents
```

## Update or uninstall

```text
Read https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/INSTALL.md and update SSOT-CONTEXT for this agent in the current project. Preserve the template language.
```

Updating never rewrites your context documents. Existing repositories stay on format 4; writing a format-5 space needs bundle 5.0 or newer, so upgrade every agent that writes to it. Manual commands, uninstalling, recovery from an interrupted install, and migration from 2.x or 3.x are in the [install guide](./INSTALL.md#update-or-remove-an-existing-installation).

## Documentation

- [Install guide](./INSTALL.md): setup, wiring, upgrade, removal and recovery.
- [Design](./DESIGN.md): why the bundle is shaped this way.
- [Evolution review](./docs/evolution-review-2026-11-12.md): current improvements, real continuation trials and evidence limits.
- [Changelog](./CHANGELOG.md): what changed in each version.
- [Contributing](./CONTRIBUTING.md) and [AGENTS.md](./AGENTS.md): how to change this bundle repository.
- [Security policy](./SECURITY.md): how to report a vulnerability.

## Star History

<a href="https://www.star-history.com/#huangpufan/SSOT-CONTEXT&Date"> <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=huangpufan/SSOT-CONTEXT&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=huangpufan/SSOT-CONTEXT&type=Date" /> <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=huangpufan/SSOT-CONTEXT&type=Date" /> </picture> </a>

## License

[MIT](./LICENSE) © [huangpufan](https://github.com/huangpufan)
