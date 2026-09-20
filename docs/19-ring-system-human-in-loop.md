 # 19 · 环系统与人机协作：吸收黄迅「AI Coding 深水区」与 GoPS「Agent 进生产」

 &gt; 吸收自：黄迅「两万字长文｜手把手带你趟过 AI Coding 深水区：编码让位，人退到哪里」（2026-09-12，PUBG Mobile 百万行 Lua + 自研框架实战）+ AI运维实验室「在 GOPS 讲完"一人 + AI Agent 军团"，我更确定：Agent 进生产，关键不在模型，而在 Harness」（2026-07-12/解读 2026-08-04）
 &gt; 两篇原文经 curl + 移动端 UA 实际抓取并提取正文，标题确认无误。
 &gt; 本文提取可吸收的核心论点，并逐条映射到本工作流的设计决策与已有能力。

 ---

 ## 一、黄迅篇核心论点与吸收

 ### 1.1 总纲：「机器提供事实，人做判断」

 &gt; "手上这件事，是事实，还是判断？是事实就交给机器，别让人去核对，也别听 AI 声明；是判断就留给人，别指望机制替他拍板。"

 **本工作流映射**：
 - **事实**：编译结果、测试结果、覆盖率、lint 输出 → `scripts/` 确定性脚本产出
 - **判断**：架构决策、安全取舍、需求理解、上线审批 → Planner（G3 approve）、人工 `*` 标记节点
 - **AI 声明不得替代事实**：Reviewer 的 `APPROVE` 必须绑定 SHA + 命令输出（`docs/03-gates.md`）；Implementer 不得自审（`skills/_shared/contracts/role-boundaries.md`）

 ### 1.2 提示词的尽头是基础设施

 &gt; "注意点堆在提示词里，模型会变笨；把约束沉进框架，越厚模型越省心。判据是确定的事实才能做硬门禁，是代理指标最多做提醒；信号要从外部取；误报会逼人把代码写得更差。"

 **本工作流映射**：
 - **已下沉的**：`scripts/validate_workflow.py`（结构校验、无环检查、star 不可绕过）、`scripts/selftest.sh`（48 项断言）、`scripts/compile_dag.py`（DAG 编译归一化）
 - **尚未下沉但已识别的**：CI 侧第二次挂载 selftest（`docs/13-roadmap.md`）
 - **代理指标 vs 事实的区分**：已在 `skills/_shared/contracts/gate-policy.md` 风险分层表中体现

 | 黄迅判据 | 本工作流实施 |
 |---|---|
 | 判据是确定事实 → 硬门禁 | `validate_workflow.py` 拒绝无效 YAML、环、star 绕过 |
 | 判据是代理指标 → 最多提醒 | Reviewer 的 advisory Finding → 转后续技术债 |
 | 信号要从外部取 | Verdict 绑定 SHA + 命令输出 |
 | 误报的代价：逼人写得更差 | gate-policy 不因"改动小"自动降级 |

 ### 1.3 编排的尽头是 Runtime

 &gt; "agent loop 的每个环节都必须可审计、可干预。编排问题追到根上是 runtime 主权问题。"

 **本工作流映射**：
 - v1.6.0 的 `run_flow.py --advance --execute-check` → `loop_control` 信号驱动循环
 - 每块状态写入 state.yaml，可审计
 - `run_flow.py` 拒绝超限重试、拒绝 status 回退——运行期强制

 **黄迅「失败不可见」四类事故 vs 本工作流检测**：

 | 失败类型 | 黄迅案例 | 本工作流检测 |
 |---|---|---|
 | 空提交循环 | 资产入库每次提交空 commit | check 命令非零退出即阻断 |
 | 信号混淆 | 覆盖率"采集失败"="没有数据" | Reviewer 区分 UNKNOWN vs FAILED |
 | 僵尸任务 | 重试队列锁死调度 | max_attempts + 熔断（`docs/07`） |
 | 替身实现 | 可选能力被实现=测试绿，生产漏接 | completion_contract 逐条判定（`docs/03`） |

 ### 1.4 环系统（Ring System）

 &gt; "环的骨架只有一副——触发、生产、闸门、人审、入库、复用。环的目标是整个研发周期。"

 **本工作流 G0–G10 门禁链即环骨架实例**：

 ```
 触发(G0) → 生产(G1→G2→G4→G5) → 闸门(G3/G5/G6/G7) → 人审(G3`*`/G8) → 入库(G9) → 复用(G10)
 ```

 **环间接口标准化**：

 | 环接口 | 传入事实 | 传出事实 | 本工作流实现 |
 |---|---|---|---|
 | Intake→Recon | 用户需求原文 | 场景分类+非目标 | state.yaml + current.md |
 | Spec→Plan | Spec+门禁判定 | 冻结DAG+变更预算 | compile_dag.py 编译输出 |
 | Implement→Review | 候选SHA+实现报告 | Review Verdict+Findings | evidence.md 只追加 |
 | Review→Accept | Review Passed SHA | Accepted SHA | state.yaml status 转换 |
 | Accept→Close | Accepted SHA+证据 | lessons+change-summary | current.md 追加 |

 **核心原则**：环与环之间不传两份事实，不传"AI 说它是这样"。事实源唯一且可推导（如文件路径推导归属，而非依赖 AI 声明）。

 ### 1.5 人是环里的节点，不是环外的验收员

 &gt; "降低人做判断的成本——用一切手段，让人能高效、轻松地完成判断。"

 **本工作流映射**：
 - `star: true` 节点 = 环内人工接口
 - v1.6.0 `WAIT_USER` 信号 = 环内节点等待判断
 - 交接包（`handoff.md`）必须结构化，不让 Reviewer 读全文才做判断

 ### 1.6 「常」与「流」

 &gt; "提示词、编排、评测数字都会随模型换代作废——它们是流。把问题想清楚的过程、运维纪律、runtime 主权判断、框架层能力、验收杠杆、评测题集、治理判据——它们是常。"

 **本工作流分类**：

 | 类型 | 内容 | 处理方式 |
 |---|---|---|
 | 常 | 三层模型、四角色所有权、G0–G10 门禁、Evidence 只追加账本、scripts/ 确定性校验、VERSION 单一事实源 | 不随模型换代变更 |
 | 流 | Prompt 模板（`prompts/`）、编排参数、LLM 相关配置 | 定期审视（`rule-lifecycle.md` 维护节奏） |

 ---

 ## 二、GoPS 篇新吸收

 ### 2.1 不急着自建统一 RAG

 &gt; "先治理事实源。文件和 Wiki 保持权威。只有召回/权限/时效长期不达标时，才升级检索层。"

 **本工作流**：`docs/` 19 篇是事实源——规则只在唯一位置维护，不复制。

 ### 2.2 知识不是越多越好

 &gt; "只增不减的知识库会把过期事实不断塞回上下文。活跃知识进主索引，定期复核。"

 **本工作流**：`rule-lifecycle.md` 已定义规则复核与废弃节奏。渐进式披露避免全量塞入上下文。

 ### 2.3 OPC 最小单元是闭环

 **本工作流**：`selftest.sh` 70/70（站点在线口径）= 当前闭环证据；离线为 69/69 + 1 SKIP。

 ---

 ## 三、新吸收的设计决策

 ### 决策 1：「失败必须有名字」（v1.7.0 新增）

 - `docs/07-failure-and-recovery.md` 失败分类从 4 类扩展到 6 类：新增"空操作失败""信号混淆"
 - `test-report.yaml` Verdict 增加显式 `UNKNOWN` 判定
 - `run_flow.py` check 输出的 error_message 不得为空或与成功消息相同

 ### 决策 2：判据下沉路线图

 | 级别 | 示例 | 状态 |
 |---|---|---|
 | L1 Prompt | 叮嘱式规则 | ✅ |
 | L2 Skill | SKILL.md + references | ✅ |
 | L3 Hook | pre-commit + selftest | ✅ v1.4.0 |
 | L4 Runtime | run_flow.py 强制 | ✅ v1.6.0 |
 | L5 Permission | 沙箱/网络/文件系统 | 🟡 依赖宿主 |
 | L6 CI 侧 | selftest 在 CI 重跑 | 🟡 roadmap |

 ### 决策 3：环间接口标准化（v1.7.0 强化）

 交接包（`handoff.md`）必须包含且仅包含：
 - 输入事实（SHA、文件清单、测试输出——来自确定性脚本）
 - 判断结论（APPROVE/REQUEST_CHANGES/BLOCKED——独立判断）
 - 不得包含不可追溯的声明

 ### 决策 4：人机协作的「判断成本」设计（v1.7.0 新增原则）

 - WAIT_USER 信号的 handoff 信息必须结构化
 - 未来方向（v1.8+）：交接产物从 Markdown 走向结构化 HTML

 ---

 ## 四、参考链接

 - 黄迅「两万字长文｜手把手带你趟过 AI Coding 深水区」：https://mp.weixin.qq.com/s/tSmMdSSzLgTsAX1JUaZI9Q
 - AI运维实验室「GOPS：Agent 进生产，关键不在模型，而在 Harness」：https://mp.weixin.qq.com/s/1fbIwI5omis0lQ9GFKhl2Q
 - GoPS 深度解读镜像：https://hongtao2agent.xyz/html/gops-agent-production-harness/
 - 黄迅前篇「Harness 会过期吗」：https://mp.weixin.qq.com/s/begqTCRK-6xA9dTJgLr_og（已收录 a15）
