# 模块画像：consistency

> 项目：AIWorflow | 首次：2026-09-17 | 最近更新：2026-09-17

## 职责边界

- 校验 G0–G10 在 `docs/03-gates.md`、`workflows/feature-delivery.workflow.yaml` 和 `aiworflow-full-flow.html` 三方一致。
- 校验 G3/G8 人工确认、G4 TDD Red、G5 Code Review、G1/G10 context 说明。
- 不执行 Run，也不替代 `validate_run.py` 的运行期状态校验。

## 已知问题

| 问题 | 状态 | 影响 | 来源 Run |
|---|---|---|---|
| `.ai_worflow` 不受 Git 跟踪 | 已接受 | 一致性证据用主仓 HEAD + 文件 SHA256 绑定 | RUN-20260917-006 |

## 测试缺口

| 缺口 | 风险等级 | 补测建议 | 来源 Run |
|---|---|---|---|
| 其他 workflow 未纳入三方一致性脚本 | P3 | 后续可扩展参数化校验 bugfix/ui workflow | RUN-20260917-006 |

## 依赖关系

| 上游 | 下游 | 耦合度 | 说明 |
|---|---|---|---|
| docs/03-gates.md | selftest §11 | 中 | 改门禁定义必须同步脚本 |
| feature-delivery workflow | selftest §11 | 中 | 改块/门禁必须同步脚本 |
| full-flow HTML | selftest §11 | 中 | 改流程图必须同步语义 |
