"""Starter: DataFrame API. Fill every TODO; keep the function names.

The runner (and TASKS.md) expects: duplicate_keys, naive_join, totals,
current_plants_by_window, current_plants_by_aggregate, has_ties,
matched_join, unmatched_inspections, region_report, plants_with_counts,
weighted_and_averaged.
"""
from pyspark.sql import Window, functions as F


def totals(frame):
    row = frame.agg(F.count("*").alias("row_count"),
                    F.sum("inspected_units").alias("inspected"),
                    F.sum("defective_units").alias("defective")).first()
    return {"row_count": row["row_count"], "inspected": row["inspected"], "defective": row["defective"]}


def duplicate_keys(plants):
    raise NotImplementedError("TODO: plant_id and row_count for keys that appear more than once")


def naive_join(inspections, plants):
    return inspections.join(plants, "plant_id", "inner")  # keep: this is the mistake under study


def current_plants_by_window(plants):
    window = Window.partitionBy("plant_id").orderBy(F.col("valid_from").desc())  # TODO: add the tie-break
    raise NotImplementedError("TODO: row_number over the window, keep rank 1, drop the rank column")


def has_ties(plants):
    raise NotImplementedError("TODO: true when any (plant_id, valid_from) pair repeats")


def current_plants_by_aggregate(plants):
    raise NotImplementedError("TODO: groupBy plant_id with max_by(column, valid_from) for each attribute")


def matched_join(inspections, current_plants, how):
    return inspections.join(current_plants, "plant_id", how)


def unmatched_inspections(inspections, current_plants):
    raise NotImplementedError("TODO: left_anti join")


def region_report(inspections, current_plants):
    raise NotImplementedError("TODO: left join, group by region, count/sum/sum, guarded weighted defect_rate")


def plants_with_counts(current_plants, inspections):
    joined = current_plants.join(inspections, "plant_id", "left")
    return joined.groupBy("plant_id").agg(F.count("*").alias("inspection_count"))  # TODO: this counts the null row; fix and add inspected_sum / inspected


def weighted_and_averaged(inspections):
    # TODO: weighted_rate from summed units; average_of_rates via AVG of try_divide row rates;
    # rate_rows = COUNT(row_rate); row_count = COUNT(*)
    raise NotImplementedError
