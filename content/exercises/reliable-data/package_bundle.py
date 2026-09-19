"""Create the content-managed ZIP from authored sources after a successful run."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parent
ALLOWED = {".md", ".txt", ".json", ".csv", ".py", ".sql", ".toml"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--execution", required=True, type=Path)
    args = parser.parse_args()
    execution = json.loads(args.execution.read_text(encoding="utf-8"))
    if not execution.get("successful") or execution.get("spark") != "4.0.4" or execution.get("skipped") != 0:
        raise ValueError("Packaging requires successful complete pinned local Spark execution")
    for relative, digest in {**execution["input_sha256"], **execution["program_sha256"]}.items():
        if sha256((ROOT / relative).read_bytes()).hexdigest() != digest:
            raise ValueError("Execution source changed; rerun before packaging: " + relative)
    candidates = [ROOT / name for name in ("README.md", "TASKS.md", "SOLUTIONS.md", "requirements.txt",
                  "sources.json", "run_tests.py", "package_bundle.py", "sync_lesson_examples.py")]
    for directory in ("fixtures", "expected", "solutions", "starters", "lesson_examples"):
        candidates.extend((ROOT / directory).rglob("*"))
    files = [(path.relative_to(ROOT).as_posix(), path.read_bytes()) for path in sorted(candidates)
             if path.is_file() and path.suffix in ALLOWED and "__pycache__" not in path.parts]
    files.append(("execution.json", args.execution.read_bytes()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(args.output, "w") as archive:
        for name, data in sorted(files):
            info = ZipInfo(name, date_time=(2026, 9, 19, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    print(json.dumps({"path": args.output.as_posix(), "files": len(files),
                      "bytes": args.output.stat().st_size, "sha256": sha256(args.output.read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
