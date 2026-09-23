"""Spark SQL versions of the same diagnosis, repair and traps.

Each string takes view names via str.format so the runner can register the
baseline and transfer dimensions under different names in one session.
"""

DUPLICATE_KEYS_SQL = """
SELECT plant_id, COUNT(*) AS row_count
FROM {plants}
GROUP BY plant_id
HAVING COUNT(*) > 1
ORDER BY plant_id
"""

NAIVE_TOTALS_SQL = """
SELECT COUNT(*) AS row_count,
       SUM(i.inspected_units) AS inspected,
       SUM(i.defective_units) AS defective
FROM {inspections} i
JOIN {plants} p ON i.plant_id = p.plant_id
"""

CURRENT_PLANTS_SQL = """
SELECT plant_id, plant_name, region, manager, valid_from, row_source
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY plant_id
                               ORDER BY valid_from DESC, row_source DESC) AS version_rank
  FROM {plants}
)
WHERE version_rank = 1
"""

CURRENT_PLANTS_AGGREGATE_SQL = """
SELECT plant_id,
       max_by(plant_name, valid_from) AS plant_name,
       max_by(region, valid_from)     AS region,
       max_by(manager, valid_from)    AS manager,
       MAX(valid_from)                AS valid_from,
       max_by(row_source, valid_from) AS row_source
FROM {plants}
GROUP BY plant_id
"""

REGION_REPORT_SQL = """
SELECT p.region,
       COUNT(*) AS inspections,
       SUM(i.inspected_units) AS inspected,
       SUM(i.defective_units) AS defective,
       CASE WHEN SUM(i.inspected_units) > 0
            THEN CAST(SUM(i.defective_units) AS DOUBLE) / SUM(i.inspected_units) END AS defect_rate
FROM {inspections} i
LEFT JOIN {current} p ON i.plant_id = p.plant_id
GROUP BY p.region
"""

PLANT_COUNTS_SQL = """
SELECT p.plant_id,
       COUNT(*) AS row_count,
       COUNT(i.inspection_id) AS inspection_count,
       SUM(i.inspected_units) AS inspected_sum,
       COALESCE(SUM(i.inspected_units), 0) AS inspected
FROM {current} p
LEFT JOIN {inspections} i ON p.plant_id = i.plant_id
GROUP BY p.plant_id
"""

RATES_SQL = """
SELECT plant_id,
       CASE WHEN SUM(inspected_units) > 0
            THEN CAST(SUM(defective_units) AS DOUBLE) / SUM(inspected_units) END AS weighted_rate,
       AVG(try_divide(CAST(defective_units AS DOUBLE), inspected_units))   AS average_of_rates,
       COUNT(try_divide(CAST(defective_units AS DOUBLE), inspected_units)) AS rate_rows,
       COUNT(*) AS row_count
FROM {inspections}
GROUP BY plant_id
"""


def register(spark, inspections, plants, current_plants, prefix):
    names = {"inspections": prefix + "_inspections", "plants": prefix + "_plants", "current": prefix + "_current"}
    inspections.createOrReplaceTempView(names["inspections"])
    plants.createOrReplaceTempView(names["plants"])
    current_plants.createOrReplaceTempView(names["current"])
    return names


def query(spark, template, names):
    return spark.sql(template.format(**names))
