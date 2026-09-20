#!/usr/bin/env python3
"""候选 DAG 编译器（意图层 LLM → 编译层脚本，见 docs/16 §三）。

职责边界：
- 输入是 Planner（LLM）产出的**候选** workflow YAML（结构可能漂移）。
- 本脚本做确定性归一化 + 全量结构校验 + 变更预算检查，输出可冻结的产物。
- 不猜测业务意图：缺字段只报错，不静默补全关键语义（label/role/gate/next）。
- 编译通过 ≠ G4 冻结；冻结仍由 Planner 在 approve(G3) 之后执行并写 state.yaml。

用法：
  python3 scripts/compile_dag.py <candidate.yaml> [-o compiled.workflow.yaml] [--max-blocks N]
退出码：0 = 编译通过；1 = 拒绝（打印全部违规项）；2 = 参数错误。
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

try:
    import yaml  # type: ignore
    def load_yaml_text(text: str):
        return yaml.safe_load(text)
except Exception:
    from _yaml_min import loads as _min_loads
    def load_yaml_text(text: str):
        return _min_loads(text)

# 预算硬上限（与 AGENTS.md 切分门禁同口径的块级约束；防止 LLM 生成不可执行的巨图）。
DEFAULT_MAX_BLOCKS = 40


def normalize(data, errors):
    """确定性归一化：只修格式漂移，不发明语义。"""
    if not isinstance(data, dict):
        errors.append("顶层必须是 map")
        return data

    # 常见 LLM 漂移：schema_version 写成字符串
    sv = data.get("schema_version")
    if isinstance(sv, str) and sv.strip().isdigit():
        data["schema_version"] = int(sv.strip())

    # 常见漂移：blocks 键写成大写或嵌套在顶层自创字段里
    if "blocks" not in data:
        for alt in ("Blocks", "BLOCKS", "block"):
            if alt in data:
                data["blocks"] = data.pop(alt)
                break

    blocks = data.get("blocks")
    if not isinstance(blocks, list):
        errors.append("blocks 必须是列表")
        return data

    for b in blocks:
        if not isinstance(b, dict):
            continue
        # 常见漂移：id/name 代替 label
        if "label" not in b:
            for alt in ("id", "name", "block_id"):
                if isinstance(b.get(alt), str):
                    b["label"] = b.pop(alt)
                    break
        # 常见漂移：type/blockType 代替 block_type
        if "block_type" not in b:
            for alt in ("type", "blockType", "block_kind"):
                if isinstance(b.get(alt), str):
                    b["block_type"] = b.pop(alt)
                    break
        # 常见漂移：next/next_label/next_block 代替 next_block_label
        if "next_block_label" not in b:
            for alt in ("next", "next_label", "next_block", "nextLabel"):
                if alt in b:
                    b["next_block_label"] = b.pop(alt)
                    break
        # 常见漂移：star 写成字符串
        if isinstance(b.get("star"), str):
            b["star"] = b["star"].strip().lower() in ("true", "yes", "1")
    return data


def budget_check(data, max_blocks, errors):
    blocks = data.get("blocks")
    if isinstance(blocks, list) and len(blocks) > max_blocks:
        errors.append(f"块数 {len(blocks)} 超过预算上限 {max_blocks}；候选 DAG 过大，必须拆分工作包")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate", help="Planner 产出的候选 workflow YAML")
    ap.add_argument("-o", "--output", default=None, help="编译产物路径（默认 <candidate>.compiled.yaml）")
    ap.add_argument("--max-blocks", type=int, default=DEFAULT_MAX_BLOCKS)
    args = ap.parse_args()

    src = Path(args.candidate)
    if not src.exists():
        print(f"FAIL: 候选文件不存在: {src}")
        return 2

    text = src.read_text(encoding="utf-8")
    errors = []
    try:
        data = load_yaml_text(text)
    except Exception as e:
        print(f"REJECT {src}: YAML 解析失败: {e}")
        return 1

    data = normalize(data, errors)
    budget_check(data, args.max_blocks, errors)

    out = Path(args.output) if args.output else src.with_suffix(".compiled.yaml")
    # 归一化结果先落盘，再交给 validate_workflow.py 做全量结构规则（单一事实源，不复制规则）。
    try:
        import yaml as _y  # type: ignore
        out.write_text(_y.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    except Exception:
        # 无 PyYAML：归一化结果无法安全序列化。直接拒绝，避免产物与被校验对象不一致。
        print(f"REJECT {src}: 环境无 PyYAML，无法序列化归一化结果；请安装 PyYAML 后重试")
        return 1

    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_workflow.py"), str(out)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        errors.append("validate_workflow 拒绝:\n" + (proc.stdout + proc.stderr).strip())

    if errors:
        print(f"REJECT {src}")
        for e in errors:
            print(f"  - {e}")
        # 编译失败不保留半成品
        if out.exists():
            out.unlink()
        return 1

    print(f"COMPILED {src} -> {out}")
    print("下一步：G4 冻结由 Planner 执行（写 state.yaml + evidence.md），本脚本不代签。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
