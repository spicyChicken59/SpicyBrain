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

Every count below is from a synthetic dataset; nothing was deployed.

#### Target and action

Predict at 09:00 each day, for each of the North plant's six coating ovens, a fault stop in the next 24 hours. The action: the maintenance lead adds a flagged oven to that day's inspection round, which holds four ovens at most. Available at 09:00: sensor readings to 09:00 (temperature, door cycles, humidity), oven age, days since last service. Recorded afterwards and excluded: fault code, technician's diagnosis, repair duration, any later reading.

#### Baselines

Rule in use: inspect an oven when its temperature exceeded the set point twice in the previous shift. Trivial predictor: never warn. Class balance: 84 fault stops in the 2,184 oven-days the splits use (3.8%).

#### Split

By time and by oven. Training: weeks 1 to 48, four ovens (1,344 oven-days, 52 faults). Validation: weeks 49 to 60, the same four ovens (336 oven-days, 14 faults), used to choose the threshold. Test: weeks 61 to 72, all six ovens (504 oven-days, 18 faults), of which the two ovens never seen in training contribute 168 oven-days and 7 faults; their earlier weeks are set aside. Leakage check: a point-in-time join test compared every feature's timestamp with 09:00; a first version computing "days since last service" from the service after the fault was caught by it and rebuilt.

#### Results on the test period, threshold chosen on validation

| Predictor | Recall | Precision | Warnings a day (84 days) | Missed |
|---|---|---|---|---|
| Never warn | 0 of 18 | none | 0 | 18 |
| Rule, six ovens | 7 of 18 | 7 of 31 | 0.37 | 11 |
| Model, six ovens | 11 of 18 | 11 of 34 | 0.40 | 7 |
| Rule, four training ovens | 4 of 11 | 4 of 20 | 0.24 | 7 |
| Model, four training ovens | 9 of 11 | 9 of 22 | 0.26 | 2 |
| Rule, two unseen ovens | 3 of 7 | 3 of 11 | 0.13 | 4 |
| Model, two unseen ovens | 2 of 7 | 2 of 12 | 0.14 | 5 |

At this threshold the round gets 0.4 flagged ovens a day against four places; a lower threshold catching two more faults raised warnings to 2.9 a day, most of the round.

#### Reading the results

On seen ovens the model catches 9 of 11 against the rule's 4, at a similar load (22 warnings against 20). On unseen ovens it catches 2 of 7 against the rule's 3; 7 faults are too few to say by how much. The plan warns on all ovens, including two replaced next quarter, so the unseen result is the one that matters.

#### Risks

Small sample: 18 test faults; model and rule differ by 4 on all six ovens. Label delay: the technician confirms a fault the next day, so monitoring is a day behind. Drift: set points change with product mix, which training covered only partly. Untested: behaviour after a service, when readings reset; oven 5's humidity sensor, offline for a week and imputed.

#### Monitoring, if used

Daily: warnings against capacity; each input against its training range; missing readings. Weekly, once labels arrive: recall and precision, separately for seen and unseen ovens. Review when warnings exceed capacity on three days, an input leaves its training range for a full day, or recall trails the rule's for four consecutive weeks.

#### Decision

Not for use on all ovens. Supported: the model is worth continuing, because on seen ovens it beats the rule at a similar load. Not supported: any claim about unseen ovens or the two replacements. Recommended: keep the temperature rule, collect twelve more weeks including the replaced ovens, and re-run this report with the same split design. What would change the decision: recall on unseen ovens at or above the rule's on at least 20 faults.

#### Run record

Tracked run `ovens-eval-01`, dataset snapshot `ovens-synthetic-v1`, code tag `report-v1`, environment captured with the run; all are synthetic placeholders.

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
