### Purpose

This lab takes the Delta ideas of two modules, [Delta tables, commits and snapshots](#/module/dbxfe-delta) and the module on Delta writes, evolution and table maintenance, and checks them against a real table. One tiny table of fictional Cinderline Components inspection lots moves through nine committed versions: a write, an append, a correcting `UPDATE`, a property commit that turns on the change data feed, three `MERGE` statements with different intentions, an append that adds a column, and `OPTIMIZE`. After each step you predict what Delta will report and then read it back from Delta itself: rows by version (`versionAsOf`), `DESCRIBE HISTORY`, `DESCRIBE DETAIL`, the change data feed and the files in the folder. Four requests are refused on purpose. Everything ran on local Apache Spark 4.0.4 with open-source `delta-spark` 4.0.0 in `local[2]` mode on one machine; nothing ran on Databricks, no number is a timing, and no data file was ever deleted.

### The fixture

Six hand-written JSON deliveries, eleven rows in total, with the columns `inspection_id` (the merge key), `plant`, `inspected`, `defective` and `revision` (higher is newer; 0 marks a stale replay). One delivery carries an extra `inspector` column.

| Delivery | Rows | Used for |
|---|---|---|
| initial | A North 10 inspected, revision 1 | version 0 |
| append | C North 8, revision 1 | version 1 |
| day 2 (incremental) | C North revision 2; D South 15, revision 1 | version 4: A is absent |
| day 3 (incremental) | A revision 0 (stale replay); D revision 2; D revision 3; E South 12 | refused as delivered; version 5 after the fix |
| South snapshot (complete) | D revision 3 | version 6: E is retired |
| evolved append | F North 7, inspector QA-2 | refused, then version 7 with evolution |

Every expected value comes from a plain-Python replay of these rows that imports neither Spark, Delta nor the solution, plus literals copied from the Delta Lake 4.0.0 documentation. The test suite checks that the committed expected file equals a fresh replay.

### Task by task

**Versions 0 to 2.** Writing A, appending C and correcting A from 10 to 12 gives totals of 10, 18 and 20 when each version is read with `versionAsOf`. The `UPDATE` reports one updated row, zero copied rows, one file removed and one added: the table has no deletion vectors, so the only file holding A was rewritten. The old file is still on disk, so a plain Parquet read of the folder sums 10 + 8 + 12 = 30 while the table says 20. The log decides membership, not the folder.

**Version 3.** Setting `delta.enableChangeDataFeed = true` changes no row, but `DESCRIBE DETAIL` does change: the table features go from `appendOnly, invariants` (writer version 2) to `appendOnly, changeDataFeed, invariants` (writer version 7), with reader version still 1. Turning on the feed is a writer-side protocol change.

**Version 4.** The day-2 merge (`WHEN MATCHED THEN UPDATE SET *`, `WHEN NOT MATCHED THEN INSERT *`) reports two source rows, one insert (D), one update (C) and no delete. A is untouched because nothing in the statement acts on a target row that the source does not mention. An incremental delivery lists changes; its silence about A is not evidence that A was retired.

**The refusal and version 5.** Run as delivered, day 3 fails with `DELTA_MULTIPLE_SOURCE_ROW_MATCHING_TARGET_ROW_IN_MERGE`: two source rows match target D, and Delta will not guess which one wins. The table stays at version 4. The fix keeps the highest revision per key and adds a guard, `WHEN MATCHED AND s.revision > t.revision`. Version 5 updates D to revision 3 (16 inspected), inserts E and leaves A at revision 1, because the replay's revision 0 is older than what the table holds. The same naive merge run against a copy of version 3, before D existed, is not refused at all: no target row is matched twice, so it commits five rows with D twice and A overwritten by the stale replay. The error protects matched keys only, which is why de-duplication belongs before every merge.

**Version 6 and the wrong way.** The South snapshot is complete for South only, so the delete clause is scoped: `WHEN NOT MATCHED BY SOURCE AND t.plant = 'South' THEN DELETE`. E is deleted; North's A and C stay. On a disposable copy of version 5, the same statement without the plant condition deletes three rows and leaves only D, which is the failure the scope prevents.

**The change feed.** Reading versions 4 to 6 returns seven change rows: C's update pre-image and post-image and D's insert at version 4; D's pre-image, post-image and E's insert at version 5; E's delete at version 6. A `_change_data` folder appears beside the data files. Asking for versions 2 to 6 fails with `DELTA_MISSING_CHANGE_DATA`: the feed starts after the commit that enabled it and never reconstructs the past.

**Version 7.** Appending F without evolution fails with "A schema mismatch detected when writing to the Delta table" and commits nothing. With the `mergeSchema` write option the append commits: six columns, `inspector` null for A, C and D, `QA-2` for F. Reading version 6 still returns five columns.

**Version 8 and retention.** `OPTIMIZE` removed the current version's two files and added one; version 8 selects exactly version 7's rows, and one more Parquet file sits in the folder than before. A second `OPTIMIZE` removed and added nothing and committed no version. `VACUUM ... DRY RUN` listed no data file, because every replaced file is younger than the seven-day default retention (the only path listed was the `_change_data` directory entry itself). A request for `RETAIN 0 HOURS DRY RUN` was refused by the safety check ("Are you sure you would like to vacuum files with such a low retention period?") before anything was listed, and version 0 was still readable afterwards.

**Protocol and transfer.** A second table declared with `CLUSTER BY (plant)` reports the `clustering` and `domainMetadata` features with writer version 7 and reader version 1. Rerunning everything with A corrected to 14 moves the folder reading to 32 and every total from version 2 onward by 2 (22, 22, 37, 50, 38, 45, 45), with no row count changing.

### The failure cases

Four refusals are part of the expected behaviour, and each is asserted by its reason, not merely by "an error happened": the duplicate-match `MERGE` by its error class, the early change-feed read by its error class, the schema-mismatched append by its message, and the zero-hour `VACUUM` by the safety check's message. The duplicate and schema refusals are also shown to commit nothing. The unscoped snapshot merge is the one wrong approach that succeeds, which is why it only ever runs on a copy.

### What the tests prove and do not prove

The 19 tests prove that open-source Delta 4.0.0 on local Spark produced exactly these rows per version, merge metrics, change rows, schemas, table features and refusals for this commit sequence. They do not show Databricks behaviour: its Delta implementation, defaults, duplicate-match rules, predictive optimization and automatic clustering are outside the lab. They do not measure performance, and they never run a `VACUUM` that deletes anything. A deliberately broken solution (guard and scope removed) was run separately and failed six tests for the expected reasons.

### Setup, run and cleanup

Create a Python 3.12 virtual environment, install the pinned `requirements.txt` (PySpark 4.0.4, Py4J 0.10.9.9, delta-spark 4.0.0 and its two small dependencies), make sure Java 21 is available, and run `python run_tests.py --evidence <file>` from the lab folder. The Delta jars are resolved by Spark's Ivy at session start; set `SPICYBRAIN_IVY_DIR` to a pre-filled Ivy folder, or `LAB_DELTA_JARS` to local jar paths, if the machine cannot reach Maven Central. The runner and the starter create one temporary folder each and delete it when they finish; delete any leftover `lab-l05-*` folder if a run is killed, and remove the virtual environment when you are done.
