# runs/ · 运行期证据容器

一次非平凡的 AI 开发任务对应一个 Run：`runs/<RUN-ID>/`。

`RUN-ID` 命名：`RUN-YYYYMMDD-NNN`（例如 `RUN-20260907-001`）。同一需求的续作复用同一 RUN-ID，不新开。

## 布局

```text
runs/<RUN-ID>/
├── state.yaml       当前索引：状态、阶段、风险、门禁、块进度、绑定 SHA（唯一由 Planner 写入）
├── current.md       正文：Intake、Spec、Tasks、Decisions、Change Log（原地修订，底部追加变更记录）
├── test-plan.md     测试计划与用例（唯一由 Tester 维护）
├── evidence.md      只追加账本：审核 / 实现 / 测试 / 缺陷 / 完成度判定记录
├── attachments/     必要脱敏附件（截图、日志片段、视口矩阵）
└── .local/          临时物：Prompt 草稿、搜索输出、diff 中间件、调试日志（永不作为正式证据）
```

## 硬规则

- 只有当前 Run 的 Planner 可以写 `state.yaml`；其他角色的记录由 Planner **原样追加**到 `evidence.md`，Planner 只承担传输，不获得作者权或批准权。
- 先写完整证据与身份（Commit SHA、路径、命令、退出码），再更新状态索引；未完成写入不得被状态引用。
- 失败、`BLOCKED`、`not_run` 同样是正式证据，必须落盘，不能只留在 `.local/` 或对话里。
- 已发布记录不可修改；修正由原作者发布新 ID 与 `supersedes` 字段声明取代关系。
- 正式证据不能只依赖 `.local/`；`.local/` 可随时删除而不影响结论可复核性。

## 与 WanGoPlatform 的关系

在 WanGoPlatform 仓库内执行交付工作包时，**不在仓库内创建 `.ai-native/runs/`、`state.json` 或每任务过程文档**（仓库 `AGENTS.md` 第 10 节明确禁止）。此时：

- 本目录只做**我个人的过程索引**，不作为工作包验收证据来源；
- 验收证据写入 WanGo 的交付报告与 `docs/plan/` 计划正文/索引；
- 状态以 WanGo 的 `planned -> ready -> in_progress -> implementer_verified -> accepted` 为准，映射表见 `../docs/10-wango-adapter.md`。

## 入库状态（当前事实，2026-09-20 复核 · v1.8.3）

- `.ai_worflow` **不是独立 Git 仓库**（v1.8.2 曾短暂自建本地仓库，v1.8.3 按用户决定撤销）：目录内无 `.git/`，`git rev-parse --show-toplevel` 指向主仓，`git ls-files .ai_worflow` 返回 0。
- 主仓通过 `.git/info/exclude` 排除 `/.ai_worflow/`，本目录全部内容不进入父仓库历史；pre-commit hook v3 装于主仓 `.git/hooks/`（旧 v2 已自动备份）。
- 因此 `runs/` 是本地过程索引，不是版本化证据；在 WanGoPlatform 内交付时以 `docs/plan/` 的交付报告和计划正文为验收证据来源。`runs/` 的护栏是 `validate_run`/`validate_transition`/`check_all`，不依赖 git。

## 已登记的占位目录

> 本表不是说明文字，而是 `scripts/validate_package.py` 第 10 步（v1.4.1 起）的**机器可读白名单**：
> `runs/` 下每个目录要么通过 `validate_run.py`，要么在此登记；两者都不满足则包校验 FAIL、
> pre-commit 闸门拒绝提交。理由是恒定 FAIL 会让人和 Agent 习惯性忽略 FAIL，护栏被当噪音就等于没有。
> `scripts/selftest.sh` §3b 用临时负例目录证明该护栏真的会开火（用完即清理）。

| 目录 | 内容 | 状态 |
|---|---|---|
| `RUN-TEST-001/` | 仅 `state.yaml`，内容 `# cleaned` | 已清空的历史测试占位 |
| `RUN-TEST-002/` | 同上 | 同上 |
| `RUN-20260914-001/` | skill-tool-tag-classification 功能交付（已合入 develop `e7b544fd`） | DAG 定义与 state 块不一致（自建 merge/close 代替 integrate/test/verify_ui 等标准块）、gate owner 违规（G5=tester 应为 reviewer、G7/G8/G9 类似）；v1.8.0 起另命中 R-1（close completed 但 integrate/notify 留 pending）。已通过勘误 ERRATA-001 记录并承接下一 Run，详见 evidence.md#ERRATA-001。**显式承担，不伪造历史** |
| `RUN-20260915-001/` | tag 管理交付 run（2026-09-16 机器重启致会话丢失；2026-09-20 维护处置标 terminated，快见 state.prev.yaml） | 命中 R-1：`review` 停在 running（待 G5 复审）但下游 `test`/`release_check` 已 completed，`integrate` skipped 无凭据——中断现场的真实不一致，无法补凭据而不伪造，显式承担 |

> 2026-09-20 维护处置（docs/31 P3-5）：`RUN-20260916-002`（check 补 skip_reason）、`RUN-20260917-003/004`（未命中分支块补 skipped+skip_reason）、`RUN-20260917-006`（integrate 补 skip_reason）、`RUN-20260920-001`（owner 大小写修正）已全部恢复 validate_run PASS 并移出本表；`RUN-20260914-002/16-001/17-001/18-001/18-002` 同批收口（canceled/completed），处置记录见各 run `current.md#Change Log`。

正式 run 已移出（`RUN-20260908-*` 磁盘目录不存在，见下文"失效描述已修正"）。

## 失效描述已修正（2026-09-14）

以下为本次复核中发现的与事实不符的旧描述，已在上文中修正：

- ~~`.ai_worflow` 是独立 Git 仓库~~ → 实际无 `.git/`，被主仓 `.git/info/exclude` 排除
- ~~`git ls-files runs` 有 44 个受跟踪文件~~ → `git ls-files .ai_worflow` 为 0
- ~~正式 run（`RUN-20260908-002` ~ `-006`）均 `validate_run.py` PASS~~ → 磁盘目录已不存在，无法验证
