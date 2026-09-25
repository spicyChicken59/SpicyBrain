"""Reference solution for lab L05: one small open-source Delta table, written, corrected, merged,
evolved, compacted and read back by version.

Everything here runs on local Apache Spark 4.0.4 with delta-spark 4.0.0 (open-source Delta Lake)
in local[2] mode on one machine, web UI disabled. Nothing runs on Databricks; nothing here is a
benchmark. Every value the tests compare against is authored in expected/ by a plain-Python
replay and by hand from the documentation; expected/ never imports this module.

Safety: no function in this module disables Delta's retention safety check, shortens a
retention period or runs a VACUUM that deletes anything. `vacuum_dry_run` only lists.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

from pyspark.sql import SparkSession, Window, functions as F, types as T

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = T.StructType([
    T.StructField("inspection_id", T.StringType(), False),
    T.StructField("plant", T.StringType(), False),
    T.StructField("inspected", T.IntegerType(), False),
    T.StructField("defective", T.IntegerType(), False),
    T.StructField("revision", T.IntegerType(), False),
])
EVOLVED_SCHEMA = T.StructType(SCHEMA.fields + [T.StructField("inspector", T.StringType(), True)])
CORRECTION = 12           # A's corrected inspected count: the 18 -> 20, not 30 sequence
CHANGE_FEED_PROPERTY = "delta.enableChangeDataFeed"
DELTA_PACKAGE = "io.delta:delta-spark_2.13:4.0.0"


# ------------------------------------------------------------------ session and jar resolution
def build_session(app_name="SpicyBrain lab L05", local_dir=None, warehouse_dir=None):
    """Local Spark with the Delta SQL extension and catalog.

    Delta's jars are resolved by `configure_spark_with_delta_pip`, which adds
    spark.jars.packages=io.delta:delta-spark_2.13:4.0.0; Ivy looks in the local Maven and Ivy
    caches first and downloads from Maven Central only when they lack the jars. Two optional
    environment variables change that without editing code:
      SPICYBRAIN_IVY_DIR  an Ivy directory that already holds the jars (spark.jars.ivy);
      LAB_DELTA_JARS      comma-separated local jar paths, which bypass Ivy entirely.
    Returns (spark, resolution) where resolution records what actually happened."""
    os.environ["PYSPARK_PYTHON"] = sys.executable  # Python workers must use the driver's interpreter
    builder = (SparkSession.builder.master("local[2]").appName(app_name)
               .config("spark.ui.enabled", "false")
               .config("spark.ui.showConsoleProgress", "false")
               .config("spark.driver.bindAddress", "127.0.0.1")
               .config("spark.sql.shuffle.partitions", "2")
               .config("spark.databricks.delta.snapshotPartitions", "2")
               .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
               .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog"))
    if local_dir:
        builder = builder.config("spark.local.dir", str(local_dir))
    if warehouse_dir:
        builder = builder.config("spark.sql.warehouse.dir", str(warehouse_dir))
    jars = os.environ.get("LAB_DELTA_JARS")
    ivy_dir = os.environ.get("SPICYBRAIN_IVY_DIR")
    if jars:
        spark = builder.config("spark.jars", jars).getOrCreate()
        method = "LAB_DELTA_JARS (spark.jars, no Ivy resolution)"
    else:
        if ivy_dir:
            builder = builder.config("spark.jars.ivy", ivy_dir)
        from delta import configure_spark_with_delta_pip
        spark = configure_spark_with_delta_pip(builder).getOrCreate()
        method = "configure_spark_with_delta_pip"
    conf = spark.sparkContext.getConf()
    resolved = [Path(j.replace("file://", "")) for j in (conf.get("spark.jars", "") or "").split(",") if j]
    resolution = {
        "method": method,
        "spark.jars.packages": conf.get("spark.jars.packages", None),
        "spark.jars.ivy": ("SPICYBRAIN_IVY_DIR (an Ivy directory given by the environment)" if (ivy_dir and not jars)
                           else "not set (Spark's default Ivy location)"),
        "resolvedJars": {j.name: _sha256(j) for j in resolved},
        "sameBytesInLocalMavenRepository": {j.name: _in_local_maven(j) for j in resolved},
    }
    return spark, resolution


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "unreadable"


def _in_local_maven(jar):
    """True when ~/.m2/repository holds a file with the same name and bytes as a loaded jar: evidence that
    Ivy took it from the local Maven cache (its 'local-m2-cache' resolver) rather than a download."""
    group, _, artifact = jar.name.partition("_")
    folder = Path.home() / ".m2" / "repository" / Path(*group.split("."))
    if not artifact or not folder.is_dir():
        return False
    digest = _sha256(jar)
    return any(_sha256(candidate) == digest for candidate in folder.rglob(artifact))


def delta_table(spark, path):
    from delta.tables import DeltaTable
    return DeltaTable.forPath(spark, str(path))


def ref(path):
    """SQL name of a path-addressed Delta table."""
    return f"delta.`{path}`"


# ------------------------------------------------------------------ fixtures
def fixture_rows(name):
    return json.loads((ROOT / "fixtures" / name).read_text(encoding="utf-8"))


def batch(spark, name, schema=None):
    """One fixture as a typed single-partition DataFrame, so each plain write adds exactly one data file."""
    rows = fixture_rows(name)
    schema = schema or (EVOLVED_SCHEMA if any("inspector" in r for r in rows) else SCHEMA)
    data = [tuple(r.get(f.name) for f in schema.fields) for r in rows]
    return spark.createDataFrame(data, schema).coalesce(1)


# ------------------------------------------------------------------ the commit sequence
def write_initial(spark, path, name="initial_a.json"):
    """Version 0: create the table with A. mode('error') refuses to overwrite an existing table."""
    batch(spark, name).write.format("delta").mode("error").save(str(path))


def append(spark, path, name, merge_schema=False):
    """An append. With merge_schema=True the write may add columns the table lacks (explicit schema
    evolution for this one write); without it a new column is a schema-enforcement error."""
    writer = batch(spark, name).write.format("delta").mode("append")
    if merge_schema:
        writer = writer.option("mergeSchema", "true")
    writer.save(str(path))


def correct_inspected(spark, path, inspection_id, value):
    """Version 2: an UPDATE rewrites only the file that holds the matched row (copy-on-write here,
    because this table has no deletion vectors)."""
    spark.sql(f"UPDATE {ref(path)} SET inspected = {int(value)} WHERE inspection_id = '{inspection_id}'")


def enable_change_feed(spark, path):
    """Version 3: a table-property commit. Changes are recorded from the next commit on, never before."""
    spark.sql(f"ALTER TABLE {ref(path)} SET TBLPROPERTIES ({CHANGE_FEED_PROPERTY} = true)")


def merge_incremental(spark, path, source):
    """An incremental delivery: matched rows are replaced, new keys inserted. A target key that is absent
    from the source is neither matched nor 'not matched', so it is untouched: a missing row is not a delete."""
    source.createOrReplaceTempView("incoming")
    spark.sql(f"""
        MERGE INTO {ref(path)} AS t
        USING incoming AS s
        ON t.inspection_id = s.inspection_id
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
    """)


def dedupe_latest_revision(source):
    """Keep one source row per key, the highest revision. Without this a source with two rows for one
    matched key makes Delta refuse the MERGE, because it cannot know which row should win."""
    latest = Window.partitionBy("inspection_id").orderBy(F.col("revision").desc())
    return source.withColumn("_rank", F.row_number().over(latest)).filter(F.col("_rank") == 1).drop("_rank")


def merge_guarded(spark, path, source):
    """The Python API form of a guarded upsert: update only when the source carries a newer revision,
    insert unseen keys, touch nothing else. A replayed older revision is skipped, not applied."""
    (delta_table(spark, path).alias("t")
        .merge(source.alias("s"), "t.inspection_id = s.inspection_id")
        .whenMatchedUpdateAll(condition="s.revision > t.revision")
        .whenNotMatchedInsertAll()
        .execute())


def merge_full_snapshot(spark, path, source, plant):
    """A complete snapshot of one plant: a target row of that plant with no source row was retired, so
    WHEN NOT MATCHED BY SOURCE deletes it. The clause is scoped to the plant the snapshot covers."""
    source.createOrReplaceTempView("snapshot")
    spark.sql(f"""
        MERGE INTO {ref(path)} AS t
        USING snapshot AS s
        ON t.inspection_id = s.inspection_id
        WHEN MATCHED AND s.revision > t.revision THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
        WHEN NOT MATCHED BY SOURCE AND t.plant = '{plant}' THEN DELETE
    """)


def merge_unscoped_snapshot_wrong(spark, path, source):
    """THE WRONG APPROACH, run only against a disposable copy: an unscoped NOT MATCHED BY SOURCE clause
    deletes every target row the delivery did not mention, including rows it never covered."""
    source.createOrReplaceTempView("snapshot_unscoped")
    spark.sql(f"""
        MERGE INTO {ref(path)} AS t
        USING snapshot_unscoped AS s
        ON t.inspection_id = s.inspection_id
        WHEN MATCHED AND s.revision > t.revision THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
        WHEN NOT MATCHED BY SOURCE THEN DELETE
    """)


def copy_version(spark, source_path, version, destination):
    """Write the rows one version selects into a new, disposable table (for the wrong-approach test)."""
    (spark.read.format("delta").option("versionAsOf", int(version)).load(str(source_path))
        .coalesce(1).write.format("delta").mode("error").save(str(destination)))


def optimize(spark, path):
    """Compaction: OPTIMIZE rewrites small files into fewer larger ones and commits a version that
    changes no row. The old files stay on disk for time travel until VACUUM removes them."""
    row = spark.sql(f"OPTIMIZE {ref(path)}").collect()[0]
    metrics = row["metrics"].asDict(recursive=True)
    return {"numFilesAdded": metrics["numFilesAdded"], "numFilesRemoved": metrics["numFilesRemoved"]}


def vacuum_dry_run(spark, path, retain_hours=None):
    """Lists what VACUUM would delete, deleting nothing and committing nothing. With retain_hours=None the
    table's retention applies (7 days by default). A retain_hours below the table's retention is refused
    by Delta's safety check before anything is listed; this lab never turns that check off."""
    retain = f" RETAIN {int(retain_hours)} HOURS" if retain_hours is not None else ""
    return [r[0] for r in spark.sql(f"VACUUM {ref(path)}{retain} DRY RUN").collect()]


# ------------------------------------------------------------------ reading evidence
def snapshot(spark, path, version=None, columns=None):
    """The rows one table version selects, as sorted dicts. version=None reads the current version."""
    reader = spark.read.format("delta")
    if version is not None:
        reader = reader.option("versionAsOf", int(version))
    df = reader.load(str(path))
    cols = columns or df.columns
    return sorted((r.asDict() for r in df.select(*cols).collect()), key=lambda r: r["inspection_id"])


def totals(rows):
    return {"row_count": len(rows), "total_inspected": sum(r["inspected"] for r in rows),
            "total_defective": sum(r["defective"] for r in rows)}


def directory_parquet_sum(spark, path):
    """The wrong reading: every Parquet data file in the directory, ignoring the log. Superseded files are
    still on disk, so their rows are counted again. Spark skips underscore-prefixed folders."""
    return spark.read.format("parquet").load(str(path)).agg(F.sum("inspected")).collect()[0][0]


def history(spark, path):
    """DESCRIBE HISTORY, oldest first: version, operation and Delta's operation metrics and parameters."""
    rows = (delta_table(spark, path).history()
            .select("version", "operation", "operationMetrics", "operationParameters").collect())
    return sorted(({"version": r["version"], "operation": r["operation"],
                    "operationMetrics": dict(r["operationMetrics"] or {}),
                    "operationParameters": dict(r["operationParameters"] or {})} for r in rows),
                  key=lambda h: h["version"])


def detail(spark, path):
    """DESCRIBE DETAIL: file count, protocol versions, table features, properties and clustering columns."""
    r = spark.sql(f"DESCRIBE DETAIL {ref(path)}").collect()[0].asDict()
    return {k: r.get(k) for k in ("numFiles", "minReaderVersion", "minWriterVersion", "tableFeatures",
                                  "properties", "clusteringColumns", "partitionColumns")}


def current_version(spark, path):
    return history(spark, path)[-1]["version"]


def change_feed(spark, path, start, end):
    """Row-level changes between two versions (inclusive), read with the change data feed. The feed must
    have been enabled at or before the start version, otherwise Delta refuses the read."""
    df = (spark.read.format("delta").option("readChangeFeed", "true")
          .option("startingVersion", int(start)).option("endingVersion", int(end)).load(str(path)))
    rows = [r.asDict() for r in df.select("inspection_id", "inspected", "defective", "revision", "_change_type",
                                         "_commit_version").collect()]
    return sorted(rows, key=lambda c: (c["_commit_version"], c["inspection_id"], c["_change_type"]))


def data_files(path):
    """Parquet data files physically in the table directory (outside _delta_log and _change_data), whether
    or not the current version selects them."""
    return sorted(str(p.relative_to(path)) for p in Path(path).rglob("*.parquet")
                  if not any(part.startswith("_") for part in p.relative_to(path).parts))


def change_files(path):
    """Change data files written for UPDATE, DELETE and MERGE commits after the feed was enabled."""
    folder = Path(path) / "_change_data"
    return sorted(p.name for p in folder.glob("*.parquet")) if folder.is_dir() else []


def log_files(path):
    return sorted(p.name for p in (Path(path) / "_delta_log").glob("*.json"))


def columns(spark, path, version=None):
    reader = spark.read.format("delta")
    if version is not None:
        reader = reader.option("versionAsOf", int(version))
    return reader.load(str(path)).columns


def create_clustered_table(spark, path):
    """A second, tiny table declared with liquid clustering (an open-source Delta 3.1+ mechanism). Creating
    it enables the clustering and domain-metadata table features, which DESCRIBE DETAIL reports."""
    spark.sql(f"CREATE TABLE {ref(path)} (inspection_id STRING, plant STRING, inspected INT) "
              f"USING delta CLUSTER BY (plant)")
    spark.sql(f"INSERT INTO {ref(path)} VALUES ('Z', 'West', 5)")
    return detail(spark, path)


# ------------------------------------------------------------------ the whole sequence, for transfer runs
def run_sequence(spark, path, correction=CORRECTION):
    """Runs versions 0-8 on a fresh path and returns totals per version plus the directory reading after
    version 2. Used by the transfer test with a different correction."""
    write_initial(spark, path)
    append(spark, path, "append_c.json")
    correct_inspected(spark, path, "A", correction)
    directory_sum = directory_parquet_sum(spark, path)
    enable_change_feed(spark, path)
    merge_incremental(spark, path, batch(spark, "incremental_day2.json"))
    merge_guarded(spark, path, dedupe_latest_revision(batch(spark, "incremental_day3.json")))
    merge_full_snapshot(spark, path, batch(spark, "snapshot_south.json"), "South")
    append(spark, path, "append_f_inspector.json", merge_schema=True)
    optimize(spark, path)
    return {"versions": {str(v): totals(snapshot(spark, path, v)) for v in range(0, 9)},
            "directory_parquet_sum_after_version_2": directory_sum}
