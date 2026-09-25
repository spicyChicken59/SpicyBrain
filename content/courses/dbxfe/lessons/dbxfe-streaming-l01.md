<!-- section:dbxfe-streaming-l01-outcome -->

After this lesson you can explain a Structured Streaming query as an incremental query over a table that keeps growing; predict, for each micro-batch, the watermark, the windows it finalizes and whether a late row counts; read a checkpoint to see what a restart will replay; and say where exactly-once holds and where a downstream effect needs an idempotency key. Every number here comes from lab L08, a real and bounded run of local Apache Spark 4.0.4 over five small files that land in a fixed order. Nothing in it ran on Databricks.

<!-- section:dbxfe-streaming-l01-start -->

Bring grouping and joins in SQL and PySpark ([DataFrames, schemas, and column expressions](#/lesson/dbxfe-dataframes)), the difference between the order records arrive in and the order they describe ([Identity, ordering, and incremental inputs](#/lesson/dbxfe-m04-l02)), and the idea of a commit log ([Delta tables: files, log, and snapshots](#/lesson/dbxfe-m03-l02)). Retries and reconciliation in general are covered in [Orchestration, failure, and reconciliation](#/lesson/dbxfe-m04-l03); this lesson is about what a streaming engine itself remembers.

<!-- section:dbxfe-streaming-l01-model -->

Structured Streaming treats a stream as an input table that keeps receiving rows and runs your query on it incrementally. By default each **micro-batch** is a small batch job over the rows that arrived since the last one, combined with state kept from earlier batches.

```python
events = (spark.readStream.schema("event_id STRING, line STRING, event_time TIMESTAMP, units INT")
          .option("maxFilesPerTrigger", 1).json(landing_dir))
```

The **trigger** sets the timing: none (the next batch as soon as the previous ends), a fixed interval, or `availableNow=True`, which drains what is present in one or more batches and stops. The once trigger is deprecated and continuous processing is experimental. The lab's second run read 4 rows, not 10: committed files are never planned again.

<!-- section:dbxfe-streaming-l01-time -->

**Event time** is when the press counted the parts; processing time is when the file landed. Grouped by event time, L1 made 36 units in 09:00-09:10; grouped by landing time the same window is empty, because the first file landed at 09:13.

A **window** is a grouping key on event time: tumbling windows do not overlap, sliding windows do, so an event can be in two. The **watermark** is the latest event time seen minus a declared delay, recomputed after every micro-batch; a window is final once the watermark reaches its end.

| After | Latest event | Watermark (5 min) | Final windows |
|---|---|---|---|
| 01.json | 09:12:40 | 09:07:40 | none |
| 02.json | 09:18:30 | 09:13:30 | 09:00 |
| 03.json | 09:27:00 | 09:22:00 | 09:10 |

<!-- section:dbxfe-streaming-l01-state -->

The **state store** keeps one row per open window and line and drops it once the watermark passes the window's end. Lateness is judged per window: e008 (09:05:00) was older than its batch's 09:07:40 watermark but counted, because its window ended at 09:10. e011 (09:03:00) arrived after its window had been emitted, and Spark reported `numRowsDroppedByWatermark = 1`. The documented guarantee is one-directional: rows within the delay are never dropped; later rows may or may not count.

The **output mode** decides what the sink sees: append writes each window once when final (an aggregation needs a watermark for it), update writes windows that changed, complete rewrites everything and never drops state.

<!-- section:dbxfe-streaming-l01-joins -->

A stream-static join matches each micro-batch against a static table and keeps no state; the lab adds each event's plant from a three-row line table. A stream-stream join must buffer both inputs, because a row can match one that has not arrived. Watermarks on both sides and an event-time range, such as a ticket within 30 minutes of a stop, let Spark discard buffered rows. Outer and semi joins must declare them, and outer NULL rows appear only after the delay and range have passed. Queries with joins use append mode.

<!-- section:dbxfe-streaming-l01-recovery -->

A checkpoint is one query's directory. Before a batch runs, Spark writes `offsets/N`: the source offsets it will read and the watermark it will use. After the sink returns, it writes `commits/N`. State versions and the file-source log sit beside them.

A restart on the same checkpoint with the same query finishes any batch that has an offset entry but no commit, with the same plan, then reads only new data. It cannot absorb a change to the number or type of sources or to a stateful operation's schema, and it keeps recorded settings such as the shuffle partition count. Deleting or moving the checkpoint starts a new query from scratch.

<!-- section:dbxfe-streaming-l01-sinks -->

End-to-end exactly-once needs a replayable source, the checkpointed engine and an idempotent sink. The file sink is exactly-once; Kafka and foreach sinks are at-least-once; `foreachBatch` is at-least-once unless your function deduplicates. A replayed batch arrives with the same id and the same rows, and everything the first attempt did outside Spark happens again. Key each external effect by its business identity, here the window start and line, and record the key in the same step as the effect.

<!-- section:dbxfe-streaming-l01-example -->

Scenario S lands one file per run on one checkpoint; the sink is armed to fail once, after sending, in the batch that finalizes the 09:20 windows.

| Run | Batches | Watermark | Sink receives |
|---|---|---|---|
| 01 | 0, 1 | 09:07:40 | nothing |
| 02 | 2, 3 | 09:13:30 | 09:00 L1 27, L2 23 |
| 03 | 4, 5 | 09:22:00 | 09:10 L1 21, L2 18; e011 dropped |
| 04 | 6, 7 (fails) | 09:33:00 | 09:20 L1 6, L2 4, L3 2, then error |
| restart | 7 again | 09:33:00 | the same three rows again |
| restart | none | — | nothing |
| 05 | 8, 9 | 09:41:00 | 09:30 L2 3, L3 5 |

After the failure the checkpoint held offsets 0-7 and commits 0-6. At the end the naive outbox held 12 messages for 9 windows, the keyed outbox 9, and 09:40 L1 (8 units) was still waiting in state.

<!-- section:dbxfe-streaming-l01-exercise -->

Put all five files in the landing directory first, then start one `availableNow` run on a fresh checkpoint with the same query. One file is read per micro-batch and no no-data batch runs between files. Predict, before looking: how many micro-batches run, which watermark batch 2 uses when it reads 03.json, whether e011 counts, and what 09:00 L1 is emitted as. Then compare with scenario S and say which of the two results the documented guarantee allows.

<!-- section:dbxfe-streaming-l01-solution -->

Six micro-batches run: one per file, then a final no-data batch. Batch 2 reads 03.json under the watermark 09:13:30, but no batch between 02.json and 03.json had evicted the 09:00 window, so it was still in state. In local Spark 4.0.4 late rows are compared with the previous batch's watermark (09:07:40), and 09:10 is later, so e011 is counted; eviction then uses 09:13:30 and emits 09:00 L1 as **36 / 4**, where scenario S emitted 27 / 3. Both results are allowed: e011 is later than the 5-minute delay, and only rows within the delay are guaranteed. Lab test 07 confirmed the attribution with an internal setting that is not a recommendation.

<!-- section:dbxfe-streaming-l01-mistakes -->

- **Treating the watermark as a per-row cutoff.** It closes windows; a row older than it can still count.
- **Grouping by arrival time for a business report.** Delivery delay moves units into the wrong window.
- **Summing sliding windows.** Overlapping rows count each event more than once.
- **Removing the watermark to keep every late row.** Append refuses the query; other modes grow state forever.
- **Trusting the checkpoint for side effects.** It makes processing exactly-once, not your HTTP calls.
- **Deleting a checkpoint to clear an error.** That starts a new query that rereads the source.
- **Changing an aggregation and restarting.** The saved state no longer fits; plan a new checkpoint.

<!-- section:dbxfe-streaming-l01-sources -->

The mechanism follows the Apache Spark 4.0.4 [Structured Streaming Programming Guide](https://spark.apache.org/docs/4.0.4/streaming/index.html), especially its [programming model](https://spark.apache.org/docs/4.0.4/streaming/getting-started.html) and [API page](https://spark.apache.org/docs/4.0.4/streaming/apis-on-dataframes-and-datasets.html) (windows, watermarks, output modes, sinks, triggers, recovery), read from the guide's source at the v4.0.4 tag. Databricks context comes from [Structured Streaming checkpoints](https://docs.databricks.com/aws/en/structured-streaming/checkpoints) and [Use foreachBatch to write to arbitrary data sinks](https://docs.databricks.com/aws/en/structured-streaming/foreach). All numbers come from lab L08's recorded local run; the update and complete outputs and the stream-stream join are derived or schematic and were not executed.

<!-- section:dbxfe-streaming-l01-related -->

Recovery after failures in scheduled work continues in [Orchestration and operations](#/module/dbxfe-orchestration), and the commit log idea comes from [Delta Lake: files, log and snapshots](#/module/dbxfe-delta). Record identity and replay are in [Ingestion, records and reliable updates](#/module/dbxfe-m04). The declarative pipelines module builds streaming tables on the same engine, and the Delta writes module covers what a keyed MERGE does to a table.

<!-- section:dbxfe-streaming-l01-revisit -->

Come back to three questions: after 04.json, which watermark closes the 09:20 windows and why did they reach the sink twice? If a file had landed with an event at 09:50, which window would leave the state store? And if the sink's effect were a database write rather than a message, what would make the replay harmless? Then rerun lab L08 with a 15-minute delay and compare what changes.
