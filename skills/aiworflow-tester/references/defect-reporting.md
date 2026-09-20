# 缺陷报告参考

> 受约契约：`../../_shared/contracts/artifact-lifecycle.md`（失败必须入账、归因交 Planner）
> 吸收自：a01 周期性系统审计、GoPS「失败路径必须入账」

## 记录字段

`defect_id`、归属（`SPEC/TEST/IMPLEMENTATION/ENVIRONMENT/BASELINE/SCOPE_CHANGE/UNKNOWN`）、严重度、复现步骤、期望/实际、环境、证据（命令输出/截图/日志片段，脱敏）。

## 规则

- 归因由 Planner 最终写入 `state.yaml`，Tester 提供事实。
- 不得把新增需求伪装成 Defect；范围变化走 `SCOPE_CHANGE`。
- `BLOCKED` 只用于证据/环境不可用，不因"难"而阻塞；写精确解阻条件。
- 失败、`BLOCKED`、`not_run` 都必须落盘，不允许静默消失或改写成"基本通过"。
- Tester 不自行修改生产代码修复 Defect。
