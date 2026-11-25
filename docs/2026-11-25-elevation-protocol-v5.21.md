# 协议 5.21 多维抬升与候选对照：只读预检直出（E2 采纳）、跨格式任务续接与热路径去重（E3 采纳），以及格式 5 收尾直写（E1 撤回）与条件读模型（E4 撤回）

**2026-11-25，基于多维度项目抬升审计（真实成熟分片多 worktree 仓库聚合数据、协议与模板冷读者审查、工具链与检查器状态边界审查、标尺与文档审计），在 `codex-cli 0.172.0` + `gpt-6.1-terra`（`medium`）上对四项独立协议候选（E1、E2、E3、E4）共运行 24 组反向平衡冻结配对（48 次隔离原生回合，Linux `bwrap` 隔离，官方 `install.sh --quickstart --agent codex --scope project` 接线）：仅候选 E2（只读预检直出）与 E3（跨格式 `task-continuation.md` 抽离、批量收尾保护前置与热路径去重，附带成本噪声披露）合入协议 5.21；候选 E1 与 E4 均因明确未通过预声明门禁而被证伪撤回。** 协议 5.21 保持 `ssot_format: 4`/`5` 向后兼容、零常驻目录或受管指令块字节增量、零预算扩容；结合同批将 opt-in 旧兼容壳移入冷路径分区的标尺修正，入口词数净降 26 词至 `3,206 / 3,600`，热路径词数净降 220 词至 `8,751 / 9,200`（E2 与 E3 自身净减 98 词），冷分支 `10,232 / 10,400`，模型读取运行资产 `159,748 / 163,840 B`。完整脱敏机读回执见 [`tests/benchmark/results/2026-11-25-elevation-trials-a.json`](../tests/benchmark/results/2026-11-25-elevation-trials-a.json)（E1/E3）与 [`tests/benchmark/results/2026-11-25-elevation-trials-b.json`](../tests/benchmark/results/2026-11-25-elevation-trials-b.json)（E2/E4）。

## 多维审计与真实生产聚合发现（脱敏摘要）

为避免在合成小夹具上空转微调，本轮先对一个已长期运行 1,224 次提交的成熟分片多 worktree 消费仓库做只读结构与会话分布审计（不采集私有正文、路径或对话原文），并交叉核对全仓协议、模板、检查器、安装器、预提交守卫与标尺脚本。聚合观测暴露出四类跨仓库根因问题（消费者自身的历史债务如 76 个入库旧版技能文件、853 提交未复核或积压清理留给消费仓库本地处理，不写入通用协议）：

- **只读审阅仍落入收尾链路：** 在该成熟仓库 38 次分片后 Codex 收尾会话（多为自动化只读审阅或排查）中，**36/38（94.7%）** 未做任何 SSOT 修改，而 `ssot-preflight/SKILL.md` 原文缺少只读无发现直出规则，末尾又列出无条件的 `## Where to go next` 收尾路由，诱使只读任务额外加载 `ssot-closeout`。
- **分片与多 worktree 下的检查器盲区与噪声错配：** 该仓库 `SSOT/` 经 5.17 分片后共 261.8 KB（1 入口 + 9 个主题分片，最大分片达 47.5 KB（61 行）与 42.0 KB（72 行）；370 行不变量中 283 行即 76.5% 为 `candidate`，单行中位数 529 B、最长 2,059 B，`reviewed_through` 落后 `HEAD` 853 次提交）。实测暴露 `ssot-check.py` 在 5.17 后漏扫仅由分片链接的外部 owner，未覆盖分片内多个不变量章节，对本地存在但已 gitignore 的链接在主检出仅报 `WARN` 却在全部 **11/11** 次 linked worktree 检查中以不透明 `ERROR broken link` 失败，同时外部文档的 `reading-budget` `WARN` 淹没了真实可行动告警；此外子模块 `.git` 文件阻塞了 `.git/hooks/pre-commit` 安装。
- **多 worktree 与多宿主安装分裂：** 该仓库登记了 57 个 worktree，主工作区覆盖了相对路径本地软链，而 Git 跟踪的旧副本导致近期 **38/51（74.5%）** 的 Codex worktree 会话仍停留在冻结的 v5.0 技能；同时 `install.sh` 未登记 DeepSeek Harness（`dsh`），导致最近 **0/40** 次 DSH 会话发现 `.agents/skills/`。
- **协议、模板与标尺自身的结构漂移：** 模板中 `BOOTSTRAP.md` 仍鼓励指向被 `.gitignore` 忽略的 `.ssot-work/` Markdown 链接，且 `ssot-readme.md` / `context-readme.md` 仍将 `candidate` 表述为等待用户逐条确认的队列（与 `memory-model.md` 第 91 行矛盾）；`memory-layout.md` 混装了跨格式任务续接条款，导致格式 4/5 暂停与续接被迫加载整份 1,098 词格式 4 布局手册；`batch-closeout.md` 把“保护人的规则”放在已落盘的步骤 2 之后；`tests/test-bundle-shape.sh` 把已移出新装默认的两个旧兼容壳计入热路径（占去 140 词），且缺少模板零告警、8 份指令文件表同步、`CHANGELOG.md` 版本头与全部 12 个收费试跑脚本的 `CI=1` 拒绝门禁。

## 协议变更四问（[`CONTRIBUTING.md`](../CONTRIBUTING.md#changing-the-protocol)，针对采纳的 E2 与 E3）

1. **这属于通用协议职责吗？** 属于。**E2** 解决所有开发仓库与通用空间中高频出现的只读评审/调研误入收尾问题：原有入口既未在 `## 3` 豁免只读审阅，又在文末用无条件表格指向 `$ssot-closeout`，造成额外读取与往返。**E3** 解决三处通用协议归属与顺序缺陷：跨格式任务续接本就服务于格式 4 与格式 5，寄生在格式 4 专属的 `memory-layout.md` 会强迫格式 5 暂停/续接读取无关布局规则；`batch-closeout.md` 先写（步骤 2）后核保护（步骤 4）违反“改前先核人定规则”的先后顺序；多处文件内重复表述与 `ssot-doctor/SKILL.md` 第 21 行缺失分片锚点也属于协议自身的单一权威整理。其余仓库规模治理、worktree 软链、子模块钩子和模板文案问题则分别交由检查器、安装器、工具脚本、模板与标尺修复，不污染共享协议。
2. **它替代或新增了什么？** **E2** 仅修改 [`skills/ssot-preflight/SKILL.md`](../skills/ssot-preflight/SKILL.md) 第 43 行与第 51 行：在 `## 3` 开头明确只读评审或调查可跳过保护影响分析（仍需报告已观察到的违规），删除末尾冗余的 `## Where to go next` 表，并将第 51 行替换为清晰的触发条件（讨论中确定持久选择仍立即调 `$ssot-closeout`，批次改了文件、要求交接、或发现持久结论/SSOT 错漏时在回复或提交前调 `$ssot-closeout`，无以上情形的纯只读评审或调查直接结束且不加载 `$ssot-closeout`），净减 2 词。**E3** 新增 237 词的 [`skills/ssot-preflight/references/task-continuation.md`](../skills/ssot-preflight/references/task-continuation.md)（纳入 `HOT_RUNTIME_FILES`），在 [`skills/ssot-preflight/references/memory-layout.md`](../skills/ssot-preflight/references/memory-layout.md) 原 `#existing-task-and-evidence-owners` 处保留指针以保外部锚点不断，将 [`skills/ssot-preflight/SKILL.md`](../skills/ssot-preflight/SKILL.md) 第 49 行、[`skills/ssot-closeout/SKILL.md`](../skills/ssot-closeout/SKILL.md) 第 25 行与 [`skills/ssot-preflight/references/context-spaces.md`](../skills/ssot-preflight/references/context-spaces.md) 两处链接改指 `task-continuation.md`；将 [`skills/ssot-closeout/references/batch-closeout.md`](../skills/ssot-closeout/references/batch-closeout.md) 的受保护规则前置校验合并到步骤 2 写操作之前并删去重复的旧步骤 4；清理 `ssot-preflight/SKILL.md` 第 19/25 行、`ssot-doctor/SKILL.md` 原第 16 行合并至第 10 行与 [`skills/ssot-closeout/references/decision-capture.md`](../skills/ssot-closeout/references/decision-capture.md) 第 10 行已证实的文件内重复语句，并在 [`skills/ssot-doctor/SKILL.md`](../skills/ssot-doctor/SKILL.md) 第 21 行补齐指向 [`memory-model.md#5-invariants`](../skills/ssot-preflight/references/memory-model.md#5-invariants) 的分片链接。E2+E3 合计净减 26 入口词、98 热路径词与 572 B 运行资产（其中 E2 `+79 B`、E3 `-651 B`），零常驻目录或受管块字节变化。
3. **验证层级是否匹配影响范围？** 是。机械层在模型试跑前与合入后均通过 `bash tests/test-bundle-shape.sh`（合入后 107/107，含模板零告警、CommonMark 围栏、链接锚点、预算与卫生门禁）、8/8 零费用 `codex debug prompt-input` 技能发现探针、Linux 内核 `inotify` 阴阳校准（`true`、`aged_git_status_e1_a2` 与 `--owners` 均为 `0 B`，`cat` 与未限定范围检查器均为 `32 B`）以及未修改夹具负向预言机；行为层在独立 `bwrap` 与官方安装接线环境下完成 24 组反向平衡冻结配对（48 次 `gpt-6.1-terra` `medium` 原生会话），覆盖只读评审、多 owner 只读确认、四类收尾反例、格式 4/5 暂停续接、已确认不变量冲突反例、格式 5 受限采集与常规/安全编码对照，全部 48/48 回执经脚本校验 `models=["gpt-6.1-terra"]`、`reasoning=["medium"]`、`completed=true`、`returncode=0` 与 `observation_complete=true`。
4. **整任务净收益与代价是什么？** **E2** 在全部 8 组（16 次会话）中保持 8/8 质量与安全全通过，4/4 必须收尾的反例（`C1–C4`）零误跳，只读任务对 `ssot-closeout/SKILL.md` 的冗余读取由 **2/4 降至 0/4（0%）**（含多 owner 确认组强制走入 `ssot-preflight/SKILL.md` 后的 `1→0`），预声明 6 组原生输入下降 **2.71%**、未命中缓存下降 **19.15%**，全部 4 组只读任务原生输入下降 **4.03%**、未命中缓存下降 **33.21%**，全部 8 组原生输入下降 **0.39%**、未命中缓存下降 **19.11%**、工具调用下降 **4.76%**（`63 → 60`），仅总往返在 8 组上波动 `+1`（`41 → 42`，预声明 6 组持平 `32 → 32`）。**E3** 在全部 4 组（8 次会话）中保持 4/4 语义质量与安全全通过（含 `E3_C1` 已确认不变量 UTF-8 BOM 冲突零退化），暂停/续接场景确定性将 `memory-layout.md` 读取从 **3/3 降至 0/3** 并 **3/3** 命中 237 词 `task-continuation.md`，兑现 `-96` 热路径词 / `-24` 入口词减法与保护顺序修复；其 4 组合计原生输入为 `+1.55%`（`+7,731` token，约 0.38 轮往返，2 胜 1 平 1 负），已按反向复测揭示的高方差基线如实披露。同期 **E1** 与 **E4** 均未达门禁并撤回，不引入任何未证实的提示词膨胀。

## 冻结包 SHA-256 与零费用校准结果

两条试验通道各自以 `5.20`（提交 `baefb7e`）为基线冻结只读技能树并校验 `codex debug prompt-input`（全部 8/8 探针均发现 4 个核心生命周期技能并加载 `AGENTS.md`）。两条通道因清单范围细节不同而分别记录各自的冻结树 SHA-256：

| 通道与版本 | 冻结包树 SHA-256 | 发现探针（`codex debug prompt-input`） | 校准摘要 |
|---|---|---|---|
| 通道 A 基线（`5.20` `baefb7e`） | `7befdad7cf791727008e9a15f60dc87ed3967d86d7e6391672dfbd71ae3b3422` | `f4`: OK（70,500 B）· `f5`: OK（70,217 B） | 7/7 负向预言机与初始 `ssot-check.py` 全过 |
| 通道 A 候选 `e1`（已撤回） | `57d91b72090bcd97118188c5c2270b07e93f7bfdbff064b5d1825c9cf7fe06bb` | `f5`: OK（70,188 B） | `inotify`: `true`/`aged_git_status`/`--owners` 均 `0 B`；`cat`/未限定检查均 `32 B` |
| 通道 A 候选 `e3`（已采纳） | `941f0ff311644dd9ba85112039bfd093c99c7d6540946d8d909e8dedb2421971` | `f4`: OK（70,472 B）· `f5`: OK（70,187 B） | 入口 `-24` 词、热路径 `-96` 词、资产 `-651 B` |
| 通道 B 基线（`5.20` `baefb7e`） | `d9bad6f4ea744ee3fcbee7b49f3e26772998813f92c61c36616f606754beee21` | `bwrap`: OK（70,487 B） | 全部 16 份夹具初始 `ssot-check.py` 与未改代码负向预言机全过 |
| 通道 B 候选 `e2`（已采纳） | `7649e0aa709ec3273ccc3e584609bad4c1caeb3b1e32b0a6b6dadd0590783814` | `bwrap`: OK（70,455 B） | 入口 `-2` 词、热路径 `-2` 词、零目录/适配器增量 |
| 通道 B 候选 `e4`（已撤回） | `33dd33250ec2cec31717d181ecbc2fea4ba134edc2dfaa22f3dd1c31efdaafec` | `bwrap`: OK（70,456 B） | 入口 `+6` 词、热路径 `+6` 词、零目录/适配器增量 |

## E2 配对实测结果（8 组 16 次会话：6 组预声明 + 2 组多 owner 只读确认，采纳）

候选 E2 在 `skills/ssot-preflight/SKILL.md` 引入只读评审/调查豁免 `## 3` 与无发现直出规则并删除冗余文末跳转表。除预声明 6 组（2 组只读 + 4 组必走收尾的反例）外，由于 `E2_A2` 上候选臂凭相同的 `AGENTS.md` 直接走单文档限定查询（未进入 `ssot-preflight/SKILL.md`），试验增补了 2 组跨多 owner 的中/英文只读确认配对（`E2_A3_r1/r2`），确保 4/4 次会话均先读入 `ssot-preflight/SKILL.md` 再检验是否跳过 `ssot-closeout`。

| 用例与顺序 | 通过（B→C） | 基线→候选原生输入（变化） | 未命中缓存 | 往返 / 工具 | 读 `ssot-closeout`（括号为 `preflight`） | 候选读取协议文件 |
|---|---|---:|---:|---:|---|---|
| `E2_A1_readonly_review_en`（B→C，只读审阅） | 通过* / 通过 | 75,103 → 75,876（+1.03%） | 17,375 → 9,956 | 4→4 / 5→7 | 0→0（1→1） | `preflight, memory-model` |
| `E2_A2_readonly_trace_zh`（C→B，中文只读追踪） | 通过 / 通过 | 76,055 → 47,690（-37.30%） | 15,127 → 7,370 | 4→3 / 5→4 | **1→0**（1→0） | *（限定单源查询：`[]`）* |
| `E2_C1_readonly_finds_wrong_ssot_en`（B→C，反例：查出 SSOT 错漏） | 通过* / 通过* | 107,969 → 103,309（-4.32%） | 13,889 → 17,933 | 5→5 / 9→7 | **1→1**（1→1） | `preflight, memory-model, closeout, batch-closeout, writing-memory` |
| `E2_C2_discussion_decision_zh`（C→B，反例：讨论中定规） | 通过 / 通过 | 140,556 → 131,138（-6.70%） | 22,284 → 9,922 | 7→7 / 11→8 | **1→1**（0→0） | `closeout, decision-capture, memory-model` |
| `E2_C3_readonly_finds_trap_en`（B→C，反例：只读发现持久陷阱） | 通过 / 通过 | 153,025 → 173,425（+13.33%） | 12,737 → 25,201 | 7→8 / 11→18 | **1→1**（1→1） | `preflight, memory-model, closeout, batch-closeout, writing-memory` |
| `E2_C4_normal_code_edit_en`（C→B，反例：常规改代码） | 通过 / 通过 | 98,341 → 101,980（+3.70%） | 20,005 → 11,612 | 5→5 / 8→7 | **1→1**（1→1） | `preflight, memory-model, closeout` |
| **E2 预声明 6 组合计（12 会话）** | **6/6 → 6/6** | **651,049 → 633,418（-2.71%）** | **101,417 → 81,994（-19.15%）** | **32→32 / 49→51** | **A1–A2: 1/2→0/2；C1–C4: 4/4→4/4** | — |
| `E2_A3_r1_multiowner_readonly_zh`（B→C，多 owner 只读确认） | 通过 / 通过 | 78,548 → 93,780（+19.39%） | 20,948 → 10,196 | 4→5 / 7→5 | **1→0**（1→1） | `preflight, memory-model` |
| `E2_A3_r2_multiowner_readonly_en`（C→B，多 owner 只读确认） | 通过 / 通过 | 97,982 → 97,148（-0.85%） | 9,790 → 14,716 | 5→5 / 7→4 | 0→0（1→1） | `preflight, memory-model` |
| **E2 全部 4 组只读小计（8 会话）** | **4/4 → 4/4** | **327,688 → 314,494（-4.03%）** | **63,240 → 42,238（-33.21%）** | **17→17 / 24→20** | **2/4 → 0/4（0%）** | — |
| **E2 全部 8 组总计（16 会话）** | **8/8 → 8/8** | **827,579 → 824,346（-0.39%）** | **132,155 → 106,906（-19.11%）** | **41→42 / 63→60** | **6/8 → 4/8** | — |

**诚实披露（E2）：** 表中 3 处 `通过*` 为原始正则未匹配同义措辞但人工核查落盘产物与最终回答均完全通过的语义达标（`E2_A1` 基线用 `"header mapping"`/`"three"` 表达 `"idempotency"`/`"3"`；`E2_C1` 双臂均遵守 `memory-model.md §2` 不在文档硬写默认值，改为写明 `"least recently used"` 并指向 `src/cache.py`，同时在回答中准确报告 `600s/2,048`）。`E2_A3_r1` 虽因额外 1 轮代码核对使总输入上升 `+19.39%`，但工具调用从 `7` 降至 `5`、未命中缓存减半且验证了进入 `ssot-preflight` 后的因果跳过（`ssot-closeout` `1→0`）；全部 4 组反例无一误跳。

## E3 配对实测结果（4 组 8 次会话：3 组预声明 + 1 组反向复测，采纳并披露噪声）

候选 E3 抽离 237 词跨格式 `task-continuation.md`、将 `batch-closeout.md` 的保护前置到步骤 2、清理文件内重复并补齐 `ssot-doctor/SKILL.md:21` 分片链接。首轮 3 组中 `E3_A2`（C→B）出现候选 8 轮对基线 6 轮的抖动，故保留首轮原记录不覆盖并补跑反向配对 `E3_A2_r2`（B→C）测量基线自身方差。

| 用例与顺序 | 语义通过（B→C） | 基线→候选原生输入（变化） | 未命中缓存 | 往返 / 工具 | 读 `memory-layout` → 读 `task-continuation` |
|---|---|---:|---:|---:|---|
| `E3_A1_f4_pause_resume_en`（B→C，格式 4 暂停续接） | 通过 / 通过 | 86,887 → 85,368（-1.75%） | 6,887 → 5,752 | 5→5 / 5→5 | **1→0** / **0→1** |
| `E3_A2_f5_pause_resume_en`（C→B，格式 5 暂停续接 r1） | 通过* / 通过 | 119,994 → 157,940（+31.62%） | 15,418 → 20,340 | 6→8 / 5→8 | **1→0** / **0→1** |
| `E3_A2_r2_f5_pause_resume_en`（B→C，格式 5 暂停续接 r2） | 通过* / 通过 | 171,147 → 141,835（-17.13%） | 16,907 → 23,435 | 8→7 / 7→6 | **1→0** / **0→1** |
| `E3_C1_batch_protected_conflict_en`（B→C，反例：已确认规则冲突） | 通过 / 通过 | 120,649 → 121,265（+0.51%） | 10,697 → 16,561 | 6→6 / 9→15 | 0→0 / 0→0 |
| **E3 首轮 3 组小计（6 会话）** | **3/3* → 3/3** | **327,530 → 364,573（+11.31%）** | **33,002 → 42,653（+29.24%）** | **17→19 / 19→28** | **A1–A2: 2/2→0/2 / 0/2→2/2** |
| **E3 全部 4 组总计（8 会话，含 r2）** | **4/4* → 4/4** | **498,677 → 506,408（+1.55%）** | **49,909 → 66,088（+32.42%）** | **25→26 / 26→34** | **A1–A2: 3/3→0/3 / 0/3→3/3** |

**采纳理由与噪声披露（E3）：** `E3_A2` 两轮对比表明，同一基线在 `E3_A2` 上的自身波动即达 `119,994 ↔ 171,147`（`6 ↔ 8` 轮，源于 `"resume"` 触发了 `ssot-bootstrap/SKILL.md` 试探），反向 `r2` 候选反降 `-17.13%`（`8→7` 轮），合并 4 组后总输入差仅为 `+1.55%`（`+7,731` token，约 0.38 次 Codex 往返；赢 2 组、平 `C1` `+0.51%`、输出 `-1.07%`）。同时，E3 在行为上 **3/3→0/3** 消除格式 4/5 暂停续接对 1,098 词 `memory-layout.md` 的误读并 **3/3** 精准读取 237 词 `task-continuation.md`，在安全上修正了 `batch-closeout.md` 先写后护的顺序缺陷并通过 `E3_C1`（UTF-8 BOM 已确认不变量拦截），且净减 96 词热路径与 24 词入口；鉴于其结构归属与净减法收益明确、总输入差落在单轮随机噪声内，维护者裁决连同噪声披露一并采纳（表中 `E3_A2` 基线 `通过*` 仅因原始关键词检查未在最终答复中找到字面 `v2`，落盘检查证实 `tasks/survey-wave2.md` 已写入 `revised v2 consent form` 且语义完全达标）。

## E1 配对实测结果（4 组 8 次会话：格式 5 收尾直写路由，证伪撤回）

候选 E1 试图在 `skills/ssot-closeout/SKILL.md` 中直接为格式 5 的即时采集与暂停交接提供短路由（入口与热路径 `+38` 词、冷分支 `-14` 词），以期减少跳转到 `context-spaces.md` 的往返。

| 用例与顺序 | 通过（B→C） | 基线→候选原生输入（变化） | 未命中缓存 | 往返 / 工具 | 读 `context-spaces.md`（B→C） | `inotify` / 候选读取文件 |
|---|---|---:|---:|---:|---|---|
| `E1_A1_f5_immediate_capture_en`（B→C，格式 5 即时建规） | 通过 / 通过 | 94,002 → 79,316（-15.62%） | 8,882 → 10,964 | 5→4 / 5→3 | 1 → 1 | — / `closeout, decision-capture, context-spaces, doctor, structural-review` |
| `E1_A2_f5_restricted_capture_en`（C→B，格式 5 受限采集） | 通过 / 通过 | 73,999 → 90,944（+22.90%） | 9,103 → 8,512 | 4→5 / 3→4 | **1 → 0** | **0 B → 0 B** / `closeout, decision-capture, source-retention, memory-model` |
| `E1_A3_f5_pause_handoff_en`（B→C，格式 5 暂停交接） | 通过 / 通过 | 69,667 → 88,052（+26.39%） | 9,763 → 13,300 | 4→5 / 3→4 | 0 → 0 | — / `closeout, memory-layout` |
| `E1_C1_f5_batch_experience_en`（C→B，反例：格式 5 批量经历记录） | 通过 / 通过 | 71,294 → 71,435（+0.20%） | 7,678 → 14,859 | 4→4 / 3→3 | 1 → 1 | — / `closeout, context-spaces`（无 `--since`） |
| **E1 全部 4 组总计（8 会话）** | **4/4 → 4/4** | **308,962 → 329,747（+6.73%）** | **35,426 → 47,635（+34.46%）** | **17→18 / 14→14** | **A1–A3: 2/3→1/3；C1: 1/1** | **证伪撤回** |

**撤回原因（E1）：** 尽管 4/4 通过质量与安全检查（含 `E1_A2` 内核 `inotify` 双方 `0 B`），但明确未通过预声明门禁：`context-spaces.md` 读取仅在 `A1–A3` 上下降 **1/3**（门禁要求 `≥2/3`），聚合原生输入反升 **+6.73%**、未命中缓存升 **+34.46%**、总往返增 `+1`（`17 → 18`），且净增 `+38` 热路径词。工具轨迹揭示的根因是：[5.16 合批读取](2026-11-24-batching-readback-v5.16.md) 已让基线在 `E1_A1`/`E1_A2` 的第 2 轮用单次 `cat` 合并读取 `decision-capture.md` 与 `context-spaces.md`，而 `E1_A3` 基线本身就已跳过 `context-spaces.md`——所假设的格式 5 往返乒乓在 5.20 基线上并不成立。因此撤回 E1，保留原文件不变。

## E4 配对实测结果（8 组 16 次会话：条件加载 `memory-model.md`，证伪撤回）

候选 E4 试图在 `skills/ssot-preflight/SKILL.md` 将 14.8 KB 的 `memory-model.md` 改为按触发条件加载（入口与热路径 `+6` 词），在常规编码任务中跳过该参考，仅在遇到计划项、冲突、保护规则边界等信号时按需加载。

| 用例与顺序 | 通过（B→C） | 基线→候选原生输入（变化） | 未命中缓存 | 往返 / 工具 | 读 `memory-model.md`（B→C） | 候选读取协议文件 |
|---|---|---:|---:|---:|---|---|
| `E4_A1_routine_code_en`（B→C，常规编码 Parcel Desk） | 通过 / 通过 | 101,819 → 125,770（+23.52%） | 11,963 → 21,706 | 5→6 / 9→10 | 1 → 1 | `preflight, memory-model, closeout` |
| `E4_A2_routine_warm_en`（C→B，常规热更新编码） | 通过 / 通过 | 96,738 → 152,773（+57.92%） | 13,154 → 9,925 | 5→8 / 9→13 | **1 → 0** | `preflight, closeout, batch-closeout, writing-memory` |
| `E4_A3_routine_code_zh`（B→C，常规中文编码） | 通过 / 通过 | 195,124 → 134,809（-30.91%） | 26,548 → 10,265 | 9→7 / 11→16 | **1 → 0** | `preflight, closeout, batch-closeout, writing-memory` |
| `E4_C1_undoc_code_guard_en`（C→B，反例：未登记代码守卫） | 通过 / 通过 | 97,721 → 76,699（-21.51%） | 19,641 → 19,739 | 5→4 / 6→11 | 1 → 1 | `preflight, memory-model, protection-departure` |
| `E4_C2_confirmed_invariant_en`（B→C，反例：已确认不变量） | 通过 / 通过 | 75,944 → 75,190（-0.99%） | 15,400 → 17,974 | 4→4 / 3→6 | 1 → 1 | `preflight, memory-model, protection-departure` |
| `E4_C3_candidate_departure_en`（C→B，反例：候选规则偏离） | 通过 / 通过 | 75,865 → 75,944（+0.10%） | 10,201 → 10,280 | 4→4 / 5→5 | 1 → 1 | `preflight, memory-model, protection-departure, closeout` |
| `E4_C4_conditional_512_en`（B→C，反例：5.12 条件生效规则） | 通过* / 通过* | 97,437 → 97,710（+0.28%） | 10,269 → 19,502 | 5→5 / 8→6 | 1 → 1 | `preflight, memory-model, closeout` |
| `E4_C5_doc_vs_code_conflict_en`（C→B，反例：文档与代码冲突） | 通过 / 通过 | 107,983 → 155,362（+43.88%） | 13,775 → 18,658 | 5→7 / 13→17 | 1 → 1 | `preflight, memory-model, closeout, batch-closeout, writing-memory` |
| **E4 常规主组 A1–A3（6 会话）** | **3/3 → 3/3** | **393,681 → 413,352（+5.00%）** | **51,665 → 41,896（-18.91%）** | **19→21 / 29→39** | **3/3 → 1/3** | — |
| **E4 安全反例 C1–C5（10 会话）** | **5/5 → 5/5** | **454,950 → 480,905（+5.71%）** | **69,286 → 86,153（+24.34%）** | **23→24 / 35→45** | **5/5 → 5/5** | — |
| **E4 全部 8 组总计（16 会话）** | **8/8 → 8/8** | **848,631 → 894,257（+5.38%）** | **120,951 → 128,049（+5.87%）** | **42→45 / 64→84** | **8/8 → 6/8** | **证伪撤回** |

**撤回原因与工具轨迹根因（E4）：** 尽管 E4 取得 8/8 质量与安全通过（5/5 安全反例均正确加载 `memory-model.md`；`E4_C4` 双臂 `通过*` 仅因原始正则要求字面 `2027-01-01`/`cfo`/`v2`，单测、20% v1 SE VAT 行为与 `ssot-check.py` 均通过且明确陈述 `"governing 20% v1 VAT rate"`），并在 2/3 常规编码上跳过了 `memory-model.md`，却在**主组与反例组双双恶化了成本与轮次**：总原生输入上升 **+5.38%**（主组 `+5.00%`、反例 `+5.71%`），未命中缓存上升 **+5.87%**，API 往返上升 **+7.14%**（`42 → 45`），工具调用暴增 **+31.25%**（`64 → 84`）。逐条工具轨迹揭示了三条可复现的机制根因：(1) 在 `E4_A1` 中，现有文档一句 `"express is planned, not yet built"` 合法触发了 E4 的 `"planned"` 条件，导致 `memory-model.md` 从原本可合批的首读退化为**滞后串行补读**（`5→6` 轮，`+23.52%`）；(2) 在 `E4_A2` 中，跳过 `memory-model.md §2`（"不复述函数签名与参数细节"）使候选臂误以为需要把 `max_length` 记入 `docs/architecture.md`，额外触发 `batch-closeout.md` 与 `writing-memory.md`（`5→8` 轮，`+57.92%`）；(3) 在 `E4_C5` 中，推迟到发现代码与文档冲突后才回头补读 `memory-model.md` 增加了 2 轮串行往返（`5→7` 轮，`+43.88%`）。三处回跳收益为负，彻底抵消了 `E4_A3` 的 `-30.91%`（与此前 [5.15 热读拆分研究](2026-11-24-hotpath-split-study.md) 证明的“单次串行往返惩罚远大于省下几 KB 文本”一致）。因此撤回 E4，保持 `ssot-preflight/SKILL.md` 第 29 行热路径读取 `memory-model.md` 关键章节不变。

## 5.21 同批工程、模板、标尺与文档升级（零额外协议成本）

除 E2/E3 协议变更外，本版本在各自权威 owner 处一并修复了多维审计暴露的工程、模板与标尺根因，并经全套离线回归验证通过：

- **检查器与来源契约加固：** `ssot-check.py`（`74,238 / 98,304 B`）补齐 5.17 仅分片引用外部 owner 的可达扫描（`--owners` 仍经 `sys.addaudithook` 验证严格零越权打开）、覆盖分片内多章节不变量保护、为缺失的 gitignored 目标输出 worktree 感知 `ERROR` 与存在目标的 worktree 警示 `WARN`、将外部 owner 的 `reading-budget` 降级为 `INFO` 并新增入口/分片总规模、单行超 500 字与 `reviewed_through` 落后 ≥100 提交的非阻塞 `INFO` 信号、修复含中文路径英文格式 5 块的语言误判及非法行号锚点（`#L0`/倒置/超 EOF）；`context-source.py` 拒绝 `upsert` 非空 `replaces`（忽略 `null`）、在全部绑定 owner 遇非缺失读错误时记录 `unavailable` 并阻塞 `no-update`/`complete`、禁止已撤回来源或只读 `inspect --history` 写入状态。
- **安装器、预提交守卫与本地软链加固：** `install.sh` 消除本地模板查找的跨仓 `$PWD` 串扰、规范化 `dedup_targets` 路径并对空全局目录发出跳过提示、将 `--uninstall` 改为带 `.ssot-transaction` 回滚与 SIGKILL 恢复的事务操作、修复 `select_agents()` 空搜索崩溃与 `set -e` 返回 1 缺陷、对齐 `detect_block_lang()` 英文中文路径判断、支持 `CLAUDE_CONFIG_DIR`/`DSH_HOME` 自动探测优先级并正式登记 DeepSeek Harness（`dsh`）；`tools/ssot-precommit.sh` 支持浅克隆 `.git/shallow`、在定向与回退快照中正确保留 `160000` 子模块边界、支持分离 `GIT_DIR`/`GIT_WORK_TREE`、将触发器与 `.mdc`/`.cursorrules`/`.windsurfrules`/`SSOT_TARGET="."` 对齐并扩展 `find_checker()`；`tools/link-local.py` 接入与 `install.sh` 互通的 `.ssot-skill-lock` 并发锁、拒绝静默覆盖 Git 跟踪技能目录（需显式 `--allow-tracked`）并新增 worktree 安全的 `--absolute` 选项。
- **模板、标尺与文档对齐：** 修复 `bootstrap.md` 与 `{en,zh}/bootstrap-progress.md` 的 `.ssot-work/` 链接与注释格式，统一 `{en,zh}/{ssot-readme,context-readme}.md` 的 `candidate` 语义并补齐格式 4 分片提示、`memory-model.md:88` 禁止分片索引表告警以及 `mining.md` 单行简写与 `.ssot-work/` 清理；`tests/test-bundle-shape.sh` 升级为真实目录布局 `0 error(s), 0 warning(s)` 模板冒烟测试、CommonMark §4.5 围栏检查、跨文件同步门禁（`CHANGELOG.md` 版本头、`install.sh` 与 `ssot-check.py` 8 份指令文件一致、双语 README 结构/外链一致、双语模板 frontmatter 键与 `$ssot-*` 一致）及旧兼容壳冷路径分区；`tests/benchmark/test_benchmark.py` 新增参数化测试覆盖全部 12 个 `--run-models` 脚本的 `CI=1` 拒绝；同步收敛 `README.md`/`README.zh.md`、`INSTALL.md`、`docs/2026-11-24-install-maintenance.md`、`CONTRIBUTING.md`、`DESIGN.md`、`.github/PULL_REQUEST_TEMPLATE.md`、`tests/benchmark/README.md` 与 `docs/2026-11-20-context-evolution-route.md`。

## 证据边界与清理披露

全部 24 组配对（48 次原生会话）仅在单一授权低价模型（`gpt-6.1-terra` `medium`）与单一宿主（`codex-cli 0.172.0`）上的合成夹具中运行，每类场景仅 1–2 次重复，不能直接外推为跨模型或跨宿主的稳定降幅；其中 `E3` 的总输入存在单轮往返级方差，已如实保留首轮与反向复测记录。两条通道的原始 `/tmp` 临时运行目录与试跑脚本在提取全部脱敏原生回执并核对冻结技能树 SHA-256 哈希后均已按清理要求删除，因此本仓库仅保留脱敏机读汇总与逐次指标（[`2026-11-25-elevation-trials-a.json`](../tests/benchmark/results/2026-11-25-elevation-trials-a.json) 与 [`2026-11-25-elevation-trials-b.json`](../tests/benchmark/results/2026-11-25-elevation-trials-b.json)），不声称存在外部完整归档副本。
