# 01 · 三层架构

```text
┌──────────────────────────────────────────────────────────────────────┐
│ L1 Flow 层    workflows/*.workflow.yaml                              │
│   parameters + blocks(DAG) + finally_block_label                     │
│   + error_code_mapping + completion_contract                         │
│   决定：顺序、分支、循环、重试、失败是否继续、收尾清理、完成度判定   │
├──────────────────────────────────────────────────────────────────────┤
│ L2 Role 层    skills/aiworflow-*                                     │
│   Planner / Implementer / Reviewer / Tester（+ 入口路由）            │
│   决定：谁能写状态、谁能下结论、谁只读、谁一次只干一件               │
├──────────────────────────────────────────────────────────────────────┤
│ L3 Evidence 层 runs/<RUN-ID>/                                        │
│   state.yaml + current.md + test-plan.md + evidence.md               │
│   决定：结论是否成立、能否恢复中断、能否被第三方接管                 │
└──────────────────────────────────────────────────────────────────────┘
```

三层是**正交**的：改 Flow 不改角色权限；换角色不改证据格式；证据格式变化不得放宽门禁。

## L1 Flow 层：工作流即块 DAG

直接移植 Skyvern 的 `WorkflowDefinition`（`references/skyvern/skyvern/forge/sdk/workflow/models/workflow.py:133`）：

```yaml
schema_version: 1
workflow_id: <稳定 ID>
title: <标题>
version: 1
status: draft | published
risk_level: FAST | STANDARD | HIGH_RISK
run_with: agent | script
parameters: [...]          # 入参、上下文、秘密引用、输出
blocks: [...]              # 块 DAG，label 唯一，next_block_label 显式连边
finally_block_label: <label>   # 必须是顶层且终结（next 为 null）
error_code_mapping: {CODE: 含义}   # 业务错误码白名单
completion_contract: {...}        # 完成度逐条判定，禁止模糊声明
```

关键语义（与 Skyvern 一致，防止我自己发明第二套）：

- **`label` 在工作流内唯一**，嵌套循环体内也计入唯一性（Skyvern 在 `WorkflowDefinition.validate()` 里递归收集 label 并拒绝重复）。
- **`next_block_label` 显式连边**；`version >= 2` 的 DAG 不做"默认顺序执行"回退，否则 disconnected subgraph 检测不出来（Skyvern `validate_workflow_block_graph` 的 `skip_sequential_defaulting=True`）。
- **`finally_block_label`** 必须是顶层块且自身终结；执行前从图中剥离其引用（`_strip_finally_block_references`），保证任何失败路径都能收尾。
- **`continue_on_failure`** 让非关键块失败后流程继续；**`next_loop_on_failure`** 只在循环体内有效，表示失败跳到下一次迭代。
- **图校验在持久化之前**：孤立块、悬挂 `next_block_label`、无界环必须在写入前被拒绝，而不是运行时炸掉。我的实现是 `scripts/validate_workflow.py`。

## L2 Role 层：四角色 + 一个入口

移植 DevFlow 的所有权矩阵（`references/ric-dev-workflow-skills/.agents/skills/_devflow_shared/contracts/role-boundaries.md`），并保留其"单层调度、不递归研发"的约束：

| 角色 | 拥有 | 不得 |
|---|---|---|
| Planner | 需求、仓库画像、Spec、任务 DAG、变更预算、`state.yaml`（唯一写入者）、缺陷归因、按 DAG 合并 | 写生产代码、批准自己的产物、兼任 Tester/Reviewer |
| Implementer | 单个已批准块/Task 的实现、块级测试、实现报告 | 改需求、扩预算、自审、合并 |
| Reviewer | 只读独立结论、稳定 Finding ID、Verdict | 修改被审对象、更新状态、合并 |
| Tester | 测试计划、测试执行、测试报告、Defect 证据 | 改生产代码或已批准 Spec、为通过而改断言 |

`skills/aiworflow/` 是**入口路由 + Flow 引擎语义**，不是第五角色：它负责识别场景、选工作流定义、决定下一个块、执行熔断与账本追加规则；**Run 状态写入权仍唯一属于 Planner**。这条边界防止"入口 Agent 悄悄变成第二个规划者"。

调度是**决策所有权**，不是必须嵌套的工具调用：需要其他角色时返回精确交接，由主会话发起同级调用；四个角色都不再派生角色链。

## L3 Evidence 层：Compact 四文件 + 只追加账本

移植 DevFlow Compact v2 布局（`.devflow/changes/<REQ-ID>/` 四文件），落到 `runs/<RUN-ID>/`：

- `state.yaml`：当前索引（状态、阶段、风险、门禁、块进度、绑定 SHA）。**只保留当前**，历史进账本。
- `current.md`：正文（Intake / Recon / Spec / Tasks / Decisions / Change Log）。原地修订，每个 Task 独立修订号，局部修改不递增无关对象版本。
- `test-plan.md`：Tester 独立维护。
- `evidence.md`：**只追加**账本。审核、实现、测试、缺陷、完成度判定记录一经发布不可修改；修正由原作者发布新 ID + `supersedes`。

融合 Skyvern 的 run 状态生命周期（`created → queued → running → (paused) → completed | failed | canceled | terminated | timed_out`）与块状态（`running / completed / failed / terminated / canceled / timed_out / skipped`），再叠加 WanGo 的工作包状态（`planned → ready → in_progress → implementer_verified → accepted`）。三套状态的映射表在 `05-state-and-evidence.md`。

## 数据流

```text
用户请求
  → [intake] 需求/授权边界（*）              → current.md#Intake
  → [recon]  仓库画像 + base_sha             → current.md#Recon
  → [spec]   行为 + AC + 预算                → current.md#Spec
  → [review] SPEC_REVIEW Verdict             → evidence.md（Reviewer 原样载荷）
  → [approve] 用户批准（*）绑定 Spec 修订     → evidence.md
  → [plan]   块 DAG 冻结                     → current.md#Tasks
  → [implement] 单块实现                     → evidence.md（实现报告 + head_sha）
  → [check]  确定性命令 + 退出码             → evidence.md
  → [review] CODE_REVIEW base..head          → evidence.md（Finding + Verdict）
  → [integrate] 合入集成分支                 → state.yaml（integration SHA）
  → [test] 增量 / 完整测试                   → test-plan.md + evidence.md
  → [verify_ui] 真实浏览器 + 视口矩阵        → attachments/ + evidence.md
  → [release_check] → [smoke] 目标 SHA       → evidence.md
  → [close] completion_contract 逐条判定     → evidence.md + state.yaml: DONE
  ↳ 任意失败 → finally_block_label 收尾 + 归因（07-failure-and-recovery.md）
```

## 设计原则（为什么这样分层）

1. **可校验优于可描述**：能写成 YAML 并被脚本拒绝的规则，就不写成散文。散文规则会被"我以为"绕过。
2. **门禁不递归**：G0–G4 是 Run/阶段级共享准备，G5/G6 面向完整块候选，G7–G10 面向最终交付。角色动作不是 DAG 节点，不给每个步骤套一遍审核（DevFlow `gate-policy.md` 的适用性省略规则）。
3. **证据身份不可伪造**：文档身份 = 完整 Commit SHA + 路径 + 对象 ID；代码证据 = `base_sha / head_sha / tested_sha`。后续记账提交不等于已受测候选。
4. **确定性优先，AI 兜底**：能固化为脚本的验证不要每次让模型即兴发挥；模型只在探索、判断和修复时上场（`08-determinism-and-caching.md`）。
5. **失败是正常输出**：`failed / BLOCKED / not_run` 必须落盘为正式证据，不允许静默消失或改写成"基本通过"。
