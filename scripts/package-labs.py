#!/usr/bin/env python3
"""Package lab exercise directories into deterministic ZIP downloads.

Usage: python scripts/package-labs.py [--check] [package-id ...]

Each content/exercises/<lab-id>/ or capstone-<id>/ data-pack directory
(excluding the original reliable-data package, which has its own packager)
is written to
content/downloads/<lab-id>.zip with sorted members, fixed timestamps and
deflate compression, so a rebuild from unchanged sources produces identical
bytes. Only the member types the application accepts are packaged; caches
and virtual environments are refused rather than skipped silently. The
script prints the SHA-256 and member count for course.json. With --check it
rebuilds nothing and fails when a committed ZIP's members differ from the
source directory.
"""
from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXERCISES = ROOT / "content" / "exercises"
DOWNLOADS = ROOT / "content" / "downloads"
ALLOWED = {".md", ".txt", ".json", ".csv", ".py", ".sql", ".toml"}
REFUSED_DIRS = {"__pycache__", ".venv", "venv", ".pytest_cache", "spark-warehouse", "metastore_db"}
FIXED_TIME = (2026, 9, 23, 0, 0, 0)


def members(directory: Path) -> list[Path]:
    files = []
    for path in sorted(directory.rglob("*")):
        if path.is_dir():
            if path.name in REFUSED_DIRS:
                raise SystemExit(f"refused directory inside lab package: {path}")
            continue
        if path.is_symlink():
            raise SystemExit(f"symlink not allowed: {path}")
        if path.suffix.lower() not in ALLOWED:
            raise SystemExit(f"member type not allowed: {path}")
        files.append(path)
    if len(files) > 200:
        raise SystemExit(f"too many members ({len(files)}) in {directory}")
    return files


def package(lab: str) -> dict:
    source = EXERCISES / lab
    if not source.is_dir():
        raise SystemExit(f"missing lab directory: {source}")
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    target = DOWNLOADS / f"{lab}.zip"
    files = members(source)
    expanded = 0
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            data = path.read_bytes()
            expanded += len(data)
            info = zipfile.ZipInfo(path.relative_to(source).as_posix(), date_time=FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)
    payload = target.read_bytes()
    if len(payload) > 20 * 1024 * 1024 or expanded > 50 * 1024 * 1024:
        raise SystemExit(f"archive bounds exceeded for {lab}")
    return {
        "lab": lab,
        "path": f"{lab}.zip",
        "bytes": len(payload),
        "expandedBytes": expanded,
        "members": len(files),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def check(lab: str) -> list[str]:
    """Compare a committed ZIP with its source directory, member by member.

    Byte-identical archives are not required (deflate output may differ between
    zlib builds); the member names and every member's bytes must be equal, so a
    stale or hand-edited download cannot pass.
    """
    source = EXERCISES / lab
    target = DOWNLOADS / f"{lab}.zip"
    if not target.exists():
        return [f"{lab}: missing {target.relative_to(ROOT)}"]
    expected = {p.relative_to(source).as_posix(): p.read_bytes() for p in members(source)}
    problems = []
    with zipfile.ZipFile(target) as archive:
        names = [i.filename for i in archive.infolist()]
        if sorted(names) != sorted(expected):
            missing = sorted(set(expected) - set(names))
            extra = sorted(set(names) - set(expected))
            problems.append(f"{lab}: members differ (missing {missing}, extra {extra})")
        for name in set(names) & set(expected):
            if archive.read(name) != expected[name]:
                problems.append(f"{lab}: {name} differs from its source file")
    return problems


def main(argv: list[str]) -> None:
    checking = "--check" in argv
    argv = [a for a in argv if a != "--check"]
    labs = argv or sorted(
        p.name for p in EXERCISES.iterdir() if p.is_dir() and p.name.startswith(("lab-", "capstone-"))
    )
    if checking:
        problems = [problem for lab in labs for problem in check(lab)]
        if problems:
            print("\n".join(problems), file=sys.stderr)
            raise SystemExit(1)
        print(f"PASS: {len(labs)} packages match their source directories member for member")
        return
    results = [package(lab) for lab in labs]
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:])
