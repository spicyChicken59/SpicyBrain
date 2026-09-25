"""Tracked training runs for lab L17 on open-source MLflow 3.16.1 with a local file store.

Five kinds of run share one experiment:
  never-warn, temperature-rule   the two baselines, logged as runs so they sit in the same table;
  time-split-*                   clean runs: time split, dictionary-checked features, seed, dataset
                                 digest, signature, artifacts and the captured environment;
  random-split-seeded            the same logging discipline over a random split (a leaking split);
  time-split-leaky               the same discipline with a post-event feature (a leaking feature):
                                 a complete, honest record of an invalid experiment;
  hero                           the run that looks best: the post-event feature, an unrecorded
                                 random split, no seed, no dataset, no signature.
reproduce() reruns a run from nothing but its logged record, or refuses and names what is missing.
"""
from dataclasses import dataclass, field

import mlflow
import mlflow.data
import mlflow.sklearn
import pandas as pd
import sklearn
from mlflow.models import infer_signature
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from solutions.data import (FEATURES, LABEL, OVENS, TRAIN_THROUGH_DAY, feature_frame, leakage_report, split_by_day,
                            split_random, split_report)
from solutions.tracking import tracking_directory  # noqa: F401  (sets the MLflow environment before mlflow use)

SEED = 20260923
RULE_THRESHOLD_C = 220.0
MODEL_NAME = "logistic_regression"
DATASET_SOURCE = "fixtures/oven_days.csv"
REQUIRED_PARAMS = ("model", "C", "class_weight", "max_iter", "seed", "split", "features")
SPLIT_PARAMS = {"time": "train_through_day", "random": "train_fraction"}


class ReproductionRefused(ValueError):
    """The run's record cannot support a rerun: something is not recorded, or the environment differs."""

    def __init__(self, missing=(), mismatched=()):
        self.missing = list(missing)
        self.mismatched = list(mismatched)
        parts = []
        if self.missing:
            parts.append("not recorded: " + ", ".join(self.missing))
        if self.mismatched:
            parts.append("environment differs: " + ", ".join(self.mismatched))
        super().__init__("cannot reproduce this run: " + "; ".join(parts))


@dataclass
class RunResult:
    run_id: str
    run_name: str
    metrics: dict
    model_uri: str | None = None
    model_id: str | None = None
    dataset_digest: str | None = None
    signature: dict | None = None
    checks: dict = field(default_factory=dict)


def metrics_from(y_true, y_pred):
    """Confusion counts and the three rates the contract reads, plus warnings per day over the fleet."""
    y_true, y_pred = [int(v) for v in y_true], [int(v) for v in y_pred]
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    n = len(y_true)
    metrics = {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "rows": n, "warnings": tp + fp,
               "accuracy": (tp + tn) / n, "recall": tp / (tp + fn) if tp + fn else 0.0,
               "warnings_per_day": (tp + fp) / n * OVENS}
    if tp + fp:
        metrics["precision"] = tp / (tp + fp)  # undefined when nothing was warned: then it is simply absent
    return metrics


def make_model(C, seed, class_weight="balanced", max_iter=1000):
    """Scaling lives inside the pipeline so it is fitted on training rows only."""
    return Pipeline([("scale", StandardScaler()),
                     ("model", LogisticRegression(C=C, class_weight=class_weight, max_iter=max_iter,
                                                  random_state=seed))])


def dataset_of(rows, name):
    """The rows a run saw, as an MLflow dataset. All columns are kept: the dataset pins the rows, and
    the "features" parameter says which columns the model used, so a feature ablation shares a digest."""
    return mlflow.data.from_pandas(rows, source=DATASET_SOURCE, name=name, targets=LABEL)


def log_baselines(test, *, experiment_id, rule_threshold=RULE_THRESHOLD_C):
    """Two baselines as runs over the same test days: never warn, and the plant's temperature rule."""
    results = {}
    evaluation = dataset_of(test, "oven-days-test")
    with mlflow.start_run(experiment_id=experiment_id, run_name="never-warn") as run:
        mlflow.log_params({"model": "never_warn", "role": "baseline", "split": "time",
                           "train_through_day": TRAIN_THROUGH_DAY})
        mlflow.log_input(evaluation, context="evaluation")
        metrics = metrics_from(test[LABEL], [0] * len(test))
        mlflow.log_metrics(metrics)
        results["never-warn"] = RunResult(run.info.run_id, "never-warn", metrics)
    with mlflow.start_run(experiment_id=experiment_id, run_name="temperature-rule") as run:
        mlflow.log_params({"model": "temperature_rule", "role": "baseline", "rule": f"temp_max_c >= {rule_threshold}",
                           "split": "time", "train_through_day": TRAIN_THROUGH_DAY})
        mlflow.log_input(evaluation, context="evaluation")
        metrics = metrics_from(test[LABEL], (test["temp_max_c"] >= rule_threshold).astype(int))
        mlflow.log_metrics(metrics)
        results["temperature-rule"] = RunResult(run.info.run_id, "temperature-rule", metrics)
    return results


def _fit_and_log(train, test, *, experiment_id, run_name, features, C, seed, split_params,
                 class_weight="balanced", max_iter=1000):
    """One fully recorded run: params, datasets, checks, metrics, signature, input example, artifacts."""
    leakage = leakage_report(features)
    split = split_report(train, test)
    X_train, X_test = feature_frame(train, features), feature_frame(test, features)
    train_ds, test_ds = dataset_of(train, "oven-days-train"), dataset_of(test, "oven-days-test")
    with mlflow.start_run(experiment_id=experiment_id, run_name=run_name) as run:
        mlflow.log_params({"model": MODEL_NAME, "C": C, "class_weight": class_weight, "max_iter": max_iter,
                           "seed": seed, "features": ",".join(features), "scikit_learn": sklearn.__version__,
                           **split_params})
        mlflow.log_input(train_ds, context="training")
        mlflow.log_input(test_ds, context="evaluation")
        mlflow.log_dict(leakage, "checks/leakage_report.json")
        mlflow.log_dict(split, "checks/split_report.json")
        model = make_model(C, seed, class_weight, max_iter).fit(X_train, train[LABEL])
        predictions = model.predict(X_test)
        metrics = metrics_from(test[LABEL], predictions)
        # The output is named so the signature says what the model returns, not just an int64 tensor.
        signature = infer_signature(X_train, pd.Series(model.predict(X_train.head(5)), name=LABEL))
        info = mlflow.sklearn.log_model(model, name="model", signature=signature, input_example=X_train.head(3))
        mlflow.log_metrics(metrics, model_id=info.model_id)
        mlflow.log_dict(metrics, "evaluation/metrics.json")
        mlflow.log_dict({"labels": [0, 1], "matrix": [[metrics["tn"], metrics["fp"]], [metrics["fn"], metrics["tp"]]]},
                        "evaluation/confusion_matrix.json")
    return RunResult(run.info.run_id, run_name, metrics, info.model_uri, info.model_id, train_ds.digest,
                     signature.to_dict(), {"leakage": leakage, "split": split})


def train_time_split(frame, *, experiment_id, run_name, C=1.0, seed=SEED, train_through_day=TRAIN_THROUGH_DAY,
                     features=FEATURES, class_weight="balanced", max_iter=1000):
    train, test = split_by_day(frame, train_through_day)
    return _fit_and_log(train, test, experiment_id=experiment_id, run_name=run_name, features=features, C=C,
                        seed=seed, split_params={"split": "time", "train_through_day": train_through_day},
                        class_weight=class_weight, max_iter=max_iter)


def train_random_split(frame, *, experiment_id, run_name, C=1.0, seed=SEED, fraction=0.7, features=FEATURES,
                       class_weight="balanced", max_iter=1000):
    train, test = split_random(frame, fraction, seed)
    return _fit_and_log(train, test, experiment_id=experiment_id, run_name=run_name, features=features, C=C,
                        seed=seed, split_params={"split": "random", "train_fraction": fraction},
                        class_weight=class_weight, max_iter=max_iter)


def train_hero(frame, *, experiment_id, run_name="hero", hidden_seed=None):
    """The run that looks best. A random split whose seed is used but never logged, a post-event feature
    (repair_minutes), no dataset, no feature list and no signature. With hidden_seed=None the split
    is different on every execution; the tests pass fixed hidden seeds so they can check the result."""
    features = FEATURES + ["repair_minutes"]
    train, test = split_random(frame, 0.7, hidden_seed)
    with mlflow.start_run(experiment_id=experiment_id, run_name=run_name) as run:
        mlflow.log_param("model", MODEL_NAME)
        model = make_model(1.0, hidden_seed).fit(feature_frame(train, features), train[LABEL])
        metrics = metrics_from(test[LABEL], model.predict(feature_frame(test, features)))
        info = mlflow.sklearn.log_model(model, name="model")
        mlflow.log_metrics(metrics, model_id=info.model_id)
    return RunResult(run.info.run_id, run_name, metrics, info.model_uri, info.model_id)


def training_digest(run_id):
    """The digest of the dataset a run logged with context "training", or None."""
    for item in mlflow.get_run(run_id).inputs.dataset_inputs:
        if any(t.key == "mlflow.data.context" and t.value == "training" for t in item.tags):
            return item.dataset.digest
    return None


def reproduce(run_id, frame, *, experiment_id, run_name=None):
    """Rerun a run from its own record only.

    Refuses, naming every gap, when a parameter the rerun needs, the split's own parameter or the
    training dataset is not recorded, or when the recorded scikit-learn version is not the installed
    one. Otherwise it retrains and reports whether the data digest and every metric came back equal.
    """
    run = mlflow.get_run(run_id)
    params = run.data.params
    missing = [key for key in REQUIRED_PARAMS if key not in params]
    split_key = SPLIT_PARAMS.get(params.get("split"))
    if split_key and split_key not in params:
        missing.append(split_key)
    original_digest = training_digest(run_id)
    if original_digest is None:
        missing.append("training_dataset")
    mismatched = []
    if "scikit_learn" not in params:
        missing.append("scikit_learn")
    elif params["scikit_learn"] != sklearn.__version__:
        mismatched.append(f"scikit-learn {params['scikit_learn']} recorded, {sklearn.__version__} installed")
    if missing or mismatched:
        raise ReproductionRefused(sorted(missing), mismatched)
    features = params["features"].split(",")
    common = dict(experiment_id=experiment_id, run_name=run_name or f"{run.info.run_name}-rerun",
                  C=float(params["C"]), seed=int(params["seed"]), features=features,
                  class_weight=params["class_weight"], max_iter=int(params["max_iter"]))
    if params["split"] == "time":
        rerun = train_time_split(frame, train_through_day=int(params["train_through_day"]), **common)
    else:
        rerun = train_random_split(frame, fraction=float(params["train_fraction"]), **common)
    original_metrics = run.data.metrics
    differences = {k: [original_metrics.get(k), v] for k, v in sorted(rerun.metrics.items())
                   if original_metrics.get(k) != v}
    same_digest = original_digest == rerun.dataset_digest
    return {"original_run_id": run_id, "rerun_run_id": rerun.run_id, "same_digest": same_digest,
            "original_digest": original_digest, "rerun_digest": rerun.dataset_digest,
            "identical_metrics": not differences, "differences": differences,
            "reproduced": same_digest and not differences, "rerun": rerun}


def compare_runs(experiment_id, run_names=None, order_by="metrics.accuracy DESC"):
    """The experiment as a table, one row per run, sorted the way a hurried reader sorts it.

    MLflow does the ordering; ties (two runs at accuracy 1.0) are then broken by run name so that the
    table is the same on every execution.
    """
    frame = mlflow.search_runs(experiment_ids=[experiment_id], order_by=[order_by])
    columns = {"run_id": "run_id", "tags.mlflow.runName": "run_name", "params.model": "model", "params.C": "C",
               "params.seed": "seed", "params.split": "split", "params.features": "features",
               "metrics.accuracy": "accuracy", "metrics.precision": "precision", "metrics.recall": "recall",
               "metrics.warnings_per_day": "warnings_per_day"}
    rows = []
    for _, row in frame.iterrows():
        record = {short: (None if pd.isna(row[column]) else row[column]) if column in frame.columns else None
                  for column, short in columns.items()}
        if run_names is not None and record["run_name"] not in run_names:
            continue
        record["dataset_digest"] = training_digest(record["run_id"])
        rows.append(record)
    rows.sort(key=lambda r: (-(r["accuracy"] if r["accuracy"] is not None else -1.0), r["run_name"]))
    return rows


def comparable(run_a, run_b):
    """Two runs compare cleanly when they trained on the same rows and differ in exactly one parameter."""
    a, b = mlflow.get_run(run_a).data.params, mlflow.get_run(run_b).data.params
    differing = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
    digest_a, digest_b = training_digest(run_a), training_digest(run_b)
    same_digest = digest_a is not None and digest_a == digest_b
    return {"differing_params": differing, "same_dataset_digest": same_digest,
            "comparable": same_digest and len(differing) == 1}
