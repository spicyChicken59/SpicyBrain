# Lab L07 solutions

Open this after your own attempt. The reference is `solutions/scd_reference.py`;
`python solutions/scenarios.py` prints every intermediate output quoted here.
All outputs below come from local Apache Spark 4.0.4 in `local[2]` mode on one
machine. The platform adaptation at the end was **not executed**.

## 1. Predictions (Task 1)

| Prediction | Answer | Why |
|---|---|---|
| P-100 unit cost after batch 3 | 1310 | seq 3 is the highest sequence; the late seq 2 (1290) is older |
| P-100 history rows after batch 3 | 3 | [1]→[2] 1250, [2]→[3] 1290, [3]→open 1310 |
| P-300 after batch 3 | withheld | e-08 (830) and e-15 (850) both claim seq 2 |
| P-400 after batch 2 | withheld | e-09's seq is the string "2"; it cannot be placed, so the latest state is unknown |
| P-200 open row after batch 2 | False | the delete at seq 2 closes [1]→[2] and opens nothing |

## 2. The evidence before any table

`resolve()` returns evidence first and states second. Through all three batches:

| Evidence | Value |
|---|---|
| raw rows / distinct deliveries / orderable states | 18 / 17 / 11 |
| quarantine | #8 invalid_sequence, #12 invalid_op, #17 missing_part_id |
| duplicate deliveries | e-05 at raw [4, 9] |
| redundant evidence | P-500 at [1]: e-05 and e-16 |
| unresolved | P-300 tied_sequence at [2] (830 vs 850); P-400 invalid_sequence (#8) |
| excluded | P-700 |

Record resolution itself is module B3's subject; here it is the precondition
that makes a sequence meaningful. Two rules matter for SCD: a tie is not
settled by arrival order, and an unplaceable event withholds its key rather
than being skipped.

## 3. Type 1 and Type 2 with window functions (Tasks 3 and 4)

The resolved states become a typed DataFrame (key, sequence columns, op,
attributes; deletes included). Two windows over the same partition do the work:

```python
sequence = F.struct(*[F.col(c) for c in contract.sequence])
ascending = Window.partitionBy(contract.key).orderBy(*[F.col(c).asc() for c in contract.sequence])
descending = Window.partitionBy(contract.key).orderBy(*[F.col(c).desc() for c in contract.sequence])
history = (df.withColumn("valid_from", sequence)
             .withColumn("valid_to", F.lead(sequence).over(ascending))   # next state, upsert or delete
             .filter(F.col("op") == "upsert")                           # a delete closes, never opens
             .withColumn("is_current", F.col("valid_to").isNull()))
current = (df.withColumn("rn", F.row_number().over(descending))
             .filter((F.col("rn") == 1) & (F.col("op") == "upsert")))   # latest state, unless deleted
```

The order of `.filter` matters: `lead` must see the delete rows, or P-200's
[1] version would stay open. The same tables in Spark SQL:

```sql
SELECT part_id, valid_from, valid_to, valid_to IS NULL AS is_current, description, unit_cost_cents, supplier_code
FROM (
  SELECT *, named_struct('seq', seq) AS valid_from,
         LEAD(named_struct('seq', seq)) OVER (PARTITION BY part_id ORDER BY seq) AS valid_to
  FROM lab_l07_states
) AS ordered
WHERE op = 'upsert'
```

Output through each batch:

| Part | after batch 1 | after batch 2 | after batch 3 |
|---|---|---|---|
| P-100 current | seq 1, 1250 | seq 3, 1310 | seq 3, 1310 |
| P-100 history | [1]→open | [1]→[3], [3]→open | [1]→[2], [2]→[3], [3]→open |
| P-200 current | seq 1, 400 | none (deleted) | seq 3, 420 SUP-C |
| P-200 history | [1]→open | [1]→[2] | [1]→[2], [3]→open |
| P-300 | seq 1, 800 | seq 2, 830 | withheld (tie) |
| P-400 | seq 1, 90 | withheld | withheld |
| P-500 | seq 1, 150 | seq 1, 150 | seq 1, 150 |
| P-600 | — | seq 2 SUP-D; history [1]→[2] SUP-C, [2]→open | unchanged |

Gaps after batch 3: P-200 from [2] to [3], the delete's gap. Type 1 equals the
open Type 2 rows in every scenario (test 07), which cross-checks two
independently written windows.

## 4. What batch 3 does to published tables

Comparing whole rows between the batch-2 and batch-3 tables: current loses
P-300 and gains P-200 seq 3; history loses P-100 [1]→[3] and both P-300 rows,
and gains P-100 [1]→[2], P-100 [2]→[3] and P-200 [3]→open. The late arrival
never touched the present, but it rewrote a closed row and inserted one
between two existing rows. A history that can only be appended to cannot
absorb that; an incremental engine must update and insert.

## 5. The wrong approach, and why it fails

`append_per_arrival` (in the starter) closes the open row at each arrival's
sequence and opens a new one. For P-100 it opens [1], closes it at [3] when e-06
arrives, opens [3], then closes that row at **[2]** when the late e-13 arrives.
`check_intervals` raises `interval_order` for P-100 with the row [3]→[2]. The
fault is the assumption that arrival order is sequence order; batch 3 breaks
it. `last_arrival_wins` fails the same way on Type 1 (P-100 ends at 1290, the
older price) and also publishes P-300 by arrival order (850) and P-400's stale
seq 1 row, because it skips the unplaceable event silently. Test 10 shows the
same stale P-400 row appearing when invalid rows are dropped before a correct
SCD computation: dropping is a decision about the current row, not a neutral
clean-up.

## 6. Invariants, and what they do not prove (Task 5)

`check_current_unique` and `check_intervals` pass on every produced table and
reject three deliberately broken ones: a second P-100 current row
(`duplicate_current_key`), P-100's [1] version stretched to [3]
(`overlap`), and P-600's first version reopened (`open_rows_per_key`). They
prove the tables are well formed. They do not prove the tables are right: the
last-arrival table passes uniqueness while holding the wrong price, which is why
the literals in `expected/` exist.

## 7. Transfer: the contract decides the tie (Task 6)

Marlow's C-1 carries a correction: m-03 (silver) and m-04 (gold) share seq 2 with
revision numbers 1 and 2, and m-08 repeats m-04 under a new event id. With the
composite contract `(seq, revision_no)` there is no tie: C-1 has three
versions, [1,1]→[2,1] bronze, [2,1]→[2,2] silver, [2,2]→open gold, and m-08 is
redundant evidence. With `seq` alone the same rows tie at 2 and C-1 is
withheld; only C-2 is published. The data did not change; the promise did.

## 8. Snapshots (Task 7)

Comparing consecutive supplier snapshots gives eight changes: four upserts at 1;
at 2 an upsert for SUP-B (9 days), a delete for SUP-C and an upsert for SUP-E;
at 3 an upsert for SUP-B (7 days). SUP-B's history has three versions. Skip
snapshot 2 and SUP-B has one version: the 9-day period happened and reverted
between the two snapshots you kept, so no comparison can see it. SUP-C's end
and SUP-E's start move to snapshot 3. Snapshot-derived history is only as fine
as the snapshot cadence.

## 9. Platform adaptation — NOT EXECUTED

Nothing below was run: PySpark 4.0.4, this lab's engine, has no
`pyspark.pipelines` module (the runner records that check), and no Databricks
workspace was used. Argument names for Databricks are as previously read in
its AUTO CDC documentation; confirm them against the current page first.

On Databricks, the Type 2 table would be a streaming table filled by an AUTO CDC
flow (formerly APPLY CHANGES), reading a source that has already passed your
validation:

```sql
CREATE OR REFRESH STREAMING TABLE part_history;

CREATE FLOW part_history_cdc AS AUTO CDC INTO part_history
FROM STREAM(part_events_valid)
KEYS (part_id)
APPLY AS DELETE WHEN op = 'delete'
SEQUENCE BY seq
COLUMNS * EXCEPT (op, seq, event_id, batch)
STORED AS SCD TYPE 2;
```

```python
from pyspark import pipelines as dp
from pyspark.sql.functions import col, expr, struct

dp.create_streaming_table("customer_history")
dp.create_auto_cdc_flow(
    target="customer_history",
    source="customer_events_valid",
    keys=["customer_id"],
    sequence_by=struct("seq", "revision_no"),   # the composite contract: seq, then revision_no
    apply_as_deletes=expr("op = 'delete'"),
    except_column_list=["op", "seq", "revision_no", "event_id", "batch"],
    stored_as_scd_type=2,
)
```

How the reference maps onto it, and where it does not:

| Reference | AUTO CDC | Gap to close yourself |
|---|---|---|
| `Contract.key` | `KEYS` / `keys` | — |
| `Contract.sequence` | `SEQUENCE BY` / `sequence_by`, a struct for a tie-breaker | the documentation asks for one distinct update per key per sequence value and does not support NULL sequencing; the reference withholds the tie instead |
| `op == "delete"` | `APPLY AS DELETE WHEN` | — |
| `valid_from`, `valid_to` | `__START_AT`, `__END_AT`, typed like the sequence column | column names differ |
| quarantine with reasons | nothing built in | validate upstream (expectations or a quarantine table) and decide what a withheld key means |
| full recompute each call | incremental maintenance | the engine keeps its own state; replaying a changed history needs a full refresh |
| snapshot comparison | `create_auto_cdc_from_snapshot_flow` (Python) | the same cadence blindness applies |

Open-source Apache Spark differs by release. The Spark Declarative Pipelines
Python API at the v4.1.x tags exports no AUTO CDC function. At the v4.2.0 tag,
`pyspark.pipelines` exports `create_auto_cdc_flow`, whose docstring accepts only
SCD type 1, requires a target made with `create_streaming_table`, and treats the
key set as persisted state that cannot change between incremental runs without
a full refresh; the v4.2.0 SQL grammar has no AUTO CDC statement. So only the
Type 1 half of this lab maps onto open-source Spark 4.2.0, and none of it onto
4.0.4 or 4.1.x. Verify against the release you actually run.
