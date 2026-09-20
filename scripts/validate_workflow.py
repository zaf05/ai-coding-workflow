#!/usr/bin/env python3
"""校验单条工作流定义（块 DAG）。

用法：python3 validate_workflow.py <file.workflow.yaml>
退出码：0 = 通过；1 = 失败。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml  # type: ignore
    def _load(text):
        return yaml.safe_load(text)
except Exception:
    from _yaml_min import loads as _load

BLOCK_TYPES = {
    # 交付主链
    "intake", "recon", "spec", "decision", "approve", "plan",
    "implement", "check", "review", "test", "verify_ui", "integrate",
    # 收口
    "release_check", "smoke", "notify", "close",
    # 控制流
    "conditional", "for_loop", "while_loop", "wait", "script",
}
ROLES = {"planner", "implementer", "reviewer", "tester", "engine", "user"}
GATES = {"G0", "G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "G10"}
GATE_ROLES = {
    "G0": {"planner"}, "G1": {"planner"}, "G2": {"planner"}, "G10": {"planner"},
    "G3": {"user"}, "G4": {"planner", "tester", "reviewer"},
    "G5": {"reviewer"}, "G8": {"reviewer"},
    "G6": {"planner", "tester"}, "G7": {"tester"}, "G9": {"tester"},
}

# 护栏 ID 注册表。照 Skyvern `AUTHOR_TIME_HARD_BLOCKS` 的 ADR：
# 新增校验器必须在此显式注册，不允许"悄悄变成一堵墙"。
# Errors.add 传入未注册 ID 会直接抛错，因此护栏集合本身是被强制的。
GUARDRAIL_IDS = frozenset({
    "structural",          # 结构 / 类型 / 引用可达性
    "star_bypass",         # 人工边界被模型代签
    "banned_block",        # 职责分离被绕过
    "unbounded_loop",      # 循环或顶层图无界
    "unbounded_retry",     # 重试无上限
    "secret_inline",       # 凭据内联进可提交定义
    "unsafe_command",      # 破坏性且不可回滚的命令
    "evidence_free_gate",  # 门禁未绑定证据
})

# 有界重试硬上限。运行期由 run_flow.py 强制 attempts 不得超过块的 max_attempts；
# 这里是 author-time 上限，防止把 max_attempts 写成天文数字绕过运行期约束。
# 角色层"同一块自愈 ≤2 次，第 3 次 BLOCKED"是更严的行为规则（docs/07）。
MAX_ATTEMPTS_CAP = 5

UNSAFE_COMMAND_PATTERNS = (
    "rm -rf", "rm -fr", "git push --force", "git push -f",
    "git reset --hard", "git clean", "git checkout --",
    "drop table", "chmod 777", "mkfs", ":(){",
)
PIPE_TO_SHELL = re.compile(r"(curl|wget)[^|]*\|\s*(ba)?sh")
CREDENTIAL_LITERAL = re.compile(
    r"(password|passwd|api[_-]?key|secret[_-]?key|access[_-]?token|private[_-]?key)"
    r"\s*[:=]\s*\S|-----BEGIN |AKIA[0-9A-Z]{12,}", re.I)


class Errors:
    def __init__(self):
        self.items = []

    def add(self, msg, guard="structural"):
        if guard not in GUARDRAIL_IDS:
            raise AssertionError(f"未注册的护栏 ID: {guard!r}（必须加入 GUARDRAIL_IDS）")
        self.items.append(f"[{guard}] {msg}")

    def __bool__(self):
        return bool(self.items)

    def render(self):
        return "\n".join(f"  - {m}" for m in self.items)


def collect_blocks(blocks, path="$"):
    """递归收集块，返回 (list[dict], list[str labels])。"""
    out = []
    if not isinstance(blocks, list):
        raise ValueError(f"{path}: blocks 必须是列表")
    for i, b in enumerate(blocks):
        if not isinstance(b, dict):
            raise ValueError(f"{path}[{i}]: 块必须是 map")
        out.append((b, f"{path}[{i}]"))
        for ctrl in ("loop_blocks",):
            if ctrl in b and isinstance(b[ctrl], list):
                out.extend(collect_blocks(b[ctrl], f"{path}[{i}].{ctrl}"))
    return out


def main(path):
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    errors = Errors()
    try:
        data = _load(text)
    except Exception as e:
        print(f"FAIL {path}: YAML 解析失败: {e}")
        return 1

    if not isinstance(data, dict):
        print(f"FAIL {path}: 顶层必须是 map")
        return 1

    # schema_version
    if data.get("schema_version") != 1:
        errors.add("schema_version 必须为 1")

    blocks_raw = data.get("blocks")
    if not isinstance(blocks_raw, list) or not blocks_raw:
        errors.add("blocks 必须是非空列表")

    mapping = data.get("error_code_mapping", {})
    if not isinstance(mapping, dict):
        errors.add("error_code_mapping 必须是 map")

    try:
        all_blocks = collect_blocks(blocks_raw)
    except ValueError as e:
        print(f"FAIL {path}: {e}")
        return 1

    labels = [b.get("label") for b, _ in all_blocks]
    labels_no_none = [l for l in labels if l is not None]
    if len(labels_no_none) != len(set(labels_no_none)):
        errors.add("存在重复的 block label")
    if len(labels_no_none) != len(labels):
        errors.add("每个块必须声明 label")

    label_set = set(labels_no_none)
    for b, bp in all_blocks:
        label = b.get("label")
        btype = b.get("block_type")
        role = b.get("role")
        gate = b.get("gate")
        star = b.get("star", False)
        continue_fail = b.get("continue_on_failure", False)

        if btype not in BLOCK_TYPES:
            errors.add(f"{bp} ({label}): 非法 block_type {btype!r}（未注册块类型）", "banned_block")
        if role not in ROLES:
            errors.add(f"{bp} ({label}): 非法 role {role!r}")
        if gate is not None and gate not in GATES:
            errors.add(f"{bp} ({label}): 非法 gate {gate!r}")

        # star 块禁止 continue_on_failure
        if star and continue_fail:
            errors.add(f"{bp} ({label}): star:true 块禁止 continue_on_failure（人工边界不得被跳过）", "star_bypass")

        # approve 必须 user + star
        if btype == "approve":
            if role != "user":
                errors.add(f"{bp} ({label}): approve 块 role 必须为 user", "star_bypass")
            if not star:
                errors.add(f"{bp} ({label}): approve 块必须 star:true", "star_bypass")

        # review/release_check 必须 reviewer
        if btype in ("review", "release_check") and role != "reviewer":
            errors.add(f"{bp} ({label}): {btype} 块 role 必须为 reviewer（不得自审）", "banned_block")

        # 门禁-角色一致性
        if gate is not None and gate in GATE_ROLES and role not in GATE_ROLES[gate]:
            errors.add(f"{bp} ({label}): gate {gate} 不允许 role {role!r}（职责分离）", "banned_block")

        # 循环必须有 max_iterations
        if btype in ("for_loop", "while_loop"):
            if not isinstance(b.get("max_iterations"), int) or b.get("max_iterations", 0) < 1:
                errors.add(f"{bp} ({label}): {btype} 必须声明正整数 max_iterations", "unbounded_loop")
            if not isinstance(b.get("loop_blocks"), list) or not b.get("loop_blocks"):
                errors.add(f"{bp} ({label}): {btype} 必须声明非空 loop_blocks", "unbounded_loop")

        # conditional 必须恰有一个默认分支
        if btype == "conditional":
            branches = b.get("branch_conditions", [])
            if not isinstance(branches, list) or not branches:
                errors.add(f"{bp} ({label}): conditional 必须声明 branch_conditions")
            else:
                defaults = [x for x in branches if isinstance(x, dict) and x.get("is_default") is True]
                if len(defaults) != 1:
                    errors.add(f"{bp} ({label}): conditional 必须恰有一个 is_default:true 分支")
                for x in branches:
                    if isinstance(x, dict):
                        nb = x.get("next_block_label")
                        if nb is not None and nb not in label_set:
                            errors.add(f"{bp} ({label}): 分支 next_block_label {nb!r} 未定义")

        # next_block_label 引用
        nxt = b.get("next_block_label")
        if nxt is not None and nxt not in label_set:
            errors.add(f"{bp} ({label}): next_block_label {nxt!r} 未定义")

        # error_codes 必须在 mapping 中定义
        for code in b.get("error_codes", []) or []:
            if code not in mapping:
                errors.add(f"{bp} ({label}): error_code {code!r} 未在 error_code_mapping 定义")

        # commands 必须含 cmd
        if btype in ("check", "script"):
            cmds = b.get("commands", [])
            if not isinstance(cmds, list) or not cmds:
                errors.add(f"{bp} ({label}): {btype} 必须声明 commands")
            else:
                for c in cmds:
                    if not isinstance(c, dict) or "cmd" not in c:
                        errors.add(f"{bp} ({label}): 每个 command 必须含 cmd")

        # 护栏 unbounded_retry：max_attempts 必须是 1..MAX_ATTEMPTS_CAP 的整数。
        # 运行期 run_flow.py 已拒绝超过 max_attempts 的重试；这里防止把上限写成天文数字。
        if "max_attempts" in b:
            ma = b.get("max_attempts")
            if isinstance(ma, bool) or not isinstance(ma, int) or ma < 1 or ma > MAX_ATTEMPTS_CAP:
                errors.add(
                    f"{bp} ({label}): max_attempts 必须是 1..{MAX_ATTEMPTS_CAP} 的整数，当前 {ma!r}"
                    f"（重试必须有界，否则失败会无限烧 token）", "unbounded_retry")

        # 护栏 evidence_free_gate：门禁必须绑定证据路径/锚点，否则门禁只是口头声明。
        if gate is not None:
            ev = b.get("evidence")
            if not isinstance(ev, list) or not ev:
                errors.add(
                    f"{bp} ({label}): gate {gate} 必须声明非空 evidence 列表"
                    f"（例如 evidence.md#REVIEW-001）", "evidence_free_gate")

        # 护栏 secret_inline：凭据不得内联进会被提交/复制/渲染进 Prompt 的定义。
        params = b.get("parameters")
        if params is not None and not isinstance(params, list):
            errors.add(f"{bp} ({label}): parameters 必须是列表", "structural")
            params = []
        for pi, prm in enumerate(params or []):
            if not isinstance(prm, dict):
                errors.add(f"{bp} ({label}): parameters[{pi}] 必须是 map", "structural")
                continue
            ptype = str(prm.get("type") or prm.get("parameter_type") or "").lower()
            is_secret = ("secret" in ptype or "credential" in ptype
                         or bool(prm.get("is_secret_or_credential")))
            pname = prm.get("name") or prm.get("key") or f"#{pi}"
            if is_secret:
                for k in ("value", "default", "default_value", "literal"):
                    v = prm.get(k)
                    if v not in (None, ""):
                        errors.add(
                            f"{bp} ({label}): parameters[{pi}] ({pname!r}) 是 secret，"
                            f"禁止内联 {k}；改用参数引用（值不写入定义）", "secret_inline")
            else:
                for k in ("value", "default", "default_value"):
                    v = prm.get(k)
                    if isinstance(v, str) and CREDENTIAL_LITERAL.search(v):
                        errors.add(
                            f"{bp} ({label}): parameters[{pi}] ({pname!r}) 的 {k} 疑似内联凭据；"
                            f"改用 secret 参数引用", "secret_inline")

        # 护栏 unsafe_command：破坏性且不可回滚的命令在 author-time 直接拒绝。
        for ci, c in enumerate(b.get("commands") or []):
            cmd = c.get("cmd") if isinstance(c, dict) else None
            if not isinstance(cmd, str):
                continue
            low = cmd.lower()
            for pat in UNSAFE_COMMAND_PATTERNS:
                if pat in low:
                    errors.add(
                        f"{bp} ({label}): commands[{ci}] 命中禁用模式 {pat!r}"
                        f"（破坏性且不可回滚）", "unsafe_command")
            if PIPE_TO_SHELL.search(low):
                errors.add(
                    f"{bp} ({label}): commands[{ci}] 命中禁用模式 '下载后管道到 shell'",
                    "unsafe_command")
            if CREDENTIAL_LITERAL.search(cmd):
                errors.add(
                    f"{bp} ({label}): commands[{ci}] 疑似内联凭据；改用参数引用并脱敏",
                    "secret_inline")

    # finally 块校验
    finally_label = data.get("finally_block_label")
    if finally_label is not None:
        if finally_label not in label_set:
            errors.add(f"finally_block_label {finally_label!r} 未定义")
        else:
            for b, bp in all_blocks:
                if b.get("label") == finally_label:
                    if b.get("next_block_label") is not None:
                        errors.add(f"finally 块 {finally_label!r} 必须 next_block_label:null")
                    break

    # 顶层 DAG 环检测（控制流子图内部不检测）
    if isinstance(blocks_raw, list):
        top_labels = [b.get("label") for b in blocks_raw if isinstance(b, dict)]
        edges = {}
        for b in blocks_raw:
            if isinstance(b, dict):
                nxt = b.get("next_block_label")
                if nxt is not None and nxt in top_labels:
                    edges[b.get("label")] = nxt
        for start in top_labels:
            seen = set()
            cur = start
            while cur is not None and cur in edges:
                if cur in seen:
                    errors.add(f"顶层 DAG 存在环，包含块 {cur!r}（图必须无界自由，环即拒绝）", "unbounded_loop")
                    break
                seen.add(cur)
                cur = edges[cur]

    if errors:
        print(f"FAIL {path}")
        print(errors.render())
        return 1
    print(f"PASS {path} ({len(all_blocks)} 个块)")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python3 validate_workflow.py <file.workflow.yaml>")
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
