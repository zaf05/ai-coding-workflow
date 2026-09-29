# 39 · Ng 技能图谱帖 + 阿里《AI Native 研发范式实践手册》对照收编（2026-09-29）

> 批次：附录 135 → **137**（136 = Andrew Ng X 帖；137 = 阿里手册）。两源均 L1 证据。
> 结论先行：**两源都有用，但都不立项**——136 以印证为主（evals 与部署监控两个强化信号指向已登记缺口）；137 为全景参照（核心主张与既有语料大面积重叠，唯一真新概念 Agent 身份 Delegation Chain 归团队化议题）。零代码、零规则变更，selftest 维持 113。

## 一、来源与取证方式

### 136 · Andrew Ng《AI Engineering Skills Map: Using coding agents》

- URL：https://x.com/AndrewYNg/status/2095890279865721217 （2026-09-04 发帖）
- 取证：X 页面全文抓取（2026-09-29），五技能 / 三阶段结构完整在手。
- 证据级：**L1 全文**。
- 身份注意：帖内另引一幅第三方技能图谱图（作者 Rohan），本批只采信 Ng 帖正文文字，图谱图仅作结构参考。

### 137 · 阿里《AI Native 研发范式实践手册》（68 页 PDF）

- 入口 URL（用户提供）：https://ai-native.alistatic.com/app/ainativeinfra/ai-native-handbook-web/index
- 取证管线（2026-09-29，五步）：
  1. 入口是 **JS PDF 查看器壳**（webReader 只返回「正在打开手册…暂时无法显示预览」）——不是不可达；
  2. curl 壳 HTML，在资产引用中挖出版本化 **PDF 正本直链** `https://g.alistatic.com/s/v/ainativeinfra/ai-native-handbook/0.0.1/ai-native-handbook.pdf`；
  3. 下载正本：27,286,928 B，PDF 1.6，**68 页**；
  4. pypdf 与 pymupdf 文本提取均 **0 正文字符**——确认为**纯图片型 PDF**（每页约 400KB 渲染图）；
  5. pymupdf `get_pixmap(dpi=110)` 渲染 PNG + 视觉转写，覆盖 11 个关键页：p02/p03（简介）、p05（完整目录）、p07（页码偏移确认：PDF 页 = 印刷页 + 6）、p41–p43（3.1.1 核心运行机制）、p49（3.2.1 Sandbox）、p57（3.3.1 Identity & Policy）、p61（3.3.2 Guardrail）、p65（3.4 可观测）、p28（2.3 度量）。
- 证据级：**L1 视觉转写**（正文 PDF 无可提取字符这一事实本身已记录；文字证据来自渲染后转写，非文本层提取）。
- 身份注意：检索中另有一个相似命名仓库 `aliyun/ai-agent-handbook`（995⭐，"enterprise AI agents full lifecycle"），是**不同文档**，仅作生态参考，不作为本源证据。手册署名作者未在所读页中出现，作者信息不入库（不从二手来源补写）。
- 可复用技术备注：纯图片 PDF 的取证路径（壳内直链 → 下载 → 渲染 → 视觉转写）可作为后续同类来源的标准管线；RapidOCR 在本机当前两套解释器均不可用（docs/26 先例曾用过）。

## 二、136 Ng 帖对照：五技能 / 三阶段 → 既有设计

帖结构：三阶段 Planning → Execution →（Deployment & monitoring）；五技能 Directing / Enabling autonomy / Reviewing / Customizing environment / Foundations。

| Ng 帖主张 | 本工作流对应 | 判定 |
|---|---|---|
| Planning→Execution→Verification 生命周期 | G0–G10 门禁链 + 块 DAG | 印证 |
| Reviewing：agentic code review / security audit / human review，截图等 hard evidence | Reviewer 只读角色 + review_preflight + v1.8.21 跨宿主交叉复核 + ui-verification 工作流 | 印证（且我们有交叉宿主版） |
| Customizing environment：AGENTS.md 常备上下文、hooks、CI | context/ 四模板 + docs 语料 + pre-commit hook v3 + CI（v1.8.16） | 印证 |
| 「模型进步就修剪技能」（prune skills when models improve） | rule-lifecycle Add/Thin（v1.8.1 删减四信号 + 模型升级复检） | **直接外部印证** |
| 跨会话保状态（preserve state across sessions） | ledger / checkpoint / task_resume（F1-R L3 断点演练已实证） | 印证 |
| Run 后复盘（post-run retrospectives） | G10 close + lessons/change-summary | 印证 |
| 对 autonomy 保持怀疑、人审关键决策 | `*` 人工不可代签 + 熔断 + 单 Session 边界 | 印证 |
| evals + LLM-as-a-judge 是工程化必经之路 | docs/13 F5 已登记（docs/29 F5 实施方案） | **强化信号，不重复立项** |
| Deployment & monitoring 阶段（上线后监控环） | automations 心跳层缺口已登记（docs/13，v1.8.11） | **强化信号，不重复立项** |

判定：**印证为主 + 两个已登记缺口的独立强化信号**。两个强化信号分别来自业界头部分量来源，可作为未来启动 F5 / automations 时的优先级佐证，记录在案即完成吸收。

## 三、137 阿里手册对照：核心主张 → 既有语料

手册结构（目录 L1 转写）：一、研发范式实践案例（AIDC 数字投手 / 干什么用啥 Agent / 万有无界平台）；二、实践中的挑战（环境与验证 / 平台能力 / 度量 / 数字员工自主性 / 组织配套）；三、企业级 AI 研发基础设施（3.1 Harness：核心运行机制 / 企业知识库 / MCP·Skill·CLI；3.2 运行环境：Sandbox / Coding 环境；3.3 可信与安全：Identity & Policy / Guardrail；3.4 可观测）；四、总结。

| 手册主张（L1 转写页） | 本工作流 / 既有语料对应 | 判定 |
|---|---|---|
| 「模型即引擎，Harness 即底盘」；Coding Agent 时代以 Agent 为核心、Harness 约束 Agent（p41） | a19 黄迅「提示词的尽头是基础设施」同构；三层模型本身就是这个立场 | 印证 |
| 上下文治理四层次：编译 / 分发 / 注入 / **回收（Reclaim）**（p41） | a31 Claude 5 上下文工程（Compilation / Subtraction）已有编译；回收与 compaction/caching 同族，ledger/checkpoint 部分对应 | 印证（「回收」提法可挂 docs/13 evals 语境，不单独立项） |
| Memory 三层：原始层 / 中间层 / 人格化层（p42） | context/ 四模板 + ledger ≈ 原始+中间层；人格化层是企业数字员工概念，单人工作流不适用 | 部分印证 |
| Skill=动态挂载说明书、SOP=流程级规则、Agent+Tool 乐高（p42） | Flow/Role/Skill 三层 + a32 装配/作用域分离已印证 | 印证 |
| Net Anchor：端到端串联全链路、不写具体代码但控制全局（p43） | Planner 唯一状态写入者 + 单层调度同构 | 印证 |
| Agent 级集成测试（p43） | G6/G7 + check 块命令事实 | 印证 |
| Sandbox 三理由：安全 / 环境一致性（长程任务成功率关键）/ 隔离环境验证更可信；gVisor/Firecracker/Kata 选型（p49） | 宿主沙箱 + v1.8.21 最小权限收紧（workspace-write/read-only）；worktree 隔离同族（附录 134） | 印证 |
| Prompt→Skill→Hook→Permission 四层护栏，「与 Claude Code 的四层护栏完全对应」；高风险动作必人工授权（p61） | **a20 GoPS 原文先提出同一四层**；我们 Prompt/Skill/Hook 三层已落地，Permission 依赖宿主（docs/13 登记）；`*` 人工不可代签 | 印证（与大厂生产口径三方一致：GoPS=手册=Claude Code） |
| 可观测三能力：全链路 Trace / 会话回放 / Ledger 不可篡改账本（p65） | ledger + session-meta（model/tokens_used）+ review_preflight 已有 Trace 与 Ledger；会话回放对我们=transcript，单人场景不适用 | 印证 |
| 度量：采纳率 / 读改比 / 改动吸收率（p28） | docs/36（附录 131 淘天海外批）已登记度量口径候选挂 docs/13 evals；同族不重复立项 | 印证（强化 docs/36 批） |
| **Agent 身份三元组 <身份、策略、凭证> + Delegation Chain（代理人身份链传递与收缩）+ AuthN/AuthZ/Audit（p57）** | 无直接对应：单人工作流 Agent 即代表我本人；`*` 不可代签 + session 归因是弱对应物 | **真新概念 → 归 docs/13 团队化议题补充视角，不立项** |

判定：**全景参照**。约九成主张与 a19/a20/a31/a32/a36 及 docs/36 批重叠，其独特价值是「企业平台侧全景图」（数字员工身份、平台化 Sandbox、组织配套、度量运营指标）——全部落在我们明确不做、且已在 roadmap 登记的团队化方向。Delegation Chain 是唯一真新概念，登记进 docs/13 团队化议题作为补充视角（团队化启动时的设计输入），不预写任何代码。

## 四、归属判定汇总

| # | 来源 | 证据级 | verdict | 去向 |
|---|---|---|---|---|
| 136 | Ng 技能图谱帖（X，2026-09-04） | L1 全文 | 印证为主 + 两个已登记缺口的独立强化信号（evals→docs/13 F5；部署监控→automations 心跳层） | docs/13 缺口条目未来启动时的优先级佐证；无代码/规则变更 |
| 137 | 阿里《AI Native 研发范式实践手册》68 页 PDF | L1 视觉转写 | 全景参照（与既有语料大面积重叠）；真新概念 Delegation Chain 归团队化 | docs/13 团队化议题补充视角；纯图片 PDF 取证管线沉淀本文 §一 |

## 五、计数与版本

- 附录：135 → **137**（HTML 附录行 +1+1；README 核验表 row 115–116）。
- 文档：38 篇 → **39 篇**（本文档）。
- 版本：v1.8.21 → **v1.8.22**（纯文档批次，无脚本/断言变更）。
- selftest：维持 **113**（count_sync 口径不变；版本 bump 后双宿主 `install_skills.py --upgrade --apply` 刷新收据）。
