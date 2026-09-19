<!-- section:why -->

A job succeeded yesterday but fails today after writing part of its output. The customer asks whether pressing Retry is safe. Answer by tracing state changes and side effects.

<!-- section:understand -->

An operation is **idempotent** when repeating it has the same intended effect as applying it once. A retry policy says when to try again; it does not make the underlying work idempotent. For each task identify inputs, output state, commit boundary, and effects outside the data transaction.

Orchestration coordinates task dependencies and execution. Lakeflow Jobs supplies jobs, tasks, triggers, and run monitoring. Declarative pipelines describe data transformations and dependencies in SQL or Python. These responsibilities complement each other; neither removes the need for an operating plan.

Quality handling should distinguish valid data, rejected data, and unknown data. Pipeline expectations can evaluate record-level Boolean rules with actions such as retaining, dropping, or failing invalid records. Cinderline still needs a place to inspect quarantined data and a named owner to decide how to correct it. Silently dropping every surprising row makes a clean-looking report at the cost of hidden incompleteness.

<!-- section:see -->

**Fictional failure walkthrough.** Task 1 stores the raw batch; task 2 applies accepted inspection revisions; task 3 publishes a report; task 4 sends a notification. The process fails after task 3 but before the notification acknowledgement.

| Boundary | Question before retry |
|---|---|
| Raw write | Can the same batch ID be recognized? |
| Transformation | Does replay preserve the accepted inspection state? |
| Report publication | Is the published version identifiable? |
| Notification | Can a repeated request send duplicate messages? |

A successful data transaction does not answer the last question. Track the external effect or design a safe repeat policy.

<!-- section:deeper -->

An expectation is not a general cross-table reconciliation engine. Use explicit tests for aggregate counts, totals, referential relationships, and business exceptions that exceed a row-level expression. Define alert thresholds, owner, investigation evidence, replay procedure, and escalation. A recoverability test should introduce a known failure, then compare actual output after retry with the expected state; a green task icon alone is insufficient.

<!-- section:customer -->

For the operating team: “We will test a retry after a partial failure and compare the final data to the expected result. We also need an owner for quarantined records and a safe policy for notifications, because repeating a job must not silently double-count or duplicate external actions.”

<!-- section:try -->

A hypothetical batch has 100 records, of which 4 fail a required quantity rule. The report must disclose incomplete coverage. Choose a handling plan, an owner, and a replay test. Explain why “drop the 4 and mark success” is incomplete.

<!-- section:revisit -->

A defensible plan retains the raw 100, publishes only the 96 valid records if the agreed policy permits it, exposes the 4-record gap, and assigns the quality lead to investigate. If the report requires complete coverage, withhold publication or fail the update under the agreed rule. After correction, replay using stable keys and compare counts and totals to an explicit expected result.

The correct choice depends on the reporting contract. In either case, losing the rejected records or hiding the missing population prevents diagnosis and misleads the reader.
