<div align="center">

# SSOT-CONTEXT

**长期 context 有归属，人的决定受保护。**

[![CI](https://github.com/huangpufan/SSOT-CONTEXT/actions/workflows/ci.yml/badge.svg)](https://github.com/huangpufan/SSOT-CONTEXT/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE) [![Agents](https://img.shields.io/badge/agents-70%2B-purple)](#支持的-agent) [![Stars](https://img.shields.io/github/stars/huangpufan/SSOT-CONTEXT?style=social)](https://github.com/huangpufan/SSOT-CONTEXT/stargazers)

[English](./README.md) · [中文](./README.zh.md) · [安装指南](./INSTALL.md) · [协议版本](./VERSION) · [更新日志](./CHANGELOG.md)

</div>

新开的 Agent 会话对项目的历史、规则与过往教训一无所知。SSOT-CONTEXT 为长期项目知识提供一个精简、持续维护的归宿：一份简短入口把每类任务路由到对应的权威文档，同时守住人已确认的决定，让 Agent 在边界内工作而不是悄悄改写规则。要求暂停或交接时，Agent 会更新获准写入的任务记录，让下一个会话动手前先核对已经发生了什么。

它用在两类地方：

- **开发仓库。** 人定义不变量——必须持续守住的结果，例如接口兼容、重试不能重复扣款；Agent 在这些边界内修改代码。入口是 `SSOT/README.md`（`ssot_format: 4`）。
- **你明确声明的通用 context 空间：** 一项研究、一部创作、一个人生领域或一个组织。Git 不是必需的，已有的文件夹和文档保持原位。入口是你指定的文档（`ssot_format: 5`）。

## 原则

- **一条事实，一个 owner。** SSOT 即 Single Source of Truth（单一事实源）：每条长期事实有一篇负责维护它的文档，其他文档通过链接引用。
- **人定的规则始终由人决定。** 已确认的规则登记在入口里；Agent 在规则内工作，不会擅自改规则，任务与规则冲突时会停下来向你请示。
- **日常少读，需要时找得回。** 热入口、现行主题正文与冷历史界限清晰；[分层与变更对账](./skills/ssot-preflight/references/context-tiering.md)处理主动整理、无损冷迁与局部替代，不另建冗余存储。
- **不同性质的材料分开。** 事实、假设、已确认决定、带范围的[目标与偏好](./skills/ssot-preflight/references/memory-model.md#goals-and-preferences)、获授权的[经历原话](./skills/ssot-preflight/references/context-spaces.md#what-the-material-means)与变化中的状态分开保存。
- **写给新来的人看。** 用平实的话，现行事实在前、冷历史在后，短段分条并写清适用范围，让下一个 Agent 或不读代码的决策者都能据此行动（[写作规则](./skills/ssot-preflight/references/writing-memory.md)）。
- **路由不等于权限。** 打开链接来源前先核实读取授权；实际文件访问由宿主控制，导入的正文是证据而非可执行指令。
- **说明查到了哪一步。** 只读[检查器](./skills/ssot-doctor/assets/scripts/ssot-check.py)核对机械结构（断链、锚点、不变量表格式、已确认规则篡改、豁免冷归档后的膨胀整理候选及 `--owners` 受限子集），不替人判定真假；审查明确列出发现、覆盖范围与缺口。
- **从真实长期 context 需求演进。** 改进从反复出现的真实需求与整任务证据出发，而不是按单次失误堆砌规则（[演进方向](./DESIGN.md#accepted-direction-evolve-from-context-needs)）。

## 快速开始

### 1. 安装

用 Agent 打开那个仓库，或你想维护的空间所在文件夹，把下面这句话发给它：

```text
请阅读 https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/INSTALL.md 并按照指南安装。
```

Agent 会把 Skill 安装到当前项目并验证，再接入 `AGENTS.md`、`CLAUDE.md` 等指令文件。文件夹看起来不像代码仓库时，它会问你一次用哪种模式。你也可以在同一句话里指定模板语言（`en` / `zh`）或要求全局安装。

<details> <summary>改用终端安装</summary>

需要 **Bash 4+**、`git`、`curl` 和 `python3`（macOS 先 `brew install bash`，并改用 `"$(brew --prefix)/bin/bash"`）。在项目根目录执行：

```bash
set -o pipefail
curl -fsSL https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/install.sh | bash -s -- --quickstart --scope project --lang zh
```

脚本会安装 Skill 并输出指令块，但不会修改指令文件，也不会创建 context。按[安装指南第 4 步](./INSTALL.md#4-wire-the-skills-into-the-repos-agent-instructions-file)合并指令块，通用空间的接法也在那里。

</details>

### 2. 重启 Agent，然后照常提需求

照常描述任务即可，四个 Skill 会自动处理工作流程：

- [`ssot-preflight`](./skills/ssot-preflight/SKILL.md) 在实质性工作开始前读取任务路由、适用约束及相关权威来源。开发仓库的长入口按章节读取。
- [`ssot-bootstrap`](./skills/ssot-bootstrap/SKILL.md)：经你同意后建立或迁移 context，保留既有权威文档，并由新读者验证生成的路由是否可用。
- [`ssot-closeout`](./skills/ssot-closeout/SKILL.md) 在目标、偏好和决定确定时保存它们。用户要求交接时使用任务记录，批次收尾时按实际变化更新长期知识。
- [`ssot-doctor`](./skills/ssot-doctor/SKILL.md)：检查健康，并补上在这个流程之外完成的工作。

也可以直接提出，例如“检查这个项目的 SSOT 是否健康”或“让 SSOT 追上最近的提交”。

### 3. 通用空间要先声明

你明确说明之前，一个文件夹不会被当作 context 空间：

```text
把当前文件夹作为这项研究的 context 空间。保留现有文件，只建立有用的入口和确实缺少的 context。
```

普通聊天、研究回答和创作本身不会触发建立。

## 项目里会生成什么

在开发仓库里，只有 `SSOT/README.md` 是必需的，其他文件在有真实内容可写时才会出现：

```text
 your-repo/SSOT/
 ├── README.md        项目是什么、每类任务先看哪里、阻塞待决问题、人定下的规则
 ├── invariants/      可选：不变量表长大后的按主题分片（以及可选冷分片 retired.md）
 ├── product.md       谁在用、承诺了什么、不做什么
 ├── architecture.md  由哪些部分组成、谁掌管哪些状态、关键流程、出错与恢复
 ├── process.md       怎样构建、测试、发布和部署
 ├── decisions/       冷读历史：决策来由、被替代的旧规则与否决方案（常规任务跳过）
 ├── gotchas.md       已经让人栽过跟头的坑与临时绕行
 ├── glossary.md      新人容易误解的项目用语
 └── research/        结论仍在指导决定的调查（结项后常规任务跳过）
```

已有且持续维护的文档可以继续当 owner，由入口链接。通用空间没有固定目录：入口说明目的、范围和受保护的规则，并链接已经负责各个主题的文档。同目录可以有多个空间。搭建尚未完成时，每个入口链接自己的进度记录。详见[记忆模型](./skills/ssot-preflight/references/memory-model.md)和[空间模型](./skills/ssot-preflight/references/context-spaces.md)。

日常限定查询可直接依据单一获准读取的权威文档作答，已批准的单文档正文修订也可原地更新并从磁盘回读。为自动遏制长期膨胀，温层主题文档把现行生效说明放在前面，删除单次验证回执与已解决的临时条目，将被替代旧文、否决试跑与长篇原话默认无损迁入独立冷文件（`decisions/` 或 `*-history.md`；仅在通用空间固定单文件时才用末尾冷历史节），冷索引保持单行定位器，而仍在生效的旧规则继续留在活跃层。`ssot-check.py` 会自动发现结构性膨胀候选（同时豁免冷归档与冷退役分片），收尾阶段就地整理已触及的 SSOT 文件，并对未触及、外部文档或结构拆分以一行明确提议告知用户而不越权改写；不变量表长大后可拆分为 `SSOT/invariants/<topic>.md` 及冷分片 `invariants/retired.md`。如需在所有 Agent 上零模型 token 做提交前机械校验，可选用 [`tools/ssot-precommit.sh`](./tools/ssot-precommit.sh) 钩子（[配置说明](./docs/2026-11-24-install-maintenance.md#optional-zero-token-git-pre-commit-guard)）。

## 限度

- **不后台采集，也不替代宿主权限。** Skill 只在 Agent 加载并看到输入时生效；无法删除触及不到的副本（Git 历史、备份、服务商日志），也无法绕过宿主的文件访问控制。
- **决策权、受限来源与限定范围检查。** 换人接手依项目决策权保留前后归属与唯一旧理由（[决策证据](./skills/ssot-preflight/references/memory-model.md#human-decision-evidence)）；受限来源支持仅元数据撤回（[来源集成](./skills/ssot-doctor/references/source-integration.md#correction-and-withdrawal)）以及使用 `--owners` 限定文件范围的机械检查（[受限检查](./skills/ssot-preflight/references/source-retention.md#selected-mechanical-checks)）。
- **纯提示词路径的运行边界。** 仅靠提示词无法在所有宿主上保证 100% 触发收尾检查，也不会自动同步各工作区中复制的指令块或入库的技能副本；按需配合 `--sync-block`、可选主题分片、全局/软链接安装与可选提交前守卫使用（[真实会话审计](./docs/2026-11-24-real-session-stage5-audit.md)）。

## 支持的 Agent

Antigravity App 使用 `--agent agy`（项目安装与 Codex 共用 `.agents/skills`）；DeepSeek Harness 使用 `--agent dsh`。[维护与排障参考](./docs/2026-11-24-install-maintenance.md#when-a-skill-appears-unavailable)说明多端位置差异、子仓库发现边界、worktree 建议与本机软链接方案（`tools/link-local.py`）。

安装器登记了 **70 多种 Agent** 的安装路径，包括 Claude Code、Codex、Cursor、Windsurf、Gemini CLI、GitHub Copilot、DeepSeek Harness（`dsh`）、OpenCode 和 Cline。登记了路径不等于行为完全一致，安装后请重启 Agent，确认它能发现这些 Skill。查看全部标识与路径：

```bash
set -o pipefail
curl -fsSL https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/install.sh | bash -s -- --list-agents
```

## 更新与卸载

```text
请阅读 https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/INSTALL.md，为当前 Agent 更新本项目的 SSOT-CONTEXT，保留原模板语言。
```

更新技能文件（或拉取软链接源码）后，检查并刷新仓库指令文件中的受管块，再重启 Agent：

```bash
curl -fsSL https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/install.sh | bash -s -- --check-block AGENTS.md
curl -fsSL https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/install.sh | bash -s -- --sync-block AGENTS.md
```

更新会保留软链接安装，不会改写你的 context 文档，也不强制 format 4 仓库转为 format 5。本地源码仓命令、多 Agent 参数、卸载、中断恢复、2.x/3.x 迁移与[更名兼容](./INSTALL.md#project-rename-compatibility)见[维护指南](./INSTALL.md#update-or-remove-an-existing-installation)。

## 文档

- [安装指南](./INSTALL.md)与[维护与恢复参考](./docs/2026-11-24-install-maintenance.md)：新装、指令块同步、升级、卸载、软链接、提交前守卫与中断恢复。
- [设计说明](./DESIGN.md)：Skill 包为什么是现在这个形态，以及 v3 移除了什么。
- [活论文：活的上下文为什么难维护](./paper/LIVING-PAPER.md)（中文正文含英文导读）：跨批次叙事，复盘 v2 崩塌、386 次真实会话与配对实测证明了什么，以及哪些直觉优化被证伪撤回。
- [Stage 5 真实会话审计](./docs/2026-11-24-real-session-stage5-audit.md)与[长期路线审视](./docs/2026-11-20-context-evolution-route.md)：真实消费遥测、当前阶段与后续优先级。
- [外部调研与吸收路线图](./docs/2026-11-27-external-research-absorption-roadmap.md)、[Batches 2–4 与 5.24 实证报告](./docs/2026-11-27-external-research-batches2-4-v5.24.md)与 [`tools/ssot-backlinks.py`](./tools/ssot-backlinks.py)：多模型论文/开源项目评估、62 次隔离实证、5.24 收尾站位守卫与可选工作树反向链接查询工具。
- [评测指南与各版本实测索引](./tests/benchmark/README.md#recorded-studies-and-additional-lanes)：配对原生试验、冷接续、普通文档对照与证据边界。
- [持续修改的研究和创作项目](./docs/2026-11-14-evolving-research-and-creative-projects.md)：格式 5 通用空间的实用示例。
- [更新日志](./CHANGELOG.md)、[贡献指南](./CONTRIBUTING.md)、[AGENTS.md](./AGENTS.md)与[安全政策](./SECURITY.md)。

## Star 趋势

<a href="https://www.star-history.com/#huangpufan/SSOT-CONTEXT&Date"> <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=huangpufan/SSOT-CONTEXT&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=huangpufan/SSOT-CONTEXT&type=Date" /> <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=huangpufan/SSOT-CONTEXT&type=Date" /> </picture> </a>

## 许可证

[MIT](./LICENSE) © [huangpufan](https://github.com/huangpufan)
