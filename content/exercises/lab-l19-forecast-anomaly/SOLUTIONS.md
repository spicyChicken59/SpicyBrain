# Solutions — Lab L19

The complete reference is `solutions/forecast_lab.py`. This page explains each
gap, shows the intermediate outputs the tests check, and works through the
wrong approaches in `starters/shortcuts.py`. All numbers come from the
committed fixture and are reproduced by `expected/derive_expected.py`.

## Task 1 — rolling origins

```python
def rolling_origin_folds(n_rows, n_splits=4, horizon=7, gap=0, max_train_size=None):
    splitter = TimeSeriesSplit(n_splits=n_splits, test_size=horizon, gap=gap,
                               max_train_size=max_train_size)
    return [(train, test) for train, test in splitter.split(np.arange(n_rows))]
```

`TimeSeriesSplit` places the test blocks at the end of the series, one
`test_size` apart, and gives each fold every earlier index as training data.
For 82 days, 4 splits and a 7-day horizon the folds are:

| Fold | Training days | Rows | Origin (last known day) | Test days |
|---|---|---|---|---|
| 1 | 2026-06-01 to 2026-07-24 | 54 | Fri 2026-07-24 | Sat 07-25 to Fri 07-31 |
| 2 | 2026-06-01 to 2026-07-31 | 61 | Fri 2026-07-31 | Sat 08-01 to Fri 08-07 |
| 3 | 2026-06-01 to 2026-08-07 | 68 | Fri 2026-08-07 | Sat 08-08 to Fri 08-14 |
| 4 | 2026-06-01 to 2026-08-14 | 75 | Fri 2026-08-14 | Sat 08-15 to Fri 08-21 |

Each test week contains one closed Sunday, so 24 working days are scored in
total. `gap=1` ends fold 1's training on Thursday 2026-07-23 (53 rows): use it
when Friday's count is not final at planning time. `max_train_size=28` keeps
2026-06-27 to 2026-07-24 only: a sliding window instead of an expanding one.

## Task 2 — seasonal naive

```python
def seasonal_naive_forecast(units, origin, horizon, season=7):
    steps = np.arange(1, horizon + 1)
    return units[origin + steps - season * ((steps - 1) // season + 1)].astype(float)
```

For steps 1 to 7 this is simply "the same weekday last week". Fold 1's
forecasts next to the actuals and the naive forecast (409, Friday's value
repeated):

| Day | Actual | Naive | Seasonal naive | Lag regression |
|---|---|---|---|---|
| Sat 07-25 | 169 | 409 | 176 | 175.9 |
| Sun 07-26 | 0 (closed) | 409 | 0 | 0 |
| Mon 07-27 | 382 | 409 | 379 | 374.2 |
| Tue 07-28 | 425 | 409 | 388 | 399.4 |
| Wed 07-29 | 419 | 409 | 418 | 411.2 |
| Thu 07-30 | 393 | 409 | 411 | 416.8 |
| Fri 07-31 | 407 | 409 | 409 | 410.4 |

The naive forecast is 240 units wrong on Saturday because it carries a
two-shift Friday into a one-shift day. With horizon 14 from the last origin,
the seasonal naive forecast is 197, 0, 403, 422, 418, 404, 409 and then the
same seven values again: the last observed week is all it knows.

## Task 3 — the lag regression's forecast

```python
def lag_regression_forecast(model, units, working, horizon, calendar=True):
    shortest = min(model.lags)
    if horizon > shortest:
        raise ValueError(f"horizon {horizon} needs units from after the origin: "
                         f"lag {shortest} is only known for steps 1..{shortest}")
    days = model.origin + np.arange(1, horizon + 1)
    X = np.column_stack([units[days - lag] for lag in model.lags])
    forecast = model.intercept + X @ np.asarray(model.coefficients)
    if calendar:
        forecast = np.where(working[days], forecast, 0.0)
    return forecast
```

`fit_lag_regression` fits `LinearRegression` on working days from day 14 to
the origin. The coefficients are readable and stable across folds:

| Fold | Rows | Intercept | × last week | × two weeks ago |
|---|---|---|---|---|
| 1 | 35 | 7.32 | 0.477 | 0.498 |
| 2 | 41 | 5.93 | 0.464 | 0.515 |
| 3 | 47 | 1.73 | 0.475 | 0.516 |
| 4 | 53 | 8.69 | 0.453 | 0.522 |

In words: next Tuesday is about half of last Tuesday plus half of the Tuesday
before, plus a few units. It is a smoothed seasonal naive, which is why it can
only beat seasonal naive by averaging away some noise. Step 8 would need
`units[t − 7]` for a day after the origin, so a 14-day horizon is refused
rather than silently filled.

## Task 4 — MAPE that refuses a zero

```python
def mape(actual, forecast):
    actual, forecast = np.asarray(actual, float), np.asarray(forecast, float)
    if np.any(actual == 0):
        raise ValueError("MAPE is undefined when an actual is zero: score working days, "
                         "or use MAE or MASE")
    return float(np.mean(np.abs(actual - forecast) / np.abs(actual)) * 100)
```

The backtest's metrics on the 24 working days:

| Fold | MAE naive | MAE seasonal naive | MAE lag regression | MAPE naive | MAPE s. naive | MAPE lag reg. |
|---|---|---|---|---|---|---|
| 1 | 51.83 | 11.33 | 12.55 | 26.6% | 3.2% | 3.5% |
| 2 | 47.00 | 11.50 | 9.71 | 27.6% | 3.5% | 3.5% |
| 3 | 41.83 | 14.50 | 11.72 | 19.6% | 5.2% | 4.3% |
| 4 | 89.17 | 57.33 | 50.69 | 50.1% | 32.1% | 29.4% |
| Mean | 57.46 | 23.67 | 21.17 | | | |

MASE divides each fold's MAE by the seasonal naive method's in-sample MAE on
that fold's training days (a scale of about 14 units). Mean MASE: naive 4.03,
seasonal naive 1.67, lag regression 1.49. Values above 1 in fold 4 say that
week was harder than the history the scale came from.

The model choice is honest but narrow: the lag regression wins the mean
(21.17 against 23.67) and folds 2, 3 and 4, and loses fold 1. Fold 4's single
breakdown day (156 units against forecasts of 409 to 418) adds 42 to 44 units
to every method's fold-4 MAE: its error divided by the six scored days.

## Task 5 — an empirical band

```python
def residual_band(model, forecast, quantiles=(0.1, 0.9)):
    low, high = np.quantile(model.residuals, quantiles)
    return forecast + low, forecast + high
```

Fold 4's band, the week with the breakdown:

| Day | Actual | Forecast | Lower | Upper | Inside |
|---|---|---|---|---|---|
| Sat 08-15 | 182 | 180.5 | 160.7 | 200.5 | yes |
| Mon 08-17 | 387 | 394.5 | 374.7 | 414.5 | yes |
| Tue 08-18 | 402 | 413.1 | 393.2 | 433.0 | yes |
| Wed 08-19 | 156 | 412.3 | 392.5 | 432.2 | **no** |
| Thu 08-20 | 425 | 407.5 | 387.7 | 427.5 | yes |
| Fri 08-21 | 399 | 409.3 | 389.4 | 429.2 | yes |

Coverage per fold is 4, 6, 5 and 5 of 6 days: 20 of 24 (83%) against a
nominal 80%. The four misses are two ordinary days just outside in fold 1, a
busy Saturday in fold 3 and the breakdown. A band built from how wrong the
model was on ordinary days cannot contain an event that has not happened in
its history; say that when you publish it.

## Task 6 — anomaly scores

```python
def anomaly_scores(frame, rate, start=28):
    scored = frame.iloc[start:].copy()
    expected = rate * scored["units"]
    scored["expected"] = expected
    with np.errstate(divide="ignore", invalid="ignore"):
        z = (scored["defects"] - expected) / np.sqrt(expected)
    scored["z"] = z.where(scored["units"] > 0)
    return scored
```

The calibration rate is 0.02025203 defects per unit (the 28 days to
2026-06-28). The 12 highest scores:

| Day | Units | Defects | Expected | z | Event |
|---|---|---|---|---|---|
| Tue 08-11 | 422 | 29 | 8.55 | 6.996 | bad_lot |
| Thu 08-06 | 413 | 24 | 8.36 | 5.406 | bad_lot |
| Thu 07-16 | 429 | 19 | 8.69 | 3.498 | bad_lot |
| Wed 07-22 | 418 | 18 | 8.47 | 3.277 | none |
| Mon 07-27 | 382 | 16 | 7.74 | 2.971 | bad_lot |
| Mon 08-03 | 389 | 14 | 7.88 | 2.181 | none |
| Thu 08-13 | 404 | 14 | 8.18 | 2.034 | none |
| Tue 07-07 | 409 | 14 | 8.28 | 1.986 | bad_lot |
| Wed 07-01 | 428 | 14 | 8.67 | 1.811 | none |
| Sat 07-04 | 179 | 7 | 3.63 | 1.773 | none |
| Fri 07-24 | 409 | 13 | 8.28 | 1.639 | none |
| Sat 08-01 | 158 | 6 | 3.20 | 1.565 | none |

Thursday 07-16 scores 3.498, just under 3.5, so the highest threshold misses it. The breakdown day scores −0.090: its defect rate is ordinary. It is a
production anomaly that the forecast band catches, not a quality anomaly.

## Tasks 7 and 8 — the threshold table and the cost choice

| Threshold | Flagged | Caught | False positives | Missed | Review hours | Total, miss = 12 h | Total, miss = 40 h |
|---|---|---|---|---|---|---|---|
| 1.5 | 12 | 5 | 7 | 0 | 36 | 36 | **36** |
| 2.0 | 7 | 4 | 3 | 1 | 21 | 33 | 61 |
| 2.5 | 5 | 4 | 1 | 1 | 15 | **27** | 55 |
| 3.0 | 4 | 3 | 1 | 2 | 12 | 36 | 92 |
| 3.5 | 2 | 2 | 0 | 3 | 6 | 42 | 126 |

`choose_threshold` adds review hours to missed days times the miss cost and
takes the minimum (ties to the higher threshold). The base cost picks 2.5;
when a missed bad lot costs 40 hours, 1.5 is cheapest even though 7 of its 12
reviews find nothing. Neither choice is a guarantee: five injected bad lots
are all the evidence there is.

## Task 9 — precision and recall at k

```python
def precision_recall_at_k(lots, score_column, k):
    ranked = lots.sort_values(score_column, ascending=False, kind="mergesort")
    top = ranked.head(k)
    hits = int(top["nonconforming"].sum())
    return hits / k, hits / int(lots["nonconforming"].sum()), top["lot_id"].tolist()
```

| Measure | Model A | Model B | "All conforming" |
|---|---|---|---|
| Accuracy at 0.5 | 0.75 | 0.60 | 0.75 |
| Precision at 4 | 0.50 (L05, L12, L03, L07) | **1.00** (L11, L03, L14, L18) | — |
| Recall at 4 | 0.40 | 0.80 | 0 |
| Precision at 8 | **0.625** | 0.50 | — |
| Recall at 8 | 1.00 | 0.80 | — |

Accuracy prefers A and cannot tell A from a rule that inspects nothing. Four
inspectors should work from B's queue; eight should work from A's.

## Wrong approaches and why they fail

1. **Shuffled K-fold** (`shuffled_folds`). Every one of the four shuffled
   folds trains on days later than some of its test days, so a lag model
   would be scored on weeks it had already seen. The test counts those days.
2. **A same-day covariate** (`same_day_forecast`). Units regressed on the
   same day's `run_hours` score a mean MAE of 12.06 (folds 11.00, 12.22,
   10.79, 14.22), far better than the honest 21.17, and even "predict" the
   breakdown. But `run_hours` is recorded when the day ends; the test changes
   the last test day's run hours and watches that step's forecast move by
   more than 100 units. At a Friday origin none of those values exist.
3. **Lag 1 at horizon 7** (`lag1_forecast`). Step 2 reads the day after the
   origin; adding 100 units to that day moves step 2's forecast by exactly
   100. The backtest has quietly become one-day-ahead.
4. **Calibrating on the scored days** (`rate_from_all_days`). The rate rises
   from 0.02025 to 0.02280 because the bad lots are inside it; at threshold
   2.5 the leaky table misses 2 bad-lot days instead of 1.
5. **MAPE over closed days** (`mape_including_closed`). numpy divides 409 by 0
   and returns infinity. scikit-learn's `mean_absolute_percentage_error`
   divides by machine epsilon instead and returns about 2.6 × 10^17 for the
   naive forecast; the lag regression without the calendar forecasts 7.3
   units on a closed Sunday and scores about 4.7 × 10^15. Neither number is
   an error rate.
6. **Choosing the queue by accuracy** (`pick_by_accuracy`) returns model A,
   which puts two conforming lots in the first four places.
