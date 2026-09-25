"""Declared schemas and typed loaders for the fixtures.

A declared schema makes assumptions visible: inspected_units is a nullable
32-bit integer, so a missing quantity stays a null rather than becoming zero,
and reading the same file with inference (bigint, alphabetical columns) is a
different, comparable choice rather than an accident.
"""
from pyspark.sql import types as T

EVENT_SCHEMA = T.StructType([
    T.StructField("event_id", T.StringType(), True),
    T.StructField("plant_id", T.StringType(), True),
    T.StructField("line_id", T.StringType(), True),
    T.StructField("inspected_units", T.IntegerType(), True),
    T.StructField("defective_units", T.IntegerType(), True),
    T.StructField("inspected_on", T.StringType(), True),
])
PLANT_SCHEMA = T.StructType([
    T.StructField("plant_id", T.StringType(), True),
    T.StructField("plant_name", T.StringType(), True),
    T.StructField("region", T.StringType(), True),
])
EVENT_COLUMNS = [field.name for field in EVENT_SCHEMA.fields]


def rows_for(records, schema):
    """Order each JSON object's values by the declared schema; absent keys are null."""
    return [tuple(record.get(field.name) for field in schema.fields) for record in records]


def events_frame(spark, records):
    return spark.createDataFrame(rows_for(records, EVENT_SCHEMA), EVENT_SCHEMA)


def plants_frame(spark, records):
    return spark.createDataFrame(rows_for(records, PLANT_SCHEMA), PLANT_SCHEMA)
