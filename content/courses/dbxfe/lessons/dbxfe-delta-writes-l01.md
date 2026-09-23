<!-- section:dbxfe-delta-writes-l01-outcome -->

After this lesson you can move one Delta table through a pipeline's writes and say what each does to rows, files, history and clients: which MERGE clause acts on which row, why an omitted key survives while a snapshot retires rows inside its scope, how Delta refuses duplicate matches and a guard fixes them, how to read the change data feed, enforcement versus evolution, and the maintenance decisions around OPTIMIZE, VACUUM, liquid clustering and predictive optimization. Every number comes from Lab L05, a local open-source run on synthetic data.

<!-- section:dbxfe-delta-writes-l01-start -->

[Delta tables: files, log, and snapshots](#/lesson/dbxfe-m03-l02) explains why a version selects files and the folder is not the table; this lesson builds on it. [Version-aware updates and replay](#/lesson/dbxfe-versioned-updates) sets the update policy (newer replaces, older never overwrites, equal revisions with different values conflict); here that policy runs on a real table and extends to deletes, change records, schema and maintenance.

The running example is Cinderline Components' inspection table: inspection_id, plant, inspected, defective and revision, where higher is newer and 0 marks a stale replay.

<!-- section:dbxfe-delta-writes-l01-clauses -->

A MERGE joins a source to a target on a key and sorts every row into three cases: a matched source row goes to WHEN MATCHED (update or delete), an unmatched source row to WHEN NOT MATCHED (insert only), and a target row no source row matches to WHEN NOT MATCHED BY SOURCE (update or delete), which exists only if written. A row no clause selects keeps its values.

Day 2 is an incremental delivery: C's revision 2 and a new lot D. A is not mentioned and the statement has no delete-by-source clause, so A survives: silence in an incremental delivery is not a delete. Version 4 reported one update, one insert, no delete.

Absence means something only in a complete snapshot, and only inside its scope. South's snapshot lists D alone, so South's E is retired; North's A and C were never described:

```sql
WHEN NOT MATCHED BY SOURCE AND t.plant = 'South' THEN DELETE
```

Version 6 deleted one row. The same clause without the plant condition, run on a copy of version 5, deleted three and left only D.

<!-- section:dbxfe-delta-writes-l01-duplicates -->

Day 3 carried two rows for D (revisions 2 and 3), a stale replay of A at revision 0 and a new E. Both D rows match target D, so the update is ambiguous and Delta refused the whole statement with DELTA_MULTIPLE_SOURCE_ROW_MATCHING_TARGET_ROW_IN_MERGE: no E, no new version. The same file merged into a copy of version 3, before D existed, was accepted: nothing was matched twice, so both D rows were inserted and A's replay overwrote revision 1. The error protects matched keys only, so de-duplication belongs before every merge.

The fix keeps the highest revision per key with row_number() over inspection_id, then guards the matched clause:

```sql
WHEN MATCHED AND s.revision > t.revision THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
```

Version 5 updated D, inserted E and skipped A, because 0 is not greater than 1. On Databricks, which conditions count toward a duplicate match depends on the runtime; resolve ambiguity before the MERGE either way.

<!-- section:dbxfe-delta-writes-l01-feed -->

A DELETE, or a MERGE delete clause, commits a version that no longer selects the row. Without deletion vectors each file holding a changed row is rewritten whole and the old file is logged as removed but kept, so version 5 still returns E after version 6 deleted it. The bytes leave storage only when VACUUM runs after the retention.

The change data feed records row changes from the commit after it is enabled:

```sql
ALTER TABLE inspections SET TBLPROPERTIES (delta.enableChangeDataFeed = true);
SELECT * FROM table_changes('inspections', 4, 6);
```

Enabled at version 3, it returned seven rows for versions 4 to 6: C's update_preimage and update_postimage and D's insert; D's pre- and post-image and E's insert; E's delete. A read from version 2 was refused with DELTA_MISSING_CHANGE_DATA. Change files sit under _change_data and expire with the table's retention. On Databricks, check which change-feed mode a table uses.

<!-- section:dbxfe-delta-writes-l01-schema -->

Schema enforcement checks every write against the table. F arrived with an inspector column the table lacked, and the append was refused ("A schema mismatch detected when writing to the Delta table") without a commit. A table column missing from a batch is written as null instead, and UPDATE SET * in a MERGE ignores extra source columns unless automatic evolution is on.

Evolution is a decision recorded in a commit; prefer ALTER TABLE ... ADD COLUMNS or the mergeSchema option for one write over the session-wide spark.databricks.delta.schema.autoMerge.enabled. With mergeSchema, version 7 gained inspector, older rows read null and version 6 still reads five columns. Streams reading the table stop at a schema change and must be restarted.

Some changes add table features to the protocol. Enabling the change data feed moved the writer version from 2 to 7 with changeDataFeed listed while readers stayed at 1; CLUSTER BY added clustering and domainMetadata. Writer features bind every writer, reader features every reader, and upgrades cannot simply be undone, so list the clients first.

<!-- section:dbxfe-delta-writes-l01-maintenance -->

OPTIMIZE bin-packs small files into fewer larger ones without changing a row. Version 8 replaced two files with one; a second run committed nothing. The old files stay on disk, so readers of version 7 and time travel are unaffected.

VACUUM is the only command that deletes data files: those no longer referenced and removed longer ago than the retention, seven days by default. It is not automatic in open-source Delta and never deletes log files. The lab's dry run listed no data file, and a RETAIN 0 HOURS request, made only as a dry run, was refused by the safety check. Keep that check on: a retention must outlast the longest reader and stream lag, and it is decided with the table's owners.

Liquid clustering declares keys with CLUSTER BY; OPTIMIZE clusters incrementally and keys can change without rewriting data. It replaces partitioning and ZORDER.

| Capability | Open-source Delta 4.0 | Databricks |
|---|---|---|
| OPTIMIZE, VACUUM, CLUSTER BY, change data feed | yes; you schedule them | yes |
| Automatic clustering keys | no | AUTO on managed tables |
| Predictive optimization | no | Unity Catalog managed tables |

Predictive optimization decides when to run maintenance such as OPTIMIZE and VACUUM, and is enabled, disabled or inherited per catalog and schema. Verify availability, defaults and billing for the actual account.

<!-- section:dbxfe-delta-writes-l01-example -->

Lab L05's run, matching a plain-Python replay:

| Version | Operation | Rows after | Evidence |
|---|---|---|---|
| 0-2 | WRITE, WRITE, UPDATE | A, C | totals 10, 18, 20; the folder sums 30 |
| 3 | SET TBLPROPERTIES | A, C | changeDataFeed added |
| 4 | MERGE, day 2 | A, C, D | 1 update, 1 insert |
| none | MERGE, day 3 as delivered | unchanged | refused, no commit |
| 5 | MERGE, de-duplicated and guarded | A, C, D, E | A's replay skipped |
| 6 | MERGE, South snapshot | A, C, D | 1 delete by source |
| none | append with inspector | unchanged | schema mismatch |
| 7 | WRITE with mergeSchema | A, C, D, F | inspector null for A, C, D |
| 8 | OPTIMIZE | same rows | 2 files removed, 1 added |

<!-- section:dbxfe-delta-writes-l01-exercise -->

Start from version 8 (North: A, C, F; South: D at revision 3). North now sends a complete daily snapshot of its open lots; today it lists A and F. South moves to a change feed with an op column (UPSERT or DELETE) and a revision; today it holds D (UPSERT, revision 4, 17 inspected), the same D row again, and G (DELETE, revision 1), a lot the table never had. A nullable line column arrives next week. An export stream reads the change data feed and can lag ten days. Storage asks for a nightly VACUUM.

Write North's and South's MERGE statements and the rows each changes, choose the schema change for line, and write the VACUUM decision row.

<!-- section:dbxfe-delta-writes-l01-solution -->

North: guard matched updates, insert new keys, and delete by source only inside North (WHEN NOT MATCHED BY SOURCE AND t.plant = 'North' THEN DELETE). C is deleted; A, F and South are untouched. Check the snapshot's row count first so a truncated file cannot retire valid lots.

South: collapse the exact duplicate (same key, revision and values); same-revision rows with different values are a conflict. Then WHEN MATCHED AND s.op = 'DELETE' AND s.revision > t.revision THEN DELETE; WHEN MATCHED AND s.op = 'UPSERT' AND s.revision > t.revision THEN UPDATE; WHEN NOT MATCHED AND s.op = 'UPSERT' THEN INSERT, listing columns so op is not written. D moves to revision 4; G matches nothing and is not inserted, because a delete instruction never creates a row.

line: ALTER TABLE inspections ADD COLUMNS (line STRING) before the first delivery; old rows read null; warn the export stream's owner, since the stream stops at a schema change.

VACUUM: the seven-day default is shorter than the export's ten-day lag, so change files could expire unread. Raise delta.deletedFileRetentionDuration above the lag (say 14 days), run a DRY RUN, then VACUUM nightly at that retention with the check on. The table, export and dashboard owners agree.

<!-- section:dbxfe-delta-writes-l01-mistakes -->

- A delete-by-source clause on an incremental merge: every quiet row disappears.
- A snapshot delete scoped by nothing, or by the wrong column: rows the delivery never covered are retired.
- Treating the multiple-match error as de-duplication: new keys still arrive twice.
- A guard on an unreliable revision.
- A change-feed consumer lagging past the retention.
- Session-wide automatic evolution to rescue one append.
- Enabling a feature without listing every reader and writer.
- Calling DELETE an erasure, or shortening a shared table's retention or disabling its VACUUM safety check: never do either.
- Expecting predictive optimization in open-source Delta.

<!-- section:dbxfe-delta-writes-l01-sources -->

Eight open-source Delta Lake 4.0.0 documentation pages were read in full as Markdown sources at tag v4.0.0 of the delta-io/delta repository on 23 September 2026 (docs.delta.io itself is blocked here), and two Databricks Terraform provider pages at a pinned commit. Databricks pages on MERGE, the change data feed, liquid clustering and predictive optimization were not re-read in this build; their records say so, and Databricks-only statements are marked for verification.

<!-- section:dbxfe-delta-writes-l01-related -->

[Delta tables, commits and snapshots](#/module/dbxfe-delta) for snapshots, commits and concurrency; [Duplicates, invalid records, and conflicts](#/lesson/dbxfe-record-resolution) and [Version-aware updates and replay](#/lesson/dbxfe-versioned-updates) for resolving source rows before any MERGE. The streaming and declarative pipelines modules build on the change data feed and MERGE. Lab L05 runs every statement here locally.

<!-- section:dbxfe-delta-writes-l01-revisit -->

Redo the exercise with the North snapshot scoped to the wrong column and predict the damage, then review the cards. Reading or revealing records no completion; mark it only when you choose.

