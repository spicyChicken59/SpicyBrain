"""Drive the UNCHANGED reference resolver through every scenario of both plants.

This file adds no policy. It only assembles fixture histories, calls
solutions/reference.py (a byte-for-byte copy of the original Cinderline
resolver) and reports what it returned, so SOLUTIONS.md and run_tests.py read
the same observations. Everything is in-memory Python; nothing is sent.
"""
from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from solutions.reference import LocalPipeline, resolve  # noqa: E402

PLANTS = {
    "cinderline": {"baseline": "fixtures/cinderline-baseline.json", "batches": "fixtures/cinderline-batches.json",
                   "unkeyed": "fixtures/cinderline-unkeyed.json"},
    "northgate": {"baseline": "fixtures/northgate-baseline.json", "batches": "fixtures/northgate-batches.json",
                  "unkeyed": "fixtures/northgate-unkeyed.json"},
}
BUSINESS_FIELDS = ("accepted", "totals", "excluded_keys", "unresolved", "publication_allowed")


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def fixtures(plant):
    paths = PLANTS[plant]
    return load(paths["baseline"]), load(paths["batches"]), load(paths["unkeyed"])


def business(result):
    """The five fields a reader compares; conflicts and quarantine are read separately."""
    return {field: result[field] for field in BUSINESS_FIELDS}


def quarantine_view(result):
    return [{"raw_index": item["raw_index"], "inspection_id": item["row"].get("inspection_id"),
             "reasons": item["reasons"]} for item in result["quarantine"]]


def observation(pipe):
    return {"status": pipe.status, "raw_count": len(pipe.raw), "local_effect_count": len(pipe.outbox),
            "published_totals": None if pipe.published is None else pipe.published["totals"],
            "candidate_totals": pipe.resolved["totals"], "unresolved": pipe.resolved["unresolved"],
            "conflicts": pipe.resolved["conflicts"], "publication_allowed": pipe.resolved["publication_allowed"]}


def resolution_scenarios(plant):
    base, batches, unkeyed = fixtures(plant)
    histories = {
        "baseline": base, "replay": base + base, "late": base + batches["late"],
        "correction": base + batches["correction"], "correction_replay": base + batches["correction"] * 2,
        "event_conflict": base + batches["event_conflict"], "version_conflict": base + batches["version_conflict"],
        "version_conflict_reversed": list(reversed(base + batches["version_conflict"])),
        "invalid_latest": base + batches["invalid_latest"], "missing_order": base + batches["missing_order"],
        "invalid_only": batches["invalid"], "unkeyed_first_run": unkeyed,
    }
    return {name: {"business": business(result), "conflicts": result["conflicts"],
                   "quarantine": quarantine_view(result), "raw_count": result["raw_count"]}
            for name, result in ((name, resolve(history)) for name, history in histories.items())}


def pipeline_scenarios(plant):
    base, batches, unkeyed = fixtures(plant)
    out = {}
    pipe = LocalPipeline()
    pipe.ingest(base)
    out["baseline"] = observation(pipe)
    pipe.ingest(base)
    out["replay"] = observation(pipe)
    pipe = LocalPipeline()
    pipe.ingest(base)
    pipe.ingest(batches["late"])
    out["late"] = observation(pipe)
    pipe = LocalPipeline()
    pipe.ingest(base)
    pipe.ingest(batches["correction"])
    out["correction"] = observation(pipe)
    pipe.ingest(batches["correction"])
    out["correction_replay"] = observation(pipe)
    for name in ("event_conflict", "invalid_latest"):
        pipe = LocalPipeline()
        pipe.ingest(base)
        pipe.ingest(batches[name])
        out[name + "_after_baseline"] = observation(pipe)
    pipe = LocalPipeline()
    pipe.ingest(base + batches["version_conflict"])
    out["first_run_conflict"] = {**observation(pipe), "published": pipe.published}
    pipe = LocalPipeline()
    pipe.ingest(unkeyed)
    out["unkeyed_first_run"] = {**observation(pipe), "published": pipe.published, "accepted": pipe.resolved["accepted"]}
    pipe = LocalPipeline()
    pipe.ingest(base)
    previous = deepcopy(pipe.published)
    pipe.ingest([unkeyed[0]])
    pipe.ingest([unkeyed[1]] + batches["correction"])
    out["unkeyed_cross_batch"] = {**observation(pipe), "accepted_candidate": pipe.resolved["accepted"],
                                  "previous_published_totals": previous["totals"],
                                  "snapshot_unchanged": pipe.published == previous}
    pipe = LocalPipeline()
    pipe.ingest(base)
    try:
        pipe.ingest(batches["correction"], fail_after="retained_raw")
    except RuntimeError as error:
        failure = str(error)
    before = observation(pipe)
    pipe.recover()
    out["failure_after_retained_raw"] = {"injected": failure, "before_recovery": before, "after_recovery": observation(pipe)}
    pipe = LocalPipeline()
    pipe.ingest(base)
    try:
        pipe.ingest(batches["correction"], fail_after="published_snapshot")
    except RuntimeError as error:
        failure = str(error)
    before = observation(pipe)
    pipe.recover()
    pipe.recover()
    out["failure_after_published_snapshot"] = {"injected": failure, "before_recovery": before, "after_two_recoveries": observation(pipe)}
    pipe = LocalPipeline()
    pipe.ingest(batches["invalid"])
    out["invalid_only_first_run"] = observation(pipe)
    return out


def main():
    report = {plant: {"resolution": resolution_scenarios(plant), "pipeline": pipeline_scenarios(plant)} for plant in PLANTS}
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
