"""Spark tasks: begin with typed data, predict before running any action."""
import json
from pathlib import Path
import sys
from pyspark.sql import SparkSession
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from solutions.spark_transform import SCHEMA


def transform(raw):
    """Return accepted and totals DataFrames. Write SQL and PySpark versions.

    Stages: exact delivery dedup -> validation -> conflict guard -> latest
    revision before invalid filtering -> canonical projection -> weighted ratio.
    Use a left semijoin for 'has a tag' rather than multiplying inspection rows.
    """
    raise NotImplementedError("Predict baseline and correction rows/types, then implement")


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    spark = SparkSession.builder.master("local[2]").appName("SpicyBrain learner task").getOrCreate()
    try:
        rows = json.loads((root / "fixtures/baseline.json").read_text())
        raw = spark.createDataFrame(rows, SCHEMA)
        raw.printSchema()
        transform(raw)
    finally:
        spark.stop()
