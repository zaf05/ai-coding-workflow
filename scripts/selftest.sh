#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/.."
pass=0; fail=0

echo "== 1. 正例工作流（应 PASS，含 _examples/） =="
# _examples/ 一并校验：示例是给人和 Planner 抄的，烂掉比没有更糟。
for wf in workflows/*.workflow.yaml workflows/_examples/*.workflow.yaml; do
  if python3 scripts/validate_workflow.py "$wf" >/tmp/aiw.out 2>&1; then
    echo "PASS $wf"; pass=$((pass+1))
  else
    echo "FAIL $wf"; cat /tmp/aiw.out; fail=$((fail+1))
  fi
done

echo "== 2. 反例工作流（应 FAIL） =="
for wf in workflows/_invalid/*.workflow.yaml; do
  if python3 scripts/validate_workflow.py "$wf" >/tmp/aiw.out 2>&1; then
    echo "FAIL(错误接受) $wf"; fail=$((fail+1))
  else
    echo "OK(按预期拒绝) $wf"; pass=$((pass+1))
  fi
done

echo "== 3. 包校验（正例应 PASS；runs 墓碑护栏应开火） =="
if python3 scripts/validate_package.py; then
  echo "PASS 包校验"; pass=$((pass+1))
else
  echo "FAIL 包校验"; fail=$((fail+1))
fi

# 3b 负例：未登记且不合法的 run 目录必须被拒。护栏要证明会开火，不是文档承诺。
#    用完立刻清理；若上次自检中断留下残留，先报错，不带病跑。
neg_run="runs/RUN-19700101-999"
if [ -e "$neg_run" ]; then
  echo "FAIL 残留 $neg_run（上次自检中断未清理，请人工确认后处理）"; fail=$((fail+1))
else
  mkdir -p "$neg_run"
  if python3 scripts/validate_package.py > /tmp/aiw-neg-run.out 2>&1; then
    echo "FAIL 未登记的非法 run 目录竟被接受（runs 护栏未开火）"; fail=$((fail+1))
  elif ! grep -q "也未在 runs/README.md 登记为占位" /tmp/aiw-neg-run.out; then
    echo "FAIL runs 护栏拒绝原因不可读"; cat /tmp/aiw-neg-run.out; fail=$((fail+1))
  else
    echo "PASS runs 护栏开火：未登记的非法 run 目录被拒且原因可读"; pass=$((pass+1))
  fi
  python3 -c 'import shutil,sys;shutil.rmtree(sys.argv[1],ignore_errors=True)' "$neg_run"
  if [ -e "$neg_run" ]; then echo "FAIL 负例目录未清理干净"; fail=$((fail+1)); fi
fi

# 3c 负例：state.yaml 块标签与声明的 DAG 定义不一致必须被拒（护栏 state_dag_mismatch）。
#     真实动机：run_flow.py 用 workflow_path 的图连边、用 state.yaml 的 status 推进；
#     两边块名不一致时解释器不报错也不停，只是永远算出与真实进度无关的 frontier，
#     确定性执行器静默失效。这条断言证明该缺口已被机器捕获，不是文档承诺。
mismatch_run="runs/RUN-19700102-999"
if [ -e "$mismatch_run" ]; then
  echo "FAIL 残留 $mismatch_run（上次自检中断未清理，请人工确认后处理）"; fail=$((fail+1))
else
  mkdir -p "$mismatch_run"
  cp skills/_shared/templates/current.md skills/_shared/templates/evidence.md "$mismatch_run/" 2>/dev/null
  python3 - "$mismatch_run" <<'PY'
import sys, yaml
from pathlib import Path
d = Path(sys.argv[1])
st = yaml.safe_load((d / "state.yaml").read_text()) if (d / "state.yaml").exists() else None
base = yaml.safe_load(Path("skills/_shared/templates/run-state.yaml").read_text(encoding="utf-8"))
base["run"].update({"id": d.name, "workflow": "feature-delivery",
                    "workflow_path": "../../workflows/feature-delivery.workflow.yaml",
                    "status": "running", "current_block_label": "intake",
                    "finally_block_label": "close"})
base["repository"].update({"root": "/tmp/x", "current_branch": "wp/x",
                           "current_sha": "a" * 40, "target_branch": "develop",
                           "target_base_sha": "a" * 40, "integration_branch": ""})
# 故意让块标签与 feature-delivery 定义不一致：多一个不存在的块 + 少一个定义里的块
base["blocks"] = [
    {"label": "intake", "status": "running", "role": "planner", "gate": "G0",
     "base_sha": "a" * 40, "head_sha": None, "tested_sha": None, "attempts": 0,
     "error_codes": []},
    {"label": "no_such_block", "status": "pending", "role": "planner", "gate": "G1",
     "base_sha": None, "head_sha": None, "tested_sha": None, "attempts": 0,
     "error_codes": []},
]
base["gates"] = {"G0": {"passed": False, "evidence_ref": "", "owner": "", "verified_at": ""}}
(d / "state.yaml").write_text(
    yaml.safe_dump(base, allow_unicode=True, sort_keys=False), encoding="utf-8")
PY
  if python3 scripts/validate_run.py "$mismatch_run" > /tmp/aiw-dag-mismatch.out 2>&1; then
    echo "FAIL 块标签与 DAG 定义不一致竟被接受（state_dag_mismatch 护栏未开火）"; fail=$((fail+1))
  elif ! grep -q "不在 DAG 定义" /tmp/aiw-dag-mismatch.out \
    || ! grep -q "在 state.yaml 中缺失" /tmp/aiw-dag-mismatch.out; then
    echo "FAIL state_dag_mismatch 拒绝原因不可读（需同时指出多余块与缺失块）"
    cat /tmp/aiw-dag-mismatch.out; fail=$((fail+1))
  else
    echo "PASS state_dag_mismatch 护栏开火：多余块与缺失块都被指出且原因可读"; pass=$((pass+1))
  fi
  python3 -c 'import shutil,sys;shutil.rmtree(sys.argv[1],ignore_errors=True)' "$mismatch_run"
  if [ -e "$mismatch_run" ]; then echo "FAIL 负例目录未清理干净"; fail=$((fail+1)); fi
fi

# 3d 正例：模板默认值必须直接通过 SHA 校验（未绑定写 null，不是 ""）。
#     真实动机：模板曾把未绑定 SHA 写成 ""，而 check_sha 只放行 null，
#     于是「从模板新建的每个 run 必然 FAIL」，恒定 FAIL 会让护栏沦为噪音。
template_run="runs/RUN-19700103-999"
if [ -e "$template_run" ]; then
  echo "FAIL 残留 $template_run（上次自检中断未清理）"; fail=$((fail+1))
else
  mkdir -p "$template_run"
  cp skills/_shared/templates/run-state.yaml "$template_run/state.yaml"
  cp skills/_shared/templates/current.md skills/_shared/templates/evidence.md "$template_run/" 2>/dev/null
  if python3 -c '
import sys, yaml
from pathlib import Path
p = Path(sys.argv[1]) / "state.yaml"
st = yaml.safe_load(p.read_text(encoding="utf-8"))
st["run"].update({"id": p.parent.name, "workflow": "feature-delivery", "status": "created"})
st["blocks"] = [{"label": b["label"], "status": "pending", "role": b.get("role", "planner"),
                 "gate": b.get("gate"), "base_sha": None, "head_sha": None,
                 "tested_sha": None, "attempts": 0, "error_codes": []}
                for b in yaml.safe_load(Path("workflows/feature-delivery.workflow.yaml").read_text(encoding="utf-8"))["blocks"]]
st["gates"] = {}
p.write_text(yaml.safe_dump(st, allow_unicode=True, sort_keys=False), encoding="utf-8")
' "$template_run" && python3 scripts/validate_run.py "$template_run" > /tmp/aiw-template.out 2>&1; then
    echo "PASS 模板默认值（未绑定 SHA = null）通过 validate_run.py"; pass=$((pass+1))
  else
    echo "FAIL 模板派生的 run 无法通过校验（模板与校验器契约冲突）"; cat /tmp/aiw-template.out; fail=$((fail+1))
  fi
  python3 -c 'import shutil,sys;shutil.rmtree(sys.argv[1],ignore_errors=True)' "$template_run"
  if [ -e "$template_run" ]; then echo "FAIL 负例目录未清理干净"; fail=$((fail+1)); fi
fi

# 3e 负例/正例：transition 写入时护栏（docs/31 P0）。护栏要证明会开火：
#     复现 2026-09-20 实测的"Planner 代签 G9 类"越权（这里用 G8=reviewer 同构形态）。
tr_run="runs/RUN-19700104-999"
if [ -e "$tr_run" ]; then
  echo "FAIL 残留 $tr_run（上次自检中断未清理，请人工确认后处理）"; fail=$((fail+1))
else
  mkdir -p "$tr_run"
  cat > "$tr_run/state.prev.yaml" <<'YAML'
run:
  workflow: feature-delivery
blocks:
  - {label: approve, status: running, attempts: 1, error_codes: []}
gates:
  G8: {passed: false, owner: "", evidence_ref: ""}
YAML
  # 3e-1 负例：planner 代签 G8（owner 不在 {'reviewer'}）
  cat > "$tr_run/state.yaml" <<'YAML'
run:
  workflow: feature-delivery
blocks:
  - {label: approve, status: running, attempts: 1, error_codes: []}
gates:
  G8: {passed: true, owner: planner, evidence_ref: "evidence.md#REVIEW-002"}
YAML
  if python3 scripts/validate_transition.py "$tr_run" > /tmp/aiw-tr1.out 2>&1; then
    echo "FAIL planner 代签 G8 竟被接受（T-01 未开火）"; fail=$((fail+1))
  elif ! grep -q "\[T-01\]" /tmp/aiw-tr1.out; then
    echo "FAIL T-01 拒绝原因不可读"; cat /tmp/aiw-tr1.out; fail=$((fail+1))
  else
    echo "PASS T-01 开火：planner 代签 G8 被拒且原因可读"; pass=$((pass+1))
  fi
  # 3e-2 负例：completed→running 无新增返修凭据
  cat > "$tr_run/state.prev.yaml" <<'YAML'
run:
  workflow: feature-delivery
blocks:
  - {label: implement, status: completed, attempts: 1, error_codes: []}
gates:
  G8: {passed: false, owner: "", evidence_ref: ""}
YAML
  cat > "$tr_run/state.yaml" <<'YAML'
run:
  workflow: feature-delivery
blocks:
  - {label: implement, status: running, attempts: 1, error_codes: []}
gates:
  G8: {passed: false, owner: "", evidence_ref: ""}
YAML
  if python3 scripts/validate_transition.py "$tr_run" > /tmp/aiw-tr2.out 2>&1; then
    echo "FAIL completed→running 无返修凭据竟被接受（T-02 未开火）"; fail=$((fail+1))
  elif ! grep -q "\[T-02\]" /tmp/aiw-tr2.out; then
    echo "FAIL T-02 拒绝原因不可读"; cat /tmp/aiw-tr2.out; fail=$((fail+1))
  else
    echo "PASS T-02 开火：无返修凭据的 completed→running 被拒"; pass=$((pass+1))
  fi
  # 3e-3 正例：reviewer 合法签 G8 + star 块带 approvals.user 人工证据 + 合法迁移
  cat > "$tr_run/state.prev.yaml" <<'YAML'
run:
  workflow: feature-delivery
blocks:
  - {label: approve, status: running, attempts: 1, error_codes: []}
gates:
  G8: {passed: false, owner: "", evidence_ref: ""}
YAML
  cat > "$tr_run/state.yaml" <<'YAML'
run:
  workflow: feature-delivery
blocks:
  - {label: approve, status: completed, attempts: 1, error_codes: [], gate: G3}
gates:
  G8: {passed: true, owner: reviewer, evidence_ref: "evidence.md#REVIEW-002"}
  G3: {passed: true, owner: user, evidence_ref: "evidence.md#APPROVAL-001"}
approvals:
  user: approved 1970-01-01
YAML
  if python3 scripts/validate_transition.py "$tr_run" > /tmp/aiw-tr3.out 2>&1; then
    echo "PASS transition 正例（合法 owner/star 证据/迁移放行）"; pass=$((pass+1))
  else
    echo "FAIL transition 正例被误拒"; cat /tmp/aiw-tr3.out; fail=$((fail+1))
  fi
  python3 -c 'import shutil,sys;shutil.rmtree(sys.argv[1],ignore_errors=True)' "$tr_run"
  if [ -e "$tr_run" ]; then echo "FAIL 3e 负例目录未清理干净"; fail=$((fail+1)); fi
fi

# 3f 负例：DAG 语义一致性（docs/31 P1）。复刻 RUN-20260918-002 暴露的形态：
#     close 已 completed 但祖先 pending、run.status=completed 但 frontier 非空。
sem_run="runs/RUN-19700105-999"
if [ -e "$sem_run" ]; then
  echo "FAIL 残留 $sem_run（上次自检中断未清理，请人工确认后处理）"; fail=$((fail+1))
else
  mkdir -p "$sem_run"
  cp skills/_shared/templates/current.md skills/_shared/templates/evidence.md \
     skills/_shared/templates/test-plan.md "$sem_run/" 2>/dev/null
  python3 - "$sem_run" <<'PY'
import sys, yaml
from pathlib import Path
d = Path(sys.argv[1])
base = yaml.safe_load(Path("skills/_shared/templates/run-state.yaml").read_text(encoding="utf-8"))
base["run"].update({"id": d.name, "workflow": "feature-delivery",
                    "workflow_path": "../../workflows/feature-delivery.workflow.yaml",
                    "status": "completed", "current_block_label": "close",
                    "finally_block_label": "close"})
base["repository"].update({"root": "/tmp/x", "current_branch": "wp/x",
                           "current_sha": "a" * 40, "target_branch": "develop",
                           "target_base_sha": "a" * 40, "integration_branch": ""})
# 全部 16 块登记：intake/recon/close completed，其余 pending —— close 的祖先
# 大量 pending，且 completed 状态下 frontier 非空，应同时命中 R-1 与 R-2。
base["blocks"] = [
    {"label": b["label"],
     "status": "completed" if b["label"] in ("intake", "recon", "close") else "pending",
     "role": b.get("role", "planner"), "gate": b.get("gate"),
     "base_sha": None, "head_sha": None, "tested_sha": None,
     "attempts": 0, "error_codes": []}
    for b in yaml.safe_load(Path("workflows/feature-delivery.workflow.yaml").read_text(encoding="utf-8"))["blocks"]
]
base["gates"] = {"G0": {"passed": True, "evidence_ref": "current.md#Intake", "owner": "planner",
                        "verified_at": "1970-01-01T00:01:00+00:00"}}
(d / "state.yaml").write_text(
    yaml.safe_dump(base, allow_unicode=True, sort_keys=False), encoding="utf-8")
PY
  if python3 scripts/validate_run.py "$sem_run" > /tmp/aiw-sem.out 2>&1; then
    echo "FAIL close completed 但祖先 pending 竟被接受（R-1/R-2 未开火）"; fail=$((fail+1))
  elif ! grep -q "R-1" /tmp/aiw-sem.out || ! grep -q "R-2" /tmp/aiw-sem.out; then
    echo "FAIL DAG 语义拒绝原因不可读（需同时命中 R-1 与 R-2）"; cat /tmp/aiw-sem.out; fail=$((fail+1))
  else
    echo "PASS dag_semantics 护栏开火：R-1（祖先未终态）与 R-2（completed 但 frontier 非空）都被指出"; pass=$((pass+1))
  fi
  python3 -c 'import shutil,sys;shutil.rmtree(sys.argv[1],ignore_errors=True)' "$sem_run"
  if [ -e "$sem_run" ]; then echo "FAIL 3f 负例目录未清理干净"; fail=$((fail+1)); fi
fi

# 3g check_all：陈旧检测只建议不代写，超限 running run 必须被点名。
ca_dir="$(mktemp -d "${TMPDIR:-/tmp}/aiw-checkall.XXXXXX")"
mkdir -p "$ca_dir/RUN-19700106-999"
cat > "$ca_dir/RUN-19700106-999/state.yaml" <<'YAML'
run:
  id: RUN-19700106-999
  status: running
  max_elapsed_time_minutes: 60
blocks: []
YAML
python3 - "$ca_dir/RUN-19700106-999/state.yaml" <<'PY'
import sys, os, time
os.utime(sys.argv[1], (time.time() - 3 * 86400, time.time() - 3 * 86400))  # 停滞 3 天
PY
if python3 scripts/check_all.py --runs-dir "$ca_dir" --skip-install > "$ca_dir/out" 2>&1; then :; fi
if grep -q "WARN RUN-19700106-999" "$ca_dir/out" && grep -q "timed_out" "$ca_dir/out"; then
  echo "PASS check_all 陈旧检测：超限 run 被点名且给出建议动作"; pass=$((pass+1))
else
  echo "FAIL check_all 陈旧检测未点名或无建议动作"; cat "$ca_dir/out"; fail=$((fail+1))
fi
python3 - "$ca_dir/RUN-19700106-999/state.yaml" <<'PY'
import sys, os, time
os.utime(sys.argv[1], None)  # 恢复新鲜 mtime
PY
python3 scripts/check_all.py --runs-dir "$ca_dir" --skip-install > "$ca_dir/out2" 2>&1
if grep -q "WARN RUN-19700106-999" "$ca_dir/out2"; then
  echo "FAIL 新鲜 mtime 的 running run 被误报陈旧"; cat "$ca_dir/out2"; fail=$((fail+1))
else
  echo "PASS check_all 不误报新鲜 run（仅超限者 WARN）"; pass=$((pass+1))
fi
python3 -c 'import shutil,sys;shutil.rmtree(sys.argv[1],ignore_errors=True)' "$ca_dir"

# 3h 规则生命周期接线（v1.8.1，docs/32 落地项）。能力观察与删减判据是 instruction 级
#     规则，无法用行为反例触发；确定性底线 = 契约正文、G10 行、Planner SKILL 三处接线，
#     任何一处被静默删除或脱钩，selftest 必须开火（与 §10.1 断言 hook 版本标记同理）。
if grep -q "任务后能力观察" skills/_shared/contracts/rule-lifecycle.md \
   && grep -q "误伤" skills/_shared/contracts/rule-lifecycle.md \
   && grep -q "无人消费" skills/_shared/contracts/rule-lifecycle.md \
   && grep -q "能力观察" docs/03-gates.md \
   && grep -q "能力观察" skills/aiworflow-planner/SKILL.md; then
  echo "PASS 规则生命周期接线（能力观察 + 删减信号在契约/G10/Planner 三处一致）"; pass=$((pass+1))
else
  echo "FAIL 规则生命周期接线断裂（契约、G10 或 Planner SKILL 缺能力观察/删减信号）"; fail=$((fail+1))
fi

# 3i 引擎完整性护栏（v1.8.12，RUN-20260916-001 审计驱动）。四条硬门禁：
#     workflow SHA 冻结/漂移拦截、mark-done 证据锚点门禁、implement head_sha 门禁、
#     终态引擎收口（消灭手改 state 把 running 改 completed 的旁路）。每条都要证明
#     会开火，不是文档承诺。
ei_dir="$(mktemp -d "${TMPDIR:-/tmp}/aiw-engine-integrity.XXXXXX")"
mkdir -p "$ei_dir/run"
cat > "$ei_dir/wf.yaml" <<'YAML'
schema_version: 1
name: "引擎完整性测试"
workflow_id: selftest-engine-integrity
error_code_mapping:
  AIW_WORKFLOW_DRIFT: "定义漂移"
  AIW_HEAD_SHA_MISSING: "缺候选提交"
finally_block_label: done
blocks:
  - label: intake
    block_type: intake
    next_block_label: "impl"
    role: planner
    goal: "g"
    complete_criterion: "c"
    evidence: ["evidence.md#IMPL-001"]
  - label: impl
    block_type: implement
    next_block_label: "done"
    role: implementer
    goal: "g"
    complete_criterion: "实现报告绑定 head_sha"
    evidence: ["evidence.md#IMPL-001"]
  - label: done
    block_type: close
    next_block_label: null
    role: planner
    goal: "g"
    complete_criterion: "c"
    evidence: ["evidence.md#DONE-001"]
YAML
cat > "$ei_dir/run/state.yaml" <<'YAML'
schema_version: 1
run:
  id: RUN-19700107-999
  workflow: selftest-engine-integrity
  status: running
  current_block_label: null
  finally_block_label: done
repository:
  root: /tmp
blocks:
  - {label: intake, status: pending, role: planner, gate: null, base_sha: null, head_sha: null, tested_sha: null, attempts: 0, error_codes: []}
  - {label: impl, status: pending, role: implementer, gate: null, base_sha: null, head_sha: null, tested_sha: null, attempts: 0, error_codes: []}
  - {label: done, status: pending, role: planner, gate: null, base_sha: null, head_sha: null, tested_sha: null, attempts: 0, error_codes: []}
YAML
printf '# Evidence\n' > "$ei_dir/run/evidence.md"
cp "$ei_dir/wf.yaml" "$ei_dir/wf.orig"

# 3i-1 首触冻结：默认 frontier 调用即写入 workflow_sha256
python3 scripts/run_flow.py "$ei_dir/wf.yaml" "$ei_dir/run" >/dev/null 2>&1
if python3 -c '
import sys, yaml
st = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
sha = st.get("run", {}).get("workflow_sha256", "")
assert len(sha) == 64 and all(c in "0123456789abcdef" for c in sha)
' "$ei_dir/run/state.yaml" 2>/dev/null; then
  echo "PASS 引擎首触冻结 workflow_sha256（64 位 sha256 落盘）"; pass=$((pass+1))
else
  echo "FAIL 引擎首触未冻结 workflow_sha256"; fail=$((fail+1))
fi

# 3i-2 漂移拦截：冻结后改定义，任何调用必须被拒
printf '\n# tampered\n' >> "$ei_dir/wf.yaml"
drift_out=$(python3 scripts/run_flow.py "$ei_dir/wf.yaml" "$ei_dir/run" --advance 2>&1)
drift_rc=$?
if [ $drift_rc -ne 0 ] && echo "$drift_out" | grep -q "AIW_WORKFLOW_DRIFT"; then
  echo "PASS workflow 漂移拦截（冻结后改定义被拒且错误码可读）"; pass=$((pass+1))
else
  echo "FAIL workflow 漂移未拦截"; echo "$drift_out"; fail=$((fail+1))
fi
cp "$ei_dir/wf.orig" "$ei_dir/wf.yaml"   # 字节级还原，保证与冻结 SHA 一致

# 3i-3 证据门禁：锚点缺失时 mark-done completed 必须被拒
ev_out=$(python3 scripts/run_flow.py "$ei_dir/wf.yaml" "$ei_dir/run" --mark-done intake 2>&1)
ev_rc=$?
if [ $ev_rc -ne 0 ] && echo "$ev_out" | grep -q "AIW_EVIDENCE_MISSING" && echo "$ev_out" | grep -q "锚点不存在"; then
  echo "PASS mark-done 证据门禁（锚点缺失被拒且原因可读）"; pass=$((pass+1))
else
  echo "FAIL mark-done 证据门禁未开火"; echo "$ev_out"; fail=$((fail+1))
fi

# 补锚点后放行，且 attempts/current_block_label 同步落盘
printf '\n## IMPL-001 · test anchor\n' >> "$ei_dir/run/evidence.md"
ev2_out=$(python3 scripts/run_flow.py "$ei_dir/wf.yaml" "$ei_dir/run" --mark-done intake 2>&1)
if echo "$ev2_out" | grep -q '"new_status": "completed"' \
   && python3 -c '
import sys, yaml
st = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
b = next(b for b in st["blocks"] if b["label"] == "intake")
assert b["status"] == "completed" and b["attempts"] == 1
assert st["run"]["current_block_label"] == "intake"
' "$ei_dir/run/state.yaml" 2>/dev/null; then
  echo "PASS mark-done 放行后账本同步（attempts=1、current_block_label 归位）"; pass=$((pass+1))
else
  echo "FAIL mark-done 放行后账本未同步"; echo "$ev2_out"; fail=$((fail+1))
fi

# 3i-4 implement head_sha 门禁：有证据但无候选提交仍被拒
hs_out=$(python3 scripts/run_flow.py "$ei_dir/wf.yaml" "$ei_dir/run" --mark-done impl 2>&1)
hs_rc=$?
if [ $hs_rc -ne 0 ] && echo "$hs_out" | grep -q "AIW_HEAD_SHA_MISSING"; then
  echo "PASS implement head_sha 门禁（无候选提交被拒）"; pass=$((pass+1))
else
  echo "FAIL implement head_sha 门禁未开火"; echo "$hs_out"; fail=$((fail+1))
fi
hs2_out=$(python3 scripts/run_flow.py "$ei_dir/wf.yaml" "$ei_dir/run" --mark-done impl --head-sha 0123456789abcdef0123456789abcdef01234567 2>&1)
if echo "$hs2_out" | grep -q '"new_status": "completed"' \
   && python3 -c '
import sys, yaml
st = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
b = next(b for b in st["blocks"] if b["label"] == "impl")
assert b["head_sha"] == "0123456789abcdef0123456789abcdef01234567"
' "$ei_dir/run/state.yaml" 2>/dev/null; then
  echo "PASS --head-sha 绑定候选提交后放行且落盘"; pass=$((pass+1))
else
  echo "FAIL --head-sha 未生效"; echo "$hs2_out"; fail=$((fail+1))
fi

# 3i-5 check 块人工 completed 必须被拒（只能由命令退出码自动完成）
cat > "$ei_dir/wf2.yaml" <<'YAML'
schema_version: 1
name: "check 拒绝手工完成"
workflow_id: selftest-check-manual
error_code_mapping: {}
blocks:
  - label: chk
    block_type: check
    next_block_label: null
    role: implementer
    goal: "g"
    complete_criterion: "c"
    commands:
      - {cmd: "true", workdir: ".", expect: 0}
YAML
mkdir -p "$ei_dir/run-chk"
cat > "$ei_dir/run-chk/state.yaml" <<'YAML'
schema_version: 1
run:
  id: RUN-19700108-999
  workflow: selftest-check-manual
  status: running
repository:
  root: /tmp
blocks:
  - {label: chk, status: pending, role: implementer, gate: null, base_sha: null, head_sha: null, tested_sha: null, attempts: 0, error_codes: []}
YAML
chk_out=$(python3 scripts/run_flow.py "$ei_dir/wf2.yaml" "$ei_dir/run-chk" --mark-done chk 2>&1)
chk_rc=$?
if [ $chk_rc -ne 0 ] && echo "$chk_out" | grep -q "不得人工标记 completed"; then
  echo "PASS check 块人工 completed 被拒（只能由 --execute-check 退出码完成）"; pass=$((pass+1))
else
  echo "FAIL check 块人工完成未拦截"; echo "$chk_out"; fail=$((fail+1))
fi

# 3i-6 终态引擎收口：全部块 terminal 时 --advance 写入 completed + finally 指针
printf '\n## DONE-001 · test anchor\n' >> "$ei_dir/run/evidence.md"
python3 scripts/run_flow.py "$ei_dir/wf.yaml" "$ei_dir/run" --mark-done done >/dev/null 2>&1
python3 scripts/run_flow.py "$ei_dir/wf.yaml" "$ei_dir/run" --advance >/dev/null 2>&1
if python3 -c '
import sys, yaml
st = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
assert st["run"]["status"] == "completed"
assert st["run"]["current_block_label"] == "done"
' "$ei_dir/run/state.yaml" 2>/dev/null; then
  echo "PASS 终态引擎收口（completed + current_block_label=finally，无需手改 state）"; pass=$((pass+1))
else
  echo "FAIL 终态引擎未收口"; head -12 "$ei_dir/run/state.yaml"; fail=$((fail+1))
fi

# 3i-7 validate_run R-4/R-5 负例：终态索引错位 + implement 无 head_sha 必须被点名
mkdir -p "$ei_dir/RUN-19700109-999"
cat > "$ei_dir/RUN-19700109-999/state.yaml" <<'YAML'
schema_version: 1
run:
  id: RUN-19700109-999
  workflow: feature-delivery
  workflow_path: "workflows/feature-delivery.workflow.yaml"
  status: completed
  current_block_label: implement
  finally_block_label: close
repository:
  root: /tmp
  current_branch: wp/x
  current_sha: null
  target_branch: develop
  target_base_sha: null
  integration_branch: ""
  integration_sha: null
  dirty_worktree_detected: false
  dirty_worktree_overlap: false
blocks: []
gates: {}
versions: {spec: 1, test_plan: 1, change_budget: 1}
approvals: {spec: null, user: null, test_plan: null}
open_findings: []
open_defects: []
open_blockers: []
completion_contract: []
ledger: []
YAML
python3 - "$ei_dir/RUN-19700109-999/state.yaml" <<'PY'
import sys, yaml
from pathlib import Path
p = Path(sys.argv[1])
st = yaml.safe_load(p.read_text(encoding="utf-8"))
wf_path = Path("workflows/feature-delivery.workflow.yaml").resolve()
st["run"]["workflow_path"] = str(wf_path)
wf = yaml.safe_load(wf_path.read_text(encoding="utf-8"))
st["blocks"] = [
    {"label": b["label"], "status": "completed", "role": b.get("role", "planner"),
     "gate": b.get("gate"), "base_sha": None, "head_sha": None, "tested_sha": None,
     "attempts": 1, "error_codes": []}
    for b in wf["blocks"]]
p.write_text(yaml.safe_dump(st, allow_unicode=True, sort_keys=False), encoding="utf-8")
PY
bad_out=$(python3 scripts/validate_run.py "$ei_dir/RUN-19700109-999" 2>&1)
bad_rc=$?
if [ $bad_rc -ne 0 ] && echo "$bad_out" | grep -q "R-4" && echo "$bad_out" | grep -q "R-5"; then
  echo "PASS validate_run R-4/R-5 开火（终态索引错位与 implement 无 head_sha 都被点名）"; pass=$((pass+1))
else
  echo "FAIL validate_run R-4/R-5 未开火"; echo "$bad_out"; fail=$((fail+1))
fi

python3 -c 'import shutil,sys;shutil.rmtree(sys.argv[1],ignore_errors=True)' "$ei_dir"

echo "== 4. 安装器本机锁定（本机收据属于本副本时应 PASS，否则 SKIP） =="
# 静默失败是 bug 的藏身处：任何一项失败都必须打印 FAIL。
# 可移植性（实测教训）：安装目标若属于**另一个来源根**（换机器 / 克隆到别处 /
# 多个工作副本并存），--check 按设计返回非零——那是环境事实，不是本包缺陷。
# 若在此一律判 FAIL，pre-commit 闸门会在任何非规范机器上把所有提交拦死，
# 「让别人也能用这套工作流」直接不成立。故：同根＝硬断言，异根＝显式 SKIP。
receipt="$HOME/.codex/skills/aiworflow-install-receipt.json"
repo_root="$(pwd)"
rec_root=""
if [ -f "$receipt" ]; then
  rec_root="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1])).get("source_root",""))' "$receipt" 2>/dev/null)"
fi
if [ "$rec_root" = "$repo_root" ]; then
  if python3 scripts/install_skills.py --check >/tmp/aiw-install-check.out 2>&1; then
    echo "PASS 安装器本机锁定（--check 版本与指纹一致）"; pass=$((pass+1))
  else
    echo "FAIL 安装器本机锁定（--check 版本/指纹不一致；用 --upgrade --apply 同步）"
    cat /tmp/aiw-install-check.out; fail=$((fail+1))
  fi
else
  echo "SKIP 安装器本机锁定（本机安装目标属于其他来源根或未安装：${rec_root:-无收据}）"
  echo "     环境事实，不判失败；本机若要锁定版本：python3 scripts/install_skills.py --apply"
fi

echo "== 5. 内置 YAML fallback 自检 =="
if python3 -c "from scripts._yaml_min import loads; import pathlib; d=loads(pathlib.Path('workflows/feature-delivery.workflow.yaml').read_text()); print('fallback OK', len(d['blocks']), 'blocks')" 2>/tmp/aiw.out; then pass=$((pass+1)); else echo "fallback FAIL"; cat /tmp/aiw.out; fail=$((fail+1)); fi

echo "== 6. 候选 DAG 编译器（正例应 COMPILE，反例应 REJECT） =="
tmpd=$(mktemp -d)
if python3 scripts/compile_dag.py workflows/feature-delivery.workflow.yaml -o "$tmpd/fd.compiled.yaml" >/tmp/aiw.out 2>&1; then
  echo "PASS compile 正例"; pass=$((pass+1))
else
  echo "FAIL compile 正例"; cat /tmp/aiw.out; fail=$((fail+1))
fi
cat > "$tmpd/bad-star.yaml" <<'YAML'
schema_version: 1
name: "反例"
workflow_id: "selftest-bad-star"
error_code_mapping: {}
blocks:
  - label: approve
    block_type: approve
    next_block_label: null
    role: user
    gate: G3
    goal: "批准"
    complete_criterion: "批准"
YAML
if python3 scripts/compile_dag.py "$tmpd/bad-star.yaml" >/tmp/aiw.out 2>&1; then
  echo "FAIL(错误接受) compile 反例"; cat /tmp/aiw.out; fail=$((fail+1))
else
  echo "OK(按预期拒绝) compile 反例"; pass=$((pass+1))
fi
cat > "$tmpd/drift.yaml" <<'YAML'
schema_version: "1"
name: "漂移正例"
workflow_id: "selftest-drift"
error_code_mapping: {}
finally_block_label: close
blocks:
  - id: notify
    type: notify
    next: "close"
    role: planner
    goal: "g"
    complete_criterion: "c"
  - id: close
    type: close
    next: null
    role: planner
    gate: G10
    goal: "g"
    complete_criterion: "c"
    evidence: ["state.yaml"]
YAML
if python3 scripts/compile_dag.py "$tmpd/drift.yaml" -o "$tmpd/drift.compiled.yaml" >/tmp/aiw.out 2>&1; then
  echo "PASS compile 漂移归一化"; pass=$((pass+1))
else
  echo "FAIL compile 漂移归一化"; cat /tmp/aiw.out; fail=$((fail+1))
fi

echo "== 7. run_flow.py 新功能（条件分支 / 重试 / 账本 / 推进） =="

# 7a. 条件分支评估
mkdir -p "$tmpd/run-cond"
cat > "$tmpd/run-cond/state.yaml" <<'YAML'
schema_version: 1
run:
  id: SELFTEST-COND
  workflow: test
  status: running
  current_block_label: route
repository:
  root: /tmp
blocks:
  - label: start
    status: completed
    attempts: 1
  - label: route
    status: pending
    attempts: 0
  - label: path_a
    status: pending
    attempts: 0
  - label: path_b
    status: pending
    attempts: 0
conditions:
  verdict: "APPROVE"
YAML
cat > "$tmpd/cond-wf.yaml" <<'YAML'
schema_version: 1
name: "条件测试"
workflow_id: "selftest-cond"
error_code_mapping: {}
blocks:
  - label: start
    block_type: intake
    next_block_label: route
    role: planner
    goal: "g"
    complete_criterion: "c"
  - label: route
    block_type: conditional
    next_block_label: path_a
    role: planner
    goal: "路由"
    complete_criterion: "c"
    branch_conditions:
      - condition_key: verdict
        equals: "REQUEST_CHANGES"
        next_block_label: path_b
      - is_default: true
        next_block_label: path_a
  - label: path_a
    block_type: notify
    next_block_label: null
    role: planner
    goal: "g"
    complete_criterion: "c"
  - label: path_b
    block_type: notify
    next_block_label: null
    role: planner
    goal: "g"
    complete_criterion: "c"
YAML
cond_out=$(python3 scripts/run_flow.py "$tmpd/cond-wf.yaml" "$tmpd/run-cond" --evaluate-conditional route verdict 2>&1)
if echo "$cond_out" | grep -q '"matched_branch": "path_a"'; then
  echo "PASS 条件分支评估（APPROVE → path_a 默认分支）"; pass=$((pass+1))
else
  echo "FAIL 条件分支评估"; echo "$cond_out"; fail=$((fail+1))
fi

# 7b. 重试
mkdir -p "$tmpd/run-retry"
cat > "$tmpd/run-retry/state.yaml" <<'YAML'
schema_version: 1
run:
  id: SELFTEST-RETRY
  workflow: test
  status: running
repository:
  root: /tmp
blocks:
  - label: impl
    status: failed
    attempts: 1
    max_attempts: 2
YAML
cat > "$tmpd/retry-wf.yaml" <<'YAML'
schema_version: 1
name: "重试测试"
workflow_id: "selftest-retry"
error_code_mapping: {}
blocks:
  - label: impl
    block_type: implement
    next_block_label: null
    role: implementer
    goal: "g"
    complete_criterion: "c"
    max_attempts: 2
YAML
retry_out=$(python3 scripts/run_flow.py "$tmpd/retry-wf.yaml" "$tmpd/run-retry" --retry impl 2>&1)
if echo "$retry_out" | grep -q '"new_attempts": 2' && echo "$retry_out" | grep -q '"new_status": "pending"'; then
  echo "PASS 重试（attempts 1→2, status failed→pending）"; pass=$((pass+1))
else
  echo "FAIL 重试"; echo "$retry_out"; fail=$((fail+1))
fi

# 7c. 账本追加
ledger_out=$(python3 scripts/run_flow.py "$tmpd/retry-wf.yaml" "$tmpd/run-retry" --append-ledger '{"event":"test","source":"selftest"}' 2>&1)
if echo "$ledger_out" | grep -q '"action": "append_ledger"' && echo "$ledger_out" | grep -q '"event": "test"'; then
  echo "PASS 账本追加"; pass=$((pass+1))
else
  echo "FAIL 账本追加"; echo "$ledger_out"; fail=$((fail+1))
fi

# 7d. 推进模式（advance）
mkdir -p "$tmpd/run-adv"
cat > "$tmpd/run-adv/state.yaml" <<'YAML'
schema_version: 1
run:
  id: SELFTEST-ADV
  workflow: test
  status: running
  current_block_label: check
  finally_block_label: null
repository:
  root: /tmp
blocks:
  - label: impl
    status: completed
    attempts: 1
  - label: check
    status: pending
    attempts: 0
  - label: done
    status: pending
    attempts: 0
YAML
cat > "$tmpd/adv-wf.yaml" <<'YAML'
schema_version: 1
name: "推进测试"
workflow_id: "selftest-adv"
error_code_mapping: {}
blocks:
  - label: impl
    block_type: implement
    next_block_label: check
    role: implementer
    goal: "g"
    complete_criterion: "c"
  - label: check
    block_type: check
    next_block_label: done
    role: implementer
    goal: "g"
    complete_criterion: "c"
    commands:
      - {cmd: "echo ok", expect: 0}
  - label: done
    block_type: close
    next_block_label: null
    role: planner
    goal: "g"
    complete_criterion: "c"
YAML
adv_out=$(python3 scripts/run_flow.py "$tmpd/adv-wf.yaml" "$tmpd/run-adv" --advance --execute-check 2>&1)
if echo "$adv_out" | grep -q '"action": "CHECK"' && echo "$adv_out" | grep -q '"pass": true'; then
  echo "PASS 推进模式（check 自动执行并标记 completed）"; pass=$((pass+1))
else
  echo "FAIL 推进模式"; echo "$adv_out"; fail=$((fail+1))
fi

# 7d-bis. TERMINAL 报告统一契约：终结路径也必须带 loop_control
# （v1.8.6 修复：双宿主消费方按 loop_control 解析不再 KeyError）
python3 - "$tmpd/run-adv/state.yaml" <<'PY'
import sys, yaml
from pathlib import Path
p = Path(sys.argv[1])
st = yaml.safe_load(p.read_text(encoding="utf-8"))
st["run"]["status"] = "completed"
p.write_text(yaml.safe_dump(st, allow_unicode=True, sort_keys=False), encoding="utf-8")
PY
term_out=$(python3 scripts/run_flow.py "$tmpd/adv-wf.yaml" "$tmpd/run-adv" --advance 2>&1)
if echo "$term_out" | grep -q '"action": "TERMINAL"' && echo "$term_out" | grep -q '"loop_control": "DONE"'; then
  echo "PASS TERMINAL 报告统一契约（loop_control=DONE）"; pass=$((pass+1))
else
  echo "FAIL TERMINAL 报告缺 loop_control"; echo "$term_out"; fail=$((fail+1))
fi

# 7d-ter. 会话归因：--advance / --append-ledger 必须把 model 与尽力可得 tokens 写入账本；
#           非法 session-meta 必须非零退出，不允许账本看似有归因、实际缺 model。
mkdir -p "$tmpd/run-meta"
cat > "$tmpd/run-meta/state.yaml" <<\YAML
schema_version: 1
run:
  id: SELFTEST-META
  workflow: test
  status: running
  current_block_label: check
  finally_block_label: null
repository:
  root: /tmp
blocks:
  - label: check
    status: pending
    attempts: 0
YAML
cat > "$tmpd/meta-wf.yaml" <<\YAML
schema_version: 1
name: "会话归因测试"
workflow_id: "selftest-meta"
error_code_mapping: {}
blocks:
  - label: check
    block_type: check
    next_block_label: null
    role: implementer
    goal: "g"
    complete_criterion: "c"
    commands:
      - {cmd: "echo ok", expect: 0}
YAML
meta_json="{\"model\":\"test-model\",\"tokens_used\":123}"
meta_neg_json="{\"tokens_used\":10}"
meta_out=$(python3 scripts/run_flow.py "$tmpd/meta-wf.yaml" "$tmpd/run-meta" --advance --execute-check --session-meta "$meta_json" 2>&1)
meta_neg=$(python3 scripts/run_flow.py "$tmpd/meta-wf.yaml" "$tmpd/run-meta" --advance --session-meta "$meta_neg_json" 2>&1); meta_neg_rc=$?
if echo "$meta_out" | grep -q "\"session_meta\": {" \
  && echo "$meta_out" | grep -q "\"model\": \"test-model\"" \
  && echo "$meta_out" | grep -q "\"tokens_used\": 123" \
  && grep -q "model: test-model" "$tmpd/run-meta/state.yaml" \
  && grep -q "tokens_used: 123" "$tmpd/run-meta/state.yaml" \
  && [ "$meta_neg_rc" -ne 0 ] && echo "$meta_neg" | grep -q "session-meta.model"; then
  echo "PASS session-meta 归因（正常入账 + 非法输入拒绝）"; pass=$((pass+1))
else
  echo "FAIL session-meta 归因或负例"; echo "$meta_out"; echo "negative rc=$meta_neg_rc $meta_neg"; cat "$tmpd/run-meta/state.yaml"; fail=$((fail+1))
fi

# 7d-quatro. Review deterministic preflight：secret / 禁改区 / 破坏性命令必须开火；干净 diff PASS。
pf_repo="$tmpd/preflight-repo"
mkdir -p "$pf_repo"
git init -q "$pf_repo"
git -C "$pf_repo" config user.email selftest@aiworkflow.invalid
git -C "$pf_repo" config user.name "AIWorflow Selftest"
printf "base\n" > "$pf_repo/a.txt"
git -C "$pf_repo" add a.txt
git -C "$pf_repo" commit -qm "base"
pf_base=$(git -C "$pf_repo" rev-parse HEAD)
mkdir -p "$pf_repo/runs/RUN-PREFLIGHT"
printf "ledger\n" > "$pf_repo/runs/RUN-PREFLIGHT/state.yaml"
cat > "$pf_repo/script.txt" <<\EOF2
api_key = "abcdefghijklmnopqrstuvwxyz"
git reset --hard HEAD
EOF2
git -C "$pf_repo" add .
git -C "$pf_repo" commit -qm "bad candidate"
pf_bad_head=$(git -C "$pf_repo" rev-parse HEAD)
mkdir -p "$tmpd/preflight-run/RUN-PREFLIGHT"
cat > "$tmpd/preflight-run/RUN-PREFLIGHT/state.yaml" <<\YAML
run: {id: RUN-PREFLIGHT}
repository:
  root: "$pf_repo"
  target_base_sha: "$pf_base"
  current_sha: "$pf_bad_head"
YAML
pf_bad=$(python3 scripts/review_preflight.py "$tmpd/preflight-run/RUN-PREFLIGHT" --root "$pf_repo" --base "$pf_base" --head "$pf_bad_head" 2>&1); pf_bad_rc=$?
if [ "$pf_bad_rc" -ne 0 ] \
  && echo "$pf_bad" | grep -q "id: SECRET_SCAN" && echo "$pf_bad" | grep -q "status: FAIL" \
  && echo "$pf_bad" | grep -q "id: PROTECTED_PATHS" \
  && echo "$pf_bad" | grep -q "id: DESTRUCTIVE_COMMANDS" \
  && ! echo "$pf_bad" | grep -q "abcdefgh"; then
  echo "PASS review_preflight 三条硬规则开火且密钥材料不回显（secret/禁改区/破坏性命令）"; pass=$((pass+1))
else
  echo "FAIL review_preflight 硬规则未开火"; echo "rc=$pf_bad_rc"; echo "$pf_bad"; fail=$((fail+1))
fi
printf "safe candidate\n" > "$pf_repo/a.txt"
python3 -c "from pathlib import Path; import sys; Path(sys.argv[1]).unlink(); Path(sys.argv[2]).unlink()" "$pf_repo/script.txt" "$pf_repo/runs/RUN-PREFLIGHT/state.yaml"
git -C "$pf_repo" add -A
git -C "$pf_repo" commit -qm "clean candidate"
pf_good_head=$(git -C "$pf_repo" rev-parse HEAD)
python3 - "$tmpd/preflight-run/RUN-PREFLIGHT/state.yaml" "$pf_good_head" <<\PY
import sys, yaml
from pathlib import Path
p = Path(sys.argv[1]); st = yaml.safe_load(p.read_text(encoding="utf-8")); st["repository"]["current_sha"] = sys.argv[2]
p.write_text(yaml.safe_dump(st, allow_unicode=True, sort_keys=False), encoding="utf-8")
PY
pf_good=$(python3 scripts/review_preflight.py "$tmpd/preflight-run/RUN-PREFLIGHT" --root "$pf_repo" --base "$pf_base" --head "$pf_good_head" 2>&1); pf_good_rc=$?
if [ "$pf_good_rc" -eq 0 ] && echo "$pf_good" | grep -q "verdict: PASS"; then
  echo "PASS review_preflight 干净 diff 通过"; pass=$((pass+1))
else
  echo "FAIL review_preflight 干净 diff 被误拦"; echo "rc=$pf_good_rc"; echo "$pf_good"; fail=$((fail+1))
fi

# 7e. 候选 DAG 编译（prompts/examples/ 正例）
if [ -f "prompts/examples/candidate-dag-bugfix.yaml" ]; then
  if python3 scripts/compile_dag.py prompts/examples/candidate-dag-bugfix.yaml -o "$tmpd/bugfix.compiled.yaml" >/tmp/aiw.out 2>&1; then
    echo "PASS 候选 DAG 示例编译"; pass=$((pass+1))
  else
    echo "FAIL 候选 DAG 示例编译"; cat /tmp/aiw.out; fail=$((fail+1))
  fi
fi

echo "== 8. 版本锁定（VERSION / 安装收据 / 漂移检测 / 原子升级） =="
vtmpd=$(mktemp -d)
# 8a. VERSION 是单一事实源，且必须是合法 semver
if grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$' VERSION; then
  echo "PASS VERSION 存在且为 semver（$(cat VERSION)）"; pass=$((pass+1))
else
  echo "FAIL VERSION 缺失或不是 semver"; fail=$((fail+1))
fi
# 8b. apply 后必须写出安装收据，且 --check 通过
if python3 scripts/install_skills.py --target "$vtmpd" --mode copy --apply >/tmp/aiw.out 2>&1 \
   && [ -f "$vtmpd/aiworflow-install-receipt.json" ] \
   && python3 scripts/install_skills.py --target "$vtmpd" --check >/tmp/aiw.out 2>&1; then
  echo "PASS apply 写收据且 --check 一致"; pass=$((pass+1))
else
  echo "FAIL apply/收据/--check"; cat /tmp/aiw.out; fail=$((fail+1))
fi
# 8c. 目标被手改必须被 --check 判为漂移（exit!=0）
echo "被手改" >> "$vtmpd/aiworflow-reviewer/SKILL.md"
if python3 scripts/install_skills.py --target "$vtmpd" --check >/tmp/aiw.out 2>&1; then
  echo "FAIL 漂移未被检出"; fail=$((fail+1))
else
  if grep -q "目标漂移" /tmp/aiw.out; then
    echo "PASS 手改目标被检出为漂移"; pass=$((pass+1))
  else
    echo "FAIL 漂移输出缺字段"; cat /tmp/aiw.out; fail=$((fail+1))
  fi
fi
# 8d. --upgrade --apply 后必须恢复一致
if python3 scripts/install_skills.py --target "$vtmpd" --mode copy --upgrade --apply >/tmp/aiw.out 2>&1 \
   && python3 scripts/install_skills.py --target "$vtmpd" --check >/tmp/aiw.out 2>&1; then
  echo "PASS --upgrade 后目标恢复一致"; pass=$((pass+1))
else
  echo "FAIL --upgrade 未恢复一致"; cat /tmp/aiw.out; fail=$((fail+1))
fi
# 8e. 收据未登记的宿主文件必须原样保留
echo "host" > "$vtmpd/host-owned.md"
mkdir -p "$vtmpd/host-owned-skill"; echo x > "$vtmpd/host-owned-skill/SKILL.md"
python3 scripts/install_skills.py --target "$vtmpd" --mode copy --upgrade --apply >/tmp/aiw.out 2>&1
if [ -f "$vtmpd/host-owned.md" ] && [ -f "$vtmpd/host-owned-skill/SKILL.md" ]; then
  echo "PASS 升级不触碰收据未登记的宿主文件"; pass=$((pass+1))
else
  echo "FAIL 升级破坏了宿主文件"; fail=$((fail+1))
fi
# 8f. 认领路径：目标已装好但收据缺失时，--apply 必须补出收据且 --check 通过
#     （回归防护：旧实现在 `if not actions: return 0` 提前返回，已装好的环境
#      永远拿不到收据，导致 --check 报"未安装"、--upgrade 拒绝执行）
atmpd=$(mktemp -d)
python3 scripts/install_skills.py --target "$atmpd" --mode copy --apply >/tmp/aiw.out 2>&1
rm -f "$atmpd/aiworflow-install-receipt.json"          # 模拟历史安装 / 收据丢失
if python3 scripts/install_skills.py --target "$atmpd" --check >/tmp/aiw.out 2>&1; then
  echo "FAIL 无收据时 --check 竟然通过"; fail=$((fail+1))
else
  if python3 scripts/install_skills.py --target "$atmpd" --mode copy --apply >/tmp/aiw.out 2>&1 \
     && [ -f "$atmpd/aiworflow-install-receipt.json" ] \
     && python3 scripts/install_skills.py --target "$atmpd" --check >/tmp/aiw.out 2>&1; then
    echo "PASS 认领：已装好但无收据 → --apply 补收据且 --check 一致"; pass=$((pass+1))
  else
    echo "FAIL 认领路径未补出可用收据"; cat /tmp/aiw.out; fail=$((fail+1))
  fi
fi

# 8g. 认领的安全边界：目标已漂移时 --apply 必须拒绝写收据（不得把漂移洗白成已锁定）
rm -f "$atmpd/aiworflow-install-receipt.json"
echo "被手改" >> "$atmpd/aiworflow-tester/SKILL.md"
if python3 scripts/install_skills.py --target "$atmpd" --mode copy --apply >/tmp/aiw.out 2>&1; then
  echo "FAIL 漂移目标被错误认领"; fail=$((fail+1))
else
  if [ ! -f "$atmpd/aiworflow-install-receipt.json" ] && grep -q "未写收据" /tmp/aiw.out; then
    echo "PASS 漂移目标拒绝认领，未写收据"; pass=$((pass+1))
  else
    echo "FAIL 拒绝认领的输出或未写收据不符合预期"; cat /tmp/aiw.out; fail=$((fail+1))
  fi
fi

# 8h. dry-run 认领不得写盘
rm -rf "$atmpd"; mkdir -p "$atmpd"
python3 scripts/install_skills.py --target "$atmpd" --mode copy --apply >/tmp/aiw.out 2>&1
rm -f "$atmpd/aiworflow-install-receipt.json"
python3 scripts/install_skills.py --target "$atmpd" --dry-run >/tmp/aiw.out 2>&1
if [ ! -f "$atmpd/aiworflow-install-receipt.json" ] && grep -q "加 --apply 认领" /tmp/aiw.out; then
  echo "PASS dry-run 认领只预览不写盘"; pass=$((pass+1))
else
  echo "FAIL dry-run 认领写盘或提示缺失"; cat /tmp/aiw.out; fail=$((fail+1))
fi
rm -rf "$atmpd"

rm -rf "$vtmpd"

rm -rf "$tmpd"

# 8x. 环境无关硬断言：收据不得为「没装的文件」背书。
# 旧缺陷（实测复现过）：目标里有一个外来软链时，--apply 会装其余 5 个、
# 写下覆盖全部 6 个 Skill 的收据、打印「完成」并返回 0 —— 收据作伪证，
# 而 exit code 正是 selftest / CI / pre-commit 唯一信任的信号。
neg_dir="$(mktemp -d "${TMPDIR:-/tmp}/aiw-neg.XXXXXX")"
mkdir -p "$neg_dir/fake/aiworflow" "$neg_dir/target"
echo "foreign" > "$neg_dir/fake/aiworflow/SKILL.md"
ln -s "$neg_dir/fake/aiworflow" "$neg_dir/target/aiworflow"
python3 scripts/install_skills.py --target "$neg_dir/target" --apply > "$neg_dir/out" 2>&1
neg_rc=$?
neg_installed=0
for n in aiworflow-planner aiworflow-implementer aiworflow-reviewer aiworflow-tester _shared; do
  [ -e "$neg_dir/target/$n" ] && neg_installed=$((neg_installed+1))
done
if [ "$neg_rc" -eq 0 ]; then
  echo "FAIL 外来目标上 --apply 竟返回 0（调用方会误判成功）"; cat "$neg_dir/out"; fail=$((fail+1))
elif [ -f "$neg_dir/target/aiworflow-install-receipt.json" ]; then
  echo "FAIL 收据为未安装的 Skill 背书（作伪证）"; fail=$((fail+1))
elif [ "$neg_installed" -ne 0 ]; then
  echo "FAIL 拒绝部分安装不彻底：仍装了 $neg_installed 个"; fail=$((fail+1))
elif [ "$(readlink "$neg_dir/target/aiworflow")" != "$neg_dir/fake/aiworflow" ]; then
  echo "FAIL 动到了不属于本包的文件（越界）"; fail=$((fail+1))
elif ! grep -q "拒绝部分安装" "$neg_dir/out"; then
  echo "FAIL 拒绝原因不可读（未打印『拒绝部分安装』+ 处置指引）"; cat "$neg_dir/out"; fail=$((fail+1))
else
  echo "PASS 外来目标：拒绝部分安装、零文件落地、零收据、不越界、原因可读"; pass=$((pass+1))
fi
python3 -c 'import shutil,sys;shutil.rmtree(sys.argv[1],ignore_errors=True)' "$neg_dir"

echo "== 9. author-time 硬护栏逐条生效（护栏 ID 必须被反例真实触发，不是文档承诺） =="
# 每条护栏都必须有一个专属反例证明它会开火；否则就是"配置存在 ≠ 行为有效"。
for pair in \
  "star_bypass:star-bypass" \
  "banned_block:self-review" \
  "unbounded_loop:unbounded-loop" \
  "unbounded_retry:unbounded-retry" \
  "secret_inline:secret-inline" \
  "unsafe_command:unsafe-command" \
  "evidence_free_gate:evidence-free-gate" ; do
  gid=${pair%%:*}; wf=${pair##*:}
  gout=$(python3 scripts/validate_workflow.py "workflows/_invalid/$wf.workflow.yaml" 2>&1)
  grc=$?
  if [ "$grc" -ne 0 ] && echo "$gout" | grep -q "\[$gid\]"; then
    echo "PASS 护栏 $gid 真实触发（_invalid/$wf）"; pass=$((pass+1))
  else
    echo "FAIL 护栏 $gid 未触发（exit=$grc）"; echo "$gout"; fail=$((fail+1))
  fi
done

# 9h. 护栏注册表完备性：注册了却没有任何反例触发的护栏 = 死护栏，必须暴露。
reg_out=$(python3 - <<'PYEOF'
import re, subprocess, sys
from pathlib import Path
sys.path.insert(0, "scripts")
import validate_workflow as vw
emitted = set()
for f in sorted(Path("workflows/_invalid").glob("*.workflow.yaml")):
    r = subprocess.run([sys.executable, "scripts/validate_workflow.py", str(f)],
                       capture_output=True, text=True)
    emitted |= set(re.findall(r"\[([a-z_]+)\]", r.stdout + r.stderr))
registered = set(vw.GUARDRAIL_IDS)
dead = sorted(registered - emitted - {"structural"})
unreg = sorted(emitted - registered)
if dead:
    print("DEAD:" + ",".join(dead))
if unreg:
    print("UNREGISTERED:" + ",".join(unreg))
if not dead and not unreg:
    print("OK")
PYEOF
)
if [ "$reg_out" = "OK" ]; then
  echo "PASS 护栏注册表完备（无死护栏、无未注册 ID）"; pass=$((pass+1))
else
  echo "FAIL 护栏注册表不完备"; echo "$reg_out"; fail=$((fail+1))
fi

echo "== 10. 运行期闸门（pre-commit）：安装状态必须可证明，不可静默篡改/覆盖 =="
# 为什么要有这一节：.git/hooks/ 不入版本库，「hook 存在」不能靠假设。
# 护栏若只靠人手动敲 selftest，改坏工作流的那次提交不会遇到任何阻力
# ——这正是两篇参考文章共同指出的「规范存在 ≠ 行为有效」。
hook_src="scripts/hooks/pre-commit"
hook_dir="$(mktemp -d "${TMPDIR:-/tmp}/aiw-hooks.XXXXXX")"

# 10.1 hook 本体合法：存在、语法通过、带标记、有执行位
if [ ! -f "$hook_src" ]; then
  echo "FAIL 缺 hook 本体 $hook_src"; fail=$((fail+1))
elif ! bash -n "$hook_src" 2>/dev/null; then
  echo "FAIL hook 本体语法错误"; fail=$((fail+1))
elif ! grep -q "aiworflow-pre-commit v3" "$hook_src"; then
  echo "FAIL hook 本体缺版本标记（安装器无法识别自己的产物）"; fail=$((fail+1))
elif [ ! -x "$hook_src" ]; then
  echo "FAIL hook 本体无执行位"; fail=$((fail+1))
else
  echo "PASS hook 本体合法（存在/语法/标记/执行位）"; pass=$((pass+1))
fi

# 10.2 安装器 dry-run 不写盘
if python3 scripts/install_hooks.py --dry-run --hook-dir "$hook_dir" > "$hook_dir/o" 2>&1 \
   && ! [ -e "$hook_dir/pre-commit" ]; then
  echo "PASS install_hooks --dry-run 不写盘"; pass=$((pass+1))
else
  echo "FAIL install_hooks --dry-run 行为异常"; cat "$hook_dir/o"; fail=$((fail+1))
fi

# 10.3 未安装时 --check 必须失败（不得谎报已装）
if python3 scripts/install_hooks.py --check --hook-dir "$hook_dir" > "$hook_dir/o" 2>&1; then
  echo "FAIL 未安装却 --check 通过（谎报）"; cat "$hook_dir/o"; fail=$((fail+1))
elif ! grep -q "install_hooks.py --apply" "$hook_dir/o"; then
  echo "FAIL --check 失败时未给出修复指令"; cat "$hook_dir/o"; fail=$((fail+1))
else
  echo "PASS 未安装时 --check 拒绝并指路 --apply"; pass=$((pass+1))
fi

# 10.4 安装后 --check 通过，且再装一次幂等
if python3 scripts/install_hooks.py --apply --hook-dir "$hook_dir" > "$hook_dir/o" 2>&1 \
   && python3 scripts/install_hooks.py --check --hook-dir "$hook_dir" >> "$hook_dir/o" 2>&1 \
   && python3 scripts/install_hooks.py --apply --hook-dir "$hook_dir" 2>&1 | grep -q "无需改动"; then
  echo "PASS install_hooks --apply 生效、--check 通过、重复 apply 幂等"; pass=$((pass+1))
else
  echo "FAIL install_hooks 安装/复核/幂等链路异常"; cat "$hook_dir/o"; fail=$((fail+1))
fi

# 10.5 已装 hook 被改一个字节 → --check 必须报漂移
printf '\n# tampered\n' >> "$hook_dir/pre-commit"
if python3 scripts/install_hooks.py --check --hook-dir "$hook_dir" > "$hook_dir/o" 2>&1; then
  echo "FAIL hook 被篡改却 --check 通过（漂移检测失效）"; fail=$((fail+1))
elif ! grep -q "不一致" "$hook_dir/o"; then
  echo "FAIL 漂移原因不可读"; cat "$hook_dir/o"; fail=$((fail+1))
else
  echo "PASS hook 被篡改时 --check 报漂移"; pass=$((pass+1))
fi

# 10.6 外来 hook 不被静默覆盖：先备份，卸载后能恢复
hk2="$(mktemp -d "${TMPDIR:-/tmp}/aiw-hooks2.XXXXXX")"
printf '#!/bin/sh\necho foreign-logic\n' > "$hk2/pre-commit"
chmod +x "$hk2/pre-commit"
if python3 scripts/install_hooks.py --apply --hook-dir "$hk2" > "$hk2/o" 2>&1 \
   && ls "$hk2"/pre-commit.foreign-backup-* >/dev/null 2>&1 \
   && grep -q "aiworflow-pre-commit v3" "$hk2/pre-commit" \
   && python3 scripts/install_hooks.py --uninstall --apply --hook-dir "$hk2" >> "$hk2/o" 2>&1 \
   && grep -q "foreign-logic" "$hk2/pre-commit"; then
  echo "PASS 外来 hook 先备份再安装、卸载后原样恢复（不静默吃掉别人的逻辑）"; pass=$((pass+1))
else
  echo "FAIL 外来 hook 保护链路异常"; cat "$hk2/o"; fail=$((fail+1))
fi
python3 -c 'import shutil,sys;[shutil.rmtree(d,ignore_errors=True) for d in sys.argv[1:]]' "$hook_dir" "$hk2"

# 10.7 本仓库自己的闸门必须在位（这一项与本机环境绑定，故按 §4 同样规则：
#      仅当本副本就是已锁定来源时才硬断言，否则 SKIP 并指路）
if [ "$rec_root" = "$repo_root" ]; then
  if python3 scripts/install_hooks.py --check > /tmp/aiw.out 2>&1; then
    echo "PASS 本副本 pre-commit 闸门在位且与来源一致"; pass=$((pass+1))
  else
    echo "FAIL 本副本 pre-commit 闸门缺失/漂移"; cat /tmp/aiw.out; fail=$((fail+1))
  fi
else
  echo "SKIP 本副本闸门在位性（本机安装目标属于其他来源根；python3 scripts/install_hooks.py --apply 可安装）"
fi

echo
echo "结果: $pass 通过, $fail 失败"
[ "$fail" -eq 0 ]

echo "== 11. 架构一致性与生产闭环护栏 =="
# 11a 正例：docs、feature workflow、HTML 三方必须由脚本判定一致。
if python3 scripts/validate_consistency.py \
  --docs docs/03-gates.md \
  --workflow workflows/feature-delivery.workflow.yaml \
  --html aiworflow-full-flow.html > /tmp/aiw-consistency.out 2>&1; then
  echo "PASS 架构一致性正检"; pass=$((pass+1))
else
  echo "FAIL 架构一致性正检"; cat /tmp/aiw-consistency.out; fail=$((fail+1))
fi

# 11b 负例：删除 G4/TDD Red 的篡改文档必须被拒绝，护栏不能只做 happy path。
negative_docs="$(mktemp)"
negative_out="$(mktemp)"
sed '/| G4 测试先行/d' docs/03-gates.md > "$negative_docs"
if python3 scripts/validate_consistency.py \
  --docs "$negative_docs" \
  --workflow workflows/feature-delivery.workflow.yaml \
  --html aiworflow-full-flow.html > "$negative_out" 2>&1; then
  echo "FAIL 缺失 G4/TDD Red 的文档竟被接受"; fail=$((fail+1))
elif ! grep -q "G4" "$negative_out" || ! grep -q "TDD Red" "$negative_out"; then
  echo "FAIL G4/TDD Red 护栏拒绝原因不可读"; cat "$negative_out"; fail=$((fail+1))
else
  echo "PASS G4/TDD Red 护栏开火且原因可读"; pass=$((pass+1))
fi
rm -f "$negative_docs" "$negative_out"

echo "== 12. 全站内容一致性（G7 增强 · 站点在线时计入，离线 SKIP） =="
# 真实条件执行：先探测站点，在线才跑校验并计数；离线显式 SKIP 不计数。
# （历史缺陷：本节曾位于 exit 之后恒不执行，"条件执行"实为死代码——闸门假象，v1.8.5 修复。）
if python3 -c 'import sys,urllib.request;sys.exit(0 if urllib.request.urlopen("http://127.0.0.1:8096",timeout=2).status==200 else 1)' 2>/dev/null; then
  if python3 scripts/validate_site_consistency.py --base http://127.0.0.1:8096; then
    echo "PASS 全站内容一致性（站点在线）"; pass=$((pass+1))
  else
    echo "FAIL 全站内容一致性"; fail=$((fail+1))
  fi
else
  echo "SKIP 全站内容一致性（127.0.0.1:8096 未启动；站点在线时自动计入，或手动：python3 scripts/validate_site_consistency.py --base http://127.0.0.1:8096）"
fi

echo ""
echo "== 13. 长周期任务恢复链（task.yaml / checkpoint / task_resume） =="
# 真实动机：数小时~数天任务的恢复能力此前只有协议文档（docs/30）与实现，零自检覆盖；
# 违反"新增能力必须新增自检项"。本节把恢复链变成可执行断言。

# 13a 模板存在且结构完整：task/progress/handoff 三段与恢复必需字段
tpl=skills/_shared/templates/task-state.yaml
if [ -f "$tpl" ] && grep -q '^task:' "$tpl" && grep -q '^progress:' "$tpl" && grep -q '^handoff:' "$tpl" \
  && grep -q 'current_block' "$tpl" && grep -q 'next_action' "$tpl" && grep -q 'last_session' "$tpl"; then
  echo "PASS task-state.yaml 模板存在且含恢复必需字段"; pass=$((pass+1))
else
  echo "FAIL task-state.yaml 模板缺失或缺少恢复必需字段（task/progress/handoff/current_block/next_action/last_session）"; fail=$((fail+1))
fi

# 13b checkpoint 写入：checkpoint_interval=1 时推进一轮必须落盘 checkpoint.yaml
mkdir -p "$tmpd/run-cp"
cat > "$tmpd/run-cp/state.yaml" <<'YAML'
schema_version: 1
run:
  id: SELFTEST-CP
  workflow: test
  status: running
  current_block_label: check
  finally_block_label: null
repository:
  root: /tmp
blocks:
  - label: impl
    status: completed
    attempts: 1
  - label: check
    status: pending
    attempts: 0
YAML
cat > "$tmpd/cp-wf.yaml" <<'YAML'
schema_version: 1
name: "检查点测试"
workflow_id: "selftest-cp"
error_code_mapping: {}
loop_control:
  checkpoint_interval: 1
blocks:
  - label: impl
    block_type: implement
    next_block_label: check
    role: implementer
    goal: "g"
    complete_criterion: "c"
  - label: check
    block_type: check
    next_block_label: null
    role: implementer
    goal: "g"
    complete_criterion: "c"
    commands:
      - {cmd: "echo ok", expect: 0}
YAML
cp_out=$(python3 scripts/run_flow.py "$tmpd/cp-wf.yaml" "$tmpd/run-cp" --advance --execute-check 2>&1)
if [ -f "$tmpd/run-cp/checkpoint.yaml" ] && grep -q '# checkpoint round' "$tmpd/run-cp/checkpoint.yaml" \
  && grep -q 'timestamp:' "$tmpd/run-cp/checkpoint.yaml" && grep -q '^check: ' "$tmpd/run-cp/checkpoint.yaml"; then
  echo "PASS checkpoint 按 interval 落盘（round/timestamp/块状态齐全）"; pass=$((pass+1))
else
  echo "FAIL checkpoint 未落盘或字段缺失"; echo "$cp_out"; cat "$tmpd/run-cp/checkpoint.yaml" 2>/dev/null; fail=$((fail+1))
fi

# 13c task_resume 正例：填充列表字段的 task.yaml 必须完整进入恢复提示词
#     （历史缺陷：轻量解析器不支持列表，completed_blocks 填充后丢失——恢复时不知道哪些块别重跑）
mkdir -p "$tmpd/TASK-SELFTEST-001"
cat > "$tmpd/TASK-SELFTEST-001/task.yaml" <<'YAML'
task:
  id: TASK-SELFTEST-001
  title: "自检用长周期任务"
  total_sessions: 3
  completed_sessions: 1
progress:
  phase: "spec"
  percentage: 40
  completed_blocks:
    - "intake"
    - "recon"
  current_block: "decision"
  next_action: "等待用户批准 Spec"
handoff:
  last_session: "RUN-SELFTEST-000"
  notes: "Spec 已完成"
timeline: []
YAML
resume_out=$(python3 scripts/task_resume.py "$tmpd/TASK-SELFTEST-001" 2>&1); resume_rc=$?
if [ "$resume_rc" -eq 0 ] && echo "$resume_out" | grep -q 'decision' \
  && echo "$resume_out" | grep -q 'intake' && echo "$resume_out" | grep -q 'recon' \
  && echo "$resume_out" | grep -q '等待用户批准 Spec' && echo "$resume_out" | grep -q 'RUN-SELFTEST-000'; then
  echo "PASS task_resume 恢复提示词完整（含已完成块列表/当前块/下一步/上次会话）"; pass=$((pass+1))
else
  echo "FAIL task_resume 丢失恢复必需信息"; echo "$resume_out"; fail=$((fail+1))
fi

# 13c-bis checkpoint/state/ledger 消费：恢复提示词必须给出机器快照与副作用不重复硬规则
cat > "$tmpd/TASK-SELFTEST-001/checkpoint.yaml" <<'YAML'
# checkpoint round 7
timestamp: "2026-09-20T10:00:00+00:00"
intake: completed
recon: completed
decision: running
YAML
cat > "$tmpd/TASK-SELFTEST-001/state.yaml" <<'YAML'
schema_version: 1
run: {id: TASK-SELFTEST-001, status: running}
blocks:
  - {label: intake, status: completed}
  - {label: recon, status: completed}
  - {label: decision, status: running}
ledger:
  - {round: 7, timestamp: "2026-09-20T10:00:00+00:00", block: decision, action: HANDOFF, signal: WAIT_USER, model: test-model, tokens_used: 123}
YAML
resume_cp=$(python3 scripts/task_resume.py "$tmpd/TASK-SELFTEST-001" 2>&1)
if echo "$resume_cp" | grep -q "checkpoint round：7" \
  && echo "$resume_cp" | grep -q "decision: running" \
  && echo "$resume_cp" | grep -q "state blocks：" \
  && echo "$resume_cp" | grep -q "model=test-model" \
  && echo "$resume_cp" | grep -q "已 completed 块的外部副作用（migration/commit/push）零重复执行"; then
  echo "PASS task_resume 消费 checkpoint/state/ledger 并给出副作用不重复规则"; pass=$((pass+1))
else
  echo "FAIL task_resume 未消费 checkpoint/state/ledger 或缺少副作用规则"; echo "$resume_cp"; fail=$((fail+1))
fi

# 13d task_resume 负例：task.yaml 缺失必须非零退出且报错可读（恢复链不假成功）
mkdir -p "$tmpd/TASK-EMPTY-001"
resume_neg=$(python3 scripts/task_resume.py "$tmpd/TASK-EMPTY-001" 2>&1); neg_rc=$?
if [ "$neg_rc" -ne 0 ] && echo "$resume_neg" | grep -q 'ERROR'; then
  echo "PASS task_resume 对缺失 task.yaml 非零退出且报错可读"; pass=$((pass+1))
else
  echo "FAIL task_resume 坏输入竟返回 0（假成功，会话会拿着空提示词继续）"; echo "rc=$neg_rc $resume_neg"; fail=$((fail+1))
fi

# 13e 容器兼容：长周期文件（task.yaml/checkpoint.yaml）与 runs 容器护栏不冲突
compat_run="runs/RUN-19700104-999"
if [ -e "$compat_run" ]; then
  echo "FAIL 残留 $compat_run（上次自检中断未清理，请人工确认后处理）"; fail=$((fail+1))
else
  mkdir -p "$compat_run"
  cp skills/_shared/templates/current.md skills/_shared/templates/evidence.md "$compat_run/" 2>/dev/null
  cp skills/_shared/templates/task-state.yaml "$compat_run/task.yaml"
  printf '# checkpoint round 3\ntimestamp: "2026-09-20T00:00:00+00:00"\nintake: completed\n' > "$compat_run/checkpoint.yaml"
  python3 - "$compat_run" <<'PY'
import sys, yaml
from pathlib import Path
d = Path(sys.argv[1])
base = yaml.safe_load(Path("skills/_shared/templates/run-state.yaml").read_text(encoding="utf-8"))
base["run"].update({"id": d.name, "workflow": "feature-delivery",
                    "workflow_path": "../../workflows/feature-delivery.workflow.yaml",
                    "status": "created"})
base["repository"].update({"root": "/tmp/x", "current_branch": "wp/x",
                           "current_sha": "a" * 40, "target_branch": "develop",
                           "target_base_sha": "a" * 40, "integration_branch": ""})
base["blocks"] = [{"label": b["label"], "status": "pending", "role": b.get("role", "planner"),
                   "gate": b.get("gate"), "base_sha": None, "head_sha": None,
                   "tested_sha": None, "attempts": 0, "error_codes": []}
                  for b in yaml.safe_load(Path("workflows/feature-delivery.workflow.yaml").read_text(encoding="utf-8"))["blocks"]]
base["gates"] = {}
(d / "state.yaml").write_text(yaml.safe_dump(base, allow_unicode=True, sort_keys=False), encoding="utf-8")
PY
  if python3 scripts/validate_run.py "$compat_run" > /tmp/aiw-compat.out 2>&1; then
    echo "PASS 含 task.yaml/checkpoint.yaml 的 run 容器不误报"; pass=$((pass+1))
  else
    echo "FAIL 长周期文件竟被容器护栏误报"; cat /tmp/aiw-compat.out; fail=$((fail+1))
  fi
  python3 -c 'import shutil,sys;shutil.rmtree(sys.argv[1],ignore_errors=True)' "$compat_run"
  if [ -e "$compat_run" ]; then echo "FAIL 兼容性 fixture 未清理干净"; fail=$((fail+1)); fi
fi

echo "结果: $pass 通过, $fail 失败"
exit "$fail"
