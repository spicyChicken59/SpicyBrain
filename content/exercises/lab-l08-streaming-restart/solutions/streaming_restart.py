"""Lab L08 reference solution: a real local Structured Streaming query that restarts.

Local Apache Spark 4.0.4 in local[2] mode with the web UI disabled. Nothing here
imitates streaming with a Python loop over records: fixture files are moved into a
landing directory in a controlled order, and Spark's own file source, watermark,
state store, checkpoint and foreachBatch sink do the work. Every run is bounded:
trigger(availableNow=True) processes what is available and stops by itself, and the
one query with the default trigger is ended with processAllAvailable() and stop().

The downstream "systems" are local stand-ins that append to Python lists and dicts;
nothing leaves the process.
"""
import calendar
import json
import os
import shutil
import sys
import time
from pathlib import Path

from pyspark.errors import StreamingQueryException
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

SCHEMA = "event_id STRING, line STRING, event_time TIMESTAMP, units INT"
SHUFFLE_PARTITIONS = 2
WINDOW = "10 minutes"
DELAY = "5 minutes"
INJECTED = "injected failure after downstream effects"
RUN_TIMEOUT_SECONDS = 300
FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


# --------------------------------------------------------------------- session
def build_session(app_name, local_dir, warehouse_dir):
    """One local Spark session: two cores, no UI, two shuffle partitions, UTC."""
    os.environ["PYSPARK_PYTHON"] = sys.executable
    return (
        SparkSession.builder.master("local[2]")
        .appName(app_name)
        .config("spark.ui.enabled", "false")
        .config("spark.ui.showConsoleProgress", "false")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.sql.shuffle.partitions", str(SHUFFLE_PARTITIONS))
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.local.dir", str(local_dir))
        .config("spark.sql.warehouse.dir", str(warehouse_dir))
        .getOrCreate()
    )


# -------------------------------------------------------------------- fixtures
def manifest():
    return json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))


def landing_time(name):
    for entry in manifest()["arrivals"]:
        if entry["file"] == name:
            return calendar.timegm(time.strptime(entry["landsAt"], "%Y-%m-%dT%H:%M:%SZ"))
    raise KeyError(name)


def land(name, landing_dir, staging_dir):
    """Place one arrival file atomically: copy to staging, stamp its landing time, rename.

    The file source lists the directory and orders new files by modification time,
    and it expects files to appear complete, which a rename within one file system
    guarantees. The modification time is the file's processing-time arrival.
    """
    staging_dir.mkdir(parents=True, exist_ok=True)
    landing_dir.mkdir(parents=True, exist_ok=True)
    staged = staging_dir / name
    shutil.copyfile(FIXTURES / "arrivals" / name, staged)
    stamp = landing_time(name)
    os.utime(staged, (stamp, stamp))
    os.replace(staged, landing_dir / name)


def lines_table(spark):
    rows = json.loads((FIXTURES / "lines.json").read_text(encoding="utf-8"))
    return spark.createDataFrame([(r["line"], r["plant"], r["press"]) for r in rows],
                                 "line STRING, plant STRING, press STRING")


# --------------------------------------------------------------------- queries
def read_events(spark, landing_dir):
    """A streaming DataFrame over the landing directory, at most one new file per micro-batch."""
    return spark.readStream.schema(SCHEMA).option("maxFilesPerTrigger", 1).json(str(landing_dir))


def line_windows(events, delay=DELAY, window=WINDOW):
    """Units and event count per line in tumbling event-time windows, with a watermark."""
    return (events.withWatermark("event_time", delay)
            .groupBy(F.window("event_time", window), "line")
            .agg(F.sum("units").alias("units"), F.count("*").alias("events")))


def line_windows_with_largest(events, delay=DELAY, window=WINDOW):
    """The same aggregation with one more aggregate: a different state schema."""
    return (events.withWatermark("event_time", delay)
            .groupBy(F.window("event_time", window), "line")
            .agg(F.sum("units").alias("units"), F.count("*").alias("events"),
                 F.max("units").alias("largest")))


def line_windows_without_watermark(events, window=WINDOW):
    return (events.groupBy(F.window("event_time", window), "line")
            .agg(F.sum("units").alias("units"), F.count("*").alias("events")))


def enrich(events, lines):
    """Stream-static inner join: stateless, the static side is read for every micro-batch."""
    return events.join(lines, "line")


# ------------------------------------------------------------------------ sink
def iso(moment):
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def window_rows(batch_df):
    """Collect one micro-batch's output (tiny here) into sorted plain dicts."""
    rows = [{"window_start": iso(r["window"]["start"]), "line": r["line"],
             "units": int(r["units"]), "events": int(r["events"])}
            for r in batch_df.collect()]
    return sorted(rows, key=lambda r: (r["window_start"], r["line"]))


class DownstreamStub:
    """Local stand-ins for the systems a foreachBatch function writes to.

    table        an idempotent keyed upsert: (window start, line) -> latest row
    naive_outbox every notification sent, one per emitted row per call (at-least-once)
    keyed_outbox notifications sent only when their idempotency key has not been sent
                 before; sent_keys is the durable record a real outbox would keep
    """

    def __init__(self):
        self.calls = []
        self.table = {}
        self.naive_outbox = []
        self.keyed_outbox = []
        self.sent_keys = set()
        self.fail_on_window = None

    def __call__(self, batch_df, batch_id):
        rows = window_rows(batch_df)  # one action consumes the whole micro-batch
        self.calls.append({"batchId": batch_id, "rows": rows})
        for row in rows:
            key = f"{row['window_start']}|{row['line']}"
            message = {"key": key, "batchId": batch_id,
                       "text": f"{row['line']} made {row['units']} units in the window starting {row['window_start']}"}
            self.table[key] = dict(row)
            self.naive_outbox.append(message)
            if key not in self.sent_keys:
                self.sent_keys.add(key)
                self.keyed_outbox.append(message)
        if self.fail_on_window and any(r["window_start"] == self.fail_on_window for r in rows):
            self.fail_on_window = None  # one-shot: the restarted attempt succeeds
            raise RuntimeError(f"{INJECTED} in batch {batch_id}")

    def table_rows(self):
        return [self.table[k] for k in sorted(self.table)]


# ------------------------------------------------------------------ run control
def _progress(query):
    out = []
    for p in query.recentProgress:
        raw = p.json if isinstance(p.json, str) else p.json()
        d = json.loads(raw)
        ops = d.get("stateOperators") or []
        watermark = (d.get("eventTime") or {}).get("watermark")
        out.append({
            "batchId": d["batchId"],
            "inputRows": d["numInputRows"],
            "watermark": watermark.replace(".000Z", "Z") if watermark else None,
            "stateRows": ops[0]["numRowsTotal"] if ops else None,
            "updated": ops[0]["numRowsUpdated"] if ops else None,
            "removed": ops[0]["numRowsRemoved"] if ops else None,
            "droppedLate": ops[0]["numRowsDroppedByWatermark"] if ops else None,
        })
    return out


def _log_ids(checkpoint, name):
    directory = Path(checkpoint) / name
    if not directory.exists():
        return []
    return sorted(int(p.name) for p in directory.iterdir() if p.name.isdigit())


def checkpoint_logs(checkpoint):
    """Read the offset log, commit log and file-source log a query keeps in its checkpoint."""
    checkpoint = Path(checkpoint)
    offsets, commits = _log_ids(checkpoint, "offsets"), _log_ids(checkpoint, "commits")
    batch_watermark, source_offset, next_watermark, files, shuffle = {}, {}, {}, {}, {}
    for batch in offsets:
        lines = (checkpoint / "offsets" / str(batch)).read_text(encoding="utf-8").splitlines()
        meta = json.loads(lines[1])
        batch_watermark[str(batch)] = iso_ms(meta["batchWatermarkMs"])
        shuffle[str(batch)] = meta["conf"].get("spark.sql.shuffle.partitions")
        source_offset[str(batch)] = json.loads(lines[2])["logOffset"]
    for batch in commits:
        lines = (checkpoint / "commits" / str(batch)).read_text(encoding="utf-8").splitlines()
        next_watermark[str(batch)] = iso_ms(json.loads(lines[1])["nextBatchWatermarkMs"])
    source_log = checkpoint / "sources" / "0"
    if source_log.exists():
        for entry in sorted((p for p in source_log.iterdir() if p.name.isdigit()), key=lambda p: int(p.name)):
            names = [Path(json.loads(line)["path"]).name
                     for line in entry.read_text(encoding="utf-8").splitlines()[1:] if line.strip()]
            files[entry.name] = names
    state_dir = checkpoint / "state" / "0"
    partitions = sorted(p.name for p in state_dir.iterdir() if p.name.isdigit()) if state_dir.exists() else []
    return {"offsets": offsets, "commits": commits, "batchWatermark": batch_watermark,
            "batchSourceOffset": source_offset, "nextBatchWatermark": next_watermark,
            "sourceFiles": files, "shufflePartitions": shuffle, "statePartitions": partitions}


def iso_ms(millis):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(millis / 1000))


def run_available_now(frame, checkpoint, sink):
    """Start, let availableNow drain what is present, and return what Spark reported.

    Returns (executed batches, error, trigger reports that planned no batch). A batch
    counts as executed in this run when its id is in the offset log afterwards and was
    not committed before the run started; the replay of a planned-but-uncommitted batch
    therefore counts, and a progress report with nothing planned does not.
    """
    committed_before = set(_log_ids(checkpoint, "commits"))
    query = (frame.writeStream.outputMode("append")
             .option("checkpointLocation", str(checkpoint))
             .foreachBatch(sink)
             .trigger(availableNow=True)
             .start())
    error = None
    try:
        if not query.awaitTermination(RUN_TIMEOUT_SECONDS):
            query.stop()
            raise TimeoutError("availableNow run did not terminate within the bound")
    except StreamingQueryException as exc:
        error = exc
    finally:
        query.stop()  # already terminated; stop() is idempotent and releases resources
    planned = set(_log_ids(checkpoint, "offsets"))
    reported = _progress(query)
    executed = [p for p in reported if p["batchId"] in planned and p["batchId"] not in committed_before]
    idle = [p for p in reported if p not in executed]
    return executed, error, idle


def run_until_idle_then_stop(frame, output_dir, checkpoint):
    """Default trigger (a new micro-batch as soon as the previous one ends) into a Parquet file sink.

    processAllAvailable() blocks until everything present has been processed and
    committed; stop() then ends the query. Returns (committed batches, still active?).
    """
    committed_before = set(_log_ids(checkpoint, "commits"))
    query = (frame.writeStream.format("parquet")
             .option("path", str(output_dir))
             .option("checkpointLocation", str(checkpoint))
             .start())
    query.processAllAvailable()
    reported = _progress(query)
    query.stop()
    committed = set(_log_ids(checkpoint, "commits")) - committed_before
    batches = [{"batchId": p["batchId"], "inputRows": p["inputRows"]}
               for p in reported if p["batchId"] in committed]
    return batches, query.isActive


def state_rows(spark, checkpoint, batch_id):
    """The aggregation state as of a committed batch, read with the (experimental) state data source."""
    frame = spark.read.format("statestore").option("batchId", batch_id).load(str(checkpoint))
    rows = [{"window_start": iso(r["key"]["window"]["start"]), "line": r["key"]["line"],
             "units": int(r["value"]["sum"]), "events": int(r["value"]["count"])}
            for r in frame.collect()]
    return sorted(rows, key=lambda r: (r["window_start"], r["line"]))


# ------------------------------------------------------------ batch comparisons
def _window_totals(frame, column, size, slide=None):
    window = F.window(column, size, slide) if slide else F.window(column, size)
    rows = (frame.groupBy(window.start.alias("start"), "line")
            .agg(F.sum("units").alias("units"), F.count("*").alias("events"))
            .collect())
    out = [{"window_start": iso(r["start"]), "line": r["line"], "units": int(r["units"]),
            "events": int(r["events"])} for r in rows]
    return sorted(out, key=lambda r: (r["window_start"], r["line"]))


def batch_windows(spark, landing_dir):
    """Batch (not streaming) reads of every landed file: event-time, processing-time and sliding windows.

    Processing time is the file's landing time, exposed by the file source's hidden
    _metadata.file_modification_time column.
    """
    events = (spark.read.schema(SCHEMA).json(str(landing_dir))
              .select("*", F.col("_metadata.file_modification_time").alias("landed_at")))
    return {
        "eventTimeTumbling": _window_totals(events, "event_time", WINDOW),
        "processingTimeTumbling": _window_totals(events, "landed_at", WINDOW),
        "sliding": _window_totals(events, "event_time", WINDOW, "5 minutes"),
    }
