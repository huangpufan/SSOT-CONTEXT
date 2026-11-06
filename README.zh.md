<div align="center">

# SSOT Skill

**人定义不变量，Agent 演进代码。**

[![CI](https://github.com/huangpufan/SSOT-SKILL/actions/workflows/ci.yml/badge.svg)](https://github.com/huangpufan/SSOT-SKILL/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE) [![Agents](https://img.shields.io/badge/agents-70%2B-purple)](#支持的-agent) [![Stars](https://img.shields.io/github/stars/huangpufan/SSOT-SKILL?style=social)](https://github.com/huangpufan/SSOT-SKILL/stargazers)

[English](./README.md) · [中文](./README.zh.md) · [安装指南](./INSTALL.md) · [协议版本](./VERSION) · [更新日志](./CHANGELOG.md)

</div>

我们的判断是：Coding Agent 会向设计、实现和代码审查的自动化持续演进。SSOT Skill 探索并适应这种范式变化：**人参与定义项目的不变量；当出现修改不变量的建议时，由人判断修改是否正确、是否合适，并决定是否接受。** 不变量是实现无论怎样演进都必须守住的承诺，例如接口兼容、租户数据隔离、重试不能重复扣款。

在这些边界内，Agent 执行任务，外层 **Harness**（围绕 Agent 的工具、检查与执行控制）支撑自动化。

**SSOT Skill 让这些不变量和决策有据可循。** 它以随代码版本管理的 `SSOT/README.md` 为入口，指向约束及其理由、架构、决策和已知陷阱的唯一维护位置。仓库内已有且持续维护的文档可以保留权威归属，让不同会话、不同 Agent 从同一组明确的共识出发。

**SSOT** 是 **Single Source of Truth（单一事实源）**：每条长期事实只在一个位置维护，其他文档通过链接引用。本项目提供六个 Skill、Markdown 模板和本地检查脚本，在你已有的编程 Agent 中维护这份共享知识；任务的执行与验证由你的 Harness 和测试设施承担。

## 快速开始

### 1. 安装到你想整理的项目中

用编程 Agent 打开那个项目，把下面这句话发给它：

```text
请阅读 https://raw.githubusercontent.com/huangpufan/SSOT-SKILL/main/INSTALL.md 并按照指南安装。
```

Agent 会按[安装指南](./INSTALL.md)识别安装位置，安装并验证全部六个 Skill，再把日常触发指令合并到项目的 `AGENTS.md`、`CLAUDE.md` 等文件中。默认**只安装到当前项目**，沿用已有模板语言；首次安装时根据对话语言选择 `en` 或 `zh`。你也可以在同一句话里指定其他语言，或明确要求全局安装。

<details> <summary>希望在终端里手动安装？</summary>

环境需要 **Bash 4+**、`git`、`curl` 和 `python3`。macOS 用户先运行 `brew install bash`，再把下面命令里的 `bash` 换成 `"$(brew --prefix)/bin/bash"`；系统自带的 Bash 版本过旧。

在你想整理的项目根目录执行：

```bash
set -o pipefail
curl -fsSL https://raw.githubusercontent.com/huangpufan/SSOT-SKILL/main/install.sh | bash -s -- --quickstart --scope project --lang zh
```

需要英文模板时改用 `--lang en`。`--quickstart` 会识别 Agent 并跳过交互选择。如果识别结果不唯一，或你希望明确指定安装对象，可以追加 `--agent codex`、`--agent claude-code` 或其他[支持的标识](#支持的-agent)。

脚本会安装 Skill 并输出建议的指令块，**不会修改项目的 Agent 指令文件，也不会创建 `SSOT/`**。请按[安装指南第 4 步](./INSTALL.md#4-wire-the-skills-into-the-repos-agent-instructions-file)合并指令块；已有 SSOT 指令时原地更新，避免重复。随后继续下一步。

</details>

### 2. 重启 Agent，然后照常提需求

重启 Agent 会话，让它加载已安装的 Skill 和项目指令。**之后照常描述任务，Agent 会自动按 SSOT 工作流程处理。** 例如：

```text
排查并修复登录超时的问题，验证修复结果。
```

项目指令会让 Agent 在对应时机执行：

- **实质性任务开始前：** 读 `SSOT/README.md` 和这次任务涉及的少数几篇文档，核对人定下的规则，指出会影响这次任务的待决问题。如果项目还没有 `SSOT/`，Agent 会提议建立一份；不经你同意，它什么都不会建。
- **工作过程中：** 用户确认、纠正、否决或限定范围时，立即保存其中长期有效的决定并回读已保存段落，保留回答的问题，区分已经接受与已经实现；批次收尾再核对其余长期事实。
- **一批实质性改动收尾或提交前：** 把这些事实写到它们该在的位置，并删掉被取代的旧说法。没有长期事实变化时，什么都不写。

你不需要在每一步手动选择或调用 Skill。大型项目的初次建立可能需要不止一次会话，进度保存在 `SSOT/BOOTSTRAP.md` 里，完成后删除。建好之后，从 `SSOT/README.md` 开始阅读。

建立和追平时，Agent 会按项目盘点可访问的 AI 对话来源，恢复相关问题、回答和后续纠偏，也检查旧对话后来追加的内容。私密原始对话不进入仓库；不可访问的来源明确留下缺口。提交水位不表示对话已覆盖。这些 Skill 不会自动后台采集，也不保证零遗漏。

<details> <summary>可选：直接要求建立或检查</summary>

也可以用日常语言直接提出：

```text
根据代码和现有文档，为这个项目建立 SSOT。
检查这个项目的 SSOT 是否健康。
让 SSOT 追上最近的提交。
```

也可以直接点名 Skill，例如 `使用 $ssot-doctor 检查这个项目的 SSOT。` 这在排查某个 Skill 为什么没有自动触发时有用。这是发给 Agent 的对话指令，不同 Agent 的调用写法可能不同。

</details>

## Agent 怎样选择 Skill？

Agent 根据任务和项目状态，从四个 Skill 中选择；另外两个名字用来兼容旧的提示词。下表仅供了解。

| 情境 | Skill | 作用 |
|---|---|---|
| 开始一项实质性的项目任务 | [`ssot-preflight`](./skills/ssot-preflight/SKILL.md) | 读取相关记忆，以及约束这次任务的规则 |
| 新建、继续建立或迁移 `SSOT/` | [`ssot-bootstrap`](./skills/ssot-bootstrap/SKILL.md) | 从项目的代码、历史和文档中建立记忆 |
| 接受长期决定，或完成一批实质性改动 | [`ssot-closeout`](./skills/ssot-closeout/SKILL.md) | 记下长期有效的变化；没有就什么都不写 |
| 检查健康、对照领域证据审查、追平提交与对话来源 | [`ssot-doctor`](./skills/ssot-doctor/SKILL.md) | 运行检查器、对照领域证据审查，并说明查到了哪一步 |
| 旧提示词里的 `$ssot-audit` 或 `$ssot-skill` | [`ssot-audit`](./skills/ssot-audit/SKILL.md)、[`ssot-skill`](./skills/ssot-skill/SKILL.md) | 转到上面对应的 Skill |

## 项目里会生成什么？

安装的 Skill 是指令和工具；项目里的 `SSOT/README.md` 是它们维护的记忆入口：

```text
你的任务 → Agent 读 SSOT → 完成工作 → 有长期变化时更新 SSOT
```

只有入口文件是必需的，其他文件在有真实内容可写时才会出现：

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

新建的 SSOT owner 文档过大时可以拆成同名目录；已有 owner 沿用本地维护规范，不自动拆分。仓库内已有且持续维护的 README、设计文档和领域契约可以保留原有归属，由 `SSOT/README.md` 指向它们。文档重组先保全有意义的内容及其理由，再把原文改成指针；研究原件、任务产物和运行状态沿用适合它们的 owner。

## 怎样让这份记忆持续有用？

**只存代码说不清的东西。** 意图、各部分怎样配合、决定及其理由、被否决的方案、陷阱。不抄字段清单、版本号或测试日志：这些过时最快，而且代码里本来就有。

**写给新来的人看。** 用平实的话，先讲情境再讲机制，段落讲道理，表格只用来查找。不读代码、只负责委托工作的人能看懂，下一个 Agent 也能看懂。具体规则见[记忆模型](./skills/ssot-preflight/references/memory-model.md)。

**人定的规则始终由人决定。** 你确认过的规则登记在 `SSOT/README.md` 里。Agent 可以在规则内工作，但不会改规则；任务和规则冲突时，它会停下来问你。

**检查会说明自己的边界。** [检查器](./skills/ssot-doctor/assets/scripts/ssot-check.py)能发现断链、格式错误的规则表、未带日期批准就被改动的已确认规则、过大的文件，以及文档里提到、但 git 显示已被删除或移走的代码文件，但判断不了文档是否属实、是否好懂；这部分由 Doctor 对照代码审查，并说明查到了哪一步。

**维护跟着 Agent 的工作流走。** 在这个流程之外做的改动，可以在你要求追平时补上。积压很久的追平可以分几次会话完成，每次都从上一次处理完的最后一个提交接着往下做。

## 支持的 Agent

安装器登记了 **70 多种 Agent** 的安装路径，包括 Claude Code、Codex、Cursor、Windsurf、Gemini CLI、GitHub Copilot、OpenCode 和 Cline。常用的项目级安装位置如下：

| Agent | 安装器标识 | 项目 Skill 目录 |
|---|---|---|
| Claude Code | `claude-code` | `.claude/skills/` |
| Codex | `codex` | `.agents/skills/` |
| Cursor | `cursor` | `.agents/skills/` |
| Windsurf | `windsurf` | `.windsurf/skills/` |
| Gemini CLI | `gemini-cli` | `.agents/skills/` |

查看全部标识与安装路径，不执行安装：

```bash
set -o pipefail
curl -fsSL https://raw.githubusercontent.com/huangpufan/SSOT-SKILL/main/install.sh | bash -s -- --list-agents
```

登记了安装路径，不等于已经证明各 Agent 版本的 Skill 发现机制和执行行为完全一致。安装后请重启 Agent，并确认它能发现这些 Skill。

## 更新与卸载

更新时，也让 Agent 按同一份指南处理：

```text
请阅读 https://raw.githubusercontent.com/huangpufan/SSOT-SKILL/main/INSTALL.md，为当前 Agent 更新本项目的 SSOT Skill，保留原模板语言。
```

更新后重启 Agent。替换安装的 Skill 本身不会改动 `SSOT/`。卸载时，让 Agent 按指南移除指定范围的安装，并检查是否还有过时的触发指令。

### 从 2.x 或 3.x 升级

4.0 使用 `ssot_format: 4`，允许仓库内 `SSOT/` 以外的持续维护文档保留权威归属。Agent 会读 v2 和 v3 记忆，但迁移前不会更新它们。你同意后，可以说“把这个项目的 SSOT 迁移到 v4”；迁移前，所有会写入这个项目的安装都应使用 v4。v3 迁移保留原有知识和路径；v2 迁移还会先提取长期内容，再移除旧账本，并改接调用退役工具的脚本。迁移需经你同意，作为一个提交。继续使用 v2 可指定 `--ref v2-final`；保留 v3 可用 `--ref` 指定一个 v3 版本。

<details> <summary>手动更新与卸载命令</summary>

例如，在使用 SSOT Skill 的项目根目录更新项目级 Codex 安装：

```bash
set -o pipefail
curl -fsSL https://raw.githubusercontent.com/huangpufan/SSOT-SKILL/main/install.sh | bash -s -- --upgrade --agent codex --scope project
```

想固定在已冻结的 v2 协议而不是当前版本，在安装或更新命令后加 `--ref v2-final`。

移除这份安装：

```bash
set -o pipefail
curl -fsSL https://raw.githubusercontent.com/huangpufan/SSOT-SKILL/main/install.sh | bash -s -- --uninstall --agent codex --scope project --yes
```

请使用安装时对应的 Agent 标识和范围。共享同一 Skill 目录的 Agent 也共享这份安装，卸载会影响该共享位置。命令会保留 `SSOT/` 文档和 Agent 指令文件；停止使用本 Skill 包时，请自行移除不再适用的 SSOT 触发指令。

不带范围的 `--upgrade` 会更新当前项目和全局检测到的所有安装；只想更新一处时，请使用上面限定 Agent 和范围的写法。

</details>

## 文档与贡献

- [安装指南](./INSTALL.md)：由 Agent 完成安装、写入触发指令，以及网络异常时的备用方式。
- [更新日志](./CHANGELOG.md)与[当前协议版本](./VERSION)：Skill 包的变更记录。
- [设计说明](./DESIGN.md)：Skill 包为什么是现在这个形态，以及 3.0 去掉了什么。
- [贡献指南](./CONTRIBUTING.md)：怎样提交改进，以及运行本地检查。
- [AGENTS.md](./AGENTS.md)：Agent 维护**本 Skill 包源仓库**时应遵循的指令。
- [安全政策](./SECURITY.md)：怎样报告安全漏洞。

## Star 趋势

<a href="https://www.star-history.com/#huangpufan/SSOT-SKILL&Date"> <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=huangpufan/SSOT-SKILL&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=huangpufan/SSOT-SKILL&type=Date" /> <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=huangpufan/SSOT-SKILL&type=Date" /> </picture> </a>

## 许可证

[MIT](./LICENSE) © [huangpufan](https://github.com/huangpufan)
