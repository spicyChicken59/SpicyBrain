"""lab-l18-point-in-time-features test runner (local-executed, pandas).

    python run_tests.py --evidence <path>    (Python 3.12 with requirements.txt installed)

Offline; pandas 3.0.6 and numpy 2.5.3. Every expected value is a
hand-authored literal in expected/*.json (derivations in DATA.md); no test
compares the solution with a value the solution computed. The deliberately
wrong code in starters/ is asserted to fail for its documented reason.
Fixture, expected, solution, starter and produced-output SHA-256 hashes go
into the evidence JSON.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
from importlib import metadata
import json
from pathlib import Path
import platform
import sys
import time
import unittest

sys.dont_write_bytecode = True  # keep the package free of __pycache__
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from solutions import features as F  # noqa: E402
from starters import serving_port, shortcuts  # noqa: E402

LAB = "lab-l18-point-in-time-features"
FIX = ROOT / "fixtures"
EXPECTED = {name: json.loads((ROOT / "expected" / f"{name}.json").read_text(encoding="utf-8"))
            for name in ("feature_table", "training_set", "leaks", "serving", "drift", "late", "reuse")}
TRAIN_COLUMNS = ["machine_id", "prediction_time", "label", "feature_time", "available_at", "temp_mean_2h",
                 "vib_max_2h", "reading_count_2h", "vib_count_2h", "low_coverage", "feature_age_minutes",
                 "feature_status", "label_status"]
OUTPUTS: dict[str, object] = {}
CONTRACT = F.load_contract(FIX / "feature_contract.json")
CONSUMERS = F.load_consumers(FIX / "consumers.json")
FAILURE = CONSUMERS["failure_warning"]
HANDOVER = CONSUMERS["handover_scrap"]


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def ts(text: str) -> pd.Timestamp:
    return pd.Timestamp(text)


def primary_observations() -> pd.DataFrame:
    return F.load_observations(FIX / "observations.csv")


def all_observations() -> pd.DataFrame:
    return F.load_observations(FIX / "observations.csv", FIX / "late_observations.csv")


def labels() -> pd.DataFrame:
    return F.load_labels(FIX / FAILURE["label_file"])


def by_key(rows: list[dict]) -> dict:
    return {(row["machine_id"], row["prediction_time"]): row for row in rows}


class FeatureTableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table = F.build_feature_table(primary_observations(), CONTRACT)
        OUTPUTS["feature_table"] = F.records(cls.table)

    def test_feature_table_matches_the_authored_rows(self):
        self.assertEqual(F.records(self.table), EXPECTED["feature_table"]["rows"])

    def test_boundary_reading_and_null_vibration_follow_the_contract(self):
        rows = {(r["machine_id"], r["feature_time"]): r for r in F.records(self.table)}
        pr02 = rows[("PR-02", "2026-03-02T10:00:00+00:00")]
        self.assertEqual(pr02["reading_count_2h"], 3, "the 10:00:00 reading closes the window ending 10:00")
        self.assertEqual(pr02["vib_count_2h"], 2, "the 09:10 reading has no vibration value: counted as a row, not a value")
        pr03 = rows[("PR-03", "2026-03-02T10:00:00+00:00")]
        self.assertIsNone(pr03["vib_max_2h"], "no vibration value in the window stays missing, never 0.0")
        self.assertEqual(pr03["vib_count_2h"], 0)
        self.assertTrue(pr03["low_coverage"])
        self.assertNotIn(("PR-02", "2026-03-02T12:00:00+00:00"), rows, "no readings: no row, not a row of zeros")

    def test_every_row_is_published_after_its_window_closes(self):
        delay = pd.Timedelta(minutes=CONTRACT["publish_delay_minutes"])
        for row in self.table.itertuples(index=False):
            self.assertGreaterEqual(row.available_at - row.feature_time, delay)
            self.assertLessEqual(row.source_max_ingested_at, row.available_at)

    def test_duplicate_entity_time_row_is_refused_and_would_make_the_join_order_dependent(self):
        copy = self.table[(self.table["machine_id"] == "PR-01") & (self.table["feature_time"] == ts("2026-03-02T10:00:00Z"))]
        duplicated = pd.concat([self.table, copy.assign(temp_mean_2h=99.0)], ignore_index=True)
        with self.assertRaises(F.DuplicateEntityTimeError) as caught:
            F.validate_feature_table(duplicated, CONTRACT)
        self.assertEqual(str(caught.exception),
                         "duplicate entity-time feature row: machine_id=PR-01 feature_time=2026-03-02T10:00:00+00:00 "
                         "available_at=2026-03-02T10:30:00+00:00 appears 2 times")
        with self.assertRaises(F.DuplicateEntityTimeError):
            F.point_in_time_join(labels(), duplicated, CONTRACT)
        # Why the contract refuses: without it, the value a model sees depends on storage order.
        forward = shortcuts.join_on_availability_unchecked(labels(), duplicated)
        backward = shortcuts.join_on_availability_unchecked(labels(), duplicated.iloc[::-1].reset_index(drop=True))
        pick = lambda frame: frame[(frame["machine_id"] == "PR-01") & (frame["prediction_time"] == ts("2026-03-02T11:00:00Z"))]["temp_mean_2h"].iloc[0]
        self.assertEqual(sorted([pick(forward), pick(backward)]), [77.0, 99.0])
        OUTPUTS["duplicate_order_dependence"] = sorted([float(pick(forward)), float(pick(backward))])

    def test_duplicate_reading_is_refused_before_aggregation(self):
        observations = primary_observations()
        reading = observations[(observations["machine_id"] == "PR-02") & (observations["observed_at"] == ts("2026-03-02T10:00:00Z"))]
        with self.assertRaises(F.DuplicateEntityTimeError) as caught:
            F.build_feature_table(pd.concat([observations, reading.assign(temp_c=75.0)], ignore_index=True), CONTRACT)
        self.assertEqual(str(caught.exception),
                         "duplicate entity-time reading: machine_id=PR-02 observed_at=2026-03-02T10:00:00+00:00 appears 2 times")

    def test_quality_rules_reject_impossible_rows(self):
        cases = [
            ({"vib_count_2h": 4}, "PR-01", "vib_count_2h outside [0, reading_count_2h]"),
            ({"vib_max_2h": float("nan")}, "PR-02", "vib_max_2h must be null exactly when the window has no vibration value"),
            ({"temp_mean_2h": 400.0}, "PR-01", "temp_mean_2h outside the plausible range [-40, 150]"),
            ({"low_coverage": True}, "PR-01", "low_coverage disagrees with reading_count_2h"),
        ]
        for change, machine, message in cases:
            broken = self.table.copy()
            target = (broken["machine_id"] == machine) & (broken["feature_time"] == ts("2026-03-02T08:00:00Z"))
            for column, value in change.items():
                broken.loc[target, column] = value
            with self.assertRaises(F.FeatureContractError) as caught:
                F.validate_feature_table(broken, CONTRACT)
            self.assertEqual(str(caught.exception), message)


class PointInTimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table = F.build_feature_table(primary_observations(), CONTRACT)
        cls.training = F.build_training_set(labels(), cls.table, CONTRACT, FAILURE)
        OUTPUTS["training_set"] = F.records(cls.training, TRAIN_COLUMNS)

    def test_training_set_matches_the_authored_rows(self):
        self.assertEqual(F.records(self.training, TRAIN_COLUMNS), EXPECTED["training_set"]["rows"])

    def test_training_rows_and_exclusions(self):
        usable = F.training_rows(self.training)
        self.assertEqual([[r["machine_id"], r["prediction_time"]] for r in F.records(usable, ["machine_id", "prediction_time"])],
                         EXPECTED["training_set"]["training_row_keys"])
        kept = {tuple(key) for key in EXPECTED["training_set"]["training_row_keys"]}
        excluded = [r for r in F.records(self.training, ["machine_id", "prediction_time", "feature_status", "label_status"])
                    if (r["machine_id"], r["prediction_time"]) not in kept]
        self.assertEqual(excluded, EXPECTED["training_set"]["excluded"])
        OUTPUTS["training_rows"] = len(usable)

    def test_merge_asof_on_availability_agrees_on_the_primary_fixture(self):
        asof = F.build_training_set(labels(), self.table, CONTRACT, FAILURE, join=F.asof_join_on_availability)
        self.assertEqual(F.records(asof, TRAIN_COLUMNS), EXPECTED["training_set"]["rows"])

    def test_label_contract_rejects_duplicates_past_outcomes_and_unknown_keys(self):
        frame = labels()
        with self.assertRaises(F.DuplicateEntityTimeError) as caught:
            F.point_in_time_join(pd.concat([frame, frame.iloc[[1]]], ignore_index=True), self.table, CONTRACT)
        self.assertEqual(str(caught.exception),
                         "duplicate entity-time label: machine_id=PR-01 prediction_time=2026-03-02T11:00:00+00:00 appears 2 times")
        past = frame.copy()
        row = (past["machine_id"] == "PR-02") & (past["prediction_time"] == ts("2026-03-02T09:00:00Z"))
        past.loc[row, "event_at"] = ts("2026-03-02T08:50:00Z")
        past.loc[row, "label"] = 1
        with self.assertRaises(F.FutureInformationError) as caught:
            F.point_in_time_join(past, self.table, CONTRACT)
        self.assertIn("outcome event at or before its prediction time: machine_id=PR-02", str(caught.exception))
        renamed = frame.replace({"machine_id": {"PR-02": "pr-02"}})
        with self.assertRaises(F.FeatureContractError) as caught:
            F.point_in_time_join(renamed, self.table, CONTRACT)
        self.assertTrue(str(caught.exception).startswith("unknown entity key in labels: ['pr-02']"))


class FutureInformationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table = F.build_feature_table(primary_observations(), CONTRACT)

    def assert_leaks(self, joined, expected, name):
        with self.assertRaises(F.FutureInformationError) as caught:
            F.assert_no_future_information(joined)
        self.assertEqual(sorted(caught.exception.rows, key=lambda r: (r["machine_id"], r["prediction_time"])), expected)
        OUTPUTS[name] = caught.exception.rows

    def test_event_time_join_is_rejected_for_the_two_delayed_rows(self):
        self.assert_leaks(shortcuts.join_on_feature_time(labels(), self.table),
                          EXPECTED["leaks"]["join_on_feature_time"], "leaks_join_on_feature_time")

    def test_latest_row_lookup_is_rejected_for_seven_rows(self):
        self.assert_leaks(shortcuts.latest_row_lookup(labels(), self.table),
                          EXPECTED["leaks"]["latest_row_lookup"], "leaks_latest_row_lookup")

    def test_guard_accepts_the_point_in_time_join(self):
        joined = F.point_in_time_join(labels(), self.table, CONTRACT)
        F.assert_no_future_information(joined)  # raises on any leak
        published = joined.dropna(subset=["available_at"])
        self.assertTrue((published["available_at"] <= published["prediction_time"]).all())
        self.assertEqual(len(published), 9)


class ServingConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table = F.build_feature_table(primary_observations(), CONTRACT)
        cls.late_table = F.build_feature_table(all_observations(), CONTRACT)

    def test_serving_equals_training_at_every_label_time(self):
        columns = ["machine_id", "prediction_time", "feature_time", "available_at", *F.FEATURE_COLUMNS,
                   "feature_age_minutes", "feature_status"]
        for table in (self.table, self.late_table):
            training = F.records(F.build_training_set(labels(), table, CONTRACT, FAILURE), columns)
            for row in training:
                served = F.serve_features(table, row["machine_id"], ts(row["prediction_time"]), FAILURE)
                self.assertEqual(served, row)

    def test_serving_responses_match_the_authored_literals(self):
        for name, table in (("primary", self.table), ("late", self.late_table)):
            for expected in EXPECTED["serving"][name]:
                served = F.serve_features(table, expected["machine_id"], ts(expected["prediction_time"]), FAILURE)
                self.assertEqual(served, expected)
                OUTPUTS.setdefault("serving", []).append(served)

    def test_shared_transformation_passes_at_every_run(self):
        for run_at in CONTRACT["run_times"]:
            F.assert_same_transformation(F.compute_features, F.compute_features, all_observations(), run_at, CONTRACT)

    def test_drifted_port_is_rejected_with_the_authored_differences(self):
        with self.assertRaises(F.TransformationMismatchError) as caught:
            F.assert_same_transformation(F.compute_features, serving_port.compute_features_port, primary_observations(),
                                         ts(EXPECTED["drift"]["run_at_with_edge_cases"]), CONTRACT)
        self.assertEqual(caught.exception.differences, EXPECTED["drift"]["differences"])
        self.assertEqual(json.loads(str(caught.exception)), EXPECTED["drift"]["differences"])
        OUTPUTS["drift"] = caught.exception.differences

    def test_drifted_port_passes_when_inputs_lack_the_edge_cases(self):
        # No boundary reading and no missing vibration value is ingested by 08:30,
        # so the same drifted port agrees: a consistency check proves nothing
        # about inputs it never saw.
        F.assert_same_transformation(F.compute_features, serving_port.compute_features_port, primary_observations(),
                                     ts(EXPECTED["drift"]["run_at_without_edge_cases"]), CONTRACT)
        self.assertEqual(EXPECTED["drift"]["differences_without_edge_cases"], [])


class LateArrivalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table = F.build_feature_table(primary_observations(), CONTRACT)
        cls.late_table = F.build_feature_table(all_observations(), CONTRACT)
        cls.before = F.build_training_set(labels(), cls.table, CONTRACT, FAILURE)
        cls.after = F.build_training_set(labels(), cls.late_table, CONTRACT, FAILURE)
        OUTPUTS["late_feature_table"] = F.records(cls.late_table)
        OUTPUTS["late_training_set"] = F.records(cls.after, TRAIN_COLUMNS)

    def test_late_rerun_appends_two_versions_and_rewrites_nothing(self):
        before, after = F.records(self.table), F.records(self.late_table)
        for row in before:
            self.assertIn(row, after, "a published version is never rewritten")
        added = [row for row in after if row not in before]
        self.assertEqual(added, EXPECTED["late"]["new_versions"])
        self.assertEqual(len(after), len(before) + 2)

    def test_only_the_prediction_after_the_new_version_changes(self):
        before = by_key(F.records(self.before, TRAIN_COLUMNS))
        after = by_key(F.records(self.after, TRAIN_COLUMNS))
        changed = [{"machine_id": key[0], "prediction_time": key[1], "before": before[key], "after": after[key]}
                   for key in before if before[key] != after[key]]
        self.assertEqual(changed, EXPECTED["late"]["changed_training_rows"])
        # PR-01's 09:50 reading arrived at 11:05; the 11:00 prediction must still see the 10:30 version.
        eleven = after[("PR-01", "2026-03-02T11:00:00+00:00")]
        self.assertEqual((eleven["available_at"], eleven["temp_mean_2h"]), ("2026-03-02T10:30:00+00:00", 77.0))
        OUTPUTS["late_changed_rows"] = changed

    def test_asof_on_availability_alone_picks_the_republished_older_window(self):
        asof = by_key(F.records(F.build_training_set(labels(), self.late_table, CONTRACT, FAILURE, join=F.asof_join_on_availability), TRAIN_COLUMNS))
        pit = by_key(F.records(self.after, TRAIN_COLUMNS))
        fields = ["feature_time", "available_at", "temp_mean_2h", "feature_age_minutes", "feature_status"]
        disagreements = [{"machine_id": key[0], "prediction_time": key[1],
                          "point_in_time": {f: pit[key][f] for f in fields},
                          "asof_on_availability": {f: asof[key][f] for f in fields}}
                         for key in pit if pit[key] != asof[key]]
        self.assertEqual(disagreements, EXPECTED["late"]["asof_on_availability_disagreements"])
        OUTPUTS["late_asof_disagreements"] = disagreements

    def test_online_store_keeps_the_newer_window_after_a_republication(self):
        store = F.online_store_at(self.late_table, ts("2026-03-02T12:45:00Z"))
        self.assertEqual(store.loc["PR-02", "feature_time"], ts("2026-03-02T10:00:00Z"))
        republished = self.late_table[(self.late_table["machine_id"] == "PR-02") & (self.late_table["available_at"] == ts("2026-03-02T12:30:00Z"))]
        self.assertEqual(list(republished["feature_time"]), [ts("2026-03-02T08:00:00Z")], "an OLDER window was published at 12:30")

    def test_overwrite_backfill_is_refused_by_lineage_and_would_leak_three_rows(self):
        backfilled = shortcuts.overwrite_backfill(all_observations(), CONTRACT)
        with self.assertRaises(F.FeatureContractError) as caught:
            F.validate_feature_table(backfilled, CONTRACT)
        message = str(caught.exception)
        expected = EXPECTED["late"]["backfill"]
        self.assertTrue(message.startswith(f"{expected['refused_count']} row(s) claim readings ingested after they were published"))
        for identity in expected["refused_row_identities"]:
            self.assertIn(identity, message)
        # What the backfill would have fed a model if nothing checked it:
        with self.assertRaises(F.FutureInformationError) as leaked:
            F.assert_no_future_information(shortcuts.join_on_availability_unchecked(labels(), backfilled))
        self.assertEqual(sorted(leaked.exception.rows, key=lambda r: (r["machine_id"], r["prediction_time"])),
                         expected["leaking_training_rows"])
        OUTPUTS["backfill_leaks"] = leaked.exception.rows


class ReuseTests(unittest.TestCase):
    def test_second_consumer_reuses_the_table_without_recomputing(self):
        table = F.build_feature_table(primary_observations(), CONTRACT)
        snapshot = canonical(F.records(table))
        handover = F.build_training_set(F.load_labels(FIX / HANDOVER["label_file"]), table, CONTRACT, HANDOVER)
        self.assertEqual(canonical(F.records(table)), snapshot, "the shared table is read, never modified")
        columns = ["machine_id", "prediction_time", "feature_time", "available_at", "feature_age_minutes", "feature_status"]
        self.assertEqual(F.records(handover, columns), EXPECTED["reuse"]["rows"])
        self.assertEqual(len(F.training_rows(handover)), EXPECTED["reuse"]["usable_rows"])
        relaxed = F.build_training_set(F.load_labels(FIX / HANDOVER["label_file"]), table, CONTRACT,
                                       {**HANDOVER, "max_feature_age_minutes": FAILURE["max_feature_age_minutes"]})
        self.assertEqual(list(relaxed["feature_status"]), EXPECTED["reuse"]["statuses_at_180_minutes"])
        OUTPUTS["reuse"] = F.records(handover, columns)


class StarterTests(unittest.TestCase):
    def test_starter_marks_each_gap_and_keeps_the_rest(self):
        from starters import features as S
        calls = {
            "GAP 1": lambda: S.window_end(primary_observations()["observed_at"], 2),
            "GAP 2": lambda: S.compute_features(primary_observations(), ts("2026-03-02T10:30:00Z"), CONTRACT),
            "GAP 3": lambda: S.refuse_duplicates(labels(), ["machine_id", "prediction_time"], "label"),
            "GAP 4": lambda: S.point_in_time_join(labels(), F.build_feature_table(primary_observations(), CONTRACT), CONTRACT),
            "GAP 5": lambda: S.assess(ts("2026-03-02T11:00:00Z"), ts("2026-03-02T10:00:00Z"), 180),
            "GAP 6": lambda: S.online_store_at(F.build_feature_table(primary_observations(), CONTRACT), ts("2026-03-02T11:00:00Z")),
        }
        for gap, call in calls.items():
            with self.assertRaises(NotImplementedError) as caught:
                call()
            self.assertTrue(str(caught.exception).startswith(gap), gap)
        self.assertEqual(S.FEATURE_COLUMNS, F.FEATURE_COLUMNS)
        self.assertEqual(S.plain(pd.NaT), None)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()
    started_at = datetime.now(timezone.utc)
    started = time.monotonic()
    suite = unittest.TestSuite()
    for case in (FeatureTableTests, PointInTimeTests, FutureInformationTests, ServingConsistencyTests,
                 LateArrivalTests, ReuseTests, StarterTests):
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    exit_code = 0 if result.wasSuccessful() else 1
    hashes = lambda directory: {str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path.read_bytes()).hexdigest()
                                for path in sorted((ROOT / directory).iterdir()) if path.is_file()}
    evidence = {
        "lab": LAB, "executionClass": "local-executed", "runtime": "ml",
        "python": platform.python_version(), "interpreter": sys.executable,
        "packages": {name: metadata.version(name) for name in ("pandas", "numpy", "python-dateutil")},
        "java": "not used", "spark": "not used", "platform": platform.system() + " " + platform.release(),
        "startedAt": started_at.isoformat(), "finishedAt": datetime.now(timezone.utc).isoformat(),
        "durationSeconds": round(time.monotonic() - started, 3),
        "tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "skipped": len(result.skipped), "exit": exit_code,
        "fixtureHashes": hashes("fixtures"), "expectedHashes": hashes("expected"),
        "solutionHashes": {**hashes("solutions"), **hashes("starters"),
                           "run_tests.py": sha256((ROOT / "run_tests.py").read_bytes()).hexdigest()},
        "outputHashes": {name: sha256(canonical(value).encode("utf-8")).hexdigest() for name, value in sorted(OUTPUTS.items())},
        "commands": [f"{Path(sys.executable).name} run_tests.py --evidence <path>"],
        "notes": ("Local pandas on one machine; no Spark, no Databricks, no network. Expected values are hand-authored "
                  "literals in expected/*.json with derivations in DATA.md. The shortcuts and the drifted serving port "
                  "in starters/ are asserted to fail for their documented reasons; the starter's six gaps are asserted "
                  "to be marked. Machines, readings, schedule and policies are fictional."),
    }
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: evidence[key] for key in ("lab", "python", "tests", "failures", "errors", "skipped", "exit")}, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
