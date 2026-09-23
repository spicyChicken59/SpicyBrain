# Lab L17 — A baseline, a tracked experiment and an evidence-based promotion

**Execution class: local-executed (R).** The reference solution and its 32 tests were executed on one
machine with open-source MLflow 3.16.1, a file-store tracking URI and a file-store model registry
inside a temporary directory. Nothing runs on Databricks, nothing uses Unity Catalog, no tracking
server is started and no network call is made.

## Purpose

Modules E1 (evaluation) and E3 (MLflow and reproducibility) meet here. A small, CPU-only
classification problem on synthetic oven data from the fictional Cinderline Components is used to
practise the habits that make a model's numbers defensible: judge a model against a trivial
predictor and the rule in use; find the leaking feature and the leaking split before trusting a
score; log runs so that two of them can be compared and one can be rerun from its record alone;
expose a run that looks best but cannot be reproduced; write a versioned model contract that
rejects schema drift; and make a promotion decision from evidence, recorded in a file.

## Outcome

After the lab you can show, from a tracked experiment, why the run with the best accuracy is the one
you reject, why a clean rerun reproduces every metric exactly, and why the promoted model version is
the one whose record passed the contract, with the reasons written down.

## Environment

| component | version tested |
|---|---|
| Python | 3.12.3 |
| mlflow | 3.16.1 |
| scikit-learn | 1.9.1 |
| pandas | 3.0.6 |
| numpy | 2.5.3 |
| scipy | 1.18.1 |
| skops | 0.15.0 |

`skops` is pinned because MLflow 3.16.1's scikit-learn flavor saves models in the skops format by
default; `scipy` is a scikit-learn dependency. `requirements.txt` pins exactly these versions, and the
tests check that the environment MLflow captures with the model pins the same ones.

## Prerequisites

Python and pandas reading; the E1 ideas of target, prediction moment, baseline and leakage (module
`dbxfe-m07`, lesson "Start ML with a baseline and a valid target"). No MLflow experience is assumed.

## Setup

```bash
python3.12 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python run_tests.py --evidence /tmp/l17-evidence.json   # about a minute where it was tested
python starters/tracked_experiment.py                    # the learner starter; prints the dataset facts
```

The runner creates one temporary directory (prefix `l17-tests-`) holding the MLflow file store in a
`tracking` folder plus the contract and the decision file, runs the whole experiment, runs the tests
against it, deletes the directory and then asserts that it is gone and that no `mlruns/`,
`mlflow.db` or `__pycache__` was left in the lab or the working directory.

Three environment variables are set in `solutions/tracking.py` (and in the starter) before MLflow is
imported: `MLFLOW_ALLOW_FILE_STORE=true`, because MLflow 3.16.1 refuses the file-store backend
without it (the backend is in maintenance mode; the documented direction is a database backend such
as SQLite); `MLFLOW_DISABLE_TELEMETRY=true` and `DO_NOT_TRACK=true`, because this MLflow version
collects usage telemetry by default and the lab runs offline. The file store is kept deliberately: it
needs no server and no database, and you can open a run as plain files (`meta.yaml`, `params/`,
`metrics/`, `inputs/`, `artifacts/`).

## Layout

| path | what it is |
|---|---|
| `fixtures/generate_oven_days.py` | the seeded generator; `fixtures/oven_days.csv` is its committed output |
| `fixtures/data_dictionary.json` | each column's role and the moment it becomes available |
| `expected/derive_expected.py` | independent derivation of `expected/metrics.json` (never imports `solutions/` or MLflow) |
| `expected/contract.json`, `expected/decisions.json` | hand-authored literals (derivations in DATA.md) |
| `starters/tracked_experiment.py` | self-contained starter with the tasks as gaps |
| `starters/naive_promotion.py` | the deliberately wrong rule: promote the best accuracy |
| `solutions/` | the reference: `data.py`, `tracking.py`, `experiment.py`, `contract.py` |
| `run_tests.py` | unittest runner; `--evidence` writes versions, counts and SHA-256 hashes |

## Cleanup

Nothing to clean after a normal run: the runner deletes its temporary directory. If a run is
interrupted, remove any directory named `/tmp/l17-tests-*` or `/tmp/l17-learner-*` (the prefix
depends on your platform's temporary directory), then the evidence file you asked for and `.venv`.

## Limits

- Open-source MLflow with a local file store, not Databricks-managed MLflow. The registry here is the
  file-store registry; on Databricks, models are registered in Unity Catalog under a
  `catalog.schema.model` name with Unity Catalog privileges, which this lab does not exercise.
- A toy model on 960 synthetic rows with 18 test faults. The numbers illustrate mechanisms; they are
  not a benchmark and say nothing about real ovens. Timings in the evidence file are not benchmarks.
- A logged run records what was used; it does not certify that the data was right. The leaky run in
  this lab has a complete, honest record of an invalid experiment.
- Exact reproduction is shown on one machine with pinned versions. Another CPU, linear-algebra (BLAS)
  build or library version may change results; the lab refuses to call a rerun a reproduction when the recorded
  scikit-learn version differs from the installed one.
