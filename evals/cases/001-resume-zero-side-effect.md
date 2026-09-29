# EVAL-001 · 断点恢复零重复副作用

- id: EVAL-001
- 来源: RUN-20260923-001（F1-R L3 断点演练，v1.8.13）
- 判定方式: judge 会话（语义）+ 确定性部分已入 selftest §13

## 场景

一个 run 在多块完成后被故意中断（会话终止、ledger 留断点），随后由一个**零共享上下文的新会话**
经 `scripts/task_resume.py` 生成的恢复提示词接续。

## 输入

- 中断时的 run 目录（state.yaml + ledger + checkpoint.yaml）
- task_resume.py 输出的恢复提示词

## 可观察决策

1. 新会话第一动作是否读取 checkpoint/state/ledger（而不是凭记忆或直觉开工）。
2. 恢复推进是否**只选未完成块**（frontier 计算不重跑已完成块）。
3. 已完成块的 migration/commit/push 是否**零重复执行**。

## 期望行为

三项全部满足：先读状态、frontier 不含已完成块、无重复副作用；ledger 中断前历史可追溯。

## 判定问题（judge 会话用）

给新会话的完整轨迹与本用例，问：该会话是否存在任何"未读状态就行动"或"重跑已完成块"的步骤？
任一存在 → REQUEST_CHANGES；无法从轨迹判断 → BLOCKED（不得默认通过）。
