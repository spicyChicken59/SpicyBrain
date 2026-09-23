# Lab L18 — Point-in-time features

**Execution class: R (local-executed), pandas.** Everything runs under
CPython 3.12.3 in a virtual environment holding `requirements.txt`: pandas 3.0.6 and
numpy 2.5.3 (python-dateutil 2.9.0.post0 as pandas' own dependency). No Spark,
no Java, no MLflow, no network, no Databricks. The tests and the reference
solution were executed on one Linux machine; see
`docs/academy/labs/lab-l18-point-in-time-features.json` for the recorded run.

## Purpose and outcome

A feature is only honest if the model could have had it at the moment it was
asked. This lab gives you fifteen timestamped sensor readings from three
fictional Cinderline press-line machines, a feature job that publishes
two-hour window aggregates thirty minutes after each window closes, eleven
labelled prediction times for a failure-warning model, and two readings that
arrive late. You build the feature table, join it to the labels **as of each
prediction time**, and prove with tests that nothing from the future got in.

After the lab you can:

1. give every feature row two times — `feature_time` (the window it
   describes) and `available_at` (the run that published it) — and explain
   why the join must use the second;
2. build a point-in-time training set with `pandas.merge_asof` or an explicit
   filter-and-pick, and say exactly when the two disagree (an older window
   republished after a newer one);
3. separate three missingness causes — no row yet (`none_available`), a row
   too old for this consumer (`stale`), a row with an empty column
   (`vib_max_2h` null with `vib_count_2h` 0) — and apply one written policy
   in training and serving alike;
4. refuse duplicate entity-time rows, an unknown entity key, a label that
   describes the past, and a transformation port that drifted from the
   training code — each with a test that asserts the reason;
5. rerun with late-arriving readings and show that one training row changes,
   the one predicted after the new version was published, while every earlier
   row keeps the value that existed at its prediction time.

## Prerequisites

The retained machine-learning lesson `dbxfe-m07-l01` (target, prediction time
and leakage) and the features module's lesson (`dbxfe-features-l01`). Reading
a small pandas program; `groupby`, `merge` and `sort_values` are explained
where they are used in `SOLUTIONS.md`.

## Setup and run

```sh
cd lab-l18-point-in-time-features
python -m venv .venv && . .venv/bin/activate      # optional; any Python 3.12
pip install -r requirements.txt                   # pandas 3.0.6, numpy 2.5.3
python run_tests.py --evidence local-evidence.json
python solutions/features.py                      # primary replay as JSON
python solutions/features.py --late               # with the two late readings
```

A passed run is 25 tests, 0 failures, 0 errors, **0 skipped**, exit 0.
`--evidence` writes the interpreter, package versions, start and end times,
counts and the SHA-256 of every fixture, expected, solution and starter file
and of every produced output. Work through `TASKS.md` first:
`starters/features.py` has six marked gaps (`GAP 1` to `GAP 6`),
`starters/shortcuts.py` holds four tempting wrong approaches and
`starters/serving_port.py` a drifted re-implementation. Open `SOLUTIONS.md`
and `solutions/` after your attempt.

## Layout

```
README.md  TASKS.md  SOLUTIONS.md  DATA.md  requirements.txt  run_tests.py
fixtures/  observations.csv          15 readings, PR-01..PR-03, 06:30-11:50 UTC
           late_observations.csv     2 readings ingested late (11:05, 11:40)
           labels.csv                11 failure-warning prediction times with outcomes
           labels_handover.csv       6 prediction times of a second model (reuse)
           feature_contract.json     producer contract: entities, window, schedule, bounds
           consumers.json            consumer policies: max feature age, training cutoff
expected/  feature_table.json  training_set.json  leaks.json  serving.json
           drift.json  late.json  reuse.json           (hand-authored; derivations in DATA.md)
starters/  features.py (six gaps)  shortcuts.py (wrong on purpose)  serving_port.py (drifted)
solutions/ features.py
```

## Failure states and cleanup

A failing test prints both values. The two most common mistakes while
filling the starter: joining on `feature_time` (the guard then names the
10:15 and 10:20 predictions) and counting rows instead of values for
`vib_count_2h` (the contract then refuses PR-03's window). The runner sets
`sys.dont_write_bytecode`, so no `__pycache__` appears; if you ran the
programs another way, delete any `__pycache__` folders. The only file the lab
writes is the evidence JSON at the path you chose; delete it, and the
optional `.venv`, when done.

## Limits and honesty

The schedule, windows, contract and consumer policies are an **original
fictional teaching policy**, not a Databricks feature table, Feature View,
online store or lookup behaviour; the module explains which documented
platform capabilities correspond to each idea and what must be verified. A
local pass shows the stated rules behave as described on these inputs. It
says nothing about scale, streaming, clock skew between systems, or whether
any of these features predicts failure: no model is trained and no metric is
reported. Machines, readings and outcomes are fiction.
