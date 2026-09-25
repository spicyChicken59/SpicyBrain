# Solutions — with intermediate outputs from the recorded run

Everything below was executed on local Apache Spark 4.0.4, `local[2]`, one
machine, `spark.sql.shuffle.partitions = 4`. Plan outlines and plan lines are
copied verbatim from the committed evidence
(`docs/academy/labs/lab-l04-plans-shuffle.json`, under `observations`); `…`
marks lines left out, never text changed. Shuffle records per stage and per
task are Spark's own metrics (the web UI's *Shuffle Read* and *Shuffle Write*),
read from its status store. Nothing here is a benchmark.

## Task 1 — narrow chain

```python
narrow = df.filter(F.col("defective_units") > 0).select("event_id", "plant", "defective_units")
```

Formatted plan outline:

```text
* Project (3)
+- * Filter (2)
   +- * Scan ExistingRDD (1)
```

No `Exchange`; 4 partitions in, 4 out; `collect()` ran 1 job, 1 stage, 4
tasks; 187 rows. Rows per output partition: 0: 47, 1: 48, 2: 45, 3: 47 —
exactly the defective rows of each input slice, because each task read one
input partition and wrote its own output: that is a narrow dependency. The
input slices themselves held North/South/West
44/9/7, 42/11/7, 45/10/5, 49/6/5
rows, as the derivation's premise predicted. And `narrow.groupBy().count()`
plans:

```text
*(2) HashAggregate(keys=[], functions=[count(1)])
+- Exchange SinglePartition, ENSURE_REQUIREMENTS, [plan_id=103]
   +- *(1) HashAggregate(keys=[], functions=[partial_count(1)])
      +- *(1) Project
         +- *(1) Filter (defective_units#4L > 0)
            +- *(1) Scan ExistingRDD[event_id#0,plant#1,line#2,inspected_units#3L,defective_units#4L]
```

A count is an aggregation, so it has its own boundary, to one partition.

## Task 2 — grouped sum

```python
totals = df.groupBy("plant").agg(F.count("*").alias("rows"),
                                 F.sum("inspected_units").alias("inspected"),
                                 F.sum("defective_units").alias("defective"))
```

`explain()` inside its own job group started 0 jobs. The outline, then the
details of nodes 3 and 4:

```text
* HashAggregate (5)
+- Exchange (4)
   +- * HashAggregate (3)
      +- * Project (2)
         +- * Scan ExistingRDD (1)

(3) HashAggregate [codegen id : 1]
Input [3]: [plant#1, inspected_units#3L, defective_units#4L]
Keys [1]: [plant#1]
Functions [3]: [partial_count(1), partial_sum(inspected_units#3L), partial_sum(defective_units#4L)]
Aggregate Attributes [3]: [count#51L, sum#52L, sum#53L]
Results [4]: [plant#1, count#54L, sum#55L, sum#56L]

(4) Exchange
Input [4]: [plant#1, count#54L, sum#55L, sum#56L]
Arguments: hashpartitioning(plant#1, 4), ENSURE_REQUIREMENTS, [plan_id=133]
```

Measured: 1 job; executed stages of 4 tasks then 4 tasks. The map stage wrote
12 records (3, 3, 3, 3 per task: one partial row per plant per input
partition); the reduce stage read them as 8, 0, 4, 0 per task. So one reduce task
received North's and West's four partials each, one received South's, two
received nothing, and the stage still had four tasks because
`spark.sql.shuffle.partitions` is four, not because of the data. Result: North
180 / 5898 / 336; South 36 / 1391 / 79; West 24 / 961 / 46.

## Task 3 — join two ways

Sort-merge (broadcast disabled):

```text
* HashAggregate (14)
+- Exchange (13)
   +- * HashAggregate (12)
      +- * Project (11)
         +- * SortMergeJoin Inner (10)
            :- * Sort (4)
            :  +- Exchange (3)
            :     +- * Project (2)
            :        +- * Scan ExistingRDD (1)
            +- * Sort (9)
               +- Exchange (8)
                  +- * Project (7)
                     +- * Filter (6)
                        +- * Scan ExistingRDD (5)
```

The three `Exchange` nodes (3, 8, 13) are `hashpartitioning(plant#1, 4)` over
the facts, `hashpartitioning(plant#10, 4)` over the dimension, and
`hashpartitioning(region#11, 4)` for the regional sum. Measured: 1 job; executed
stages with 1, 4, 4, 4 tasks. Shuffle records: the one-task dimension stage
wrote 3, the four fact tasks wrote 240 (60, 60, 60, 60), the join stage read
243 as 206, 0, 37, 0 per task and wrote 3 regional partials, and the last
stage read those 3. One join task read 206 records: North's 180 facts, West's 24
and both of their dimension rows.

Broadcast (`F.broadcast(plants)`):

```text
* HashAggregate (11)
+- Exchange (10)
   +- * HashAggregate (9)
      +- * Project (8)
         +- * BroadcastHashJoin Inner BuildRight (7)
            :- * Project (2)
            :  +- * Scan ExistingRDD (1)
            +- BroadcastExchange (6)
               +- * Project (5)
                  +- * Filter (4)
                     +- * Scan ExistingRDD (3)
```

One `Exchange` plus one `BroadcastExchange`; **two** jobs: a one-stage, one-task
job collects the dimension and broadcasts it (no shuffle records), then the main
job runs 4 and 4 tasks. Only 8 records crossed a shuffle
(2, 2, 2, 2 per map task: one partial per region per input partition). The fact-side
shuffle disappeared; the join happened inside the task that scanned the facts.
Both joins give coastal 60 / 2352 and inland 180 / 5898.

## Task 4 — the hot key never splits

`repartition(n, "plant")` then rows per `spark_partition_id()`:

| n | rows per partition (id: rows) | largest | share |
|---|---|---|---|
| 4 | 0: 204, 2: 36 | 204 | 0.85 |
| 8 | 0: 180, 2: 36, 4: 24 | 180 | 0.75 |
| 16 | 0: 180, 10: 36, 12: 24 | 180 | 0.75 |

Hash partitioning sends every row with the same key to one partition. With
four partitions West happened to share North's slot (204); with more partitions
the collision disappeared, but North's 180 rows are still one task's work. The
floor is the hot key, and no partition count moves it: more workers would sit
idle while one finishes North.

## Task 5 — wrong fix, real fix

**Wrong:** `df.repartition(16)` before
`row_number().over(Window.partitionBy("plant").orderBy("event_id"))`.

```text
Window (5)
+- * Sort (4)
   +- Exchange (3)
      +- Exchange (2)
         +- * Scan ExistingRDD (1)
```

Node 2 is `RoundRobinPartitioning(16), REPARTITION_BY_NUM` and node 3 is
`hashpartitioning(plant#1, 4), ENSURE_REQUIREMENTS`. Without the round-robin
the window job wrote 240 shuffle records and its window tasks read
204, 0, 36, 0. With it the job wrote 480: the 16 round-robin tasks each read
14–16 rows, and then the window's own exchange re-collected the key, so the
window tasks read 204, 0, 36, 0 again. The extra shuffle cost a full pass over the data and
bought nothing.

**Real (for a join):** salt the facts, replicate the dimension.

```python
fact = df.withColumn("salt", (F.crc32(F.col("event_id")) % 4).cast("int"))
salts = spark.range(4).select(F.col("id").cast("int").alias("salt"))
joined = fact.join(plants.crossJoin(salts), ["plant", "salt"])
```

```text
* Project (14)
+- * SortMergeJoin Inner (13)
   :- * Sort (5)
   :  +- Exchange (4)
   :     +- * Project (3)
   :        +- * Filter (2)
   :           +- * Scan ExistingRDD (1)
   +- * Sort (12)
      +- Exchange (11)
         +- CartesianProduct Inner (10)
            :- * Filter (7)
            :  +- * Scan ExistingRDD (6)
            +- * Project (9)
               +- * Range (8)
```

Still a `SortMergeJoin` with two exchanges (`hashpartitioning(plant#1, salt#…, 4)`
and `hashpartitioning(plant#10, salt#…, 4)`), but rows per partition became
0: 101, 1: 11, 2: 6, 3: 122 — the largest fell from 204 to 122 (share
0.5083). Four salts split North into groups of 47, 41, 47 and 45 rows;
hash collisions among the twelve `(plant, salt)` groups in four partitions explain
why 122 is not 47. With `spark.sql.shuffle.partitions = 8` the same join gave
0: 88, 1: 11, 3: 100, 4: 13, 6: 6, 7: 22 (largest 100): once the key is split, more
partitions help. The join still returns 240 rows and the same regional totals,
because each fact row meets exactly one replica of its plant. The cost is a
12-row dimension instead of 3 and a plan that a reader must now understand.

## Task 6 — guard the collection

```python
def bounded_collect(df, max_rows):
    arriving = df.limit(max_rows + 1).count()
    if arriving > max_rows:
        raise ValueError(f"collection bound exceeded: more than {max_rows} rows would reach the driver")
    return [row.asDict() for row in df.collect()]
```

The raw frame is refused at 50 (`ValueError: collection bound exceeded: more
than 50 rows would reach the driver`); the three plant totals come back. The
count of the raw frame (240) is computed by the executors and returns one
number. `collect()` on an unbounded frame is how a driver runs out of memory:
every row is serialized and sent to one process.

## Task 7 — adaptive execution coalesces

Before the action (simple mode):

```text
AdaptiveSparkPlan isFinalPlan=false
+- HashAggregate(keys=[plant#1], functions=[count(1), sum(inspected_units#3L), sum(defective_units#4L)])
   +- Exchange hashpartitioning(plant#1, 4), ENSURE_REQUIREMENTS, [plan_id=1310]
      +- HashAggregate(keys=[plant#1], functions=[partial_count(1), partial_sum(inspected_units#3L), partial_sum(defective_units#4L)])
         +- Project [plant#1, inspected_units#3L, defective_units#4L]
            +- Scan ExistingRDD[event_id#0,plant#1,line#2,inspected_units#3L,defective_units#4L]
```

After the action (final plan; the initial plan printed below it repeats the one above):

```text
AdaptiveSparkPlan isFinalPlan=true
+- == Final Plan ==
   ResultQueryStage 1
   +- *(2) HashAggregate(keys=[plant#1], functions=[count(1), sum(inspected_units#3L), sum(defective_units#4L)])
      +- AQEShuffleRead coalesced
         +- ShuffleQueryStage 0
            +- Exchange hashpartitioning(plant#1, 4), ENSURE_REQUIREMENTS, [plan_id=1321]
               +- *(1) HashAggregate(keys=[plant#1], functions=[partial_count(1), partial_sum(inspected_units#3L), partial_sum(defective_units#4L)])
                  +- *(1) Project [plant#1, inspected_units#3L, defective_units#4L]
                     +- *(1) Scan ExistingRDD[event_id#0,plant#1,line#2,inspected_units#3L,defective_units#4L]
```

The planned exchange still says 4 partitions; the runtime read them back as one
(`coalesced`). The map stage wrote the same 12 records (789 bytes of shuffle
output), the result has 1 partition, and the last executed stage ran 1 task that
read all 12 records, where the non-adaptive run ran 4. `spark.sql.shuffle.partitions`
still read 4 afterwards. The status tracker shows the adaptive run as two jobs
with one skipped stage: adaptive execution materializes the shuffle, looks at
its statistics, then plans the rest. Same totals.

## Task 8 — the join switches, and the side is not stable

With the default 10 MB threshold the initial plan is the sort-merge join above
(a parallelized list gives the planner no usable size estimate). The first run's final plan:

```text
AdaptiveSparkPlan isFinalPlan=true
+- == Final Plan ==
   ResultQueryStage 4
   +- *(4) HashAggregate(keys=[region#11], functions=[count(1), sum(inspected_units#3L)])
      +- AQEShuffleRead coalesced
         +- ShuffleQueryStage 3
            +- Exchange hashpartitioning(region#11, 4), ENSURE_REQUIREMENTS, [plan_id=1522]
               +- *(3) HashAggregate(keys=[region#11], functions=[partial_count(1), partial_sum(inspected_units#3L)])
                  +- *(3) Project [inspected_units#3L, region#11]
                     +- *(3) BroadcastHashJoin [plant#1], [plant#10], Inner, BuildLeft, false
                        :- BroadcastQueryStage 2
                        :  +- BroadcastExchange HashedRelationBroadcastMode(List(input[0, string, false]),false), [plan_id=1458]
                        :     +- AQEShuffleRead local
                        :        +- ShuffleQueryStage 0
                        :           +- Exchange hashpartitioning(plant#1, 4), ENSURE_REQUIREMENTS, [plan_id=1408]
                        :              +- *(1) Project [plant#1, inspected_units#3L]
                        :                 +- *(1) Scan ExistingRDD[event_id#0,plant#1,line#2,inspected_units#3L,defective_units#4L]
                        +- AQEShuffleRead local
                           +- ShuffleQueryStage 1
                              +- Exchange hashpartitioning(plant#10, 4), ENSURE_REQUIREMENTS, [plan_id=1415]
                                 +- *(2) Project [plant#10, region#11]
                                    +- *(2) Filter isnotnull(plant#10)
                                       +- *(2) Scan ExistingRDD[plant#10,region#11,manager_code#12]
```

Across the six runs of the identical query on fresh DataFrames the recorded
build sides were BuildLeft, BuildLeft, BuildRight, BuildRight, BuildRight, BuildRight (BuildLeft 2, BuildRight 4). `BuildLeft` broadcasts the 240-row
fact side, `BuildRight` the dimension. Spark documents that adaptive execution
converts a sort-merge join when the runtime statistics of *any* join side fall
below the threshold; the two input shuffles run concurrently, so whichever
finishes first is the likely reason the side varies — the lab records the
variation, it does not prove the cause. A choice that changes between two runs
on identical toy data says nothing about which side production sizes would
favour.

## Task 9 — cache

```text
* HashAggregate (7)
+- Exchange (6)
   +- * HashAggregate (5)
      +- InMemoryTableScan (1)
            +- InMemoryRelation (2)
                  +- * Filter (4)
                     +- * Scan ExistingRDD (3)
```

Node 2's arguments end in `StorageLevel(disk, memory, deserialized, 1 replicas)`.
North has 180 rows: L1 64, L2 63, L3 53. After `unpersist()` a fresh
plan shows `Scan` and `Filter` again. A cache changes where the input comes
from; it does not change the answer, and it does not remove the grouped exchange.

## Task 10 — adaptive skew handling, made visible

Read back before anything changed: skew threshold
`268435456b`, factor
`5.0`, advisory partition size
`67108864b`, coalescing minimum
`1048576b`.

At those defaults, with adaptive execution on and broadcast off, the join stayed
a plain `SortMergeJoin`, and because the whole shuffle was far below the 1 MB
coalescing minimum, the runtime read the join's four partitions as **one** task
that read all 243 records: on toy data, adaptive execution removes the parallelism
question rather than answering it.

With the threshold and the advisory size both set to `1KB`:

```text
AdaptiveSparkPlan isFinalPlan=true
+- == Final Plan ==
   ResultQueryStage 3
   +- *(6) HashAggregate(keys=[region#11], functions=[count(1), sum(inspected_units#3L)])
      +- AQEShuffleRead coalesced
         +- ShuffleQueryStage 2
            +- Exchange hashpartitioning(region#11, 4), ENSURE_REQUIREMENTS, [plan_id=3499]
               +- *(5) HashAggregate(keys=[region#11], functions=[partial_count(1), partial_sum(inspected_units#3L)])
                  +- *(5) Project [inspected_units#3L, region#11]
                     +- *(5) SortMergeJoin(skew=true) [plant#1], [plant#10], Inner
                        :- *(3) Sort [plant#1 ASC NULLS FIRST], false, 0
                        :  +- AQEShuffleRead coalesced and skewed
                        :     +- ShuffleQueryStage 0
                        :        +- Exchange hashpartitioning(plant#1, 4), ENSURE_REQUIREMENTS, [plan_id=3371]
                        :           +- *(1) Project [plant#1, inspected_units#3L]
                        :              +- *(1) Scan ExistingRDD[event_id#0,plant#1,line#2,inspected_units#3L,defective_units#4L]
                        +- *(4) Sort [plant#10 ASC NULLS FIRST], false, 0
                           +- AQEShuffleRead coalesced
                              +- ShuffleQueryStage 1
                                 +- Exchange hashpartitioning(plant#10, 4), ENSURE_REQUIREMENTS, [plan_id=3378]
                                    +- *(2) Project [plant#10, region#11]
                                       +- *(2) Filter isnotnull(plant#10)
                                          +- *(2) Scan ExistingRDD[plant#10,region#11,manager_code#12]
```

The join is marked `SortMergeJoin(skew=true)` and the fact side is read through
`AQEShuffleRead coalesced and skewed`. The join stage ran 3 tasks that read
102, 106, 37 records: the North-and-West partition was split into two pieces, and
each piece re-read the matching dimension rows, which is why the total read is
245 instead of 243. The largest task read 106 records where the
non-adaptive join's largest read 206. Totals unchanged. This shows the mechanism; the
thresholds exist because splitting has a cost, and 1 KB is a toy value, not a
setting to copy.

## Task 11 — balanced transfer

The grouped plan's operator outline is identical to the skewed feed's
(`HashAggregate, Exchange, HashAggregate, Project, Scan`); a plan cannot see
skew. `repartition(8, "plant")` gives 0: 80, 2: 80, 4: 80 (share 0.3333). Totals:
North 80 / 2752 / 154, South 80 / 2717 / 157, West 80 / 2330 / 185; coastal
160 / 5047, inland 80 / 2752.

## The wrong approach, named once more

"Give it more partitions" (Task 4) and "spread the input first" (Task 5) both
fail for the same reason: the operator that needs a key together will shuffle
by that key regardless, and one task inherits every row of the hot key. Only a
change of key (salting), a change of strategy (broadcast, when one side is
small enough), or a runtime split of oversized partitions (adaptive skew-join
handling, which at its defaults engages only above 256 MB and five times the
median partition) changes that.
