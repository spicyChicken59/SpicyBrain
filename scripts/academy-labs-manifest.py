#!/usr/bin/env python3
"""Write docs/academy/LABS.json from the committed lab evidence and downloads.

Usage: python scripts/academy-labs-manifest.py [--check]

One entry per lab package (content/exercises/lab-*): its execution class,
linked modules, recorded runtime and package versions, test counts, fixture
and output hashes, the target steps it did not execute (tabletop and platform
guides), and the committed download's SHA-256, size and member count. The
evidence file is the record; this manifest only gathers it. With --check the
manifest is rebuilt in memory and compared with the committed file.
"""
from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXERCISES = ROOT / "content" / "exercises"
EVIDENCE = ROOT / "docs" / "academy" / "labs"
DOWNLOADS = ROOT / "content" / "downloads"
COURSE = ROOT / "content" / "courses" / "dbxfe" / "course.json"
OUT = ROOT / "docs" / "academy" / "LABS.json"

CLASSES = {
    "local-executed": "Executed locally in the recorded, pinned environment (Python, local Apache Spark, open-source Delta Lake, open-source MLflow or local PostgreSQL). Not a Databricks workspace run.",
    "tabletop": "An authored decision exercise checked locally against independently authored answers. The target platform behaviour (for example Unity Catalog enforcement or cloud networking) was not executed.",
    "platform-guide": "Local checks of the authored configuration and application code only; every platform step (deploy, validate against a workspace, managed service) is listed as not executed.",
}


def build() -> dict:
    course = json.loads(COURSE.read_text())
    registered = {lab["id"]: lab for lab in course.get("labs", [])}
    labs = []
    for lab_dir in sorted(p for p in EXERCISES.glob("lab-*") if p.is_dir()):
        lab_id = lab_dir.name
        evidence_path = EVIDENCE / f"{lab_id}.json"
        evidence = json.loads(evidence_path.read_text()) if evidence_path.exists() else None
        archive = DOWNLOADS / f"{lab_id}.zip"
        download = None
        if archive.exists():
            data = archive.read_bytes()
            with zipfile.ZipFile(archive) as z:
                members = len(z.infolist())
            download = {
                "path": f"content/downloads/{lab_id}.zip",
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
                "members": members,
            }
        meta = registered.get(lab_id, {})
        entry = {
            "id": lab_id,
            "title": meta.get("title"),
            "registered": lab_id in registered,
            "executionClass": evidence.get("executionClass") if evidence else None,
            "moduleIds": meta.get("moduleIds", []),
            "evidence": f"docs/academy/labs/{lab_id}.json" if evidence else None,
            "download": download,
        }
        if evidence:
            entry.update(
                runtime=evidence.get("runtime") or "stdlib",
                python=evidence.get("python"),
                java=evidence.get("java"),
                packages=evidence.get("packages"),
                tests=evidence.get("tests"),
                failures=evidence.get("failures"),
                errors=evidence.get("errors"),
                skipped=evidence.get("skipped"),
                exit=evidence.get("exit"),
                startedAt=evidence.get("startedAt"),
                fixtureHashes=evidence.get("fixtureHashes"),
                outputHashes=evidence.get("outputHashes"),
                notExecuted=evidence.get("notExecuted", []),
            )
        labs.append(entry)
    by_class: dict[str, int] = {}
    checks_by_class: dict[str, int] = {}
    for lab in labs:
        by_class[lab["executionClass"] or "no evidence"] = by_class.get(lab["executionClass"] or "no evidence", 0) + 1
        key = lab["executionClass"] or "no evidence"
        checks_by_class[key] = checks_by_class.get(key, 0) + (lab.get("tests") or 0)
    return {
        "generatedBy": "python scripts/academy-labs-manifest.py",
        "reexecution": "CI job 'labs' extracts every committed lab download to a clean directory and runs it with run-labs.py --from-zip in environments built from the recorded pins; a differing test count, a skip or a differing fixture hash fails the job.",
        "classes": CLASSES,
        "totals": {
            "labs": len(labs),
            "byClass": by_class,
            "checksByClass": checks_by_class,
            "tests": sum(lab.get("tests") or 0 for lab in labs),
            "skipped": sum(lab.get("skipped") or 0 for lab in labs),
            "registered": sum(1 for lab in labs if lab["registered"]),
        },
        "labs": labs,
    }


def main(argv: list[str]) -> int:
    text = json.dumps(build(), indent=1, ensure_ascii=False) + "\n"
    if "--check" in argv:
        if not OUT.exists() or OUT.read_text() != text:
            print("docs/academy/LABS.json is stale; run scripts/academy-labs-manifest.py", file=sys.stderr)
            return 1
        print("PASS: LABS.json matches the committed evidence and downloads")
        return 0
    OUT.write_text(text)
    print(json.dumps(json.loads(text)["totals"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
