<!-- section:why -->

“Make reports faster” leaves room for two teams to call the same pilot both successful and disappointing. Define what will be measured, under which conditions, and who accepts the result.

<!-- section:understand -->

A **baseline** describes current behavior using a stated measurement method. A **target** is desired behavior. A **result** is an observation from a test. Label each explicitly. Never turn a proposed target into a measured outcome in a recap.

A useful criterion includes a metric, threshold, test population, measurement window, exclusions, and acceptor. For latency, distinguish source-to-serving freshness from the time a dashboard takes after a user clicks. For correctness, define which records and totals must reconcile and what exceptions are allowed.

Fictional Cinderline proposes that an approved one-plant quality report reflect accepted source records within 60 minutes during staffed hours. That is a target, not a product guarantee. The data lead still needs to establish today's delay distribution and whether source records are ready in time. If the source releases data once per day, the target may require changing an upstream process.

<!-- section:see -->

**Fictional criterion worksheet.**

| Part | Proposed entry |
|---|---|
| Population | Approved one-plant inspection records |
| Metric | Source-available timestamp to served timestamp |
| Threshold | 95% within 60 minutes |
| Window | Five agreed staffed days |
| Correctness | Agreed counts and accepted-unit totals reconcile by plant/day |
| Acceptor | Operations lead and data lead |
| Still missing | Baseline, correction policy, clocks, and exception handling |

The 95th percentile describes a distribution; it is not a claim that every record meets the threshold.

<!-- section:deeper -->

Avoid moving the goalposts after seeing results. Agree how to handle excluded records, missing timestamps, downtime, and failed runs before the test. A small sample can be informative without supporting a broad reliability claim. Record the denominator: “19 of 20 test records met the target” is clearer than an isolated “95%.” If the test population is too small to represent normal operations, state that limit and propose the next evidence.

<!-- section:customer -->

For the pilot sponsor: “We propose measuring from when approved source data becomes available to when the report can use it. The target and test window need your agreement. We will report misses and excluded records alongside the headline result.”

<!-- section:try -->

Hypothetical test: 18 of 20 records arrive within 60 minutes, one arrives after 90 minutes, and one has no source timestamp. The agreed criterion requires valid timestamps for all 20 and at least 95% within 60 minutes. Write the honest readout.

<!-- section:revisit -->

The criterion is not met. Only 18 of 20, or 90%, are demonstrably within the threshold, and the timestamp-completeness condition also fails. Do not silently remove the unknown record to improve the result. Investigate the delayed record and missing timestamp with their owners, then rerun the agreed test after correction.

The useful conclusion is bounded: these inputs did not satisfy this criterion. It does not prove the platform can never satisfy it, and it does not justify relabeling the target. Save the actual counts, the missing-data issue, and the next action.
