# Tasks — predict, then read the evidence

Work in `starters/execution_task.py`. Every task has a prediction you write down
first and an observation you read from Spark afterwards. Record both; the
comparison is the learning, not the code. Expected behaviour is stated so you
can check yourself; the derivations are in `DATA.md`.

Session for every task unless told otherwise: `local[2]`, UI off,
`spark.sql.shuffle.partitions = 4`, adaptive execution **off**,
`spark.sql.autoBroadcastJoinThreshold = -1`. The fact frame is loaded with four
input partitions; the three-row plant dimension with one. Use `measure()` to
read jobs, stages and tasks, and `stage_metrics()` on its result to read the
shuffle records each stage and task read and wrote.

## Task 1 — A narrow chain

Filter `defective_units > 0` and select `event_id, plant, defective_units`.
Capture `plan_text()` (formatted mode).

Expected: the outline is `Project` over `Filter` over `Scan ExistingRDD` with
**no `Exchange`**; the output still has 4 partitions; collecting it runs **one
job, one stage, four tasks**; 187 rows come back. Rows per output partition
are 47, 48, 45 and 47: exactly the defective rows of each input slice, because
no row moved. Then explain the plan of `narrow.groupBy().count()`: even
`count()` ends with `Exchange SinglePartition`.

## Task 2 — A grouped sum

`groupBy("plant")` with `count`, `sum(inspected_units)`, `sum(defective_units)`.

Predict the number of `Exchange` nodes, the tasks in the second stage and the
number of records that cross the Exchange before running. Show first that
`explain()` alone starts no job. Expected: **one** `Exchange
hashpartitioning(plant, 4)` between a partial and a final `HashAggregate`; one
job with executed stages of **4 then 4 tasks** (the second equals
`spark.sql.shuffle.partitions`). The map stage wrote **12 records**, three per
task (one partial row per plant per input partition), not 240; the reduce
tasks read 8, 0, 4 and 0 of them on the recorded run. Totals: North 180 rows /
5898 / 336, South 36 / 1391 / 79, West 24 / 961 / 46.

## Task 3 — The same join two ways

Join the facts to `plants` on `plant` and sum `inspected_units` per `region`.

1. As planned with broadcast disabled. Expected: `SortMergeJoin`, **three**
   `Exchange` nodes (each join input, then the regional aggregate), one job,
   executed stages with task counts **1, 4, 4, 4** in some order. The two input
   stages wrote **240 and 3 records**: every row of both sides crossed the
   network, and the join stage read all **243**. On the recorded run one join
   task read 206 of them.
2. With `F.broadcast(plants)`. Expected: `BroadcastHashJoin` plus one
   `BroadcastExchange`, **one** `Exchange`, **two** jobs (one builds the
   broadcast: one stage, one task), main job stages **4, 4**. Only **8 records**
   crossed a shuffle: two regional partials per input partition.

Both give coastal 60 rows / 2352 and inland 180 rows / 5898. Write one sentence
on which shuffle disappeared and what replaced it.

## Task 4 — The hot key never splits

Measure rows per partition after `repartition(n, "plant")` for n = 4, 8, 16.

Expected: at most three non-empty partitions each time; the largest holds **at
least 180** rows (all of North) every time; the smallest largest-partition
across the three runs is exactly 180. Explain why adding partitions could not
reduce that floor. (Observed on the recorded run: 204/36 at n=4 because West
shared North's partition; 180/36/24 at 8 and 16.)

## Task 5 — A wrong fix and a real one

1. Wrong approach: `repartition(16)` (round-robin, no key) before a window
   `row_number()` partitioned by plant. Expected: the plan gains a
   `RoundRobinPartitioning(16)` exchange **and still** has the window's own
   `hashpartitioning(plant, 4)` exchange after it; the job now writes **480**
   shuffle records instead of 240, and the window task that reads the most
   still reads the same number of rows as without the round-robin (204 on the
   recorded run). Say why the extra shuffle bought nothing.
2. Real fix for a join: add `salt = crc32(event_id) % 4` to the facts, replicate
   the dimension once per salt, join on `(plant, salt)`. Expected: still a
   `SortMergeJoin` with two exchanges, but the largest partition is now **below
   180** (122 on the recorded run); the join still returns 240 rows and the same
   regional totals; the `(plant, salt)` group sizes match `expected/totals.json`.
   Then repeat with `spark.sql.shuffle.partitions = 8`: once the key is split,
   more partitions can spread the twelve groups further (largest 100 on the
   recorded run).

## Task 6 — Guard the collection

Write `safe_rows(df, max_rows)` that raises `ValueError("collection bound
exceeded: …")` when more than `max_rows` rows would reach the driver, and
returns the rows otherwise. Expected: the raw 240-row frame is refused at
`max_rows=50`; the three-row plant totals are returned. `df.count()` still
reports 240 without moving any row to the driver.

## Task 7 — Adaptive execution coalesces (one variable changed)

Turn `spark.sql.adaptive.enabled` on. Build the grouped sum of Task 2,
`explain()` it, run it, `explain()` it again.

Expected: before the action the root is `AdaptiveSparkPlan isFinalPlan=false`
and the exchange still says `hashpartitioning(plant, 4)`; after the action the
root says `isFinalPlan=true`, the final plan carries `AQEShuffleRead coalesced`,
the result has **1** partition and the last executed stage ran **1 task** that
read all 12 partial records, instead of 4 tasks. `spark.sql.shuffle.partitions`
still reads 4: the setting did not change, the runtime read its output
differently. Same totals.

## Task 8 — Adaptive execution switches the join, and the side is not stable

Restore the default broadcast threshold (10 MB) with adaptive execution on and
repeat the join of Task 3: the initial plan says `SortMergeJoin`, the final plan
says `BroadcastHashJoin`. Record which side was built (`BuildLeft` is the 240-row
fact side, `BuildRight` the dimension), then run the identical query five more
times on fresh DataFrames and record the side each time.

Expected: every run switches to a broadcast join, and the side is **not**
guaranteed to be the same: the committed evidence recorded BuildRight four times
and BuildLeft twice in six runs. Write one sentence on why a choice that varies
between two runs on identical 240-row data is not evidence about production
sizes.

## Task 9 — Cache changes the plan, not the answer

Filter North, `cache()`, count it (180), explain a grouped count by `line`:
expected `InMemoryTableScan` over `InMemoryRelation` with
`StorageLevel(disk, memory, deserialized, 1 replicas)` and the same number of
`Exchange` nodes as before caching. `unpersist()` and explain again: the
in-memory nodes are gone. Line counts: L1 64, L2 63, L3 53.

## Task 10 — Adaptive skew handling, made visible

With adaptive execution on and broadcast off, read back
`spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes` (expected
`268435456b`, 256 MB) and `...skewedPartitionFactor` (5.0). Predict whether the
204-row partition of the Task 3 sort-merge join is split. Then set the
threshold and `spark.sql.adaptive.advisoryPartitionSizeInBytes` to `1KB` (both
at once, deliberately: the split needs a target size smaller than the
partition) and run the join again.

Expected: at the defaults nothing is split (on this toy data adaptive execution
instead coalesced the join's four shuffle partitions into one task that read
all 243 records); at toy thresholds the final plan
reads `SortMergeJoin(skew=true)` over an `AQEShuffleRead coalesced and skewed`,
the join stage runs 3 tasks that read 102, 106 and 37 records instead of one
task reading 206, the total read grows to 245 because each piece of the split
partition re-reads its matching dimension rows, and the regional totals are
unchanged. Say why this is a demonstration of a mechanism and not a setting to
copy.

## Task 11 — Transfer to a balanced feed

Run Task 2 and Task 4 (n = 8) over `inspections_balanced.json`.

Expected: the operator outline of the grouped plan is **identical** to the
skewed one — a plan cannot see skew — while the partition distribution is
80/80/80 and the largest-partition share drops from 0.75 to 0.3333. Totals:
North 80 / 2752 / 154, South 80 / 2717 / 157, West 80 / 2330 / 185.
