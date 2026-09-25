"""DataFrame API: the multiplying join, its diagnosis, two repairs, and the
two metric traps (average of rates; left-join null counts).

Nothing here decides which dimension version is "right" by accident: the
current-row rule is explicit (latest valid_from, tie-break row_source desc)
and the aggregate variant is checked for ties before it is trusted.
"""
from pyspark.sql import Window, functions as F

def current_order():
    # Built on demand: a Column expression needs a live session in classic PySpark.
    return [F.col("valid_from").desc(), F.col("row_source").desc()]


def rate(numerator, denominator):
    # Unit-weighted rate over totals; NULL, not an error, for a zero denominator.
    return F.when(F.col(denominator) > 0, F.col(numerator).cast("double") / F.col(denominator))


def totals(frame):
    """Row count and unit totals of any inspection-bearing relation, as one dict."""
    row = frame.agg(F.count("*").alias("row_count"),
                    F.sum("inspected_units").alias("inspected"),
                    F.sum("defective_units").alias("defective")).first()
    return {"row_count": row["row_count"], "inspected": row["inspected"], "defective": row["defective"]}


def duplicate_keys(plants):
    return (plants.groupBy("plant_id").agg(F.count("*").alias("row_count"))
            .filter(F.col("row_count") > 1))


def naive_join(inspections, plants):
    # The plausible mistake: joining the fact to a dimension whose key repeats.
    return inspections.join(plants, "plant_id", "inner")


def by_region(joined):
    return joined.groupBy("region").agg(F.count("*").alias("inspections"),
                                        F.sum("inspected_units").alias("inspected"),
                                        F.sum("defective_units").alias("defective"))


def aggregate_then_join(inspections, plants):
    # Aggregating the fact side first does NOT remove a duplicate on the dimension side.
    plant_totals = inspections.groupBy("plant_id").agg(F.sum("inspected_units").alias("inspected_units"),
                                                       F.sum("defective_units").alias("defective_units"))
    return plant_totals.join(plants, "plant_id", "inner")


def current_plants_by_window(plants):
    # Repair 1: an explicit rule picks one version per key.
    window = Window.partitionBy("plant_id").orderBy(*current_order())
    return (plants.withColumn("version_rank", F.row_number().over(window))
            .filter(F.col("version_rank") == 1).drop("version_rank"))


def has_ties(plants):
    return (plants.groupBy("plant_id", "valid_from").agg(F.count("*").alias("n"))
            .filter(F.col("n") > 1).count() > 0)


def current_plants_by_aggregate(plants):
    # Repair 2: aggregate the dimension to its key with max_by on the ordering column.
    # max_by has no tie-break; the caller must check has_ties() first.
    return plants.groupBy("plant_id").agg(
        F.max_by("plant_name", "valid_from").alias("plant_name"),
        F.max_by("region", "valid_from").alias("region"),
        F.max_by("manager", "valid_from").alias("manager"),
        F.max("valid_from").alias("valid_from"),
        F.max_by("row_source", "valid_from").alias("row_source"))


def matched_join(inspections, current_plants, how):
    return inspections.join(current_plants, "plant_id", how)


def unmatched_inspections(inspections, current_plants):
    return inspections.join(current_plants, "plant_id", "left_anti")


def region_report(inspections, current_plants):
    joined = matched_join(inspections, current_plants, "left")
    return (joined.groupBy("region")
            .agg(F.count("*").alias("inspections"),
                 F.sum("inspected_units").alias("inspected"),
                 F.sum("defective_units").alias("defective"))
            .withColumn("defect_rate", rate("defective", "inspected")))


def plants_with_counts(current_plants, inspections):
    # Left-join null-count trap: COUNT(*) counts the null row a plant without
    # inspections produces; COUNT(column) does not.
    joined = current_plants.join(inspections, "plant_id", "left")
    return (joined.groupBy("plant_id")
            .agg(F.count("*").alias("row_count"),
                 F.count("inspection_id").alias("inspection_count"),
                 F.sum("inspected_units").alias("inspected_sum"),
                 F.coalesce(F.sum("inspected_units"), F.lit(0)).alias("inspected")))


def weighted_and_averaged(inspections):
    # try_divide: ANSI mode raises on 0/0; NULL here is then ignored by AVG -- the trap.
    row_rate = F.try_divide(F.col("defective_units").cast("double"), F.col("inspected_units"))
    return (inspections.withColumn("row_rate", row_rate)
            .groupBy("plant_id")
            .agg(F.sum("inspected_units").alias("inspected"),
                 F.sum("defective_units").alias("defective"),
                 F.avg("row_rate").alias("average_of_rates"),
                 F.count("row_rate").alias("rate_rows"),
                 F.count("*").alias("row_count"))
            .select("plant_id", rate("defective", "inspected").alias("weighted_rate"),
                    "average_of_rates", "rate_rows", "row_count"))
