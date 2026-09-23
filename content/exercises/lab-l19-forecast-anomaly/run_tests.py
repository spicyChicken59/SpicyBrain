"""lab-l19-forecast-anomaly test runner (local-executed; pandas, numpy, scikit-learn).

    python run_tests.py --evidence <path>     # the reference solution
    python run_tests.py --starter             # your completed starters/forecast_lab.py

Run from this directory with Python 3.12 and requirements.txt installed.
Offline and CPU-only: no network, no Spark, no Databricks, no model service.
Every expected value is a literal, either written into this file or committed
in expected/*.json by the standard-library derivation in
expected/derive_expected.py (see DATA.md), which imports no solution code and
none of pandas, numpy or scikit-learn. No test compares the solution with a
value the solution computed. The six shortcuts in starters/shortcuts.py are
asserted to fail for their documented reasons, and the starter's nine gaps are
asserted to be marked. Fixture, expected, solution, starter and produced-output
SHA-256 hashes go into the evidence JSON.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from functools import cache
from hashlib import sha256
from importlib import import_module, metadata
import importlib.util
import json
import math
from pathlib import Path
import platform
import sys
import tempfile
import time
import unittest

sys.dont_write_bytecode = True  # keep the package free of __pycache__
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
from sklearn.metrics import mean_absolute_percentage_error  # noqa: E402

STARTER = "--starter" in sys.argv
L = import_module("starters.forecast_lab" if STARTER else "solutions.forecast_lab")
from starters import shortcuts  # noqa: E402

LAB = "lab-l19-forecast-anomaly"
FIX = ROOT / "fixtures"
NAMES = ("folds", "forecasts", "metrics", "intervals", "anomaly", "ranking")
EXPECTED = {name: json.loads((ROOT / "expected" / f"{name}.json").read_text(encoding="utf-8")) for name in NAMES}
DECISIONS = json.loads((FIX / "decisions.json").read_text(encoding="utf-8"))
H = DECISIONS["forecast"]["horizon_days"]
K = DECISIONS["forecast"]["folds"]
QUANTILES = tuple(DECISIONS["forecast"]["interval_quantiles"])
ANOMALY = DECISIONS["anomaly"]
RANKING = DECISIONS["ranking"]
FRAME = L.load_days(FIX / "line_days.csv")
UNITS, WORKING = L.arrays(FRAME)
LOTS = L.load_lots(FIX / "lots.csv")
METHODS = ("naive", "seasonal_naive", "lag_regression")
TOL = 2e-6
OUTPUTS: dict[str, object] = {}


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def num(values, digits: int = 6):
    return [round(float(v), digits) for v in values]


def iso(index: int) -> str:
    return FRAME["date"].iloc[int(index)].date().isoformat()


def load_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@cache
def folds():
    return L.rolling_origin_folds(len(FRAME), K, H)


@cache
def records():
    return L.backtest(FRAME, K, H)


@cache
def scores():
    return L.anomaly_scores(FRAME, L.calibration_rate(FRAME, ANOMALY["calibration_days"]),
                            ANOMALY["calibration_days"])


@cache
def table():
    return L.threshold_table(scores(), ANOMALY["thresholds"], ANOMALY["review_hours_per_flag"])


def fold_record(train, test) -> dict:
    return {"train_start": iso(train[0]), "train_end": iso(train[-1]), "train_rows": len(train),
            "test_start": iso(test[0]), "test_end": iso(test[-1]), "test_rows": len(test)}


class Close(unittest.TestCase):
    def close_list(self, produced, expected, label, delta=TOL):
        self.assertEqual(len(produced), len(expected), label)
        for got, want in zip(produced, expected):
            self.assertAlmostEqual(float(got), float(want), delta=delta, msg=label)


# --------------------------------------------------------------------------- fixture
class FixtureTests(unittest.TestCase):
    def test_generator_rebuilds_the_committed_csv_byte_for_byte(self):
        generator = load_path("generate_line_days", FIX / "generate_line_days.py")
        self.assertEqual(("\n".join(generator.rows()) + "\n").encode("utf-8"), (FIX / "line_days.csv").read_bytes())

    def test_calendar_and_injected_events_are_as_documented(self):
        self.assertEqual(len(FRAME), 82)
        self.assertEqual((iso(0), FRAME["weekday"].iloc[0]), ("2026-06-01", "Mon"))
        self.assertEqual((iso(81), FRAME["weekday"].iloc[81]), ("2026-08-21", "Fri"))
        sundays = FRAME[FRAME["weekday"] == "Sun"]
        self.assertEqual(len(sundays), 11)
        self.assertTrue(((sundays["planned_hours"] == 0) & (sundays["units"] == 0)).all())
        self.assertTrue((FRAME.loc[FRAME["weekday"] == "Sat", "planned_hours"] == 8).all())
        bad = [d.date().isoformat() for d in FRAME.loc[FRAME["event"] == "bad_lot", "date"]]
        self.assertEqual(bad, ["2026-07-07", "2026-07-16", "2026-07-27", "2026-08-06", "2026-08-11"])
        breakdown = FRAME[FRAME["event"] == "breakdown"]
        self.assertEqual((breakdown["date"].iloc[0].date().isoformat(), float(breakdown["run_hours"].iloc[0])),
                         ("2026-08-19", 5.5))

    def test_load_days_refuses_a_missing_day_and_a_duplicate_day(self):
        lines = (FIX / "line_days.csv").read_text(encoding="utf-8").splitlines()
        with tempfile.TemporaryDirectory() as tmp:
            gap = Path(tmp) / "gap.csv"
            gap.write_text("\n".join(l for l in lines if not l.startswith("2026-07-01")) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing day 2026-07-01"):
                L.load_days(gap)
            twice = Path(tmp) / "twice.csv"
            twice.write_text("\n".join(lines[:10] + [lines[9]] + lines[10:]) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate day 2026-06-09"):
                L.load_days(twice)

    def test_expected_literals_are_the_standard_library_derivation(self):
        source = (ROOT / "expected" / "derive_expected.py").read_text(encoding="utf-8")
        imports = [line for line in source.splitlines() if line.startswith(("import ", "from "))]
        for forbidden in ("numpy", "pandas", "sklearn", "solutions", "starters"):
            self.assertFalse(any(forbidden in line for line in imports), forbidden)
        built = load_path("derive_expected", ROOT / "expected" / "derive_expected.py").build()
        for name in NAMES:
            self.assertEqual(json.dumps(built[name], indent=2) + "\n",
                             (ROOT / "expected" / f"{name}.json").read_text(encoding="utf-8"), name)


# --------------------------------------------------------------------------- folds
class FoldTests(unittest.TestCase):
    def test_rolling_origins_match_the_index_arithmetic(self):
        produced = [fold_record(train, test) for train, test in folds()]
        OUTPUTS["folds"] = produced
        self.assertEqual(produced, EXPECTED["folds"]["folds"])
        self.assertEqual(sum(int(WORKING[test].sum()) for _, test in folds()), 24)

    def test_every_training_day_precedes_every_test_day(self):
        for train, test in folds():
            self.assertLess(train.max(), test.min())
            self.assertEqual(test.max() - test.min() + 1, H)

    def test_gap_and_sliding_window_move_the_training_edges(self):
        gap = [fold_record(tr, te) for tr, te in L.rolling_origin_folds(len(FRAME), K, H, gap=1)]
        sliding = [fold_record(tr, te) for tr, te in L.rolling_origin_folds(len(FRAME), K, H, max_train_size=28)]
        OUTPUTS["folds_gap_sliding"] = {"gap_1": gap, "max_train_28": sliding}
        self.assertEqual(gap, EXPECTED["folds"]["gap_1"])
        self.assertEqual(sliding, EXPECTED["folds"]["max_train_28"])

    def test_shuffled_kfold_trains_on_days_after_its_test_days(self):
        leaks = [int((train > test.min()).sum()) for train, test in shortcuts.shuffled_folds(len(FRAME))]
        OUTPUTS["shuffled_future_training_days"] = leaks
        self.assertTrue(all(n > 0 for n in leaks), "every shuffled fold trains on a later day")


# --------------------------------------------------------------------------- baselines and the model
class ForecastTests(Close):
    def test_naive_repeats_the_origin_value(self):
        for rec, exp in zip(records(), EXPECTED["forecasts"]["folds"]):
            self.assertEqual(iso(rec["origin"]), exp["origin"])
            self.assertEqual(num(rec["forecasts"]["naive"]), num(exp["naive"]))

    def test_seasonal_naive_copies_the_same_weekday_last_week(self):
        for rec, exp in zip(records(), EXPECTED["forecasts"]["folds"]):
            self.assertEqual(num(rec["forecasts"]["seasonal_naive"]), num(exp["seasonal_naive"]))
        OUTPUTS["seasonal_naive"] = [num(r["forecasts"]["seasonal_naive"]) for r in records()]

    def test_seasonal_naive_at_horizon_14_repeats_the_last_season(self):
        origin = int(folds()[-1][0][-1])
        produced = L.seasonal_naive_forecast(UNITS, origin, 14)
        OUTPUTS["horizon_14_seasonal_naive"] = num(produced)
        self.assertEqual(num(produced), num(EXPECTED["forecasts"]["horizon_14_seasonal_naive"]["forecast"]))
        self.assertEqual(num(produced[7:]), num(produced[:7]))

    def test_lag_regression_coefficients_match_exact_least_squares(self):
        for rec, exp in zip(records(), EXPECTED["forecasts"]["folds"]):
            model = rec["model"]
            self.assertEqual(len(model.training_rows), exp["training_rows"])
            self.close_list([model.intercept, *model.coefficients],
                            [exp["coefficients"][k] for k in ("intercept", "lag7", "lag14")], f"fold {rec['fold']}")
        OUTPUTS["coefficients"] = [num([r["model"].intercept, *r["model"].coefficients]) for r in records()]

    def test_lag_regression_forecasts_match_and_closed_days_are_zero(self):
        for rec, exp in zip(records(), EXPECTED["forecasts"]["folds"]):
            produced = rec["forecasts"]["lag_regression"]
            self.close_list(produced, exp["lag_regression"], f"fold {rec['fold']}")
            closed = ~WORKING[rec["test"]]
            self.assertEqual(closed.tolist(), exp["closed"])
            self.assertTrue(np.all(produced[closed] == 0.0))
        OUTPUTS["lag_regression"] = [num(r["forecasts"]["lag_regression"]) for r in records()]

    def test_a_horizon_beyond_the_shortest_lag_is_refused(self):
        model = records()[-1]["model"]
        with self.assertRaisesRegex(ValueError, r"horizon 14 .*lag 7"):
            L.lag_regression_forecast(model, UNITS, WORKING, 14)
        self.assertEqual(len(L.lag_regression_forecast(model, UNITS, WORKING, 7)), 7)

    def test_honest_forecasts_ignore_every_value_after_the_origin(self):
        train, _ = folds()[0]
        origin = int(train[-1])
        altered = UNITS.copy()
        altered[origin + 1:] = altered[origin + 1:] * 3 + 50
        for units in (UNITS, altered):
            model = L.fit_lag_regression(units, WORKING, origin)
            produced = (L.naive_forecast(units, origin, H), L.seasonal_naive_forecast(units, origin, H),
                        L.lag_regression_forecast(model, units, WORKING, H))
            if units is UNITS:
                reference = produced
            else:
                for got, want in zip(produced, reference):
                    self.assertEqual(num(got), num(want))

    def test_lag1_shortcut_reads_a_day_after_the_origin(self):
        origin = int(folds()[0][0][-1])
        altered = UNITS.copy()
        altered[origin + 1] += 100
        before, after = shortcuts.lag1_forecast(UNITS, origin, H), shortcuts.lag1_forecast(altered, origin, H)
        self.assertEqual(before[0], after[0], "step 1 reads the origin day itself")
        self.assertEqual(after[1] - before[1], 100, "step 2 reads the day after the origin")

    def test_same_day_shortcut_scores_better_than_anything_available_at_the_origin(self):
        maes = []
        for rec, exp in zip(records(), EXPECTED["metrics"]["leaky_same_day"]["folds"]):
            origin, test = rec["origin"], rec["test"]
            forecast = shortcuts.same_day_forecast(FRAME, origin, H)
            scored = WORKING[test]
            maes.append(L.mae(UNITS[test][scored], forecast[scored]))
            self.assertAlmostEqual(maes[-1], exp["mae"], delta=TOL)
        OUTPUTS["leaky_same_day_mae"] = num(maes)
        self.assertLess(np.mean(maes), EXPECTED["metrics"]["mean_mae"]["lag_regression"] * 0.6)
        origin = records()[-1]["origin"]
        shifted = FRAME.copy()
        shifted.loc[origin + H, "run_hours"] = shifted.loc[origin + H, "run_hours"] - 4
        moved = shortcuts.same_day_forecast(shifted, origin, H)[-1] - shortcuts.same_day_forecast(FRAME, origin, H)[-1]
        self.assertLess(moved, -100, "the last step moves with its own day's run_hours")


# --------------------------------------------------------------------------- metrics
class MetricTests(Close):
    def test_mae_per_fold_and_the_mean_over_folds(self):
        for rec, exp in zip(records(), EXPECTED["metrics"]["folds"]):
            for name in METHODS:
                self.assertAlmostEqual(rec["mae"][name], exp["mae"][name], delta=TOL, msg=f"{name} fold {rec['fold']}")
        for name in METHODS:
            self.assertAlmostEqual(float(np.mean([r["mae"][name] for r in records()])),
                                   EXPECTED["metrics"]["mean_mae"][name], delta=TOL)
        OUTPUTS["mae"] = {name: num([r["mae"][name] for r in records()]) for name in METHODS}

    def test_the_model_wins_the_mean_and_three_folds_but_not_fold_one(self):
        wins = [r["mae"]["lag_regression"] < r["mae"]["seasonal_naive"] for r in records()]
        self.assertEqual(wins, [False, True, True, True])
        self.assertEqual(sum(wins), EXPECTED["metrics"]["lag_regression_wins_vs_seasonal_naive"])
        means = {name: np.mean([r["mae"][name] for r in records()]) for name in METHODS}
        self.assertEqual(min(means, key=means.get), EXPECTED["metrics"]["preferred_by_mean_mae"])
        self.assertLess(means["lag_regression"], means["seasonal_naive"])
        self.assertLess(means["seasonal_naive"], means["naive"])

    def test_mape_on_working_days(self):
        for rec, exp in zip(records(), EXPECTED["metrics"]["folds"]):
            for name in METHODS:
                self.assertAlmostEqual(rec["mape"][name], exp["mape"][name], delta=TOL)

    def test_mape_refuses_a_zero_actual(self):
        rec = records()[0]
        with self.assertRaisesRegex(ValueError, "zero"):
            L.mape(UNITS[rec["test"]], rec["forecasts"]["naive"])

    def test_numpy_mape_over_a_closed_day_is_infinite(self):
        rec = records()[0]
        value = shortcuts.mape_including_closed(UNITS[rec["test"]], rec["forecasts"]["naive"])
        OUTPUTS["numpy_mape_with_zero"] = str(value)
        self.assertTrue(math.isinf(value))

    def test_scikit_learn_mape_turns_a_zero_actual_into_a_huge_number(self):
        produced = {}
        for rec, exp in zip(records(), EXPECTED["metrics"]["folds"]):
            actual = UNITS[rec["test"]]
            without_calendar = L.lag_regression_forecast(rec["model"], UNITS, WORKING, H, calendar=False)
            values = {
                "naive": mean_absolute_percentage_error(actual, rec["forecasts"]["naive"]),
                "seasonal_naive": mean_absolute_percentage_error(actual, rec["forecasts"]["seasonal_naive"]),
                "lag_regression_with_calendar": mean_absolute_percentage_error(actual, rec["forecasts"]["lag_regression"]),
                "lag_regression_without_calendar": mean_absolute_percentage_error(actual, without_calendar),
            }
            for name, value in values.items():
                want = exp["sklearn_mape_all_days"][name]
                self.assertTrue(math.isclose(value, want, rel_tol=1e-9), f"{name} fold {rec['fold']}: {value} vs {want}")
            self.assertGreater(values["naive"], 1e15)
            self.assertGreater(values["lag_regression_without_calendar"], 1e14)
            self.assertLess(values["seasonal_naive"], 1.0)
            produced[rec["fold"]] = {k: float(f"{v:.9e}") for k, v in values.items()}
        OUTPUTS["sklearn_mape_all_days"] = produced

    def test_mase_scales_and_values(self):
        for rec, exp in zip(records(), EXPECTED["metrics"]["folds"]):
            self.assertAlmostEqual(rec["mase_scale"], exp["mase_scale"], delta=TOL)
            for name in METHODS:
                self.assertAlmostEqual(rec["mase"][name], exp["mase"][name], delta=TOL)
        OUTPUTS["mase"] = {name: num([r["mase"][name] for r in records()]) for name in METHODS}


# --------------------------------------------------------------------------- uncertainty
class IntervalTests(Close):
    def test_residual_quantiles_per_fold(self):
        for rec, exp in zip(records(), EXPECTED["forecasts"]["folds"]):
            low, high = np.quantile(rec["model"].residuals, QUANTILES)
            self.assertAlmostEqual(low, exp["residual_quantiles"]["q10"], delta=TOL)
            self.assertAlmostEqual(high, exp["residual_quantiles"]["q90"], delta=TOL)

    def test_band_rows_and_coverage(self):
        inside_total, produced = 0, []
        for rec, exp in zip(records(), EXPECTED["intervals"]["folds"]):
            lower, upper = L.residual_band(rec["model"], rec["forecasts"]["lag_regression"], QUANTILES)
            rows = []
            for i, t in enumerate(rec["test"]):
                if not WORKING[t]:
                    continue
                rows.append({"date": iso(t), "forecast": round(float(rec["forecasts"]["lag_regression"][i]), 6),
                             "lower": round(float(lower[i]), 6), "upper": round(float(upper[i]), 6),
                             "inside": bool(lower[i] <= UNITS[t] <= upper[i])})
            self.assertEqual([r["date"] for r in rows], [r["date"] for r in exp["rows"]])
            for got, want in zip(rows, exp["rows"]):
                for key in ("forecast", "lower", "upper"):
                    self.assertAlmostEqual(got[key], want[key], delta=TOL)
                self.assertEqual(got["inside"], want["inside"], got["date"])
            inside_total += sum(r["inside"] for r in rows)
            produced.append(rows)
        OUTPUTS["intervals"] = produced
        self.assertEqual((inside_total, EXPECTED["intervals"]["working_days"]), (EXPECTED["intervals"]["inside"], 24))
        self.assertEqual([f["inside"] for f in EXPECTED["intervals"]["folds"]], [4, 6, 5, 5])

    def test_the_breakdown_day_falls_far_below_its_band(self):
        rec = records()[-1]
        lower, _ = L.residual_band(rec["model"], rec["forecasts"]["lag_regression"], QUANTILES)
        position = list(rec["test"]).index(int(FRAME.index[FRAME["event"] == "breakdown"][0]))
        self.assertLess(UNITS[rec["test"][position]], lower[position] - 200)


# --------------------------------------------------------------------------- anomalies
class AnomalyTests(Close):
    def test_calibration_uses_only_the_days_before_scoring(self):
        rate = L.calibration_rate(FRAME, ANOMALY["calibration_days"])
        self.assertAlmostEqual(rate, EXPECTED["anomaly"]["rate"], delta=1e-8)
        leaky = shortcuts.rate_from_all_days(FRAME)
        self.assertAlmostEqual(leaky, EXPECTED["anomaly"]["rate_all_days"], delta=1e-8)
        self.assertGreater(leaky, rate)

    def test_closed_days_are_not_scored(self):
        z = scores()["z"]
        self.assertEqual(int(z.isna().sum()), EXPECTED["anomaly"]["closed_days_not_scored"])
        self.assertEqual(int(z.notna().sum()), EXPECTED["anomaly"]["scored_days"])
        self.assertTrue((scores().loc[z.isna(), "units"] == 0).all())

    def test_high_scores_match_the_derivation(self):
        rated = scores().dropna(subset=["z"])
        high = rated[rated["z"] >= min(ANOMALY["thresholds"])].sort_values("z", ascending=False)
        want = EXPECTED["anomaly"]["scores_at_or_above_lowest_threshold"]
        self.assertEqual([d.date().isoformat() for d in high["date"]], [w["date"] for w in want])
        self.close_list(high["z"], [w["z"] for w in want], "z", delta=6e-5)
        OUTPUTS["high_scores"] = [[d.date().isoformat(), round(float(z), 4)] for d, z in zip(high["date"], high["z"])]

    def test_threshold_table_counts_reviews_catches_and_misses(self):
        produced = table().to_dict("records")
        OUTPUTS["threshold_table"] = produced
        for got, want in zip(produced, EXPECTED["anomaly"]["table"]):
            for key in ("threshold", "flagged", "true_positive", "false_positive", "missed", "review_hours", "flagged_dates"):
                self.assertEqual(got[key], want[key], f"{key} at {want['threshold']}")
        self.assertEqual(len(produced), len(EXPECTED["anomaly"]["table"]))

    def test_raising_the_threshold_never_adds_reviews(self):
        flagged, missed = table()["flagged"].tolist(), table()["missed"].tolist()
        self.assertEqual(flagged, sorted(flagged, reverse=True))
        self.assertEqual(missed, sorted(missed))

    def test_the_base_cost_and_the_altered_cost_prefer_different_thresholds(self):
        produced = {}
        for name, miss in ANOMALY["miss_hours"].items():
            choice, totals = L.choose_threshold(table(), miss)
            want = EXPECTED["anomaly"]["costs"][name]
            self.assertEqual(totals, [float(t) for t in want["total_hours"]], name)
            self.assertEqual(choice, want["preferred_threshold"], name)
            produced[name] = {"threshold": choice, "totals": totals}
        OUTPUTS["costs"] = produced
        self.assertEqual((produced["base"]["threshold"], produced["altered"]["threshold"]), (2.5, 1.5))

    def test_a_cost_tie_goes_to_the_higher_threshold(self):
        tied = table().iloc[:0].copy()
        tied = tied.reindex(range(2))
        tied["threshold"], tied["review_hours"], tied["missed"] = [2.0, 2.5], [6.0, 3.0], [0, 1]
        choice, totals = L.choose_threshold(tied, 3)
        self.assertEqual((choice, totals), (2.5, [6.0, 6.0]))

    def test_calibrating_on_the_scored_days_hides_a_bad_lot(self):
        leaky = L.threshold_table(L.anomaly_scores(FRAME, shortcuts.rate_from_all_days(FRAME), ANOMALY["calibration_days"]),
                                  ANOMALY["thresholds"], ANOMALY["review_hours_per_flag"]).to_dict("records")
        OUTPUTS["leaky_threshold_table"] = leaky
        for got, want in zip(leaky, EXPECTED["anomaly"]["leaky_rate_table"]):
            self.assertEqual((got["flagged"], got["true_positive"], got["missed"]),
                             (want["flagged"], want["true_positive"], want["missed"]))
        at_base = [row for row in leaky if row["threshold"] == 2.5][0]
        honest = [row for row in table().to_dict("records") if row["threshold"] == 2.5][0]
        self.assertEqual((honest["missed"], at_base["missed"]), (1, 2))

    def test_the_breakdown_is_not_a_defect_anomaly(self):
        row = scores()[scores()["event"] == "breakdown"]
        self.assertAlmostEqual(float(row["z"].iloc[0]), EXPECTED["anomaly"]["breakdown_day"]["z"], delta=6e-5)
        self.assertLess(float(row["z"].iloc[0]), min(ANOMALY["thresholds"]))


# --------------------------------------------------------------------------- ranking
class RankingTests(unittest.TestCase):
    def test_accuracy_prefers_model_a_and_ties_it_with_calling_every_lot_conforming(self):
        labels = LOTS["nonconforming"].to_numpy()
        produced = {"model_a": L.accuracy_at(LOTS["score_a"], labels, RANKING["accuracy_threshold"]),
                    "model_b": L.accuracy_at(LOTS["score_b"], labels, RANKING["accuracy_threshold"]),
                    "all_conforming": L.accuracy_at(np.zeros(len(LOTS)), labels, RANKING["accuracy_threshold"])}
        OUTPUTS["accuracy"] = produced
        self.assertEqual(produced, EXPECTED["ranking"]["accuracy"])
        self.assertEqual(produced["model_a"], produced["all_conforming"])

    def check_capacity(self, name):
        k = RANKING["capacity"][name]
        want = EXPECTED["ranking"]["capacity"][name]
        produced = {}
        for model, column in (("model_a", "score_a"), ("model_b", "score_b")):
            precision, recall, top = L.precision_recall_at_k(LOTS, column, k)
            produced[model] = {"precision": precision, "recall": recall, "top": top}
            self.assertEqual(top, want[model]["top"])
            self.assertAlmostEqual(precision, want[model]["precision"], delta=TOL)
            self.assertAlmostEqual(recall, want[model]["recall"], delta=TOL)
        OUTPUTS[f"ranking_{name}"] = produced
        return max(produced, key=lambda m: produced[m]["precision"])

    def test_four_inspections_prefer_model_b(self):
        self.assertEqual(self.check_capacity("base"), EXPECTED["ranking"]["capacity"]["base"]["preferred"])
        self.assertEqual(self.check_capacity("base"), "model_b")

    def test_eight_inspections_prefer_model_a(self):
        self.assertEqual(self.check_capacity("altered"), EXPECTED["ranking"]["capacity"]["altered"]["preferred"])
        self.assertEqual(self.check_capacity("altered"), "model_a")

    def test_picking_by_accuracy_chooses_the_worse_queue_for_four_inspections(self):
        self.assertEqual(shortcuts.pick_by_accuracy(LOTS, RANKING["accuracy_threshold"]), "model_a")
        self.assertNotEqual("model_a", EXPECTED["ranking"]["capacity"]["base"]["preferred"])


# --------------------------------------------------------------------------- starter
class StarterTests(unittest.TestCase):
    def test_every_gap_in_the_untouched_starter_is_marked(self):
        S = import_module("starters.forecast_lab")
        model = S.fit_lag_regression(UNITS, WORKING, 53)
        empty = FRAME.iloc[:0]
        calls = {
            "TASK 1": lambda: S.rolling_origin_folds(len(FRAME)),
            "TASK 2": lambda: S.seasonal_naive_forecast(UNITS, 53, H),
            "TASK 3": lambda: S.lag_regression_forecast(model, UNITS, WORKING, H),
            "TASK 4": lambda: S.mape([1.0], [1.0]),
            "TASK 5": lambda: S.residual_band(model, np.zeros(H)),
            "TASK 6": lambda: S.anomaly_scores(FRAME, 0.02, 28),
            "TASK 7": lambda: S.threshold_table(empty, [2.0], 3),
            "TASK 8": lambda: S.choose_threshold(empty, 12),
            "TASK 9": lambda: S.precision_recall_at_k(LOTS, "score_a", 4),
        }
        for tag, call in calls.items():
            with self.assertRaises(NotImplementedError, msg=tag) as caught:
                call()
            self.assertTrue(str(caught.exception).startswith(tag + ":"), tag)
        reference = L.fit_lag_regression(UNITS, WORKING, 53)
        self.assertEqual(num([model.intercept, *model.coefficients]), num([reference.intercept, *reference.coefficients]))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--starter", action="store_true",
                        help="test your completed starters/forecast_lab.py instead of the reference solution")
    args = parser.parse_args()
    if args.starter and args.evidence:
        parser.error("evidence records the reference solution only; drop --evidence when using --starter")
    started_at = datetime.now(timezone.utc)
    started = time.monotonic()
    suite = unittest.TestSuite()
    cases = [FixtureTests, FoldTests, ForecastTests, MetricTests, IntervalTests, AnomalyTests, RankingTests]
    if not args.starter:  # the gap check only makes sense on the untouched starter
        cases.append(StarterTests)
    for case in cases:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    exit_code = 0 if result.wasSuccessful() else 1

    def hashes(directory: str) -> dict[str, str]:
        return {str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path.read_bytes()).hexdigest()
                for path in sorted((ROOT / directory).iterdir()) if path.is_file()}

    packages = ("pandas", "numpy", "scikit-learn", "scipy", "joblib", "threadpoolctl")
    evidence = {
        "lab": LAB, "executionClass": "local-executed", "runtime": "ml",
        "python": platform.python_version(), "interpreter": sys.executable,
        "packages": {name: metadata.version(name) for name in packages},
        "java": "not used", "spark": "not used", "platform": platform.system() + " " + platform.release(),
        "startedAt": started_at.isoformat(), "finishedAt": datetime.now(timezone.utc).isoformat(),
        "durationSeconds": round(time.monotonic() - started, 3),
        "tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "skipped": len(result.skipped), "exit": exit_code,
        "fixtureHashes": hashes("fixtures"), "expectedHashes": hashes("expected"),
        "solutionHashes": {**hashes("solutions"), **hashes("starters"),
                           "run_tests.py": sha256((ROOT / "run_tests.py").read_bytes()).hexdigest(),
                           "requirements.txt": sha256((ROOT / "requirements.txt").read_bytes()).hexdigest()},
        "outputHashes": {name: sha256(canonical(value).encode("utf-8")).hexdigest() for name, value in sorted(OUTPUTS.items())},
        "commands": [f"{Path(sys.executable).name} run_tests.py --evidence <path>"],
        "notes": ("Local pandas, numpy and scikit-learn on one machine, CPU only: TimeSeriesSplit rolling origins, "
                  "naive and seasonal-naive baselines, a LinearRegression on the 7- and 14-day lags, an empirical "
                  "residual band, a defect-rate anomaly score with a threshold table, and precision at k for an "
                  "inspection queue. No Spark, no Databricks, no AutoML, no network, no model service. The daily "
                  "fixture comes from the seeded standard-library generator in fixtures/ and is checked byte for "
                  "byte; expected values are literals in this runner or in expected/*.json, written by the "
                  "independent standard-library derivation in expected/derive_expected.py (DATA.md). The six "
                  "shortcuts in starters/shortcuts.py are asserted to fail for their documented reasons; the "
                  "starter's nine gaps are asserted to be marked. Cinderline, line L4, its lots, events and "
                  "inspector-hour costs are fictional; nothing here is a safety or financial guarantee."),
    }
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: evidence[key] for key in ("lab", "python", "tests", "failures", "errors", "skipped", "exit")}, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
