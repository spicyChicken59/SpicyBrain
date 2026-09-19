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


def nonempty_sql(column):
    # Match Python str.strip's blank-key policy, including tabs and Unicode
    # whitespace. SQL's ordinary trim removes spaces only. This is authored policy.
    return f"{column} IS NOT NULL AND {column} RLIKE r'(?U)[^\\s\\x1c-\\x1f]'"


VALID_SQL = f"""({nonempty_sql('event_id')})
 AND ({nonempty_sql('inspection_id')})
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
                       .filter(f"({nonempty_sql('event_id')}) AND payloads > 1"))
    revision_conflicts = (distinct.filter(f"version > 0 AND ({nonempty_sql('inspection_id')})")
                          .groupBy("inspection_id", "version")
                          .agg(F.countDistinct(F.struct("inspected_units", "defective_units")).alias("payloads"))
                          .filter("payloads > 1"))
    event_keys = distinct.join(event_conflicts, "event_id").select("inspection_id")
    # 4. Latest is computed before filtering invalid quantities: no resurrection.
    latest = (distinct.filter("version > 0").groupBy("inspection_id")
              .agg(F.max("version").alias("version")))
    current = checked.join(latest, ["inspection_id", "version"])
    known_valid = valid.select("inspection_id").distinct()
    invalid_current = current.filter(~F.col("valid")).select("inspection_id").join(known_valid, "inspection_id")
    unordered_known = (distinct.filter("version IS NULL OR version <= 0")
                       .select("inspection_id").join(known_valid, "inspection_id"))
    unresolved = (event_keys.union(revision_conflicts.select("inspection_id")).union(invalid_current).union(unordered_known)
                  .filter(nonempty_sql("inspection_id")).distinct())
    # 5. Reject ambiguity, then project one canonical current inspection row.
    accepted = (current.filter(F.col("valid")).join(unresolved, "inspection_id", "left_anti")
                .select(*BUSINESS).distinct())
    # 6. Weighted ratio: total defective / total inspected, never mean(row ratios).
    totals = (accepted.agg(F.sum("inspected_units").alias("inspected_units"),
                          F.sum("defective_units").alias("defective_units"))
              .withColumn("defect_rate", F.when(F.col("inspected_units") > 0,
                         F.col("defective_units").cast("double") / F.col("inspected_units"))))
    # Expose a decision relation separately from candidate rows. Empty unresolved
    # keys do not clear global provenance conflicts. This does not publish a report.
    publication = (event_conflicts.agg(F.count("*").alias("event_conflict_count"))
                   .crossJoin(revision_conflicts.agg(F.count("*").alias("revision_conflict_count")))
                   .crossJoin(unresolved.agg(F.count("*").alias("unresolved_key_count")))
                   .withColumn("publication_allowed", (F.col("event_conflict_count") == 0)
                               & (F.col("revision_conflict_count") == 0) & (F.col("unresolved_key_count") == 0)))
    return {"distinct": distinct, "quarantine": quarantine, "valid": valid,
            "accepted": accepted, "unresolved": unresolved, "totals": totals,
            "event_conflicts": event_conflicts, "revision_conflicts": revision_conflicts,
            "publication": publication}


SQL_STAGES = f"""
WITH distinct_input AS (SELECT DISTINCT * FROM raw_inspections),
checked AS (SELECT *, coalesce(({VALID_SQL}), false) AS valid FROM distinct_input),
valid_keys AS (SELECT DISTINCT inspection_id FROM checked WHERE valid),
event_conflicts AS (
 SELECT event_id, count(DISTINCT struct(inspection_id, version, inspected_units, defective_units)) AS payloads
 FROM distinct_input WHERE {nonempty_sql('event_id')} GROUP BY event_id
 HAVING count(DISTINCT struct(inspection_id, version, inspected_units, defective_units)) > 1),
revision_conflicts AS (
 SELECT inspection_id, version, count(DISTINCT struct(inspected_units, defective_units)) AS payloads
 FROM distinct_input WHERE version > 0 AND ({nonempty_sql('inspection_id')}) GROUP BY inspection_id, version
 HAVING count(DISTINCT struct(inspected_units, defective_units)) > 1),
latest AS (SELECT inspection_id, max(version) AS version FROM distinct_input
 WHERE version > 0 GROUP BY inspection_id),
current_rows AS (SELECT c.* FROM checked c JOIN latest l
 ON c.inspection_id = l.inspection_id AND c.version = l.version),
unresolved_evidence AS (
 SELECT d.inspection_id FROM distinct_input d JOIN event_conflicts e USING (event_id)
 UNION SELECT inspection_id FROM revision_conflicts
 UNION SELECT c.inspection_id FROM current_rows c JOIN valid_keys v USING (inspection_id) WHERE NOT c.valid
 UNION SELECT d.inspection_id FROM distinct_input d JOIN valid_keys v USING (inspection_id)
 WHERE d.version IS NULL OR d.version <= 0),
unresolved AS (SELECT DISTINCT inspection_id FROM unresolved_evidence WHERE {nonempty_sql('inspection_id')}),
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
    publication = spark.sql(SQL_STAGES + """,
      decision_counts AS (
        SELECT (SELECT count(*) FROM event_conflicts) AS event_conflict_count,
               (SELECT count(*) FROM revision_conflicts) AS revision_conflict_count,
               (SELECT count(*) FROM unresolved) AS unresolved_key_count)
      SELECT *, event_conflict_count = 0 AND revision_conflict_count = 0
                AND unresolved_key_count = 0 AS publication_allowed FROM decision_counts""")
    return {"accepted": accepted, "totals": totals,
            "unresolved": spark.sql(SQL_STAGES + "SELECT * FROM unresolved"),
            "event_conflicts": spark.sql(SQL_STAGES + "SELECT * FROM event_conflicts"),
            "revision_conflicts": spark.sql(SQL_STAGES + "SELECT * FROM revision_conflicts"),
            "publication": publication}


def join_experiment(spark, accepted):
    # Cinderline tags are one-to-many. Two tags for A multiply A's 12/1 facts.
    tags = spark.createDataFrame([("A", "urgent"), ("A", "sampled"), ("C", "routine")],
                                 "inspection_id string, tag string")
    flawed = accepted.join(tags, "inspection_id")
    # A semijoin means 'inspection has any tag', preserving inspection grain.
    corrected = accepted.join(tags.select("inspection_id").distinct(), "inspection_id", "left_semi")
    return flawed, corrected
