"""A deliberately wrong promotion rule for lab L17: complete code, kept as the counterexample.

"Promote whichever run has the best accuracy" is what a hurried reader of the experiment table does.
It reads one metric, ignores the record behind it and ignores the baselines. On this experiment it
picks a run that trained on repair_minutes, a column written after the fault it predicts. The test
suite asserts that it does exactly that, and that the evidence gate rejects the run it picks.
"""
import mlflow


def pick_best_by_accuracy(experiment_id):
    """Return (run_id, run_name, accuracy) of the run MLflow sorts first by accuracy."""
    frame = mlflow.search_runs(experiment_ids=[experiment_id], order_by=["metrics.accuracy DESC"], max_results=1)
    row = frame.iloc[0]
    return row["run_id"], row["tags.mlflow.runName"], float(row["metrics.accuracy"])
