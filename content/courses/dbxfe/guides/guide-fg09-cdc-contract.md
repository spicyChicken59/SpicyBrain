<!-- section:action -->

Write the contract before the first incremental load and have the source owner read it; a resolver built on an assumed ordering field will quietly publish the wrong current state.

1. **Name the keys**: the business key that identifies an entity across changes, the delivery identifier that identifies one arrival, and any surrogate the target adds. State which is immutable.
2. **Name the ordering field and its owner**: a source revision, a sequence, a commit timestamp. Arrival order is not business order; say what the field means and who validates it.
3. **Decide what a deletion is**: an explicit delete event, a tombstone flag, or nothing. Absence from a later batch is never a delete unless the source owner has said the batch is a complete snapshot.
4. **Classify duplicates**: an identical redelivery (count once), redundant evidence of the same key and revision (count once, retain both), and a conflict (same key and revision, different payload). Each gets a rule.
5. **Write the conflict policy**: what a conflict blocks and what the reader sees meanwhile (the course's reliable-data policy blocks the new report and keeps the last verified one visible, labelled stale), who adjudicates, how the adjudication is recorded, and whether the source is corrected.
6. **Choose the target shape**: current state only, or history with valid-from and valid-to, and how late corrections and tied revisions are represented.
7. **Test with an authored sequence** covering every rule, with the expected output written by hand.

Go deeper: [ingestion, quality and changing records](#/module/dbxfe-m04), [identity, ordering and incremental inputs](#/lesson/dbxfe-m04-l02), [duplicates, invalid records and conflicts](#/lesson/dbxfe-record-resolution), [version-aware updates and replay](#/lesson/dbxfe-versioned-updates), [declarative pipelines and change-data processing](#/module/dbxfe-pipelines) for sequence keys and history tables, and [Delta writes and MERGE](#/module/dbxfe-delta-writes) for what a guarded update does with multiple source matches.

<!-- section:example -->

### Change-data contract: Cinderline Components (fictional), inspection corrections

Version 1, proposed; the quality lead agreed the ordering rule and the conflict policy in conversation, not yet in writing.

#### Keys

`inspection_id` is the business key and persists through corrections; the quality lead confirms it is never reused. `event_id` identifies one delivered payload and is immutable. The target adds no surrogate for the pilot.

#### Ordering

`version` is a positive integer: the nightly export delivers an inspection as version 1; each approved correction, which never touches the ERP, carries a higher one in the corrections file. Version 3 replaces version 2 completely; it is not a delta. Arrival order is ignored: correction files arrive out of sequence and reruns re-read them. A record with a missing, zero or non-integer version is quarantined as unorderable; one whose quantities are not non-negative integers with defective at most inspected, as invalid. A re-typed row has already reused a version once, so equal versions are handled under conflicts.

#### Deletions

The source has no delete event. A voided inspection arrives as a new version with zero inspected units: a replacement state, not a deletion. Absence from a correction file means nothing; those files carry only approved changes. Absence from the nightly export is not a deletion; the DBA is asked whether rows are ever physically removed.

#### Duplicates

| Case | Rule |
|---|---|
| Same `event_id`, identical payload | Redelivery; retained, counted once |
| Different `event_id`, same key, same version, identical quantities | Redundant evidence; both retained, one state |
| Same key, same version, different quantities | Conflict; see policy |
| Same `event_id`, different payload | Conflict; see policy |
| Same key, lower version than accepted | Older revision; retained, not current |

#### Conflict policy

A conflict blocks any new report. The last verified snapshot stays visible, labelled stale with the reason; with no earlier snapshot the state is "blocked, no snapshot". An inspection whose latest version is invalid after it had a valid state blocks in the same way. Candidate totals meanwhile are diagnostic, never a published rate. Both payloads go to `quarantine.conflicts` with arrival times, and the quality lead is messaged before the morning report. The quality lead adjudicates by recording there which payload was mistyped and approving a higher version through the corrections file; nobody edits the accepted table. Publication resumes only when both exist, because a later version alone does not clear a conflict in retained history.

#### Target shape

For the pilot, current state only: one row per `inspection_id` with the highest valid version. History stays in raw and table history until restatement reporting needs a valid-from, valid-to table by version. Equal versions either conflict or, with identical quantities, collapse to one state, so no tie reaches the target.

#### Test sequence, expected output authored by hand

Arrivals: `ev1` A v1 10/1; `ev1` A v1 10/1 again; `ev2` B v1 −3/1; `ev3` A v2 12/1; `ev4` C v1 8/0; `ev5` A v3 14/1; `ev5` A v3 15/1; `ev6` E, no version, 16/1; `ev7` A v2 12/1; `ev8` A v3 15/1; `ev9` D v2 0/0; `ev10` D v1 5/0.

Expected: `ev1` counts once; `ev7` is redundant evidence for A's superseded v2. B (invalid) and E (unorderable) are quarantined and, never having been valid, excluded and disclosed. `quarantine.conflicts` holds an event conflict (`ev5`, two payloads) and a key-and-version conflict (A v3: 14/1 against 15/1 in `ev5` and `ev8`), so A is unresolved. D v2 voids D at 0/0; `ev10` is older and ignored. The candidate, C 8/0 plus D 0/0, is a diagnostic 0 of 8, not a published rate: the state is "blocked, no snapshot", with A unresolved and B and E excluded beside it. If the quality lead records the 15/1 payloads as mistyped and approves A v4 14/1, A enters as 14/1 and the published rate is 1 of 22.

#### Conclusion

The test sequence has a hand-authored answer, so the resolver is checked against something it did not produce. Still to confirm: whether approval can stop a re-typed row reusing a version (the quality lead) and whether rows are ever physically removed (the DBA); until then both are treated conservatively.

<!-- section:template -->

### Change-data contract

#### Keys

- Business key (what it identifies, whether it is ever reused); delivery identifier (immutable or not); any target surrogate and why.

#### Ordering

- The field, its type, who assigns it, what a higher value means (replacement or delta), how unorderable records are handled, and what the source owner still has to confirm.

#### Deletions

- What a delete looks like in this source, or that none exists; what absence from a batch means; what a voided or zeroed entity looks like.

#### Duplicates

| Case (keys and payload relationship) | Rule (count once, retain both, conflict, ignore) |
|---|---|

#### Conflict policy

- What a conflict blocks and what the reader sees meanwhile; who adjudicates and through which path; how adjudications are recorded and when publication resumes; what triggers a message and to whom.

#### Target shape

- Current state, history, or both; how late corrections and restatements are represented; whether tied ordering values are possible.

#### Test sequence

- An authored arrival list covering every rule above, and its expected output written by hand before the resolver runs.

<!-- section:limits -->

The contract makes resolution rules explicit and testable; it cannot establish that the ordering field behaves as the source owner believes, that versions are unique, or that deletes never happen, each of which needs the owner's written confirmation and a test against real deliveries. It describes business resolution, not connector semantics: what a managed connector emits for an update or delete depends on the source, its version and the connector, and must be verified separately. A hand-authored test proves the resolver matches the contract, not that the contract matches the source. Escalate when the source owner cannot say what a delete looks like, when conflicts occur more often than the adjudication path can absorb, or when someone proposes resolving conflicts by arrival time.
