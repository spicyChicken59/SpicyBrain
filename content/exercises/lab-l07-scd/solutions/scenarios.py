"""Drive the reference over the fixtures and print every intermediate output quoted in SOLUTIONS.md.

    python solutions/scenarios.py

Spark's scratch files go to a temporary directory that is deleted at the end.
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True  # leave no __pycache__ inside the package
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from solutions.scd_reference import (  # noqa: E402
    CINDERLINE, MARLOW_COMPOSITE, MARLOW_SINGLE, SUPPLIERS, build_session, check_current_unique,
    check_intervals, load_events, resolve, rows, scd_tables, snapshot_changes)


def show(title, value):
    print(f"\n== {title} ==")
    print(json.dumps(value, indent=1))


def through(events, batch):
    return [e for e in events if e["batch"] <= batch]


def main():
    scratch = tempfile.mkdtemp(prefix="lab-l07-scenarios-")
    spark = build_session("SpicyBrain lab L07 scenarios", scratch)
    try:
        events = load_events("cinderline-events.json")
        for batch in (1, 2, 3):
            resolution = resolve(through(events, batch), CINDERLINE)
            current, history = scd_tables(spark, resolution, CINDERLINE)
            current_rows, history_rows = rows(current, CINDERLINE), rows(history, CINDERLINE)
            check_current_unique(current_rows, "part_id")
            evidence = {k: v for k, v in resolution.items() if k not in ("states", "withheld_states")}
            show(f"cinderline through batch {batch}: evidence", evidence)
            show(f"cinderline through batch {batch}: current (Type 1)", current_rows)
            show(f"cinderline through batch {batch}: history (Type 2)", history_rows)
            show(f"cinderline through batch {batch}: gaps", check_intervals(history_rows, "part_id"))
        marlow = load_events("marlow-events.json")
        for contract in (MARLOW_COMPOSITE, MARLOW_SINGLE):
            resolution = resolve(marlow, contract)
            current, history = scd_tables(spark, resolution, contract)
            show(f"{contract.label}: unresolved", resolution["unresolved"])
            show(f"{contract.label}: current", rows(current, contract))
            show(f"{contract.label}: history", rows(history, contract))
        snapshots = load_events("supplier-snapshots.json")["snapshots"]
        changes = snapshot_changes(snapshots, SUPPLIERS)
        show("supplier snapshots: derived changes", changes)
        _, history = scd_tables(spark, resolve(changes, SUPPLIERS), SUPPLIERS)
        show("supplier snapshots: history", rows(history, SUPPLIERS))
        skipped = snapshot_changes([s for s in snapshots if s["snapshot_no"] != 2], SUPPLIERS)
        _, history = scd_tables(spark, resolve(skipped, SUPPLIERS), SUPPLIERS)
        show("supplier snapshots 1 and 3 only: history", rows(history, SUPPLIERS))
    finally:
        spark.stop()
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    main()
