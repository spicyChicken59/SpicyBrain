#!/usr/bin/env python3
"""Execute every runnable lab package and compare with the committed evidence.

Usage:
  python scripts/run-labs.py [--python PATH] [--spark-python PATH] [--ml-python PATH]
                             [--evidence-dir DIR] [--only lab-id ...]

For each content/exercises/lab-*/run_tests.py the runner executes
`python run_tests.py --evidence <dir>/<lab>.json` with the lab directory as
the working directory, then checks the produced evidence against
docs/academy/labs/<lab>.json: same execution class, same test count, zero
skips, exit status 0 and identical fixture hashes. A differing test count or
a skipped test fails the run; nothing is relabelled. The committed evidence's
"runtime" field ("spark", "ml" or absent for the standard library) selects the
interpreter, which must already have that lab's pinned requirements.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXERCISES = ROOT / "content" / "exercises"
COMMITTED = ROOT / "docs" / "academy" / "labs"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", default=sys.executable,
                        help="interpreter for labs whose evidence names no runtime")
    parser.add_argument("--spark-python", default=None,
                        help="interpreter for labs whose evidence runtime is 'spark'")
    parser.add_argument("--ml-python", default=None,
                        help="interpreter for labs whose evidence runtime is 'ml'")
    parser.add_argument("--evidence-dir", default=str(ROOT / "test-results" / "labs"))
    parser.add_argument("--only", nargs="*", default=None)
    parser.add_argument("--from-zip", action="store_true",
                        help="extract each lab's committed download to a clean temp dir and run it there")
    args = parser.parse_args()
    out = Path(args.evidence_dir)
    out.mkdir(parents=True, exist_ok=True)
    labs = sorted(p.parent.name for p in EXERCISES.glob("lab-*/run_tests.py"))
    if args.only:
        labs = [lab for lab in labs if lab in set(args.only)]
    failures: list[str] = []
    summary = []
    for lab in labs:
        evidence = out / f"{lab}.json"
        committed_path = COMMITTED / f"{lab}.json"
        runtime = (
            json.loads(committed_path.read_text()).get("runtime")
            if committed_path.exists()
            else None
        )
        interpreter = {
            "spark": args.spark_python,
            "ml": args.ml_python,
        }.get(runtime) or args.python
        workdir = EXERCISES / lab
        extracted = None
        if args.from_zip:
            archive = ROOT / "content" / "downloads" / f"{lab}.zip"
            if not archive.exists():
                failures.append(f"{lab}: no committed download at {archive}")
                continue
            extracted = tempfile.TemporaryDirectory(prefix=f"{lab}-")
            with zipfile.ZipFile(archive) as bundle:
                bundle.extractall(extracted.name)
            workdir = Path(extracted.name)
        result = subprocess.run(
            [interpreter, "run_tests.py", "--evidence", str(evidence)],
            cwd=workdir,
            capture_output=True,
            text=True,
        )
        if extracted:
            extracted.cleanup()
        tail = (result.stdout + result.stderr)[-2000:]
        if result.returncode != 0 or not evidence.exists():
            failures.append(f"{lab}: exit {result.returncode}\n{tail}")
            continue
        produced = json.loads(evidence.read_text())
        if not committed_path.exists():
            failures.append(f"{lab}: no committed evidence at {committed_path}")
            continue
        committed = json.loads(committed_path.read_text())
        problems = []
        for key in ("executionClass", "tests"):
            if produced.get(key) != committed.get(key):
                problems.append(f"{key}: produced {produced.get(key)!r}, committed {committed.get(key)!r}")
        if produced.get("skipped") or produced.get("failures") or produced.get("errors"):
            problems.append("tests skipped or failed")
        if produced.get("fixtureHashes") != committed.get("fixtureHashes"):
            problems.append("fixture hashes differ from committed evidence")
        if problems:
            failures.append(f"{lab}: " + "; ".join(problems))
        summary.append({"lab": lab, "tests": produced.get("tests"), "exit": result.returncode})
    print(json.dumps(summary, indent=2))
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(f"PASS: {len(summary)} lab packages executed and matched committed evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
