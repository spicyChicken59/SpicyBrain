# Lab L05 tasks

Work in `starters/delta_sequence_task.py`. Before each task, write your prediction into
`PREDICTIONS`; after it, compare Delta's answer with your prediction and with
`expected/snapshots.json`. The data is described in `DATA.md`. Every expected behaviour below is
checkable from Delta's own output: `snapshot()` (rows by version), `history()` (`DESCRIBE
HISTORY`), `detail()` (`DESCRIBE DETAIL`) and `change_feed()`.

Two rules hold for the whole lab: never add a setting that disables Delta's retention check, and
never run `VACUUM` without `DRY RUN`. No task needs either.

## Task 1 — Three versions, one truth (versions 0-2)

Write A (inspected 10), append C (8), then correct A to 12 with an `UPDATE`. Read versions 0, 1
and 2 with `versionAsOf`.

Expected behaviour:

- the totals are 10, 18 and 20;
- `DESCRIBE HISTORY` names the three commits `WRITE`, `WRITE`, `UPDATE`, and the `UPDATE` reports
  one updated row, zero copied rows, one file removed and one file added;
- the table directory now holds three Parquet data files while `DESCRIBE DETAIL` says the current
  version uses two;
- `spark.read.format("parquet").load(<table folder>)` sums `inspected` to **30**. Explain in one
  sentence which file makes it 30 and why Delta's answer is still 20.

## Task 2 — A missing incremental row is not a delete (versions 3-4)

Enable the change data feed with `ALTER TABLE ... SET TBLPROPERTIES (delta.enableChangeDataFeed =
true)`. Then complete `merge_incremental()`: `MERGE` the day-2 delivery (C revision 2, new D) on
`inspection_id`, updating matched rows and inserting unseen keys. A is not in the delivery.

Expected behaviour:

- the property commit (version 3) changes no row, and `DESCRIBE DETAIL` now lists the
  `changeDataFeed` table feature while `minReaderVersion` stays 1;
- after the merge (version 4) the table has three rows, A unchanged; the merge metrics are one
  row inserted, one updated, none deleted, two source rows;
- write a comment explaining why A must survive: which clause could have removed it, and why an
  incremental delivery does not license that clause.

## Task 3 — Two rows for one key, and a stale replay (version 5)

Run your `merge_incremental()` on the day-3 delivery as delivered. It carries two rows for D
(revisions 2 and 3), a replay of A with revision 0, and a new E.

Expected behaviour:

- Delta refuses the `MERGE` with the error class
  `DELTA_MULTIPLE_SOURCE_ROW_MATCHING_TARGET_ROW_IN_MERGE`, and the table stays at version 4 with
  the same three rows;
- complete `dedupe_latest_revision()` (one row per key, highest revision) and `merge_guarded()`
  (update a matched row only when the source revision is greater; insert unseen keys);
- the guarded merge commits version 5: D becomes revision 3 (16 inspected, 4 defective), E is
  inserted, and A keeps revision 1 because a revision-0 replay is older than what the table holds.
  Metrics: one inserted, one updated, none deleted, three source rows.
- predict, then check on a disposable copy of **version 3** (where D does not exist yet): the same naive
  merge is **not** refused. Nothing in the target is matched twice, so both D rows are inserted, E is
  inserted and A is overwritten by the stale revision-0 replay: five rows, two of them D. The
  duplicate-match error protects matched keys only; de-duplication must happen before every merge.

## Task 4 — Silence means retired only in a complete snapshot (version 6)

The South plant sends a complete snapshot of its open inspections: only D. Complete
`merge_full_snapshot()` with a `WHEN NOT MATCHED BY SOURCE ... THEN DELETE` clause scoped to the
plant the snapshot covers.

Expected behaviour:

- version 6 has A, C and D; E (South, not in the snapshot) is deleted; A and C (North) are untouched;
- the history metrics show one row deleted, and that deletion is counted under
  `numTargetRowsNotMatchedBySourceDeleted`;
- predict, then check on a disposable copy of version 5 (see `SOLUTIONS.md` for the helper): an
  unscoped clause deletes **three** rows, leaving only D. Say which assumption made that wrong.

## Task 5 — Read the changes, and ask for changes that were never recorded

Read the change data feed from version 4 to version 6.

Expected behaviour:

- seven change rows: C's pre- and post-image and D's insert at version 4; D's pre- and post-image
  and E's insert at version 5; E's delete at version 6;
- a folder `_change_data` now exists in the table directory;
- reading from version 2 to 6 is refused with `DELTA_MISSING_CHANGE_DATA`, because the feed was
  enabled at version 3 and past changes are not captured.

## Task 6 — Enforcement first, evolution on purpose (version 7)

Append F, which carries a new column `inspector`.

Expected behaviour:

- without evolution the append is refused with "A schema mismatch detected when writing to the Delta
  table" and no version is committed;
- complete `append_with_new_column()` using the write option `mergeSchema` for this write only;
  version 7 has six columns, A, C and D have a null `inspector`, F has `QA-2`;
- reading version 6 still returns five columns: time travel returns the schema that version had.

## Task 7 — Maintenance changes files, not rows (version 8)

Run `OPTIMIZE` twice, then `VACUUM ... DRY RUN`, then ask for `VACUUM ... RETAIN 0 HOURS DRY RUN`.

Expected behaviour:

- the first `OPTIMIZE` removes every file of the current version (at least two) and adds one;
  version 8 selects exactly the rows of version 7; one more Parquet file sits on disk than before;
- the second `OPTIMIZE` adds and removes nothing and commits no version;
- the default dry run lists no Parquet data file, because every replaced file is younger than the
  seven-day default retention; version 0 is still readable afterwards;
- the zero-hour request is refused by the safety check ("Are you sure you would like to vacuum
  files with such a low retention period?") before anything is listed. Write two sentences on who
  would have to agree before a shorter retention is ever chosen for a shared table, and why.

## Task 8 — Protocol, features and a transfer

Create a second tiny table with `CLUSTER BY (plant)` and read `DESCRIBE DETAIL`; then rerun the
whole sequence on a fresh path with A corrected to 14 instead of 12.

Expected behaviour:

- the clustered table lists the `clustering` and `domainMetadata` table features, clustering
  column `plant`, `minWriterVersion` 7 and `minReaderVersion` 1;
- with the correction 14, the directory reading after version 2 is 32 and every later total
  moves by 2 (22, 22, 37, 50, 38, 45, 45 for versions 2-8), while row counts do not change.
