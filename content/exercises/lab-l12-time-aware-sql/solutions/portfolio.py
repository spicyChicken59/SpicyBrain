"""Load the Lab L12 fixtures into temporary views and run named portfolio queries.

Everything runs on local Apache Spark 4.0.4 (Spark SQL) on one machine. Nothing here talks to
Databricks, a warehouse or the network. Timestamps in the fixtures are UTC instants written as
ISO-8601 strings ending in Z; the session time zone is set explicitly so that every date, hour,
day and duration answer is stated for a named zone rather than for whatever the host uses.
"""
from __future__ import annotations

import atexit
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path

# Spark's Python workers must run the same interpreter (and minor version) as the driver.
os.environ["PYSPARK_PYTHON"] = sys.executable

from pyspark.sql import SparkSession  # noqa: E402  (imported after the interpreter pin)

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "solutions" / "portfolio.sql"
SESSION_TIME_ZONE = "America/New_York"

SCHEMAS = {
    "machines": "machine_id STRING, machine_name STRING, plant STRING",
    "shift_output": "machine_id STRING, day DATE, shift STRING, units INT",
    "inspections": (
        "inspection_id STRING, revision INT, received_at STRING, machine_id STRING, "
        "result STRING, measurements STRUCT<width_mm: DOUBLE, weight_g: DOUBLE>, "
        "defect_codes ARRAY<STRING>, raw_units STRING"
    ),
    "machine_status": "machine_id STRING, day DATE, status STRING",
    "machine_events": "event_id STRING, machine_id STRING, event_type STRING, event_time_utc STRING",
}
DATE_TEXT = re.compile(r"\d{4}-\d{2}-\d{2}")


def build_session(workdir: Path | None = None, time_zone: str = SESSION_TIME_ZONE) -> SparkSession:
    """A small local session: two threads, no web UI, two shuffle partitions.

    Spark's scratch space and its warehouse directory live under `workdir`, so nothing is
    written into the lab folder. Without a `workdir` a temporary one is created and deleted
    when the Python process exits.
    """
    if workdir is None:
        workdir = Path(tempfile.mkdtemp(prefix="lab-l12-"))
        atexit.register(shutil.rmtree, workdir, True)
    return (
        SparkSession.builder.master("local[2]")
        .appName("lab-l12-time-aware-sql")
        .config("spark.ui.enabled", "false")
        .config("spark.ui.showConsoleProgress", "false")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.sql.session.timeZone", time_zone)
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .config("spark.local.dir", str(workdir / "spark-local"))
        .config("spark.sql.warehouse.dir", str(workdir / "spark-warehouse"))
        .getOrCreate()
    )


def load_queries(path: Path = REFERENCE) -> dict[str, str]:
    """Split a portfolio file on '-- query: <name>' markers."""
    text = Path(path).read_text(encoding="utf-8")
    parts = re.split(r"^-- query: ([a-z0-9_]+)\s*$", text, flags=re.MULTILINE)
    return {parts[i]: parts[i + 1].strip() for i in range(1, len(parts), 2)}


def fixture_rows(rows: list[dict]) -> list[tuple]:
    """JSON rows as tuples in schema order: dates become DATE values, structs become tuples."""
    out = []
    for row in rows:
        values = []
        for value in row.values():
            if isinstance(value, dict):
                values.append(tuple(value.values()))
            elif isinstance(value, str) and DATE_TEXT.fullmatch(value):
                values.append(date.fromisoformat(value))
            else:
                values.append(value)
        out.append(tuple(values))
    return out


def register_views(
    spark: SparkSession,
    overrides: dict[str, list] | None = None,
    queries: dict[str, str] | None = None,
) -> None:
    """Create one temporary view per fixture with an explicit schema, then latest_inspections.

    `overrides` maps a fixture name to a replacement row list in the fixture's JSON shape (the
    transfer tests use it for altered inputs). `queries` supplies the portfolio whose
    latest_inspection block defines the latest_inspections view (the reference by default).
    """
    overrides = overrides or {}
    for name, ddl in SCHEMAS.items():
        rows = overrides.get(name)
        if rows is None:
            rows = json.loads((ROOT / "fixtures" / f"{name}.json").read_text(encoding="utf-8"))
        spark.createDataFrame(fixture_rows(rows), ddl).createOrReplaceTempView(name)
    queries = queries or load_queries()
    spark.sql(queries["latest_inspection"]).createOrReplaceTempView("latest_inspections")


def run(spark: SparkSession, name: str, queries: dict[str, str] | None = None):
    """Run one named query; return its schema string and its rows as plain Python lists."""
    queries = queries or load_queries()
    df = spark.sql(queries[name])
    return df.schema.simpleString(), [list(r) for r in df.collect()]


if __name__ == "__main__":  # manual exploration: print every reference query that succeeds
    session = build_session()
    session.sparkContext.setLogLevel("OFF")
    register_views(session)
    for query_name, sql in load_queries().items():
        print("==", query_name)
        try:
            session.sql(sql).show(50, truncate=False)
        except Exception as exc:  # the portfolio holds deliberate failures
            print("   raised", getattr(exc, "getCondition", lambda: None)() or type(exc).__name__)
    session.stop()
