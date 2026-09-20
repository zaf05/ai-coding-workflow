# contracts/ · 工作流契约

本目录是 AIWorflow 四角色之间的共享契约。每个文件是执行摘要，权威来源在 `../../../../docs/`。

## 契约文件

| 文件 | 内容 | 吸收自 |
|---|---|---|
| `role-boundaries.md` | 四角色所有权矩阵、硬规则、单层调度 | a17 软件工程判断力、a03 Review≠Truth Generator、a12 确定性优先 |
| `gate-policy.md` | G0–G10 门禁、Verdict 三值、门禁过期检查 | a15 Harness会过期、a11 多Agent≠可控执行、a14 规范工具化 |
| `evidence-rules.md` | 六层验证框架、确定性规则优先、账本追加顺序 | a03 六层验证、a12 阿里open-code-review、a01 周期性审计 |
| `workflow-state.md` | 三轨状态、多天恢复、五层闭环映射 | a10 多天工作流、a16 五层闭环、GoPS 上下文连续性 |
| `change-control.md` | 变更类型、冻结例外、渐进式澄清 | a02 Vibe→SDD→Harness、a08 渐进式澄清、a15 规则版本化 |
| `git-policy.md` | 基线顺序、授权边界、Commit非证据 | a04 统一约束入口、a01 Commit时间线 |
| `handoff-contract.md` | 七项交接要素、上下文连续性、跨会话恢复 | GoPS 上下文连续性、a10 多天恢复 |
| `rule-lifecycle.md` | 规则三层体系、有效期与淘汰、规范工具化、护栏分层 | a15 Harness过期、a14 规范工具化、a16 五层闭环 |
| `artifact-lifecycle.md` | Run容器四文件、草稿→发布→取代、局部修订 | `docs/05-state-and-evidence.md` |
