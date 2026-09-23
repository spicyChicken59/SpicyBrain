"""Independent derivation of the expected literals for lab L17.

This script never imports the solution package and never touches MLflow. It reads the committed
fixture with the csv module into numpy arrays, counts the dataset facts and the two baselines with
numpy comparisons, and fits each model configuration with scikit-learn called directly on those
arrays (a StandardScaler fitted on the training rows, then LogisticRegression), without a Pipeline,
without pandas and without the solution's split helpers. It writes metrics.json; run_tests.py re-runs
derive() in memory and asserts the committed file matches, so the literals cannot drift from the
fixture. The derivations are described in DATA.md.
"""
import csv
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
FIXTURES = HERE.parent / "fixtures"
sys.path.insert(0, str(FIXTURES))
from generate_oven_days import TRANSFER_SEED, rows as generate_rows  # noqa: E402

FEATURES = ["oven_age_years", "days_since_service", "temp_mean_c", "temp_max_c", "door_cycles", "humidity_pct"]
LABEL = "fault_next_24h"
OVENS = 8
TRAIN_THROUGH_DAY = 84
RULE_THRESHOLD = 220.0
SEED = 20260923
HERO_HIDDEN_SEEDS = (11, 12)


def read_fixture():
    with (FIXTURES / "oven_days.csv").open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def arrays(records, features):
    X = np.array([[float(r[f]) for f in features] for r in records], dtype=np.float64)
    y = np.array([int(r[LABEL]) for r in records], dtype=np.int64)
    days = np.array([int(r["day"]) for r in records], dtype=np.int64)
    return X, y, days


def counts(y, pred):
    tp = int(np.sum((y == 1) & (pred == 1)))
    fp = int(np.sum((y == 0) & (pred == 1)))
    fn = int(np.sum((y == 1) & (pred == 0)))
    tn = int(np.sum((y == 0) & (pred == 0)))
    n = int(len(y))
    out = {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "rows": n, "warnings": tp + fp,
           "accuracy": round((tp + tn) / n, 4), "recall": round(tp / (tp + fn), 4) if tp + fn else 0.0,
           "warnings_per_day": round((tp + fp) / n * OVENS, 4)}
    out["precision"] = round(tp / (tp + fp), 4) if tp + fp else None
    return out


def fit_predict(X_train, y_train, X_test, C, seed):
    scaler = StandardScaler().fit(X_train)
    model = LogisticRegression(C=C, class_weight="balanced", max_iter=1000, random_state=seed)
    model.fit(scaler.transform(X_train), y_train)
    return model.predict(scaler.transform(X_test))


def time_split(records, through=TRAIN_THROUGH_DAY):
    train = [r for r in records if int(r["day"]) <= through]
    test = [r for r in records if int(r["day"]) > through]
    return train, test


def random_split(records, fraction, seed):
    order = np.random.default_rng(seed).permutation(len(records))
    cut = int(round(fraction * len(records)))
    return [records[i] for i in order[:cut]], [records[i] for i in order[cut:]]


def derive_dataset(records):
    train, test = time_split(records)
    return {"rows": len(records), "faults": sum(int(r[LABEL]) for r in records), "ovens": len({r["oven_id"] for r in records}),
            "days": len({r["day"] for r in records}), "train_rows": len(train),
            "train_faults": sum(int(r[LABEL]) for r in train), "test_rows": len(test),
            "test_faults": sum(int(r[LABEL]) for r in test), "train_max_day": max(int(r["day"]) for r in train),
            "test_min_day": min(int(r["day"]) for r in test)}


def derive_for(records):
    train, test = time_split(records)
    X_tr, y_tr, _ = arrays(train, FEATURES)
    X_te, y_te, _ = arrays(test, FEATURES)
    out = {"dataset": derive_dataset(records),
           "never_warn": counts(y_te, np.zeros(len(y_te), dtype=np.int64)),
           "temperature_rule": counts(y_te, (np.array([float(r["temp_max_c"]) for r in test]) >= RULE_THRESHOLD).astype(np.int64)),
           "time_split_C_1": counts(y_te, fit_predict(X_tr, y_tr, X_te, 1.0, SEED)),
           "time_split_C_0_01": counts(y_te, fit_predict(X_tr, y_tr, X_te, 0.01, SEED))}
    leak = FEATURES + ["repair_minutes"]
    X_tr, y_tr, _ = arrays(train, leak)
    X_te, y_te, _ = arrays(test, leak)
    out["time_split_leaky"] = counts(y_te, fit_predict(X_tr, y_tr, X_te, 1.0, SEED))
    r_train, r_test = random_split(records, 0.7, SEED)
    X_tr, y_tr, _ = arrays(r_train, FEATURES)
    X_te, y_te, _ = arrays(r_test, FEATURES)
    out["random_split_seeded"] = counts(y_te, fit_predict(X_tr, y_tr, X_te, 1.0, SEED))
    out["random_split_days"] = {"train_max_day": max(int(r["day"]) for r in r_train),
                                "test_min_day": min(int(r["day"]) for r in r_test),
                                "train_faults": sum(int(r[LABEL]) for r in r_train),
                                "test_faults": sum(int(r[LABEL]) for r in r_test)}
    for hidden in HERO_HIDDEN_SEEDS:
        h_train, h_test = random_split(records, 0.7, hidden)
        X_tr, y_tr, _ = arrays(h_train, leak)
        X_te, y_te, _ = arrays(h_test, leak)
        out[f"hero_hidden_seed_{hidden}"] = counts(y_te, fit_predict(X_tr, y_tr, X_te, 1.0, hidden))
    return out


def derive():
    fixture = derive_for(read_fixture())
    transfer_records = [{k: str(v) for k, v in r.items()} for r in generate_rows(TRANSFER_SEED)]
    transfer = derive_for(transfer_records)
    return {"fixture": fixture, "transfer": {"dataset": transfer["dataset"], "time_split_C_1": transfer["time_split_C_1"],
                                             "never_warn": transfer["never_warn"]}}


if __name__ == "__main__":
    (HERE / "metrics.json").write_text(json.dumps(derive(), indent=1) + "\n", encoding="utf-8")
    print("wrote metrics.json")
