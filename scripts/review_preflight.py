#!/usr/bin/env python3
"""Reviewer deterministic preflight for a committed candidate diff.

The checker is intentionally conservative: it does not decide code correctness;
it only catches facts that a reviewer should not have to rediscover by eye.

Checks:
  SECRET_SCAN          secret-like additions (placeholders are exempt)
  PROTECTED_PATHS      immutable run ledgers / previous-state snapshots
                       (paths named runs/... or state.prev.yaml inside the
                       reviewed main-repo diff; .ai_worflow itself is not a
                       git repo, so this rule is defense-in-depth for
                       main-repo copies of those names, and ledger integrity
                       is otherwise enforced by the runs/ append-only rule)
  DESTRUCTIVE_COMMANDS destructive command patterns in added lines
  REVIEW_SIZE          changed-file and added-line thresholds

Usage:
  python3 scripts/review_preflight.py runs/RUN-ID [--output PATH|-]
  python3 scripts/review_preflight.py runs/RUN-ID --base SHA --head SHA --root PATH

The base/head/root values default to ``state.yaml:repository``. Output defaults
to stdout, so Reviewer can stay read-only. Use ``--output`` only when the
Planner explicitly authorizes a persistent report path.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - PyYAML is part of the current runtime
    print("FAIL: review_preflight.py requires PyYAML to read state.yaml", file=sys.stderr)
    raise

ROOT = Path(__file__).resolve().parent.parent

SECRET_PATTERNS = [
    ("sk-key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("bearer-token", re.compile(r"\bBearer\s+[A-Za-z0-9._+/=-]{20,}\b", re.I)),
    ("key-assignment", re.compile(r"\b(?:api[_-]?key|secret|token|password)\s*[:=]\s*[\"']?[A-Za-z0-9._+/=-]{20,}", re.I)),
]
PLACEHOLDER_WORDS = (
    "<", "${", "$", "example", "placeholder", "dummy", "synthetic",
    "redacted", "xxxx", "fake", "changeme", "test",
)
DESTRUCTIVE_PATTERNS = [
    re.compile(r"\bgit\s+reset\s+--hard\b"),
    re.compile(r"\bgit\s+checkout\s+--\b"),
    re.compile(r"\brm\s+-rf\b"),
]
PROTECTED_PATH_PATTERNS = [
    re.compile(r"(?:^|/)runs/(?:.+)"),
    re.compile(r"(?:^|/)state\.prev\.yaml$"),
]
DEFAULT_MAX_FILES = 25
DEFAULT_MAX_LINES = 2500


@dataclass
class Finding:
    path: str
    line: int | None
    message: str

    def as_dict(self) -> dict:
        return {"path": self.path, "line": self.line, "message": self.message}


def run_git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=False
    )


def require_commit(root: Path, sha: str, label: str) -> str | None:
    result = run_git(root, ["cat-file", "-e", f"{sha}^{{commit}}"])
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()
        detail_text = detail[0] if detail else "unknown git error"
        return f"{label} commit is unavailable: {sha} ({detail_text})"
    return None


def parse_added_patch(patch: str) -> list[tuple[str, int, str]]:
    rows: list[tuple[str, int, str]] = []
    path = ""
    old_line = 0
    new_line = 0
    for raw in patch.splitlines():
        if raw.startswith("+++ b/"):
            path = raw[6:]
            continue
        match = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", raw)
        if match:
            new_line = int(match.group(1))
            continue
        if not path or not raw.startswith("+") or raw.startswith("+++"):
            if raw.startswith("-"):
                old_line += 1
            elif raw.startswith(" "):
                old_line += 1
                new_line += 1
            continue
        rows.append((path, new_line, raw[1:]))
        new_line += 1
    return rows


def count_changed_patch_lines(patch: str) -> tuple[int, int]:
    added = 0
    deleted = 0
    for raw in patch.splitlines():
        if raw.startswith("+++") or raw.startswith("---"):
            continue
        if raw.startswith("+"):
            added += 1
        elif raw.startswith("-"):
            deleted += 1
    return added, deleted


def scan_secret(rows: list[tuple[str, int, str]]) -> list[Finding]:
    findings: list[Finding] = []
    lowered_placeholders = tuple(word.lower() for word in PLACEHOLDER_WORDS)
    for path, line_no, text in rows:
        lower = text.lower()
        if any(word in lower for word in lowered_placeholders):
            continue
        for label, pattern in SECRET_PATTERNS:
            match = pattern.search(text)
            if not match:
                continue
            # Report the rule class only; never echo matched key material,
            # not even a prefix (a finding that leaks the secret defeats itself).
            findings.append(Finding(path, line_no, f"secret-like addition ({label})"))
            break
    return findings


def scan_destructive(rows: list[tuple[str, int, str]]) -> list[Finding]:
    findings: list[Finding] = []
    for path, line_no, text in rows:
        for pattern in DESTRUCTIVE_PATTERNS:
            if pattern.search(text):
                findings.append(Finding(path, line_no, f"destructive command pattern: {pattern.pattern}"))
                break
    return findings


def scan_protected(paths: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for path in paths:
        normalized = path.replace("\\", "/")
        if any(pattern.fullmatch(normalized) or pattern.search(normalized) for pattern in PROTECTED_PATH_PATTERNS):
            findings.append(Finding(normalized, None, "protected run ledger/snapshot path changed"))
    return findings


def make_rule(rule_id: str, findings: list[Finding], warn: bool = False) -> dict:
    status = "PASS"
    if findings:
        status = "WARN" if warn else "FAIL"
    return {"id": rule_id, "status": status, "findings": [f.as_dict() for f in findings]}


def write_report(path: str, report: dict) -> None:
    text = yaml.safe_dump(report, allow_unicode=True, sort_keys=False)
    if path == "-":
        print(text, end="")
        return
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--base")
    parser.add_argument("--head")
    parser.add_argument("--root", type=Path)
    parser.add_argument("--output", default="-")
    parser.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES)
    parser.add_argument("--max-lines", type=int, default=DEFAULT_MAX_LINES)
    args = parser.parse_args(argv)

    run_dir = args.run_dir
    if not run_dir.is_absolute():
        run_dir = ROOT / run_dir
    state_path = run_dir / "state.yaml"
    if not state_path.is_file():
        print(f"FAIL: state.yaml not found: {state_path}", file=sys.stderr)
        return 2
    try:
        state = yaml.safe_load(state_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        print(f"FAIL: cannot parse {state_path}: {exc}", file=sys.stderr)
        return 2
    repository = state.get("repository") if isinstance(state, dict) else None
    if not isinstance(repository, dict):
        print("FAIL: state.yaml repository section is missing", file=sys.stderr)
        return 2

    raw_root = args.root or repository.get("root")
    if not raw_root:
        print("FAIL: repository.root is missing", file=sys.stderr)
        return 2
    repo_root = Path(str(raw_root))
    if not repo_root.is_absolute():
        repo_root = (ROOT.parent / repo_root).resolve()
    else:
        repo_root = repo_root.resolve()
    if not repo_root.is_dir():
        print(f"FAIL: repository root does not exist: {repo_root}", file=sys.stderr)
        return 2

    base = args.base or repository.get("target_base_sha")
    head = args.head or repository.get("current_sha")
    if not base or not head:
        print("FAIL: target_base_sha/current_sha are missing", file=sys.stderr)
        return 2

    error = require_commit(repo_root, str(base), "base") or require_commit(repo_root, str(head), "head")
    if error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 2

    patch_result = run_git(repo_root, ["diff", f"{base}..{head}"])
    if patch_result.returncode != 0:
        detail = (patch_result.stderr or patch_result.stdout).strip()
        print(f"FAIL: git diff failed: {detail}", file=sys.stderr)
        return 2
    names_result = run_git(repo_root, ["diff", "--name-only", f"{base}..{head}"])
    if names_result.returncode != 0:
        detail = (names_result.stderr or names_result.stdout).strip()
        print(f"FAIL: git diff --name-only failed: {detail}", file=sys.stderr)
        return 2

    patch = patch_result.stdout
    changed_paths = [line for line in names_result.stdout.splitlines() if line]
    added_rows = parse_added_patch(patch)
    added_lines, deleted_lines = count_changed_patch_lines(patch)
    changed_lines = added_lines + deleted_lines

    rules = [
        make_rule("SECRET_SCAN", scan_secret(added_rows)),
        make_rule("PROTECTED_PATHS", scan_protected(changed_paths)),
        make_rule("DESTRUCTIVE_COMMANDS", scan_destructive(added_rows)),
    ]
    size_findings: list[Finding] = []
    if len(changed_paths) > args.max_files:
        size_findings.append(Finding("-", None, f"changed files {len(changed_paths)} > {args.max_files}"))
    if added_lines > args.max_lines:
        size_findings.append(Finding("-", None, f"added lines {added_lines} > {args.max_lines}"))
    rules.append(make_rule("REVIEW_SIZE", size_findings, warn=True))

    verdict = "FAIL" if any(rule["status"] == "FAIL" for rule in rules) else "PASS"
    report = {
        "schema_version": 1,
        "run_id": (state.get("run") or {}).get("id") if isinstance(state.get("run"), dict) else None,
        "base_sha": str(base),
        "head_sha": str(head),
        "changed_files": len(changed_paths),
        "added_lines": added_lines,
        "deleted_lines": deleted_lines,
        "changed_lines": changed_lines,
        "verdict": verdict,
        "rules": rules,
    }
    write_report(args.output, report)
    return 1 if verdict == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
