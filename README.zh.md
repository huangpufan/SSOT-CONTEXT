<div align="center">

# SSOT-CONTEXT

本项目原名 SSOT-SKILL。已有技能名称保持兼容；详见[改名兼容说明](./INSTALL.md#project-rename-compatibility)。

**长期 context 有归属，人的决定受保护。**

[![CI](https://github.com/huangpufan/SSOT-CONTEXT/actions/workflows/ci.yml/badge.svg)](https://github.com/huangpufan/SSOT-CONTEXT/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE) [![Agents](https://img.shields.io/badge/agents-70%2B-purple)](#支持的-agent) [![Stars](https://img.shields.io/github/stars/huangpufan/SSOT-CONTEXT?style=social)](https://github.com/huangpufan/SSOT-CONTEXT/stargazers)

[English](./README.md) · [中文](./README.zh.md) · [安装指南](./INSTALL.md) · [协议版本](./VERSION) · [更新日志](./CHANGELOG.md)

</div>

SSOT-CONTEXT 帮助 Agent 为开发仓库，以及明确声明的研究、创作、人生领域和组织空间维护长期 context。**每条事实或记录有一个维护 owner；人的决定保留原有范围和决定权。** 入口把下一项任务引向相关 owner，减少每次重新还原历史的工作。

它从一项开发承诺开始：人定义不变量，Agent 在边界内演进代码。接口兼容、租户隔离和重试不能重复扣款等约束仍受保护。原有流程继续使用消费者 format 4；升级 bundle 不要求迁移。

通用空间使用消费者 format 5 和明确接线的入口，保留既有 owner 与目录，不强制 Git 或统一大目录。Agent 区分事实、假设、已接受的选择、偏好、经历与变化中的状态。授权保存的经历可以因纪念价值保留；人格推断和研究假设不会变成默认约束行为的 candidate 规则。

**SSOT** 是 **Single Source of Truth（单一事实源）**：每条维护内容有一个 owner，其他文档通过链接引用。本项目提供四个主 Skill、两个兼容名、模板、机械检查器和可选的来源进度 CLI。执行、访问和调度由 Agent/宿主提供；技能不后台采集不可见材料，也不保证删除全部副本。

## 快速开始

### 1. 安装到你想整理的项目中

用编程 Agent 打开那个项目，把下面这句话发给它：

```text
请阅读 https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/INSTALL.md 并按照指南安装。
```

Agent 会按[安装指南](./INSTALL.md)识别安装位置，安装并验证全部六个 Skill，再把日常触发指令合并到项目的 `AGENTS.md`、`CLAUDE.md` 等文件中。默认**只安装到当前项目**，沿用已有模板语言；首次安装时根据对话语言选择 `en` 或 `zh`。你也可以在同一句话里指定其他语言，或明确要求全局安装。

<details> <summary>希望在终端里手动安装？</summary>

环境需要 **Bash 4+**、`git`、`curl` 和 `python3`。macOS 用户先运行 `brew install bash`，再把下面命令里的 `bash` 换成 `"$(brew --prefix)/bin/bash"`；系统自带的 Bash 版本过旧。

在你想整理的项目根目录执行：

```bash
set -o pipefail
curl -fsSL https://raw.githubusercontent.com/huangpufan/SSOT-CONTEXT/main/install.sh | bash -s -- --quickstart --scope project --lang zh
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

**直接用 Markdown 和路由阅读。** Preflight 使用 `cat`、`rg`、`sed` 等普通文件工具，无需专用读取器。任务路由直接链接权威章节，说明回答什么问题、何时跟进关联约束；路由缺失或过期时，从产品、架构入口和搜索寻找当前 owner。布局、写作和保护规则变更审查仍按需读取独立引用文件。仍在上下文中的指令可以复用；每个新任务刷新入口和相关 owner，包括未提交内容。可主动运行[读取 benchmark](./tests/benchmark/README.md)，对照完整任务的正确性、耗时和原生 token 用量；字数减少本身不代表变快。

你不需要在每一步手动选择或调用 Skill。大型项目的初次建立可能需要不止一次会话，进度保存在 `SSOT/BOOTSTRAP.md` 里，完成后删除。建好之后，从 `SSOT/README.md` 开始阅读。

<details> <summary>可选：直接要求建立或检查</summary>

也可以用日常语言直接提出：

```text
根据代码和现有文档，为这个项目建立 SSOT。
检查这个项目的 SSOT 是否健康。
让 SSOT 追上最近的提交。
```

也可以直接点名 Skill，例如 `使用 $ssot-doctor 检查这个项目的 SSOT。` 这在排查某个 Skill 为什么没有自动触发时有用。这是发给 Agent 的对话指令，不同 Agent 的调用写法可能不同。

</details>

## 通用 context 空间

安装同一套 bundle 后，明确要维护的主题和工作位置。例如：

```text
把当前文件夹作为这项研究的 context 空间。保留现有原始资料和 findings owner，只建立有用的入口及确实缺少的 context。
```

你同意后，Bootstrap 使用 format 5，通过所选语言的 `context-adapter.md` 接线实际入口，保留已有规范 owner。顶层空间可以维护跨域优先级和取舍；子域细节、原始材料、现场状态及任务进度仍归原 owner。路由不授予跨空间读写权限。未声明空间的普通聊天、研究回答和创作跳过工作流。

已知 format-5 writer 需要 bundle 5.0+。旧 writer 必须能发现只读入口，并升级 bundle；不能为了满足旧检查器把数据降为 4。已有开发 format 4 和独立授权的 owner 记录流程继续遵循原有规则。归属、授权记录及撤回/删除的区别见[空间模型](./skills/ssot-preflight/references/context-spaces.md)。

对于可重复导出，可选的 POSIX/Python [来源契约与 CLI](./skills/ssot-doctor/references/source-integration.md) 管理稳定条目/修订身份、声明的 owner 和冲突。更新必须保存后读回才确认；经判断无需更新的结果须保留理由。Agent 理解来源并更新 owner；状态只存元数据和定位，不缓存来源正文。它能停止使用并定位已登记影响，包括未确认捕获，但不声称找到所有下游副本。单次明确记事只需正常 owner 写入/读回。[Context 试验](./tests/context/README.md) 区分受控行为、真实安装发现和来源接入证据。

[原生验证报告](./tests/context/trials-5.0.md) 保留实际结果、失败、冻结身份与成本。小型配对样本中的开发 token 成本有所增加，不声称性能优化。后续元数据/检查器修正有独立机械证据；报告同时说明未覆盖范围与写作质量的限度。

## Agent 怎样选择 Skill？

Agent 根据任务和项目状态，从四个 Skill 中选择；另外两个名字用来兼容旧的提示词。下表仅供了解。

| 情境 | Skill | 作用 |
|---|---|---|
| 开始实质性的仓库或已声明空间工作 | [`ssot-preflight`](./skills/ssot-preflight/SKILL.md) | 读取相关 context 和受保护规则 |
| 经同意建立、继续或迁移 | [`ssot-bootstrap`](./skills/ssot-bootstrap/SKILL.md) | 从主题的证据与既有 owner 建立 context |
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

**检查会说明自己的边界。** [检查器](./skills/ssot-doctor/assets/scripts/ssot-check.py)能发现断链、格式错误的规则表、未新增带日期来源说明就被改动的已确认规则、过大的文件，以及文档里提到、但 git 显示已被删除或移走的代码文件。它不能判断内容真实性、可读性或授权是否成立；Doctor 按相关[领域证据](./skills/ssot-preflight/references/memory-model.md#3-current-planned-and-unknown)核对事实与授权，检查可读性，并说明查到了哪一步。

**按问题选择结构审查。** Doctor 和挖掘可按范围与风险使用[结构审查](./skills/ssot-doctor/references/structural-review.md)：状态与路径、owner 关系图、需求和决定到实现及证据的映射、约束与反例。覆盖结论只针对明确的模型和实际证据；来源遗漏、未测路径和未知仍是缺口，不能证明全部真实诉求已被覆盖。协议不要求每个任务全面建模，也不提供自动模型检测器。

**维护跟着 Agent 的工作流走。** 在这个流程之外做的改动，可以在你要求追平时补上。积压很久的追平可以分几次会话完成，每次都从上一次处理完的最后一个提交接着往下做。

**对话恢复有明确范围。** 执行建立或追平的 Agent 自己发现跨 AI 产品的项目相关对话来源，恢复原始问题、回答和后续纠正，也检查旧对话后来追加的内容。私密原始对话不进入仓库；来源缺口明确保留，提交水位不表示对话已覆盖。这些 Skill 不会自动后台采集，也不保证零遗漏。

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

更新后重启 Agent。替换安装的 Skill 本身不会改动 `SSOT/`。卸载时，让 Agent 按指南移除指定范围的安装，并检查是否还有过时的触发指令。

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

请使用安装时对应的 Agent 标识和范围。共享同一 Skill 目录的 Agent 也共享这份安装，卸载会影响该共享位置。命令会保留 `SSOT/` 文档和 Agent 指令文件；停止使用本 Skill 包时，请自行移除不再适用的 SSOT 触发指令。

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
