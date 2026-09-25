# SOLUTIONS — lab L17

The reference lives in `solutions/`. Every number below was printed by the executed reference run
(open-source MLflow 3.16.1, file store in a temporary directory, Python 3.12.3); digests are MLflow's
8-character dataset digests and are stable for this fixture and these versions.

## Task 1 — baselines

`experiment.log_baselines()` logs two runs over the 288 test rows and attaches the evaluation dataset.

| run | tp | fp | fn | tn | accuracy | recall | precision | warnings/day |
|---|---|---|---|---|---|---|---|---|
| never-warn | 0 | 0 | 18 | 270 | 0.9375 | 0.0 | (not logged) | 0.0 |
| temperature-rule | 12 | 31 | 6 | 239 | 0.8715 | 0.6667 | 0.2791 | 1.1944 |

Precision is not logged for never-warn: it is undefined, and a zero would be a claim.

## Task 2 — the dictionary and the split

`data.leakage_report()` compares each proposed column's `available_at` with the prediction moment:

```text
repair_minutes  -> recorded_after_prediction  (available after the fault, same day)
fault_code      -> recorded_after_prediction
fault_next_24h  -> is_the_label
```

`data.split_report()` for the day-84 split: 672 training rows (49 faults), 288 test rows (18 faults),
latest training day 84, earliest test day 85, kind `time`. For `split_random(frame, 0.7, 20260923)`:
kind `not_time_ordered`, reason "test rows start on day 1, before training ends on day 120".

## Task 3 — a complete run

`experiment.train_time_split()` logs, inside one `mlflow.start_run`:

```text
params    model=logistic_regression C=1.0 class_weight=balanced max_iter=1000 seed=20260923
          split=time train_through_day=84 scikit_learn=1.9.1
          features=oven_age_years,days_since_service,temp_mean_c,temp_max_c,door_cycles,humidity_pct
inputs    oven-days-train (context training, digest 4950f73b), oven-days-test (context evaluation)
artifacts checks/leakage_report.json  checks/split_report.json
          evaluation/metrics.json     evaluation/confusion_matrix.json
model     models:/m-<id>  MLmodel, model.skops, requirements.txt, python_env.yaml, conda.yaml,
          input_example.json, serving_input_example.json
metrics   tp 15, fp 53, fn 3, tn 217, accuracy 0.8056, recall 0.8333, precision 0.2206,
          warnings_per_day 1.8889 (logged against the run and linked to the logged model)
```

The logged dataset holds every column of the training rows; the `features` parameter says which six
the model used. That makes the digest a statement about rows: the C = 0.01 run and the leaky run
train on the same rows and share digest 4950f73b; the random split's training rows have digest
3f06bea0. `MLmodel` lists two flavors, `python_function` (loader `mlflow.sklearn`) and `sklearn`
(`serialization_format: skops`, `sklearn_version: 1.9.1`), and the signature:

```text
inputs : oven_age_years, days_since_service, temp_mean_c, temp_max_c, door_cycles, humidity_pct  (double, required)
outputs: fault_next_24h (long, required)
```

`requirements.txt` in the model directory reads `mlflow==3.16.1`, `numpy==2.5.3`, `pandas==3.0.6`,
`scikit-learn==1.9.1`, `scipy==1.18.1`, `skops==0.15.0`: MLflow inferred it from the modules the model
imports. Parameters are immutable: logging `C=0.5` into the finished run raises
`Changing param values is not allowed`.

## Task 4 — the table a hurried reader sorts

`experiment.compare_runs()` asks MLflow for the runs ordered by accuracy and breaks ties by name:

| run | accuracy | recall | warnings/day | training digest |
|---|---|---|---|---|
| hero | 1.0 | 1.0 | 0.5556 | none logged |
| time-split-leaky | 1.0 | 1.0 | 0.5 | 4950f73b |
| never-warn | 0.9375 | 0.0 | 0.0 | none (baseline) |
| temperature-rule | 0.8715 | 0.6667 | 1.1944 | none (baseline) |
| random-split-seeded | 0.8438 | 0.7368 | 1.5 | 3f06bea0 |
| time-split-C-1 | 0.8056 | 0.8333 | 1.8889 | 4950f73b |
| time-split-C-0.01 | 0.7396 | 0.9444 | 2.5278 | 4950f73b |

Every row above the clean model is wrong in a different way: two used a column written after the
fault; never-warn is accurate because faults are rare. `experiment.comparable()`:

| pair | differing parameters | same rows | comparable |
|---|---|---|---|
| C-1 / C-0.01 | C | yes | yes |
| C-1 / leaky | features | yes | yes: the leak alone moves accuracy 0.8056 → 1.0 |
| C-1 / random split | split, train_fraction, train_through_day | no | no |
| C-1 / hero | eight parameters | hero logged no dataset | no |

## Task 5 — reproduction

`experiment.reproduce()` refuses the hero:

```text
cannot reproduce this run: not recorded: C, class_weight, features, max_iter, scikit_learn, seed, split, training_dataset
```

The hero's code run a second time (`hero-again`, a different hidden seed) leaves an identical record,
`{"model": "logistic_regression"}`, and a different result: 20 of 20 faults in one test set, 18 of 18
in the other. The record cannot say which test rows produced its number, so the number is not a
property of the record.

The clean rerun of C = 1 trains from the logged parameters, gets training digest 4950f73b again and
logs metrics equal to the original's bit for bit (the test compares floats with `==`). The same rerun
on the transfer plant's rows gets digest 2729bc65 and recall 0.6: `reproduced` is false because the
data changed. A record copied from the clean run but carrying `scikit_learn=1.8.0` is refused with
`environment differs: scikit-learn 1.8.0 recorded, 1.9.1 installed`.

## Task 6 — contract and drift

`contract.check_signature()` over signatures inferred from altered frames:

| drift | contract reasons |
|---|---|
| `humidity_pct` renamed `humidity` | `missing_input:humidity_pct`, `unexpected_input:humidity` |
| `door_cycles` sent as int64 | `type_mismatch:door_cycles:double->long` |
| `repair_minutes` added | `unexpected_input:repair_minutes` |
| output named `prediction` | `output_mismatch:prediction:long` |
| same six columns reversed | none |

MLflow's pyfunc enforcement on the logged model: the renamed column raises
`Model is missing inputs ['humidity_pct']`; the int64 column raises
`Can not safely convert int64 to float64`; the extra `repair_minutes` column is logged as
`These inputs will be ignored` and predictions are unchanged; reordering changes nothing. Enforcement
protects the model from missing and unsafe inputs; the contract adds the rule that nobody may send a
post-event column, which MLflow would silently drop.

## Task 7 — decisions and promotion

`contract.decide()`:

| run | gate | decision | reasons |
|---|---|---|---|
| time-split-C-1 | thresholds | promote-candidate | none |
| time-split-C-0.01 | thresholds | reject | precision_below_min, warnings_above_cap |
| random-split-seeded | evidence | reject | split_not_time_based |
| time-split-leaky | evidence | reject | post_event_feature:repair_minutes, unexpected_input:repair_minutes |
| hero | evidence | reject | dataset_digest_missing, features_not_recorded, seed_not_recorded, signature_missing, split_not_time_based |

`contract.promote()` registers C = 1 as `cinderline-oven-fault` version 1, tags it
`contract_version=1.0.0` and `decided_from_run=<run id>`, and points `candidate` at it;
`models:/cinderline-oven-fault@candidate` loads a model that warns 68 times on the test rows, 15 of
them faults. The decision file (`promotion/decision.json` next to the store) lists the contract
version, thresholds, baselines, every decision with its reasons, the promotion, six limitations (18
test faults, synthetic data, no oven absent from training, a gate that reads declarations, no serving
evidence, no data-quality certificate) and the note that nothing is deployed. Registering the reproduced
rerun creates version 2; moving the alias leaves version 1 with none; moving it back is the rollback.
Both versions predict identically: a version is a registration event, not a content hash.

## Task 8 — transfer

C = 1 on the transfer plant: tp 9, fp 24, fn 6, tn 249, recall 0.6, precision 0.2727, 0.9167
warnings a day. Decision: reject at the thresholds gate, `recall_below_min`.

## The wrong approach, and why it fails

`starters/naive_promotion.py` promotes the run MLflow sorts first by accuracy. On this experiment it
picks a run at accuracy 1.0, the hero or the leaky run depending on MLflow's order for the tie, and
the evidence gate rejects either: the hero's record holds nothing a reviewer could check, and the
leaky run's record honestly states a post-event feature. Accuracy is the wrong single number twice
over here: faults are 6% of test rows, so never-warn beats every honest model at 0.9375; and the one
column that makes a model perfect is the technician's repair record, written after the fault. A
second wrong approach is the random split: its model is scored on days that come before some of its
training days, so its numbers describe interpolation inside a period, not a warning about tomorrow.

One limit of the reference itself: the evidence gate reads what a run declares (its `split`
parameter, its `features` list, its logged signature). A record that misstates them would pass. The
logged check reports under `checks/` are there so a reviewer can compare the declaration with what
the rows show; the gate does not open them.
