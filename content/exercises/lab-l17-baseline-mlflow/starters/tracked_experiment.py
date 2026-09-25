"""Learner starter for lab L17. Predict first, then run and compare.

Fill PREDICTIONS from TASKS.md before writing code, then complete each function marked with its task
number. This file is self-contained: it does not import the reference solution, which lives under
solutions/ and is described in SOLUTIONS.md; read it only after your own attempt. Everything runs on
open-source MLflow 3.16.1 with a file store inside a temporary directory that is deleted on exit;
nothing talks to a tracking server, to Databricks or to the network.

    python starters/tracked_experiment.py
"""
import json
import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path

# Set before mlflow is imported: allow the maintenance-mode file store, send no telemetry.
os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")
os.environ.setdefault("MLFLOW_DISABLE_TELEMETRY", "true")
os.environ.setdefault("DO_NOT_TRACK", "true")
os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")

import mlflow  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ["oven_age_years", "days_since_service", "temp_mean_c", "temp_max_c", "door_cycles", "humidity_pct"]
LABEL = "fault_next_24h"
TRAIN_THROUGH_DAY = 84
DTYPES = {"oven_id": "string", "day": "int64", "date": "string", "oven_age_years": "float64",
          "days_since_service": "int64", "temp_mean_c": "float64", "temp_max_c": "float64", "door_cycles": "int64",
          "humidity_pct": "float64", "fault_next_24h": "int64", "repair_minutes": "int64", "fault_code": "string"}

# Write your predictions before running anything. Each one is checkable against your own experiment.
PREDICTIONS = {
    "never_warn_accuracy_on_test": None,       # 18 faults in 288 test rows: what accuracy does "never warn" get?
    "run_with_highest_accuracy": None,         # which run tops search_runs ordered by accuracy?
    "leaked_columns": None,                    # which columns does the data dictionary date after 09:00?
    "runs_that_pass_the_evidence_gate": None,  # which runs carry a time split, seed, digest and matching signature?
    "reproducible_from_record": None,          # which runs can be rerun from their logged record alone?
    "mlflow_accepts_an_extra_column": None,    # does pyfunc schema enforcement reject an extra input column?
}


@contextmanager
def tracking_directory(prefix="l17-learner-"):
    """Given, not a task: a temporary file-store tracking directory that is deleted on exit."""
    previous = mlflow.get_tracking_uri()
    root = Path(tempfile.mkdtemp(prefix=prefix))
    mlflow.set_tracking_uri(root.as_uri())
    try:
        yield root
    finally:
        mlflow.set_tracking_uri(previous)
        shutil.rmtree(root, ignore_errors=True)


def load_oven_days(path=ROOT / "fixtures" / "oven_days.csv"):
    """Given: the fixture with explicit types; an empty fault_code stays an empty string."""
    return pd.read_csv(path, dtype=DTYPES, keep_default_na=False)


def load_dictionary(path=ROOT / "fixtures" / "data_dictionary.json"):
    """Given: the data dictionary, which says when each column becomes available."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def split_by_day(frame, train_through_day=TRAIN_THROUGH_DAY):
    """Given: days up to and including the cut-off train, later days test."""
    return (frame[frame["day"] <= train_through_day].reset_index(drop=True),
            frame[frame["day"] > train_through_day].reset_index(drop=True))


def split_random(frame, fraction=0.7, seed=None):
    """Given: a random row split. With seed=None the permutation cannot be reproduced."""
    order = np.random.default_rng(seed).permutation(len(frame))
    cut = int(round(fraction * len(frame)))
    return frame.iloc[order[:cut]].reset_index(drop=True), frame.iloc[order[cut:]].reset_index(drop=True)


def leakage_report(features, dictionary):
    """Task 2: return the proposed features that are not available at 09:00, each with a reason."""
    raise NotImplementedError("Task 2: read the dictionary's available_at and role, not the correlation")


def split_report(train, test):
    """Task 2: return row counts and whether every test day comes after every training day."""
    raise NotImplementedError("Task 2: a time split has train max day < test min day")


def train_time_split(frame, *, experiment_id, run_name, C, seed):
    """Task 3: one run whose record could rerun it: params (C, seed, split, features, library version),
    the training and evaluation datasets, metrics, a signature, an input example and artifacts."""
    raise NotImplementedError("Task 3: log everything a rerun would need")


def reproduce(run_id, frame, *, experiment_id):
    """Task 5: rerun from the logged record only; raise, naming what is missing, when it cannot."""
    raise NotImplementedError("Task 5: refuse, do not guess")


def check_signature(contract, signature):
    """Task 6: compare the logged signature with the contract; list missing, unexpected and retyped inputs."""
    raise NotImplementedError("Task 6: the contract rejects drift by name and type")


def decide(contract, run_id):
    """Task 7: evidence gate first, thresholds second; return the decision with its sorted reasons."""
    raise NotImplementedError("Task 7: metrics are read only after the record has passed")


if __name__ == "__main__":
    with tracking_directory() as root:
        frame = load_oven_days()
        train, test = split_by_day(frame)
        print("tracking in", root)
        print("rows", len(frame), "train", len(train), "test", len(test), "test faults", int(test[LABEL].sum()))
        print("dictionary roles:", {c["name"]: c["role"] for c in load_dictionary()["columns"]})
        r_train, r_test = split_random(frame, 0.7, 1)
        print("a random split tests on day", int(r_test["day"].min()), "while training reaches day",
              int(r_train["day"].max()))
        print("your predictions:", PREDICTIONS)
