<!-- section:dbxfe-mlflow-l01-outcome -->

After this lesson you can read an MLflow run as evidence: what its parameters, metrics, artifacts, datasets and model record, and what none of them proves. You can judge whether two runs are comparable, rerun a run from its record or name what is missing, package a model with its signature and environment, and promote a registered version by moving an alias only after its record passes a written contract. Everything runs on open-source MLflow 3.16.1; no Databricks workspace is needed.

<!-- section:dbxfe-mlflow-l01-start -->

Bring the habits from [Start ML with a baseline and a valid target](#/lesson/dbxfe-m07-l01): a target tied to an action, a prediction moment, a trivial baseline beside the rule in use, and a split shaped like deployment. This lesson gives them a record. The running example is fictional Cinderline Components predicting, at 09:00, whether a coating oven will stop with a fault in the next 24 hours; a flagged oven joins an inspection round that holds two of eight ovens. Lab L17 produced the running example's numbers by execution, on synthetic data.

<!-- section:dbxfe-mlflow-l01-record -->

An **experiment** groups **runs**, and a run is one execution of training or evaluation code. A run records **parameters** (inputs you chose, such as `C=1.0` or `seed=20260923`), **metrics** (numbers you measured, each with an optional step history), tags, the **datasets** it read and the **artifacts** it wrote: reports, plots and a model directory. A backend store keeps the metadata and an artifact store keeps the files; in the lab's file store you can open them as `params/C`, `metrics/recall` and `artifacts/checks/split_report.json`.

Parameters are logged once: logging `C=0.5` into a run that recorded `C=1.0` raises *Changing param values is not allowed*. In MLflow 3 a logged model is its own entity with an ID (`models:/m-…`), and metrics can be linked to it as well as to the run.

```python
with mlflow.start_run(run_name="time-split-C-1"):
    mlflow.log_params({"C": 1.0, "seed": 20260923, "split": "time", "train_through_day": 84})
    mlflow.log_input(train_ds, context="training")
    info = mlflow.sklearn.log_model(model, name="model", signature=signature, input_example=X.head(3))
    mlflow.log_metrics(metrics, model_id=info.model_id)
```

<!-- section:dbxfe-mlflow-l01-datasets -->

`mlflow.data.from_pandas()` turns the rows a run saw into a dataset with a name, source, schema, profile and **digest**; `mlflow.log_input()` attaches it with a context such as `training` or `evaluation`. Log the rows, not only the chosen columns: the lab's C = 1, C = 0.01 and leaky runs share digest `4950f73b` because they trained on the same 672 rows, while the random split's training rows have `3f06bea0`.

A digest identifies content; it does not judge it. In MLflow 3.16.1 the pandas digest hashes at most the first 10,000 rows plus the row count and column names, so a change in row 10,001 leaves it unchanged. And a complete record can describe an invalid experiment: the leaky run logged everything, including `repair_minutes`, which the technician writes after the fault. **A logged run does not certify data quality.** The availability dictionary and the split check do that work, and the run keeps their reports as artifacts.

<!-- section:dbxfe-mlflow-l01-compare -->

Two runs compare cleanly when they trained on the same rows and differ in one deliberate parameter. C = 1 against C = 0.01 isolates regularization; C = 1 against the leaky run differs only in `features`, so the jump from accuracy 0.8056 to 1.0 is the leak alone. A run on different rows, or with no dataset at all, is not a comparison. Log baselines as runs in the same experiment, then sort by accuracy: the two runs that read the repair record tie at 1.0, and never-warn is third at 0.9375 because faults are rare. The contract's measures (recall, precision, warnings a day) are the ones that map to the inspection round.

<!-- section:dbxfe-mlflow-l01-reproduce -->

A run is **reproducible from its record** when its parameters, training data and environment are enough to rerun it and get the same numbers. The lab's clean rerun reads `C`, `seed`, `split`, `train_through_day`, the feature list and the scikit-learn version from the record, retrains, gets the same digest and metrics equal to the original bit for bit. The hero run cannot: it logged only `model=logistic_regression`, used an unseeded random split and read the repair record. Running its code again produced an identical record and a different result, 20 of 20 faults caught in one test set and 18 of 18 in another, so its number is not a property of its record. Refuse rather than guess, and name what is missing. A rerun on changed data is a new experiment, and a different library version is refused.

<!-- section:dbxfe-mlflow-l01-package -->

A logged model is a directory whose `MLmodel` file lists its **flavors**: `python_function`, the generic interface MLflow's tools load, and a library flavor such as `sklearn`. MLflow 3.16.1 saved the lab's pipeline as `model.skops` by default and wrote `requirements.txt`, `python_env.yaml` and `conda.yaml` pinning the **environment** that loads it.

A **signature** names six `double` inputs and `fault_next_24h` as a `long` output. Loading as `python_function` enforces it before the model runs; loading with the native flavor does not. A versioned **model contract** adds what the signature leaves out: no unexpected inputs, the output clause, thresholds and required evidence.

| drift | pyfunc enforcement | contract 1.0.0 |
|---|---|---|
| `humidity_pct` renamed | error: missing input | missing and unexpected input |
| `door_cycles` as int64 | error: unsafe conversion | type mismatch |
| `repair_minutes` added | ignored with a warning | unexpected input |
| columns reordered | accepted | accepted |

<!-- section:dbxfe-mlflow-l01-registry -->

A **registered model** holds numbered **versions**, each with lineage to the run that produced it. An **alias** is a mutable name for one version, loaded as `models:/cinderline-oven-fault@candidate`; tags annotate versions. A version's model files do not change; the alias moves, and moving it back is a rollback. The lab's reproduced rerun became version 2 with identical predictions: a version records a registration, not unique content.

**Promotion by evidence** reads the record before the metrics:

1. Evidence gate: a time split, a recorded seed, a logged training dataset, a feature list with no post-event column, a signature matching the contract.
2. Thresholds, only for runs that passed: recall ≥ 0.75, precision ≥ 0.2, at most 2.0 warnings a day.
3. Register only the run decided `promote-candidate`, tag the version with the contract version and the run, move the alias, and write every run's reasons to a decision file.

Promotion here deploys nothing.

<!-- section:dbxfe-mlflow-l01-managed -->

Open-source MLflow gives you the APIs and file formats; you run the tracking server and choose, secure and back up its stores. In MLflow 3.16.1 the default tracking URI is a local SQLite file, and the `./mlruns` file store is in maintenance mode: the lab opts in with `MLFLOW_ALLOW_FILE_STORE=true`.

Databricks-managed MLflow hosts tracking in the workspace, where experiments carry permission levels such as CAN READ, CAN EDIT and CAN MANAGE. Its registry is **Unity Catalog**: a three-level name such as `cinderline_ml.maintenance.oven_fault`, catalog privileges (`CREATE MODEL` with `USE CATALOG` and `USE SCHEMA` to create, `EXECUTE` to load), aliases and tags instead of stages, and with MLflow 3 the default registry. The platform takes hosting and access; choosing the run, writing the contract and checking the data stay with the team.

<!-- section:dbxfe-mlflow-l01-example -->

From the executed lab. Time-split runs and baselines are scored on days 85–120 (288 oven-days, 18 faults); the random-split runs on their own 288 rows.

| run | recorded split | training digest | accuracy | recall | warnings/day | decision |
|---|---|---|---|---|---|---|
| hero | none | none | 1.0 | 1.0 | 0.56 | reject: evidence, 5 reasons |
| time-split-leaky | time | 4950f73b | 1.0 | 1.0 | 0.50 | reject: post-event feature |
| never-warn | time | baseline | 0.9375 | 0 | 0 | baseline |
| temperature-rule | time | baseline | 0.8715 | 0.6667 | 1.19 | baseline |
| random-split-seeded | random | 3f06bea0 | 0.8438 | 0.7368 | 1.50 | reject: split |
| time-split-C-1 | time | 4950f73b | 0.8056 | 0.8333 | 1.89 | promote-candidate |
| time-split-C-0.01 | time | 4950f73b | 0.7396 | 0.9444 | 2.53 | reject: precision, cap |

On a second synthetic plant the same C = 1 configuration reaches recall 0.6 and the same contract rejects it.

<!-- section:dbxfe-mlflow-l01-exercise -->

A colleague's run reports accuracy 0.99 and recall 0.97 and asks for the `candidate` alias. Its record holds `model=gbm`, `max_depth=6`, `split=random`, a training dataset, no seed, no feature list, and a signature with seven inputs including `fault_code`. Write the review: what you check first, the decision, the reasons, and what the record would need for a rerun.

<!-- section:dbxfe-mlflow-l01-solution -->

Evidence before metrics. `split=random` puts days before the end of training into the test rows: `split_not_time_based`. No seed: `seed_not_recorded`, so the split cannot be recreated. No feature list: `features_not_recorded`. The signature's seventh input is `fault_code`, which the dictionary dates after the fault, so the contract adds `unexpected_input:fault_code`. Decision: reject at the evidence gate; the 0.99 is never read. A rerun needs the seed, a time split with its cut-off day, the feature list, the library versions and a signature matching contract 1.0.0; then compare it with the promoted version on the same rows.

<!-- section:dbxfe-mlflow-l01-mistakes -->

- Promoting the top of a table sorted by accuracy; with rare faults, never-warn scores 0.9375.
- Logging only the chosen columns as the dataset, so two feature sets look like different data.
- Treating a digest as a quality check; it fingerprints rows, in MLflow 3.16.1 at most the first 10,000.
- Calling a run with an unseeded random split reproducible.
- Expecting pyfunc enforcement to stop an extra column; it ignores it.
- Loading with the native flavor and assuming the signature was enforced.
- Treating an alias as a deployment, or carrying stages into Unity Catalog, which does not support them.

<!-- section:dbxfe-mlflow-l01-sources -->

MLflow's tracking, dataset tracking, models, signatures, dependencies, model registry and file store migration pages support the mechanisms. Databricks' MLflow and Unity Catalog model lifecycle pages support the managed column. scikit-learn's common pitfalls page supports leakage and `random_state`. Version-specific behaviour (skops by default, the 10,000-row digest, ignored extra inputs, the SQLite default) was observed by executing lab L17 on MLflow 3.16.1; re-check it on another version. Titles and URLs were confirmed by search; documentation hosts were unreachable.

<!-- section:dbxfe-mlflow-l01-related -->

Before this: [Start ML with a baseline and a valid target](#/lesson/dbxfe-m07-l01) in the [machine-learning foundations module](#/module/dbxfe-m07). Alongside: the features module for point-in-time feature data, the serving module for what happens after an alias moves, and the model evaluation report field guide, whose run record section asks for the tracked run, dataset version, code version and environment behind every number. Lab L17 executes each step.

<!-- section:dbxfe-mlflow-l01-revisit -->

In a week, without notes: list what a run must record to be rerun; explain why never-warn tops an accuracy table when faults are rare; name the two drifts pyfunc enforcement rejects and the one it ignores; and say what moves in a promotion and what does not. Then open an experiment of your own and find a run you could not reproduce from its record alone.
