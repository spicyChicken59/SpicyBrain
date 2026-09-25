### Purpose

This lab turns the module's diagrams into evidence you can read yourself. Over a 240-row synthetic Cinderline inspection feed you build a narrow chain, a grouped sum, the same join two ways, a window, a salted join and a cached filter. For each one you read the plan `explain()` prints, predict the expensive boundary, run one action, and compare the prediction with what Spark actually executed. All of the evidence is Spark's own: operator outlines, rows per partition from `spark_partition_id()`, jobs, stages and tasks from the status tracker, and the shuffle records every stage and task read and wrote (the *Shuffle Read* and *Shuffle Write* columns of the web UI, read from Spark's status store because the UI is disabled). Everything ran on local Apache Spark 4.0.4 in `local[2]` mode on one machine with `spark.sql.shuffle.partitions` set to 4. No number is a timing, and nothing ran on Databricks.

### The fixture

Two feeds share one schema (`event_id`, `plant`, `line`, `inspected_units`, `defective_units`) and one seeded generator; a three-row dimension maps North to inland and South and West to coastal.

| Feed | North | South | West | Rows with defects | Largest key share |
|---|---|---|---|---|---|
| `inspections.json` (skewed) | 180 rows, 5898 inspected, 336 defective | 36 / 1391 / 79 | 24 / 961 / 46 | 187 | 0.75 |
| `inspections_balanced.json` | 80 / 2752 / 154 | 80 / 2717 / 157 | 80 / 2330 / 185 | 198 | 0.3333 |

The skewed feed is loaded into four input partitions of 60 rows. Their North/South/West mix is 44/9/7, 42/11/7, 45/10/5 and 49/6/5: every partition holds every plant, which is why a grouped sum must move data. Every expected number comes from a plain-Python script that never imports Spark; the runner re-derives it and asserts the committed literals are identical, and it checks the one premise that script relies on (how `parallelize` slices a list) against the partition membership Spark reports.

### Task by task

**Narrow chain.** Filter `defective_units > 0` and select three columns. The formatted outline is `Project (3)` over `Filter (2)` over `Scan ExistingRDD (1)` and nothing else. Collecting it ran one job, one stage, four tasks and returned 187 rows; the rows kept per partition were 47, 48, 45 and 47, exactly each input slice's defective rows, because no row left its partition. Even `count()` plans an `Exchange SinglePartition`, because a count is an aggregation. Wrapping `explain()` in its own job group showed it started zero jobs: planning costs nothing.

**Grouped sum.** `groupBy("plant")` plans a partial `HashAggregate`, one `Exchange` whose arguments read `hashpartitioning(plant#1, 4), ENSURE_REQUIREMENTS`, and a final `HashAggregate`. Measured:

| Stage | Tasks | Shuffle records written | Shuffle records read, per task |
|---|---|---|---|
| map (scan, project, partial sums) | 4 | 12 (3 per task) | — |
| reduce (final sums) | 4 | — | 8, 0, 4, 0 |

Twelve partial rows crossed the boundary, not 240 raw rows. One reduce task received North's and West's partials, one received South's, and two received nothing: the reduce stage had four tasks because the setting says four, not because the data needed them.

**Join two ways.** With broadcast disabled, the regional sum plans a `SortMergeJoin` under three exchanges (fact side, dimension side, regional sum). Executed stages carried 1, 4, 4 and 4 tasks. The dimension stage wrote 3 records, the fact stage 240, and the join stage read all 243, one task reading 206 of them (North, West and their two dimension rows). With `F.broadcast(plants)` the plan becomes `BroadcastHashJoin Inner BuildRight` with one `BroadcastExchange` and one `Exchange`. A separate one-task job built the broadcast, the main job ran 4 and 4 tasks, and only 8 records crossed a shuffle: two regional partials per input partition. Both give coastal 60 rows / 2352 and inland 180 / 5898.

**The hot key never splits.** After `repartition(n, "plant")`:

| n | Rows per partition (id: rows) | Largest | Share |
|---|---|---|---|
| 4 | 0: 204, 2: 36 | 204 | 0.85 |
| 8 | 0: 180, 2: 36, 4: 24 | 180 | 0.75 |
| 16 | 0: 180, 10: 36, 12: 24 | 180 | 0.75 |

Hash partitioning sends every row of one key to one partition, so the largest partition never falls below North's 180 rows. More partitions, or more workers, cannot shorten the task that holds North.

**Wrong fix, real fix.** A round-robin `repartition(16)` before a window partitioned by plant adds a `RoundRobinPartitioning(16)` exchange and keeps the window's own `hashpartitioning(plant#1, 4)` exchange after it. The job wrote 480 shuffle records instead of 240, and the window tasks still read 204, 0, 36 and 0 rows: a full extra pass bought nothing. Salting changes the key: `salt = crc32(event_id) % 4` on the facts, the dimension replicated once per salt, the join on `(plant, salt)`. North splits into groups of 47, 41, 47 and 45 rows; rows per partition became 101, 11, 6 and 122 (share 0.5083), and with eight shuffle partitions the largest fell to 100. The join still returned 240 rows and the same regional totals.

**Adaptive execution.** With `spark.sql.adaptive.enabled` on, the grouped plan printed before its action reads `AdaptiveSparkPlan isFinalPlan=false` and still names four partitions; after the action it reads `isFinalPlan=true` with `AQEShuffleRead coalesced`, the result has one partition, and the last stage ran one task that read all 12 partial records. The setting still reads 4. With the default 10 MB broadcast threshold restored, the join's initial plan is a sort-merge join and every final plan was a `BroadcastHashJoin`, but the side it built changed between identical runs: six runs recorded `BuildLeft` twice and `BuildRight` four times. A choice that varies on identical toy data is not evidence about production sizes.

**Adaptive skew handling, made visible.** The skew-join threshold read back as `268435456b` (256 MB) with a factor of 5.0, so at the defaults nothing here was split; on this toy data adaptive execution instead coalesced the join into one task reading all 243 records. With the threshold and the advisory partition size scaled down to 1 KB, on the record, the final plan read `SortMergeJoin(skew=true)` over `AQEShuffleRead coalesced and skewed`, and the join stage ran three tasks reading 102, 106 and 37 records instead of one task reading 206. The total rose to 245 because each piece of the split partition re-read its dimension rows. Totals were unchanged. That demonstrates a mechanism; 1 KB is not a setting to copy.

**Cache.** Filtering North, caching and counting (180) makes the next grouped plan read `InMemoryTableScan` over `InMemoryRelation` at `StorageLevel(disk, memory, deserialized, 1 replicas)` with the same number of exchanges; after `unpersist()` the in-memory nodes are gone. Line counts: L1 64, L2 63, L3 53.

### The failure case

`bounded_collect(df, max_rows)` counts `df.limit(max_rows + 1)` first and raises `ValueError("collection bound exceeded: more than 50 rows would reach the driver")` for the raw frame, while returning the three plant totals. The test asserts the exception and its message, then confirms `count()` still reports 240 without moving a row. `collect()` on an unbounded frame is the ordinary way a driver runs out of memory.

### Transfer

On the balanced feed the grouped plan's operator outline is identical to the skewed feed's: a plan cannot see skew. The distribution at n = 8 is 80 / 80 / 80 and the largest share drops from 0.75 to 0.3333; totals match their own derivation.

### What the tests prove and do not prove

They prove, for Spark 4.0.4 in `local[2]` with four shuffle partitions: operator names and exchange counts, executed jobs, stages and task counts, shuffle records per stage and per task, partition-membership properties (a key never splits; salting reduces the largest partition), exact rows and totals, and the raised guard. They record rather than require where a key's partition id lands and which side adaptive execution broadcasts, because the first depends on Spark's hash function and the second varied between identical runs. They do not prove any duration, memory use, spill, network cost, behaviour on another Spark version, or anything about a cluster, and shuffle bytes are recorded but never asserted.

### Setup, run and cleanup

Create a Python 3.12 virtual environment, `pip install -r requirements.txt` (PySpark 4.0.4, Py4J 0.10.9.9), point `JAVA_HOME` at a Java 17 or 21 JDK, then run `python run_tests.py --evidence local-evidence.json`. The recorded run used Python 3.12.3 and OpenJDK 21.0.10: 14 tests, 0 failures, 0 errors, 0 skips, exit 0. The runner sets `PYSPARK_PYTHON` to its own interpreter, sends Spark's temporary files to a directory it creates, and deletes that directory after stopping Spark; it writes nothing else except the evidence file you name. Delete the virtual environment and that file when finished. Studying this page needs no installation.
