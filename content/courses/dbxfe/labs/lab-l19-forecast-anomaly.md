*Local-executed (R): pandas 3.0.6, numpy 2.5.3 and scikit-learn 1.9.1 on
Python 3.12, one machine, CPU only, no network. Nothing runs on Databricks and
no AutoML or model service is called. The line, its lots and every event are
synthetic. Everything below can be studied without installing anything.*

### What this lab is for

Three decisions at fictional Cinderline Components get called "prediction",
and each needs its own evaluation. The planner forecasts next week's units on
bracket line L4 every Friday. Quality flags days whose defect count looks
abnormal, and every flag costs an inspector three hours. The incoming-goods
team can inspect only four of twenty lots per shift and wants them ranked. The
lab builds all three, evaluates each the way its decision needs, and makes six
tempting shortcuts fail in front of you.

### The data, briefly

82 days, Monday 2026-06-01 to Friday 2026-08-21, one row per calendar day,
written by a seeded standard-library generator that the tests re-run byte for
byte. The published calendar plans two shifts on weekdays, one on Saturday and
none on Sunday. Five days carry injected bad lots (extra defects) and one
Wednesday carries a breakdown.

| date | weekday | planned_hours | run_hours | units | defects | event |
|---|---|---|---|---|---|---|
| 2026-08-14 | Fri | 16 | 15.25 | 409 | 10 | none |
| 2026-08-15 | Sat | 8 | 7.50 | 182 | 5 | none |
| 2026-08-16 | Sun | 0 | 0.00 | 0 | 0 | none |
| 2026-08-19 | Wed | 16 | 5.50 | 156 | 3 | breakdown |

Two columns matter for honesty. `planned_hours` is known weeks ahead;
`run_hours` is written when the day ends, so no forecast made on Friday may
use next week's value. `event` is ground truth only because the data are
synthetic; it is used to evaluate, never as an input.

### Task by task, with the intermediate output

**Rolling origins.** `TimeSeriesSplit(n_splits=4, test_size=7)` produces four
folds. Fold 1 trains on 2026-06-01 to Friday 2026-07-24 (54 days) and tests
Saturday 07-25 to Friday 07-31; each later fold adds a week. Every training
index precedes every test index. `gap=1` ends fold 1's training on Thursday
(for a Friday count that is not final at planning time) and
`max_train_size=28` keeps a sliding four-week window.

**Baselines.** The naive forecast repeats Friday's 409 units for all seven
days, so it is 240 units wrong on Saturday. The seasonal naive forecast copies
the same weekday last week: 176 for Saturday, 0 for the closed Sunday, 379 for
Monday. With a 14-day horizon it repeats the last observed week twice.

**An interpretable model.** A linear regression on the values 7 and 14 days
back, fitted on working days up to the origin, gives in fold 1
`7.32 + 0.477 × last week + 0.498 × two weeks ago`: a smoothed seasonal naive
whose coefficients anyone can read. It refuses a 14-day horizon, because step
8 would need a value from after the origin, and a test proves its forecasts do
not change when every value after the origin is tripled.

**Metrics.** Mean absolute error on the 24 scored working days:

| Fold | Naive | Seasonal naive | Lag regression |
|---|---|---|---|
| 1 | 51.83 | **11.33** | 12.55 |
| 2 | 47.00 | 11.50 | **9.71** |
| 3 | 41.83 | 14.50 | **11.72** |
| 4 | 89.17 | 57.33 | **50.69** |
| Mean | 57.46 | 23.67 | **21.17** |

The model wins the mean and three folds, and loses fold 1: an honest, narrow
improvement over a strong baseline. The breakdown day alone adds 42 to 44
units to every method's fold-4 error. Mean MASE (error scaled by the seasonal
naive method's in-sample error) is 4.03, 1.67 and 1.49.

**An uncertainty band.** Shifting each forecast by the 10th and 90th
percentiles of the model's training residuals (about −20 and +21 units) gives
an 80% band. It contains 20 of the 24 scored days (4, 6, 5 and 5 per fold).
On Wednesday 2026-08-19 the band is 392.5 to 432.2 and the line made 156
units: a range built from ordinary days cannot contain an event its history
never showed.

**Anomaly scores.** The defect rate is calibrated on the first 28 days only
(0.02025 per unit). Each later working day gets
`z = (defects − rate × units) / √(rate × units)`; the 7 closed Sundays are not
scored rather than called normal. The top score is Tuesday 2026-08-11: 29
defects against 8.55 expected, z = 6.996. The breakdown day scores −0.09: its
defect rate is ordinary, so it is a production anomaly, not a quality one.

**Thresholds and inspection load.**

| Threshold | Flagged | Bad lots caught | False positives | Missed | Hours (miss = 12 h) | Hours (miss = 40 h) |
|---|---|---|---|---|---|---|
| 1.5 | 12 | 5 | 7 | 0 | 36 | **36** |
| 2.0 | 7 | 4 | 3 | 1 | 33 | 61 |
| 2.5 | 5 | 4 | 1 | 1 | **27** | 55 |
| 3.0 | 4 | 3 | 1 | 2 | 36 | 92 |
| 3.5 | 2 | 2 | 0 | 3 | 42 | 126 |

Hours are three per review plus the miss cost per missed bad-lot day. With a
12-hour miss the cheapest threshold is 2.5; when a miss costs 40 hours it is
1.5, although 7 of its 12 reviews find nothing.

**A ranked queue.** Model A scores accuracy 0.75 at a 0.5 cut, model B 0.60,
and calling every lot conforming also scores 0.75. With four inspections,
B's top four are all nonconforming (precision 1.00) and A's are half
(0.50). With eight inspections the preference flips: A reaches 0.625 and
recall 1.0, B 0.50. The metric has to match the capacity.

### The failure cases

- Shuffled K-fold trains every fold on days later than its test days.
- Regressing units on the same day's `run_hours` scores a mean MAE of 12.06,
  far better than anything possible at the origin; the test moves one day's
  run hours and watches that day's "forecast" move by more than 100 units.
- A lag-1 feature at horizon 7 reads the day after the origin for step 2.
- Calibrating the defect rate on all 82 days raises it to 0.0228 and misses a
  second bad lot at threshold 2.5.
- MAPE over a closed Sunday: numpy returns infinity; scikit-learn divides by
  machine epsilon and returns about 2.6 × 10^17 for the naive forecast. The
  reference `mape` raises instead.
- Choosing the queue by accuracy picks model A for four inspectors.

### What the tests prove and do not prove

The 41 tests prove that the reference code reproduces literals derived
independently with the standard library (exact fractions for the regression,
index arithmetic for the folds), that no honest forecast uses a value after
its origin, and that each shortcut fails for its stated reason. They do not
prove that the lag regression would beat seasonal naive on another line, that
80% of future days will fall inside the band, or that 2.5 is a safe threshold
anywhere. Four folds, 24 scored days and five injected bad lots are far too
few for such claims, and nothing here is a safety or financial guarantee.

### Setup, run and cleanup

Install Python 3.12 and the three pinned packages from `requirements.txt` in a
virtual environment outside the lab folder, then from the lab directory run
`python run_tests.py` (reference, 41 tests), `python run_tests.py --starter`
(your completed starter) or `python run_tests.py --evidence evidence.json`.
The runner writes nothing else; its one temporary directory is deleted when
the test that uses it finishes. Remove `evidence.json` and the virtual
environment when you are done.
