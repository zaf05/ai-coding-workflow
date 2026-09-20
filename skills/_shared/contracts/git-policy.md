# Git 策略契约

> 吸收自：a04 左泽位「CLAUDE.md + AGENTS.md 建立统一工程约束」、a15 The fool ss「Harness 会过期」
> 权威来源：`../../../docs/10-wango-adapter.md` 与仓库 `docs/develop/agent-delivery-protocol.md`。本文件是执行摘要。

## 基线顺序（WanGo 仓库内固定）

```text
integration baseline → base_commit → candidate commit → implementer_verified
→ review_passed target → temporary integration check → accepted target
→ integration baseline
```

- candidate target = 实现 + 验证证据 + 计划正文 + 计划索引同步为 `implementer_verified` 后的精确最新 commit。
- Reviewer 通过只产生 review_passed target，状态仍 `implementer_verified`。
- 临时集成检查无冲突、无行为变化后成为 accepted target；正式合入产生 integration merge commit。
- 下一包 Entry 读取状态同步后的实际 integration HEAD 作为 baseline/base_commit。

## 固定授权

本地 worktree/分支、候选/返修/状态同步提交、临时试合入、accepted 后合入 integration 已授权。
**合入 develop、push、部署、改远端、删未知分支/worktree 需用户单独授权。**

## 保护

- 绝不 `git reset --hard` / `git clean` / `git checkout --` / 自动 stash 处理未知改动。
- 不覆盖他人未提交修改，不混入无关变更。
- 提交前跑 `git diff --check`，确认空白与冲突标记零报告；清理文档尾随空格。

## Commits 时间线非证据（吸收自 a01）

> a01「不做人工Code Review，如何保障 Vibe Coding 的项目质量？」：AI 可能一天提交 50 次，审查的是"净变更"而非每次提交。

本工作流对应：
- Reviewer 审查的是 `base_sha..candidate_sha` 的**净 diff**，不是中间的 WIP commits。
- Implementer 在中间可以自由 commit 探索过程，但 candidate commit 必须是整理后的干净提交（squash/rebase 后）。
- 提交频率不自动代表质量或进度。

## 统一工程约束入口（吸收自 a04）

> a04「用 CLAUDE.md + AGENTS.md 建立统一工程约束」：CLAUDE.md/AGENTS.md 作为统一工程约束入口，渐进式披露不建巨型文件。

本工作流对应：
- WanGoPlatform 仓库的 `AGENTS.md` 是所有 Agent 的统一约束入口。
- 本文件（`git-policy.md`）是工作流层面的 Git 策略补充，不能与 `AGENTS.md` 和 `agent-delivery-protocol.md` 冲突。
- 约束只在一个地方维护：Git 策略在 `agent-delivery-protocol.md`；工作流特有约束在本文件。
