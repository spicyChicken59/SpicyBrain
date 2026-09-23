# Tasks — Lab L19

Work in `starters/forecast_lab.py`. Each gap raises `NotImplementedError`
with its `TASK n` tag until you fill it. The functions without a tag are
complete: `load_days` (refuses a missing or duplicated day), `arrays`,
`naive_forecast`, `fit_lag_regression`, `mae`, `mase_scale`, `backtest`,
`calibration_rate`, `load_lots` and `accuracy_at`. Run
`python run_tests.py --starter` after each gap; the tests name the behaviour
they expect. Do not edit `fixtures/` or `expected/`.

Vocabulary used below: an **origin** is the index of the last day known when
a forecast is made (a Friday in this lab); **step h** is the day origin + h;
the **horizon** is the number of steps forecast (7). `units` is a numpy array
with one value per calendar day and `working` is True where the published
calendar plans hours (Sundays are closed).

## Task 1 — rolling origins (`rolling_origin_folds`)

Return a list of `(train, test)` index arrays for `n_rows` days using
`sklearn.model_selection.TimeSeriesSplit` with `n_splits`, `test_size=horizon`,
`gap` and `max_train_size` passed through.

Expected behaviour: for the 82-day fixture with 4 splits and horizon 7, the
test blocks are the last 28 days in four consecutive weeks (Saturday to
Friday), the first training window runs from 2026-06-01 to 2026-07-24 (54
days) and each later window grows by one week. No training index is ever
greater than a test index. With `gap=1` each training window loses its last
day; with `max_train_size=28` each keeps only the 28 days before its test
block.

## Task 2 — seasonal naive (`seasonal_naive_forecast`)

Step h repeats the last observed value from the same point in the season:
`units[origin + h - season * (k + 1)]` where `k = (h - 1) // season`.

Expected behaviour: from the Friday 2026-07-24 origin, the forecast for
Saturday 2026-07-25 is the previous Saturday's 176 units and the forecast for
the closed Sunday is 0. With horizon 14, steps 8 to 14 repeat steps 1 to 7.

## Task 3 — the lag regression's forecast (`lag_regression_forecast`)

The model (already fitted for you by `fit_lag_regression`) is
`units[t] ≈ intercept + a × units[t − 7] + b × units[t − 14]`.

Expected behaviour:

- raise `ValueError` whose message contains `horizon <n>` and `lag <shortest>`
  when the horizon is longer than the shortest lag, because step 8 would need
  a value from after the origin;
- otherwise return the forecast for steps 1..horizon;
- when `calendar=True`, return exactly 0 for any day the calendar closes.

## Task 4 — MAPE that refuses a zero (`mape`)

Return the mean absolute percentage error in percent. If any actual is 0,
raise `ValueError` with the word `zero` in the message instead of returning a
number.

Expected behaviour: on the six working days of fold 1, the seasonal-naive
MAPE is 3.16%; on all seven days (which include a closed Sunday) the function
raises.

## Task 5 — an empirical band (`residual_band`)

Take the quantiles of the model's training residuals (`np.quantile` with its
default linear interpolation) and shift the forecast by them. Return
`(lower, upper)`.

Expected behaviour: with quantiles (0.1, 0.9), fold 1's band runs from 19.91
units below to 21.00 units above the forecast, and 20 of the 24 scored working
days fall inside their band.

## Task 6 — anomaly scores (`anomaly_scores`)

Copy the frame from row `start` on and add two columns:
`expected = rate × units` and `z = (defects − expected) / sqrt(expected)`.
Leave `z` as `NaN` where `units` is 0.

Expected behaviour: with the calibration rate from the first 28 days, 47 days
are scored and 7 closed Sundays are not. The highest score is 6.996, on Tuesday
2026-08-11.

## Task 7 — the threshold table (`threshold_table`)

For each threshold, count over the scored days only: `flagged` (z at or above
the threshold), `true_positive` (flagged bad-lot days), `false_positive`,
`missed` (bad-lot days not flagged) and `review_hours` (flagged × review hours
per flag), plus the list `flagged_dates` as ISO strings.

Expected behaviour: at 2.5 the table flags 5 days, catches 4 of the 5 bad-lot
days, raises 1 false positive and costs 15 review hours.

## Task 8 — choose by cost (`choose_threshold`)

Total hours = review hours + missed days × `miss_hours`. Return the threshold
with the lowest total (a tie goes to the higher threshold, which triggers
fewer reviews) and the list of totals in table order.

Expected behaviour: with a miss costing 12 hours the choice is 2.5 (27
hours); with a miss costing 40 hours it is 1.5 (36 hours).

## Task 9 — precision and recall at k (`precision_recall_at_k`)

Sort the lots by the named score column from highest to lowest (a stable
sort), keep the top k and return `(precision at k, recall at k, top lot ids)`.
Recall divides by all nonconforming lots in the file.

Expected behaviour: at k = 4, model B's queue is L11, L03, L14, L18 with
precision 1.0 and recall 0.8, while model A's reaches precision 0.5.

## Investigations (after the tests pass)

1. Change `fixtures/decisions.json` locally so a miss costs 20 hours and
   predict the chosen threshold before running `choose_threshold`. Restore
   the file afterwards (`git checkout` or your copy), because the expected
   literals are tied to the committed values.
2. Remove the breakdown week from the scored days (score only folds 1 to 3)
   and compare the three methods again. What does one bad day do to a
   four-fold average?
3. Explain in two sentences why the same-day shortcut in `starters/shortcuts.py`
   has the best MAE in the lab and would still be the worst model to deploy.
4. Change a copy of `fit_lag_regression` so it only uses days inside a
   sliding 28-day window (what `max_train_size=28` gives the folds). Fold 1
   then keeps 24 working-day rows instead of 35. Explain why a sliding window
   matters more when a line's level drifts, and what it costs when it does not.
