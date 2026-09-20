# 交接参考（详细）

权威来源：`../contracts/handoff-contract.md`。本文件补充各角色的最小交接包与常见错误。

## Planner → Implementer

```yaml
run_id: RUN-20260908-001
block_label: implement_wp1
action: 实现一个完整纵向块，不实现无关重构
spec_ref: current.md#Spec@v3
base_sha: "<40位完整SHA>"
allowed_paths: ["wanGo/frontend/src/**"]
protected_paths: ["docs/", "contracts/", "wanQore/", "wanDeck/"]
output_contract: implementation-report.yaml → evidence.md#IMPL-<NNN>
budget: {max_attempts: 1, timeout_minutes: 30, tokens_soft: 3000}
```

## Planner → Reviewer

```yaml
run_id: RUN-20260908-001
mode: CODE_REVIEW            # 一次只选一种模式
target: {base_sha: "<SHA>", head_sha: "<SHA>"}
review_scope: "base..head 增量 + 当前开放 Finding"
expected_output: review.yaml → evidence.md#REVIEW-<NNN>
read_only: true
```

## Planner → Tester

```yaml
run_id: RUN-20260908-001
mode: INCREMENTAL | FULL | SMOKE
tested_sha: "<SHA>"
test_plan_ref: test-plan.md
expected_output: test-report.yaml → evidence.md#TEST-<NNN>
```

## 常见错误（接收方应 BLOCKED）

- 只给分支名不给完整 SHA。
- 说"审核一下"却不说审核哪个对象哪个版本。
- 说"修好这个"却不说允许写哪、预算多少、停止条件是什么。
- 让 Implementer 顺带重构无关模块。
- 让 Reviewer 顺带改代码。
- 让 Tester 顺带修生产代码。
