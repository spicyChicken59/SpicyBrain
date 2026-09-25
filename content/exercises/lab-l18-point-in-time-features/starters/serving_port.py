"""lab-l18-point-in-time-features: a serving-side port of the transformation.

A fictional service team re-wrote `compute_features` for a request path
instead of importing it. It reads cleanly and matches the training output on
the 08:30 run. It has two drifts from the contract; Task 5 asks you to find
them with the consistency check, not by reading this file first.

Deliberately wrong. Plain pandas 3.0.6; imports nothing from solutions/.
"""
from __future__ import annotations

import pandas as pd

COLUMNS = ["machine_id", "feature_time", "available_at", "temp_mean_2h", "vib_max_2h",
           "reading_count_2h", "vib_count_2h", "low_coverage", "source_max_ingested_at"]


def compute_features_port(observations: pd.DataFrame, run_at: pd.Timestamp, contract: dict) -> pd.DataFrame:
    window = pd.Timedelta(hours=contract["window_hours"])
    known = observations[observations["ingested_at"] <= run_at].copy()
    # bucket each reading by the start of its window, then name the window by its end
    known["feature_time"] = known["observed_at"].dt.floor(window) + window
    known = known[known["feature_time"] <= run_at]
    # a sensor that sent nothing is treated as a sensor that read zero
    known["vibration_mm_s"] = known["vibration_mm_s"].fillna(0.0)
    grouped = known.groupby(["machine_id", "feature_time"], as_index=False).agg(
        temp_mean_2h=("temp_c", "mean"),
        vib_max_2h=("vibration_mm_s", "max"),
        reading_count_2h=("temp_c", "size"),
        vib_count_2h=("vibration_mm_s", "count"),
        source_max_ingested_at=("ingested_at", "max"),
    )
    grouped["reading_count_2h"] = grouped["reading_count_2h"].astype("int64")
    grouped["vib_count_2h"] = grouped["vib_count_2h"].astype("int64")
    grouped["low_coverage"] = grouped["reading_count_2h"] < contract["expected_readings_per_window"]
    grouped["available_at"] = run_at
    return grouped[COLUMNS].sort_values(["machine_id", "feature_time"], kind="stable").reset_index(drop=True)
