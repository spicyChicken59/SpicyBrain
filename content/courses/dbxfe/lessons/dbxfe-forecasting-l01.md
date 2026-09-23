<!-- section:dbxfe-forecasting-l01-outcome -->

After this lesson you can evaluate three predictions at fictional Cinderline Components the way each decision needs. For the Friday forecast of next week's units on bracket line L4, you fix the origin and horizon, beat naive and seasonal naive baselines on rolling origins and publish a range with its coverage. For the daily defect flag, you read a threshold as inspection load and choose it by cost. For the lot queue, you measure precision at the inspectors' capacity. All numbers are lab L19's synthetic results, not guarantees.

<!-- section:dbxfe-forecasting-l01-start -->

Bring the habits from [Start ML with a baseline and a valid target](#/lesson/dbxfe-m07-l01): a target, a prediction time, a baseline, held-out data and a metric chosen for its consequence. Time series change two of them: held-out days must come after the training days, because neighbouring days resemble each other, and the prediction time becomes an origin with a horizon. You also need precision and recall. The Python is short and every result also appears as a table.

<!-- section:dbxfe-forecasting-l01-horizon -->

A forecast is made at an **origin**, the last day whose data may be used, for a **horizon** of steps. Cinderline sets rosters at 23:00 on Friday, once the night shift's count is posted, for Saturday to Friday: origin Friday, steps 1 to 7. Each input must exist at the origin for every step it feeds: units seven or fourteen days back and the published calendar qualify, yesterday's units only for step 1, the target day's run hours never.

Two baselines need no fitting. The **naive** forecast repeats Friday's 409 units for every day, 240 units wrong on the one-shift Saturday. The **seasonal naive** forecast repeats the same weekday last week, following L4's weekly seasonality:

| Day | Actual | Naive | Seasonal naive |
|---|---|---|---|
| Sat 07-25 | 169 | 409 | 176 |
| Mon 07-27 | 382 | 409 | 379 |
| Tue 07-28 | 425 | 409 | 388 |

Seasonal naive copies anomalies too: from the 2026-08-21 origin it forecasts next Wednesday as 156 units, last Wednesday's breakdown.

<!-- section:dbxfe-forecasting-l01-backtest -->

One split scores one week. A **rolling-origin backtest** repeats the real situation: fit on everything up to an origin, forecast the horizon, score, move the origin a week, refit.

```python
from sklearn.model_selection import TimeSeriesSplit
for train, test in TimeSeriesSplit(n_splits=4, test_size=7).split(range(82)):
    print(train[-1], test[0], test[-1])   # 53 54 60 | 60 61 67 | 67 68 74 | 74 75 81
```

Every origin is a Friday and every training day precedes every test day. `gap=1` drops the origin day when Friday's count is not final at the meeting; `max_train_size=28` keeps only the latest four weeks.

**Temporal leakage** is any path from after the origin into training or prediction. A regression on the target day's run hours scores 12.06 units of error against the honest 21.17 because run hours are written when the day ends. Shuffled K-fold, a lag-1 input at step 2 and a rate fitted on the whole series leak too. The check: change every value after the origin; an honest forecast must not move.

<!-- section:dbxfe-forecasting-l01-metrics -->

The lag regression (in fold 1, 7.32 + 0.477 × last week + 0.498 × the week before) is a smoothed seasonal naive. On the same folds and working days:

| Fold | Naive | Seasonal naive | Lag regression |
|---|---|---|---|
| 1 | 51.83 | 11.33 | 12.55 |
| 2 | 47.00 | 11.50 | 9.71 |
| 3 | 41.83 | 14.50 | 11.72 |
| 4 | 89.17 | 57.33 | 50.69 |
| Mean | 57.46 | 23.67 | 21.17 |

It wins the mean and three folds and loses fold 1: a narrow gain, reported with its exception. The fold 4 breakdown adds 42 to 44 units to every method's error.

MAE is in units. **MAPE** divides by the actual, so a closed Sunday is a division by zero: numpy returns infinity, and scikit-learn divides by machine epsilon and returns about 2.6 × 10^17 for a week of naive forecasts. **MASE** divides MAE by the seasonal naive method's in-sample MAE (1.49 for the lag regression, 1.67 for seasonal naive) and stays defined.

<!-- section:dbxfe-forecasting-l01-uncertainty -->

A **prediction interval** states a range. The lab's 80% band adds the 10th and 90th percentiles of the model's training residuals, about −20 to +20 units, to each forecast. Checked like a forecast, it contained 20 of 24 held-out working days (4, 6, 5 and 5 per fold), 83% against a nominal 80%, but not Wednesday 2026-08-19's breakdown: 156 units against 392.5 to 432.2. Publish it with those limits: in-sample residuals understate new errors, one width for every step ignores that uncertainty usually grows with the horizon, and ordinary weeks cannot cover an event they never showed.

<!-- section:dbxfe-forecasting-l01-anomaly -->

An anomaly detector is a **score** and a **threshold**. Quality calibrates a defect rate on the first 28 days only (0.02025 per unit) and scores each later working day as (defects − expected) / √expected, with expected = rate × units: Tuesday 2026-08-11 scores about 7.0. A closed Sunday is not scored, which differs from normal, and the breakdown scores −0.09 because its defect rate was ordinary. Each flag costs an inspector three hours:

| Threshold | Flagged | Caught (of 5) | False positives | Missed | Hours, miss 12 h | Hours, miss 40 h |
|---|---|---|---|---|---|---|
| 1.5 | 12 | 5 | 7 | 0 | 36 | 36 |
| 2.0 | 7 | 4 | 3 | 1 | 33 | 61 |
| 2.5 | 5 | 4 | 1 | 1 | 27 | 55 |
| 3.0 | 4 | 3 | 1 | 2 | 36 | 92 |
| 3.5 | 2 | 2 | 0 | 3 | 42 | 126 |

At 12 hours per miss 2.5 is cheapest; at 40 hours 1.5 is, despite seven false positive reviews; the break-even is 21 hours. Calibrating on all 82 days would raise the rate to 0.0228 and miss one more bad lot at 2.5.

<!-- section:dbxfe-forecasting-l01-ranking -->

Not all ML is classification. Ranking and recommendation tasks return an ordered list per request, and people act on its top. Incoming goods inspects four of twenty lots per shift:

| Measure | Model A | Model B |
|---|---|---|
| Accuracy at 0.5 | 0.75 | 0.60 |
| Precision at 4 | 0.50 | 1.00 |
| Recall at 4 | 0.40 | 0.80 |
| Precision at 8 | 0.625 | 0.500 |

Accuracy prefers A, yet a rule that calls every lot conforming scores the same 0.75. With four inspections B's queue is right; with eight, A's. For a recommender such as suggested spare parts per work order, compute precision at k for each request and average it.

<!-- section:dbxfe-forecasting-l01-platform -->

Databricks documents AutoML, which prepares data, trains and tunes candidate models and writes a notebook per trial, including for forecasting; check the current page for supported runtimes, because nothing here ran it. A tool can search models. It cannot know the Friday origin, which columns exist then, that Sundays are closed, which baselines count or what a missed bad lot costs. Read each trial's notebook, rerun it on the baselines' rolling origins and keep those decisions with the team.

<!-- section:dbxfe-forecasting-l01-example -->

At the Friday 2026-08-14 origin the lag regression forecasts Wednesday 2026-08-19 at 412.3 units, 80% band 392.5 to 432.2; seasonal naive says 418 and naive 409. The line breaks down and makes 156. Every method misses by 253 to 262 units, and the day falls 236 units below the band. Its defect score is −0.09, because 3 defects on 156 units is an ordinary rate: a production anomaly, visible to the forecast and invisible to the quality score. A week later seasonal naive copies 156 into the next Wednesday unless the event is recorded.

<!-- section:dbxfe-forecasting-l01-exercise -->

The planner asks for a 14-day forecast from the Friday 2026-08-14 origin, and quality replaces its 3-hour review with a 6-hour teardown per flag; a missed bad lot still costs 40 hours.

1. Which of the three methods can produce steps 8 to 14 without reading data after the origin, and what does seasonal naive forecast for them?
2. Using the threshold table's flags and misses, which threshold is now cheapest?
3. What would you tell the planner about the far end of the 14-day forecast?

<!-- section:dbxfe-forecasting-l01-solution -->

1. Naive can (409 for all 14 days) but is poor. Seasonal naive repeats the last observed week, 197, 0, 403, 422, 418, 404 and 409, for steps 8 to 14. The lag regression cannot: step 8's lag-7 input is after the origin, so the lab refuses the horizon; it would need lags of 14 and 21 days, or a recursive forecast evaluated as recursive.
2. At 6 hours per flag and 40 per miss the totals for 1.5 to 3.5 are 72, 82, 70, 104 and 132: 2.5 is cheapest, 2 hours below 1.5.
3. Steps 8 to 14 rest on older information: expect larger errors and a wider honest interval, and backtest them separately.

<!-- section:dbxfe-forecasting-l01-mistakes -->

- Shuffled splits, inputs written after the target day, or lags shorter than the horizon.
- Calling a model better without beating seasonal naive on the same folds, or quoting only the mean.
- MAPE over closed days or near-zero actuals.
- An interval published as a guarantee, or tuned on the days used to check it.
- Unscored days treated as normal, or an anomaly baseline calibrated on the scored days.
- A threshold chosen for accuracy rather than workload and cost, or kept after the costs change.
- A capacity-limited queue ordered by accuracy.

<!-- section:dbxfe-forecasting-l01-sources -->

- scikit-learn, *Cross-validation: evaluating estimator performance* and *TimeSeriesSplit*: time-ordered folds, test_size, gap and max_train_size, executed in lab L19.
- Hyndman and Athanasopoulos, *Forecasting: Principles and Practice* (3rd ed): baselines, rolling origins, percentage and scaled errors, prediction intervals.
- scikit-learn, *Metrics and scoring* and *Tuning the decision threshold for class prediction*: precision, the MAPE epsilon, scores separate from thresholds.
- Databricks, *What is AutoML?*: managed model search with trial notebooks.

Each source record states how its title and URL were confirmed; pages could not be fetched in this build.

<!-- section:dbxfe-forecasting-l01-related -->

- Lab L19, *Forecasts, anomaly thresholds and a ranked queue*, runs every number in this lesson with 41 tests on seeded synthetic data.
- [Start ML with a baseline and a valid target](#/lesson/dbxfe-m07-l01) covers baselines and prediction time for problems without a time order.
- The features module applies the same leakage question to point-in-time feature joins, the MLflow module records each backtest run, and the serving module monitors a deployed forecast.

<!-- section:dbxfe-forecasting-l01-revisit -->

Return in a week and answer without notes: the roster forecast's origin and horizon; why naive fails on Saturday; which rows the first fold tests; which input leaked and how to prove it; why MAPE breaks on Sunday; what 20 of 24 says about the band; why 2.0 adds only false positives; which queue four inspectors should use.
