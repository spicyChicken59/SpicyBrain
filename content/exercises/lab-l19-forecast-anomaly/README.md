# Lab L19 — Forecasts, anomaly thresholds and a ranked queue

**Execution class: R (local-executed).** The reference solution and its 41
tests run on one machine with Python 3.12, pandas 3.0.6, numpy 2.5.3 and
scikit-learn 1.9.1 (`requirements.txt`). Nothing runs on Databricks, nothing
calls AutoML or a model service, and nothing needs a network connection.

**What this lab is not.** It is not a forecasting benchmark, not an
evaluation of Databricks AutoML or any managed forecasting feature, and not a
safety, quality or financial guarantee. Fictional Cinderline Components, its
bracket line L4, the lots, the injected events and the inspector-hour costs are
synthetic. The numbers show mechanisms on one seeded dataset of 82 days; they
say nothing about how often real lines break down or ship bad lots.

## Purpose

Three different decisions hide behind the word "prediction", and each needs a
different evaluation:

1. **A forecast** of next week's units, made every Friday for the following
   seven days. It is judged on rolling origins against the naive and the
   seasonal-naive baselines, at the horizon the planner actually uses, with
   errors measured in units and a range around the point value.
2. **An anomaly flag** on daily defect counts. It is judged by what its
   threshold does to the inspectors: reviews triggered, bad-lot days caught,
   false positives, missed days, and hours under two cost assumptions.
3. **A ranked inspection queue** of 20 incoming lots. It is judged at its
   top k, because inspectors only open the first four (or eight), not by
   accuracy over all 20.

The lab makes each judgement executable and shows six tempting shortcuts
failing for a reason you can read in the test output.

## Outcome

After the lab you can:

- produce rolling-origin folds with `TimeSeriesSplit` and explain why every
  training day must precede every test day;
- compute naive and seasonal-naive forecasts and say why the naive forecast
  made on a Friday is wrong about Saturday;
- fit a two-lag regression whose coefficients you can read, refuse a horizon
  its lags cannot reach, and show it ignores every value after the origin;
- compare MAE, MAPE and MASE, and show MAPE failing on a closed day's zero;
- build an empirical 80% band from residuals, measure its coverage and name
  the day it cannot cover;
- turn an anomaly threshold into inspection load and pick a threshold by cost,
  then watch a higher miss cost move the choice;
- show that the queue accuracy prefers is not the queue four inspectors
  should work from, and that eight inspectors change the answer again.

## Prerequisites

- Python you can read: functions, lists, dictionaries, `numpy` arrays and a
  `pandas` DataFrame.
- The ideas of a training/test split and of precision and recall from the
  machine-learning foundations module.
- No Databricks workspace, no GPU, no account of any kind.

## Files

| Path | What it holds |
|---|---|
| `fixtures/line_days.csv` | 82 days of line L4: calendar, run hours, units, defects, injected event |
| `fixtures/generate_line_days.py` | the seeded standard-library generator that writes the CSV byte for byte |
| `fixtures/lots.csv` | 20 incoming lots, two models' scores, the inspection outcome |
| `fixtures/decisions.json` | horizon, folds, quantiles, thresholds, costs and capacities |
| `expected/*.json` | literal expected values |
| `expected/derive_expected.py` | the independent standard-library derivation of those literals |
| `starters/forecast_lab.py` | the lab with nine gaps marked `TASK 1` to `TASK 9` |
| `starters/shortcuts.py` | six wrong approaches the tests expect to fail |
| `solutions/forecast_lab.py` | the complete reference solution |
| `run_tests.py` | the unittest runner and evidence writer |
| `TASKS.md`, `SOLUTIONS.md`, `DATA.md` | the tasks, the explained solution, the data dictionary |

## Setup

Create a virtual environment anywhere outside the lab folder and install the
pins:

```bash
python3.12 -m venv ~/venvs/lab-l19
~/venvs/lab-l19/bin/pip install -r requirements.txt
```

Every command below runs from this lab directory with that environment's
`python`.

## Run

```bash
python run_tests.py                            # reference solution, 41 tests
python run_tests.py --evidence evidence.json   # the same, and write an evidence record
python run_tests.py --starter                  # your completed starters/forecast_lab.py (40 tests)
python expected/derive_expected.py --check     # the literals are the derivation's (standard library only)
python fixtures/generate_line_days.py --out regenerated.csv   # rebuild the fixture elsewhere
```

A clean reference run ends with `OK` and an exit status of 0; the summary
prints `"skipped": 0`. On the untouched starter, `--starter` fails with
`NotImplementedError` messages that name each gap. The evidence record holds
the interpreter and package versions, start and finish times, test counts and
SHA-256 hashes of every fixture, expected file, program and produced output.

## Cleanup

The runner writes no files unless you pass `--evidence`; the one temporary
directory it creates (for the missing-day and duplicate-day checks) is deleted
when that test finishes. Delete `evidence.json` and `regenerated.csv` if you
wrote them, and remove the virtual environment with `rm -rf ~/venvs/lab-l19`.

## Limits

- One synthetic line, 82 days, four rolling origins and 24 scored working
  days: every rate here has a very wide real uncertainty. Four folds show
  mechanism, not a stable ranking of methods.
- The 80% band comes from in-sample residuals of the lag regression. It is an
  empirical range, not a probability guarantee, and it ignores parameter
  uncertainty and any change the next weeks bring.
- The anomaly score treats defects as roughly Poisson given units. The
  generator adds day-to-day variation on purpose, so the score flags more
  normal days than a Poisson table would suggest; a real line needs its own
  calibration.
- Five injected bad-lot days are the only ground truth. Real labels arrive
  late, are incomplete and depend on who investigated.
- The ranking fixture is authored by hand to make one contrast visible. It is
  not evidence that either kind of model is better in general.
