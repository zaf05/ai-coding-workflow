# 05 · 状态、证据与产物生命周期

## Run 容器

```text
runs/<RUN-ID>/            RUN-ID = RUN-YYYYMMDD-NNN
├── state.yaml            当前索引（唯一由 Planner 写）
├── current.md            正文：Intake / Recon / Spec / Tasks / Decisions / Change Log
├── test-plan.md          测试计划与用例（唯一由 Tester 写）
├── evidence.md           只追加账本
├── attachments/          必要脱敏附件（截图、视口矩阵、日志片段）
└── .local/               临时物，永不作为正式证据
```

按进度创建文件，不预建空目录。模板在 `skills/_shared/templates/`。

## 三轨状态

三条状态轨道描述同一件事的不同侧面，**不得互相替代**，也不得只更新一轨。

### 轨道 A：Run 生命周期（借自 Skyvern run status）

```text
created → queued → running → (paused) → completed | failed | canceled | terminated | timed_out
```

- `paused` 非终结，可恢复（等待人工批准 `*`、外部系统、凭据）。
- `terminated` = 被门禁或 guardrail 主动终止；`timed_out` = 超过 `max_elapsed_time_minutes`。
- 运维约定：为每类工作流定义最大运行时长；对超过阈值仍处非终结态的 Run 告警；跟踪失败签名做优先级排序。

### 轨道 B：块状态（借自 Skyvern BlockStatus）

```text
running → completed | failed | terminated | canceled | timed_out | skipped
```

- `skipped` 必须写原因（条件分支未命中、门禁不适用、被 `finally` 短路）。
- `failed` 必须绑定 `error_codes` 中的已注册码或明确归因，不能只写"出错了"。

#### 写入时迁移校验（v1.8.0 起，`scripts/validate_transition.py`）

Planner 覆写 `state.yaml` 前必须先 `cp state.yaml state.prev.yaml` 建立快照，写入后立即运行
`python3 scripts/validate_transition.py runs/<RUN-ID>`，FAIL 则回滚本次写入并按报错修正——
约束的强制性来自"违反后写不进去"，不是提醒措辞。规则（稳定编号，供自检反例断言）：

- **T-01** 新置 `passed: true` 的门禁，`owner` 必须 ∈ GATE_ROLES（集合见 [03-gates.md](03-gates.md) 决策所有者列；代码定义在 `validate_workflow.py`，import 复用不复制）。堵"Planner 代签 G9"类越权。
- **T-02** 块状态机：`pending→running→completed|failed|skipped|canceled|terminated|timed_out`；`failed→pending` 是 `run_flow --retry` 的合法语义；`completed→running|failed` 仅当本次写入新增返修凭据（`error_codes` 增量非空，对应 WanGo `implementer_verified→in_progress` 例外）。终态不可迁出。
- **T-03** 新 completed 块的 `gate` 必须与工作流定义的门禁绑定一致。
- **T-04** `attempts` 单调不减；`star: true` 块新增 completion 必须有人工证据（`approvals[label]` / `approvals.user` / 该块门禁 `evidence_ref` 指向 `APPROVAL-*` 锚点）。

`skipped` 凭据口径（同时是 `validate_run.py` R-1 的判定）：机器可读首选 **`skip_reason` 字段**
（一行说明为何跳过），`error_codes` 次之，最低限度块内注释；三者皆空判 FAIL。

#### DAG 语义一致性（v1.8.0 起，`validate_run.py` R-1/R-2/R-3）

容器结构合法 ≠ 语义一致（2026-09-20 实测：close 已 completed 但 spec 从未开始，容器校验
却 PASS）。判定基于 run 声明的 DAG 定义（编译产物优先，回落 `workflows/` 模板），连边语义与
`run_flow.py` 完全同源（`build_graph` 复用）：

- **R-1** 任一 completed 块的全部 DAG 祖先必须 completed/skipped；祖先包含条件分支目标
  （未命中的分支块必须显式标 `skipped`+凭据，不能留 pending）。
- **R-2** `run.status == completed` ⇒ 全部块 terminal（completed/skipped，frontier 为空），
  且 `finally_block_label` 指向的块必须 completed。
- **R-3** 未登记的工作流块一律视为 pending（与 `run_flow.load_statuses` 同一语义，明文固定防漂移）。

存量不一致 run 在 `runs/README.md` 占位表**显式登记承担，不为迁就存量放水规则**。

#### 全系统日检（v1.8.0 起，`scripts/check_all.py`）

`python3 scripts/check_all.py`：逐 run 校验 + 陈旧检测 + 安装收据/闸门汇总，只读。
陈旧判定用文件 mtime（账本时间戳可伪造，mtime 不能），`status ∈ {running, paused}` 且
`last_activity` 超过 `max_elapsed_time_minutes` 即 WARN 并给出建议动作（续跑 / Planner
标记 `timed_out|terminated`）——脚本不代写状态，唯一写入者仍是 Planner。白名单登记过的
run 计 WARN 不计 FAIL（恒定 FAIL 会被当噪音，护栏被当噪音就等于没有）。

#### 评审-only Run 的合法收尾（v1.8.10 起）

适用：交付物是评审报告/建议本身、不改代码的 run，在 G3 用户接受后终结。处方全部来自
RUN-20260921-001 实操（每条都是现场踩到后补齐的，缺一条 `validate_run` 就 FAIL）：

1. **fix 路径块逐块跳过且带凭据**：`--mark-done <label> --status skipped`，每个 skipped 块
   必须写 `skip_reason`（R-1 跳过凭据；`error_codes` 或块内注释亦可，
   `skip_reason` 最直白）。
   理由示例："评审-only run：G3 用户接受后按 Decision 不进修复路径，修复另立工作包另行授权"。
2. **notify/close 可 completed**：报告已当面交付（notify）与 run 终结（close）是真实完成的
   事实，其 skipped 祖先凭 `skip_reason` 放行，不必硬跳整条尾巴。
3. **`test-plan.md` 写 N/A 记录而非留空**：completed 状态强制该文件存在。评审-only run 写
   N/A：列实际验证面（基线门禁的历史实测引用、主仓与 worktree `git status` 双空复核、
   `validate_run` 结果），明确"不存在修复类测试计划"——不伪造测试计划。
4. **star:user 块亲签出处必须落位**：mark-down approve 这类人工门块时，同步在 `approvals.<label>`
   写 `decided_by/decided_at/evidence`（亲签原话 + 会话时间），账本追加一条注明"用户会话亲签、
   AI 未代签"。Planner 的 mark-done 只做簿记，不产生批准。
5. **终态前双复核**：`validate_run` PASS + `run_flow --advance` 输出 `loop_control: DONE`
   （frontier 空）才算关闭。

#### mark-done 硬门禁（v1.8.12 起，引擎强制）

- **证据锚点门禁**：`--mark-done <label> --status completed` 时，引擎逐条校验工作流块
  声明的 `evidence` 引用（文件存在 + `## Anchor` / `id: Anchor` 锚点存在），不满足即拒绝
  写入（`AIW_EVIDENCE_MISSING`）。无 `#anchor` 的引用（`state.yaml` / `test-plan.md` /
  `attachments/` 等）与 `validate_run` 同语义：跳过而非拒绝（§3k 回归守护）。
- **implement head_sha 门禁**：implement 类块 completed 必须绑定候选提交
  `--head-sha <sha>`（或块内已有合法 head_sha），否则 `AIW_HEAD_SHA_MISSING` 拒绝。
- **check/script 人工完成禁令**：check/script 块的 completed 只能由
  `--advance --execute-check` 按命令退出码自动产生，人工 mark-done 一律拒绝。
- **workflow 冻结**：引擎首触 run 时把 DAG 定义 SHA256 写入 `run.workflow_sha256`；
  定义随后被修改则一切推进/写入被 `AIW_WORKFLOW_DRIFT` 拦截。
- **refreeze 受控迁移（双宿主兼容）**：定义发生**非结构变更**（注释/错误码表等）且
  state 块集合与角色与新定义逐项一致时，`--refreeze-workflow "<原因>"` 允许把冻结 SHA
  迁移到当前定义并在 ledger 留 `workflow_refreeze` 凭据；结构变更（增删块/改角色）仍拒绝，
  需 Change Log + 新建 run。用途：一个宿主升级工作流定义不得锁死另一宿主正在跑的 run。
- **终态引擎收口**：全部块 terminal 时 `--advance` 由引擎写入 `run.status=completed` 与
  `current_block_label=finally`，消灭手改 state 的旁路；validate_run 以 R-4/R-5 复核。

账本 note 的命令形态：`--append-ledger '{"note":"..."}'`（单个 JSON 参数；没有 `--note`
标志——RUN-20260921-001 首次使用时踩过）。

### 轨道 C：交付状态（借自 DevFlow Root/Task + WanGo 工作包）

```text
Run 主路径：
DRAFT → REPOSITORY_BASELINE → SPEC_REVIEW → USER_APPROVAL → TEST_REVIEW
      → READY → IMPLEMENTING → INTEGRATING → FULL_VALIDATION
      → RELEASE_REVIEW → READY_TO_MERGE → POST_MERGE_VERIFY → DONE

块/Task 主路径：
PLANNED → READY → IN_PROGRESS → CODE_REVIEW → APPROVED → MERGED → INTEGRATION_TESTED → DONE

辅助状态：BLOCKED / CHANGE_REQUESTED / CANCELLED / ROLLED_BACK
```

映射到 WanGo 工作包状态：`planned → ready → in_progress → implementer_verified → accepted`（阻塞用 `blocked`，允许 `implementer_verified → in_progress` 返修；`accepted` 不回退，问题开新包）。

## 自动化推进轮次日志（ledger）

`state.yaml` 的 `ledger` 字段记录 `run_flow.py --advance` 的每轮推进结果。

### 字段结构

```yaml
ledger:
  - round: 1            # 轮次编号（int）或 "final"
    timestamp: "2026-09-14T12:00:00.000000+00:00"   # ISO8601 UTC
    block: "intake"     # 当前推进的块 label
    action: "STAR"       # STAR | CHECK | HANDOFF | DONE
    signal: "WAIT_USER"  # CONTINUE | DONE | WAIT_USER | WAIT_ROLE | BLOCKED
    gate: "G3"           # 可选：gate 编号
    passed: true          # 可选：CHECK 块是否通过
```

### 写入时机

| 触发条件 | 写入内容 |
|---|---|
| 遇到 `star:true` 块 | `action=STAR, signal=WAIT_USER, gate` |
| CHECK 块执行通过 | `action=CHECK, signal=CONTINUE, passed=true` |
| CHECK 块执行失败 | `action=CHECK, signal=BLOCKED, failed=true` |
| CHECK 块未执行（无 --execute-check） | `action=HANDOFF, signal=WAIT_ROLE` |
| HANDOFF 块 | `action=HANDOFF, signal=WAIT_ROLE, gate` |
| 全部完成（DONE） | `round=final, action=DONE, signal=DONE, remaining_blocks` |

### 恢复中断

Planner 恢复时读取 `ledger` 最后一条，即可知道上次停在哪个块、什么信号、到了第几轮，无需扫描 `evidence.md` 全账本。


状态推进条件（关键几条）：

- `READY` 要求 G2/G3/G4 全部有当前有效证据，且前置能力已进入 integration baseline。
- `FULL_VALIDATION` 要求所有块 `INTEGRATION_TESTED`。
- `READY_TO_MERGE` 要求同一集成 SHA 已通过完整验证与发布审核。
- `DONE` 要求存在目标分支冒烟证据、`completion_contract` 逐条通过、无未解决阻断 Finding/Defect/过期证据。
- 行为性 Spec 变更使 Run 回到 `SPEC_REVIEW`，并按变更控制使下游状态失效。
- 不得因为产物很小就跳过状态；`FAST` 可以压缩产物与轮次，但必须保留同样证据。

## 产物生命周期

### 草稿 → 发布 → 取代

- **草稿**可连续原地编辑；不为内部预检、commentary 或每次保存制造正式修订或提交。状态可以索引草稿，但不能把它当作有效门禁证据。
- **发布**前固定对象修订与不可变身份：Git 完整 Commit SHA + 路径 + 对象 ID；无 Git、不能跟踪或没有提交授权时，保存不可变本地快照与内容哈希，并注明"仅本地可恢复"。代码门禁所需 SHA **不能**用文档哈希替代。
- 一经交给独立 Reviewer 或产生正式结论，被审内容即已发布；被拒绝或阻塞的版本也必须可逐字恢复。
- **取代**：审核、测试、实现、缺陷记录一经发布不可修改；修正由原职责作者发布新 ID/版本并写 `supersedes: <旧 ID>`。Planner 只原样追加，不改写载荷。

### 局部修订，不版本连锁

- 每个 Task/块独立修订号；局部修改不递增无关 Task、测试用例或矩阵的版本。
- 不生成 `tasks-v2.md`、`reports-v3.md` 这类重复版本矩阵；正文保持最新版 + 底部 Change Log，正式历史由 Git 或快照保全。

### 有效性判定（按对象真实影响传播，不按父文件版本传播）

| 证据 | 原绑定始终保留 | 当前使用要求 |
|---|---|---|
| Spec 审核、用户批准 | Spec 对象修订与文档身份 | 受影响行为变化重开 G2/G3；含义未变按变更控制记录适用性 |
| 测试审核 | Spec + 测试计划对象修订与身份 | Oracle/权限/环境边界变更重开受影响 G4；纯职责映射做局部复核 |
| 代码审核 | Task/Spec + 完整 `base_sha..head_sha` | head 或相关行为变化需新的绑定审核，可按风险增量复审 |
| 测试报告 | Spec + 计划 + 环境 + 完整 `tested_sha` | 仅证明原输入；代码/环境/必要输入改变需按影响补充验证 |
| 发布审核 | 集成 SHA + 证据集 | 当前集成 SHA 与覆盖必须一致，不能用后续记账提交冒充受测候选 |

跨对象沿用时必须说明：旧/新对象、精确 Delta、未受影响范围、复核依据。不得篡改旧载荷、空写"继续有效"，或把旧 `tested_sha` 换成新 SHA。

## 账本写入顺序与中断恢复

1. 各角色独立生成**完整载荷**；Planner 原样追加到 `evidence.md`。
2. 先写完整证据、身份与载荷，**再**更新 `state.yaml` 索引。
3. 中断恢复先核对记录 ID：同 ID 同载荷 → 复用，不重复追加；同 ID 异载荷 → 阻塞并向原作者求解。
4. 未完成写入不得被状态引用；临时草稿可重建，已完整发布的记录不得覆盖。
5. 矛盾证据未解决前，对应门禁保持未通过。

## 必须入账本的五类记录（无第六类）

每次迭代中，以下角色产出**必须**以独立记录写入 `evidence.md`。不写 Per-block 状态迁移 EVENT——那由 `state.yaml` 追踪。只写跨会话恢复需要读取的完整载荷。

| 记录 ID | 产出角色 | 何时写 | 载荷来源模板 |
|---|---|---|---|
| `REVIEW-xxx` | Reviewer | 审核完成后 | `skills/_shared/templates/review.yaml` |
| `IMPL-xxx` | Implementer | 实现完成后 | `skills/_shared/templates/implementation-report.yaml` |
| `CHECK-xxx` | Implementer | 确定性检查完成后 | 下文 §CHECK 记录格式 |
| `APPROVAL-xxx` | Planner（转录用户） | 用户批准后 | 转录原话 + 批准范围 |
| `DEFECT-xxx` | Tester 或 Reviewer | 发现缺陷后 | `skills/_shared/templates/test-report.yaml` 的 defect 段 |

### 为什么是这五类

- **REVIEW / APPROVAL**：决定下一个门禁能不能过，断联恢复时必须读到原始结论。
- **IMPL**：记录 `files_changed` + `tests_run` + 直接验证证据，后续 Reviewer 需要对照审核，Test 需要知道覆盖了哪些文件。
- **CHECK**：命令列表 + 退出码 vs expect，是 `check` 块 pass/fail 的唯一事实源；不靠 AI 说"type-check 通过了"。
- **DEFECT**：独立发现的缺陷有独立身份；返修时按 ID 找、修完写 `supersedes`；不入账本 = 跨会话丢失。

### 记录写入纪律

1. 各角色用对应模板产出 **YAML 载荷**（review.yaml / implementation-report.yaml / check 格式 / defect 格式）。
2. Planner 逐字转录到 `evidence.md`，不加摘要、不改字段、不带评论。
3. 先追加完整记录 → 再 `--append-ledger` 更新 state 索引。
4. 同一 ID + 同一载荷不得重复追加；先核对已有记录。
5. 失败的实现或检查也必须入账本（状态 `failed` 不等于"不需要记录"）。

### CHECK 记录格式（非 YAML 模板，内联定义）

```
## CHECK-001 · <block_label> · implementer · <ISO时间>

check_id: CHECK-001
block_label: check-backend
head_sha: <完整 SHA>
outcome: PASS | FAIL
results:
  - cmd: "<命令原文>"
    workdir: <相对路径>
    exit_code: <实际退出码>
    expect: <期望退出码>
    key_output: |   # 关键输出行（截取，不全量）
      ...
  - ...
```

每行命令都必须有 `exit_code` 与 `expect` 对照。`outcome=PASS` 仅当所有 `exit_code == expect`；任一不匹配 → `FAIL`。

### DEFECT 记录格式

```
## DEFECT-001 · <severity> · <发现角色> · <ISO时间>

defect_id: DEFECT-001
severity: blocking | important | minor
found_by: tester | reviewer
target_sha: <完整 SHA>
title: "..."
steps_to_reproduce: [...]
evidence: "..."
expected: "..."
disposition: IMPLEMENTATION | SPEC | ENVIRONMENT
superseded_by: null   # 修复后写到新的 DEFECT 记录
```




## 失败尝试账本（防死路重试）

借鉴 Anthropic 2026-03 长任务实践（`docs/14-current-practices.md`）：失败路径必须像成功路径一样被记录，否则下一个会话会重试同一条死路。

- `current.md` 固定保留 **Failed Attempts** 段：记录"试了什么、为什么失败、证据、结论"。
- `BLOCKED` / `failed` / `not_run` 的正式结果不得只丢进 `.local/`；要在 `current.md` 与 `evidence.md` 中留下可检索条目。
- 恢复会话先读 `current.md` 的 Failed Attempts，再决定下一步；同一条失败路径未经新信息不得重试。
- 同一 Finding/Defect 第二次失败时换全新会话与最小根因包，不允许沿用旧上下文自愈。

## 变更控制（修订类型）

| 类型 | 影响 | 处理 |
|---|---|---|
| `EDITORIAL` | 拼写/格式，含义不变 | Planner 记录精确差异与无语义影响依据，不单独调用 Reviewer；原批准仍绑定原对象 |
| `TECHNICAL` | 块内预算/内部约束，行为不变 | G2 局部技术复审；块内执行顺序与检查点不属此类，无须送审 |
| `TECHNICAL` | DAG 节点/依赖/所有权变化，行为不变 | 先满足冻结例外，再 G2 局部复审受影响节点 |
| `BEHAVIORAL` | 用户可观察行为、契约、数据、权限变化 | 重开 G2 + G3，下游状态全部失效，重新走 G4 及以后 |
| `SCOPE` | 范围扩大或缩小 | 写入 Decision，缩小范围必须显式记录被砍掉的目标与其去向 |

DAG 首次通过 G2 后**冻结**；只有已证实无法在原块内安全完成 AC 的**结构性障碍**才通过 Decision + Change Log 做最小改图与受影响门禁复审，不自动重建全图。

## 跟踪与脱敏

- 默认跟踪：`state.yaml`、`current.md`、`test-plan.md`、`evidence.md`、必要脱敏附件。
- 默认不跟踪（放 `.local/`）：临时 Prompt、搜索输出、diff 中间件、调试日志、会话 ID/cursor/PID/机器缓存。
- 失败、`BLOCKED`、`not_run` 的正式结果仍须持久化，不能统统归为临时文件。
- 凭据、Cookie、私钥、生产数据、未脱敏日志**不得**进入任何受跟踪产物或外部上传。
- 在 WanGoPlatform 内：`.ai_worflow/` 已被仓库根 `.gitignore` 忽略（当前事实：commit `d51eeaab`，规则 `.ai_worflow/`），本目录内容不入库；工作包证据写入 WanGo 的交付报告与计划文档。
