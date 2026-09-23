"""Learner starter for lab L04. Predict first, then run and compare.

Fill the PREDICTIONS dictionary from TASKS.md before writing code, then complete
each function. The reference functions in solutions/execution_evidence.py are
the answer key; consult SOLUTIONS.md after your own attempt.

Run from the lab directory:  python starters/execution_task.py
"""
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["PYSPARK_PYTHON"] = sys.executable  # Python workers must match the driver's interpreter
os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")

from pyspark.sql import functions as F  # noqa: E402

from solutions.execution_evidence import (  # noqa: E402  helpers you may reuse: session, loading, measurement
    build_session, count_nodes, load_inspections, load_plants, measure, partition_rows, plan_text, stage_metrics,
)

# Write your predictions before running anything. Each is checkable against Spark's own output.
PREDICTIONS = {
    "exchanges_in_grouped_plan": None,          # how many Exchange nodes does groupBy('plant').sum need?
    "tasks_in_grouped_reduce_stage": None,      # with spark.sql.shuffle.partitions=4 and adaptive execution off
    "records_written_by_grouped_map_stage": None,  # partial rows that cross the Exchange (not raw rows)
    "exchanges_in_sort_merge_join_plan": None,  # join + regional sum, broadcast disabled
    "exchanges_in_broadcast_join_plan": None,   # same query with F.broadcast(plants)
    "fact_rows_shuffled_by_broadcast_join": None,  # how many of the 240 fact rows cross a shuffle?
    "largest_partition_after_repartition_by_plant": None,  # the fixture has 180 North rows
    "build_side_chosen_by_adaptive_execution": None,       # BuildLeft, BuildRight, or "cannot say in advance"?
}


def grouped_totals(df):
    """Return rows/inspected/defective per plant. Then capture plan_text() and count Exchange nodes."""
    raise NotImplementedError("Task 2: build the grouped frame and inspect its plan and its shuffle records")


def join_two_ways(df, plants):
    """Return (sort_merge_frame, broadcast_frame): the same regional sum with and without F.broadcast."""
    raise NotImplementedError("Task 3: build both joins; compare Exchange counts, stages and shuffled records")


def hot_key_distribution(df, partitions):
    """Return rows per partition after repartition(partitions, 'plant'). Try 4, 8 and 16."""
    raise NotImplementedError("Task 4: measure where the North rows land; explain why the maximum never drops")


def safe_rows(df, max_rows):
    """Return collected rows only when at most max_rows would reach the driver; otherwise raise ValueError."""
    raise NotImplementedError("Task 6: guard the collection before calling collect()")


if __name__ == "__main__":
    scratch = Path(tempfile.mkdtemp(prefix="lab-l04-learner-"))
    spark = build_session("SpicyBrain lab L04 learner", local_dir=scratch / "local", warehouse_dir=scratch / "warehouse")
    try:
        inspections = load_inspections(spark)
        plants = load_plants(spark)
        inspections.printSchema()
        print("input partitions:", inspections.rdd.getNumPartitions())
        narrow = inspections.filter(F.col("defective_units") > 0)
        print(plan_text(narrow))
        print("Exchange nodes:", count_nodes(plan_text(narrow), "Exchange"))
        rows, measured = measure(spark, "narrow", lambda: len(narrow.collect()))
        print("rows:", rows, "executed stage tasks:", measured["executed_stage_tasks"])
        print("rows per partition:", partition_rows(narrow))
        print("shuffle records per stage:", [(s["shuffle_read_records"], s["shuffle_write_records"])
                                             for s in stage_metrics(spark, measured)])
    finally:
        spark.stop()
        shutil.rmtree(scratch, ignore_errors=True)
