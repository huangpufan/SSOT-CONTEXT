<div align="center">

# SSOT-CONTEXT

**长期 context 有归属，人的决定受保护。**

[![CI](https://github.com/huangpufan/SSOT-CONTEXT/actions/workflows/ci.yml/badge.svg)](https://github.com/huangpufan/SSOT-CONTEXT/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE) [![Agents](https://img.shields.io/badge/agents-70%2B-purple)](#支持的-agent) [![Stars](https://img.shields.io/github/stars/huangpufan/SSOT-CONTEXT?style=social)](https://github.com/huangpufan/SSOT-CONTEXT/stargazers)

[English](./README.md) · [中文](./README.zh.md) · [安装指南](./INSTALL.md) · [协议版本](./VERSION) · [更新日志](./CHANGELOG.md)

</div>

新开的 Agent 会话需要知道工作的目标、大家同意怎样做，以及哪些决定仍然影响下一步。SSOT-CONTEXT 让这些信息有地方持续维护。一份简短的入口指向负责相关内容的文档。你要求暂停或交接时，Agent 使用获准写入的任务记录，让新会话核对已经发生的事，以及下一步是否仍服务于当前目标。一轮试验可以结束，目标仍可能有待验证。若决定要等签字才生效，或者试用两次就要复议，执行指南会写清这段时间按什么做。新任务据此核对适用于自己的证据。若把决定写进交接文件就会触发送印或投递，Agent 还要核对谁有权发出。

它用在两类地方：

- **开发仓库。** 人定义不变量，即必须持续守住的结果，例如接口兼容、重试不能重复扣款；Agent 在这些边界内修改代码。入口是 `SSOT/README.md`（`ssot_format: 4`）。
- **你明确声明的通用 context 空间：** 一项研究、一部创作、一个人生领域或一个组织。Git 不是必需的，已有的文件夹和文档保持原位。入口是你指定的文档（`ssot_format: 5`）。

本项目原名 SSOT-SKILL，旧的技能名称仍然可用（[详情](./INSTALL.md#project-rename-compatibility)）。

## 原则

- **日常少读，需要时找得回。** 当前任务工作集、持续维护的主题正文和冷历史各有访问方式。[分层与变更对账](./skills/ssot-preflight/references/context-tiering.md)指导按需整理、局部替代和冻结依赖，沿用现有 owner。已经进入会话的内容何时退出上下文，由宿主控制。

- **从长期 context 需求出发演进。** 开发项目内的任何事情，以及软件之外、自有项目之外的需求，都可以推动完善。先看人们长期需要理解、完成或保留什么；[演进方向](./DESIGN.md#accepted-direction-evolve-from-context-needs)说明怎样把需求变成经过验证的改进。
- **一条事实，一个 owner。** SSOT 即 Single Source of Truth（单一事实源）：每条事实有一篇负责维护它的文档，其他文档通过链接引用。
- **人定的规则始终由人决定。** 你确认过的规则登记在入口里。Agent 在规则内工作，不会改规则；任务和规则冲突时，它会停下来问你。
- **偏好有适用范围。** 长期偏好在指定的对象和场合下指导工作。你可以为单次任务明确指定不同做法，长期偏好仍然有效。[目标与偏好](./skills/ssot-preflight/references/memory-model.md#goals-and-preferences)
- **选择性提炼知识，保留你授权的记录。** 保存意图、各部分怎样配合、决定及其理由、被否决的方案和陷阱；字段清单、版本号和日志留在原件里，原始文档和私密对话通过链接引用。在通用空间里，你要求保留的经历和原话可以留在获授权的 owner 中，不必证明它能影响未来决定；见[空间模型](./skills/ssot-preflight/references/context-spaces.md#what-the-material-means)。
- **不同性质的材料分开。** 事实、假设、决定、偏好和变化中的状态分开保存。研究假设或对某人的猜测，不会变成受保护的规则。
- **写给新来的人看。** 用平实的话，先讲情境再讲机制，让下一个 Agent、或不读代码只负责委托工作的人都能看懂。见[写作规则](./skills/ssot-preflight/references/writing-memory.md)。
- **路由不等于权限。** 打开链接指向的材料前，先确认本次读取在授权范围内。宿主工具的访问控制决定哪些文件实际能打开。导入的文本是需要解读的证据，从不当作要执行的指令。
- **说明查到了哪一步。** [检查器](./skills/ssot-doctor/assets/scripts/ssot-check.py)能发现断链等机械问题，但不能判断内容是否真实。检查具名通用空间时请传入口文件；传目录会选中其中的 `README.md`。如需限定范围检查经索引访问的任务卡，用 `--owners` 同时指定获准的索引和任务卡。审查说明发现的问题、检查范围和证据缺口，获准修复时按指定范围改动。

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
- [`ssot-bootstrap`](./skills/ssot-bootstrap/SKILL.md)：经你同意后建立或迁移 context。建库时，已有权威文档足以指导操作、范围也能逐项查清时，由一人起草、另一人独立核对，再请新读者试用。需要跨来源重建指南、范围过大或权威来源有争议的部分单独分工。
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
 ├── README.md        项目是什么、每类任务先看哪里、人定下的规则、待决问题
 ├── product.md       谁在用、承诺了什么、不做什么
 ├── architecture.md  由哪些部分组成、谁掌管哪些状态、关键流程、出错与恢复
 ├── process.md       怎样构建、测试、发布和部署
 ├── decisions/       事情为什么是现在这样，包括被否决的方案
 ├── gotchas.md       已经让人栽过跟头的坑
 ├── glossary.md      新人容易误解的项目用语
 └── research/        结论仍在指导决定的调查
```

已有且持续维护的文档可以继续当 owner，由入口链接。通用空间没有固定目录：入口说明目的、范围和受保护的规则，并链接已经负责各个主题的文档。同目录可以有多个空间。搭建尚未完成时，每个入口链接自己的进度记录。详见[记忆模型](./skills/ssot-preflight/references/memory-model.md)和[空间模型](./skills/ssot-preflight/references/context-spaces.md)。

协议 5.14 中，日常查询可以直接依据获准读取、负责该事项的现行文档作答。已经批准的改动若只涉及这一份文档的现有正文，维护者就地更新，保留应当留存的旧决定及其理由，再读回核对。涉及其他负责人、审批或保护规则时，走完整流程。

## 限度

Skill 只在 Agent 加载它们时生效。它们不会在后台采集材料，也删不掉触及不到的副本，例如备份或服务商日志。[5.1 试验](./tests/context/trials-5.1.md)覆盖冷会话接续、来源准入和大型保护规则表。这些小型合成证据不证明普遍可靠；[5.0 报告](./tests/context/trials-5.0.md)中，开发热任务的 token 用量增加约 5–13%。

项目负责人换人后，依项目约定判断继任者能够修改哪项选择，分别保留前后两次决定的归属。若早先采用某个偏好的理由只存在于现行指南，替换该做法时会按保留权限保存这段来由。对已登记的来源，还可以查到文档完成读回后，其内容是否又有改动。[决策权与来源](./skills/ssot-preflight/references/memory-model.md#human-decision-evidence) · [来源进度](./skills/ssot-doctor/references/source-integration.md#readback-progress-and-recovery)

撤回访谈等已登记的来源时，工具先保存撤回决定，再盘点受影响文档。若工作文档必须保持关闭，使用 `withdraw-source --metadata-only`。以后的状态查询可以据已有登记列出目标和早先的回执，正文保持关闭。[来源撤回与恢复](./skills/ssot-doctor/references/source-integration.md#correction-and-withdrawal)

开发仓库和通用空间都可以保留指向受限原件的链接。Doctor 能只检查入口和本次获准读取的文档，报告会列出范围。通用空间的入口放在子目录时，`--space-root DIR` 配合 `--owners` 可以检查同一约定根目录下、位于平级目录的指定指南。补录 Git 历史时会读合并分支中的决定，只有连续区间核对完才推进已检查到的提交。[受限检查](./skills/ssot-preflight/references/source-retention.md#selected-mechanical-checks)、[5.9 追补示例](./docs/catchup-5.9.md)

更正决定后，复核保存结果时既对照新交流，也在当前保留授权范围内核对必要的早期来源摘录。[5.3 试验](./tests/context/trials-5.3.md)记录了原话丢失的失败，以及对这条复核规则的有限验证。

## 支持的 Agent

Antigravity App 使用 `--agent agy`，项目安装与 Codex 共用 `.agents/skills`。[安装指南](./INSTALL.md#when-a-skill-appears-unavailable)区分 App、CLI 和独立 IDE 的位置，并说明如何核验实际会话发现。

若希望本机安装即时跟随同一份源码，使用[本机软链接安装](./INSTALL.md#link-local-installations-to-one-checkout)。普通安装仍保留独立副本；软链接依赖持续保留的源码 checkout。

安装器登记了 **70 多种 Agent** 的安装路径，包括 Claude Code、Codex、Cursor、Windsurf、Gemini CLI、GitHub Copilot、OpenCode 和 Cline。登记了路径不等于行为完全一致，安装后请重启 Agent，确认它能发现这些 Skill。查看全部标识与路径：

```bash
set -o pipefail
curl -fsSL https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/install.sh | bash -s -- --list-agents
```

从独立子仓库启动 Agent 时，父目录安装的 Skill 可能不可见。[按实际启动位置确认发现结果](./INSTALL.md)；指向父级上下文的路由和 Skill 安装是两项独立条件。

## 更新与卸载

```text
请阅读 https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/INSTALL.md，为当前 Agent 更新本项目的 SSOT-CONTEXT，保留原模板语言。
```

更新技能文件后，刷新仓库中受管理的指令块，再重启 Agent。更新不会改写你的 context 文档。已有仓库继续使用 format 4；写入 format 5 空间需要 bundle 5.0 或更新版本，所以每个会写入它的 Agent 都要升级。手动命令、卸载、安装中断后的恢复，以及从 2.x 或 3.x 迁移，见[安装指南](./INSTALL.md#update-or-remove-an-existing-installation)。

## 文档

- [安装指南](./INSTALL.md)：安装、接线、升级、卸载和恢复。
- [设计说明](./DESIGN.md)：Skill 包为什么是现在这个形态。
- [持续修改的研究和创作项目](./docs/evolving-research-and-creative-projects.md)：沿用现有 owner，处理局部修订、来源缺口、旧素材与暂缓同步的具体例子。
- [跨领域 context 审计与发布试验](./docs/context-paths-study.md)比较纯文档、已安装协议与可复跑的架构候选，覆盖软件、研究与创作交接。[读取与交接验证](./docs/read-trigger-study.md)记录了直接查询省下多少输入，以及新接手者能从项目文档中找回哪些决定。
- [日常使用与维护成本](./docs/ordered-lookup-cost.md)把查价、改一条规则的成本与普通文档做同题比较，也检查了新人能找回什么，以及 AI 实际打开了哪些文件。
- [长期路线与阶段判断](./docs/context-evolution-route.md)说明现在走到哪、离真实项目持续受益还有多远，以及什么结果会改变下一步的优先级。
- [5.13 的长期 context 审视与六班交接](./docs/context-stewardship-5.13.md)检验负责人交接、目标争用、证据重复和文档核对。
- [5.12 的决定生效与交接试验](./docs/conditional-context-5.12.md)比较签字前后、部分部署、送印权限和受限撤回时的实际产物。
- [5.8 维护审视与试验](./docs/context-maintenance-5.8.md)记录了同目录空间的接续、撤回中断恢复，以及尚待验证的设计。
- [演进审视](./docs/evolution-review-2026-11-12.md)：本轮改进、真实接续试验与证据边界。
- [评测指南](./tests/benchmark/README.md)：任务结果、冷接续、普通文档对照和证据边界。
- [更新日志](./CHANGELOG.md)：每个版本改了什么。
- [贡献指南](./CONTRIBUTING.md)和 [AGENTS.md](./AGENTS.md)：怎样修改本 Skill 包仓库。
- [安全政策](./SECURITY.md)：怎样报告安全漏洞。

## Star 趋势

<a href="https://www.star-history.com/#huangpufan/SSOT-CONTEXT&Date"> <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=huangpufan/SSOT-CONTEXT&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=huangpufan/SSOT-CONTEXT&type=Date" /> <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=huangpufan/SSOT-CONTEXT&type=Date" /> </picture> </a>

## 许可证

[MIT](./LICENSE) © [huangpufan](https://github.com/huangpufan)
