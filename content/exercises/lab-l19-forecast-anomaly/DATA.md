# Data — Lab L19

Everything in `fixtures/` is synthetic and written for this lab. Cinderline
Components, bracket line L4, the lots and every event are fictional; no value
was measured on a real line.

## fixtures/line_days.csv — 82 days, one row per calendar day

| Column | Type | Meaning | Known at a Friday origin? |
|---|---|---|---|
| `date` | ISO date | 2026-06-01 (Monday) to 2026-08-21 (Friday), no gaps | yes |
| `weekday` | Mon..Sun | derived from `date` | yes |
| `planned_hours` | integer | published calendar: 16 Mon–Fri, 8 Sat, 0 Sun (closed) | yes, weeks ahead |
| `run_hours` | decimal | hours the line actually ran, recorded when the day ends | no |
| `units` | integer | units produced that day (the forecast target) | only up to the origin |
| `defects` | integer | defective units found at end-of-line inspection | only up to the origin |
| `event` | text | synthetic ground truth: `none`, `bad_lot`, `breakdown` | never; evaluation only |

Eleven Sundays have 0 planned hours, 0 run hours, 0 units and 0 defects. The
injected events are five bad-lot days with extra defects — Tue 2026-07-07 (+5),
Thu 2026-07-16 (+8), Mon 2026-07-27 (+11), Thu 2026-08-06 (+15) and Tue
2026-08-11 (+22) — and one breakdown, Wed 2026-08-19, with run hours forced to
5.5 (156 units instead of about 410).

A small excerpt (the first week of fold 4 and its origin):

| date | weekday | planned_hours | run_hours | units | defects | event |
|---|---|---|---|---|---|---|
| 2026-08-14 | Fri | 16 | 15.25 | 409 | 10 | none |
| 2026-08-15 | Sat | 8 | 7.50 | 182 | 5 | none |
| 2026-08-16 | Sun | 0 | 0.00 | 0 | 0 | none |
| 2026-08-17 | Mon | 16 | 15.50 | 387 | 5 | none |
| 2026-08-18 | Tue | 16 | 15.50 | 402 | 8 | none |
| 2026-08-19 | Wed | 16 | 5.50 | 156 | 3 | breakdown |
| 2026-08-20 | Thu | 16 | 16.00 | 425 | 5 | none |
| 2026-08-21 | Fri | 16 | 15.25 | 399 | 7 | none |

### How the file is generated

`fixtures/generate_line_days.py` uses only the Python standard library and
draws every random number from `random.Random(47).random()`. Its normal draws
use the Box-Muller cosine branch and its Poisson draws use Knuth's product
method, both written out in the file, so no library version can change the
output. For each open day it draws, in this order: a stoppage (up to 1 hour,
0.5 on Saturday) that is subtracted from the planned hours and rounded to a
quarter hour; normal noise with standard deviation 8 added to units per run
hour times run hours (25.0 Monday, 26.5 Tuesday to Friday, 23.0 Saturday);
a day-level multiplier drawn uniformly from 0.55 to 1.45; and a Poisson count
of defects with mean 0.02 × units × multiplier. Sundays consume no draws. The
multiplier makes defect counts vary more than a Poisson count would, as real
daily defect counts usually do; that is why a Poisson-style score raises
false positives here.

**Seed selection, disclosed.** Seed 47 and the injected sizes were chosen from
a handful of candidates because they produce a backtest in which the lag
regression wins the mean but not every fold, and a threshold table in which
the two cost assumptions choose different thresholds. The lab teaches those
mechanisms; it says nothing about how often such outcomes occur.

`run_tests.py` rebuilds the CSV in memory from the generator and compares it
byte for byte with the committed file.

## fixtures/lots.csv — 20 incoming lots

| Column | Meaning |
|---|---|
| `lot_id` | L01 to L20 |
| `score_a` | model A's score (hand-authored), cautious: few scores above 0.5 |
| `score_b` | model B's score (hand-authored), overconfident but well ordered at the top |
| `nonconforming` | 1 when inspection found the lot out of specification (L03, L07, L11, L14, L18) |

No two scores tie within a model, so every top-k list is unambiguous.

## fixtures/decisions.json — the decision parameters

Horizon 7 days, 4 folds, season 7, lags 7 and 14, band quantiles 0.1 and 0.9;
anomaly calibration on the first 28 days, thresholds 1.5, 2.0, 2.5, 3.0 and
3.5, 3 inspector-hours per review, a missed bad-lot day costing 12 hours
(base) or 40 hours (altered); an accuracy threshold of 0.5 and inspection
capacities of 4 (base) and 8 (altered). The hours are teaching values, not
measured costs.

## How the expected literals were produced

`expected/derive_expected.py` recomputes every expected value with the
standard library only (it imports no solution code and none of pandas, numpy
or scikit-learn); `python expected/derive_expected.py --check` confirms the
committed files are its output, and one test runs the same check. The
derivations:

- **Folds** are index arithmetic: test block k starts at
  `82 − (4 − k) × 7`; training is every earlier index, minus `gap` days at
  its end, or only the last 28 of them for a sliding window.
- **Naive** repeats the origin's units; **seasonal naive** reads
  `units[origin + h − 7 × ((h − 1) // 7 + 1)]`.
- **The lag regression** is solved exactly: the normal equations
  (XᵀX)b = Xᵀy for an intercept and the 7- and 14-day lags on working days
  from day 14 to the origin, with `fractions.Fraction` and Gauss-Jordan
  elimination, so no floating-point solver is shared with scikit-learn.
- **Band quantiles** use linear interpolation between order statistics at
  position (n − 1) × q, the rule numpy's default quantile method follows.
- **MAE, MAPE and MASE** are exact fractions over the six working days of
  each fold; the MASE scale is the mean of |units[t] − units[t − 7]| over the
  fold's working training days from day 7.
- **scikit-learn's MAPE on a closed day** is predicted from its documented
  guard, dividing each absolute error by max(|actual|, machine epsilon =
  2⁻⁵²), and stored to 12 significant digits; the test compares with a
  relative tolerance of 10⁻⁹.
- **The anomaly rate** is total defects over total units for the first 28
  days as an exact fraction; each score is
  (defects − rate × units) / √(rate × units); the derivation asserts no score
  lies within 10⁻⁶ of a threshold and no actual within 10⁻³ of a band edge,
  so the literals cannot flip on rounding.
- **Costs** are review hours plus missed days × miss hours; ties would go to
  the higher threshold.
- **Ranking**: accuracy compares `score >= 0.5` with the label for all 20
  lots; precision and recall at k count nonconforming lots in the k highest
  scores.

Values are rounded to 6 decimal places in the JSON (8 for the rates, 4 for
the listed scores); the tests allow 2 × 10⁻⁶ (10⁻⁸ for the rates, 6 × 10⁻⁵ for
the four-place scores).

## A hand check you can do with a calculator

Fold 1's origin is Friday 2026-07-24 (409 units). The seasonal naive forecast
for Tuesday 2026-07-28 is the previous Tuesday's 388 units, and the actual is
425: an absolute error of 37 and a percentage error of 37 / 425 = 8.7%. The
lag regression forecasts 7.320 + 0.4766 × 388 + 0.4980 × 416 = 399.4
(416 is Tuesday 2026-07-14), 25.6 units short. For the anomaly score on
Tuesday 2026-08-11: expected defects = 0.02025203 × 422 = 8.546, and
(29 − 8.546) / √8.546 = 6.996.
