# 角色边界契约

> 吸收自：a17 就是克克「AI Coding 时代真正重要的是软件工程判断力」、a03 仁「Review = Candidate Generator 非 Truth Generator」、a05 王安林「SpecKit+Pi+Superpowers 组合」
> 权威来源：`../../../docs/04-roles.md`。本文件是执行摘要，冲突以 docs 为准。

## 四个角色 + 一个入口

| 角色 | 负责 | 禁止 |
|---|---|---|
| Planner | 需求、仓库画像、Spec、块 DAG、变更预算、`state.yaml`（唯一写入者）、缺陷归因、按 DAG 合并 | 写生产代码、批准自己的产物、兼任 Tester/Reviewer |
| Implementer | 单个已批准块的实现、块级测试、实现报告 | 改需求、扩预算、自审、合并 |
| Reviewer | 只读独立结论、Finding、Verdict | 修改被审对象、更新状态、合并 |
| Tester | 测试计划、测试执行、测试报告、Defect 证据 | 改生产代码或已批准 Spec、为通过而改断言 |
| 入口（aiworflow） | 识别场景、选工作流、决定下一块、交接 | 写状态、下结论、做规划 |

## 软件工程判断力是核心稀缺能力（吸收自 a17）

> a17「AI Coding 时代真正重要的是软件工程判断力」：AI 降低了执行成本，但没有降低质量标准。**判断"什么该做、什么不该做、做到什么程度算够了"的能力是核心稀缺能力。**

本工作流把这个判断力分配到四个角色中：
- **Planner**：判断"需求是否理解到位、拆解是否合理、预算是否可控"——这是最核心的工程判断。
- **Reviewer**：判断"实现是否符合规格、设计是否有隐患"——这是质量判断。
- **Tester**：判断"什么场景最可能出问题、如何覆盖"——这是风险判断。
- **Implementer**：判断"在约束内如何最干净地实现"——这是执行判断。

规则：任何一个角色的判断被跳过（如"小任务不需要 Review"），必须在 `current.md#Decisions` 中记录跳过的理由和风险评估，不得无声省略。

## Review ≠ Truth Generator（吸收自 a03）

> a03「Code Review 与 Verification Agent」十大变化之一：**Review 是 Candidate Generator，不是 Truth Generator。** Verification Agent 才是 Gate。

本工作流对应：
- Reviewer 产出的是 **候选结论**（Candidate Verdict），不是最终真理。
- 最终门禁通过需要：Reviewer APPROVE + 所有 Finding 关闭 + Tester 独立验证。
- 不得因为"Reviewer 说过了"就跳过后续验证步骤。

## 硬规则

1. 任何角色不得批准自己创建或修改的产物。
2. Planner 不写/不修生产代码，不修合并冲突代码。
3. Reviewer 对被审对象只读。
4. Tester 可改测试与测试产物，不可改生产代码/已批准行为，不可为通过改断言。
5. Implementer 一次一个块或一个归因 `IMPLEMENTATION` 的 Defect。
6. 同一 Run 任一时刻只有一个 Planner 写全局状态。
7. 跨角色边界时返回精确缺口，必要时 `BLOCKED`；不得兼任角色或自行派生角色链。

## 单层调度

- 只有当前 Run 的 Planner 创建正式块并调度角色；不为每个块再启动 Planner。
- Reviewer/Tester/Implementer 只完成交接动作，不创建子 Run/Task、不重规划 DAG、不派生角色。
- 块内步骤不是新审批对象。
- 宿主主会话只转发，不是第二个 Planner。

## Reviewer 审核不替代编码规范检查（吸收自 a12）

> a12 Hank「阿里 open-code-review」：确定性规则引擎先扫硬伤，LLM 只做深层判断。

规则：Reviewer 的角色是判断设计/行为/安全语义，不是检查命名规范、缩进、import 顺序。这些由确定性脚本（`validate_*.py`、linter、formatter、pre-commit hook）覆盖。Reviewer 发现格式/规范问题应在 Finding 中注明"应由自动化检查覆盖，建议补充规则"而非逐条手写。
