# 消费空间 Antigravity 真实会话审计、20 会话配对实验与检查器精炼（维持协议 `5.24`）

**2026-11-28，我们对近 10 天内跨 6 个在用消费空间（3 个格式 4 开发仓库、3 个格式 5 通用空间，下文全部匿名编号为空间 A–F）的 644 条 Antigravity 真实会话记录及现场 `ssot-check.py` 运行结果做了只读审计（证据层级：`production-resident` 观测审计，零收费模型调用），随后针对暴露出的四类真实高频摩擦设计并执行了 20 次隔离反向平衡 `gpt-6.1-terra medium` 配对实验（证据层级：`live-model-paired-sandbox`，含 14 份零模型前置校准夹具）。** 最终裁决：**（1）撤回 `ssot-closeout/SKILL.md` 措辞改动，维持协议版本 `5.24` 不变**（`+0` 入口词数、`+0 B` 常驻目录与受管指令块），因为配对实证表明 `5.24` 自身在 3/3 直接日期条目改写上已能正确归并，且额外措辞在中文格式 4 确认用例 `C7` 上诱发了文末内联冷尾退化；**（2）零模型上下文代价落地 4 项 `ssot-check.py` 机械检查器精炼**（识别日期列表项流水、格式 5 外部路由折叠、`--since` 改动文件与存量错误分栏、`check_codex_chain()` 跳过冷归档含中文 `*归档` 目录），零 CI 预算扩容（`ssot-check.py` `100,644 / 102,400 B`，全部脚本 `130,756 / 131,072 B`）；**（3）补齐两项极简精准引导**——在 [`memory-model.md`](../skills/ssot-preflight/references/memory-model.md#5-invariants) 明确将主题分片列表置于跨主题行上方，并在 [`INSTALL.md`](../INSTALL.md#1-resolve-the-installation-choices) 补充 Monorepo 嵌套子项目 `SSOT/` 的根安装与路由说明。完整脱敏机器回执见 [`tests/benchmark/results/2026-11-28-consumer-audit-and-checker-v5.24.json`](../tests/benchmark/results/2026-11-28-consumer-audit-and-checker-v5.24.json)（本地持久证据归档 `2026-11-28-consumer-audit-and-checker-v5.24.tar.gz`，共 `743` 文件、`2,925,159 B`，SHA-256 `c12b3aead310ecf39e5b00d1618b6905994023a52be4eca7ea191b14de1e25a7`）。

## 一、立题主张卡（遵循活论文维护契约）

- **具体场景钩子：** 2026-11-28，在一个已运行 `v5.24` 的格式 5 个人/组织主空间（空间 B）的真实 Antigravity 会话中，负责人拍板推翻了一条早期媒体发布禁令。Agent 加载了 `ssot-preflight` 与 `ssot-closeout`，更新了 `decisions.md`（`36,350 B` / `19,591` 字符、**61 条 `- **2026-XX-XX ...**` 日期列表项、0 个日期标题**），并运行 `ssot-check.py README.md`，却既没有把被替代的旧条文归并到冷历史，也没有向用户转述 `compaction candidates` 建议，在第二轮甚至直接执行 `ssot-check.py README.md | tail -n 3`。同期在重型 Monorepo 格式 4 子项目（空间 A）中，`ssot-check.py SSOT --since HEAD` 在 10 天内因未触及历史文档的 10 处断链连续报错 27 次，迫使 Agent 养成加 `2>&1 || true` 的盲跳习惯；且 6/6 从 Monorepo 根启动的大型长会话未发现子目录内的 `.agents/skills/ssot-*`，其中一轮在 `SSOT/README.md` 用 `rg` 查找界面不变量时直接漏掉了排在 40 余行跨主题表下方的主题分片。
- **核心主张与反证条件：** 先在配对实验里同时检验“检查器机械补盲 + `ssot-closeout/SKILL.md` 条款增补”相对 `5.24` 基线的净收益；仅当协议条款自身在质量与安全反例上不可替代地胜出且无跨格式退化时才升版，若主收益来自检查器且协议改写引发反效果，则撤回协议改动、只吸收零上下文代价的检查器与文档修复。
- **一手同行坐标：** 承接 `v5.23`（[主动整理与分层报告](2026-11-26-auto-compaction-layering-v5.23.md)）、`v5.24`（[Batches 2–4 报告](2026-11-27-external-research-batches2-4-v5.24.md)）及 *Context Has a Price*（`arXiv:2611.22238`）、*Catastrophic Remembering*（`arXiv:2608.11095`），将验证视角从合成日期标题夹具推进到真实消费现场的日期列表流水、检查器信噪比与 Monorepo 嵌套发现边界。
- **活论文落点：** 更新 [`paper/LIVING-PAPER.md`](../paper/LIVING-PAPER.md) 第 6 节表 3（记入撤回的 `SKILL.md` 日期列表措辞候选）与第 7 节（补充 Antigravity 真实会话观测边界）。

## 二、真实消费空间现场审计发现（644 会话 + 6 个活跃空间，零模型费用）

对近 10 天 644 条 Antigravity 消费会话与 6 个活跃空间的只读盘点，暴露出五项合成测试夹具未曾复现的真实工程摩擦：

| 编号 | 现场观察到的具体摩擦（匿名空间） | 根因定位 | 责任归属与本次处置 |
|---|---|---|---|
| 1 | 空间 B（格式 5）的 `decisions.md` 达 `36,350 B` / `19,591` 字符、含 **61 条日期列表项**与 **0 个日期标题**，`5.24` 检查器仅报泛化的 `10 sections -> propose split/consolidation`，未给出日期流水归并建议 | `ssot-check.py` 仅统计带日期的 Markdown 标题（`DATE_RE`），对真实中英文文档最常见的 `- **YYYY-MM-DD ...**` 日期列表项完全盲视 | **`ssot-check.py`（已修复）：** 新增 `DATED_BULLET_RE`，在活跃温层（排除围栏与文末冷尾）计数日期列表项，使空间 B 立即精确报出 `61 dated entries -> consolidate + cold archive (or ## History (cold) if layout fixed)` |
| 2 | 空间 B 运行 `ssot-check.py README.md` 共输出 37 行，其中 **27 行（73.0%）** 为逐条刷屏的 `INFO external-space route not read`，诱使多轮会话改用 `\| tail -n 3` 盲截输出 | 格式 5 跨空间链接在 `check_link()` 里逐条打印，无折叠上限 | **`ssot-check.py`（已修复）：** 超过 3 条时折叠为 1 行按文件汇总的 `INFO`，空间 B 输出从 **37 行降至 11 行（`-70.3%`）**，零信号损失 |
| 3 | 空间 A（格式 4 子项目）近 10 天出现 **27 次 `ssot-check.py SSOT --since HEAD` 退出码 1**，全由未触及的旧历史文档里的 10 处 `.gitignore` 断链引起，诱使多轮会话加 `2>&1 \|\| true` 忽略全部报错 | `--since <commit>` 未区分“本次改动文件引入的错误”与“未触及文件的存量错误” | **`ssot-check.py`（已修复）：** 保持 `exit 1` 不放松门禁，同时在 `--since` 报错时增打 1 行 `INFO . since <commit>: <T> error(s) in touched files, <P> pre-existing error(s) in untouched files` |
| 4 | 空间 C（格式 5）运行含 Codex 32 KB 链检查（提交 `8057896`）的 `ssot-check.py` 时，冒出 **74 条 `WARN`（占全部 80 行输出的 92.5%）**，全部落在历史验证归档目录 `docs/.../03_验证归档/.../AGENTS.md` | `check_codex_chain()` 未跳过冷归档目录，且 `is_cold_dir_part()` 未识别以 `归档` 结尾的中文复合目录名（如 `03_验证归档`） | **`ssot-check.py`（已修复）：** `is_cold_dir_part()` 增加 `part.endswith("归档")`，且 `check_codex_chain()` 跳过冷归档子目录；空间 C 误报从 **74 条降至 0 条**（`0 error(s), 0 warning(s)`） |
| 5 | 空间 A 作为 Monorepo 嵌套子项目时，6/6 从仓库根启动的大型长会话虽打开了 `SSOT/README.md`，却 **0/6 发现并加载子目录内的 `.agents/skills/ssot-*`**；其中 1 轮在入口表执行 `rg` 漏掉了排在 40+ 行内联表下方的主题分片 | Monorepo 根启动不会自动发现深层子目录的 `.agents/skills/`；同时分片列表若置于长内联表底部，首读截断或局部 `rg` 极易漏看 | **文档与引用精准补强（已落地）：** 在 [`INSTALL.md`](../INSTALL.md#1-resolve-the-installation-choices) 补充 Monorepo 嵌套子项目根安装/全局安装与路由说明；在 [`memory-model.md`](../skills/ssot-preflight/references/memory-model.md#5-invariants) 明确将主题分片列表置于跨主题行上方 |

## 三、冻结反向平衡配对实验（20 次 `gpt-6.1-terra medium` 独立会话）

为避免凭直觉往 `SKILL.md` 加条款，我们在隔离沙箱中冻结基线 `5.24`（`00560ca`，`skills/` 树 SHA-256 `ad3cdd010e57fb93...`）与候选版（含 `ssot-closeout/SKILL.md` 第 12/14 行措辞 + `ssot-check.py` 改动，树 SHA-256 `198b013998dce60f...`），先完成全部 14 份安装夹具与正/改写/负例评分器的零模型前置校准（`100%` 通过），再执行两批共 7 组反向平衡配对（20 次原生会话：`run_r1` 5 组 10 写手 + 6 冷读者，`run_confirm_r1` 2 组 4 写手）：

| 配对用例（执行顺序） | 基线 `5.24` 表现 | 候选版表现 | 归因判定 |
|---|---|---|---|
| `C1_f5_zh_dated_bullets_supersede`（B→C，写手+冷读者） | 写手过（温层缩至 `637c`，0 回执，`eff01=31,787.4`）；冷读者语义 4/4（`66,599` 输入） | 写手过（温层缩至 `619c`，0 回执，`eff01=32,164.4`）；冷读者语义 4/4（`118,559` 输入，随机多读未改动的 `context-spaces.md`） | `5.24` 写手自身已能归并中文日期列表流水；双臂冷读者全对 |
| `C2_f5_en_multiowner_compaction_relay`（C→B，写手） | **写手失败**：`backlog-notes.md`（`10.1k` 字符、14 条日期列表）未被基线检查器检出，未转述整理建议；`111,226` 输入 / `57,598 B` 工具输出 | **写手通过**：零打开未触及文件、准确转述 1 行整理建议；`101,165` 输入（`-9.05%`）/ `36,885 B` 工具输出（**`-35.96%`**） | **检查器 `DATED_BULLET_RE` + 外部路由折叠是决定性机制** |
| `C3_f4_en_dated_bullets_offload`（B→C，写手+冷读者） | 写手过（独立 `release-policy-history.md`，0 回执，`eff01=32,152.4`）；冷读者语义 4/4（`eff01=18,946.6`） | 写手过（独立 `release-policy-history.md`，0 回执，`eff01=25,867.8`）；冷读者语义 4/4（`eff01=18,811.2`） | 双臂均通过，候选写手未缓存输入与 `eff01` 略省 |
| `C4_f5_safety_active_bullets_2024`（C→B，安全反例） | 写手过（保留全部 6 条 2024–2026 活跃条目，零按龄降冷，`eff01=20,267.8`） | 写手过（零按龄降冷，`eff01=20,128.6`） | 100% 守住“不按年龄降级活跃规则”红线 |
| `C5_f4_control_clean_single_edit`（B→C，洁净对照） | 写手过（0 多余冷文件，`eff01=29,511.0`）；冷读者 2/2（`eff01=15,370.4`） | 写手过（0 多余冷文件，`eff01=20,420.8`）；冷读者 2/2（`eff01=15,627.4`） | 零回归 |
| `C6_f5_zh_multiowner_relay`（B→C，未见中文确认） | 写手过（因 `>24 KB` UTF-8 触发泛化拆题提示，`eff01=28,715.2`），输出刷 8 行外部路由 | 写手过（精准诊断 `12 dated entries -> consolidate + cold archive`，8 条外部路由折叠为 1 行，`eff01=28,540.8`） | 证明 `5.24` 只要收到检查器信号就能在格式 5 正确转述，无需扩写 `SKILL.md` |
| `C7_f4_zh_dated_bullets_offload`（C→B，未见中文格式 4 确认） | **写手通过**：独立新建 `deploy-policy-history.md`，温层缩至 `381c`（`109,429` 输入，`eff01=30,757.8`） | **写手未达标（`sep_cold=False`）**：退化为文末 `## 历史记录（冷读）`（全文件留存 `10,161c`，`132,064` 输入 `+20.7%`，`eff01=33,632.8`） | **直接否决 `ssot-closeout/SKILL.md` 措辞改动** |

**聚合账本与诚实裁决：** 在首轮 5 组（16 会话）上，候选写手通过率 `5/5`（基线 `4/5`，败于 `C2`）、写手总 `eff01` 降 `-8.64%`（`146,757.4 → 134,072.2`）、未缓存降 `-15.60%`、工具字节降 `-15.53%`，全部 `6/6` 冷读者人工核验语义全对（原正则 `q2` 误报系日期中文空格与英文月名改写，双口径均已载入回执 JSON）。但次轮 `C6`/`C7` 确认清楚拆开了因果：`C2` 的胜出源于 `ssot-check.py` 补上了日期列表项检出与外部路由折叠，而 `ssot-closeout/SKILL.md` 的额外措辞既非 `C1`/`C3`/`C6`/`C7` 所需，还在 `C7` 上诱发了格式 4 文末内联冷尾退化。据此我们严格遵循 [`CONTRIBUTING.md`](../CONTRIBUTING.md#changing-the-protocol) 第 1–4 问：**撤回 `SKILL.md` 改动、保持协议 `5.24` 简洁不变，只合入经过 live 与单测双重验证的 4 项 `ssot-check.py` 精炼、分片置顶说明与 Monorepo 安装指南**。
