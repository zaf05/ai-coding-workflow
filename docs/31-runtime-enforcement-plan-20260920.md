# 31 · 运行期强制执行与回收 · 实施方案（2026-09-20）

> **实施状态（2026-09-20 更新，v1.8.0 → v1.8.3 全部完成）**：**P0 / P1 / P2 已实施并全绿**（selftest、validate_package PASS、check_all FAIL 0）——P0 = `scripts/validate_transition.py`（T-01..T-04）+ Planner SKILL 写入步骤 + docs/05/03 规则源同步；P1 = `validate_run.py` 新增 R-1/R-2/R-3（连边复用 `run_flow.build_graph`；skipped 凭据口径 = `skip_reason`/`error_codes`/注释三者其一，`skip_reason` 为机器可读首选）；P2 = `scripts/check_all.py`（mtime 陈旧检测 + 收据/闸门汇总，白名单登记过的 FAIL 计 WARN）。实测额外收获：R-1 揭示 6 个存量 run 的真实语义缺口，已按"显式承担"登记 `runs/README.md`。**P3 已于 v1.8.2 实施**（在途 run 结束后执行）：① `.ai_worflow` `git init` 为独立本地仓库（无远端不 push；`runs/` 与 `references/` 经本地 `.gitignore` 不入库）；② pre-commit hook 升 **v3** 支持"仓库根即包根"布局（旧 v2 在嵌套仓库会恒定跳过、闸门变假象）；③ `{{ run_id }}` 已补渲染（RUN-20260915-001/current.md）；④ 7 个陈旧 run 按 Planner 处置协议收口（`cp state.prev.yaml` 快照 → 改写 → `validate_transition`/`validate_run` 双校验，处置记录在各 run `current.md#Change Log`）：15-001 terminated（R-1 真实不一致保留白名单）、16-002/17-003/17-004/17-006/20-001 修复凭据或 owner 后撤白名单、14-002/18-001 canceled、16-001/17-001/18-002 补记 completed。**v1.8.3 修正（用户决定）**：① 中的本地仓库整体撤销（删除 `.ai_worflow/.git` 与包内 `.gitignore`，本目录不入任何版本库）；hook v3 改装于**主仓** `/WanGoPlatform/.git/hooks/`（旧 v2 自动备份 `pre-commit.foreign-backup-20260920-111942`，`--check` PASS，布局 A 生效、布局 B 代码保留备用）。②③④ 的成果不受影响。注：P0 设计时预期的"state.prev.yaml 需登记容器白名单"实际不必要——validate_run 无多余文件清单。
>
> **文档性质**：开发方案 + 新会话完整上下文。本文所有"问题"均已于 2026-09-20 实测复现（命令见 §2），不是推测。
>
> 与既有路线图的关系：`29-enhancement-roadmap.md` 的 F1（长时自主运行）覆盖"跨天继续"方向；本方案处理的是 2026-09-20 实测暴露的**运行期强制执行缺口**（写入时拦截、DAG 语义一致性、超时回收），两者互补不冲突。

## 0. 新会话启动指令（直接粘贴）

```text
读取 /home/feifz/workspace/WanGoPlatform/.ai_worflow/docs/31-runtime-enforcement-plan-20260920.md，
按 P0 开始实施（完成一项经我确认后再做下一项）。
硬约束：Python 3 + bash，除当前环境已有 PyYAML外不新增外部依赖；selftest.sh 现有 52 项必须保持全绿、新增能力必须新增自检项；
state.yaml 的唯一写入者仍是 Planner，脚本只校验不代写；不 push、不删未知文件。
```

## 1. 系统现状快照（2026-09-20 实测）

- 版本 `1.7.8`（单一事实源 `VERSION`），`schema_version: 1`。
- 位置 `/home/feifz/workspace/WanGoPlatform/.ai_worflow/`；已被主仓库 `.gitignore` 忽略（`! `条目 `.ai_worflow/`），在本目录改动不影响 WanGo 仓库状态。
- **本目录已无嵌套 `.git`**（v1.1.0→v1.7.8 的演进无版本控制，见 P3）。
- 自检基线：`bash scripts/selftest.sh` → **52 通过 / 0 失败**（含收据、漂移、pre-commit 防篡改、7 条 author-time 护栏逐条反例触发、架构一致性、G4/TDD Red）。
- 工作流 4/4 PASS：bugfix-triage(8 块)、feature-delivery(16 块)、refactor-migration(7 块)、ui-verification(5 块)。
- run 证据：`runs/RUN-20260914-001` … `RUN-20260918-002` 共 14 个。
- 宿主：Codex 与 Claude Code 已实机加载；ZCode 未验证。
- 运行期闸门现状：`install_hooks.py --check` 报 PASS，hook 位于 **主仓库** `/home/feifz/workspace/WanGoPlatform/.git/hooks/pre-commit`。注意：由于 `.ai_worflow/` 被主仓库忽略、本目录又无自己的 `.git`，**该 hook 实际上永远不可能因 `runs/` 变更而触发**——闸门在位但结构上失明（P3 修复）。

已实测可用的命令（新会话直接复用）：

```bash
cd /home/feifz/workspace/WanGoPlatform/.ai_worflow
python3 scripts/validate_package.py                          # PASS
bash scripts/selftest.sh                                     # 52/52
python3 scripts/validate_workflow.py workflows/feature-delivery.workflow.yaml
python3 scripts/validate_run.py runs/<RUN-ID>                # 逐 run
python3 scripts/run_flow.py workflows/<wf>.yaml runs/<RUN-ID>   # frontier/STAR/HANDOFF（只读）
python3 scripts/run_flow.py workflows/<wf>.yaml runs/<RUN-ID> --evaluate-conditional <label> <key>
python3 scripts/install_skills.py --check                    # 报 1 处漂移（见 §2.4）
python3 scripts/install_hooks.py --check                     # PASS（主仓库 hooks）
```

可复用的关键既有资产（**import 复用，不要复制**）：

| 资产 | 位置 | 用途 |
|---|---|---|
| `GATE_ROLES`（gate → 允许 owner 集合） | `scripts/validate_run.py:22` 起，与 `validate_workflow.py` 同源 | P0 门禁 owner 校验的判定依据 |
| `resolve_workflow_path()` | `scripts/validate_run.py:43`（读 `run.workflow_path`，指向 `compile_dag.py` 编译产物） | P1 加载工作流 DAG |
| 最小 YAML 解析 | `scripts/_yaml_min.py` | 新脚本解析 YAML 用这个，不引入 PyYAML |
| 收据/漂移机制 | `scripts/install_skills.py`（`--check/--upgrade/--apply`） | P3 漂移修复 |
| selftest 分节结构 | `scripts/selftest.sh`（`== N. 标题 ==` 分节） | 新增自检项照此追加 |

## 2. 四个实测问题（证据与复现）

### 2.1 P0 问题：门禁违规无写入时拦截

```bash
python3 scripts/validate_run.py runs/RUN-20260914-001
# 输出含：gate G9 owner 'planner' 不在 {'tester'} 中
```

该 run `status: completed`；`state.yaml` 中 G9 由 Planner "补记为通过"（注释自述"复核修订…补记为通过"），即 **Planner 代签了 Tester 拥有的 G9 门禁**，勘误 `evidence.md#ERRATA-001` 只记录了"合入先于独立复核"的顺序违规，没有纠正 owner 越权本身。`feature-delivery.workflow.yaml` 定义 `smoke` 块 `role: tester, gate: G9`。

根因：所有门禁/块状态校验都是**事后**（validate_run / selftest）才跑；Planner 写 `state.yaml` 时没有任何机制拦截非法 transition。

### 2.2 P1 问题：validate_run 不校验 DAG 语义一致性

```bash
python3 scripts/run_flow.py workflows/feature-delivery.workflow.yaml runs/RUN-20260918-002
# frontier = [spec, integrate, release_check] —— 但该 run 的 close/verify_ui/review 已 completed
python3 scripts/validate_run.py runs/RUN-20260918-002
# PASS（容器结构合法）
```

`RUN-20260918-002` 的 `blocks:` 只登记 5 块（intake/recon/verify_ui/review/close 全 completed，`attempts: 0`），`run.status=running`。"已 close 但 spec 未做、frontier 非空"这种结构 validate_run 判 PASS——它只查容器结构，不比对工作流依赖图。

### 2.3 P2 问题：`max_elapsed_time_minutes` 是死字段

```bash
for r in runs/RUN-*; do grep -m1 'status:' $r/state.yaml; done
# 5 个 run 停在 running：RUN-20260914-002、20260915-001、20260916-001、20260917-001、20260918-001
```

`runs/RUN-20260915-001/state.yaml` 自述"2026-09-16T09:14 机器重启导致站点服务与 3 个子代理会话全部丢失"。模板声明 `max_elapsed_time_minutes: 240`，但 `timed_out` 只是合法状态值，**没有任何自动机制**发现或标记超时；`27-gap-analysis-20260918.md` 也未把该项列为缺口。

### 2.4 P3 问题：卫生与版本控制

- Codex 宿主漂移未处理：`install_skills.py --check` 报 `_shared/templates/task-state.yaml` 指纹不一致；实测 `~/.codex/skills/_shared/templates/task-state.yaml` 是**普通文件**（安装模式 symlink，应为符号链接；内容与源一致，属"去符号链接化"漂移）。
- `runs/RUN-20260915-001/current.md` 标题仍是未渲染占位符 `# Run {{ run_id }} · Current`。
- 本目录无 `.git`：规则文档与脚本从 v1.1.0 到 v1.7.8 的全部演进**不可回溯**；且 §1 所述 pre-commit 闸门因此对 `runs/` 失明。

## 3. 实施方案

### P0 · `validate_transition.py`：状态写入时校验（最高优先级）

**目标**：把"事后发现 G9 越权"升级为"写入时拒绝"。成本最低（复用 GATE_ROLES），直接堵住 §2.1。

**新文件** `scripts/validate_transition.py`：

```
用法：python3 scripts/validate_transition.py <run_dir> [--prev state.prev.yaml]
契约：只读校验，绝不写 state.yaml（唯一写入者仍是 Planner）。
```

设计要点：

1. **快照来源**：Planner 保存新 state 前把旧版复制为 `state.prev.yaml`（同 run 目录）。校验器 diff 两个快照；`state.prev.yaml` 加入 run 容器白名单（`validate_run.py`/`validate_package.py` 的容器清单需同步登记，属预期变更）。
2. **校验规则**（每条独立报错，带稳定编号 T-01…）：
   - T-01 新置 `passed: true` 的门禁，`owner` 必须 ∈ `GATE_ROLES[gate]`（import `validate_run` 的定义，不复制）。
   - T-02 块状态机：`pending→running→completed|failed|skipped|blocked` 合法；`completed→running/in_progress` 仅当 `error_codes` 记录返修凭据（对应 docs/05 状态机与 `implementer_verified→in_progress` 例外）。
   - T-03 新 completed 块的 `gate` 与工作流定义的门禁绑定一致。
   - T-04 `attempts` 单调不减；`star: true` 块新增 completion 必须引用 `approvals.user` 或显式人工证据（evidence_ref 指向 `APPROVAL-*` 锚点）。
3. **接入点（两层）**：
   - `skills/aiworflow-planner/SKILL.md` 的状态写入步骤追加一条硬规则："覆写 state.yaml 前：`cp state.yaml state.prev.yaml` → 写入 → `python3 scripts/validate_transition.py runs/<RUN-ID>`，FAIL 则回滚本次写入并按报错修正。"
   - P3 完成后由 `.ai_worflow` 自己的 pre-commit hook 对变更过的 run 目录自动执行（见 P3）。
4. **自检**：`selftest.sh` 新增一节"transition 护栏"，用临时 fixture 复现 §2.1 的 G9-owner 形态，断言 FAIL 且报错含 T-01。

**验收**：fixture 中"planner 代签 G9"被拒绝并输出 T-01；正常 PASS 的旧快照序列（可从 RUN-20260917-002 的账本构造）全部放行；52+新增 项全绿。

### P1 · DAG 语义一致性：validate_run 升级

**目标**：让 §2.2 的"close 已完成但 spec 在 frontier"判 FAIL。

**改动文件**：`scripts/validate_run.py`（复用 `resolve_workflow_path` 加载编译产物建图）。

新增校验（编号沿用其现有报错风格）：

- R-1 任一 `completed` 块在工作流 DAG 中的全部祖先必须是 `completed` 或 `skipped`（skipped 必须在 `error_codes`/注释携带跳过凭据）。
- R-2 `run.status == completed` ⇒ 所有非 skipped 块 terminal、frontier 为空、`finally_block_label` 指向的块 completed。
- R-3 run 登记的块集合 ⊆ 工作流块集合，且未登记块一律视为 pending（现状即如此，明文固定该语义防止漂移）。

**自检**：fixture 复刻 RUN-20260918-002 形态（5 块 completed 含 close，工作流 16 块），断言 FAIL 且命中 R-1/R-2。

**注意**：存量 run 里有真实数据会因此新规则变 FAIL（RUN-20260918-002 本身）。处理口径：校验器输出 FAIL 是**正确行为**，该 run 属于在途验证 run，由 Planner 决定补记 skipped 凭据或按 R-1 补齐前置块；不为迁就存量放水规则。

### P2 · 超时回收与 `check_all.py` 日检

**目标**：`max_elapsed_time_minutes` 活起来；一个命令看全系统健康。

**新文件** `scripts/check_all.py`（只读汇总，退出码：FAIL=1，仅有 WARN=0）：

1. 逐 run 跑 validate_run → 汇总 PASS/FAIL。
2. **陈旧检测**：`status ∈ {running, paused}` 且 `last_activity = max(mtime(state.yaml), mtime(evidence.md), mtime(task.yaml), mtime(checkpoint.yaml))` 距今超过 `max_elapsed_time_minutes` → 输出 WARN 列表（run ID、停滞时长、建议动作：续跑 / Planner 标记 `timed_out` / terminated）。用文件 mtime 是刻意选择：账本时间戳可伪造、mtime 不可；口径在脚本 docstring 写明。
3. 汇总 `install_skills.py --check` 与 `install_hooks.py --check` 的漂移结果。

**边界**：脚本**不代写** `timed_out`（Planner 是唯一写入者），只产出建议——这保持角色所有权不变。

**自检**：fixture 造一个 mtime 超限的 running run，断言 WARN 输出含 run ID 与建议动作。

**验收**：当前实跑应报出 §2.3 的 5 个陈旧 run（今天为准已停滞 2–6 天）。

### P3 · 版本控制与卫生修复

1. **`git init` 本目录**（本地仓库，不建远端、不 push——push 属用户单独授权操作）。首个 commit 收录现状（`runs/` 是否入库遵循现状：runs 一直是本地证据不入库，加入本仓库 `.gitignore`）。此后每次规则/脚本变更正常提交，恢复演进可回溯性。
2. **迁移运行期闸门**：`python3 scripts/install_hooks.py --apply` 指向新 `.git/hooks/`，使 pre-commit 真正覆盖 `runs/` 与规则文件；`--check` 必须继续 PASS。主仓库 hooks 是否保留由用户决定（它对被忽略路径无实际作用）。
3. **修 Codex 漂移**：`python3 scripts/install_skills.py --target "$HOME/.codex/skills" --upgrade --apply`，恢复 symlink，`--check` 归零。
4. **补渲染** `runs/RUN-20260915-001/current.md` 的 `{{ run_id }}`（Planner 会话执行，一行修复）。
5. **僵尸 run 处置**：Planner 逐个审阅 §2.3 的 5 个 run：仍要做的 → 续跑并刷新账本；不做的 → 标记 `canceled`/`terminated` 并在 evidence.md 记录原因。机器重启丢失场景（20260915-001）同时验证 `30-multi-day-task-protocol.md` 的 task_resume 路径是否已可覆盖该恢复场景，不可覆盖则记入 gap。

## 4. 全局硬约束（实施会话必须遵守）

- Python 3 + bash，除当前环境已有 PyYAML外不新增外部依赖；只读 YAML 路径可用 `_yaml_min.py` fallback。
- `state.yaml` 唯一写入者是 Planner；所有新脚本只读校验、只产出建议。
- selftest 现有 52 项保持全绿，每项新能力配新增自检（护栏必须被反例真实触发——沿用本仓库既有验收哲学）。
- 规则正文唯一来源：新校验规则同步写进 `docs/05-state-and-evidence.md`（状态机）与 `docs/03-gates.md`（owner 集合引用），`skills/` 只留执行摘要；新增文档/规则后跑 `python3 scripts/validate_package.py`（docs 索引、runs 容器清单都会校验）。
- 本目录受主仓库 `.gitignore` 保护，改动不进入 WanGo 仓库状态；在 WanGo 仓库内另行的未提交修改（schemas.py 等 5 文件 + 4 篇未跟踪文档）与本方案无关，不得触碰。
- 不 push、不删未知文件、不用 `git reset --hard` 处理未知改动。

## 5. 建议实施顺序与规模

| 项 | 优先级 | 预估 | 依赖 |
|---|---|---|---|
| P0 transition 校验 | **P0** | ~2h（脚本+SKILL 接入+selftest） | 无 |
| P1 DAG 语义一致性 | P1 | ~1.5h | 无 |
| P2 check_all + 陈旧检测 | P1 | ~1h | 无 |
| P3 git init + 闸门迁移 + 漂移/占位符/僵尸处置 | P2 | ~1h | 建议在 P0 后做（让首个 commit 已含 transition 护栏） |

总量约一个会话可完成 P0+P1；P2/P3 可第二个会话。每完成一项：跑 `validate_package.py` + `selftest.sh` + 针对性 fixture，全绿后向用户汇报再进下一项。
