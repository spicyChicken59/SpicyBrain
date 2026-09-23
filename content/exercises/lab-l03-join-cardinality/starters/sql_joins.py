"""Starter: Spark SQL. Complete each template; keep the names."""

DUPLICATE_KEYS_SQL = """
SELECT plant_id, COUNT(*) AS row_count
FROM {plants}
GROUP BY plant_id
-- TODO: keep only repeated keys, ordered by plant_id
"""

NAIVE_TOTALS_SQL = """
SELECT COUNT(*) AS row_count, SUM(i.inspected_units) AS inspected, SUM(i.defective_units) AS defective
FROM {inspections} i
JOIN {plants} p ON i.plant_id = p.plant_id
"""

CURRENT_PLANTS_SQL = """
-- TODO: ROW_NUMBER() OVER (PARTITION BY plant_id ORDER BY valid_from DESC, row_source DESC) = 1
SELECT plant_id, plant_name, region, manager, valid_from, row_source FROM {plants}
"""

REGION_REPORT_SQL = """
SELECT p.region, COUNT(*) AS inspections
       -- TODO: inspected, defective, guarded weighted defect_rate
FROM {inspections} i
JOIN {current} p ON i.plant_id = p.plant_id   -- TODO: which join keeps inspections of an unknown plant?
GROUP BY p.region
"""

PLANT_COUNTS_SQL = """
SELECT p.plant_id, COUNT(*) AS inspection_count   -- TODO: COUNT(*) versus COUNT(i.inspection_id); inspected_sum; COALESCE
FROM {current} p
LEFT JOIN {inspections} i ON p.plant_id = i.plant_id
GROUP BY p.plant_id
"""

RATES_SQL = """
SELECT plant_id,
       AVG(defective_units / inspected_units) AS average_of_rates   -- TODO: this raises in ANSI mode on 0/0; and it is the wrong metric
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
