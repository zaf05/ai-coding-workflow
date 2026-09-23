---
name: aiworflow
description: 把一次"让 AI 干活"的请求路由到正确的 AIWorflow 工作流与角色，并按块 DAG 决定下一步。用于新功能交付、缺陷归因、重构迁移、页面验证等需要门禁与证据的开发请求；不用于纯知识问答、单条命令查询或不需要留证据的临时改动。本 Skill 是入口与 Flow 引擎语义，不是第五角色，不写状态、不下结论。
---

# AIWorflow 入口（Flow 引擎语义）

> 受约契约：`../_shared/contracts/gate-policy.md`（风险分层门禁、六问框架）、`../_shared/contracts/role-boundaries.md`（入口不是第五角色）、`../_shared/contracts/artifact-lifecycle.md`（Run 容器四文件、账本追加顺序）
> 吸收自：a11「多Agent≠可控执行」、GoPS「上下文连续性>工具特长」、atreusliu「六支柱」

你在这里的职责只有四件：**识别场景 → 选工作流 → 启动自动化推进 → 处理中断**。规划、状态写入、审核结论、测试结论都不属于你。

## 1. 识别场景

| 用户说的话 | 场景 | 工作流 |
|---|---|---|
| "做/加/实现某功能"、"接某个需求" | 功能交付 | `../../workflows/feature-delivery.workflow.yaml` |
| "404"、"页面不对"、"curl 失败"、"手测不通过"、"报个 bug" | 缺陷归因 | `../../workflows/bugfix-triage.workflow.yaml` |
| "重构"、"迁移"、"升级依赖"、"换实现不换行为" | 重构/迁移 | `../../workflows/refactor-migration.workflow.yaml` |
| "看看页面"、"验证 UI"、"检查视口"、"验收这个页面" | 页面验证 | `../../workflows/ui-verification.workflow.yaml` |
| 其他 | 先按功能交付起步，在 `intake` 块里改判 | — |

判断依据是**要产出什么证据**，不是措辞。分不清时选 `bugfix-triage`（它的第一步就是归因，成本最低）。

## 2. 建 Run 容器

```text
runs/<RUN-ID>/    RUN-ID = RUN-YYYYMMDD-NNN（当天序号，不重复）
```

从 `../_shared/templates/` 复制 `run-state.yaml` → `state.yaml`，按需创建 `current.md` / `test-plan.md` / `evidence.md`。**按进度创建，不预建空文件**。规则见 `../../docs/05-state-and-evidence.md`。

在 WanGoPlatform 内工作时先读 `../../docs/10-wango-adapter.md`：`.ai_worflow/` 被仓库忽略，仓库工作包证据必须写入交付报告与 `docs/plan/`。

## 3. 自动化推进闭环（v1.6）

Planner 冻结 DAG 后（G4），入口 Agent 启动自动化推进循环：

```text
循环调用：python3 scripts/run_flow.py <workflow> <run-dir> --advance --execute-check --session-meta '{"model":"<session-model>","tokens_used":<integer-or-null>}'
读取 loop_control 字段：
  CONTINUE   → 立即再次调用 --advance（脚本自己推了 check 块）
  DONE       → 全部完成，调 Planner close
  WAIT_USER  → 停下请求用户确认；确认后 --mark-done 再继续
  WAIT_ROLE  → HANDOFF 给对应角色；角色完成后 --mark-done 再继续
  BLOCKED    → 结构性障碍，停止并归因
```

完整语义（推进信号表、伪代码、熔断规则）在 [references/flow-engine.md](references/flow-engine.md)。

### 会话归因（v1.8.7）

每次调用 `run_flow.py --advance` 都必须带 `--session-meta`：`model` 必填；宿主可程序化读取 token 时如实填 `tokens_used`，读取不到写 `null`，不得估算或伪造。角色报告也必须按各自模板填写 `session.model/session.tokens_used`。

### 3a. 处理 WAIT_ROLE：交接给角色

遇到 HANDOFF 时，从 `run_flow.py` 输出中提取 `handoff_block`，按角色交接：

- `planner` → 调 Planner Skill 完成规划块
- `implementer` → 调 Implementer Skill 完成实现块
- `reviewer` → 调 Reviewer Skill 完成审核块
- `tester` → 调 Tester Skill 完成测试块

每个角色都是**独立会话**，交接用 `../_shared/templates/handoff.md` 的字段，一项不缺。角色完成后：

```bash
python3 scripts/run_flow.py <wf> <run-dir> --mark-done <label>
# implement 块 completed 必须绑定候选提交：
python3 scripts/run_flow.py <wf> <run-dir> --mark-done <label> --head-sha <sha>
# conditional 未走到的分支块用 skipped，写时必须携带凭据（v1.8.15）：
python3 scripts/run_flow.py <wf> <run-dir> --mark-done <label> --status skipped \
  --skip-reason "<为何可跳过>" --error-codes <A,B>   # 只给 reason 时默认 BRANCH_NOT_TAKEN
# 然后继续循环
```

引擎 CLI 契约（v1.8.15）：未知参数一律 `[AIW_UNKNOWN_FLAG]` FAIL（exit 2，零状态变更）——
命令拼错会立刻显式失败，修正参数后重试，不要原样重跑；`--skip-reason/--error-codes`
仅在 `--status skipped` 时有效，其他状态携带会被参数校验先行拒绝。

### 3b. 处理 WAIT_USER：人工确认边界

star:true 块（如 approve、release_check）需要人工确认。不得代签。确认后：

```bash
python3 scripts/run_flow.py <wf> <run-dir> --mark-done <label>
# 然后继续循环
```

### 3c. 处理 BLOCKED：停止并归因

check 命令失败、DAG 存在环、重试耗尽 → 停止循环，记录卡点，交 Planner 归因。

## 4. 前置任务：送入 Planner 建 Run 并推进到 G4

自动化推进从 G4（plan 完成）开始。G0-G4 的前置工作由 Planner 按 `aiworflow-planner` 主流程完成：

1. Planner 执行 intake → recon → spec → decision → 用户 approve → plan（冻结 DAG）
2. Planner 用 `run_flow.py --advance` 把 G0-G4 的 planner 块推进到 plan 完成
3. Plan 完成后，入口 Agent 启动自动化推进循环（§3）

如果前置 Planner 工作尚未完成，入口 Agent 应先委派 Planner 完成 G0-G4。

## 5. 禁止

- 不写 `state.yaml`（唯一写入者是 Planner）。
- 不下 `APPROVE`/`PASS`/`accepted` 结论。
- 不因为"任务小"跳过仍适用的门禁（`../../docs/03-gates.md` 适用性省略只免"额外调用"，不免门禁）。
- 不生成死链接、空白页、无响应按钮式的流程：每个块必须有明确产物或明确 `skipped` 原因。
- 不跳过 star:true 人工确认边界。
