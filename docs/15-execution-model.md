# 15 · 执行模型选择与测试基线

本文只回答一个问题：**一次 AIWorflow 调用该用哪个模型参数？** 其他规则见 `11-toolchain-install.md`。

## 结论

`-c model_reasoning_effort=low`（配合 `~/.codex/config.toml` 默认模型）是**低成本冒烟参数**，只用于：

- 单角色 smoke；
- 单块 `doc_fix` / 只读审核 / 增量测试；
- 验证 Skill 能被 Codex 加载、能产出合法容器与报告。

它不是 AIWorflow 的正式执行标准。正式执行仍以 `~/.codex/config.toml` 的默认模型为准。注：原冒烟推荐 `-m qwen3.7-flash` 已于 2026-09-20 实测下线（`codex exec` 报「模型不存在」），冒烟改用默认模型 + low effort，实测可用：

```toml
model_provider = "custom"
model = "qifu/qwen3.8-max"  # 2026-09-10 实测 ~/.codex/config.toml；以实测为准，可能随环境变化
model_reasoning_effort = "high"
```

## 为什么不能把 flash 写死为唯一参数

- `qwen3.7-flash + low` 在简单路径够快，但 **feature-delivery 多块规划**中出现过错误 schema（顶层自创 `run_id/base_sha/blocks[id]`，或把多个 Planner 块合并成一个大写 `PLANNER`）。
- 正式任务涉及权限、安全、数据、迁移、完整 Planner→Implementer→Reviewer→Tester 链路时，schema/门禁正确性优先于速度。
- 低成本模型不得代签 `APPROVE`、`PASS`、`accepted`；否则结论缺少可信依据。

## 选择矩阵

| 任务 | 模型与 reasoning | 理由 |
|---|---|---|
| 单角色 smoke、只读审核、doc_fix | 默认模型 + low（2026-09-20 实测 flash 已下线） | 快速、低风险，不写核心状态 |
| 完整 feature-delivery / 权限 / 安全 / 数据 / 迁移 | 默认模型 + high（2026-09-10 实测 `qifu/qwen3.8-max`） | 规划与门禁可靠性优先 |
| 多块规划、Planner 建 Run、候选 DAG 生成 | 默认模型 + high（同上） | `compile_dag.py` + `validate_run.py` 严格校验，减少返工 |
| 单块实现 / 定向回归 | 默认模型优先；确有预算限制才降级 | 降级后必须跑块级检查与状态校验 |
| Reviewer / Tester 结论 | 默认模型优先 | 结论门禁不能依赖低成本单点 |

## 最小验证集（每次改动后执行）

```bash
cd /home/feifz/workspace/WanGoPlatform/.ai_worflow
python3 scripts/validate_package.py
bash scripts/selftest.sh
for f in workflows/*.workflow.yaml; do python3 scripts/validate_workflow.py "$f"; done
python3 scripts/validate_run.py runs/RUN-20260920-003
```

## 实机 smoke 命令

```bash
cd /home/feifz/workspace/WanGoPlatform/.ai_worflow
python3 scripts/validate_run.py runs/RUN-20260920-003
timeout 180 codex exec \
  --ephemeral --skip-git-repo-check \
  -C /home/feifz/workspace/WanGoPlatform/.ai_worflow \
  -s danger-full-access \
  -c model_reasoning_effort=low \
  -o /tmp/aiworflow-smoke.txt \
  '你是 aiworflow-reviewer。只读审核 RUN-20260920-003 的 verify_ui 块，输出 review.yaml 到对应 run 目录；不要改 state.yaml。'
```

## 当前事实

- 历史冒烟 Run `RUN-20260908-002`（bugfix-triage doc_fix 主径）磁盘已不存在；现行可验证真实 Run 包括 `runs/RUN-20260920-003`（ui-verification 全块 completed，`validate_run.py` PASS）等，见 `runs/README.md`。
- `~/.codex/skills` 与 `~/.claude/skills` 的 `aiworflow*` 均为符号链接（两宿主收据 1.8.9 指纹一致）；2026-09-20 双宿主只读探针实测：Codex exec 会话与 Claude Code 嵌套会话均能发现并实读 Skill。
- Flow 引擎为 `scripts/run_flow.py` 确定性 DAG 实现（instruction-only 边界内的可执行引擎），非独立常驻进程。
