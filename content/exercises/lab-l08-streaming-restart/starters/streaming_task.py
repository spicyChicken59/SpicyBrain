"""Learner starter for lab L08. Predict first, then run a real streaming query and compare.

Fill PREDICTIONS from TASKS.md before writing code, then close each gap marked
"Gap n". The finished reference is solutions/streaming_restart.py; read
SOLUTIONS.md only after your own attempt.

Run from the lab directory:  python starters/streaming_task.py
It creates a temporary directory for the landing files, the checkpoint and Spark's
own files, and deletes it at the end.
"""
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["PYSPARK_PYTHON"] = sys.executable  # Python workers must match the driver's interpreter
os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")

from pyspark.sql import functions as F  # noqa: E402,F401  (you will need F.window, F.sum, F.count)

from solutions.streaming_restart import (  # noqa: E402  helpers you may reuse; the gaps below are yours
    build_session, checkpoint_logs, land, manifest, read_events, state_rows, window_rows,
)

# Write these down before running anything; each is checkable against Spark's own output.
PREDICTIONS = {
    "watermark_after_first_file": None,           # max event time in 01.json minus 5 minutes
    "windows_emitted_after_first_file": None,     # append mode: how many rows reach the sink?
    "is_e008_counted": None,                      # 09:05:00, read under the 09:07:40 watermark
    "is_e011_counted_one_file_at_a_time": None,   # 09:03:00, arrives in 03.json
    "batch_replayed_after_the_injected_failure": None,
    "naive_outbox_messages_at_the_end": None,
    "keyed_outbox_messages_at_the_end": None,
    "is_e011_counted_as_a_backlog": None,         # all five files present before one availableNow run
}


def windows_with_watermark(events, delay="5 minutes", window="10 minutes"):
    """Gap 1: declare the watermark on event_time, then sum units and count events per (window, line).

    Alias the aggregates "units" and "events". The watermark must be declared on the same
    column the window uses, and before the aggregation, or append mode will refuse the query.
    """
    raise NotImplementedError("Gap 1: withWatermark, then groupBy(window, line).agg(...)")


def start_bounded(frame, checkpoint, sink, timeout_seconds=300):
    """Gap 2: start in append mode with an explicit checkpoint, foreachBatch(sink) and trigger(availableNow=True).

    Wait with awaitTermination(timeout_seconds); if it returns False, stop the query and
    raise. Return the query so the caller can read query.recentProgress. Never sleep.
    """
    raise NotImplementedError("Gap 2: writeStream ... .trigger(availableNow=True).start(), then a bounded wait")


class Outboxes:
    """Downstream stand-ins. naive appends one message per row per call; keyed must not duplicate."""

    def __init__(self):
        self.naive, self.keyed, self.sent_keys, self.fail_on_window = [], [], set(), None

    def __call__(self, batch_df, batch_id):
        rows = window_rows(batch_df)
        for row in rows:
            message = {"batchId": batch_id, "line": row["line"], "window_start": row["window_start"],
                       "units": row["units"]}
            self.naive.append(message)
            # Gap 3: choose an idempotency key that is the same when this batch is replayed;
            # append the message to self.keyed (and the key to self.sent_keys) only if the key is new.
            raise NotImplementedError("Gap 3: an idempotency key for the keyed outbox")
        if self.fail_on_window and any(r["window_start"] == self.fail_on_window for r in rows):
            self.fail_on_window = None
            raise RuntimeError(f"injected failure after downstream effects in batch {batch_id}")


def planned_not_committed(checkpoint):
    """Gap 4: return the batch ids present in the offset log but absent from the commit log."""
    raise NotImplementedError("Gap 4: compare checkpoint_logs(checkpoint)['offsets'] with ['commits']")


def main():
    root = Path(tempfile.mkdtemp(prefix="lab-l08-starter-"))
    spark = build_session("lab L08 starter", root / "local", root / "warehouse")
    spark.sparkContext.setLogLevel("ERROR")
    landing, checkpoint, staging = root / "landing", root / "checkpoint", root / "staging"
    sink = Outboxes()
    try:
        for entry in manifest()["arrivals"]:
            land(entry["file"], landing, staging)
            sink.fail_on_window = "2026-09-14T09:20:00Z" if entry["file"] == "04.json" else None
            for attempt in ("first", "restart"):
                query = None
                try:
                    query = start_bounded(windows_with_watermark(read_events(spark, landing)), checkpoint, sink)
                except Exception as exc:  # the injected failure surfaces here
                    print(f"{entry['file']}: query failed ({type(exc).__name__}); planned, not committed:",
                          planned_not_committed(checkpoint))
                    continue
                for progress in query.recentProgress:
                    print(entry["file"], attempt, "batch", progress.batchId, "rows", progress.numInputRows,
                          "watermark", (progress.eventTime or {}).get("watermark"))
                break
            print("  state now:", state_rows(spark, checkpoint, checkpoint_logs(checkpoint)["commits"][-1]))
        print("naive outbox:", len(sink.naive), "keyed outbox:", len(sink.keyed))
    finally:
        spark.stop()
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    main()
