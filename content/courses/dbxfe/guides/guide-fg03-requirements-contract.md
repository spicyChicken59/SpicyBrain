<!-- section:action -->

Write the contract once the decision and the metric are named, and before anyone estimates effort. A requirement that nobody can test is a wish; write it so that a specific observation would show it unmet.

1. **Start each functional requirement from a decision or an action** the customer must be able to take, then state what the system must do for that, with the population it applies to.
2. **State nonfunctional requirements as measurements**: freshness with its clock and window, correctness with what must reconcile and which exceptions are accepted, availability with the hours that matter, recovery with who acts and how long it may take, access with who may and who must not.
3. **Attach an acceptance test to every requirement**: population, method, threshold, evidence produced, and the person who accepts. A requirement without an acceptor is not in the contract.
4. **Separate must, should and later**, and record who asked for each tier.
5. **Record the assumptions the contract rests on** and what happens to it if one fails.
6. **Have each acceptor read their own rows** and either agree or revise before execution.

Evidence to collect: the metric contract, the current-state baseline (or the fact that none exists), any policy the security lead has issued in writing, and the operating hours that define "available."

Go deeper: [define success and expose missing information](#/lesson/dbxfe-m02-l03) for baseline, target and result, [discovery and qualification](#/module/dbxfe-m02), [proofs of value](#/module/dbxfe-m10) for how a contract becomes a charter, and [data modeling and metric contracts](#/module/dbxfe-modeling) for the metric rows this contract depends on.

<!-- section:example -->

### Requirements contract: Cinderline Components (fictional), one-plant daily quality report

#### Purpose

Give the North plant's 8 a.m. meeting one previous-day defect rate that operations, quality and the plant analyst all accept, so nobody argues about the number before choosing a line.

#### Functional requirements

| Id | Requirement | Population | Tier | Asked by |
|---|---|---|---|---|
| F1 | Publish a per-line defect rate for the previous business day under the agreed metric contract | North plant inspections | Must | Operations director |
| F2 | Apply approved corrections in source-revision order, replacing the earlier state of the same inspection | Periodic correction CSVs | Must | Quality lead |
| F3 | While a conflict (same inspection and revision, different quantities) is unresolved, publish no new rate; show the last verified one as stale; list the conflict for the quality lead | All inspections | Must | Quality lead |
| F4 | Show, beside the rate, the number of inspections excluded and why | Published report | Must | Plant analyst |
| F5 | Restate a prior day's rate when a correction for that day is approved, and mark the restatement | Previous 30 business days | Should | Quality lead |

#### Nonfunctional requirements

| Id | Requirement | Measurement | Tier |
|---|---|---|---|
| N1 | Freshness: the report includes every record approved by the time the ERP export completes and is available before 7:30 a.m. plant time | Source-to-report timestamps, each test day | Must |
| N2 | Correctness: per-line inspected and defective totals reconcile exactly to the accepted source rows except listed exclusions | Independent recount from the raw export, per line per day | Must |
| N3 | Access: reporting analysts read the published rate; only the quality lead's group reads quarantined rows; nobody in the pilot can modify raw inspections | Allowed and denied tests, representative identities | Must |
| N4 | Recovery: a failed nightly run is detected before 7:00 a.m. and a named operator reruns it to the intended state without duplicating corrections | One rehearsed failure during the test | Must |
| N5 | Operability: the data team runs the path within its stated part-time capacity | Runbook walkthrough | Should |

#### Acceptance

| Requirement | Method | Threshold | Evidence | Acceptor |
|---|---|---|---|---|
| F1, F4, N2 | Recompute from raw rows for five staffed days | Exact match per line; disclosed exclusion counts equal the sheet's | Reconciliation sheet with both counts | Quality lead and plant analyst |
| F2, F3, F5 | Replay the synthetic correction set with a conflict and a late correction for day 2 | Conflict blocks the new rate, the last verified one shown stale; each correction applied once; day 2 restated and marked | Replay output and quarantine list | Quality lead |
| N1 | Timestamp pairs, same five days | Available before 7:30 on at least four of five days; every miss explained | Timing log | Operations director |
| N3 | Access matrix executed with two test identities | Every expected allow passes, every expected deny fails | Test log with error text | Security lead (open: no reviewer assigned) |
| N4, N5 | Injected failure on one test night, handled from the runbook | Rerun reaches the intended state; time to detect and rerun recorded; the path fits the engineers' stated hours | Operator's log | Data lead (open: operator not named) |

#### Assumptions

The ERP export completes before 6:00 a.m. (stated by the DBA, not measured). The business day ends at midnight plant time (proposed; not yet agreed by the quality lead). Synthetic records stand in until the security review completes; N3 runs on them first, then again on real objects.

#### Exclusions

Sensor context per line (asked by the operations director; later tier): not a failure of this pilot.

#### Sign-off

None yet: version 0.2 is proposed. Testable, with an acceptance row for every requirement, but not accepted: N3 has no reviewer and N4 has no operator, and both are "must." Do not start execution until those two names exist.

<!-- section:template -->

### Requirements contract

#### Purpose

- The decision or action this system supports, the population it covers, and the people who accept it; the version and its status (proposed, accepted, revised).

#### Functional requirements

| Id | Requirement (what the system must do, stated so an observation could show it unmet) | Population | Tier (must, should, later) | Asked by |
|---|---|---|---|---|

#### Nonfunctional requirements

| Id | Requirement (freshness, correctness, availability, recovery, access, operability, cost) | Measurement (clock, window, method) | Tier |
|---|---|---|---|

#### Acceptance

| Requirement ids | Method | Threshold, including how misses are counted | Evidence produced | Acceptor (a named role; "open" if none yet) |
|---|---|---|---|---|

#### Assumptions

- Each assumption, who stated it, whether it is measured, and which requirements fail if it is wrong.

#### Exclusions

- What this contract does not cover, so it cannot be counted as a failure later.

#### Sign-off

- Each acceptor, the rows they read, and the date they agreed or revised.

<!-- section:limits -->

The contract establishes what will be tested, how, and who decides; it cannot establish that the requirements are achievable, that the baseline exists, or that the customer's stated operating hours are the real ones. Thresholds are proposals until each acceptor agrees, and an accepted threshold is not an observed result. The contract does not replace a security review, a metric contract or a cost model; it references them. Rows without an acceptor are not in force. Escalate when a "must" row has no acceptor a week before execution, when an acceptor wants a threshold changed after seeing results, or when two acceptors give incompatible definitions of the same requirement.
