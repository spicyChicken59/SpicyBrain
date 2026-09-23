"""Declared schemas and typed loaders for the two relations.

inspections: one accepted, current inspection per row (unique inspection_id).
plants: one loaded *version* of a plant record per row -- the key repeats,
which is the whole point of this lab. valid_from is a real DateType so the
"latest version" rule orders dates, not strings.
"""
import datetime

from pyspark.sql import types as T

INSPECTION_SCHEMA = T.StructType([
    T.StructField("inspection_id", T.StringType(), True),
    T.StructField("plant_id", T.StringType(), True),
    T.StructField("inspected_units", T.IntegerType(), True),
    T.StructField("defective_units", T.IntegerType(), True),
])
PLANT_SCHEMA = T.StructType([
    T.StructField("plant_id", T.StringType(), True),
    T.StructField("plant_name", T.StringType(), True),
    T.StructField("region", T.StringType(), True),
    T.StructField("manager", T.StringType(), True),
    T.StructField("valid_from", T.DateType(), True),
    T.StructField("row_source", T.StringType(), True),
])
PLANT_COLUMNS = [field.name for field in PLANT_SCHEMA.fields]


def _typed(value, field):
    if value is None:
        return None
    if isinstance(field.dataType, T.DateType):
        return datetime.date.fromisoformat(value)   # deliberate conversion, no inference
    return value


def rows_for(records, schema):
    return [tuple(_typed(record.get(field.name), field) for field in schema.fields) for record in records]


def inspections_frame(spark, records):
    return spark.createDataFrame(rows_for(records, INSPECTION_SCHEMA), INSPECTION_SCHEMA)


def plants_frame(spark, records):
    return spark.createDataFrame(rows_for(records, PLANT_SCHEMA), PLANT_SCHEMA)
