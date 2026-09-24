#!/usr/bin/env python3
"""list_runs · 只读 run 聚合视图（v1.8.17）

回答「任务拆了几个 run、各自什么状态、推进了多少轮、返修几次」。
只读：不写任何文件；不判断质量（那是 Reviewer 的职责），只聚合 state.yaml 已有事实。

用法：
  python3 scripts/list_runs.py [--runs-dir runs]

输出：逐 run 一行 + 固定 key=value 汇总行（机器可 grep）。
退出码：0 正常（含占位/WARN）；2 用法错误。
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

try:
    import yaml  # type: ignore

    def _load(text: str):
        return yaml.safe_load(text)
except Exception:
    from _yaml_min import loads as _min_loads

    def _load(text: str):
        return _min_loads(text)


def _parse_ts(value) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _collect(run_dir: Path) -> dict:
    """聚合单个 run 目录；不抛异常，异常降级为 note 字段。"""
    info: dict = {"id": run_dir.name, "note": ""}
    state_path = run_dir / "state.yaml"
    if not state_path.exists():
        info["placeholder"] = True
        return info
    try:
        state = _load(state_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # 解析失败不炸整个视图
        info["parse_error"] = str(exc)
        return info
    run = state.get("run") or {}
    blocks = state.get("blocks") or []
    ledger = state.get("ledger") or []

    info["workflow"] = str(run.get("workflow") or "")
    info["status"] = str(run.get("status") or "?")
    info["depth"] = str(run.get("delivery_depth") or "")
    info["owner"] = str(run.get("planner_owner") or "")
    done = sum(1 for b in blocks if isinstance(b, dict) and b.get("status") == "completed")
    info["blocks"] = f"{done}/{len(blocks)}"
    info["rounds"] = len([e for e in ledger if isinstance(e, dict)])
    info["retries"] = sum(
        max(0, int(b.get("attempts") or 1) - 1)
        for b in blocks
        if isinstance(b, dict)
    )
    stamps = [t for t in (_parse_ts(e.get("timestamp")) for e in ledger if isinstance(e, dict)) if t]
    info["first_ts"] = min(stamps) if stamps else None
    info["last_ts"] = max(stamps) if stamps else None
    if info["first_ts"] and info["last_ts"] and info["last_ts"] > info["first_ts"]:
        info["span_min"] = round((info["last_ts"] - info["first_ts"]).total_seconds() / 60, 1)
    else:
        info["span_min"] = None
    return info


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="只读 run 聚合视图")
    ap.add_argument("--runs-dir", default="runs", help="runs 目录（默认 ./runs）")
    args = ap.parse_args(argv)

    runs_root = Path(args.runs_dir)
    if not runs_root.is_dir():
        print(f"FAIL: runs 目录不存在：{runs_root}")
        return 2

    run_dirs = sorted(p for p in runs_root.iterdir() if p.is_dir() and p.name.startswith("RUN-"))
    if not run_dirs:
        print(f"（{runs_root} 下无 RUN-* 目录）")
        print("汇总: runs_total=0")
        return 0

    header = f"{'RUN-ID':<22}{'DATE':<11}{'WORKFLOW':<14}{'STATUS':<12}{'BLOCKS':<9}{'ROUNDS':<8}{'RETRIES':<9}{'SPAN(min)':<11}OWNER"
    print(header)
    print("-" * len(header))
    infos = []
    for run_dir in run_dirs:
        info = _collect(run_dir)
        infos.append(info)
        if info.get("placeholder"):
            print(f"{info['id']:<22}{'-':<11}{'（占位/白名单）':<14}")
            continue
        if "parse_error" in info:
            print(f"{info['id']:<22}{'-':<11}{'（state 解析失败）':<14}{info['parse_error'][:40]}")
            continue
        date_part = info["id"][4:12] if len(info["id"]) >= 12 else "-"
        date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}" if date_part != "-" and date_part.isdigit() else "-"
        span = info["span_min"] if info["span_min"] is not None else "-"
        print(
            f"{info['id']:<22}{date:<11}{info['workflow'][:12]:<14}{info['status'][:10]:<12}"
            f"{info['blocks']:<9}{info['rounds']:<8}{info['retries']:<9}{str(span):<11}{info['owner'][:12]}"
        )

    parsed = [i for i in infos if "workflow" in i]
    with_ledger = [i for i in parsed if i["rounds"] > 0]
    multi_round = [i for i in with_ledger if i["rounds"] >= 2 and i.get("span_min") is not None]
    total_rounds = sum(i["rounds"] for i in parsed)
    total_retries = sum(i["retries"] for i in parsed)
    # 一次通过（口径见 docs/37）：分母=终态 completed 且有账本的 run；分子=其中零返修（全块 attempts==1）
    completed_ledger = [i for i in with_ledger if i["status"] == "completed"]
    first_pass = [i for i in completed_ledger if i["retries"] == 0]
    spans = sorted(i["span_min"] for i in multi_round)

    def _median(vals: list[float]) -> float | None:
        if not vals:
            return None
        n = len(vals)
        return vals[n // 2] if n % 2 else round((vals[n // 2 - 1] + vals[n // 2]) / 2, 1)

    status_counts: dict[str, int] = {}
    for i in parsed:
        status_counts[i["status"]] = status_counts.get(i["status"], 0) + 1
    status_txt = " ".join(f"{k}={v}" for k, v in sorted(status_counts.items()))
    placeholders = sum(1 for i in infos if i.get("placeholder"))
    fp_rate = f"{len(first_pass)}/{len(completed_ledger)}" if completed_ledger else "n/a"
    median_span = _median([float(s) for s in spans]) if spans else None

    print()
    print(
        f"汇总: runs_total={len(infos)} parsed={len(parsed)} placeholder={placeholders} {status_txt} | "
        f"runs_with_ledger={len(with_ledger)} completed_with_ledger={len(completed_ledger)} "
        f"total_rounds={total_rounds} total_retries={total_retries} | "
        f"first_pass={fp_rate} median_span_min={median_span if median_span is not None else 'n/a'}"
    )
    if placeholders:
        print(f"注：{placeholders} 个占位目录见 runs/README.md 白名单（机器可读，validate_package 第 10 步）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
