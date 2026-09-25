# Migration and reconciliation plan (template)

Fictional exercise. A read-path migration only; no operational write authority
moves. Fill for the path you provisionally choose and note where the
alternative path differs.

## Paths compared

| Criterion | Path A: governed lakehouse (AWS) | Path B: strengthen the existing SQL Server / ETL estate | Contract in the workbook only |
|---|---|---|---|
| Correctness under the contract | | | |
| Morning availability and freshness label | | | |
| Stale labelling and blocked publication | | | |
| Recovery from the timeline's failures | | | |
| Operating effort within disclosed hours | | | |
| Complete cost (named exclusions) | | | |
| What reverses the choice | | | |

Provisional choice and why: [ ]

## Waves

| Wave | Purpose | Entry condition | Exit condition | Owner (role) | Window it needs |
|---|---|---|---|---|---|
| 0 Agree | contract, admission, access, environment, operator, limits | | | | |
| 1 Parallel run | pilot path beside the current report, same population and days | | | | |
| 2 Cutover | switch the read path; old path still fed | | | | |
| 3 Retire | after an agreed recovery window and cleanup sign-off | | | | |

## Reconciliation matrix (per plant and business day)

| Check | Current report | Pilot path | Match rule | Accepted exception | Owner |
|---|---|---|---|---|---|
| Distinct inspection keys | | | | | |
| Accepted count | | | | | |
| Inspected / defective totals | | | | | |
| Revision per corrected key | | | | | |
| Duplicates identified by delivery | | | | | |
| Quarantined rows and reasons | | | | | |
| Missing keys | | | | | |
| Snapshot identity the board showed | | | | | |

Why matching totals alone are insufficient: [use North 2 March]

## Cutover conditions (proposed, not observed)

1.
2.
3.

## Rollback

- Trigger: [unapproved discrepancy, unavailable report, unsafe access behaviour]
- Action: [restore prior board; record which snapshot users saw; keep raw evidence; coordinate corrections with quality]
- Who decides: [ ]
- What is never deleted before acceptance: [ ]

## Governed boundaries (AWS, conditional)

- Compute model drawn: [classic in customer account / serverless in the managed plane]; approved? [no]
- Identities and what each cannot do: [pipeline principal, analyst group, quality group, operator]
- Classification before real data: [owner, status]
- Tests of permitted and denied actions: [ ]
