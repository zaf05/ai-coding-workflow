#!/usr/bin/env python3
"""确定性 DAG 解释器（结构推进 + check/script 执行 + 条件分支 + 失败重试 + 账本追加）。

职责边界：
- 读 workflow YAML + run state.yaml，计算 DAG 前沿（frontier）。
- 对 frontier 中 block_type in {check, script} 的块，用 --execute-check 执行 commands，
  输出逐条 exit_code vs expect，但不写 state.yaml（state 唯一写入者是 Planner）。
- 对 star:true 块输出 STAR（请求人工确认），对其它块输出 HANDOFF（交接给角色）。
- 支持条件分支（conditional 块）：根据 state 中的条件值选择分支。
- 支持失败重试：对 max_attempts > 1 的块，记录 attempts 并在失败时允许重试。
- 支持账本追加：--append-ledger 向 state.yaml 追加 ledger 条目（不覆盖已有）。
- 不调用任何 LLM，不写生产代码，不替代 Reviewer/Tester/Planner 的判断。

用法：
  python3 scripts/run_flow.py <workflow.workflow.yaml> <runs/RUN-ID> [选项]

选项：
  --execute-check       真实执行 frontier 中 check/script 块的 commands
  --evaluate-conditional <block_label> <condition_key>
                        评估 conditional 块，输出应走的分支 next_block_label
  --retry <block_label> 将指定块的 attempts +1，状态回退到 pending（不超过 max_attempts）
  --append-ledger <json> 向 state.yaml 的 ledger 列表追加一条记录
  --session-meta <json> 会话归因元数据：{"model":"...","tokens_used":123|null}
                        --advance 自动账本与 --append-ledger 会合并该元数据
  --mark-running <block_label> 将指定块状态设为 running（Planner 用）
  --refreeze-workflow <reason>
                        受控迁移：工作流发生"非结构变更"（如错误码表/注释）且 run 的
                        块集合与角色与新定义完全一致时，把冻结 SHA 迁移到当前定义并
                        记 ledger；结构变更（增删块/改角色）仍拒绝，需新建 run
  --mark-done <block_label> [--status completed|failed|skipped] [--head-sha <sha>]
                        将指定块标记为完成/失败/跳过（Planner 用）。completed 必须通过
                        证据锚点门禁；implement 块还必须绑定候选提交 --head-sha
  --advance             自动推进所有可确定性推进的块（check/script 自动执行，
                        STAR/HANDOFF 只输出不推进），输出完整推进报告

退出码：0 = 没有确定性命令失败；1 = 存在 check/script 命令失败或参数错误。
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

try:
    import yaml  # type: ignore
    def load_yaml_text(text: str):
        return yaml.safe_load(text)
    def dump_yaml(data) -> str:
        return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
except Exception:
    from _yaml_min import loads as _min_loads
    def load_yaml_text(text: str):
        return _min_loads(text)
    def dump_yaml(data) -> str:
        # 内置 fallback 只支持 load，不支持 dump；需要 PyYAML 才能写 state
        raise RuntimeError("写操作需要 PyYAML；请 pip install pyyaml")


RUN_TERMINAL = {"completed", "failed", "canceled", "terminated", "timed_out"}
BLOCK_DONE = {"completed", "skipped"}
CHECK_TYPES = {"check", "script"}
VALID_BLOCK_STATUS = {"pending", "running", "completed", "failed", "terminated", "canceled", "timed_out", "skipped"}
SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")


def load_yaml(path: Path):
    return load_yaml_text(path.read_text(encoding="utf-8"))


def save_yaml(path: Path, data):
    path.write_text(dump_yaml(data), encoding="utf-8")


def collect_top_blocks(blocks):
    out = []
    for b in blocks:
        if not isinstance(b, dict):
            continue
        out.append(b)
    return out


def build_graph(blocks):
    succ = {}
    pred = {}
    conditional_labels = set()
    labels = [b.get("label") for b in blocks if isinstance(b, dict) and b.get("label")]
    for lab in labels:
        succ[lab] = []
        pred.setdefault(lab, [])
    for b in blocks:
        lab = b.get("label")
        if not lab:
            continue
        if b.get("block_type") == "conditional":
            conditional_labels.add(lab)
        # 主路径（next_block_label）
        nxt = b.get("next_block_label")
        if nxt:
            if nxt in labels and nxt not in succ[lab]:
                succ[lab].append(nxt)
            if nxt in labels and lab not in pred[nxt]:
                pred[nxt].append(lab)
        # conditional 分支路径（不计入主 DAG 的 succ/pred，避免误判环）
        if b.get("block_type") == "conditional":
            for br in b.get("branch_conditions") or []:
                if isinstance(br, dict) and br.get("next_block_label"):
                    br_target = br["next_block_label"]
                    if br_target in labels and br_target not in succ[lab]:
                        succ[lab].append(br_target)
                    if br_target in labels and lab not in pred[br_target]:
                        pred[br_target].append(lab)
    return succ, pred, labels, conditional_labels


def load_statuses(run_state, labels):
    status = {lab: "pending" for lab in labels}
    for b in run_state.get("blocks") or []:
        if isinstance(b, dict) and b.get("label") in status:
            status[b.get("label")] = b.get("status") or "pending"
    return status


def find_block_state(run_state, label):
    for b in run_state.get("blocks") or []:
        if isinstance(b, dict) and b.get("label") == label:
            return b
    return None


def find_cycles(succ, labels, conditional_labels=None):
    """检测 DAG 中的环。经过 conditional 块的环不算真环（是有意循环分支）。"""
    conditional_labels = conditional_labels or set()
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {l: WHITE for l in labels}
    cycles = []
    stack = []

    def dfs(u):
        color[u] = GRAY
        stack.append(u)
        for v in succ.get(u, []):
            if color[v] == GRAY:
                # 如果环路径中包含 conditional 块，这是有意的循环分支，不算真环
                i = stack.index(v)
                cycle_path = stack[i:]
                if any(node in conditional_labels for node in cycle_path):
                    continue
                cycles.append(cycle_path + [v])
            elif color[v] == WHITE:
                dfs(v)
        stack.pop()
        color[u] = BLACK

    for l in labels:
        if color[l] == WHITE:
            dfs(l)
    return cycles


def compute_frontier(succ, pred, labels, status):
    ready = []
    for lab in labels:
        if status[lab] not in {"pending", "running"}:
            continue
        if all(status[p] in BLOCK_DONE for p in pred.get(lab, [])):
            ready.append(lab)
    return ready


def execute_commands(commands, repo_root):
    """执行 commands 列表，返回结果列表和是否有失败。"""
    results = []
    failed_any = False
    for c in commands:
        cmd = c.get("cmd")
        workdir = c.get("workdir") or "."
        expect = c.get("expect", 0)
        wd = Path(workdir)
        cwd = wd if wd.is_absolute() else (repo_root / wd)
        cwd = cwd.resolve()
        try:
            proc = subprocess.run(
                cmd, cwd=str(cwd), shell=True,
                capture_output=True, text=True, timeout=600,
            )
            rc = proc.returncode
            ok = (rc == expect)
            results.append({
                "cmd": cmd, "workdir": workdir, "expect": expect,
                "exit_code": rc, "pass": ok,
                "stdout_tail": (proc.stdout or "")[-500:],
                "stderr_tail": (proc.stderr or "")[-500:],
            })
            if not ok:
                failed_any = True
        except Exception as e:
            results.append({
                "cmd": cmd, "workdir": workdir, "expect": expect,
                "exit_code": None, "pass": False, "error": str(e),
            })
            failed_any = True
    return results, failed_any


def cmd_evaluate_conditional(run_state, blocks, label, condition_key):
    """评估 conditional 块，输出应走的分支。"""
    block = next((b for b in blocks if b.get("label") == label), None)
    if not block:
        print(f"FAIL: 块 {label!r} 不存在")
        return 1
    if block.get("block_type") != "conditional":
        print(f"FAIL: 块 {label!r} 不是 conditional 类型")
        return 1

    # 从 state 中读取条件值
    conditions = (run_state.get("conditions") or {})
    value = conditions.get(condition_key)

    branches = block.get("branch_conditions") or []
    default_branch = None
    for br in branches:
        if not isinstance(br, dict):
            continue
        if br.get("is_default"):
            default_branch = br
            continue
        # 匹配条件
        match_key = br.get("condition_key") or condition_key
        match_value = br.get("equals")
        if match_value is not None and str(value) == str(match_value):
            print(json.dumps({
                "label": label,
                "condition_key": condition_key,
                "value": value,
                "matched_branch": br.get("next_block_label"),
                "match_type": "equals",
            }, ensure_ascii=False, indent=2))
            return 0

    # 没有匹配，走默认分支
    if default_branch:
        print(json.dumps({
            "label": label,
            "condition_key": condition_key,
            "value": value,
            "matched_branch": default_branch.get("next_block_label"),
            "match_type": "default",
        }, ensure_ascii=False, indent=2))
        return 0

    print(f"FAIL: conditional 块 {label!r} 无匹配分支且无默认分支")
    return 1


def cmd_retry(run_state_path, run_state, blocks, label):
    """将指定块的 attempts +1，状态回退到 pending。"""
    block_def = next((b for b in blocks if b.get("label") == label), None)
    if not block_def:
        print(f"FAIL: 块 {label!r} 不存在")
        return 1

    max_attempts = block_def.get("max_attempts", 1)
    block_st = find_block_state(run_state, label)
    if not block_st:
        print(f"FAIL: state.yaml 中无块 {label!r}")
        return 1

    current_attempts = block_st.get("attempts", 0)
    current_status = block_st.get("status", "pending")

    if current_status not in ("failed", "running", "pending"):
        print(f"FAIL: 块 {label!r} 当前状态 {current_status!r}，只有 failed/running/pending 可重试")
        return 1

    if current_attempts >= max_attempts:
        print(f"FAIL: 块 {label!r} 已达最大尝试次数 {max_attempts}，不可重试")
        return 1

    # 执行重试
    block_st["attempts"] = current_attempts + 1
    block_st["status"] = "pending"
    save_yaml(run_state_path, run_state)

    print(json.dumps({
        "label": label,
        "action": "retry",
        "previous_attempts": current_attempts,
        "new_attempts": current_attempts + 1,
        "max_attempts": max_attempts,
        "new_status": "pending",
    }, ensure_ascii=False, indent=2))
    return 0


def normalize_session_meta(value):
    """Validate deterministic session attribution metadata.

    ``model`` is mandatory because host/model changes materially affect instruction
    following. ``tokens_used`` is best-effort and may be null when the host does not
    expose a stable programmatic usage counter.
    """
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("--session-meta must be a JSON object")
    model = value.get("model")
    if not isinstance(model, str) or not model.strip():
        raise ValueError("--session-meta.model must be a non-empty string")
    tokens = value.get("tokens_used", None)
    if tokens is not None and (not isinstance(tokens, int) or isinstance(tokens, bool) or tokens < 0):
        raise ValueError("--session-meta.tokens_used must be a non-negative integer or null")
    result = {"model": model.strip()}
    if "tokens_used" in value:
        result["tokens_used"] = tokens
    for key in ("host", "session_id"):
        if key in value and value[key] is not None:
            item = value[key]
            if not isinstance(item, str) or not item.strip():
                raise ValueError(f"--session-meta.{key} must be a non-empty string or absent")
            result[key] = item.strip()
    return result


def cmd_append_ledger(run_state_path, run_state, ledger_entry_json, session_meta=None):
    """向 state.yaml 的 ledger 追加一条记录。"""
    try:
        entry = json.loads(ledger_entry_json)
    except json.JSONDecodeError as e:
        print(f"FAIL: ledger 条目 JSON 解析失败: {e}")
        return 1

    if not isinstance(entry, dict):
        print("FAIL: ledger 条目必须是 JSON object")
        return 1

    ledger = run_state.get("ledger") or []
    entry["appended_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    entry.update(session_meta or {})
    ledger.append(entry)
    run_state["ledger"] = ledger
    save_yaml(run_state_path, run_state)

    print(json.dumps({
        "action": "append_ledger",
        "entry_index": len(ledger) - 1,
        "entry": entry,
    }, ensure_ascii=False, indent=2))
    return 0



def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _anchor_exists(content: str, anchor: str) -> bool:
    escaped = re.escape(anchor)
    h2 = re.search(rf'^##\s+{escaped}(?:\s|$|\(|·)', content, re.MULTILINE)
    yid = re.search(rf'^id:\s+{escaped}\s*$', content, re.MULTILINE)
    return bool(h2 or yid)


def verify_block_evidence(block_def, run_dir):
    """completed 门禁：块声明的 evidence 引用必须真实可达（文件 + 锚点）。

    与 validate_run._verify_evidence_refs 同语义：锚点支持 `## Anchor` 标题与
    `id: Anchor` 两种约定。引擎侧不 import 校验器，避免共享全局 errors 状态。
    """
    problems = []
    refs = block_def.get("evidence") or []
    if isinstance(refs, str):
        refs = [refs]
    for ref in refs:
        if not isinstance(ref, str) or not ref.strip():
            continue
        part = ref.strip()
        m = re.match(r'^(?P<file>[^#]+)#(?P<anchor>.+)$', part)
        if not m:
            problems.append(f"证据引用缺少 #anchor: {part}")
            continue
        ref_file = m.group('file')
        anchor = m.group('anchor').strip()
        resolved = run_dir / ref_file
        if not resolved.exists():
            alt = ROOT / ref_file
            if alt.exists():
                resolved = alt
            else:
                problems.append(f"证据文件不存在: {part}")
                continue
        try:
            content = resolved.read_text(encoding='utf-8', errors='replace')
        except Exception:
            problems.append(f"证据文件不可读: {part}")
            continue
        if not _anchor_exists(content, anchor):
            problems.append(f"证据锚点不存在: {part}")
    return problems


def cmd_mark_status(run_state_path, run_state, blocks, label, new_status, run_dir, head_sha=None):
    """将指定块标记为指定状态（completed 必须过证据门禁与 implement head_sha 门禁）。"""
    if new_status not in VALID_BLOCK_STATUS:
        print(f"FAIL: 非法状态 {new_status!r}，合法值: {sorted(VALID_BLOCK_STATUS)}")
        return 1

    block_st = find_block_state(run_state, label)
    if not block_st:
        print(f"FAIL: state.yaml 中无块 {label!r}")
        return 1

    block_def = next((b for b in blocks if b.get("label") == label), None)
    btype = (block_def or {}).get("block_type")

    if new_status == "completed":
        # check/script 块的 completed 只能由 --advance --execute-check 按命令
        # 退出码自动产生；人工 mark-done 会绕过命令执行，一律拒绝。
        if btype in CHECK_TYPES:
            print(f"FAIL: [AIW_EVIDENCE_MISSING] 块 {label!r} 是 {btype} 块，"
                  f"必须用 --advance --execute-check 按命令退出码完成，不得人工标记 completed")
            return 1
        problems = verify_block_evidence(block_def or {}, run_dir)
        if problems:
            print(f"FAIL: [AIW_EVIDENCE_MISSING] 块 {label!r} completed 证据门禁未通过：")
            for q in problems:
                print(f"  - {q}")
            return 1
        if btype == "implement":
            effective_head = str(head_sha or block_st.get("head_sha") or "").strip()
            if not effective_head:
                print(f"FAIL: [AIW_HEAD_SHA_MISSING] implement 块 {label!r} completed 必须绑定"
                      f"候选提交 head_sha（--head-sha <sha>）")
                return 1
            if not SHA_RE.match(effective_head):
                print(f"FAIL: [AIW_HEAD_SHA_MISSING] 块 {label!r} head_sha 格式非法: {effective_head!r}")
                return 1
            if head_sha:
                block_st["head_sha"] = str(head_sha).strip()

    old_status = block_st.get("status", "pending")
    block_st["status"] = new_status
    block_st["attempts"] = int(block_st.get("attempts") or 0) + 1
    run_cfg = run_state.get("run")
    if isinstance(run_cfg, dict):
        run_cfg["current_block_label"] = label
    save_yaml(run_state_path, run_state)

    print(json.dumps({
        "label": label,
        "action": "mark_status",
        "old_status": old_status,
        "new_status": new_status,
        "attempts": block_st.get("attempts"),
        "evidence_gate": ("passed" if new_status == "completed" and btype not in CHECK_TYPES
                          else "not_applicable"),
        "head_sha": block_st.get("head_sha"),
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_refreeze_workflow(run_state_path, run_state, blocks, labels, reason,
                          frozen, wf_digest):
    """受控迁移冻结 SHA：仅当 state 块集合/角色与新定义完全一致（非结构变更）。

    双宿主场景（Codex 升级工作流定义不能锁死 Claude Code 正在跑的 run）：
    定义演进后，活跃 run 可凭结构兼容校验迁移到新 SHA 并留 ledger 凭据；
    增删块/改角色属于结构变更，仍走 Change Log + 新建 run。
    """
    reason = (reason or "").strip()
    if not reason:
        print("FAIL: --refreeze-workflow 必须提供非空迁移原因（将写入 ledger）")
        return 1

    run_cfg = run_state.get("run")
    if not isinstance(run_cfg, dict):
        print("FAIL: state.yaml.run 必须是 map")
        return 1
    if run_cfg.get("status") in RUN_TERMINAL:
        print(f"FAIL: [AIW_WORKFLOW_DRIFT] 终态 run 不得 refreeze（status="
              f"{run_cfg.get('status')!r}，历史不改写）")
        return 1

    if frozen == wf_digest:
        print(json.dumps({
            "action": "workflow_refreeze",
            "result": "noop",
            "reason": "冻结 SHA 已与当前定义一致，无需迁移",
            "workflow_sha256": wf_digest,
        }, ensure_ascii=False, indent=2))
        return 0

    # 结构兼容校验：state 块标签（含顺序）与角色必须与新定义逐项一致。
    state_blocks = [b for b in run_state.get("blocks") or [] if isinstance(b, dict)]
    state_labels = [b.get("label") for b in state_blocks if b.get("label")]
    state_roles = {b.get("label"): b.get("role") for b in state_blocks}
    def_roles = {b.get("label"): b.get("role") for b in blocks if isinstance(b, dict)}
    problems = []
    if state_labels != labels:
        extra = [x for x in state_labels if x not in labels]
        missing = [x for x in labels if x not in state_labels]
        problems.append(f"块集合不一致（state 多出 {extra}，定义缺失 {missing}，或顺序不同）")
    for lab in labels:
        if state_roles.get(lab) != def_roles.get(lab):
            problems.append(f"块 {lab!r} 角色不一致：state={state_roles.get(lab)!r} "
                            f"定义={def_roles.get(lab)!r}")
    if problems:
        print("FAIL: [AIW_WORKFLOW_DRIFT] 工作流发生结构变更，refreeze 拒绝（需 Change Log + 新建 run）：")
        for q in problems:
            print(f"  - {q}")
        return 1

    run_cfg["workflow_sha256"] = wf_digest
    ledger = run_state.setdefault("ledger", [])
    ledger.append({
        "action": "workflow_refreeze",
        "from_sha256": frozen,
        "to_sha256": wf_digest,
        "reason": reason,
        "structural_check": "labels+roles identical",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    })
    save_yaml(run_state_path, run_state)
    print(json.dumps({
        "action": "workflow_refreeze",
        "result": "migrated",
        "from_sha256": frozen,
        "to_sha256": wf_digest,
        "reason": reason,
        "structural_check": "labels+roles identical",
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_advance(wf, run_state, run_state_path, blocks, succ, pred, labels, conditional_labels, repo_root, execute, session_meta=None):
    """自动推进所有可确定性推进的块，输出完整报告。

    每次调用至少推进一轮；报告中的 loop_control 字段告诉 Agent 接下来该做什么：
      CONTINUE  → 本脚本可继续推进（check 通过），Agent 应再次调用 --advance
      DONE      → 没有更多可推进的块，Agent 应判定 completion_contract 或交 Planner close
      WAIT_USER → 遇到 star:true 块，Agent 必须停下请求用户确认，不得代签
      WAIT_ROLE → 遇到需要角色处理的块，Agent 应调用对应 Skill 完成工作，然后 mark-done 再 --advance
      BLOCKED   → 遇到结构性障碍（环/check 失败/重试耗尽），Agent 应停止并归因
    """
    status = load_statuses(run_state, labels)
    run_status = (run_state.get("run") or {}).get("status")

    # 初始化 ledger（若模板未预置）
    if "ledger" not in run_state:
        run_state["ledger"] = []

    # 推进信号：初始 CONTINUE；每个出口点设置最终信号。
    loop_control = "CONTINUE"
    def _set_lc(s: str):
        nonlocal loop_control
        if loop_control == "CONTINUE":
            loop_control = s

    report = {
        "run_id": (run_state.get("run") or {}).get("id"),
        "run_status": run_status,
        "actions": [],
        "cycles": [],
        "session_meta": session_meta or {},
    }

    if run_status in RUN_TERMINAL:
        report["actions"].append({
            "action": "TERMINAL",
            "reason": f"run 已终结（{run_status}），无待执行块",
        })
        _set_lc("DONE")
        # 统一契约：所有 --advance 报告（含终结/环两条提前返回路径）都带 loop_control，
        # 消费方（Codex/Claude Code 会话）按 loop_control 解析不再 KeyError。
        report["loop_control"] = loop_control
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    cycles = find_cycles(succ, labels, conditional_labels)
    if cycles:
        report["cycles"] = cycles
        report["actions"].append({
            "action": "CYCLE_DETECTED",
            "cycle": cycles[0],
        })
        _set_lc("BLOCKED")
        report["loop_control"] = loop_control
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1

    failed_any = False

    def _append_round_ledger(round_num, lab, action_type, signal, extra=None):
        """每轮结束后自动向 state.yaml 追加一条轮次日志。"""
        import datetime
        entry = {
            "round": round_num,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "block": lab,
            "action": action_type,
            "signal": signal,
        }
        if extra:
            entry.update(extra)
        entry.update(session_meta or {})
        run_state.setdefault("ledger", []).append(entry)
        try:
            save_yaml(run_state_path, run_state)
        except Exception as exc:
            # 失败必须有名字：轮次日志写失败不阻断推进，但必须在 stderr 可见，
            # 不允许静默吞掉（否则 ledger 可能悄悄缺行且无告警）。
            print(f"WARN: 轮次日志写入失败（不阻断推进）: {exc}", file=sys.stderr)

        # Checkpoint: every N rounds
        checkpoint_interval = int(loop_cfg.get("checkpoint_interval", 10))
        if checkpoint_interval > 0 and (round_num + 1) % checkpoint_interval == 0:
            cp_path = run_state_path.parent / "checkpoint.yaml"
            cp_lines = [f"# checkpoint round {round_num + 1}", f"timestamp: {__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()}"]
            # state.yaml 的 blocks 是列表形式（每项含 label/status）。
            # 历史 bug（v1.8.5 修复）：曾按 dict.items() 遍历，interval 一触发即
            # AttributeError 崩溃——该代码路径此前从未被任何测试执行过。
            for b in run_state.get("blocks") or []:
                if isinstance(b, dict) and b.get("label"):
                    cp_lines.append(f"{b['label']}: {b.get('status', 'unknown')}")
            cp_path.write_text("\n".join(cp_lines) + "\n", encoding="utf-8")
            print(f"CHECKPOINT: round {round_num + 1} -> checkpoint.yaml")

    # 多轮推进：每轮处理一个 frontier 块，直到没有可推进的
    loop_cfg = wf.get("loop_control") or {}
    configured_max = loop_cfg.get("max_rounds")
    if configured_max is not None:
        max_rounds = min(int(configured_max), 200)
    else:
        max_rounds = len(labels) + 5  # 安全上限
    for round_num in range(max_rounds):
        status = load_statuses(run_state, labels)
        ready = compute_frontier(succ, pred, labels, status)
        if not ready:
            _set_lc("DONE")
            break

        lab = ready[0]  # 每次只处理第一个就绪块
        block = next((b for b in blocks if b.get("label") == lab), {})
        btype = block.get("block_type")
        star = bool(block.get("star", False))
        role = block.get("role")

        if star:
            action = {
                "round": round_num + 1,
                "label": lab,
                "action": "STAR",
                "reason": "star:true 人工确认/授权边界，不得代签",
                "role": role,
                "gate": block.get("gate"),
            }
            report["actions"].append(action)
            _append_round_ledger(round_num + 1, lab, "STAR", "WAIT_USER", {"gate": block.get("gate")})
            _set_lc("WAIT_USER")
            break  # STAR 阻断后续推进

        elif btype in CHECK_TYPES:
            action = {
                "round": round_num + 1,
                "label": lab,
                "action": "CHECK",
                "block_type": btype,
                "role": role,
                "commands": block.get("commands") or [],
            }
            if execute:
                results, failed = execute_commands(block.get("commands") or [], repo_root)
                action["results"] = results
                if failed:
                    failed_any = True
                    # 检查是否可重试
                    max_att = block.get("max_attempts", 1)
                    block_st = find_block_state(run_state, lab)
                    att = (block_st.get("attempts") if block_st else 0) or 0
                    if att < max_att:
                        action["retry_available"] = True
                        action["remaining_attempts"] = max_att - att
                        _set_lc("BLOCKED")
                    else:
                        _set_lc("BLOCKED")
                    report["actions"].append(action)
                    _append_round_ledger(round_num + 1, lab, "CHECK", "BLOCKED", {"failed": failed})
                    break  # 失败阻断后续
                else:
                    # check 通过，自动标记 completed，继续推进下一轮
                    report["actions"].append(action)
                    # check 通过，自动标记为 completed（如果 state 中有此块）
                    block_st = find_block_state(run_state, lab)
                    if block_st:
                        block_st["status"] = "completed"
                        save_yaml(run_state_path, run_state)
                        action["auto_marked"] = "completed"
                    _append_round_ledger(round_num + 1, lab, "CHECK", "CONTINUE", {"passed": True})
                    # 不阻断，不设 loop_control，继续下一轮
            else:
                # 不执行 check 命令时，输出 HANDOFF 语义让 Agent 接力
                action["action"] = "HANDOFF"
                action["note"] = "CHECK 块需要 --execute-check 执行；当前未执行"
                report["actions"].append(action)
                _append_round_ledger(round_num + 1, lab, "HANDOFF", "WAIT_ROLE", {"note": "check未执行"})
                _set_lc("WAIT_ROLE")
                break  # 不执行时停在 check

        else:
            action = {
                "round": round_num + 1,
                "label": lab,
                "action": "HANDOFF",
                "role": role,
                "block_type": btype,
                "gate": block.get("gate"),
                "goal": block.get("goal"),
                "complete_criterion": block.get("complete_criterion"),
            }
            report["actions"].append(action)
            _append_round_ledger(round_num + 1, lab, "HANDOFF", "WAIT_ROLE", {"gate": block.get("gate")})
            _set_lc("WAIT_ROLE")
            break  # HANDOFF 需要角色会话处理，阻断后续

    # 最终状态
    status = load_statuses(run_state, labels)
    remaining = [l for l in labels if status[l] not in BLOCK_DONE]
    report["remaining_blocks"] = remaining
    report["total_rounds"] = round_num + 1
    report["loop_control"] = loop_control

    # DONE 时追加最终轮次日志
    if loop_control == "DONE":
        import datetime
        done_entry = {"round": "final", "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                      "action": "DONE", "signal": "DONE", "remaining_blocks": remaining}
        done_entry.update(session_meta or {})
        run_state.setdefault("ledger", []).append(done_entry)
        # 引擎收尾（v1.8.12）：全部块 terminal 时由引擎写入 run 终态与 finally 指针，
        # 消灭"手改 state.yaml 把 running 改成 completed"的旁路。仍有未决块时
        # （frontier 空但存在 failed/pending）不代写终态，交 Planner 归因。
        if not remaining:
            fin = wf.get("finally_block_label")
            run_cfg = run_state.get("run")
            if isinstance(run_cfg, dict) and run_cfg.get("status") not in RUN_TERMINAL:
                run_cfg["status"] = "completed"
                if fin:
                    run_cfg["current_block_label"] = fin
        save_yaml(run_state_path, run_state)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if failed_any else 0

def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2

    wf_path = Path(argv[1])
    run_dir = Path(argv[2])
    rest = argv[3:]

    execute = "--execute-check" in rest
    append_ledger_json = None
    session_meta_json = None
    evaluate_conditional = None
    retry_label = None
    mark_running = None
    mark_done = None
    mark_done_status = "completed"
    mark_done_head_sha = None
    refreeze_reason = None
    advance = False

    i = 0
    while i < len(rest):
        arg = rest[i]
        if arg == "--append-ledger" and i + 1 < len(rest):
            append_ledger_json = rest[i + 1]
            i += 2
        elif arg == "--session-meta" and i + 1 < len(rest):
            session_meta_json = rest[i + 1]
            i += 2
        elif arg == "--evaluate-conditional" and i + 2 < len(rest):
            evaluate_conditional = (rest[i + 1], rest[i + 2])
            i += 3
        elif arg == "--retry" and i + 1 < len(rest):
            retry_label = rest[i + 1]
            i += 2
        elif arg == "--mark-running" and i + 1 < len(rest):
            mark_running = rest[i + 1]
            i += 2
        elif arg == "--mark-done" and i + 1 < len(rest):
            mark_done = rest[i + 1]
            i += 2
            if i < len(rest) and rest[i] == "--status" and i + 1 < len(rest):
                mark_done_status = rest[i + 1]
                i += 2
            if i < len(rest) and rest[i] == "--head-sha" and i + 1 < len(rest):
                mark_done_head_sha = rest[i + 1]
                i += 2
        elif arg == "--refreeze-workflow" and i + 1 < len(rest):
            refreeze_reason = rest[i + 1]
            i += 2
        elif arg == "--advance":
            advance = True
            i += 1
        else:
            i += 1

    if not wf_path.exists():
        print(f"FAIL: 工作流不存在: {wf_path}")
        return 1
    if not run_dir.is_dir() or not (run_dir / "state.yaml").exists():
        print(f"FAIL: run 目录或 state.yaml 不存在: {run_dir}")
        return 1

    wf = load_yaml(wf_path)
    run_state = load_yaml(run_dir / "state.yaml")
    run_state_path = run_dir / "state.yaml"

    session_meta = None
    if session_meta_json is not None:
        try:
            raw_session_meta = json.loads(session_meta_json)
        except json.JSONDecodeError as exc:
            print(f"FAIL: --session-meta 不是合法 JSON: {exc}")
            return 1
        try:
            session_meta = normalize_session_meta(raw_session_meta)
        except ValueError as exc:
            print(f"FAIL: {exc}")
            return 1

    # 命令工作目录解析
    repo_root = ROOT.parent
    repo_cfg = run_state.get("repository") or {}
    if repo_cfg.get("root"):
        rp = Path(str(repo_cfg["root"]))
        repo_root = rp if rp.is_absolute() else (ROOT.parent / rp)
    repo_root = repo_root.resolve()

    if not isinstance(wf, dict) or not isinstance(wf.get("blocks"), list):
        print("FAIL: 工作流格式错误")
        return 1
    if not isinstance(run_state, dict):
        print("FAIL: state.yaml 格式错误")
        return 1

    # 护栏 workflow_freeze（v1.8.12）：run 首次被引擎触碰时冻结 DAG 定义 SHA256；
    # 之后定义被修改（运行中改图）则拒绝一切推进/写入——state 必须能回答
    # "按哪个版本的工作流流转"。历史终态 run 不回写、不拦截（validate_run 仅 WARN）。
    run_cfg = run_state.get("run")
    if not isinstance(run_cfg, dict):
        run_cfg = {}
        run_state["run"] = run_cfg
    wf_digest = file_sha256(wf_path)
    if run_cfg.get("status") not in RUN_TERMINAL:
        frozen = str(run_cfg.get("workflow_sha256") or "").strip()
        if not frozen:
            run_cfg["workflow_sha256"] = wf_digest
            save_yaml(run_state_path, run_state)
        elif frozen != wf_digest and refreeze_reason is None:
            print(f"FAIL: [AIW_WORKFLOW_DRIFT] 工作流定义在运行中被修改："
                  f"state 冻结 {frozen[:12]}…，当前 {wf_digest[:12]}…（{wf_path}）")
            print("      处置：恢复定义原文；非结构变更可用 --refreeze-workflow <reason> 受控迁移；"
                  "结构变更需 Change Log + 新建 run 并终结旧 run")
            return 1

    blocks = collect_top_blocks(wf["blocks"])
    succ, pred, labels, conditional_labels = build_graph(blocks)

    # 子命令分发
    if evaluate_conditional:
        label, cond_key = evaluate_conditional
        return cmd_evaluate_conditional(run_state, blocks, label, cond_key)

    if retry_label:
        return cmd_retry(run_state_path, run_state, blocks, retry_label)

    if append_ledger_json:
        return cmd_append_ledger(run_state_path, run_state, append_ledger_json, session_meta)

    if refreeze_reason is not None:
        frozen_now = str(run_state.get("run", {}).get("workflow_sha256") or "").strip()
        return cmd_refreeze_workflow(run_state_path, run_state, blocks, labels,
                                     refreeze_reason, frozen_now, wf_digest)

    if mark_running:
        return cmd_mark_status(run_state_path, run_state, blocks, mark_running, "running", run_dir)

    if mark_done:
        return cmd_mark_status(run_state_path, run_state, blocks, mark_done, mark_done_status,
                                run_dir, mark_done_head_sha)

    if advance:
        cycles = find_cycles(succ, labels, conditional_labels)
        if cycles:
            print(f"FAIL: DAG 存在环: {cycles[0]}")
            return 1
        return cmd_advance(wf, run_state, run_state_path, blocks, succ, pred, labels, conditional_labels, repo_root, execute, session_meta)

    # 默认行为：输出 frontier 报告（向后兼容）
    cycles = find_cycles(succ, labels, conditional_labels)
    if cycles:
        print(f"FAIL: DAG 存在环: {cycles[0]}")
        return 1

    status = load_statuses(run_state, labels)
    run_status = (run_state.get("run") or {}).get("status")

    report = {
        "run_id": (run_state.get("run") or {}).get("id"),
        "run_status": run_status,
        "frontier": [],
        "cycles": cycles,
    }

    if run_status in RUN_TERMINAL:
        print(f"RUN {run_status} 已终结；无待执行块。")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    ready = compute_frontier(succ, pred, labels, status)
    failed_any = False

    for lab in ready:
        block = next((b for b in blocks if b.get("label") == lab), {})
        btype = block.get("block_type")
        star = bool(block.get("star", False))
        role = block.get("role")

        if star:
            action = {
                "label": lab,
                "action": "STAR",
                "reason": "star:true 人工确认/授权边界，不得代签",
                "role": role,
                "gate": block.get("gate"),
            }
        elif btype in CHECK_TYPES:
            action = {
                "label": lab,
                "action": "CHECK",
                "block_type": btype,
                "role": role,
                "commands": block.get("commands") or [],
            }
            if execute:
                results, failed = execute_commands(block.get("commands") or [], repo_root)
                action["results"] = results
                if failed:
                    failed_any = True
        else:
            action = {
                "label": lab,
                "action": "HANDOFF",
                "role": role,
                "block_type": btype,
                "gate": block.get("gate"),
                "goal": block.get("goal"),
                "complete_criterion": block.get("complete_criterion"),
            }

        report["frontier"].append(action)

    # 默认路径：根据 frontier 动作计算 loop_control
    if not ready:
        lc = "DONE"
    elif any(a.get("action") == "STAR" for a in report["frontier"]):
        lc = "WAIT_USER"
    elif any(a.get("action") in ("HANDOFF", "CHECK") for a in report["frontier"]):
        lc = "WAIT_ROLE"
    else:
        lc = "CONTINUE"
    report["loop_control"] = lc
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if failed_any else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
