#!/usr/bin/env python3
"""状态写入时校验：diff state.prev.yaml → state.yaml，拦截非法 transition。

用法：python3 scripts/validate_transition.py <runs/<RUN-ID>> [--prev state.prev.yaml]
退出码：0 = 通过；1 = 失败。

契约（与 docs/05-state-and-evidence.md 轨道 B 一致）：
- 本脚本只读校验，绝不写 state.yaml —— 唯一写入者仍是 Planner。
- 快照来源：Planner 覆写 state.yaml 前必须 `cp state.yaml state.prev.yaml`；
  写入后立即运行本脚本，FAIL 则回滚本次写入并按报错修正。
- 工作流绑定（T-03/T-04 的 gate/star）取 run 声明的 DAG 定义
  （resolve_workflow_path：优先编译产物，回落 workflows/ 模板）。

规则编号（稳定，供 selftest 反例断言）：
- T-01 新置 passed:true 的门禁，owner 必须 ∈ GATE_ROLES[gate]
     （import validate_workflow 的定义，不复制 —— 堵住"Planner 代签 G9"类越权）。
- T-02 块状态机：pending→running→completed|failed|skipped|canceled|terminated|timed_out；
     failed→pending 为 run_flow --retry 的合法语义；
     completed→running|failed 仅当本次写入新增了返修凭据（error_codes 增量非空）。
- T-03 新 completed 块的 gate 必须与工作流定义的门禁绑定一致。
- T-04 attempts 单调不减；star:true 块新增 completion 必须有人工证据
     （approvals[label] / approvals.user / 该块门禁 evidence_ref 指向 APPROVAL-* 锚点）。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

try:
    import yaml

    def _load(text):
        return yaml.safe_load(text)
except Exception:
    from _yaml_min import loads as _load

# GATE_ROLES 与 validate_run.py / validate_workflow.py 同一份定义，import 复用不复制。
sys.path.insert(0, str(ROOT / "scripts"))
from validate_workflow import GATE_ROLES  # noqa: E402
from validate_run import resolve_workflow_path  # noqa: E402

# 块状态合法迁移表（终态不可迁出；同态=无迁移，恒合法）。
LEGAL_TRANSITIONS = {
    "pending": {"running", "skipped", "canceled", "terminated", "timed_out"},
    "running": {"completed", "failed", "canceled", "terminated", "timed_out"},
    "failed": {"pending", "running", "canceled", "terminated", "timed_out"},
    "completed": {"running", "failed"},  # 仅限带返修凭据，见 T-02
    "skipped": set(),
    "canceled": set(),
    "terminated": set(),
    "timed_out": set(),
}

errors = []


def err(rule, msg):
    errors.append(f"[{rule}] {msg}")


def load_yaml_file(path):
    return _load(path.read_text(encoding="utf-8"))


def index_blocks(state):
    """state.blocks list → {label: block-dict}。"""
    out = {}
    for b in (state or {}).get("blocks") or []:
        if isinstance(b, dict) and b.get("label"):
            out[b["label"]] = b
    return out


def workflow_bindings(run, run_dir):
    """工作流定义 → ({label: gate}, {label: star})；定义不可用时返回 ({}, {})。"""
    wf_path = resolve_workflow_path(run_dir, run or {})
    if wf_path is None or not wf_path.exists():
        return {}, {}
    try:
        data = load_yaml_file(wf_path)
    except Exception:
        return {}, {}
    if not isinstance(data, dict):
        return {}, {}
    gates, stars = {}, {}

    def walk(blocks):
        for b in blocks or []:
            if not isinstance(b, dict):
                continue
            if b.get("label"):
                gates[b["label"]] = b.get("gate")
                stars[b["label"]] = bool(b.get("star"))
            for key in ("loop_blocks",):
                if isinstance(b.get(key), list):
                    walk(b[key])

    walk(data.get("blocks"))
    return gates, stars


def validate(prev, curr, run_dir):
    curr_run = curr.get("run") or {}
    prev_run = prev.get("run") or {}

    # ---- T-01 门禁 owner：只审"本次新置 passed:true"的门禁 ----
    prev_gates = prev.get("gates") or {}
    curr_gates = curr.get("gates") or {}
    if not isinstance(prev_gates, dict):
        prev_gates = {}
    for g, v in (curr_gates.items() if isinstance(curr_gates, dict) else []):
        if not isinstance(v, dict) or v.get("passed") is not True:
            continue
        pv = prev_gates.get(g)
        already = isinstance(pv, dict) and pv.get("passed") is True
        if already:
            continue
        owner = (v.get("owner") or "").strip()
        if g in GATE_ROLES and owner not in GATE_ROLES[g]:
            err("T-01", f"gate {g} 新置 passed:true 但 owner {owner!r} 不在 "
                        f"{sorted(GATE_ROLES[g])} 中（GATE_ROLES 之外的角色不得签该门禁）")

    # ---- T-02/T-04 块迁移、attempts、star 人工证据 ----
    prev_blocks = index_blocks(prev)
    curr_blocks = index_blocks(curr)
    wf_gates, wf_stars = workflow_bindings(curr_run, run_dir)
    approvals = curr.get("approvals")
    if not isinstance(approvals, dict):
        approvals = {}
    for label, b in curr_blocks.items():
        p = prev_blocks.get(label)
        prev_status = p.get("status") if isinstance(p, dict) else "pending"
        prev_attempts = p.get("attempts") if isinstance(p, dict) else 0
        status = b.get("status")
        prev_codes = set(p.get("error_codes") or []) if isinstance(p, dict) else set()
        new_codes = set(b.get("error_codes") or [])

        # T-02 状态机
        if status != prev_status:
            allowed = LEGAL_TRANSITIONS.get(prev_status, set())
            if status not in allowed:
                err("T-02", f"块 {label!r} 非法迁移 {prev_status!r} → {status!r}"
                            f"（合法目标：{sorted(allowed) or '无（终态）'}）")
            elif prev_status == "completed" and status in ("running", "failed"):
                added = new_codes - prev_codes
                if not added:
                    err("T-02", f"块 {label!r} completed → {status!r} 必须携带本次新增的"
                                f"返修凭据（error_codes 增量为空）")

        # T-03 新 completed 块的 gate 绑定
        if status == "completed" and prev_status != "completed" and label in wf_gates:
            if (b.get("gate") or None) != (wf_gates[label] or None):
                err("T-03", f"块 {label!r} 新置 completed 但 gate "
                            f"{b.get('gate')!r} 与工作流绑定 {wf_gates[label]!r} 不一致")

        # T-04 attempts 单调
        try:
            if int(b.get("attempts") or 0) < int(prev_attempts or 0):
                err("T-04", f"块 {label!r} attempts 由 {prev_attempts} 减到 "
                            f"{b.get('attempts')}（必须单调不减）")
        except (TypeError, ValueError):
            pass  # 非数值由 validate_run 的结构校验负责

        # T-04 star 块人工证据
        if (status == "completed" and prev_status != "completed"
                and wf_stars.get(label)):
            gate_entry = curr_gates.get(b.get("gate")) if isinstance(curr_gates, dict) else None
            ev_ref = ""
            if isinstance(gate_entry, dict):
                ev_ref = gate_entry.get("evidence_ref") or ""
            has_approval = (
                bool(approvals.get(label))
                or bool(approvals.get("user"))
                or "APPROVAL-" in str(ev_ref)
            )
            if not has_approval:
                err("T-04", f"块 {label!r} 为 star:true 人工边界，新置 completed 但缺人工证据"
                            f"（需 approvals[{label!r}] / approvals.user / 门禁 evidence_ref 指向 APPROVAL-*）")

    # 未使用的变量显式声明，避免误读为遗漏
    _ = prev_run


def main(argv):
    ap = argparse.ArgumentParser(description="state.prev.yaml → state.yaml 写入时迁移校验")
    ap.add_argument("run_dir", help="runs/<RUN-ID> 目录")
    ap.add_argument("--prev", default="state.prev.yaml",
                    help="旧快照文件名（相对 run 目录，默认 state.prev.yaml）")
    args = ap.parse_args(argv)

    run_dir = Path(args.run_dir)
    prev_file = run_dir / args.prev
    curr_file = run_dir / "state.yaml"

    if not curr_file.exists():
        print(f"FAIL: {args.run_dir} 缺少 state.yaml")
        return 1
    if not prev_file.exists():
        print(f"FAIL: {args.run_dir} 缺少 {args.prev}（Planner 覆写 state.yaml 前必须 "
              f"`cp state.yaml {args.prev}` 建立快照）")
        return 1

    try:
        prev = load_yaml_file(prev_file)
        curr = load_yaml_file(curr_file)
    except Exception as e:
        print(f"FAIL: {args.run_dir} 快照解析失败: {e}")
        return 1
    if not isinstance(prev, dict) or not isinstance(curr, dict):
        print(f"FAIL: {args.run_dir} 快照顶层必须是 map")
        return 1

    validate(prev, curr, run_dir)

    if errors:
        print(f"FAIL: {args.run_dir}（本次 state.yaml 写入含 {len(errors)} 处非法迁移）")
        for e in errors:
            print(f"  - {e}")
        print("处置：回滚本次写入（cp 回 state.prev.yaml），按报错修正后再写。")
        return 1
    print(f"PASS: {args.run_dir}（state.prev.yaml → state.yaml 迁移合法）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
