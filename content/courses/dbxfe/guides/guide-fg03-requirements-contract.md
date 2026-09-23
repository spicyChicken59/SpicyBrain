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

Version 0.2, proposed; rows marked "open" have no agreed acceptor yet.

#### Purpose

Give the North plant's 8 a.m. meeting one defect rate for the previous business day that operations, quality and the plant analyst all accept, so the choice of which line to investigate is not delayed by arguing about the number.

#### Functional requirements

| Id | Requirement | Population | Tier | Asked by |
|---|---|---|---|---|
| F1 | Publish a per-line defect rate for the previous business day, defined as defective units divided by inspected units under the agreed metric contract | North plant inspections | Must | Operations director |
| F2 | Apply approved corrections in source-revision order, replacing the earlier state of the same inspection | Corrections in the periodic CSV export | Must | Quality lead |
| F3 | Hold conflicting records (same inspection and revision, different quantities) out of the published rate and list them for the quality lead | All inspections | Must | Quality lead |
| F4 | Show, beside the rate, the number of inspections excluded and why | Published report | Must | Plant analyst |
| F5 | Restate a prior day's rate when a correction for that day is approved, and mark the restatement | Previous 30 business days | Should | Quality lead |

#### Nonfunctional requirements

| Id | Requirement | Measurement | Tier |
|---|---|---|---|
| N1 | Freshness: the report reflects every source record approved by the time the ERP export completes, and is available before 7:30 a.m. plant time | Source-available timestamp to report-available timestamp, each staffed day of the test | Must |
| N2 | Correctness: per-line inspected and defective totals reconcile exactly to the accepted source rows except listed exclusions | Independent count from the raw export against the report, per line per day | Must |
| N3 | Access: reporting analysts read the published rate; only the quality lead's group reads quarantined rows; nobody in the pilot can modify raw inspections | Positive and negative access tests with representative identities | Must |
| N4 | Recovery: a failed nightly run is detected before 7:00 a.m. and a named operator can rerun it to the intended state without duplicating corrections | One rehearsed failure during the test | Must |
| N5 | Operability: the data team can operate the path with the part-time capacity it has stated | Runbook walkthrough accepted by the data lead | Should |

#### Acceptance

| Requirement | Method | Threshold | Evidence | Acceptor |
|---|---|---|---|---|
| F1, N2 | Recompute from raw rows for five staffed days | Exact match per line, exclusions listed | Reconciliation sheet with both counts | Quality lead and plant analyst |
| F2, F3 | Replay the synthetic correction set including a conflict | Conflict withheld, correction applied once | Replay output and quarantine list | Quality lead |
| N1 | Timestamp pairs for the same five days | Available before 7:30 on at least four of five days; every miss explained | Timing log | Operations director |
| N3 | Access matrix executed with two test identities | Every expected allow passes, every expected deny fails | Test log with error text | Security lead (open: reviewer not yet assigned) |
| N4 | Injected failure on one test night | Rerun reaches the intended state; time to detect and rerun recorded | Operator's log | Data lead (open: operator not named) |

#### Assumptions

The ERP export completes before 6:00 a.m. (stated by the DBA, not measured). The business day ends at midnight plant time (proposed; not yet agreed by the quality lead). Synthetic records stand in until the security review completes; N3 is tested on them first and repeated on real objects.

#### Conclusion

Testable but not yet accepted: N3 has no reviewer and N4 has no operator, and both are "must." Do not start execution until those two names exist. Sensor context per line was requested, is recorded under exclusions, and cannot count as a failure of this pilot.

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
