#!/usr/bin/env python3
"""dep_graph · 只读代码依赖图（v1.9.0，docs/29 F2 · 附录 038/054 code-review-graph 同族最小版）

回答「改这个文件会波及谁」。两档精度，诚实标注：
  Python：stdlib ast 精确解析 import / from-import（含相对导入按包路径还原）；
  其他语言（.ts/.tsx/.js/.mjs/.go）：正则近似扫描 import 语句，JSON 里标 "approx": true，
  近似文件的 imports 只是线索，不进入 imported_by 精确口径与 --file 爆炸半径。

只读：不写任何文件。扫描自动跳过 runs/、references/、site/、node_modules 等（SKIP_DIRS）。

用法：
  python3 scripts/dep_graph.py --root scripts                       # 概览 + 最多被依赖文件
  python3 scripts/dep_graph.py --root scripts --file run_flow.py    # 传递爆炸半径（被谁依赖）
  python3 scripts/dep_graph.py --root . --json                      # 全图 JSON（review 用）

退出码：0 正常；2 用法错误（root 不存在 / --file 不在图内）。
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

SKIP_DIRS = {"__pycache__", ".git", "node_modules", "references", "runs", "site", ".worktree", ".venv"}

_JS_LIKE = re.compile(r"""(?:import\s+[^;'"]*?\s+from\s*|import\s*|require\(\s*)['"]([^'"]+)['"]""")
_GO_LIKE = re.compile(r'import\s+(?:_\s+)?"([^"]+)"')

# 后缀 → 近似 import 扫描规则（None = 不做 import 分析，只登记文件）
_APPROX_RULES: dict[str, re.Pattern | None] = {
    ".ts": _JS_LIKE, ".tsx": _JS_LIKE, ".js": _JS_LIKE, ".mjs": _JS_LIKE, ".go": _GO_LIKE,
}


def _imports_from_ast(tree: ast.Module, rel_mod: str) -> list[str]:
    """收集本文件 import 的模块名（顶层名 + 完整点路径都收，供精确匹配）。

    相对导入（from . import x / from ..pkg import y）按包路径还原成绝对点路径。
    """
    names: set[str] = set()
    pkg_parts = rel_mod.split(".")[:-1] if "." in rel_mod else []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                names.add(a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:  # 相对导入：按包路径还原
                base = pkg_parts[: len(pkg_parts) - (node.level - 1)] if node.level > 1 else pkg_parts
                if node.module:
                    names.add(".".join(base + node.module.split(".")))
                else:
                    for a in node.names:
                        names.add(".".join(base + [a.name]))
            elif node.module:
                names.add(node.module.split(".")[0])
                names.add(node.module)
    return sorted(names)


def _defs_from_ast(tree: ast.Module) -> tuple[list[str], list[str]]:
    funcs, classes = [], []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs.append(node.name)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
    return funcs, classes


def build_graph(root: Path) -> dict:
    """扫描 root 构建 {relpath: {imports, imported_by, functions, classes, approx, lines}}。"""
    files: dict[str, dict] = {}
    py_modules: list[str] = []  # 点路径模块名（来自可解析的 .py）

    for p in sorted(root.rglob("*")):
        if not p.is_file() or any(part in SKIP_DIRS for part in p.parts):
            continue
        rel = p.relative_to(root)
        key = str(rel.with_suffix("")).replace("\\", "/")
        entry: dict = {"imports": [], "imported_by": [], "functions": [], "classes": [],
                       "approx": False, "lines": len(p.read_text(encoding="utf-8", errors="replace").splitlines())}
        if p.suffix == ".py":
            rel_mod = key.replace("/", ".")
            try:
                tree = ast.parse(p.read_text(encoding="utf-8"))
            except SyntaxError as exc:
                entry["parse_error"] = f"SyntaxError: line {exc.lineno}"
            else:
                entry["imports"] = _imports_from_ast(tree, rel_mod)
                entry["functions"], entry["classes"] = _defs_from_ast(tree)
                py_modules.append(rel_mod)
        else:
            rule = _APPROX_RULES.get(p.suffix)
            if rule is not None:
                text = p.read_text(encoding="utf-8", errors="replace")
                mods = {m for m in rule.findall(text) if m and not m.startswith(".")}
                entry["imports"] = sorted(m.split("/")[-1].rsplit(".", 1)[0] or m for m in mods)
                entry["approx"] = True
        files[key] = entry

    # 模块名 → 文件 key（点路径全名优先，短名兜底；同短名时首个胜出并保持稳定）
    mod_to_file: dict[str, str] = {}
    for mod in sorted(py_modules):
        key = mod.replace(".", "/")
        mod_to_file.setdefault(mod, key)
        mod_to_file.setdefault(mod.split(".")[-1], key)

    # 正向重建精确边：A imports M、M 解析到文件 B ⇒ B.imported_by += A（仅 Python ast 边）
    for key, entry in files.items():
        if entry.get("approx") or "parse_error" in entry:
            continue
        for imp in entry["imports"]:
            target = mod_to_file.get(imp)
            if target and target != key:
                files[target]["imported_by"].append(key)
    for entry in files.values():
        entry["imported_by"] = sorted(set(entry["imported_by"]))
    return files


def blast_radius(files: dict, target: str) -> list[str]:
    """被依赖方向的传递闭包（改 target 会波及谁）。只用 Python 精确边。"""
    seen: set[str] = set()
    frontier = [target]
    while frontier:
        for dep in files.get(frontier.pop(), {}).get("imported_by", []):
            if dep not in seen:
                seen.add(dep)
                frontier.append(dep)
    return sorted(seen)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="只读代码依赖图（Python ast 精确 + 其他语言正则近似）")
    ap.add_argument("--root", default=".", help="扫描根目录（默认当前目录；自动跳过 runs/references/site 等）")
    ap.add_argument("--file", default="", help="目标文件（相对 root，如 scripts/run_flow.py）→ 传递爆炸半径")
    ap.add_argument("--json", action="store_true", help="输出全图 JSON")
    args = ap.parse_args(argv)

    root = Path(args.root)
    if not root.is_dir():
        print(f"FAIL: root 不存在：{root}")
        return 2
    files = build_graph(root)
    if not files:
        print(f"（{root} 下无可分析文件）")
        return 0

    if args.file:
        needle = args.file.replace("\\", "/")
        if needle.endswith(".py"):
            needle = needle[:-3]
        match = next((f for f in files if f == needle or f.split("/")[-1] == needle), None)
        if not match:
            print(f"FAIL: --file 不在图内：{args.file}")
            return 2
        radius = blast_radius(files, match)
        e = files[match]
        print(f"目标: {match}  imports={len(e['imports'])}  defs={len(e['functions']) + len(e['classes'])}")
        for dep in radius:
            d = files[dep]
            print(f"  波及: {dep}  (defs={len(d['functions']) + len(d['classes'])})")
        print(f"爆炸半径: direct_and_transitive={len(radius)}")
        return 0

    if args.json:
        print(json.dumps({"root": str(root), "files": files}, ensure_ascii=False, indent=1))
        return 0

    py_count = sum(1 for e in files.values() if not e["approx"] and "parse_error" not in e)
    approx_count = sum(1 for e in files.values() if e["approx"])
    err_count = sum(1 for e in files.values() if "parse_error" in e)
    print(f"files={len(files)} python={py_count} approx={approx_count} parse_error={err_count}")
    for f, e in sorted(files.items(), key=lambda kv: -len(kv[1]["imported_by"]))[:5]:
        if e["imported_by"]:
            print(f"  最多被依赖: {f}  imported_by={len(e['imported_by'])} -> {', '.join(e['imported_by'][:4])}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
