"""Run one named query from a portfolio file on local Spark and print its rows.

    python starters/explore.py running_total                           # solutions/portfolio.sql
    python starters/explore.py running_total starters/portfolio.sql    # your own file

Studying the lab needs no installation; this helper is for readers who want to see the rows
on local Apache Spark 4.0.4 themselves. Spark's scratch and warehouse directories go to a
temporary folder that is deleted when the script ends. A block that is expected to fail prints
its error class instead of rows.
"""
import sys

sys.dont_write_bytecode = True

from pathlib import Path  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from solutions.portfolio import build_session, load_queries, register_views  # noqa: E402

import logging  # noqa: E402

from pyspark.logger import PySparkLogger  # noqa: E402

for _logger in ("SQLQueryContextLogger", "DataFrameQueryContextLogger"):
    PySparkLogger.getLogger(_logger).setLevel(logging.CRITICAL)

if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "running_total"
    source = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "solutions" / "portfolio.sql"
    queries = load_queries()
    queries.update(load_queries(source))
    spark = build_session()
    spark.sparkContext.setLogLevel("OFF")
    try:
        register_views(spark, queries=queries)
        try:
            spark.sql(queries[name]).show(100, truncate=False)
        except Exception as exc:  # the portfolio holds deliberate failures
            print("raised", getattr(exc, "getCondition", lambda: None)() or type(exc).__name__)
    finally:
        spark.stop()
