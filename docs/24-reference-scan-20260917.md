# 24 · 参考来源扫描（2026-09-17）：13 篇微信文章

> 扫描日期：2026-09-17（Asia/Shanghai）。
> 证据等级沿用 `22` §〇：L1 全文核验 + L1-IMG 图片识别。
> 所有 URL 以 MicroMessenger UA 实际抓取，HTTP 200；正文提取成功；126 张配图全部下载并 RapidOCR 识别。
> 原始数据在 `/tmp/iai-ref2/`（会话级，非仓库交付物）。

---

## 一、来源清单

| # | 标题 | 正文 | 图片 | 核心主题 |
|---|---|---|---|---|
| b1 | 看完我的AGENTS.md | 2,926 字 | 4 | AGENTS.md 语言纪律：禁废话句式/黑话/单字缩写；一步到位不分期；不许无意义列举 |
| b2 | 15.5万Star的19个skill | 3,488 字 | 10 | Matt Pocock 流水线 grill→to-spec→to-tickets→implement→review；四种翻车根因=无流程 |
| b3 | 货拉拉 AI Coding 落地 | 6,710 字 | 12 | 三阶段演进(普及→规范→AI Native)；AiBox 统一工作台(Rules/Skills/Context/Spec 四类资产)；SDD 五步产线；Spec 自反馈闭环 |
| b4 | 看懂AI写的技术方案 | 5,501 字 | 7 | AliExpress AAIC：/explore /propose /apply /test 四命令；方案面向AI执行 vs 面向人评审的矛盾 |
| b5 | Agent 自进化全景 | 11,070 字 | 20 | Skill/Memory/Prompt/Workflow 非参进化 + RL/微调参数进化；Trace2Skill；执行→反馈→优化→再执行闭环 |
| b6 | Matt Pocock 工作流拆解 | 22,023 字 | 48 | 上下文越长模型越笨；每次会话重新开始；深工作模式=窄窗口单Skill；Sandcastle 多Agent编排 |
| b7 | Worktree+Submodule 多仓Git | 8,435 字 | 4 | 多需求并行用 Worktree 隔离现场；Submodule 锁定多仓版本；集成在 Workspace 根目录 |
| b8 | code-review-graph 80x | 3,853 字 | 2 | Tree-sitter 代码图谱+Blast Radius；增量更新；精准上下文 |
| b9 | Compound Engineering | 12,675 字 | 4 | 小改进复合成大结果；PLAN→EXECUTE→VERIFY；知识在交叉点复合 |
| b10 | Bug分析写成Skill | 3,554 字 | 2 | 八步：数据输入→校验→清洗→特征→模型→规则→风险→报告；10分钟出排查报告 |
| b11 | Debugging Skill | 2,756 字 | 2 | Reproduce→Isolate→Reduce→Fix Root Cause→Guard→Verify；Stop-the-Line 原则 |
| b12 | Archify 19.5K Star | 5,282 字 | 11 | 从代码生成可验证架构/工作流/时序/数据流/生命周期图；HTML/SVG/PNG 导出 |
| b13 | Codex 多Agent实战 | 8,886 字 | 0 | 职责隔离而非数量：实现Agent/审查Agent/测试Agent；独立代码审查门禁 |

---

## 二、图片识别结果

126 张图片全部下载并 OCR。关键框架图识别摘要：

| 图片 | OCR 内容 |
|---|---|
| b2-01 | 核心流水线：数据流→grill-with-docs→to-spec→to-tickets→implement→code-review |
| b2-03 | AI写代码四种翻车：①没听懂要什么 ②代码太啰嗦 ③看着对一跑就炸 ④越改越烂；根因=跟人合作有PRD/CodeReview/测试规范，跟AI只有聊天框 |
| b3-01 | 三阶段演进：01普及(全员用起来)→02规范驱动(AI按规范写)→03 AI Native(全生命周期闭环) |
| b3-03 | AiBox四类资产：Rules规范+Skills技能+Context上下文+Spec说明书；一个人调好，所有人复利 |
| b3-04 | SDD五步产线：澄清需求→技术方案→实施计划→编码实现→代码审查；每一步产物都是下一步输入 |
| b3-05 | Spec自反馈闭环：①使用spec→②打分spec(命中度/缺口/误导)→③回写spec→④进化spec→下一轮用新版 |
| b3-06 | 全生命周期闭环：前向交付(需求到合入)→资产沉淀→线上反哺→下一轮需求自带历史资产 |
| b6-48 | Sandcastle README：TypeScript库，本地多Agent编排 |
| b7-01 | 一个目录只能排队，两个Worktree才能并行：Agent A退款需求，Agent B登录问题，各自独立现场 |
| b7-03 | Workspace根目录锁定多个Submodule：backend/share/frontend 通过 .gitmodules + gitlink 记录 commit |
| b7-04 | 跨仓任务流程：确认多仓基线→创建任务Worktree→每仓库一条任务分支→集成验证 |
| b8-02 | 爆炸半径：影响分析→范围评估→变更感知→实时同步→82x token 缩减 |
| b9-02 | Debug流程：Bug→Terminal→Traceback→定位→修复 |
| b9-03 | PLAN: Clarify objective→Gather context→Choose strategy→Define success criteria |
| b10-01 | 八步工作流总览：数据输入→校验→清洗→特征→模型→规则→风险→报告 |
| b10-02 | 对比：没有工作流(混乱低效率) VS 有工作流(清晰高效) |
| b12-03 | Archify流程：Intake→Plan+route→Workflow→Generated-Checked |
| b12-05 | 观测性架构：Signals+SLO Alert→Incident Command→Declare→Page→Triage+mitigate→Verify+close |

---

## 三、核心发现与采纳决策

### 已成立（不需要改）

| 来源 | 发现 | 与现有设计对应 |
|---|---|---|
| b2 | 五步流水线 grill→spec→tickets→implement→review | G0→G2→G4→G5 已覆盖同一骨架 |
| b6 | 上下文越长模型越笨；窄窗口单Skill深工作 | 最小任务包 ~3000 token + 单块实现 |
| b7 | Worktree 并行隔离 + Submodule 多仓版本 | WanGo 交付协议已规定 worktree + 并行包 |
| b8 | Blast Radius 代码图谱省 80x | C1 影响面范围已落地 |
| b9 | PLAN→EXECUTE→VERIFY | G2 Spec→G5 Implement→G6-G7 Verify |
| b13 | 多Agent职责隔离：实现/审查/测试各司其职 | 四角色分离 + Reviewer 只读 + Tester 独立 |
| b1 | AGENTS.md 语言纪律 | 根 AGENTS.md 已有类似规则（中文/证据/验证） |

### 应吸收的改进

| # | 来源 | 改进 | 落地位置 | 状态 |
|---|---|---|---|---|
| D1 | b3 | **Spec 质量反馈**：Run 结束后对 Spec 打分（命中度/缺口/误导），回写使下一轮进化 | `docs/07-failure-and-recovery.md` §Spec 质量反馈 | ✅ 本轮落地 |
| D2 | b11 | **调试流程结构化**：bugfix-triage 工作流加入 Reproduce→Isolate→Reduce→Fix→Guard→Verify 六步 + Stop-the-Line 原则 | `docs/07-failure-and-recovery.md` §调试六步 | ✅ 本轮落地 |
| D3 | b3 | **全生命周期闭环意识**：前向交付→资产沉淀→线上反哺→下一轮需求自带历史资产。G10 Close 时必须检查是否已产出可复用资产 | `docs/07-failure-and-recovery.md` §沉淀出口（增强） | ✅ 本轮落地 |

### 记录为参考但不采纳

| 来源 | 能力 | 理由 |
|---|---|---|
| b5 | Agent 自进化全景（Trace2Skill/RL/微调） | 理论全景有价值但当前无足量轨迹数据和训练预算；非参进化已由 C2/D3 覆盖 |
| b12 | Archify 架构图生成 | 生成工具与工作流引擎无关；站点已有静态架构图 |
| b4 | AAIC 四命令 /explore /propose /apply /test | 命令式封装与我们块DAG+四角色等价；不引入命令别名层 |
| b10 | Bug 分析八步 Skill | 与 D2 调试六步重叠；八步更适合数据分析场景而非代码bug |
| b6 | Sandcastle TypeScript 多Agent编排 | 引入 TypeScript 运行时依赖；与 instruction-only 定位冲突 |

---

## 四、核验声明

- 所有 URL 实际 HTTP 200，正文提取成功；无一篇被反爬拦截。
- 126 张图片全部下载（mmbiz 域过滤），RapidOCR 逐张识别，纯图形标注为 0 行文本。
- "应吸收"条目只改文档层指引，不改变 workflow YAML schema。
- b13 正文 0 张图（纯文字+代码），已确认非漏抓。
