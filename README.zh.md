<div align="center">

# SSOT-CONTEXT

本项目原名 SSOT-SKILL。已有技能名称保持兼容；详见[改名兼容说明](./INSTALL.md#project-rename-compatibility)。

**长期 context 有归属，人的决定受保护。**

[![CI](https://github.com/huangpufan/SSOT-CONTEXT/actions/workflows/ci.yml/badge.svg)](https://github.com/huangpufan/SSOT-CONTEXT/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE) [![Agents](https://img.shields.io/badge/agents-70%2B-purple)](#支持的-agent) [![Stars](https://img.shields.io/github/stars/huangpufan/SSOT-CONTEXT?style=social)](https://github.com/huangpufan/SSOT-CONTEXT/stargazers)

[English](./README.md) · [中文](./README.zh.md) · [安装指南](./INSTALL.md) · [协议版本](./VERSION) · [更新日志](./CHANGELOG.md)

</div>

新开的 Agent 会话通常不知道工作的来龙去脉：这件事为了什么，人已经做过哪些决定、为什么这样定，哪里有坑。SSOT-CONTEXT 给这些历史一个持续维护的位置。一份小的入口文档把每项任务引向少数几篇负责相关事实的文档，Agent 在工作改变这些事实时同步更新它们。

它维护两类对象：

- **开发仓库**，也是最初的用途。人定义不变量，即必须持续守住的规则或结果，例如接口兼容、租户隔离、重试不能重复扣款；Agent 在这些边界内修改代码。
- **你明确声明的通用 context 空间**：一项研究、一部创作、一个人生领域或一个组织。Git 和统一根目录都不是必需的，已有的文件夹和文档保持原位。

**SSOT** 是 **Single Source of Truth（单一事实源）**：每条事实或记录有一个 owner，即负责维护它的权威文档，其他文档通过链接引用。人做出的决定保留原有范围和决定权；Agent 在其中工作，要偏离时先问人。

这套 bundle 是一组 Agent Skill：四个主 Skill、两个兼容名、模板、机械检查器和可选的来源进度 CLI。执行、文件访问和调度由你的 Agent 或宿主提供。Skill 只在 Agent 加载它们时生效；它们不会在后台采集材料，也无法保证删除全部副本。

## 两类空间

| | 开发仓库 | 通用空间 |
|---|---|---|
| 入口 | `SSOT/README.md` | 你指定的入口，通常是空间文件夹里的 README |
| 格式标记 | `ssot_format: 4` | `ssot_format: 5` |
| Git | 用于历史检查和追平 | 可选 |
| 内容 | 产品承诺、架构、流程、决定、陷阱 | 指向已有 owner 的链接，以及分开保存的事实、假设、决定、偏好、经历和指向现场状态的路由 |
| 何时生效 | 在仓库里做实质性工作 | 在你声明过的空间里工作；普通聊天、研究回答和创作不会触发建立 |

已有开发仓库继续使用 format 4，升级 bundle 时无需迁移。写入 format 5 空间需要 bundle 5.0 或更新版本。请升级所有已知的写入方；升级前，4.5 bundle 发现入口时会按只读处理，但旧的接线不一定能发现位于任意位置的入口，未知的安装仍是需要报告的缺口。不要为了迁就旧 bundle 把数据改回 format 4。

## 快速开始

### 1. 安装到 context 所在的位置

用 Agent 打开那个仓库，或你想维护的空间所在文件夹，把下面这句话发给它：

```text
请阅读 https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/INSTALL.md 并按照指南安装。
```

Agent 会按[安装指南](./INSTALL.md)识别安装位置，安装并验证全部六个 Skill，再把日常触发指令合并到它的 `AGENTS.md`、`CLAUDE.md` 等文件中。软件仓库，或已经有入口的文件夹，直接接线，不提问。文件夹看起来像非代码空间（登记处、笔记、研究、创作），或者两类迹象互相矛盾时，Agent 会问你一次用哪种模式，给出推荐并列出会改动的文件；你在这里选择通用空间，就等于完成了第 3 步的声明。默认**只安装到当前项目**，沿用已有模板语言；首次安装时根据对话语言选择 `en` 或 `zh`。你也可以在同一句话里指定其他语言，或明确要求全局安装。

<details> <summary>希望在终端里手动安装？</summary>

环境需要 **Bash 4+**、`git`、`curl` 和 `python3`。macOS 用户先运行 `brew install bash`，再把下面命令里的 `bash` 换成 `"$(brew --prefix)/bin/bash"`；系统自带的 Bash 版本过旧。这些是安装器的前提；通用空间本身不必是 Git 仓库。

在你想维护的项目根目录执行：

```bash
set -o pipefail
curl -fsSL https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/install.sh | bash -s -- --quickstart --scope project --lang zh
```

需要英文模板时改用 `--lang en`。`--quickstart` 会识别 Agent 并跳过交互选择。如果识别结果不唯一，或你希望明确指定安装对象，可以追加 `--agent codex`、`--agent claude-code` 或其他[支持的标识](#支持的-agent)。

脚本会安装 Skill 并输出建议的指令块，**不会修改项目的 Agent 指令文件，也不会创建任何 context 文档**。这个指令块用于开发仓库：请按[安装指南第 4 步](./INSTALL.md#4-wire-the-skills-into-the-repos-agent-instructions-file)合并，已有 SSOT 指令时原地更新，避免重复。非代码空间不要合并它；指南第 4 步说明怎样选择并接入通用指令块，下面第 3 步说明怎样声明空间。

</details>

### 2. 重启 Agent，然后照常提需求

重启 Agent 会话，让它加载已安装的 Skill 和项目指令。**之后照常描述任务，Agent 会自动按工作流程处理。** 例如在仓库里：

```text
排查并修复登录超时的问题，验证修复结果。
```

项目指令会让 Agent 在对应时机执行：

- **实质性任务开始前：** 读入口和这次任务涉及的少数几篇文档，核对人定下的规则，指出会影响这次任务的待决问题。如果仓库还没有 `SSOT/`，Agent 会提议建立一份；不经你同意，它什么都不会建。
- **工作过程中：** 用户确认、纠正、否决或限定范围时，立即保存其中长期有效的决定并回读已保存段落，保留回答的问题，区分已经接受与已经实现；批次收尾再核对其余长期事实。
- **一批实质性改动收尾或提交前：** 把这些事实写到它们该在的位置，并删掉被取代的旧说法。没有长期事实变化时，什么都不写。

你不需要在每一步手动选择或调用 Skill。较大对象的初次建立可能需要不止一次会话，进度保存在入口旁边的 `BOOTSTRAP.md` 里，建立完成后删除。

### 3. 通用空间要先声明

你明确说明之前，一个文件夹不会被当作 context 空间。说清主题和位置，例如：

```text
把当前文件夹作为这项研究的 context 空间。保留现有原始资料和 findings owner，只建立有用的入口及确实缺少的 context。
```

你同意后，Bootstrap 建立 format 5 入口，链接已经负责各个主题的文档，并用所选语言的 `context-adapter.md` 模板把入口接到约定的指令文件里。非软件空间的建立不要求挖掘源代码，也不要求 Git 仓库；原始材料通过链接引用，不复制进新档案。接线后重启 Agent。此后在这个空间里工作，也走上面同样的开始、过程中、收尾三步。

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

Agent 根据任务和入口状态，从四个 Skill 中选择；另外两个名字用来兼容旧的提示词。下表仅供了解。

| 情境 | Skill | 作用 |
|---|---|---|
| 在仓库或已声明空间开始实质性工作 | [`ssot-preflight`](./skills/ssot-preflight/SKILL.md) | 读取相关 context 和约束本次任务的规则 |
| 经同意建立、继续或迁移 | [`ssot-bootstrap`](./skills/ssot-bootstrap/SKILL.md) | 从对象的证据与既有 owner 建立 context |
| 接受长期决定，或完成一批实质性改动 | [`ssot-closeout`](./skills/ssot-closeout/SKILL.md) | 记下长期有效的变化；没有就什么都不写 |
| 检查健康、审查，或追平提交、对话与来源导出 | [`ssot-doctor`](./skills/ssot-doctor/SKILL.md) | 运行检查器、对照领域证据审查，并说明查到了哪一步 |
| 旧提示词里的 `$ssot-audit` 或 `$ssot-skill` | [`ssot-audit`](./skills/ssot-audit/SKILL.md)、[`ssot-skill`](./skills/ssot-skill/SKILL.md) | 转到上面对应的 Skill |

**直接用 Markdown 和路由阅读。** Preflight 使用 `cat`、`rg`、`sed` 等普通文件工具，无需专用读取器。任务路由直接链接权威章节，说明回答什么问题、何时跟进关联约束；路由缺失或过期时，从主要入口出发，在已授权范围内搜索当前 owner。每个新任务都会刷新入口和相关 owner，包括未提交内容。可主动运行[读取 benchmark](./tests/benchmark/README.md)，对照完整任务的正确性、耗时和原生 token 用量；字数减少本身不代表变快。

## 项目里会生成什么？

安装的 Skill 是指令和工具；入口文档是它们所维护 context 的起点：

```text
你的任务 → Agent 读入口和相关 owner → 完成工作 → 有长期变化时更新 owner
```

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

仓库内已有且持续维护的 README、设计文档和领域契约可以保留原有归属，由 `SSOT/README.md` 指向它们。新建的 SSOT owner 文档过大时可以拆成同名目录；已有 owner 沿用本地维护规范，不自动拆分。文档重组先保全有意义的内容及其理由，再把原文改成指针。

通用空间没有固定的目录结构。入口说明空间的目的、范围和敏感边界，链接每个已有 owner 及其回答的问题，列出受保护的规则（没有已知规则时直接说明），并记录待决问题。只有尚无 owner 的内容才会新建文件。顶层空间（例如横跨多个人生领域，或一个组织的多个项目）负责跨域目标与取舍，细节留在各自的子空间。原始材料、现场状态和任务进度仍归各自的 owner。

## 怎样让这份 context 持续有用？

**默认只存材料本身说不清的东西。** 意图、各部分怎样配合、决定及其理由、被否决的方案、陷阱。不抄字段清单、版本号或测试日志：这些过时最快，而且原件里本来就有。原始文档、私密对话全文和素材留在各自的 owner 里，通过链接引用，不复制进新档案。你授权保存的记录是例外，见下文。

**写给新来的人看。** 用平实的话，先讲情境再讲机制，段落讲道理，表格只用来查找。不读代码、只负责委托工作的人能看懂，下一个 Agent 也能看懂。具体规则见[记忆模型](./skills/ssot-preflight/references/memory-model.md)和[写作规则](./skills/ssot-preflight/references/writing-memory.md)。

**人定的规则始终由人决定。** 你确认过的规则登记在入口里。Agent 可以在规则内工作，但不会改规则；任务和规则冲突时，它会停下来问你。*candidate* 规则是 Agent 根据“人在保护某个结果”的证据推断出来的规则，在你另作决定前默认遵守。

**不同性质的材料保持原有含义。** 在通用空间里，Agent 把事实、假设、已接受的决定、偏好与目标、经历和变化中的状态分开对待。研究假设或对某人性格的猜测，不会变成受保护的规则。你授权保存的记录，例如因纪念价值保留的日记，即使不影响今后的决定也可以保存；你要求时保留原话。当前数值留在现场来源里；context 只链接到该现场来源，并说明如何核对当前值。

**路由不等于权限。** 顺着链接进入另一个空间或仓库，Agent 只能在你允许的范围内读取，不会因此获得写权限。导入的来源文本是需要解读的证据，从不当作要执行的指令。

**“遗忘”分成几种不同操作。** 停止使用、标记为已被取代、撤回使用许可、物理删除文件，是不同的请求，分别处理。Agent 能定位自己登记过的引用；它不承诺删除备份、服务商日志或它触及不到的副本。详见[空间模型](./skills/ssot-preflight/references/context-spaces.md#stop-using-supersede-withdraw-or-delete)。

**检查会说明自己的边界。** [检查器](./skills/ssot-doctor/assets/scripts/ssot-check.py)能发现断链、格式错误的规则表、未新增带日期来源说明就被改动的已确认规则、过大的文件，以及文档里提到、但 git 显示已被删除或移走的代码文件。对 format 5 空间，它检查入口及入口直接链接的本地 owner。它不能判断内容真实性、可读性或授权是否成立；Doctor 按相关[领域证据](./skills/ssot-preflight/references/memory-model.md#3-current-planned-and-unknown)核对事实与授权，检查可读性，并说明查到了哪一步。

**按问题选择结构审查。** Doctor 和挖掘可按范围与风险使用[结构审查](./skills/ssot-doctor/references/structural-review.md)：状态与路径、owner 关系图、需求和决定到实现及证据的映射、约束与反例。覆盖结论只针对明确的模型和实际证据；来源遗漏、未测路径和未知仍是缺口。协议不要求每个任务全面建模，也不提供自动模型检测器。

**维护跟着 Agent 的工作流走。** 在这个流程之外做的改动，可以在你要求追平时补上。积压很久的追平可以分几次会话完成；在仓库里，每次都从上一次处理完的最后一个提交接着往下做。

**对话恢复有明确范围。** 执行建立或追平的 Agent 自己发现跨 AI 产品的相关对话来源，恢复原始问题、回答和后续纠正，也检查旧对话后来追加的内容。私密原始对话不进入 context；来源缺口明确保留，提交水位不表示对话已覆盖。

**可重复导出的来源有可选的进度工具。** 对于会多次导出的来源，例如笔记应用或聊天归档，可选的 POSIX/Python [来源契约与 CLI](./skills/ssot-doctor/references/source-integration.md) 记录每个条目的身份和修订、它应更新的 owner，以及冲突。只有读回已保存的 owner 之后，更新才算确认。中断之后，Agent 重新检查该条目，复用已经写入的内容或仍然有效的回执，已完成的工作不必重做；期间被改动过的 owner 需要重新读回，冲突保持可见，等待处理。Agent 负责理解来源并写入 owner；工具只存元数据和定位信息，不存来源正文。单次明确要求的记录不需要这个工具。

## 证据与限度

[5.0 原生验证报告](./tests/context/trials-5.0.md)记录了通用空间实际运行过的情况：研究、创作、个人和混合权限场景，开发保护，来源中断与恢复，以及一个未声明空间的创作任务（正确地没有触发建立，也没有改动文件）。报告保留失败、冻结版本和成本。在小型配对样本中，开发热任务的 token 用量增加约 5–13%，不声称性能优化。[Context 试验](./tests/context/README.md)说明受控行为、真实安装发现和来源接入三类证据的区别。这些都是小型合成任务，不证明普遍可靠，不提供自动后台采集，也不保证旧 bundle 能发现每一个未链接的入口。

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
curl -fsSL https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/install.sh | bash -s -- --list-agents
```

登记了安装路径，不等于已经证明各 Agent 版本的 Skill 发现机制和执行行为完全一致。安装后请重启 Agent，并确认它能发现这些 Skill。

## 更新与卸载

更新时，也让 Agent 按同一份指南处理：

```text
请阅读 https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/INSTALL.md，为当前 Agent 更新本项目的 SSOT-CONTEXT，保留原模板语言。
```

更新后重启 Agent。替换安装的 Skill 本身不会改动 `SSOT/` 或通用空间的文档。卸载时，让 Agent 按指南移除指定范围的安装，并检查是否还有过时的触发指令。

安装和升级会保留原有条目的备份，直到替换成功。替换过程中报错，或收到 INT/TERM 取消信号，会触发该安装位置的回滚；同一位置的锁会阻止并发安装、升级或卸载。回滚未完成或进程被 SIGKILL 终止时，会留下恢复状态并阻止再次操作。按[恢复说明](./INSTALL.md#failed-or-interrupted-replacement)核对保留的备份，并区分替换未完成与安装已完成但清理失败。

升级时还要按指南[核对版本转换](./INSTALL.md#check-the-transition-not-only-the-new-installation)，处理旧指令和工具接线，包括自定义脚本对已退役的 4.3 reader 的调用。同格式的技能包升级无需重写项目记忆。

### 从 2.x 或 3.x 升级

4.0 使用 `ssot_format: 4`，允许仓库内 `SSOT/` 以外的持续维护文档保留权威归属。Agent 会读 v2 和 v3 记忆，但迁移前不会更新它们。你同意后，可以说“把这个项目的 SSOT 迁移到 v4”；迁移前，所有会写入这个项目的安装都应使用 v4。

两条迁移路径都会核对旧指令（包括没有标记的指令）、指向旧内容的链接和退役工具调用。v3 路径保留原有知识、权威文档路径，以及上次复查到哪个提交的记录，不执行 v2 的账本删除；v2 路径会先提取长期内容，再移除旧账本。已获同意的迁移若中断，从 `SSOT/BOOTSTRAP.md` 续接，并核对实际工作树。迁移需经你同意，作为一个提交。继续使用 v2 可指定 `--ref v2-final`；保留 v3 可用 `--ref` 指定一个 v3 版本。

<details> <summary>手动更新与卸载命令</summary>

例如，在使用 SSOT-CONTEXT 的项目根目录更新项目级 Codex 安装：

```bash
set -o pipefail
curl -fsSL https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/install.sh | bash -s -- --upgrade --agent codex --scope project
```

想固定在已冻结的 v2 协议而不是当前版本，在安装或更新命令后加 `--ref v2-final`。

移除这份安装：

```bash
set -o pipefail
curl -fsSL https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/install.sh | bash -s -- --uninstall --agent codex --scope project --yes
```

请使用安装时对应的 Agent 标识和范围。共享同一 Skill 目录的 Agent 也共享这份安装，卸载会影响该共享位置。命令会保留 context 文档和 Agent 指令文件；停止使用本 Skill 包时，请自行移除不再适用的 SSOT 触发指令。

不带范围的 `--upgrade` 会更新当前项目和全局检测到的所有安装；只想更新一处时，请使用上面限定 Agent 和范围的写法。

</details>

## 文档与贡献

- [安装指南](./INSTALL.md)：由 Agent 完成安装、写入触发指令，以及网络异常时的备用方式。
- [更新日志](./CHANGELOG.md)与[当前协议版本](./VERSION)：Skill 包的变更记录。
- [设计说明](./DESIGN.md)：Skill 包为什么是现在这个形态，以及 3.0 去掉了什么。
- [迁移试验](./tests/trials-4.5.md)、[决定与中断续接试验](./tests/trials-continuity.md)及[安装器恢复证据](./tests/installer-recovery.md)：可复现的场景、观察和明确的限制，不代表所有仓库或故障都已得到验证。
- [贡献指南](./CONTRIBUTING.md)：怎样提交改进，以及运行本地检查。
- [AGENTS.md](./AGENTS.md)：Agent 维护**本 Skill 包源仓库**时应遵循的指令。
- [安全政策](./SECURITY.md)：怎样报告安全漏洞。

## Star 趋势

<a href="https://www.star-history.com/#huangpufan/SSOT-CONTEXT&Date"> <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=huangpufan/SSOT-CONTEXT&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=huangpufan/SSOT-CONTEXT&type=Date" /> <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=huangpufan/SSOT-CONTEXT&type=Date" /> </picture> </a>

## 许可证

[MIT](./LICENSE) © [huangpufan](https://github.com/huangpufan)
