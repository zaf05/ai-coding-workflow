# EVAL-003 · 未知 CLI 参数显式 FAIL，不静默吞

- id: EVAL-003
- 来源: RUN-20260923-002（发现 `--error-codes` 被静默吞掉，v1.8.15 修复为 AIW_UNKNOWN_FLAG）
- 判定方式: 确定性（已入 selftest §15；本用例保留语义口径供 judge 复核）

## 场景

角色会话调用 `run_flow.py` 时传了一个引擎不认识的参数（拼写错误或版本差异，例如
`--error-code` 少了 s）。

## 输入

- `python3 scripts/run_flow.py workflows/x.yaml runs/RUN --advance --error-code FOO`

## 可观察决策

1. 引擎是**显式报错退出**还是**静默忽略该参数继续跑**。
2. 退出码与错误码是否可见（`AIW_UNKNOWN_FLAG`，非零退出）。

## 期望行为

显式 `[AIW_UNKNOWN_FLAG]` FAIL，退出码 2，不做任何状态变更。静默吞参 = 凭据丢失
（RUN-20260923-002 实际踩中：skipped 凭据被吞，验收时才发现凭据从未写入）。

## 判定问题（judge 会话用）

给命令与完整 stdout/stderr/退出码，问：未知参数是否被显式拒绝？任何"继续执行且无告警"
→ REQUEST_CHANGES。
