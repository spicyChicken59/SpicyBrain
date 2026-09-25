"""Six tempting shortcuts, each wrong for a reason the tests assert.

Nothing here is a solution. run_tests.py imports these functions and checks
that each one fails in the documented way, so you can see the failure rather
than take it on trust:

1. shuffled_folds          KFold with shuffle=True trains on days after the test days.
2. same_day_forecast       uses run_hours, which is recorded only when the target day ends.
3. lag1_forecast           uses yesterday's units, which do not exist yet for steps 2..7.
4. rate_from_all_days      calibrates the defect rate on the very days it then scores.
5. mape_including_closed   divides by a closed Sunday's zero units.
6. pick_by_accuracy        chooses an inspection queue by accuracy at 0.5, not by its top k.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold


def shuffled_folds(n_rows: int, n_splits: int = 4, seed: int = 19) -> list[tuple[np.ndarray, np.ndarray]]:
    """Wrong: random folds ignore time, so most folds train on later days than they test."""
    return list(KFold(n_splits=n_splits, shuffle=True, random_state=seed).split(np.arange(n_rows)))


def same_day_forecast(frame: pd.DataFrame, origin: int, horizon: int) -> np.ndarray:
    """Wrong: regresses units on the SAME day's run_hours, then 'forecasts' each test day
    from that day's own run_hours, a value nobody has at the origin."""
    working = (frame["planned_hours"] > 0).to_numpy()
    train = np.array([t for t in range(0, origin + 1) if working[t]])
    hours = frame["run_hours"].to_numpy(dtype=float)
    units = frame["units"].to_numpy(dtype=float)
    model = LinearRegression().fit(hours[train].reshape(-1, 1), units[train])
    days = origin + np.arange(1, horizon + 1)
    return model.predict(hours[days].reshape(-1, 1))


def lag1_forecast(units: np.ndarray, origin: int, horizon: int) -> np.ndarray:
    """Wrong: step h reads units[origin + h - 1] from the finished series; for h >= 2 that
    day is after the origin, so the backtest quietly becomes a one-day-ahead test."""
    days = origin + np.arange(1, horizon + 1)
    return units[days - 1].astype(float)


def rate_from_all_days(frame: pd.DataFrame) -> float:
    """Wrong: the bad-lot days being scored raise the baseline they are compared with."""
    return float(frame["defects"].sum() / frame["units"].sum())


def mape_including_closed(actual, forecast) -> float:
    """Wrong: a closed day has actual 0, so its percentage error is a division by zero."""
    actual, forecast = np.asarray(actual, dtype=float), np.asarray(forecast, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return float(np.mean(np.abs(actual - forecast) / np.abs(actual)) * 100)


def pick_by_accuracy(lots: pd.DataFrame, threshold: float = 0.5) -> str:
    """Wrong for a queue: accuracy counts every lot, but inspectors only open the top k."""
    labels = lots["nonconforming"].astype(bool).to_numpy()
    accuracy = {name: float(np.mean((lots[column].to_numpy() >= threshold) == labels))
                for name, column in (("model_a", "score_a"), ("model_b", "score_b"))}
    return max(accuracy, key=accuracy.get)
