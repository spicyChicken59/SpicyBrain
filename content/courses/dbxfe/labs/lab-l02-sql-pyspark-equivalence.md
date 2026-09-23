# Lab L02 — SQL and PySpark equivalence, proved rather than assumed

*Execution class R (local-executed): the reference solution ran on one
machine with Apache Spark 4.0.4, Python 3.12.3 and Java 21.0.10, `local[2]`,
UI off, two shuffle partitions. No Databricks workspace was involved. You
can study this page without installing anything; the package
`lab-l02-sql-pyspark-equivalence` holds the files if you want to run it.*

## Purpose

Module A3 says SQL and the DataFrame API express the same relational
transformations. This lab makes that claim testable. One typed synthetic
dataset — Cinderline inspection events — goes through the same four stages
in Spark SQL and in PySpark, and each stage is compared in two separate
ways: rows after an explicit sort, and the schema as an object. Two cases
are built to disagree first: a comparison that relies on implicit row order,
and a DataFrame null test that looks right and keeps nothing. Every expected
number was derived by hand in `DATA.md` before the code ran.

## The fixture

Twenty-six raw deliveries; a raw row is one delivery of one event, so an
event can appear twice. Nulls are "not reported", never zero.

| event_id | plant | line | inspected | defective | note |
|---|---|---|---|---|---|
| ev-001 | P1 | L1 | 12 | 1 | delivered twice |
| ev-002 | P1 | L1 | 8 | 0 | |
| ev-003 | P1 | L2 | 20 | 3 | |
| ev-004 | P2 | L1 | 10 | 2 | delivered twice |
| ev-005 | P2 | L1 | 0 | 0 | zero units, valid |
| ev-006 | P2 | L2 | 15 | 1 | |
| ev-007 | P3 | L1 | 9 | 0 | delivered twice |
| ev-008 | P3 | L1 | null | 1 | missing_units |
| ev-009 | P3 | L2 | 7 | null | missing_units |
| ev-010 | null | L1 | 11 | 1 | missing_plant |
| ev-011 | null | L2 | 5 | 0 | missing_plant |
| ev-012 | P1 | L2 | -4 | 0 | negative_units |
| ev-013 | P2 | L2 | 6 | 9 | defects_exceed_inspected |
| ev-014 | P9 | L1 | 10 | 1 | plant unknown to the dimension |
| ev-015 | P1 | L1 | 14 | 2 | |
| ev-016 | P1 | L2 | 16 | 0 | |
| ev-017 | P2 | L1 | 13 | 1 | |
| ev-018 | P2 | L2 | 12 | 1 | |
| ev-019 | P3 | L1 | 18 | 2 | |
| ev-020 | P3 | L2 | 4 | 0 | |
| ev-021 | P3 | L2 | null | null | missing_units |
| ev-022 | P1 | L1 | -1 | -1 | negative_units |
| ev-023 | P2 | L1 | 25 | 5 | |

The plant dimension has four rows with unique keys: P1 North Works (NE),
P2 South Mill (SE), P3 East Yard (NE), P4 West Forge (W). P4 has no events;
P9 has an event but no row.

## Task 1 — declare, count, distinct

The declared schema is `event_id string, plant_id string, line_id string,
inspected_units int, defective_units int, inspected_on string`, every field
nullable so that a missing quantity remains inspectable. `SELECT DISTINCT *`
and `.distinct()` remove exactly the three identical re-deliveries:
**26 raw → 23 distinct** in both interfaces, and the two distinct relations
have the same `StructType`.

## Task 2 — classify with a reason

One `CASE` (SQL) and one `when().when()` chain (DataFrame) assign the first
matching reason in the order missing_plant, missing_units, negative_units,
defects_exceed_inspected; a row with no reason is accepted. Intermediate
output, sorted by event_id: ev-008, ev-009, ev-021 missing_units; ev-010,
ev-011 missing_plant; ev-012, ev-022 negative_units; ev-013
defects_exceed_inspected — **8 rejected, 15 accepted**. The `reason` column
is a nullable string on both sides; the schemas are equal.

## Task 3 — the plant report, rows and types

Accepted rows are aggregated by plant, then LEFT JOINed to the dimension so
the unknown plant keeps its row:

| plant_id | plant_name | region | inspections | inspected | defective | defect_rate |
|---|---|---|---|---|---|---|
| P1 | North Works | NE | 5 | 70 | 6 | 0.08571428571428572 |
| P2 | South Mill | SE | 6 | 75 | 10 | 0.13333333333333333 |
| P3 | East Yard | NE | 3 | 31 | 2 | 0.06451612903225806 |
| P9 | null | null | 1 | 10 | 1 | 0.1 |

Grand total 15 / 186 / 19. Types are string, string, string, bigint,
bigint, bigint, double — `COUNT` and `SUM` over `int` columns widen to
bigint, and the guarded `CAST(... AS DOUBLE) / inspected` is a double. The
rate is unit-weighted: 6/70, not the mean of five row rates.

## Task 4 — the failure case: positional comparison

The validity filter applied to the raw frame keeps 18 rows (the three
re-deliveries are valid). Loaded in file order, `collect()` begins with
ev-001; loaded in reverse order it begins with ev-023. A learner's first
check, `assertEqual(forward_rows, backward_rows)`, **fails** — and the test
asserts that it fails and names ev-001 in the message. Sorted on event_id
the two lists are equal, and as multisets they are identical. What the
narrow filter did was preserve input order by implementation accident;
nothing in the relational contract promised it. The evidence also records
the order that `.distinct()` actually emitted (`ev-001, ev-002, ev-005,
ev-007, ev-003, ...`): neither file order nor sorted, and not asserted.

## Task 5 — null handling that differs until corrected

`F.col("plant_id") == None` turns into the predicate `plant_id = NULL`,
which is unknown for every row, and a filter keeps only true: **0 rows**,
where SQL's `WHERE plant_id IS NULL` returns **2** (ev-010, ev-011). The
correction is `isNull()`. Second divergence: `COUNT(DISTINCT plant_id)`
ignores null and returns **4**; `.select("plant_id").distinct().count()`
counts null as a value and returns **5**. Both are honest answers to
different questions. The contract "an unknown plant is not a plant" is
written explicitly — filter `isNotNull()` before `distinct()` — and both
sides return 4.

## Task 6 — inferred versus declared types

Reading the same file with `spark.read.json(multiLine=True)` yields
alphabetical columns and `bigint` integers. After reordering the columns,
the sorted rows compare equal as values, while the schema comparison
reports `inspected_units type bigint versus int` and the same for
`defective_units`. That is the reason both comparisons exist.

## Task 7 — transfer

Appending five rows (P4 30/3; P1 10/10, valid because defective may equal
inspected; P3 null/0; a fourth re-delivery of ev-016; a null-plant 3/1)
gives 31 raw, 27 distinct, 10 rejected, 17 accepted. P1 becomes 6 / 80 / 16
at 0.2, P4 West Forge appears as 1 / 30 / 3 at 0.1, the rest are unchanged,
and the grand total is 17 / 226 / 32. The author's first expected file said
22 defective; the runner refused it and the sum was redone by hand. That is
what independently authored expectations are for.

## What the tests prove, and do not

Nine cases, zero skips, exit 0 on the pinned environment: counts and
dtypes; rejected rows, reasons and schema; accepted rows and schema; the
report's rows, dtypes, schema and grand total in both interfaces; the
deliberate order failure; both null divergences and their corrections;
inferred versus declared; the transfer batch. The evidence JSON records the
versions, timestamps, SHA-256 of every fixture, expected and solution file,
and SHA-256 of every collected output. Not proved: anything about Databricks
Runtime, cluster execution, performance, or rows these fixtures do not
contain — no plant here totals zero inspected units, so the NULL-rate branch
is stated policy, not exercised behaviour.

## Setup and cleanup

Install Python 3.12 and a JDK (Java 21.0.10 was used), set `JAVA_HOME`,
create a virtual environment, `pip install -r requirements.txt` (PySpark
4.0.4, Py4J 0.10.9.9), then run
`python run_tests.py --evidence local-evidence.json`. The runner stops
Spark itself, writes no bytecode and creates nothing but the evidence file
you name. Cleanup is deleting `.venv/` and that file. Keep your written
predictions; they are the part that transfers.
