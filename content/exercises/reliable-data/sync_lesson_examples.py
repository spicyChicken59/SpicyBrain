"""Maintainer helper: copy exact complete displayed examples into the bundle.

Run after editorial changes, then rerun tests and package. The app never runs
this helper or the copied code. Repository-relative metadata avoids local paths.
"""
from hashlib import sha256
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
COURSE = ROOT.parents[1] / "courses" / "dbxfe" / "lessons"
IDS = ["dbxfe-python-bridge", "dbxfe-dataframes", "dbxfe-m04-l01", "dbxfe-grain-joins",
       "dbxfe-versioned-updates", "dbxfe-m04-l03"]
EMBEDS = [
    ("dbxfe-record-resolution", "dbxfe-record-resolution-reference-code", "reference.py", "full", "dbxfe-record-resolution-reference.py"),
    ("dbxfe-record-resolution", "dbxfe-record-resolution-spark-code", "spark_transform.py", "full", "dbxfe-record-resolution-spark.py"),
    ("dbxfe-m04-l03", "dbxfe-m04-l03-pipeline-code", "reference.py", "pipeline_class", "dbxfe-m04-l03-pipeline.py"),
    ("dbxfe-m04-l03", "dbxfe-m04-l03-transfer-code", "transfer.py", "full", "dbxfe-m04-l03-transfer.py"),
]


def source_fragment(filename, fragment):
    text = (ROOT / "solutions" / filename).read_text(encoding="utf-8")
    if fragment == "before_pipeline":
        text = text.split("\nclass LocalPipeline:\n", 1)[0]
    elif fragment == "pipeline_class":
        text = "class LocalPipeline:\n" + text.split("\nclass LocalPipeline:\n", 1)[1].split("\ndef parse_bridge(", 1)[0]
    elif fragment != "full":
        raise ValueError("Unknown source fragment: " + fragment)
    return text.rstrip() + "\n"


def section_text(text, section_id):
    marker = "<!-- section:" + section_id + " -->"
    if text.count(marker) != 1:
        raise ValueError("Expected one stable section marker: " + section_id)
    return text.split(marker, 1)[1].split("<!-- section:", 1)[0]


def sync_embedded_sources():
    for lesson, section_id, filename, fragment, _ in EMBEDS:
        path = COURSE / (lesson + ".md")
        text = path.read_text(encoding="utf-8")
        section = section_text(text, section_id)
        if len(re.findall(r"~~~python\n(.*?)\n~~~", section, re.DOTALL)) != 1:
            raise ValueError("Expected one Python source fence: " + section_id)
        updated = re.sub(r"~~~python\n.*?\n~~~", lambda _: "~~~python\n" + source_fragment(filename, fragment).rstrip() + "\n~~~",
                         section, count=1, flags=re.DOTALL)
        text = text.replace(section, updated, 1)
        path.write_text(text, encoding="utf-8", newline="\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--embed-source", action="store_true", help="Synchronize four stable source sections before regenerating the manifest")
    args = parser.parse_args()
    if args.embed_source:
        sync_embedded_sources()
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
    for lesson, section_id, filename, fragment, output_name in EMBEDS:
        text = (COURSE / (lesson + ".md")).read_text(encoding="utf-8")
        snippet = re.findall(r"~~~python\n(.*?)\n~~~", section_text(text, section_id), re.DOTALL)[0] + "\n"
        if snippet != source_fragment(filename, fragment):
            raise ValueError("Embedded source differs; run --embed-source: " + section_id)
        (destination / output_name).write_text(snippet, encoding="utf-8", newline="\n")
        manifest.append({"lesson_id": lesson, "language": "python", "file": output_name,
                         "selection": "complete source fence in stable section", "section_id": section_id,
                         "source_file": filename, "source_fragment": fragment,
                         "sha256": sha256(snippet.encode()).hexdigest()})
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("Copied", len(manifest), "exact displayed examples")


if __name__ == "__main__":
    main()
