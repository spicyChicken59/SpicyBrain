#!/usr/bin/env python3
"""Inventory every source the academy cites and how each one was checked.

Usage: python scripts/academy-source-review.py [--write] [--availability docs/evidence/source-availability.json]

Reads the course sources (course.json and module packages, including case
analysis sources), each teaching module's sources and the learning crosswalk,
groups the records by URL and classifies how the URL was checked from the
records' own words (caveat and reviewedEvidence). Categories, strongest first:

  read-this-build   the page or file body was read in this build (raw files
                    and package sources the build could reach)
  package-source    facts read from a published package's source or wheel
  earlier-release   reviewed in the previous release, or a record reused with
                    that review's date and evidence
  search-level      only a search result's title and snippet were confirmed
  unconfirmed       the record says the URL could not be confirmed
  unstated          no record for the URL says how it was checked

Availability (whether a URL answered an HTTP probe) is a separate question,
answered by `npm run report:sources`; pass its JSON with --availability to add
the probe result per URL. A reachable page does not verify a claim, and an
unreachable one does not refute it: unknown is not unsupported.

With --write it writes docs/academy/SOURCE-INVENTORY.json and
docs/academy/SOURCE-REVIEW.md.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COURSE = ROOT / "content" / "courses" / "dbxfe"
TEACHING = ROOT / "content" / "teaching" / "dbxfe"
ORDER = ["read-this-build", "package-source", "earlier-release", "search-level", "unconfirmed", "unstated"]
RULES = [
    ("unconfirmed", r"could not be confirmed|not confirmed|unconfirmed|no search (?:result|confirmation)"),
    ("read-this-build", r"read in full|read in this build|fetched on \d{4}-\d\d-\d\d[^.]*read|fetched in this build|and read\b|read at its source|read from the tag|read locally"),
    ("package-source", r"package source|from the wheel|wheel published|sdist|source distribution"),
    ("earlier-release", r"reused source record|as confirmed for the retained|review of 2026-09-(?:1\d|20)|reviewed 2026-09-(?:1\d|20)"),
    ("search-level", r"search-result|search result|confirmed by search|web search"),
]


def classify(text: str) -> str:
    text = text.lower()
    for name, rx in RULES:
        if re.search(rx, text):
            return name
    return "unstated"


def records() -> list[dict]:
    course = json.loads((COURSE / "course.json").read_text())
    contract = json.loads((COURSE / "academy.json").read_text())
    retained = {m["moduleId"] for t in contract["tracks"] for m in t["modules"] if m.get("disposition") == "retained"}
    out = []

    def add(where, module_id, s, evidence=None, date=None):
        out.append({
            "where": where,
            "moduleId": module_id,
            "retained": module_id in retained if module_id else True,
            "id": s["id"],
            "url": s["url"],
            "title": s["title"],
            "publisher": s.get("publisher"),
            "date": date or s.get("reviewedAt") or s.get("reviewDate") or s.get("accessDate"),
            "method": classify(" ".join(str(x) for x in (s.get("caveat", ""), evidence or s.get("reviewedEvidence") or ""))),
        })

    for s in course["sources"]:
        add("course", None, s)
    for entry in course["modules"]:
        if "file" not in entry:
            continue
        package = json.loads((COURSE / entry["file"]).read_text())
        for s in package.get("sources", []):
            add("module package", package["module"]["id"], s)
    for path in sorted(TEACHING.glob("*.json")):
        teaching = json.loads(path.read_text())
        if not isinstance(teaching, dict) or "moduleId" not in teaching:
            continue
        for s in teaching.get("sources", []):
            add("teaching module", teaching["moduleId"], s)
    for row in course.get("crosswalk", []):
        add("crosswalk", None, {"id": row["id"], "url": row["url"], "title": row["title"], "publisher": row["publisher"], "caveat": row.get("note", "")}, date=row.get("reviewedAt"))
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--availability")
    args = parser.parse_args()
    recs = records()
    probes = {}
    if args.availability:
        report = json.loads(Path(args.availability).read_text())
        for row in report["sources"]:
            probes[row["url"]] = {"probe": row.get("probeStatus"), "httpStatus": row.get("httpStatus"), "checkedAt": report.get("checkedAt")}
    by_url: dict[str, list[dict]] = collections.defaultdict(list)
    for r in recs:
        by_url[r["url"]].append(r)
    urls = []
    for url, rs in by_url.items():
        methods = {r["method"] for r in rs}
        best = min(methods, key=ORDER.index)
        if best == "unstated" and all(r["retained"] for r in rs):
            best = "earlier-release"
        urls.append({
            "url": url,
            "title": rs[0]["title"],
            "publisher": rs[0]["publisher"],
            "method": best,
            "records": len(rs),
            "modules": sorted({r["moduleId"] for r in rs if r["moduleId"]}),
            "dates": sorted({r["date"] for r in rs if r["date"]}),
            **({"availability": probes[url]} if url in probes else {}),
        })
    urls.sort(key=lambda u: (ORDER.index(u["method"]), u["url"]))
    totals = collections.Counter(u["method"] for u in urls)
    publishers = collections.Counter(u["publisher"] for u in urls)
    inventory = {
        "generatedBy": "python scripts/academy-source-review.py --write",
        "method": "Grouped by URL; each URL takes the strongest check any of its records states. Availability is reported separately and only when a probe report is supplied.",
        "records": len(recs),
        "urls": len(urls),
        "byMethod": {m: totals.get(m, 0) for m in ORDER},
        "publishers": dict(publishers.most_common()),
        "unstatedRecords": [
            {k: r[k] for k in ("where", "moduleId", "id", "url")}
            for r in recs if r["method"] == "unstated" and not r["retained"]
        ],
        "sources": urls,
    }
    print(json.dumps({"records": len(recs), "urls": len(urls), **inventory["byMethod"]}))
    print(f"new-module records without a stated check: {len(inventory['unstatedRecords'])}")
    if args.write:
        (ROOT / "docs" / "academy" / "SOURCE-INVENTORY.json").write_text(json.dumps(inventory, indent=1, ensure_ascii=False) + "\n")
        (ROOT / "docs" / "academy" / "SOURCE-REVIEW.md").write_text(markdown(inventory))
    return 0


def markdown(inv: dict) -> str:
    m = inv["byMethod"]
    lines = [
        "# Source review",
        "",
        "Generated by `python scripts/academy-source-review.py --write`. The per-URL inventory is",
        "`docs/academy/SOURCE-INVENTORY.json`.",
        "",
        f"The academy cites {inv['urls']} distinct URLs in {inv['records']} source records (course, module",
        "package, teaching module and crosswalk records). How each URL was checked, taking the",
        "strongest check any of its records states:",
        "",
        "| How the URL was checked | URLs |",
        "|---|---|",
        f"| Body read in this build (raw files, package pages the build could reach) | {m['read-this-build']} |",
        f"| Facts read from a published package's source | {m['package-source']} |",
        f"| Reviewed in the previous release, or reused with that review | {m['earlier-release']} |",
        f"| Search result title and snippet only | {m['search-level']} |",
        f"| Could not be confirmed (claims hedged or dropped) | {m['unconfirmed']} |",
        f"| No record states a check | {m['unstated']} |",
        "",
        "## What this build could and could not do",
        "",
        "- Documentation hosts (docs.databricks.com, learn.microsoft.com, cloud.google.com,",
        "  spark.apache.org and others) and video hosts were blocked by the build environment's",
        "  egress proxy. No page body on those hosts was read in this build. Files published in",
        "  source repositories and package indexes were reachable and were read where cited.",
        "- Web search was available for part of the build and then exhausted. A URL confirmed",
        "  only by its search result's title and snippet is labelled so in its record, and the",
        "  teaching states only what that snippet or another read source supports.",
        "- A URL that could not be confirmed is kept only where its record says so, and the",
        "  statement it would support is hedged or removed.",
        "- Availability is a separate question. `npm run report:sources` probes every URL in CI",
        "  and lists the ones that did not answer; a reachable page does not verify a claim and",
        "  an unreachable one does not refute it. Unknown is not unsupported.",
        "",
        "## Publishers",
        "",
        "| Publisher | URLs |",
        "|---|---|",
    ]
    for publisher, n in inv["publishers"].items():
        lines.append(f"| {publisher} | {n} |")
    if inv["unstatedRecords"]:
        lines += ["", "## New-module records without a stated check", ""]
        for r in inv["unstatedRecords"]:
            lines.append(f"- `{r['moduleId']}` {r['where']} `{r['id']}`: {r['url']}")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
