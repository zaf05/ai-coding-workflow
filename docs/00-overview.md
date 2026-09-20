# 00 · 全流程总览

## 一句话

AIWorflow 是一个**本地 AI 研发控制层**：人负责意图、授权和产品判断，AI 负责执行、验证、记录和复查。目标不是让模型更快写代码，而是让每一次开发都留下可追溯的 scope、evidence、review、claim 和 blocker。

## 主流程（13 段）

段落编号沿用我 V4.0 的讲法，便于对照；每段右侧是它在块 DAG 里的 `block_type` 与门禁。

| # | 阶段 | 干什么 | block_type | 门禁 | 角色 |
|---|---|---|---|---|---|
| 1 | 需求澄清 | 固定用户、场景、目标、非目标、验收方式；对敏感域、真实 mutation、账号/session、外部系统做授权判断 `*` | `intake` | G0 | Planner |
| 2 | 仓库侦察 | 建立仓库画像、当前 ref/完整 SHA、工作区脏状态、既有流程与工具链事实 | `recon` | G1 | Planner |
| 3 | Spec | 写出行为规格、验收标准（AC）、UI/技术决策、变更预算 | `spec` | G2 | Planner → Reviewer |
| 4 | 任务 DAG | 拆工作包/块，标依赖、所有权、并行边界；首次通过 G2 后**冻结** | `plan` | G2 | Planner |
| 5 | 用户批准 `*` | 产品行为与重要取舍由人批准，绑定 Spec 版本 | `approve` | G3 | 用户 |
| 6 | 测试计划 | Oracle、用例、环境、数据、视口矩阵；独立审核 | `plan` | G4 | Tester → Reviewer |
| 7 | 实现 | 单块实现：契约与不变量优先，再主行为，再错误/边界/资源生命周期 | `implement` | — | Implementer |
| 8 | 确定性检查 | 该块负责的单元/组件测试、lint、type-check、构建；记录精确命令与退出码 | `check` | G5 前置 | Implementer |
| 9 | 独立审核 | 只读审核 `base_sha..head_sha`，产出稳定 Finding ID 与 Verdict | `review` | G5 | Reviewer |
| 10 | 集成与增量测试 | 按 DAG 顺序合入集成分支，跑增量测试 | `integrate` + `test` | G6 | Planner + Tester |
| 11 | 完整验证 | 所有块验证后跑完整测试、页面真实浏览器与视口检查、diff 驱动 QA | `test` + `verify_ui` | G7 | Tester |
| 12 | 发布审核与合并 | 迁移/配置/回滚/文档齐备后发布审核；合入目标分支 `*`；目标 SHA 冒烟 | `release_check` + `smoke` | G8 / G9 | Reviewer + Tester |
| 13 | 关闭与复盘 | 完成度按 `completion_contract` 逐条判定；更新 change-summary / lessons | `close` + `notify` | G10 | Planner |

失败不终结流程：任何块失败进入 `07-failure-and-recovery.md` 的归因路径（bug intake / 返修 / `BLOCKED`），`finally_block_label` 负责收尾与清理。

## `*` 边界（人工判断、授权、外部平台）

沿用 V4.0 的星号约定：带 `*` 的节点是自动化边界，AI 不得代签。

- **人工判断 `*`**：Product Brief Gate、Spec 取舍批准、风险接受（仅 P2）、发布决策。
- **授权与凭据 `*`**：真实账号/session 登录、生产或外部系统写操作、付费操作、凭据访问、push/部署/改远端。
- **外部平台 `*`**：CI、PR、部署、监控、第三方评审平台、真实 live target。
- **自动化边界 `*`**：多 Agent 调度、worktree 隔离、run lease/freshness、hook 强制。

工作流定义里用 `star: true` 标记块；`scripts/validate_workflow.py` 会检查 G3/G8 等必须人工的门禁是否确实标了星号。

## 相比 V4.0（schema 18）的变化

| 维度 | V4.0 | AIWorflow v1.0 | 来源 |
|---|---|---|---|
| 流程表达 | 文字段落 + contracts 名 | 可校验的块 DAG（`workflows/*.yaml`） | Skyvern `WorkflowDefinition` |
| 节点身份 | 无 | `label` 唯一 + `next_block_label` 显式连边 | Skyvern block graph |
| 失败处理 | bug intake 分类 | 分类 + `error_code_mapping` 白名单 + `continue_on_failure` + `finally` + 有界重试 | Skyvern + DevFlow |
| 角色 | controller / worker / reviewer / remediation | Planner / Implementer / Reviewer / Tester 四角色 + 唯一状态写入者 | DevFlow |
| 门禁 | gates 字段 | G0–G10 + 适用性省略规则（不递归套门禁） | DevFlow |
| 证据 | `.ai-native/runs/<run-id>/state.json` | Compact 四文件容器（state/current/test-plan/evidence）+ 只追加账本 | DevFlow Compact v2 |
| 完成声明 | completion_claim 枚举 | `completion_contract` 逐条判定 + 禁止模糊声明清单 | Skyvern Copilot |
| 提速 | 无 | agent → script 渐进确定性 + `run_signature` 缓存 | Skyvern script generation |
| Prompt | 无规范 | 模板 static/dynamic 分段 + 秘密脱敏 | Skyvern prompt templates |
| 校验 | `validate_plan.py` / `validate_run.py`（外部） | 自带 `scripts/validate_workflow.py`、`validate_run.py`、`validate_package.py`、`selftest.sh`（标准库，可离线跑） | 本工作流新增 |
| 仓库适配 | 通用 | 显式 WanGo 适配层与冲突优先级 | `10-wango-adapter.md` |

保留不变的 V4.0 内核：人管意图与授权、AI 管执行与记录；证据先于状态；`*` 边界；不许用"主体完成"表示业务完成。

## 讲解路径

先讲需求入口为什么要收敛（第 1–2 段），再讲 Spec 与 DAG 如何把大需求变成可执行块（第 3–6 段），然后讲四角色与门禁如何防止"自己批准自己"（第 7–10 段），最后用完成度契约与 bug intake 说明兜底责任如何从用户转回工程系统（第 11–13 段）。
