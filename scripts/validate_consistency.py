#!/usr/bin/env python3
"""Validate G0-G10 consistency across gates doc, feature workflow, and flow HTML."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

GATES = [f"G{i}" for i in range(11)]


def gate_tokens(text: str) -> set[str]:
    return set(re.findall(r"\bG(?:10|[0-9])\b", text))


def workflow_blocks(text: str) -> list[dict[str, str]]:
    blocks: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for raw in text.splitlines():
        match = re.match(r"\s*-?\s*label:\s*(\S+)\s*$", raw)
        if match:
            if current:
                blocks.append(current)
            current = {"label": match.group(1)}
        elif current:
            gate = re.match(r"\s*gate:\s*(G(?:10|[0-9]))\s*$", raw)
            star = re.match(r"\s*star:\s*true\s*$", raw)
            if gate:
                current["gate"] = gate.group(1)
            elif star:
                current["star"] = "true"
    if current:
        blocks.append(current)
    return blocks


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs", type=Path, default=root / "docs/03-gates.md")
    parser.add_argument("--workflow", type=Path, default=root / "workflows/feature-delivery.workflow.yaml")
    parser.add_argument("--html", type=Path, default=root / "aiworflow-full-flow.html")
    args = parser.parse_args()

    errors: list[str] = []
    paths = {"docs": args.docs, "workflow": args.workflow, "html": args.html}
    for name, path in paths.items():
        if not path.is_file():
            print(f"FAIL {name} file not found: {path}")
            return 1
    docs = args.docs.read_text(encoding="utf-8")
    workflow = args.workflow.read_text(encoding="utf-8")
    html = args.html.read_text(encoding="utf-8")

    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    title_match = re.search(r"<title>(.*?)</title>", html, re.S)
    if not title_match or f"v{version}" not in title_match.group(1):
        errors.append(f"HTML title must contain current VERSION v{version}")
    readme = (root / "README.md").read_text(encoding="utf-8")
    readme_version_lines = [line for line in readme.splitlines() if line.startswith("版本：")]
    if not readme_version_lines or f"v{version}" not in readme_version_lines[0]:
        errors.append(f"README version line must contain current VERSION v{version}")

    docs_gates = {token for token in gate_tokens(docs) if re.search(rf"^\|\s*{token}(?:\s|\s*，|)", docs, re.M)}
    # Table rows are authoritative here; avoid matching unrelated references.
    docs_gates = set(re.findall(r"^\|\s*(G(?:10|[0-9]))\s", docs, re.M))
    missing_docs = sorted(set(GATES) - docs_gates)
    if missing_docs:
        errors.append(f"missing docs gates: {', '.join(missing_docs)}")
    if "TDD Red" not in docs:
        errors.append("missing TDD Red in docs")

    blocks = workflow_blocks(workflow)
    workflow_gates = {b["gate"] for b in blocks if "gate" in b}
    missing_workflow = sorted(set(GATES) - workflow_gates)
    if missing_workflow:
        errors.append(f"missing workflow gates: {', '.join(missing_workflow)}")
    star_gates = {b.get("gate") for b in blocks if b.get("star") == "true"}
    if star_gates != {"G3", "G8"}:
        errors.append(f"workflow star gates must be exactly G3/G8, got {sorted(star_gates)}")
    if "TDD Red" not in workflow or "TDD-RED" not in workflow:
        errors.append("missing TDD Red / TDD-RED evidence in workflow")
    if "CODE_REVIEW APPROVE" not in workflow:
        errors.append("missing CODE_REVIEW APPROVE in workflow")

    html_gates = gate_tokens(html)
    missing_html = sorted(set(GATES) - html_gates)
    if missing_html:
        errors.append(f"missing html gates: {', '.join(missing_html)}")
    if "TDD Red" not in html:
        errors.append("missing TDD Red in html")
    if "Code Review" not in html:
        errors.append("missing Code Review in html")
    if "context/" not in html or "G1 读入" not in html or "G10 写出" not in html:
        errors.append("missing G1 read / G10 write context explanation in html")

    if errors:
        print("FAIL architecture consistency")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        "RESULT "
        f"docs_gates={len(docs_gates)} workflow_gates={len(workflow_gates)} "
        f"html_gates={len(html_gates)} star_blocks={len(star_gates)} "
        "tdd_red=true code_review=true context=true"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
