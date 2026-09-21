# 35 · 2026-09-21 微信文章收编（Loop Engineering，淘天集团）

> **目的**：登记用户指定评估的微信文章《Loop engineering：把 agent 放进工程循环》（苏雄，淘天集团-会员技术团队）的对照结论，并把本批来源 125–130 编入附录索引。
> **触发指令**：用户「AI工作流，今天这个微信文章对我们有用吗，有用的话，必须进行参考，并附录上」。
> **版本锚点**：v1.8.11。结论先行：**有用，必须收**——五个组件独立印证既有设计，一个组件（automations 心跳层）是本工作流真实缺口，登记 `docs/13`；文章引用的一手源两条可达补录、三条转引落档。

## 〇 · 方法与证据边界

- **主文 L1**：webReader 于 2026-09-21 全文直抓（无截断），作者署名「苏雄，淘天集团-会员技术团队」取自文末作者栏。页面发布日期元数据抓取为空，**不臆造日期**，附录行日期列按惯例记收录日 2026-09-21。
- **转引一手源实测**（curl 桌面 UA，2026-09-21）：Addy Osmani 原文 HTTP 200（199,027 B，标题命中）；Martin Fowler 原文 HTTP 200（40,733 B，标题命中）——两者为**可达性+标题级 L3**（正文未读，观点经 125 转述，不得直接引用其原文观点）；Amplitude 文章页两次尝试未取到（000 超时 / 仅博客通用标题）；arXiv 两篇出口连接失败（000）。L3 纪律沿用 `docs/33` §三：**转引条目不得引用原文观点，仅生态样本/线索记录**；A/B 判定要求全文可指认，本批转引条目一律 C/R/N。
- 证据分级定义见 `docs/22` §〇（L1 全文 / L2 同文镜像 / L3 仅元数据）。

## 一 · 文章主张概要（原文观点，L1 直读）

- **命题**：与其每轮给 agent 写更长的 prompt，不如把「读状态→判断→执行→验证→写状态→停止条件」的循环工程化——loop engineering 是 prompt engineering 的接棒者。
- **六组件**：automations（定时唤醒的心跳层）、worktrees（每循环独立分支隔离）、skills（项目知识外置为可版本化资产）、plugins/connectors（能力面）、sub-agents（maker/checker 分权）、memory（loop 状态外置，state 文件由循环自己写）。
- **guides vs sensors**（引 Martin Fowler）：harness 工程的判据是「有没有在收集证据」，不是「有没有指导文档」。
- **automations 的定位**：「automation 是心跳不是大脑」——按节奏唤醒循环；唤醒 prompt 应是**操作规程**：前馈（本轮约束、预算、先读状态文件）+ 反馈（传感器清单：看哪些文件/命令输出来判断成败）。
- **六条失败模式**：① 脚本不是循环（无状态，每次从零）；② 验证被 agent 自己吞掉；③ 状态写了没人读（下一轮 prompt 必须先读状态）；④ 长循环上下文腐化；⑤ 循环会过期（产品演进后旧循环失效）；⑥ 权限错配（运行时拒绝循环要做的动作）。
- **loop 化判据（六条）**：输入充分 / 失败模式已知 / 任务自带测试 / 循环收敛 / 失败不灾难性 /（作者个人补充第 6 条）**循环产出可积累复用**——每次运行让下一次更聪明。
- **引用源**：Addy Osmani《Loop Engineering》为本文章主源；Martin Fowler harness engineering；Amplitude Ralph loop 实验（ sweeping logs，名字出自 Calvin and Hobbes）；arXiv 2605.10907（AI Workflow Store：循环需要 store 而非现场拼装）；arXiv 2606.13662（EurekAgent：E=mc² 经验-记忆-缓存框架）。

## 二 · 六组件逐条对照（独立印证面）

| 文章组件 | 本工作流对应 | 覆盖 | 证据位置 |
|---|---|---|---|
| automations（定时唤醒心跳层） | **无**——`run_flow --advance` 由会话内 Agent 驱动，无 cron/宿主调度触发层 | ❌ **真缺口** | 登记 `docs/13` 未实现表（见 §三） |
| worktrees（循环隔离） | 主仓 `AGENTS.md` §11 `/.worktree/<work-package>/` + wango-delivery 协议 | ✅ 工程层已有 | 主仓交付协议 |
| skills（知识外置） | `skills/aiworflow-*` 5 入口 + 双宿主实机加载 | ✅ | README 实现状态表 |
| plugins/connectors（能力面） | `scripts/` 16 个确定性校验器 + 宿主 MCP；本包有意不自建插件运行时 | ✅ 等价物 | `docs/01`、`docs/08` |
| sub-agents（maker/checker） | 四角色所有权分离 + Reviewer 只读 + `review_preflight` 确定性前置 | ✅ 且更深（门禁链 G0–G10） | `docs/04`、`docs/03` |
| memory（loop 状态外置） | `state.yaml`/`current.md`/`evidence.md` 只追加账本 + `ledger` + `checkpoint.yaml` + `context/` | ✅ 且更深（恢复链 v1.8.5/08） | `docs/05`、`docs/30` |

**六动作循环同构性**：文章「读状态→判断→执行→验证→写状态→停止条件」与 `--advance` 的读 state→frontier 判定→执行 check→验证→写 state+ledger→DONE/WAIT_USER/WAIT_ROLE/BLOCKED 终止信号一一对应——**独立来源对我们核心执行模型的印证**。

**六条失败模式对照**：①我们不是无状态脚本（state+ledger）；②证据纪律+`review_preflight`+UNKNOWN≠PASS；③`task_resume` 先消费 checkpoint/state/ledger（v1.8.8）；④证据外置不依赖对话记忆；⑤rule-lifecycle Add/Thin+模型换代复检（v1.8.1）；⑥star:user 不可代签+权限分层。**六条全部有既有答案**，无新增失败模式。

## 三 · 真缺口：触发/心跳层（automations）

- **缺口描述**：循环本体（`--advance`）与循环驱动（谁来唤醒下一轮）在本工作流中是同一宿主会话。无人值守的节奏化唤醒（定时任务/宿主 automations/webhook 触发 `task_resume` 链路）不存在。
- **登记落点**：`docs/13-roadmap.md` 未实现表新增一行（本批同步写入）。
- **触发条件**（不现在实现，符合「出现真实案例再写代码」纪律）：① 出现首个「无人值守自动跟进」真实需求（如夜间跑 check_all 后自动处置停滞 run）；② 宿主原生调度可用（Codex automations / Claude Code 定时任务）。
- **形态约束**：先做 **prompt 模板**（文章的操作规程结构：前馈约束+反馈传感器+先读状态文件，见 §四①），不做守护进程——守住 instruction-only 与 0 新增依赖边界。

## 四 · 记录在案的候选做法（不写代码，触发时落地）

1. **自动化唤醒 prompt 模板**：前馈（本轮目标/预算/必须先读 `state.yaml`+最近 ledger）+ 反馈（传感器清单：check_all 退出码、validate_run 结果、陈旧 run 名单）——登记为 `prompts/` 候选，与 §三触发条件绑定。
2. **loop 化六条件判据**（含第 6 条「产出可积累」）：作为 G0 Intake 判断「这事值不值得立 run/工作流」的检查问题**记录于本篇**，不改动 G0 契约正文（避免为一条参考扩契约；后续若 G0 改版再合并）。
3. **维护环（harness maintenance loop）**：文章建议每周读 agent PR 反哺护栏——认定与 G10「任务后能力观察」（v1.8.1）同族；2026-09-21 RUN-20260921-001 事故→处方固化（docs/05/07 新增节）即该环的真实实例，**不新建流程**。

## 五 · 附录增补 125–130 逐条归属判定

判定口径同 `docs/33` §〇（A 吸收+护栏化 / B 吸收为规则 / C 印证 / R 记录未吸收 / N 明确不采纳）。L3 转引条目不得为 A/B。

| 编号 | 来源（短名） | 判定 | 质量 | 证据级 | 一句话依据 |
|---|---|---|---|---|---|
| 125 | 淘天·苏雄《Loop engineering》 | C | Q1 | **L1**（webReader 全文） | 六组件五条印证 + 心跳层缺口登记 docs/13 + 三条候选做法记录（§四）；六动作循环与 `--advance` 同构 |
| 126 | Addy Osmani《Loop Engineering》 | C | Q1 | L3（200+标题，正文未读） | 125 的主源；原始英文出处，读全文时升级 L1 |
| 127 | Martin Fowler《Harness engineering for coding agent users》 | C | Q1 | L3（200+标题，正文未读） | 原始出处补录；中文衍生 a18 与 hongtao 镜像（核验表 row 13/33）已双 L1 在库 |
| 128 | Amplitude《Sweeping Logs》(Ralph loop) | R | Q2 | L3 转引（文章页未取到） | Ralph loop 实验线索；心跳层实施时再读 |
| 129 | arXiv 2605.10907（AI Workflow Store） | R | Q2 | L3 转引（出口 000） | 「循环需要 store」印证 workflows/ 版本化方向；未读不引用观点 |
| 130 | arXiv 2606.13662（EurekAgent） | R | Q3 | L3 转引（出口 000） | E=mc² 经验-记忆-缓存框架线索；生态样本 |

## 六 · 一句话总评

> 这篇文章对本工作流的价值是「**五个 yes 一个 no**」：worktrees/skills/connectors/sub-agents/memory 五组件从独立中文一线实践者得到印证，六动作循环与 `--advance` 信号模型同构，六条失败模式全部有既有答案；唯一的 no——automations 心跳层——是真实缺口，已按纪律登记 roadmap 并绑定触发条件，不为参考文章预先写代码。附录 124→130。
