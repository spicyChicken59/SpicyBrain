#!/usr/bin/env python3
"""Audit displayed code against the lab source it may claim to come from.

Usage: python scripts/snippet-audit.py [--write]

For every registered module that the academy contract links to one or more
labs, every fenced code block in the module's lessons and beat handbooks is
compared with the lab packages' code files (.py and .sql). Lines are compared
after trimming, collapsing whitespace and dropping blank and comment-only
lines. A block is:

  verbatim      its lines appear as one contiguous run in a single lab file
  lines         every line appears somewhere in the lab's code, not as one run
  partial       at least half of its lines appear in the lab's code
  illustrative  fewer than half do: shown to explain, not executed by a lab

"illustrative" is not a defect: platform-only statements (grants, cloud
configuration, workspace commands) cannot run in a local lab. The audit makes
the distinction visible so a reader never mistakes one for the other. With
--write the result is recorded in docs/academy/SNIPPETS.json.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COURSE = ROOT / "content" / "courses" / "dbxfe"
TEACHING = ROOT / "content" / "teaching" / "dbxfe"
EXERCISES = ROOT / "content" / "exercises"
FENCE = re.compile(r"^(```|~~~)([A-Za-z0-9_+-]*)\s*\n(.*?)^\1\s*$", re.M | re.S)
CODE_LANGS = {"python", "py", "sql", "pyspark", "sh", "bash", "shell", "yaml", "yml", "json", "text", ""}


def normalize(text: str) -> list[str]:
    out = []
    for raw in text.splitlines():
        line = " ".join(raw.strip().split())
        if not line or line.startswith("#") or line.startswith("--"):
            continue
        # A displayed excerpt often carries an inline teaching comment the
        # executed file does not; compare the code before it.
        line = re.sub(r"\s+(#|--)\s.*$", "", line)
        out.append(line)
    return out


def modules() -> list[str]:
    course = json.loads((COURSE / "course.json").read_text())
    ids = []
    for entry in course["modules"]:
        if "file" in entry:
            ids.append(json.loads((COURSE / entry["file"]).read_text())["module"]["id"])
        else:
            ids.append(entry["id"])
    return ids


def module_lessons(mid: str) -> list[Path]:
    course = json.loads((COURSE / "course.json").read_text())
    for entry in course["modules"]:
        module = json.loads((COURSE / entry["file"]).read_text())["module"] if "file" in entry else entry
        if module["id"] == mid:
            bodies = []
            for lesson_file in module["lessonFiles"]:
                lesson = json.loads((COURSE / lesson_file).read_text())
                bodies.append(COURSE / lesson["bodyFile"])
            return bodies
    return []


def main(argv: list[str]) -> int:
    contract = json.loads((COURSE / "academy.json").read_text())
    labs_for = {m["moduleId"]: m["labIds"] for t in contract["tracks"] for m in t["modules"]}
    registered = set(modules())
    report = {"generatedBy": "python scripts/snippet-audit.py", "rule": " ".join(" ".join(__doc__.split("\n\n")[2:]).split()), "modules": [], "totals": {}}
    totals = {"verbatim": 0, "lines": 0, "partial": 0, "illustrative": 0}
    for mid, lab_ids in labs_for.items():
        if mid not in registered or not lab_ids:
            continue
        lab_files = {}
        for lab in lab_ids:
            for path in sorted((EXERCISES / lab).rglob("*")):
                if path.suffix in (".py", ".sql") and "__pycache__" not in path.parts:
                    lab_files[str(path.relative_to(ROOT))] = normalize(path.read_text())
        if not lab_files:
            continue
        all_lines = {line for lines in lab_files.values() for line in lines}
        sources = [(str(p.relative_to(ROOT)), p.read_text()) for p in module_lessons(mid)]
        teaching = TEACHING / f"{mid}.json"
        if teaching.exists():
            t = json.loads(teaching.read_text())
            sources += [(f"{teaching.relative_to(ROOT)}#{b['id']}", b["handbook"]["markdown"]) for b in t["beats"]]
        blocks = []
        for where, text in sources:
            for match in FENCE.finditer(text):
                lang, body = match.group(2).lower(), match.group(3)
                if lang not in CODE_LANGS:
                    continue
                lines = normalize(body)
                if not lines:
                    continue
                verdict = "illustrative"
                for name, file_lines in lab_files.items():
                    joined = "\n".join(file_lines)
                    if "\n".join(lines) in joined:
                        verdict = "verbatim"
                        break
                if verdict != "verbatim":
                    found = sum(1 for line in lines if line in all_lines)
                    verdict = "lines" if found == len(lines) else "partial" if found * 2 >= len(lines) else "illustrative"
                totals[verdict] += 1
                blocks.append({"where": where, "language": lang or "plain", "lines": len(lines), "verdict": verdict, "firstLine": lines[0][:100]})
        counts = {k: sum(1 for b in blocks if b["verdict"] == k) for k in totals}
        report["modules"].append({"moduleId": mid, "labs": lab_ids, "blocks": len(blocks), **counts, "detail": blocks})
    report["totals"] = {"blocks": sum(totals.values()), **totals}
    print(json.dumps(report["totals"]))
    for m in report["modules"]:
        print(f"{m['moduleId']}: {m['blocks']} blocks, verbatim {m['verbatim']}, lines {m['lines']}, partial {m['partial']}, illustrative {m['illustrative']}")
    if "--write" in argv:
        (ROOT / "docs" / "academy" / "SNIPPETS.json").write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
