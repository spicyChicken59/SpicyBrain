"""One-machine Apache Spark 4.0.4 session for this lab.

local[2] threads, web UI disabled, two shuffle partitions so tiny aggregates
stay inspectable. Nothing here contacts Databricks or any network service.
"""
import os
import sys

from pyspark.sql import SparkSession

SPARK_CONFIG = {
    "spark.ui.enabled": "false",
    "spark.driver.bindAddress": "127.0.0.1",
    "spark.sql.shuffle.partitions": "2",
}


def local_session(app_name="lab-l03-join-cardinality"):
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
    builder = SparkSession.builder.master("local[2]").appName(app_name)
    for key, value in SPARK_CONFIG.items():
        builder = builder.config(key, value)
    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    return spark
