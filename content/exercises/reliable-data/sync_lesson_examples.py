"""Maintainer helper: copy exact complete displayed examples into the bundle.

Run after editorial changes, then rerun tests and package. The app never runs
this helper or the copied code. Repository-relative metadata avoids local paths.
"""
from hashlib import sha256
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
COURSE = ROOT.parents[1] / "courses" / "dbxfe" / "lessons"
IDS = ["dbxfe-python-bridge", "dbxfe-dataframes", "dbxfe-m04-l01", "dbxfe-grain-joins",
       "dbxfe-versioned-updates", "dbxfe-m04-l03"]


def main():
    destination = ROOT / "lesson_examples"
    destination.mkdir(exist_ok=True)
    manifest = []
    for lesson in IDS:
        text = (COURSE / (lesson + ".md")).read_text(encoding="utf-8")
        snippet = re.findall(r"~~~python\n(.*?)\n~~~", text, re.DOTALL)[0] + "\n"
        (destination / (lesson + ".py")).write_text(snippet, encoding="utf-8", newline="\n")
        manifest.append({"lesson_id": lesson, "language": "python", "file": lesson + ".py",
                         "selection": "first complete Python fence", "sha256": sha256(snippet.encode()).hexdigest()})
    lesson = "dbxfe-grain-joins"
    text = (COURSE / (lesson + ".md")).read_text(encoding="utf-8")
    snippet = re.findall(r"~~~sql\n(.*?)\n~~~", text, re.DOTALL)[0] + "\n"
    (destination / (lesson + ".sql")).write_text(snippet, encoding="utf-8", newline="\n")
    manifest.append({"lesson_id": lesson, "language": "sql", "file": lesson + ".sql",
                     "selection": "existence query; views supplied by test", "sha256": sha256(snippet.encode()).hexdigest()})
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("Copied", len(manifest), "exact displayed examples")


if __name__ == "__main__":
    main()
