# 09 · 让 AI 编写工作流（Authoring Copilot）

本篇定义"用自然语言让 AI 生成/修改 `workflows/*.workflow.yaml`"时的授权、评审门禁与硬护栏。参考 Skyvern 的 Workflow Copilot（`references/skyvern/skyvern/forge/sdk/copilot/`，约 90 个模块），只取其治理结构，不取其云实现。

## 授权：谁可以改工作流定义

| 动作 | 需要 |
|---|---|
| 新建草稿定义 | 任何角色可写草稿，但**不得自称可执行** |
| 让草稿成为可执行定义 | `validate_workflow.py` 通过 + Reviewer `APPROVE` + 用户批准 `*`（当定义包含 `star` 块或会触发不可逆动作时） |
| 修改已批准定义 | 走变更控制（`05-state-and-evidence.md`）：`EDITORIAL` / `TECHNICAL` / `BEHAVIORAL` / `SCOPE` |
| 删除块、放宽门禁、去掉 `star` | 一律 `BEHAVIORAL` + 用户批准 `*`，AI 不得自行放宽 |

Skyvern 的对应事实：Copilot 的 `update_and_run` 路径要求先有一次 skipped run（`_update_and_run_requires_skipped_run`，`copilot/tools/guardrails.py:139`），凭据类草稿同理（`:128`）。翻译过来：**改完就自动跑，必须先有一次可对照的空跑/校验记录**，不允许"改完直接对生产执行"。

## 硬护栏（author-time hard blocks）

Skyvern 用 `AUTHOR_TIME_HARD_BLOCKS = {code_safety, credential_scout, banned_blocks}`（`copilot/author_time_block.py:14`），并且 `AuthorTimeBlock` 构造时校验 `block_id` 必须在这个集合里——**新增校验器不能悄悄变成一堵墙，必须改这个常量**。三个 ADR 理由写在源码注释里：不安全代码会被持久化并在组织的浏览器里长期执行；凭据一旦被写进持久草稿就是不可逆泄露；被禁块会绕过强制迁移路径。

我的等价硬护栏（`scripts/validate_workflow.py` 静态拒绝，非人工裁量）。下表每一行都是**已实现并被反例证明会开火**的规则，不是意图声明：
「证明」列给出 `workflows/_invalid/` 下的专属反例，`selftest.sh` §9 逐条断言其护栏 ID 真实出现在拒绝输出中；护栏 ID 必须在 `GUARDRAIL_IDS` 注册，`Errors.add` 传入未注册 ID 会直接抛错——注册了却没有任何反例触发的「死护栏」同样被 §9 判失败。

| 护栏 ID | 拒绝什么 | 为什么不可逆 | 证明（专属反例） |
|---|---|---|---|
| `secret_inline` | `secret`/`credential` 类参数出现 `value`/`default`/`default_value`/`literal`；参数值或 `commands[].cmd` 命中凭据字面量模式 | 定义会被提交、复制、渲染进 Prompt | `_invalid/secret-inline.workflow.yaml` |
| `unsafe_command` | `commands` 中出现 `rm -rf`、`git push --force`、`git reset --hard`、`git clean`、`git checkout --`、下载后管道到 shell、`DROP TABLE`、`chmod 777`、`mkfs` | 破坏性且不可回滚 | `_invalid/unsafe-command.workflow.yaml` |
| `star_bypass` | `star: true` 块被设 `continue_on_failure: true`，或 `approve` 块 `role != user` / 缺 `star` | 人工边界被模型代签 | `_invalid/star-bypass.workflow.yaml` |
| `banned_block` | 使用未注册 `block_type`；`review`/`release_check` 不是 `reviewer`；`gate` 与 `role` 不匹配（如 `implement` 承担 G5 审核） | 职责分离被绕过 | `_invalid/self-review.workflow.yaml` |
| `unbounded_loop` | `while_loop`/`for_loop` 缺正整数 `max_iterations` 或 `loop_blocks` 为空；顶层图存在环 | 无限烧 token | `_invalid/unbounded-loop.workflow.yaml` |
| `unbounded_retry` | `max_attempts` 不是 `1..MAX_ATTEMPTS_CAP`（当前 5）的整数 | 失败路径无限重试，烧 token 且不收敛 | `_invalid/unbounded-retry.workflow.yaml` |
| `evidence_free_gate` | `gate` 非空但块没有非空 `evidence` 列表 | 门禁变成口头声明 | `_invalid/evidence-free-gate.workflow.yaml` |

护栏失败必须返回**精确、可动作**的错误，而不是笼统拒绝；每条错误形如 `[护栏ID] $[i] (label): 具体字段 + 为什么 + 怎么改`。

有界性是三层叠加，不靠任何一层单独兜底：**author-time** 拒绝无界定义（`unbounded_loop` / `unbounded_retry`）→ **运行期** `run_flow.py` 拒绝超过 `max_attempts` 的重试并打印剩余次数 → **角色层** `docs/07` 的「同一块自愈 ≤2 次，第 3 次 `BLOCKED` 升级给人」。

## 评审门禁：diff 投影，不读全文

Skyvern 的 `copilot/review_gate.py` 做三件值得照搬的事：

1. **块指纹**忽略 `label` 与 `next_block_label`（`_IGNORED_FINGERPRINT_KEYS` / `_IGNORED_COMPARISON_KEYS`，`:26-27`）——改个名字不算行为变化，评审不该被噪音淹没。
2. **参数解析身份**：把参数引用还原成身份再比较（`_resolved_identity_value`，`:72`），避免"换了个写法指向同一凭据"被当成新授权。
3. **重复写入检测**（`_duplicate_writes`，`:308`）与**评审投影**（`build_review_projection`，`:329`）：只把真正变化的块投影给评审者，并附执行回执（`serialize_execution_receipts`，`:272`）。

对应规则：AI 修改工作流后，必须产出**评审投影**（新增/删除/语义变化的块列表 + 每条的护栏结果 + 校验器输出），Reviewer 审投影而不是重读整份 YAML。纯 label 重命名、纯注释、纯顺序等价格改写记为 `EDITORIAL`。

## 完成判据（completion_contract）

Skyvern 把"完成"变成可判定的契约，而不是一句"我做好了"：

- 定义侧：`WorkflowDefinitionYAML.completion_contract`（`skyvern/schemas/workflows.py:1593`）。
- 判据集合不可变，整体取代而非逐条编辑；过期只降级为重新生成，不会变成永久卡死（`copilot/completion_criteria_store.py` 模块文档串）。
- 判定侧：`copilot/completion_verification.py` 用固定原因码 `{evidence_confirms, no_evidence, evidence_contradicts, unknown}`（`:49`）+ 结构性/条件性弃权码（`:50-53`），证据字段有长度上限（`_EVIDENCE_VALUE_MAX_CHARS = 2000`、`_EVIDENCE_REF_MAX_CHARS = 240`、`_MISSING_EVIDENCE_MAX_CHARS = 500`，`:44-46`），未满足项由 `summarize_unsatisfied_outcomes`（`:634`）汇总成人可读结论。

我的强制形式：每条 `completion_contract` 项 = `{id, 判据文本, 证据要求, 决策角色}`，判定结果只能取上面四个原因码之一，**`unknown` 不等于通过**。缺证据写 `no_evidence`，矛盾写 `evidence_contradicts`，两者都使 G10 不通过。

## 生成质量约束（防止 AI 写出"看起来对"的定义）

- **别名归一化**：模型爱写 `type: llm` / `block-type` 之类变体，先归一化再校验（Skyvern `copilot/block_type_aliases.py`），归一化不了的直接报错，不猜。
- **链修复要显式**：断裂的 `next_block_label` 链可以自动修复，但修复动作必须写进评审投影（Skyvern `copilot/workflow_yaml.py` 的 chain repair）。
- **参数绑定不变量**：引用未声明参数 = 错误（`_parameter_binding_invariant_error`，`guardrails.py:212`），并给出该参数类型的占位符建议（`_PARAMETER_TYPE_PLACEHOLDERS`，`:198`）。
- **输出策略护栏**：块输出不得绕过声明的输出契约（`_workflow_yaml_output_policy_guardrail`，`:48`）。
- **秘密脱敏**：进 Prompt 前脱敏原始秘密（`copilot/request_policy.py: redact_raw_secrets_for_prompt`），诊断文本有长度上限（`diagnosis_repair_contract.py`：`_TEXT_MAX = 240`、`_SUMMARY_MAX = 180`、`_MAX_ITEMS = 20`）。
- **修复要绑根因**：返修请求带根因签名（`compute_repair_root_cause_signature`，`copilot/failure_tracking.py`），同一根因第二次失败换新会话，不在原上下文里叠补丁。

## 禁止项

- 不得生成"为了通过校验而放宽"的定义（例如给 `review` 块换个 `block_type` 躲开角色一致性检查）。
- 不得在没有用户批准 `*` 的情况下，把包含 push、部署、删除、真实 mutation 的命令写进 `commands`。
- 不得把生成结果直接写成"已验证"；生成 ≠ 校验 ≠ 实机运行，三者在 `state.yaml` 中分别记录。
