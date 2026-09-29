#!/usr/bin/env python3
"""metrics_summary · 只读 run 度量聚合（v1.9.0，docs/29 F3+F5 / docs/13 evals 最小落地）

在 list_runs.py（单目录逐 run 视图）之上做三件它不做的事：
  1. 跨目录聚合：一次吃多个 runs 目录（主副本 + 各工程副本），统一口径汇总；
  2. 分组维度：按 workflow（task_type 代理）与按 model 出成功率/返修/耗时/token 行；
  3. token 诚实口径：ledger 有 model 的行数、其中 tokens_used 实报数与 null 数分开统计，
     只对实报求和——查不到就是 null，绝不估算（与 run_flow --session-meta 同一纪律）。

只读：不写任何文件。基线漂移对比用 --baseline 显式传入（docs/37 数字），脚本不内嵌基线。

用法：
  python3 scripts/metrics_summary.py runs /path/to/wancall/.ai_worflow/runs [...]
  python3 scripts/metrics_summary.py runs --baseline first_pass=0.938,median_span_min=159.6

输出：逐目录 key=value 行 + 分组行 + 汇总行（机器可 grep）。
退出码：0 正常（含空目录 WARN）；2 用法错误（所有目录都不存在）。
"""
from __future__ import annotations

import argparse
import json
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
    """聚合单个 run 目录；解析失败降级为 note，不炸整个视图（与 list_runs 同纪律）。"""
    info: dict = {"id": run_dir.name}
    state_path = run_dir / "state.yaml"
    if not state_path.exists():
        info["placeholder"] = True
        return info
    try:
        state = _load(state_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        info["parse_error"] = str(exc)
        return info
    run = state.get("run") or {}
    blocks = state.get("blocks") or []
    ledger = state.get("ledger") or []

    done = sum(1 for b in blocks if isinstance(b, dict) and b.get("status") == "completed")
    retries = sum(
        max(0, int(b.get("attempts") or 1) - 1)
        for b in blocks if isinstance(b, dict)
    )
    stamps = [t for t in (_parse_ts(e.get("timestamp")) for e in ledger if isinstance(e, dict)) if t]
    span_min = None
    if len(stamps) >= 2:
        span = (max(stamps) - min(stamps)).total_seconds() / 60
        if span > 0:
            span_min = round(span, 1)
    # token 诚实口径：只数 ledger 里带 model 的行；tokens_used 为非负整数才算实报
    token_rows = [e for e in ledger if isinstance(e, dict) and e.get("model")]
    tokens_reported = []
    tokens_null = 0
    for e in token_rows:
        tv = e.get("tokens_used")
        if isinstance(tv, int) and not isinstance(tv, bool) and tv >= 0:
            tokens_reported.append(tv)
        else:
            tokens_null += 1

    info.update({
        "workflow": str(run.get("workflow") or "?"),
        "status": str(run.get("status") or "?"),
        "blocks_done": done,
        "blocks_total": len(blocks),
        "rounds": len([e for e in ledger if isinstance(e, dict)]),
        "retries": retries,
        "span_min": span_min,
        "models": sorted({str(e.get("model")) for e in token_rows}),
        "tokens_reported": tokens_reported,
        "tokens_null": tokens_null,
    })
    return info


def _median(vals: list[float]):
    if not vals:
        return None
    s = sorted(vals)
    n = len(s)
    return s[n // 2] if n % 2 else round((s[n // 2 - 1] + s[n // 2]) / 2, 1)


def _group_label(dir_path: Path) -> str:
    """runs 目录的分组标签：…/<工程>/.ai_worflow/runs → 工程名；其余取父目录名。"""
    if dir_path.parent.name == ".ai_worflow":
        return dir_path.parent.parent.name or dir_path.name
    return dir_path.parent.name or dir_path.name


def _fmt_group(prefix: str, items: list[dict]) -> list[str]:
    lines = []
    by_wf: dict[str, list[dict]] = {}
    for i in items:
        by_wf.setdefault(i["workflow"], []).append(i)
    for wf, runs in sorted(by_wf.items()):
        comp = [i for i in runs if i["status"] == "completed"]
        with_led = [i for i in runs if i["rounds"] > 0]
        comp_led = [i for i in comp if i["rounds"] > 0]
        fp = [i for i in comp_led if i["retries"] == 0]
        med = _median([float(i["span_min"]) for i in comp_led if i["span_min"] is not None])
        lines.append(
            f"{prefix}wf:{wf} runs={len(runs)} completed={len(comp)} with_ledger={len(with_led)} "
            f"first_pass={len(fp)}/{len(comp_led)} retries={sum(i['retries'] for i in runs)} "
            f"median_span_min={med if med is not None else 'n/a'}"
        )
    # model 行只做 token 口径 + 出现 run 数（一个 run 可能换模型，tokens 无法按 model 精拆，
    # 摊给该 run ledger 的首个 model——诚实口径：跨 model 精拆需要 ledger 行级归因，当前不伪造）
    runs_by_model: dict[str, int] = {}
    tokens_by_model: dict[str, list[int]] = {}
    null_by_model: dict[str, int] = {}
    for i in items:
        # tokens_reported 无法按 model 拆（一个 run 可能换模型）；按 run 的 model 列表摊给首个 model
        m = i["models"][0] if i["models"] else None
        if not m:
            continue
        runs_by_model[m] = runs_by_model.get(m, 0) + 1
        tokens_by_model.setdefault(m, []).extend(i["tokens_reported"])
        null_by_model[m] = null_by_model.get(m, 0) + i["tokens_null"]
    for m in sorted(runs_by_model):
        rep = tokens_by_model[m]
        token_txt = f"tokens_reported={len(rep)} tokens_sum={sum(rep)}" if rep else "tokens_reported=0"
        lines.append(
            f"{prefix}model:{m} runs={runs_by_model[m]} {token_txt} tokens_null={null_by_model[m]}"
        )
    return lines


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="只读 run 度量聚合（跨目录 / 分组 / token 诚实口径）")
    ap.add_argument("runs_dirs", nargs="*", default=[], help="一个或多个 runs 目录（默认 ./runs）")
    ap.add_argument("--baseline", default="", help="显式基线对比，如 first_pass=0.938,median_span_min=159.6（±20% 告警，docs/29 F5）")
    ap.add_argument("--json", action="store_true", help="输出 JSON（机器消费）")
    args = ap.parse_args(argv)

    dirs = [Path(d) for d in args.runs_dirs] or [Path("runs")]
    existing = [d for d in dirs if d.is_dir()]
    for d in dirs:
        if not d.is_dir():
            print(f"WARN: runs 目录不存在，跳过：{d}", file=sys.stderr)
    if not existing:
        print("FAIL: 所有 runs 目录均不存在")
        return 2

    per_dir: dict[str, list[dict]] = {}
    used_labels: dict[str, int] = {}
    for d in existing:
        label = _group_label(d)
        n = used_labels.get(label, 0)
        used_labels[label] = n + 1
        if n:
            label = f"{label}-{n + 1}"
        infos = [_collect(rd) for rd in sorted(d.iterdir()) if rd.is_dir() and rd.name.startswith("RUN-")]
        per_dir[label] = infos

    out_lines: list[str] = []
    all_parsed: list[dict] = []
    for label, infos in per_dir.items():
        parsed = [i for i in infos if "workflow" in i]
        all_parsed.extend(parsed)
        with_led = [i for i in parsed if i["rounds"] > 0]
        comp_led = [i for i in with_led if i["status"] == "completed"]
        fp = [i for i in comp_led if i["retries"] == 0]
        med = _median([float(i["span_min"]) for i in comp_led if i["span_min"] is not None])
        rep = sum(len(i["tokens_reported"]) for i in parsed)
        nul = sum(i["tokens_null"] for i in parsed)
        out_lines.append(
            f"[{label}] runs_total={len(infos)} parsed={len(parsed)} "
            f"placeholder={sum(1 for i in infos if i.get('placeholder'))} "
            f"completed_with_ledger={len(comp_led)} first_pass={len(fp)}/{len(comp_led)} "
            f"rounds={sum(i['rounds'] for i in parsed)} retries={sum(i['retries'] for i in parsed)} "
            f"median_span_min={med if med is not None else 'n/a'} tokens_reported={rep} tokens_null={nul}"
        )
        out_lines.extend(_fmt_group("  ", parsed))

    comp_led_all = [i for i in all_parsed if i["rounds"] > 0 and i["status"] == "completed"]
    fp_all = [i for i in comp_led_all if i["retries"] == 0]
    med_all = _median([float(i["span_min"]) for i in comp_led_all if i["span_min"] is not None])
    rep_all = sum(len(i["tokens_reported"]) for i in all_parsed)
    nul_all = sum(i["tokens_null"] for i in all_parsed)
    summary = (
        f"汇总(全部): runs_total={sum(len(v) for v in per_dir.values())} parsed={len(all_parsed)} "
        f"completed_with_ledger={len(comp_led_all)} first_pass={len(fp_all)}/{len(comp_led_all)} "
        f"total_rounds={sum(i['rounds'] for i in all_parsed)} total_retries={sum(i['retries'] for i in all_parsed)} "
        f"median_span_min={med_all if med_all is not None else 'n/a'} "
        f"tokens_reported={rep_all} tokens_null={nul_all}"
    )
    out_lines.append(summary)

    if args.baseline and comp_led_all:
        fp_rate = round(len(fp_all) / len(comp_led_all), 4)
        base: dict[str, str] = {}
        for kv in args.baseline.split(","):
            if "=" in kv:
                k, v = kv.split("=", 1)
                base[k.strip()] = v.strip()
        drift_parts = []
        if "first_pass" in base and med_all is not None or "first_pass" in base:
            try:
                bfp = float(base["first_pass"])
                if bfp > 0:
                    d = round((fp_rate - bfp) / bfp * 100, 1)
                    drift_parts.append(f"first_pass={fp_rate}（基线 {bfp}，偏差 {d:+.1f}%{' ⚠ 超出±20%' if abs(d) > 20 else ''}）")
            except ValueError:
                pass
        if "median_span_min" in base and med_all is not None:
            try:
                bmed = float(base["median_span_min"])
                if bmed > 0:
                    d = round((float(med_all) - bmed) / bmed * 100, 1)
                    drift_parts.append(f"median_span_min={med_all}（基线 {bmed}，偏差 {d:+.1f}%{' ⚠ 超出±20%' if abs(d) > 20 else ''}）")
            except ValueError:
                pass
        if drift_parts:
            out_lines.append("基线对比: " + "；".join(drift_parts) + "（样本小，偏差只作信号不作结论）")

    if args.json:
        print(json.dumps({"per_dir": {k: v for k, v in per_dir.items()}, "lines": out_lines},
                         ensure_ascii=False, default=str))
    else:
        for line in out_lines:
            print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
