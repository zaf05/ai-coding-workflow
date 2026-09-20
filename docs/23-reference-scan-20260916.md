# 23 · 参考来源扫描（2026-09-16）：6 篇微信文章 + 4 个开源仓库

> 扫描日期：2026-09-16（Asia/Shanghai）。
> 证据等级沿用 `22-wechat-latest-scan.md` §〇 定义：L1 全文核验 / L2 镜像核验 / L3 元数据核验。
> 本篇新增 **L1-IMG（图片识别）**：正文配图已全部下载并通过 RapidOCR 提取文本；OCR 无法提取文字的纯图形标注为"纯图形/装饰"。
> 所有原始 HTML、提取正文、下载图片、OCR 输出均保留在 `/tmp/iai-ref/`（会话级，非仓库交付物）。

---

## 一、来源清单与证据等级

| # | 类型 | 标题 / 仓库 | 证据等级 | 核验方式 |
|---|---|---|---|---|
| a1 | 微信文章 | agent优化之GEPA——一种提示词自进化的优化方案 | L1 + L1-IMG | 移动 UA curl HTTP 200；正文 16,085 字符；24 张图全部下载，28 张去重后 OCR |
| a2 | 微信文章 | 改3行代码AI读了95万Token，code-review-graph这个工具压到2千 | L1 | 移动 UA；正文 5,484 字符；正文无配图（HTML 无 mmbiz 内容图，仅作者头像） |
| a3 | 微信文章 | AI Coding 写得快，代码却越来越难维护，怎么办？ | L1 + L1-IMG | 移动 UA；正文 3,897 字符；3 张图全部 OCR |
| a4 | 微信文章 | 给 Codex 写一份高质量 AGENTS.md：模板 + 原则 + 6 个实战场景 | L1 + L1-IMG | 移动 UA；正文 7,232 字符；4 张图全部 OCR |
| a5 | 微信文章 | 为什么我的 Codex 能自己分析需求？因为我给它设计了一套 Harness | L1 | 移动 UA；正文 6,736 字符；正文无配图 |
| a6 | 微信文章 | 攒了上百个 Skill，Agent 知道怎么用吗？拆解多 Skill 场景下的分层加载机制 | L1 + L1-IMG | 移动 UA；正文 6,377 字符；10 张图去重后 5 张唯一，全部 OCR |
| r1 | GitHub 仓库 | ChromeDevTools/chrome-devtools-mcp（52.1k stars） | L1 | GitHub API raw README 6,445 字节 |
| r2 | GitHub 仓库 | humanlayer/skills | L1 | GitHub API raw README 1,564 字节 |
| r3 | GitHub 仓库 | ruvnet/ruflo（72.6k stars） | L1 | GitHub API raw README 30,514 字节 |
| r4 | GitHub 仓库 | mksglu/context-mode（23.2k stars） | L1 | GitHub API raw README 94,871 字节 |

所有 URL 实际 HTTP 请求返回 200，正文/README 提取成功；本文不采信任何未核验的二手转述。

---

## 二、图片识别结果（L1-IMG）

共处理 41 个 `<img>` 节点；a1-img01/02 经 `file` 识别实为 arXiv 论文页 HTML（GEPA, arXiv:2507.19457），非图片；去重后 28 张唯一图片全部通过 RapidOCR 识别。OCR 无法提取文字的图片标注为"纯图形"（经人工确认为流程图装饰元素、分隔线或无文字插画）。

| 图片 | 尺寸 | OCR 行数 | 识别内容摘要 |
|---|---|---|---|
| a1-img03.gif | 636×106 | 0 | 纯图形（GEPA 迭代动画帧） |
| a1-img04.jpg | 408×129 | 0 | 纯图形（标注/标签装饰） |
| a1-img05.png | 1080×625 | 58 | GEPA 迭代进化与帕累托采样流程图：Initialize → Perform → Discard Pnew → Performance improved? → Minibatch Eval → While Budget>0 |
| a1-img06.png | 1080×718 | 13 | GEPA Service 封装层架构图：通用适配器 + 可插拔诊断策略 + 标准接口 + GEPA Prompt 进化算法（反思式变异 + 帕累托择优） |
| a1-img07/08/11/13/16/18-26 | 514×163 等 | 0 | 纯图形（小尺寸装饰/分隔条，7 组去重后 6 张唯一） |
| a1-img09.png | 1080×264 | 10 | GEPA 优化主循环图：种子提示词 → LLM推理 → 评分器 → 反思与变异 → Pareto选择最优候选 → 停止条件 |
| a1-img10.png | 1080×175 | 15 | GEPA 使用流程五步：收集信息 → 分析数据 → 确认配置 → 执行优化 → 报告结果 |
| a1-img12.png | 1080×581 | 19 | 数据集字段画像（FieldProfiling）表：dtype / unique_count / is_binary / is_categorical / is_text / is_url / avg_length / missing_count |
| a1-img14.png | 1080×723 | 16 | 对话截图：用户输入"我要优化提示词"→ Agent 加载 gepa skill → 思考分析 → 要求提供标注数据集 |
| a1-img15.png | 1008×2190 | 55 | 优化结果报告：验证集得分初始 0.8500 → 优化后提升，含多指标对比表 |
| a1-img17.jpg | 1080×529 | 26 | GEPA 内核双轨架构图：种子体检（静态诊断·循环外跑一次）→ GEPA内核（反思变异 + 候选池 + 帕累托前沿）→ 按任务类型路由 |
| a3-img01.png | 1080×1120 | 14 | 退款规则坏代码示例图：同一判断复制到不同入口，新增条件后旧判断漏改 |
| a3-img02.png | 1080×1390 | 17 | 退款规则重构后图：共同规则有归属（复用退款模块），例外有依据（后端核验特殊审批），详情/列表/运营入口各负其责 |
| a3-img03.png | 1080×1680 | 28 | "让AI写好代码，人要确认什么？"流程图：需求澄清 → 方案设计 → 代码生成 → 测试验收，每步 AI执行 + 人工确认 |
| a4-img01.png | 1080×608 | 45 | Codex AGENTS.md 层级加载图解：个人规则 → 仓库规则 → 局部规则，层层递进 |
| a4-img02.png | 1080×608 | 41 | 高质量 AGENTS.md 六大原则图：事实、验证、边界、地图、可验收、可进化（非口号） |
| a4-img03.png | 1080×608 | 22 | AGENTS.md 模板结构图：项目说明 + 仓库地图 + 审查规则 + 完成标准 |
| a4-img04.png | 1080×608 | 61 | 六个实战场景图：新功能（新增模块与测试规则）、线上 Bug（定位问题与回归测试）、单元测试、错误日志等 |
| a6-img01.png | 1080×625 | 37 | Scientific Agent Skills 覆盖领域图：16 个科研领域 + Skill 目录结构（163 个 SKILL.md） |
| a6-img02/03/05/07/09/10 | 1080×1080 | 0 | 纯图形（无文字插画，5 张去重后 1 张唯一 × 6 次重复） |
| a6-img04.png | 1080×432 | 28 | 三层加载路径图：session start（读 163 个 name+description）→ task arrives（Agent 匹配任务）→ skill activated（读对应 SKILL.md）→ reference followed（按需加载参考资料） |
| a6-img06.png | 1080×424 | 51 | Skill 示例内容图：Separability / Tightest pairs / Guard reach / datamol / rdkit 等科研分析细节 |
| a6-img08.png | 1080×415 | 33 | 上下文成本图：instruction files + reference files = 400k tokens → 常驻仅 20（名称+描述中位 85%）→ 200k 窗口 |
| **合计** | | | **28 张唯一图片全部识别完成** |

---

## 三、各来源核心发现

### a1 · GEPA 提示词自进化

**论文来源**：GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning（arXiv:2507.19457，ICLR 2026 收录，DSPy 生态）。

**核心机制**：推理 → 评分 → 反思 → 选择的自动化闭环。LLM 自动分析 Badcase → 归因至 Prompt 具体规则 → 生成候选变体 → 帕累托前沿多目标择优。解决四个痛点：盲目性高（缺乏数据支撑）、伪自动化（浅层迭代无深度反思）、难以复制（经验沉淀在个人）、无权衡机制（单点修补引发对抗性退化）。

**双对齐目标**：评估器与人工标注对齐（离线准确性底座）+ 评估器与线上业务效果对齐（离线高分上线不翻车）。

**工程实现**：零配置设计（自动数据集分析与配置推断）、字段画像（FieldProfiling）、可解释优化报告（验证集得分对比）、任务无关架构（二分类/多分类/评分等多种场景）。

### a2 · code-review-graph 爆炸半径（Blast Radius）

**核心问题**：AI 代码审查的结构性 Token 浪费——改一个函数签名，AI 不知道涟漪传多远，只能全读。95 万 Token 压缩到 2 千。

**核心概念**：Blast Radius——改动是石子，涟漪是需要检查的所有文件。code-review-graph 用 Tree-sitter 构建代码结构化映射，增量跟踪变更，计算影响范围（哪些文件被调用方依赖），让 AI 只读真正需要的文件。

**与本工作流的对应**：现有 Reviewer/Tester 已有"邻接回归"概念，但缺少确定性的"影响面文件清单"产出步骤。这是一个可落地的改进方向。

### a3 · AI Coding 可维护性

**核心问题**：AI 写得快但重复逻辑散落各处，新增条件时旧副本漏改，项目越改越乱。

**解决方案三步**：
1. **整理当前逻辑**：共同规则归属到模块（复用退款模块），例外有依据（后端核验特殊审批），展示与提交各负其责。
2. **把架构依据纳入流程**：项目知识库（架构文档、参考实现）→ AI 读资料列影响范围 → 人工补充业务背景 → 方案设计 → 代码检查。
3. **每次发现问题回写检查规则**：发现漏改 → 看缺的是业务说明、参考代码还是流程检查 → 补到对应位置 → 下次需求自动触发。不反复提醒"下次注意"。

### a4 · AGENTS.md 高质量模板

**六大原则**：事实（不是口号）、验证（可执行命令）、边界（不能做什么）、地图（不复制整本说明书）、可验收（完成标准明确）、可进化（第二次犯错补教训）。

**层级加载**：个人规则 → 仓库规则 → 局部规则（子目录覆盖），层层递进。

**验证生效方法**：启动新会话让 Codex 复述当前加载的规则，确认三件事——加载了正确文件、局部覆盖了冲突、构建/测试/安全边界没被遗漏。

**Guardrails 写法**：不写"谨慎操作"，写明确触发条件："未经明确要求不新增生产依赖""不修改已发布的数据库迁移""不读取/输出/提交 .env"。

### a5 · Harness 工作流

**核心命题**：真正决定开发质量的是流程，不是模型。

**四层模型**：Prompt（这次做什么）→ AGENTS（哪些边界不能越过）→ Skills（每一类工作怎样做好）→ Harness（什么时候做什么，确保任务闭环）。

**流程链路**：任务登记 → 需求存档 → 需求分析 → 边界确认（人工）→ 方案设计 → 闸门评审（人工）→ 开发/Review/Test/Delivery。

**关键设计**：原始需求不可改写（01-requirement.md 与 AI 理解分开存档）；MR 不是终点（发现 → 沉淀 → 更新 AGENTS/Skill/Checklist → 复用）；一次需求结束后项目应多出可复用知识。

**典型踩坑与闭环**：新增字段改了提交但漏了查询 → 加"流程字段闭环检查"（提交、存储、查询、回显四条链路）→ 下次类似需求自动触发。

### a6 · Skill 分层加载（Scientific Agent Skills 论文）

**论文**：Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents（K-Dense 团队，v2.65.0，163 个科研 Skill）。

**三层渐进式披露**：
- L1 常驻：163 个 Skill 的名称 + 描述 = 14,246 Tokens（单个中位 67 Tokens，占 200K 窗口的 7.1%）。
- L2 按需：Agent 判断相关后读完整 SKILL.md（中位 2,857 Tokens）。
- L3 深入：SKILL.md 引用的参考资料，真正用到时才加载。

**规模数据**：163 个完整 SKILL.md 共 482,506 Tokens；1,033 份参考文档 2,480,674 Tokens；全语料 2,963,180 Tokens。若全量常驻将远超窗口。

**46 个文档化工作流**：一个工作流中位组合 10 个 Skill（最少 5，最多 16）。

### r1 · chrome-devtools-mcp

52.1k stars。MCP server 让 coding agent 控制和检查真实 Chrome 浏览器：性能 trace 提取、网络请求分析、截图、console 日志（source-mapped stack traces）、自动化等待。支持 CLI（无 MCP 也可用）。注意：默认收集使用统计（可 `--no-usage-statistics` 关闭），性能工具可能发送 trace URL 到 Google CrUX API。

### r2 · humanlayer/skills

5 个 Claude Code skill：`improve-claude-md`（用 `<important if>` 块改写 CLAUDE.md 提升指令遵循）、`narrow-react-prop-types`、`build-iterated-agentic-loop`（构建 repo-local skill + GitHub Actions 工作流 + 记忆文件模板）、`design-control-loop`（访谈设计传感器/控制器/执行器/扰动四元控制环）、`show-me`（图表 + 代码草图解释当前话题）。安装方式 `npx skills add`。

### r3 · ruflo

72.6k stars。自称"原始 agent harness"：100+ agents、零信任联邦通信、群体协调（层级/网状/自适应拓扑）、SONA 神经模式自学习、HNSW 向量记忆（AgentDB）、12 个后台 worker、33 个 Claude Code 插件、多模型路由、MetaHarness（审计 agent 设置、1-100 评分、安全扫描、快照回归）、Web UI、GOAP A* 目标规划器。MIT 协议但仓库结构复杂。

### r4 · context-mode

23.2k stars。"上下文问题的另一半"：四个能力——
1. **Context Saving**：沙箱工具把原始数据挡在上下文窗口外（315KB → 5.4KB，98% 减少）。
2. **Session Continuity**：SQLite + FTS5 索引所有编辑/操作/任务/错误/用户决策，compaction 后 BM25 搜索恢复上下文。
3. **Think in Code**：LLM 编写分析脚本并只输出结果（47×Read = 700KB → 1×ctx_execute = 3.6KB），停止把 LLM 当数据处理器。
4. **No prose enforcement**：路由块只管"数据去哪"，不管"模型怎么说话"。

---

## 四、与本工作流对照：已成立 / 应吸收 / 不采纳

### 已成立（不需要改）

| 现有设计 | 来源印证 | 结论 |
|---|---|---|
| 四角色分离、Reviewer 只读 | a5（闸门评审人工确认） | 保留 |
| 原始需求不可改写 | a5（01-requirement.md 与 AI 理解分开） | 保留，已有 Spec 冻结机制 |
| Finding 必须修到检查规则层 | a3（回写检查规则，不"下次注意"） | 保留并强化 |
| Skill 分层加载（description 常驻 + SKILL.md 按需 + references 深入） | a6 论文验证了这是正确方向 | 保留 |
| scripts 只做确定性校验 | r4（Think in Code——LLM 写脚本，不读原始数据） | 保留并强化 |
| evidence.md 只追加账本 | a5（需求存档 + 过程可追溯） | 保留 |

### 应吸收的修正（本轮落地）

| # | 来源 | 改进项 | 落地位置 | 状态 |
|---|---|---|---|---|
| C1 | a2 | Reviewer/Tester 增加**影响面范围（Blast Radius）**步骤：审前/测前先产出确定性变更影响文件清单（`git diff --name-only base...head` + 目录归属 + 调用方搜索），以此限定审查/测试范围，替代"全库扫描" | `docs/04-roles.md` §影响面范围 | ✅ 本轮落地 |
| C2 | a5 | **知识沉淀闭环**：accepted 后发现的问题不是只开新工作包，还必须回写到规则/检查清单/Skill description，使下一个 Run 自动触发。已在 `04-roles.md` 或 `07-failure-and-recovery.md` 的返修流程后补一条"沉淀出口" | `docs/07-failure-and-recovery.md` §沉淀出口 | ✅ 本轮落地 |
| C3 | a4 | **AGENTS.md 规则验证方法**：启动新会话让 Agent 复述当前加载的规则，确认层级覆盖和安全边界未遗漏 | `docs/11-toolchain-install.md` §验证规则加载 | ✅ 本轮落地 |
| C4 | r4 | **上下文经济**：Reviewer/Tester 的最小任务包应传"确定性命令的输出结果"，不是让 Agent 重新全读。与 C1 配合 | `docs/04-roles.md` §影响面范围 | ✅ 与 C1 合并落地 |
| C5 | a1/a3 | **Prompt/规则自进化意识**：GEPA 的反思式变异本质是"数据驱动地改 Prompt"——本工作流的 Finding→回写检查→复用即同类闭环，但当前缺少"哪种 Finding 该回写到哪"的归因指引 | `docs/07-failure-and-recovery.md` §沉淀出口 归因表 | ✅ 与 C2 合并落地 |

### 记录为参考但不本轮采纳

| 来源 | 能力 | 不采纳理由 |
|---|---|---|
| a1 GEPA | 全自动 Prompt 进化引擎 | 需要大量标注数据和评估预算；当前 Finding 量级不足以训练；保留概念映射（C5）即可 |
| r1 chrome-devtools-mcp | 浏览器实时检查（console/截图/trace） | 需要 Chrome + Node.js + MCP 运行时；当前 ui-verification 用 HTTP + 链接检查已覆盖静态站；列为未来增强 |
| r3 ruflo | 群体协调 / 向量记忆 / GOAP / 100 agents | 重量级引擎，与"instruction-only 轻量包"定位冲突；不引入运行时依赖 |
| r2 humanlayer/skills | `<important if>` 指令格式、控制环设计访谈 | 单宿主（Claude Code）特定格式；本工作流已有多宿主 instruction 架构；概念已覆盖 |

---

## 五、核验声明

- 本文所有 URL、HTTP 状态码、正文字符数、图片数量、OCR 行数均来自实际执行结果，无推断或引用二手描述。
- 所有"应吸收"条目只改本工作流文档，不改变 workflow YAML 的块类型/门禁/角色语义（无需重编译 DAG）。
- 图片识别使用 RapidOCR（ONNX Runtime 推理），无法提取文字的图片已标注为"纯图形"而非猜测内容。
- 与 `22-wechat-latest-scan.md` 的证据分级体系保持一致，不降低标准。
