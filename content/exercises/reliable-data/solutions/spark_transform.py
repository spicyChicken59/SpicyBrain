"""Complete local Spark 4.0.4 transformations. No Delta dependency or cloud use.

This layer accepts explicitly typed source rows. reference.py validates raw
JSON types before this boundary; try_cast is taught separately in the runner.
"""
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

SCHEMA = StructType([
    StructField("event_id", StringType(), True),
    StructField("inspection_id", StringType(), True),
    StructField("version", IntegerType(), True),
    StructField("inspected_units", IntegerType(), True),
    StructField("defective_units", IntegerType(), True),
])
BUSINESS = ["inspection_id", "version", "inspected_units", "defective_units"]
VALID_SQL = """event_id IS NOT NULL AND length(trim(event_id)) > 0
 AND inspection_id IS NOT NULL AND length(trim(inspection_id)) > 0
 AND version IS NOT NULL AND version > 0
 AND inspected_units IS NOT NULL AND inspected_units >= 0
 AND defective_units IS NOT NULL AND defective_units >= 0
 AND defective_units <= inspected_units"""


def pyspark_transform(raw):
    # 1. Remove identical deliveries only; never pick arbitrary conflicting rows.
    distinct = raw.distinct()
    # 2. A predicate is a Column expression evaluated by Spark, not a Python bool.
    checked = distinct.withColumn("valid", F.coalesce(F.expr(VALID_SQL), F.lit(False)))
    quarantine = checked.filter(~F.col("valid"))
    valid = checked.filter(F.col("valid"))
    # 3. Detect conflicting identities before selecting the latest version.
    event_conflicts = (distinct.groupBy("event_id")
                       .agg(F.countDistinct(F.struct(*BUSINESS)).alias("payloads"))
                       .filter("event_id IS NOT NULL AND payloads > 1"))
    revision_conflicts = (distinct.filter("version > 0").groupBy("inspection_id", "version")
                          .agg(F.countDistinct(F.struct("inspected_units", "defective_units")).alias("payloads"))
                          .filter("payloads > 1").select("inspection_id"))
    event_keys = distinct.join(event_conflicts, "event_id").select("inspection_id")
    # 4. Latest is computed before filtering invalid quantities: no resurrection.
    latest = (distinct.filter("version > 0").groupBy("inspection_id")
              .agg(F.max("version").alias("version")))
    current = checked.join(latest, ["inspection_id", "version"])
    known_valid = valid.select("inspection_id").distinct()
    invalid_current = current.filter(~F.col("valid")).select("inspection_id").join(known_valid, "inspection_id")
    unordered_known = (distinct.filter("version IS NULL OR version <= 0")
                       .select("inspection_id").join(known_valid, "inspection_id"))
    unresolved = (event_keys.union(revision_conflicts).union(invalid_current).union(unordered_known)
                  .filter("inspection_id IS NOT NULL").distinct())
    # 5. Reject ambiguity, then project one canonical current inspection row.
    accepted = (current.filter(F.col("valid")).join(unresolved, "inspection_id", "left_anti")
                .select(*BUSINESS).distinct())
    # 6. Weighted ratio: total defective / total inspected, never mean(row ratios).
    totals = (accepted.agg(F.sum("inspected_units").alias("inspected_units"),
                          F.sum("defective_units").alias("defective_units"))
              .withColumn("defect_rate", F.when(F.col("inspected_units") > 0,
                         F.col("defective_units").cast("double") / F.col("inspected_units"))))
    return {"distinct": distinct, "quarantine": quarantine, "valid": valid,
            "accepted": accepted, "unresolved": unresolved, "totals": totals}


SQL_STAGES = f"""
WITH distinct_input AS (SELECT DISTINCT * FROM raw_inspections),
checked AS (SELECT *, coalesce(({VALID_SQL}), false) AS valid FROM distinct_input),
valid_keys AS (SELECT DISTINCT inspection_id FROM checked WHERE valid),
event_conflicts AS (
 SELECT event_id FROM distinct_input WHERE event_id IS NOT NULL GROUP BY event_id
 HAVING count(DISTINCT struct(inspection_id, version, inspected_units, defective_units)) > 1),
revision_conflicts AS (
 SELECT inspection_id FROM distinct_input WHERE version > 0 GROUP BY inspection_id, version
 HAVING count(DISTINCT struct(inspected_units, defective_units)) > 1),
latest AS (SELECT inspection_id, max(version) AS version FROM distinct_input
 WHERE version > 0 GROUP BY inspection_id),
current_rows AS (SELECT c.* FROM checked c JOIN latest l
 ON c.inspection_id = l.inspection_id AND c.version = l.version),
unresolved AS (
 SELECT d.inspection_id FROM distinct_input d JOIN event_conflicts e USING (event_id)
 UNION SELECT inspection_id FROM revision_conflicts
 UNION SELECT c.inspection_id FROM current_rows c JOIN valid_keys v USING (inspection_id) WHERE NOT c.valid
 UNION SELECT d.inspection_id FROM distinct_input d JOIN valid_keys v USING (inspection_id)
 WHERE d.version IS NULL OR d.version <= 0),
accepted AS (
 SELECT DISTINCT c.inspection_id, c.version, c.inspected_units, c.defective_units
 FROM current_rows c LEFT ANTI JOIN unresolved u ON c.inspection_id = u.inspection_id
 WHERE c.valid)
"""


def sql_transform(raw, spark):
    raw.createOrReplaceTempView("raw_inspections")
    accepted = spark.sql(SQL_STAGES + "SELECT * FROM accepted")
    totals = spark.sql(SQL_STAGES + """
      SELECT sum(inspected_units) AS inspected_units,
             sum(defective_units) AS defective_units,
             CASE WHEN sum(inspected_units) > 0
                  THEN CAST(sum(defective_units) AS DOUBLE) / sum(inspected_units)
             END AS defect_rate FROM accepted""")
    return {"accepted": accepted, "totals": totals}


def join_experiment(spark, accepted):
    # Cinderline tags are one-to-many. Two tags for A multiply A's 12/1 facts.
    tags = spark.createDataFrame([("A", "urgent"), ("A", "sampled"), ("C", "routine")],
                                 "inspection_id string, tag string")
    flawed = accepted.join(tags, "inspection_id")
    # A semijoin means 'inspection has any tag', preserving inspection grain.
    corrected = accepted.join(tags.select("inspection_id").distinct(), "inspection_id", "left_semi")
    return flawed, corrected
