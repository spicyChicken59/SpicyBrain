<!-- section:action -->

A charter is written so that the result can be interpreted afterwards by someone who was not there. Every field exists to remove one way the result could be argued about.

1. **Baseline first.** Measure the current state on the same metric and population the test will use: timing distribution, error and correction counts, effort. If it cannot be measured before the test, say so and make measuring it the first test.
2. **Hypothesis.** One sentence of the form "the proposed path can do X on population Y within Z, operated by W".
3. **Scope.** Population, fields, time window, environment, workload basis, and the deliberate edge cases. Name what is excluded.
4. **Roles.** Who executes, who accepts each criterion, who approves access and spending, who operates. Roles are proposed until the named people confirm.
5. **Criteria.** Measurable, with a threshold, a measurement method and an acceptor each. Include correctness, freshness, recovery and operation, not only performance.
6. **Stop conditions.** Events that pause the test: unapproved data, spending past the bound, an invalid comparison basis, a missing owner.
7. **Exit decisions.** The readout will choose one of: expand a bounded slice, revise, collect missing evidence, retain the current path, stop. Say what evidence leads to each.
8. **Prerequisites and limits.** Access, environment, budget ceiling and its status (planning figure or authorization), data approvals.

Evidence to collect: the baseline measurements, the signed-off criteria table, the confirmation from each role holder, the prerequisite status, and the change log.

Deeper: the retained lessons [Build a baseline and a hypothesis](#/lesson/dbxfe-m10-l01) and [Write the charter before execution](#/lesson/dbxfe-m10-l02), the module [Proofs of value](#/module/dbxfe-m10), and [Compute choices, cost and FinOps reasoning](#/module/dbxfe-finops) for the spending bound.

<!-- section:example -->

**Fictional worked example: Cinderline one-plant quality pilot charter, draft for review.** All names, dates, figures and thresholds are fictional and marked proposed until the named people confirm them.

### Baseline (partly measured)

Over the last ten reporting days at plant one, the analyst workbook was ready between 09:15 and 11:40 clock time, measured from its save timestamps; the 08:00 meeting used the plant sheet on every one of those days. Minutes from source availability could not be computed, because nobody records when its inputs arrive; the baseline week records the current path on both measures. Three corrections arrived in the period; two were applied to the workbook, one was missed. Reconciliation effort was not measured; the data lead estimates two to four hours per week, and the charter records it as an estimate, to be measured on the current process in the baseline week.

### Hypothesis

The approved plant-one inspection population can be interpreted consistently by one accepted-inspection path and served before the 08:00 meeting on staffed reporting days, operated by a named person within the effort the team can sustain.

### Scope

Population: plant-one inspections with approved fields only, as classified by the security lead. Window: five consecutive staffed reporting days, plus the baseline week. Environment: the platform workspace the data lead provisions, in the region security accepts; until then, local execution over approved synthetic data, labelled separately. Workload basis: the same morning report and the same two analyst queries, nothing added. Edge cases delivered deliberately: a duplicate batch, a late correction, an invalid quantity, and one injected failure with replay. Excluded: the other two plants, sensor events, the maintenance assistant, any write back to the ERP.

### Roles (proposed)

| Role | Person | Confirms |
|---|---|---|
| Executes the path | Data lead | Not yet |
| Accepts metric meaning and corrections | Quality lead | Confirmed in writing after the demo |
| Accepts operational usefulness | Operations director | Not yet |
| Approves data and network access | Security lead | Requires specialist review first |
| Approves spending | Sponsor | Planning figure only; no authorization |
| Operates during the test | Oskar (engineer) | Nominated; backup not identified |

### Criteria (proposed)

| Criterion | Threshold | Measured how | Acceptor |
|---|---|---|---|
| Correctness | Key-level and total reconciliation against the re-cut old report, exceptions named | Reconciliation record per day | Quality lead |
| Freshness | Served by 07:45 plant time, and within 60 minutes of source availability, on at least 4 of 5 days; the fifth explained | Publication and source-availability timestamps, from the pipeline | Operations director |
| Replay | Same snapshot after duplicate delivery; corrected snapshot after correction | Snapshot ids | Quality lead |
| Recovery | Injected failure recovered by the operator within 30 minutes using the runbook | Timed rehearsal record | Operations director |
| Operation | Operator reports effort per day; no day exceeds one hour | Operator log | Operations director |

Clock time tests the hypothesis; the 60 minutes isolate the path's own delay. Neither the data lead nor the operator, who execute the path, accepts a criterion.

### Stop conditions

Unapproved fields appear in any input; spending approaches the planning figure of a hypothetical $1,500 without an authorization; the old report's basis changes mid-test so the comparison is invalid; the operator is unavailable for a day with no backup.

### Exit decisions

Expand to a second plant only if all five criteria are met and an operator with a backup is confirmed. Revise if correctness or replay fail. Collect missing evidence if freshness fails on a source-availability cause. Retain the current path if operation effort exceeds what the team confirms it can sustain. Stop if access is not approved in the window.

### Prerequisites and their status

Specialist review of the source path: not started. Region and connectivity pattern: not agreed. CDC permission: awaiting the DBA. Baseline effort measurement: the baseline week. Budget: a planning ceiling, not authorization.

### Change log

2026-02-24: draft 1 sent for review; the maintenance assistant request raised during the demo was declined for this charter and logged separately.

<!-- section:template -->

### Baseline

- **Metric, population and method used to measure the current state; the measured values; anything estimated rather than measured, and when it will be measured.**

### Hypothesis

- **One sentence: the proposed path can do what, on which population, within what bound, operated by whom.**

### Scope

- **Population and fields, time window, environment and its status, workload basis, deliberate edge cases, explicit exclusions.**

### Roles

| Role | Person | Confirmed? |
|---|---|---|
| Executes / accepts each criterion / approves access / approves spending / operates | | Yes, no, or conditional on what |

### Criteria

| Criterion | Threshold | Measured how | Acceptor | Status (proposed / accepted) |
|---|---|---|---|---|
| Correctness / freshness / replay / recovery / operation, and others the decision needs | | | | |

### Stop conditions

- **Observable events that pause the test, and who declares the pause.**

### Exit decisions

- **Expand / revise / collect evidence / retain / stop, each with the evidence that leads to it.**

### Prerequisites and limits

- **Access, environment, data approvals, budget figure and whether it is authorization, and each item's status.**

### Change log

- **Date, change, effect on what the test can still establish, who agreed.**

<!-- section:limits -->

A charter establishes what will be tested, how it will be judged and by whom, before execution; it establishes no result. Criteria remain proposals until the named acceptors accept them, and a baseline that was estimated rather than measured cannot support a before-and-after claim. A planning budget figure is not authorization to spend, and no execution in a customer environment follows from a signed charter without separate access and spending approval. The charter also cannot make a synthetic test representative of production; it can only label which evidence is synthetic. Escalate when a stop condition fires, when scope changes are requested mid-test, or when a role has no confirmed person by the start date.
