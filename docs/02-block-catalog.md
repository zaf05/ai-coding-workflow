# 02 · 块类型目录

块（block）是工作流的最小可编排单元。设计取自 Skyvern 的 `BlockType`（`references/skyvern/skyvern/schemas/workflows.py:475`，31 种浏览器自动化块）与 `Block` 基类（`.../workflow/models/block.py:765`），语义换成软件交付。

## 通用字段

| 字段 | 类型 | 必需 | 语义 |
|---|---|---|---|
| `label` | string | 是 | 工作流内唯一（含循环体内），作者可读标识 |
| `block_type` | enum | 是 | 见下表 |
| `next_block_label` | string\|null | 否 | 显式连边；`null` 表示终结。DAG 模式不做顺序回退 |
| `role` | enum | 是 | `planner` / `implementer` / `reviewer` / `tester` / `engine` / `user` |
| `gate` | enum\|null | 否 | `G0`–`G10`；该块产出是哪个门禁的通过证据 |
| `goal` | string | AI 块必需 | 自然语言目标，写"要达成什么可观察结果"，不写实现步骤 |
| `complete_criterion` | string | AI 块必需 | 可观察的完成判据（Skyvern `complete_criterion` 语义） |
| `inputs` | list | 否 | 参数 key 或 `<label>.output` 引用 |
| `output_parameter` | string | 否 | 本块输出键名，供下游 `inputs` 与模板引用 |
| `evidence` | list | `gate` 非空时**必填** | 必须存在并写入的证据路径/锚点，例如 `current.md#Spec`、`evidence.md#REVIEW-001`；缺失由护栏 `evidence_free_gate` 静态拒绝 |
| `commands` | list | `check`/`script` 必需 | `[{cmd, workdir, expect}]`，`expect` 是期望退出码，默认 `0` |
| `star` | bool | 否 | `true` 表示人工判断/授权/外部平台边界，AI 不得代签 |
| `max_attempts` | int | 否 | 有界重试次数，默认 `1`（不重试） |
| `retry_backoff_seconds` | int | 否 | 重试间隔 |
| `continue_on_failure` | bool | 否 | 失败后是否继续流程，默认 `false` |
| `next_loop_on_failure` | bool | 否 | 仅循环体内有效：失败跳到下一次迭代 |
| `timeout_minutes` | int | 否 | 块级超时；超时按 `timed_out` 处理 |
| `error_codes` | list | 否 | 本块可能抛出的业务错误码，必须是 `error_code_mapping` 的键 |
| `circuit_breaker` | object | 否 | `{no_output_minutes: 5, soft_checkpoint_minutes: 30}` |

## 块类型

### 交付主链（12 种）

| block_type | 语义 | 默认 role | 常见 gate | 关键产物 |
|---|---|---|---|---|
| `intake` | 需求接收：用户、场景、目标、非目标、验收方式、授权边界 | planner | G0 | `current.md#Intake` |
| `recon` | 仓库侦察：画像、当前 ref/完整 SHA、脏工作区、既有工具链与流程事实 | planner | G1 | `current.md#Recon` |
| `spec` | 行为规格与验收标准（AC）、UI/技术决策、变更预算 | planner | G2 | `current.md#Spec` |
| `decision` | 关键取舍与决策记录（含风险接受，仅 P2 可接受） | planner | G2 | `current.md#Decisions` |
| `approve` | 人工批准，绑定 Spec 对象修订；**必须 `star: true`** | user | G3 | `evidence.md#APPROVAL-NNN` |
| `plan` | 任务/块 DAG、依赖、所有权、并行边界、切分门禁统计 | planner | G2/G4 | `current.md#Tasks`、`test-plan.md` |
| `implement` | 单块实现：契约与不变量 → 主行为 → 错误/边界/资源生命周期 | implementer | — | diff + `evidence.md#IMPL-NNN` |
| `check` | 确定性检查：单元/组件测试、lint、type-check、构建；记录精确命令与退出码 | implementer | G5 前置 | `evidence.md`（命令 + 退出码） |
| `review` | 独立只读审核 `base_sha..head_sha`，产出 Finding 与 Verdict | reviewer | G5/G8 | `evidence.md#REVIEW-NNN` |
| `test` | 独立测试执行：增量、完整、回归、契约、权限、状态转换 | tester | G6/G7 | `test-plan.md` + `evidence.md#TEST-NNN` |
| `verify_ui` | 真实浏览器 + 视口矩阵 + diff 驱动 QA；页面任务的强制项 | tester | G7/G9 | `attachments/` + `evidence.md` |
| `integrate` | 按 DAG 顺序合入集成分支，记录 integration merge commit | planner | G6 | `state.yaml`（SHA） |

### 收口与发布（4 种）

| block_type | 语义 | 默认 role | 常见 gate |
|---|---|---|---|
| `release_check` | 迁移/配置/回滚/文档齐备性审核；发布决策 `star: true` | reviewer | G8 |
| `smoke` | 目标分支 SHA 冒烟：路由/auth/关键业务操作 | tester | G9 |
| `notify` | 交付报告（默认 ≤60 行）、下一包进入条件 | planner | G10 |
| `close` | 关闭与复盘：change-summary、lessons、完成度判定 | planner | G10 |

### 控制流（5 种）

| block_type | 语义 | 关键字段 | Skyvern 对应 |
|---|---|---|---|
| `conditional` | 已知分支状态。判据用 `expression`（可求值）优先，只有依赖难以结构化表达的观察状态才用 `prompt` | `branch_conditions: [{criteria:{criteria_type, expression}, next_block_label, description, is_default}]`，必须恰有一个 `is_default: true` | `ConditionalBlock` + `JinjaBranchCriteria` / `PromptBranchCriteria` |
| `for_loop` | 已有确定列表要遍历（工作包、页面、缺陷、视口） | `loop_over`、`loop_blocks`、`max_iterations` | `ForLoopBlock` |
| `while_loop` | 重复直到条件变化（返修循环、轮询状态、分页） | `condition`、`condition_type`、`loop_blocks`、`max_iterations`（必需，防无界） | `WhileLoopBlock` |
| `wait` | 等待人工、外部系统或异步产物 `*` | `wait_seconds` 或 `until` | `WaitBlock` |
| `script` | 固化确定性脚本执行（渐进确定性的落点） | `commands`、`run_signature` | `run_with: code` + script block 缓存 |

## 角色 ↔ 门禁一致性（校验器强制）

`scripts/validate_workflow.py` 会拒绝以下不一致，因为这些正是"自己批准自己"的入口：

| gate | 允许的 role | 说明 |
|---|---|---|
| G0 / G1 / G2 / G10 | `planner` | 规划者负责，但 G2 的 Verdict 必须由后续 `review` 块（reviewer）产出 |
| G3 | `user` + `star: true` | 人工批准不可代签 |
| G4 | `tester`（计划）+ `reviewer`（审核） | 计划作者是 Tester，Verdict 作者是 Reviewer |
| G5 / G8 | `reviewer` | 只读独立结论 |
| G6 / G7 / G9 | `tester` | 独立验证 |
| — | `implementer` | 实现块自身不产出门禁 Verdict，只产出候选与自测证据 |

其他强制规则：

- `review` / `release_check` 块**不得**与它审核的 `implement` 块同 `role`。
- 任何 `star: true` 块不得写 `continue_on_failure: true`（人工边界失败必须停）。
- `while_loop` 与 `for_loop` 必须给正整数 `max_iterations`（护栏 `unbounded_loop`）。
- 顶层图**不允许有环**：检测到环直接拒绝（护栏 `unbounded_loop`）。有界性由三件事共同保证——顶层无环 + 循环必填 `max_iterations` + `max_attempts` 有上限。
- `max_attempts` 若声明，必须是 `1..MAX_ATTEMPTS_CAP`（当前 5）的整数（护栏 `unbounded_retry`）；运行期 `run_flow.py --retry` 另强制 `attempts` 不得超过该块的 `max_attempts`。
- `gate` 非空的块必须声明非空 `evidence` 列表（护栏 `evidence_free_gate`）。
- `secret` 类参数不得带内联值；`commands[].cmd` 命中破坏性模式直接拒绝（护栏 `secret_inline` / `unsafe_command`）。
- `finally_block_label` 指向的块必须顶层且 `next_block_label: null`。
- `error_codes` 里的每个码必须在 `error_code_mapping` 中定义（Skyvern 的教训：LLM 会幻觉错误码，必须白名单过滤，见 `references/skyvern/skyvern/errors/errors.py` 的 `filter_to_user_defined_codes`）。

## 选块决策规则

1. 能用 `script`/`check` 表达确定性验证的，不要用 AI 块（省 token、可复算）。
2. 只有"是/否"判断用 `conditional` + `expression`；需要看页面/截图才用 `criteria_type: prompt`。
3. 已知列表遍历用 `for_loop`；未知次数、依赖状态变化用 `while_loop`。避免嵌套循环，它放大 run 方差（Skyvern `block-types.md` 的经验）。
4. 页面/前端交付必须有 `verify_ui`；测试或构建通过**不能**单独证明页面可用。
5. 人工节点一律 `star: true`，并配 `wait` 或 `approve`，不要让模型"假设已批准"。
6. 块粒度 = 一个完整纵向动作，不是实现步骤。步骤在块内由角色自行分解，不升级成新块（否则门禁会递归爆炸）。
