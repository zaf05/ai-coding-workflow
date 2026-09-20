#!/usr/bin/env python3
"""长周期任务恢复：读取 task.yaml + checkpoint/state/ledger + context/，生成继续执行的提示词。

用法：
  python3 scripts/task_resume.py runs/TASK-20260918-001
  python3 scripts/task_resume.py --list                     # 列出所有活跃任务

退出码：0 成功；2 task.yaml 缺失或结构不可用（恢复链不允许假成功）。
"""
import sys
from pathlib import Path

import yaml


def parse_simple_yaml(path: Path) -> dict:
    """轻量 YAML 解析（不引入外部依赖）。

    支持两级结构：顶层 key → 二级 key；二级 key 下的 `- item` 列表
    归入该二级 key（task.yaml 的 completed_blocks / key_decisions /
    blockers / context_files_written 依赖此行为，否则恢复提示词丢失
    "哪些块已完成"——断点恢复恰恰靠它避免重跑）。
    """
    result: dict = {}
    current_key = None
    last_sub_key = None
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("  ") and current_key:
            stripped = line.strip()
            if stripped.startswith("- "):
                item = stripped[2:].strip().strip("\"'")
                target = last_sub_key if last_sub_key else "_list"
                bucket = result[current_key].setdefault(target, [])
                if isinstance(bucket, list):
                    bucket.append(item)
            elif ":" in stripped:
                k, _, v = stripped.partition(":")
                last_sub_key = k.strip()
                # 空值占位为列表，等待后续 - item 填充；有值保持标量
                result[current_key][last_sub_key] = (
                    v.strip().strip("\"'") if v.strip() else []
                )
        elif ":" in line and not line.startswith(" "):
            k, _, v = line.partition(":")
            current_key = k.strip()
            last_sub_key = None
            result[current_key] = v.strip().strip("\"'") if v.strip() else {}
    return result


def _fmt(value) -> str:
    """列表/空值的人类可读渲染。"""
    if isinstance(value, list):
        return ", ".join(str(x) for x in value) if value else "(none)"
    s = str(value).strip()
    return s if s not in ("", "[]") else "(none)"


def read_checkpoint(path: Path) -> dict:
    """Parse the intentionally small checkpoint format written by run_flow."""
    if not path.exists():
        return {}
    round_no = "unknown"
    timestamp = "unknown"
    blocks: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("# checkpoint round "):
            round_no = line.removeprefix("# checkpoint round ").strip()
        elif line.startswith("timestamp:"):
            timestamp = line.partition(":")[2].strip().strip("\"'")
        elif ":" in line and not line.startswith("#"):
            label, status = line.split(":", 1)
            blocks.append(f"{label.strip()}: {status.strip()}")
    return {"round": round_no, "timestamp": timestamp, "blocks": blocks}


def read_state_snapshot(path: Path) -> dict:
    """Read block status and recent ledger entries when state.yaml exists."""
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {"parse_error": True}
    blocks = []
    for item in data.get("blocks") or []:
        if isinstance(item, dict) and item.get("label"):
            blocks.append(f"{item['label']}: {item.get('status', 'unknown')}")
    ledger = [item for item in data.get("ledger") or [] if isinstance(item, dict)]
    return {"blocks": blocks, "recent_ledger": ledger[-5:]}


def render_dict_item(item: dict) -> str:
    allowed = ("round", "timestamp", "block", "action", "signal", "model", "tokens_used")
    parts = [f"{key}={item.get(key)}" for key in allowed if key in item]
    return " ".join(parts) if parts else str(item)


def find_active_tasks() -> list[Path]:
    root = Path(__file__).parent.parent / "runs"
    tasks = []
    for d in sorted(root.iterdir()):
        if d.is_dir() and (d / "task.yaml").exists():
            tasks.append(d / "task.yaml")
    return tasks


def generate_resume_prompt(task_dir: Path) -> str | None:
    """生成恢复提示词；task.yaml 缺失或无 task/progress 段时返回 None（调用方以非 0 退出）。"""
    task_file = task_dir / "task.yaml"
    if not task_file.exists():
        return None

    data = parse_simple_yaml(task_file)
    task = data.get("task", {})
    progress = data.get("progress", {})
    handoff = data.get("handoff", {})
    if not isinstance(task, dict) or not task:
        return None
    if not isinstance(progress, dict) or not progress:
        return None

    checkpoint = read_checkpoint(task_dir / "checkpoint.yaml")
    state_snapshot = read_state_snapshot(task_dir / "state.yaml")

    # Read context files
    ctx_dir = task_dir.parent.parent / "context"
    ctx_files = []
    if ctx_dir.exists():
        for f in sorted(ctx_dir.glob("*.md")):
            if f.name not in ("README.md",):
                ctx_files.append(f.name)

    lines = [
        "## 继续长周期任务",
        "",
        f"**Task ID**: {task.get('id', task_dir.name)}",
        f"**Title**: {task.get('title', 'N/A')}",
        f"**Phase**: {progress.get('phase', 'unknown')}",
        f"**Progress**: {progress.get('percentage', '0')}%",
        f"**Completed blocks**: {_fmt(progress.get('completed_blocks'))}",
        f"**Current block**: {progress.get('current_block', 'unknown')}",
        f"**Next action**: {progress.get('next_action', 'unknown')}",
        f"**Last session**: {handoff.get('last_session', 'unknown') if isinstance(handoff, dict) else 'unknown'}",
        f"**Notes**: {handoff.get('notes', 'N/A') if isinstance(handoff, dict) else 'N/A'}",
        "",
        "### Checkpoint / State 快照",
        f"- checkpoint.yaml 存在：{'是' if checkpoint else '否'}",
        f"- checkpoint round：{checkpoint.get('round', 'unknown')}",
        f"- checkpoint timestamp：{checkpoint.get('timestamp', 'unknown')}",
        "- checkpoint blocks：" + ("；".join(checkpoint.get("blocks", [])) or "(none)"),
        "- state blocks：" + ("；".join(state_snapshot.get("blocks", [])) or "(none)"),
        "- 最近 ledger：" + ("；".join(render_dict_item(x) for x in state_snapshot.get("recent_ledger", [])) or "(none)"),
        "",
        "### 恢复上下文（按顺序读取）",
        f"1. `runs/{task_dir.name}/task.yaml`（任务状态）",
        f"2. `runs/{task_dir.name}/checkpoint.yaml`（机器快照；存在时必读）",
        f"3. `runs/{task_dir.name}/state.yaml`（块级权威状态；存在时必读）",
    ]
    for i, cf in enumerate(ctx_files, 4):
        lines.append(f"{i}. `context/{cf}`")

    lines += [
        "",
        "### 继续规则",
        "- 从 `current_block` 继续，不要重跑已完成的块",
        "- 已 completed 块的外部副作用（migration/commit/push）零重复执行",
        "- 读取 context/ 恢复项目理解",
        "- 用 `git diff <last_sha>..HEAD` 做增量扫描",
        "- 完成后更新 task.yaml + context/",
    ]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] == "--help":
        print(__doc__)
        return 0

    if argv[1] == "--list":
        tasks = find_active_tasks()
        if not tasks:
            print("No active tasks found.")
            return 0
        print(f"Active tasks ({len(tasks)}):")
        for t in tasks:
            data = parse_simple_yaml(t)
            task = data.get("task", {})
            progress = data.get("progress", {})
            print(f"  {t.parent.name} | {task.get('title', '?')[:40]} | {progress.get('percentage', '?')}% | {progress.get('phase', '?')}")
        return 0

    task_dir = Path(argv[1])
    if not task_dir.is_absolute():
        task_dir = Path(__file__).parent.parent / task_dir

    prompt = generate_resume_prompt(task_dir)
    if prompt is None:
        print(f"ERROR: {task_dir / 'task.yaml'} 不存在或缺少 task/progress 段，无法生成恢复提示词", file=sys.stderr)
        return 2
    print(prompt)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
