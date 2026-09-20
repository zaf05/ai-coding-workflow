#!/usr/bin/env python3
"""把 author-time 护栏下沉到运行期：安装可复核的 Git pre-commit 闸门。

解决的问题（两篇参考文章共同指出的唯一生产级缺口）：
  「规范存在 ≠ 行为有效」——护栏若只写在文档里、只靠人手动敲 selftest，
  那么改坏工作流的那次提交不会遇到任何阻力。本脚本把 `scripts/hooks/pre-commit`
  （hook 本体版本化在仓库里）安装到 `.git/hooks/pre-commit`，并让安装状态本身
  可被 `--check` 逐字节复核。

为什么需要安装器而不是直接把 hook 放进仓库根：
  `.git/hooks/` 不入版本库。所以「hook 存在」这件事必须是可验证事实，
  不能靠假设——这正是 install_skills.py 收据机制的同一套思路。

安全边界（不变）：
  * 默认 dry-run，不写盘；
  * 不覆盖不是本脚本安装的 hook：发现外来 hook 先备份为
    `pre-commit.foreign-backup-<ts>` 再安装，绝不静默吃掉别人的逻辑；
  * 写入用临时文件 + os.replace 原子替换；
  * `--uninstall` 只删自己装的（按标记 + SHA 双重确认），并尝试恢复最近备份。

已知边界（诚实声明，不假装闭环）：
  `git commit --no-verify` 可以绕过任何 pre-commit hook。这是 Git 的既有设计，
  本脚本不声称能阻止；因此 docs/13-roadmap 把「CI 侧再挂一次」列为下一层。

用法：
  python3 scripts/install_hooks.py --dry-run
  python3 scripts/install_hooks.py --apply
  python3 scripts/install_hooks.py --check        # exit 0 = 已装且与来源逐字节一致
  python3 scripts/install_hooks.py --uninstall            # dry-run，只看将做什么
  python3 scripts/install_hooks.py --uninstall --apply    # 真删自己的 hook 并恢复备份
  python3 scripts/install_hooks.py --check --hook-dir /tmp/x   # 可测试性：指定目标目录
"""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE = REPO_ROOT / "scripts" / "hooks" / "pre-commit"
MARKER = "# aiworflow-pre-commit v3"
HOOK_NAME = "pre-commit"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _find_git_dir(start: Path) -> Path | None:
    """从 start 向上遍历父目录，找到第一个 .git 目录或文件（worktree）。"""
    for p in [start] + list(start.parents):
        candidate = p / ".git"
        if candidate.exists():
            return candidate
    return None


def default_hook_dir() -> Path:
    """返回本仓库的 .git/hooks；支持 GIT_DIR 覆盖、worktree（.git 为文件）以及
    本目录不在仓库根（如 .ai_worflow/）时向上查找父目录的 .git。"""
    git = _find_git_dir(REPO_ROOT)
    if git is None:
        raise SystemExit("FAIL: 未找到 .git，无法确定 hooks 目录（可用 --hook-dir 指定）")
    if git.is_dir():
        return git / "hooks"
    # worktree / submodule：.git 文件里写着 gitdir: <path>
    for line in git.read_text(encoding="utf-8").splitlines():
        if line.startswith("gitdir:"):
            gd = Path(line.split(":", 1)[1].strip())
            if not gd.is_absolute():
                gd = (git.parent / gd).resolve()
            common = gd / "commondir"
            if common.is_file():
                base = (gd / common.read_text(encoding="utf-8").strip()).resolve()
                return base / "hooks"
            return gd / "hooks"
    raise SystemExit("FAIL: 未找到 .git/hooks，无法确定 hooks 目录（可用 --hook-dir 指定）")


def is_ours(path: Path) -> bool:
    return path.is_file() and MARKER in path.read_text(encoding="utf-8", errors="replace")


def cmd_check(hook_dir: Path) -> int:
    target = hook_dir / HOOK_NAME
    if not SOURCE.is_file():
        print(f"FAIL: 来源 hook 不存在：{SOURCE}")
        return 1
    if not target.is_file():
        print(f"FAIL: 未安装（缺 {target}）——护栏只在手动运行 selftest 时生效")
        print(f"      修复：python3 scripts/install_hooks.py --apply")
        return 1
    if not is_ours(target):
        print(f"FAIL: {target} 存在但不是本脚本安装的 hook（无标记 {MARKER!r}）")
        return 1
    src, dst = sha256(SOURCE), sha256(target)
    if src != dst:
        print(f"FAIL: 已安装 hook 与来源不一致（漂移）")
        print(f"      来源 {src[:16]}…  已装 {dst[:16]}…")
        print(f"      修复：python3 scripts/install_hooks.py --apply")
        return 1
    if not os.access(target, os.X_OK):
        print(f"FAIL: {target} 无执行位，Git 不会调用它")
        return 1
    print(f"PASS: pre-commit 闸门已安装且与来源逐字节一致（{src[:16]}…）")
    print(f"      位置：{target}")
    return 0


def cmd_apply(hook_dir: Path, dry: bool) -> int:
    if not SOURCE.is_file():
        print(f"FAIL: 来源 hook 不存在：{SOURCE}")
        return 1
    hook_dir.mkdir(parents=True, exist_ok=True)
    target = hook_dir / HOOK_NAME
    src_sha = sha256(SOURCE)
    print(f"来源：{SOURCE}（{src_sha[:16]}…）")
    print(f"目标：{target}")

    if target.is_file() and not is_ours(target):
        stamp = time.strftime("%Y%m%d-%H%M%S")
        backup = target.with_name(f"{HOOK_NAME}.foreign-backup-{stamp}")
        print(f"发现外来 hook → 先备份到 {backup.name}（不静默覆盖别人的逻辑）")
        if not dry:
            shutil.copy2(target, backup)
    elif target.is_file():
        if sha256(target) == src_sha and os.access(target, os.X_OK):
            print("已安装且一致，无需改动（幂等）")
            return 0
        print("已安装但与来源不一致 → 原子替换")

    if dry:
        print("[dry-run] 未写盘")
        return 0

    tmp = target.with_name(f".{HOOK_NAME}.tmp-{os.getpid()}")
    shutil.copy2(SOURCE, tmp)
    tmp.chmod(0o755)
    os.replace(tmp, target)  # 原子替换：失败不留半成品
    if sha256(target) != src_sha:
        print("FAIL: 写入后校验不一致")
        return 1
    print(f"已安装：{target}（mode 755，SHA {sha256(target)[:16]}…）")
    print("效果：此后任何改坏工作流的提交都会被 selftest 拦下（阻断级）。")
    return 0


def cmd_uninstall(hook_dir: Path, dry: bool) -> int:
    target = hook_dir / HOOK_NAME
    if not target.is_file():
        print("未安装，无需卸载")
        return 0
    if not is_ours(target):
        print(f"拒绝卸载：{target} 不是本脚本安装的（无标记），不碰别人的 hook")
        return 1
    backups = sorted(hook_dir.glob(f"{HOOK_NAME}.foreign-backup-*"))
    if dry:
        print(f"[dry-run] 将删除 {target}" + (f"，并恢复 {backups[-1].name}" if backups else ""))
        return 0
    target.unlink()
    print(f"已删除 {target}")
    if backups:
        shutil.copy2(backups[-1], target)
        target.chmod(0o755)
        print(f"已恢复备份 {backups[-1].name} → {target.name}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="安装/复核 aiworflow pre-commit 闸门")
    # --uninstall 不在互斥组里：它同样默认 dry-run，需要 --apply 才真删。
    # （旧版把它塞进互斥组，导致 `--uninstall --apply` 直接 argparse 报错，
    #   卸载永远只能停在 dry-run —— 由 selftest §10.6 抓到。）
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true", help="只打印将做什么（默认行为）")
    g.add_argument("--apply", action="store_true", help="实际写入 / 实际卸载")
    g.add_argument("--check", action="store_true", help="复核安装状态与一致性")
    ap.add_argument("--uninstall", action="store_true",
                    help="卸载本脚本装的 hook（默认 dry-run，配 --apply 才真删）")
    ap.add_argument("--hook-dir", type=Path, default=None, help="覆盖 hooks 目录（测试用）")
    a = ap.parse_args()

    if a.uninstall and a.check:
        ap.error("--uninstall 与 --check 不能同时使用")

    hook_dir = (a.hook_dir or default_hook_dir()).resolve()
    if a.check:
        return cmd_check(hook_dir)
    if a.uninstall:
        return cmd_uninstall(hook_dir, dry=not a.apply)
    return cmd_apply(hook_dir, dry=not a.apply)


if __name__ == "__main__":
    sys.exit(main())
