# 14 · 2025–2026 主流实践对齐报告

本篇回答"这套工作流是否紧贴时间线、是否还专业"。来源分两类：

- **已克隆并扫描**：`references/skyvern`、`references/ric-dev-workflow-skills`，见 `12-reference-scan.md`。
- **网页调研**：2026-09-08 当日检索并打开官方/一手页面；URL 与日期在表格中记录。GitHub 对 `github/spec-kit` 的 clone 本次失败（`Failed to connect to github.com port 443`），所以没有进入 `references/`，只记录官方文档事实与搜索快照；不得把该仓库当成本地已扫描仓库。

> 结论先给：现有三层模型（Flow / Role / Evidence）与 2025–2026 主流方向同向，不需要推倒重来；需要吸收的是四件事——Spec-Kit 的"阶段产物门"、OpenAI 的"skill description 即路由逻辑 + script 即微型 CLI + 大声失败"、Anthropic 的"进展文件 + 测试 oracle + 每步 commit"、Addy Osmani 的"人始终验证/评审，测试当安全网"。下面逐条列事实与映射。

## 一、权威来源与关键事实

| # | 来源 | 日期 | URL | 关键结论 | 与本工作流关系 |
|---|---|---|---|---|---|
| 1 | GitHub Spec Kit 官方文档 | 2026-08-21 更新 | https://github.github.com/spec-kit/ | SDD 默认主链：Spec → Plan → Tasks → Implement；每阶段产出 Markdown artifact 喂给下一阶段；38 个 agent 集成；用 building blocks 定制流程 | 直接印证 `intake → recon → spec → approve → plan → implement → check → review → integrate → test` 的"先 spec 后 code"主链 |
| 2 | GitHub spec-kit `docs/reference/agentic-sdd.md` | 2026-08-10 | https://github.com/github/spec-kit/blob/197dde62/docs/reference/agentic-sdd.md?plain=1#1 | 命令主链：`constitution → specify → clarify → plan → checklist → tasks → analyze → implement → converge` | 可对标现有门禁 G0–G10；`constitution` 近似 WanGo `AGENTS.md` 的规则吸收；`tasks` 近似块 DAG；`analyze` 近似 Reviewer |
| 3 | OpenAI Developers：Shell + Skills + Compaction | 2026-02-10 | https://developers.openai.com/blog/skills-shell-tips （⚠️ 本环境 403 区域封锁，2026-09-14 以 4 种 UA 复测均不可达，见 README 核验表 row 63；下表四条论点改由可达中文二手来源支撑：虎嗅《OpenAI 也来教你怎么写 Skills》 https://www.huxiu.com/article/4834939.html ，curl HTTP 200 / 99,991 B / 2026-02-13，逐条覆盖 description 路由写法、Glean 负面例子触发率降 20%、模板近乎免费） | 1) skill description 写成路由逻辑，不是营销文案；2) 把确定性部分放进 script，当作微型 CLI；3) 脚本 stdout 可解析、失败要大声报错；4) 长任务要 compaction 与可恢复上下文 | 现有 `skills/aiworflow` description 就是路由；`scripts/` 已经只做确定性静态校验；需要把"脚本失败大声报错"写得更明确 |
| 4 | Addy Osmani：My LLM coding workflow going into 2026 | 2026-01-04 | https://addyosmani.com/blog/ai-coding-workflow/ | specs before code；小步迭代；提供充分上下文；选强模型并可换模型；真人验证、测试、评审；测试是 safety net | 与现有四角色、最小任务包、Reviewer 独立审核、Tester 安全网一致；补充"可换模型"作为工程策略而非流程规则 |
| 5 | Anthropic：Long-running Claude for scientific computing | 2026-03-23 | https://www.anthropic.com/research/long-running-Claude | CLAUDE.md 承载整体计划；CHANGELOG.md 作为可移植长期记忆（记录失败路径）；测试 oracle；git 每步 commit；Ralph loop 防"假完成" | 现有 `state.yaml + current.md + evidence.md` 已是进展文件；需要把"失败尝试必须记录，避免下个会话重试同一死路"提升为硬规则 |
| 6 | Anthropic：Claude Code Advanced Patterns webinar | 2026-03-24 | https://www.anthropic.com/webinars/claude-code-advanced-patterns | subagents + hooks 编排；MCP 连接内部工具；大仓库 CLAUDE.md 结构；CI 里自动化 PR review/test | 现有单层调度、四角色、Reviewer 只读与子代理触发一致；补充：不把内部实现细节当证据 |
| 7 | Kiro（AWS SDD IDE/agent）公开信息 | 2026 公开 | 搜索索引：https://github.com/vasilyu1983/AI-Agents-public/blob/main/frameworks/shared-skills/skills/docs-ai-prd/references/spec-driven-dev-landscape.md | Kiro 强制 spec-first pipeline，spec 文件入仓库；企业落地 SDD | 印证 SDD 是企业方向；本工作流仍保留 WanGo 交付协议优先，不引入 IDE 锁定 |
| 8 | GitHub Spec Kit 生态快照 | 2026-08-21 | https://github.github.com/spec-kit/ | 130K+ stars、38 integrations、157 extensions、33 presets；支持 AIDE/Canon/MAQA 等非 SDD 流程 | 说明 Spec Kit 是"意图驱动 harness"而非唯一答案；本工作流选择本地文件 + instruction-only，避免重型引擎 |

## 二、与现有设计对照：哪些已成立

### 已成立的判断（不需要改）

| 现有设计 | 2025–2026 主流印证 | 结论 |
|---|---|---|
| 先 Spec 后 Plan 再实现 | Spec Kit 主链、Addy Osmani、Kiro 均一致 | 保留 |
| Planner 唯一写状态、Reviewer 只读 | Anthropic subagent 编排、Claude Code 独立 reviewer | 保留 |
| 小任务包、单块实现 | Addy Osmani 小步迭代、Anthropic 长任务拆解 | 保留 |
| Tester 独立验证、测试为安全网 | Addy Osmani、Anthropic test oracle | 保留 |
| 证据文件 + SHA 绑定 | Anthropic CHANGELOG、每步 commit | 保留并强化 |
| 人工边界 `*` 不得代签 | Addy Osmani 人始终验证；企业治理需要 | 保留 |
| 无重型运行时，instruction-only | Spec Kit 也可 step-by-step；本地文件足够 | 保留 |
| scripts 只做静态校验、不下语义结论 | OpenAI scripts 只放确定性逻辑 | 保留 |

### 应吸收的修正（小改，不推倒）

1. **Skill description 明确按路由逻辑写**。现有四个角色 description 已接近路由，但要在 `skills/README.md` 和 `docs/04-roles.md` 明确：description 的目标是让宿主把请求分给唯一正确角色，不写营销词，不写"多面手"。

2. **脚本边界补一条"大声失败"**。`scripts/` 只做确定性校验；但任何脚本在输入非法、校验失败、环境缺失时必须非零退出并给出可解析错误，不得静默通过。改 `scripts/README.md`。

3. **失败尝试必须入账**。现有 `current.md` 要固定字段记录失败路径；同一死路跨会话不得重试。改 `docs/05-state-and-evidence.md` 或在 `docs/14` 标注，并在 `templates/run-state.yaml` 中确认已有字段；若无，下一步补模板。

4. **不把"可换模型"写成流程规则**。模型选择是执行策略，记录在 run 环境/交付报告，不进入 YAML 状态机，避免把工具能力混成门禁。

5. **Spec-Kit 可作第二参考，但不复制其 engine**。官方主链与现有 13 段重叠度高；应借鉴其"阶段产物是下一阶段唯一输入"的硬门，而不是引入 `speckit` CLI 或命令目录。

## 三、当前事实与未验证（必须区分）

| 项目 | 状态 | 证据 |
|---|---|---|
| 两个指定参考工程 clone + 扫描 | 已完成 | `references/skyvern` commit `35cb497c99dc940472023e682692613e1014e51f`；`references/ric-dev-workflow-skills` commit `84954fbda3c1d8c47ef2a5ee9fb43e18ab4a3c4a`；索引见 `12-reference-scan.md` |
| 第三方 `github/spec-kit` 本地 clone | 未完成 | 2026-09-08 尝试 `git clone --depth 1 https://github.com/github/spec-kit.git` 失败：`Failed to connect to github.com port 443 after 136915 ms`；官方文档经网页可读 |
| 本文网页调研 | 已完成（可复现） | 上表 URL，检索日期 2026-09-08 |
| 上述修正是否落地 | 部分待办 | 第 1、2、3 项是本次补充；模板字段是否已存在需跑 `scripts/selftest.sh` 与 `validate_package.py` 确认 |
| 真实 run / 宿主实机加载 | 已完成多个真实 run + 双宿主实测 | 历史 `RUN-20260908-002`（Codex Reviewer `verdict=APPROVE`，磁盘已不存在）；现行可验证 run 见 `runs/`（`RUN-20260920-003` `validate_run.py` PASS；`RUN-20260921-001` 首个真实任务驱动 + G3 用户亲签 + 评审-only 合法收尾，validate_run PASS / `--advance` DONE）；2026-09-20 Codex exec 与 Claude Code 嵌套会话双宿主只读探针均实测发现/实读 skill |
| Claude Code / ZCode 宿主实机加载、Flow 引擎 | 未验证/未实现 | 见 `13-roadmap.md` |

## 四、下一步（按优先级）

1. 把"失败尝试入账"固定到 `current.md` / `docs/05-state-and-evidence.md`，必要时补模板字段。
2. 重跑 `python3 scripts/validate_package.py` 与 `bash scripts/selftest.sh` 取证。
3. 等网络可用时补 clone `github/spec-kit`，把命令/模板/agents 结构写入 `12-reference-scan.md` 或新增 `16-spec-kit-scan.md`。
4. 下一个真实 run 优先验证 feature-delivery 的 Planner→Implementer→Reviewer→Tester 完整链路，验证"阶段产物门"是否真的减少上下文浪费。

## 五、2026-09-16 补充来源（详细分析见 `23-reference-scan-20260916.md`）

| # | 来源 | 日期 | URL | 核心发现 | 与本工作流的关系 |
|---|---|---|---|---|---|
| 9 | GEPA (arXiv:2507.19457) | 2026-09 | 微信 a1 | 反思式 Prompt 进化 + 帕累托择优；解决人工调 Prompt 盲目性 | 概念映射到 Finding→回写规则闭环（C2/C5） |
| 10 | code-review-graph | 2026-09 | 微信 a2 | Blast Radius：确定性变更影响面文件清单，替代全库扫描 | 吸收为 Reviewer/Tester 影响面范围（C1/C4） |
| 11 | 老A AI Coding 工程化 #17 | 2026-09 | 微信 a3 | 重复逻辑归属模块；发现问题回写检查规则 | 印证 C2 沉淀出口 |
| 12 | AGENTS.md 模板 | 2026-09 | 微信 a4 | 事实/验证/边界/地图/可验收/可进化；验证加载方法 | 吸收为规则加载验证（C3） |
| 13 | Codex Harness 实战 #05 | 2026-09 | 微信 a5 | 四层模型（Prompt→AGENTS→Skills→Harness）；MR 不是终点 | 印证现有架构 + C2 沉淀闭环 |
| 14 | Scientific Agent Skills 论文 | 2026-09 | 微信 a6 | 三层渐进式披露（L1 常驻/L2 SKILL.md/L3 references） | 印证现有 Skill 分层加载 |
| 15 | chrome-devtools-mcp | 持续 | GitHub r1 | MCP 浏览器检查（console/截图/trace） | 未来增强，需运行时前置 |
| 16 | humanlayer/skills | 持续 | GitHub r2 | 5 个 Claude Code skill；`<important if>` 指令格式 | 参考不采纳（单宿主特定） |
| 17 | ruflo | 持续 | GitHub r3 | 100+ agents / 群体协调 / 向量记忆 / GOAP | 不采纳（重量级，与轻量 instruction-only 冲突） |
| 18 | context-mode | 持续 | GitHub r4 | 沙箱工具挡原始数据 / FTS5 会话恢复 / Think in Code | 印证 scripts 确定性边界 + C4 上下文经济 |

## 六、2026-09-17 补充来源（详细分析见 `24-reference-scan-20260917.md`）

| # | 来源 | 核心发现 | 与本工作流的关系 |
|---|---|---|---|
| 19 | AGENTS.md 语言纪律（腾讯技术） | 禁废话句式/黑话/单字缩写；一步到位 | 印证现有 AGENTS.md 规则 |
| 20 | Matt Pocock 19 skills（155K⭐） | grill→to-spec→to-tickets→implement→review | 印证 G0→G10 骨架 |
| 21 | 货拉拉 AI Coding 组织落地 | AiBox 统一工作台 + SDD 五步 + Spec 自反馈 + 全生命周期闭环 | 吸收 D1 Spec 质量反馈 + D3 G10 资产沉淀 |
| 22 | AliExpress AAIC 技术方案 | /explore /propose /apply /test 四命令 | 印证块DAG分阶段等价 |
| 23 | Agent 自进化全景 | Skill/Memory/Prompt/Workflow 非参 + RL 参数进化 | 理论参考，当前无预算实施 |
| 24 | Matt Pocock 96 分钟工作坊 | 上下文越长越笨；窄窗口深工作；Sandcastle 编排 | 印证最小任务包 + 单块实现 |
| 25 | Worktree + Submodule 多仓 Git | 多需求并行用 Worktree 隔离；Submodule 锁版本 | 印证 WanGo worktree 协议 |
| 26 | code-review-graph（21K⭐） | Blast Radius 82x token 缩减 | C1 已落地 |
| 27 | Compound Engineering | PLAN→EXECUTE→VERIFY；小改进复合 | 印证现有 G2→G5→G6/G7 |
| 28 | Bug 分析 Skill | 八步：输入→校验→清洗→特征→模型→规则→风险→报告 | 与 D2 调试六步互补 |
| 29 | Debugging Skill | Reproduce→Isolate→Reduce→Fix→Guard→Verify | 吸收 D2 调试六步 |
| 30 | Archify（19.5K⭐） | 从代码生成可验证架构图 | 未来增强，当前不需要 |
| 31 | Codex 多 Agent 实战 | 职责隔离：实现/审查/测试各司其职 | 印证四角色分离 |
