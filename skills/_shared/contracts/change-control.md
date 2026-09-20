# 变更控制契约

> 吸收自：a02「Vibe Coding → SDD → Harness 三层递进」、a08 得乐胶囊「渐进式澄清到 PRD 再到 Spec 驱动」、a15「Harness 会过期」
> 权威来源：`../../../docs/05-state-and-evidence.md`。本文件是执行摘要。

| 类型 | 影响 | 处理 |
|---|---|---|
| `EDITORIAL` | 拼写/格式，含义不变 | Planner 记差异与无语义影响依据，不单独叫 Reviewer |
| `TECHNICAL`（块内预算/内部约束） | 行为不变 | G2 局部技术复审 |
| `TECHNICAL`（DAG 节点/依赖/所有权） | 行为不变 | 先满足冻结例外，再 G2 局部复审受影响节点 |
| `BEHAVIORAL` | 用户可观察行为/契约/数据/权限变化 | 重开 G2 + G3，下游全部失效，重走 G4 及以后 |
| `SCOPE` | 范围扩大/缩小 | 写 Decision；缩小必须记录被砍目标与其去向 |

## 冻结例外

DAG 首次通过 G2 后冻结；只有已证实无法在原块内安全完成 AC 的**结构性障碍**才通过 Decision + Change Log 做最小改图与受影响门禁复审，不自动重建全图。

## 从 Vibe Coding 到 SDD 到 Harness 的递进（吸收自 a02）

> a02「从"凭感觉写代码"到"可控地交付"」提出三层递进模型：
> **Vibe Coding**（凭感觉写）→ **SDD**（规约驱动）→ **Harness**（工作环境+操作规程+反馈回路+安全边界）

本工作流对应的变更控制递进：
- Vibe Coding 阶段（原型探索）：不需要走完整门禁，但变更必须在 `current.md#Decisions` 记录。
- SDD 阶段：所有行为变更走 BEHAVIORAL 流程，Spec 先行。
- Harness 阶段：变更不仅要有 Spec，还必须有证据门禁通过，护栏脚本自动执行。

## 渐进式澄清（吸收自 a08）

> a08「AI 原生开发下的需求确定性构建」：PRD 不是一次性写完的，是渐进式澄清的过程。从模糊意图 → PRD → Spec → AI Coding。

本工作流对应：G0 Intake 接受模糊意图，G2 Spec 做精确化，变更控制允许在 Spec 阶段逐步澄清；**但一旦进入 Plan（G2 冻结），只能通过变更控制改 Spec，不得"边实现边澄清"**。

## 规则本身的变更也需要版本化（吸收自 a15）

> a15：Harness 会过期。删旧规则同写新规则一样重要。

本工作流契约文件的变更：
- 每次修改 `_shared/contracts/` 下的文件，在文件头部或底部记录修改日期与吸收自哪篇文章。
- 被替代的规则行不得保留原样加注释——直接删除。
- 修改后跑 `python3 scripts/validate_package.py` 确认无破坏。
