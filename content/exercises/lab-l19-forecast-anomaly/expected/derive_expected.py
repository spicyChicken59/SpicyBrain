"""Independent derivation of every expected value in expected/*.json.

    python expected/derive_expected.py            # rewrite expected/*.json
    python expected/derive_expected.py --check    # fail if a committed file differs

Standard library only (csv, json, math, fractions). It never imports
solutions/, pandas, numpy or scikit-learn, and it does not share code with
the reference solution: fold boundaries are index arithmetic, the lag
regression is solved exactly with fractions.Fraction from the normal
equations, quantiles use the linear-interpolation rule written out below,
and scikit-learn's MAPE on a zero actual is predicted from its documented
guard (divide by max(|actual|, machine epsilon)) rather than by calling it.
DATA.md explains each derivation in words.
"""
from __future__ import annotations

import csv
from fractions import Fraction
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / "fixtures"
OUT = ROOT / "expected"
EPS = 2.0 ** -52  # float64 machine epsilon, 2.220446049250313e-16
R6 = 6


def r(x: float, digits: int = R6) -> float:
    return round(float(x), digits)


def load_days():
    with open(FIX / "line_days.csv", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return [
        {
            "date": row["date"],
            "weekday": row["weekday"],
            "planned": int(row["planned_hours"]),
            "run": Fraction(row["run_hours"]),
            "units": int(row["units"]),
            "defects": int(row["defects"]),
            "event": row["event"],
        }
        for row in rows
    ]


DAYS = load_days()
DEC = json.loads((FIX / "decisions.json").read_text(encoding="utf-8"))
N = len(DAYS)
Y = [d["units"] for d in DAYS]
WORK = [d["planned"] > 0 for d in DAYS]
H = DEC["forecast"]["horizon_days"]
K = DEC["forecast"]["folds"]
M = DEC["forecast"]["season_days"]
Q_LO, Q_HI = DEC["forecast"]["interval_quantiles"]


# ---------------------------------------------------------------- folds
def fold_bounds(gap: int = 0, max_train: int | None = None):
    """Expanding-window folds: the last K blocks of H days are the test sets."""
    folds = []
    for k in range(K):
        test_start = N - (K - k) * H
        train_end = test_start - gap          # exclusive
        train_start = 0
        if max_train is not None and max_train < train_end:
            train_start = train_end - max_train
        folds.append((train_start, train_end - 1, test_start, test_start + H - 1))
    return folds


FOLDS = fold_bounds()


def fold_record(bounds):
    a, b, c, d = bounds
    return {
        "train_start": DAYS[a]["date"], "train_end": DAYS[b]["date"], "train_rows": b - a + 1,
        "test_start": DAYS[c]["date"], "test_end": DAYS[d]["date"], "test_rows": d - c + 1,
    }


# ---------------------------------------------------------------- linear algebra (exact)
def solve(matrix, vector):
    """Gauss-Jordan elimination over Fractions (exact)."""
    n = len(vector)
    a = [[Fraction(v) for v in row] + [Fraction(vector[i])] for i, row in enumerate(matrix)]
    for col in range(n):
        pivot = next(i for i in range(col, n) if a[i][col] != 0)
        a[col], a[pivot] = a[pivot], a[col]
        p = a[col][col]
        a[col] = [v / p for v in a[col]]
        for i in range(n):
            if i != col and a[i][col] != 0:
                f = a[i][col]
                a[i] = [vi - f * vc for vi, vc in zip(a[i], a[col])]
    return [a[i][n] for i in range(n)]


def ols(rows_x, rows_y):
    """Least squares with an intercept: returns exact Fraction coefficients."""
    X = [[1] + list(x) for x in rows_x]
    p = len(X[0])
    xtx = [[sum(Fraction(row[i]) * row[j] for row in X) for j in range(p)] for i in range(p)]
    xty = [sum(Fraction(row[i]) * yv for row, yv in zip(X, rows_y)) for i in range(p)]
    return solve(xtx, xty)


def quantile(values, q):
    """Linear interpolation between order statistics at position (n - 1) * q."""
    xs = sorted(values)
    pos = (len(xs) - 1) * q
    lo = math.floor(pos)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (pos - lo) * (xs[hi] - xs[lo])


# ---------------------------------------------------------------- forecasts
def naive(origin, horizon):
    return [Y[origin]] * horizon


def seasonal_naive(origin, horizon):
    return [Y[origin + h - M * ((h - 1) // M + 1)] for h in range(1, horizon + 1)]


def lag_rows(origin):
    return [t for t in range(14, origin + 1) if WORK[t]]


def lag_model(origin):
    rows = lag_rows(origin)
    coef = ols([(Y[t - 7], Y[t - 14]) for t in rows], [Y[t] for t in rows])
    fitted = [coef[0] + coef[1] * Y[t - 7] + coef[2] * Y[t - 14] for t in rows]
    residuals = [float(Fraction(Y[t]) - f) for t, f in zip(rows, fitted)]
    return coef, rows, residuals


def lag_forecast(coef, origin, horizon, calendar=True):
    out = []
    for h in range(1, horizon + 1):
        t = origin + h
        if calendar and not WORK[t]:
            out.append(Fraction(0))
        else:
            out.append(coef[0] + coef[1] * Y[t - 7] + coef[2] * Y[t - 14])
    return out


def same_day_model(origin):
    """The leaky shortcut: units explained by the SAME day's run_hours."""
    rows = [t for t in range(0, origin + 1) if WORK[t]]
    return ols([(DAYS[t]["run"],) for t in rows], [Y[t] for t in rows])


# ---------------------------------------------------------------- metrics
def mae(actual, forecast):
    """Exact mean absolute error (a Fraction)."""
    return sum(abs(Fraction(a) - Fraction(f)) for a, f in zip(actual, forecast)) / len(actual)


def mape(actual, forecast):
    """Exact mean absolute percentage error in percent; every actual here is positive."""
    return sum(abs(Fraction(a) - Fraction(f)) / a for a, f in zip(actual, forecast)) / len(actual) * 100


def sklearn_style_mape(actual, forecast):
    """What sklearn.metrics.mean_absolute_percentage_error returns: a fraction, not a
    percentage, dividing each absolute error by max(|actual|, machine epsilon)."""
    terms = [abs(float(f) - float(a)) / max(abs(float(a)), EPS) for a, f in zip(actual, forecast)]
    return float(f"{math.fsum(terms) / len(terms):.12e}")  # 12 significant digits, any Python version


def mase_scale(origin):
    rows = [t for t in range(M, origin + 1) if WORK[t]]
    return Fraction(sum(abs(Y[t] - Y[t - M]) for t in rows), len(rows))


def build():
    expected = {}
    # folds -------------------------------------------------------------
    expected["folds"] = {
        "n_rows": N, "n_splits": K, "test_size": H,
        "folds": [fold_record(f) for f in FOLDS],
        "gap_1": [fold_record(f) for f in fold_bounds(gap=1)],
        "max_train_28": [fold_record(f) for f in fold_bounds(max_train=28)],
        "working_test_days": sum(WORK[t] for f in FOLDS for t in range(f[2], f[3] + 1)),
    }

    # forecasts, metrics, intervals ---------------------------------------
    forecasts, metric_rows, interval_folds = [], [], []
    methods = ("naive", "seasonal_naive", "lag_regression")
    inside_total, margins = 0, []
    exact = {m: [] for m in methods}
    exact_mase = {m: [] for m in methods}
    for k, (_, origin, c, d) in enumerate(FOLDS, start=1):
        test = list(range(c, d + 1))
        coef, rows, residuals = lag_model(origin)
        f_naive = naive(origin, H)
        f_snaive = seasonal_naive(origin, H)
        f_lag = lag_forecast(coef, origin, H)
        f_lag_nocal = lag_forecast(coef, origin, H, calendar=False)
        q_lo, q_hi = quantile(residuals, Q_LO), quantile(residuals, Q_HI)
        forecasts.append({
            "fold": k, "origin": DAYS[origin]["date"],
            "dates": [DAYS[t]["date"] for t in test],
            "closed": [not WORK[t] for t in test],
            "actual": [Y[t] for t in test],
            "naive": [int(v) for v in f_naive],
            "seasonal_naive": [int(v) for v in f_snaive],
            "lag_regression": [r(v) for v in f_lag],
            "coefficients": {"intercept": r(coef[0]), "lag7": r(coef[1]), "lag14": r(coef[2])},
            "training_rows": len(rows),
            "residual_quantiles": {"q10": r(q_lo), "q90": r(q_hi)},
        })
        work_idx = [i for i, t in enumerate(test) if WORK[t]]
        actual_w = [Y[test[i]] for i in work_idx]
        scale = mase_scale(origin)
        row = {"fold": k, "origin": DAYS[origin]["date"], "working_days": len(work_idx),
               "mase_scale": r(scale), "mae": {}, "mape": {}, "mase": {}}
        for name, f in zip(methods, (f_naive, f_snaive, f_lag)):
            fw = [f[i] for i in work_idx]
            exact[name].append(mae(actual_w, fw))
            exact_mase[name].append(mae(actual_w, fw) / scale)
            row["mae"][name] = r(exact[name][-1])
            row["mape"][name] = r(mape(actual_w, fw))
            row["mase"][name] = r(exact_mase[name][-1])
        all_actual = [Y[t] for t in test]
        row["sklearn_mape_all_days"] = {
            "naive": sklearn_style_mape(all_actual, f_naive),
            "seasonal_naive": sklearn_style_mape(all_actual, f_snaive),
            "lag_regression_with_calendar": sklearn_style_mape(all_actual, f_lag),
            "lag_regression_without_calendar": sklearn_style_mape(all_actual, f_lag_nocal),
        }
        metric_rows.append(row)
        band = []
        for i in work_idx:
            t = test[i]
            point = float(f_lag[i])
            lower, upper = point + q_lo, point + q_hi
            inside = lower <= Y[t] <= upper
            margins.append(min(abs(Y[t] - lower), abs(Y[t] - upper)))
            inside_total += inside
            band.append({"date": DAYS[t]["date"], "weekday": DAYS[t]["weekday"], "actual": Y[t],
                         "forecast": r(point), "lower": r(lower), "upper": r(upper), "inside": inside})
        interval_folds.append({"fold": k, "rows": band, "inside": sum(b["inside"] for b in band)})
    assert min(margins) > 1e-3, "an actual sits on an interval bound; the fixture would be fragile"

    means = {m: r(sum(exact[m]) / K) for m in methods}
    mase_means = {m: r(sum(exact_mase[m]) / K) for m in methods}
    wins = sum(a < b for a, b in zip(exact["lag_regression"], exact["seasonal_naive"]))
    preferred = min(methods, key=lambda m: sum(exact[m]))

    leaky, leaky_exact = [], []
    for k, (_, origin, c, d) in enumerate(FOLDS, start=1):
        coef = same_day_model(origin)
        test = [t for t in range(c, d + 1) if WORK[t]]
        f = [coef[0] + coef[1] * DAYS[t]["run"] for t in test]
        leaky_exact.append(mae([Y[t] for t in test], f))
        leaky.append({"fold": k, "intercept": r(coef[0]), "per_run_hour": r(coef[1]),
                      "mae": r(leaky_exact[-1])})

    last_origin = FOLDS[-1][1]
    expected["forecasts"] = {
        "folds": forecasts,
        "horizon_14_seasonal_naive": {
            "origin": DAYS[last_origin]["date"],
            "forecast": [int(v) for v in seasonal_naive(last_origin, 14)],
        },
    }
    expected["metrics"] = {
        "folds": metric_rows,
        "mean_mae": means,
        "mean_mase": mase_means,
        "lag_regression_wins_vs_seasonal_naive": wins,
        "preferred_by_mean_mae": preferred,
        "leaky_same_day": {"folds": leaky, "mean_mae": r(sum(leaky_exact) / K)},
    }
    expected["intervals"] = {
        "quantiles": [Q_LO, Q_HI],
        "folds": interval_folds,
        "inside": inside_total,
        "working_days": expected["folds"]["working_test_days"],
        "coverage": r(inside_total / expected["folds"]["working_test_days"]),
    }

    # anomaly ---------------------------------------------------------------
    a = DEC["anomaly"]
    cal = a["calibration_days"]
    rate = Fraction(sum(d["defects"] for d in DAYS[:cal]), sum(d["units"] for d in DAYS[:cal]))
    rate_all = Fraction(sum(d["defects"] for d in DAYS), sum(d["units"] for d in DAYS))

    def scores(rate_used):
        out = []
        for t in range(cal, N):
            if DAYS[t]["units"] == 0:
                continue
            e = rate_used * DAYS[t]["units"]
            z = float(DAYS[t]["defects"] - e) / math.sqrt(float(e))
            out.append((t, float(e), z))
        return out

    def table(score_rows):
        rows = []
        for thr in a["thresholds"]:
            flagged = [t for t, _, z in score_rows if z >= thr]
            bad = [t for t, _, _ in score_rows if DAYS[t]["event"] == "bad_lot"]
            tp = sum(DAYS[t]["event"] == "bad_lot" for t in flagged)
            rows.append({"threshold": thr, "flagged": len(flagged), "true_positive": tp,
                         "false_positive": len(flagged) - tp, "missed": len(bad) - tp,
                         "review_hours": len(flagged) * a["review_hours_per_flag"],
                         "flagged_dates": [DAYS[t]["date"] for t in flagged]})
        return rows

    honest = scores(rate)
    for _, _, z in honest:
        assert min(abs(z - thr) for thr in a["thresholds"]) > 1e-6, "a score sits on a threshold"
    honest_table = table(honest)
    costs = {}
    for name, miss in a["miss_hours"].items():
        totals = [row["review_hours"] + row["missed"] * miss for row in honest_table]
        best = min(totals)
        choice = max(row["threshold"] for row, tot in zip(honest_table, totals) if tot == best)
        costs[name] = {"miss_hours": miss, "total_hours": totals, "preferred_threshold": choice}
    expected["anomaly"] = {
        "calibration_days": cal,
        "calibration_end": DAYS[cal - 1]["date"],
        "rate": r(rate, 8),
        "rate_all_days": r(rate_all, 8),
        "scored_days": len(honest),
        "closed_days_not_scored": sum(1 for t in range(cal, N) if DAYS[t]["units"] == 0),
        "bad_lot_days": sum(1 for t, _, _ in honest if DAYS[t]["event"] == "bad_lot"),
        "scores_at_or_above_lowest_threshold": [
            {"date": DAYS[t]["date"], "weekday": DAYS[t]["weekday"], "units": DAYS[t]["units"],
             "defects": DAYS[t]["defects"], "expected": r(e, 4), "z": r(z, 4), "event": DAYS[t]["event"]}
            for t, e, z in sorted(honest, key=lambda x: -x[2]) if z >= min(a["thresholds"])
        ],
        "table": honest_table,
        "costs": costs,
        "leaky_rate_table": table(scores(rate_all)),
        "breakdown_day": next({"date": DAYS[t]["date"], "z": r(z, 4)} for t, _, z in honest
                              if DAYS[t]["event"] == "breakdown"),
    }

    # ranking -----------------------------------------------------------------
    with open(FIX / "lots.csv", newline="", encoding="utf-8") as handle:
        lots = [{"lot": row["lot_id"], "a": Fraction(row["score_a"]), "b": Fraction(row["score_b"]),
                 "y": int(row["nonconforming"])} for row in csv.DictReader(handle)]
    rk = DEC["ranking"]
    positives = sum(l["y"] for l in lots)

    def accuracy(key):
        return sum((l[key] >= Fraction(str(rk["accuracy_threshold"]))) == bool(l["y"]) for l in lots) / len(lots)

    def top(key, k):
        return [l["lot"] for l in sorted(lots, key=lambda l: -l[key])[:k]]

    def at_k(key, k):
        chosen = top(key, k)
        hits = sum(l["y"] for l in lots if l["lot"] in chosen)
        return {"top": chosen, "hits": hits, "precision": r(hits / k), "recall": r(hits / positives)}

    ranking = {
        "lots": len(lots), "nonconforming": positives,
        "accuracy": {"model_a": r(accuracy("a")), "model_b": r(accuracy("b")),
                     "all_conforming": r(sum(1 - l["y"] for l in lots) / len(lots))},
        "capacity": {},
    }
    for name, k in rk["capacity"].items():
        pa, pb = at_k("a", k), at_k("b", k)
        ranking["capacity"][name] = {
            "k": k, "model_a": pa, "model_b": pb,
            "preferred": "model_a" if pa["precision"] > pb["precision"] else "model_b",
        }
    ranking["preferred_by_accuracy"] = "model_a" if ranking["accuracy"]["model_a"] > ranking["accuracy"]["model_b"] else "model_b"
    expected["ranking"] = ranking
    return expected


def main() -> int:
    expected = build()
    check = "--check" in sys.argv
    stale = []
    for name, value in expected.items():
        text = json.dumps(value, indent=2) + "\n"
        path = OUT / f"{name}.json"
        if check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                stale.append(name)
        else:
            path.write_text(text, encoding="utf-8", newline="\n")
    if stale:
        print("stale expected files: " + ", ".join(stale), file=sys.stderr)
        return 1
    print("expected files " + ("current" if check else "written") + ": " + ", ".join(expected))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
