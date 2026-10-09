# 40 · 微信 AI Coding 落地实践 16 篇对照收编（2026-10-09）

> 批次：附录 137 → **153**（16 条新收录；用户提供 19 URL 经三层去重后 16 条入库）。全部 L1 证据，其中 40+ 张实质配图经多模态模型真实转写。
> 结论先行：**16 篇全部有用、全部收录，零真缺口立项**——核心主张与本工作流既有设计大面积正面同构（小米 Job/Task/Approval/Event 四实体、去哪儿状态落盘三原则、菜鸟 todo.json 状态机、光剑AI「状态机优于专家圆桌」、小红书「transcript≠运行状态」等）；真新概念仅 3 项且均属边界外或已登记缺口的强化信号（Super Mock 依赖模拟=执行环境层、ACI 工具设计=宿主层、知识自动衰减=rule-lifecycle Thin 强化），记录在案不立项。零代码、零规则变更，selftest 维持 129。

## 一、来源与取证方式

| # | URL 尾段 | 公众号 / 作者 | 标题 | 取证 |
|---|---|---|---|---|
| 138 | mh8XQH5oDk5gq4EZq6oMlQ | InfoQ（得物 AICon 演讲） | AI Coding 之后，如何让 Agent 进入企业研发全链路？得物推荐的 Harness 实践 | webReader 全文 + curl MicroMessenger UA 补图；6 图多模态（Truman 观点卡/PDCA 全 AI 化/7 阶段护栏表等 4 张转写成功，1 张格式 400 放弃，1 张限流 429 重试未果） |
| 139 | TudS13UPV5J6Ap0vLJSiIA | AI前线（菜鸟·郭凤钊演讲实录） | AI Coding 贡献率超 90%，需求交付却只快了 10%：菜鸟如何用 Agent 托管端到端交付？ | webReader 全文 + curl 补图；13 图多模态（贡献率数据页/6 Job·28 Task 全景/Plugins 上下文组件等） |
| 140 | O8hsiVwY9k0ekKC02gixKA | 菜鸟技术星球（已晨） | AICon \| 从 Vibe Coding 到托管交付 Agent：菜鸟研发效能的 AI 实践 | webReader 全文（与 139/141 同演讲独立成文，对照分析合并） |
| 141 | OmdRDue84PQ-dqCDVFwyOg | 进击的雷神（转述郭凤钊 AICon 演讲） | AI 写了 90% 的代码，可需求交付只快了 10%：菜鸟的需求托管交付实践复盘 | curl MicroMessenger UA 全文 + data-src 补图；10 实质图清单 + 3 张多模态（托管全景/Plugins/todo.json+Executor） |
| 142 | 1c_9ZqaaOmrrXekT0Nma2g | 51CTO博客（caison） | 从 Prompt→Context→Harness：AI 编程从代码生成走向工程交付的演进之路 | webReader 全文 + curl 补图；Harness engineering 架构图（Guides 前馈+模块 双向循环）多模态成功 |
| 143 | dSheY-3NpHnpblodK1cwvQ | 火山引擎Agent社区（DeliveryAI产研） | 基于 AgentKit 的端到端需求交付平台：从个人提效到组织提效的 AI 落地实践 | webReader 全文 + curl 补图（列表内重复 URL ×2，合并 1 条）；「一条需求一份 Spec 一条证据链」流程图多模态成功 |
| 144 | Of6On2RiWgscEoV2jwRacQ | Qunar技术沙龙（赵翔） | 去哪儿网：前端需求端到端交付AI落地实践 | webReader 全文；3 图多模态（设计稿预处理/单 Case 执行/多 Agent 调度） |
| 145 | aopO-3KO9lenKF5WHhBD7w | 大淘宝技术（寂秋） | 复杂业务团队的 AI Coding 交付实践：知识库、RD 流程和质量门禁 | webReader 全文；3 图多模态（三层资产/整体架构/ROUTING） |
| 146 | KNJLcIARope82xZoBm-lxA | InfoQ（郑鑫祺，小红书 Muse AICon 演讲稿） | AI 写代码飞快，为何交付没有变快？小红书 Muse 的 Agentic 架构实践 | curl + data-src 补图；3 图多模态（控制架构演进/上下文三层注入/整体架构） |
| 147 | 8LVwfSPux7-ITrSPSmvGew | InfoQ（姚斌斌，腾讯云 CloudQ） | 从 Coding 到 Running：AI Native SRE Agent 的工程实践 | curl + data-src；3 图多模态成功 + 2 张失败如实记录（治理架构图 400×2、评测图服务端黑图） |
| 148 | l5qeFWtXtaStweOqLP7RKA | 小米技术 | 从个人提速到团队提效：小米 AI Coding 工程化实践 | webReader 全文；3 图多模态（多服务汇聚/VKF 2.0 pipeline/核心模型 eight-claw 控制面） |
| 149 | KtFwncQtyfm7x0_s-4Ngyw | 字节范儿（洪定坤，2026-06-25） | 字节跳动技术副总裁洪定坤：AI Coding 的实践与探索 | curl MicroMessenger UA；3 图多模态（TRAE 数据图/900 实验表/Harness 前后散点） |
| 150 | 93KI79Y5GM-ao81-iqD51g | 无处不在的技术（整理自蚂蚁数科刘秀婷 AICon 分享，2026-07-19） | 90%的企业AI Coding落地都"提效了个寂寞"，蚂蚁数科研发体系重塑实践 | curl + data-src；3 图多模态（Harness&Loop 环路/战役大图/Agentic Dev 框架）；质量数据图 400×2 如实记录 |
| 151 | PC3IHMkxUj6IyWuJEr7HfA | PM有所思（2026-07-24） | AI 编程最佳实践：如何让 Agent 真正完成一个需求 | curl + data-src；2 图多模态（六原则总览/沉淀归类） |
| 152 | bmk_y0oM-c2Uzxd-UJouTg | 窥豹（alswl，2026-10-06） | AI Native 时代的工作方式：从信息到交付 | curl + data-src；4 图多模态（minds 仓库结构/自测分层等）；认知图 400 如实记录 |
| 153 | IP5uAElibjv9AmNd-g0mQA | 光剑AI（2026-08-06，开源 AIGeniusInstitute/deepthink） | 自动端到端需求交付的 AI Coding 平台：架构设计与落地实现 | curl + data-src；行业现状表/L3+L4 四角色与 ACI 等 2 张多模态成功；七层图 400×2、总图黑图如实记录 |

取证管线（本批重申，docs/22 §〇 以来铁律）：webReader 对微信正文图仅返回 `blob:` 占位 → `curl -A "MicroMessenger UA"` 抓 HTML → 提取 `data-src`（`&amp;` 反转义、去 `tp=webp` 参数）→ 按文档序去重 → 多模态模型转写。多模态合计约 50 次调用（批 A 主线 + 批 B 子代理 22 次 19 成功 + 批 C 子代理 14 张成功），失败（400 code 1210 格式类、服务端黑图）逐条如实记录，不以正文推断代替图片证据。

## 二、去重台账（列表内 + 库内）

| 重复类型 | 条目 | 处置 |
|---|---|---|
| 列表内同 URL | dSheY ×2 | 合并为 1 条 → 143 |
| 库内 URL 级 | UE-RZH9hnbBd06CVapFGrA | 核验表 row 34 已在库 → 跳过 |
| 库内内容级 | CTY5mdgKh6TmPrO6xsKhWQ（美团 31 万行微信版，og:title《用Agent评测思路管理AI Coding —— 31万行代码AI重构的实践》） | **附录 075 同一篇**（tech.meituan.com/2026/05/07 原文）→ 跳过收录；075 记微信转载版 2026-10-09 可达（证据更新，不新增编号） |
| 内容级同源 | 139/140/141 菜鸟三篇 | 同一郭凤钊 AICon 演讲的三个独立发布（实录/AICon 版/评述转述），分别编号、对照分析合并 |
| 批 C 库内查重 | 洪定坤 / deepthink / AIGeniusInstitute / 刘秀婷 全库 grep 零命中；150（刘秀婷）与 a35（魏长征《可验收》2026-09-04）同公司不同作者不同文章 | 全部按新来源收录 |

## 三、对照判断（按主题簇）

### 3.1 端到端托管交付（139/140/141 菜鸟、143 AgentKit、144 去哪儿、150 蚂蚁数科、153 光剑AI）

| 主张 | 本工作流对应 | 判定 |
|---|---|---|
| 菜鸟：「编码自动化≠交付提速」——贡献率 10%→90%+ 但变更周期仅缩短 ~10%，6 Job/28 Task 仅编码 Job 高度自动化 | G0–G10 覆盖需求对焦到收口全链而非仅编码；docs/37 度量即端到端口径 | 印证 + 度量口径强化 |
| 菜鸟：todo.json 严格状态机——只挑最小序号未完成项、Agent 仅可改状态与起止时间、precheck/gate/artifacts/waitForHuman、Rewind 回退重置后续 | state.yaml + run_flow 引擎（frontier 由 DAG 计算优于固定序号；`--mark-done` 证据/head_sha 门禁=precheck/gate；star 块=waitForHuman）；Rewind 不需要——块间上下文本就不共享 | 强印证（正面同构且引擎侧更强） |
| 菜鸟：「Skill 活在上下文里，没法从外部管自己」 | 外部确定性机制：pre-commit hook v3、validate_* 家族、selftest 129 项 | 印证 |
| 菜鸟：Plugins 四组件（Skills 渐进加载/Subagents 隔离/Hooks 事件前后/MCP·CLI） | context/ 四模板 + skills 分层 + hooks v3 + MCP 使用纪律 | 印证 |
| AgentKit：「一条需求、一份 Spec、一条证据链」「Agent 持续推进·人在关键处决策·每次交付都为下一次积累能力」 | G2 Spec 冻结 + evidence.md 锚点链 + star 人工卡点 + G10 复盘/能力观察 | 强印证 |
| 去哪儿：「执行进度从聊天上下文拿出来写入工程内状态文件」「用户明确确认才能进决策文件，Agent 推荐的不能写成已确认」「多 Agent 只传结构化产物路径不复制聊天记录」 | state.yaml/checkpoint/task_resume 三件套；approvals + star 不可代签；块间 HANDOFF 传 evidence 引用而非 transcript | 强印证（三条逐条同构） |
| 蚂蚁数科：「闭环主体不是 LLM，而是人用 Harness 把 AI 约束在预期路径里」；状态机+产物总线+质量卡点不过自动回退 | 三层模型立场；state.yaml+evidence 产物 + T-02 返修凭据（completed→running 必须有凭据） | 印证 |
| 蚂蚁数科：T1–T5 需求分级差异化授权 | FAST/STANDARD/HIGH_RISK 按风险分级（同族思想，分级轴不同：需求级别 vs 交付风险） | 印证 + 形态差异记录 |
| 光剑AI：「AutoGen 专家圆桌很性感，但生产环境状态机可调试、可重放」 | run_flow 确定性 DAG 解释器 + ledger 可回放 | 强印证（外部独立验证本工作流路线） |
| 光剑AI：「退出条件必须显式声明，不能由 Agent 自己判断」；30 分钟无进展强制暂停、同位置连续失败 3 次请求人类 | complete_criterion + check 命令退出码；熔断/max_attempts/BLOCKED 信号；wango 协议 5 分钟熔断/30 分钟软检查点同构 | 强印证 |
| 光剑AI：四角色硬边界（Coder 不改测试、Reviewer 不改码、结构化 JSON 通信、子 Agent 上下文隔离、并发 2-4） | docs/04 所有权矩阵 + Reviewer 只读 + 单 Session 单 Run + 并行最多两实现流一复核流 | 强印证 |
| 光剑AI：「80% 意味着五分之一任务会失败，平台按失败是常态设计」 | docs/07 失败分类/错误码白名单/重试与自愈/finally | 印证 |
| 光剑AI：Spec 先行「多花 10 分钟返工减 40%+」 | G2 Spec 冻结（外部量化佐证） | 印证 |

### 3.2 Harness 与工程体系价值（138 得物、149 字节、142 演进）

| 主张 | 本工作流对应 | 判定 |
|---|---|---|
| 得物 Truman 卡：「最有效的 Harness 是让他从来不知道自己被关着。好的 Harness 不是铁笼，是环境」 | 三层护栏中环境层（check 命令事实/hook/CI）是最高形态，instruction 是最低层 | 印证 |
| 得物：PDCA 全 AI 化闭环——P=Contract 结构化、D=沙箱+Super Mock、C=动态围栏（自动评测/熔断）、A=Memory bad case 沉淀为规则；7 阶段护栏表（T-PRD/Contract 评审/沙箱/UTD/Super Mock/Axis/排查+Memory） | Spec 冻结（G2/G4）；宿主沙箱；熔断+check；rule-lifecycle Add；G0–G10 门禁链与 evidence 锚点同构 | 印证（四环全有对应物） |
| 字节洪定坤：900 次真实需求实验——正确率均 >80% 但可交付性大幅下降；Harness 加持后正确率 80→90、可交付性 40-60 分→约 80 | 「正确≠可交付」= 门禁+证据链存在的理由；外部实验数据直接支撑三层模型价值 | 印证 + Harness 价值外部实验佐证 |
| 字节：「落地瓶颈不在模型而在工程体系」「单一贡献率指标失真，须端到端全局指标」 | 工程体系即本工作流全部；docs/37 端到端口径 | 印证 |
| 演进（142）：Prompt→Context→Harness 三段论；Harness engineering = Guides（前馈）+ 模块 双向迭代循环 | 三层护栏（instruction→上下文→环境）；prompts/wakeup.md 即前馈约束+反馈传感器双环 | 强印证 |

### 3.3 知识与状态文件化（145 大淘宝、148 小米、152 窥豹、151 PM有所思）

| 主张 | 本工作流对应 | 判定 |
|---|---|---|
| 大淘宝：三层资产（命令协议层/知识层/过程资产层）+ INDEX/ROUTING 按需加载 | skills 命令层 + docs 语料 + runs 过程资产；context_search.py BM25 检索 + `--write-index` | 强印证 |
| 大淘宝：「开发可以中断，研发上下文不能丢」 | task_resume 消费 checkpoint/state/ledger（F1-R L3 断点演练已实证） | 印证 |
| 大淘宝：知识 candidate→confirmed，「错误知识比没有知识更危险」 | rule-lifecycle + 收编批纪律（L3 转引不采信、跨源印证才升级） | 印证 |
| 大淘宝：门禁 fail-fast「能在 PRD 阶段暴露的问题不拖到 requirement」「自动化只会把错误更快地执行完」 | 作者期护栏 validate_workflow 在编写时拦截（而非运行后补刀）；G0–G4 前置 | 强印证 |
| 小米：Job/Task/Approval/Event 文件即状态机 + 审批是显式状态而非聊天确认 | state.yaml 四实体几乎一一对应：run/blocks/approvals/ledger；star 块=显式人工卡点 | 强印证 |
| 小米：「话题是并行推进的最小治理单元」 | 工作包切分门禁（15 文件/1,500 行）+ 单 Session 单 Run | 印证 |
| 小米：VKF「不是给 AI 塞代码，而是给知识目录和索引」；知识 draft→verified→proven + 自动衰减 + Lint | context_search 索引化；rule-lifecycle（自动衰减=Thin 的强化信号，见 §四） | 印证 |
| 窥豹：「材料进仓库，不留在聊天窗口里」；知识经营 PR 化（材料→判断→判决→证据→PR→合并） | 文件化状态/证据；收编批流程（抓取→去重→对照判定→计数同步→提交）即知识 PR 化 | 强印证 |
| 窥豹：guides 用祈使句（动作+对象+标准）；自测分层 smoke→API→CLI→E2E fail-fast + 判决带运行证据回写 | workflow.yaml 块定义即祈使句（goal/complete_criterion/commands）；check 块 + 分层验证纪律 | 印证 |
| PM有所思：六原则（先确认理解/完整业务闭环/给结果不微操/自动审核/看到结果才算验证/分层沉淀+人决定留什么） | G0/G1+Spec 冻结；纵向切片（docs/25）；star+complete_criterion；check+review；ui-verification hard evidence；五层沉淀映射（AGENTS.md→Skill→Hook·CI→专用 Agent→runs 不作知识） | 印证（五层映射一一对应） |

### 3.4 控制面与运行时（146 小红书、147 腾讯云 SRE）

| 主张 | 本工作流对应 | 判定 |
|---|---|---|
| 小红书：「模型决定能力上限，工程控制面决定能不能进生产」 | 三层模型立场（a19 同族） | 印证 |
| 小红书：「不要把对话记录当成运行状态。Transcript 是审计材料」 | state.yaml 唯一状态源；task_resume 从 state/checkpoint/ledger 恢复，从不读 transcript | 强印证 |
| 小红书：「可验证的程序化护航，取代把规则写进 Prompt 然后祈祷」 | selftest 129 项 + validate_* 家族 + review_preflight | 强印证 |
| 小红书：上下文删除实验（删掉指标不变的上下文只是在消耗窗口）；控制架构随模型演进 Workflow→Pipeline→Agent Team 刚性放松 | rule-lifecycle Thin 删减四信号 + 模型升级复检 | 印证 + 强化信号 |
| 腾讯云：「图谱不是给人看的，是给 Agent 看的」 | context_search 的消费方就是 Agent 会话 | 印证 |
| 腾讯云：L1/L2/L3 自治分级 + 只读自由探索审计留痕 | 风险分级 + Reviewer 只读 + ledger 审计 | 印证 |
| 腾讯云：图谱腐烂治理（TTL/心跳判活/时间戳衰减/content hash/GC） | rule-lifecycle Thin 的运行时版本（强化信号，见 §四） | 印证 + 强化信号 |
| 腾讯云：定时任务计划编译+重放（50% 完全脚本化 LLM=0、Token 降约 65%、178s→2-60s） | workflow.yaml 即编译好的计划、run_flow/check 命令即 PlanExecutor（同构：把 LLM 推理固化成确定性重放） | 印证 |

## 四、真新概念与强化信号（记录在案，不立项）

| 概念 | 来源 | 判定与去向 |
|---|---|---|
| Super Mock / 依赖模拟（让 AI 自主开发不卡住的 mock 层） | 138 得物、143 AgentKit「DO 零等待」 | 执行环境层基础设施，属宿主/平台职责，不在本工作流引擎边界内 → 记录为执行环境参照，不立项 |
| ACI（Agent-Computer Interface）工具设计实证：禁直接 cat（专用查看器 100 行/屏）、编辑必跑 linter、终端输出截断 | 153 光剑AI | 宿主层（Claude Code/Codex）工具设计证据；本工作流消费宿主工具不定义工具 → 记录为宿主层参照 |
| 知识自动衰减 / TTL / 心跳判活 | 148 小米、147 腾讯云 | rule-lifecycle Thin 删减四信号的自动化强化；触发条件（知识条目规模大到人工 Thin 不可持续）未到 → 挂 docs/13 既有条目，不重复立项 |
| T1–T5 需求分级授权 / L1–L5 成熟度 / SIGN 指数 | 150 蚂蚁数科 | 团队化与组织度量议题 → docs/13 团队化参照（docs/39 Delegation Chain 同区） |
| 度量口径：贡献率失真、端到端周期、AI 参与需求周期缩短 ~10% | 149 字节、139 菜鸟 | docs/37 度量基线同族强化（一次通过/返修/跨度已是端到端口径），不新增指标 |
| Harness 价值量化（900 次实验；Spec 先行 10min→返工 -40%） | 149 字节、153 光剑AI | G 门禁与三层模型价值的外部量化佐证，记录引用即可 |

## 五、归属判定汇总

| # | 来源 | 证据级 | verdict | 去向 |
|---|---|---|---|---|
| 138 | 得物 Harness 实践（InfoQ/AICon） | L1 + 6 图多模态 | 印证为主（PDCA 四环全有对应物）；Super Mock 归执行环境参照 | 本文档 §3.2/§四 |
| 139 | 菜鸟托管交付实录（AI前线） | L1 + 多模态 | 强印证（todo.json 状态机同构）；度量口径强化 | §3.1/§四 |
| 140 | 菜鸟 AICon 版（菜鸟技术星球） | L1 | 同 139（同演讲独立成文） | §3.1 |
| 141 | 菜鸟评述转述（进击的雷神） | L1 + 3 图多模态 | 同 139 + 「指标唯一目标化」印证 docs/37 诚实口径 | §3.1/§四 |
| 142 | Prompt→Context→Harness 演进 | L1 + 架构图多模态 | 强印证（wakeup.md=前馈/反馈双环） | §3.2 |
| 143 | AgentKit 端到端平台 | L1 + 流程图多模态 | 强印证（Spec/证据链/人工卡点）；「DO 零等待」归执行环境参照 | §3.1/§四 |
| 144 | 去哪儿前端端到端 | L1 + 3 图多模态 | 强印证（状态落盘三原则逐条同构）；设计稿预处理为领域特定不采纳 | §3.1 |
| 145 | 大淘宝知识库/RD/门禁 | L1 + 3 图多模态 | 强印证（三层资产/INDEX/ROUTING/fail-fast） | §3.3 |
| 146 | 小红书 Muse Agentic 架构 | L1 + 3 图多模态 | 强印证（transcript≠运行状态/程序化护航）；上下文删除=Thin 强化 | §3.4/§四 |
| 147 | 腾讯云 AI Native SRE | L1 + 3 图多模态（2 失败如实记录） | 印证（自治分级/计划编译重放）；图谱腐烂治理=Thin 强化 | §3.4/§四 |
| 148 | 小米工程化 | L1 + 3 图多模态 | 强印证（Job/Task/Approval/Event 一一对应）；组织议题归团队化 | §3.3/§四 |
| 149 | 字节洪定坤实践与探索 | L1 + 3 图多模态 | 印证 + Harness 价值外部实验佐证（900 次实验） | §3.2/§四 |
| 150 | 蚂蚁数科刘秀婷 Agentic Dev | L1 + 3 图多模态 | 印证（状态机+回退+分级）；成熟度指数归团队化 | §3.1/§四 |
| 151 | PM有所思最佳实践 | L1 + 2 图多模态 | 印证（六原则/五层沉淀映射）；深度偏个人实践 | §3.3 |
| 152 | 窥豹 AI Native 工作方式 | L1 + 4 图多模态 | 强印证（材料进仓库/知识 PR 化/祈使句/分层 fail-fast） | §3.3 |
| 153 | 光剑AI 七层平台（deepthink 开源） | L1 + 2 图多模态（2 失败如实记录） | 强印证（状态机优于圆桌/显式退出/四角色硬边界）；ACI 归宿主层参照 | §3.1/§四 |

## 六、计数与版本

- 附录：137 → **153**（HTML 附录行 +16；README 核验表 row 117–132）。
- 证据更新（不新增编号）：附录 075 记微信转载版（CTY5）2026-10-09 可达。
- 文档：39 篇 → **40 篇**（本文档）。
- 版本：v1.9.0 → **v1.9.1**（纯文档批次，零脚本/零断言变更）。
- selftest：维持 **129**（count_sync 口径不变）。
