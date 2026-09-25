"""Learner starter for lab L05. Predict first, then run and compare.

Fill PREDICTIONS from TASKS.md before writing code, then complete the five functions marked
"Task". The reference answers are in solutions/delta_sequence.py; open SOLUTIONS.md only after
your own attempt. The helpers imported below (session, fixtures, reading snapshots, history,
detail) are given so that your effort goes into the write semantics, not the plumbing.

Run from the lab directory:  python starters/delta_sequence_task.py

Safety: do not add any setting that disables Delta's retention check, and do not run VACUUM
without DRY RUN in this lab. Nothing in the tasks needs either.
"""
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["PYSPARK_PYTHON"] = sys.executable  # Python workers must use the driver's interpreter
os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")

from solutions.delta_sequence import (  # noqa: E402  given helpers: session, fixtures, reading evidence
    CORRECTION, batch, build_session, change_feed, correct_inspected, current_version, delta_table, detail,
    enable_change_feed, history, ref, snapshot, totals, write_initial,
)

# Write these before running anything. Each one is checkable against Delta's own output.
PREDICTIONS = {
    "total_inspected_at_version_2": None,          # after writing A (10), appending C (8), correcting A to 12
    "rows_after_day2_merge": None,                  # A is absent from the day-2 delivery: 2, 3 or 4 rows?
    "naive_day3_merge_outcome": None,               # "commits", "refused" or "keeps one D row"?
    "revision_of_A_after_guarded_day3": None,       # day 3 replays A with revision 0
    "rows_deleted_by_the_south_snapshot": None,     # scoped to plant South
    "rows_deleted_if_the_delete_clause_were_unscoped": None,
    "append_with_a_new_column_without_mergeSchema": None,  # "adds the column", "drops it" or "refused"?
    "rows_changed_by_optimize": None,
}


def merge_incremental(spark, path, source):
    """Task 2: MERGE the source on inspection_id: update matched rows, insert unseen keys, and nothing else.
    Explain in a comment why the key that is missing from the source must survive."""
    raise NotImplementedError("Task 2: write the incremental MERGE (two clauses, no delete clause)")


def dedupe_latest_revision(source):
    """Task 3: return one row per inspection_id, the one with the highest revision."""
    raise NotImplementedError("Task 3: keep the latest revision per key before merging")


def merge_guarded(spark, path, source):
    """Task 3: update a matched row only when the source revision is newer; insert unseen keys."""
    raise NotImplementedError("Task 3: add the revision guard to the matched clause")


def merge_full_snapshot(spark, path, source, plant):
    """Task 4: the source is a COMPLETE snapshot of one plant. Delete target rows of that plant that the
    snapshot no longer lists, and leave every other plant alone."""
    raise NotImplementedError("Task 4: add a NOT MATCHED BY SOURCE clause scoped to the snapshot's plant")


def append_with_new_column(spark, path, name):
    """Task 5: append a batch that carries a column the table lacks, evolving the schema explicitly for
    this one write only. First try it without evolution and read the error."""
    raise NotImplementedError("Task 5: append with the mergeSchema write option")


if __name__ == "__main__":
    scratch = Path(tempfile.mkdtemp(prefix="lab-l05-learner-"))
    spark, resolution = build_session("SpicyBrain lab L05 learner", local_dir=scratch / "local",
                                      warehouse_dir=scratch / "warehouse")
    spark.sparkContext.setLogLevel("ERROR")
    print("Delta jars:", resolution["method"], sorted(resolution["resolvedJars"]))
    table = scratch / "inspections"
    try:
        write_initial(spark, table)                                     # version 0
        batch(spark, "append_c.json").write.format("delta").mode("append").save(str(table))  # version 1
        correct_inspected(spark, table, "A", CORRECTION)                 # version 2
        for v in range(3):
            print(f"version {v}:", totals(snapshot(spark, table, v)))
        enable_change_feed(spark, table)                                 # version 3
        merge_incremental(spark, table, batch(spark, "incremental_day2.json"))  # version 4
        print("after day 2:", snapshot(spark, table))
        merge_guarded(spark, table, dedupe_latest_revision(batch(spark, "incremental_day3.json")))  # version 5
        merge_full_snapshot(spark, table, batch(spark, "snapshot_south.json"), "South")  # version 6
        print("changes 4..6:", change_feed(spark, table, 4, 6))
        append_with_new_column(spark, table, "append_f_inspector.json")  # version 7
        print("detail:", detail(spark, table))
        print("history:", [(h["version"], h["operation"]) for h in history(spark, table)])
        print("current version:", current_version(spark, table))
        print("compare with PREDICTIONS, then with expected/snapshots.json")
    finally:
        spark.stop()
        shutil.rmtree(scratch, ignore_errors=True)
