# Evidence · Run {{ run_id }}

<!-- 只追加账本：记录一经发布不可修改。修正由原作者发布新 ID + supersedes。 -->
<!-- 每次追加一段，按时间顺序，不重写历史。 -->
<!-- STATIC-BEGIN -->
## Ledger
<!-- DYNAMIC-END -->

<!-- ═══════════════════════════════════════════════════════════════ -->
<!--  以下五类记录是必须入账本的（没有第六类）。                      -->
<!--  □ REVIEW-xxx   # 审核报告（SPEC_REVIEW / CODE_REVIEW / TEST_REVIEW / RELEASE_REVIEW） -->
<!--  □ IMPL-xxx     # 实现报告（每块一次，含 files_changed / tests_run / 直接验证证据） -->
<!--  □ CHECK-xxx    # 确定性检查报告（命令输出 / exit_code vs expect） -->
<!--  □ APPROVAL-xxx # 用户批准（不代签，转录原话与批准范围）          -->
<!--  □ DEFECT-xxx   # 独立发现的缺陷（Tester 或 Reviewer 产出）      -->
<!-- ═══════════════════════════════════════════════════════════════ -->

<!-- 示例 1：审核报告（已有，保持） -->
<!--
## REVIEW-001 · SPEC_REVIEW · reviewer · 2026-09-08T10:00+08:00

```yaml
review_id: REVIEW-001
mode: SPEC_REVIEW
verdict: APPROVE
target:
  object: current.md#Spec (v1)
  base_sha: abc123...
findings: []
non_blocking_notes: []
evidence_reviewed: []
```
-->

<!-- 示例 2：实现报告（新增必写） -->
<!--
## IMPL-001 · implement-backend · implementer · 2026-09-08T14:00+08:00

```yaml
impl_id: IMPL-001
block_label: implement-backend
base_sha: abc123...
head_sha: def456...
spec_version: 1
files_changed:
  - path: wanGo/backend/alembic/versions/0031_tags.py
    kind: new
  - path: wanGo/backend/app/api/tags.py
    kind: new
tests_run:
  - cmd: "pytest tests/api/test_tags.py -v"
    workdir: wanGo/backend
    exit_code: 0
    expect: 0
verification: "curl POST/PATCH/DELETE 实测通过，wango_dev alembic upgrade/downgrade 各一次成功"
known_issues: []
follow_ups: []
```
-->

<!-- 示例 3：确定性检查报告（新增必写） -->
<!--
## CHECK-001 · check-backend · implementer · 2026-09-08T15:00+08:00

```yaml
check_id: CHECK-001
block_label: check-backend
head_sha: def456...
artifact:
  path: wanGo/backend
  type: python-backend
results:
  - cmd: "alembic upgrade head"
    workdir: wanGo/backend
    exit_code: 0
    expect: 0
  - cmd: "pytest tests/ -x -q"
    workdir: wanGo/backend
    exit_code: 0
    expect: 0
  - cmd: "python -c 'import app; print(app.__version__)'"
    workdir: wanGo/backend
    exit_code: 0
    expect: 0
outcome: PASS
```
-->

<!-- 示例 4：缺陷发现（新增必写） -->
<!--
## DEFECT-001 · tester · 2026-09-08T18:00+08:00

```yaml
defect_id: DEFECT-001
severity: blocking
found_by: tester
target_sha: def456...
title: "迁移 file_uploads 表缺少 organization_id NOT NULL 约束"
steps_to_reproduce:
  - "wango_dev 上执行 alembic upgrade head 到 0019"
evidence: "psql 输出：file_uploads.organization_id IS NULL DEFAULT NULL"
expected: "organization_id VARCHAR(64) NOT NULL"
disposition: IMPLEMENTATION
assigned_to: implementer
```
-->
