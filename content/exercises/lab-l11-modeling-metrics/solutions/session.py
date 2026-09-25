"""One-machine Apache Spark 4.0.4 session for lab L11.

local[2] threads, web UI and console progress off, two shuffle partitions so
tiny aggregates stay inspectable, session time zone pinned to UTC (the lab's
timestamps are TIMESTAMP_NTZ plant wall-clock values, so the zone never changes
an answer; pinning it only makes the environment explicit). ANSI mode stays at
its Spark 4 default (on). Nothing here contacts Databricks or any network
service; the warehouse directory is a temporary folder removed on stop().
"""
import logging
import os
import shutil
import sys
import tempfile

from pyspark.sql import SparkSession

SPARK_CONFIG = {
    "spark.ui.enabled": "false",
    "spark.ui.showConsoleProgress": "false",
    "spark.driver.bindAddress": "127.0.0.1",
    "spark.sql.shuffle.partitions": "2",
    "spark.sql.session.timeZone": "UTC",
}


class LocalSpark:
    """Start and stop one local session and its temporary warehouse directory."""

    def __init__(self, app_name="lab-l11-modeling-metrics"):
        os.environ["PYSPARK_PYTHON"] = sys.executable
        os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
        self.scratch = tempfile.mkdtemp(prefix="lab-l11-")
        builder = SparkSession.builder.master("local[2]").appName(app_name)
        for key, value in SPARK_CONFIG.items():
            builder = builder.config(key, value)
        builder = builder.config("spark.sql.warehouse.dir", os.path.join(self.scratch, "warehouse"))
        builder = builder.config("spark.local.dir", os.path.join(self.scratch, "local"))
        self.spark = builder.getOrCreate()
        self.spark.sparkContext.setLogLevel("OFF")
        # PySpark 4 also prints a structured JSON line for every SQL error; the
        # lab provokes DIVIDE_BY_ZERO on purpose and asserts it, so keep it quiet.
        logging.getLogger("SQLQueryContextLogger").disabled = True

    def stop(self):
        self.spark.stop()
        shutil.rmtree(self.scratch, ignore_errors=True)
