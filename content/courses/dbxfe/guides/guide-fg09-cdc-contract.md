<!-- section:action -->

Write the contract before the first incremental load and have the source owner read it; a resolver built on an assumed ordering field will quietly publish the wrong current state.

1. **Name the keys**: the business key that identifies an entity across changes, the delivery identifier that identifies one arrival, and any surrogate the target adds. State which is immutable.
2. **Name the ordering field and its owner**: a source revision, a sequence, a commit timestamp. Arrival order is not business order; say what the field means and who validates it.
3. **Decide what a deletion is**: an explicit delete event, a tombstone flag, or nothing. Absence from a later batch is never a delete unless the source owner has said the batch is a complete snapshot.
4. **Classify duplicates**: an identical redelivery (count once), redundant evidence of the same key and revision (count once, retain both), and a conflict (same key and revision, different payload). Each gets a rule.
5. **Write the conflict policy**: whether publication is blocked or the record is withheld, who adjudicates, how the adjudication is recorded, and whether the source is corrected.
6. **Choose the target shape**: current state only, or history with valid-from and valid-to, and how late corrections and tied revisions are represented.
7. **Test with an authored sequence** covering every rule, with the expected output written by hand.

Go deeper: [ingestion, quality and changing records](#/module/dbxfe-m04), [identity, ordering and incremental inputs](#/lesson/dbxfe-m04-l02), [duplicates, invalid records and conflicts](#/lesson/dbxfe-record-resolution), [version-aware updates and replay](#/lesson/dbxfe-versioned-updates), [declarative pipelines and change-data processing](#/module/dbxfe-pipelines) for sequence keys and history tables, and [Delta writes and MERGE](#/module/dbxfe-delta-writes) for what a guarded update does with multiple source matches.

<!-- section:example -->

### Change-data contract: Cinderline Components (fictional), inspection corrections

Version 1, proposed; the quality lead has agreed the ordering rule and the conflict policy in conversation and not yet in writing.

#### Keys

`inspection_id` is the business key and persists through corrections; the quality lead confirms it is never reused. `event_id` identifies one delivered payload and is immutable; the same `event_id` with a different payload is a conflict, not a correction. The target adds no surrogate for the pilot.

#### Ordering

`version` is a positive integer assigned by the ERP when a correction is approved. Version 3 replaces version 2 completely; it is not a delta of quantities. Arrival order is ignored for ordering because correction files can arrive out of sequence and a nightly rerun re-reads them. A record with a missing, zero or non-integer version cannot be ordered and is quarantined. The DBA has not yet confirmed that the ERP never assigns the same version twice for one inspection; until confirmed, equal versions are treated as described under conflicts.

#### Deletions

The source has no delete event. An inspection voided by the plant is delivered as a new version with zero inspected units, which the resolver treats as a replacement state, not a deletion. Absence from a later correction file means nothing, because correction files contain only approved changes. Absence from the nightly inspection export is not treated as a deletion for the pilot; the DBA is asked whether rows are ever physically removed.

#### Duplicates

| Case | Rule |
|---|---|
| Same `event_id`, identical payload | Identical redelivery; retained in raw, counted once |
| Different `event_id`, same key, same version, identical quantities | Redundant evidence; both retained, one state |
| Same key, same version, different quantities | Conflict; see policy |
| Same `event_id`, different payload | Conflict; see policy |
| Same key, lower version than accepted | Older revision; retained, ignored for current state |

#### Conflict policy

A conflict withholds the affected inspection from the accepted current state and lists it in `quarantine.conflicts` with both payloads and their arrival times. It does not block publication of the rest of the plant's rate; the published report shows the count of withheld inspections beside the rate. The quality lead adjudicates by approving a new, higher version in the ERP, which arrives through the ordinary path; no manual edit of the accepted table is permitted. Adjudications are recorded in the quarantine table with the adjudicator and date. Two conflicts in a day for the same line trigger a message to the quality lead before the morning report.

#### Target shape

For the pilot, current state only: one row per `inspection_id` with the highest valid version. History is retained implicitly in raw and in table history, not modelled. When restatement reporting is required, a history table with valid-from and valid-to by version is added; tied versions cannot occur under this contract because equal versions are conflicts.

#### Test sequence, expected output authored by hand

Arrivals: `ev1` A v1 10/1; `ev1` A v1 10/1 again; `ev2` B v1 with inspected units −3; `ev3` A v2 12/1; `ev4` C v1 8/0; `ev5` A v3 14/1; `ev5` A v3 15/1; `ev6` A with no version 16/1; `ev7` A v2 12/1.

Expected: accepted rows are C v1 8/0 only, because A is withheld by the `ev5` conflict; B is quarantined as invalid; `ev6` is quarantined as unorderable; `ev7` is redundant evidence for an already superseded version. Published rate for the day: 0 of 8 inspected units, with two inspections withheld and one invalid, and the counts printed beside it. If the conflict were adjudicated by a v4 for A of 14/1, A would enter as 14/1 and the rate would be 1 of 22.

#### Conclusion

The contract is executable and its test sequence has a hand-authored answer, so the resolver can be checked against something it did not produce. Two facts remain the source owner's to confirm: version uniqueness and physical deletion. Until then the contract treats both conservatively and says so in the published exclusion counts.

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

- What is withheld and what still publishes; who adjudicates and through which path; how adjudications are recorded; what triggers a message and to whom.

#### Target shape

- Current state, history, or both; how late corrections and restatements are represented; whether tied ordering values are possible.

#### Test sequence

- An authored arrival list covering every rule above, and its expected output written by hand before the resolver runs.

<!-- section:limits -->

The contract makes resolution rules explicit and testable; it cannot establish that the ordering field behaves as the source owner believes, that versions are unique, or that deletes never happen, each of which needs the owner's written confirmation and a test against real deliveries. It describes business resolution, not connector semantics: what a managed connector emits for an update or delete depends on the source, its version and the connector, and must be verified separately. A hand-authored test proves the resolver matches the contract, not that the contract matches the source. Escalate when the source owner cannot say what a delete looks like, when conflicts occur more often than the adjudication path can absorb, or when someone proposes resolving conflicts by arrival time.
