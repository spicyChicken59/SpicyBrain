# TASKS — lab L17

Work in `starters/tracked_experiment.py`. Each task says what your code must do and what you should
see; none gives the code. Write your predictions into `PREDICTIONS` before running anything, then
check each one against your own experiment. `SOLUTIONS.md` explains the reference after your attempt.

The situation: at 09:00 every day, for each of the South plant's eight coating ovens, predict whether
the oven will have a fault stop in the next 24 hours. A flagged oven joins that day's inspection
round, which holds two ovens. Training data is days 1–84; the held-out future is days 85–120.

## Task 0 — predict first

Fill `PREDICTIONS`. In particular: the test period has 18 faults in 288 rows, so what accuracy does a
predictor that never warns achieve? Which run will sort first by accuracy? Does MLflow's schema
enforcement reject an input column the model was not trained on?

## Task 1 — two baselines as runs

Log a run named `never-warn` and a run named `temperature-rule` (warn when `temp_max_c >= 220.0`)
over the test days. Each logs its parameters, the evaluation dataset and the metrics tp, fp, fn, tn,
accuracy, recall, precision (omit it when nothing was warned) and warnings per day.
**Expected:** never-warn has accuracy 0.9375 and recall 0; the rule catches 12 of 18 faults with 43
warnings, 1.19 a day.

## Task 2 — the leaking feature and the leaking split

Implement `leakage_report(features, dictionary)`: flag every proposed column whose
`available_at` is not 09:00, with a reason (`recorded_after_prediction`, or `is_the_label`).
Implement `split_report(train, test)`: counts, positives, the latest training day, the earliest test
day and whether the split is time-ordered, with a sentence when it is not.
**Expected:** `repair_minutes` and `fault_code` are flagged, the label is flagged, the six features pass.
A random 70/30 split tests on day 1 while training reaches day 120; the day-84 split is time-ordered.

## Task 3 — one run whose record could rerun it

Implement `train_time_split(...)`. Inside one run: log the parameters a rerun needs (model, C,
class_weight, max_iter, seed, split, train_through_day, the feature list and the scikit-learn
version); log the training and evaluation rows as MLflow datasets with contexts `training` and
`evaluation`; fit a pipeline that scales inside the pipeline; log the metrics, a JSON copy of them,
the confusion matrix and the two reports from Task 2 as artifacts; log the model with a signature
(inputs as float64, output named `fault_next_24h`) and an input example.
**Expected:** for C = 1: tp 15, fp 53, fn 3, tn 217, recall 0.8333, precision 0.2206, 1.8889 warnings
a day. The model directory holds `MLmodel`, `model.skops`, `requirements.txt`, `python_env.yaml`,
`conda.yaml` and the input examples, and `requirements.txt` pins the versions in this lab's
`requirements.txt`.

## Task 4 — compare runs, fairly

Log C = 0.01 with everything else unchanged, the same model over a random split, the same model with
`repair_minutes` added (keep the time split), and the hero: `repair_minutes` added, a random split
whose seed is used but not logged, no dataset, no feature list, no signature. Then sort the experiment
by accuracy with `mlflow.search_runs`.
**Expected:** the two runs that used `repair_minutes` tie at 1.0 and never-warn comes third at 0.9375,
above every honest model. Write a function that calls two runs comparable only when they trained on
the same rows (same training digest) and differ in exactly one parameter: C = 1 against C = 0.01 is
comparable, and so is C = 1 against the leaky run (they differ only in `features`); C = 1 against the
random split or the hero is not.

## Task 5 — reproduce, or refuse

Implement `reproduce(run_id, frame, ...)`: read the run's parameters and training dataset digest,
refuse (raise, naming every gap) when something a rerun needs is not recorded or the recorded
scikit-learn version is not the installed one, otherwise retrain from the record and compare the new
digest and every metric with the original.
**Expected:** the hero is refused with eight gaps; running the hero's code a second time with the
same record gives a different confusion matrix; the clean C = 1 run reruns with the same digest and
bit-identical metrics; the same rerun on another plant's data changes the digest and every rate, so it
is not a reproduction.

## Task 6 — a versioned model contract

Write `expected/contract.json`'s content from code (version 1.0.0: six double inputs, a long output,
three thresholds, the evidence required). Implement `check_signature(contract, signature)`: missing,
unexpected and retyped inputs by name, and the output clause. Then load the C = 1 model as a pyfunc and
send it a renamed column, an int64 column, an extra column and a reordered frame.
**Expected:** the contract rejects the renamed, retyped and extra columns and accepts the reordered
frame. MLflow raises for the renamed and the int64 column but only warns about the extra column, and
ignores it.

## Task 7 — decide, record, promote

Implement `decide(contract, run_id)`: the evidence gate first (time split, seed, training dataset,
feature list, no post-event feature, a signature matching the contract), thresholds only for runs
that pass it. Write every decision, with sorted reasons, and the limitations of the evidence to a
decision file. Register only the run decided `promote-candidate`, tag the version with the contract
version and the run it came from, and point the alias `candidate` at it. Register the reproduced rerun
as a second version, move the alias, then move it back.
**Expected:** only C = 1 is promoted; C = 0.01 fails precision and the warning cap; the random split,
the leaky run and the hero fail evidence before a metric is read. `starters/naive_promotion.py` picks
a run with accuracy 1.0, which the evidence gate rejects. Versions 1 and 2 predict identically; the
alias is the only thing that moves.

## Task 8 — the same contract on another plant

Run the C = 1 configuration on the transfer plant (`generate_oven_days.rows(TRANSFER_SEED)`).
**Expected:** recall 0.6 on 15 test faults: the same code, contract and thresholds reject it on recall.
