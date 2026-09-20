#!/usr/bin/env python3
"""校验一个 Run 容器：结构、状态合法性、证据引用可达、SHA 格式。

用法：python3 validate_run.py <runs/<RUN-ID>>
退出码：0 = 通过；1 = 失败。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

try:
    import yaml
    def _load(text):
        return yaml.safe_load(text)
except Exception:
    from _yaml_min import loads as _load

# GATE_ROLES: gate → 允许的 owner 角色集合，与 validate_workflow.py 同一份定义。
# 这里 import 复用，不复制正文，避免两份定义漂移。
sys.path.insert(0, str(ROOT / 'scripts'))
from validate_workflow import GATE_ROLES  # noqa: E402

RUN_STATUSES = {"created", "queued", "running", "paused", "completed",
                "failed", "canceled", "terminated", "timed_out"}
BLOCK_STATUSES = {"pending", "running", "completed", "failed", "terminated",
                  "canceled", "timed_out", "skipped"}
ROLE_NAMES = {"planner", "implementer", "reviewer", "tester", "user"}
SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")
RUN_ID_RE = re.compile(r"^RUN-\d{8}-\d{3}$")
ISO_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")

errors = []


def err(msg):
    errors.append(msg)


def resolve_workflow_path(p, run):
    """定位 state.yaml 声明的 DAG 定义文件（编译产物或包内模板）。

    优先 `run.workflow_path`（相对 run 目录解析，指向 compile_dag.py 的编译产物）；
    回落到 `workflows/<run.workflow>.workflow.yaml`。返回 Path 或 None。
    """
    declared = run.get("workflow_path")
    if isinstance(declared, str) and declared.strip():
        cand = (p / declared).resolve()
        if cand.exists():
            return cand
        return cand  # 不存在也返回，由调用方报"指向的定义不存在"
    wf = run.get("workflow")
    if isinstance(wf, str) and wf:
        return ROOT / "workflows" / f"{wf}.workflow.yaml"
    return None


def collect_workflow_labels(path):
    """读取 DAG 定义的全部块标签（含 loop_blocks 子块），失败返回 None。"""
    try:
        data = load_yaml(path)
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    labels = []

    def walk(blocks):
        for b in blocks or []:
            if not isinstance(b, dict):
                continue
            if b.get("label"):
                labels.append(b["label"])
            for key in ("loop_blocks",):
                if isinstance(b.get(key), list):
                    walk(b[key])

    walk(data.get("blocks"))
    return labels


def load_yaml(path):
    try:
        import yaml
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        from _yaml_min import loads
        return loads(path.read_text(encoding="utf-8"))



def _verify_evidence_refs(gate_name, ref_str, run_dir):
    """验证 evidence_ref 指向的文件和锚点真实存在。
    支持两种锚点约定：## Anchor 标题（markdown）和 id: Anchor（YAML 记录）。
    ref_str 可以 ; 或 , 分隔多个引用。"""
    for part in re.split(r'[;,]\s*', ref_str):
        part = part.strip()
        if not part:
            continue
        m = re.match(r'^(?P<file>[^#]+)#(?P<anchor>.+)$', part)
        if not m:
            continue
        ref_file = m.group('file')
        ref_anchor = m.group('anchor').strip()
        resolved = run_dir / ref_file
        if not resolved.exists():
            alt = ROOT / ref_file
            if alt.exists():
                resolved = alt
            else:
                err(f"gate {gate_name} evidence_ref 文件不存在: {part}")
                continue
        try:
            content = resolved.read_text(encoding='utf-8', errors='replace')
        except Exception:
            err(f"gate {gate_name} evidence_ref 文件不可读: {ref_file}")
            continue
        escaped = re.escape(ref_anchor)
        # 锚点后跟空格、行尾、左括号，或中间点（如 REVIEW-001 · ...）
        h2 = re.search(rf'^##\s+{escaped}(?:\s|$|\(|·)', content, re.MULTILINE)
        yid = re.search(rf'^id:\s*{escaped}\s*$', content, re.MULTILINE)
        if not h2 and not yid:
            err(f"gate {gate_name} evidence_ref 锚点不存在: {part}（{ref_file} 中未找到 ## {ref_anchor} 或 id: {ref_anchor}）")


def check_mapping_keys(obj, required, where):
    if not isinstance(obj, dict):
        err(f"{where} 必须是 map")
        return
    for k in required:
        if k not in obj:
            err(f"{where} 缺少字段: {k}")


def check_sha(v, where):
    """SHA 合法判别：null 与 '' 等价（均表示"尚未绑定"），非空时才校验格式。"""
    if v is None:
        return
    s = str(v)
    if s == '':
        return
    if not SHA_RE.match(s):
        err(f"{where} SHA 格式非法: {v!r}")


def _skipped_has_credential(label, raw_text):
    """R-1 辅助：skipped 块的跳过凭据 = error_codes 非空，或块文本段内带实质注释。

    docs/05 轨道 B 要求 skipped 必须写原因；既有实践把原因写在行尾/邻近注释
    （如 `# not taken`、`# D-02 not_applicable：...`）。error_codes 是机器可读
    首选，注释是兼容旧实践的最低凭据。解析器看不到注释，故对原文做确定性扫描。
    """
    lines = raw_text.splitlines()
    n = len(lines)
    for i, line in enumerate(lines):
        if "status: skipped" not in line:
            continue
        # 块起点：本行（flow 风格单行块）或向上回溯 label 行（block 风格）
        if f"label: {label}" in line or f"label: '{label}'" in line or f'label: "{label}"' in line:
            start = i
        else:
            start = None
            for j in range(i - 1, max(i - 8, -1), -1):
                if "status: skipped" in lines[j] or "error_codes" in lines[j]:
                    continue
                if f"label: {label}" in lines[j]:
                    start = j
                    break
                if "- label:" in lines[j] or "- {label:" in lines[j]:
                    break
            if start is None:
                continue
        # 块终点：下一个块起点或新的顶层键
        end = n
        for j in range(start + 1, n):
            if "- label:" in lines[j] or "- {label:" in lines[j]:
                end = j
                break
            if lines[j] and not lines[j][0].isspace() and not lines[j].startswith("-"):
                end = j
                break
        for j in range(start, end):
            if "#" in lines[j]:
                comment = lines[j].split("#", 1)[1].strip()
                if len(comment) >= 3:
                    return True
    return False


def check_created_at(v, where):
    if not isinstance(v, str):
        err(f"{where}.created_at 必须是字符串")
        return
    if not ISO_TS_RE.match(v):
        err(f"{where}.created_at 时间格式非法: {v!r}")
        return
    time_part = v.split("T", 1)[1][:8]
    if time_part == "00:00:00":
        err(f"{where}.created_at 不得为 00:00:00（需真实带时区时间）")


def validate_review(p, run_dir):
    try:
        r = load_yaml(p)
    except Exception as e:
        err(f"{run_dir}/review.yaml 解析失败: {e}")
        return
    check_mapping_keys(r, ["schema_version", "review_id", "supersedes", "mode",
                           "reviewer", "created_at", "target", "verdict", "summary",
                           "findings", "non_blocking_notes", "residual_risks",
                           "evidence_reviewed", "unblock_conditions"], "review.yaml")
    if isinstance(r, dict):
        if r.get("mode") not in {"SPEC_REVIEW", "TEST_REVIEW", "CODE_REVIEW", "RELEASE_REVIEW", "BASELINE_REVIEW"}:
            err(f"review.yaml.mode 非法: {r.get('mode')!r}")
        if r.get("verdict") not in {"APPROVE", "REQUEST_CHANGES", "BLOCKED"}:
            err(f"review.yaml.verdict 非法: {r.get('verdict')!r}")
        check_created_at(r.get("created_at"), "review.yaml")
        tgt = r.get("target")
        if isinstance(tgt, dict):
            check_sha(tgt.get("base_sha"), "review.yaml.target.base_sha")
            check_sha(tgt.get("head_sha"), "review.yaml.target.head_sha")
            check_sha(tgt.get("tested_sha"), "review.yaml.target.tested_sha")
        else:
            err("review.yaml.target 必须是 map")


def validate_test_report(p, run_dir):
    try:
        r = load_yaml(p)
    except Exception as e:
        err(f"{run_dir}/test-report.yaml 解析失败: {e}")
        return
    check_mapping_keys(r, ["schema_version", "test_report_id", "supersedes", "mode",
                           "tester", "created_at", "target", "environment", "result",
                           "summary", "cases", "defects", "coverage"], "test-report.yaml")
    if isinstance(r, dict):
        if r.get("mode") not in {"INCREMENTAL", "FULL", "SMOKE", "REGRESSION", "CONTRACT", "PERMISSION", "STATE_TRANSITION"}:
            err(f"test-report.yaml.mode 非法: {r.get('mode')!r}")
        if r.get("result") not in {"PASS", "FAIL", "BLOCKED", "NOT_RUN"}:
            err(f"test-report.yaml.result 非法: {r.get('result')!r}")
        check_created_at(r.get("created_at"), "test-report.yaml")
        tgt = r.get("target")
        if isinstance(tgt, dict):
            check_sha(tgt.get("tested_sha"), "test-report.yaml.target.tested_sha")
        else:
            err("test-report.yaml.target 必须是 map")
        if not isinstance(r.get("cases"), list):
            err("test-report.yaml.cases 必须是 list")


def validate_impl_report(p, run_dir):
    try:
        r = load_yaml(p)
    except Exception as e:
        err(f"{run_dir}/implementation-report.yaml 解析失败: {e}")
        return
    check_mapping_keys(r, ["schema_version", "impl_id", "supersedes", "implementer",
                           "created_at", "block_label", "target", "summary",
                           "files_changed", "tests_run", "verification",
                           "known_issues", "follow_ups"], "implementation-report.yaml")
    if isinstance(r, dict):
        check_created_at(r.get("created_at"), "implementation-report.yaml")
        tgt = r.get("target")
        if isinstance(tgt, dict):
            check_sha(tgt.get("base_sha"), "implementation-report.yaml.target.base_sha")
            check_sha(tgt.get("head_sha"), "implementation-report.yaml.target.head_sha")
        else:
            err("implementation-report.yaml.target 必须是 map")
        if not isinstance(r.get("files_changed"), list):
            err("implementation-report.yaml.files_changed 必须是 list")
        if not isinstance(r.get("tests_run"), list):
            err("implementation-report.yaml.tests_run 必须是 list")


def validate_artifacts(p):
    review = p / "review.yaml"
    if review.exists():
        validate_review(review, p.name)
    impl = p / "implementation-report.yaml"
    if impl.exists():
        validate_impl_report(impl, p.name)
    tr = p / "test-report.yaml"
    if tr.exists():
        validate_test_report(tr, p.name)


def main(path):
    p = Path(path)
    if not p.is_dir():
        print(f"FAIL: {path} 不是目录")
        return 1

    if not RUN_ID_RE.match(p.name):
        err(f"Run ID 格式错误: {p.name}（应为 RUN-YYYYMMDD-NNN）")

    state_file = p / "state.yaml"
    if not state_file.exists():
        err("缺少 state.yaml")
        print(f"FAIL: {path}")
        for e in errors:
            print(f"  - {e}")
        return 1

    try:
        state = load_yaml(state_file)
    except Exception as e:
        err(f"state.yaml 解析失败: {e}")
        print(f"FAIL: {path}")
        for e in errors:
            print(f"  - {e}")
        return 1
    raw_state_text = state_file.read_text(encoding="utf-8")

    if not isinstance(state, dict):
        err("state.yaml 顶层必须是 map")
    else:
        top_required = ["schema_version", "run", "repository", "blocks", "gates",
                        "versions", "approvals", "open_findings", "open_defects",
                        "open_blockers", "completion_contract"]
        check_mapping_keys(state, top_required, "state.yaml")

        run = state.get("run") or {}
        if isinstance(run, dict):
            if run.get("status") not in RUN_STATUSES:
                err(f"run.status 非法: {run.get('status')!r}")
            wf = run.get("workflow")
            if not isinstance(wf, str) or not wf:
                err(f"run.workflow 非法: {wf!r}")
            else:
                # 定义可以来自包内模板（workflows/<id>.workflow.yaml），也可以来自本 run
                # 的候选 DAG 编译产物（runs/<RUN-ID>/workflow.compiled.yaml，见
                # docs/18-dag-pipeline.md 与 planner references/task-decomposition.md）。
                # 二者至少其一必须存在；块一致性由下方 state_dag_mismatch 护栏检查。
                template = ROOT / "workflows" / f"{wf}.workflow.yaml"
                resolved = resolve_workflow_path(p, run)
                if not template.exists() and not (resolved and resolved.exists()):
                    err(
                        f"run.workflow {wf!r} 无对应定义："
                        f"既没有 workflows/{wf}.workflow.yaml，"
                        f"也没有可用的 run.workflow_path 编译产物"
                    )
        else:
            err("state.yaml.run 必须是 map")

        repo = state.get("repository") or {}
        if isinstance(repo, dict):
            repo_required = ["root", "current_branch", "current_sha", "target_branch",
                             "target_base_sha", "integration_branch", "integration_sha",
                             "dirty_worktree_detected", "dirty_worktree_overlap"]
            check_mapping_keys(repo, repo_required, "state.yaml.repository")
            for key in ("current_sha", "target_base_sha", "integration_sha"):
                check_sha(repo.get(key), f"state.yaml.repository.{key}")
        else:
            err("state.yaml.repository 必须是 map")

        blocks = state.get("blocks")
        if not isinstance(blocks, list):
            err("state.yaml.blocks 必须是 list")
        else:
            for b in blocks:
                if not isinstance(b, dict):
                    err("block 必须是 map")
                    continue
                block_required = ["label", "status", "role", "gate", "base_sha", "head_sha",
                                  "tested_sha", "attempts", "error_codes"]
                check_mapping_keys(b, block_required, f"block[{b.get('label')!r}]")
                if b.get("status") not in BLOCK_STATUSES:
                    err(f"block {b.get('label')!r} status 非法: {b.get('status')!r}")
                if b.get("role") not in ROLE_NAMES:
                    err(f"block {b.get('label')!r} role 非法: {b.get('role')!r}")
                for key in ("base_sha", "head_sha", "tested_sha"):
                    check_sha(b.get(key), f"block[{b.get('label')!r}].{key}")

        # 护栏 state_dag_mismatch：state.yaml 的块必须与它声明的 DAG 定义逐块一致。
        # 为什么必须有这一条：run_flow.py 用 workflow_path 的图连边、用 state.yaml 的
        # status 推进。两边块名不一致时，解释器既不报错也不停，只是永远算出一个
        # 与真实进度无关的 frontier —— 确定性执行器静默失效，门禁退化为口头声明。
        if isinstance(run, dict) and isinstance(blocks, list):
            wf_path = resolve_workflow_path(p, run)
            if wf_path is None:
                err("state.yaml 未声明可用的 DAG 定义（run.workflow_path 或 run.workflow 至少一个有效）")
            elif not wf_path.exists():
                err(f"state.yaml 声明的 DAG 定义不存在: {wf_path}")
            else:
                wf_labels = collect_workflow_labels(wf_path)
                if wf_labels is None:
                    err(f"DAG 定义解析失败: {wf_path}")
                else:
                    state_labels = [
                        b.get("label") for b in blocks if isinstance(b, dict)
                    ]
                    wf_set, state_set = set(wf_labels), set(state_labels)
                    for extra in state_labels:
                        if extra not in wf_set:
                            err(
                                f"state.yaml 块 {extra!r} 不在 DAG 定义 {wf_path.name} 中"
                                f"（块名必须与定义逐块一致，否则 run_flow.py 的 frontier 与真实进度无关）"
                            )
                    for missing in wf_labels:
                        if missing not in state_set:
                            err(f"DAG 定义 {wf_path.name} 的块 {missing!r} 在 state.yaml 中缺失")
                    dup = {x for x in state_labels if state_labels.count(x) > 1}
                    for d in sorted(dup):
                        err(f"state.yaml 块标签重复: {d!r}")

                    # 护栏 dag_semantics：容器结构合法 ≠ 语义一致。真实动机（2026-09-20
                    # 实测，docs/31 §2.2）：close 已 completed 但 spec 从未开始，validate_run
                    # 却 PASS——run_flow 的 frontier 与 state 各说各话，"完成"沦为口头声明。
                    # R-3 语义在此明文固定：未登记的工作流块一律视为 pending。
                    try:
                        from run_flow import build_graph
                        wf_data = load_yaml(wf_path) or {}
                        wf_blocks = [b for b in wf_data.get("blocks") or []
                                     if isinstance(b, dict)]
                        succ, pred, wf_labels_g, _cond = build_graph(wf_blocks)
                        eff = {b["label"]: b.get("status")
                               for b in blocks if isinstance(b, dict) and b.get("label")}
                        for lab in wf_labels_g:
                            eff.setdefault(lab, "pending")  # R-3：未登记 = pending

                        def ancestors(label):
                            seen, stack = set(), list(pred.get(label, []))
                            while stack:
                                u = stack.pop()
                                if u in seen:
                                    continue
                                seen.add(u)
                                stack.extend(pred.get(u, []))
                            return seen

                        # R-1：completed 块的全部 DAG 祖先必须 completed/skipped；
                        #     skipped 祖先必须携带 error_codes 跳过凭据。
                        for lab in sorted(wf_labels_g):
                            if eff.get(lab) != "completed":
                                continue
                            for anc in sorted(ancestors(lab)):
                                st = eff.get(anc)
                                if st == "skipped":
                                    reg = next((b for b in blocks if isinstance(b, dict)
                                                and b.get("label") == anc), None)
                                    cred = ((reg or {}).get("error_codes") or []) \
                                        or str((reg or {}).get("skip_reason") or "").strip() \
                                        or _skipped_has_credential(anc, raw_state_text)
                                    if not cred:
                                        err(f"R-1: 块 {lab!r} 已 completed，但祖先 {anc!r} 为 "
                                            f"skipped 且无跳过凭据（error_codes/skip_reason/注释均为空）")
                                elif st not in ("completed", "skipped"):
                                    err(f"R-1: 块 {lab!r} 已 completed，但祖先 {anc!r} 状态为 "
                                        f"{st!r}（completed 块的全部祖先必须 completed/skipped）")

                        # R-2：run.status == completed ⇒ 全部块 terminal（completed/skipped，
                        #     即 frontier 必空），且 finally 块必须 completed。
                        if run.get("status") == "completed":
                            for lab in sorted(wf_labels_g):
                                if eff.get(lab) not in ("completed", "skipped"):
                                    err(f"R-2: run.status=completed 但块 {lab!r} 状态为 "
                                        f"{eff.get(lab)!r}（frontier 必须为空）")
                            fin = wf_data.get("finally_block_label")
                            if fin and eff.get(fin) != "completed":
                                err(f"R-2: run.status=completed 但 finally 块 {fin!r} 状态为 "
                                    f"{eff.get(fin)!r}（finally 必须已 completed）")
                    except ImportError:
                        pass  # run_flow 不可用时跳过语义层（结构层护栏仍在）

        gates = state.get("gates")
        if isinstance(gates, dict):
            for g, v in gates.items():
                if not re.match(r"^G(\d{1,2})$", g):
                    err(f"gate 键名非法: {g!r}")
                    continue
                if not isinstance(v, dict):
                    err(f"gate {g} 必须是 map")
                    continue
                if "passed" in v and not isinstance(v["passed"], bool):
                    err(f"gate {g}.passed 必须是 bool")

                # gate owner 护栏（参考 a03：Verification Agent 才是 Gate）
                gate_owner = (v.get("owner") or "").strip()
                if gate_owner and g in GATE_ROLES:
                    if gate_owner not in GATE_ROLES[g]:
                        err(f"gate {g} owner {gate_owner!r} 不在 {GATE_ROLES[g]} 中")

                # evidence_ref 可达性护栏（参考 a01+a12：确定性规则引擎先扫锚点可达性）
                ref = (v.get("evidence_ref") or "").strip()
                if ref:
                    _verify_evidence_refs(g, ref, p)
        else:
            err("state.yaml.gates 必须是 map")

        for key in ("open_findings", "open_defects", "open_blockers"):
            if not isinstance(state.get(key), list):
                err(f"state.yaml.{key} 必须是 list")
        if not isinstance(state.get("completion_contract"), list):
            err("state.yaml.completion_contract 必须是 list")

    # 核心文件的存在性与状态关联：中间态允许尚未生成 test-plan。
    run_status = (state.get("run") or {}).get("status") if isinstance(state, dict) else None
    for f in ("current.md", "evidence.md"):
        if run_status not in {"created", "queued"} and not (p / f).exists():
            err(f"缺少 {f}（{run_status} 状态必须存在）")
    if run_status == "completed" and not (p / "test-plan.md").exists():
        err("缺少 test-plan.md（completed 状态必须存在）")

    validate_artifacts(p)

    if errors:
        print(f"FAIL: {path}")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"PASS: {path}（Run 容器结构合法）")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python3 validate_run.py <runs/<RUN-ID>>")
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
