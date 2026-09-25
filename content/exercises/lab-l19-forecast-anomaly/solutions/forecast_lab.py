"""Reference solution for lab-l19-forecast-anomaly.

Forecast next week's units for fictional Cinderline's bracket line L4, compare
the forecast with two baselines on rolling origins, put an honest range around
it, turn an anomaly threshold into an inspection workload, and compare two
inspection-queue rankings. pandas, numpy and scikit-learn only; CPU; offline.

Conventions used everywhere below:
- `units` is the numpy array of daily units, one element per calendar day.
- `working` is a boolean array: True where the published calendar plans hours.
- An `origin` is the index of the last day known when the forecast is made;
  step h of a forecast is the day origin + h.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import TimeSeriesSplit

COLUMNS = ["date", "weekday", "planned_hours", "run_hours", "units", "defects", "event"]


# --------------------------------------------------------------------------- data
def load_days(path: str | Path) -> pd.DataFrame:
    """Read the daily file and refuse anything a positional lag would misread.

    Lags are taken by position (day t - 7 is seven rows up), so the file must hold
    exactly one row per calendar day with no gap, no duplicate and no reordering.
    """
    frame = pd.read_csv(path)
    if list(frame.columns) != COLUMNS:
        raise ValueError(f"expected columns {COLUMNS}, found {list(frame.columns)}")
    frame["date"] = pd.to_datetime(frame["date"], format="%Y-%m-%d")
    if frame["date"].duplicated().any():
        raise ValueError(f"duplicate day {frame.loc[frame['date'].duplicated(), 'date'].iloc[0].date()}")
    if not frame["date"].is_monotonic_increasing:
        raise ValueError("days are not in calendar order")
    calendar = pd.date_range(frame["date"].iloc[0], frame["date"].iloc[-1], freq="D")
    missing = calendar.difference(pd.DatetimeIndex(frame["date"]))
    if len(missing):
        raise ValueError(f"missing day {missing[0].date()}: positional lags would shift")
    if (frame[["planned_hours", "run_hours", "units", "defects"]] < 0).any().any():
        raise ValueError("negative hours or counts")
    return frame.reset_index(drop=True)


def arrays(frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    return frame["units"].to_numpy(dtype=float), (frame["planned_hours"] > 0).to_numpy()


# --------------------------------------------------------------------------- folds
def rolling_origin_folds(n_rows: int, n_splits: int = 4, horizon: int = 7, gap: int = 0,
                         max_train_size: int | None = None) -> list[tuple[np.ndarray, np.ndarray]]:
    """Expanding-window folds whose test blocks are the last n_splits * horizon days.

    scikit-learn's TimeSeriesSplit keeps every training index before every test
    index; test_size fixes the horizon, gap drops days between the two, and
    max_train_size turns the expanding window into a sliding one.
    """
    splitter = TimeSeriesSplit(n_splits=n_splits, test_size=horizon, gap=gap, max_train_size=max_train_size)
    return [(train, test) for train, test in splitter.split(np.arange(n_rows))]


# --------------------------------------------------------------------------- baselines
def naive_forecast(units: np.ndarray, origin: int, horizon: int) -> np.ndarray:
    """Every step repeats the last observed value."""
    return np.full(horizon, units[origin], dtype=float)


def seasonal_naive_forecast(units: np.ndarray, origin: int, horizon: int, season: int = 7) -> np.ndarray:
    """Step h repeats the last observed value from the same point in the season:
    units[origin + h - season * (k + 1)] with k = (h - 1) // season."""
    steps = np.arange(1, horizon + 1)
    return units[origin + steps - season * ((steps - 1) // season + 1)].astype(float)


# --------------------------------------------------------------------------- lag regression
@dataclass(frozen=True)
class LagModel:
    origin: int
    lags: tuple[int, ...]
    intercept: float
    coefficients: tuple[float, ...]
    training_rows: np.ndarray
    residuals: np.ndarray


def fit_lag_regression(units: np.ndarray, working: np.ndarray, origin: int,
                       lags: tuple[int, ...] = (7, 14)) -> LagModel:
    """Least squares on working days up to the origin: units[t] ~ units[t - lag] ..."""
    start = max(lags)
    rows = np.array([t for t in range(start, origin + 1) if working[t]])
    X = np.column_stack([units[rows - lag] for lag in lags])
    model = LinearRegression().fit(X, units[rows])
    residuals = units[rows] - model.predict(X)
    return LagModel(origin, tuple(lags), float(model.intercept_), tuple(float(c) for c in model.coef_),
                    rows, residuals)


def lag_regression_forecast(model: LagModel, units: np.ndarray, working: np.ndarray, horizon: int,
                            calendar: bool = True) -> np.ndarray:
    """Direct forecast for steps 1..horizon. Refuses a step whose lag is not yet observed.

    With calendar=True a day the published calendar closes is forecast as 0: a
    scheduled closure is a known fact, not something to predict.
    """
    shortest = min(model.lags)
    if horizon > shortest:
        raise ValueError(
            f"horizon {horizon} needs units from after the origin: lag {shortest} is only known "
            f"for steps 1..{shortest}")
    days = model.origin + np.arange(1, horizon + 1)
    X = np.column_stack([units[days - lag] for lag in model.lags])
    forecast = model.intercept + X @ np.asarray(model.coefficients)
    if calendar:
        forecast = np.where(working[days], forecast, 0.0)
    return forecast


# --------------------------------------------------------------------------- metrics
def mae(actual, forecast) -> float:
    return float(mean_absolute_error(actual, forecast))


def mape(actual, forecast) -> float:
    """Mean absolute percentage error in percent; undefined when any actual is zero."""
    actual, forecast = np.asarray(actual, dtype=float), np.asarray(forecast, dtype=float)
    if np.any(actual == 0):
        raise ValueError("MAPE is undefined when an actual is zero: score working days, "
                         "or use MAE or MASE")
    return float(np.mean(np.abs(actual - forecast) / np.abs(actual)) * 100)


def mase_scale(units: np.ndarray, working: np.ndarray, origin: int, season: int = 7) -> float:
    """In-sample MAE of the seasonal naive method on working days up to the origin."""
    rows = np.array([t for t in range(season, origin + 1) if working[t]])
    return float(np.mean(np.abs(units[rows] - units[rows - season])))


def backtest(frame: pd.DataFrame, n_splits: int = 4, horizon: int = 7, season: int = 7) -> list[dict]:
    """One record per rolling origin: forecasts for every method and working-day metrics."""
    units, working = arrays(frame)
    records = []
    for fold, (train, test) in enumerate(rolling_origin_folds(len(frame), n_splits, horizon), start=1):
        origin = int(train[-1])
        model = fit_lag_regression(units, working, origin)
        forecasts = {
            "naive": naive_forecast(units, origin, horizon),
            "seasonal_naive": seasonal_naive_forecast(units, origin, horizon, season),
            "lag_regression": lag_regression_forecast(model, units, working, horizon),
        }
        scored = working[test]
        actual = units[test][scored]
        scale = mase_scale(units, working, origin, season)
        records.append({
            "fold": fold, "origin": origin, "test": test, "model": model, "forecasts": forecasts,
            "mase_scale": scale,
            "mae": {name: mae(actual, f[scored]) for name, f in forecasts.items()},
            "mape": {name: mape(actual, f[scored]) for name, f in forecasts.items()},
            "mase": {name: mae(actual, f[scored]) / scale for name, f in forecasts.items()},
        })
    return records


def residual_band(model: LagModel, forecast: np.ndarray, quantiles=(0.1, 0.9)) -> tuple[np.ndarray, np.ndarray]:
    """An empirical range: the forecast shifted by quantiles of the model's training residuals.

    It describes how wrong the model has been on days it was fitted to; it is not a
    guarantee, and in-sample residuals tend to understate new errors.
    """
    low, high = np.quantile(model.residuals, quantiles)
    return forecast + low, forecast + high


# --------------------------------------------------------------------------- anomalies
def calibration_rate(frame: pd.DataFrame, calibration_days: int = 28) -> float:
    """Defects per unit over the calibration window only (the days before scoring starts)."""
    window = frame.iloc[:calibration_days]
    return float(window["defects"].sum() / window["units"].sum())


def anomaly_scores(frame: pd.DataFrame, rate: float, start: int = 28) -> pd.DataFrame:
    """Standardized excess defects per day: (defects - expected) / sqrt(expected).

    A day with no units has no expected defect count, so it is not scored (NaN):
    'not scored' is different from 'normal'.
    """
    scored = frame.iloc[start:].copy()
    expected = rate * scored["units"]
    scored["expected"] = expected
    with np.errstate(divide="ignore", invalid="ignore"):
        z = (scored["defects"] - expected) / np.sqrt(expected)
    scored["z"] = z.where(scored["units"] > 0)
    return scored


def threshold_table(scores: pd.DataFrame, thresholds, review_hours: float) -> pd.DataFrame:
    """For each threshold: reviews triggered, bad-lot days caught and missed, inspector hours."""
    rated = scores.dropna(subset=["z"])
    bad = rated["event"] == "bad_lot"
    rows = []
    for threshold in thresholds:
        flagged = rated["z"] >= threshold
        rows.append({
            "threshold": float(threshold),
            "flagged": int(flagged.sum()),
            "true_positive": int((flagged & bad).sum()),
            "false_positive": int((flagged & ~bad).sum()),
            "missed": int((~flagged & bad).sum()),
            "review_hours": float(flagged.sum() * review_hours),
            "flagged_dates": [d.date().isoformat() for d in rated.loc[flagged, "date"]],
        })
    return pd.DataFrame(rows)


def choose_threshold(table: pd.DataFrame, miss_hours: float) -> tuple[float, list[float]]:
    """Lowest total inspector-hours (reviews plus missed bad-lot days x miss_hours);
    a tie goes to the higher threshold, which triggers fewer reviews."""
    totals = table["review_hours"] + table["missed"] * miss_hours
    best = totals.min()
    choice = table.loc[totals == best, "threshold"].max()
    return float(choice), [float(t) for t in totals]


# --------------------------------------------------------------------------- ranking
def load_lots(path: str | Path) -> pd.DataFrame:
    lots = pd.read_csv(path)
    if lots["lot_id"].duplicated().any():
        raise ValueError("duplicate lot")
    return lots


def accuracy_at(scores, labels, threshold: float = 0.5) -> float:
    predicted = np.asarray(scores) >= threshold
    return float(np.mean(predicted == np.asarray(labels).astype(bool)))


def precision_recall_at_k(lots: pd.DataFrame, score_column: str, k: int) -> tuple[float, float, list[str]]:
    """Only the top k of the queue get inspected, so only they count."""
    ranked = lots.sort_values(score_column, ascending=False, kind="mergesort")
    top = ranked.head(k)
    hits = int(top["nonconforming"].sum())
    return hits / k, hits / int(lots["nonconforming"].sum()), top["lot_id"].tolist()
