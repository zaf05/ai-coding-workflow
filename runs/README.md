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

## 入库状态（当前事实，2026-09-21 复核 · v1.8.10）

- `.ai_worflow` **是独立 Git 仓库**（历史：v1.8.2 自建 → v1.8.3 撤销 → **2026-09-20 21:02 重新自建**，init import 提交 `d551273`，分支 `main`，remote `git@github.com:zaf05/ai-coding-workflow.git`；2026-09-21 用户确认保留并适配）。
- 主仓 `.git/info/exclude` 仍排除 `/.ai_worflow/`，本目录内容不进入父仓库历史；pre-commit hook v3 **双布局在位**：主仓 `.git/hooks/` 与本仓 `.git/hooks/` 各一份（本仓一份为 2026-09-21 `install_hooks.py --apply` 装入，布局 B 生效，`--check` PASS）。
- `runs/` 因此升级为版本化过程索引；在 WanGoPlatform 内交付时验收证据来源不变（以 `docs/plan/` 的交付报告和计划正文为准），`runs/` 的机器护栏仍是 `validate_run`/`validate_transition`/`check_all`，不因入库而放松。
- **可见性现状（2026-09-24 实测）**：远端 `zaf05/ai-coding-workflow` 为 **public**（匿名 API 返回 private=false）。`runs/RUN-*/` 已被 .gitignore 排除未上云；但 `runs/README.md` 与 `context/*.md` 已入库公开，含内部项目描述。**用户需决策**：转私有，或接受公开并评估 context/runs-README 中的业务细节是否需要脱敏。runs 证据归档方案必须在此决策之后才能执行（归档到 public 仓会暴露过程证据）。

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
| `RUN-20260914-002/` | canceled run | R-4：canceled 收口时 `current_block_label` 停在 `plan`，终态索引未归位 finally（v1.8.12 前无此护栏） |
| `RUN-20260916-001/` | AgentWan 文档站 3 页交付 run（site/ 为 git 忽略本地产物） | R-4+R-5：run.status 手改为 completed 但 `current_block_label=implement`；implement/check/review 等关键块 `head_sha=null`、`attempts=0` 却全部 completed——引擎加固前的真实账本缺口，审计结论见 v1.8.12 工作包，不改写历史 |
| `RUN-20260916-002/` | canceled run | R-4：canceled 收口时 `current_block_label=smoke` |
| `RUN-20260917-001/` | doc_fix 交付 run | R-4+R-5：completed 但 `current_block_label=doc_fix`；implement 类块 completed 未绑定 head_sha |
| `RUN-20260917-002/` | 功能交付 run | R-5：implement 块 completed 未绑定 head_sha |
| `RUN-20260917-003/` | doc_fix run | R-5：doc_fix（implement 类）块 completed 未绑定 head_sha |
| `RUN-20260917-004/` | doc_fix run | R-5：doc_fix（implement 类）块 completed 未绑定 head_sha |
| `RUN-20260918-001/` | canceled run | R-4：canceled 收口时 `current_block_label=intake` |
| `RUN-20260918-002/` | 功能交付 run | R-4：completed 但 `current_block_label=intake` |
| `RUN-20260921-007/` | 启动即中断的 run（仅 current.md/test-plan.md） | 缺少 `state.yaml`，无机器可复核状态，显式承担；不虚构补写 |
| `RUN-20260922-001/` | .venv 环境修复 run（FAST，Planner 直登） | 自定义块定义只存在于 current.md、`workflow_path: null`，DAG 定义不可机器复核——v1.8.12 起此类形态必须使用可保存的工作流定义，本 run 作为反面样本显式承担 |
| `RUN-20260923-001/` | v1.8.13 工作包 run（bugfix-triage：DEFECT-001 修复 + F1-R L3 断点演练载体） | L3 演练恢复会话接续 implement→test→close 收口，收口后由 `validate_run` 直接通过；中断/中间态期间曾以本行占位防包校验恒定 FAIL |
| `RUN-20260923-004/` | v1.8.15 引擎 CLI 契约收口 run（bugfix-triage；docs/13 两缺口销账载体） | 八块全终态；env_note/doc_fix 以新参数 --skip-reason 原生跳过（dogfood）；validate_run PASS |
| `RUN-20260923-003/` | v1.8.14 真实任务 run（feature-delivery：六模块实测+修复；P2′ 端到端首战） | 16 块全链路 completed（G0-G10 闭环）；候选 1e4010f5 停 wp 分支待授权；validate_run/validate_package PASS |
| `RUN-20260923-002/` | v1.8.14 工作包 run（bugfix-triage：P1 并发写保护 + R-1/R-2 复核发现修复） | 容器由修复后 `--init` 创建（dogfood 相对路径）；推进中间态直接通过 validate_run |

> 2026-09-23 引擎加固处置（v1.8.12）：新增 R-4（终态 current_block_label 必须归位 finally）、R-5（implement completed 必须绑定 head_sha）、workflow_sha256 冻结护栏后，历史 run 的账本缺口被显式暴露并登记为墓碑。`RUN-20260921-002..006` 是 Claude Code 会话的工作包 run（曾停在 integrate/review/implement）：v1.8.12 升级后经 `--refreeze-workflow` 结构校验迁移定义；**2026-09-23 用户确认 CC 彻底结束，Codex 接手归账收口**——implement 逐一绑定 review_passed target（002=`d63a215b`、003=`3057118e`、004=`4e081837`、005=`4cdc3c82`、006=`842e299f`），剩余流程块 skip+`BUSINESS_CLOSED_ELSEWHERE` 凭据（业务复核已由主仓计划协议完成，见各 run evidence.md 的 IMPL-001/CLOSEOUT-20260923），notify/close 完成后由引擎自动终态；五个 run validate_run 全 PASS。原则：不改写历史，只显式承担；结构变更仍需 Change Log + 新建 run。

> 2026-09-20 维护处置（docs/31 P3-5）：`RUN-20260916-002`（check 补 skip_reason）、`RUN-20260917-003/004`（未命中分支块补 skipped+skip_reason）、`RUN-20260917-006`（integrate 补 skip_reason）、`RUN-20260920-001`（owner 大小写修正）已全部恢复 validate_run PASS 并移出本表；`RUN-20260914-002/16-001/17-001/18-001/18-002` 同批收口（canceled/completed），处置记录见各 run `current.md#Change Log`。

正式 run 已移出（`RUN-20260908-*` 磁盘目录不存在，见下文"失效描述已修正"）。

## 失效描述已修正（2026-09-14）

以下为本次复核中发现的与事实不符的旧描述，已在上文中修正：

- ~~`.ai_worflow` 是独立 Git 仓库~~ → 实际无 `.git/`，被主仓 `.git/info/exclude` 排除
- ~~`git ls-files runs` 有 44 个受跟踪文件~~ → `git ls-files .ai_worflow` 为 0
- ~~正式 run（`RUN-20260908-002` ~ `-006`）均 `validate_run.py` PASS~~ → 磁盘目录已不存在，无法验证
