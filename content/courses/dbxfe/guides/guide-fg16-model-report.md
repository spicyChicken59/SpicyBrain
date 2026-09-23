<!-- section:action -->

Write the report so a reader who never saw the notebook can tell whether the model should be used, and so a reader who did can check every number. The report exists to support a decision, and "not yet" is a legitimate one.

1. **Define the target**: the outcome predicted, the horizon, the moment of prediction, and the action a prediction would change. State which fields exist at that moment and which are recorded afterwards.
2. **Name the baselines**: the rule in use today and a trivial predictor. A model is judged against both.
3. **Describe the split** so it mirrors deployment: by time, by machine or entity, or both; record the periods and counts on each side and how leakage was checked.
4. **Report the metrics that map to consequences**, at the threshold you propose, beside the baselines: what a false alarm costs in inspection load, what a miss costs, how many alerts a day the threshold produces. Include the class balance.
5. **List the risks** you found and the ones you could not test: leakage, label delay, drift, small samples, entities absent from training.
6. **State the monitoring** that would run if the model were used: which inputs, which outputs, when labels arrive, what triggers a review.
7. **Conclude with the decision the evidence supports** and what evidence would change it.

Go deeper: [machine-learning foundations and evaluation](#/module/dbxfe-m07), [start ML with a baseline and a valid target](#/lesson/dbxfe-m07-l01), [features and point-in-time correctness](#/module/dbxfe-features) for the availability timeline, [MLflow and reproducibility](#/module/dbxfe-mlflow) for the run record behind each number, and [inference, serving and model operations](#/module/dbxfe-serving) for monitoring.

<!-- section:example -->

### Model report: Cinderline Components (fictional), coating-oven fault warning

Every count below is from a synthetic dataset built for this example; nothing was deployed.

#### Target and action

Predict, at 09:00 each day for each of the North plant's six coating ovens, whether the oven will have a fault stop in the following 24 hours. The action: the maintenance lead adds a flagged oven to that day's inspection round, which holds four ovens at most. Available at 09:00: sensor readings to 09:00 (temperature, door cycles, humidity), oven age, days since last service. Recorded afterwards and excluded: fault code, technician's diagnosis, repair duration, any later reading.

#### Baselines

Rule in use: inspect an oven when its temperature exceeded the set point twice in the previous shift. Trivial predictor: never warn. Class balance in the dataset: 84 fault stops in 2,160 oven-days (3.9%).

#### Split

By time and by oven. Training: weeks 1 to 8, four ovens (1,344 oven-days, 52 faults). Validation: weeks 9 and 10, the same four ovens (336 oven-days, 14 faults), used to choose the threshold. Test: weeks 11 and 12, all six ovens (504 oven-days, 18 faults), of which the two ovens never seen in training contribute 168 oven-days and 7 faults. Leakage check: a point-in-time join test compared every feature's timestamp with 09:00; a first version computing "days since last service" from the service after the fault was caught by it and rebuilt.

#### Results on the test period, threshold chosen on validation

| Predictor | Recall of fault stops | Precision of warnings | Warnings per day (six ovens) | Missed faults |
|---|---|---|---|---|
| Never warn | 0 of 18 | none | 0 | 18 |
| Temperature rule | 7 of 18 | 7 of 31 | 2.2 | 11 |
| Model, all six ovens | 11 of 18 | 11 of 34 | 2.4 | 7 |
| Model, four training ovens only | 9 of 11 | 9 of 22 | 1.6 per four ovens | 2 |
| Model, two unseen ovens only | 2 of 7 | 2 of 12 | 0.9 per two ovens | 5 |

At this threshold the round holds 2.4 flagged ovens on average against a capacity of four; a lower threshold recovering two more faults raised warnings to 4.1 a day, beyond the round.

#### Reading the results

On ovens the model has seen, it catches more faults than the rule at a similar warning load. On the two ovens it has not seen it is worse than the rule, and 7 faults are too few to say by how much. Since the plan is to warn on all ovens, including two replaced next quarter, the unseen-oven result is the one that matters.

#### Risks

Small sample: 18 test faults; the difference between the model and the rule on all six ovens is 4 faults. Label delay: a fault is confirmed by the technician the next day, so any monitoring is a day behind. Drift: the ovens' set points change with product mix, which the training period covered only partly. Untested: behaviour after a service, when readings reset; the humidity sensor on oven 5, which was offline for a week and imputed.

#### Monitoring, if used

Daily: warnings against the round's capacity; each input's distribution against its training range; ovens with missing readings. Weekly, once labels arrive: recall and precision on the confirmed faults, separately for ovens seen and unseen in training. Review triggered by warnings exceeding capacity on three days, by any input outside its training range for a full day, or by four consecutive weeks with recall below the rule's.

#### Decision

Not for use on all ovens. Supported: the model is worth continuing, because on seen ovens it beats the rule at the same load. Not supported: any claim about unseen ovens or about the two replacements. Recommended: keep the temperature rule, collect twelve more weeks including the replaced ovens, and re-run this report with the same split design. What would change the decision: recall on unseen ovens at or above the rule's on at least 20 faults.

<!-- section:template -->

### Model report

#### Target and action

- Outcome, horizon, prediction moment, the action a prediction changes; fields available at that moment and fields recorded afterwards and excluded.

#### Baselines

- The rule in use; a trivial predictor; class balance in the dataset.

#### Split

- Method (time, entity, both); periods and counts per side including positives; how the threshold was chosen; the leakage test and what it caught.

#### Results

| Predictor | Recall (positives caught / total) | Precision (correct warnings / warnings) | Warnings per period against capacity | Misses |
|---|---|---|---|---|

- Results for entities absent from training reported separately.

#### Risks

- Sample size in positives; label delay; drift sources; imputed or missing inputs; conditions not tested.

#### Monitoring, if used

- Daily and periodic checks on inputs, outputs and labels; the triggers for a review; who reviews.

#### Decision

- What the evidence supports, what it does not, the recommendation, and the observation that would change it.

#### Run record

- The tracked run, dataset version, code version and environment behind every number above.

<!-- section:limits -->

The report establishes what a model did on the data and split you recorded; it cannot establish future performance, behaviour on entities or conditions absent from the test, or that the action it supports is worth taking, which needs the maintenance owner's judgement of the costs of misses and false alarms. Small positive counts make differences between predictors unreliable, and a good offline result is not evidence about serving latency, feature availability at prediction time in production, or monitoring cost. Metrics without a threshold and a warning load are not decision evidence. Escalate when a feature's availability time cannot be established, when labels will arrive later than any review could act, or when a sponsor asks for a deployment claim the split cannot support.
