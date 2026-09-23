#!/usr/bin/env python3
"""Write the candidate release manifest for a built checkout.

Usage: python scripts/release-manifest.py --out docs/academy/release-manifest.json [dist ...]

Records the source commit, the Node version, the course content manifest
(course id, contentVersion, module/track/lab/guide/case/scenario counts and
download hashes) and, for every build directory given (default: dist and
dist-nested), every published file with its size and SHA-256. A later
publishing session compares the files it uploads with this manifest; it is
evidence of what was built and reviewed, not an authorization to publish.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_listing(directory: Path) -> dict:
    files = sorted(p for p in directory.rglob("*") if p.is_file())
    rows = [{"path": p.relative_to(directory).as_posix(), "bytes": p.stat().st_size, "sha256": sha(p)} for p in files]
    return {
        "directory": directory.name,
        "files": len(rows),
        "bytes": sum(r["bytes"] for r in rows),
        "listing": rows,
    }


def content_manifest() -> dict:
    course = json.loads((ROOT / "content/courses/dbxfe/course.json").read_text())
    modules = []
    for entry in course["modules"]:
        module = json.loads((ROOT / "content/courses/dbxfe" / entry["file"]).read_text())["module"] if "file" in entry else entry
        modules.append(module["id"])
    return {
        "courseId": course["id"],
        "contentVersion": course.get("contentVersion"),
        "modules": len(modules),
        "moduleIds": modules,
        "tracks": len(course.get("tracks", [])),
        "routes": len(course.get("routes", [])),
        "labs": len(course.get("labs", [])),
        "guides": len(course.get("guides", [])),
        "cases": len(course.get("cases", [])),
        "crosswalk": len(course.get("crosswalk", [])),
        "scenarios": len(course["scenarios"]),
        "downloads": [{"id": d["id"], "path": d["path"], "sha256": d["sha256"]} for d in course.get("downloads", [])],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("dist", nargs="*", default=["dist", "dist-nested"])
    args = parser.parse_args()
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    tree = subprocess.run(["git", "rev-parse", "HEAD^{tree}"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    node = subprocess.run(["node", "--version"], capture_output=True, text=True).stdout.strip()
    manifest = {
        "sourceCommit": head,
        "sourceTree": tree,
        "workingTreeClean": not dirty,
        "node": node,
        "content": content_manifest(),
        "builds": [build_listing(ROOT / d) for d in args.dist],
        "note": "Evidence of the reviewed candidate build. Publication requires separate authorization and must re-verify the Site identity, the served bytes against this listing and same-origin study-data continuity.",
    }
    Path(args.out).write_text(json.dumps(manifest, indent=1) + "\n")
    print(json.dumps({k: manifest[k] for k in ("sourceCommit", "workingTreeClean", "node")}), [(b["directory"], b["files"], b["bytes"]) for b in manifest["builds"]])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
