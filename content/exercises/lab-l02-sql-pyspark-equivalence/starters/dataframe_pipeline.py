"""Starter: DataFrame API stages. Fill every TODO; keep the stage names.

Use Column expressions: & and | with parentheses, isNull()/isNotNull(),
F.when().when() chains, F.count/F.sum with alias(). Python and/or and == None
do not build Spark predicates (Task 5 shows what they do instead).
"""
from pyspark.sql import functions as F


def reason_column():
    return (F.when(F.col("plant_id").isNull(), F.lit("missing_plant"))
             # TODO: missing_units when either quantity is null
             # TODO: negative_units when either quantity is below zero
             # TODO: defects_exceed_inspected
             )


def dataframe_stages(events, plants):
    distinct = events.distinct()
    classified = distinct.withColumn("reason", reason_column())
    rejected = None  # TODO
    accepted = None  # TODO: drop the reason column
    totals = accepted.groupBy("plant_id").agg(
        F.count("*").alias("inspections"),
        # TODO: inspected and defective sums with these exact aliases
    )
    report = None  # TODO: left join to plants; select the seven report columns; unit-weighted defect_rate, null when inspected is 0
    return {"distinct": distinct, "classified": classified, "rejected": rejected,
            "accepted": accepted, "report": report}


def null_plant_events(distinct):
    return distinct.filter(F.col("plant_id") == None)  # noqa: E711  TODO: this returns no rows; correct it and explain why


def known_plant_count(distinct):
    return distinct.select("plant_id").distinct().count()  # TODO: this counts the unknown plant as a plant; apply the contract
