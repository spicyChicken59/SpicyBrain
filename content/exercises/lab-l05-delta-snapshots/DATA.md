# Lab L05 data dictionary

All data is synthetic and hand-written for this lab: six JSON files, eleven rows in total,
describing inspections at the fictional Cinderline Components plants North and South. No row
comes from a real company, device or person. There is no generator and no random seed; the files
are the data.

## Columns

| Column | Type in the table | Meaning |
|---|---|---|
| `inspection_id` | string | business key of one inspection lot (A, C, D, E, F); the `MERGE` key |
| `plant` | string | `North` or `South`; the scope of a complete snapshot |
| `inspected` | integer | parts inspected in the lot |
| `defective` | integer | parts found defective |
| `revision` | integer | the sender's revision of this lot; higher is newer, and 0 marks a stale replay |
| `inspector` | string, nullable | only in `append_f_inspector.json`; added to the table by explicit evolution |

## Fixtures, in the order the lab uses them

| File | Rows | Role |
|---|---|---|
| `initial_a.json` | A North 10/1 rev 1 | version 0, the first write |
| `append_c.json` | C North 8/0 rev 1 | version 1, a plain append |
| `incremental_day2.json` | C North 8/1 rev 2; D South 15/3 rev 1 | version 4, an incremental delivery: A is absent |
| `incremental_day3.json` | A North 99/9 rev 0; D South 15/4 rev 2; D South 16/4 rev 3; E South 12/1 rev 1 | refused as delivered (two D rows); version 5 after de-duplication and the revision guard |
| `snapshot_south.json` | D South 16/4 rev 3 | version 6, a complete snapshot of South: E is retired |
| `append_f_inspector.json` | F North 7/0 rev 1, inspector QA-2 | refused without evolution; version 7 with `mergeSchema` |

Version 2 is the `UPDATE` that corrects A's inspected count to 12 (14 in the transfer test),
version 3 the property commit that enables the change data feed, version 8 the `OPTIMIZE`.

## How every expected value is derived (independently of the solution)

`expected/derive_expected.py` imports only `json`, `copy` and `pathlib`. It replays the sequence
over the fixture rows with dictionaries, using the `MERGE` rules as the open-source Delta Lake
4.0.0 documentation states them: a matched source row updates the target row, an unmatched source
row is inserted, a target row that no source row matches is deleted only by a `NOT MATCHED BY
SOURCE` clause and only inside that clause's scope, and a matched target row with two matching
source rows makes the whole `MERGE` fail. The tests assert that `expected/snapshots.json` equals a
fresh run of this derivation, and that the derivation imports neither Spark, Delta nor the solution.

Worked numbers for the base run (correction 12):

| Version | Rows | Total inspected | Why |
|---|---|---|---|
| 0 | A | 10 | first write |
| 1 | A, C | 18 | 10 + 8 |
| 2 | A, C | 20 | A corrected from 10 to 12 |
| 3 | A, C | 20 | a property commit changes no row |
| 4 | A, C, D | 35 | C updated (still 8 inspected), D inserted (15) |
| 5 | A, C, D, E | 48 | D updated to revision 3 (16), E inserted (12); A's revision-0 replay skipped |
| 6 | A, C, D | 36 | E deleted by the scoped South snapshot |
| 7 | A, C, D, F | 43 | F appended (7) with the new column |
| 8 | A, C, D, F | 43 | compaction changes files, not rows |

Merged naively into a copy of version 3 (before D existed), the day-3 delivery is not refused: A is
overwritten by its revision-0 replay (99 inspected), both D rows and E are inserted, giving five rows with
two D rows (metrics: three inserted, one updated, four source rows).

The directory reading after version 2 is 10 + 8 + 12 = 30: the superseded file that still holds
A at 10 is counted beside the rewritten one. The wrong unscoped snapshot merge, run on a copy of
version 5, deletes A, C and E (three rows) and leaves only D. The change-feed rows for versions 4 to
6 are C's update pre- and post-image and D's insert; D's update pre- and post-image and E's insert;
E's delete: seven rows (two inserts, two pre-images, two post-images, one delete).

The transfer run changes one input, A's correction, from 12 to 14: the directory reading becomes
32 and every total from version 2 onwards rises by 2, while every row count stays the same.

## Documented literals

The `documented` block of `expected/snapshots.json` is copied by hand from the Delta Lake 4.0.0
documentation sources (tag `v4.0.0` of the delta-io/delta repository): history operation names;
that the change data feed is a writer-side feature (reader version 1, writer version at least 4);
that a liquid-clustered table carries the `clustering` and `domainMetadata` features with writer
version 7 and reader version 1; the default retentions (seven days for removed data files, 30 days
for the log); the error classes and message fragments Delta 4.0.0 uses for the four refusals; and
that bin-packing compaction is idempotent. The refusal texts were cross-checked against the
`error/delta-error-classes.json` file inside the delta-spark 4.0.0 jar and the text of Delta's
`VACUUM` retention check.
