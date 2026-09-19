from pyspark.sql import SparkSession, functions as F, types as T
spark = SparkSession.builder.master("local[2]").appName("typed-records").getOrCreate()
schema = T.StructType([
    T.StructField("inspection_id", T.StringType(), True),
    T.StructField("version", T.LongType(), True),
    T.StructField("inspected_units", T.LongType(), True),
    T.StructField("defective_units", T.LongType(), True),
])
rows = [("A", 2, 12, 1), ("C", 1, 8, 0), ("D", 1, None, 0)]
raw = spark.createDataFrame(rows, schema)
raw.printSchema()
valid = raw.filter(
    F.col("inspected_units").isNotNull()
    & F.col("defective_units").isNotNull()
    & (F.col("inspected_units") >= 0)
    & (F.col("defective_units") >= 0)
    & (F.col("defective_units") <= F.col("inspected_units")))
projected = valid.select("inspection_id",
    F.col("inspected_units").alias("inspected"),
    (F.col("inspected_units") - F.col("defective_units")).alias("nondefective"),
    F.col("inspected_units").cast("double").alias("units_as_double"))
projected.orderBy("inspection_id").show()
spark.stop()
