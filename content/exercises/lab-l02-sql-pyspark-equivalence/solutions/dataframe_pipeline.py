"""PySpark DataFrame version of the same staged transformation.

Each stage mirrors sql_pipeline.py. "Equivalent" means the same rows and the
same schema under this engine and these fixtures, checked deliberately; it is
not a claim about textual similarity or performance.
"""
from pyspark.sql import functions as F


def reason_column():
    # A chained when() without otherwise() is null for rows that pass: that null
    # is the acceptance signal, so the reason column must stay nullable string.
    return (F.when(F.col("plant_id").isNull(), F.lit("missing_plant"))
             .when(F.col("inspected_units").isNull() | F.col("defective_units").isNull(), F.lit("missing_units"))
             .when((F.col("inspected_units") < 0) | (F.col("defective_units") < 0), F.lit("negative_units"))
             .when(F.col("defective_units") > F.col("inspected_units"), F.lit("defects_exceed_inspected")))


def dataframe_stages(events, plants):
    distinct = events.distinct()
    classified = distinct.withColumn("reason", reason_column())
    rejected = classified.filter(F.col("reason").isNotNull())
    accepted = classified.filter(F.col("reason").isNull()).drop("reason")
    totals = accepted.groupBy("plant_id").agg(
        F.count("*").alias("inspections"),
        F.sum("inspected_units").alias("inspected"),
        F.sum("defective_units").alias("defective"))
    report = (totals.join(plants, "plant_id", "left")
              .select("plant_id", "plant_name", "region", "inspections", "inspected", "defective",
                      F.when(F.col("inspected") > 0, F.col("defective").cast("double") / F.col("inspected"))
                       .otherwise(F.lit(None).cast("double")).alias("defect_rate")))
    return {"distinct": distinct, "classified": classified, "rejected": rejected,
            "accepted": accepted, "report": report}


def null_plant_events_wrong(distinct):
    # Deliberately wrong: == None becomes "plant_id = NULL", unknown for every row.
    return distinct.filter(F.col("plant_id") == None)  # noqa: E711


def null_plant_events(distinct):
    return distinct.filter(F.col("plant_id").isNull())


def known_plant_count_wrong(distinct):
    # distinct() treats null as one more distinct value; COUNT(DISTINCT) does not.
    return distinct.select("plant_id").distinct().count()


def known_plant_count(distinct):
    # The contract: an unknown plant is not a plant. Say so with an explicit null test.
    return distinct.filter(F.col("plant_id").isNotNull()).select("plant_id").distinct().count()
