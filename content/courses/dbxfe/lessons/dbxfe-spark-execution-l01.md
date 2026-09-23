<!-- section:dbxfe-spark-execution-l01-outcome -->

After this lesson you can read a Spark physical plan, predict its shuffle boundaries, stages and task counts before anything runs, and then check that prediction against what actually ran: jobs, stages, tasks, rows per partition and the shuffle records each task read. You can show with numbers why one hot key defeats more workers and more partitions, say what a broadcast, a salt, adaptive execution and a cache change, and design a one-variable experiment whose limits you state before anyone asks.

<!-- section:dbxfe-spark-execution-l01-start -->

Bring three ideas from [DataFrames, schemas, and column expressions](#/lesson/dbxfe-dataframes) and [Grain, joins, and execution behavior](#/lesson/dbxfe-grain-joins): a Column describes work rather than holding a value, an action is what asks for results, and a physical plan lists the operators Spark proposes. Every number below comes from the recorded run of lab L04: local Apache Spark 4.0.4 in `local[2]` mode on one machine, `spark.sql.shuffle.partitions` set to 4, a 240-row synthetic Cinderline inspection feed. None is a timing, and nothing ran on Databricks.

<!-- section:dbxfe-spark-execution-l01-model -->

A Spark application has one **driver** process and one or more **executor** processes. The driver holds the `SparkSession`, turns your transformations into a plan, splits the plan into **stages** and **tasks**, and sends tasks to executors, which compute and hold data. In `local[2]` the executor is a pool of two task slots inside the driver's own JVM: enough to observe every mechanism, useless for measuring speed.

A DataFrame is split into **partitions**, and a stage runs one **task** per partition. The lab loads 240 rows into four partitions of 60, so a filter runs four tasks, two at a time on two slots. Transformations (`filter`, `select`, `groupBy`, `join`) only extend the plan; nothing executes until an **action** (`collect`, `count`, `show`, a write) asks for output. The lab wrapped `explain()` in its own job group and counted zero jobs: you can read the plan before paying for it.

A **narrow** step, such as a filter or a projection, computes each output partition from exactly one input partition, so no row moves. A **wide** step needs rows from many partitions in one place: every North row for a grouped sum by plant, every matching key for a join. Spark satisfies it with a **shuffle**: tasks write rows out by destination partition, and the next stage's tasks read them back. The plan shows it as an `Exchange`, and every `Exchange` ends a stage.

<!-- section:dbxfe-spark-execution-l01-boundaries -->

Read a formatted plan from the bottom up: `Scan` supplies rows, `Filter` and `Project` change them in place, `HashAggregate` combines, `Exchange` moves. Everything between two exchanges runs pipelined inside one task per partition. A stage that reads the input has one task per input partition; a stage that reads a shuffle has `spark.sql.shuffle.partitions` tasks unless adaptive execution changes that at runtime.

The plan is a proposal. What ran is a separate fact: which stages executed, how many tasks each had, how many records each task read and wrote, whether it spilled. The Spark web UI's Stages tab shows those per stage and per task; the lab reads the same numbers through the status tracker and Spark's status store so its tests can assert them. Keep the two apart when you explain a slow query: "the plan has three exchanges" is planning evidence; "one join task read 206 of 243 records" is runtime evidence.

<!-- section:dbxfe-spark-execution-l01-worked -->

The lab's grouped sum, and the same regional sum joined to the three-row plant dimension two ways:

~~~python
totals = facts.groupBy("plant").agg(F.count("*").alias("rows"),
                                    F.sum("inspected_units").alias("inspected"),
                                    F.sum("defective_units").alias("defective"))
by_region = facts.join(plants, "plant").groupBy("region").agg(
    F.count("*").alias("rows"), F.sum("inspected_units").alias("inspected"))
by_region_bc = facts.join(F.broadcast(plants), "plant").groupBy("region").agg(
    F.count("*").alias("rows"), F.sum("inspected_units").alias("inspected"))
totals.explain(mode="formatted")
~~~

The grouped sum's outline as printed by local Spark 4.0.4; node 4's arguments read `hashpartitioning(plant#1, 4), ENSURE_REQUIREMENTS`:

~~~text
* HashAggregate (5)
+- Exchange (4)
   +- * HashAggregate (3)
      +- * Project (2)
         +- * Scan ExistingRDD (1)
~~~

| Query | Join operator | `Exchange` nodes | Executed stages (tasks) | Records crossing a shuffle |
|---|---|---|---|---|
| Grouped sum | none | 1 | 4, 4 | 12 partial rows |
| Regional sum, broadcast off | `SortMergeJoin` | 3 | 1, 4, 4, 4 | 243 rows, then 3 partials |
| Regional sum, `F.broadcast(plants)` | `BroadcastHashJoin` | 1 | 1 (broadcast job), then 4, 4 | 8 partials |

Each grouped map task wrote three partial rows, one per plant, and the reduce tasks read 8, 0, 4 and 0 of them. The broadcast removed the exchange over the 240 fact rows: one task collected the dimension and copied it to every task, and the join ran where the facts were scanned. Both joins return coastal 60 rows / 2352 and inland 180 / 5898.

<!-- section:dbxfe-spark-execution-l01-skew -->

Now the counterexample. Hash partitioning sends every row of one key to one partition. After `repartition(n, "plant")` the lab measured 204 and 36 rows at n = 4 (West shared North's slot), then 180, 36 and 24 at n = 8 and 16. The floor is the hot key, and a stage cannot finish before its longest task, so two slots, four or forty all wait for the task holding North. "More workers is always faster" fails with numbers.

A round-robin `repartition(16)` before a window partitioned by plant is the common wrong fix: the plan keeps the window's own `hashpartitioning(plant#1, 4)` exchange right after the new one, the job shuffled 480 records instead of 240, and the busiest window task still read 204. Salting changes the key instead: `salt = crc32(event_id) % 4` on the facts, the dimension replicated once per salt, the join on `(plant, salt)`. The largest partition fell to 122, and the join still returned 240 rows and the same regional totals.

<!-- section:dbxfe-spark-execution-l01-adaptive -->

With `spark.sql.adaptive.enabled` on, Spark materializes each shuffle, measures it and plans the rest. The grouped plan printed before its action reads `AdaptiveSparkPlan isFinalPlan=false` with four planned partitions; after the action it reads `isFinalPlan=true` with `AQEShuffleRead coalesced`, and one task read all 12 partials. With the default 10 MB broadcast threshold, the join's initial plan was a sort-merge join (a parallelized list gives the planner no usable size estimate) and every final plan was a `BroadcastHashJoin`, but the side it built changed between identical runs: `BuildLeft` twice and `BuildRight` four times in six. Adaptive skew-join handling split nothing at its defaults (a partition must exceed 256 MB and five times the median); with the threshold and advisory size scaled to 1 KB on the record, the plan read `SortMergeJoin(skew=true)` and three tasks read 102, 106 and 37 records instead of one reading 206.

<!-- section:dbxfe-spark-execution-l01-memory -->

Caching the North filter put `InMemoryTableScan` over `InMemoryRelation` at `StorageLevel(disk, memory, deserialized, 1 replicas)` into the next plan, left its exchange in place and changed no count. `collect()` serializes every row of a frame into the driver, one process with one heap; that is the ordinary way a driver runs out of memory, and `spark.driver.maxResultSize` (documented default 1g) aborts an action whose serialized results exceed it: a fuse, not a design. The lab's guard counts `df.limit(max_rows + 1)` and raises `ValueError` for the raw frame while returning the three plant totals; `count()` reports 240 without moving a row.

<!-- section:dbxfe-spark-execution-l01-task -->

Cinderline adds a fourth plant, East, with 600 inspection rows to the skewed feed (North 180, South 36, West 24) and keeps four input partitions, four shuffle partitions and adaptive execution off. Predict, without running: the `Exchange` nodes and executed stages for `groupBy("plant")`; the largest partition after `repartition(8, "plant")` and its share; whether `F.broadcast(plants)` still changes the exchange count; and what `repartition(32)` does to a slow window by plant. Then say which answers the plan alone could give and which needed a measurement.

<!-- section:dbxfe-spark-execution-l01-solution -->

The grouped sum still has one `Exchange hashpartitioning(plant, 4)` and two stages of 4 and 4 tasks: the plan depends on the operators and the settings, not on the rows. After `repartition(8, "plant")` the largest partition holds at least East's 600 of 840 rows, a share of at least 0.71, more if another plant hashes into the same slot; the partition id needs a run. The broadcast still drops the join's exchanges from three to one, because broadcasting is about the small side. `repartition(32)` adds a round-robin exchange and leaves the window's own exchange by plant, so one window task still reads all 600 East rows. Exchange and stage counts came from the plan; partition sizes and the wasted shuffle are runtime evidence.

<!-- section:dbxfe-spark-execution-l01-limits -->

A toy run on one machine with 240 rows proves operator structure, exchange counts, stage and task counts, shuffle records and partition membership; it proves nothing about duration, memory, spill or network on a cluster. Which partition a key lands in depends on Spark's hash function and version, and the adaptive build side varied between identical runs. "Always broadcast", "always cache" or "raise shuffle partitions" is not supported by any evidence here: each experiment changed one thing in one configuration. Databricks Runtime bundles its own Spark version and defaults, so read its optimization pages rather than assuming parity with this run.

<!-- section:dbxfe-spark-execution-l01-links -->

[Diagnose a slow query](#/lesson/dbxfe-m05-l02) applies the planned-versus-measured distinction to warehouse query profiles, latency and concurrency. [Grain, joins, and execution behavior](#/lesson/dbxfe-grain-joins) owns the correctness side of joins, which no physical strategy repairs.

<!-- section:dbxfe-spark-execution-l01-sources -->

Primary documentation titles and URLs were confirmed by search on 23 September 2026; page bodies could not be fetched in this build, and each source record says so. Official mechanisms, original guidance and fictional records are separate claims. Lab L04 (`content/exercises/lab-l04-plans-shuffle`) carries the fixtures, independent expected values, starter, reference solution and recorded evidence: 14 tests, 0 failures, 0 errors, 0 skips on Python 3.12.3, OpenJDK 21.0.10 and Apache Spark 4.0.4 in `local[2]`. Reading this lesson needs no installation, workspace or paid service.

<!-- section:dbxfe-spark-execution-l01-revisit -->

Work the checks, then review the linked cards. A revealed solution, a visited section or an opened plan does not record a pass; mark completion only when you choose, and keep assessment evidence separate from reading.
