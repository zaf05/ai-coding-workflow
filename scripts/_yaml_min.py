"""极简 YAML 子集解析器：覆盖本仓库工作流定义。零第三方依赖。

支持：嵌套 map、`- item` 序列、`- key: value` 序列项为 map、行内 flow map/seq
（`{a: 1, b: "x"}`、`[a, b]`）、标量 string/int/float/bool/null、注释、空行。
不支持：锚点/别名、多行字符串 `|`/`>`、复杂引号内转义以外的语法。
优先使用 PyYAML（若可用），本模块仅作 fallback。
"""
from __future__ import annotations

import ast
import re

_TRUE = {"true", "True", "TRUE"}
_FALSE = {"false", "False", "FALSE"}
_NULL = {"null", "None", "none", "~", ""}
_INT_RE = re.compile(r"^[-+]?\d+$")
_FLOAT_RE = re.compile(r"^[-+]?(\d+\.\d*|\.\d+|\d+[eE][-+]?\d+)$")


def loads(text: str):
    lines = []
    for raw in text.splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        if "\t" in raw[:indent]:
            raise ValueError("YAML 缩进不能使用 Tab")
        lines.append((indent, s))
    value, idx = _parse_value(lines, 0, -1)
    if idx < len(lines):
        raise ValueError(f"多余内容：第 {idx + 1} 行附近 {lines[idx][1]!r}")
    return value


def _parse_value(lines, i, min_indent):
    if i >= len(lines):
        return None, i
    indent, content = lines[i]
    if indent < min_indent:
        return None, i
    if content.startswith("- "):
        return _parse_seq(lines, i, indent)
    return _parse_map(lines, i, indent)


def _parse_seq(lines, i, indent):
    result = []
    while i < len(lines):
        ind, content = lines[i]
        if ind < indent:
            break
        if ind > indent:
            raise ValueError(f"缩进错误：{content!r}")
        if not content.startswith("- "):
            raise ValueError(f"期望序列项：{content!r}")
        rest = content[2:].strip()
        if rest == "":
            # 嵌套块
            if i + 1 < len(lines) and lines[i + 1][0] > indent:
                i += 1
                val, i = _parse_value(lines, i, indent + 2)
            else:
                val = None
                i += 1
            result.append(val)
        elif rest.startswith("- "):
            result.append(_parse_scalar(rest))
            i += 1
        elif _looks_like_map_item(rest):
            # `- key: value`：把它当作 map 首项，后续更深缩进行属于同一 map
            val, i = _parse_seq_map(lines, i, indent, rest)
            result.append(val)
        else:
            result.append(_parse_scalar(rest))
            i += 1
    return result, i


def _looks_like_map_item(s: str):
    if s.startswith(("{", "[")):
        return False
    return ":" in s


def _parse_seq_map(lines, i, indent, first_content):
    """解析 `- key: value` 开始的 map 项。"""
    result = {}
    key, val = _split_kv(first_content)
    result[key] = _parse_scalar(val)

    # 后续更深缩进的行属于此 map
    j = i + 1
    while j < len(lines):
        ind, content = lines[j]
        if ind <= indent:
            break
        if content.startswith("- "):
            break
        expected_indent = indent + 2
        if ind != expected_indent:
            # 允许更深嵌套，交给 _parse_map 处理
            pass
        sub, j = _parse_map(lines, j, indent + 2)
        result.update(sub)
    return result, j


def _parse_map(lines, i, indent):
    result = {}
    while i < len(lines):
        ind, content = lines[i]
        if ind < indent:
            break
        if ind > indent:
            raise ValueError(f"缩进错误：{content!r}")
        if content.startswith("- "):
            break
        key, val = _split_kv(content)
        if val == "":
            # 嵌套值
            if i + 1 < len(lines) and lines[i + 1][0] > indent:
                i += 1
                child_indent = lines[i][0]
                val, i = _parse_value(lines, i, child_indent)
            else:
                val = None
                i += 1
        else:
            val = _parse_scalar(val)
            i += 1
        result[key] = val
    return result, i


def _split_kv(s: str):
    if ":" not in s:
        raise ValueError(f"期望 key: value：{s!r}")
    key, val = s.split(":", 1)
    return key.strip(), val.strip()


def _parse_scalar(s: str):
    s = s.strip()
    if s == "":
        return None
    if s in _TRUE:
        return True
    if s in _FALSE:
        return False
    if s in _NULL:
        return None
    if s.startswith("{"):
        return _parse_flow_map(s)
    if s.startswith("["):
        return _parse_flow_seq(s)
    if _INT_RE.match(s):
        return int(s)
    if _FLOAT_RE.match(s):
        return float(s)
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return _unquote(s)
    return s


def _unquote(s: str):
    quote = s[0]
    body = s[1:-1]
    if quote == '"':
        try:
            return ast.literal_eval(s)
        except Exception:
            return body
    return body.replace("''", "'")


def _split_flow(s: str):
    """把 flow map/seq 内容按顶层逗号拆分，尊重引号与嵌套括号。"""
    parts = []
    depth = 0
    buf = []
    quote = None
    for ch in s:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
            buf.append(ch)
            continue
        if ch in "{[":
            depth += 1
        elif ch in "}]":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append("".join(buf).strip())
            buf = []
            continue
        buf.append(ch)
    if buf:
        parts.append("".join(buf).strip())
    return [p for p in parts if p]


def _parse_flow_map(s: str):
    inner = s[1:-1].strip()
    result = {}
    for part in _split_flow(inner):
        key, val = _split_kv(part)
        result[key] = _parse_scalar(val)
    return result


def _parse_flow_seq(s: str):
    inner = s[1:-1].strip()
    if not inner:
        return []
    return [_parse_scalar(p) for p in _split_flow(inner)]
