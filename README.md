# AIWorflow · 我的 AI 工作流

版本：v1.8.11（单一事实源 `VERSION`） · `schema_version: 1` · 更新日期：2026-09-21

这是属于我自己的 AI 原生研发工作流系统（当前 v1.8.11，130 个外部参考来源，覆盖 13 家一二线大厂：国内 9——阿里/腾讯/字节/美团/快手/华为/京东/网易有道/货拉拉，国际 4——OpenAI/Anthropic/AWS/Google）。它把一次“让 AI 干活”的请求，升级成一条**可编排（块 DAG）、可分权（四角色）、可验证（门禁 + 证据）、可自动推进（loop_control 信号驱动循环）、可接管（状态与账本）**的交付链路。当前状态：v1.8.10，selftest **70/70 PASS**（站点在线时；离线 69/69 + 1 SKIP），validate_package **全部通过**。近期演进：v1.8.5 修复长周期恢复链三个真 bug；v1.8.6 统一 `--advance` 报告契约并让账本写失败可观测；v1.8.7 落地会话归因与 Reviewer 确定性前置检查；v1.8.8 让 `task_resume` 消费 checkpoint/state/ledger、声明 run 内串行治理边界、补人类摘要与模型替换复检；v1.8.9 收口独立检查的 4 条 P3（REVIEW_SIZE 口径统一 / secret 告警不回显密钥 / PROTECTED_PATHS 边界说明 / 依赖措辞统一补申报），并把当日全网检索批（087–124，`docs/34`）全部编入 HTML 附录索引；v1.8.10 用首个真实任务驱动的 G3 人工门评审 run（RUN-20260921-001：六功能域只读评审、用户亲签接受、评审-only 合法收尾）沉淀三条运行规则——侦察 fan-out 启动清单、评审-only Run 收尾处方、star 块亲签出处落位；v1.8.11 收编淘天《Loop engineering》对照批（`docs/35`，附录 124→130）：五组件印证既有设计、automations 心跳层登记为缺口（docs/13）、三条候选做法记录在案。诚实边界：真实 ≥3 块的 L3 断点演练仍未执行，当前只能声明恢复组件可用且有自检，不能声明跨会话实战闭环。

## 血缘与来源

| 来源 | 我取走了什么 | 位置 |
|---|---|---|
| 我原有的 `AI Native Dev Pipeline V4.0 · schema 18` | 13 段主流程、contracts 概念、`*` 人工/授权/外部平台边界标记、bug intake 分类、completion claim 枚举 | `references/ai-native-dev-pipeline-v4-full-flow.html`（内嵌 Markdown 原文可下载） |
| [Skyvern-AI/skyvern](https://github.com/Skyvern-AI/skyvern) | 工作流即**块 DAG**（label / next_block_label / output_parameter / continue_on_failure / finally_block / error_code_mapping）、参数系统、run 状态生命周期、Copilot 的 completion_contract 与 review gate、author-time guardrail、agent→script 渐进缓存、Prompt 模板 static/dynamic 拆分、Skill 包（SKILL.md + references + examples）与 diff 驱动 QA | `references/skyvern/`（commit `35cb497`） |
| [lichong-a/ric-dev-workflow-skills](https://github.com/lichong-a/ric-dev-workflow-skills) | 四角色职责分离与所有权矩阵、G0–G10 门禁、Verdict 三值与 P0–P3 严重度、Compact 四文件证据容器、变更控制与 Git 策略、多宿主（Codex/Claude/ZCode）薄配置、instruction-only 原则 | `references/ric-dev-workflow-skills/`（commit `84954fb`） |
| [驾驭AI Coding：面向团队的Harness Engineering落地规范](https://mp.weixin.qq.com/s/g4nTfxm7ebzRwkAVIGdIbg) | 六支柱框架（上下文/工具/编排/记忆/评估/护栏）、3+1 Phase 落地路线、团队 Rules 与 AGENTS.md 版本化分发、风险分层与审计飞轮、"配置存在 ≠ 行为有效"的生产级缺口 | 本文对照分析见下方 §Harness Engineering 落地规范对照 |
| [模型给能力，Harness 给责任边界｜Agent 进生产（GoPS 会后复盘）](https://hongtao2agent.xyz/html/gops-agent-production-harness/) | 责任状态机（事实→准备→授权→执行→验证→写回）、OPC 闭环、上下文连续性 > 工具特长、护栏分层 Prompt→Skill→Hook→Permission、验证须区分 成功/失败/未知（未知 ≠ 成功）、L4→L5 团队平台（可复用/可评审/可度量/可发布） | 本文对照分析见下方 §GoPS 生产 Harness 对照 |
| WanGo Platform `AGENTS.md` + `docs/develop/agent-delivery-protocol.md` | 工作包状态机、切分门禁口径、integration baseline Git 顺序、熔断与软检查点、证据驱动与"已验证"定义 | `docs/10-wango-adapter.md` 定义适配与冲突规则 |
| [awslabs/aidlc-workflows](https://github.com/awslabs/aidlc-workflows) | 多宿主适配（7宿主：Claude/Codex/Cursor/Kiro/Copilot）、`aidlc` CLI + approval gate + 自动工作流选择、`aidlc doctor` 宿主诊断 | 详细分析见 `docs/20-external-workflow-projects.md` §二-a21；GitHub 核验 4,598⭐ |
| [langflow-ai/langflow](https://github.com/langflow-ai/langflow) | 可视化 Agent 编排思路（节点组件化+拖拽连线）、块类型目录（Agent/Tool/Prompt/Memory/Output 分类） | 详细分析见 `docs/20-external-workflow-projects.md` §二-a22；GitHub 核验 155K⭐ |
| [fengshao1227/ccg-workflow](https://github.com/fengshao1227/ccg-workflow) | 多模型协作策略路由（`/ccg:go` → 意图分析→策略选择→Claude+Codex+Gemini 分派）、策略可配置设计 | 详细分析见 `docs/20-external-workflow-projects.md` §二-a23；GitHub 核验 5,884⭐ |
| [nicepkg/ai-workflow](https://github.com/nicepkg/ai-workflow) | 170+ 预构建 Skill 集合（14+ AI 工具）、多领域分类体系、一键安装体验（`npx ai-workflow install`）、标签词典参考 | 详细分析见 `docs/20-external-workflow-projects.md` §二-a24；GitHub 核验 283⭐ |
| [bmad-code-org/BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD) | 敏捷 AI 驱动开发突破方法：Task Dependency Graph 自动生成、Agile+AI 融合 | 详细分析见 `docs/21-emerging-paradigms.md` §a25；GitHub 核验 52,999⭐ |
| [modu-ai/moai-adk](https://github.com/modu-ai/moai-adk) | 验证驱动 Agent 编排 Harness：TRUST 5 质量门、Kanban/Factory Mode 上下文隔离、No False Verification、Self-Improving Loop | 详细分析见 `docs/21-emerging-paradigms.md` §a26；GitHub 核验 1,211⭐ |
| [NeoLabHQ/context-engineering-kit](https://github.com/NeoLabHQ/context-engineering-kit) | 上下文工程工具包：Skill 即上下文净化器、14+ 宿主兼容 | 详细分析见 `docs/21-emerging-paradigms.md` §a27；GitHub 核验 1,694⭐ |
| [Windy3f3f3f3f/how-claude-code-works](https://github.com/Windy3f3f3f3f/how-claude-code-works) | Claude Code 源码深度解析：Agent Loop 内部机制、上下文工程、工具系统 | 详细分析见 `docs/21-emerging-paradigms.md` §a28；GitHub 核验 3,626⭐ |
| [gmickel/flow-next](https://github.com/gmickel/flow-next) | 可重复 Agentic 工程：durable specs + fresh-context workers + adversarial cross-model reviews + receipts | 详细分析见 `docs/21-emerging-paradigms.md` §a29；GitHub 核验 696⭐ |
| [using-system/oddyssey](https://github.com/using-system/oddyssey) | ODD（Observability-Driven Development）：OpenTelemetry 驱动 spec 改进循环 | 详细分析见 `docs/21-emerging-paradigms.md` §a30；GitHub 核验 7⭐ |

| [Loop engineering：把 agent 放进工程循环](https://mp.weixin.qq.com/s/RxRzTsRvmZJMmtQjQM79_g)（苏雄 · 淘天集团） | Loop 六动作工程化定义（与 `--advance` 信号模型同构）、automations 心跳层缺口识别（登记 docs/13）、自动化唤醒 prompt 前馈/反馈结构、loop 化六条件判据（含「产出可积累」） | 对照分析见 `docs/35-wechat-loop-engineering-20260921.md`（附录 125） |
| [hongtao2agent.xyz](https://hongtao2agent.xyz) 全站 25 篇深度内容 | Claude 5 上下文工程七判断（编译后上下文/减法优先/信息架构分层）、DeepSeek Harness 插件五层原理（装配与作用域分离/插件价值来自收窄）、Agentic SRE 五层架构（动作分级/最小权限/人工Gate/可回滚+全链路审计）、Pi Compaction 长会话恢复 | 详细分析见 `docs/22-wechat-latest-scan.md` §a31–a34；25 篇标题列表已获取 |


参考资产：4 份本地（1 份原始 HTML + 3 个工程 clone：skyvern / ric-dev-workflow-skills / jakubkrehel-skills）在 `references/` 下，另 10 个 GitHub 开源项目通过 GitHub API 核验提取：原 4 个（AWS AI-DLC / Langflow / CCG / AI Workflow）见 `docs/20-external-workflow-projects.md`，新增 6 个（BMAD 53K⭐/ MoAI-ADK / CEK / how-claude-code-works / flow-next / oddyssey）见 `docs/21-emerging-paradigms.md`，微信+镜像最新文章扫描见 `docs/22-wechat-latest-scan.md`（a31–a34 hongtao 深度解读 L1，a35 蚂蚁数科 Harness 工程实践 L1 全文 8,259 字符，a36 阿里 AI 代码评审/AACR-Bench L1 全文 8,430 字符；另附搜狗微信 2026-09 扫描 55 篇候选清单，L3 仅元数据）。均为**只读参考**，不作为本工作流的规则源；扫描结论与证据见 `docs/12-reference-scan.md`。2025–2026 主流实践的网页调研见 `docs/14-current-practices.md`，2026 前沿范式全景扫描见 `docs/21-emerging-paradigms.md`。

## 三层模型（一句话）

```text
Flow 层    workflows/*.workflow.yaml   —— 块 DAG + 自动化推进闭环（run_flow.py --advance + loop_control 信号）
Role 层    skills/aiworflow-*          —— 四角色 + 一个入口路由：所有权分离，Planner 是唯一状态写入者
Evidence 层 runs/<RUN-ID>/             —— state.yaml / current.md / test-plan.md / evidence.md：只追加账本与当前索引
```

- **Flow 决定顺序与边界**，**Role 决定谁能下结论**，**Evidence 决定结论是否成立**。
- 三层都不允许用"我说完成了"替代"证据显示完成了"。

## 目录

```text
.ai_worflow/
├── README.md                  本文件：权威入口
├── docs/                      规则与设计（36 篇 + README）
├── skills/                    可被 Codex / Claude Code / ZCode 发现的 Skill 包
│   ├── aiworflow/             入口与 Flow 引擎语义（不是第五角色）
│   ├── aiworflow-planner/     规划、状态、协调、合并
│   ├── aiworflow-implementer/ 单块实现
│   ├── aiworflow-reviewer/    只读独立结论
│   ├── aiworflow-tester/      测试计划与独立验证
│   └── _shared/               契约、模板、参考（无 SKILL.md）
│       ├── contracts/          四角色共享契约（9 份：角色/门禁/证据/状态/变更/Git/交接/规则生命周期/产物；护栏注册表在 docs/09）
│       ├── templates/          模板（state/current/test-plan/evidence/report/handoff）
│       └── references/         详细参考（各角色最小交接包）
├── workflows/                 可复用工作流定义（块 DAG，YAML）
│   └── _examples/             示例工作流（含条件分支演示）
├── prompts/                   Prompt 模板（static / dynamic 分段）
│   ├── candidate-dag.md       候选 DAG 生成模板（13 条规则）
│   └── examples/              候选 DAG 示例
├── scripts/                   校验器、安装器、DAG 编译器与解释器（Python 3 标准库，无第三方依赖）
├── runs/                      运行期证据容器（本目录自 2026-09-20 起为独立 git 仓库，见 runs/README 入库状态）
└── references/                四个参考资产（V4.0 HTML + 3 工程 clone，只读）
    └── ai-native-dev-pipeline-v4-full-flow.html  V4.0 全流程讲解页（保留原文）
```

## 快速开始

1. 读 `docs/00-overview.md`（全流程）与 `docs/01-architecture.md`（三层模型）。
2. 选一条工作流：`workflows/feature-delivery.workflow.yaml`（功能交付）、`bugfix-triage`（缺陷归因）、`refactor-migration`（重构/迁移）、`ui-verification`（页面验证）。
3. 校验定义是否可执行：

```bash
python3 scripts/validate_workflow.py workflows/feature-delivery.workflow.yaml
python3 scripts/validate_package.py            # Skill 包结构、链接、frontmatter、模板与工作流
python3 scripts/selftest.sh                    # 正例 + 反例全量自检
```

4. 安装到宿主（默认 dry-run，先看清单再落地）：

```bash
python3 scripts/install_skills.py --dry-run
python3 scripts/install_skills.py --target "$HOME/.codex/skills" --mode symlink --apply
python3 scripts/install_skills.py --target "$HOME/.codex/skills" --check      # 校验装的是哪版、有没有被手改
python3 scripts/install_skills.py --target "$HOME/.codex/skills" --upgrade --apply
```

5. 一次真实 run 从 `runs/<RUN-ID>/state.yaml` 开始，模板在 `skills/_shared/templates/`。

### 自动化推进（v1.6.0）

G4 冻结 DAG 后，用自动化推进循环替代手工逐块接力：

```bash
# 单次推进（输出 loop_control 信号）
python3 scripts/run_flow.py workflows/feature-delivery.workflow.yaml runs/<RUN-ID> --advance --execute-check

# Agent 读取 loop_control 信号后自动循环：
#   CONTINUE   → 立即再次 --advance（check 块通过自动继续）
#   DONE       → 全部完成，Planner close
#   WAIT_USER  → 停下请求用户确认 → --mark-done → 继续
#   WAIT_ROLE  → 调对应角色 Skill → --mark-done → 继续
#   BLOCKED    → 停止并归因
```

自动化推进完整语义见 `skills/aiworflow/references/flow-engine.md` §自动化推进闭环，Agent 伪代码见 `docs/18-dag-pipeline.md` §八。

## 执行模型选择（不是"一个参数跑到底"）

低风险 smoke / 快速单角色自检用 `model_reasoning_effort=low` 即可，不是正式工作流标准。理由：低成本模型在简单路径够快，但规划多块、权限/安全/重构等任务中曾出现 schema 漂移；工作流结论不能依赖低成本模型单点证明。注：原推荐的 `qwen3.7-flash` 已于 2026-09-20 实测下线（`codex exec` 报「模型不存在」），smoke 探针改用 `~/.codex/config.toml` 默认模型 + low effort，实测可用。

| 场景 | 建议参数 |
|---|---|
| 快速冒烟、单块 `doc_fix`、单角色 smoke | `config.toml` 默认模型 + `-c model_reasoning_effort=low`（2026-09-20 实测 flash 已下线） |
| 正式功能交付、权限/安全/数据/迁移、多块 Planner→Implementer→Reviewer→Tester | 使用 `~/.codex/config.toml` 默认模型 + `model_reasoning_effort=high`（2026-09-10 实测为 `qifu/qwen3.8-max`；以实测为准） |
| 大模型规划慢或已过预算 | 规划仍用默认模型，单块实现/回归可按任务类型降级；不得让降级模型代签 `APPROVE`/`PASS` |

真实验证命令示例（只调用单一角色，避免入口自动派生 5 个 agent）：

```bash
cd /home/feifz/workspace/WanGoPlatform/.ai_worflow
python3 scripts/validate_package.py
python3 scripts/validate_run.py runs/RUN-20260920-003
timeout 180 codex exec   --ephemeral --skip-git-repo-check   -C /home/feifz/workspace/WanGoPlatform/.ai_worflow   -s danger-full-access   -c model_reasoning_effort=low   -o /tmp/aiworflow-smoke.txt   '你是 aiworflow-reviewer。只读审核 RUN-20260920-003 的 verify_ui 块，输出 review.yaml 到对应 run 目录；不要改 state.yaml。'
```

## 不可妥协的边界

- **人负责意图、授权与产品判断；AI 负责执行、验证、记录与复查。** `*` 标记的节点必须人工确认，不得由模型代签。
- 任何角色不得批准自己产出的结论；Reviewer 对被审对象只读。
- 没有绑定 SHA / 版本 / 命令输出的结论，不得写成 `APPROVE`、`PASS` 或 `accepted`。
- 不使用"主体完成""进入最终章""大概可以了"这类模糊完成声明；完成度由 `completion_contract` 逐条判定。
- 不把 token、密码、Cookie、私钥、真实用户数据或未脱敏日志写进任何工作流定义、Prompt 或证据文件。
- 不覆盖他人未提交修改，不用 `git reset --hard` / `git checkout --` / `git clean` 处理未知改动。
- 自动化循环中同一块 CONTINUE 超过 10 轮 → BLOCKED；同一 WAIT_ROLE 连续 2 次角色失败 → BLOCKED（熔断规则）。
- 在 WanGoPlatform 仓库内工作时，仓库 `AGENTS.md` 与 `agent-delivery-protocol.md` 优先；本工作流只能加严，不能放宽。冲突规则见 `docs/10-wango-adapter.md`。

## 版本管理与分发（v1.2.0 起 → v1.6.0 自动化推进闭环）

### 版本历史

| 版本 | 变更 | 对使用者的影响 |
|---|---|---|
| **v1.8.11** | **微信《Loop engineering》对照收编（docs/35）**：六组件对照——worktrees/skills/connectors/sub-agents/memory 五条印证既有设计，六动作循环（读状态→判断→执行→验证→写状态→停止条件）与 `--advance` 信号模型同构，六条失败模式全部有既有答案；**真缺口「触发/心跳层（automations）」登记 `docs/13`** 并绑定触发条件（首个无人值守自动跟进真实需求 + 宿主原生调度可用；形态先做唤醒 prompt 模板——前馈约束+反馈传感器+先读状态——不做守护进程，守住 instruction-only 与 0 新增依赖边界）；三条候选做法记录在案不写代码（唤醒模板结构、G0 loop 化六条件判据、维护环认定与 G10 任务后能力观察同族——RUN-20260921-001 事故→处方固化即该环实例，不新建流程）；**附录 124→130**：125 淘天原文 L1（webReader 全文）、126 Addy Osmani《Loop Engineering》与 127 Martin Fowler 原文 curl 200 可达补录（L3 可达性级，正文未读观点经 125 转述）、128 Amplitude Ralph loop / 129 arXiv AI Workflow Store / 130 arXiv EurekAgent 转引 L3（出口失败，强制「生态样本/非规则依据」标注）；README 核验表扩至 row 109；修复 HTML 页脚版本残留 v1.8.9；无脚本变更，selftest 维持 70/70 | 该文的价值是「五个 yes 一个 no」：独立中文一线实践者印证既有设计，唯一 no（心跳层）已按纪律登记 roadmap 不预写代码；附录来源 +6 且每条证据级诚实标注 |
| **v1.8.10** | **真实 G3 门评审 run 的规则固化**：首个以真实任务驱动完整走过 Planner 段 + 人工门 + 收尾的 run（RUN-20260921-001：六功能域只读评审，用户会话亲签"我接受"，validate_run PASS、`--advance` DONE）。踩出的三条运行规则沉淀为文档：① `docs/07` 新增**侦察 fan-out 启动清单**——fan-out 前 manifest 落 current.md、按域回收不按份数、重试必须同域原 prompt（实测事故：Soul 探针启动失败被 IAM prompt 顶替重试，4 份报告掩盖 1 域缺失）、分类器不可用时 Planner 直评有界域并显式记录；② `docs/05` 新增**评审-only Run 合法收尾处方**——fix 路径块逐块 skipped+skip_reason、notify/close 可 completed、test-plan.md 写 N/A 记录不伪造、`approvals.<label>` 落亲签出处、终态前 validate_run+DONE 双复核、`--append-ledger '{"note":...}'` 命令形态；③ star:user 块 mark-done 只做簿记不产生批准的边界成文；④ **入库状态适配**（2026-09-20 21:02 用户重新自建本目录 git 仓库 `d551273`、remote `zaf05/ai-coding-workflow`，2026-09-21 确认保留）：`install_hooks.py --apply` 把 pre-commit 闸门装入本仓 `.git/hooks/`（布局 B 生效，与主仓双布局在位，`--check` PASS），`runs/README` 入库状态、`docs/11` 版本历史行、`context/project-aiworkflow` 形态事实按新现实改写并附隐私提示（`runs/`、`context/` 推远端前用户确认可见性）。无脚本变更，selftest 恢复 70/70 | 评审-only 类任务有了可直接照抄的收尾路径，不再现场摸索踩 R-1/缺 test-plan 的 FAIL；多探针评审不会再出现"重复域顶替缺失域"的静默覆盖；人工门签收在 state.yaml 有结构化出处可审计 |
| **v1.8.9** | **P3 收口 + 全网检索批入附录**：① 独立检查 4 条 P3 全部修复——`review_preflight.py` REVIEW_SIZE 消息与阈值统一为 added lines 口径（原消息打印 changed_lines 会误导对照）、secret 告警不再回显命中串前 8 字符（改为仅回显规则类别 sk-key/bearer-token/key-assignment，selftest §7d-quatro 新增「密钥材料不回显」断言）、PROTECTED_PATHS 对主仓同名路径的纵深防御边界说明落 `docs/30` §十二、v1.8.7 实施期未申报的「0 外部依赖→不新增外部依赖（已有 PyYAML）」措辞统一在 `docs/29` 补记声明；② 附录 086→**124**：新增 `docs/34-web-scan-20260920.md`（GitHub 周榜 2026-09-14~20 webReader 直抓 15 仓 + 12 组主题检索两轮 + 6+4 反趴复盘），087–124 共 38 条编入 HTML 附录与核验表 row 66–103（检索快照级 L3 为主，按 `docs/33` §三强制标注「生态样本/非规则依据」）；012/025/046/066 四条既有来源获证据更新（012 本周 +15,028 星居周榜第一）；README/docs/HTML 计数全量同步 | 检查发现的问题当版清零；今天全网爬到的内容全部可溯引入附录索引；secret 告警自身不再泄密 |
| **v1.8.8** | **checkpoint 消费 + 串行边界 + 人类摘要**：① `task_resume.py` 读取 `checkpoint.yaml`、`state.yaml` 块状态与最近 ledger，恢复提示词明确“已 completed 块的 migration/commit/push 零重复执行”；② docs/04 声明 run 内单活跃角色与串行推进是 Planner 唯一写入者治理设计，并行只发生在工作包层；③ Review/Test 报告模板增加 `human_summary`，角色报告增加 `session.model/session.tokens_used`；④ 规则生命周期增加模型升级/替换/供应商切换复检；⑤ 本地 HTML `<title>` 与 README 版本行纳入 `validate_consistency.py`；⑥ selftest §4 从 dry-run 改为 `install_skills.py --check`，防止同版本指纹漂移假 PASS；selftest 69→70 | 恢复提示词从 task.yaml 单一来源升级为 task+checkpoint+state+ledger；L3 真实演练边界仍保留；签核者第一眼可读结论；模型漂移有复检触发 |
| **v1.8.7** | **会话归因 + Reviewer 确定性前置层**：① `run_flow.py --session-meta` 支持 `model`（必填）与 `tokens_used`（非负整数或 `null`），自动写入本轮 ledger 并在 `--advance` 报告回显，非法输入非零退出；② 新增 `review_preflight.py`，对已提交 diff 执行 secret / 禁改区 / 破坏性命令 / 规模四条确定性规则，默认 stdout 保持 Reviewer 只读，FAIL 非零；③ Reviewer SKILL 接线为 CODE_REVIEW / RELEASE_REVIEW 第 0 步，机器 FAIL 直接转 deterministic finding；selftest 66→69 | 能回答“这个 run 由哪个模型执行”；secret、账本禁改区和破坏性命令从人工目测下沉为机器前置检查；token 查不到时诚实写 null，不估算 |
| **v1.8.6** | **run_flow 报告契约统一 + 轮次账本可观测**（触发指令"必须保证 AI 工作流可被 Codex 和 Claude Code 正确使用"）：① `--advance` 的 **TERMINAL 与 CYCLE_DETECTED 两条提前返回路径此前缺 `loop_control` 键**——双宿主会话按惯例解析该键会直接 KeyError（RUN-20260920-003 收口时实际踩中）；两条路径现与正常路径同样输出 `loop_control`（DONE/BLOCKED），"所有 --advance 报告都带 loop_control"成为机器契约，selftest 新增 §7d-bis 断言终结报告；② `_append_round_ledger` 写失败原被 `except: pass` 静默吞掉（轮次日志可能悄悄缺行且无告警），现 stderr 显式 WARN 且不阻断推进（与 v1.8.5 修掉的"假成功"同族，失败必须有名字）；selftest 65→66 | 双宿主（Codex/Claude Code）消费 run_flow 报告的解析契约统一且有断言护栏；轮次日志缺行从静默变为可见告警 |
| **v1.8.5** | **长周期任务恢复链自检覆盖**（触发指令"必须保证可以完成数小时，数天的工作任务"）：selftest 新增 **§13 五项断言**（task-state 模板结构 / checkpoint 落盘 / 恢复提示词完整性 / 负例非零退出 / run 容器兼容），59→65；修复三个真 bug——① `run_flow.py` checkpoint 曾按 `dict.items()` 遍历列表形 blocks，`checkpoint_interval` 一触发即 AttributeError（**该路径此前零测试覆盖，被 §13b fixture 首跑捕获——"文档冒充实现"的典型形态**）；② `task_resume.py` 轻量解析器不支持列表字段，`completed_blocks` 填充即丢失（恢复会话不知道哪些块已完成，会重跑）；③ task.yaml 缺失时假成功退出 0（现退出 2 + ERROR，恢复链不假成功）；修复 selftest **§12 死代码闸门**（曾位于 `exit` 之后恒不执行，"条件执行"实为闸门假象；现 urllib 探测 → 在线跑+计数 / 离线显式 SKIP），本机站点在线实测 65/65；`docs/30` 新增 §九 自检覆盖与诚实边界（Session×Run 级联仍属协议层，首次真实 2-3 天任务是端到端验证点） | 数小时~数天任务的恢复能力从「协议文档 + 未测实现」变为机器断言覆盖；docs/30 的 checkpoint 声明首次为真；离线机器 selftest 语义明确为 64/64 + SKIP，不再依赖闸门假象 |
| **v1.8.4** | 附录收录 **086**（腾讯云《删掉80%的Prompt规则》L1，docs/32 对照扫描，核验表 row 65）；新增 `docs/33-appendix-full-review-20260920.md`：86 条附录来源全量复盘（逐簇判定吸收状态：已吸收且护栏化 / 印证 / 记录未吸收+理由 / 明确不采纳），框架完善度结论与诚实缺口清单；修正 docs/README 来源总数（59→86）与验证命令的陈旧表述；`aiworflow-full-flow.html`（原名 `aiworflow-v1.7-full-flow.html`，本轮更名消除文件名版本歧义；版本事实由页内快照横幅 + 版本演进表 + `VERSION` 承载）加快照状态横幅、补 v1.8.0–v1.8.4 版本演进行、附录 086、计数 85→86；同日二次校准：页内数字全量对齐 v1.8.4（核心数字/七工程对比/资产清单/一句话定位/快速开始/页脚，消除快照数字与增补数字混排），README 参考资产数修正 3→4（jakubkrehel-skills 2026-09-16 入库，docs/12 §E）；页首精简为「我的 AI 工作流」，版本状态说明下沉至「版本演进」节首 | 86 条外部来源每条有归属判定，无「收录未消化」悬空项；框架完善度有据可查（docs/33） |
| **v1.8.3** | 按用户决定**撤销 v1.8.2 的本地 git 仓库**（删除 `.ai_worflow/.git` 与包内 `.gitignore`，本目录整体不入任何版本库，主仓 `.git/info/exclude` 照旧排除）；pre-commit hook **v3 装到主仓** `/WanGoPlatform/.git/hooks/`（旧 v2 自动备份为 `pre-commit.foreign-backup-*`；布局 A 生效，布局 B 代码保留备用） | 本目录恢复纯目录形态，零 git 状态；主仓提交仍受 selftest 阻断级闸门覆盖，`install_hooks.py --check` PASS |
| **v1.8.2** | docs/31 P3 收口：`.ai_worflow` `git init` 为独立本地仓库（无远端；`runs/`、`references/` 经 `.gitignore` 不入库）——**该仓库于 v1.8.3 按用户决定撤销**；pre-commit hook 升 **v3**（新增"仓库根即包根"布局分支——v2 在嵌套仓库恒定跳过，闸门变假象）；`{{ run_id }}` 补渲染；7 个陈旧 run 按快照协议收口（15-001 terminated 保留 R-1 白名单、5 个修复后撤白名单、16-001/17-001/18-002 补记 completed） | 陈旧 run 收口与 `{{ run_id }}` 修复持续有效；`check_all` 陈旧 WARN 清零 |
| **v1.8.1** | 规则生命周期补齐（docs/32 落地）：`_shared/contracts/rule-lifecycle.md` 新增"任务后能力观察"（Add 发现机制：信号触发才输出、最多一条、只建议不自动改、记录在 current.md#Change Log 不新增账本类型）与删减判据四信号（误伤 ≥2 次 / 无人消费 / 重复实现 / 模型升级复检）；G10 行与 Planner Close 步骤同步接线；selftest 58→59（3h 存在性护栏：契约/G10/SKILL 三处任一脱钩即 FAIL） | 重复路径的沉淀从"靠人临场想起"变为 close 时信号触发；只增不减的 Harness 有了删减的判据与流程（删减走与新增相同的变更控制） |
| **v1.8.0** | 运行期强制执行三件套（`docs/31` 方案）：① `scripts/validate_transition.py` 写入时迁移校验（T-01 门禁 owner 越权 / T-02 块状态机 / T-03 gate 绑定 / T-04 attempts+star 人工证据），Planner 覆写前 `cp state.yaml state.prev.yaml` 建快照；② `validate_run.py` 新增 DAG 语义一致性 R-1/R-2/R-3（completed 块祖先必须终态、completed run frontier 必空、未登记块=pending），连边复用 `run_flow.build_graph`；③ `scripts/check_all.py` 全系统日检（mtime 陈旧检测 + 收据/闸门汇总，只读不代写）。selftest 52→58，新增护栏全部有反例真实触发；存量不一致 run 按"显式承担"登记 `runs/README.md` | "Planner 代签 G9"类越权在写入瞬间被拒；"close 完成但 spec 未做"类伪完成判 FAIL；停滞 run 有日检点名与建议动作 |
| **v1.7.8** | 新增 `docs/26-reference-scan-20260918.md`：15 篇微信参考 L1 全文 + 39 张图 RapidOCR；附录 59→74 条（a01–a59 + c01–c15）；E9 落地到 `prompts/intake.md`（G0 Intake 增加领域术语/业务不变量）；11 个改进项（E1–E11，其中 8 个印证已有设计、1 个本轮落地、3 个记录为未来方向） | 参考视野扩展到 74 个外部来源；G0 需求接收从"目标+边界"升级为"目标+边界+领域语言" |
| **v1.7.7** | 新增 `scripts/validate_consistency.py`，把 G0–G10、G3/G8 人工确认、G4 TDD Red、G5 Code Review、context 读写跨 `docs/03-gates.md`、feature workflow 与 HTML 流程图三方对齐为确定性护栏；selftest 从 50/50 扩至 52/52，并用真实 Run 完成跨 Run context 读/写与 TDD Red→Green 闭环 | 一致性不再靠人工矩阵声明；流程图或门禁漂移会被 selftest 阻断 |
| **v1.7.6** | 功能交付 `check` 由站点专用 `python3 site/scripts/check-links.py` 改为通用 `git diff --check origin/develop...HEAD`；pre-commit hook 增加“仓库根无 `.ai_worflow/scripts/selftest.sh` 时安全跳过”的 worktree 边界，hook 标记升级为 v2 | 工作流 check 不再绑定不存在的站点脚本；生产 worktree 复用 common git hook 时不再误报阻断 |
| **v1.7.6** | **TDD 门禁补全**：G4 从"测试计划文档"升级为 TDD Red（测试文件先于实现写入且执行 FAIL 证据绑定 SHA），G6 增量测试 PASS 证明 Red→Green 闭环；新增 `docs/25-large-task-protocol.md`（拆分阈值 >15 文件/>1500 行/≥3 模块；跨 Run 交接：Run1 G10 写 context → Run2 G1 读 + 增量扫描）；新增 `context/` 目录（project/area/decisions/risk-register 四模板）；`run-state.yaml` 新增 timestamps 字段 | 影响文件：`docs/03-gates.md` / `skills/_shared/contracts/gate-policy.md` / `skills/aiworflow-tester/SKILL.md` / `workflows/feature-delivery.workflow.yaml` / `context/` / `docs/25` |
| **v1.7.5** | **全量来源核验收口**：README「访问核验」表由 26 行扩至 **64 行**并于 2026-09-14 全量复跑（62 行可访问；`developers.openai.com` 403 区域封锁、`51cto.com` JS 反爬两行诚实标注不可用）；23 个微信 URL 以 MicroMessenger UA 重抓，记录每篇真实全文字数；**a35 升 L1**（腾讯新闻直接提取 8,259 字符）、**a36 升 L1**（阿里云移动 UA 取 `lark-content` SSR 正文 8,430 字符，AACR-Bench/南京大学/覆盖率+285% 等事实全部落到全文证据）；GitHub star 数刷新为 API 实值（aidlc 4,598 / langflow 154,789 / BMAD 52,999 等，以核验表带时间戳的 API 读数为准）；`docs/22` 收录搜狗微信 2026-09 扫描 55 篇候选（L3）；证据分级 L1/L2/L3 在 `docs/22` §〇 定义 | 全局视野：34→36 个正式收录来源；**每条引用都有可复跑的 HTTP 证据**；不可达来源不再被冒充为已核验，替代来源（虎嗅 4834939 等）显式标注 |
| **v1.7.4** | 微信搜索 + hongtao2agent.xyz 全站 25 篇扫描；新增 `docs/22-wechat-latest-scan.md`（Claude 5 上下文工程七判断、DeepSeek Harness 五层插件原理、Agentic SRE 五层架构、Pi Compaction）；附录新增 a31–a34；吸收：Compilation 上下文编译概念、Subtraction 减法优先、Assembly/Scope 分离 | 全局视野：30→34 个外部来源；上下文工程成为显式设计目标；DSH 的装配/作用域分离验证了 AIWorflow Flow/Role 分层的设计思路 |
| **v1.7.3** | 新增 `docs/21-emerging-paradigms.md` 前沿范式全景扫描（BMAD 53K⭐/ MoAI-ADK TRUST 5+Kanban/CEK/flow-next 对抗式审查/oddyssey ODD 等 12 个新兴范式）；附录新增 a25–a30（6 个 GitHub 项目+范式条目）；README 血缘表新增 6 个来源 | 全局视野更新：24→30 个外部来源；吸收清单新增：No False Verification、TRUST 5 五维门、对抗式跨模型审查、ODD 可观测驱动、Task Dependency Graph 自动生成、上下文工程 |
| **v1.7.2** | `run_flow.py --advance` 每轮自动持久化轮次日志到 `state.yaml` 的 `ledger` 字段；`run-state.yaml` 模板新增 `ledger` 字段；`--advance` 结束信号 `DONE` 时自动写入 final 条目 | 每轮推进都有持久化审计记录，中断后可从 ledger 恢复推进位置；所有 history 可追溯不依赖 stdout |
| v1.2.0 | 引入 `VERSION` 单一事实源 + 安装收据 + 漂移检测 + 原子升级 | 可回答「装的是哪版、有没有被手改」 |
| v1.2.1 | 补「认领已装好但无收据的环境」路径（`--apply` 补收据；漂移目标拒绝认领） | 历史安装可纳管 |
| **v1.5.2** | 全量审计：5 个 SKILL.md（入口+四角色）全部添加「受约契约」与「吸收自」元数据段；5 个 Prompt 模板（intake/spec/implement/review/test）全部添加契约引用与文章溯源注释；`candidate-dag.md` 添加护栏清单引用；5 个角色参考文件补充契约锚定；Reviewer SKILL.md 明确「确定性脚本覆盖的结构不在 Review 范围」；Tester SKILL.md/test-strategy.md 新增「UNKNOWN≠PASS」显式区分；Planner SKILL.md 整合六问框架/风险分层/周期性审计/失败入账到主流程 | 所有 Prompt 和 SKILL.md 均可追溯到 18 篇文章和 9 份契约，消除「契约写了但 Prompt 没用」的断层
| **v1.5.3** | `install_hooks.py` 修复 `.git` 查找逻辑：`default_hook_dir()` 新增 `_find_git_dir()` 向上遍历父目录，解决 `.ai_worflow/` 不在仓库根时无法定位 hooks 目录的问题；selftest.sh §10 从"找不到 .git 报 FAIL"变为"找到父目录 .git 后正确安装/检查" | selftest 52/52 PASS，pre-commit hook 已安装到仓库 .git/hooks/
| **v1.5.1** | 基于 18 篇 AI Coding/Harness Engineering 文章系统优化所有共享契约：`evidence-rules.md` 新增「六层验证框架」（a03）+「确定性规则优先」（a12）+「周期性系统审计」（a01）；`gate-policy.md` 新增「规则过期淘汰」（a15）；`role-boundaries.md` 新增「软件工程判断力」（a17）+「Review≠Truth Generator」（a03）+「确定性优先」（a12）；`workflow-state.md` 新增「多天/多会话恢复」（a10）+「五层闭环状态映射」（a16）；`change-control.md` 新增「Vibe→SDD→Harness 递进」（a02）+「渐进式澄清」（a08）+「规则版本化」（a15）；`git-policy.md` 新增「Commit 时间线非证据」（a01）+「统一约束入口」（a04）；`handoff-contract.md` 新增「上下文连续性 > 对话历史」（GoPS）+「跨会话恢复交接」（a10）；新增 `rule-lifecycle.md`（规则三层体系/有效期与淘汰/规范工具化/护栏分层）；`artifact-lifecycle.md` 新增「失败尝试必须入账」；`contracts/README.md` 新建；README 附录确认 18 篇文章（a01–a18）完整收录 | 所有契约文件均标注吸收自哪篇文章，可追溯 |
| **v1.4.1** | `validate_package.py` 新增第 10 步 **`runs/` 容器一致性护栏**：每个 `runs/<ID>` 要么通过 `validate_run.py`，要么在 `runs/README.md` 显式登记为占位，不允许「半清理的 run 恒定 FAIL」这种第三态（恒定 FAIL 会让人和 Agent 习惯性忽略 FAIL，护栏被当噪音就等于没有）；`selftest.sh` §3b 用临时负例目录证明它真的会开火、用完即清理，全量 47 → 50 项 |
| **v1.4.0** | 护栏从「有人跑才生效」下沉到**提交动作本身**：新增 `scripts/hooks/pre-commit` + `scripts/install_hooks.py`（`--dry-run/--apply/--check/--uninstall`，原子替换、外来 hook 先备份、标记+SHA 双确认才卸载），`selftest.sh` 39 → 50 项（§10 七项闸门断言 + §8 第九项「外来目标拒绝部分安装」）；§4/§10.7 改为**同根硬断言、异根显式 SKIP**，换机器/克隆也能用；修复 `install_skills.py` 真实缺陷——目标含外来软链时旧版会装其余 5 个、写下覆盖 6 个 Skill 的收据并返回 0（**收据为没装的文件作伪证**），现在拒绝部分安装：零落地、零收据、非 0 退出；hook 失败时透出 `[护栏ID] 位置: 具体问题 + 怎么改`（旧版只给 FAIL 文件名，看不到原因） |
| **v1.3.0** | `docs/09` 声称的 7 条 author-time 硬护栏**全部代码落地**（新增 `secret_inline` / `unsafe_command` / `evidence_free_gate` / `unbounded_retry`，既有规则挂护栏 ID，`GUARDRAIL_IDS` 注册表强制）；`selftest.sh` 26 → 50 项（§9 逐条证明护栏开火 + 死护栏检测）；`_examples/` 纳入自检；修正 docs/02·06·07·09·11·13 与 `runs/README` 中「文档冒充实现」的失效描述 | **破坏性收紧**：v1.2.1 下能通过的定义，若 `gate` 块缺 `evidence`、`max_attempts` 越界、`commands` 含破坏性模式或 `secret` 参数内联值，在 v1.3.0 会被拒绝 |

这个包现在是一份**可版本化、可校验、可交给别人**的工程资产，不是一堆散落的 Markdown。

### 版本单一事实源

| 事实 | 位置 | 说明 |
|---|---|---|
| 包版本 | `VERSION` | semver，唯一权威；README 头部版本必须与之一致 |
| 版本历史 | `VERSION` 文件为唯一事实源 | 本目录为独立 git 仓库（2026-09-20 21:02 重新自建 `d551273`，remote `zaf05/ai-coding-workflow`）；主仓 `.git/info/exclude` 排除本目录，安装收据（`~/.codex/skills/aiworflow-install-receipt.json`）记录 source_version 与 source_root |
| 第三方参考 | `references/`（**不入库**，590MB） | 来源与钉住 commit 记录在 `docs/12-reference-scan.md`，可按需重新 clone 复现 |

### 安装即锁定：收据 + 摘要

`scripts/install_skills.py --apply` 会在目标目录写 `aiworflow-install-receipt.json`：

```json
{
  "receipt_version": 1,
  "source_root": "/path/to/.ai_worflow",
  "source_version": "1.4.1",
  "source_fingerprint": "<整包 SHA256>",
  "mode": "symlink",
  "installed_at": "2026-09-11T...",
  "manifest": { "aiworflow": { "SKILL.md": "<sha256>", ... }, ... }
}
```

有了收据，下面三个问题从"猜"变成"查"：

| 问题 | 命令 | 判定依据 |
|---|---|---|
| 目标机器装的是哪一版？ | `--check` | 收据 `source_version` vs `VERSION` |
| 有没有人绕过流程手改过？ | `--check` | 逐文件 SHA256 与收据比对，列出漂移文件 |
| 升级会不会破坏宿主？ | `--upgrade --apply` | 只替换收据登记过的 Skill；先备份→替换→失败回滚；收据未登记的文件一律不动 |

### 这套行为本身也被测试覆盖

不写"应该支持版本锁定"这种文档承诺，而是写成断言——`scripts/selftest.sh` §8 共 8 项：

1. `VERSION` 存在且为合法 semver；
2. `--apply` 必须写出收据，且随后 `--check` 一致；
3. 手改目标文件后 `--check` 必须判为漂移（非零退出）；
4. `--upgrade --apply` 后必须恢复一致；
5. 升级不得触碰收据未登记的宿主文件；
6. **认领**：目标已装好且与来源逐文件一致、但缺收据时，`--apply` 必须补写收据且随后 `--check` 一致（不改任何 Skill 文件）；
7. 目标与来源存在漂移时**拒绝认领**，不写收据并非零退出；
8. `--dry-run` 认领只预览、不落盘。

全量自检（`bash scripts/selftest.sh`，当前 70/70 通过；§12 站点在线时计入，离线 69/69 + 1 SKIP）。

### 运行期闸门（v1.4.0 起 · v1.8.2 双布局）

author-time 护栏只解决「写坏的定义过不了校验」，但校验**只在有人运行时才发生**。v1.4.0 把它绑到提交动作上；hook **v3** 支持两种布局（自动探测）：**布局 A（当前）** 装于主仓 `.git/hooks/`、主仓根提交时生效；**布局 B** 仓库根即包根（`install_hooks.py --apply` 从包目录运行即自动探测，本目录一旦自建 git 仓库即可用）。注意布局 A 下 `.ai_worflow` 被主仓 exclude，**其自身变更不触发 hook**——改完规则后手动跑 `bash scripts/selftest.sh` 兜底：

```bash
python3 scripts/install_hooks.py --apply    # 装到 .git/hooks/pre-commit（自动探测布局）
python3 scripts/install_hooks.py --check    # 复核：未装/非本包产物/漂移/无执行位 → 全部非 0
```

端到端实测（临时克隆，不碰真仓库）：干净改动放行；`gate` 缺 `evidence` 或 `commands` 含 `rm -rf` 的提交被拒且 `HEAD` 不前进，终端直接给出 `[evidence_free_gate]` / `[unsafe_command]` 与修复建议；补上 evidence 后同一提交放行。

已知边界（不假装闭环）：`git commit --no-verify` 能绕过任何本地 hook，换机器也需重新 `--apply`——所以 `docs/13-roadmap` 把「CI 侧再挂一次」列为下一层。

### 给别人用的最小路径

```bash
# 对方机器上
cd <path_to_ai_worflow>                   # 本目录已在主仓工作副本中
bash scripts/selftest.sh                              # 先证明包本身是好的（70 项，站点在线口径）
python3 scripts/install_skills.py --target "$HOME/.codex/skills" --dry-run
python3 scripts/install_skills.py --target "$HOME/.codex/skills" --mode symlink --apply
python3 scripts/install_skills.py --target "$HOME/.codex/skills" --check
python3 scripts/install_hooks.py --apply              # 把护栏绑到提交动作（阻断级闸门）
python3 scripts/install_hooks.py --check
```

> 边界：文件系统安装成功 ≠ 宿主实机加载成功。实机加载必须在宿主会话内真实触发一次才算验证过。
> 本包不含密钥、令牌、Cookie 或真实用户数据；`runs/` 里的证据均为本地开发记录。

## 当前实现状态（事实，不是目标）

| 能力 | 状态 | 证据 |
|---|---|---|
| 参考工程 clone ×3 | 已完成 | `references/skyvern`（5496 文件，commit `35cb497c99dc940472023e682692613e1014e51f`）、`references/ric-dev-workflow-skills`（95 文件，commit `84954fbda3d1d8c47ef2a5ee9fb43e18ab4a3c4a`）、`references/jakubkrehel-skills`（11 个 Skill 目录，commit `267330e`，2026-09-16 入库，见 `docs/12-reference-scan.md` §E） |
| 规则与设计文档 | 已完成 | `docs/`（35 篇 + README；本仓库内相对链接全部可解析，由 `scripts/validate_package.py` 校验） |
| Skill 包（5 入口 + `_shared`） | 已完成 | `skills/`，frontmatter 与链接由 `scripts/validate_package.py` 校验 |
| 工作流定义（4 正例 + 7 反例） | 已完成 | `workflows/`，由 `scripts/validate_workflow.py` 校验；7 个反例各对应一条 author-time 硬护栏 |
| 校验器 / 安装器 / 自检 | 已完成 | `scripts/`，`python3 scripts/validate_package.py` 与 `bash scripts/selftest.sh` 70/70 PASS |
| 版本管理与分发 | 已完成（v1.4.1） | `VERSION` + 安装收据/漂移检测/原子升级/认领已装环境/拒绝部分安装（见 §版本管理与分发） |
| 版本锁定行为自测 | 已完成 | `scripts/selftest.sh` §8 九项断言（含外来目标拒绝部分安装）；全量 70/70 通过 |
| `runs/` 容器一致性护栏 | 已完成（v1.4.1） | `validate_package.py` 第 10 步：非法 run 必须清理或登记为占位；`selftest.sh` §3b 负例证明护栏开火 |
| 运行期闸门（pre-commit） | 已完成（v1.4.0） | `scripts/hooks/pre-commit` + `scripts/install_hooks.py`；`selftest.sh` §10 七项断言；端到端实测破坏被拦、修复后放行 |
| 2025–2026 主流实践调研 | 已完成（网页证据） | `docs/14-current-practices.md`：8 条一手/官方来源、与三层模型对照、5 项应吸收修正 |
| Prompt 模板 | 已完成（纯文本模板，无模板引擎依赖） | `prompts/` |
| 真实 run 记录 | 已完成多个真实 run | `RUN-20260914-001`（skill-tool-tag，已合入 develop）、`RUN-20260920-001`（运行期强制执行落地 run，已完成）；2026-09-20 维护处置收口 7 个陈旧 run（详见 `docs/31` P3 记录与各 run `current.md#Change Log`）；历史 run（`RUN-20260908-*`）磁盘已不存在 |
| 宿主实机加载 | Codex 与 Claude Code 双宿主已实测加载 | `~/.codex/skills` 与 `~/.claude/skills` 的 `aiworflow*` 符号链接均落地（两宿主 `install_skills.py --check` 收据指纹一致；2026-09-21 随 v1.8.11 升级复核）；`RUN-20260908-002` 由 Codex 角色会话真实产出；2026-09-20 双宿主只读探针复测：Codex 会话列出 5 个 skill 链接并读出 SKILL.md frontmatter / VERSION 1.8.9 / 角色规则引文，Claude Code 嵌套会话系统 skill 清单实际注册全部 5 个 aiworflow* skill 并经符号链接实读 SKILL.md / 安装收据 / contracts |
| 会话归因（model / tokens_used） | 已完成（v1.8.7） | `run_flow.py --session-meta` + selftest §7d-ter：model 必填、tokens 可为 null、非法输入拒绝；角色报告模板含 session 字段 |
| Review 确定性前置检查 | 已完成（v1.8.7） | `scripts/review_preflight.py` + selftest §7d-quatro：secret/禁改区/破坏性命令负例开火，干净 diff 通过 |
| task_resume checkpoint/state/ledger 消费 | 已完成（v1.8.8） | selftest §13c-bis；真实 ≥3 块断点演练仍待触发，不能宣称 L3 实战闭环 |
| Flow 引擎可执行实现（真正跑 DAG 的进程） | 已完成 | `scripts/run_flow.py` 已实现确定性 DAG 构图/环检测/frontier/STAR/HANDOFF/CHECK，`--execute-check` 真实执行 check；`RUN-20260908-006` 已用它跑 `check` 块并 PASS，最终 frontier 为空 |

---

## 当前工作流核心能力总结

### 一句话：这是什么

AIWorflow 是一套**纯文件驱动的 AI 研发控制层**。它不提供浏览器自动化、不做云端编码环境、不依赖数据库或消息队列。它的唯一职责是：**把 AI 的一次请求变成一条可证明的交付链路**。

### 完整链路

```
用户说"做某功能"
  → aiworflow 入口识别场景、选工作流
  → Planner 执行 G0 intake → G1 recon → G2 spec（六问框架逐条回答）
  → 用户 approve（G3，`*` 不可代签）
  → Planner 产出候选 DAG → compile_dag.py 编译 → G4 冻结
  → 自动化推进循环（v1.6+）：
      CONTINUE → 继续 / WAIT_ROLE → 调角色 / WAIT_USER → 等人 / BLOCKED → 归因 / DONE → close
  → Implementer 按块实现（单块、小任务包）
  → Reviewer 只读独立审核（绑定 SHA + 命令输出，不得 AI 自述）
  → Tester 独立验证（UNKNOWN ≠ PASS）
  → G8 release_check（人工确认）
  → G9 accepted → integration baseline
  → G10 close（lessons/change-summary 写回供下一环复用）
```

### 核心数字（2026-09-21，v1.8.11）

| 指标 | 数值 |
|---|---|
| 规则文档 | 36 篇 + docs/README |
| 共享契约 | 9 份（角色/门禁/证据/状态/变更/Git/交接/规则生命周期/产物；护栏注册表在 `docs/09` 与脚本 `GUARDRAIL_IDS`，非独立契约文件） |
| Skill 入口 | 5 个（入口+四角色）+ 1 个 `_shared` 共享底座 |
| 工作流定义 | 4 正例 + 7 反例（每个反例对一条 hard guardrail 开火） |
| Prompt 模板 | 7 个（intake/spec/implement/review/test/candidate-dag + 1 示例） |
| 确定性脚本 | 16 个代码脚本 + pre-commit hook（校验×7：workflow/package/run/transition/consistency/content-quality/site-consistency；引擎×7：compile_dag/run_flow/check_all/task_resume/review_preflight/install×2；selftest + _yaml_min；Python 3 + bash + 已有 PyYAML） |
| selftest | 70/70 PASS，13 个分组覆盖包结构→反例→transition→DAG语义→日检→安装→编译→执行→版本锁定→闸门→站点一致性→长周期恢复链 |
| 总代码行（脚本） | 5,180 行 Python + Shell（wc -l 实测 2026-09-20） |
| 总文档行 | 6,165 行 Markdown（docs 5,437 + 根 README 728，wc -l 实测 2026-09-21） |
| 外部依赖 | 0 新增（Python 3 + bash + 当前环境已有 PyYAML；不引入数据库/消息队列/npm 依赖） |
| 宿主加载 | Codex 与 Claude Code 双宿主已实测加载（2026-09-20 只读探针：Codex exec 会话与 Claude Code `-p` 嵌套会话各自发现/注册并实读 skill；两宿主收据 1.8.11 指纹一致，2026-09-21 升级后复核） |

### 三层防护体系

```
author-time 护栏 (validate_workflow.py/compile_dag.py)
  → 拒绝无效 YAML、环、star 绕过、越界重试、内联秘密、自审
commit-time 闸门 (pre-commit hook via install_hooks.py)
  → 提交时 Block，不可静默绕过
run-time 强制执行 (run_flow.py --advance --execute-check)
  → loop_control 信号驱动、重试上限硬拒绝、熔断
```

### 版本分发

一条命令安装/升级/检查：

```bash
python3 scripts/install_skills.py --target ~/.codex/skills --mode symlink --apply
python3 scripts/install_skills.py --target ~/.codex/skills --check    # 哪版？有没有被手改？
python3 scripts/install_skills.py --target ~/.codex/skills --upgrade --apply  # 原子升级
```

## 七工程对比分析：我们的优势与劣势

三个本地参考资产位于 `references/`（V4.0 / Skyvern / ric-dev），另 4 个 GitHub 开源项目（AWS AI-DLC / Langflow / CCG / AI Workflow）通过 GitHub API 核验提取，详细扫描分析见 `docs/20-external-workflow-projects.md`。

### 七工程对比总表

| 维度 | 我们 AIWorflow v1.8.9 | Skyvern | ric-dev | V4.0 | AWS AI-DLC | Langflow | CCG | AI Workflow |
|---|---|---|---|---|---|---|---|---|
| **定位** | AI 研发控制层（纯文件） | 浏览器自动化 | 四角色Skill包 | 流程图 | AI开发生命周期 | 可视化Agent编排 | 多模型协作引擎 | Skill内容市场 |
| **规模** | 36 docs+9 contracts+16 scripts | 5496文件 | 95文件 | 1 HTML | TypeScript+CLI | Python+React+DB | Go/Node.js+CLI | HTML(Skills集合) |
| **DAG 执行** | ✅ run_flow.py | ✅ 完整引擎 | ❌ 无 | ❌ 无 | ✅ aidlc CLI | ✅ Python后端 | ✅ ccg CLI | ❌ 无 |
| **护栏系统** | ✅ 三层全自动 | ✅ author+review | ⚠️ 语义定义 | ❌ 无 | ✅ approval gate | ⚠️ 平台层 | ❌ 未明确 | ❌ 无 |
| **版本管理** | ✅ VERSION+SHA256 | ❌ 无 | ❌ 无 | ❌ 无 | ✅ GitHub Release | ✅ PyPI | ✅ npm | ❌ 无 |
| **selftest** | ✅ **70/70 PASS** | ⚠️ pytest不测Skill | ❌ 无 | ❌ 无 | ⚠️ 有CI | ⚠️ 有pytest | ⚠️ CI+codecov | ❌ 无 |
| **多宿主** | Codex/Claude/ZCode | 自建平台 | Codex/Claude/ZCode | 无 | **7宿主** | Web UI | Claude+Codex+Gemini | **14+宿主** |
| **证据系统** | ✅ 只追加账本+ledger | DB记录 | Compact四文件 | 无 | ❌ 未明确 | ❌ 运行日志 | ❌ 未明确 | ❌ 无 |
| **环系统建模** | ✅ 显式+环间接口 | 隐式 | 未建模 | 隐式 | 隐式(13段) | 隐式(流程) | 未建模 | 未建模 |
| **轮次日志** | ✅ ledger 自动持久化 | DB记录 | 无 | 无 | 无 | DB记录 | 无 | 无 |
| **AI自动路由** | 入口description | ❌ 手动 | ❌ 手动 | ❌ 无 | ✅ 自动选工作流 | 用户拖拽 | ✅ 意图分析 | 用户手动选择 |
| **外部依赖** | **已有 PyYAML；本版本 0 新增** | PG+Redis+200+包 | 0 | 0 | Node.js/Bun | Python+React+DB | Node.js>=20 | Node.js |
| **文章溯源** | ✅ 130 来源全量收录与复盘（001–086 docs/33、087–124 docs/34、125–130 docs/35） | 无 | 无 | 无 | 无 | 无 | 无 | 无 |

### 我们的优势（七工程中独有或更深）

1. **确定性自检体系（selftest 70/70）**：七工程中唯一把包结构、反例护栏开火、版本锁定、DAG 编译、钩子安装、长周期恢复链全部写成确定性断言并换机器可跑的。Skyvern 有 pytest 但不测 Skill 包一致性；Langflow/CCG 有 CI 但无 workflow 工作流级 selftest。

2. **除当前环境已有 PyYAML 外零新增依赖**：Skyvern 需 PG+Redis+CDP+200+包；Langflow 需 Python+React+DB；AI-DLC/CCG 需 Node.js。我们 Python 3 + bash，仅复用当前环境已有 PyYAML；本版本未新增 pip/npm/数据库依赖。

3. **版本锁定与漂移检测**：七工程中唯一有 `install_skills.py --check` 回答"装的是哪版、有没有被手改"，VERSION 单一事实源 + 逐文件 SHA256 收据 + 原子升级。

4. **三层护栏自动下沉**：author-time → commit-time (pre-commit hook) → run-time (loop_control + 熔断)。AI-DLC 有 approval gate 但无 commit-time hook；ric 有门禁定义但无自动化执行。

5. **环系统显式建模 + 轮次日志（ledger）**：七工程中唯一把环骨架和环间接口显式建为规范，且每轮自动持久化轮次日志到 `state.yaml`。

6. **124 条外部来源全量收录与溯源**：a01–a36 于 2026-09-14 全量核验（README「访问核验」表，a37 于 09-20 增补），后续批次（docs/23/24/26/28/32）逐批扫描落档、编号统一登记在 HTML 附录；每份契约、每个 SKILL.md、每个 Prompt 模板标注了吸收来源，吸收点记录在 `docs/21`、`docs/22`、README 附录与各批扫描文档。2026-09-20 完成全量复盘：001–086 每条有归属判定（`docs/33`），无「收录未消化」悬空项；同日全网检索批 087–124（38 条，L3 快照级为主并强制「生态样本/非规则依据」标注）归属判定见 `docs/34` §八，012/025/046/066 获证据更新；2026-09-21 收编 Loop Engineering 批 125–130（`docs/35`：五组件印证 + automations 心跳层缺口登记 `docs/13`）。其他六工程不记录外部文章吸收。

### 我们的劣势（七工程中别人更强的地方）

1. **治理深度不如 Skyvern**：Skyvern 90 个 Copilot 文件有 completion verification 原因码白名单、修复根因签名、自愈日上限。我们三层护栏在"能做真实拦截"上成立，但精细度不如。**场景决定**：Skyvern 是平台级，我们是个人+小团队控制层，当前够用。

2. **多宿主不如 AI-DLC 广**：AI-DLC 适配 7 宿主，AI Workflow 支持 14+ 宿主。我们只有 Codex/Claude/ZCode 三宿主。**下一步**：需要时按 AI-DLC 的薄配置模式扩展。

3. **可视化编排表现力不如 Langflow**：Langflow 的拖拽式 DAG 编辑 + 155K stars 证明市场强烈需求可视化。我们的 YAML 驱动更适合 Git 版本化和 review，但缺少可视化。**明确不吸收**：文件驱动 > 拖拽，YAML 可 diff/review/CI。

4. **无多模型协作策略**：CCG 的 `/ccg:go` 能自动分析意图→选择策略→分派给不同模型（Claude规划/Codex实现/Gemini审查）。我们的四角色不区分底层模型。**未来可借鉴**：当需要"Planner 用强模型、Implementer 用快模型"时吸收 CCG 策略配置设计。

5. **无多语言审查规则**：ric-dev 有 9 种语言审查规则。我们通用规则 + WanGo AGENTS.md 覆盖前端。

6. **无团队协作方案**：Skyvern 有组织/租户/权限模型。单人阶段通过安装收据分发。**已在 roadmap 登记**。

7. **Skill 市场不如 AI Workflow**：AI Workflow 有 170+ 预构建 Skill + 多领域分类 + 一键安装。我们的 Skill/Tool 管理功能正在建设中，标签分类可参考 AI Workflow 的领域词典。

### 一句话定位

> **AIWorflow = Skyvern 的 DAG 思想 + ric 的四角色模型 + V4.0 的流程骨架 + AI-DLC 的多宿主思路 + CCG 的策略路由理念 + Langflow 的块类型目录 + AI Workflow 的 Skill 组织方式 + 130 条外部来源（文章/深度解读 + 开源项目/GitHub 范式；001–086 归属判定见 docs/33、087–124 见 docs/34、125–130 见 docs/35）+ 黄迅环系统/GoPS 责任状态机，去掉浏览器面、可视化 UI 和重型基础设施，加上 selftest 确定性自检、版本锁定分发、三层护栏下沉、环间接口规范、ledger 轮次日志——在"最小可验证"前提下做到最完整。**

---


## 附录：AI Coding / Harness Engineering 参考文章（2026-09-14 完整收录）

> 以下 37 条（a01–a37）中 a01–a36 于 2026-09-14 通过 curl 实际抓取核验，a37 于 2026-09-20 增补。核验方式与逐条证据见下方「访问核验」表：HTTP 状态码、`og:title`/`<title>` 匹配、微信正文 `js_content` 提取字数、GitHub 走 API `stargazers_count`。
> **证据分级（与 `docs/22-wechat-latest-scan.md` §〇 一致）**：L1 全文核验 · L2 同文镜像核验 · L3 仅元数据核验（标题/公众号/日期/摘要）。标注 L3 的条目**不得引用其正文观点**。
> 文章可能有错——引用时注"原文观点"，与本工作流既有规则冲突时以 `docs/` 契约为准。
> 2026-09-20 全网检索批（087–124，共 38 条）登记于 HTML 附录与 `docs/34-web-scan-20260920.md`：GitHub 周榜条目 star 为榜单快照值，L3 条目仅作生态样本/观点记录；访问证据见下方核验表 row 66–103。2026-09-21 Loop Engineering 收编批（125–130，淘天原文 L1 + Addy/MF 原文可达补录 + 三条转引 L3）登记于 HTML 附录与 `docs/35`；访问证据见核验表 row 104–109。

| # | 日期 | 作者 | 标题 | 核心观点（与本工作流相关） |
|---|---|---|---|---|
| a01 | 2026-09-09 | 闫鹏 | [不做人工Code Review，如何保障 Vibe Coding 的项目质量？](https://mp.weixin.qq.com/s/a07Lu59zXHjNkXDqembyWA) | Agent 必须交付验证证据而非口头声明；周期性系统审计防止代码退化 |
| a02 | 2026-08-29 | AI模型之外 | [从"凭感觉写代码"到"可控地交付"：一篇讲透 Vibe Coding、SDD 与 Harness](https://mp.weixin.qq.com/s/hxB8tcV-APTdONcaLhiW3A) | Vibe Coding→SDD→Harness 三层递进模型；Harness 是 AI 的工作环境+操作规程+反馈回路+安全边界 |
| a03 | 2026-08-28 | 仁 | [Code Review 与 Verification Agent —— AI 如何审查 AI，如何避…](https://mp.weixin.qq.com/s/qj-ac6mW809wUPeoKkz8Lw) | 十个变化：Review=Candidate Generator 非 Truth Generator；Verification Agent 才是 Gate；六层验证（Requirement/Contract/Behavior/Evidence/Security/Regression） |
| a04 | 2026-08-13 | 左泽位 | [多 AI Coding Agent 工程化实践：用 CLAUDE.md + AGENTS.md 建立…](https://mp.weixin.qq.com/s?__biz=MzIwNDY3MDg1OA==&mid=2247495595&idx=1&sn=ebe7d9e43744de542a47b1a97f471427&chksm=96fffb5b20d16bd53da410ef8c219a17dd470bcb23f9870e3e2f713159817147a038c00b1720#rd) | CLAUDE.md/AGENTS.md 作为统一工程约束入口；渐进式披露不建巨型文件 |
| a05 | 2026-08-19 | 王安林 | [用 SpecKit + Pi + Superpowers 打造高效 AI 编程工作流](https://mp.weixin.qq.com/s/r0f4HfjNVHb6deJPU4jyvQ) | SpecKit 规约驱动 + Pi 规划器 + Superpowers 工具链的组合实践 |
| a06 | 2026-08-14 | XPoet | [AI 编程工程化：实战——从 0 到 1 搭建 AI 编程工作流](https://mp.weixin.qq.com/s/mDjpXRe_9TcIRD7VN2S17A) | 从零搭建 AI 编程工作流的完整实战：Rules/Skills/MCP/知识库 |
| a07 | 2026-08-22 | 离殇 | [Vibe Coding 项目规范](https://mp.weixin.qq.com/s/aycwkSyxhcRrJkyKPjU_8Q) | Vibe Coding 项目目录结构/命名/分支/提交规范 |
| a08 | 2026-08-05 | 得乐胶囊 | [AI 原生开发下的需求确定性构建：从渐进式澄清到 PRD，再到 Spec 驱动 AI Coding](https://mp.weixin.qq.com/s/tiBLN0_BFkGp2gZ-PX8QKg) | 需求澄清的渐进式流程；PRD→Spec→AI Coding 的确定性构建 |
| a09 | 2026-09-10 | 老A | [团队普及 AI Coding 以后，技术负责人应该怎样重新评估团队产能、安排需求和制定研发排期](https://mp.weixin.qq.com/s/T69Yk-kFDiQZBF4ChfHiTQ) | 团队产能评估、需求排期在 AI Coding 时代的重新思考 |
| a10 | 2026-07-30 | 丶单向箔 | [番外｜用一个完整需求跑通多天 AI Coding 工作流](https://mp.weixin.qq.com/s/P6kwha7fRnQznkrUoAHP7w) | 用完整需求跑通多天 AI Coding 的端到端实录 |
| a11 | 2026-09-08 | dialog996 | [AI 编程助手正在从"流程叙事"转向"模型 + Harness"](https://mp.weixin.qq.com/s/EsQIMi0bXCf5f4dQ6CM91g) | 多 Agent ≠ 可控执行；真正重要的是模型路由/执行编排/企业治理 |
| a12 | 2026-07-27 | Hank | [阿里内部用了两年的 open-code-review：一条命令扫完 vibe coding 的所有雷](https://mp.weixin.qq.com/s/E96e9pVj7uak99aa8-4Glg) | 两层审查：确定性规则引擎先扫硬伤（零误报），LLM 只做深层；每条规则来自几十万真实 bug |
| a13 | 2026-07-22 | 张逸少 | [SDD 工程化落地：双环驱动开发流程](https://mp.weixin.qq.com/s/AXgQR5wxKvQXu8zpZIWUfw) | SDD 双环驱动：规约环（Spec→Clarify→Plan）与实现环（Tasks→Implement→Verify） |
| a14 | 2026-09-03 | 孔令飞 | [Harness AI Coding 工程化实践：如何将不同项目的代码一致性提升至 96%](https://mp.weixin.qq.com/s/ESWOKhUzBSJWutPqLSMdiA) | 规范工具化（46 个 MCP Tool 覆盖 Go 全生命周期）；高质量数据是 AI 代码一致性的核心 |
| a15 | 2026-09-10 | The fool ss | [【AI-Native 研发踩坑·下】Harness 会过期：AI 编程的方法论也在迭代](https://mp.weixin.qq.com/s/begqTCRK-6xA9dTJgLr_og) | Harness 会过期：删旧规则同写新规则一样重要；权限边界+验证闭环+规则编码是新增重点 |
| a16 | 2026-08-27 | AI实验室的一角 | [玩转 AI Coding：一份面向团队的 Harness Engineering 实践指南](https://mp.weixin.qq.com/s/txxB1aaO_nFbQ52r3oqaxw) | 五层闭环架构（输入/配置/模式引擎/Agent/MCP）；Rules 三层体系（User/Team/Project） |
| a17 | 2026-08-30 | 就是克克 | [AI Coding 时代真正重要的是软件工程判断力](https://mp.weixin.qq.com/s/Psm4zIMJcbj95-alf2-4VQ) | AI 降低的是执行成本不是质量标准；软件工程判断力是核心稀缺能力 |
| a18 | 2026-07-20 | David | [《驾驭 AI Coding：一份面向团队的 Harness Engineering 落地规范》详细解…](https://mp.weixin.qq.com/s/ZjnmJYWoRmL7vdYFLq6cUA) | 六大支柱（上下文管理/工具系统/执行编排/状态记忆/评估观测/约束恢复）；3+1 阶段落地；八类反模式三根因 |
| a19 | 2026-09-12 | 黄迅/PUBG Mobile | [两万字长文｜手把手带你趟过 AI Coding 深水区：编码让位，人退到哪里](https://mp.weixin.qq.com/s/tSmMdSSzLgTsAX1JUaZI9Q) | 「机器提供事实，人做判断」；提示词的尽头是基础设施；编排的尽头是 Runtime；环系统（触发→生产→闸门→人审→入库→复用）；「失败必须有名字」；「常」与「流」 |
| a20 | 2026-07-12 | AI运维实验室 | [在 GOPS 讲完"一人 + AI Agent 军团"，我更确定：Agent 进生产，关键不在模型，而在 Harness](https://mp.weixin.qq.com/s/1fbIwI5omis0lQ9GFKhl2Q) | OPC 闭环六段（问题→事实→判断→执行→验证→写回）；五个边界（事实源/权限/确认/成功/写回）；反直觉三则（不急着自建RAG/知识不是越多越好/Prompt不是治理机制）；L4→L5 团队过渡 |
| a21 | 2025+ | AWS Labs | [awslabs/aidlc-workflows](https://github.com/awslabs/aidlc-workflows) (NEW) | AI-DLC：一套核心适配 7 宿主（Claude/Codex/Cursor/Kiro/Copilot）；aidlc CLI + approval gate + 自动工作流选择；4,598 stars |
| a22 | 2024+ | Langflow | [langflow-ai/langflow](https://github.com/langflow-ai/langflow) (NEW) | 可视化 Agent 工作流编排（155K stars）；节点组件化+拖拽连线；可作块类型目录参考 |
| a23 | 2025+ | 枫少 | [fengshao1227/ccg-workflow](https://github.com/fengshao1227/ccg-workflow) (NEW) | 多模型协作引擎：/ccg:go → 意图分析→策略选择→Claude+Codex+Gemini 协作；5,884 stars |
| a24 | 2025+ | nicepkg | [nicepkg/ai-workflow](https://github.com/nicepkg/ai-workflow) (NEW) | 170+ 预构建 Skill 集合（14+ AI 工具）；多领域分类；可作标签词典参考 |
| a25 | 2025+ | BMAD | [bmad-code-org/BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD) | 敏捷 AI 驱动开发：Task Dependency Graph 自动生成；52,999⭐（2026-09-14 API 实时）。详见 `docs/21-emerging-paradigms.md` §a25 |
| a26 | 2025+ | MoAI | [modu-ai/moai-adk](https://github.com/modu-ai/moai-adk) | 验证驱动 Agent 编排 Harness：TRUST 5 质量门（Tested·Readable·Unified·Secured·Trackable）、Kanban/Factory Mode 上下文隔离、No False Verification；1,211⭐。详见 `docs/21` §a26 |
| a27 | 2025+ | NeoLabHQ | [NeoLabHQ/context-engineering-kit](https://github.com/NeoLabHQ/context-engineering-kit) | 上下文工程工具包：Skill 即上下文净化器、14+ 宿主兼容；1,694⭐。详见 `docs/21` §a27 |
| a28 | 2026 | Windy3f | [Windy3f3f3f3f/how-claude-code-works](https://github.com/Windy3f3f3f3f/how-claude-code-works) | Claude Code 内部机制深度解析：Agent Loop、上下文工程、工具系统；3,626⭐。详见 `docs/21` §a28 |
| a29 | 2025+ | gmickel | [gmickel/flow-next](https://github.com/gmickel/flow-next) | 可重复 Agentic 工程：durable specs + fresh-context workers + 对抗式跨模型审查 + receipts；696⭐。详见 `docs/21` §a29 |
| a30 | 2025+ | using-system | [using-system/oddyssey](https://github.com/using-system/oddyssey) | ODD（Observability-Driven Development）：OpenTelemetry 驱动 spec 改进循环；7⭐。详见 `docs/21` §a30 |
| a31 | 2026 | hongtao2agent | [Claude 5 上下文工程新规则：从堆规则到设计信息架构](https://hongtao2agent.xyz/html/claude-5-context-engineering/) | **L1** Compilation（编译后上下文）/ Subtraction（减法优先，"删掉 80% system prompt 无可测量损失"）/ 信息架构分层；详见 `docs/22` §a31 |
| a32 | 2026 | hongtao2agent | [DeepSeek Harness 插件机制全景解读](https://hongtao2agent.xyz/html/deepseek-harness-plugin-architecture/) | **L1** 五层插件原理；Assembly（装配）与 Scope（作用域）分离——"决定 Agent 看见什么" > "决定装了什么"；详见 `docs/22` §a32 |
| a33 | 2026 | hongtao2agent | [Agentic SRE：重写可靠性控制面](https://hongtao2agent.xyz/html/agentic-sre-control-plane/) | **L1** 动作分级（只读→建议→预批准→人工审批→禁止）、最小权限、人工 Gate、可回滚 + 全链路审计；详见 `docs/22` §a33 |
| a34 | 2026 | hongtao2agent | [Pi 的 Compaction：长会话如何继续工作](https://hongtao2agent.xyz/html/pi-compaction/) | **L1** 把长会话压成一份可继续工作的交接单；中断恢复机制；详见 `docs/22` §a34 |
| a35 | 2026-09-04 | InfoQ / 蚂蚁数科（魏长征） | [AI Coding 的下一步不是写得更快，而是可验收：蚂蚁数科 Harness 工程实践](https://news.qq.com/rain/a/20260904A0BX2G00) | **L1**（腾讯新闻本站正文直接提取全文 8,259 字符，2026-09-14 复抓一致）AI Coding 不创造新问题而是把需求模糊/目标漂移/事实冲突/验证不足**集中放大**；「验证能力是否跟上产能是最核心矛盾」；存量项目先重建事实源与质量门禁再放 Agent（60 万行 C++ 缺陷率 20%+→个位数）；详见 `docs/22` §二 a35 |
| a36 | 2026-03-12 | 阿里开发者（作者李峥峰，阿里云开发者公众号） | [给"氛围编程"系上安全带：阿里集团 AI 代码评审实践与 Benchmark 开源](https://developer.aliyun.com/article/1716140) | **L1**（2026-09-14 移动 UA 取 `lark-content` SSR 正文，全文 8,430 字符；桌面 UA 只有标题+简介）历时一年半 / 数万亿 Token 打磨；联合南京大学研发效能实验室开源 **AACR-Bench**（80 多位资深工程师交叉标注，问题覆盖率 +285%，10 种语言+仓库级上下文）；「阅读理解-提出假设-寻找证据-判定结论」评审闭环；日期以页面 `<meta name="date">`=2026-03-12 为准（搜狗快照为 03-09）；与 a12 同源、观点不重复计；详见 `docs/22` §二 a36 |
| a37 | 2026-09-20 | 蓝翔（腾讯云开发者） | [删掉80%的Prompt规则，Agent交付成功率反而更高了](https://mp.weixin.qq.com/s/fV8qN6qs9ac-VXDwZCuaxA) | 三支柱（可信上下文/可执行约束/可恢复流程）；「规则能不能形成约束，取决于违反它以后会发生什么」；Add/Thin 修剪纪律与任务后能力观察规则（对照扫描 docs/32，两条真缺口已落地 v1.8.1） |


---

- https://baijiahao.baidu.com/s?id=1864874679798414791&wfr=spider&for=pc
- https://zhuanlan.zhihu.com/p/2056025288866378509
- http://www.uml.org.cn/ai/202605101.asp?artid=27372
- https://github.com/Skyvern-AI/skyvern
- https://github.com/lichong-a/ric-dev-workflow-skills
- https://mp.weixin.qq.com/s/g4nTfxm7ebzRwkAVIGdIbg
- https://github.com/awslabs/aidlc-workflows
- https://github.com/langflow-ai/langflow
- https://github.com/fengshao1227/ccg-workflow
- https://github.com/nicepkg/ai-workflow
- https://mp.weixin.qq.com/s/hxB8tcV-APTdONcaLhiW3A
- https://mp.weixin.qq.com/s/tSmMdSSzLgTsAX1JUaZI9Q
- https://mp.weixin.qq.com/s/1fbIwI5omis0lQ9GFKhl2Q
- https://mp.weixin.qq.com/s/UE-RZH9hnbBd06CVapFGrA
- https://mp.weixin.qq.com/s/rlIyIIZOXFObNIXbPI7gDg
- https://github.com/bmad-code-org/BMAD-METHOD
- https://github.com/modu-ai/moai-adk
- https://github.com/NeoLabHQ/context-engineering-kit
- https://github.com/Windy3f3f3f3f/how-claude-code-works
- https://github.com/gmickel/flow-next
- https://github.com/using-system/oddyssey
- https://hongtao2agent.xyz/html/claude-5-context-engineering/
- https://hongtao2agent.xyz/html/deepseek-harness-plugin-architecture/
- https://hongtao2agent.xyz/html/agentic-sre-control-plane/
- https://hongtao2agent.xyz/html/pi-compaction/
- https://mp.weixin.qq.com/s/qj-ac6mW809wUPeoKkz8Lw
- https://mp.weixin.qq.com/s/a07Lu59zXHjNkXDqembyWA


## 访问核验（首核 2026-09-08 · row 6–8 于 2026-09-11 复核 · **2026-09-14 全量 64 行复跑** · row 65 于 2026-09-20 增补 · **row 66–103 于 2026-09-20 增补（全网检索批，docs/34） · row 104–109 于 2026-09-21 增补（Loop Engineering 批，docs/35）**，Asia/Shanghai）

核验方式：`curl` 跟随重定向记录 HTTP 状态码与响应字节数，并按站点选择 UA——`mp.weixin.qq.com` **必须**用 MicroMessenger/移动端 UA（桌面 UA 只返回 17 KB 空壳页），知乎/百家号用移动 UA，其余用桌面 UA；GitHub 仓库另走 API `stargazers_count` 并以本地 clone 的 commit 作硬证据。本表**只写实际访问到的结果**：能列出 URL 不等于可访问，能返回 HTTP 200 也不等于取到正文（见最后两行的反例）。

结果：**63/65 行可访问且证据可用；2 行诚实标注不可用**（`developers.openai.com` 区域封锁、`51cto.com` JS 反爬）。证据分级见 `docs/22-wechat-latest-scan.md` §〇：L1 全文核验 · L2 同文镜像核验 · L3 仅元数据核验。row 66–103（2026-09-20 全网检索批，`docs/34`）：GitHub 周榜条目 11 行为周榜页 webReader 直抓快照（star 为榜单快照值，未走 API 复核），其余 27 行为检索快照级 **L3**（仅标题/日期/摘要，深路径未单独核验，**不得引用正文观点**）。row 104–109（2026-09-21 Loop Engineering 批，`docs/35`）：row 104 为 webReader L1 全文；row 105/106 为 curl 200 可达性级 L3（正文未读）；row 107 文章页未取到、row 108/109 出口连接失败，均为转引 L3（生态样本/非规则依据）。

| # | URL | 核验方式 | 核验结果 | 页面标题 / 权威确认 | 补充证据与采信边界 |
|---|---|---|---|---|---|
| 1 | https://baijiahao.baidu.com/s?id=1864874679798414791&wfr=spider&for=pc | curl（移动 UA） | HTTP 200（468,367 B），可访问 | 打造持续可靠的AI工程：Harness Engineering实践 | 作者崔皓 / 51CTO；正文可读 |
| 2 | https://zhuanlan.zhihu.com/p/2056025288866378509 | curl（移动 UA） | HTTP 200（299,116 B），可访问 | 从AI Coding到Harness Engineering的端到端工程开发实践 | 知乎专栏；正文可读 |
| 3 | http://www.uml.org.cn/ai/202605101.asp?artid=27372 | curl（桌面 UA） | HTTP 200（83,995 B），可访问 | Harness Engineering：耗时一周，我是如何将应用的AI Coding率提升至90%的 | 火龙果软件转载 / 阿里云开发者 |
| 4 | https://news.qq.com/rain/a/20260904A0BX2G00 | curl（桌面 UA）+ 正文提取 | HTTP 200（322,578 B），可访问，正文提取成功 | AI Coding 的下一步不是写得更快，而是可验收：蚂蚁数科 Harness 工程实践_腾讯新闻 | a35；**L1** 本站正文直接提取全文 8,259 字符（tag-strip 法，2026-09-14 复抓复核一致）；专有名词命中：魏长征×3 / 「40多万行的Rust」/ 「超过60万行的C++」/ 「缺陷率从20%以上降至个位数」；InfoQ 官方账号 2026-09-04 18:05 发布 |
| 5 | https://developer.aliyun.com/article/1716140 | curl（移动 UA 取 `lark-content` SSR 正文；桌面 UA 仅得标题+简介 1,699 字符） | HTTP 200（桌面 UA 130,740 B / 移动 UA 121,932 B），正文提取成功 | 给“氛围编程”系上安全带：阿里集团 AI 代码评审实践与 Benchmark 开源-阿里云开发者社区 | a36；**L1** 移动 UA 全文提取 8,430 字符；关键事实：历时一年半 / 数万亿 Token / 联合南京大学研发效能实验室开源 AACR-Bench / 80 多位资深工程师交叉标注 / 问题覆盖率提升 285% / 作者李峥峰（阿里云开发者公众号）；页面 `<meta name="date">`=2026-03-12 10:52:41（搜狗快照元数据为 03-09）；与 a12 同源、观点不重复计 |
| 6 | https://developer.aliyun.com/article/1745179 | curl（桌面 UA） | HTTP 200（68,283 B），可访问 | OpenCode Agent 编排能力：如何让 AI 自主拆解任务、并行推进？-阿里云开发者社区 | docs/16 引用；旧核验记录里的 HTTP 400 是 URL 提取时多带了「、npm」造成的假象，实际 200 |
| 7 | https://hongtao2agent.xyz | curl（桌面 UA）+ 正文提取 | HTTP 200（39,379 B），正文提取成功 | Hongtao HTML Lab · 单页作品档案 | 可枚举全站 25 篇 HTML 深度解读列表 |
| 8 | https://hongtao2agent.xyz/html/claude-5-context-engineering/ | curl（桌面 UA）+ 正文提取 | HTTP 200（33,756 B），正文提取成功 | Claude 5 上下文工程新规则：从堆规则到设计信息架构 | a31；L1 全文提取（Compilation / Subtraction / 信息架构分层） |
| 9 | https://hongtao2agent.xyz/html/deepseek-harness-plugin-architecture/ | curl（桌面 UA）+ 正文提取 | HTTP 200（2,138,592 B），正文提取成功 | DeepSeek Harness 插件机制全景解读 | a32；L1 全文提取（五层原理、Assembly 与 Scope 分离） |
| 10 | https://hongtao2agent.xyz/html/agentic-sre-control-plane/ | curl（桌面 UA）+ 正文提取 | HTTP 200（38,144 B），正文提取成功 | Agentic SRE：不是自动修复，而是重写可靠性控制面｜详细解读 | a33；L1 全文提取（动作分级 / 最小权限 / 人工 Gate / 可回滚+审计） |
| 11 | https://hongtao2agent.xyz/html/pi-compaction/ | curl（桌面 UA）+ 正文提取 | HTTP 200（1,827,028 B），正文提取成功 | Pi 的 Compaction：把长会话压成一份可继续工作的交接单 | a34；L1 全文提取（长会话压缩与中断恢复） |
| 12 | https://hongtao2agent.xyz/html/gops-agent-production-harness/ | curl（桌面 UA）+ 正文提取 | HTTP 200（46,327 B），正文提取成功 | 模型给能力，Harness 给责任边界｜Agent 进生产深度解读 | a20 的镜像全文；OPC 闭环六段 / 五个边界 / L4→L5 |
| 13 | https://hongtao2agent.xyz/html/team-harness-engineering/ | curl（桌面 UA）+ 正文提取 | HTTP 200（40,730 B），正文提取成功 | 把“好代码”写进系统：团队 Harness Engineering 深度解读 | a18 同主题的渲染版全文；七核心判断 / 六支柱 / 3+1 Phase / 审计飞轮 |
| 14 | https://mp.weixin.qq.com/s/a07Lu59zXHjNkXDqembyWA | curl（MicroMessenger/移动端 UA）+ `js_content` 正文提取 | HTTP 200（3,466,539 B），正文提取成功，全文 2,740 字符 | 不做人工Code Review，如何保障 Vibe Coding 的项目质量？ | 桌面 UA 会返回 17 KB 空壳页，必须移动端 UA——这是本表所有微信短链可核验的前提 |
| 15 | https://mp.weixin.qq.com/s/hxB8tcV-APTdONcaLhiW3A | curl（MicroMessenger/移动端 UA）+ `js_content` 正文提取 | HTTP 200（3,539,280 B），正文提取成功，全文 8,372 字符 | 从“凭感觉写代码”到“可控地交付”：一篇讲透 Vibe Coding、SDD 与 Harness | 桌面 UA 会返回 17 KB 空壳页，必须移动端 UA——这是本表所有微信短链可核验的前提 |
| 16 | https://mp.weixin.qq.com/s/qj-ac6mW809wUPeoKkz8Lw | curl（MicroMessenger/移动端 UA）+ `js_content` 正文提取 | HTTP 200（3,471,292 B），正文提取成功，全文 2,578 字符 | 第五章：Code Review 与 Verification Agent —— AI 如何审查 AI，如何避免“自己写、自己通过”的问题 | 桌面 UA 会返回 17 KB 空壳页，必须移动端 UA——这是本表所有微信短链可核验的前提 |
| 17 | https://mp.weixin.qq.com/s/r0f4HfjNVHb6deJPU4jyvQ | curl（MicroMessenger/移动端 UA）+ `js_content` 正文提取 | HTTP 200（3,519,806 B），正文提取成功，全文 2,629 字符 | 用 SpecKit + Pi + Superpowers 打造高效 AI 编程工作流 | 桌面 UA 会返回 17 KB 空壳页，必须移动端 UA——这是本表所有微信短链可核验的前提 |
| 18 | https://mp.weixin.qq.com/s/mDjpXRe_9TcIRD7VN2S17A | curl（MicroMessenger/移动端 UA）+ `js_content` 正文提取 | HTTP 200（4,030,350 B），正文提取成功，全文 26,871 字符 | AI 编程工程化：实战——从 0 到 1 搭建 AI 编程工作流 | 桌面 UA 会返回 17 KB 空壳页，必须移动端 UA——这是本表所有微信短链可核验的前提 |
| 19 | https://mp.weixin.qq.com/s/aycwkSyxhcRrJkyKPjU_8Q | curl（MicroMessenger/移动端 UA）+ `js_content` 正文提取 | HTTP 200（3,550,624 B），正文提取成功，全文 3,420 字符 | Vibe Coding 项目规范 | 桌面 UA 会返回 17 KB 空壳页，必须移动端 UA——这是本表所有微信短链可核验的前提 |
| 20 | https://mp.weixin.qq.com/s/tiBLN0_BFkGp2gZ-PX8QKg | curl（MicroMessenger/移动端 UA）+ `js_content` 正文提取 | HTTP 200（3,534,168 B），正文提取成功，全文 3,550 字符 | AI 原生开发下的需求确定性构建：从渐进式澄清到PRD，再到Spec驱动AI Coding | 桌面 UA 会返回 17 KB 空壳页，必须移动端 UA——这是本表所有微信短链可核验的前提 |
| 21 | https://mp.weixin.qq.com/s/T69Yk-kFDiQZBF4ChfHiTQ | curl（MicroMessenger/移动端 UA）+ `js_content` 正文提取 | HTTP 200（3,434,342 B），正文提取成功，全文 2,720 字符 | 团队普及 AI Coding 以后，技术负责人应该怎样重新评估团队产能、安排需求和制定研发排期？ | 桌面 UA 会返回 17 KB 空壳页，必须移动端 UA——这是本表所有微信短链可核验的前提 |
| 22 | https://mp.weixin.qq.com/s/P6kwha7fRnQznkrUoAHP7w | curl（MicroMessenger/移动端 UA）+ `js_content` 正文提取 | HTTP 200（3,575,794 B），正文提取成功，全文 7,586 字符 | 番外｜用一个完整需求跑通多天 AI Coding 工作流 | 桌面 UA 会返回 17 KB 空壳页，必须移动端 UA——这是本表所有微信短链可核验的前提 |
| 23 | https://mp.weixin.qq.com/s/EsQIMi0bXCf5f4dQ6CM91g | curl（MicroMessenger/移动端 UA）+ `js_content` 正文提取 | HTTP 200（3,467,577 B），正文提取成功，全文 3,178 字符 | AI 编程助手正在从“流程叙事”转向“模型 + Harness” | 桌面 UA 会返回 17 KB 空壳页，必须移动端 UA——这是本表所有微信短链可核验的前提 |
| 24 | https://mp.weixin.qq.com/s/E96e9pVj7uak99aa8-4Glg | curl（MicroMessenger/移动端 UA）+ `js_content` 正文提取 | HTTP 200（3,428,471 B），正文提取成功，全文 3,353 字符 | 阿里内部用了两年的open-code-review 一条命令，扫完你 vibe coding 的所有雷 | 桌面 UA 会返回 17 KB 空壳页，必须移动端 UA——这是本表所有微信短链可核验的前提 |
| 25 | https://mp.weixin.qq.com/s/AXgQR5wxKvQXu8zpZIWUfw | curl（MicroMessenger/移动端 UA）+ `js_content` 正文提取 | HTTP 200（3,639,118 B），正文提取成功，全文 9,016 字符 | SDD工程化落地：双环驱动开发流程 | 桌面 UA 会返回 17 KB 空壳页，必须移动端 UA——这是本表所有微信短链可核验的前提 |
| 26 | https://mp.weixin.qq.com/s/ESWOKhUzBSJWutPqLSMdiA | curl（MicroMessenger/移动端 UA）+ `js_content` 正文提取 | HTTP 200（3,735,036 B），正文提取成功，全文 18,335 字符 | Harness AI Coding工程化实践：如何将不同项目的代码一致性提升至 96% | 桌面 UA 会返回 17 KB 空壳页，必须移动端 UA——这是本表所有微信短链可核验的前提 |
| 27 | https://mp.weixin.qq.com/s/begqTCRK-6xA9dTJgLr_og | curl（MicroMessenger/移动端 UA）+ `js_content` 正文提取 | HTTP 200（3,566,830 B），正文提取成功，全文 3,011 字符 | 【AI-Native 研发踩坑·下】Harness 会过期：AI 编程的方法论也在迭代 | 桌面 UA 会返回 17 KB 空壳页，必须移动端 UA——这是本表所有微信短链可核验的前提 |
| 28 | https://mp.weixin.qq.com/s/txxB1aaO_nFbQ52r3oqaxw | curl（MicroMessenger/移动端 UA）+ `js_content` 正文提取 | HTTP 200（3,556,735 B），正文提取成功，全文 4,924 字符 | 玩转 AI Coding：一份面向团队的 Harness Engineering 实践指南 | 桌面 UA 会返回 17 KB 空壳页，必须移动端 UA——这是本表所有微信短链可核验的前提 |
| 29 | https://mp.weixin.qq.com/s/Psm4zIMJcbj95-alf2-4VQ | curl（MicroMessenger/移动端 UA）+ `js_content` 正文提取 | HTTP 200（3,474,751 B），正文提取成功，全文 4,627 字符 | AI Coding 时代真正重要的是软件工程判断力 | 桌面 UA 会返回 17 KB 空壳页，必须移动端 UA——这是本表所有微信短链可核验的前提 |
| 30 | https://mp.weixin.qq.com/s/ZjnmJYWoRmL7vdYFLq6cUA | curl（MicroMessenger/移动端 UA）+ `js_content` 正文提取 | HTTP 200（3,827,662 B），正文提取成功，全文 14,500 字符 | 《驾驭 AI Coding：一份面向团队的 Harness Engineering 落地规范》详细解读 | 桌面 UA 会返回 17 KB 空壳页，必须移动端 UA——这是本表所有微信短链可核验的前提 |
| 31 | https://mp.weixin.qq.com/s/tSmMdSSzLgTsAX1JUaZI9Q | curl（MicroMessenger/移动端 UA）+ `js_content` 正文提取 | HTTP 200（3,954,522 B），正文提取成功，全文 29,082 字符 | 两万字长文｜手把手带你趟过 AI Coding 深水区：编码让位，人退到哪里 | 桌面 UA 会返回 17 KB 空壳页，必须移动端 UA——这是本表所有微信短链可核验的前提 |
| 32 | https://mp.weixin.qq.com/s/1fbIwI5omis0lQ9GFKhl2Q | curl（MicroMessenger/移动端 UA）+ `js_content` 正文提取 | HTTP 200（3,628,342 B），正文提取成功，全文 4,435 字符 | 在 GOPS 讲完“一人 + AI Agent 军团”，我更确定：Agent 进生产，关键不在模型，而在 Harness | 桌面 UA 会返回 17 KB 空壳页，必须移动端 UA——这是本表所有微信短链可核验的前提 |
| 33 | https://mp.weixin.qq.com/s/g4nTfxm7ebzRwkAVIGdIbg | curl（MicroMessenger/移动端 UA）+ `js_content` 正文提取 | HTTP 200（5,449,241 B），正文提取成功，全文 25,087 字符 | 驾驭AI Coding：一份面向团队的Harness Engineering落地规范 | 桌面 UA 会返回 17 KB 空壳页，必须移动端 UA——这是本表所有微信短链可核验的前提 |
| 34 | https://mp.weixin.qq.com/s/UE-RZH9hnbBd06CVapFGrA | curl（MicroMessenger/移动端 UA）+ `js_content` 正文提取 | HTTP 200（4,017,652 B），正文提取成功，全文 15,062 字符 | 从AI Coding到Harness Engineering的端到端工程开发实践 | 桌面 UA 会返回 17 KB 空壳页，必须移动端 UA——这是本表所有微信短链可核验的前提 |
| 35 | https://mp.weixin.qq.com/s/rlIyIIZOXFObNIXbPI7gDg | curl（MicroMessenger/移动端 UA）+ `js_content` 正文提取 | HTTP 200（3,972,781 B），正文提取成功，全文 14,841 字符 | Harness Engineering：耗时一周，我是如何将应用的AI Coding率提升至90%的 | 桌面 UA 会返回 17 KB 空壳页，必须移动端 UA——这是本表所有微信短链可核验的前提 |
| 36 | https://mp.weixin.qq.com/s?__biz=MzIwNDY3MDg1OA==&mid=2247495595&idx=1&sn=ebe7d9e43744de542a47b1a97f471427&chksm=96fffb5b20d16bd53da410ef8c219a17dd470bcb23f9870e3e2f713159817147a038c00b1720#rd | curl（MicroMessenger UA）+ `js_content` 正文提取 + `author` meta 读取 | HTTP 200（3,791,677 B），正文提取成功，全文 8,177 字符（去空白口径，与本表其余微信行一致；含空白为 9,153 字符） | 多 AI Coding Agent 工程化实践：用 CLAUDE.md + AGENTS.md 建立统一工程约束 | a04 · 左泽位《多 AI Coding Agent 工程化实践：用 CLAUDE.md + AGENTS.md 建立统一工程约束》。**此前被误判为反爬拦截，真因是 URL 缺 `&chksm=` 校验参数被截断**（截断版返回 17,694 B 空壳、无 `js_content`）；补全后 L1 全文核验通过 |
| 37 | https://github.com/Skyvern-AI/skyvern | GitHub API `stargazers_count`（2026-09-14T14:43:08Z）+ 仓库页 curl | HTTP 200（621,631 B）；22,996 ⭐ | GitHub - Skyvern-AI/skyvern: Automate browser based workflows with AI | 块 DAG / 参数系统 / Copilot completion_contract 的直接来源。本地 clone：`references/skyvern` commit `35cb497c99dc940472023e682692613e1014e51f`；docs/12 另记 `.git` 克隆地址 |
| 38 | https://github.com/lichong-a/ric-dev-workflow-skills | GitHub API `stargazers_count`（2026-09-13T16:29:27Z）+ 仓库页 curl | HTTP 200（403,018 B）；2 ⭐ | GitHub - lichong-a/ric-dev-workflow-skills: 面向 多种 Agent 的四角色 DevFlow Skills：Brownfield 接管、证据门禁、独立审核测试与高效交接。长程任务首选！ | 四角色所有权矩阵 / G0–G10 门禁 / Compact 证据容器的直接来源。本地 clone：`references/ric-dev-workflow-skills` commit `84954fbda3c1d8c47ef2a5ee9fb43e18ab4a3c4a`，96 文件；docs/12 另记 `.git` 克隆地址 |
| 39 | https://github.com/awslabs/aidlc-workflows | GitHub API `stargazers_count`（2026-09-14T14:49:27Z）+ 仓库页 curl | HTTP 200（376,865 B）；4,598 ⭐ | GitHub - awslabs/aidlc-workflows: AI-Driven Life Cycle (AI-DLC) adaptive workflow steering rules for AI coding agents | a21 · AI-DLC 多宿主适配 + approval gate + 自动工作流选择。docs/20 §二 深度分析 |
| 40 | https://github.com/langflow-ai/langflow | GitHub API `stargazers_count`（2026-09-14T13:42:57Z）+ 仓库页 curl | HTTP 200（402,791 B）；154,789 ⭐ | GitHub - langflow-ai/langflow: Langflow is a powerful tool for building and deploying AI-powered agents and workflows. | a22 · 可视化 Agent 编排、块类型目录。docs/20 §二 深度分析 |
| 41 | https://github.com/fengshao1227/ccg-workflow | GitHub API `stargazers_count`（2026-09-03T03:31:56Z）+ 仓库页 curl | HTTP 200（440,315 B）；5,884 ⭐ | GitHub - fengshao1227/ccg-workflow: 多模型协作工作流引擎 — /ccg:go 一个命令，AI 自动分析意图、选择策略、编排 Codex + Gemini + Claude 协作执行 | a23 · 多模型协作策略路由 `/ccg:go`。docs/20 §二 深度分析 |
| 42 | https://github.com/nicepkg/ai-workflow | GitHub API `stargazers_count`（2026-01-20T08:50:30Z）+ 仓库页 curl | HTTP 200（397,525 B）；283 ⭐ | GitHub - nicepkg/ai-workflow: 🚀 170+ pre-built skills for Claude Code, Cursor, Codex & 14+ AI tools. Stop re-teaching your AI the same things. One command → instant domain expertise. Marketing, SEO, Trading, Video, PM workflows included. | a24 · 170+ 预构建 Skill、多领域分类、标签词典参考。docs/20 §二 深度分析 |
| 43 | https://github.com/bmad-code-org/BMAD-METHOD | GitHub API `stargazers_count`（2026-09-14T11:16:09Z）+ 仓库页 curl | HTTP 200（361,830 B）；52,999 ⭐ | GitHub - bmad-code-org/BMAD-METHOD: Breakthrough Method for Agile Ai Driven Development | a25 · 敏捷 AI 驱动开发、Task Dependency Graph。docs/21 §a25 |
| 44 | https://github.com/modu-ai/moai-adk | GitHub API `stargazers_count`（2026-09-14T13:23:37Z）+ 仓库页 curl | HTTP 200（713,465 B）；1,211 ⭐ | GitHub - modu-ai/moai-adk: Agentic development harness for Claude Code — SPEC-driven plan/run/sync, TRUST 5 quality gates, model+effort routing, and Claude×GLM multi-LLM cost control. Single Go binary, 16 languages, zero deps. | a26 · TRUST 5 质量门 / Kanban·Factory Mode / No False Verification。docs/21 §a26 |
| 45 | https://github.com/NeoLabHQ/context-engineering-kit | GitHub API `stargazers_count`（2026-08-26T21:08:01Z）+ 仓库页 curl | HTTP 200（490,190 B）；1,694 ⭐ | GitHub - NeoLabHQ/context-engineering-kit: Hand-crafted Claude Code Skills focused on improving agent results quality. Compatible with OpenCode, Cursor, Antigravity, Gemini CLI, and others. Includes CodeRabbit open-source alternative. | a27 · 上下文工程工具包、Skill 即上下文净化器。docs/21 §a27 |
| 46 | https://github.com/Windy3f3f3f3f/how-claude-code-works | GitHub API `stargazers_count`（2026-08-17T08:27:42Z）+ 仓库页 curl | HTTP 200（369,864 B）；3,626 ⭐ | GitHub - Windy3f3f3f3f/how-claude-code-works: Deep dive into Claude Code internals — architecture, agent loop, context engineering, and more. / 深入解析 Claude Code 源码：架构、Agent 循环、上下文工程、工具系统等 | a28 · Claude Code 内部机制（Agent Loop / 上下文 / 工具系统）。docs/21 §a28 |
| 47 | https://github.com/gmickel/flow-next | GitHub API `stargazers_count`（2026-09-14T12:40:40Z）+ 仓库页 curl | HTTP 200（443,106 B）；696 ⭐ | GitHub - gmickel/flow-next: Repeatable agentic engineering. The workflow layer that turns AI coding agents into a disciplined factory: durable specs, fresh-context workers, adversarial cross-model reviews, receipts. Everything in your repo, zero dependencies. Claude Code · Codex · Cursor · Droid. | a29 · durable specs + fresh-context workers + 对抗式跨模型审查 + receipts。docs/21 §a29 |
| 48 | https://github.com/using-system/oddyssey | GitHub API `stargazers_count`（2026-09-14T06:27:46Z）+ 仓库页 curl | HTTP 200（409,990 B）；7 ⭐ | GitHub - using-system/oddyssey: CLI toolbox for Observability-Driven Development (ODD): coding agents observe local runs on an OpenTelemetry/Grafana stack - or remote ones on any OpenTelemetry backend - and feed the next spec-driven improvement loop. | a30 · ODD 可观测驱动开发。docs/21 §a30 |
| 49 | https://github.com/github/spec-kit.git | GitHub API `stargazers_count`（2026-09-14T14:19:34Z）+ 仓库页 curl | HTTP 200（516,903 B）；136,677 ⭐ | GitHub - github/spec-kit: 💫 Toolkit to help you get started with Spec-Driven Development | SDD 主链 Spec→Plan→Tasks→Implement 的官方工具。docs/13 / docs/14 引用；本次未 clone（clone 曾失败），只作官方文档事实引用 |
| 50 | https://github.com/ErwanLorteau/BMAD_Openclaw | GitHub API `stargazers_count`（2026-02-25T16:23:57Z）+ 仓库页 curl | HTTP 200（305,126 B）；309 ⭐ | GitHub - ErwanLorteau/BMAD_Openclaw: Bridging the BMad Method to OpenClaw — Structured AI-driven development workflows. | BMAD→OpenClaw 桥接（生态样本）。docs/21 生态清单 |
| 51 | https://github.com/alenberlin/DarkFactory-skills | GitHub API `stargazers_count`（2026-07-08T10:24:04Z）+ 仓库页 curl | HTTP 200（322,451 B）；0 ⭐ | GitHub - alenberlin/DarkFactory-skills: Senior-engineer discipline for AI coding agents — 15 skills across the full build lifecycle, 4 review personas, 6 slash commands, and an optional autonomous workflow. Apache-2.0. | 资深工程纪律型 Skill 集（生态样本）。docs/21 生态清单 |
| 52 | https://github.com/cexll/bmad-mcp-server | GitHub API `stargazers_count`（2025-10-10T02:18:35Z）+ 仓库页 curl | HTTP 200（469,560 B）；19 ⭐ | GitHub - cexll/bmad-mcp-server: Breakthrough Method for Agile Ai Driven Development MCP Server | BMAD 的 MCP Server（生态样本）。docs/21 生态清单 |
| 53 | https://github.com/shuhei0866/vdd-framework | GitHub API `stargazers_count`（2026-02-24T04:03:31Z）+ 仓库页 curl | HTTP 200（329,772 B）；3 ⭐ | GitHub - shuhei0866/vdd-framework: Vision-Driven Development / Release-Driven Development framework for AI-autonomous software development with enforced guardrails. | VDD/RDD 愿景与发布驱动开发（生态样本）。docs/21 生态清单 |
| 54 | https://github.com/skyf0xx/hedgehog | GitHub API `stargazers_count`（2026-09-14T11:14:00Z）+ 仓库页 curl | HTTP 200（412,925 B）；39 ⭐ | GitHub - skyf0xx/hedgehog: HEDGEHOG codes Cleaner, Faster and with Fewer Tokens. Hedgehog's AI-driven development builds a task dependency graph from your spec-driven, BMAD-METHOD plan, so Claude Code, Cursor & Gemini CLI stay locked to it. A CLI-enforced state machine for agentic coding. Now builds DeepSeek DSH Plugins. DeepSeek Harness、DSH 插件、AI 编程、BMAD 方法. AI Copywriting | 基于 BMAD 的 CLI 强制状态机（生态样本）。docs/21 生态清单 |
| 55 | https://github.com/vasilyu1983/AI-Agents-public/blob/main/frameworks/shared-skills/skills/docs-ai-prd/references/spec-driven-dev-landscape.md | GitHub API `stargazers_count`（2026-09-02T05:50:47Z）+ 仓库页 curl | HTTP 200（276,040 B）；87 ⭐ | AI-Agents-public/frameworks/shared-skills/skills/docs-ai-prd/references/spec-driven-dev-landscape.md at main · vasilyu1983/AI-Agents-public | SDD 生态全景综述（Kiro 等企业落地事实来源）。docs/14 表格 #7 引用 |
| 56 | https://addyosmani.com/blog/ai-coding-workflow/ | curl（桌面 UA） | HTTP 200（216,565 B），可访问 | My LLM coding workflow going into 2026 \| AddyOsmani.com | Addy Osmani · My LLM coding workflow going into 2026：specs before code / 小步迭代 / 真人验证与评审 / 测试是安全网 |
| 57 | https://www.anthropic.com/research/long-running-Claude | curl（桌面 UA） | HTTP 200（190,043 B），可访问 | Long-running Claude for scientific computing | Anthropic · Long-running Claude for scientific computing：CLAUDE.md 承载计划、CHANGELOG 当长期记忆、测试 oracle、每步 commit、Ralph loop 防伪完成 |
| 58 | https://www.anthropic.com/webinars/claude-code-advanced-patterns | curl（桌面 UA） | HTTP 200（106,059 B），可访问 | Claude Code Advanced Patterns: Subagents, MCP, and Scaling to Real Codebases \| Webinars \ Anthropic | Anthropic · Claude Code Advanced Patterns：subagents + hooks 编排、MCP、大仓库 CLAUDE.md 结构、CI 自动 review |
| 59 | https://code.claude.com/docs/en/workflows | curl（桌面 UA） | HTTP 200（639,699 B），可访问 | Orchestrate subagents at scale with dynamic workflows - Claude Code Docs | Claude Code 官方文档 · Orchestrate subagents at scale with dynamic workflows |
| 60 | https://github.github.com/spec-kit/ | curl（桌面 UA） | HTTP 200（10,803 B），可访问 | GitHub Spec Kit \| Spec Kit Documentation | GitHub Spec Kit 官方文档站（SDD 主链、building blocks、集成数量） |
| 61 | https://github.com/github/spec-kit/blob/197dde62/docs/reference/agentic-sdd.md?plain=1#1 | curl（桌面 UA） | HTTP 200（325,586 B），可访问 | spec-kit/docs/reference/agentic-sdd.md at 197dde62534480693e50d9cd6d1f6083c19f2c15 · github/spec-kit | spec-kit `docs/reference/agentic-sdd.md` @ commit `197dde62534480693e50d9cd6d1f6083c19f2c15`：constitution→specify→clarify→plan→checklist→tasks→analyze→implement→converge |
| 62 | https://www.skyvern.com/docs/developers/getting-started/core-concepts | curl（桌面 UA） | HTTP 200（602,855 B），可访问 | Core Concepts - Skyvern | Skyvern 官方文档 · Core Concepts（block / parameter / run 生命周期），与本地 clone 互相印证 |
| 63 | https://developers.openai.com/blog/skills-shell-tips | curl × 4 种 UA（桌面 / 移动 / bingbot / googlebot）+ `/blog/` 首页 + `openai.com/index/skills-shell-tips` 回退 | ❌ **本环境不可达**：全部 HTTP 403（59 B，响应体只有「403: Forbidden」） | 403: Forbidden（无正文） | 结论是**出口 IP 区域封锁**，不是链接失效（`/blog/` 首页同样 403，`openai.com/index/...` 回退路径为 404/403）。保留原 URL 以便读者在可访问网络下自行打开；`docs/14` 表格 #3 的四条论点改由**可达中文二手来源**支撑：虎嗅《OpenAI 也来教你怎么写 Skills，我建议你看一下》 https://www.huxiu.com/article/4834939.html （curl HTTP 200，99,991 B，2026-02-13，作者署名「思考机器/陆三金」，逐条覆盖 description 当路由逻辑写、Glean 负面例子使触发率降 20%、模板塞进 Skill 几乎免费） |
| 64 | https://www.51cto.com/article/852090.html | curl（桌面 UA） | ❌ **HTTP 200 但只有 985 B 的 JS 反爬挑战页**（脚本内含 `EO_Bot_Ssid` cookie 计算，无 `<title>`、无正文） | （无标题，正文未取到） | 因此**不能**把 51CTO 当作 a18 的可用镜像；README 正文里凡引用它处均已标注「JS 反爬，本环境不可取正文」。同文的可达版本：微信原文 row 20（L1 全文）与 hongtao2agent.xyz row 13（L1 全文） |
| 65 | https://mp.weixin.qq.com/s/fV8qN6qs9ac-VXDwZCuaxA | webReader 全文抓取（2026-09-20） | L1 全文约 1.2 万字，无截断 | 删掉80%的Prompt规则，Agent交付成功率反而更高了 | a37 / 附录 086；对照扫描 docs/32：三支柱与三层模型同构，Add/Thin 两缺口已落地 v1.8.1 |
| 66 | https://github.com/affaan-m/ECC | GitHub 周榜页 webReader 直抓（2026-09-20） | 周榜快照可访问；star 262,961、+6,265/周 | affaan-m/ECC · agent harness 性能优化系统 | 附录 087；docs/34 §二；star 为周榜快照值（L1 榜单页），未单独走 API 复核 |
| 67 | https://github.com/stablyai/orca | 同上 | 周榜快照（72,621、+5,404/周） | stablyai/orca · 并行 agent 舰队 ADE | 附录 088；并行只在工作包层的对照样本 |
| 68 | https://github.com/anthropics/knowledge-work-plugins | 同上 | 周榜快照（25,128、+1,034/周） | Anthropic Cowork 官方插件 | 附录 089；Skill 分层加载生态印证 |
| 69 | https://github.com/ayghri/i-have-adhd | 同上 | 周榜快照（48,697、+5,589/周） | 输出纪律 Skill | 附录 090；生态样本（非规则依据） |
| 70 | https://github.com/blader/humanizer | 同上 | 周榜快照（50,255、+3,024/周） | 去 AI 味写作 Skill | 附录 091；生态样本 |
| 71 | https://github.com/Tencent/WeKnora | 同上 | 周榜快照（27,430、+4,867/周） | 知识平台/RAG | 附录 092；「不自建 RAG」既有决定的对照 |
| 72 | https://github.com/openai/plugins | 同上 | 周榜快照（7,034、+522/周） | OpenAI Plugins 官方仓库 | 附录 093 |
| 73 | https://github.com/kunchengguid/firstmate | 同上 | 周榜快照（6,734、+1,073/周） | firstmate · 多 agent 协作 | 附录 094 |
| 74 | https://github.com/max-sixty/worktrunk | 同上 | 周榜快照（8,117、+1,141/周） | 并行 agent 的 git worktree 管理 CLI | 附录 095；印证主仓 wango-delivery worktree 协议 |
| 75 | https://github.com/Panniantong/Agent-Reach | 同上 | 周榜快照（83,462、+3,914/周） | Agent web-reading CLI | 附录 096；生态样本 |
| 76 | https://github.com/xiaohuailabs/xiaohu-wechat-format | 检索快照（2026-09-20） | 仅元数据 | 公众号一键排版+发布 Skill（30 主题） | 附录 097；L3 生态样本 |
| 77 | https://github.com/anthropics/claude-code | 周榜直抓（2026-09-20） | 周榜快照（146,711、+2,000/周） | claude-code（宿主本体） | 附录 098；周榜热度样本 |
| 78 | https://support.claude.com | 检索快照（2026-09-20） | 仅元数据 | Release notes · Claude Help Center | 附录 099；L3（2026-09-01 Fable 5.1/Mythos 5.1；模型换代触发 rule-lifecycle 复检） |
| 79 | https://clockedcode.com | 检索快照（2026-09-20） | 仅元数据 | Claude Code v2.1.263 | 附录 100；L3（9/6，Sonnet 5 默认） |
| 80 | https://releasebot.io | 检索快照（2026-09-20） | 仅元数据 | Codex 2026-09 更新汇总 | 附录 101；L3（voice/live reasoning/task management/Touch-ID/daemon） |
| 81 | https://blakecrosley.com | 检索快照（2026-09-20） | 仅元数据 | Codex CLI v0.154.0 | 附录 102；L3（9/9） |
| 82 | https://developers.openai.com | 检索快照（2026-09-20） | 仅元数据；站点本环境 403 区域封锁（row 63 先例） | Agents API 公测 | 附录 103；L3（managed Codex harness） |
| 83 | https://claude.com | 检索快照（2026-09-20） | 仅元数据 | changelog | 附录 104；L3（9/8 Windows KB5124008） |
| 84 | https://github.com/SWE-bench/SWE-bench | 检索快照（2026-09-20） | 仅元数据 | SWE-bench | 附录 105；L3（Multimodal v2 9/1 全量开源，480 任务；F5 生态样本） |
| 85 | https://artificialanalysis.ai | 检索快照（2026-09-20） | 仅元数据 | Terminal-Bench 2.1 Benchmark Leaderboard | 附录 106；L3（frontier <65%；F5 生态样本） |
| 86 | https://www.tbench.ai | 检索快照（2026-09-20） | 仅元数据 | The Terminal-Bench Dataset Registry | 附录 107；L3 |
| 87 | https://arxiv.org | 检索快照（2026-09-20） | 仅元数据 | Terminal-Bench: Benchmarking Agents on Hard, Realistic Tasks | 附录 108；L3（2026-01-17 论文） |
| 88 | https://github.blog | 检索快照（2026-09-20） | 仅元数据 | Spec-driven development with AI | 附录 109；L3（2025-09-02 原始公告，本轮经 LinkedIn 帖回溯） |
| 89 | https://www.linkedin.com | 检索快照（2026-09-20） | 仅元数据（原帖 URL 在快照中截断，落站点根） | techievinayak 9/8 GitHub 活动转述帖 | 附录 110；L3 |
| 90 | https://wavect.io | 检索快照（2026-09-20） | 仅元数据 | GitHub Spec Kit Review for Production Teams | 附录 111；L3（9/2） |
| 91 | https://devops.com | 检索快照（2026-09-20） | 仅元数据 | GitHub's Spec Kit Puts the Spec Back in Software | 附录 112；L3（5/11） |
| 92 | https://codemyspec.com | 检索快照（2026-09-20） | 仅元数据 | GitHub Spec Kit: How It Works and When to Use It | 附录 113；L3（6/3，「sea-of-markdown」批评） |
| 93 | https://www.cnblogs.com | 检索快照（2026-09-20） | 仅元数据 | 博客园《给 Claude Code 装上 40 个 Skill 后》 | 附录 114；L3（9/16，3 个月实战） |
| 94 | https://www.cnblogs.com | 检索快照（2026-09-20） | 仅元数据 | 博客园《54k+Star 爆火！AI「新王者框架」Harness Agent 来了！》 | 附录 115；L3（4/12） |
| 95 | https://zhuanlan.zhihu.com | 检索快照（2026-09-20） | 仅元数据 | 知乎《国内用 Claude Code 三条路径》 | 附录 116；L3（9/9：官方订阅/API 中转/换国产模型） |
| 96 | https://zhuanlan.zhihu.com | 检索快照（2026-09-20） | 仅元数据 | 知乎《2026年AI智能体开发指南》 | 附录 117；L3 宏观样本（449 亿元、年增 107%） |
| 97 | https://developers.google.cn | 检索快照（2026-09-20） | 仅元数据 | Google Codelabs · 构建多智能体系统实验 | 附录 118；L3（9/8 更新） |
| 98 | https://www.infoq.com | 检索快照（2026-09-20） | 仅元数据 | InfoQ · LinkedIn Context Engineering（MCP 组织上下文层） | 附录 119；L3（9/19，Ajay Prakash） |
| 99 | https://yuanqi.tencent.com | 检索快照（2026-09-20） | 仅元数据 | 腾讯元器《5 分钟创建公众号智能体》 | 附录 120；L3（2/5） |
| 100 | https://blog.traversaal.ai/durable-execution-for-ai-agents | 检索快照（2026-09-20） | 仅元数据 | Durable Execution for AI Agents | 附录 121；L3（9/1；印证 F1） |
| 101 | https://www.louisbouchard.ai | 检索快照（2026-09-20） | 仅元数据 | Context Engineering in 2026: Why We Stopped | 附录 122；L3（8/18，compaction vs prompt caching；E2 触发后评估） |
| 102 | https://winder.ai | 检索快照（2026-09-20） | 仅元数据 | A Comparison of AI Agent Harnesses in 2026 | 附录 123；L3（8/20，Qwen Code harness-模型绑定） |
| 103 | https://openai.com | 检索快照（2026-09-20） | 仅元数据 | OpenAI Harness Engineering 报告 | 附录 124；L3 |
| 104 | https://mp.weixin.qq.com/s/RxRzTsRvmZJMmtQjQM79_g | webReader 全文抓取（2026-09-21） | L1 全文无截断；发布日期元数据抓取为空，不臆造 | Loop engineering：把 agent 放进工程循环 | 附录 125；对照扫描 `docs/35`：五组件印证既有设计，automations 心跳层缺口登记 `docs/13`；六动作循环与 `--advance` 同构 |
| 105 | https://addyosmani.com/blog/loop-engineering/ | curl（桌面 UA，2026-09-21） | HTTP 200（199,027 B），标题命中 | Loop Engineering \| AddyOsmani.com | 附录 126；L3 可达性级（正文未读，观点经 125 转述）；125 的主源 |
| 106 | https://martinfowler.com/articles/harness-engineering.html | curl（桌面 UA，2026-09-21） | HTTP 200（40,733 B），标题命中 | Harness engineering for coding agent users | 附录 127；L3 原始出处补录（该文中文衍生 a18=核验 row 33 与 hongtao 镜像 row 13 已双 L1 在库） |
| 107 | https://amplitude.com/blog/sweeping-logs-ralph-weng | curl ×2（2026-09-21） | 首次 000 超时；重试仅得博客通用首页标题，文章页未取到 | （文章标题未取到） | 附录 128；L3 转引（未核验）；Ralph loop 实验线索，心跳层实施时再读 |
| 108 | https://arxiv.org/abs/2605.10907 | curl（2026-09-21） | 出口 000（连接失败） | — | 附录 129；L3 转引（未核验）；AI Workflow Store（125 文内引用），生态样本/非规则依据 |
| 109 | https://arxiv.org/abs/2606.13662 | curl（2026-09-21） | 出口 000（连接失败） | — | 附录 130；L3 转引（未核验）；EurekAgent E=mc² 框架（125 文内引用），生态样本/非规则依据 |

## Harness Engineering 落地规范对照（2026-09-11）

> 原文：[驾驭AI Coding：一份面向团队的Harness Engineering落地规范](https://mp.weixin.qq.com/s/g4nTfxm7ebzRwkAVIGdIbg)
> 作者：atreusliu / 腾讯程序员 · 2026-07-17
> 镜像：[51CTO](https://www.51cto.com/article/852090.html)（JS 反爬，本环境不可取正文，见核验表 row 64）· [深度解读](https://hongtao2agent.xyz/html/team-harness-engineering/)（L1 全文）
> 核心论点："交付代码的成本已经接近免费了，但交付好代码的成本依然很高。"

### 文章六大支柱 vs 本工作流三层模型

| 文章六支柱 | 控制问题 | 本工作流对应 | 覆盖状态 |
|---|---|---|---|
| 看什么（上下文） | 信息输入 | AGENTS.md 索引 + 35 篇 docs + 渐进式披露 | ✅ 已覆盖 |
| 能触达什么（工具） | 能力面 | MCP / Skills / 知识库（WanGo 层 connector + skill） | ✅ 已覆盖 |
| 按什么顺序（编排） | 执行顺序 | 块 DAG + G0–G10 门禁 + 四角色交接 | ✅ 已覆盖且更深 |
| 记住什么（记忆） | 状态持久化 | `state.yaml` + `current.md` + `evidence.md` 只追加账本 | ✅ 已覆盖 |
| 如何证明（评估） | 验证 | G5 代码审核 → G6 集成 → G7 完整验证 → G8 发布 | ✅ 已覆盖 |
| 如何止损（护栏） | 恢复 | Rules / Safety / Git 回滚 / WanGo 交付协议切分门禁 | ✅ 已覆盖 |

### 已成立的设计（不需要改）

| 现有设计 | 文章印证 | 结论 |
|---|---|---|
| 先 Spec 后 Plan 再实现 | Spec Kit 主链、Addy Osmani、Kiro 均一致 | 保留 |
| Planner 唯一写状态、Reviewer 只读 | Anthropic subagent 编排、Claude Code 独立 reviewer | 保留 |
| 小任务包、单块实现 | Addy Osmani 小步迭代、Anthropic 长任务拆解 | 保留 |
| Tester 独立验证、测试为安全网 | Addy Osmani、Anthropic test oracle | 保留 |
| 证据文件 + SHA 绑定 | Anthropic CHANGELOG、每步 commit | 保留 |
| 人工边界 `*` 不得代签 | Addy Osmani 人始终验证 | 保留 |
| Instruction-only，无重型运行时 | Spec Kit 也可 step-by-step；本地文件足够 | 保留 |
| scripts 只做确定性校验 | OpenAI scripts 只放确定性逻辑 | 保留 |
| 块 DAG 编译器 + 确定性验证器 | 文章未涉及此深度 | 本工作流更深 |
| G0–G10 完整门禁链 | 文章只提"阶段产物门" | 本工作流更深 |


### 风险分层门禁（吸收自 Harness Engineering 批判性校准 #2）

> atreusliu「驾驭AI Coding」+"先 Spec 后 Code"红线允许半天内需求直接 Agent 模式的内部冲突→**批判性校准建议：按风险、可逆性、跨模块影响、数据权限与验收难度分流，不按时间长短分流**。

| 维度 | 低风险 | 中风险 | 高风险 |
|---|---|---|---|
| 可逆性 | 单文件、git revert | 多文件、手动回滚 | 数据库迁移、共享契约 |
| 爆炸半径 | 单页面/组件 | 多页面同模块 | 跨模块、公共组件、API 契约 |
| 数据/权限 | 无变更 | 新增字段/权限 | 数据迁移、权限模型变更 |
| 验收难度 | 单页面、单视口 | 多页面、集成环境 | 跨服务、多租户、真实数据 |
| 流程 | FAST | STANDARD | STRICT |

硬规则：任一维度触及"高风险"→必须走 STRICT；不可逆操作→额外安全审查；不得因"改动小"自动降级。详见 `skills/_shared/contracts/gate-policy.md`。

### 六问框架：每接入一个 Agent 场景都必须回答（吸收自 Harness Engineering 六支柱）

| # | 控制问题 | 本工作流对应 |
|---|---|---|
| 1 | 看什么？（信息输入） | Intake（G0）+ Recon（G1）+ `current.md` |
| 2 | 能触达什么？（工具系统） | MCP/Skills + scripts/ 确定性校验 |
| 3 | 按什么顺序？（执行编排） | 块 DAG + G0–G10 门禁 + 四角色交接 |
| 4 | 记住什么？（状态记忆） | `state.yaml` + `current.md` + `evidence.md` 只追加账本 |
| 5 | 如何证明？（评估观测） | 六层验证（L1–L6）+ SHA 绑定 |
| 6 | 如何止损？（约束恢复） | `docs/07` 失败分类 + `finally` + `max_attempts` + 熔断 |

G2 Spec 阶段必须逐条回答六问，任一项未明确→Spec 不通过。模板已更新到 `skills/_shared/templates/current.md`。


### 真实差距（文章指出但本工作流尚未解决）

| # | 文章批评 | 本工作流现状 | 严重度 | 行动 |
|---|---|---|---|---|
| 1 | 规范存在 ≠ 行为有效——Rules 需下沉到 Hook/CI 确定性执行 | **本地已闭环（v1.4.0 / v1.4.1）**：`selftest.sh` 50 项把包结构、docs 索引完整性、`runs/` 容器一致性、工作流正反例、DAG 编译、run_flow 行为、版本锁定、**7 条硬护栏逐条开火**、**闸门安装状态可证明**全部变成可执行断言；并由 `install_hooks.py` 装成 pre-commit 阻断级闸门（端到端实测：破坏被拦、修复后放行）。仍缺 CI 侧第二次挂载——`--no-verify` 与换机器是两个真实绕过口 | 🟢 低（本地）/ 🟡 中（团队） | 下一步：CI job 跑 `selftest.sh` + `install_hooks.py --check`，失败即阻断合并 |
| 2 | 同步脚本制造不可复现漂移——团队 Harness 需版本锁定 | **已完成（v1.2.1）**：`VERSION` 单一事实源 + 安装收据 `aiworflow-install-receipt.json`（来源根/版本/模式/逐文件 SHA256）+ `--check` 漂移检测 + `--upgrade` 原子替换与失败回滚 + `--apply` 认领已装好但无收据的环境；selftest §8 九项断言覆盖 | 🟢 已解决 | 无 |
| 3 | 评估偏传统工程检查——缺行为评测 | `validate_run.py` 只查结构/SHA/引用可达，不做语义判断（有意留给 Reviewer） | 🟢 低 | 设计决策，不是遗漏 |
| 4 | 安全边界偏 Prompt 化——缺 sandbox、细粒度权限 | 依赖宿主 sandbox（Codex 有沙箱），工作流本身没有独立策略层 | 🟢 低 | 宿主已覆盖 |
| 5 | 合规评分偏"文件完备度"——应改为结果指标 | 没有审计评分系统（这反而是优势——不诱发刷分） | 🟢 低 | 不需要做 |
| 6 | 自动恢复仍是愿景——缺 checkpoint/重试上限/工作区隔离 | **重试上限已落地**（author-time `max_attempts ≤ 5` 护栏 `unbounded_retry` + 运行期 `run_flow.py` 拒绝超限重试）；仍缺 checkpoint、工作区隔离与回滚失败分支 | 🟡 中 | 出现真实案例时补 checkpoint / 工作区隔离 |
| 7 | "先 Spec 后 Code"存在内部冲突——Risk-based gating 允许直接 Agent 模式 | WanGo 交付协议有切分门禁（15 文件/1500 行/80KB） | 🟢 低 | 由 WanGo 协议覆盖 |

### 最值得吸收的 5 个想法

1. **六问框架做架构评审模板**：每接入一个 Agent 场景，都回答：信息、权限、顺序、状态、证据、恢复。`docs/02-block-catalog.md` 可加检查清单。
2. **失败尝试必须入账**：`current.md` 应有固定字段记录失败路径；同一死路跨会话不得重试。
3. **关键规范绑定 Hook/CI**：至少把 G5 代码审核的"SHA 绑定"和"证据引用可达"做成 git hook 或 CI check。
4. **版本化分发**（✅ 已落地 v1.2.0，v1.2.1 补认领路径）：`install_skills.py` 记录来源版本与逐文件 SHA256，`--check` 回答「目标装的是哪版、有没有被手改」，`--upgrade` 走原子替换；包通过安装收据（）记录版本与文件指纹，可直接分发。
5. **行为评测 > 文件完备度**：每次真实 run 后补一条"可观察决策"用例到 evals 库。

### 一句话总评

> 本工作流的三层模型（Flow/Role/Evidence）已覆盖 Harness Engineering 六支柱 80% 的核心建议，且在块 DAG 编译器、G0–G10 门禁链和确定性验证器方面更深。文章的最大价值是指出"配置存在 ≠ 行为有效"——v1.4.0/v1.4.1 已通过本地 pre-commit hook + selftest 50 项闭环本地侧；CI 侧第二次挂载见 roadmap。

## GoPS 生产 Harness 对照（2026-09-11）

> 原文：[模型给能力，Harness 给责任边界｜Agent 进生产](https://hongtao2agent.xyz/html/gops-agent-production-harness/)
> 作者：AI运维实验室 · 第 19 篇 · 2026-07-12（深度解读 2026-08-04）
> 同系列团队篇：[把"好代码"写进系统：团队 Harness Engineering](https://hongtao2agent.xyz/html/team-harness-engineering/)
> 核心命题："Agent 可以替你干活，但不会替你承担生产责任。"模型决定一次任务"可能做到多好"，Harness 决定它"被允许做什么、依据什么做、做完如何证明、失败怎样退出、经验能否留下"。

### 责任状态机（OPC 闭环六段）vs 本工作流

| GoPS 闭环段 | 它承担的责任 | 本工作流对应 | 覆盖 |
|---|---|---|---|
| ① Input 业务问题 | 落在明确场景，不泛化 | G0 Intake：用户/场景/目标/非目标/验收方式/授权边界 | ✅ |
| ② Grounding 事实与证据 | 读权威来源、历史判断、当前基线 | Evidence 层 `state.yaml`/`current.md`/`evidence.md` 只追加账本 + SHA 绑定 | ✅ |
| ③ Prepare 判断与准备 | 命令/Diff/风险/验证/回滚方案 | Spec(G2) + Plan/G4 冻结 DAG + 变更预算 + `test-plan.md` | ✅ |
| ④ Gate 人工确认 | 高风险动作授权前不得执行 | `*` 标记节点必须人工确认、不得代签（G3 等） | ✅ |
| ⑤ Act 执行与验证 | 单步执行 + 查询 + 冒烟 + 必要时回滚 | Implementer 单块实现 + G6 集成/G7 完整验证 + `finally`/回滚 | ✅ |
| ⑥ Learn 结果写回 | 沉淀到 Incident/Wiki/Skill | 第 13 步 关闭与复盘 → `lessons`/`change-summary`（G10 `close`+`notify`） | ✅ |

### 五条边界（文章"明天只做三步"之 Step 02）

| 边界 | 本工作流的回答 | 位置 |
|---|---|---|
| 事实源在哪 | 版本化工件是唯一事实源，聊天不是；规则只在唯一位置维护 | `docs/05`、`docs/README` |
| 能做什么 | 四角色所有权矩阵 + 状态相关权限裁剪 + Git 策略（破坏性操作需单独授权） | `docs/04`、`_shared/contracts/git-policy.md` |
| 何时必须找人 | `*` 人工/授权边界 + 门禁不得由模型代签 | `docs/00`、`docs/03` |
| 怎样证明成功 | `completion_contract` 逐条判定 + Verdict 绑定 SHA/命令输出；无证据不得 `APPROVE`/`DONE` | `docs/03`、§不可妥协的边界 |
| 结果写回哪 | 关闭复盘写 `lessons`/`change-summary`，证据进只追加账本 | `docs/00` 第 13 步、`docs/05` |

### 已成立 / 更深（不需要改）

- **上下文连续性 > 工具特长**：Planner 是唯一全局状态写入者、单层调度、主线对所有权——与文章"指定一个主线 Agent 对上下文负责到底，其他工具只做入口或补位"同向。
- **护栏分层 Prompt→Skill→Hook→Permission**：四层已落地三层——Prompt 层（`prompts/` 模板 + `docs/06` 参数规则）、Skill 层（`skills/` 四角色所有权 + `docs/09` 禁止"改完直接对生产执行"）、**Hook 层（v1.4.0：`install_hooks.py` 装 pre-commit，`selftest.sh` 50 项失败即拒绝提交，§9 逐条证明 7 条 author-time 硬护栏真的会开火）**。仅剩 Permission 层依赖宿主沙箱（本包不自建独立权限层，属 `docs/13-roadmap` 团队化议题）。
- **十步变更链的"准备→授权→执行→验证→写回"**：与 G0–G10 门禁链一一对应，且本工作流把"授权"显式建为 `*` 不可代签节点。

### 真实差距（文章指出，本工作流尚未解决）

| # | 文章原则 | 本工作流现状 | 严重度 | 行动 |
|---|---|---|---|---|
| 1 | 护栏要下沉到运行期 Hook/Permission（系统不允许，而非请不要） | author-time 有静态护栏 + 确定性 selftest + **v1.6.0 自动化推进闭环**（loop_control 信号 + 熔断规则）；仍缺 CI 侧第二次挂载 + 独立权限层 | 🟡 中 | `docs/13-roadmap` 已登记：把 `selftest.sh` 挂 CI，失败即阻断；Permission 层依赖宿主沙箱，团队化时补齐 |
| 2 | 验证须区分 成功/失败/**未知**，未知不得自动视为成功 | Verdict 三值（APPROVE/REQUEST_CHANGES/BLOCKED）+ G10 要求"所有证据当前有效"，**隐式**排除未验证；但未把"验证结果未知"显式建为独立状态 | 🟢 低 | 可在 `test-report.yaml` 模板显式加 `UNKNOWN` 判定，杜绝"没测=通过" |
| 3 | 失败分支工程细节（确认超时/部分成功/回滚失败/并发冲突/幂等） | `docs/07` 有失败分类 + 错误码白名单 + 有界重试（两层强制）+ `finally` + 熔断；仍缺工作区隔离、回滚失败分支与幂等键 | 🟡 中 | 与团队篇差距 #6 同源，出现真实案例时补 |
| 4 | L5 团队平台：可复用/可评审/可度量/可发布 | 已有版本化分发（v1.2.0 起的收据机制，当前 v1.5.0：逐文件 SHA256 + 原子升级 + 认领已装环境 + 拒绝部分安装）；缺度量指标与发布节奏 | 🟢 低 | 单人阶段不紧急，团队化时补 |

### 一句话总评

> GoPS 篇把"人机协作"落到一台责任状态机（事实→准备→授权→执行→验证→写回）。本工作流的 G0–G10 门禁 + 四角色所有权 + Evidence 只追加账本，就是这条责任链的研发版。v1.7.3 新增 BMAD/MoAI-ADK/CEK/flow-next/oddyssey 等前沿范式全景扫描，将 No False Verification、TRUST 5 五维门、对抗式审查、ODD 可观测驱动、Task Dependency Graph 自动生成纳入吸收清单。
