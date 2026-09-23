<!-- section:action -->

Decide what happens to a bad record before the first one arrives. A response designed during an incident will be whatever clears the error fastest, and that is usually deletion.

1. **List the failure classes the checks can detect**: invalid values, missing identity, unorderable records, conflicts, late corrections, a missing or empty delivery, a schema change. Each class gets its own response; "quality issue" is not a class.
2. **Define quarantine as a place with an owner**: where the record goes, what is kept with it (the raw payload, the arrival time, the reason), who may read it, and how it leaves.
3. **Define the unresolved state**: what the published output shows while a record is quarantined, in counts and in words, so a reader can see that something is withheld rather than absent.
4. **Decide the publication rule per class**: publish with the exclusion disclosed, hold the new report and show the last verified one as stale while an entity is unresolved, or hold the whole output. Tie the choice to what a wrong number would cause.
5. **Define resolution paths**: who acts, through which system, and how the resolution re-enters the pipeline. A manual edit of the published table is not a path.
6. **Rehearse one case end to end** and write down what the reader of the report saw at each step.

Go deeper: [ingestion, quality and changing records](#/module/dbxfe-m04), [duplicates, invalid records and conflicts](#/lesson/dbxfe-record-resolution), [orchestration and recoverable execution](#/module/dbxfe-orchestration) for quality gates that stop a run, [orchestration, failure and reconciliation](#/lesson/dbxfe-m04-l03), and [declarative pipelines](#/module/dbxfe-pipelines) for expectations that drop, warn or fail.

<!-- section:example -->

### Quality response: Cinderline Components (fictional), North plant nightly resolution

Agreed in conversation with the quality lead and the operations director; operator steps reviewed by the data lead; rehearsed once on synthetic records.

#### Failure classes and responses

| Class | Detected by | Response | Publication |
|---|---|---|---|
| Invalid or unorderable row; the inspection was never valid | Row check | Quarantine; exclude the inspection | Publish; disclose the count |
| Invalid or unorderable latest version; the inspection was valid before | Resolver, against retained history | Quarantine; inspection unresolved | Hold new report; last verified stale |
| Missing or reused inspection identifier | Row check; resolver against history if reused | Quarantine | Publish; disclose the count |
| Conflict (one key and version, or one delivery, with two payloads) | Resolver | Quarantine both payloads; inspection unresolved | Hold new report; last verified stale |
| Late correction to an earlier day | Resolver | Apply in version order; restate that day | Publish; mark the restated day |
| Empty or missing nightly export | Delivery check | Do not run the resolver | Hold all output; banner on yesterday's report |
| Column added or renamed in the export | Schema check | Do not run the resolver | Hold all output; page the operator |

All output is held when the input cannot be trusted as a set; a new report, while any inspection's current state is unresolved. The operations director accepted a rate that excludes and discloses never-valid records as more useful at 8 a.m. than none; the quality lead asked that a conflict block the report rather than pick a side.

#### Quarantine

Table `quarantine.records` holds the raw payload, arrival time, failure class, rule fired and resolution status; only the quality-stewards group reads it. A record leaves when a higher version for its inspection arrives through the ordinary path, with any adjudication recorded, or when the steward closes it as "source corrected" or "will not fix" with a reason. Nothing is ever deleted.

#### The unresolved state as the reader sees it

Beside each line's rate: inspections accepted, inspections excluded (never valid), records quarantined, and a mark on any day restated by a late correction. When a new report is held, the page shows the last verified day labelled stale, with the reason ("conflict under adjudication", "not updated: export missing") and when the owner was notified. The analyst asked for counts rather than a footnote, because the workbook argument is about whether rows are missing.

#### Resolution paths

Invalid rows and missing identifiers go back to the plant through the quality lead, who approves a higher version in the corrections file (corrections never touch the ERP) and, for a conflict, records which payload was mistyped. A missing export is the DBA's; the operator then reruns the night. A schema change stops the pipeline until the data team has reviewed the mapping; the DBA's promise to announce export changes a week ahead is not yet a process.

#### Notification

A held report: the quality lead (conflict, unresolved inspection) or the operator (missing export, schema change) at detection, and the plant analyst by 7:30 a.m., before the meeting. Quarantined rows on a published day: the quality lead, in the morning summary.

#### Rehearsal

Synthetic night with one negative quantity on a new inspection, one conflict and a correction for two days earlier. The resolver quarantined the negative row, applied the correction and held the new report on the conflict: the page showed the previous day labelled stale, and the held candidate read 19 accepted, 1 unresolved, 1 excluded. The steward saw both payloads and arrival times, recorded which was mistyped and approved a higher version in the synthetic corrections file; the next run published 20 accepted, 1 excluded, the earlier day marked restated. Detection to published report: two runs, or one night in production. Not rehearsed: a missing export, until an operator is named.

#### Conclusion

Every class has a response, an owner and a visible unresolved state; a bad record cannot disappear or silently change the rate. Open, not done: the missing-export rehearsal and the DBA's schema-change promise.

<!-- section:template -->

### Quality response

#### Failure classes

| Class (what is wrong) | Detected by (row check, resolver, delivery check, schema check) | Response (quarantine row, exclude entity, mark entity unresolved, hold output) | Publication rule and disclosure |
|---|---|---|---|

#### Quarantine

- Location; what is stored with each record (raw payload, arrival time, class, rule, status); who may read it; how a record leaves; whether anything is ever deleted.

#### The unresolved state

- What the published output shows, in counts and in words, while records are excluded or unresolved or the output is held; what the reader sees when nothing new is published.

#### Resolution paths

- Per class: who acts, through which system, how the fix re-enters the pipeline, and the paths that are forbidden.

#### Notification

- What triggers a message, to whom, and by when relative to the decision the output serves.

#### Rehearsal

- The case run, what each role saw at each step, time to resolution, and the cases not yet rehearsed with the reason.

<!-- section:limits -->

This guide establishes what happens to records the checks can detect; it cannot establish that the checks detect everything, and a record that passes every rule can still be wrong at the source. The publication rules are a business agreement about the cost of a wrong number, so they need the operations owner's acceptance, not only the data team's. Quarantine holds records; it does not adjudicate them, and a resolution path that depends on a person is only as fast as that person. A rehearsal on synthetic records shows the mechanism, not production timing. Escalate when a class has no owner for its resolution, when someone proposes deleting quarantined records to clear a count, or when the whole output has been held for longer than the decision it serves can wait.
