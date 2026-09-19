# Reliable Data Foundations: optional local tasks

All records are original fiction. Predict on paper or in a SpicyBrain note first.
Local execution is optional; these tasks have no cloud prerequisite. Opening a
solution is not completion or evidence of mastery. Keep your attempted reasoning.

## 1. Parse, explain, and reject

Read `fixtures/python_bridge.csv`. Write the accepted/rejected rows before
running `parse_bridge`. Why is p5 accepted? Why can p2 not become zero? In
`starters/python_bridge.py`, implement the *different* s1–s4 case. Include a
function, a loop, explicit missing-value check, conversion with a narrow
exception, and assertions. Explain why `int('2.5')` is not `2`.

## 2. A DataFrame is a plan with typed columns

Create a local Spark session and use `SCHEMA` with `fixtures/baseline.json`.
Predict `printSchema()`. Select inspection_id, version, and inspected_units;
alias inspected_units as inspected. Filter required quantities with `isNull`
and `isNotNull`. Explain why `raw.inspected_units > 0` is a Column expression,
while `12 > 0` is a Python boolean. Predict what `= NULL` versus `IS NULL`
returns. Repair a string input with `try_cast`, retaining malformed rows as
rejected evidence rather than silently dropping them.

## 3. SQL and PySpark give the same business answer

Use `starters/spark_task.py`. Implement the staged transformation in both
languages. Predict the distinct, valid, quarantined and current rows; compare
exact ordered accepted rows *and types*, not screenshots alone. Compute total
defective / total inspected. Now append the correction in `batches.json`.
Which output row changes? Why must 5% change to 1/22 rather than remain 5%?
State the report's excluded source coverage in your answer.

## 4. Diagnose duplicated totals with a real plan

Join accepted inspections to tags A/urgent, A/sampled, C/routine. Predict the
row count and total inspected units before running `count()` and `sum()`.
The question is “inspections with at least one tag.” Repair the join using
that grain; do not average away the error. Run `explain(mode='formatted')`.
Find a join and an Exchange. Explain the grouping/redistribution it describes.
This tiny local test cannot establish production performance, skew, capacity,
cloud permissions or a Databricks runtime's plan.

## 5. Resolve retained history across batches

Repair `starters/resolver.py`. Process the baseline, replay, late A v1,
correction A v3, then replay that correction. In separate fresh simulations,
append event_conflict, version_conflict, invalid_latest and missing_order.
Keep the raw records. Compare the independent literal expected files.
Explain why discarding an invalid latest revision then choosing a lower valid
revision lies about current state. Do not use arrival order as revision order.

## 6. Name and recover the failed boundary

Publish the baseline. Inject failure after `retained_raw` while ingesting A v3.
Record raw count, prior published totals, status, and local notification count.
Recover from retained history and compare to a clean successful correction.
Repeat with `resolved_state` and `published_snapshot`. Why must publication
state and external-effect state be distinct? The notification outbox is an
in-memory simulation and sends nothing.

## 7. Transfer: order-line corrections

Study `fixtures/orders.json`; do not rename inspection columns and assume the
same contract. Choose the business key when O7/L1 and O8/L1 both exist. Explain
whether absence of O7/L2 from a later batch deletes it. Calculate order totals
in integer cents after an explicit cancellation. Retain the cancellation's
revision so replaying its older upsert cannot resurrect it. Add a conflicting
O7/L1 revision 2 quantity 4 and specify what becomes unpublishable.

The complete model and rationale are in `SOLUTIONS.md`; implementation is in
`solutions/`. The solutions are teaching material, not a production framework.
