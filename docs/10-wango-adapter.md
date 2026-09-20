# 10 · WanGoPlatform 适配层

在 `/home/feifz/workspace/WanGoPlatform` 内使用本工作流时，**仓库规则赢**。本篇定义映射与冲突裁决，避免两套规则打架。

## 权威顺序

```text
1. 仓库 AGENTS.md                                    （最高）
2. docs/develop/agent-delivery-protocol.md（v0.6）    （交付流程唯一事实源）
3. .agents/skills/wango-delivery/SKILL.md             （触发与执行摘要）
4. 本工作流 docs/ + skills/                            （只能加严，不能放宽）
```

冲突时执行更严格的一项；若本工作流的某条规则与仓库协议矛盾，**停用本条**并在 run 的 `evidence.md` 记一行"规则冲突：以仓库协议为准"。

## 当前仓库事实（实测，非推断）

| 事实 | 值 | 验证方式 |
|---|---|---|
| 当前分支 | `develop_test` | `git branch --show-current` |
| `.ai_worflow/` 是否入库 | **否**，被根 `.gitignore:37` 忽略 | `git check-ignore -v .ai_worflow` → `.gitignore:37:.ai_worflow/` |
| 忽略规则提交 | `d51eeaab chore: gitignore .ai_worflow/ local artifacts` | `git log -1 -S".ai_worflow" -- .gitignore` |
| 交付协议版本 | v0.6，创建 2026-08-10，最后修订 2026-08-18 | `docs/develop/agent-delivery-protocol.md` 头部 |
| 项目 Skill | `.agents/skills/wango-delivery/SKILL.md`（20 行摘要）+ `agents/openai.yaml` | 目录实测 |
| 宿主目录 | `.codex/`、`.claude/skills/wango-delivery`（软链）、`.agents/skills/` | 目录实测 |

**推论（重要）**：因为 `.ai_worflow/` 不入库，本工作流的 `runs/` 证据**不能**作为仓库工作包的验收证据。仓库工作包的证据必须写入 WanGo 的交付报告与 `docs/plan/` 下的计划文档；`runs/` 只作为我自己的过程草稿与推理留痕。

## 状态机映射

| 本工作流 Run 状态 | WanGo 工作包状态 | 说明 |
|---|---|---|
| `INTAKE` / `RECON` / `SPEC_REVIEW` | `planned` | Spec 与 DAG 尚未冻结 |
| `READY`（G2/G3/G4 均有效） | `ready` | 前置能力必须已有 accepted target 进入 integration baseline |
| `IMPLEMENTING` | `in_progress` | 一个实现会话只处理一个工作包 |
| `REVIEW` / `FULL_VALIDATION` | `implementer_verified` | **实现者最多标到这里**，不得自标 accepted |
| `READY_TO_MERGE` + 独立复核产生 review_passed target + 临时集成检查通过 | `accepted` | 只有这条路径能到 accepted |
| `BLOCKED` | `blocked` | 必须写精确解阻条件 |

允许的迁移与仓库一致：`implementer_verified → in_progress` 可回退；`accepted` 不回退，accepted 后的问题开新工作包。

## Git 基线顺序（照抄仓库，不改）

```text
integration baseline → base_commit → candidate commit → implementer_verified
→ review_passed target → temporary integration check → accepted target
→ integration baseline
```

- candidate target = 实现 + 验证证据 + 计划正文 + 计划索引都同步为 `implementer_verified` 后的**精确最新 commit**；不得把更早的实现提交与随后的状态提交一起称作 candidate。
- Reviewer 通过只产生 review_passed target，状态仍是 `implementer_verified`。
- 临时集成检查无冲突、无行为变化后，review_passed target 成为 accepted target；正式合入产生 integration merge commit；随后状态同步提交在 integration 分支同时把计划正文与索引改为 `accepted`。
- 下一工作包 Entry 时读取状态同步后的实际 integration HEAD 作为自己的 baseline/base_commit。

授权边界同样照抄：`/.worktree/<work-package>/`、本地 `integration/<program>`、`wp/<work-package>`、候选/返修/状态同步提交、临时试合入、accepted 后合入 integration 已固定授权；**合入 `develop`、push、部署、改远端、删未知分支/worktree 需用户单独授权**。

## 切分门禁（仓库口径，本工作流只加严）

| 指标 | 目标 | 硬上限 | 统计口径 |
|---|---|---|---|
| 文件数 | 15 | 25 | **全部**修改文件，生成物也计 |
| 行数 | 1,500 | 2,500 | 非生成代码的新增+修改行，生成代码不计行数 |
| Review Packet | 80 KB | 120 KB | 实际完整任务包字节数 |

预计超硬上限不得开工，必须拆包；只有原子迁移或不可分割生成物一致性可在进入 `ready` 前经用户明确批准后例外。

## 风险等级映射

| WanGo | 本工作流 `delivery_depth` | 复核 |
|---|---|---|
| Lite | `FAST` | 按协议可压缩轮次，但角色分离与证据不压缩 |
| Standard | `STANDARD` | 1 名主独立复核者 |
| Strict | `HIGH_RISK` | Strict 是同一 Review Packet 的**检查维度**，不自动增加复核者 |

## 禁止事项（仓库特有）

- 不创建 `.ai-native/runs/`、`state.json`、运行状态数据库或每任务过程文档（协议 §10 末条）。本工作流的 `runs/` 属于被忽略的本地目录，**不得**被包装成仓库要求的产物。
- 不用"主体完成""进入最终章"、提交数或测试数表示业务完成；进度只报已 `accepted` 的业务场景、当前活动工作包（默认 1 个、并行最多 2 个）、状态、阻塞与解除条件。
- 不新建开发数据库；canonical 栈固定为 `wango_dev` / `wango_wanqore` / `wango_agno_live`，临时库必须记录用途、使用者和清理时间。
- 不把 Radix Themes 代替 Radix Primitives + shadcn，不引入 Redux，页面不直接导入 Mock Fixture 或散落 `fetch`。
- 页面任务必须有真实启动 + 浏览器检查 + 目标视口检查；测试或构建通过不能单独证明页面可用。

## 在 WanGo 内启动一次 run 的最小流程

```bash
cd /home/feifz/workspace/WanGoPlatform
# 1) 仓库侧事实（必须实测）
git branch --show-current && git log --oneline -1 && git status --porcelain | head
# 2) 本地过程容器（不入库）
RUN=RUN-$(date +%Y%m%d)-001
mkdir -p .ai_worflow/runs/$RUN
cp .ai_worflow/skills/_shared/templates/run-state.yaml .ai_worflow/runs/$RUN/state.yaml
# 3) 按 skills/aiworflow/SKILL.md 选工作流，Planner 填 current.md，证据同时写入仓库交付报告
```
