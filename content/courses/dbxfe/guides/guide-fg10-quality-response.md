<!-- section:action -->

Decide what happens to a bad record before the first one arrives. A response designed during an incident will be whatever clears the error fastest, and that is usually deletion.

1. **List the failure classes the checks can detect**: invalid values, missing identity, unorderable records, conflicts, late corrections, a missing or empty delivery, a schema change. Each class gets its own response; "quality issue" is not a class.
2. **Define quarantine as a place with an owner**: where the record goes, what is kept with it (the raw payload, the arrival time, the reason), who may read it, and how it leaves.
3. **Define the unresolved state**: what the published output shows while a record is quarantined, in counts and in words, so a reader can see that something is withheld rather than absent.
4. **Decide the publication rule per class**: publish with the exclusion disclosed, hold the affected entity, or hold the whole output. Tie the choice to what a wrong number would cause.
5. **Define resolution paths**: who acts, through which system, and how the resolution re-enters the pipeline. A manual edit of the published table is not a path.
6. **Rehearse one case end to end** and write down what the reader of the report saw at each step.

Go deeper: [ingestion, quality and changing records](#/module/dbxfe-m04), [duplicates, invalid records and conflicts](#/lesson/dbxfe-record-resolution), [orchestration and recoverable execution](#/module/dbxfe-orchestration) for quality gates that stop a run, [orchestration, failure and reconciliation](#/lesson/dbxfe-m04-l03), and [declarative pipelines](#/module/dbxfe-pipelines) for expectations that drop, warn or fail.

<!-- section:example -->

### Quality response: Cinderline Components (fictional), North plant nightly resolution

Agreed in conversation with the quality lead and the operations director; the data lead has reviewed the operator steps. Rehearsed once on synthetic records.

#### Failure classes and responses

| Class | Detected by | Response | Publication |
|---|---|---|---|
| Invalid quantity (negative or non-numeric units) | Row check | Quarantine the row | Publish; disclose the count |
| Missing or reused inspection identifier | Row check | Quarantine the row | Publish; disclose the count |
| Unorderable record (missing or invalid version) | Row check | Quarantine the row | Publish; disclose the count |
| Conflict (same key and version, different payload) | Resolver | Withhold the inspection; quarantine both payloads | Publish the rest; disclose withheld inspections by line |
| Late correction to an earlier business day | Resolver | Apply in version order; restate that day | Publish today; mark the restated day |
| Empty or missing nightly export | Delivery check | Do not run the resolver | Hold the whole output; keep yesterday's report visible with a banner |
| Column added or renamed in the export | Schema check | Do not run the resolver | Hold the whole output; page the operator |

The whole output is held only when the input cannot be trusted as a set. A single bad row never holds the plant's rate, because the operations director confirmed that a rate with disclosed exclusions is more useful at 8 a.m. than no rate.

#### Quarantine

Table `quarantine.records` holds the raw payload as delivered, the arrival time, the failure class, the rule that fired and a resolution status. Read by the quality-stewards group only. A record leaves quarantine when a new version for its inspection arrives through the ordinary path and supersedes it, or when the steward marks it "closed, source corrected" or "closed, will not fix" with a reason. Records are never deleted from quarantine.

#### The unresolved state as the reader sees it

Beside each line's rate the report prints: inspections accepted, inspections withheld (conflict), records quarantined (invalid or unorderable), and a restatement mark on any day changed by a late correction. When the whole output is held, the report shows the last published day with the words "not updated: export missing" and the time the operator was notified. The analyst asked specifically for the counts rather than a footnote, because the workbook argument is about whether rows are missing.

#### Resolution paths

Invalid quantities and missing identifiers go back to the plant through the quality lead, who has the ERP corrected; the corrected row arrives as a new version. Conflicts are adjudicated by the quality lead approving a higher version in the ERP. A missing export is the DBA's; the operator reruns the night once the export exists. A schema change stops the pipeline until the data team has reviewed the mapping; the DBA has agreed to announce export changes a week ahead, which is a promise and not yet a process.

#### Rehearsal

Synthetic night with one negative quantity, one conflict and a correction for two days earlier. The resolver quarantined the negative row, withheld the conflicted inspection with both payloads, applied the correction and marked the earlier day restated. The report showed 19 inspections accepted, 1 withheld, 1 quarantined, one restated day. The steward opened the quarantine, saw the conflict's two payloads and arrival times, and approved a new version in the synthetic ERP; the next run accepted it and the withheld count dropped to zero. Time from detection to resolved report: two runs, or one night in production. The missing-export case was not rehearsed because the operator is not yet named.

#### Conclusion

Every class has a response, an owner and a visible unresolved state; a bad record cannot disappear and cannot silently change the rate. Two gaps: the missing-export rehearsal waits on a named operator, and the schema-change announcement is a promise. Both are recorded as open, not as done.

<!-- section:template -->

### Quality response

#### Failure classes

| Class (what is wrong) | Detected by (row check, resolver, delivery check, schema check) | Response (quarantine row, withhold entity, hold output) | Publication rule and disclosure |
|---|---|---|---|

#### Quarantine

- Location; what is stored with each record (raw payload, arrival time, class, rule, status); who may read it; how a record leaves; whether anything is ever deleted.

#### The unresolved state

- What the published output shows, in counts and in words, while records are withheld or the output is held; what the reader sees when nothing new is published.

#### Resolution paths

- Per class: who acts, through which system, how the fix re-enters the pipeline, and the paths that are forbidden.

#### Notification

- What triggers a message, to whom, and by when relative to the decision the output serves.

#### Rehearsal

- The case run, what each role saw at each step, time to resolution, and the cases not yet rehearsed with the reason.

<!-- section:limits -->

This guide establishes what happens to records the checks can detect; it cannot establish that the checks detect everything, and a record that passes every rule can still be wrong at the source. The publication rules are a business agreement about the cost of a wrong number, so they need the operations owner's acceptance, not only the data team's. Quarantine holds records; it does not adjudicate them, and a resolution path that depends on a person is only as fast as that person. A rehearsal on synthetic records shows the mechanism, not production timing. Escalate when a class has no owner for its resolution, when someone proposes deleting quarantined records to clear a count, or when the whole output has been held for longer than the decision it serves can wait.
