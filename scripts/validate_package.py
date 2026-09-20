#!/usr/bin/env python3
"""校验整个 AIWorflow 包：Skill 结构、frontmatter、相对链接、模板与工作流一致性。

退出码：0 = 通过；1 = 失败。
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
DOCS = ROOT / "docs"
WORKFLOWS = ROOT / "workflows"
PROMPTS = ROOT / "prompts"

ROLE_SKILLS = ["aiworflow", "aiworflow-planner", "aiworflow-implementer",
               "aiworflow-reviewer", "aiworflow-tester"]

errors = []


def err(msg):
    errors.append(msg)


def check_frontmatter(path: Path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        err(f"{path.relative_to(ROOT)}: 缺少 frontmatter")
        return text
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        err(f"{path.relative_to(ROOT)}: frontmatter 未闭合")
        return text
    fm = m.group(1)
    name_m = re.search(r"^name:\s*(.+)$", fm, re.M)
    desc_m = re.search(r"^description:\s*(.+)$", fm, re.M)
    if not name_m:
        err(f"{path.relative_to(ROOT)}: frontmatter 缺少 name")
    if not desc_m:
        err(f"{path.relative_to(ROOT)}: frontmatter 缺少 description")
    elif len(desc_m.group(1).strip()) < 30:
        err(f"{path.relative_to(ROOT)}: description 太短，缺乏区分度")
    if name_m and path.parent.name != name_m.group(1).strip():
        err(f"{path.relative_to(ROOT)}: name 与目录名不一致 ({name_m.group(1).strip()})")
    return text


def check_links(path: Path, text: str):
    base = path.parent
    for m in re.finditer(r"\]\(([^)]+)\)", text):
        target = m.group(1).strip()
        if target.startswith(("http://", "https://", "#", "<")):
            continue
        if "<" in target or ">" in target:
            continue
        # 去掉锚点
        pure = target.split("#", 1)[0]
        if not pure:
            continue
        resolved = (base / pure).resolve()
        if not resolved.exists():
            err(f"{path.relative_to(ROOT)}: 链接失效 -> {target}")


def walk_md(directory: Path):
    for p in sorted(directory.rglob("*.md")):
        yield p


def main():
    # 1. Skill 目录结构
    if not SKILLS.exists():
        err("skills/ 目录不存在")
        return 1

    for name in ROLE_SKILLS:
        d = SKILLS / name
        if not (d / "SKILL.md").exists():
            err(f"{d.relative_to(ROOT)}: 缺少 SKILL.md")

    # _shared 绝不能有 SKILL.md
    for p in (SKILLS / "_shared").rglob("SKILL.md"):
        err(f"{p.relative_to(ROOT)}: _shared 不允许包含 SKILL.md")

    # 2. frontmatter + 链接（SKILL.md 与 references）
    for name in ROLE_SKILLS:
        d = SKILLS / name
        sk = d / "SKILL.md"
        if sk.exists():
            text = check_frontmatter(sk)
            check_links(sk, text)
        for ref in sorted((d / "references").glob("*.md")):
            check_links(ref, ref.read_text(encoding="utf-8"))

    # 3. _shared 契约与参考链接
    for p in list((SKILLS / "_shared" / "contracts").glob("*.md")) + \
             list((SKILLS / "_shared" / "references").glob("*.md")):
        check_links(p, p.read_text(encoding="utf-8"))

    # 4. 模板存在性（至少 state/current/test-plan/evidence 四文件）
    required_templates = ["run-state.yaml", "current.md", "test-plan.md", "evidence.md",
                          "handoff.md", "review.yaml", "test-report.yaml", "implementation-report.yaml"]
    for t in required_templates:
        if not (SKILLS / "_shared" / "templates" / t).exists():
            err(f"skills/_shared/templates/{t}: 缺失")

    # 5. Prompt 模板 static/dynamic 分段
    for p in sorted(PROMPTS.glob("*.md")):
        text = p.read_text(encoding="utf-8")
        if p.name == "README.md":
            continue
        if "STATIC-BEGIN" not in text or "STATIC-END" not in text:
            err(f"{p.relative_to(ROOT)}: 缺少 STATIC 分段")
        if "DYNAMIC-BEGIN" not in text or "DYNAMIC-END" not in text:
            err(f"{p.relative_to(ROOT)}: 缺少 DYNAMIC 分段")

    # 6. 工作流正例必须通过 validate_workflow.py
    for wf in sorted(WORKFLOWS.glob("*.workflow.yaml")):
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_workflow.py"), str(wf)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            err(f"{wf.relative_to(ROOT)}: 正例校验失败 -> {r.stdout.strip()}")

    # 7. 反例必须被拒绝
    for wf in sorted((WORKFLOWS / "_invalid").glob("*.workflow.yaml")):
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_workflow.py"), str(wf)],
                           capture_output=True, text=True)
        if r.returncode == 0:
            err(f"{wf.relative_to(ROOT)}: 反例被错误接受（应 FAIL）")

    # 8. docs 链接检查
    for p in walk_md(DOCS):
        check_links(p, p.read_text(encoding="utf-8"))

    # 9. docs 索引完整性（确定性护栏）：每篇编号文档必须在 docs/README.md 索引中出现。
    #    把"请不要漏登记"升级成"系统不允许漏登记"——杜绝新增 doc 未进索引的漂移
    #    （文章核心教训：配置存在 ≠ 行为有效；约束要下沉到可执行检查）。
    docs_index = DOCS / "README.md"
    if docs_index.exists():
        index_text = docs_index.read_text(encoding="utf-8")
        for doc in sorted(DOCS.glob("[0-9][0-9]-*.md")):
            if doc.name not in index_text:
                err(f"docs/README.md: 索引缺少 `{doc.name}`（每篇编号文档必须登记）")
    else:
        err("docs/README.md: 索引文件缺失")

    # 10. runs/ 容器一致性（确定性护栏）：每个 run 目录要么通过 validate_run.py，
    #     要么在 runs/README.md 里被显式登记为占位（墓碑）。不允许第三种状态。
    #     为什么要管：半清理的 run 静静躺在库里恒定 FAIL，会让人和 Agent 习惯性
    #     忽略 FAIL——护栏一旦被当噪音，就等于没有。要么清理，要么显式承担。
    runs_dir = ROOT / "runs"
    if not runs_dir.is_dir():
        err("runs/: 目录缺失")
    else:
        runs_readme = runs_dir / "README.md"
        registry = runs_readme.read_text(encoding="utf-8") if runs_readme.exists() else ""
        for d in sorted(x for x in runs_dir.iterdir() if x.is_dir()):
            r = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_run.py"), str(d)],
                               capture_output=True, text=True)
            if r.returncode == 0:
                continue
            if f"`{d.name}/`" in registry or f"`{d.name}`" in registry:
                continue  # 已登记为占位：显式承担，不算噪音
            err(f"runs/{d.name}: 既不通过 validate_run.py，也未在 runs/README.md 登记为占位"
                f"（要么清理，要么登记——不允许恒定 FAIL 沦为噪音）")

    if errors:
        print(f"FAIL（{len(errors)} 个问题）")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("PASS：Skill 结构、frontmatter、相对链接、模板、Prompt 分段、工作流正例/反例、docs 索引完整性、runs 容器一致性全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
