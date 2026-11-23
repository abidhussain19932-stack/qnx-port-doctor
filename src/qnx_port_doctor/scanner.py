"""Walks a source tree and reports Linux-only API usage."""
from __future__ import annotations

import os
from dataclasses import dataclass, asdict
from pathlib import Path

from .rules import RULES, C_EXTS, BUILD_FILES, BUILD_ONLY_RULES, Rule

SKIP_DIRS = {".git", "build", "build-qnx", "node_modules", "__pycache__", ".venv"}


@dataclass
class Finding:
    rule_id: str
    severity: str
    path: str  # relative to scan root, POSIX separators
    line: int
    column: int
    snippet: str
    title: str
    advice: str

    def to_dict(self):
        return asdict(self)


def _strip_line_comment(line: str) -> str:
    # good-enough comment stripping: drop // comments that aren't inside a string
    in_str = False
    for i, ch in enumerate(line):
        if ch == '"' and (i == 0 or line[i - 1] != "\\"):
            in_str = not in_str
        if not in_str and line.startswith("//", i):
            return line[:i]
    return line


def scan_file(path: Path, root: Path, rules: list[Rule] = RULES) -> list[Finding]:
    is_build = path.name in BUILD_FILES or path.suffix == ".mk"
    active = [r for r in rules if (r.id in BUILD_ONLY_RULES) == is_build]
    findings: list[Finding] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return findings
    in_block = False
    rel = path.relative_to(root).as_posix()
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw
        if not is_build:
            # strip /* ... */ block comments across lines
            out, i = [], 0
            while i < len(line):
                if in_block:
                    end = line.find("*/", i)
                    if end < 0:
                        i = len(line)
                    else:
                        in_block, i = False, end + 2
                else:
                    start = line.find("/*", i)
                    if start < 0:
                        out.append(line[i:])
                        i = len(line)
                    else:
                        out.append(line[i:start])
                        in_block, i = True, start + 2
            line = _strip_line_comment("".join(out))
        elif line.lstrip().startswith("#"):
            continue
        if "qpd: ignore" in raw:
            continue
        for rule in active:
            m = rule.regex.search(line)
            if m:
                findings.append(Finding(rule.id, rule.severity, rel, lineno, m.start() + 1,
                                        raw.strip()[:200], rule.title, rule.qnx_equivalent))
    return findings


def iter_sources(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            p = Path(dirpath) / name
            if p.suffix in C_EXTS or name in BUILD_FILES or p.suffix == ".mk":
                yield p


def scan(root: str | Path) -> list[Finding]:
    root = Path(root).resolve()
    if root.is_file():
        return scan_file(root, root.parent)
    out: list[Finding] = []
    for p in iter_sources(root):
        out.extend(scan_file(p, root))
    return out


def summarize(findings: list[Finding]) -> dict:
    s = {"error": 0, "warning": 0, "note": 0, "files": len({f.path for f in findings})}
    for f in findings:
        s[f.severity] += 1
    # Portability score: 100 minus weighted issues, floored at 0
    s["score"] = max(0, 100 - 10 * s["error"] - 3 * s["warning"] - s["note"])
    return s
