"""Spark SQL version of the staged transformation.

Stages: distinct deliveries -> classified (reason column) -> rejected /
accepted -> plant report. Every stage is returned so tests can compare each
one with the DataFrame version and with authored expected literals.
"""

REASON_SQL = """CASE
  WHEN plant_id IS NULL THEN 'missing_plant'
  WHEN inspected_units IS NULL OR defective_units IS NULL THEN 'missing_units'
  WHEN inspected_units < 0 OR defective_units < 0 THEN 'negative_units'
  WHEN defective_units > inspected_units THEN 'defects_exceed_inspected'
END"""

REPORT_SQL = """
WITH totals AS (
  SELECT plant_id,
         COUNT(*) AS inspections,
         SUM(inspected_units) AS inspected,
         SUM(defective_units) AS defective
  FROM {accepted}
  GROUP BY plant_id
)
SELECT t.plant_id, p.plant_name, p.region,
       t.inspections, t.inspected, t.defective,
       CASE WHEN t.inspected > 0 THEN CAST(t.defective AS DOUBLE) / t.inspected
            ELSE CAST(NULL AS DOUBLE) END AS defect_rate
FROM totals t
LEFT JOIN {plants} p ON t.plant_id = p.plant_id
"""

# Task 5: explicit null test. "= NULL" is unknown for every row and keeps nothing.
NULL_PLANT_SQL = "SELECT event_id FROM {distinct} WHERE plant_id IS NULL ORDER BY event_id"
# Task 5: COUNT(DISTINCT column) ignores null, by SQL aggregate semantics.
KNOWN_PLANT_COUNT_SQL = "SELECT COUNT(DISTINCT plant_id) AS plants FROM {distinct}"


def sql_stages(spark, events, plants, prefix="l02"):
    names = {key: "%s_%s" % (prefix, key) for key in ("events", "plants", "distinct", "classified", "accepted")}
    events.createOrReplaceTempView(names["events"])
    plants.createOrReplaceTempView(names["plants"])
    distinct = spark.sql("SELECT DISTINCT * FROM %s" % names["events"])
    distinct.createOrReplaceTempView(names["distinct"])
    classified = spark.sql("SELECT *, %s AS reason FROM %s" % (REASON_SQL, names["distinct"]))
    classified.createOrReplaceTempView(names["classified"])
    rejected = spark.sql("SELECT * FROM %s WHERE reason IS NOT NULL" % names["classified"])
    accepted = spark.sql("SELECT event_id, plant_id, line_id, inspected_units, defective_units, inspected_on "
                         "FROM %s WHERE reason IS NULL" % names["classified"])
    accepted.createOrReplaceTempView(names["accepted"])
    report = spark.sql(REPORT_SQL.format(accepted=names["accepted"], plants=names["plants"]))
    return {"distinct": distinct, "classified": classified, "rejected": rejected,
            "accepted": accepted, "report": report, "views": names}


def null_plant_event_ids(spark, views):
    return [row.event_id for row in spark.sql(NULL_PLANT_SQL.format(distinct=views["distinct"])).collect()]


def known_plant_count(spark, views):
    return spark.sql(KNOWN_PLANT_COUNT_SQL.format(distinct=views["distinct"])).first().plants
