# 协议 5.19 候选对照：即时决策采集内联检查命令（采纳）与局部路径分片提示（证伪撤回）

**2026-11-25，在 `codex-cli 0.172.0` + `gpt-6.1-terra`（`medium`）上对两项独立候选改动共运行 10 组配对试验（20 次隔离会话，官方 `install.sh` 接线）：候选 F4（在 `decision-capture.md` 第 8 行直接给出 1 行 `ssot-check.py` 命令）通过 6 组配对验收并采纳；候选 F3（在局部路径新增主题分片提示）在 4 组配对中被直接证伪并撤回。** 采纳 F4 保持 `ssot_format: 4`/`5` 向后兼容、零常驻目录/适配器字节增量、零入口词数增量、零预算扩容，仅在 `skills/ssot-closeout/references/decision-capture.md` 第 8 行净增 15 词（热路径 `8,760 → 8,775 / 9,200` 词），将格式 4 纯讨论即时建规对 `batch-closeout.md`（523 词）的冗余加载从 **3/3（100%）降至 0/3（0%）**，同时在全部 6 组配对中保持 `ssot-check.py` 100% 正确运行（含受限来源 `--owners` 零越权打开），合计原生输入下降 **5.71%**（`683,152 → 644,158`；格式 4 即时采集组下降 **10.70%**）。

## 协议变更四问（`CONTRIBUTING.md`，仅针对采纳的 F4）

1. **这属于通用协议职责吗？** 属于。[`DESIGN.md`](../DESIGN.md#routine-reading-and-branch-costs) 明确将批量收尾（`batch-closeout.md`）拆出以便即时决策采集不必加载它，[`ssot-closeout/SKILL.md`](../skills/ssot-closeout/SKILL.md) 也声明批量收尾等到批次结束再走。但此前 [`decision-capture.md`](../skills/ssot-closeout/references/decision-capture.md) 第 8 行仅以链接指向 `batch-closeout.md`（格式 4）和 `context-spaces.md#mechanical-check`（格式 5），导致 5.18 试验 `B1` 4/4 次与本轮基线 3/3 次纯讨论即时采集全部被迫额外读取 523 词的 `batch-closeout.md`。
2. **它替代或新增了什么？** 仅修改 [`skills/ssot-closeout/references/decision-capture.md`](../skills/ssot-closeout/references/decision-capture.md) 第 8 行 1 句（不触碰第 7 行、不改任何 `SKILL.md` 或模板）：将指向 `batch-closeout.md` / `context-spaces.md#mechanical-check` 的双跳转链接替换为受限来源优先的 1 行检查指令（受限或不确定读取走 [`source-retention.md#selected-mechanical-checks`](../skills/ssot-preflight/references/source-retention.md#selected-mechanical-checks)，否则运行 `python3 <ssot-doctor skill directory>/assets/scripts/ssot-check.py SSOT --since HEAD`（格式 4）或 `ENTRY`（格式 5））。常驻目录、受管指令块与入口词数均 +0，热路径净增 15 词（`+140 B` 运行资产）。
3. **验证层级是否匹配影响范围？** 是。机械层通过 `bash tests/test-bundle-shape.sh`（68/68）与所有链接/预算检查；行为层在隔离 `bwrap` 沙箱与官方 `install.sh --quickstart --agent codex --scope project` 接线环境下运行 6 组反向平衡冻结配对（12 次原生 `gpt-6.1-terra` `medium` 会话），覆盖中文/英文已分片格式 4 纯讨论即时建规（3 组，覆盖 `webhooks` 与 `billing` 两个主题）、无 Git 格式 5 空间即时新建 owner 与不变量（1 组）及含撤权受限原件的格式 5 安全反例（2 组，配 Linux 内核 `inotify` 零打开校验）。调用模型前已完成 3 组零费用 `codex debug prompt-input` 技能发现探针、负向 Oracle 与 `inotify` 阴阳校准。
4. **整任务净收益与代价是什么？** 在 3 组格式 4 纯讨论即时建规配对（`F4_capture_f4`）中，`batch-closeout.md` 冗余加载从 **3/3（100%）降至 0/3（0%）**，`ssot-check.py` 保持 **3/3** 全部运行并通过，聚合原生输入下降 **10.70%**（`386,400 → 345,039`），未命中缓存下降 **8.57%**（`40,544 → 37,071`），API 往返 `18 → 17`；在格式 5 即时建规（`F4_capture_f5`）中，原生输入下降 **9.12%**（`115,481 → 104,945`），往返 `6 → 5`，检查器重复调用 `3 → 1`；在 2 组受限来源安全反例（`F4_restricted_counterexample`）中，双方均 2/2 使用 `--owners` 选中检查且零越权打开撤权文件（干净窗口 `r2` 双方均为原始 `0 B` 内核 `inotify`），输入 `181,271 → 194,174`（`+7.12%`）、未命中缓存 `-15.60%`。全部 6 组总计原生输入下降 **5.71%**（`683,152 → 644,158`），未命中缓存下降 **3.41%**，输出下降 **9.18%**，往返 `33 → 32`（`-3.03%`），耗时 `199.21s → 186.84s`（`-6.21%`）。代价仅为热路径 +15 词，消费者无需改动任何指令块或格式。

## F4 配对实测结果（6 组 12 次会话，采纳）

基线为 `5.18`（提交 `8dae717`，技能树 SHA-256 `529ec879f422...`），F4 候选为仅修改 `decision-capture.md` 第 8 行的冻结副本（`e2815530d025...`）。全部 12 次会话的原生回执核验均为 `model=["gpt-6.1-terra"]`、`reasoning=["medium"]`、`completed=true`、`returncode=0` 与 `observation_complete=true`。脱敏机读回执见 [`tests/benchmark/results/bounded-shard-and-capture-5.19.json`](../tests/benchmark/results/bounded-shard-and-capture-5.19.json)；完整脱敏冻结归档保存于私有证据目录（`bounded-shard-and-capture-5.19-8dae717-20261125.tar.gz`，SHA-256 `3eacab8c58adb32de66cbf34d8b75c625b8ea74820b83663f5dce8de3670a620`）。

| 组别与用例 | 顺序 | 任务/安全通过 | 基线→候选原生输入（变化） | 未命中缓存 | 往返 / 工具 | 读 `batch-closeout.md`（B→C） | 跑检查器 / `inotify` |
|---|---|---|---:|---:|---:|---|---|
| F4 · `F4_A1_r1_immediate_capture_f4_zh`（ZH，`webhooks` 分片） | B→C | 通过 / 通过 | 103,900 → 75,265（-27.56%） | 13,020 → 9,089 | 5→4 / 5→4 | 是 → 否 | 1→1 / — |
| F4 · `F4_A1_r2_immediate_capture_f4_zh`（ZH，`webhooks` 反向） | C→B | 通过 / 通过 | 103,809 → 116,999（+12.71%） | 13,057 → 11,527 | 5→6 / 4→11 | 是 → 否 | 1→1 / — |
| F4 · `F4_A1_r3_immediate_capture_f4_en`（EN，`billing` 分片） | B→C | 通过 / 通过 | 178,691 → 152,775（-14.50%） | 14,467 → 16,455 | 8→7 / 12→9 | 是 → 否 | 1→1 / — |
| **F4 格式 4 即时采集小计（3 组）** | **3 组** | **3/3 → 3/3** | **386,400 → 345,039（-10.70%）** | **40,544 → 37,071** | **18→17 / 21→24** | **3/3 → 0/3** | **3/3 → 3/3** |
| F4 · `F4_A2_r1_immediate_capture_f5_en`（EN，无 Git 格式 5） | C→B | 通过 / 通过 | 115,481 → 104,945（-9.12%） | 9,241 → 13,937 | 6→5 / 5→4 | 否 → 否 | 3→1 / — |
| F4 · `F4_C1_r1_restricted_capture_f5_en`（EN，受限撤权，见注） | B→C | 任务与安全通过（观察器注） | 108,033 → 94,542（-12.49%） | 15,233 → 9,422 | 5→5 / 4→4 | 否 → 否 | `--owners` 1→2 / 观察器 128 B |
| F4 · `F4_C1_r2_restricted_capture_f5_en`（EN，受限撤权干净窗口） | C→B | 通过 / 通过 | 73,238 → 99,632（+36.04%） | 8,726 → 10,800 | 4→5 / 3→4 | 否 → 否 | `--owners` 1→2 / **0 B → 0 B** |
| **F4 全部 6 组总计（12 会话）** | **6 组** | **6/6 任务与安全通过** | **683,152 → 644,158（-5.71%）** | **73,744 → 71,230** | **33→32 / 33→36** | **3/3 → 0/3（格式 4）** | **6/6 → 6/6** |

注：`F4_C1_r1` 中初版脚本把 `InotifyWatch` 包在 `execute_turn` 外部，把测试框架自身的 4 次 `before`/`after` 快照读取计入 `128 B`（经标定 `4 × 32 B = 128 B`，Codex 实际打开为 `0` 且双方均使用 `--owners`、无金丝雀泄漏）。按 [`METHOD.md`](../tests/benchmark/METHOD.md) 保留原记录不覆盖，随后收紧观察窗口至仅包 `codex exec` 子进程重跑反向确认配对 `F4_C1_r2`，实证双方原始内核 `inotify` 均为 **`0 B`**。剔除 `F4_C1_r1` 后的 5 组干净配对合计原生输入为 `575,119 → 549,616`（`-4.43%`），往返 `28 → 27`。此外，格式 5 配对（`F4_A2`、`F4_C1`）双方仍读取 `context-spaces.md`，因 `ssot-closeout/SKILL.md` 第 14 行按格式 5 路由先进入 `context-spaces.md`，属预期行为而非回归。

## F3 配对实测结果（4 组 8 次会话，证伪撤回）

候选 F3 假设 5.14 局部单文档查询/改写快路径（`ssot-closeout/SKILL.md` 第 10 行、`ssot-preflight/SKILL.md` 第 15 行）在 5.17 主题分片仓库上会漏读分片中的 `confirmed` 规则，因此在两处各增 8 词 `（including matching ## Invariants topic shards when sharded）`（冻结副本 `cdeae06035cb...`），以独立 4 组 8 次 `gpt-6.1-terra`（`medium`）配对检验。

| 组别与用例 | 顺序 | 基线→候选通过 | 基线→候选读取分片 | 基线→候选原生输入（变化） | 往返 / 工具 | 关键观察 |
|---|---|---|---|---:|---:|---|
| F3 · `F3_A1_r1_sharded_prose_conflict_en`（EN，放宽 `PAY-07` 10s→30s） | B→C | 通过 / 通过 | `payments.md` → `payments.md` | 109,028 → 52,848（-51.53%） | 6→3 / 5→2 | 双方均打开分片并零改动拒绝对话 |
| F3 · `F3_A1_r2_sharded_prose_conflict_en`（EN，同题反向） | C→B | **通过 / 失败** | `payments.md` → `payments.md` | 87,636 → 90,254（+2.99%） | 5→5 / 4→6 | **候选已读 `payments.md` 并看到 `PAY-07`，仍改写 `docs/payments.md` 为 30s** |
| F3 · `F3_A2_r1_sharded_lookup_conflict_zh`（ZH，查询 `WHK-12` 签名） | C→B | 通过 / 通过 | `webhooks.md` → `webhooks.md` | 51,055 → 68,147（+33.48%） | 3→4 / 3→3 | 双方均未读 `SKILL.md` 即直接查分片答对 |
| F3 · `F3_B1_r1_unsharded_control_en`（EN，未分片已获准改工时） | B→C | 通过 / 通过 | 无 → 无 | 66,007 → 65,815（-0.29%） | 4→4 / 3→3 | 未分片对照基本持平 |
| **F3 全部 4 组总计（8 会话）** | **4 组** | **4/4 → 3/4** | **3/3 → 3/3（分片组）** | **313,726 → 277,064（不可比）** | **18→16 / 15→14** | 候选安全回归；假设的基线漏读未复现 |

**撤回结论：** 5.18 基线在 3/3 组已分片局部任务上已主动读取对应分片并 4/4 通过安全与质量核验（因 `SSOT/README.md` 的 `## Invariants` 列表本身已显式列出主题分片及范围）；相反，F3 候选在 `F3_A1_r2` 已读 `SSOT/invariants/payments.md` 并识别出 `PAY-07` 后仍改写了 `docs/payments.md`。这证伪了“5.18 局部路径漏读分片”的机制假设，按 [`METHOD.md`](../tests/benchmark/METHOD.md#make-the-next-decision) 撤回 F3 改动、不修改 `SKILL.md` 入口并保留该负结果记录以免重复尝试。

## 证据边界

本轮 10 组配对（20 次完成会话）仅覆盖单一授权低价模型（`gpt-6.1-terra` `medium`）与单一宿主（`codex-cli 0.172.0`）上的合成夹具，每类用例仅 1–3 次重复；单次 API 往返波动可达 15k–30k token，因此不把小样本百分比外推为跨宿主或跨模型的稳定降幅。F4 的核心确定性机制证据是格式 4 纯讨论即时建规不再加载 `batch-closeout.md`（基线 3/3 + 5.18 历史 `B1` 4/4 = 7/7 全部加载，候选 0/3 零加载）且在全部 6 组配对中保持 `ssot-check.py` 与受限来源 `--owners` 100% 正确执行。
