# Flow 引擎语义（入口角色执行手册）

本篇是 `skills/aiworflow/SKILL.md` §3 的展开。v1.6 起支持自动化推进闭环：`run_flow.py --advance --execute-check` 逐轮推进，Agent 根据 `loop_control` 信号执行对应动作。v1.7 吸收黄迅「环系统」与 GoPS「OPC 闭环」：**机器提供事实、人做判断、环间只传可验证事实、WAIT_USER 结构化交接**。

> 吸收自：黄迅「AI Coding 深水区」（2026-09-12）+ AI运维实验室「GOPS Agent进生产」（2026-07-12）
> 核心理念：**环间只传可验证事实，不传"AI说是这样"**；**人不是环外验收员，是环内判断节点**

## 图模型

- 顶层块列表 + `next_block_label` 显式连边；`null` 表示终结。
- DAG 模式**不做顺序回退**：不因为"下一个块看起来更合适"就跳着走，改图要走变更控制。
- `for_loop` / `while_loop` 有 `loop_blocks` 子图；子块 label 在全工作流内唯一。
- `conditional` 有 `branch_conditions`，必须恰有一个 `is_default: true`；判据优先 `expression`，只有依赖难以结构化表达的观察状态才用 `prompt`。
- `finally_block_label` 指向的块必须是顶层且自身终结；校验与执行前把它从连边中剥离（Skyvern `_strip_finally_block_references`），避免误判孤立/环。

## 自动化推进闭环（v1.6 主模式）

`run_flow.py --advance --execute-check` 输出的 `loop_control` 字段是 Agent 的推进协议。

### 推进信号表

| 信号 | 含义 | Agent 动作 |
|---|---|---|
| `CONTINUE` | 脚本自己推了一轮（check 通过自动标记 completed），无需 Agent 干预 | **立即再次调用 `--advance`**，同一次会话内循环直到非 CONTINUE |
| `DONE` | 没有更多可推进的块（全部 completed 或 run 已终结） | 执行 finally 块收尾，判定 completion_contract，交 Planner 写 close 状态；close 时写入 lessons/change-summary 供下一环复用（GoPS「结果写回」） |
| `WAIT_USER` | 遇到 star:true 块，需要人工确认 | **环内节点等待判断**：呈现结构化 handoff（仅含事实 SHA + 待判断项 + 不可代签边界），不要求用户读全文；确认后 `--mark-done <label>` 再 `--advance` |
| `WAIT_ROLE` | 遇到需要角色处理的块（HANDOFF），或 check 块需要执行 | 调用对应角色 Skill；完成后 `--mark-done <label>` 再 `--advance` |
| `BLOCKED` | 遇到结构性障碍（环、check 失败、重试耗尽） | 停止并输出障碍，交 Planner 归因 |

## 环系统（v1.7 吸收自黄迅「环的骨架只有一副」）

G0–G10 门禁链 = 环骨架实例：**触发(G0) → 生产(G1→G2→G4→G5) → 闸门(G3/G5/G6/G7) → 人审(G3`*`/G8) → 入库(G9) → 复用(G10)**。

### Agent 实现伪代码

```text
function run_automation(workflow_path, run_dir):
    loop:
        output = run("python3 scripts/run_flow.py {workflow_path} {run_dir} --advance --execute-check")
        signal = output.loop_control

        if signal == "CONTINUE":
            continue  // 脚本自己推了 check 块，继续下一轮

        elif signal == "DONE":
            // 全部完成；确保 finally 被执行（再调一次）
            run("python3 scripts/run_flow.py ... --advance --execute-check")
            call planner to close run
            break

        elif signal == "WAIT_USER":
            // 环内节点：呈现结构化判断材料，不要求人读全文
            ask_user_with_structured_handoff(output.actions[-1])
            on_confirm:
                run("python3 scripts/run_flow.py ... --mark-done {star_block.label}")
                continue

        elif signal == "WAIT_ROLE":
            // 环间交接：只传可验证事实（SHA+命令输出），不传"AI说是这样"
            handoff = extract_facts(output.actions[-1])  // SHA, file list, deterministic output only
            if handoff_block.block_type in ("check", "script"):
                call implementer skill with handoff  // evidence-only, no AI claims
            else:
                call {handoff_block.role} skill with handoff
            run("python3 scripts/run_flow.py ... --mark-done {handoff_block.label}")
            continue

        elif signal == "BLOCKED":
            report_blocked(output)
            break

        else:
            error("unknown signal: " + signal)
            break
```

### 轮次日志（ledger）v1.7.2

`run_flow.py --advance` 每轮自动向 `state.yaml` 的 `ledger` 字段追加一条记录（含 round/timestamp/block/action/signal）。中断恢复时读取 ledger 最后一条即可定位推进位置，无需扫描全账本。详细字段见 `docs/05-state-and-evidence.md` §自动化推进轮次日志。

### 环间接口规范（v1.7）

环间交接包（`handoff.md`）必须：
- **只传可验证事实**：SHA、文件清单、测试输出——来自确定性脚本
- **不含 AI 声明**：不得包含"经检查通过""已验证完成"等不可追溯声明
- **判断结论独立**：APPROVE/REQUEST_CHANGES/BLOCKED 来自该角色独立判断，不递推上一环结论

### 熔断

自动化循环内仍需 Agent 层熔断：

- 5 分钟无可观察产物 → 中断当前块，记录卡点。
- 30 分钟 → 软检查点，汇报进度与缺口。
- 同一块 CONTINUE 超过 10 轮 → BLOCKED（脚本本身不应出现无限循环，Agent 兜底）。
- 同一 WAIT_ROLE 连续 2 次角色失败 → BLOCKED，交 Planner 归因。

## 单轮决策算法（v1.5 兼容模式）

不使用 `--advance` 时，`run_flow.py` 输出 frontier 报告 + `loop_control` 字段。Agent 可按旧模式逐轮手工推进。

```text
输入：state.yaml、工作流定义
1. 若 run_status ∈ {completed, failed, canceled, terminated, timed_out} → 只做 finally 收尾检查，不再派块
2. 若存在 open_blockers → 输出解阻条件，停
3. candidates = 所有 status ∈ {pending, running} 且前置块 status = completed/skipped 的块
4. 若 candidates 为空 → 走终结路径（执行 finally，判定 completion_contract，交 Planner close）
5. 取 candidates 中连边序最靠前的一个 block（黄迅「环骨架」：触发→生产→闸门→人审→入库→复用）：
   a. star == true           → 请求人工确认（approve/wait），不得代签
   b. block_type ∈ {check, script} → 执行 commands，逐条记录 cmd/workdir/exit_code/expect
   c. gate != null           → 先核对门禁证据是否当前有效；无效则派给门禁决策角色
   d. 其他                    → 按 role 交接（handoff 模板字段齐全）
6. 写回块状态（由 Planner 落盘），追加 evidence.md，再更新 state.yaml 索引
```

## 块状态

```text
running → completed | failed | terminated | canceled | timed_out | skipped
```

- `skipped` 必须写原因：条件分支未命中 / 门禁不适用 / 被 finally 短路。
- `failed` 必须绑定已注册 `error_codes` 或明确归因，不能只写"出错了"。
- 循环级合成失败（超 `max_iterations`、缺 block label）要标为**合成失败**，不得当成真实子块结果（Skyvern `BlockResult.is_synthetic_loop_failure`）。

## Run 状态

```text
created → queued → running → (paused) → completed | failed | canceled | terminated | timed_out
```

`paused` 非终结，可恢复（等人工批准 `*`、外部系统、凭据）。`terminated` = 被门禁或护栏主动终止。`timed_out` = 超 `max_elapsed_time_minutes`。

## 失败路由

| 现象 | 动作 |
|---|---|
| 命令退出码 ≠ expect | 记 `failed` + 错误码；`max_attempts` 未耗尽则退避重试 |
| 重试耗尽 | 交 Planner 归因（`SPEC/TEST/IMPLEMENTATION/ENVIRONMENT/BASELINE/SCOPE_CHANGE/UNKNOWN`） |
| 非关键块失败且 `continue_on_failure: true` | 记失败并继续；`star` 块禁止此路径 |
| 循环体内失败且 `next_loop_on_failure: true` | 跳到下一次迭代 |
| 身份/授权/证据缺失 | `BLOCKED`，写精确解阻条件，不改生产代码 |
| 任何终结路径 | 执行 `finally_block_label`；finally 不得做发布、合并、push 或不可逆动作 |
| **空操作失败**（命令成功但无副作用） | 黄迅 2026-09 案例：资产入库每次提交空 commit → `run_flow.py` check 命令非零退出 + 附加副作用检测（v1.7 新增「失败必须有名字」） |
| **信号混淆**（成功/失败/未知共享同一显示） | 黄迅案例：覆盖率"采集失败"="没有数据" → Reviewer 必须显式区分 UNKNOWN vs FAILED（v1.7 新增） |

## 账本追加顺序（不可颠倒）

1. 角色独立生成完整载荷。
2. Planner **原样**追加到 `evidence.md`（不改写、不摘要、不合并）。
3. 再更新 `state.yaml` 索引。
4. 中断恢复先核对记录 ID：同 ID 同载荷 → 复用；同 ID 异载荷 → 阻塞并向原作者求解。
5. 矛盾证据未解决前，对应门禁保持未通过。

## 渐进固化

一个块**首次由角色成功完成**后，才允许降级为 `script`/`check`，并记录 `run_signature`（命令 + workdir + 期望退出码 + 关键输入哈希）。任一顶层块未固化，整条 run 仍按 `agent` 语义执行，不得"半自动混跑却宣称确定性"。`conditional`、`wait`、`approve`、`review`、`release_check` 永不固化。
