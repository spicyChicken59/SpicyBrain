"""Starter: Spark SQL stages. Fill every TODO; keep the stage names.

Contract (see TASKS.md): distinct deliveries; reason precedence missing_plant,
missing_units, negative_units, defects_exceed_inspected; accepted rows drop
the reason column; the report is one row per plant_id present in accepted
rows, LEFT JOINed to the plant dimension, with a unit-weighted defect_rate
that is NULL when inspected is 0.
"""

REASON_SQL = """CASE
  WHEN plant_id IS NULL THEN 'missing_plant'
  -- TODO: missing_units, negative_units, defects_exceed_inspected, in that order
END"""

REPORT_SQL = """
WITH totals AS (
  SELECT plant_id,
         COUNT(*) AS inspections
         -- TODO: inspected and defective sums
  FROM {accepted}
  GROUP BY plant_id
)
SELECT t.plant_id, p.plant_name, p.region, t.inspections
       -- TODO: inspected, defective and defect_rate (CAST to DOUBLE; NULL when inspected = 0)
FROM totals t
-- TODO: join the plant dimension without losing plants absent from it
"""

NULL_PLANT_SQL = "SELECT event_id FROM {distinct} WHERE plant_id = NULL ORDER BY event_id"  # TODO: this keeps nothing; why?
KNOWN_PLANT_COUNT_SQL = "SELECT COUNT(DISTINCT plant_id) AS plants FROM {distinct}"


def sql_stages(spark, events, plants, prefix="l02"):
    names = {key: "%s_%s" % (prefix, key) for key in ("events", "plants", "distinct", "classified", "accepted")}
    events.createOrReplaceTempView(names["events"])
    plants.createOrReplaceTempView(names["plants"])
    distinct = spark.sql("SELECT DISTINCT * FROM %s" % names["events"])
    distinct.createOrReplaceTempView(names["distinct"])
    classified = spark.sql("SELECT *, %s AS reason FROM %s" % (REASON_SQL, names["distinct"]))
    classified.createOrReplaceTempView(names["classified"])
    rejected = None  # TODO: rows whose reason is not null, keeping every column
    accepted = None  # TODO: rows whose reason is null, without the reason column
    accepted.createOrReplaceTempView(names["accepted"])
    report = spark.sql(REPORT_SQL.format(accepted=names["accepted"], plants=names["plants"]))
    return {"distinct": distinct, "classified": classified, "rejected": rejected,
            "accepted": accepted, "report": report, "views": names}
