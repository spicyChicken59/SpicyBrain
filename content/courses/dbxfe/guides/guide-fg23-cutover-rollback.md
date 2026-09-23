<!-- section:action -->

A cutover plan is a set of conditions and a set of people. Write the conditions so they can be checked, name the people so they can say no, and rehearse the way back.

1. **Entry conditions.** State each one as something a named person can verify: the number of reconciled days and the exception register, access sign-off, an alert and replay rehearsal, a named operator, a communication sent.
2. **Ownership.** Who gives the technical go, who gives the business go, who can pause or revert at any time without asking, and who tells users. One person per role.
3. **Retained path.** What keeps running on the old side, for how long, where users find it, and what it is called so nobody mistakes it for the new one.
4. **Triggers.** The observable conditions that start a rollback: a discrepancy beyond the accepted exceptions, an unavailable report by a named time, an access anomaly. Write them so a tired operator can recognise them.
5. **Steps and data consequences.** The switch steps, the reverse steps, and what happens to data entered or decisions made during the window.
6. **Recovery test.** Rehearse the rollback as a sequence with expected outputs and a time limit, before cutover day, and record what the rehearsal found.
7. **Cleanup deferral.** Nothing on the old side is deleted until the recovery window ends and the owners accept the cleanup.

Evidence to collect: the checked entry conditions, the role list with names, the rehearsal record with timings and findings, the trigger list, and the communication sent.

Deeper: the retained lesson [Migrate with reconciliation and rollback](#/lesson/dbxfe-m08-l03), [Warehouse and distributed-platform migrations](#/module/dbxfe-warehouse-migration) for the pilot, parallel-run, cutover and rollback sequence, [Production operations, observability and recovery](#/module/dbxfe-operations) for recovery validation, and [Architecture reasoning and migration decisions](#/module/dbxfe-m08).

<!-- section:example -->

**Fictional worked example: switching Cinderline's plant-one morning report to the new path.** This is a read-path cutover. The ERP stays the system of record, the nightly stored procedure keeps running, and only the report users open at 08:00 changes.

### Entry conditions (status on the day before)

| Condition | Verifier | Status |
|---|---|---|
| Five consecutive reconciled days with only accepted exceptions | Data lead | Met: days 6 to 10 after the day-5 fixes; register has one exception (inspector-code backfill) |
| Access review of the new report and its pipeline identity | Security lead | Met, with a note that the analyst group still has read on the old table |
| Alert and replay rehearsal on the new path | Operator | Met on day 8; replay produced the same snapshot id |
| Named operator with a backup | Data lead | Met: operator named; backup named for one week only |
| Business acceptance of the metric and the 06:00 plant-time boundary | Quality lead, operations director | Met in writing |
| Users told the date and the fallback location | Operations analyst | Sent two working days before |

### Ownership

Technical go: the data lead. Business go: the operations director. Pause or revert at any time: the operator, who does not need permission to revert and does need to say so within fifteen minutes. User communication: the operations analyst. Access changes: the security lead.

### Retained path

The stored procedure keeps running nightly for twenty working days. The old report stays at its existing location, renamed "Morning defect report (fallback until day 30)". The plant sheet's link is the only thing that moves. Analyst workbooks that read the old table directly were inventoried; two do, and their owners chose to stay on the old table for the recovery window.

### Triggers

Revert if: the new report is not available by 07:30 plant time; the day's inspected or defective total differs from the old path by more than the exception register explains; the security lead reports an access anomaly; or the operator cannot reach the pipeline logs. Any one trigger is enough; the operator reverts first and diagnoses second.

### Steps

Switch: repoint the plant sheet link; post the notice; record the snapshot id shown at 08:00. Revert: repoint the link back; post the notice naming which day's data users saw and from which path; record the snapshot id; open an escalation packet with the trigger and the observations. Data consequence: nothing is written through the report, so no user data is stranded; dispositions entered in the exception review application during the window are unaffected because they live in their own store.

### Recovery test (rehearsed on day −2)

The operator switched the link at 09:10, stopped the new pipeline deliberately at 09:20 to simulate an unavailable report, recognised the trigger at 09:31 from the alert, reverted the link at 09:34 and confirmed the old report showed day −3's totals, matching the register. Total time from trigger to usable fallback: 14 minutes against a 30-minute target. Finding: the plant sheet cached the old link target in two browsers; users must reload, and the notice now says so. Second finding: the alert went to the operator only; the backup was added.

### Unknowns

One analyst workbook of unknown ownership may read the new table by name; if it does, a revert leaves it on the new path. The operations analyst owns finding its owner before cutover day; if not found, cutover proceeds with that workbook listed as a known non-reverting consumer.

### Decision

Proceed, conditional on the workbook question being closed or listed, with the rehearsal record attached and the twenty-day retained path unchanged.

<!-- section:template -->

### Scope

- **What switches** (read path, write path, both) and **what stays** (system of record, old jobs).

### Entry conditions

| Condition | How it is verified | Verifier | Status (met / not met / proposed) | Evidence |
|---|---|---|---|---|

### Ownership

- **Technical go:** name. **Business go:** name. **Pause or revert without asking:** name, and the time within which they must announce it. **User communication:** name. **Access changes:** name.

### Retained path

- **What keeps running, for how long, where users find it, what it is called, and which consumers stay on it deliberately.**

### Triggers

- **Each as an observable condition with a time or a threshold**, and the rule that any one is sufficient.

### Steps

- **Switch steps** in order. **Revert steps** in order. **Data consequences:** what users entered or decided during the window and how it is handled. **Communication text** for both directions.

### Recovery test

- **Date, sequence executed, expected outputs, observed outputs, time from trigger to usable fallback against the target, findings and fixes.**

### Cleanup deferral

- **What is not deleted, until when, and who accepts the cleanup.**

### Unknowns and decision

<!-- section:limits -->

This plan establishes that the conditions you named were checked, that named people hold the decisions, and that a rollback was rehearsed once with the outputs you expected. It cannot establish that every consumer of the old path was found; an inventory gap becomes a non-reverting consumer, and the plan should list it rather than assume it away. A rehearsal proves the sequence on the day it ran, with the data it had. A write-path cutover, or a transfer of operational authority, needs a separate design with conflicting-write handling that this guide does not cover. Escalate when an entry condition is marked met by the person who benefits from proceeding, when a trigger fires and the reversion does not restore a usable report within the target, or when cleanup of the old path is requested before the recovery window ends.
