# 16 · DAG 自动拆分、模型能力与存量/原型工程驱动

> 回答三个追问：①“LLM 生成 DAG + 确定性执行”是不是只能 Claude Code；②DAG 生成环节模型能力不够怎么办；③存量工程 / 原型（vibe coding 产物）如何用 AI 工作流驱动。所有结论都落到本仓库 `.ai_worflow` 现有 13 段门禁，不另造引擎。

## 一、直接结论

1. **不是只能 Claude Code**。“LLM 提议 DAG → 审批/冻结 → deterministic 执行器跑 DAG”是一个通用架构，Claude Code 只是其中一个消费级产品形态。任何宿主（Codex、OpenCode、Claude Code、LangGraph、Temporal/Prefect）都能实现。
2. **DAG 生成不应押注单一模型的“脑补能力”**，而应拆成“LLM 给意图与候选 DAG → 确定性编译/校验（schema、环、依赖、预算）→ 冻结 → 执行”。模型负责“想清楚”，脚本负责“保证结构合法”。
3. **原型可以 vibe coding，产品/存量代码必须切到 spec + 行为基线 + 证据门禁**。2026 的成熟做法是：先 characterization/golden master 测试锁住现状行为，再小步迁移，最后 shadow/differential 测试证明行为保真。

## 二、DAG 自动拆分不是 Claude Code 独有（事实）

| 方案 | 谁生成 DAG | 谁执行 | 是否冻结/审批 | 来源 |
|---|---|---|---|---|
| Claude Code dynamic workflows | LLM 现场写 JS 编排脚本 | 后台 runtime 拉起 subagents | 运行前可批准 plan，可存 `.claude/workflows/` | `https://code.claude.com/docs/en/workflows` |
| GitHub Spec Kit | `specify/plan/tasks` 生成结构化任务+依赖 | 宿主 Agent 增量执行 | 阶段产物门逐层送审 | `https://github.github.com/spec-kit/` |
| OpenCode `opencode-agent-teams` | 主 Agent 生成 task 依赖 DAG | plugin 拓扑排序，每层 `Promise.all` 并行执行 | 依赖/环由 plugin 校验 | `https://developer.aliyun.com/article/1745179`、npm `opencode-agent-teams` |
| `sdd-multiagent-opencode` | orchestrator 生成 DAG | DAG 调度 + 冲突检测 | 冲突检测在 scheduler | npm 快照 2026-05-17 |
| maestro-cli | YAML DAG | 依赖校验 + 环检测 + 并行执行 | 定义即声明，执行前校验 | 开源仓库（历史调研） |
| Skyvern | 可视化块 DAG + AI 辅助生成/录制 | 显式 `next_block_label` 执行 | 面向浏览器自动化，非软件研发 DAG | `https://www.skyvern.com/docs/developers/getting-started/core-concepts` |
| ric-dev-workflow-skills | Planner 生成 DAG | instruction-only 四角色，宿主执行 | **G2 通过后冻结，仅真实结构阻塞最小改图** | 本地 `references/ric-dev-workflow-skills` |

共性：**“自动拆分”发生在规划/送审阶段；执行阶段用确定性调度，不让 LLM 边跑边无限重构图。**

## 三、DAG 生成环节的模型能力怎么办

不要把“能不能跑通 DAG”交给单一模型的临场发挥，拆成四层：

1. **意图层（LLM，高 reasoning）**：从需求写 Intake/Spec、识别纵向业务场景、候选块与依赖。用默认模型（2026-09-10 实测 `~/.codex/config.toml` 为 `qifu/qwen3.8-max + high`；以实测为准，不要写死某个型号）。
2. **编译层（确定性脚本）**：把 LLM 候选 DAG 转成合法 YAML，校验 `schema_version`、`blocks[].label` 唯一、`next_block_label` 指向存在块、无环、预算不超硬上限。**已实现**：`scripts/compile_dag.py` 做归一化（id→label、type→block_type、next→next_block_label、字符串 schema_version/star 等已知漂移）+ 块数预算上限，然后委托 `validate_workflow.py` 执行全量结构规则（单一事实源，不复制规则）；编译通过产出 `*.compiled.yaml`，编译拒绝则打印全部违规项并非零退出、不保留半成品。
3. **冻结层（人/Reviewer 门禁）**：`feature-delivery` 在 `approve`（G3）批准产品行为，`plan`（G4）冻结块 DAG；冻结后非真实结构障碍不得重建全图。
4. **执行层（deterministic 或独立会话）**：当前为 instruction-only + deterministic 解释器混合。`scripts/run_flow.py` 已实现确定性 DAG 构图、环检测、frontier、STAR/HANDOFF/CHECK 与 check/script 命令执行；Planner/Implementer/Reviewer/Tester 的语义块仍由宿主 Agent 按 `skills/aiworflow/SKILL.md` 独立会话执行，状态唯一写入 Planner。

已观察到的真实约束（来自 `docs/15`）：`qwen3.7-flash + low` 在多块规划中出现过错误 schema（顶层自创 `run_id/base_sha/blocks[id]`、把多个 Planner 块合并成 `PLANNER`）。因此：

- **规划/DAG 生成用默认高 reasoning 模型**，不降级。
- **结构合法性永远由脚本兜底**，不靠 prompt 保证。
- 已有开源先例 `@kirha/planner` 用微调 Qwen3 8B 直出 DAG，但本仓库不引入新依赖/新模型，先走“大模型候选 + 脚本校验”。

## 四、存量工程 / 原型如何驱动（2026 可行方案）

### 4.1 原型（vibe coding 产物）

- 允许用 vibe coding 快速产出可交互原型，但**进入产品阶段必须做一次“冻结交接”**：把当前行为转成 Spec + AC + 测试基线，之后只走 spec→plan→implement→review→test。
- 本仓库已经内建这条路径：`AGENTS.md` 规定 MockRepository 驱动完整产品交互，未来接 HttpRepository 时不推倒页面层；页面按 P01–P36 逐页验收。映射到 ai_worflow 的 `spec(G2) → approve(G3) → plan(G4)` 就是“冻结交接”。

### 4.2 存量/遗留代码

2026 多个来源收敛为同一套顺序：

1. **行为基线先行**：先给关键路径建 characterization / golden master 测试，锁住现状行为（哪怕行为很奇怪）。不先写新代码。
2. **隔离高风险区**：无测试、复杂控制流、多调用方的模块优先识别与隔离。
3. **小步增量迁移**：strangler fig / 增量现代化，不做整仓重写。
4. **保真验证**：新旧并行跑，golden master / shadow execution / differential testing 证明行为等价，再合入。
5. **证据门禁**：每步绑定 `base_sha`、`head_sha`、测试报告；blocking Finding 稳定编号返修。

关键证据：

- AgentModernize（arXiv `2605.17535`，2026-05）：把现代化定义为**行为保真问题**，四个专职 agent（extraction / specification / code generation / validation）+ behavioral specification graph；单 prompt 基线能编译运行但行为测试 0.0%。
- Agentic Code Surgery for Brownfield（Zenodo 2026-04）：七 agent 流程，先 characterization 再动代码；相对普通 plan+implement 从 0 新测试/0.82% 覆盖率提升到 43 个新测试/16.78%。
- Claude Code Legacy Modernization（2026 实践指南）：先补测试安全网，再重构；逐块小步。
- Kellton shadow execution（2026-05）：golden master / back-to-back parallel execution 做迁移 QA。

### 4.3 映射到本仓库 13 段

| 存量/原型需求 | 本工作流已有块/门禁 | 是否缺 |
|---|---|---|
| 行为基线先行 | `recon(G1)` 可扩展到“characterization 基线”；`test(G7)` 负责回归 | 缺“characterization baseline”显式块 |
| 冻结交接 | `spec(G2)→approve(G3)→plan(G4)` | 已具备 |
| 小步增量 | 单块实现、预算硬上限 15/1500/80KB | 已具备 |
| 保真验证 | `verify_ui(G7)`、`smoke(G9)` | 缺 differential/shadow 对比块 |
| 证据门禁 | `review(G5)/release_check(G8)` | 已具备 |

## 五、下一步（可执行）

1. `docs/15` 修正模型漂移：实际默认是 `qwen3.7-plus + high`，不再写死 `qwen3.8-max`。
2. 跑 `python3 scripts/validate_package.py` + `bash scripts/selftest.sh` 取证。
3. 若要在存量工程上落地：给 `recon` 增加 characterization/golden master 基线字段，给 `test/verify_ui` 增加 differential 对比证据类型；不新增角色。
4. DAG 自动拆分：编译层已由 `scripts/compile_dag.py` 落地（含正例/漂移/反例自检，见 `scripts/selftest.sh` 第 6 节）；剩余动作是在下一个真实业务 run 中让 Planner 实际产出候选 YAML 并走「compile → G4 冻结 → run_flow 推进」全链，取得真实证据后更新 `docs/13-roadmap.md`。`run_flow.py` 已承担冻结后的确定性执行。
