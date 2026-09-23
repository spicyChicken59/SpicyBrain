<!-- section:action -->

A handoff moves a working path from the people who built it to the people who will live with it. The plan is a list of things that must be true on the day the builders step back, with a name against each.

1. **List the components** being handed over: pipelines, tables, reports, runbooks, identities, alerts, the comparison and reconciliation records.
2. **Name an owner and a backup for each**, and record whether each person has acknowledged the role. A name in a table is a proposal until the person says yes.
3. **Map the dependencies** the path relies on and who provides them: source approvals, permissions, schedules held by other teams, budget renewals, environment ownership.
4. **Check operational readiness** as observable items: the runbook was used by the owner in a rehearsal, alerts reach the owner and the backup, replay was performed by the owner, access was reviewed, the freshness message is visible to users, the cost bound is monitored.
5. **Plan adoption**: who uses the output, what they stop using and when, what training or explanation they need, and the condition under which the old artifact is retired.
6. **Schedule follow-ups**: dated reviews with the question each answers, and the open risks carried into them.
7. **State what the handoff does not include**: capabilities, plants, writes, support commitments nobody has agreed.

Evidence to collect: the owner table with acknowledgements, the dependency map, the readiness checklist with the date each item was observed, the adoption plan with retirement conditions, and the follow-up schedule.

Deeper: the retained lessons [Write follow-ups people can act on](#/lesson/dbxfe-m12-l02), [Assemble the customer engagement](#/lesson/dbxfe-m12-l03) and [Move from discovery to decision](#/lesson/dbxfe-m01-l03), and [Production operations, observability and recovery](#/module/dbxfe-operations) for ownership, runbooks and recovery objectives.

<!-- section:example -->

**Fictional worked example: handing the Cinderline plant-one quality path to its operating team after the second five-day run.** Names, dates and statuses are fictional.

### Components and owners

| Component | Owner | Backup | Acknowledged |
|---|---|---|---|
| Nightly job `quality-nightly` | Named engineer (operator) | Data lead | Operator yes; data lead conditional on a second engineer by month end |
| Accepted-inspection table and metric definition | Quality lead (meaning); data lead (schema) | None for meaning | Both yes |
| Morning report | Operations analyst | Operations director | Analyst yes; director not asked yet |
| Runbook and alerts | Operator | Data lead | Yes |
| Pipeline identity and grants | Security lead | Data lead | Security lead yes, with a quarterly review condition |
| Reconciliation and ledger records | Data lead | None | Yes |
| Old stored procedure (fallback until day 30) | DBA | None | Yes |

### Dependencies

Weekly CSV approvals from the quality lead, with a named cover during her absence (not yet named); CDC permission on the inspections table, granted for the pilot and expiring at quarter end unless renewed by the DBA; the workspace region and connectivity pattern, owned by the security lead's review, which closed on day 12 for this plant only; the planning budget, which expires with the pilot and needs a sponsor decision for continued operation; the platform's scheduled maintenance windows, which nobody on the team currently watches.

### Operational readiness

| Item | Observed | Date |
|---|---|---|
| Runbook used by the operator in a rehearsal | Yes, injected failure, 14 minutes | Day 8 |
| Runbook used by the backup | No | Scheduled day 16 |
| Alerts reach owner and backup | Owner yes; backup added day 9 after the escalation | Day 9 |
| Replay performed by the owner | Yes | Day 8 and day 9 |
| Access reviewed | Yes, plant one only | Day 12 |
| Freshness message visible on the report | Yes: "data as of" with the snapshot time | Day 6 |
| Cost bound monitored | No: usage is read manually by the data lead weekly | Open |
| Second failure mode rehearsed | No | Scheduled day 16 |

### Adoption

Users of the output: the 08:00 meeting through the operations analyst's report, and two analyst workbooks that moved to the new table on day 11. The plant sheet's link moved at cutover; the old report stays reachable under its fallback name until day 30. Retirement of the old procedure's report is conditional on twenty working days without a revert and on the third workbook's owner being found; if the owner is not found by day 25, the procedure keeps running and the retirement decision moves to the next review. Training was one session for the operations analyst and a written note for the two workbook owners; the quality lead asked for a one-page explanation of the quarantine reasons, which is owed.

### Follow-ups

Day 16: backup rehearsal and second failure mode; question answered: can someone other than the operator recover the path? Day 25: third workbook and retirement decision. Quarter end: CDC permission renewal and the security lead's quarterly access review. Sponsor decision on continued operation before the planning budget lapses, with the illustrative model's caveats attached.

### Open risks carried forward

One operator with a conditional backup; no automated cost monitoring; the quality lead's approval cover unnamed; maintenance windows unwatched.

### Not included

Plants two and three; sensor data; any ERP write; the maintenance assistant; any support commitment from outside the customer's team, which nobody has agreed.

<!-- section:template -->

### Components and owners

| Component | Owner | Backup | Acknowledged (yes / no / conditional on what) |
|---|---|---|---|
| Pipelines, tables and their meaning, reports, runbooks and alerts, identities and grants, records, retained fallbacks | | | |

### Dependencies

| Dependency | Provided by | Expires or renews when | Status |
|---|---|---|---|
| Approvals, permissions, schedules held elsewhere, budget, environment ownership, platform maintenance | | | |

### Operational readiness

| Item | Observed (what happened, not "done") | Date | Open? |
|---|---|---|---|
| Runbook used by owner; runbook used by backup; alerts reach both; replay by owner; access reviewed; freshness visible to users; cost bound monitored; second failure mode rehearsed | | | |

### Adoption

- **Who uses the output; what they stop using and when; training or explanation owed; the retirement condition for each old artifact and what happens if it is not met.**

### Follow-ups

| Date or condition | Question this review answers | Owner |
|---|---|---|

### Open risks carried forward

- **Each with the review that will look at it.**

### Not included

- **Capabilities, populations, writes and support commitments that this handoff does not cover.**

<!-- section:limits -->

A handoff plan establishes who has agreed to own what, which readiness items were observed and on which date, and what remains open; it does not establish that the path will be operated well, only that the conditions for operating it were checked once. An acknowledged owner without a backup is a single point of failure the plan should name rather than resolve on paper. Readiness observed during a pilot may not survive a change of schedule, volume or personnel, which is why the follow-ups carry questions rather than checkmarks. Escalate when a dependency expires before its renewal owner has acted, when an owner withdraws without a replacement, or when users retire the old path on their own before the retirement condition is met.
