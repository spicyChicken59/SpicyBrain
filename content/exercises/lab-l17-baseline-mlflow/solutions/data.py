"""Loading, splitting and the two leakage checks for lab L17.

Everything here is plain pandas. The checks read the data dictionary, not the model: a feature is
rejected because of WHEN it is recorded, and a split is rejected because of WHERE its test rows sit
in time. Neither check looks at a metric, which is why a metric cannot talk them out of a verdict.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "oven_days.csv"
DICTIONARY = ROOT / "fixtures" / "data_dictionary.json"

FEATURES = ["oven_age_years", "days_since_service", "temp_mean_c", "temp_max_c", "door_cycles", "humidity_pct"]
LABEL = "fault_next_24h"
OVENS = 8
TRAIN_THROUGH_DAY = 84  # weeks 1 to 12 train; days 85 to 120 are the held-out future
DTYPES = {"oven_id": "string", "day": "int64", "date": "string", "oven_age_years": "float64",
          "days_since_service": "int64", "temp_mean_c": "float64", "temp_max_c": "float64", "door_cycles": "int64",
          "humidity_pct": "float64", "fault_next_24h": "int64", "repair_minutes": "int64", "fault_code": "string"}


def load_oven_days(path=FIXTURE):
    """Read the fixture with explicit types; an empty fault_code is an empty string, never NaN."""
    frame = pd.read_csv(path, dtype=DTYPES, keep_default_na=False)
    return frame


def frame_from_records(records):
    """Build the same typed frame from generator records (used by the transfer test)."""
    frame = pd.DataFrame(records)
    for column, dtype in DTYPES.items():
        frame[column] = frame[column].astype(dtype)
    return frame


def load_dictionary(path=DICTIONARY):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def feature_frame(frame, features=FEATURES):
    """Model inputs as float64 columns, in the contract's order: the signature is inferred from this."""
    return frame[list(features)].astype("float64")


def split_by_day(frame, train_through_day=TRAIN_THROUGH_DAY):
    """Time-based split: everything up to and including the cut-off day trains; later days test."""
    train = frame[frame["day"] <= train_through_day].reset_index(drop=True)
    test = frame[frame["day"] > train_through_day].reset_index(drop=True)
    return train, test


def split_random(frame, fraction=0.7, seed=None):
    """Random row split. With seed=None the permutation cannot be reproduced later; that is the point."""
    order = np.random.default_rng(seed).permutation(len(frame))
    cut = int(round(fraction * len(frame)))
    train = frame.iloc[order[:cut]].reset_index(drop=True)
    test = frame.iloc[order[cut:]].reset_index(drop=True)
    return train, test


def leakage_report(features, dictionary=None):
    """Flag every proposed feature the dictionary says is not available at the prediction moment."""
    dictionary = dictionary or load_dictionary()
    moment = dictionary["prediction_moment"]
    columns = {c["name"]: c for c in dictionary["columns"]}
    flagged = []
    for name in features:
        column = columns.get(name)
        if column is None:
            flagged.append({"feature": name, "reason": "unknown_column", "available_at": None})
        elif column["role"] == "label":
            flagged.append({"feature": name, "reason": "is_the_label", "available_at": column["available_at"]})
        elif column["role"] == "post_event" or column["available_at"] != "09:00":
            flagged.append({"feature": name, "reason": "recorded_after_prediction", "available_at": column["available_at"]})
    return {"prediction_moment": moment, "features": list(features), "flagged": flagged, "ok": not flagged}


def split_report(train, test):
    """A split is time-based only when every test row is later than every training row."""
    train_max, test_min = int(train["day"].max()), int(test["day"].min())
    ok = train_max < test_min
    return {"train_rows": int(len(train)), "test_rows": int(len(test)), "train_max_day": train_max,
            "test_min_day": test_min, "train_positives": int(train[LABEL].sum()),
            "test_positives": int(test[LABEL].sum()), "kind": "time" if ok else "not_time_ordered", "ok": ok,
            "reason": None if ok else f"test rows start on day {test_min}, before training ends on day {train_max}"}
