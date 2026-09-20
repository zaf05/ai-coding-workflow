# 18 · 候选 DAG 全链路：LLM 意图 → 编译 → 冻结 → 执行

> 本文记录「Planner 生成候选 DAG → compile_dag.py 编译 → G4 冻结 → run_flow.py 推进」的完整链路设计、实现与使用方法。

## 一、背景

docs/16 确立了 DAG 正确性分层原则：

1. **意图层（LLM）**：从需求写候选 DAG
2. **编译层（确定性脚本）**：归一化 + 结构校验 + 预算检查
3. **冻结层（人/Reviewer 门禁）**：approve(G3) 批准行为，plan(G4) 冻结 DAG
4. **执行层（deterministic 解释器）**：run_flow.py 推进

本文聚焦 ①②④ 的实现。③ 由 `skills/aiworflow-planner/SKILL.md` 定义。

## 二、候选 DAG 生成（意图层）

### 2.1 Prompt 模板

`prompts/candidate-dag.md` 定义了 Planner 生成候选 YAML 时必须遵守的 13 条规则：

- schema_version、label 唯一性、block_type/role 合法性
- approve 必须 user + star:true
- conditional 必须恰有一个 is_default:true 分支
- 不得产生环（conditional 回边除外）
- 块数不超过 40

### 2.2 示例产物

`prompts/examples/candidate-dag-bugfix.yaml` 是一个完整的候选 DAG 示例，描述「修复 5 个页面搜索闪烁」的工作流。它可以通过 `compile_dag.py` 编译。

### 2.3 已知 LLM 漂移与归一化

`compile_dag.py` 已处理以下常见漂移：

| 漂移 | 归一化 |
|---|---|
| `schema_version: "1"`（字符串） | → 整数 1 |
| `id` / `name` / `block_id` 代替 `label` | → `label` |
| `type` / `blockType` 代替 `block_type` | → `block_type` |
| `next` / `next_label` / `next_block` 代替 `next_block_label` | → `next_block_label` |
| `star: "true"`（字符串） | → 布尔 true |
| `Blocks` / `BLOCKS` 代替 `blocks` | → `blocks` |

## 三、编译层（compile_dag.py）

### 3.1 用法

```bash
python3 scripts/compile_dag.py <candidate.yaml> [-o compiled.workflow.yaml] [--max-blocks N]
```

### 3.2 流程

1. 读入候选 YAML
2. 归一化（只修格式漂移，不发明语义）
3. 预算检查（块数 ≤ max_blocks，默认 40）
4. 序列化归一化结果
5. 委托 `validate_workflow.py` 做全量结构校验
6. 通过 → 输出 `*.compiled.yaml`；拒绝 → 打印全部违规项，不保留半成品

### 3.3 退出码

- 0 = 编译通过
- 1 = 拒绝（结构违规）
- 2 = 参数错误

## 四、执行层（run_flow.py）

### 4.1 用法

```bash
# 默认：输出 frontier 报告
python3 scripts/run_flow.py <workflow.yaml> <runs/RUN-ID>

# 真实执行 check/script 命令
python3 scripts/run_flow.py <workflow.yaml> <runs/RUN-ID> --execute-check

# 自动推进所有可确定性推进的块
python3 scripts/run_flow.py <workflow.yaml> <runs/RUN-ID> --advance --execute-check

# 评估 conditional 块
python3 scripts/run_flow.py <workflow.yaml> <runs/RUN-ID> --evaluate-conditional <block_label> <condition_key>

# 重试失败块
python3 scripts/run_flow.py <workflow.yaml> <runs/RUN-ID> --retry <block_label>

# 追加账本条目
python3 scripts/run_flow.py <workflow.yaml> <runs/RUN-ID> --append-ledger '{"event":"...","data":"..."}'

# 标记块状态（Planner 用）
python3 scripts/run_flow.py <workflow.yaml> <runs/RUN-ID> --mark-running <block_label>
python3 scripts/run_flow.py <workflow.yaml> <runs/RUN-ID> --mark-done <block_label> [--status completed|failed|skipped]
```

### 4.2 子命令说明

| 子命令 | 职责 | 是否写 state.yaml |
|---|---|---|
| 默认（无选项） | 输出 frontier 报告（STAR/CHECK/HANDOFF） | 否 |
| `--execute-check` | 真实执行 check/script 命令 | 否 |
| `--advance` | 多轮自动推进，check 通过后自动标记 completed | 是（仅 check 自动标记） |
| `--evaluate-conditional` | 评估 conditional 块，输出应走的分支 | 否 |
| `--retry` | attempts +1，状态回退 pending | 是 |
| `--append-ledger` | 向 ledger 列表追加条目 | 是 |
| `--mark-running` / `--mark-done` | 标记块状态 | 是 |

### 4.3 条件分支处理

conditional 块创建的有意循环（review → route → fix → review）不算真环。`find_cycles()` 会检测环路径中是否包含 conditional 块，如果包含则跳过。

### 4.4 推进模式（--advance）

`--advance` 会多轮推进：

1. 计算 frontier
2. 对第一个就绪块：
   - STAR → 输出并停止（人工确认阻断）
   - CHECK → 执行命令，通过则自动标记 completed，继续下一轮
   - HANDOFF → 输出并停止（需要角色会话处理）
3. 重复直到没有可推进的块或遇到阻断

### 4.5 失败重试

块的 `max_attempts` > 1 时，失败后可以用 `--retry` 回退到 pending：

```yaml
- label: implement
  block_type: implement
  max_attempts: 2
  retry_backoff_seconds: 60
```

```bash
python3 scripts/run_flow.py workflow.yaml run-dir --retry implement
# → attempts: 1 → 2, status: failed → pending
```

## 五、完整链路示例

```bash
# 1. Planner 生成候选 DAG（用 prompts/candidate-dag.md 模板）
# 产出：candidate.yaml

# 2. 编译
python3 scripts/compile_dag.py candidate.yaml -o candidate.compiled.yaml
# → COMPILED candidate.yaml -> candidate.compiled.yaml

# 3. 创建 run 容器
mkdir runs/RUN-YYYYMMDD-NNN
# 用 skills/_shared/templates/run-state.yaml 初始化 state.yaml

# 4. G0-G2：Planner 执行 intake/recon/spec/decision
# 5. G3：STAR 停下，等用户批准
# 6. G4：Planner 冻结 DAG（把 compiled.yaml 内容写入 state）

# 7. 推进
python3 scripts/run_flow.py workflow.yaml runs/RUN-ID --advance --execute-check

# 8. 遇到 HANDOFF → 开角色会话处理
# 9. 遇到 STAR → 停下等用户
# 10. 完成
```

## 六、验证

```bash
# 全量自检（18 项）
bash scripts/selftest.sh

# 包校验
python3 scripts/validate_package.py

# 候选 DAG 编译
python3 scripts/compile_dag.py prompts/examples/candidate-dag-bugfix.yaml -o /tmp/test.compiled.yaml

# run_flow 推进
python3 scripts/run_flow.py workflows/feature-delivery.workflow.yaml runs/RUN-20260908-006
```

### 4.6 轮次日志自动持久化（v1.7.2）

`--advance` 每轮推进自动向 `state.yaml` 的 `ledger` 字段追加记录（round/timestamp/block/action/signal）。DONE 信号时写入 `round=final` 条目。中断恢复只需读 ledger 最后一条。

## 七、当前事实

- **已实现**：候选 DAG prompt 模板 + 示例、compile_dag.py 归一化 + 编译、run_flow.py 条件分支/重试/账本/推进模式。
- **未实现**：Planner 真实产出候选 DAG 的端到端 run 证据（下一次真实业务工作包时取证）。
- **selftest**：18 通过 / 0 失败。

## 八、v1.6 自动化推进闭环

### 8.1 loop_control 信号

`run_flow.py --advance --execute-check` 从 v1.6 起在报告 JSON 中输出 `loop_control` 字段：

```json
{
  "run_id": "RUN-YYYYMMDD-NNN",
  "run_status": "running",
  "actions": [...],
  "loop_control": "WAIT_ROLE",
  "remaining_blocks": [...],
  "total_rounds": 3
}
```

| 信号 | 触发条件 | Agent 动作 |
|---|---|---|
| `CONTINUE` | check 块通过，自动标记 completed | 立即再次调用 `--advance` |
| `DONE` | 没有更多可推进的块，或 run 已终结 | 判定 completion_contract，交 Planner close |
| `WAIT_USER` | 遇到 star:true 块 | 停下请求用户确认；确认后 `--mark-done` 再继续 |
| `WAIT_ROLE` | 遇到 HANDOFF 块或 check 块未执行 | 调用对应角色 Skill；完成后 `--mark-done` 再继续 |
| `BLOCKED` | 环检测失败、check 命令失败、重试耗尽 | 停止并输出障碍 |

### 8.2 Agent 自动化伪代码

```text
loop:
    output = run("python3 scripts/run_flow.py <wf> <run> --advance --execute-check")
    switch output.loop_control:
        CONTINUE   → continue
        DONE       → run finally → planner.close() → break
        WAIT_USER  → ask_user → mark_done → continue
        WAIT_ROLE  → call_role → mark_done → continue
        BLOCKED    → report → break
```

详细语义见 `skills/aiworflow/references/flow-engine.md` §自动化推进闭环。
