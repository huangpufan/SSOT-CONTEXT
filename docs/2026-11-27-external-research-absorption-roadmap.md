# 外部前沿论文与开源项目系统调研、多模型评审、Batch 1 实验裁决与长期吸收路线图

**2026-11-27，围绕“系统获取、研究、评价、实验并长期吸收外部前沿论文与开源项目（不限于 Agent 记忆）”的目标，我们完成了跨 5 个研究与工程轨道的 2025–2026 年 11 月一手语料采集（90+ 篇 arXiv 论文、17 个 2026 下半年代表性开源项目及此前 69 仓库扫描基线），组织了多模型独立红队评审（两轮 Codex Astra `gpt-6.2-astra xhigh` + Codex Terra `gpt-6.1-terra medium` + 本会话综合），并在隔离沙箱下执行了 12 次 `gpt-6.1-terra medium` 原生基线预筛试验。** 最终裁决：**保持协议 `5.23` 不变（`+0` 协议词数、不发 `5.24`）**，拒绝“代码-文档同提交卡点”反模式，**正式吸收零模型 token 的显式反向链接只读工具 [`tools/ssot-backlinks.py`](../tools/ssot-backlinks.py)**（经 Astra 8 项安全/解析审计全量加固并通过 9/9 回归测试与 CI 接入），同时将本次基线预筛暴露出的单文档快路径归档回执残留列为 Batch 2 头号实验项，并确立 Batches 2–4 长期重开触发路线图。

## 一、调研范围与一手语料分布

本次调研覆盖 2025 年至 2026 年 11 月下旬公开论文与高活跃开源实现，明确跳出“纯对话 RAG / 向量记忆”狭窄视角，按长期 context 维护的真实失败模式划分为五个交叉轨道，并补充了 Codex Astra 指出的四类非记忆基础学科参照（时态数据库与 W3C PROV、增量构建系统与 Git 原子比较交换、临床交接 I-PASS 与 Nygard ADR、前缀缓存经济学与读写摊销）：

| 轨道 | 代表论文（已核验 arXiv ID 与年份） | 代表开源项目（2026 下半年一手核验） | 与 SSOT-CONTEXT 的核心交集 |
|---|---|---|---|
| **1. 编码 Agent 上下文文件与 Skill 实证** | `Evaluating AGENTS.md` (`2602.11988`)、`Agent READMEs` (`2511.12884`)、`Census of AGENTS.md/CLAUDE.md` (`2610.31715`)、`Policy Wording` (`2611.04367`)、`Catastrophic Remembering` (`2608.11095`)、`SkillsBench` (`2602.12670`)、`SkillsBench Audit` (`2611.33943`)、`SkillBuffBench` (`2611.22017`)、`Agent Skills Can Be Harmful` (`2608.11888`) | `okf-memory/okf-agent-memory`、`spec-kitty/spec-kitty`、`github/spec-kit` | 验证了精简指令面、零无故程序化（Excessive Procedure）、按需披露与配对实测门禁 |
| **2. 记忆巩固、时态真值与认识论完整性** | `AuthMem-Bench` (`2608.01679`)、`Manufactured Confidence` (`2606.29279`)、`LAPSE` (`2609.36457`)、`STALE` (`2605.06527`)、`TOKI` (`2606.06240`)、`Nous` (`2606.22030`)、`Infini Memory` (`2606.10677`)、`TrustMem` (`2606.25161`)、`RoMem` (`2604.11544`)、`Memory in the Age of AI Agents` (`2512.13564`) | `tigerless-labs/agent-memory`、`volcengine/OpenViking`、`AgentMemoryRepo/agentmemoryrepo`、`vectorize-io/hindsight`、`getzep/graphiti`、`swarmclawai/swarmvault` | 验证 Markdown 单一事实源 + 主题文档维护方向，精准标定压缩扁平化、权威坍塌与隐式冲突测试场景 |
| **3. 交接保真、多 Agent 委托与权限漂移** | `When "Must" Becomes "Maybe"` (`2608.24569`)、`When Do Summaries Become Instructions` (`2611.06545`)、`Semantic Context Handoff (SCH)` (`2611.24357`)、`Authorization Drift` (`2611.09113`)、`DelegateGuard` (`2610.16005`)、`Delegation Without Trust` (`2609.00267`)、`Specification Satisficing` (`2611.16289`) | `oceanbase/powercontext`、`zhangfengcdt/memoir`、`thedotmack/claude-mem`、`TencentCloud/TencentDB-Agent-Memory` | 揭示多跳交接阻断器软化、摘要自造许可/限制与委托权限漂移风险 |
| **4. 上下文折叠、前缀缓存与注意力竞争** | `Context Has a Price` (`2611.22238`)、`Compaction Laundering` (`2610.29869`)、`Folio` (`2611.16627`)、`ReFold` (`2610.07863`)、`The Complexity Trap` (`2508.21433`)、`Length Is Cheap, Competition Is Not` (`2611.04169`)、`Context Poisoning` (`2609.22101`)、`SAG-Mem` (`2611.33124`) | `tobi/qmd`、`Graphify-Labs/graphify`、`VectorSpaceLab/general-agentic-memory` | 说明前缀缓存折扣下提前灌注反而增费、上下文衰减源于同格式竞争陈述而非纯长度、可重建词法检索优于黑盒向量库 |
| **5. 活文档漂移、经验记忆与评测方法论** | `Documentation Drift in AI PRs` (`2610.27381`)、`Detecting ADR Violations` (`2602.07609`)、`Operational Runbooks` (`2611.29097`)、`ACE` (`2510.04618`)、`ReasoningBank` (`2509.25140`)、`MemoryGraft` (`2512.16962`)、`MemoryArena` (`2602.16313`)、`LongMemEval-V2` (`2605.12493`) | `riponcm/projectmem` (`2606.12329`)、`AML-memory/agent-memory-leaderboard`、`Shichun-Liu/Agent-Memory-Paper-List` | 区分事实回忆与跨会话可执行交付，警示经验库投毒与无证据的“必改文档”卡点 |

## 二、多模型红队评审结论（Codex Astra + Codex Terra + 协调者）

在首轮多模型评审中，**Codex Astra（`gpt-6.2-astra xhigh`）** 与 **Codex Terra（`gpt-6.1-terra medium`）** 独立审阅了 `v5.23` 全部核心协议、`tools/ssot-precommit.sh` 与两份一手语料摘要，对 8 组候选机制形成清晰收敛并严格守住 `DESIGN.md` 反膨胀底线：

- **已由 `v5.23` 覆盖（不增写冗余条款）：** 隐式冲突与旧行为追踪（`context-tiering.md#reconcile-changed-guidance` 与 `memory-model.md#3-current-planned-and-unknown`）、理由保留与禁止杜撰理由（`decision-capture.md` 与 `memory-model.md#3-current-planned-and-unknown`）、以及 SSOT 边界的 AI 摘要不可确立批准与注入消息警示（`memory-model.md#human-decision-evidence` 与 `conversation-catchup.md`；而序列器抹除角色元数据的根本修复责任归属宿主运行时，见 `2610.29869`）。
- **明确拒绝的反模式：** **代码-文档强制同提交卡点（co-change commit gate）**。借鉴 *Build Systems à la Carte* 与实务判断，代码重构完全可能使既有 SSOT 依然准确，而同时改动文档也仍可能写错关键声明；在 `tools/ssot-precommit.sh` 里拦截普通外部代码提交会摧毁零开销快路径，并诱发敷衍式文档噪音。
- **准入 Batch 1 验证的三项最小候选：** （A）交接阻断器动作与解除条件保真；（B）写时归并压缩的时态/不确定性/归属保真；（C）位于 `tools/` 的只读显式反向链接查询工具 `tools/ssot-backlinks.py`。三方共同设定前置门禁：**必须先在冻结 `v5.23` 基线上复现真实失败，再决定是否改动协议；若基线已通过，则停止协议改写。**

## 三、Batch 1 实证结果：基线预筛（12 次隔离会话）与工具吸收

### 1. `v5.23` 基线预筛结果（保持协议 `5.23` 不变）

在 Linux `bwrap` 沙箱、隔离 `CODEX_HOME` 与官方 `install.sh --quickstart --agent codex --scope project` 接线条件下，使用授权低价模型 `gpt-6.1-terra`（`medium`，`codex-cli 0.172.0`）对固定提交 `c820164`（`skills/` 树哈希 `51a343ffd717ea818b0bcccd7eacccd7ebd6abf81c7013d39c6fe62913f6ea1a`）执行了两轮共 **6 组基线探针、12 次完成会话**（总计 `1,119,036` 输入 token，含 `970,240` 缓存输入与 `148,796` 未缓存输入、`9,426` 输出 token；另在测试脚本初始调试阶段记录了 5 次零 token 失败启动——4 次因沙箱未绑定输出路径报 exit 1、1 次因未透传代理环境变量超时——均按 [`METHOD.md`](../tests/benchmark/METHOD.md) 全量留痕）。完整脱敏回执见 [`tests/benchmark/results/2026-11-27-external-failure-prescreen-v5.23.json`](../tests/benchmark/results/2026-11-27-external-failure-prescreen-v5.23.json)。

| 探针 | 测试目标与来源论文 | 实测结果（`v5.23` 基线） | 独立审计保留意见（Codex Astra Round 2） |
|---|---|---|---|
| `A1_handoff_blocker` | 单跳交接阻断器保真（`2608.24569` / `2611.06545`） | **通过**：写手写清授权起草、阻断发布动作与 `FIN-412` 签批条件；冷接手完成草稿且保持 `webhook_v2_prod: false` 与发布说明未动 | 原始 `SSOT/release-policy.md` 仍对读者可见，不能单独隔离交接文件贡献，故补测 `A2` |
| `A2_multihop_blocker` | **加压**：2 跳压缩交接 + 归属转移，移除 `release-policy` 不变量拐杖 | **通过**：Hop 2 压缩交接保留门禁；Hop 3 冷接手停在门禁前（`webhook_v2_prod: false`），并独立指出代码未校验 `INV-01` 类型 | Hop 3 将原话“Ops/Finance 负责跟进 FIN-412”表述为“Ops/Finance 签批”（轻微措辞漂移，未改动作），留作 Batch 2“经办人 vs 签批人”专项对照 |
| `B1_compaction_f4` | 格式 4 温层压缩的临时/传闻/常设规则保真（`2609.36457` / `2606.29279`） | **意图决策通过**：温层从 `6,400 B` 压至 `661 B`（`-89.7%`），完整保留 Rae 临时窗口、Sam 未确认消息与 Lin 常设签批；冷读者 3/3 答对 | **暴露真实缺陷**：单文档快路径直接整文件复制为冷归档 `approvals-history.md`，把 **36 条重复验证回执（`5,472 B`）** 留进了冷档，违反 `v5.23` 删除回执规则；转为 Batch 2 头号实验项 |
| `B2_compaction_f5` | 格式 5 固定单文件快路径压缩 | **产物与路由通过**：零越权建文件、删除回执、保留三类陈述且冷读者 3/3 答对 | 测试夹具接线漏替换 `ENTRY`，致写读双方多查了一次 `ENTRY`；**不计入洁净路径成本声称**，已在 `B3` 修复 |
| `B3_subtle_lapse_f5` | **加压**：正确接线 `CONTEXT.md`，无“临时/未确认”明示词，仅用进行体 `"Rae is covering..."` 与传闻词 `"Reportedly"` | **意图决策通过**：仅 3 次工具调用、零越权建文件，自动保留进行体日期与未确认归属；冷读者拒绝自动派单给 Alex 并正确路由其余两单 | 冷历史末尾保留了 1 行验收摘要（样本数/0 差异/exit 0），属第二例回执残留信号，并入 Batch 2 头号实验项 |
| `D1_stale_premise` | `STALE` 过时前提抗干扰（`2605.06527`） | **通过**：拒绝修改已废弃的 SMS 桩代码，指出已确认的 Push-only 规则并请示下一步 | 需与“合法授权反转”配对才能构成完整双向测试，记入 Batch 2 |

**协议裁决：** 在全部 6/6 探针上，`v5.23` 均未复现候选 A（阻断器软化致越权执行）或候选 B（时态/不确定性扁平化致错误路由）所针对的决策失败。遵循预注册门禁与 `2608.11888` 反过度程序化原则，**不修改 `v5.23` 协议、不消耗热路径词数预算、不发布 `5.24`**；仅把本次实际观察到的“单文档快路径冷档回执残留”与“经办人/签批人分离”转入 Batch 2 验证。

### 2. Batch 1 吸收产物：`tools/ssot-backlinks.py`

受 `okf-agent-memory`（`--for-path`）、`projectmem` 与 `Graphify` 启发并经两轮多模型收窄，我们在 `skills/` 之外新增可选零闲置开销工具 [`tools/ssot-backlinks.py`](../tools/ssot-backlinks.py) 与回归测试 [`tests/test-backlinks.py`](../tests/test-backlinks.py)（已接入 `.github/workflows/ci.yml`）：

- **定位与边界：** 仅扫描调用方显式传入的已授权 Markdown 源文件，在当前工作树上解析显式本地链接并按目标路径反向归组，输出 `源文件:行号 [所在标题] -> 原始链接`（引用定义显式标注 `(reference definition)`）；**不遍历目录、不 `stat`/读取目标文件、不触发 Git 钩子、不调用模型**。零匹配时明确输出 `no explicit link in the selected sources`（绝不声称“无约束”）；出现缺失/无权/软链拒绝/非 UTF-8 源文件时输出不完整覆盖提示并返回退出码 `3`（参数错误返回 `2`，完整扫描含零匹配返回 `0`），并保留已成功扫描源的部分命中。
- **Codex Astra Round 2 全部 8 项安全与解析加固：** 采用 `root_fd` + 逐级 `O_NOFOLLOW` + `fstat` 常规文件校验消除 TOCTOU 与符号链接逃逸；分离源文件校验与目标词法归一化（不改写 POSIX 反斜杠、支持 `--root` 别名与跨 `cwd` 调用）；先剥离 HTML 注释（以空格替代防止拼接伪链接）再识别围栏与块引用围栏/缩进代码块；单遍内联扫描器正确处理反斜杠转义、跨行反引号代码段、嵌套括号/带链接图片 `[![alt](img)](dest)`、含转义引号的链接标题，排除脚注 `[^id]:`，保留 `C#` 标题与多行 Setext 标题，并对终端输出转义控制字符。
- **真实对照复现（通过实用性门禁）：** 在本仓独立复现中，单一文件 `tests/benchmark/METHOD.md` 同时指向两个同名 `README.md`，工具一次准确区分 `tests/benchmark/README.md`（第 9 行）与 `tests/context/README.md`（第 14 行）；在 13 份维护文档中查询 `tests/benchmark/README.md` 精准返回 4 条显式链接（同等范围 `rg -nF README.md` 返回 22 行含 18 行需剔除项）；查询 `skills/ssot-preflight/references/writing-memory.md` 在一次调用中统一解析 4 种不同相对写法并附标题定位（全路径 `rg` 为 0 命中）。

## 四、Batches 2–4 长期吸收路线图（带可观察重开条件与拒绝边界）

外部论文或开源特性本身**永不自动触发改动**；每一项均须由真实消费失败或可观察缺口打开，并遵循最小归属者与拒绝边界：

| 批次与外部来源 | 可观察重开条件（Trigger） | 负责归属者与最小验证实验 | 停止或拒绝边界（Reject / Stop） |
|---|---|---|---|
| **Batch 2 · 单文档快路径归档回执清理**（本次预筛 `B1`/`B3` 实证暴露） | **当前已打开**：`B1` 冷归档残留 36 条回执（`5,472 B`），`B3` 冷尾残留 1 行验收摘要，且 `B2` 曾出现 `ENTRY` 接线缺陷 | 评测维护者先补齐安装接线自检与全产物（含冷归档）回执残留评分，在保留唯一旧理由的对照下复验 `B1`/`B3` 与 `T1` | 若留出对照未复现实质问题则停止；仅当单文档快路径定向候选能在不删持久证据、不增洁净路径读取的前提下根治残留时才考虑协议微调 |
| **Batch 2 · `Authorization Drift` (`2611.09113`)、`Specification Satisficing` (`2611.16289`)、交接软化与自造政策** | 交接混淆“经办人”与“签批人”（`A2` Hop 3 已现苗头），或冷接手仅靠保守拒绝即可过关 | `tests/benchmark/` 交接维护者构建“经办人与签批人分离 + 未签批/合法签批双向用例 + 必做授权任务”夹具，分别评分写手文本与冷接手动作 | 拒绝任何编造批准、误认签批人、压制合法工作、或在合法放行后仍重复追问的候选；常规任务增加强制二次自审直接否决 |
| **Batch 2 · `TOKI` (`2606.06240`)、`Nous` (`2606.22030`)、`STALE` 与 `LAPSE`** | 生效日期、记录日期与决策权错配导致按错日执行，多份转述同一传闻被当作独立佐证，或 Agent 抵制合法授权修正 | 评测维护者与决策文档 owner 构建“生效日/记录日/决策权独立变化 + 重复传闻 vs 单一正式任命 + 合法反转对照”夹具 | 若既有 owner 已能给出正确新旧答案并支持合法变更则停止；拒绝强制时间戳 schema、置信度分数或重复确认 |
| **Batch 2 · `Compaction Laundering` (`2610.29869`)** | 授权轨迹显示摘要或导入文本获得批准地位，或宿主压缩抹除原始消息角色 | 宿主适配器 owner 核验角色保留；Doctor 维护者核验格式 4 可用证据采纳，并以“已正式登记的既有规范决定”作正例对照 | 序列器破坏的来源元数据由宿主修复；拒绝试图用提示词还原丢失角色或因原聊天不可得就废除既有合法决定的协议改动 |
| **Batch 2 · `Context Has a Price` (`2611.22238`)、`Evaluating AGENTS.md` (`2602.11988`)、`Agent Skills Can Be Harmful` (`2608.11888`)** | 任何候选改动默认读写/工具调用，或声称“缩短文件即可省成本” | 评测成本 owner 对比普通文档、冻结基线与候选，同时计入写手 + 预期读者次数、缓存/未缓存输入、输出、工具字节、往返、耗时与人工返工，并隔离或披露前缀缓存共享 | 若正确率下降、收益依赖缺乏依据的超高复用频次，或常规任务多出无收益验证轮次，直接否决 |
| **Batch 2 · `MemoryArena` (`2602.16313`)、`LongMemEval-V2` (`2605.12493`)** | 冷接手仅复述记忆事实却未完成依赖该事实的下游产物仍能通过现有裁判 | 交接评测 owner 增加跨步依赖任务（下游可执行产物必然依赖上游决策）并配无记忆/旧记忆基线 | 若外部套题无法区分“背出事实”与“完成工作”，或既有交接用例已能区分，则不引入新套题 |
| **Batch 3 · `Catastrophic Remembering` (`2608.11095`)、`Length Is Cheap, Competition Is Not` (`2611.04169`)** | 维护者因旧理由缺失而不敢退役规则，或现行 owner 存在时同格式过时竞争陈述仍压倒现行真值 | 消费文档 owner 保留最后一份有源理由或修复路由；用“同长度中性填充 vs 同格式竞争旧陈述”对照验证 | 拒绝按年龄或字节数自动裁剪、拒绝杜撰理由、拒绝把“每条决定必填理由字段”强加给所有仓库 |
| **Batch 3 · `okf-agent-memory` 与 `Graphify`** | 两次真实授权的路径影响查询在使用 `tools/ssot-backlinks.py` 与有界 `rg` 后仍漏掉适用 owner | `tools/` 维护者对照显式链接、可选消费侧自维护 `code_refs` 与单独标注的推断边，由 owner 复核真值 | 拒绝强制元数据字段、拒绝把推断边当约束、拒绝把空结果当放行许可、拒绝提交前同改卡点 |
| **Batch 3 · `QMD`、`SAG-Mem` (`2611.33124`)、`OpenViking`、`tigerless-labs/agent-memory`** | 两次独立的真实授权空间查询在标题、路由与有界 `rg` 后仍漏查已存在的证据（仅空间体量大不足以重开） | `tools/` 维护者在漏查决策上依次对比目录摘要、可重建本地词法索引与一次词法扩展，并计入更新、删除与重建成本 | 停在能修复漏查的最便宜方法；拒绝过时/已撤回命中、隐蔽扩权扫描、总任务成本上升，或强制守护进程/向量服务/第二事实源 |
| **Batch 3 · `AgentMemoryRepo`、`Hindsight`、`PowerContext`、`SwarmVault`** | 两次授权人工 Doctor 审查找回 owner 认可的重要遗漏，或提议改动无法追溯至来源版本 | Doctor 维护者与命名 owner 试行一次“仅提议”离线复核（附证据定位器、范围、来源修订号与显式处置），计量采纳价值与审阅耗时 | 拒绝无人值守自动晋升或删除、拒绝无留存授权复制原始聊天、拒绝低价值周期提案噪音，或需要第二存储才知现行规则 |
| **Batch 3 · `projectmem` (`2606.12329`)、`ReasoningBank` (`2509.25140`)、`ACE` (`2510.04618`)** | 后续执行者在已有任务或 `gotchas.md` 路由下仍重复踩入已记录失败尝试并产生可计量返工 | 先由消费侧任务/主题 owner 记录失败、根因与重试条件；仅当下一位相关执行者仍漏读时再重开可选范围查询 | 拒绝全局编辑前弹窗警告、拒绝记录所有失败命令流水账、拒绝条件已变后仍阻拦合法重试 |
| **Batch 4 · `SCH` (`2611.24357`)、`Folio` (`2611.16627`)** | 两次授权长会话在既有 SSOT 充分的前提下仍因宿主上下文压缩丢失中间证据并被迫重构 | 单一宿主适配器 owner 试行短状态记录 + 受权限校验的有界原证据句柄，并测试过期、缺失与撤回场景 | 拒绝句柄扩权、撤回后失效、计入采集与恢复后无净省，或要求消费者在 SSOT 重复存放运行时清单 |
| **Batch 4 · `Memoir` 与 `Spec-Kitty`** | 真实分支或 worktree 消费了另一分支的待决决定，或双并发写手互相覆盖 owner / 丢失已接受交接 | 消费仓库与宿主集成 owner 对比既有 Git 标识、任务 owner、worktree 安全软链与分支限定交接 + 显式合并回读 | 若普通 Git 与 owner 路由已解决则停止；拒绝并行记忆 VCS、隐式跨分支晋升或强制工作流 |
| **Batch 4 · `claude-mem`、`TencentDB-Agent-Memory`、`general-agentic-memory`** | 命名消费者在更轻试点后仍持续出现采集或跨会话检索损失，并明确授予单宿主、单范围边界权限 | 宿主集成 owner 试行一个可卸载的只读适配器，验证范围隔离、停用与撤回 | 拒绝环境全域聊天采集、跨用户泄漏、核心技能强依赖，或缺少可停用/可验卸载责任人的试点 |

## 五、可持续的长期“研究 → 实验 → 吸收”运行闭环（零 v2 官僚负担）

为持续推进该长期目标而不引入 v2 式的台账和审计税，本仓库采用四步轻量闭环：

1. **从失败决策出发：** 在既有研究任务中先记清“谁在什么安装版本下做什么失败、更便宜的既有路径是什么”；每条外部线索绑定确切 arXiv 版本或仓库 commit，写明单一可迁移机制、前置条件与一条“照搬会变糟”的反例，淘汰无法改变决策的榜单或综述噪音。
2. **先在冻结基线复现，再测最小替代：** 机械契约进确定性单测与 CI，Agent 行为进冻结配对试验（先基线预筛，复现失败才跑 AB/BA 对照与独立确认用例，出现决定性负结果立即止损撤回）。
3. **单一决策记录与脱敏证据哈希：** 每次批次结论、重开条件与负结果记入一篇带日期的 `docs/YYYY-MM-DD-*.md` 研究报告，机器回执按既有规范脱敏归档至 `tests/benchmark/results/` 并在 [`tests/benchmark/README.md`](../tests/benchmark/README.md#recorded-studies-and-additional-lanes) 登记一行索引。
4. **回到真实使用再校准：** 对已吸收改动抽样观察后续真实任务（记录版本、分母、误触发与返工）；仅当重开条件真正命中时打开下一批，仅当证据改变下一阶段投资重点时更新 [`docs/2026-11-20-context-evolution-route.md`](2026-11-20-context-evolution-route.md)。
