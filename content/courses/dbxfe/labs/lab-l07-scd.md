### Purpose

This lab turns a stream of entity change events into the two tables a change-data pipeline usually publishes: a **current** table (SCD type 1, one row per key) and a **history** table (SCD type 2, one row per version with a validity interval). It does so under an explicitly stated source contract and with the cases that break naive designs: a late arrival, an identical redelivery, a second event with the same state, a tie on the sequence value, a sequence that is not an integer, and a part that is deleted and later returns. The tables are computed by Spark window functions, once with the DataFrame API and once in Spark SQL, and both are held to rows written by hand. Everything below comes from the recorded run on local Apache Spark 4.0.4 in `local[2]` mode on one machine. Nothing ran on Databricks, no Delta table was written, and no declarative pipeline was used: PySpark 4.0.4 has no `pyspark.pipelines` module, which the runner records.

### The fixture

Eighteen Cinderline part change events arrive in three batches. The ones that matter most:

| # | Event | Batch | Part | seq | op | Cost | Why it is there |
|---|---|---|---|---|---|---|---|
| 0 | e-01 | 1 | P-100 | 1 | upsert | 1250 | first version |
| 5 | e-06 | 2 | P-100 | 3 | upsert | 1310 | arrives before seq 2 |
| 13 | e-13 | 3 | P-100 | 2 | upsert | 1290 | late arrival |
| 6 | e-07 | 2 | P-200 | 2 | delete | — | closes P-200 |
| 14 | e-14 | 3 | P-200 | 3 | upsert | 420 | P-200 returns |
| 7 | e-08 | 2 | P-300 | 2 | upsert | 830 | tie with e-15 |
| 15 | e-15 | 3 | P-300 | 2 | upsert | 850 | tie with e-08 |
| 8 | e-09 | 2 | P-400 | "2" | upsert | 95 | sequence is a string |
| 9 | e-05 | 2 | P-500 | 1 | upsert | 150 | identical redelivery of #4 |
| 16 | e-16 | 3 | P-500 | 1 | upsert | 150 | same state, new event id |
| 12 | e-12 | 2 | P-700 | 1 | modify | 60 | unknown operation |
| 17 | e-17 | 3 | (blank) | 1 | upsert | 10 | no part id |

The contract: `part_id` identifies the part, `seq` (a positive integer) orders its changes, at most one distinct payload may exist per part and sequence value, an upsert replaces every attribute, a delete carries none, and the batch a row arrived in says nothing about order. Two transfer fixtures follow the same rules: eight Marlow customer events ordered by `seq` and then `revision_no`, and three full supplier snapshots.

### Task by task

**Predict first.** Five predictions frame the lab: P-100's cost after batch 3 (1310), its number of history rows (3), P-300's fate (withheld), P-400's fate after batch 2 (withheld) and whether P-200 has an open row after its delete (no).

**Evidence before tables.** The resolver, reused in spirit from the ingestion module, reports 18 raw rows and 17 distinct deliveries (e-05 arrived twice), quarantines #8 (`invalid_sequence`), #12 (`invalid_op`) and #17 (`missing_part_id`), records P-500 at seq 1 as redundant evidence, withholds P-300 (`tied_sequence`, candidates 830 and 850) and P-400 (its unplaceable event might be the latest state), and excludes P-700, whose only event is quarantined. Eleven states remain orderable.

**Type 1.** One window ranks each part's states from the highest sequence down; the first is current unless it is a delete. After batch 1 there are five rows at seq 1. After batch 2 there are four: P-100 at seq 3 (1310), P-300 at seq 2 (830), P-500 at seq 1 and P-600 at seq 2 (SUP-D); P-200's latest state is its delete, and P-400 is withheld. After batch 3 there are four again: P-100 is still at seq 3 because the late change is older, P-200 is back at seq 3 (420, SUP-C), and P-300 has left because of the tie.

**Type 2.** `LEAD` over the same partition gives each state's `valid_to`, computed before delete rows are filtered out so that a delete can close a version without opening one. After batch 3 the history holds eight rows:

| Part | From | To | Cost | Current |
|---|---|---|---|---|
| P-100 | 1 | 2 | 1250 | no |
| P-100 | 2 | 3 | 1290 | no |
| P-100 | 3 | open | 1310 | yes |
| P-200 | 1 | 2 | 400 | no |
| P-200 | 3 | open | 420 | yes |
| P-500 | 1 | open | 150 | yes |
| P-600 | 1 | 2 | 2100 (SUP-C) | no |
| P-600 | 2 | open | 2100 (SUP-D) | yes |

The only gap is P-200's, from 2 to 3. The SQL version of both windows returns exactly the same rows, and the type 1 table equals the open type 2 rows in every scenario.

**What batch 3 changes.** Comparing whole rows with the batch-2 tables: current loses P-300 and gains P-200; history loses P-100 1 to 3 and both P-300 rows and gains P-100 1 to 2, P-100 2 to 3 and P-200 from 3. One late change rewrote a closed row and inserted another, so a history table has to be updatable. Replaying batch 3 unchanged adds five raw rows but no distinct delivery (still 17) and changes no table.

### The failure case

Two plausible designs sit in the starter. **Append per arrival** closes the open row whenever a new change arrives: P-100 opens at 1, closes at 3 when e-06 arrives, opens at 3, then closes at 2 when e-13 arrives. The interval check raises `interval_order` for P-100 on the row from 3 to 2. **Last arrival wins** builds a current table in arrival order and shows P-100 at 1290, the price that seq 3 had replaced, and publishes P-300 at 850 and P-400 at 90 although the contract cannot resolve either. A third test drops the quarantined rows before a correct SCD computation, as a drop rule would: P-400 is then published at 90 as if current and P-700 disappears without being listed, while the P-300 tie is still caught because each tied row is valid on its own. Three deliberately broken tables fail the invariant checks for the stated reasons: a second current row (`duplicate_current_key`), an overlap (`overlap`) and two open rows (`open_rows_per_key`).

### Transfer

Marlow's customer C-1 has a correction under one change number: silver at revision 1 and gold at revision 2 of seq 2, with gold delivered twice under two event ids. Ordered by `(seq, revision_no)`, C-1 has three versions ending in gold, and the second gold delivery is redundant evidence. Ordered by `seq` alone, the same rows tie and C-1 is withheld; only C-2 is published. For the suppliers, comparing consecutive snapshots derives eight changes and gives SUP-B three versions (7, 9 and 7 days of lead time). Without snapshot 2, SUP-B has one version and its 9-day period is invisible, and SUP-C's delete moves to snapshot 3.

### The platform adaptation, not executed

`SOLUTIONS.md` writes the same history as a Databricks AUTO CDC flow: `KEYS (part_id)`, `SEQUENCE BY seq` (or `STRUCT(seq, revision_no)` for Marlow), `APPLY AS DELETE WHEN op = 'delete'`, `STORED AS SCD TYPE 2`. It maps each part of the reference onto a clause and names what has none: quarantine with reasons, the tie policy and unplaceable changes. In open-source Apache Spark, `create_auto_cdc_flow` first appears at the 4.2.0 tag and accepts only SCD type 1. None of this was run.

### What the tests prove and do not prove

Seventeen tests prove, for Spark 4.0.4 in `local[2]` with two shuffle partitions: the validator's reasons; the evidence counts; the type 1 and type 2 tables after each batch, and the same final tables from Spark SQL; their invariants and gaps; the exact edits batch 3 forces; idempotent replay; the stale row a drop filter publishes; the two wrong designs and three broken tables failing for their named reasons; both Marlow contracts; and both snapshot cadences. While the lab was being written, five deliberate mutations of the reference (arrival order deciding a tie, a wrong delivery count, a delete left open, an unplaceable event ignored, `LAG` instead of `LEAD`) each turned several tests red; those mutation runs are not part of the recorded evidence. The tests do not prove any behaviour of AUTO CDC or of Databricks, incremental maintenance of the tables, performance at scale, or anything about another Spark version. The rules for classifying deliveries come from [duplicates, invalid records and conflicts](#/lesson/dbxfe-record-resolution).

### Setup, run and cleanup

Create a Python 3.12 virtual environment, install `requirements.txt` (PySpark 4.0.4, Py4J 0.10.9.9), point `JAVA_HOME` at a Java 17 or 21 runtime, and run `python run_tests.py --evidence local-evidence.json` from the lab directory. The recorded run used Python 3.12.3 and OpenJDK 21.0.10: 17 tests, 0 failures, 0 errors, 0 skips, exit 0. `python solutions/scenarios.py` prints every intermediate table quoted in `SOLUTIONS.md`. Each script creates one temporary directory for Spark's scratch files and deletes it after stopping Spark; nothing is written inside the package. Remove the virtual environment and the evidence file when finished. Studying this page needs no installation.
