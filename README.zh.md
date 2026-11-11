<div align="center">

# SSOT-CONTEXT

**长期 context 有归属，人的决定受保护。**

[![CI](https://github.com/huangpufan/SSOT-CONTEXT/actions/workflows/ci.yml/badge.svg)](https://github.com/huangpufan/SSOT-CONTEXT/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE) [![Agents](https://img.shields.io/badge/agents-70%2B-purple)](#支持的-agent) [![Stars](https://img.shields.io/github/stars/huangpufan/SSOT-CONTEXT?style=social)](https://github.com/huangpufan/SSOT-CONTEXT/stargazers)

[English](./README.md) · [中文](./README.zh.md) · [安装指南](./INSTALL.md) · [协议版本](./VERSION) · [更新日志](./CHANGELOG.md)

</div>

新开的 Agent 会话不知道工作的来龙去脉：这件事为了什么，人已经做过哪些决定、为什么这样定，哪里有坑。SSOT-CONTEXT 给这些历史一个持续维护的位置。一份小的入口文档把每项任务引向少数几篇负责相关事实的文档，Agent 在工作改变这些事实时同步更新它们。

它用在两类地方：

- **开发仓库。** 人定义不变量，即必须持续守住的结果，例如接口兼容、重试不能重复扣款；Agent 在这些边界内修改代码。入口是 `SSOT/README.md`（`ssot_format: 4`）。
- **你明确声明的通用 context 空间：** 一项研究、一部创作、一个人生领域或一个组织。Git 不是必需的，已有的文件夹和文档保持原位。入口是你指定的文档（`ssot_format: 5`）。

本项目原名 SSOT-SKILL，旧的技能名称仍然可用（[详情](./INSTALL.md#project-rename-compatibility)）。

## 原则

- **一条事实，一个 owner。** SSOT 即 Single Source of Truth（单一事实源）：每条事实有一篇负责维护它的文档，其他文档通过链接引用。
- **人定的规则始终由人决定。** 你确认过的规则登记在入口里。Agent 在规则内工作，不会改规则；任务和规则冲突时，它会停下来问你。
- **选择性提炼知识，保留你授权的记录。** 保存意图、各部分怎样配合、决定及其理由、被否决的方案和陷阱；字段清单、版本号和日志留在原件里，原始文档和私密对话通过链接引用。在通用空间里，你要求保留的经历和原话可以留在获授权的 owner 中，不必证明它能影响未来决定；见[空间模型](./skills/ssot-preflight/references/context-spaces.md#what-the-material-means)。
- **不同性质的材料分开。** 事实、假设、决定、偏好和变化中的状态分开保存。研究假设或对某人的猜测，不会变成受保护的规则。
- **写给新来的人看。** 用平实的话，先讲情境再讲机制，让下一个 Agent、或不读代码只负责委托工作的人都能看懂。见[写作规则](./skills/ssot-preflight/references/writing-memory.md)。
- **路由不等于权限。** 顺着链接，Agent 只能在你允许的范围内读取。导入的文本是需要解读的证据，从不当作要执行的指令。
- **说明查到了哪一步。** [检查器](./skills/ssot-doctor/assets/scripts/ssot-check.py)能发现断链等机械问题，但不能判断内容是否真实。审查会说明查到了哪一步，缺口保持可见。

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

- [`ssot-preflight`](./skills/ssot-preflight/SKILL.md)：实质性工作开始前，读入口和相关 owner。
- [`ssot-bootstrap`](./skills/ssot-bootstrap/SKILL.md)：建立或迁移 context，必须经你同意。
- [`ssot-closeout`](./skills/ssot-closeout/SKILL.md)：决定被接受时立即保存，一批工作收尾时记录长期变化；没有长期变化就什么都不写。
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

已有且持续维护的文档可以继续当 owner，由入口链接。通用空间没有固定目录：入口说明目的、范围和受保护的规则，并链接已经负责各个主题的文档。详见[记忆模型](./skills/ssot-preflight/references/memory-model.md)和[空间模型](./skills/ssot-preflight/references/context-spaces.md)。

## 限度

Skill 只在 Agent 加载它们时生效。它们不会在后台采集材料，也删不掉触及不到的副本，例如备份或服务商日志。现有证据来自小型合成试验，不证明普遍可靠；[5.0 报告](./tests/context/trials-5.0.md)中，开发热任务的 token 用量增加约 5–13%。

## 支持的 Agent

安装器登记了 **70 多种 Agent** 的安装路径，包括 Claude Code、Codex、Cursor、Windsurf、Gemini CLI、GitHub Copilot、OpenCode 和 Cline。登记了路径不等于行为完全一致，安装后请重启 Agent，确认它能发现这些 Skill。查看全部标识与路径：

```bash
set -o pipefail
curl -fsSL https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/install.sh | bash -s -- --list-agents
```

## 更新与卸载

```text
请阅读 https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/INSTALL.md，为当前 Agent 更新本项目的 SSOT-CONTEXT，保留原模板语言。
```

更新不会改写你的 context 文档。已有仓库继续使用 format 4；写入 format 5 空间需要 bundle 5.0 或更新版本，所以每个会写入它的 Agent 都要升级。手动命令、卸载、安装中断后的恢复，以及从 2.x 或 3.x 迁移，见[安装指南](./INSTALL.md#update-or-remove-an-existing-installation)。

## 文档

- [安装指南](./INSTALL.md)：安装、接线、升级、卸载和恢复。
- [设计说明](./DESIGN.md)：Skill 包为什么是现在这个形态。
- [演进审视](./docs/evolution-review-2026-11-11.md)：当前优先级、来源恢复修复和尚待补齐的证据。
- [更新日志](./CHANGELOG.md)：每个版本改了什么。
- [贡献指南](./CONTRIBUTING.md)和 [AGENTS.md](./AGENTS.md)：怎样修改本 Skill 包仓库。
- [安全政策](./SECURITY.md)：怎样报告安全漏洞。

## Star 趋势

<a href="https://www.star-history.com/#huangpufan/SSOT-CONTEXT&Date"> <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=huangpufan/SSOT-CONTEXT&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=huangpufan/SSOT-CONTEXT&type=Date" /> <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=huangpufan/SSOT-CONTEXT&type=Date" /> </picture> </a>

## 许可证

[MIT](./LICENSE) © [huangpufan](https://github.com/huangpufan)
