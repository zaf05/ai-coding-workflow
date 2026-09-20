# 工作流状态契约

> 吸收自：a10 丶单向箔「多天 AI Coding 工作流」、a16 AI实验室「五层闭环架构」、a11 dialog996「多Agent≠可控执行」
> 权威来源：`../../../docs/05-state-and-evidence.md`。本文件是执行摘要。

## 三轨状态（不得互相替代）

- 轨道 A  Run 生命周期：`created → queued → running → (paused) → completed | failed | canceled | terminated | timed_out`
- 轨道 B  块状态：`running → completed | failed | terminated | canceled | timed_out | skipped`
- 轨道 C  交付状态：`planned → ready → in_progress → implementer_verified → accepted`（WanGo 工作包；`blocked` 为阻塞态）

## 关键状态条件

- `READY`：G2/G3/G4 均有当前有效证据，且前置能力已进入 integration baseline。
- `FULL_VALIDATION`：所有块 `INTEGRATION_TESTED`。
- `READY_TO_MERGE`：同一集成 SHA 已通过完整验证与发布审核。
- `DONE`：目标分支冒烟证据 + completion_contract 逐条通过 + 无未解决阻断 Finding/Defect/过期证据。
- 行为性 Spec 变更使 Run 回到 `SPEC_REVIEW`，下游状态失效。

## 迁移记账

每次状态迁移记录：前一状态、后一状态、操作者、带时区时间、原因、证据。不得引用不存在/被取代/过期的证据。

## 多天/多会话工作流（吸收自 a10）

> a10「用一个完整需求跑通多天 AI Coding 工作流」的关键经验：**跨会话状态恢复不是"想起来接着做"，而是"从证据中重建上下文"。**

跨会话恢复规则：
1. 新会话开始时，先读取 `state.yaml` + `current.md` + `evidence.md` 完整内容，重建当前 Run 的完整上下文。
2. 不得仅凭记忆或会话历史"接着做"——上下文来源必须是证据文件，不是聊天记录。
3. 恢复后发现证据文件与当前仓库状态不一致（SHA 不匹配、文件缺失）→ 先记录差异到 `current.md#Decisions`，再决定是修复还是重开。
4. **失败路径必须入账**（吸收自 GoPS/Harness Engineering 对照分析 §最值得吸收的想法 #2）：`current.md` 应有固定字段 `## Failed Attempts` 记录失败尝试；同一死路跨会话不得重试。

## 上下文连续性 > 工具特长（吸收自 GoPS 对照）

> GoPS 篇：**指定一个主线 Agent 对上下文负责到底，其他工具只做入口或补位。**

本工作流对应：
- Planner 是上下文连续性的唯一负责人——每次 Run 从头到尾一个 Planner 维护 `state.yaml` 和 `current.md`。
- Implementer/Reviewer/Tester 只负责单块/单次任务，不需要理解完整上下文（由 Planner 在交接时提供最小必要上下文）。
- 不得让 Implementer 自行推断"上一步做了什么"——交接时 Planner 必须在 `current.md` 中写明精确上下文。

## 五层闭环的状态映射（吸收自 a16）

> a16「玩转 AI Coding：面向团队的 Harness Engineering 实践指南」五层闭环：输入→配置→模式引擎→Agent→MCP。状态需要贯穿五层。

本工作流对应：
- **输入层**：Intake（G0）记录用户意图、场景、验收方式。
- **配置层**：`workflows/*.workflow.yaml` 定义执行模式与约束。
- **引擎层**：`run_flow.py` 确定性推进 DAG。
- **Agent 层**：四角色按所有权执行。
- **执行层**：`scripts/` 校验、`skills/` 交接、`runs/` 记录证据。

状态贯穿要求：每层状态变更都必须反映在 Run 容器中；不得出现"引擎层标记 completed 但 Agent 层未见证据"的状态断层。
