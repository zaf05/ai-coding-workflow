# 12 · 参考工程扫描报告

本篇是"这条规则从哪来"的唯一证据索引。所有条目均为本次实测（路径 + 行号 + 关键内容），非记忆推断。

## 克隆事实

```bash
cd /home/feifz/workspace/WanGoPlatform/.ai_worflow/references
git clone --depth 1 https://github.com/Skyvern-AI/skyvern.git
git clone --depth 1 https://github.com/lichong-a/ric-dev-workflow-skills.git
```

| 仓库 | commit | 文件数（排除 `.git`） | 验证命令 |
|---|---|---|---|
| `references/skyvern` | `35cb497` "Add a web search helper for code blocks and the Copilot …(SKY-15737) (#8464)" | 5496 | `find . -not -path './.git/*' -type f \| wc -l` |
| `references/ric-dev-workflow-skills` | `84954fb` "docs(readme): 展示四角色流转并解释 Brownfield" | 95 | 同上 |

两者按仓库根 `.ai_worflow/.gitignore` 排除（`references/`），只读参考，不作为规则源。

## A. Skyvern：取走了什么

### A1 工作流即块 DAG

| 事实 | 位置 | 我用在哪 |
|---|---|---|
| `BlockType(StrEnum)` 共 31 个成员（task…data_export） | `skyvern/schemas/workflows.py:475-506` | `docs/02-block-catalog.md` 的 21 种块设计 |
| `BlockYAML(BaseModel, abc.ABC)`：YAML 侧块定义基类 | `skyvern/schemas/workflows.py:776` | `workflows/*.workflow.yaml` 的字段模型 |
| `Block(BaseModel, abc.ABC)`：运行时块基类（label / next_block_label / output_parameter / continue_on_failure / …） | `skyvern/forge/sdk/workflow/models/block.py:765` | 块通用字段表 |
| `WorkflowDefinitionYAML` + `completion_contract: dict \| None` | `skyvern/schemas/workflows.py:1586,1593` | `docs/09-authoring-copilot.md` 完成契约 |
| DAG 执行入口 `_execute_workflow_blocks_dag` | `skyvern/forge/sdk/workflow/service.py:6320` | Flow 层执行语义（`skills/aiworflow`） |
| `_strip_finally_block_references`（校验/执行前把 finally 从连边剥离） | `skyvern/forge/sdk/workflow/service.py:8257`，调用点 `:6124,6335,8392` | finally 块规则 |
| `InvalidFinallyBlockLabel` / `NonTerminalFinallyBlock` 在**建模期**抛出 | `skyvern/forge/sdk/workflow/exceptions.py:23,32`；`models/workflow.py:167,170` | "图校验在持久化之前"原则 |

### A2 参数与秘密

| 事实 | 位置 |
|---|---|
| `ParameterType(StrEnum)`、`is_secret_or_credential()` | `skyvern/forge/sdk/workflow/models/parameter.py:25,38` |
| `is_sensitive_workflow_parameter(param)` 单一事实源过滤 | `skyvern/forge/sdk/workflow/models/parameter.py:269` |
| 秘密脱敏进 Prompt：`redact_raw_secrets_for_prompt` | `skyvern/forge/sdk/copilot/request_policy.py` |
| 秘密擦除工具（console log / HAR） | `skyvern/utils/secret_redaction.py` |

→ 我的 `secret` 参数禁止内联值、渲染后做秘密检测（`docs/06`）。

### A3 错误码白名单

| 事实 | 位置 |
|---|---|
| `filter_to_user_defined_codes(...)`：把 LLM 幻觉出的码过滤到用户定义白名单 | `skyvern/errors/errors.py:41` |

→ 我的 `error_codes` 必须是 `error_code_mapping` 的键，`AIW_*` 命名（`docs/07`）。

### A4 渐进确定性与缓存（`docs/08` 的主来源）

| 事实 | 位置 |
|---|---|
| 官方内部说明文档：progressive caching、`run_with: code` 门槛、条件块不缓存、批量查询优化、块级脚本生成 | `skyvern/core/script_generations/CLAUDE.md`（全文） |
| `ScriptBlock.run_signature: str \| None  # The function call code to execute this block` | `skyvern/schemas/scripts.py:227,234` |
| `run_signature` 迁移（说明它是后加的固化门槛字段） | `alembic/versions/2025_10_14_2232-b80c42316c94_add_run_signature_to_script_block.py` |
| `BLOCK_TYPES_THAT_SHOULD_BE_CACHED` / `is_block_type_cacheable` 定义在脚本服务，被 workflow service 复用 | 定义：`skyvern/services/workflow_script_service.py`；复用：`skyvern/forge/sdk/workflow/service.py:259` |
| 块完成时生成 pending 脚本：`_generate_pending_script_for_block` | `skyvern/forge/sdk/workflow/service.py:6262`，调用点 `:6653` |
| 再生成决策：`generate_script_if_needed` | `skyvern/forge/sdk/workflow/service.py:12664` |
| 自愈日上限（缓存未配置 fail-open，缓存报错 fail-closed，带分布式锁原子占位） | `skyvern/services/self_heal_cap.py`（`check_and_increment_self_heal_cap`、`self_heal_daily_cap_key`） |
| 脚本复审日上限 v2/v3 双版本 + 实验分流 | `skyvern/services/script_review_cap.py` |
| 缓存行为测试（同块二次运行不再生成、新块触发再生成、条件分支渐进缓存、不可缓存类型跳过） | `tests/unit/test_conditional_script_caching.py`、`tests/unit/test_forloop_script_generation.py`、`tests/unit/test_nested_forloop_caching_tracking.py` |

### A5 Copilot 治理（`docs/09` 的主来源）

| 事实 | 位置 |
|---|---|
| Copilot 模块约 90 个文件（authoring / 完成校验 / 护栏 / 秘密 / 修复契约） | `skyvern/forge/sdk/copilot/`（`ls` 实测） |
| `AUTHOR_TIME_HARD_BLOCKS = {code_safety, credential_scout, banned_blocks}`，每个常量上方有 ADR 编号与不可逆理由；`AuthorTimeBlock.__post_init__` 对集合外 ID 抛错（"新校验器不能悄悄变成墙"） | `skyvern/forge/sdk/copilot/author_time_block.py:6-14,24-38` |
| 评审门禁：指纹忽略 `label`（`_IGNORED_FINGERPRINT_KEYS`）与 `label/next_block_label`（`_IGNORED_COMPARISON_KEYS`）、参数身份还原、重复写入检测、评审投影、执行回执序列化 | `skyvern/forge/sdk/copilot/review_gate.py:26-27,72,272,308,329` |
| 完成校验：原因码白名单 `{evidence_confirms,no_evidence,evidence_contradicts,unknown}`、结构性/条件性弃权码、证据长度上限 2000/240/500、`summarize_unsatisfied_outcomes` | `skyvern/forge/sdk/copilot/completion_verification.py:44-53,634` |
| 判据集合不可变、整体取代、过期降级为重新生成而非永久卡死 | `skyvern/forge/sdk/copilot/completion_criteria_store.py` 模块 docstring（SKY-10931） |
| 工具输入护栏：输出策略护栏、"改完即跑"必须先有 skipped run、凭据草稿同理、参数绑定不变量、按参数类型给占位符 | `skyvern/forge/sdk/copilot/tools/guardrails.py:48,128,139,198,212` |
| YAML 归一化 + 链修复 + 块类型别名 | `skyvern/forge/sdk/copilot/workflow_yaml.py`（1236 行）、`block_type_aliases.py` |
| 诊断/修复契约的文本长度上限（240/180/20 条）与失败状态集合 | `skyvern/forge/sdk/copilot/diagnosis_repair_contract.py:33-37` |
| 根因签名（同一根因二次失败换会话的依据） | `skyvern/forge/sdk/copilot/failure_tracking.py: compute_repair_root_cause_signature` |

### A6 Prompt 工程

| 事实 | 位置 |
|---|---|
| 模板拆 static（可缓存前缀）/ dynamic（运行时后缀），且"static 必须与完整模板前缀逐字一致" | `skyvern/forge/prompts/skyvern/CLAUDE.md`（全文 8 行） |
| `PROMPT_HARD_CEILING_TOKENS = 180_000`、`CEILING_FALLBACK_KEYS_BY_TEMPLATE`、安全边距与逐步丢弃 | `skyvern/utils/prompt_engine.py:57,62,250,265,288` |

### A7 Skill 包结构与 diff 驱动 QA

| 事实 | 位置 |
|---|---|
| Skill 包 = `SKILL.md` + `references/*.md`(18) + `examples/*.json`(3)；frontmatter 含 `allowed-tools: Bash(skyvern:*)` | `skills/skyvern/`（`find` 实测） |
| 同一包在 pip 内再放一份 | `skyvern/cli/skills/skyvern/SKILL.md` + 同名 references |
| diff 驱动 QA：读 `git diff` → 分类 `frontend/browser`、`backend API`、`backend-internal`、`mixed` → 选验证路径 → 带证据报 pass/fail；顶部 NOTE 声明 canonical 源与两份同步副本 | `skyvern/cli/skills/qa/SKILL.md:1-40` |
| 任务分类优先于工具选择（0 LLM 的 click/type 优先于 act，validate 优先于 extract） | `skills/skyvern/SKILL.md` Step 1 表 |

### A8 刻意**不**取的部分

浏览器自动化块语义（task/navigation/extraction/login/pdf_fill/google_sheets…）、S3/邮件/webhook、代理与反爬、FastAPI + Postgres + Alembic 运行时、前端 `skyvern-frontend`、云组织与实验分流、Redis 缓存实现。理由：我的场景是软件交付控制层，不需要浏览器执行面；引入它们只会带来无法验证的依赖。

## B. ric-dev-workflow-skills：取走了什么

结构实测（95 文件）：

```text
.agents/skills/devflow-{planner,reviewer,tester,implementer}/SKILL.md   四角色事实源
.agents/skills/devflow-*/agents/openai.yaml                            Codex 界面元数据（4 行）
.agents/skills/devflow-*/references/*.md                               角色专属参考（planner 3 / reviewer 5 / tester 4 / implementer 3）
.agents/skills/_devflow_shared/contracts/*.md                          8 份共享契约
.agents/skills/_devflow_shared/references/*.md                         领域审核参考 + languages/ 9 份
.agents/skills/_devflow_shared/templates/*.md|yaml                     17 份模板，其中 compact/ 4 份
.agents/skills/_devflow_shared/evals/*.md                              3 份场景用例
.claude/agents/*.md（4）+ .claude/skills -> ../.agents/skills（软链）
.zcode/agents/*.md（4）
.codex/agents/*.toml（4）+ .codex/config.toml
AGENTS.md / README.md / docs/DEVFLOW_SKILLS_DESIGN.md / docs/DEVFLOW_SKILLS_VALIDATION.md
```

| 事实 | 位置 | 我用在哪 |
|---|---|---|
| 四角色 + `_devflow_shared` 绝不能有 `SKILL.md`；纯指令实现，禁止工作流 CLI、编排脚本、Git 包装器、包清单、生成式状态机代码 | `AGENTS.md` "范围与结构" | `docs/01`、`docs/11`、`skills/README.md` |
| 不可妥协角色边界（Planner 不写生产代码/不批自己；Reviewer 只读三值结论；Tester 不改生产代码与已批准 Spec；Implementer 一次一个 Task；已发布报告不可变，Planner 原样追加） | `AGENTS.md` "不可妥协的角色边界" | `skills/_shared/contracts/role-boundaries.md` |
| Compact v2 四文件容器、原地修订 + 底部 Change Log、不生成 `tasks-v*` 版本矩阵 | `AGENTS.md` "编辑与验证"；`_devflow_shared/templates/compact/{state.yaml,current.md,test-plan.md,evidence.md}` | `docs/05`、`skills/_shared/templates/` |
| Root Planner 单层调度、不为 Task 再启 Planner、DAG 首次 G2 后冻结、结构性障碍才局部改图 | `AGENTS.md`；`devflow-planner/SKILL.md` "宿主入口" | `docs/04`、`docs/05` |
| 门禁分层适用不递归；不适用或已有有效证据的额外审核直接省略，但不能伪造 APPROVE | `_devflow_shared/contracts/gate-policy.md`；`AGENTS.md` | `docs/03` 适用性省略 |
| 调查默认一轮 + 一轮缺口补查，两次无新增事实停止同类搜索 | `AGENTS.md` | `skills/aiworflow-planner/references/orchestration.md` |
| Reviewer 工具最小权限：`tools: Read, Grep, Glob` | `.claude/agents/devflow-reviewer.md` frontmatter | `docs/11` |
| Codex 子代理 `sandbox_mode = "read-only"` + `model_reasoning_effort = "high"` + `developer_instructions` 只写模式选择与输出契约 | `.codex/agents/devflow-reviewer.toml` | `docs/11` |
| ZCode 子代理 `injectAgentsMd: true`，注入不替代检查局部规则 | `.zcode/agents/devflow-planner.md` frontmatter | `docs/11` |
| `state.yaml` 模板字段（root_issue / repository / artifacts / versions / approvals / tasks / open_findings / open_defects / open_blockers / pre_existing_failures） | `_devflow_shared/templates/compact/state.yaml` | `skills/_shared/templates/run-state.yaml` |
| `review.yaml` 载荷字段（review_id / supersedes / mode / target{base_sha,head_sha,tested_sha} / verdict / findings / non_blocking_notes / residual_risks / evidence_reviewed / unblock_conditions） | `_devflow_shared/templates/review.yaml` | `skills/_shared/templates/review.yaml` |
| 连续计数规则：同一问题连续三轮未解决停止叠补丁；同一产物同一审核模式连续两次 `REQUEST_CHANGES` 未收敛先暂停送审；两计数独立且不因拆分/换号清零 | `devflow-planner/SKILL.md` §3 | `docs/07`、Planner 参考 |
| 只有缺失信息会实质改变产品行为/契约/数据/权限/兼容/不可逆操作/凭据费用/脏工作区安全/源分支选择时才提问，低风险未知记为保守假设并继续 | `devflow-planner/SKILL.md` "必需输入" | Planner SKILL.md |

**刻意不取**：`references/languages/*`（9 份语言清单，与 WanGo 技术栈重复且易过期）、`.devflow/` 演示变更目录、v1 旧模板双轨兼容负担（我直接从 v2 布局起步，不做迁移路径）。

## C. 我自己的 V4.0（`ai-native-dev-pipeline-v4-full-flow.html`）

保留原文不动。取走并落到规则里的部分：13 段主流程编号（`docs/00`）、`*` 人工/授权/外部平台边界标记（块字段 `star`）、bug intake 六分类（`docs/07` B 表）、completion claim 枚举（→ `completion_contract` 四原因码）、"AI Native Trace"说法（→ `evidence.md` 只追加账本）。

## D. 复现本报告的命令

```bash
cd /home/feifz/workspace/WanGoPlatform/.ai_worflow/references/skyvern
git log --oneline -1
find . -not -path './.git/*' -type f | wc -l
sed -n '475,506p' skyvern/schemas/workflows.py
grep -n "run_signature" skyvern/schemas/scripts.py
grep -rn "def filter_to_user_defined_codes" skyvern/
sed -n '1,40p' skyvern/forge/sdk/copilot/author_time_block.py
cat skyvern/forge/prompts/skyvern/CLAUDE.md
cat skyvern/core/script_generations/CLAUDE.md

cd ../ric-dev-workflow-skills
git log --oneline -1
find . -not -path './.git/*' -type f | wc -l
cat AGENTS.md
cat .codex/agents/devflow-reviewer.toml
cat .agents/skills/_devflow_shared/templates/compact/state.yaml
```

## E. jakubkrehel/skills：取走了什么（2026-09-16 新增）

### 克隆事实

```bash
cd references
git clone --depth 1 https://github.com/jakubkrehel/skills.git jakubkrehel-skills
```

| 仓库 | commit | 文件数 | 大小 |
|---|---|---|---|
| `references/jakubkrehel-skills` | `267330e` | 11 个 skill 目录 | 820K |

### 11 个 Skill 与本工作流的映射

| jakubkrehel Skill | 作用 | 对应本工作流 | 采纳状态 |
|---|---|---|---|
| `interface-review` | 变更范围解析 → blast radius 扩展 → 逐 Finding 分类（Introduced/Regression/Pre-existing）| Reviewer 的"影响面范围"（`04-roles.md` §影响面范围） | ✅ 概念已吸收为 C1 |
| `better-interface` | 跨领域审查编排：按 accessibility→layout→writing→typography→colors→ui 顺序路由到领域 skill，合并为一份 ranked verdict | Reviewer 按维度检查、合并 verdict | ✅ 已有等价模式 |
| `better-accessibility` | 对比度、焦点、键盘导航、ARIA | Tester 的 UI 验证维度 | ✅ 已覆盖 |
| `better-layout` | 分组、对齐、阅读顺序、渐进披露 | 站点/文档布局审查 | ✅ 已覆盖 |
| `better-typography` | 标题 letter-spacing、行高角色、measure cap | 文档排版规范 | ✅ 已覆盖 |
| `better-colors` | 语义 token、ramp 结构、一色一义、对比度实测 | CSS 变量体系 | ✅ 已覆盖 |
| `better-ui` | 视觉打磨、阴影、圆角、动效 | 站点样式 | ✅ 已覆盖 |
| `better-writing` | 文案清晰度、术语一致性 | 文档写作 | ✅ 已覆盖 |
| `variant` | 生成 UI 变体方案 | 不适用 | ⚪ 不采纳 |
| `explain-interface` | 用图表解释接口 | 不适用 | ⚪ 不采纳 |
| `break` | 强制休息提醒 | 不适用 | ⚪ 不采纳 |

### 核心原则采纳

| 原则 | 出处 | 对应改进 |
|---|---|---|
| **Evidence, not taste** | `better-interface` §Evidence | 门禁证据必须是确定性命令输出，不接受"我觉得好" |
| **Blast radius = surfaces, not files** | `interface-review` §A diff is not a surface | C1 影响面范围：审的是渲染面，不只是变更文件 |
| **Read removed lines** | `interface-review` §4 | Reviewer 审 diff 时必须读 `-` 行，回归在删除行里 |
| **Classify every finding** | `interface-review` §5 | Finding 必须标 Introduced/Regression/Pre-existing |
| **Scope first, then review** | `interface-review` §1 | 影响面文件清单在审查前产出 |
| **Route to domain skill, don't duplicate** | `better-interface` §4 | 领域规则只在唯一位置维护，其他引用不复制 |
