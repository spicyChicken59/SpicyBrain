#!/usr/bin/env python3
"""Print the union of pinned lab requirements for one runtime.

Usage: python scripts/lab-requirements.py spark|ml|stdlib

A lab's runtime is the "runtime" recorded in its committed evidence
(docs/academy/labs/<lab>.json): "spark", "ml", or absent for the standard
library. Every requirement must be pinned with ==, and two labs on the same
runtime may not pin different versions of one package; either case fails
rather than silently choosing a version.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXERCISES = ROOT / "content" / "exercises"
EVIDENCE = ROOT / "docs" / "academy" / "labs"
PIN = re.compile(r"^([A-Za-z0-9_.\-\[\]]+)==([A-Za-z0-9_.\-+]+)$")


def main(runtime: str) -> int:
    wanted = None if runtime == "stdlib" else runtime
    pins: dict[str, tuple[str, str]] = {}
    problems = []
    for lab_dir in sorted(EXERCISES.glob("lab-*")):
        evidence = EVIDENCE / f"{lab_dir.name}.json"
        if not evidence.exists():
            continue
        if json.loads(evidence.read_text()).get("runtime") != wanted:
            continue
        requirements = lab_dir / "requirements.txt"
        if not requirements.exists():
            continue
        for raw in requirements.read_text().splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            match = PIN.match(line)
            if not match:
                problems.append(f"{lab_dir.name}: unpinned requirement {line!r}")
                continue
            name, version = match.group(1).lower(), match.group(2)
            if name in pins and pins[name][0] != version:
                problems.append(
                    f"{lab_dir.name}: {name}=={version} conflicts with "
                    f"{pins[name][1]}'s {name}=={pins[name][0]}"
                )
            pins.setdefault(name, (version, lab_dir.name))
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    for name in sorted(pins):
        print(f"{name}=={pins[name][0]}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in {"spark", "ml", "stdlib"}:
        raise SystemExit(__doc__)
    raise SystemExit(main(sys.argv[1]))
