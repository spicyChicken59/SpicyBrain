<!-- section:why -->

The customer says a dashboard takes 45 seconds. “Add compute” may help, but it may also spend money without addressing the dominant delay. Start by decomposing what the user experienced.

<!-- section:understand -->

Measure the path from user action to usable result. Waiting for capacity, starting compute, executing the query, transferring results, and rendering a dashboard are different portions of elapsed time. A query profile helps inspect execution operators and metrics such as rows, time, and memory. It does not replace the complete user-experience measurement.

Inspect a representative slow case and a useful comparison. Look for an unexpectedly large join result, a scan that reads much more data than needed, skew or spills, and queueing under concurrent use. Change one hypothesis at a time so the result has an explanation.

For fictional Cinderline, a query with a 30-second queue and 5-second execution is different from one with no queue and a 35-second join. The first points toward workload timing or capacity; the second toward the query/data shape and resource evidence. Both still need validation rather than a diagnosis based only on the total.

<!-- section:see -->

**Synthetic timing observations; not platform benchmarks.**

| Run | Queue | Execution | Render/transfer | Total |
|---|---|---|---|---|
| A, peak meeting | 30 s | 5 s | 10 s | 45 s |
| B, quiet period | 0 s | 5 s | 10 s | 15 s |
| C, changed join | 0 s | 35 s | 10 s | 45 s |

A versus B suggests peak waiting is material. B versus C suggests the query change created execution work. The diagnostic tree organizes those branches; it does not prove the root cause without the underlying run evidence.

<!-- section:deeper -->

Viewing a Databricks query profile requires query ownership or suitable warehouse monitoring permission. Cached query results may not have a profile. Avoid comparing a warm cached run with a cold execution as if they differed only by code. Operator task time can also differ from wall-clock time because work runs concurrently. Record query text, input basis, cache conditions, warehouse configuration, and concurrency before comparing.

<!-- section:customer -->

For a BI lead: “The 45 seconds includes several kinds of work. We will compare a peak and quiet run, inspect the query execution evidence, and isolate the dominant delay before choosing a query, data-layout, or capacity change.”

<!-- section:try -->

Using synthetic runs A and B, propose one experiment and its success measure. Then explain why changing the join and warehouse size in the same experiment would make the conclusion harder to interpret.

<!-- section:revisit -->

A controlled experiment could hold the query, input snapshot, and dashboard fixed while testing an agreed capacity or workload-timing change during a representative peak window. Measure queue time and end-to-end latency, recording cache and concurrency conditions. The target should be agreed before the run.

Changing both the join and warehouse size confounds the result: you cannot tell which change caused the improvement or regression. If multiple changes are necessary, stage them and preserve the intermediate observations. The synthetic table suggests a hypothesis, not a universal tuning rule.
