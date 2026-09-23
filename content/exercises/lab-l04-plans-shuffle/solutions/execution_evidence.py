"""Reference solution for lab L04: read local Spark plans and measured runtime evidence.

Everything here runs on local Apache Spark 4.0.4 in local[2] mode on one machine.
Nothing is a benchmark. The evidence is operator structure (what Spark plans),
partition membership (where rows land), stage/task counts and shuffle records
(what Spark ran), all read from Spark itself rather than asserted from memory.
"""
import io
import itertools
import json
import re
import time
from contextlib import redirect_stdout
from pathlib import Path

from pyspark.sql import SparkSession, Window, functions as F, types as T

ROOT = Path(__file__).resolve().parents[1]
INPUT_PARTITIONS = 4      # the fixture is parallelised into four input partitions
SHUFFLE_PARTITIONS = 4    # spark.sql.shuffle.partitions for every session in this lab
SALTS = 4                 # salt values used to split the hot key
SCHEMA = T.StructType([
    T.StructField("event_id", T.StringType(), False),
    T.StructField("plant", T.StringType(), False),
    T.StructField("line", T.StringType(), False),
    T.StructField("inspected_units", T.LongType(), False),
    T.StructField("defective_units", T.LongType(), False),
])
PLANT_SCHEMA = "plant string, region string, manager_code string"
# Adaptive skew-join handling only engages above two size thresholds whose defaults
# (256 MB per partition, 64 MB advisory size) dwarf this 240-row feed. Task 10 scales
# both down to toy size, deliberately and on the record, to make the mechanism visible.
TOY_SKEW_SETTINGS = {
    "spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes": "1KB",
    "spark.sql.adaptive.advisoryPartitionSizeInBytes": "1KB",
}
_counter = itertools.count()


def build_session(app_name="SpicyBrain lab L04", adaptive=False, broadcast_threshold="-1",
                  shuffle_partitions=SHUFFLE_PARTITIONS, local_dir=None, warehouse_dir=None):
    """Local Spark bound to loopback with the UI and console progress bar disabled.
    Adaptive execution and the automatic broadcast threshold are the two variables the
    tasks change deliberately. local_dir and warehouse_dir let a runner keep every
    temporary file Spark writes inside a directory it deletes afterwards."""
    builder = (SparkSession.builder.master("local[2]").appName(app_name)
               .config("spark.ui.enabled", "false")
               .config("spark.ui.showConsoleProgress", "false")
               .config("spark.driver.bindAddress", "127.0.0.1")
               .config("spark.sql.shuffle.partitions", str(shuffle_partitions))
               .config("spark.sql.adaptive.enabled", "true" if adaptive else "false")
               .config("spark.sql.autoBroadcastJoinThreshold", str(broadcast_threshold)))
    if local_dir:
        builder = builder.config("spark.local.dir", str(local_dir))
    if warehouse_dir:
        builder = builder.config("spark.sql.warehouse.dir", str(warehouse_dir))
    return builder.getOrCreate()


def load_rows(name):
    return json.loads((ROOT / "fixtures" / name).read_text(encoding="utf-8"))


def load_inspections(spark, name="inspections.json", partitions=INPUT_PARTITIONS):
    """Typed fact frame with an explicit, known partition count and no shuffle on the way in."""
    rows = [(r["event_id"], r["plant"], r["line"], r["inspected_units"], r["defective_units"]) for r in load_rows(name)]
    return spark.createDataFrame(spark.sparkContext.parallelize(rows, partitions), SCHEMA)


def load_plants(spark):
    """Three-row dimension held in one partition, so its map stage is one task."""
    rows = [(r["plant"], r["region"], r["manager_code"]) for r in load_rows("plants.json")]
    return spark.createDataFrame(spark.sparkContext.parallelize(rows, 1), PLANT_SCHEMA)


# ---------------------------------------------------------------- plan reading
def plan_text(df, mode="formatted"):
    """The text explain() prints; captured so tests and evidence can keep it."""
    stream = io.StringIO()
    with redirect_stdout(stream):
        df.explain(mode=mode)
    return stream.getvalue()


_NODE = re.compile(r"^[\s:+\-|]*(?:\*\(\d+\)\s*|\*\s*)?([A-Za-z]+)")


def outline_nodes(text):
    """Operator names in the plan outline, top to bottom, without column ids or plan ids.
    Works for formatted mode (outline before the first blank line) and simple mode."""
    names = []
    for line in text.splitlines():
        if line.startswith("=="):
            continue
        if not line.strip():
            if names:
                break
            continue
        match = _NODE.match(line)
        if match:
            names.append(match.group(1))
    return names


def count_nodes(text, name):
    return outline_nodes(text).count(name)


def final_plan(text):
    """The final-plan half of an adaptive explain (everything before '== Initial Plan ==')."""
    return text.split("== Initial Plan ==")[0]


def initial_plan(text):
    return text.split("== Initial Plan ==")[-1]


def build_side(text):
    """Which side a broadcast hash join builds, read from a printed (final) plan."""
    for side in ("BuildLeft", "BuildRight"):
        if side in text:
            return side
    return None


# ---------------------------------------------------------------- transformations
def narrow_chain(df):
    """Filter and projection: each output partition depends on exactly one input partition."""
    return df.filter(F.col("defective_units") > 0).select("event_id", "plant", "defective_units")


def plant_totals(df):
    """Grouped sums: a wide dependency, because every row of one plant must meet."""
    return df.groupBy("plant").agg(F.count("*").alias("rows"),
                                   F.sum("inspected_units").alias("inspected"),
                                   F.sum("defective_units").alias("defective"))


def region_totals(df, plants, broadcast=False):
    """Fact-to-dimension join followed by a regional sum. With broadcast=True the
    small dimension is copied to every task instead of shuffling the fact side."""
    dim = F.broadcast(plants) if broadcast else plants
    return (df.join(dim, "plant")
              .groupBy("region").agg(F.count("*").alias("rows"), F.sum("inspected_units").alias("inspected")))


def rank_within_plant(df):
    """A window function: all rows of one plant must sit in one task, in order."""
    window = Window.partitionBy("plant").orderBy("event_id")
    return df.withColumn("rank_in_plant", F.row_number().over(window))


def salted_join(df, plants, salts=SALTS):
    """Split the hot key: the fact side gets salt = crc32(event_id) % salts and the
    dimension is replicated once per salt, so the join key becomes (plant, salt)."""
    fact = df.withColumn("salt", (F.crc32(F.col("event_id")) % salts).cast("int"))
    salt_values = df.sparkSession.range(salts).select(F.col("id").cast("int").alias("salt"))
    return fact.join(plants.crossJoin(salt_values), ["plant", "salt"])


# ---------------------------------------------------------------- measurement
def partition_rows(df, keep=()):
    """Rows per physical partition of df, as {partition_id: rows}. Columns named in
    `keep` are referenced through max() so the optimizer cannot prune the operator
    that produced them (an unused window column would otherwise disappear)."""
    aggregates = [F.count("*").alias("rows")] + [F.max(c).alias("max_" + c) for c in keep]
    frame = df.withColumn("pid", F.spark_partition_id()).groupBy("pid").agg(*aggregates)
    return {row["pid"]: row["rows"] for row in frame.collect()}


def partition_key_rows(df, key):
    """Rows per (physical partition, key value) of df, as {partition_id: {key: rows}}.
    On a freshly parallelised frame this is the input membership: which plants each
    input partition holds before anything moves."""
    frame = (df.withColumn("pid", F.spark_partition_id())
               .groupBy("pid", key).agg(F.count("*").alias("rows")))
    landed = {}
    for row in frame.collect():
        landed.setdefault(row["pid"], {})[row[key]] = row["rows"]
    return landed


def keyed_partition_rows(df, partitions, *keys):
    """Where rows land after repartition(n, keys): the same movement a join or window needs."""
    return partition_rows(df.repartition(partitions, *keys), keep=keys)


def skew_share(rows_by_partition):
    total = sum(rows_by_partition.values())
    return round(max(rows_by_partition.values()) / total, 4) if total else 0.0


def bounded_collect(df, max_rows):
    """collect() moves every row into the driver process. Refuse when more than
    max_rows would arrive, instead of discovering the problem as an out-of-memory error."""
    arriving = df.limit(max_rows + 1).count()
    if arriving > max_rows:
        raise ValueError(f"collection bound exceeded: more than {max_rows} rows would reach the driver")
    return [row.asDict() for row in df.collect()]


def rows_dicts(df, order):
    """Collect a small result and sort it locally. Sorting through orderBy() would add a
    range-partitioning exchange (and a sampling job) that is not part of the query under study."""
    return sorted((row.asDict() for row in df.collect()), key=lambda row: tuple(row[c] for c in order))


def jobs_started_by(spark, label, action):
    """How many jobs Spark started while `action` ran, counted through a job group.
    Used to show that explain() plans without executing anything."""
    context = spark.sparkContext
    group = f"{label}-{next(_counter)}"
    context.setJobGroup(group, label)
    try:
        action()
    finally:
        context.setJobGroup("", "")
    return len(context.statusTracker().getJobIdsForGroup(group))


def measure(spark, label, action):
    """Run one action inside its own job group and read back what Spark executed:
    jobs, stages and tasks, distinguishing stages that ran from stages Spark skipped
    because their shuffle output already existed. Wall time is deliberately not
    recorded as evidence; a toy run on one machine is not a benchmark."""
    context = spark.sparkContext
    group = f"{label}-{next(_counter)}"
    context.setJobGroup(group, label)
    try:
        result = action()
    finally:
        context.setJobGroup("", "")
    tracker = context.statusTracker()
    previous = None
    for _ in range(100):  # the listener bus is asynchronous; wait until the counts settle
        snapshot = _snapshot(tracker, group)
        settled = all(job["status"] != "RUNNING" for job in snapshot) and snapshot == previous
        if settled and snapshot:
            break
        previous = snapshot
        time.sleep(0.05)
    executed = [s["tasks"] for j in snapshot for s in j["stages"] if s["completed"] > 0]
    skipped = sum(1 for j in snapshot for s in j["stages"] if s["completed"] == 0)
    return result, {"label": label, "jobs": len(snapshot), "executed_stage_tasks": executed,
                    "skipped_stages": skipped, "detail": snapshot}


def _snapshot(tracker, group):
    jobs = []
    for job_id in sorted(tracker.getJobIdsForGroup(group)):
        info = tracker.getJobInfo(job_id)
        if info is None:
            continue
        stages = []
        for stage_id in sorted(info.stageIds):
            stage = tracker.getStageInfo(stage_id)
            if stage is not None:
                stages.append({"stage": stage_id, "tasks": stage.numTasks, "completed": stage.numCompletedTasks})
        jobs.append({"job": job_id, "status": info.status, "stages": stages})
    return jobs


def stage_metrics(spark, measured, timeout_seconds=10.0):
    """Shuffle records and bytes per executed stage and per task, for a measure() result.

    These are the numbers the web UI's Stages tab shows (Shuffle Read / Shuffle Write).
    The UI is disabled here, so they are read from Spark's application status store,
    the store the UI renders, through Py4J. That store is an internal Spark API, used
    because this lab is pinned to Spark 4.0.4; on another version check it still exists.
    The listener bus is asynchronous, so the read waits until every task has reported
    and two consecutive reads agree; it raises rather than return partial evidence."""
    store = spark.sparkContext._jsc.sc().statusStore()
    executed = [(j["job"], s["stage"]) for j in measured["detail"] for s in j["stages"] if s["completed"] > 0]
    deadline = time.time() + timeout_seconds
    previous = None
    while True:
        try:
            snapshot = [_stage_record(store, job, stage) for job, stage in executed]
        except Exception:  # py4j error while the store has not seen the stage yet
            snapshot = None
        complete = snapshot is not None and all(
            s["completed_tasks"] == s["tasks"] == len(s["task_read_records"]) for s in snapshot)
        if complete and snapshot == previous:
            return snapshot
        if time.time() > deadline:
            raise RuntimeError(f"stage metrics for {measured['label']} did not settle")
        previous = snapshot
        time.sleep(0.05)


def _stage_record(store, job, stage_id):
    data = store.lastStageAttempt(stage_id)
    reads, writes = {}, {}
    tasks = store.taskList(stage_id, data.attemptId(), 100000).iterator()
    while tasks.hasNext():
        task = tasks.next()
        if task.taskMetrics().isDefined():
            metrics = task.taskMetrics().get()
            reads[task.index()] = metrics.shuffleReadMetrics().recordsRead()
            writes[task.index()] = metrics.shuffleWriteMetrics().recordsWritten()
    return {"job": job, "stage": stage_id, "tasks": data.numTasks(), "completed_tasks": data.numCompleteTasks(),
            "shuffle_read_records": data.shuffleReadRecords(), "shuffle_write_records": data.shuffleWriteRecords(),
            "shuffle_read_bytes": data.shuffleReadBytes(), "shuffle_write_bytes": data.shuffleWriteBytes(),
            "task_read_records": [reads[i] for i in sorted(reads)],
            "task_write_records": [writes[i] for i in sorted(writes)]}


def busiest_reader(metrics):
    """The executed stage that read the most shuffle records: for a join followed by an
    aggregate, the join stage (it reads both inputs; the final aggregate reads partials)."""
    return max(metrics, key=lambda s: s["shuffle_read_records"])
