# 08 · 渐进确定性与缓存

目标：同一件事第二次做时，**不该再花模型的钱和风险**。Skyvern 的做法是把成功的 agent run 渐进固化为可执行脚本（`run_with: agent` → `run_with: code`），本篇把它翻译成软件交付语义。

## 两级执行

| 级别 | 谁执行 | 适用块 | 成本/方差 |
|---|---|---|---|
| `agent` | 角色模型按 `goal` + `complete_criterion` 推理执行 | 首次出现的块、需要判断的块 | 高方差，可探索 |
| `code` | `script` / `check` 块按 `commands` 确定性执行 | 已固化、判据可结构化的块 | 零方差，可复算 |

规则：**能写成 `commands` + 期望退出码的验证，不要留给模型即兴发挥。** 模型只在探索、判断、修复时上场。

## 渐进缓存（Progressive Caching）

Skyvern 的事实（`references/skyvern/skyvern/core/script_generations/CLAUDE.md`）：

1. 只有**本次真正执行过**的块才被固化（`blocks_to_update`，`skyvern/forge/sdk/workflow/service.py`）；未执行的块保持未缓存。
2. 进入 `run_with: code` 的门槛是**所有顶层块**都有脚本条目且 `run_signature` 非空（`skyvern/schemas/scripts.py:234`：`run_signature` 是"执行该块的代码语句"）；缺一个就整体回落 `agent`。
3. 检测新块有两条互补机制：执行跟踪（跑过但没缓存）+ 定义比对 `missing_labels`（定义里有但没缓存）。无分支时两者等价，有分支时不等价。
4. 缓存生成在**块完成时**触发（`_generate_pending_script_for_block`，`service.py:6262`），不是每个动作后触发——把生成频率降低 10–50 倍。

对应到我的流程：

- 一个块第一次由角色成功完成后，才允许把它降级为 `script`/`check`；**不得凭设计意图预先固化未验证过的步骤**。
- 固化产物必须记录 `run_signature`：精确命令 + workdir + 期望退出码 + 关键输入哈希。签名不完整 = 未固化。
- 回落规则同样成立：任一顶层块未固化，整条 run 仍按 `agent` 语义执行，不允许"半自动"混跑却宣称确定性。

## 不缓存的块

Skyvern 明确排除 `conditional`、`wait`、`code` 等（`BLOCK_TYPES_THAT_SHOULD_BE_CACHED`，由 `skyvern/services/workflow_script_service.py` 定义并在 `service.py:259` 复用）。我的等价排除表：

| block_type | 是否可固化 | 原因 |
|---|---|---|
| `check` / `script` | 是（本身就是确定性） | 命令 + 退出码 |
| `intake` / `recon` / `spec` / `decision` / `plan` | 否 | 依赖当次意图与仓库事实 |
| `implement` | 否 | 内容每次不同 |
| `review` | 否 | 独立判断，固化即失去独立性 |
| `conditional` | **否** | 必须在运行时求值；分支内可缓存块执行后才各自固化 |
| `wait` / `approve` / `release_check` | 否 | 人工 `*` 边界，代签即失效 |
| `integrate` / `test` / `verify_ui` / `smoke` | 部分 | 命令可固化，**结论**必须由角色签名 |

## 分支的渐进固化

有 `conditional` 时，一次 run 只走一条分支，定义却包含全部分支：

```text
Run 1 走分支 A → 固化 A 内已执行块
Run 2 走分支 B → 固化 B 内已执行块，A 的固化结果保留
…最终所有被执行过的分支都有固化产物
```

因此：**"定义里有的块"≠"已固化的块"**。判断一条工作流是否可全自动跑，必须看每个分支是否都至少被执行并固化过一次，`state.yaml` 记录 `cached_labels` 与 `uncached_labels` 两个列表。

## 固化产物的失效

固化不是永久授权。出现以下任一情况，对应 `run_signature` 立即作废，块回落 `agent`：

- 命令、workdir、期望退出码、关键输入或依赖版本变化；
- 目标块被审核要求修改（Finding 未关闭前不得固化）；
- 环境重建、数据库/凭据/分支基线变化（`AIW_ENV_STALE`、`AIW_BASELINE_MISMATCH`）；
- 连续两次固化执行失败（Skyvern 的等价约束是脚本复审上限与自愈上限：`skyvern/services/script_review_cap.py`、`skyvern/services/self_heal_cap.py`，超限即停止烧钱升级给人）。

上限规则（照搬其精神）：同一块自愈尝试 ≤2 次；第 3 次一律 `BLOCKED` 并升级。固化执行的失败计数按天/按块累计，超限后停用该固化产物而不是继续重试。

## 与证据的关系

固化块同样要产出证据，且证据必须来自**本次真实执行**：命令、退出码、输出摘要、`tested_sha`。缓存命中不等于证据命中——`evidence.md` 里的旧记录不能因为"命令一样"就被复用到新 SHA 上（见 `05-state-and-evidence.md` 的有效性判定表）。
