# 30 · 2-3 天长周期任务协议 · 2026-09-18

> 目标：支持数小时到 2-3 天的复杂任务，通过**多会话编排**而非单次连续运行。
> 原理：AI 不需要连续运行 72 小时——它需要像工程师一样，每天带着完整上下文继续。

## 一、核心概念

```
Task（任务，2-3天）
 ├── Session 1（Day 1 上午）→ Run 1 → G10 写 task.yaml + context/
 ├── Session 2（Day 1 下午）→ Run 2 → G1 读 task.yaml + context/ → 继续 → G10 更新
 ├── Session 3（Day 2 上午）→ Run 3 → G1 读 → 继续 → G10 更新
 ├── Session 4（Day 2 下午）→ Run 4 → G1 读 → 继续 → G10 更新
 └── Session 5（Day 3）     → Run 5 → 最终验证 → 交付
```

## 二、task.yaml：任务级状态（跨天持久化）

```yaml
# runs/TASK-20260918-001/task.yaml
task:
  id: TASK-20260918-001
  title: "开放平台文档站 + 会话 API 文档"
  created: "2026-09-18T09:00:00Z"
  deadline: "2026-09-20T18:00:00Z"
  total_sessions: 5       # 预计需要几个 Session
  completed_sessions: 0

progress:
  phase: "spec"            # spec/implement/verify/deliver
  percentage: 15
  completed_blocks:
    - "intake"
    - "recon"
    - "spec"
  current_block: "decision"
  next_action: "等待用户批准 Spec"

handoff:
  last_session: "RUN-20260918-001"
  last_session_end: "2026-09-18T11:30:00Z"
  context_files_written:
    - "context/project-agentwan-open-platform.md"
    - "context/area-open-platform-docs.md"
  key_decisions:
    - "API 文档采用卡片式布局"
    - "认证使用 Bearer Token"
  blockers: []
  notes: "Spec 已完成，等待 G3 用户批准后进入实现阶段"

timeline:
  - session: 1
    run_id: "RUN-20260918-001"
    start: "2026-09-18T09:00:00Z"
    end: "2026-09-18T11:30:00Z"
    duration_minutes: 150
    completed: ["intake", "recon", "spec"]
    output: "Spec 文档 + task.yaml 创建"
```

## 三、会话交接协议

### 会话结束前（G10 必做）

1. **更新 task.yaml**：
   - `progress.completed_sessions += 1`
   - `progress.completed_blocks` 追加本次完成的块
   - `progress.current_block` = 当前位置
   - `progress.next_action` = 下一步该做什么
   - `handoff.notes` = 本次学到什么、下次注意什么

2. **写入 context/**：
   - 更新项目画像（新增模块/依赖/已知问题）
   - 更新模块画像（本次改了什么、测试覆盖了什么）
   - 追加决策记录（本次做了什么架构/技术选择）
   - 更新风险登记（踩到什么坑）

3. **存在运行中检查点时保留 checkpoint.yaml**：
   - 不改写历史 ledger / `state.prev.yaml`
   - 让下一会话先读机器快照，再读人类上下文

4. **生成恢复提示词**：
   ```markdown
   ## 继续任务 TASK-20260918-001

   你在继续一个 2-3 天的任务。上一个会话完成了：
   - 块：intake, recon, spec
   - 下一步：G3 用户批准

   读取以下文件恢复上下文：
   1. runs/TASK-20260918-001/task.yaml（任务状态）
   2. context/project-agentwan-open-platform.md（项目画像）
   3. context/area-open-platform-docs.md（模块画像）
   4. context/decisions.md（架构决策）

   从 current_block 开始继续，不要重复已完成的工作。
   ```

### 会话启动时（G1 必做）

1. **读取 task.yaml**：了解任务进度、当前阶段、下一步
2. **读取 checkpoint.yaml / state.yaml / 最近 ledger**：确认机器快照、已完成块与已提交物；已 completed 块的 migration/commit/push 等外部副作用禁止重复执行
3. **读取 context/ 文件**：恢复项目理解、模块理解、决策上下文
4. **执行增量扫描**：只扫描上次会话后变更的文件（`git diff <last_sha>..HEAD`）
5. **从 current_block 继续推进**：不重跑已完成的块

## 四、长周期工作流

```yaml
# 适用于 2-3 天任务的工作流
schema_version: 1

loop_control:
  max_rounds: 200          # 单次会话最大轮次
  checkpoint_interval: 10  # 每 10 轮写 checkpoint

task_control:
  mode: "multi_session"    # multi_session 表示跨天任务
  max_sessions: 12         # 最多 12 个 Session
  session_timeout: "6h"    # 单个 Session 最长 6 小时
  handoff_required: true   # Session 结束必须写 task.yaml
```

## 五、断点恢复脚本

```bash
# 继续一个长周期任务
python3 scripts/task_resume.py runs/TASK-20260918-001

# 输出为 Markdown 恢复提示词，包含：Task/Phase/Progress/Completed blocks/Current block/Next action/Checkpoint-State 快照/最近 ledger/context 读取顺序/副作用不重复规则。
```

## 六、支持的任务规模（对标一线大厂）

| 时长 | 方案 | Session 数 | 人工参与 |
|---|---|---|---|
| **数小时（2-6h）** | 单 Run + checkpoint | 1 | G3+G8 |
| **1 天（6-12h）** | 2-3 个 Run | 2-3 | G3+G8 |
| **2 天（12-24h）** | 4-6 个 Run | 4-6 | G3+G8 |
| **3 天（24-72h）** | 8-12 个 Run | 8-12 | G3+G8 |
| **持续运营** | 后续任务按新 Run 进入 | — | 每个需要变更/发布的人工门禁仍保留 |

对标：
- LongHorizon-Harness：数小时（dozens of hours），有检查点
- Anthropic Managed Agents：可运行数天，定期检查
- 我们：72h（12 Session × 6h），G3+G8 两次人工

| 时长 | 方案 | Session 数 | 机制 |
|---|---|---|---|
| **数小时（2-8h）** | 单 Run + checkpoint | 1-2 | checkpoint.yaml + context/ |
| **1 天** | 2-3 个 Run | 2-3 | task.yaml + context/ 交接 |
| **2-3 天** | 4-8 个 Run | 4-8 | task.yaml + context/ + 增量扫描 |
| **>3 天** | 必须拆分 | — | docs/25 拆分协议 |

## 七、关键保证

1. **不丢进度**：每个 Session 结束写 task.yaml + context/，下次从断点继续
2. **不重复工作**：G1 读 context/ + `git diff` 增量扫描，跳过已完成块
3. **上下文完整**：项目画像 + 模块画像 + 决策记录 + 风险登记
4. **可追溯**：timeline 记录每个 Session 的起止时间、完成内容、产出
5. **可中断**：任何时刻可以安全中断，下次恢复不丢失任何状态

## 八、与传统方案的对比

| 方案 | 原理 | 问题 |
|---|---|---|
| ❌ 单次连续运行 72h | Agent 不中断 | 上下文爆炸、成本失控、不可行 |
| ✅ 多会话编排 | 每天恢复上下文继续 | 需要 task.yaml + context/ 交接 |
| ❌ 纯人工拆分 | 人手动管理每个子任务 | 效率低、遗漏多 |

我们的方案：**多会话编排 + 结构化交接 + 自动恢复 = 2-3 天任务能力**

## 九、自检覆盖（v1.8.5；v1.8.8 增至 6 项）

本协议此前长期处于「协议文档 + 未测实现」状态——文档承诺 checkpoint 与断点恢复，但没有任何机器断言证明它们真的工作。v1.8.5 把恢复链变成 `scripts/selftest.sh` §13 的 5 项确定性断言：

1. **§13a 模板结构**：`task-state.yaml` 模板必须含 `task:`/`progress:`/`handoff:` 三段与恢复必需字段（`current_block`/`next_action`/`last_session`），模板烂掉即 FAIL——模板是给人和 Planner 抄的。
2. **§13b checkpoint 落盘**：`checkpoint_interval: 1` 的 fixture 跑 `--advance --execute-check`，断言 `checkpoint.yaml` 真实生成且含轮次号/时间戳/块状态。**这项自检首次运行就抓到一个从未被执行过的真 bug**：run_flow.py 曾按 `dict.items()` 遍历 state.yaml 的 blocks（实为列表），interval 一触发即 AttributeError 崩溃——该路径此前零测试覆盖，「文档冒充实现」的典型形态。
3. **§13c 恢复提示词完整性**：填充了 `completed_blocks` 列表（`- "intake"`/`- "recon"`）的 task.yaml 必须完整进入恢复提示词。修复前轻量解析器不支持列表字段，恢复会话不知道哪些块已完成，会重跑已完成的工作。
4. **§13d 负例非零退出**：task.yaml 缺失时 `task_resume.py` 必须退出码 2 并输出 ERROR，不允许假成功（假成功意味着会话拿着空提示词继续，比失败更危险）。
5. **§13e 容器兼容**：含 `task.yaml`/`checkpoint.yaml` 的 run 容器不被 `validate_run.py` 误报，长周期文件与 runs 护栏不冲突。
6. **§13c-bis 快照消费（v1.8.8）**：`task_resume.py` 的输出必须包含 checkpoint round/timestamp/blocks、state blocks、最近 ledger 与“migration/commit/push 零重复执行”硬规则。

**诚实边界**：多会话编排（Session×Run 级联，12 Session×6h=72h 的协议上限）仍属协议层——其组件（task.yaml/checkpoint/task_resume/context 交接）已全部有机器断言，但「Session 级联」本身要等首次真实 2-3 天任务做端到端验证（触发条件见 `docs/29-enhancement-roadmap.md` F1）。在那之前，本协议声明的是「组件可用且被测试」，不是「全链路已实战验证」。

---

## 十、run_flow 报告契约与账本可观测（v1.8.6）

v1.8.5 收口 RUN-20260920-003（首个 Claude Code 驱动的完整 run）时暴露两个双宿主可用性缺陷，v1.8.6 修复：

1. **TERMINAL 报告缺 `loop_control` 键**：`--advance` 的正常路径输出 `loop_control`（CONTINUE/DONE/WAIT_ROLE/WAIT_USER/BLOCKED），但 run 已终结（TERMINAL）与 DAG 环检测（CYCLE_DETECTED）两条提前返回路径的报告没有该键。消费方（Codex / Claude Code 会话）按统一契约解析即 KeyError——RUN-20260920-003 收口时实际踩中。修复：两条路径与正常路径同样输出 `loop_control`（终结=DONE、环=BLOCKED），"所有 --advance 报告都带 loop_control"成为机器契约，selftest §7d-bis 用 fixture 断言终结报告契约（65→66）。
2. **轮次账本写失败被静默吞掉**：`_append_round_ledger` 写 state.yaml 失败时 `except: pass`，轮次日志可能悄悄缺行且无任何告警——与 v1.8.5 修掉的"假成功退出 0"同族，违背"失败必须有名字"。修复：失败时 stderr 显式 `WARN: 轮次日志写入失败（不阻断推进）: <原因>`，推进不受影响。

**验证**：selftest 66/66；TERMINAL 契约对真实已完成 run（RUN-20260920-003，只读）实测 `loop_control=DONE`；ledger 写失败路径用只读 state.yaml fixture 实测 stderr 出现 WARN 且推进正常输出 WAIT_ROLE。

---

## 十一、会话归因（v1.8.7）

外部模型与宿主在 2026-09 内多次变化；没有归因的 ledger 无法回答“这个 run 是哪个模型执行的”，也无法解释指令遵循率漂移。自 v1.8.7 起：

```bash
python3 scripts/run_flow.py <workflow> <run-dir> \
  --advance --execute-check \
  --session-meta '{"model":"<session-model>","tokens_used":<integer-or-null>}'
```

- `model` 必填，写入本次调用产生的每条自动 ledger，并在 `--advance` 报告的 `session_meta` 回显。
- `tokens_used` 只接受非负整数或 `null`。宿主没有稳定程序化接口时必须写 `null`，禁止估算。
- Implementer / Reviewer / Tester 报告模板含 `session.model/session.tokens_used`；Planner 通过 `--append-ledger --session-meta` 把角色归因入账。
- 非法输入退出非 0。selftest §7d-ter 同时覆盖正例与负例。

## 十二、checkpoint 消费与副作用防重复（v1.8.8）

`task_resume.py` 现在会读取：

1. `task.yaml`：任务、进度、交接；
2. `checkpoint.yaml`：round / timestamp / 各块状态；
3. `state.yaml`：块状态与最近 5 条 ledger；
4. `context/*.md`：项目与模块上下文。

恢复提示词显式写入：**已 completed 块的外部副作用（migration/commit/push）零重复执行**。这是提示词与自检层面的防重复协议，不等价于数据库迁移或 Git 操作自身的幂等性；执行不可逆副作用前仍必须读取原始提交与验证证据。

run 内单块串行推进是 Planner 唯一写入者治理设计；并行只发生在工作包层（多 run / 多 worktree）。见 `docs/04-roles.md`。L3 真实断点演练已于 2026-09-23 由 RUN-20260923-001（v1.8.13）按 `docs/29` F1-R 五条验收执行通过——「单点断点恢复（≥3 块中断→新会话接续）」可宣称实证；本协议 §九的多天 Session×Run 级联仍属协议层，不随单点演练通过而宣称多天实战闭环。

**边界说明（v1.8.9）**：`review_preflight.py` 的 PROTECTED_PATHS 规则拦截的是**被审主仓 diff 中**名为 `runs/…` 与 `state.prev.yaml` 的路径——`.ai_worflow` 本身不是 git 仓库、其账本不会出现在被审 diff 里，因此该规则对主仓中的同名路径构成纵深防御（例如主仓内嵌另一套 `runs/` 账本或状态快照被误提交时仍会被拦下），并非对 `.ai_worflow/runs/` 的直接保护；后者的完整性由「runs/ 只追加、既有容器只读」边界与 selftest §3 墓碑护栏承担。
