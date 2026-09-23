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

Deeper: the retained lesson [Migrate with reconciliation and rollback](#/lesson/dbxfe-m08-l03), [Warehouse and distributed-platform migrations](#/module/dbxfe-warehouse-migration) for the pilot, parallel-run, cutover and rollback sequence, [Production operations, observability and recovery](#/module/dbxfe-operations) for recovery validation, and [Architecture and migration](#/module/dbxfe-m08).

<!-- section:example -->

**Fictional worked example: switching Cinderline's plant-one morning report to the new path.** A read-path cutover: the ERP stays the system of record, the nightly stored procedure keeps running, and only the report users open at 08:00 changes. Days are pilot days: the second five-day run was days 11 to 15; cutover is day 16.

### Entry conditions (status on day 15)

| Condition | Verifier | Status |
|---|---|---|
| Five consecutive reconciled days with only accepted exceptions | Quality lead | Met: days 11 to 15; register has one exception (inspector-code backfill) |
| Access review of the new report and its pipeline identity | Security lead | Met on day 14, with a note that the analyst group still has read on the old table |
| Alert and replay rehearsal on the new path | Operator | Met on day 8; the platform replay produced the same snapshot id |
| Named operator with a backup | Operations director | Partly met: operator Oskar named; the data lead backs him up for week one of the four-week recovery window only |
| Business acceptance of the metric and the 06:00 plant-time boundary | Quality lead, operations director | Met in writing |
| Users told the date and the fallback location | Operations analyst | Sent on day 14, two working days before |

### Ownership

Technical go: the data lead, who for that reason verifies none of the entry conditions. Business go: the operations director. Pause or revert at any time: the operator, who needs no permission to revert and must say so within fifteen minutes. User communication: the operations analyst. Access changes: the security lead.

### Retained path

The stored procedure keeps running nightly for twenty working days, to day 35. The old report stays at its existing location, renamed "Morning defect report (fallback until day 35)". The plant sheet's link is the only thing that moves. Analyst workbooks that read the old table directly were inventoried; two do, and their owners chose to stay on the old table for the recovery window.

### Triggers

Revert if: the new report is not available by 07:30 plant time; the day's inspected or defective total differs from the old path by more than the exception register explains; the security lead reports an access anomaly; or the operator cannot reach the pipeline logs. Any one trigger is enough; the operator reverts first and diagnoses second.

### Steps

Switch: repoint the plant sheet link; post the notice; record the snapshot id shown at 08:00. Revert: repoint the link back; post the notice naming which day's data users saw and from which path; record the snapshot id; open an escalation packet with the trigger and the observations. Data consequence: nothing is written through the report, so no user data is stranded; dispositions in the exception review application live in their own store and are unaffected.

### Recovery test (rehearsed on day 14, two days before cutover)

The operator switched the link at 09:10, stopped the new pipeline deliberately at 09:20 to simulate an unavailable report, recognised the trigger at 09:29 from the alert, reverted the link at 09:32 and confirmed the old report showed day 13's totals, matching the register. Total time from trigger to usable fallback: 12 minutes against a 30-minute target. Finding: the plant sheet cached the old link target in two browsers; users must reload, and the notice now says so.

### Cleanup deferral

The procedure, the old table and the fallback report are not deleted before day 35. The DBA proposes it; the operations director and the quality lead accept it in writing, only after the two workbooks on the old table have moved and the third workbook's owner is found.

### Unknowns

A third analyst workbook of unknown ownership reads the old table. A revert leaves it untouched, but cleanup would break it silently, so it blocks cleanup; the operations analyst owns finding its owner by day 25.

### Decision

Proceed on day 16 with the rehearsal record attached and the retained path unchanged. The backup gap after week one is a named risk, owned by the operations director and reviewed on day 20.

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
