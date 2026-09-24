#!/usr/bin/env python3
"""Compile the academy media review from the records the course already keeps.

Usage: python scripts/academy-media-review.py [--write]

Inputs: content/teaching/dbxfe/media.json (the reviewed video placements the
course renders) and docs/academy/media-decisions/<module>.json (one decision
per new module). The script fails when a registered module that is not in the
retained baseline has no decision, when a decision says "no-placement" but the
course renders a placement for that module, when a listed candidate claims to
have been reviewed, or when a rendered placement lacks its review record.

With --write it writes docs/academy/MEDIA-DECISIONS.json (the machine-readable
register) and docs/academy/MEDIA-REVIEW.md. A candidate in a decision is a
lead for a later reviewer: it was not watched, its captions were not read and
it is never shown to learners.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COURSE = ROOT / "content" / "courses" / "dbxfe"
MEDIA = ROOT / "content" / "teaching" / "dbxfe" / "media.json"
DECISIONS = ROOT / "docs" / "academy" / "media-decisions"
PLACEMENT_FIELDS = ("reviewedAt", "reviewMethod", "reviewedEvidence", "playbackStatus", "embeddingStatus", "fallback")


def registered_modules() -> list[str]:
    course = json.loads((COURSE / "course.json").read_text())
    out = []
    for entry in course["modules"]:
        module = json.loads((COURSE / entry["file"]).read_text())["module"] if "file" in entry else entry
        out.append(module["id"])
    return out


def retained_modules() -> set[str]:
    contract = json.loads((COURSE / "academy.json").read_text())
    return {m["moduleId"] for t in contract["tracks"] for m in t["modules"] if m.get("disposition") == "retained"}


def main(argv: list[str]) -> int:
    placements = json.loads(MEDIA.read_text())
    decisions = {p.stem: json.loads(p.read_text()) for p in sorted(DECISIONS.glob("*.json"))}
    modules = registered_modules()
    retained = retained_modules()
    problems: list[str] = []
    placed = {p["moduleId"] for p in placements}
    for p in placements:
        missing = [f for f in PLACEMENT_FIELDS if not p.get(f)]
        if missing:
            problems.append(f"placement {p['id']} lacks {', '.join(missing)}")
        if p["moduleId"] not in modules:
            problems.append(f"placement {p['id']} belongs to unregistered module {p['moduleId']}")
    for mid in modules:
        if mid in retained:
            continue
        d = decisions.get(mid)
        if not d:
            problems.append(f"new module {mid} has no media decision")
            continue
        if d["decision"] in ("no-placement", "blocked-review") and mid in placed:
            problems.append(f"{mid}: decision forbids placement but the course renders a placement")
        if d["decision"] not in ("no-placement", "blocked-review"):
            problems.append(f"{mid}: unrecognized media decision")
        if d["decision"] == "no-placement" and not d.get("editorialEvidence"):
            problems.append(f"{mid}: no-placement needs completed editorial evidence; access failure is blocked-review")
        for c in d.get("candidates", []):
            if c.get("reviewed") is not False:
                problems.append(f"{mid}: candidate {c.get('url')} is not marked reviewed: false")
    for mid in decisions:
        if mid not in modules:
            problems.append(f"decision for unregistered module {mid}")
    register = {
        "generatedBy": "python scripts/academy-media-review.py --write",
        "rule": "A placement is shown only after its segment was reviewed and its playback probed; every new-module candidate is an unreviewed lead and is never rendered.",
        "placements": [
            {k: p.get(k) for k in ("id", "moduleId", "beatId", "title", "publisher", "url", "publishedAt", "reviewedAt", "reviewMethod", "startSeconds", "endSeconds", "embeddingStatus")}
            for p in placements
        ],
        "decisions": [
            {
                "moduleId": mid,
                "decision": d["decision"],
                "date": d.get("date"),
                "suggestedBeatId": d.get("suggestedBeatId"),
                "reason": d.get("reason"),
                "remainingReview": d.get("remainingReview"),
                "candidates": [{k: c.get(k) for k in ("title", "creator", "url", "foundVia", "reviewed")} for c in d.get("candidates", [])],
            }
            for mid, d in sorted(decisions.items(), key=lambda kv: modules.index(kv[0]) if kv[0] in modules else 999)
        ],
        "totals": {
            "registeredModules": len(modules),
            "retainedModulesWithPlacement": len(placed),
            "placements": len(placements),
            "newModuleDecisions": len(decisions),
            "noPlacement": sum(1 for d in decisions.values() if d["decision"] == "no-placement"),
            "blockedReview": sum(1 for d in decisions.values() if d["decision"] == "blocked-review"),
            "unreviewedCandidates": sum(len(d.get("candidates", [])) for d in decisions.values()),
        },
        "problems": problems,
    }
    print(json.dumps(register["totals"]), f"problems: {len(problems)}")
    for p in problems:
        print("PROBLEM:", p)
    if "--write" in argv:
        (ROOT / "docs" / "academy" / "MEDIA-DECISIONS.json").write_text(json.dumps(register, indent=1, ensure_ascii=False) + "\n")
        (ROOT / "docs" / "academy" / "MEDIA-REVIEW.md").write_text(markdown(register, placements))
    return 1 if problems else 0


def markdown(register: dict, placements: list[dict]) -> str:
    t = register["totals"]
    lines = [
        "# Media review",
        "",
        "Generated by `python scripts/academy-media-review.py --write` from",
        "`content/teaching/dbxfe/media.json` and `docs/academy/media-decisions/`.",
        "",
        f"- {t['placements']} video placements are rendered, one in each of {t['retainedModulesWithPlacement']} retained modules. Each segment was",
        "  reviewed (video and transcript, or transcript where stated) and its playback probed",
        "  in the privacy-enhanced player after explicit consent, on the dates below.",
        f"- {t['newModuleDecisions']} new modules have records: {t['blockedReview']} are `blocked-review`,",
        f"  and {t['noPlacement']} have a completed `no-placement` decision. The {t['unreviewedCandidates']}",
        "  candidates remain unreviewed leads and are never shown to learners.",
        "- G10 remains BLOCKED until candidate evaluation is complete. An optional placement",
        "  and a complete authored visual do not substitute for the required editorial review.",
        "- Access attempts and exact outstanding methods are recorded in CLOSEOUT.md.",
        "",
        "Behaviour the browser suite proves for every placement: no provider request before",
        "consent, the original link and the authored equivalent when the player is blocked,",
        "no autoplay, and malformed media metadata never blanking a beat",
        "(`tests/browser/teacher-first.spec.ts`, `tests/browser/teacher-safety.spec.ts`).",
        "",
        "## Rendered placements (retained modules)",
        "",
        "| Module | Beat | Title | Publisher | Segment | Reviewed | Method | Embedding |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for p in placements:
        seg = f"{p.get('startSeconds', 0)}–{p.get('endSeconds', '')} s"
        lines.append(f"| `{p['moduleId']}` | `{p['beatId']}` | {p['title']} | {p['publisher']} | {seg} | {p['reviewedAt']} | {p['reviewMethod']} | {p['embeddingStatus']} |")
    lines += ["", "## Decisions for new modules", "", "| Module | Decision | Suggested beat | Unreviewed candidates |", "|---|---|---|---|"]
    for d in register["decisions"]:
        lines.append(f"| `{d['moduleId']}` | {d['decision']} | {('`' + d['suggestedBeatId'] + '`') if d.get('suggestedBeatId') else '—'} | {len(d['candidates'])} |")
    lines += ["", "Each decision's reason and candidate list are in `docs/academy/MEDIA-DECISIONS.json`.", ""]
    if register["problems"]:
        lines += ["## Problems", ""] + [f"- {p}" for p in register["problems"]] + [""]
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
