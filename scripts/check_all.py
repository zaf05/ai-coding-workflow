#!/usr/bin/env python3
"""全系统日检：逐 run 校验 + 陈旧 run 检测 + 安装收据/hook 汇总（只读）。

用法：python3 scripts/check_all.py [--runs-dir runs] [--skip-install]
退出码：0 = 无未登记 FAIL（允许存在 WARN）；1 = 存在未登记的 validate_run FAIL。

边界（刻意设计，勿"顺手增强"）：
- 本脚本**不写**任何 state.yaml：`timed_out` 等状态的唯一写入者是 Planner，
  这里只产出建议（run ID、停滞时长、建议动作）。
- 陈旧判定用文件 mtime 而非账本时间戳：账本时间戳可伪造，mtime 不能。
  口径：last_activity = max(mtime(state.yaml), mtime(evidence.md),
  mtime(task.yaml), mtime(checkpoint.yaml))，超过 run.max_elapsed_time_minutes
  （缺省 240）即 WARN。
- 白名单：在 runs/README.md "已登记的占位目录" 表中登记过的 run，validate_run FAIL
  计为"已登记的已知问题"（WARN 级），不拉低退出码——恒定 FAIL 会被当噪音，
  护栏被当噪音就等于没有（与 validate_package 第 10 步同一哲学）。
- 安装收据/安装 hook 的漂移计为 WARN：是否 --upgrade 由用户决定。
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

try:
    import yaml

    def _load(text):
        return yaml.safe_load(text)
except Exception:
    sys.path.insert(0, str(ROOT / "scripts"))
    from _yaml_min import loads as _load

ACTIVITY_FILES = ("state.yaml", "evidence.md", "task.yaml", "checkpoint.yaml")
STALE_STATUSES = {"running", "paused"}
DEFAULT_MAX_ELAPSED = 240

warns = []
fails = []


def load_yaml_file(path):
    return _load(path.read_text(encoding="utf-8"))


def registered_names(runs_dir):
    """解析 runs/README.md 占位登记表 → {目录名}（机器可读白名单）。"""
    readme = runs_dir / "README.md"
    if not readme.exists():
        return set()
    out = set()
    for line in readme.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        for c in cells:
            if c.startswith("`RUN-") and (c.endswith("/`") or c.endswith("`")):
                out.add(c.strip("`").rstrip("/"))
    return out


def check_run(run_dir, registry):
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_run.py"), str(run_dir)],
                       capture_output=True, text=True)
    name = run_dir.name
    if r.returncode == 0:
        print(f"PASS {name}")
        return
    first_err = next((l for l in (r.stdout + r.stderr).splitlines() if l.strip().startswith("- ")), "")
    if name in registry:
        warns.append(f"run {name}: validate_run FAIL（已登记白名单，属已知问题）{first_err}")
        print(f"WARN {name}（已登记白名单）{first_err}")
    else:
        fails.append(f"run {name}: validate_run FAIL{first_err}")
        print(f"FAIL {name} {first_err}")
        print("     处置：修复该 run，或在 runs/README.md 登记为占位（不允许恒定 FAIL 沦为噪音）")


def check_stale(run_dir):
    state_file = run_dir / "state.yaml"
    if not state_file.exists():
        return
    try:
        state = load_yaml_file(state_file)
    except Exception:
        return
    if not isinstance(state, dict):
        return
    run = state.get("run") or {}
    if not isinstance(run, dict) or run.get("status") not in STALE_STATUSES:
        return
    mtimes = [run_dir / f for f in ACTIVITY_FILES]
    mtimes = [p.stat().st_mtime for p in mtimes if p.exists()]
    if not mtimes:
        return
    last_activity = max(mtimes)
    try:
        limit_min = int(run.get("max_elapsed_time_minutes") or DEFAULT_MAX_ELAPSED)
    except (TypeError, ValueError):
        limit_min = DEFAULT_MAX_ELAPSED
    idle_min = int((time.time() - last_activity) / 60)
    if idle_min > limit_min:
        age_h = idle_min / 60
        warns.append(
            f"run {run_dir.name}: status={run.get('status')} 已停滞 {idle_min} 分钟"
            f"（约 {age_h:.1f} 小时），超过 max_elapsed_time_minutes={limit_min}。"
            f"建议：续跑刷新账本，或由 Planner 判定标记 timed_out/terminated 并记录原因"
        )
        print(f"WARN {run_dir.name} 停滞 {idle_min} 分钟 > {limit_min}（建议：续跑或 Planner 标记 timed_out/terminated）")


def check_install(cmd, label):
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / cmd), "--check"],
                       capture_output=True, text=True)
    if r.returncode == 0:
        print(f"PASS {label}")
        return
    detail = (r.stdout + r.stderr).strip().splitlines()
    detail = detail[0] if detail else "（无输出）"
    warns.append(f"{label}: {cmd} --check 报漂移 → {detail}")
    print(f"WARN {label}: {detail}")
    print("     处置：确认后运行 --upgrade --apply 同步（是否升级由用户决定）")


def main(argv):
    ap = argparse.ArgumentParser(description="AIWorflow 全系统只读日检")
    ap.add_argument("--runs-dir", default=str(ROOT / "runs"), help="runs 目录（默认 <root>/runs）")
    ap.add_argument("--skip-install", action="store_true",
                    help="跳过安装收据/hook 汇总（隔离环境自检用）")
    args = ap.parse_args(argv)

    runs_dir = Path(args.runs_dir)
    if not runs_dir.is_dir():
        print(f"FAIL runs 目录不存在: {runs_dir}")
        return 1
    registry = registered_names(runs_dir)

    print(f"== 1. 逐 run 校验（{runs_dir}） ==")
    for d in sorted(runs_dir.iterdir()):
        if d.is_dir():
            check_run(d, registry)

    print("== 2. 陈旧 run 检测（mtime 口径，只建议不代写） ==")
    for d in sorted(runs_dir.iterdir()):
        if d.is_dir():
            check_stale(d)

    if not args.skip_install:
        print("== 3. 安装与闸门一致性 ==")
        check_install("install_skills.py", "Skill 收据")
        check_install("install_hooks.py", "pre-commit 闸门")
    else:
        print("== 3. 安装与闸门一致性（--skip-install，跳过） ==")

    print()
    print(f"汇总: FAIL {len(fails)} · WARN {len(warns)}（明细见上；WARN 不拉低退出码）")
    if fails:
        for f in fails:
            print(f"  FAIL {f}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
