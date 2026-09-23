# Lab L05 solutions

The reference functions are in `solutions/delta_sequence.py`; `run_tests.py` drives them and
compares every observation with `expected/snapshots.json`. The outputs quoted below are the ones
Delta 4.0.0 reported in the recorded run (local Spark 4.0.4, `local[2]`); file names, table IDs
and paths differ on every run and are left out.

## Task 1 — versions 0-2 and the 30 that is not a total

```python
write_initial(spark, table)                                   # mode("error"): never overwrites a table
append(spark, table, "append_c.json")
correct_inspected(spark, table, "A", 12)                      # UPDATE ... SET inspected = 12 WHERE inspection_id = 'A'
[totals(snapshot(spark, table, v))["total_inspected"] for v in range(3)]   # [10, 18, 20]
```

`DESCRIBE HISTORY` shows `WRITE`, `WRITE`, `UPDATE`; the `UPDATE` metrics are
`numUpdatedRows=1, numCopiedRows=0, numRemovedFiles=1, numAddedFiles=1`. The table has no deletion
vectors, so the update rewrote the only file that held A and logged a remove action for the old
one. The old file is still on disk: three Parquet files in the folder, two in the current version.

`spark.read.format("parquet").load(table)` ignores `_delta_log` and sums all three files:
10 + 8 + 12 = **30**. Delta reads only the files the log's current version selects: 8 + 12 = 20.
That is the retained module's snapshot lesson, now on a real table.

## Task 2 — the change feed property and an incremental merge

```sql
ALTER TABLE delta.`<table>` SET TBLPROPERTIES (delta.enableChangeDataFeed = true);   -- version 3

MERGE INTO delta.`<table>` AS t USING incoming AS s                                  -- version 4
ON t.inspection_id = s.inspection_id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
```

Version 3 changes no row, but `DESCRIBE DETAIL` changes: before, `tableFeatures` was
`[appendOnly, invariants]` with writer version 2; after, `[appendOnly, changeDataFeed,
invariants]` with writer version 7 and reader version 1. Enabling the feed is a protocol change on
the writer side: readers are unaffected, writers must understand the feature.

The merge reports `numSourceRows=2, numTargetRowsInserted=1, numTargetRowsUpdated=1,
numTargetRowsDeleted=0`. A survives because a `MERGE` only acts on three situations: a source row
that matches (`WHEN MATCHED`), a source row that matches nothing (`WHEN NOT MATCHED`), and a target
row that no source row matches (`WHEN NOT MATCHED BY SOURCE`). This statement has no clause of the
third kind, so A, which is only in the target, is not touched. An incremental delivery says "these
rows changed"; it says nothing about the rows it does not mention, so adding a delete clause here
would turn every quiet day into data loss.

## Task 3 — the refused merge and the guarded fix

Run as delivered, the day-3 merge fails:

```text
[DELTA_MULTIPLE_SOURCE_ROW_MATCHING_TARGET_ROW_IN_MERGE] Cannot perform Merge as multiple source rows
matched and attempted to modify the same target row in the Delta table in possibly conflicting ways.
```

The table stays at version 4. Delta cannot know whether D should end as revision 2 or 3, so it
refuses the whole statement rather than pick one; nothing is half-applied. The fix has two halves:

```python
latest = Window.partitionBy("inspection_id").orderBy(F.col("revision").desc())
deduped = source.withColumn("_rank", F.row_number().over(latest)).filter("_rank = 1").drop("_rank")

(DeltaTable.forPath(spark, table).alias("t")
    .merge(deduped.alias("s"), "t.inspection_id = s.inspection_id")
    .whenMatchedUpdateAll(condition="s.revision > t.revision")
    .whenNotMatchedInsertAll()
    .execute())                                               # version 5
```

De-duplication keeps D revision 3, A revision 0 and E revision 1. The guard then decides per
matched row: D (3 > 1) is updated; A (0 > 1 is false) is left alone, so the stale replay of 99
inspected never lands; E is inserted. Metrics: `numSourceRows=3, numTargetRowsInserted=1,
numTargetRowsUpdated=1`. The recorded history shows the guard as the matched clause's predicate.

**Why de-duplicate even when Delta does not complain.** The same naive merge run against a copy of
version 3, before D existed, commits without error: `numTargetRowsInserted=3, numTargetRowsUpdated=1`.
D is inserted twice (revisions 2 and 3), E once, and A is overwritten by the stale replay (99 inspected,
revision 0). No target row was matched by two source rows, so there was nothing ambiguous to refuse.
The refusal you saw at version 4 is a safety net for matched keys, not a de-duplication step.

## Task 4 — a scoped snapshot delete, and the wrong way

```sql
MERGE INTO delta.`<table>` AS t USING snapshot AS s                                  -- version 6
ON t.inspection_id = s.inspection_id
WHEN MATCHED AND s.revision > t.revision THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
WHEN NOT MATCHED BY SOURCE AND t.plant = 'South' THEN DELETE
```

D matches but is not newer (3 > 3 is false), so it is unchanged. E is South and absent, so it is
deleted. A and C are absent too, but they are North, outside the clause's condition, so they stay.
Metrics: `numTargetRowsDeleted=1` and `numTargetRowsNotMatchedBySourceDeleted=1`.

**The wrong approach.** `merge_unscoped_snapshot_wrong()` runs the same statement without
`AND t.plant = 'South'` on a disposable copy of version 5 (made with `copy_version()`). It deletes
three rows (A, C and E) and leaves only D. The mistake is treating one plant's complete snapshot as
a complete snapshot of the table: the clause cannot know what the delivery was supposed to cover,
so the condition must say it. Never try this on a shared table; the lab only runs it on a copy.

## Task 5 — the change data feed

```python
spark.read.format("delta").option("readChangeFeed", "true") \
    .option("startingVersion", 4).option("endingVersion", 6).load(table)
```

| `_commit_version` | `inspection_id` | `_change_type` | inspected / defective / revision |
|---|---|---|---|
| 4 | C | update_preimage | 8 / 0 / 1 |
| 4 | C | update_postimage | 8 / 1 / 2 |
| 4 | D | insert | 15 / 3 / 1 |
| 5 | D | update_preimage | 15 / 3 / 1 |
| 5 | D | update_postimage | 16 / 4 / 3 |
| 5 | E | insert | 12 / 1 / 1 |
| 6 | E | delete | 12 / 1 / 1 |

The pre-image is the row before the update and the post-image the row after, so a downstream
consumer can apply or audit each change without re-reading whole versions. The table folder now
has a `_change_data` directory: Delta writes change files for `UPDATE`, `DELETE` and `MERGE`
commits (insert-only commits it derives from the log instead). Asking for versions 2 to 6 fails with
`DELTA_MISSING_CHANGE_DATA` ("change data was not recorded for version [2]"): the feed records
changes only from the commit after it was enabled, and nothing reconstructs the past.

## Task 6 — enforcement, then evolution

Without evolution:

```text
[_LEGACY_ERROR_TEMP_DELTA_0007] A schema mismatch detected when writing to the Delta table (Table ID: ...).
```

No version is committed. With the write option, for this write only:

```python
batch(spark, "append_f_inspector.json").write.format("delta").mode("append") \
    .option("mergeSchema", "true").save(table)                # version 7
```

Version 7 has six columns; A, C and D read `inspector = null` because their files never had the
column, and F reads `QA-2`. `versionAsOf 6` still returns five columns. Evolution is a decision
recorded as a commit, not a default: every downstream reader of the table now sees a new column.
Note the contrast with `MERGE ... UPDATE SET *`, which by the documentation ignores extra source
columns unless automatic schema evolution is enabled for the session.

## Task 7 — maintenance

`OPTIMIZE` (version 8) reported `numFilesRemoved=2, numFilesAdded=1`; `DESCRIBE DETAIL` then shows
one file, version 8 selects exactly version 7's rows, and the folder holds one more Parquet file
than before (7 then 8 in the recorded run). A second `OPTIMIZE` reported 0 and 0 and committed no
version: bin-packing is idempotent.

`VACUUM delta.<table> DRY RUN` listed no Parquet file: every replaced file was removed minutes ago,
well inside the seven-day default (`delta.deletedFileRetentionDuration`). In the recorded run the
only path in the listing was the `_change_data` directory entry itself, not any file inside it.
`VACUUM ... RETAIN 0 HOURS DRY RUN` was refused before anything was listed:

```text
requirement failed: Are you sure you would like to vacuum files with such a low retention period?
```

The message goes on to name a switch that turns the check off. This lab never uses it, and neither
should you on a shared table: a reader or stream that started before the vacuum may still need the
old files, and a writer's uncommitted files look unreferenced. A retention shorter than seven days
needs the table's owners to know the longest-running reader, the longest stream lag and the
time-travel window the business relies on. Version 0 was still readable after both requests.

## Task 8 — protocol, clustering and the transfer

The clustered table reports `tableFeatures=[appendOnly, clustering, domainMetadata, invariants]`,
`clusteringColumns=[plant]`, `minWriterVersion=7`, `minReaderVersion=1`. Declaring clustering is a
writer-protocol change: an older writer that does not understand those features must not write
the table. Protocol upgrades are one-way, so a table's features are part of its compatibility
contract, not a performance switch.

With the correction 14 the directory reading after version 2 is 32 and the totals for versions
2-8 are 22, 22, 37, 50, 38, 45, 45: every downstream total moves by the same 2 and no row count
changes, which shows the pipeline carries the corrected value through updates, merges, deletes,
evolution and compaction without re-counting it.

## What the tests prove, and what they do not

They prove that on open-source Delta 4.0.0 and local Spark these exact commits produce these exact
rows, metrics, change rows, schemas and protocol entries, and that the four refusals happen for the
stated reasons without committing. They do not prove anything about Databricks: its Delta
implementation, defaults, duplicate-match rules, predictive optimization and automatic clustering
are outside this lab. They do not measure performance, and they never show a real `VACUUM`.
