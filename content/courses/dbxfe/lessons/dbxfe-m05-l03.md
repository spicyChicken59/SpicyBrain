<!-- section:why -->

One analyst sees a fast query at noon, but the morning team sees long queues. Learn why individual query speed and service capacity are related but different questions.

<!-- section:understand -->

**Concurrency** is simultaneous work. **Latency** is time to a usable result. **Throughput** is completed work over time. A system can run one query quickly yet struggle when many users arrive together. Conversely, adding capacity may not fix a query that multiplies rows unnecessarily.

Warehouse size changes resources available within a cluster; scaling behavior and cluster count affect how work is handled under load. Databricks documents different behavior for serverless and classic/pro warehouses. Use the appropriate documentation and observed queues/spills rather than assuming one scaling model fits every type.

For fictional Cinderline, define the morning population: how many users, which dashboards, what refresh pattern, and what acceptable latency. Compare useful work completed against the total cost basis. Idle time, start behavior, data transfer, and other relevant charges can matter; an hourly compute label alone is not a customer cost model.

<!-- section:see -->

**Hypothetical experiment plan, not a price quote.**

| Test | Fixed conditions | Change | Measure |
|---|---|---|---|
| Baseline | Same queries, data, 12 concurrent users | Current configuration | Queue, end-to-end latency, failures, usage |
| Candidate | Same workload window and cache policy | One capacity setting | Same measures and cost basis |
| Quiet check | Two users, same data | Candidate configuration | Unnecessary idle consumption |

The third row matters: a configuration that helps a short peak may be wasteful for the rest of the day.

<!-- section:deeper -->

Do not translate an increase in resources into a guaranteed proportional speedup. Bottlenecks may move, and workload distributions matter. Averages can conceal slow experiences; report a distribution or counts against an agreed threshold. If an optimization improves query latency but increases rejected queries or excludes a difficult workload, preserve that tradeoff. A bounded test should have a spending limit and a stop condition, both authorized in a real environment.

<!-- section:customer -->

For a data-platform owner: “We will compare configurations under the actual morning workload and a quiet period, recording both user experience and usage. We will recommend the smallest justified change, with the assumptions and excluded costs visible.”

<!-- section:try -->

A hypothetical candidate reduces median query latency from 8 to 5 seconds but leaves the slowest 10% above 60 seconds and increases total test cost. The agreed objective is 95% under 15 seconds. Write a recommendation.

<!-- section:revisit -->

Do not call the objective met: if 10% remain over 60 seconds, fewer than 95% can be under 15 seconds. Report the median improvement and its cost alongside the failed tail-latency criterion. Investigate whether a subset of queries, skew, queueing, or another path causes the tail before recommending more capacity.

The result may justify a targeted follow-up, not a blanket rejection or acceptance. Keep the test population and conditions stable so the next experiment can explain what changed.
