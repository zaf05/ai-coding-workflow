#!/usr/bin/env python3
"""安装 Skill 到宿主，并做版本锁定（默认 dry-run，先看清单再落地）。

版本锁定解决的问题（Harness Engineering 落地规范差距 #2）：
  「同步脚本制造不可复现漂移」——cp 覆盖式安装无法回答「目标机器上装的是哪个版本、
  有没有被人手改过」。本脚本用 **安装收据 + SHA256 清单** 把这件事变成可验证事实：

  * `VERSION` 是本包版本的单一事实源；
  * 每次 `--apply` 在目标目录写 `aiworflow-install-receipt.json`，记录来源根、来源版本、
    安装模式、逐文件 SHA256；
  * `--check` 用收据对比当前源码，能明确回答「一致 / 目标被手改 / 来源已升级」；
  * `--upgrade` 只替换收据里登记过的文件，且先写临时目录再原子 rename，失败不破坏现场；
  * **认领（adopt）**：目标已由历史 symlink/cp 装好但没有收据时，`--apply` 会先用与
    `--check` 相同的标准逐项核对，全部一致才补写收据，且不改动任何 Skill 文件；
    有任何缺失或不一致就拒绝写收据并返回非 0，绝不把漂移状态"洗白"成已锁定。

安全边界（不变）：
  * 不覆盖任何不是本包安装的文件；**存在冲突即拒绝部分安装**：一个文件都不装、
    不写收据、返回非 0（收据只能为「全量安装且逐项可证明一致」的目标背书，
    exit code 是 selftest / CI / pre-commit 唯一信任的信号）；
  * `--apply` 装完立刻用与 `--check` 相同的标准复核，任何缺失/不一致都不写收据；
  * 不删除目标目录里收据未登记的内容；
  * 默认 dry-run，不写盘。

用法：
  python3 install_skills.py --dry-run
  python3 install_skills.py --target "$HOME/.codex/skills" --mode symlink --apply
  python3 install_skills.py --target "$HOME/.codex/skills" --apply    # 已装好时＝认领并补收据
  python3 install_skills.py --target "$HOME/.codex/skills" --check
  python3 install_skills.py --target "$HOME/.codex/skills" --upgrade
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
VERSION_FILE = ROOT / "VERSION"
RECEIPT_NAME = "aiworflow-install-receipt.json"
NAMES = ["_shared", "aiworflow", "aiworflow-planner", "aiworflow-implementer",
         "aiworflow-reviewer", "aiworflow-tester"]


# ------------------------------------------------------------------ 版本与摘要
def read_version() -> str:
    """读 `VERSION`（单一事实源）。缺失时返回 unknown，不猜测。"""
    try:
        return VERSION_FILE.read_text(encoding="utf-8").strip() or "unknown"
    except OSError:
        return "unknown"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def digest_tree(base: Path) -> dict[str, str]:
    """递归摘要，键为相对 POSIX 路径；跳过 __pycache__ 等噪声。"""
    out: dict[str, str] = {}
    if not base.exists():
        return out
    for p in sorted(base.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(base).as_posix()
        if "__pycache__" in rel or rel.endswith(".pyc"):
            continue
        out[rel] = sha256_file(p)
    return out


def source_manifest() -> dict[str, dict[str, str]]:
    """当前源码里每个 Skill 的逐文件摘要。"""
    return {name: digest_tree(SKILLS / name) for name in NAMES}


def source_fingerprint(manifest: dict[str, dict[str, str]]) -> str:
    """整包指纹：对所有 (skill, relpath, sha) 三元组再摘要一次，稳定可比较。"""
    h = hashlib.sha256()
    for name in sorted(manifest):
        for rel in sorted(manifest[name]):
            h.update(f"{name}:{rel}:{manifest[name][rel]}\n".encode())
    return h.hexdigest()


# ------------------------------------------------------------------ 收据读写
def receipt_path(target: Path) -> Path:
    return target / RECEIPT_NAME


def load_receipt(target: Path) -> dict | None:
    p = receipt_path(target)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def write_receipt_atomic(target: Path, receipt: dict) -> Path:
    """先写临时文件再 rename，避免半截收据。"""
    target.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".aiworflow-receipt-", dir=str(target))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(receipt, fh, ensure_ascii=False, indent=2, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, receipt_path(target))
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
    return receipt_path(target)


def build_receipt(target: Path, mode: str, version: str,
                  manifest: dict[str, dict[str, str]]) -> dict:
    return {
        "receipt_version": 1,
        "package": "ai_worflow",
        "source_root": str(ROOT),
        "source_version": version,
        "source_fingerprint": source_fingerprint(manifest),
        "target": str(target.resolve()),
        "mode": mode,
        "skills": sorted(NAMES),
        "installed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "manifest": manifest,
    }


# ------------------------------------------------------------------ 目标盘点
def detect_mode(target: Path) -> str:
    """探测目标里本包 Skill 的实际安装形态，用于认领时写真实模式而非用户入参。"""
    present = [n for n in NAMES if (target / n).exists() or (target / n).is_symlink()]
    if not present:
        return "unknown"
    links = [n for n in present if (target / n).is_symlink()]
    if len(links) == len(present):
        return "symlink"
    if not links:
        return "copy"
    return "mixed"


def inspect_installed(target: Path) -> tuple[list[str], list[str], list[str]]:
    """盘点目标现状，返回 (已一致, 缺失, 不一致说明)。

    判定标准与 `--check` 完全相同，避免「认领」放过真实漂移：
      symlink 看真实路径是否指向本包；copy 看逐文件 SHA256 是否与源码一致。
    """
    ok: list[str] = []
    missing: list[str] = []
    mismatched: list[str] = []
    src_manifest = source_manifest()
    for name in NAMES:
        src = SKILLS / name
        dst = target / name
        if not (dst.exists() or dst.is_symlink()):
            missing.append(name)
            continue
        if dst.is_symlink():
            if os.path.realpath(dst) == os.path.realpath(src):
                ok.append(name)
            else:
                mismatched.append(f"{name}: 软链指向 {os.path.realpath(dst)}，不是本包")
            continue
        actual = digest_tree(dst)
        expected = src_manifest.get(name, {})
        diff = [rel for rel in sorted(set(actual) | set(expected))
                if actual.get(rel) != expected.get(rel)]
        if diff:
            mismatched.append(f"{name}: {len(diff)} 个文件与源码摘要不一致（如 {diff[0]}）")
        else:
            ok.append(name)
    return ok, missing, mismatched


# ------------------------------------------------------------------ 安装计划
def plan(target: Path, mode: str):
    actions, conflicts = [], []
    for name in NAMES:
        src = SKILLS / name
        dst = target / name
        if dst.exists() or dst.is_symlink():
            if dst.is_symlink() and os.path.realpath(dst) == os.path.realpath(src):
                continue  # 已是指向本包的软链，视为已安装
            conflicts.append(dst)
            continue
        actions.append((name, src, dst, mode))
    return actions, conflicts


def do_install(actions) -> None:
    for name, src, dst, mode in actions:
        if mode == "symlink":
            dst.parent.mkdir(parents=True, exist_ok=True)
            os.symlink(src.resolve(), dst)
        else:
            shutil.copytree(src, dst, dirs_exist_ok=True)


# ------------------------------------------------------------------ --check
def run_check(target: Path) -> int:
    """用收据对比当前源码：明确区分「一致 / 目标漂移 / 来源已升级 / 未安装」。"""
    rec = load_receipt(target)
    version = read_version()
    if rec is None:
        print(f"未安装：{target} 下没有 {RECEIPT_NAME}")
        print(f"当前来源版本：{version}")
        return 1

    installed_ver = rec.get("source_version", "unknown")
    manifest = source_manifest()
    fp = source_fingerprint(manifest)

    # symlink 模式下目标是链接，需按真实路径摘要；copy 模式直接摘要目标目录
    drift = []
    for name in NAMES:
        expected = rec.get("manifest", {}).get(name, {})
        dst = target / name
        actual_base = Path(os.path.realpath(dst)) if dst.is_symlink() else dst
        actual = digest_tree(actual_base) if actual_base.exists() else {}
        for rel in sorted(set(expected) | set(actual)):
            if expected.get(rel) != actual.get(rel):
                drift.append(f"{name}/{rel}")

    print(f"目标        : {target}")
    print(f"已安装版本  : {installed_ver}")
    print(f"当前来源版本: {version}")
    print(f"安装模式    : {rec.get('mode')}")
    print(f"指纹一致    : {'是' if rec.get('source_fingerprint') == fp else '否'}")

    ok = True
    if installed_ver != version:
        print(f"来源已升级：{installed_ver} -> {version}（用 --upgrade 同步目标）")
        ok = False
    if drift:
        print(f"目标漂移：{len(drift)} 个文件与收据不一致（可能被手改或来源变更）")
        for d in drift[:20]:
            print(f"  - {d}")
        if len(drift) > 20:
            print(f"  ... 另有 {len(drift) - 20} 个")
        ok = False
    if ok:
        print("校验通过：目标与来源版本、逐文件摘要完全一致。")
        return 0
    return 1


# ------------------------------------------------------------------ --upgrade
def run_upgrade(target: Path, mode: str, apply: bool) -> int:
    """按收据替换本包安装的内容；收据未登记的文件一律不动。"""
    rec = load_receipt(target)
    if rec is None:
        print(f"无法升级：{target} 下没有本包收据。请先 --apply 安装。")
        return 1
    version = read_version()
    manifest = source_manifest()
    managed = {name for name in rec.get("skills", []) if name in NAMES}
    if not managed:
        print("收据未登记任何本包 Skill，拒绝升级（避免误删宿主文件）。")
        return 1

    print(f"目标: {target}")
    print(f"升级: {rec.get('source_version', 'unknown')} -> {version}（模式 {mode}）")
    print(f"将替换 {len(managed)} 个 Skill: {', '.join(sorted(managed))}")
    print("收据未登记的文件不会被触碰。")
    if not apply:
        print("dry-run：未做任何修改。加 --apply 实际执行。")
        return 0

    backup = target / f".aiworflow-backup-{int(time.time())}"
    backup.mkdir(parents=True, exist_ok=True)
    try:
        for name in sorted(managed):
            dst = target / name
            if dst.is_symlink() or dst.exists():
                shutil.move(str(dst), str(backup / name))
        actions = [(n, SKILLS / n, target / n, mode) for n in sorted(managed)]
        do_install(actions)
        write_receipt_atomic(target, build_receipt(target, mode, version, manifest))
    except BaseException as exc:  # 回滚：把备份搬回去，失败不留下半升级状态
        print(f"升级失败，回滚：{exc}")
        for name in sorted(managed):
            dst = target / name
            if dst.is_symlink() or dst.exists():
                if dst.is_dir() and not dst.is_symlink():
                    shutil.rmtree(dst, ignore_errors=True)
                else:
                    dst.unlink(missing_ok=True)
            bk = backup / name
            if bk.is_symlink() or bk.exists():
                shutil.move(str(bk), str(dst))
        return 1
    shutil.rmtree(backup, ignore_errors=True)
    print(f"升级完成，收据已更新为 {version}。")
    print("注意：文件系统安装成功 ≠ 宿主实机加载成功；实机加载需宿主会话内真实触发验证。")
    return 0


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default=str(Path.home() / ".codex" / "skills"))
    ap.add_argument("--mode", choices=["symlink", "copy"], default="symlink")
    ap.add_argument("--dry-run", action="store_true", default=True)
    ap.add_argument("--apply", action="store_true", help="实际执行（否则仅预览）")
    ap.add_argument("--check", action="store_true",
                    help="用安装收据校验目标是否与当前来源版本一致")
    ap.add_argument("--upgrade", action="store_true",
                    help="按收据原子替换本包已安装的 Skill")
    args = ap.parse_args()

    target = Path(args.target).expanduser()

    if args.check:
        return run_check(target)
    if args.upgrade:
        return run_upgrade(target, args.mode, args.apply)

    version = read_version()
    actions, conflicts = plan(target, args.mode)

    print(f"来源版本: {version}  ({ROOT})")
    print(f"目标: {target}")
    print(f"模式: {'dry-run' if not args.apply else args.mode}")

    rec = load_receipt(target)
    if rec:
        same = rec.get("source_version") == version
        print(f"已安装收据: 版本 {rec.get('source_version')} "
              f"指纹{'一致' if same else '不一致（来源已变更）'}")
    else:
        print("已安装收据: 无（首次安装）")

    if conflicts:
        print(f"冲突（跳过，不覆盖）: {len(conflicts)}")
        for c in conflicts:
            print(f"  - {c}")
    if not actions:
        # 没有待安装项 ≠ 版本已被锁定。历史 symlink/cp 安装或收据丢失时，目标内容
        # 完全正确却没有收据，于是 --check 只会回答「未安装」、--upgrade 直接拒绝，
        # 版本锁定形同虚设（配置存在 ≠ 行为有效）。这里补一条**认领**路径：
        # 先用与 --check 相同的标准逐项核对，全部一致才写收据，且不改动任何文件。
        ok, missing, mismatched = inspect_installed(target)
        if mismatched or missing:
            if mismatched:
                print(f"目标存在但与本包不一致（按安全边界不覆盖）: {len(mismatched)}")
                for m in mismatched:
                    print(f"  - {m}")
            if missing:
                print(f"缺失: {len(missing)} 个 -> {', '.join(missing)}")
            print("未写收据：目标状态无法证明与来源一致，需人工确认后再处理。")
            return 1
        if rec is not None:
            installed_ver = rec.get("source_version", "unknown")
            print(f"无待安装项：{len(ok)} 个 Skill 已全部安装，收据在位（版本 {installed_ver}）。")
            if installed_ver != version:
                # 收据在位但来源已前进：必须明确指路，否则用户会以为「装了就是最新」。
                print(f"来源已升级：{installed_ver} -> {version}；用 --upgrade --apply 同步目标并更新收据。")
                return 1
            return 0
        actual_mode = detect_mode(target)
        print(f"已安装且与来源 {version} 逐项一致（{len(ok)} 个 Skill，实际形态 {actual_mode}），但缺少收据。")
        if not args.apply:
            print("dry-run：未做任何修改。加 --apply 认领现有安装并写入收据（不改动任何 Skill 文件）。")
            return 0
        rp = write_receipt_atomic(
            target,
            build_receipt(target, actual_mode, version, source_manifest()),
        )
        print(f"认领完成：未改动任何 Skill 文件，收据已写入 {rp}")
        print("注意：文件系统安装成功 ≠ 宿主实机加载成功；实机加载需宿主会话内真实触发验证。")
        return 0

    print(f"待安装: {len(actions)}")
    for name, src, dst, mode in actions:
        print(f"  {'LINK' if mode == 'symlink' else 'COPY'} {src} -> {dst}")

    if conflicts:
        # 部分安装不是版本锁定。收据只能为「全量安装且逐项可证明一致」的目标背书。
        # 旧行为是照装、照写全量收据、返回 0——等于让收据为它根本没装的文件作伪证
        # （实测：外来软链原封不动，收据 manifest 却登记了该 Skill，--apply exit 0，
        #   只有事后 --check 才抓到漂移）。exit code 是调用方（selftest/CI/hook）
        # 唯一信任的信号，所以这里必须非零，且一个文件都不装。
        print(f"拒绝部分安装：{len(conflicts)} 个目标已存在且不属于本包，"
              f"本次只能装 {len(actions)}/{len(actions) + len(conflicts)} 个。")
        print("未装任何文件、未写收据：收据不得为未安装的文件背书。")
        print("处理方式：人工确认这些目标是谁装的；确需替换时先手工移除，再重跑 --apply。")
        return 1

    if args.apply:
        target.mkdir(parents=True, exist_ok=True)
        do_install(actions)
        # 纵深防御：装完立刻用与 --check 相同的标准复核；任何缺失/不一致都不写收据。
        ok, missing, mismatched = inspect_installed(target)
        if missing or mismatched:
            print(f"安装后复核未通过：缺失 {len(missing)}，不一致 {len(mismatched)}")
            for m in mismatched:
                print(f"  - {m}")
            for m in missing:
                print(f"  - 缺失 {m}")
            print("未写收据：目标状态无法证明与来源一致。")
            return 1
        rp = write_receipt_atomic(target, build_receipt(target, args.mode, version,
                                                       source_manifest()))
        print(f"完成。{len(ok)} 个 Skill 逐项复核一致，收据已写入 {rp}")
        print("注意：文件系统安装成功 ≠ 宿主实机加载成功；实机加载需宿主会话内真实触发验证。")
    else:
        print("dry-run：未做任何修改。加 --apply 实际执行。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
