# 实现工作流参考

> 受约契约：`../../_shared/contracts/role-boundaries.md`、`../../_shared/contracts/git-policy.md`
> 权威来源：`../../../../docs/04-roles.md`、仓库 AGENTS.md。

## 会话规则

- 一个实现会话只处理一个工作包/块，使用最小任务包（约 3,000 token：目标、基线、接口、路径、验收、停止条件）。
- 5 分钟无可观察产物中断；30 分钟软检查点；轮次/上下文/解析失败不自动恢复累计会话。

## 分层验证

- 开发中做定向检查。
- 交付前跑当前块相关测试、type-check、lint 和关键运行路径。
- Finding 返修只跑对应检查和必要邻接回归。

## 脏工作区

- 绝不 reset --hard / clean / checkout -- / 自动 stash。
- 记录脏文件与写路径重叠；无重叠则从已提交 SHA 用干净分支/worktree；重叠无法隔离则 `BLOCKED`。

## 必须产出的证据记录

每个实现会话结束前产出两份记录，交 Planner 追加到 `evidence.md`（详见 `docs/05-state-and-evidence.md` §必须入账本的五类记录）：

1. **IMPL-xxx**：用 `../../_shared/templates/implementation-report.yaml` 输出。含 `files_changed`、`tests_run`、`verification`（直接验证证据，页面任务需真实浏览器）、`known_issues`、`follow_ups`。
2. **CHECK-xxx**（check 块）：每行命令的 `cmd / workdir / exit_code / expect` 对照表。`outcome=PASS` 仅当所有 `exit_code == expect`。

失败的实现或检查也写入——状态 `failed` 不等于"不需要记录"。Record ID 在单次 Run 内唯一。

## 在 WanGo 仓库

遵守仓库 AGENTS.md 与交付协议；`.ai_worflow/` 不入库，工作包证据写入交付报告与计划文档。
