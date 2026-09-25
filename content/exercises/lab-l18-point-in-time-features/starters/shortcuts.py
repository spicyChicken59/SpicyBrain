"""lab-l18-point-in-time-features: four tempting shortcuts, all deliberately wrong.

Each one looks reasonable and runs without an error. Task 4 and Task 6 ask
you to predict what each does to the training set before running the tests,
which assert the exact rows each shortcut gets wrong and why.

1. join_on_feature_time        -- as-of join on the time the row DESCRIBES
2. latest_row_lookup           -- "the current value", used for history
3. overwrite_backfill          -- recompute every window once from today's data
4. join_on_availability_unchecked -- the right selection rule, no contract check

Plain pandas 3.0.6; these functions import nothing from solutions/.
"""
from __future__ import annotations

import pandas as pd

CARRIED = ["feature_time", "available_at", "temp_mean_2h", "vib_max_2h", "reading_count_2h",
           "vib_count_2h", "low_coverage", "source_max_ingested_at"]


def join_on_feature_time(labels: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    """WRONG: the latest window that ENDED by prediction_time, ignoring when it
    was published. A window ending 10:00 is published at 10:30, so a 10:15
    prediction gets a value that did not exist until 10:30."""
    right = features.sort_values(["feature_time", "available_at"], kind="stable")
    left = labels.sort_values("prediction_time", kind="stable")
    joined = pd.merge_asof(left, right, left_on="prediction_time", right_on="feature_time",
                           by="machine_id", direction="backward")
    return joined.sort_values(["machine_id", "prediction_time"], kind="stable").reset_index(drop=True)


def latest_row_lookup(labels: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    """WRONG for training: each machine's newest row in the table as it is
    today, whatever the prediction time. Correct at serving time only, where
    'today' and 'the prediction time' are the same instant."""
    latest = (features.sort_values(["machine_id", "feature_time", "available_at"], kind="stable")
              .groupby("machine_id").tail(1)[["machine_id"] + CARRIED])
    joined = labels.merge(latest, on="machine_id", how="left")
    return joined.sort_values(["machine_id", "prediction_time"], kind="stable").reset_index(drop=True)


def overwrite_backfill(observations: pd.DataFrame, contract: dict) -> pd.DataFrame:
    """WRONG: rebuild history in one pass from every reading ingested by the
    last run, one row per window, stamped with the NOMINAL publication time
    (window end + publish delay). Late readings are silently folded into rows
    that claim to have been available before those readings arrived."""
    last_run = max(pd.Timestamp(value) for value in contract["run_times"])
    known = observations[observations["ingested_at"] <= last_run].copy()
    known["feature_time"] = known["observed_at"].dt.ceil(pd.Timedelta(hours=contract["window_hours"]))
    known = known[known["feature_time"] <= last_run]
    table = known.groupby(["machine_id", "feature_time"], as_index=False).agg(
        temp_mean_2h=("temp_c", "mean"),
        vib_max_2h=("vibration_mm_s", "max"),
        reading_count_2h=("temp_c", "size"),
        vib_count_2h=("vibration_mm_s", "count"),
        source_max_ingested_at=("ingested_at", "max"),
    )
    table["low_coverage"] = table["reading_count_2h"] < contract["expected_readings_per_window"]
    table["available_at"] = table["feature_time"] + pd.Timedelta(minutes=contract["publish_delay_minutes"])
    columns = ["machine_id", "feature_time", "available_at", "temp_mean_2h", "vib_max_2h",
               "reading_count_2h", "vib_count_2h", "low_coverage", "source_max_ingested_at"]
    return table[columns].sort_values(["machine_id", "feature_time"], kind="stable").reset_index(drop=True)


def join_on_availability_unchecked(labels: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    """The correct selection rule (published by prediction_time, newest window,
    newest version) with no contract check and no guard. It trusts the table:
    duplicates are resolved by storage order and wrong availability stamps pass."""
    left = labels.reset_index(names="label_row")
    candidates = left.merge(features, on="machine_id", how="inner")
    candidates = candidates[candidates["available_at"] <= candidates["prediction_time"]]
    chosen = (candidates.sort_values(["label_row", "feature_time", "available_at"], kind="stable")
              .groupby("label_row", as_index=False).tail(1))
    joined = left.merge(chosen[["label_row"] + CARRIED], on="label_row", how="left").drop(columns="label_row")
    return joined.sort_values(["machine_id", "prediction_time"], kind="stable").reset_index(drop=True)
