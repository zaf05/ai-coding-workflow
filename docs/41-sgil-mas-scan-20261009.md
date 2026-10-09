# 41 · SGIL/MaS 提案收编与转述批判定（2026-10-09）

触发：用户转述「近一月（9 月中～10 月初）新趋势」汇总（含 SGIL/MaS、Skills 化、self-verify、Deterministic Build、JetBrains AI review、Always-on agent、华为/阿里动作与 XDD 范式谱系），**转述内容一律不作 L1 证据**。本批纪律与 docs/34 一致：可检索定位原文的先取证再收录；无法定位原文的记入 §三未收录清单，不入附录、不引用其正文观点。

## 一、来源与取证

| # | URL | 作者 / 站点 | 标题 | 日期 | 取证 |
|---|---|---|---|---|---|
| 154 | https://sumnerevans.com/posts/software-engineering/sgil | Sumner Evans（个人博客，页面自标 "Written by Human, Not by AI"） | How I Want to Use AI | 2026-09-25（`article:published_time` 2026-09-25T06:25-06:00；`modified` 2026-10-08） | webReader L1 全文直读（2026-10-09；curl 本环境出口超时 HTTP 000 如实记录，以 webReader 无截断全文为准） |

原文要点（逐条可溯至全文）：

- 核心诊断：「chat-based AI workflow 的根本问题是**事实源碎片化**」（The fundamental problem with chat-based AI workflows is having a fragmented source of truth）——人的决策散落在几十个会话里无法审计。
- 提案 MaS（Markdown as Source）：**人类手写的 Markdown 文件进版本库，作为软件功能的唯一事实源**；承接 Carson Gross《Markdown in /src》（"Markdown is becoming source code"）。
- 工作流 SGIL = Specify → Generate → Inspect → Loop（读作 "skill"），核心类比「LLM 当编译器」六行对照表：输入 Markdown 规格 / 规格矛盾不完整→报 generation errors / 生成中不许中途问人 / 生成期假设作 warnings 暴露 / 不编辑生成物、改 Markdown 再生 / （maybe?）审 Markdown 不审代码。
- 审查立场原文自 hedge：作者本人**目前不审 .md 而审代码**，该条带 "(maybe?)"；预计短期内仍会审代码，但「the days of this are numbered」（代码审查的日子屈指可数）。
- Inspect 明确要求「a separate agent adversarially testing what the generation agent created」（独立对抗式验证 agent）。
- 落地建议（作者自标 very speculative）：Generate 只喂规格不带实现上下文、歧义即抛错；增量编译类比（局部 spec 变更不全量再生）；存量代码逆向 spec 化（spec agents→generate→inspector 比对）；聊天 harness 如 REPL 保留用于实验。

## 二、去重台账（用户要求：转述批先与库内去重）

| 转述项 | 处置 |
|---|---|
| 阿里云栖《AI Native 研发范式实践手册》（10-08 发布） | **附录 137 已在库**（2026-09-29 收编，68 页 PDF L1 视觉转写，docs/39）；网页版可读早于发布会日期，不重复收录 |
| Skills 化（Claude Code / Codex Skills 成为主流落地方式） | 已有 042/066/089/114/136 等多条 + 本体系自身即 Skills 形态，印证不新增 |
| Always-on 常驻 agent（OpenClaw / Devin 等） | automations 心跳层缺口已在案（docs/13，v1.9.0 `prompts/wakeup.md` 已完成首次真实触发 RUN-20260925-002）；OpenClaw 生态样本见附录 050 |
| 多智能体并行标准配置（Claude Code + Cursor + CLAUDE.md + git worktree） | 134（worktree 实战）/ 095（worktrunk）/ a04·047（AGENTS.md 约束）已覆盖，印证不新增 |
| 自我验证 self-verify / 多模型互检 | a03（Verification Agent 才是 Gate）/ 026（MoAI No False Verification）/ v1.8.21 跨宿主交叉复核同族，方向一致记录不立项 |
| XDD 范式谱系（SDD/EDD/TDD/BDD/DDD/Context/RDD/PDD） | SDD=spec-kit 049/060/061、TDD-as-gate=G4、DDD=069、Context=a31、RDD=a04；对本体系的定位（SDD+Agentic+TDD 组合体）与 README 自述一致 |

## 三、无 URL 未收录清单（转述级信号，不入附录）

知乎《AI 编程开发范式深度研究（2026）》（「压缩单位验证成本」提法的出处）、JetBrains《Framework for Reviewing AI-Generated Code》（2026-10）、OpenSquilla、小米 MiMo Code 多模型互检、Deterministic Build Protocol（Verified-by-Design）、华为全联接「Agentic 开发新范式」（2026-09）、CSDN《2026年AI编程分水岭》、腾讯云开发者《2026年开源AI编程工具爆发》、《Always-On AI Coding Agents 2026》、《2026年顶级开发者的真实AI编程工作流》——均未附 URL，按 docs/34 纪律不入附录；其中的判断性结论（如「压缩单位验证成本」）仅在 §四 作为转述视角引用并标注非 L1。待用户提供 URL 或后续检索命中原文再议。

## 四、对照判定（154 → 本工作流）

同构（正面印证，5 条）：

| SGIL / MaS 原文 | 本工作流对应 |
|---|---|
| 计划/规格文件 = 唯一事实源，聊天不是 | `docs/plan` 计划正文 + `state.yaml`；a19/a20/GoPS「版本化工件是唯一事实源，聊天不是」 |
| 根本问题 = 事实源碎片化 | 附录 146 小红书「transcript≠运行状态」同族；state.yaml 唯一状态源 |
| Inspect = 独立对抗式 agent | Reviewer/Tester 只读独立 + a03 Verification Agent + 029 flow-next 对抗式跨模型审查 + v1.8.21 跨宿主交叉复核 |
| 歧义抛 generation errors、不猜不中途问人 | G2 六问框架任一未明确→Spec 不通过；`AIW_UNKNOWN_FLAG` / `AIW_INERT_CONDITIONAL` 显式 FAIL 家族；决策前置 G3 人工门 |
| 聊天 harness = REPL，源文件才是程序 | 「文件化状态」主张同向；wakeup/ledger/state 全部落盘不依赖会话 |

边界（明确不采纳当前形态，2 条）：

- **Generate 只喂规格、不带实现上下文（绿地全量再生）**：本体系面向存量工程（G1 Recon 读现状、上下文工程路线 a31），全量再生的爆炸半径与 token 成本不可接受（作者自认 token expensive、靠增量编译类比缓解——而工作包级最小 diff 交付正是该类比的既有形态）。
- **「审 Markdown 不审代码」**：安全/权限/破坏性必须看代码 diff（`review_preflight.py` 扫的就是 diff）；作者本人 hedge "(maybe?)" 且自认短期仍审代码——记录为远期视角，当前不采纳。

强化信号（记录在案，不立项，2 条）：

- 生成期假设作为显式 warnings 产物——与 G2 完成判定、test-plan「UNKNOWN≠PASS」同族，Implementer 报告的 assumptions 字段视角。
- 存量代码逆向 spec 化（spec agents → generate → inspector 比对）——docs/25 存量接管的远期参照。

判定：**全景参照 + 5 同构 + 2 边界 + 2 强化信号，零真缺口立项，零规则变更**。与 docs/40 批结论同向：又一家独立来源（本次为个人作者）走到与本体系相同的设计位置。

## 五、计数

附录 153→**154**；规则文档 41→**42** 篇（实测修正历史口径：编号 00–41 连续共 42 篇 + docs/README，此前历批误以最高编号当篇数，恒少 1）；selftest 维持 129；大厂覆盖维持 19 家（154 为个人作者，不新增公司）。零代码零脚本变更。

验证：`grep -oE '<tr><td>[0-9]{3}</td>' ../aiworflow-full-flow.html | wc -l` → 154。
