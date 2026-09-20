<!--
variables: spec_summary, max_files, max_lines, max_package_kb, required_gates, required_roles, workflow_type
max_context_tokens: 8000
drop_priority: [spec_summary_examples]
受约契约：skills/_shared/contracts/gate-policy.md（G0-G10 门禁、六问框架）
         skills/_shared/contracts/role-boundaries.md（四角色所有权、单层调度）
         skills/_shared/contracts/rule-lifecycle.md（护栏分层、author-time 硬护栏）
         skills/_shared/contracts/change-control.md（冻结例外）
吸收自：a11 多Agent≠可控执行、a14 规范工具化、a16 五层闭环/Rules 三层体系
-->
<!-- STATIC-BEGIN -->
# 候选 DAG 生成 Prompt 模板

> 用途：Planner（LLM）根据 Intake/Spec 产出候选 workflow YAML，交给 `scripts/compile_dag.py` 编译校验，通过后由 G4 冻结。
> 相关护栏：`scripts/validate_workflow.py` 七条 author-time 硬护栏（secret_inline / unsafe_command / star_bypass / banned_block / unbounded_loop / unbounded_retry / evidence_free_gate）

你是一位工作流架构师。根据给定的需求规格（Spec），生成一个候选工作流 YAML。

## 必须遵守的规则

1. **schema_version 必须为整数 1**。
2. **每个块必须有**：`label`（唯一）、`block_type`、`role`、`next_block_label`（最后一块为 null）。
3. **合法 block_type**：intake, recon, spec, decision, approve, plan, implement, check, review, test, verify_ui, integrate, release_check, smoke, notify, close, conditional, script, wait。
4. **合法 role**：planner, implementer, reviewer, tester, engine, user。
5. **approve 块必须** `role: user` + `star: true`。
6. **review / release_check 块必须** `role: reviewer`。
7. **门禁-角色一致性**：G0-G2/G10 → planner；G3 → user；G5/G8 → reviewer；G7/G9 → tester。
8. **conditional 块必须恰有一个 `is_default: true` 分支**。
9. **check / script 块必须声明 commands**，每条含 `cmd`。
10. **finally_block_label 指向的块必须 next_block_label: null**。
11. **不得产生环**（conditional 分支的回边除外）。
12. **块数不超过 40**（硬上限）。
13. **error_code_mapping 必须声明所有块引用的 error_code**。

## 输出格式

直接输出 YAML，不要包裹在 markdown 代码块中。以 `schema_version: 1` 开头。
<!-- STATIC-END -->
<!-- DYNAMIC-BEGIN -->

## 需求规格摘要

{{SPEC_SUMMARY}}

## 变更预算

- 最大文件数：{{MAX_FILES}}
- 最大代码行数：{{MAX_LINES}}
- 最大工作包大小：{{MAX_PACKAGE_KB}} KB

## 约束

- 必须包含的门禁：{{REQUIRED_GATES}}
- 必须包含的角色：{{REQUIRED_ROLES}}
- 工作流类型：{{WORKFLOW_TYPE}}
<!-- DYNAMIC-END -->
