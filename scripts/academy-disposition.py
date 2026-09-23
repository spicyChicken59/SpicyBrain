#!/usr/bin/env python3
"""Compare every retained identity with the base release; write DISPOSITION.json.

Usage: python scripts/academy-disposition.py [--base <commit>] [--check]

For each module the academy contract marks "retained", the base release's
lessons, sections, cards, questions and options, teaching beats, visuals and
visual states, checks, extension cards, card links, concepts, sources and
claims are compared with the working tree by identity. An identity is
"removed" when it is gone, "revised" when it still exists but its content
changed (with its revision/version before and after), "unchanged" otherwise,
and "added" when new. Course-level scenarios (with rubric, disclosure and
requirement ids), concepts, sources, claims, assets and downloads are compared
the same way. New modules are listed with their counts.

Following docs/AUTHORING.md, a card, question or check whose assessed meaning
changed (prompt, answer, options, correct option, model answer) must carry a new
revision, while a clarified explanation keeps it; a beat whose teaching changed
must carry a new version, so a completed beat shows as revised. --check fails on
a removal or on a change whose revision/version did not move as required. The
result is written to docs/academy/DISPOSITION.json.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COURSE = "content/courses/dbxfe"
TEACHING = "content/teaching/dbxfe"
DEFAULT_BASE = "2cde73d902b296ca4bae13dcc31ff6f6ace9e917"
SECTION = re.compile(r"<!--\s*section:([a-z0-9-]+)\s*-->")


def at_base(base: str, path: str):
    result = subprocess.run(
        ["git", "show", f"{base}:{path}"], cwd=ROOT, capture_output=True, text=True
    )
    return result.stdout if result.returncode == 0 else None


def now(path: str):
    p = ROOT / path
    return p.read_text() if p.exists() else None


def canon(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def module_entries(course: dict, read) -> dict[str, dict]:
    """Module map entries by id, resolving package references."""
    out = {}
    for entry in course["modules"]:
        if "file" in entry:
            package = json.loads(read(f"{COURSE}/{entry['file']}"))
            out[package["module"]["id"]] = package["module"]
        else:
            out[entry["id"]] = entry
    return out


def course_scenarios(course: dict, read) -> dict[str, dict]:
    scenarios = {s["id"]: s for s in course["scenarios"]}
    for entry in course["modules"]:
        if "file" in entry:
            package = json.loads(read(f"{COURSE}/{entry['file']}"))
            for s in package.get("scenarios", []):
                scenarios[s["id"]] = s
    return scenarios


def lesson_family(module: dict, read) -> dict[str, dict]:
    """Identity -> (kind, revision, canonical content) for a module's lessons."""
    ids: dict[str, dict] = {}
    for lesson_file in module.get("lessonFiles", []):
        text = read(f"{COURSE}/{lesson_file}")
        if text is None:
            continue
        lesson = json.loads(text)
        body = read(f"{COURSE}/{Path(lesson_file).parent}/{lesson['bodyFile']}") or ""
        ids[f"lesson:{lesson['id']}"] = {"revision": lesson.get("contentVersion"), "content": canon({k: v for k, v in lesson.items() if k not in ("sections", "questions", "cards")})}
        bodies = {}
        parts = SECTION.split(body)
        for i in range(1, len(parts), 2):
            bodies[parts[i]] = parts[i + 1].strip()
        for s in lesson.get("sections", []):
            ids[f"section:{s['id']}"] = {"revision": None, "content": canon([s, bodies.get(s["id"], "")])}
        for q in lesson.get("questions", []):
            ids[f"question:{q['id']}"] = {"revision": q.get("revision"), "content": canon(q)}
            for o in q.get("options", []):
                ids[f"option:{q['id']}/{o['id']}"] = {"revision": q.get("revision"), "content": canon(o)}
        for c in lesson.get("cards", []):
            ids[f"card:{c['id']}"] = {"revision": c.get("revision"), "content": canon(c)}
    return ids


def teaching_family(text: str | None) -> dict[str, dict]:
    ids: dict[str, dict] = {}
    if text is None:
        return ids
    t = json.loads(text)
    for b in t["beats"]:
        ids[f"beat:{b['id']}"] = {"revision": b.get("version"), "content": canon(b)}
    for v in t["visuals"]:
        ids[f"visual:{v['id']}"] = {"revision": None, "content": canon({k: x for k, x in v.items() if k != "states"})}
        for s in v["states"]:
            ids[f"visual-state:{v['id']}/{s['id']}"] = {"revision": None, "content": canon(s)}
    for q in t.get("questions", []):
        ids[f"beat-check:{q['id']}"] = {"revision": q.get("revision"), "content": canon(q)}
        for o in q.get("options", []):
            ids[f"beat-check-option:{q['id']}/{o['id']}"] = {"revision": q.get("revision"), "content": canon(o)}
    for q in t.get("selfQuestions", []):
        ids[f"self-check:{q['id']}"] = {"revision": q.get("revision"), "content": canon(q)}
    for c in t.get("extensionCards", []):
        ids[f"extension-card:{c['id']}"] = {"revision": c.get("revision"), "content": canon(c)}
    for link in t.get("cardLinks", []):
        ids[f"card-link:{link['cardId']}"] = {"revision": None, "content": canon(link)}
    for kind in ("concepts", "sources", "claims"):
        for x in t.get(kind, []):
            ids[f"teaching-{kind[:-1]}:{x['id']}"] = {"revision": None, "content": canon(x)}
    ids[f"recap:{t['moduleId']}"] = {"revision": None, "content": canon(t.get("recap"))}
    ids[f"applied-task:{t['moduleId']}"] = {"revision": None, "content": canon(t.get("appliedTask"))}
    return ids


# docs/AUTHORING.md: a card/question revision moves when the assessed meaning
# changes; a clarified explanation keeps it. A beat version moves for any
# material teaching change.
ASSESSED = {
    "card": ("prompt", "answer"),
    "extension-card": ("prompt", "answer"),
    "question": ("prompt", "options", "correctOptionId"),
    "beat-check": ("prompt", "options", "correctOptionId"),
    "self-check": ("prompt", "modelAnswer"),
}
BEAT_TEACHING = ("title", "outcome", "explanation", "visualId", "questionIds", "handbook", "samajh", "recap", "hint")


def compare(before: dict[str, dict], after: dict[str, dict]):
    removed = sorted(set(before) - set(after))
    added = sorted(set(after) - set(before))
    revised, unmoved = [], []
    for key in sorted(set(before) & set(after)):
        if before[key]["content"] == after[key]["content"]:
            continue
        b, a = json.loads(before[key]["content"]), json.loads(after[key]["content"])
        fields = sorted(k for k in set(a) | set(b) if isinstance(a, dict) and isinstance(b, dict) and a.get(k) != b.get(k))
        moved = before[key]["revision"] != after[key]["revision"]
        kind = key.split(":", 1)[0]
        revised.append({"id": key, "fields": fields, "before": before[key]["revision"], "after": after[key]["revision"]})
        if kind in ASSESSED and not moved and any(f in ASSESSED[kind] for f in fields):
            unmoved.append(key)
        if kind == "beat" and not moved and any(f in BEAT_TEACHING for f in fields):
            unmoved.append(key)
    unchanged = len(set(before) & set(after)) - len(revised)
    return {"removed": removed, "added": added, "revised": revised, "unchanged": unchanged, "revisionNotMoved": unmoved}


def main(argv: list[str]) -> int:
    base = argv[argv.index("--base") + 1] if "--base" in argv else DEFAULT_BASE
    checking = "--check" in argv
    contract = json.loads(now(f"{COURSE}/academy.json"))
    base_course = json.loads(at_base(base, f"{COURSE}/course.json"))
    now_course = json.loads(now(f"{COURSE}/course.json"))
    base_modules = module_entries(base_course, lambda p: at_base(base, p))
    now_modules = module_entries(now_course, now)
    retained, new, problems = [], [], []
    for track in contract["tracks"]:
        for m in track["modules"]:
            mid = m["moduleId"]
            if m["disposition"] == "retained":
                before = {**lesson_family(base_modules[mid], lambda p: at_base(base, p)), **teaching_family(at_base(base, f"{TEACHING}/{mid}.json"))}
                after = {**lesson_family(now_modules.get(mid, {}), now), **teaching_family(now(f"{TEACHING}/{mid}.json"))}
                result = compare(before, after)
                retained.append({"label": m["label"], "moduleId": mid, "track": track["id"], "identities": len(before), **result})
                problems += [f"{mid}: removed {x}" for x in result["removed"]]
                problems += [f"{mid}: {x} changed without a revision/version change" for x in result["revisionNotMoved"]]
            else:
                t = now(f"{TEACHING}/{mid}.json")
                registered = mid in now_modules
                entry = {"label": m["label"], "moduleId": mid, "track": track["id"], "registered": registered}
                if t:
                    tm = json.loads(t)
                    entry.update(beats=len(tm["beats"]), coreCards=len(tm["cardLinks"]), extensionCards=len(tm["extensionCards"]), lessons=len(tm["lessonIds"]))
                new.append(entry)
    course_level = {}
    for kind in ("concepts", "sources", "claims", "assets", "downloads"):
        before = {x["id"]: {"revision": None, "content": canon(x)} for x in base_course.get(kind, [])}
        after = {x["id"]: {"revision": None, "content": canon(x)} for x in now_course.get(kind, [])}
        course_level[kind] = compare(before, after)
        problems += [f"course {kind}: removed {x}" for x in course_level[kind]["removed"]]
    scen_before = course_scenarios(base_course, lambda p: at_base(base, p))
    scen_after = course_scenarios(now_course, now)
    def scenario_ids(scenarios):
        ids = {}
        for s in scenarios.values():
            ids[f"scenario:{s['id']}"] = {"revision": None, "content": canon(s)}
            for kind in ("rubric", "disclosures", "requirements"):
                for x in s.get(kind, []) or []:
                    if isinstance(x, dict) and "id" in x:
                        ids[f"scenario-{kind}:{s['id']}/{x['id']}"] = {"revision": None, "content": canon(x)}
        return ids
    course_level["scenarios"] = compare(scenario_ids(scen_before), scenario_ids(scen_after))
    problems += [f"scenarios: removed {x}" for x in course_level["scenarios"]["removed"]]
    report = {
        "base": base,
        "generatedBy": "python scripts/academy-disposition.py",
        "rule": "Retained identities are never removed. A card, question, check or extension card whose assessed meaning (prompt, answer, options, correct option, model answer) changed carries a new revision; one whose explanation was only clarified keeps its revision, so history and schedules stay valid. A beat whose teaching (explanation, visual, check, handbook, Samajh, recap, hint) changed carries a new version, so a completed beat shows as revised.",
        "summary": {
            "retainedModules": len(retained),
            "retainedIdentities": sum(r["identities"] for r in retained),
            "removed": sum(len(r["removed"]) for r in retained),
            "revised": sum(len(r["revised"]) for r in retained),
            "added": sum(len(r["added"]) for r in retained),
            "revisionNotMoved": sum(len(r["revisionNotMoved"]) for r in retained),
            "clarifiedWithRevisionKept": sum(1 for r in retained for x in r["revised"] if x["before"] == x["after"] and x["id"].split(":", 1)[0] in ASSESSED),
            "newModules": len(new),
            "newModulesRegistered": sum(1 for n in new if n["registered"]),
        },
        "retained": retained,
        "new": new,
        "courseLevel": course_level,
    }
    out = ROOT / "docs" / "academy" / "DISPOSITION.json"
    out.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps(report["summary"]))
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1 if checking else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
