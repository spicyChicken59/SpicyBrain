"""lab-l17-baseline-mlflow test runner (local-executed, ML environment, open-source MLflow 3.16.1).

    python run_tests.py --evidence <path>

Offline. MLflow tracks into a file store inside a temporary directory that this runner creates and
deletes; the model registry is the same file store; no server, no Databricks, no telemetry. Expected
values are literals in expected/: metrics.json is written by expected/derive_expected.py, an
independent script that never imports solutions/ or MLflow (and the first tests re-derive it in
memory); contract.json and decisions.json are hand-authored (derivations in DATA.md). No test
compares the solution with a number the solution produced. Fixture, expected, starter and solution
files and every produced output are hashed (SHA-256) into the evidence JSON.
"""
import argparse
import csv
import io
import json
import os
import platform
import sys
import tempfile
import time
import unittest
from contextlib import ExitStack
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from urllib.parse import unquote, urlparse

sys.dont_write_bytecode = True  # keep the package free of __pycache__
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"  # and the subprocess MLflow uses to infer requirements
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "expected"))
sys.path.insert(0, str(ROOT / "fixtures"))

from solutions.tracking import EXPERIMENT_NAME, experiment_id, tracking_directory  # noqa: E402  (sets the MLflow env)
import mlflow  # noqa: E402
import mlflow.pyfunc  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import sklearn  # noqa: E402
from mlflow import MlflowClient  # noqa: E402
from mlflow.exceptions import MlflowException  # noqa: E402
from mlflow.models import infer_signature  # noqa: E402

import derive_expected  # noqa: E402  (expected/: the independent derivation)
import generate_oven_days  # noqa: E402  (fixtures/: the deterministic generator)
from solutions.contract import (CONTRACT, check_signature, decide, logged_signature, promote,  # noqa: E402
                                write_contract, write_decision)
from solutions.data import (FEATURES, LABEL, feature_frame, frame_from_records, leakage_report,  # noqa: E402
                            load_oven_days, split_by_day, split_random, split_report)
from solutions.experiment import (SEED, ReproductionRefused, compare_runs, comparable, log_baselines,  # noqa: E402
                                  reproduce, train_hero, train_random_split, train_time_split, training_digest)
from starters import naive_promotion, tracked_experiment  # noqa: E402

LAB = "lab-l17-baseline-mlflow"
EXPECTED_METRICS = json.loads((ROOT / "expected" / "metrics.json").read_text(encoding="utf-8"))
EXPECTED_CONTRACT = json.loads((ROOT / "expected" / "contract.json").read_text(encoding="utf-8"))
EXPECTED = json.loads((ROOT / "expected" / "decisions.json").read_text(encoding="utf-8"))
FIX = EXPECTED_METRICS["fixture"]
COUNTS = ("tp", "fp", "fn", "tn", "rows", "warnings")
RATES = ("accuracy", "recall", "precision", "warnings_per_day")
COMPARISON_RUNS = ("never-warn", "temperature-rule", "time-split-C-1", "time-split-C-0.01", "random-split-seeded",
                   "time-split-leaky", "hero")
CANDIDATES = ("time-split-C-1", "time-split-C-0.01", "random-split-seeded", "time-split-leaky", "hero")
EXPECTED_KEY = {"never-warn": "never_warn", "temperature-rule": "temperature_rule", "time-split-C-1": "time_split_C_1",
                "time-split-C-0.01": "time_split_C_0_01", "random-split-seeded": "random_split_seeded",
                "time-split-leaky": "time_split_leaky", "hero": "hero_hidden_seed_11",
                "hero-again": "hero_hidden_seed_12"}
PINNED = {"mlflow": "3.16.1", "scikit-learn": "1.9.1", "pandas": "3.0.6", "numpy": "2.5.3", "scipy": "1.18.1",
          "skops": "0.15.0"}
OUTPUTS = {}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def rounded(metrics):
    """Counts as integers and rates at four places; precision is None when nothing was warned."""
    out = {key: int(metrics[key]) for key in COUNTS}
    for key in RATES:
        out[key] = round(float(metrics[key]), 4) if key in metrics and metrics[key] is not None else None
    return out


def expected_for(block):
    return {key: block[key] for key in COUNTS + RATES}


def local_path(uri):
    return Path(unquote(urlparse(uri).path))


def transfer_frame():
    return frame_from_records(generate_oven_days.rows(generate_oven_days.TRANSFER_SEED))


class Session:
    """The whole tracked experiment, executed once in one temporary tracking directory."""

    def __init__(self):
        self.stack = None
        self.root = None

    def open(self):
        self.stack = ExitStack()
        self.root = self.stack.enter_context(tracking_directory(prefix="l17-tests-"))
        self.client = MlflowClient()
        self.frame = load_oven_days()
        self.train, self.test = split_by_day(self.frame)
        self.exp = experiment_id()
        self.runs = dict(log_baselines(self.test, experiment_id=self.exp))
        self.runs["time-split-C-1"] = train_time_split(self.frame, experiment_id=self.exp, run_name="time-split-C-1",
                                                       C=1.0)
        self.runs["time-split-C-0.01"] = train_time_split(self.frame, experiment_id=self.exp,
                                                          run_name="time-split-C-0.01", C=0.01)
        self.runs["random-split-seeded"] = train_random_split(self.frame, experiment_id=self.exp,
                                                              run_name="random-split-seeded")
        self.runs["time-split-leaky"] = train_time_split(self.frame, experiment_id=self.exp,
                                                         run_name="time-split-leaky",
                                                         features=FEATURES + ["repair_minutes"])
        self.runs["hero"] = train_hero(self.frame, experiment_id=self.exp, run_name="hero", hidden_seed=11)
        # What a hurried reader sees, taken before anything else is logged into the experiment.
        self.table = compare_runs(self.exp, run_names=COMPARISON_RUNS)
        self.naive = naive_promotion.pick_best_by_accuracy(self.exp)
        # The same hero code executed a second time: the record is identical, the split is not.
        self.runs["hero-again"] = train_hero(self.frame, experiment_id=self.exp, run_name="hero-again", hidden_seed=12)
        self.rerun = reproduce(self.runs["time-split-C-1"].run_id, self.frame, experiment_id=self.exp)
        self.hero_refusal = self._refusal(self.runs["hero"].run_id)
        self.environment_refusal = self._refusal(self._environment_copy())
        self.altered = reproduce(self.runs["time-split-C-1"].run_id, transfer_frame(), experiment_id=self.exp,
                                 run_name="time-split-C-1-rerun-on-transfer")
        self.contract_path = self.root / "contract" / "contract.json"
        self.contract_path.parent.mkdir()
        write_contract(self.contract_path)
        self.decisions = {name: decide(CONTRACT, self.runs[name].run_id) for name in CANDIDATES}
        promoted = self.decisions["time-split-C-1"]
        self.promotion = promote(CONTRACT, promoted, self.runs["time-split-C-1"].model_uri)
        self.registry_after_promotion = self._registry_state()
        baselines = {name: rounded(self.runs[name].metrics) for name in ("never-warn", "temperature-rule")}
        self.decision_path = self.root / "promotion" / "decision.json"
        self.decision_document = write_decision(self.decision_path, CONTRACT,
                                                [self.decisions[name] for name in CANDIDATES], baselines,
                                                [dict(self.promotion, run_name="time-split-C-1")])
        # A second registration of an identical, reproduced model, then a rollback by moving the alias back.
        self.rerun_decision = decide(CONTRACT, self.rerun["rerun_run_id"])
        self.second = promote(CONTRACT, self.rerun_decision, self.rerun["rerun"].model_uri)
        self.registry_after_second = self._registry_state()
        self.client.set_registered_model_alias(CONTRACT["model_name"], "candidate", "1")
        self.registry_after_rollback = self._registry_state()
        self.transfer_exp = experiment_id(EXPERIMENT_NAME + "-transfer")
        self.transfer_run = train_time_split(transfer_frame(), experiment_id=self.transfer_exp, run_name="time-split-C-1")
        self.transfer_decision = decide(CONTRACT, self.transfer_run.run_id)
        return self

    def _refusal(self, run_id):
        try:
            reproduce(run_id, self.frame, experiment_id=self.exp)
        except ReproductionRefused as refusal:
            return {"missing": refusal.missing, "mismatched": refusal.mismatched, "message": str(refusal)}
        return None

    def _environment_copy(self):
        """A synthetic record for one negative case: the clean run's parameters and training dataset, but a
        different recorded scikit-learn version. It is built here, labelled as a copy, and never trained."""
        source = mlflow.get_run(self.runs["time-split-C-1"].run_id)
        params = dict(source.data.params, scikit_learn="1.8.0")
        train_ds = mlflow.data.from_pandas(self.train, source="fixtures/oven_days.csv", name="oven-days-train",
                                           targets=LABEL)
        with mlflow.start_run(experiment_id=self.exp, run_name="environment-copy",
                              tags={"note": "synthetic copy for the environment-mismatch test"}) as run:
            mlflow.log_params(params)
            mlflow.log_input(train_ds, context="training")
        return run.info.run_id

    def _registry_state(self):
        name = CONTRACT["model_name"]
        numbers = sorted(int(v.version) for v in self.client.search_model_versions(f"name='{name}'"))
        versions = [self.client.get_model_version(name, str(number)) for number in numbers]
        return {"alias_points_to": int(self.client.get_model_version_by_alias(name, "candidate").version),
                "versions": {int(v.version): {"aliases": sorted(v.aliases), "tags": dict(v.tags),
                                              "run_id": v.run_id} for v in versions}}

    def close(self):
        if self.stack is not None:
            self.stack.close()


SESSION = Session()


def session():
    if SESSION.root is None:
        SESSION.open()
    return SESSION


class FixtureAndExpectedTests(unittest.TestCase):
    """No MLflow: the fixture, the independent literals, the dictionary checks and the starter's gaps."""

    def test_generator_reproduces_the_committed_fixture(self):
        committed = (ROOT / "fixtures" / "oven_days.csv").read_bytes()
        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(buffer, fieldnames=generate_oven_days.COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(generate_oven_days.rows())
        self.assertEqual(sha256(buffer.getvalue().encode("utf-8")).hexdigest(), sha256(committed).hexdigest(),
                         "oven_days.csv differs from what the seeded generator writes")

    def test_expected_metrics_match_an_independent_rerun(self):
        self.assertEqual(json.loads(json.dumps(derive_expected.derive())), EXPECTED_METRICS)

    def test_dataset_facts_and_the_time_split(self):
        frame = load_oven_days()
        train, test = split_by_day(frame)
        report = split_report(train, test)
        facts = FIX["dataset"]
        self.assertEqual((len(frame), int(frame[LABEL].sum()), frame["oven_id"].nunique(), frame["day"].nunique()),
                         (facts["rows"], facts["faults"], facts["ovens"], facts["days"]))
        self.assertEqual((report["train_rows"], report["train_positives"], report["test_rows"], report["test_positives"],
                          report["train_max_day"], report["test_min_day"]),
                         (facts["train_rows"], facts["train_faults"], facts["test_rows"], facts["test_faults"],
                          facts["train_max_day"], facts["test_min_day"]))
        self.assertTrue(report["ok"])
        self.assertEqual(report["kind"], "time")
        OUTPUTS["dataset"] = facts

    def test_dictionary_flags_post_event_columns_and_the_label(self):
        proposed = FEATURES + ["repair_minutes", "fault_code", LABEL]
        report = leakage_report(proposed)
        flags = {item["feature"]: item["reason"] for item in report["flagged"]}
        self.assertEqual(flags, EXPECTED["leakage_flags"])
        self.assertFalse(report["ok"])
        self.assertTrue(leakage_report(FEATURES)["ok"], "a feature available at 09:00 was flagged")
        OUTPUTS["leakage_flags"] = flags

    def test_random_split_tests_on_days_before_training_ends(self):
        train, test = split_random(load_oven_days(), 0.7, SEED)
        report = split_report(train, test)
        days = FIX["random_split_days"]
        self.assertEqual((report["train_max_day"], report["test_min_day"], report["train_positives"],
                          report["test_positives"]),
                         (days["train_max_day"], days["test_min_day"], days["train_faults"], days["test_faults"]))
        self.assertFalse(report["ok"])
        self.assertEqual(report["kind"], "not_time_ordered")
        self.assertEqual(report["reason"], EXPECTED["random_split_reason"])

    def test_contract_literal_matches_the_written_contract(self):
        with tempfile.TemporaryDirectory(prefix="l17-contract-") as directory:
            path = Path(directory) / "contract.json"
            write_contract(path)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), EXPECTED_CONTRACT)
        OUTPUTS["contract"] = EXPECTED_CONTRACT

    def test_starter_tasks_are_real_gaps(self):
        calls = {"Task 2": [lambda: tracked_experiment.leakage_report(FEATURES, {}),
                            lambda: tracked_experiment.split_report(None, None)],
                 "Task 3": [lambda: tracked_experiment.train_time_split(None, experiment_id="0", run_name="x", C=1.0,
                                                                        seed=1)],
                 "Task 5": [lambda: tracked_experiment.reproduce("x", None, experiment_id="0")],
                 "Task 6": [lambda: tracked_experiment.check_signature({}, {})],
                 "Task 7": [lambda: tracked_experiment.decide({}, "x")]}
        for task, functions in calls.items():
            for function in functions:
                with self.assertRaises(NotImplementedError) as caught:
                    function()
                self.assertIn(task, str(caught.exception))
        self.assertTrue(all(value is None for value in tracked_experiment.PREDICTIONS.values()),
                        "the starter must not ship filled predictions")


class TrackedRunTests(unittest.TestCase):
    """The experiment: baselines, clean runs, the two leaks, the hero; what each record holds."""

    @classmethod
    def setUpClass(cls):
        cls.s = session()

    def test_baselines_match_the_expected_literals(self):
        for name in ("never-warn", "temperature-rule"):
            with self.subTest(run=name):
                self.assertEqual(rounded(self.s.runs[name].metrics), expected_for(FIX[EXPECTED_KEY[name]]))
        self.assertNotIn("precision", mlflow.get_run(self.s.runs["never-warn"].run_id).data.metrics,
                         "a precision was logged for a predictor that never warns")

    def test_every_model_run_matches_the_expected_literals(self):
        for name in ("time-split-C-1", "time-split-C-0.01", "random-split-seeded", "time-split-leaky", "hero",
                     "hero-again"):
            with self.subTest(run=name):
                logged = mlflow.get_run(self.s.runs[name].run_id).data.metrics
                self.assertEqual(rounded(logged), expected_for(FIX[EXPECTED_KEY[name]]))
        OUTPUTS["metrics"] = {name: rounded(result.metrics) for name, result in sorted(self.s.runs.items())}

    def test_a_clean_run_records_everything_a_rerun_needs(self):
        result = self.s.runs["time-split-C-1"]
        run = mlflow.get_run(result.run_id)
        self.assertEqual(sorted(run.data.params), sorted(["model", "C", "class_weight", "max_iter", "seed", "features",
                                                           "scikit_learn", "split", "train_through_day"]))
        self.assertEqual((run.data.params["C"], run.data.params["seed"], run.data.params["split"],
                          run.data.params["scikit_learn"]), ("1.0", str(SEED), "time", sklearn.__version__))
        contexts = sorted(tag.value for item in run.inputs.dataset_inputs for tag in item.tags
                          if tag.key == "mlflow.data.context")
        self.assertEqual(contexts, ["evaluation", "training"])
        self.assertRegex(training_digest(result.run_id), r"^[0-9a-f]{8}$")
        artifacts = sorted(f.path for folder in ("checks", "evaluation")
                           for f in self.s.client.list_artifacts(result.run_id, folder))
        self.assertEqual(artifacts, ["checks/leakage_report.json", "checks/split_report.json",
                                     "evaluation/confusion_matrix.json", "evaluation/metrics.json"])
        model = mlflow.get_logged_model(result.model_id)
        files = sorted(p.name for p in local_path(model.artifact_location).iterdir())
        self.assertEqual(files, ["MLmodel", "conda.yaml", "input_example.json", "model.skops", "python_env.yaml",
                                 "requirements.txt", "serving_input_example.json"])
        requirements = (local_path(model.artifact_location) / "requirements.txt").read_text(encoding="utf-8").split()
        self.assertEqual(sorted(requirements), sorted(f"{name}=={version}" for name, version in PINNED.items()))
        info = mlflow.models.get_model_info(result.model_uri)
        self.assertEqual(sorted(info.flavors), ["python_function", "sklearn"])
        self.assertEqual(info.flavors["sklearn"]["serialization_format"], "skops")
        self.assertEqual(model.metrics and sorted({m.key for m in model.metrics}),
                         sorted(set(COUNTS + RATES)), "the metrics were not linked to the logged model")
        OUTPUTS["clean_run_record"] = {"params": sorted(run.data.params), "contexts": contexts, "artifacts": artifacts,
                                       "model_files": files, "requirements": sorted(requirements),
                                       "flavors": sorted(info.flavors), "training_digest": training_digest(result.run_id)}

    def test_parameters_cannot_be_changed_after_logging(self):
        with self.assertRaises(MlflowException) as caught:
            self.s.client.log_param(self.s.runs["time-split-C-1"].run_id, "C", 0.5)
        self.assertIn("Changing param values is not allowed", str(caught.exception))

    def test_sorting_by_accuracy_puts_the_leaks_and_never_warn_first(self):
        ranking = [[row["run_name"], round(float(row["accuracy"]), 4)] for row in self.s.table]
        self.assertEqual(ranking, EXPECTED["accuracy_ranking"])
        OUTPUTS["accuracy_ranking"] = ranking

    def test_comparable_pairs_share_rows_and_differ_in_one_parameter(self):
        results = {}
        for pair, expected in EXPECTED["comparisons"].items():
            a, b = pair.split("|")
            with self.subTest(pair=pair):
                results[pair] = comparable(self.s.runs[a].run_id, self.s.runs[b].run_id)
                self.assertEqual(results[pair], expected)
        OUTPUTS["comparisons"] = results


class ReproducibilityTests(unittest.TestCase):
    """What a record can and cannot reproduce."""

    @classmethod
    def setUpClass(cls):
        cls.s = session()

    def test_the_hero_cannot_be_rerun_from_its_record(self):
        self.assertIsNotNone(self.s.hero_refusal, "reproduce() guessed instead of refusing")
        self.assertEqual({k: self.s.hero_refusal[k] for k in ("missing", "mismatched")},
                         EXPECTED["reproduce_refusals"]["hero"])
        self.assertIn("not recorded: C, class_weight, features", self.s.hero_refusal["message"])
        OUTPUTS["hero_refusal"] = self.s.hero_refusal

    def test_identical_records_can_hold_different_results(self):
        first, second = (mlflow.get_run(self.s.runs[name].run_id) for name in ("hero", "hero-again"))
        self.assertEqual(first.data.params, second.data.params, "the two hero records should be indistinguishable")
        self.assertEqual((first.inputs.dataset_inputs, second.inputs.dataset_inputs), ([], []))
        self.assertNotEqual(rounded(first.data.metrics), rounded(second.data.metrics))
        self.assertEqual((int(first.data.metrics["tp"]), int(second.data.metrics["tp"])),
                         (FIX["hero_hidden_seed_11"]["tp"], FIX["hero_hidden_seed_12"]["tp"]))

    def test_a_clean_rerun_reproduces_every_metric_exactly(self):
        rerun = self.s.rerun
        self.assertTrue(rerun["same_digest"])
        self.assertTrue(rerun["identical_metrics"], rerun["differences"])
        self.assertTrue(rerun["reproduced"])
        self.assertNotEqual(rerun["rerun_run_id"], rerun["original_run_id"])
        original = mlflow.get_run(rerun["original_run_id"]).data.metrics
        repeated = mlflow.get_run(rerun["rerun_run_id"]).data.metrics
        self.assertEqual(original, repeated)  # exact float equality, not a tolerance
        OUTPUTS["rerun"] = {k: rerun[k] for k in ("same_digest", "identical_metrics", "reproduced", "differences")}

    def test_a_rerun_on_changed_data_is_not_a_reproduction(self):
        altered = self.s.altered
        self.assertFalse(altered["same_digest"])
        self.assertFalse(altered["identical_metrics"])
        self.assertFalse(altered["reproduced"])
        self.assertEqual(rounded(altered["rerun"].metrics),
                         expected_for(EXPECTED_METRICS["transfer"]["time_split_C_1"]))
        OUTPUTS["altered_rerun"] = {k: altered[k] for k in ("same_digest", "identical_metrics", "reproduced")}

    def test_a_different_library_version_is_refused(self):
        self.assertEqual({k: self.s.environment_refusal[k] for k in ("missing", "mismatched")},
                         EXPECTED["reproduce_refusals"]["environment_copy"])
        OUTPUTS["environment_refusal"] = self.s.environment_refusal

    def test_the_digest_fingerprints_a_sample_not_every_row(self):
        """MLflow 3.16.1's pandas digest hashes the first 10,000 rows, the row count and the column names."""
        frame = pd.DataFrame({"reading": np.arange(10001, dtype="float64"), "flag": np.ones(10001)})
        late, early = frame.copy(), frame.copy()
        late.loc[10000, "reading"] = -5.0
        early.loc[0, "reading"] = -5.0
        digest = lambda f: mlflow.data.from_pandas(f, source="synthetic").digest  # noqa: E731
        self.assertEqual(digest(frame), digest(late), "a change in row 10,001 moved the digest")
        self.assertNotEqual(digest(frame), digest(early))
        self.assertNotEqual(digest(frame), digest(frame.head(10000)), "the row count is part of the digest")
        OUTPUTS["digest_sample"] = {"late_change_same_digest": True, "early_change_new_digest": True}


class ContractAndPromotionTests(unittest.TestCase):
    """The contract rejects drift; the decision reads evidence before metrics; promotion is an alias move."""

    @classmethod
    def setUpClass(cls):
        cls.s = session()
        cls.clean = feature_frame(cls.s.train)
        cls.test_inputs = feature_frame(cls.s.test)

    def test_the_logged_signature_matches_the_contract(self):
        signature = logged_signature(self.s.runs["time-split-C-1"].run_id)
        self.assertEqual(check_signature(CONTRACT, signature), {"ok": True, "reasons": []})
        self.assertEqual(json.loads(signature["outputs"]), [{"type": "long", "name": LABEL, "required": True}])
        OUTPUTS["signature"] = signature

    def test_the_contract_rejects_schema_drift_by_name_and_type(self):
        output = pd.Series([0, 1], name=LABEL)
        variants = {"renamed": (self.clean.rename(columns={"humidity_pct": "humidity"}), output),
                    "retyped": (self.clean.assign(door_cycles=self.s.train["door_cycles"].astype("int64")), output),
                    "extra": (self.clean.assign(repair_minutes=self.s.train["repair_minutes"].astype("float64")),
                              output),
                    "output_renamed": (self.clean, pd.Series([0, 1], name="prediction")),
                    "reordered": (self.clean[list(reversed(FEATURES))], output)}
        found = {}
        for case, (inputs, out) in variants.items():
            with self.subTest(case=case):
                report = check_signature(CONTRACT, infer_signature(inputs.head(2), out).to_dict())
                found[case] = report["reasons"]
                self.assertEqual(report["reasons"], EXPECTED["drift_cases"][case]["reasons"])
                self.assertEqual(report["ok"], not EXPECTED["drift_cases"][case]["reasons"])
        OUTPUTS["drift"] = found

    def test_mlflow_enforcement_rejects_missing_and_retyped_inputs_but_ignores_extra_ones(self):
        model = mlflow.pyfunc.load_model(self.s.runs["time-split-C-1"].model_uri)
        expect = EXPECTED["pyfunc_enforcement"]
        with self.assertRaises(MlflowException) as renamed:
            model.predict(self.test_inputs.rename(columns={"humidity_pct": "humidity"}))
        self.assertIn(expect["renamed"]["message_contains"], str(renamed.exception))
        with self.assertRaises(MlflowException) as retyped:
            model.predict(self.test_inputs.assign(door_cycles=self.s.test["door_cycles"].astype("int64")))
        self.assertIn(expect["retyped"]["message_contains"], str(retyped.exception))
        with self.assertLogs("mlflow", level="WARNING") as logs:
            extra = model.predict(self.test_inputs.assign(repair_minutes=self.s.test["repair_minutes"].astype("float64")))
        self.assertTrue(any(expect["extra"]["log_contains"] in line for line in logs.output))
        baseline = model.predict(self.test_inputs)
        self.assertEqual(list(extra), list(baseline), "the extra column changed predictions")
        reordered = model.predict(self.test_inputs[list(reversed(FEATURES))])
        self.assertEqual(list(reordered), list(baseline))
        OUTPUTS["pyfunc_enforcement"] = {"renamed": "raised", "retyped": "raised", "extra": "ignored with warning",
                                         "reordered": "same predictions"}

    def test_decisions_read_the_evidence_before_the_metrics(self):
        found = {name: {k: d[k] for k in ("decision", "gate", "reasons")} for name, d in self.s.decisions.items()}
        self.assertEqual(found, EXPECTED["candidates"])
        # The two runs with perfect scores are rejected before any metric is read.
        for name in ("hero", "time-split-leaky"):
            self.assertEqual(round(self.s.decisions[name]["metrics"]["accuracy"], 4), 1.0)
            self.assertEqual(self.s.decisions[name]["gate"], "evidence")
        OUTPUTS["decisions"] = found

    def test_naive_accuracy_promotion_picks_a_run_the_evidence_gate_rejects(self):
        run_id, run_name, accuracy = self.s.naive
        self.assertIn(run_name, EXPECTED["naive_pick_is_one_of"])
        self.assertEqual(accuracy, 1.0)
        verdict = decide(CONTRACT, run_id)
        self.assertEqual((verdict["decision"], verdict["gate"]), ("reject", "evidence"))
        self.assertTrue(any(r.endswith("repair_minutes") or r == "features_not_recorded" for r in verdict["reasons"]))
        OUTPUTS["naive_pick"] = {"accuracy": accuracy, "decision": verdict["decision"], "gate": verdict["gate"]}

    def test_promotion_registers_one_version_with_the_alias_and_its_evidence(self):
        state, expected = self.s.registry_after_promotion, EXPECTED["registry"]["after_promotion"]
        self.assertEqual((self.s.promotion["version"], self.s.promotion["alias"], state["alias_points_to"]),
                         (expected["version"], expected["alias"], expected["alias_points_to"]))
        version = state["versions"][1]
        self.assertEqual(version["tags"]["contract_version"], expected["tags"]["contract_version"])
        self.assertEqual(version["tags"]["decided_from_run"], self.s.runs["time-split-C-1"].run_id)
        self.assertEqual(version["run_id"], self.s.runs["time-split-C-1"].run_id)
        document = json.loads(self.s.decision_path.read_text(encoding="utf-8"))
        self.assertEqual([d["run_name"] for d in document["decisions"] if d["decision"] == "promote-candidate"],
                         EXPECTED["promoted"])
        self.assertEqual(document["contract_version"], "1.0.0")
        self.assertIn("does not certify data quality", document["note"])
        self.assertGreaterEqual(len(document["limitations"]), 5)
        self.assertTrue(any("18 faults" in line for line in document["limitations"]))
        self.assertTrue(any("absent from training" in line for line in document["limitations"]))
        OUTPUTS["decision_file"] = {"decisions": [{k: d[k] for k in ("run_name", "decision", "gate", "reasons")}
                                                  for d in document["decisions"]],
                                    "promoted": [{k: p[k] for k in ("run_name", "name", "version", "alias", "uri")}
                                                 for p in document["promoted"]],
                                    "limitations": document["limitations"]}

    def test_the_alias_moves_and_rolls_back_while_versions_stay(self):
        second, rollback = EXPECTED["registry"]["after_second_version"], EXPECTED["registry"]["after_rollback"]
        state = self.s.registry_after_second
        self.assertEqual((self.s.second["version"], state["alias_points_to"]), (2, second["alias_points_to"]))
        self.assertEqual((state["versions"][1]["aliases"], state["versions"][2]["aliases"]),
                         (second["version_1_aliases"], second["version_2_aliases"]))
        state = self.s.registry_after_rollback
        self.assertEqual(state["alias_points_to"], rollback["alias_points_to"])
        self.assertEqual((state["versions"][1]["aliases"], state["versions"][2]["aliases"]),
                         (rollback["version_1_aliases"], rollback["version_2_aliases"]))
        name = CONTRACT["model_name"]
        one = mlflow.pyfunc.load_model(f"models:/{name}/1").predict(self.test_inputs)
        two = mlflow.pyfunc.load_model(f"models:/{name}/2").predict(self.test_inputs)
        self.assertEqual(list(one), list(two), "a reproduced model should predict identically")
        OUTPUTS["registry"] = {"after_second": {k: v["aliases"] for k, v in self.s.registry_after_second["versions"].items()},
                               "after_rollback": {k: v["aliases"] for k, v in state["versions"].items()}}

    def test_the_candidate_alias_loads_the_decided_model(self):
        loaded = mlflow.pyfunc.load_model(self.s.promotion["uri"])
        predictions = loaded.predict(self.test_inputs)
        truth = self.s.test[LABEL].tolist()
        expected = FIX["time_split_C_1"]
        tp = sum(1 for t, p in zip(truth, predictions) if t == 1 and p == 1)
        self.assertEqual((int(sum(predictions)), tp), (expected["warnings"], expected["tp"]))

    def test_promotion_refuses_a_rejected_decision(self):
        with self.assertRaises(ValueError) as caught:
            promote(CONTRACT, self.s.decisions["hero"], self.s.runs["hero"].model_uri)
        self.assertIn("decided reject", str(caught.exception))


class TransferTests(unittest.TestCase):
    """Same code, same contract, another plant's data (generator seed TRANSFER_SEED)."""

    @classmethod
    def setUpClass(cls):
        cls.s = session()

    def test_transfer_plant_facts_match_the_expected_literals(self):
        frame = transfer_frame()
        train, test = split_by_day(frame)
        facts = EXPECTED_METRICS["transfer"]["dataset"]
        self.assertEqual((len(frame), int(frame[LABEL].sum()), len(train), int(train[LABEL].sum()), len(test),
                          int(test[LABEL].sum())),
                         (facts["rows"], facts["faults"], facts["train_rows"], facts["train_faults"],
                          facts["test_rows"], facts["test_faults"]))

    def test_the_same_contract_rejects_the_transfer_run_on_recall(self):
        self.assertEqual(rounded(self.s.transfer_run.metrics),
                         expected_for(EXPECTED_METRICS["transfer"]["time_split_C_1"]))
        found = {k: self.s.transfer_decision[k] for k in ("decision", "gate", "reasons")}
        self.assertEqual(found, EXPECTED["transfer"]["time-split-C-1"])
        OUTPUTS["transfer"] = {"metrics": rounded(self.s.transfer_run.metrics), "decision": found}


class CleanupTests(unittest.TestCase):
    """Runs after the session is closed: nothing of MLflow's may remain."""

    def test_the_tracking_directory_is_deleted(self):
        self.assertIsNotNone(SESSION.root)
        self.assertFalse(SESSION.root.exists(), f"{SESSION.root} was left behind")

    def test_no_mlflow_state_is_left_in_the_lab_or_the_working_directory(self):
        leftovers = [p for base in {ROOT, Path.cwd()} for name in ("mlruns", "mlflow.db", "mlartifacts",
                                                                   "spark-warehouse", "metastore_db")
                     for p in [base / name] if p.exists()]
        leftovers += list(ROOT.rglob("__pycache__"))
        self.assertEqual(leftovers, [])


def versions():
    import importlib.metadata as metadata
    return {name: metadata.version(name) for name in PINNED}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()
    started_at = datetime.now(timezone.utc)
    started = time.monotonic()
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    for case in (FixtureAndExpectedTests, TrackedRunTests, ReproducibilityTests, ContractAndPromotionTests,
                 TransferTests):
        suite.addTests(loader.loadTestsFromTestCase(case))
    runner = unittest.TextTestRunner(verbosity=2)
    try:
        first = runner.run(suite)
    finally:
        SESSION.close()
    second = runner.run(loader.loadTestsFromTestCase(CleanupTests))
    tests = first.testsRun + second.testsRun
    failures = len(first.failures) + len(second.failures)
    errors = len(first.errors) + len(second.errors)
    skipped = len(first.skipped) + len(second.skipped)
    exit_code = 0 if first.wasSuccessful() and second.wasSuccessful() and skipped == 0 else 1
    hashed = [path for directory in ("fixtures", "expected", "starters", "solutions") for path in
              sorted((ROOT / directory).iterdir()) if path.is_file()]
    hashed += [ROOT / name for name in ("run_tests.py", "requirements.txt")]
    evidence = {
        "lab": LAB, "executionClass": "local-executed", "runtime": "ml",
        "python": platform.python_version(), "interpreter": sys.executable, "java": "not used", "spark": "not used",
        "packages": versions(), "platform": platform.system() + " " + platform.release(),
        "startedAt": started_at.isoformat(), "finishedAt": datetime.now(timezone.utc).isoformat(),
        "durationSeconds": round(time.monotonic() - started, 3),
        "tests": tests, "failures": failures, "errors": errors, "skipped": skipped, "exit": exit_code,
        "fixtureHashes": {str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path.read_bytes()).hexdigest()
                          for path in hashed},
        "outputHashes": {name: sha256(canonical(value).encode("utf-8")).hexdigest()
                         for name, value in sorted(OUTPUTS.items())},
        "commands": [f"{Path(sys.executable).name} run_tests.py --evidence <path>"],
        "notes": ("Open-source MLflow 3.16.1 with a file-store tracking URI and file-store model registry in a "
                  "temporary directory created and deleted by this runner (MLFLOW_ALLOW_FILE_STORE=true; "
                  "telemetry disabled); no tracking server, no Databricks, no Unity Catalog, no network. "
                  "scikit-learn LogisticRegression (lbfgs) on a seeded synthetic fixture. Expected metrics come "
                  "from expected/derive_expected.py, which never imports solutions/ or MLflow; decisions and the "
                  "contract are hand-authored literals. The environment-copy run is a synthetic record built for "
                  "one negative test."),
    }
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: evidence[key] for key in ("lab", "python", "tests", "failures", "errors", "skipped",
                                                     "exit")}, indent=2))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
