*Local-executed (R): Python 3.12.3 with open-source MLflow 3.16.1, scikit-learn 1.9.1, pandas 3.0.6,
numpy 2.5.3, scipy 1.18.1 and skops 0.15.0, on one machine. MLflow tracks into a file store inside a
temporary directory that the tests create and delete; the model registry is that same file store.
No tracking server, no Databricks, no Unity Catalog, no network. Everything below can be studied
without installing anything.*

### What this lab is for

The machine-learning foundations module asks for a target, a baseline and an honest split; the MLflow
module asks for a record behind every number. This lab joins them on one small problem from the
fictional Cinderline Components: at 09:00 each day, for each of the South plant's eight coating
ovens, predict a fault stop in the next 24 hours. A flagged oven joins that day's inspection round,
which holds two ovens. The model is deliberately ordinary, a scaled logistic regression on six
columns. The lab is about what surrounds it: the runs that make a comparison fair, the run that looks
best and cannot be rerun, the contract a model must keep, and a promotion decision that reads the
evidence before the metrics.

### The fixture

A seeded generator writes 960 rows: eight ovens × 120 days, 67 faults. Days 1–84 train (672 rows,
49 faults); days 85–120 are the held-out future (288 rows, 18 faults). Four rows:

| oven | day | days since service | temp max °C | door cycles | fault next 24h | repair minutes | fault code |
|---|---|---|---|---|---|---|---|
| O-01 | 1 | 11 | 212.9 | 62 | 0 | 0 | |
| O-02 | 1 | 9 | 214.5 | 84 | 1 | 208 | F-DOOR |
| O-01 | 2 | 12 | 220.0 | 62 | 1 | 196 | F-DOOR |
| O-01 | 85 | 15 | 211.5 | 50 | 0 | 0 | |

The data dictionary dates every column. Age, days since service, the previous 24 hours' mean and
maximum temperature, door cycles and humidity exist at 09:00. `repair_minutes` and `fault_code` are
written by the technician **after** the fault. Notice that in the table they are non-zero exactly on
the fault rows: a model allowed to read them does not predict anything.

### Task 1 — baselines first

| predictor on the 288 test rows | caught | warnings | accuracy | recall | warnings a day |
|---|---|---|---|---|---|
| never warn | 0 of 18 | 0 | 0.9375 | 0 | 0 |
| temperature rule, max ≥ 220.0 °C | 12 of 18 | 43 | 0.8715 | 0.6667 | 1.19 |

Never warning scores 0.9375 accuracy because faults are 6% of the rows. That single line is why the
contract is written in recall, precision and warnings a day, not accuracy.

### Task 2 — the two leaks

The dictionary check flags `repair_minutes` and `fault_code` as recorded after the prediction and
the label as the label. The split check finds that a random 70/30 split tests on day 1 while training
reaches day 120; the day-84 cut is time-ordered.

### Task 3 — one complete run

The clean run logs its parameters (C = 1.0, class weight, iterations, seed 20260923, split, the day-84
cut, the six feature names, scikit-learn 1.9.1), the training and evaluation rows as datasets
(training digest `4950f73b`), the two check reports, the metrics and confusion matrix, and a model
directory: `MLmodel` with the `python_function` and `sklearn` flavors, `model.skops`, a signature
(six doubles in, `fault_next_24h` as a long out), an input example, and `requirements.txt`,
`python_env.yaml` and `conda.yaml` pinning the versions above. It catches 15 of 18 faults with 68
warnings: recall 0.8333, precision 0.2206, 1.89 warnings a day.

### Task 4 — the table, sorted by accuracy

| run | accuracy | recall | what is wrong with it |
|---|---|---|---|
| hero | 1.0 | 1.0 | repair record as input; random split; nothing recorded |
| time-split-leaky | 1.0 | 1.0 | repair record as input, honestly recorded |
| never-warn | 0.9375 | 0.0 | a rare class |
| temperature-rule | 0.8715 | 0.6667 | the rule in use |
| random-split-seeded | 0.8438 | 0.7368 | tests on days before training ends |
| time-split-C-1 | 0.8056 | 0.8333 | nothing found |
| time-split-C-0.01 | 0.7396 | 0.9444 | too many warnings |

Two runs compare cleanly when they trained on the same rows and differ in one parameter: C = 1 and
C = 0.01 differ only in `C`; C = 1 and the leaky run differ only in `features`, which isolates the leak
(accuracy 0.8056 → 1.0). The random split and the hero are not comparable with anything.

### Task 5 — the run nobody can rerun

The reproduction function refuses the hero: *not recorded: C, class_weight, features, max_iter,
scikit_learn, seed, split, training_dataset*. Running the hero's code again leaves an identical record
and a different confusion matrix (20 of 20 faults in one test set, 18 of 18 in the other). The clean
run's rerun gets the same digest and bit-identical metrics. The same rerun on another plant's rows gets
a new digest and recall 0.6, so it is a new experiment, not a reproduction. A record claiming
scikit-learn 1.8.0 is refused on a 1.9.1 installation.

### Task 6 — the contract rejects drift

Contract 1.0.0 names six double inputs, a long output and three thresholds (recall ≥ 0.75, precision
≥ 0.2, at most 2.0 warnings a day). Renaming `humidity_pct`, sending `door_cycles` as an integer,
adding `repair_minutes` and renaming the output are each rejected with a named reason; reordering the
columns is not drift. MLflow's own enforcement raises for the missing and the integer column, but an
extra column is only logged as "These inputs will be ignored", which is why the contract checks it.

### Task 7 — the decision

Evidence first: the random split, the leaky run and the hero are rejected before any metric is read.
Then thresholds: C = 0.01 fails precision (0.1868) and the cap (2.53 a day); C = 1 passes and is
registered as version 1 with the alias `candidate`, tagged with the contract version and its run. The
decision file lists every run, gate and reason, and six limitations of the evidence. Registering the reproduced rerun makes version 2;
moving the alias there and back is a rollback that changes no version.

### The failure case

The deliberately wrong starter promotes the best accuracy. It picks a run at 1.0, and the evidence
gate rejects that run. The test asserts both halves: the naive rule chooses it, and the gate refuses it
for a named reason.

### Task 8 — transfer

The same code and contract on a second synthetic plant: recall 0.6 on 15 test faults, rejected on
recall. A passing decision belongs to one dataset and one period.

### What the tests prove and do not prove

The 32 tests prove, for this fixture and these pinned versions: the fixture regenerates byte for byte;
the expected metrics come from an independent script that never imports the solution or MLflow; every
run's counts match; a clean rerun is exact; the hero cannot be rerun; the contract names each drift;
decisions and registry states match hand-authored literals; nothing is left behind. They do not prove
the model is useful for real ovens, that results hold on another machine or library version, that a
logged dataset was correct (a run records data, it does not certify it), that a record tells the
truth (the evidence gate reads what a run declares, such as its split parameter and feature list, so
a record that misstates them would pass), or anything about Databricks-managed MLflow or Unity
Catalog, which were not used.

### Setup and cleanup

Create a virtual environment, `pip install -r requirements.txt`, then
`python run_tests.py --evidence <path>`. The runner deletes its temporary directory and checks that no
`mlruns/`, `mlflow.db` or `__pycache__` remains. After an interrupted run, delete any leftover
`l17-tests-*` directory under your temporary directory, the evidence file and the virtual environment.
