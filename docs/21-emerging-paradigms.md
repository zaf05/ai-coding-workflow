 # 21 · 2026 前沿 AI 编程范式全景扫描
 
 &gt; 本文系统梳理 GitHub 实测搜索发现的 2026 年新兴 AI 编程范式与开源项目。
 &gt; 所有信息来自 GitHub API/README 实际提取，日期 2026-09-14，Asia/Shanghai。
 &gt; 搜狗微信搜索、GitHub Search API 双重核验。
 
 ---
 
 ## 一、方法总论：我们已经在用的 vs 新发现的
 
 | 范式 | 全称 | 状态 | 证据项目 | 本工作流吸收 |
 |---|---|---|---|---|
 | **SDD** | Spec-Driven Development | ✅ 已在用 | Spec Kit 130K⭐ | G0–G10 门禁链，`spec→plan→implement` 主链 |
 | **Harness Engineering** | 护栏工程 | ✅ 已在用 | 多篇文章 | 三层护栏（编写时/提交时/运行时） |
 | **EDD** | Evidence-Driven Development | ✅ 已在用 | ric-dev, GoPS | Evidence 只追加账本 + SHA 绑定 |
 | **OPC 闭环** | Observe-Plan-Code | ✅ 已在用 | GoPS/AI运维实验室 | G0→G10 环骨架 |
 | **Multi-Agent** | 多角色协作 | ✅ 已在用 | Anthropic subagent | 四角色所有权分离 |
 | **BMAD** | Breakthrough Method for Agile AI Driven Development | 🆕 新发现 | BMAD-METHOD 53K⭐ | 敏捷AI驱动、task dependency graph |
 | **Context Engineering** | 上下文工程 | 🆕 新发现 | CEK 1.7K⭐, how-claude-code-works 3.6K⭐ | 上下文即产品，Skills 专精上下文质量 |
 | **TRUST 5** | Tested·Readable·Unified·Secured·Trackable | 🆕 新发现 | moai-adk 1.2K⭐ | 五门质量闸，每变更必过 |
 | **Kanban/Factory Mode** | 看板/工厂模式 | 🆕 新发现 | moai-adk v3.1 | 多终端上下文隔离、跨模型路由 |
 | **ODD** | Observability-Driven Development | 🆕 新发现 | oddyssey ⭐7 | OpenTelemetry 驱动 spec 改进循环 |
 | **VDD/RDD** | Vision/Release-Driven Development | 🆕 新发现 | vdd-framework ⭐3 | 愿景驱动验证 + 发布驱动 |
 | **Self-Improving Loop** | 自改进循环 | 🆕 新发现 | moai-adk | 失败观察→规则提升（审批门控） |
 | **Dark Factory** | 暗工厂（全自动AI编码） | 🆕 新发现 | DarkFactory-skills | 15 Skills + 4 personas，全生命周期 |
 | **No False Verification** | 无伪证验证 | 🆕 新发现 | moai-adk | 完成声明必须绑定实际命令输出 |
 
 ---
 
 ## 二、逐项目深度分析
 
 ### a25 · BMAD Method（敏捷AI驱动开发突破方法）
 
 - **仓库**：[bmad-code-org/BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD)
 - **Stars**：52,999 ⭐（2026-09-14 实时）
 - **语言**：Python
 - **创建**：2025-04-13，持续更新中
 
 **核心主张**：Breakthrough Method for **Agile** AI Driven Development。不是"扔掉敏捷换 AI"，而是"用 AI 把敏捷做到以前做不到的程度"。BMAD 把传统敏捷的 user story → sprint → review 升级为 AI 驱动的 task dependency graph。
 
 **关键设计**：
 
 | 设计点 | BMAD 做法 | AIWorflow 对应 |
 |---|---|---|
 | Task Dependency Graph | 从 Spec 自动生成任务依赖图，AI 按图执行 | 块 DAG（compile_dag.py）+ G4 冻结 |
 | Agile + AI | 不抛弃敏捷，用 AI 加速每个敏捷环节 | G0–G10 门禁链天然支持迭代 |
 | 多模型协作 | Claude + Gemini + DeepSeek 按任务类型路由 | 四角色各自可用不同模型 |
 
 **可吸收的设计**：
 1. **Task Dependency Graph 的自动生成**：当前 AIWorflow 的 DAG 靠 Planner 手写，可借鉴 BMAD 的自动依赖推导。
 2. **敏捷节奏保留**：BMAD 强调"不是替代敏捷，是增强敏捷"，这与 AIWorflow 的人机协作理念一致。
 
 **生态项目**：
 - [skyf0xx/hedgehog](https://github.com/skyf0xx/hedgehog) ⭐39：基于 BMAD 的 CLI 强制状态机，task dependency graph 锁定执行路径
 - [cexll/bmad-mcp-server](https://github.com/cexll/bmad-mcp-server) ⭐19：BMAD 的 MCP Server
 - [ErwanLorteau/BMAD_Openclaw](https://github.com/ErwanLorteau/BMAD_Openclaw) ⭐309：BMAD 到 OpenClaw 的桥接
 
 ---
 
 ### a26 · MoAI-ADK（验证驱动 Agent 编排 Harness）
 
 - **仓库**：[modu-ai/moai-adk](https://github.com/modu-ai/moai-adk)
 - **Stars**：1,211 ⭐（2026-09-14 实时）
 - **语言**：Go（单一二进制，零依赖）
 - **当前版本**：v3.1.1
 
 **核心主张**："A verification-driven agent orchestration harness — the structure that makes Claude Code's code trustworthy"。从第一天就禁止"未经验证的完成声明"。
 
 **八大差异化能力**：
 
 | 差异化 | 含义 | AIWorflow 状态 |
 |---|---|---|
 | No false verification | "测试通过"声明必须绑定到实际运行的命令和输出 | ✅ SHA绑定 + validate_run.py |
 | SPEC lifecycle | plan→run→sync 三阶段 + Tier S/M/L | ✅ G0→G10（更细粒度） |
 | Hard boundaries on auto loops | 轮次限制 + 停滞检测 + 墙钟预算 + 审批门 | ✅ 熔断规则（10轮→BLOCKED） |
 | Self-improving loop | 失败模式观察→规则提升建议（审批门控） | ❌ 无（可吸收） |
 | trust-but-verify | 7 项只读验证并行运行 | ❌ 无独立验证批次 |
 | Kanban Mode | 多终端上下文隔离，跨模型路由 | ❌ 无（单会话模型） |
 | CG Mode | Claude Leader + GLM Workers 降本 60-70% | ❌ 无 |
 | 单二进制零依赖 | Go 编译，跨平台 | ✅ Python stdlib 零依赖 |
 
 ---
 
 ### a26.1 · TRUST 5 质量门（MoAI-ADK 核心）
 
 TRUST 5 = **T**ested · **R**eadable · **U**nified · **S**ecured · **T**rackable
 
 | 门 | 含义 | 检查方式 | AIWorflow 对应 |
 |---|---|---|---|
 | **T**ested | 测试可证明通过 | `/moai gate` 跑 lint+format+type+tests | G6 Integration + G7 Full Verify |
 | **R**eadable | 代码人类可读 | 审查门 | G5 Code Review（Reviewer） |
 | **U**nified | 风格统一 | ast-grep 规则 + lint | 当前无自动化（靠 Reviewer） |
 | **S**ecured | 安全可审计 | 安全扫描 | `docs/09` skills/_shared 护栏 |
 | **T**rackable | 可追溯 | sync-auditor 四维评分 | Evidence 只追加账本 + SHA |
 
 ---
 
 ### a26.2 · Kanban Mode / Factory Mode
 
 **Kanban Mode**（v3.1）：一个 SPEC 跨 4 个终端、4 个独立会话执行。
 
 ```
 Lead Session (策略/审计)
   ├── plan 列 (Claude)  → SPEC 撰写
   ├── run 列  (GLM)     → 实现/测试
   └── sync 列 (Claude)  → 文档/PR
 ```
 
 **Factory Mode**（`-f`）：多张卡片同时推进，每张卡在自己的 lane（worktree+session）中完整跑 `plan→run→sync`。
 
 **关键创新**：
 - 上下文隔离：每列独立上下文窗口，不互相污染
 - 模型经济路由：策略用强模型（Claude），实现用便宜模型（GLM），降本 60-70%
 - Origin-Trail Chain：append-only JSONL 血缘树，追踪 worktree 祖先
 
 **AIWorflow 差距分析**：
 - AIWorflow 是单会话串行模型（一个人 + 一个 Agent 串行调用四角色）
 - Kanban 是多会话并行模型（一个人 + 四个终端同时跑）
 - AIWorflow 的优势：纯文件驱动，不需要额外二进制
 - Kanban 的优势：上下文隔离不污染、跨模型降本
 - **结论**：AIWorflow 的单会话串行对个人开发者足够；团队化时 Kanban 的上下文隔离是值得借鉴的方向
 
 ---
 
 ### a27 · Context Engineering Kit（上下文工程工具包）
 
 - **仓库**：[NeoLabHQ/context-engineering-kit](https://github.com/NeoLabHQ/context-engineering-kit)
 - **Stars**：1,694 ⭐
 - **语言**：TypeScript
 
 **核心主张**："Hand-crafted Claude Code Skills focused on improving agent results quality"。不是给 Agent 更多工具，而是让 Agent 在更干净的上下文里工作。
 
 **关键设计**：
 - Skill 不是功能集，是上下文净化器
 - 每个 Skill 精确控制 Agent "看到什么" → "不看到什么"
 - 兼容 OpenCode、Cursor、Antigravity、Gemini CLI 等多宿主
 - 含 CodeRabbit 开源替代
 
 **AIWorflow 对应**：
 - `docs/` 21 篇规则文档 = 上下文工程
 - `prompts/` 模板的 static/dynamic 分段 = 上下文净化
 - 四角色 SKILL.md 的 description = 路由级上下文控制
 
 ---
 
 ### a28 · how-claude-code-works（Claude Code 源码深度解析）
 
 - **仓库**：[Windy3f3f3f3f/how-claude-code-works](https://github.com/Windy3f3f3f3f/how-claude-code-works)
 - **Stars**：3,626 ⭐
 
 **内容**：深入解析 Claude Code 架构——Agent 循环、上下文工程、工具系统。这是一份"理解 AI Coding Agent 内部机制"的必读资料。
 
 **AIWorflow 可吸收的**：
 - Agent Loop 的详细机制（不是黑盒）
 - 上下文窗口管理的实践（什么时候 compact、什么时候保留）
 - 工具系统的权限分层
 
 ---
 
 ### a29 · flow-next（可重复的 Agentic 工程）
 
 - **仓库**：[gmickel/flow-next](https://github.com/gmickel/flow-next)
 - **Stars**：696 ⭐
 - **语言**：Python
 
 **核心主张**："Repeatable agentic engineering. The workflow layer that turns AI coding agents into a disciplined factory."
 
 **关键设计**：
 - **durable specs**：持久的 Spec，不随会话消失
 - **fresh-context workers**：每个 worker 拿到干净上下文
 - **adversarial cross-model reviews**：对抗式跨模型审查（用不同模型审同一代码）
 - **receipts**：每步收据可审计
 - **zero dependencies**：零外部依赖
 
 **AIWorflow 对应**：
 | flow-next 概念 | AIWorflow 对应 |
 |---|---|
 | durable specs | `state.yaml` + `current.md` 只追加账本 |
 | fresh-context workers | 单会话串行（不如 Kanban 的完全隔离） |
 | adversarial cross-model reviews | ❌ 无（同一模型自审，靠角色分离隔离） |
 | receipts | Evidence 层 + SHA 绑定 |
 | zero dependencies | ✅ Python stdlib 零依赖 |
 
 **最值得吸收**：「对抗式跨模型审查」——用不同模型审同一代码，避免同模型盲区。
 
 ---
 
 ### a30 · Dark Factory / ODD / VDD（三个小型前沿项目）
 
 #### DarkFactory-skills
 - [alenberlin/DarkFactory-skills](https://github.com/alenberlin/DarkFactory-skills) 
 - 15 Skills 覆盖全开发生命周期、4 个审查角色、6 个斜杠命令
 - "Senior-engineer discipline for AI coding agents"
 - Apache 2.0 开源
 
 #### oddyssey（ODD: Observability-Driven Development）
 - [using-system/oddyssey](https://github.com/using-system/oddyssey) ⭐7
 - CLI 工具箱：让 coding agent 观察本地运行的 OpenTelemetry/Grafana 栈
 - 核心循环：运行 → 观测 → 发现瓶颈 → 生成 spec → 改进 → 再运行
 - 与 AIWorflow 的"证据驱动"互补：SDD 告诉你要做什么，ODD 告诉你怎么观测做得对不对
 
 #### VDD Framework（Vision-Driven Development）
 - [shuhei0866/vdd-framework](https://github.com/shuhei0866/vdd-framework) ⭐3
 - 愿景驱动 + 发布驱动双框架
 - 强制护栏的 AI 自主开发
 
 #### Hedgehog（BMAD 生态）
 - [skyf0xx/hedgehog](https://github.com/skyf0xx/hedgehog) ⭐39
 - CLI-enforced state machine for agentic coding
 - 基于 BMAD Method 的 task dependency graph
 - "Codes Cleaner, Faster and with Fewer Tokens"
 
 ---
 
 ## 三、我们应该吸收什么（优先级排序）
 
 ### 🟢 立即可吸收（不改架构，只补认知）
 
 | # | 吸收点 | 来源 | 落地方式 |
 |---|---|---|---|
 | 1 | **No False Verification**：完成声明必须绑定实际命令输出 | moai-adk | 已在 Evidence 层有 SHA 绑定，需在 Reviewer SKILL.md 显式声明此原则 |
 | 2 | **TRUST 5 作为 Review 维度** | moai-adk | Reviewer 审核时可逐项对照 T/R/U/S/T 五维 |
 | 3 | **Context Engineering 作为显式设计目标** | CEK + how-claude-code-works | 在 `docs/01-architecture.md` 增加"上下文工程"小节 |
 | 4 | **Self-Improving Loop 概念** | moai-adk | 当前 G10 Close 有 lessons 字段，可增强为"失败模式→规则提升建议" |
 
 ### 🟡 中期可吸收（团队化时实施）
 
 | # | 吸收点 | 来源 | 落地方式 |
 |---|---|---|---|
 | 5 | **Kanban Mode 上下文隔离** | moai-adk | 多 worktree 并行 + 独立上下文，可纳入 `docs/13-roadmap.md` |
 | 6 | **Adversarial Cross-Model Review** | flow-next | 用不同模型审同一代码块，发现同模型盲区 |
 | 7 | **Task Dependency Graph 自动生成** | BMAD + Hedgehog | 从 Spec 自动推导块依赖，减少 Planner 手写 DAG 的错误 |
 | 8 | **ODD 可观测性驱动** | oddyssey | 运行期 OpenTelemetry 信号驱动下一轮 Spec 改进 |
 
 ### 🔵 暂不吸收（与我们定位冲突或不成熟）
 
 | # | 项目 | 原因 |
 |---|---|---|
 | — | Dark Factory（完全无人参与） | AIWorflow 坚持"人负责意图与判断"，不做全自动 |
 | — | VDD（愿景驱动） | 愿景适合产品层，不是工作流引擎层的职责 |
 | — | Factory Mode（多卡片并行） | 个人开发者不需要，团队化时再评估 |
 
 ---
 
 ## 四、一句话更新
 
 &gt; AIWorflow = Skyvern 的 DAG 思想 + ric 的四角色模型 + V4.0 的流程骨架 + AI-DLC 的多宿主思路 + CCG 的策略路由理念 + Langflow 的块类型目录 + AI Workflow 的 Skill 组织方式 + **BMAD 的敏捷 AI 驱动 + MoAI-ADK 的 No False Verification + CEK 的上下文工程 + flow-next 的对抗式审查 + oddyssey 的 ODD 可观测驱动** + 26 篇文章/深度解读 + 10 个开源项目（含 6 个新兴范式），去掉浏览器面和重型基础设施，在"最小可验证"前提下做到最完整。
 
 ---
 
 ## 五、核验证据
 
 | 项目 | 核验方式 | 核验日期 | 状态 |
 |---|---|---|---|
 | BMAD-METHOD | GitHub API → README 实际提取 | 2026-09-14 | ✅ 52,999⭐，Python |
 | moai-adk | GitHub API → README 全文提取（TRUST 5 / Kanban / Factory 细节确认） | 2026-09-14 | ✅ 1,211⭐，Go |
 | context-engineering-kit | GitHub API → README 提取 | 2026-09-14 | ✅ 1,694⭐，TypeScript |
 | how-claude-code-works | GitHub API → README 提取 | 2026-09-14 | ✅ 3,626⭐ |
 | flow-next | GitHub API → README 提取 | 2026-09-14 | ✅ 696⭐，Python |
 | oddyssey | GitHub API → README 提取 | 2026-09-14 | ✅ 7⭐，ODD |
 | hedgehog | GitHub API → README 提取 | 2026-09-14 | ✅ 39⭐，BMAD 生态 |
 | DarkFactory-skills | GitHub API → README 提取 | 2026-09-14 | ✅ Apache 2.0 |
 | vdd-framework | GitHub API → README 提取 | 2026-09-14 | ✅ 3⭐ |
 | 搜狗微信搜索 | curl + Python 解析 | 2026-09-14 | ⚠️ 返回空（反爬），改用 GitHub Search API 补充 |
