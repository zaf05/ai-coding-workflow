# 29 · 五项缺失能力实施方案 · 2026-09-18

> 对应 `docs/27-gap-analysis` 识别的 5 项"缺失但需要"能力。每项给出具体设计、改动文件、工作量、验收标准。原则：**不新增外部依赖**（当前运行环境已有 PyYAML），可选用增强，核心保持纯文件。

---

## F1 · 长时自主运行（P0）

### 现状
- 熔断：CONTINUE 超 10 轮 → BLOCKED
- 问题：大型任务（跨天/跨会话）无法连续推进

### 方案

**改动 1：熔断可配置**
```yaml
# workflow YAML 新增顶层字段
loop_control:
  max_continue_rounds: 50    # 默认 50（原 10），最大 200
  checkpoint_interval: 10    # 每 10 轮写一次检查点
  checkpoint_file: checkpoint.yaml
```

**改动 2：检查点机制**
- 每 N 轮自动写入 `runs/<RUN-ID>/checkpoint.yaml`
- 内容：当前块、已完成块、ledger 快照、context 增量、token 累计
- 新会话恢复时优先读 checkpoint，而非全量扫描 state.yaml

**改动 3：分段推进**
- 一次 `run_flow.py --advance` 最多推进 20 个块
- 达到上限后输出 `CHECKPOINT_REACHED`（非 BLOCKED）
- Agent 收到 CHECKPOINT_REACHED 后启动新会话继续

### 涉及文件
| 文件 | 改动 |
|---|---|
| `workflows/feature-delivery.workflow.yaml` | 新增 `loop_control` 字段 |
| `scripts/run_flow.py` | 读取配置、检查点写入、CHECKPOINT_REACHED 信号 |
| `skills/aiworflow/SKILL.md` | 更新自动化推进循环：处理 CHECKPOINT_REACHED |
| `docs/07-failure-and-recovery.md` | 熔断规则从固定 10 改为可配置 |

### 验收
- [ ] 50 轮连续推进不触发 BLOCKED
- [ ] 检查点文件包含完整恢复所需状态
- [ ] 新会话从 checkpoint 恢复后继续推进

### 工作量：2h

### F1-R · L3 恢复演练（登记于 2026-09-20；2026-09-23 已执行，RUN-20260923-001）

**当前已实证状态（防止文档冒充实现）**
- v1.8.8 起：`task_resume.py` 已消费 `checkpoint.yaml`、`state.yaml` 的块状态与最近 ledger，并在恢复提示词中写明“已 completed 块的外部副作用零重复执行”
- selftest §13 覆盖：task-state 模板 / checkpoint 落盘 / 恢复提示词 / checkpoint+state+ledger 消费 / 缺 task.yaml 非零退出 / run 容器兼容
- **2026-09-23 实证升级（v1.8.13，RUN-20260923-001，bugfix-triage 工作流）**：intake/recon/classify 完成后主会话故意中断（ledger 留 INTERRUPT/SESSION_BREAK 条目、五件套写全），全新零共享上下文恢复会话按协议接续 implement→test→close——L3 演练从“组件级机器断言”升级为“真实断点恢复已实证”，证据逐条落 RUN-20260923-001/evidence.md 与 state.yaml completion_contract C1..C5
- run 内单活跃角色与串行推进是治理设计，见 `docs/04-roles.md`《单活跃角色与串行推进（设计边界）》；并行只发生在工作包层。

**触发条件（已满足并执行）**
- 下一个真实 ≥3 块 run：intake / recon / spec 推进完成后故意中断，中断前写全 state.yaml + task.yaml + checkpoint.yaml + context/*.md + evidence.md，开全新会话执行 `python3 scripts/task_resume.py runs/<RUN-ID>`（本 run 无 spec 块，classify 的分支决策即规格级决策点，映射记录于 current.md#Classify）

**验收条件（五条全过，L3 才升级为”真实断点恢复已实证”）——2026-09-23 全部通过**
- [x] 恢复提示词包含已完成块列表（task_resume.py 输出 `**Completed blocks**: intake, recon, classify`）
- [x] run_flow frontier 不再选择已完成块（`--advance` 报告 remaining_blocks=[env_note, doc_fix, implement, test, close] 与 frontier 动作均不含 intake/recon/classify；engine_gap 归因的实际路由分支为 implement，env_note/doc_fix 为未选分支、随后按 skipped 收口）
- [x] 新会话 G1 真读 context 文件（恢复会话实读 project-aiworkflow.md / risk-register.md / decisions.md 并引用版本事实与护栏纪律）
- [x] ledger / state 可追溯中断前历史（round=1 HANDOFF(intake) 与 round=3 INTERRUPT(classify, SESSION_BREAK) 条目在恢复会话中可读）
- [x] 恢复会话首个动作是读 ledger/checkpoint 确认已提交物；已 completed 块的外部副作用（migration/commit/push）零重复执行（首动作读 checkpoint.yaml+state.yaml ledger 并 `git log` 核对 HEAD=db854aa 无任务提交；恢复会话的第一个提交即候选提交）

**声明边界（2026-09-23 起生效）**
- `task_resume.py` 的 checkpoint 消费能力已落地，且已经 RUN-20260923-001 真实断点演练实证——「单点断点恢复（≥3 块中断→新会话接续）」可宣称“真实断点恢复已实证”
- 仍不宣称：多天 Session×Run 级联（12 Session×6h 协议上限的端到端实战，见 `docs/30` §九诚实边界）——单点演练通过不等于多天级联闭环

---

## F2 · 代码图谱 AST（P1）

### 现状
- Blast Radius 用文本 grep（`grep -rn "keyword"`）
- 问题：无法精准识别 import 依赖、类型引用、调用链

### 方案

**改动 1：可选依赖 tree-sitter**
```python
# scripts/dep_graph.py
try:
    import tree_sitter
    HAS_TS = True
except ImportError:
    HAS_TS = False  # 回退到 grep 模式
```

**改动 2：依赖图生成脚本**
- 输入：仓库根目录 + 目标文件列表
- 输出：`context/dep-graph.json`
- 内容：`{file: {imports: [], imported_by: [], types: [], functions: []}}`
- 支持：Python / TypeScript / Go（tree-sitter 语言包）

**改动 3：Blast Radius 升级**
- G1 Recon：优先用 dep-graph.json，无 tree-sitter 时回退 grep
- C1 影响面：从"文本匹配"升级为"AST 依赖链"
- 输出：`affected_files` + `dependency_chain` + `blast_radius_score`

### 涉及文件
| 文件 | 改动 |
|---|---|
| `scripts/dep_graph.py` | **新增**：AST 解析 + 依赖图生成 |
| `skills/aiworflow-planner/SKILL.md` | G1 使用 dep-graph |
| `docs/04-roles.md` | C1 Blast Radius 更新 |
| `context/` | 新增 `dep-graph.json` 输出 |

### 验收
- [ ] Python/TS 文件的 import 链准确
- [ ] 无 tree-sitter 时正常回退 grep
- [ ] dep-graph.json 包含双向依赖

### 工作量：4h

---

## F3 · 成本追踪（P1，v1.8.7 已落地最小归因）

### 现状（2026-09-20）
- `run_flow.py --advance --session-meta` 会把 `model`（必填）与 `tokens_used`（非负整数或 `null`）写入本轮自动 ledger；`--append-ledger --session-meta` 同样支持
- `--advance` 报告回显 `session_meta`；非法输入非零退出
- Implementer / Reviewer / Tester 报告模板含 `session.model/session.tokens_used`；宿主查不到 token 时必须写 `null`，禁止估算
- 尚未做 cumulative_tokens、按角色聚合与 metrics_summary：这属于 Wave 3 E2，等累计 ≥5 个真实 run 后触发，避免空转

### 已落地验收
- [x] 新生成的自动 ledger 条目含 `model`；传入时含 `tokens_used`
- [x] `--advance` 报告回显 `session_meta`
- [x] 非法 `--session-meta` 被拒绝且原因可读
- [x] 角色报告契约要求 model 必填、tokens 诚实可为 null

### 后续（Wave 3 E2 触发后）
```yaml
run_summary:
  total_tokens: 45000
  by_role: {}
  by_block: {}
```
- 涉及 `metrics.yaml`、`metrics_summary.py` 与 G10 写入；当前明确不做。

### 工作量：最小归因 1h；聚合统计 2h（触发后）

---

## F4 · 向量检索记忆（P2，分阶段）

### 现状
- `context/` 纯文件，按目录浏览
- 问题：积累大量知识后，关键词匹配不够

### 方案（不引入外部依赖）

**Phase 1：结构化索引 + BM25（纯 Python，先落地）**
- `context/index.yaml`：每条知识带 `tags`、`keywords`、`created_at`
- `scripts/context_search.py`：纯 Python BM25 关键词检索
- G1 读 context 时：先用 index 筛选相关条目，再读全文

**Phase 2：可选 embedding（后续）**
- 检测 `sentence-transformers` 是否可用
- 可用：`context/embeddings.npy` 向量索引
- 不可用：回退 BM25

**不做的事**
- ❌ 不引入 Pinecone / Weaviate 等外部服务
- ❌ 不做实时 embedding API 调用（离线批量）
- ✅ 纯文件 + 纯 Python BM25 已能满足 <100 条知识的检索

### 涉及文件
| 文件 | 改动 |
|---|---|
| `context/README.md` | 增加 index.yaml 格式说明 |
| `scripts/context_search.py` | **新增**：BM25 检索 |
| `skills/aiworflow/SKILL.md` | G1 用 search 而非全读 |

### 验收
- [ ] 20 条知识中搜索"权限"能命中相关条目
- [ ] 无外部依赖即可运行

### 工作量：Phase 1 = 2h

---

## F5 · 定量评估基准（P1）

### 现状
- selftest 70/70（站点在线口径；v1.8.7 起含 session-meta 与 review preflight，v1.8.8 起含 checkpoint/state/ledger 消费）仍只测结构与可恢复组件，不做质量度量
- 问题：不知道"成功率高不高""平均耗时多少""回滚几次"

### 方案

**改动 1：Run 结果数据采集**
```yaml
# 每个 Run G10 Close 时写入 runs/<RUN-ID>/metrics.yaml
run_metrics:
  run_id: "RUN-20260918-001"
  task_type: "feature"       # feature/bugfix/refactor/verification
  task_size: "medium"        # small/medium/large
  duration_minutes: 45
  blocks_total: 16
  blocks_completed: 16
  blocks_retried: 2
  findings_count: 3
  findings_blocking: 1
  rollback_count: 0          # Finding 返修次数
  final_verdict: "ACCEPTED"  # ACCEPTED/BLOCKED/ABANDONED
  timestamp: "2026-09-18T..."
```

**改动 2：聚合脚本**
```bash
python3 scripts/metrics_summary.py --runs runs/ --output metrics-report.yaml
```
输出：
- 按 task_type 的成功率
- 平均耗时（按 task_size 分）
- 平均回滚次数
- Finding 密度（个/千行变更）

**改动 3：趋势追踪**
- `runs/metrics-history.yaml`：追加每次 Run 的关键指标
- 积累 ≥10 个 Run 后生成基线
- 后续 Run 与基线对比（偏移超 20% 告警）

### 涉及文件
| 文件 | 改动 |
|---|---|
| `skills/_shared/templates/run-state.yaml` | 新增 metrics 字段 |
| `skills/aiworflow-planner/SKILL.md` | G10 写入 metrics |
| `scripts/metrics_summary.py` | **新增**（与 F3 共用） |
| `docs/13-roadmap.md` | 更新评估能力状态 |

### 验收
- [ ] 每个 Run 产出 metrics.yaml
- [ ] metrics_summary.py 输出按类型成功率
- [ ] ≥10 个 Run 后能生成基线

### 工作量：2h

---

## F6 · state.yaml 并发写保护（P1；2026-09-23 已落地 v1.8.14，RUN-20260923-002）

**背景**：双宿主（Claude Code / Codex）日常使用同一 run 时，引擎「读→改→写」无锁——两个一次性 CLI 命令并发操作会「后写覆盖先写」静默丢账本/块状态；2026-09-23 归账实测踩中同型事故（旧快照覆写 skip 状态）。

**已落地方案（乐观并发，零依赖）**：`load_run_state()` 记字节指纹（运行时键不落盘）→ `save_run_state()` 保存前重读比对 → 不一致 `AIW_STATE_CONFLICT` 拒绝写入且绝不覆盖 → 写入 temp+`os.replace` 原子替换；state.yaml 全部 9 处写点收口该函数。同包修复 R-1（advance 缺 task.yaml 告警）/ R-2（--init 相对 workflow_path）。

- [x] 并发冲突拒绝且他人版本完好（selftest §14-1）
- [x] 正常路径零回归：全量 selftest + validate_package/validate_run（§14-2，C2）
- [x] 原子写无 .tmp 残留（§14-2）
- [x] 恢复链缺件可见 + 容器可搬迁（§14-3/4，C4）

**遗留边界**：守卫覆盖走引擎命令的写入者；绕过引擎直接改写 state.yaml 的行为仍由协议纪律约束（validate_transition 快照 + pre-commit）。写入者一律走引擎命令。

---

## 实施优先级

| 顺序 | 能力 | 工作量 | 依赖 | 效果 |
|---|---|---|---|---|
| **第 1** | F3 成本追踪 | 1h | 无 | 立即可见"钱花在哪" |
| **第 2** | F5 评估基准 | 2h | F3 | 知道"好不好"而不只"对不对" |
| **第 3** | F1 长时运行 | 2h | 无 | 支持 12h+ 大任务 |
| **第 4** | F4 Phase1 向量索引 | 2h | 无 | 知识积累后可检索 |
| **第 5** | F2 AST 图谱 | 4h | tree-sitter 可选 | Blast Radius 精度×10 |

**总计：11h，全部不新增核心依赖。**

---

## 2026-09-20 修订 · 外部检索驱动执行计划（v1，登记版）

> 背景：2026-09-20 全网检索（GitHub 周榜直抓 25 仓 + 12 组检索，2026-09 为主），过滤出 5 项有意义改进。本节是当轮批准的执行计划，**操作顺序上取代上方"实施优先级"表**；上表保留为历史登记，其 F1-F5 编号继续沿用。
> 分工：Codex 实施，Claude Code 事后独立检查（检查清单见本节末尾）。

### Wave 1 · v1.8.7（~3h）

**A · F3 归因落地（1h）**
- `scripts/run_flow.py`：新增 `--session-meta '{"model":"...","tokens_used":N}'`——本次调用写入的每条 ledger 轮次条目自动带上该字段，`--advance` 报告回显 `session_meta`
- 角色输出契约（各 SKILL.md）：会话必报 `model`；宿主可查时报 `tokens_used`，查不到写 `null`（诚实优先，禁止伪造）；Planner 推进命令模板带 `--session-meta`
- selftest 新用例：`--advance --session-meta` 后 state.yaml ledger 条目含 `model`（66→67）

**B · Reviewer 确定性前置层（2h）**
- 新增 `scripts/review_preflight.py`：只读 git diff（base/head 取 state.yaml `repository`，指向主仓），4 条确定性规则——① secret 扫描（diff 新增行，复用 `secret_inline` 护栏正则思路，占位符白名单豁免）② 禁改区（diff 不得触碰 runs/ 账本与 state.prev.yaml）③ 破坏性命令模式（git reset --hard / checkout -- / rm -rf）④ 规模门（diff 超阈值 WARN）；默认输出到 stdout 以保持 Reviewer 只读，Planner明确授权时才用 `--output` 落持久报告；存在 FAIL 退出非 0
- `skills/aiworflow-reviewer/SKILL.md` 第 0 步接线：preflight FAIL 项直接进 findings（`category: deterministic`），LLM 不复看机器已判的
- selftest 两条用例：伪造 secret 的 fixture diff → FAIL 且指出行号；干净 diff → PASS（67→69）

**Wave 1 收口（v1.8.7）**：VERSION、README（状态行/版本史/核心数字）、docs/30、context/project-aiworkflow.md 同步；`install_skills.py --upgrade --apply`；selftest 全绿（在线 69/69；站点未启动时 §12 SKIP，语义同 v1.8.6）。

### Wave 2 · v1.8.8（~2h）

**C · F1 瘦身（~1h）**
- 本文件 F1-R 验收条件加第 5 条：`[ ] 恢复会话首个动作是读 ledger/checkpoint 确认已提交物；已 completed 块的外部副作用（migration/commit/push）零重复执行`
- `scripts/task_resume.py`：run 目录存在 `checkpoint.yaml` 时解析并输出"checkpoint 快照"段（round/timestamp/各块状态）+ 硬指令"completed 块禁止重跑副作用"（消除当前 0 处引用）
- selftest §13 新用例：带 checkpoint.yaml 的 fixture，task_resume 输出含快照段与不重复指令（69→70）

**D · 串行语义声明（10min）+ 顺手项（30min）**
- `docs/04-roles.md` 新小节《单活跃角色与串行推进（设计边界）》：frontier 可多块就绪，解释器每轮推进 ready[0]、单活跃角色是 Planner 唯一写入者治理的**有意设计**；并行发生在工作包层（多 run/多 worktree，与主仓 wango-delivery 协议一致），不在 run 内；run 内并行将来需登记新 F 项评估
- 本文件 F1 区加一行引用上述小节
- `review.yaml`/`test-report.yaml` 模板顶部加 `human_summary: {verdict, blocking_count, next_step}`；Reviewer/Tester SKILL 同步
- `skills/_shared/contracts/rule-lifecycle.md` 复检触发条件加"模型替换（更换供应商/模型系列）"

**Wave 2 收口（v1.8.8）**：同 Wave 1 纪律，selftest 在线 70/70。

### Wave 3 · 触发式（只登记触发条件，现在不实施）

| 项 | 内容 | 触发条件 | 工时 |
|---|---|---|---|
| E1 · F4 Phase 1 | context_search.py（纯 Python BM25）+ context/index.yaml + G1 改"先 search 再全读" | context/ 条目 >30 或 G1 读上下文成本可感 | 2h |
| E2 · F5 手工版 | metrics.yaml 模板 + G10 写入 + metrics_summary.py 聚合 | 累计 ≥5 个真实 run | 2h |

### 硬约束（实施方必须遵守）

- `.ai_worflow` 非 git 仓库：禁止一切 git 写操作（add/commit/branch/stash 等）
- runs/ 既有 run 容器只读；selftest 临时 fixture 沿用 `RUN-197001xx-999` 命名且用完即删（仓库既有模式）
- 零新外部依赖（stdlib + 已有 PyYAML）
- `tokens_used` 查不到写 `null`，禁止编造成本数字
- 不得宣称"checkpoint 恢复已实战验证"（F1-R 声明边界在真实演练通过前有效）
- 明确不做：双宿主 run 级对照（单独安排）、run 内并行、公共基准接入、embedding、数据库

### 检查清单（Claude Code 事后独立执行）

1. **全量 diff 审阅**：改动文件集合 ⊆ 计划集合，越界即 flag
2. **实跑**：selftest 70/70（在线口径）；check_all WARN 基线核对（≤2）；安装收据 1.8.8 且 --check 通过
3. **行为抽查**（不单信 selftest）：临时 run 目录跑 `--advance --session-meta` 亲验 ledger 字段；伪造 secret diff 跑 review_preflight；带 checkpoint 的 fixture 跑 task_resume
4. **接线 grep**：`--session-meta` 解析 / task_resume 对 checkpoint.yaml 引用 ≥1 / reviewer SKILL 第 0 步 / rule-lifecycle"模型替换" / 模板 human_summary / docs/04 串行小节
5. **边界核查**：runs/ 真实容器零改动；新脚本 import 仅 stdlib + yaml；README 版本史与 VERSION 一致

### 2026-09-20 实施收口记录（v1.8.8）

- **状态**：Wave 1 与 Wave 2 已实施；Wave 3 继续保持触发式，不实施。
- **实施中发现并修复的假闸门**：selftest §4 原来只跑 `install_skills.py --dry-run`，该命令对“版本相同但指纹漂移”可返回 0，导致本机锁定检查假 PASS；现改为同来源根时必须跑 `--check` 且退出码为 0。
- **代码与接线**：`run_flow.py --session-meta`、`review_preflight.py`、`task_resume.py` checkpoint/state/ledger 消费、Reviewer Preflight、Review/Test `human_summary`、角色报告 `session` 字段、模型替换/供应商切换复检、run 内串行治理边界均已落地。
- **验证证据**：`python3 -m py_compile scripts/*.py`、全部 shell `bash -n`、4 个正式 workflow 校验、`validate_package.py`、`validate_consistency.py`、在线内容/站点校验、`check_all.py`（FAIL 0 / WARN 2，WARN 为既有登记白名单）、`selftest.sh` 70/70（站点在线）全部通过。
- **双宿主安装**：Codex `~/.codex/skills` 与 Claude Code `~/.claude/skills` 均为 1.8.8 symlink，`install_skills.py --check` 指纹一致；pre-commit hook `--check` 通过。
- **真实 run 抽查**：对历史 `RUN-20260920-003` 只读执行 `review_preflight.py`，secret/禁改区/破坏性命令 PASS，规模门 WARN（35 个文件、6,645 行），证明 WARN 不误判为 FAIL。该抽查不冒充下一个真实 review 块的 PREFLIGHT 入账证据。
- **仍不宣称**：L3 真实断点演练、多天 Session×Run 实战、Wave 3 检索/指标能力。

### 2026-09-20 独立检查结论（Claude Code）与 v1.8.9 处置

- **检查结论**：APPROVE——上方 5 步检查清单全部执行（全量 diff 审阅 / selftest 70/70 实跑 / 三项行为抽查 / 接线 grep / 边界核查），8 项计划外变更均有正当理由并逐条核过；`install_skills.py` §4 dry-run 假闸门为真实缺陷，修复正确。
- **4 条 P3 发现，v1.8.9 全部收口**：
  - **F-01** `review_preflight.py` REVIEW_SIZE 消息打印 `changed_lines` 而阈值比较 `added_lines`（口径不一致，会误导 Reviewer 对照报告顶部 `changed_lines` 字段）→ 已统一为 added lines 口径。
  - **F-02** PROTECTED_PATHS 对 `.ai_worflow` 仅符号性生效（本目录非 git 仓库，其 runs/ 不会出现在被审 diff）→ 判定为设计边界而非缺陷，已作为纵深防御说明落 `docs/30` §十二（拦截对象是主仓 diff 中同名路径）。
  - **F-03** secret 告警回显命中串前 8 字符（含密钥材料，告警本身泄密）→ 改为仅回显规则类别（sk-key / bearer-token / key-assignment），selftest §7d-quatro 增加「密钥材料不回显」断言。
  - **F-04** v1.8.7 实施期存在未申报的措辞统一（「0 外部依赖」→「不新增外部依赖（当前运行环境已有 PyYAML）」，波及 docs/29/31/33、scripts/README 表述）→ 变更本身正确（docs/21 引用的外部原文 untouched），属流程申报缺失，本节补记声明。

## F7 · 引擎 CLI 契约收口（2026-09-23 已落地 v1.8.15，RUN-20260923-004）

来源：docs/13 两项登记缺口（RUN-20260923-002 实测 skipped 无凭据参数 + 未知 flag 静默忽略；
RUN-20260923-003 实测 standalone `--execute-check` 不落状态无告警）。

- [x] 未知参数 `[AIW_UNKNOWN_FLAG]` 显式 FAIL（退出码 2，不做任何状态变更）
- [x] `--status skipped` 写时凭据 `--skip-reason <text>` / `--error-codes <A,B>`（缺凭据
      `AIW_SKIP_CREDENTIAL_MISSING`；只给 reason 默认 `BRANCH_NOT_TAKEN`；误用于非 skipped
      意图先报参数错，不被证据门禁遮蔽）
- [x] standalone `--execute-check` 必 WARN（check/script 块唯一完成路径 `--advance --execute-check`）
- [x] selftest 99→107（§15 八断言全为「护栏证明会开火」负例/正例；count_sync 移 §16）
