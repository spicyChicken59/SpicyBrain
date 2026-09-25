#!/usr/bin/env python3
"""Replace build-machine paths in lab evidence with named placeholders.

Usage: python scripts/public-evidence.py [--check] [evidence.json ...]

Lab evidence records the command that actually ran. The build machine's
virtual-environment and scratch paths say nothing useful to a reader and
publish machine layout, so they are replaced with placeholders that the
evidence itself defines in a "placeholders" object:

  <spark-env>  a virtual environment holding the lab's pinned Spark requirements
  <ml-env>     a virtual environment holding the lab's pinned ML requirements
  <scratch>    a temporary directory outside the repository

Nothing else in the record changes. With --check the files are only read and
the script fails if any still contains a build-machine path. Without file
arguments every docs/academy/labs/*.json is processed.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLACEHOLDERS = {
    "<spark-env>": "a virtual environment holding the lab's pinned Spark requirements (see requirements.txt)",
    "<ml-env>": "a virtual environment holding the lab's pinned ML requirements (see requirements.txt)",
    "<scratch>": "a temporary directory outside the repository",
}
RULES = [
    (re.compile(r"/home/user/labenv/spark-env"), "<spark-env>"),
    (re.compile(r"/home/user/labenv/ml-env"), "<ml-env>"),
    (re.compile(r"/tmp/claude-[^\s\"']*?/scratchpad(?:/[^\s\"']*)?/"), "<scratch>/"),
    (re.compile(r"/tmp/claude-[^\s\"']*?/scratchpad"), "<scratch>"),
    (re.compile(r"/home/user/spicybrain/"), ""),
]
FORBIDDEN = re.compile(r"/home/user/|/tmp/claude-|scratchpad|JAVA_TOOL_OPTIONS|proxyHost|nonProxyHosts")


def rewrite(value):
    if isinstance(value, str):
        for pattern, replacement in RULES:
            value = pattern.sub(replacement, value)
        return value
    if isinstance(value, list):
        return [rewrite(v) for v in value]
    if isinstance(value, dict):
        return {k: rewrite(v) for k, v in value.items()}
    return value


def main(argv: list[str]) -> int:
    checking = "--check" in argv
    files = [Path(a) for a in argv if a != "--check"] or sorted(
        (ROOT / "docs" / "academy" / "labs").glob("*.json")
    )
    problems = []
    for path in files:
        text = path.read_text()
        if checking:
            if FORBIDDEN.search(text):
                problems.append(f"{path}: contains a build-machine path")
            continue
        data = json.loads(text)
        new = rewrite(data)
        used = {k: v for k, v in PLACEHOLDERS.items() if k in json.dumps(new)}
        if used:
            new["placeholders"] = {**new.get("placeholders", {}), **used}
        if new != data:
            path.write_text(json.dumps(new, indent=2, ensure_ascii=False) + "\n")
            print(f"rewrote {path.relative_to(ROOT) if path.is_absolute() else path}")
        if FORBIDDEN.search(path.read_text()):
            problems.append(f"{path}: still contains a build-machine path")
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
