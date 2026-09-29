#!/usr/bin/env python3
"""context_search · 本地语料 BM25 检索（v1.9.0，docs/29 F4 Phase 1）

回答「这个知识点/规则在哪篇文档」。纯 Python BM25（k1=1.5, b=0.75），零新依赖：
  中文按字符二元组（bigram）建索引，拉丁词按小写整词——中文查询无需分词器；
  可选加载 context/index.yaml 的 tags/keywords 作为加权 token（存在则 ×2 计入）。

只读检索；`--write-index` 是唯一写行为（重建第一个 dir 下的 index.yaml，从标题/文件名生成
tags/keywords，供后续检索加权）。runs/ 永不在默认扫描范围。

用法：
  python3 scripts/context_search.py 断点恢复                      # 默认扫 context/
  python3 scripts/context_search.py 人工确认 --dirs context docs --top 8
  python3 scripts/context_search.py --write-index                 # 重建 context/index.yaml

退出码：0 正常（含无命中）；2 用法错误（目录不存在）。
"""
from __future__ import annotations

import argparse
import datetime
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

try:
    import yaml  # type: ignore

    def _dump(obj) -> str:
        return yaml.safe_dump(obj, allow_unicode=True, sort_keys=False)

    def _load(text: str):
        return yaml.safe_load(text)
except Exception:
    from _yaml_min import loads as _min_loads

    def _dump(obj) -> str:  # _yaml_min 无 dump：极简手写（仅本工具 index 格式）
        lines = ["generated_at: " + str(obj.get("generated_at", ""))]
        lines.append("files:")
        for f, meta in obj.get("files", {}).items():
            lines.append(f"  {f}:")
            lines.append(f"    title: {meta.get('title', '')}")
            tags = meta.get("tags") or []
            kw = meta.get("keywords") or []
            lines.append("    tags: [" + ", ".join(tags) + "]")
            lines.append("    keywords: [" + ", ".join(kw) + "]")
        return "\n".join(lines) + "\n"

    def _load(text: str):
        return _min_loads(text)


_LATIN = re.compile(r"[a-z0-9_\-]{2,}")
_CJK = re.compile(r"[一-鿿]")


def tokenize(text: str) -> list[str]:
    """中文 bigram + 拉丁小写整词。中文单字查询退化为包含该字的所有 bigram。"""
    tokens: list[str] = []
    buf: list[str] = []
    for ch in text.lower():
        if _CJK.match(ch):
            buf.append(ch)
        else:
            if buf:
                tokens.extend("".join(buf)[i:i + 2] for i in range(len(buf) - 1))
                if len(buf) == 1:
                    tokens.append(buf[0])
                buf = []
    if buf:
        s = "".join(buf)
        tokens.extend(s[i:i + 2] for i in range(len(s) - 1))
        if len(s) == 1:
            tokens.append(s)
    tokens.extend(_LATIN.findall(text.lower()))
    return tokens


def load_corpus(dirs: list[Path]) -> list[dict]:
    docs: list[dict] = []
    for d in dirs:
        for p in sorted(d.rglob("*.md")):
            if any(part in {"runs", "references", "node_modules", ".git"} for part in p.parts):
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
            title = next((ln.lstrip("# ").strip() for ln in text.splitlines() if ln.startswith("# ")), p.stem)
            docs.append({"path": str(p), "rel": str(p), "title": title, "text": text})
    return docs


def load_index_boost(dirs: list[Path]) -> dict[str, list[str]]:
    """可选：context/index.yaml 的 tags/keywords → 额外 token（加权 = 重复计入 2 次）。"""
    boost: dict[str, list[str]] = {}
    for d in dirs:
        idx = d / "index.yaml"
        if not idx.exists():
            continue
        try:
            data = _load(idx.read_text(encoding="utf-8")) or {}
        except Exception:
            continue
        for rel, meta in (data.get("files") or {}).items():
            if not isinstance(meta, dict):
                continue
            tags = [str(t) for t in (meta.get("tags") or [])]
            kws = [str(k) for k in (meta.get("keywords") or [])]
            if tags or kws:
                boost[str(rel)] = tags + kws
    return boost


def bm25(docs: list[dict], query_tokens: list[str], k1: float = 1.5, b: float = 0.75) -> list[tuple[float, dict, list[str]]]:
    """返回 [(score, doc, 命中token)]，按分值降序。"""
    doc_tokens: list[list[str]] = []
    for doc in docs:
        base = tokenize(doc["title"]) * 2 + tokenize(doc["text"])  # 标题加权
        extra = load_index_boost_for(doc)
        base = base + extra + extra  # index tags/keywords ×2
        doc_tokens.append(base)
    n = len(docs)
    if n == 0:
        return []
    avgdl = sum(len(t) for t in doc_tokens) / n
    df: Counter = Counter()
    for toks in doc_tokens:
        df.update(set(toks))
    results = []
    for doc, toks in zip(docs, doc_tokens):
        tf = Counter(toks)
        score = 0.0
        hits = []
        for qt in set(query_tokens):
            if tf[qt] == 0:
                continue
            idf = math.log(1 + (n - df[qt] + 0.5) / (df[qt] + 0.5))
            score += idf * tf[qt] * (k1 + 1) / (tf[qt] + k1 * (1 - b + b * len(toks) / avgdl))
            hits.append(qt)
        if score > 0:
            results.append((round(score, 3), doc, hits))
    return sorted(results, key=lambda r: -r[0])


# index.yaml 与文档的关联：按文件名匹配（index 记录相对其所在目录的路径，corpus 用绝对路径）
_INDEX_CACHE: dict[str, list[str]] | None = None
_INDEX_DIRS: list[Path] = []


def load_index_boost_for(doc: dict) -> list[str]:
    global _INDEX_CACHE, _INDEX_DIRS
    if _INDEX_CACHE is None:
        _INDEX_CACHE = load_index_boost(_INDEX_DIRS)
    name = Path(doc["path"]).name
    for rel, toks in _INDEX_CACHE.items():
        if Path(rel).name == name:
            return toks
    return []


def build_index(dirs: list[Path]) -> dict:
    """从语料重建 index.yaml 内容：title + tags（h2 标题，最多 6 个）+ keywords（文件名/路径 token）。"""
    files: dict[str, dict] = {}
    for d in dirs:
        for p in sorted(d.rglob("*.md")):
            if p.parent.name == "" or p.name == "index.yaml.md":
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
            title = next((ln.lstrip("# ").strip() for ln in text.splitlines() if ln.startswith("# ")), p.stem)
            tags = [ln.lstrip("# ").strip() for ln in text.splitlines() if ln.startswith("## ")][:6]
            keywords = tokenize(str(p.relative_to(d)) + " " + title)
            files[str(p.relative_to(d))] = {
                "title": title,
                "tags": tags,
                "keywords": sorted({k for k in keywords if _LATIN.fullmatch(k)})[:8],
            }
    return {"generated_at": datetime.datetime.now().isoformat(timespec="seconds"), "files": files}


def main(argv: list[str]) -> int:
    global _INDEX_DIRS
    ap = argparse.ArgumentParser(description="本地语料 BM25 检索（中文 bigram，零依赖）")
    ap.add_argument("query", nargs="?", default="", help="检索词（中文/英文/混合）")
    ap.add_argument("--dirs", action="append", default=None, help="语料目录（可重复；默认 context）")
    ap.add_argument("--top", type=int, default=5, help="返回条数（默认 5）")
    ap.add_argument("--json", action="store_true", help="JSON 输出")
    ap.add_argument("--write-index", action="store_true", help="重建第一个目录的 index.yaml 后退出")
    args = ap.parse_args(argv)

    dirs = [Path(d) for d in (args.dirs or ["context"])]
    missing = [d for d in dirs if not d.is_dir()]
    if missing:
        print(f"FAIL: 语料目录不存在：{', '.join(str(m) for m in missing)}")
        return 2

    if args.write_index:
        data = build_index([dirs[0]])
        out = dirs[0] / "index.yaml"
        out.write_text(_dump(data), encoding="utf-8")
        print(f"已重建: {out}（{len(data['files'])} 文件，tags/keywords 供检索加权）")
        return 0

    if not args.query:
        print("FAIL: 缺少检索词（或使用 --write-index）")
        return 2

    _INDEX_DIRS = dirs
    docs = load_corpus(dirs)
    if not docs:
        print(f"（语料为空：{', '.join(str(d) for d in dirs)} 下无 .md）")
        return 0
    results = bm25(docs, tokenize(args.query))
    top = results[: args.top]
    if not top:
        print(f"（无命中：{args.query}）")
        return 0
    if args.json:
        print(json.dumps([{"score": s, "path": d["path"], "title": d["title"], "hits": h} for s, d, h in top],
                         ensure_ascii=False, indent=1))
        return 0
    for rank, (score, doc, hits) in enumerate(top, 1):
        print(f"{rank}) score={score}  {doc['title']}  [{doc['path']}]")
        snippet = next((ln.strip() for ln in doc["text"].splitlines()
                        if any(t in ln.lower() or t in ln for t in hits)), "")
        if snippet:
            print(f"   {snippet[:120]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
