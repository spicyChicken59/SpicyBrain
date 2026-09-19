from pyspark.sql import SparkSession, functions as F, types as T
spark = SparkSession.builder.master("local[2]").appName("weighted-metric").getOrCreate()
schema = "inspection_id string, plant string, inspected_units long, defective_units long"
df = spark.createDataFrame([
    ("A", "North", 12, 1), ("C", "North", 8, 0), ("S", "South", 10, 2)
], schema)
df.createOrReplaceTempView("accepted_inspections")
sql_result = spark.sql("""
WITH checked AS (
  SELECT inspection_id, plant, inspected_units, defective_units
  FROM accepted_inspections
  WHERE inspected_units IS NOT NULL AND defective_units IS NOT NULL
    AND inspected_units >= 0 AND defective_units >= 0
    AND defective_units <= inspected_units
), totals AS (
  SELECT plant, SUM(inspected_units) AS inspected,
         SUM(defective_units) AS defective
  FROM checked GROUP BY plant
)
SELECT plant, inspected, defective,
       CASE WHEN inspected > 0
            THEN CAST(defective AS DOUBLE) / inspected
            ELSE CAST(NULL AS DOUBLE) END AS defect_rate
FROM totals
""")
checked = df.filter(F.col("inspected_units").isNotNull()
    & F.col("defective_units").isNotNull()
    & (F.col("inspected_units") >= 0)
    & (F.col("defective_units") >= 0)
    & (F.col("defective_units") <= F.col("inspected_units")))
selected = checked.select("inspection_id", "plant", "inspected_units", "defective_units")
totals = selected.groupBy("plant").agg(
    F.sum("inspected_units").alias("inspected"),
    F.sum("defective_units").alias("defective"))
py_result = totals.select("plant", "inspected", "defective",
    F.when(F.col("inspected") > 0,
           F.col("defective").cast("double") / F.col("inspected"))
     .otherwise(F.lit(None).cast("double")).alias("defect_rate"))
expected = [("North", 20, 1, 0.05), ("South", 10, 2, 0.2)]
assert [tuple(r) for r in sql_result.orderBy("plant").collect()] == expected
assert [tuple(r) for r in py_result.orderBy("plant").collect()] == expected
assert sql_result.dtypes == py_result.dtypes == [
    ("plant", "string"), ("inspected", "bigint"),
    ("defective", "bigint"), ("defect_rate", "double")]
spark.stop()
