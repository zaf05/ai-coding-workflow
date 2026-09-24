# docs/ · 规则与设计

本目录是 AIWorflow 的规则权威来源。`skills/` 只保留角色入口与执行摘要，具体规则在此维护，不复制正文。

| 文档 | 内容 | 什么时候读 |
|---|---|---|
| `00-overview.md` | 全流程 13 段、`*` 边界、V4.0 → v1.0 的变化 | 第一次使用；对外讲解 |
| `01-architecture.md` | Flow / Role / Evidence 三层模型与数据流 | 设计新工作流前 |
| `02-block-catalog.md` | 块类型目录（21 种）、字段语义、角色与门禁绑定 | 写 `workflows/*.yaml` 时 |
| `03-gates.md` | G0–G10 门禁、适用性省略、Verdict 与严重度 | 判断"能不能过" |
| `04-roles.md` | 四角色所有权矩阵、单层调度、交接身份 | 分派任务、跨角色协作 |
| `05-state-and-evidence.md` | Run 容器、状态机、账本、产物生命周期 | 建 Run、写证据、恢复中断 |
| `06-parameters-and-prompts.md` | 参数系统、保留字、秘密处理、Prompt 模板规范 | 写参数化工作流与 Prompt |
| `07-failure-and-recovery.md` | 失败分类、错误码白名单、重试与自愈、finally、bug intake、熔断 | 出错、返修、被用户报 bug |
| `08-determinism-and-caching.md` | agent ↔ script 渐进确定性、run_signature、条件块不缓存 | 流程跑顺后想固化提速 |
| `09-authoring-copilot.md` | 自然语言 → 工作流的授权、评审门禁与 guardrail | 让 AI 自动编工作流 |
| `10-wango-adapter.md` | 与 WanGo `AGENTS.md` / 交付协议的适配、冲突与优先级 | 在 WanGoPlatform 内工作 |
| `11-toolchain-install.md` | Codex / Claude Code / ZCode / 通用 `.agents` 安装与发现 | 换宿主、装 Skill |
| `12-reference-scan.md` | 三个参考工程（skyvern / ric-dev / jakubkrehel-skills §E）的全面扫描报告（路径 + 行号 + 事实） | 追问"这条规则从哪来" |
| `13-roadmap.md` | 未实现能力与演进顺序 | 决定下一步做什么 |
| `14-current-practices.md` | 2025–2026 主流实践对齐、权威来源与应吸收修正 | 判断工作流是否不过时、下一步改哪里 |
| `15-execution-model.md` | 模型/参数选择矩阵、smoke 测试基线与实机命令 | 选择模型、跑冒烟、验证 Codex 加载 |
| `16-legacy-and-dag-driving.md` | DAG 自动拆分是否 Claude Code 独有、DAG 模型能力、存量/原型工程驱动 | 追问 DAG 与存量工程方案时 |
| `17-execution-evidence-20260908.md` | 2026-09-08 真实实施证据、可复现命令与注意事项 | 复现/审计当天实施过程时 |
| `18-dag-pipeline.md` | 候选 DAG 全链路：LLM 意图 → `compile_dag.py` 编译 → G4 冻结 → `run_flow.py` 推进 | 用 DAG 自动拆分/编译/冻结/执行时 |
| `21-emerging-paradigms.md` | 2026 前沿 AI 编程范式全景扫描（BMAD 53K⭐/MoAI-ADK TRUST 5+Kanban/CEK/flow-next 对抗式审查/oddyssey ODD 等 12 个新兴范式） | 了解 2026 前沿范式、判断吸收优先级 |
| `20-external-workflow-projects.md` | 外部 AI 工作流开源项目扫描（AWS AI-DLC / Langflow / CCG / AI Workflow）：4 项目深度分析、可吸收设计、七工程对比 | 了解行业主流编排/分发工具 |
| `19-ring-system-human-in-loop.md` | 环系统与人机协作：吸收黄迅「AI Coding深水区」+ GoPS「Agent进生产」——机器提供事实/人做判断、判据下沉、环间接口标准化 | 设计人机协作边界、理解「常」与「流」 |
| `22-wechat-latest-scan.md` | 微信/镜像最新文章扫描与**证据分级（L1 全文 / L2 同文镜像 / L3 仅元数据，§〇 定义）**：hongtao2agent 4 篇 L1（Claude 5 上下文工程、DSH 五层插件、Agentic SRE、Pi Compaction）、a35 蚂蚁数科 Harness L1 全文 8,259 字符、a36 阿里 AACR-Bench L1 全文 8,430 字符（移动 UA 取 SSR 正文）；搜狗微信 2026-09 扫描 55 篇候选（L3）；a04「反爬」误判修正（真因 URL 截断）；镜像采信双条件铁律 | 了解 2026 微信/镜像最新 AI 编程方法论；核验外部来源时先读本篇的分级与陷阱表 |
| `23-reference-scan-20260916.md` | 2026-09-16 参考来源扫描：6 篇微信文章 + 4 个开源仓库（GEPA/Blast Radius/AGENTS.md/Harness/Skill 分层加载/chrome-devtools-mcp/humanlayer-skills/ruflo/context-mode），含 L1-IMG 图片识别与 5 条落地改进 | 追问新参考来源、图片识别结果或改进依据时 |
| `24-reference-scan-20260917.md` | 2026-09-17 参考来源扫描：13 篇微信文章（AGENTS.md语言纪律/Matt Pocock 19 skills/货拉拉组织落地/AAIC技术方案/自进化全景/Worktree并行/code-review-graph/Compound Engineering/Bug分析Skill/Debug Skill/Archify/多Agent实战），126 图 OCR + 3 条落地改进 | 追问新一轮参考来源或改进依据时 |
| `25-large-task-protocol.md` | 大型任务拆分与跨 Run 交接协议：拆分阈值、纵向切片、context/ 交接载体、G1 增量扫描、G10 交接检查清单、效率度量 timestamps | 需要拆分大型任务或需要跨 Run 继承上下文时 |
| `26-reference-scan-20260918.md` | 15 篇微信参考扫描 | 追问 2026-09-18 批次参考来源或改进依据时 |
| `27-gap-analysis-20260918.md` | 对标 GitHub 高星项目 + Anthropic + 国内大厂，33 项能力矩阵（18已有/4部分/11缺失），P0=长时运行 P1=代码图谱+成本追踪 | 判断能力缺口与优先级时 |
| `28-bigtech-coverage-20260918.md` | 补扫 13 家大厂：美团31万行L1 + 字节DeerFlow82K⭐ + OpenAI Codex125K⭐ + Anthropic×4篇L1；4家L3元数据、2家反爬不可达 | 追问大厂覆盖面与 L1 证据时 |
| `29-enhancement-roadmap.md` | 5 项缺失能力实施方案：F1 长时运行 / F2 AST 图谱 / F3 成本追踪 / F4 向量检索 / F5 评估基准，总计 11h，不破坏 0 依赖 | 决定 F1–F5 实施顺序时 |
| `30-multi-day-task-protocol.md` | 2-3 天长周期任务协议：task.yaml 跨天状态 + 多会话编排 + 结构化交接 + 自动恢复 | 执行 2–3 天长周期任务时 |
| `31-runtime-enforcement-plan-20260920.md` | 运行期强制执行与回收方案（2026-09-20 实测缺口）：P0 transition 写入时校验 / P1 DAG 语义一致性 / P2 超时回收+check_all / P3 版本控制与卫生修复；含新会话启动指令。**P0/P1/P2 于 v1.8.0、P3 于 v1.8.2 实施；P3 本地仓库部分于 v1.8.3 按用户决定撤销，闸门 v3 回归主仓** | 追问运行期强制执行设计与实施状态时 |
| `32-harness-article-scan-20260920.md` | 腾讯云《删掉80%的Prompt规则》L1 全文对照扫描：三支柱与三层模型同构、与 v1.8.0 P0 互证；缺口 2 条已于 v1.8.1 落地（rule-lifecycle 删减四信号 + G10 能力观察） | 追问附录 086 对照扫描时 |
| `33-appendix-full-review-20260920.md` | 86 条附录来源全量复盘：逐簇归属判定（吸收+护栏化 / 吸收为规则 / 印证 / 记录未吸收+理由 / 明确不采纳）+ 来源质量分级（Q1–Q4，低信息密度 11 条的处置纪律）+ 框架完善度结论与诚实缺口清单 | 追问「框架是否完善、来源是否都消化了、附录有没有低质量文档」时 |
| `34-web-scan-20260920.md` | 2026-09-20 全网检索扫描（两轮）：GitHub 周榜 2026-09-14~20 webReader 直抓 15 仓 + 12 组主题检索 + 6+4 反趴复盘；附录 087–124（38 条，L3 快照级为主并强制「生态样本/非规则依据」标注）逐条归属判定；012/025/046/066 证据更新；排除清单与无 URL 未收录项 | 追问当天全网爬到内容的收录去向、周榜数据或检索批归属判定时 |
| `35-wechat-loop-engineering-20260921.md` | 2026-09-21 微信《Loop engineering》（淘天·苏雄）对照收编：六组件对照（五条印证既有设计 + automations 心跳层真缺口登记 docs/13）、六动作循环与 `--advance` 信号模型同构、六条失败模式全有既有答案、三条候选做法记录在案；附录 125–130 逐条归属判定与证据分级（L1/L3 转引纪律） | 追问该文对本工作流的价值、心跳层缺口的触发条件或 125–130 收录去向时 |
| `36-wechat-ai-native-paradigm-20260924.md` | 2026-09-24 微信《AI Native 研发范式升级》（晴晚·淘天海外技术）对照收编：九条主张印证既有设计（调度权归流程引擎与 `--advance` 正面同构、Spec 冻结、人决策卡点、客观门禁+风险分级、留痕/交叉评审、自检前置、数据回流、度量转向端到端），零真缺口；两条度量口径候选（AI 初稿采纳率 ≥80% 判定口径、阶段耗时/返工 ledger 原料成指标）挂 docs/13 evals；数字员工概念佐证心跳层缺口登记；附录 131 L1 直读 | 追问该文对本工作流的价值、AI 初稿采纳率口径或 131 收录去向时 |

## 阅读顺序

- 只想用起来：`00-overview.md` → `workflows/README.md` → `skills/aiworflow/SKILL.md`。
- 想改造流程：`01-architecture.md` → `02-block-catalog.md` → `03-gates.md` → `05-state-and-evidence.md`。
- 想在 WanGoPlatform 里用：先读 `10-wango-adapter.md`，它定义冲突时谁赢。

## 文档规则

- 文件名固定 `NN-topic.md`，`NN` 是阅读顺序，不是重要性。
- 每篇文档必须区分**当前事实**与**目标设计**；未实现的能力显式标注"未实现"，不得用现在时态描述。
- 规则只在唯一位置维护；其他文档链接过去，不复制正文。
- 修改规则时同步检查 `skills/`、`workflows/`、`scripts/` 是否出现漂移，并跑 `python3 ../scripts/validate_package.py`。

## 来源总数

截至 2026-09-24，全系统共收录 **131 个唯一外部来源**（唯一编号以 HTML 附录 001–131 为准；README 附录 a01–a37 是 001–086 中 37 条的子集视图，各批扫描文档另保留批次编号 a/b/E）：

| 批次 | 数量 | 编号 | 扫描/核验文档 |
|---|---|---|---|
| 核心方法论（微信文章） | 20 | 001–020 | docs/12–19、README a01–a20（2026-09-14 全量核验） |
| 开源项目（GitHub） | 10 | 021–030 | docs/20、docs/21（GitHub API 实值核验） |
| hongtao 深度×4 + 蚂蚁数科 + 阿里评审 | 6 | 031–036 | docs/22（均 L1 全文） |
| docs/23 批次（2026-09-16） | 10 | 037–046 | docs/23 |
| docs/24 批次（2026-09-17） | 13 | 047–059 | docs/24 |
| docs/26 批次（2026-09-18） | 15 | 060–074 | docs/26 |
| docs/28 大厂补扫（2026-09-18） | 11 | 075–085 | docs/28 |
| docs/32 批次（2026-09-20） | 1 | 086 | docs/32（L1，核验表 row 65） |
| docs/34 全网检索批（2026-09-20） | 38 | 087–124 | docs/34（周榜直抓 L1×11 + 检索快照 L3×27，核验表 row 66–103） |
| docs/35 Loop Engineering 批（2026-09-21） | 6 | 125–130 | docs/35（125 L1 webReader + 126/127 curl 200 可达补录 + 128–130 转引 L3，核验表 row 104–109） |
| docs/36 AI Native 范式批（2026-09-24） | 1 | 131 | docs/36（131 淘天海外 L1 webReader，核验表 row 110） |
| **合计** | **131** | 001–131 | 001–086 归属复盘见 `33-appendix-full-review-20260920.md`；087–124 见 `34-web-scan-20260920.md` §八；125–130 见 `35-wechat-loop-engineering-20260921.md` §五；131 见 `36-wechat-ai-native-paradigm-20260924.md` §四 |

验证命令：`grep -oE '<tr><td>[0-9]{3}</td>' aiworflow-full-flow.html | wc -l` → 131（与 HTML 附录计数一致；逐条归属判定 docs/33 + docs/34 + docs/35 + docs/36）

