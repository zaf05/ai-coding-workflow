# workflows/ · 工作流定义

块 DAG（YAML）的可复用定义。块类型、字段、角色↔门禁一致性规则见 `../docs/02-block-catalog.md` 与 `../docs/03-gates.md`。

```text
workflows/
├── feature-delivery.workflow.yaml      功能交付（正例）
├── bugfix-triage.workflow.yaml         缺陷归因（正例）
├── refactor-migration.workflow.yaml    重构/迁移（正例）
├── ui-verification.workflow.yaml       页面验证（正例）
└── _invalid/                           反例（校验器必须按预期拒绝，每个对应一条护栏）
    ├── star-bypass.workflow.yaml           [star_bypass]
    ├── self-review.workflow.yaml           [banned_block]
    ├── unbounded-loop.workflow.yaml        [unbounded_loop]
    ├── unbounded-retry.workflow.yaml       [unbounded_retry]
    ├── secret-inline.workflow.yaml         [secret_inline]
    ├── unsafe-command.workflow.yaml        [unsafe_command]
    └── evidence-free-gate.workflow.yaml    [evidence_free_gate]
```

## 使用

```bash
python3 ../scripts/validate_workflow.py workflows/feature-delivery.workflow.yaml
python3 ../scripts/selftest.sh      # 正例通过 + 反例按预期拒绝
```

## 改定义

- 修改已批准定义走变更控制（`../docs/05-state-and-evidence.md`）。
- 删块、放宽门禁、去掉 `star` = `BEHAVIORAL` + 用户批准 `*`。
- AI 生成/修改定义受 `../docs/09-authoring-copilot.md` 护栏约束。
