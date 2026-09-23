### Purpose

This lab runs a real Structured Streaming query and makes it restart. Five small files of synthetic Cinderline press-line counts are moved, one at a time and in a fixed order, into a directory that Spark's file source watches. A windowed aggregation with a watermark turns the counts into 10-minute totals per line, a checkpoint records what each micro-batch planned and committed, and a `foreachBatch` function hands every finished window to two stand-ins for downstream systems. Every run is bounded by `trigger(availableNow=True)`, which processes what is present and stops by itself; nothing sleeps and no Python loop pretends to be a stream. All numbers below are Spark's own output from the recorded run on local Apache Spark 4.0.4 in `local[2]` mode on one machine. Nothing ran on Databricks and no number is a timing.

### The fixture

Eighteen count events in five JSON Lines files. Each file is stamped with its landing time before it is renamed into the landing directory, so the file source sees it appear whole and orders it by that time.

| File | Lands | Events (line, event time, units) | Why it is there |
|---|---|---|---|
| 01 | 09:13 | six events 09:00:30 to 09:12:40, lines L1 and L2 | on-time counts |
| 02 | 09:19 | e007 L1 09:09:30 5, e008 L2 09:05:00 6, e009, e010 | late but inside an open window |
| 03 | 09:28 | e011 L1 09:03:00 9, e012, e013, e014 (first L3) | e011 arrives 25 minutes late |
| 04 | 09:39 | e015 L3 09:38:00 5, e016 L2 09:21:00 4 | closes the 09:20 windows |
| 05 | 09:47 | e017 L1 09:46:00 8, e018 L2 09:35:00 3 | arrives after the restart |

The query keeps a 5-minute watermark on `event_time`, groups by a 10-minute window and line, writes in append mode and reads one file per micro-batch. Every expected value was written by hand before the final run; the batch truths are also re-derived by a plain-Python script that never imports Spark.

### Task by task

**Arrival 01.** Batch 0 reads 6 rows under the initial watermark (1970-01-01 00:00:00) and keeps 4 windows in state. Batch 1 reads nothing: availableNow ran a no-data batch because the watermark moved to 09:07:40. The sink receives no rows, since no window ends by then.

**Arrival 02, a restart.** Batch 2 reads only 02.json's 4 rows; the checkpoint's file-source log maps source offset 1 to that file alone. e008 happened at 09:05:00, older than the 09:07:40 watermark in force, yet it counts, because its window ends at 09:10. Batch 3 moves the watermark to 09:13:30 and emits 09:00 L1 as 27 units / 3 events and L2 as 23 / 3.

**Arrival 03.** Batch 4 reports one row dropped by the watermark: e011 belongs to the 09:00 window, which is gone. The emitted 27 stays 27, while the event-time truth is 36. Batch 5 (watermark 09:22:00) emits the 09:10 windows, 21 / 2 and 18 / 3.

**Arrival 05, after the failure below.** Batch 8 reads only 05.json's 2 rows; batch 9 (watermark 09:41:00) emits the 09:30 windows, 3 / 1 and 5 / 1. One window never leaves state: 09:40 L1 with 8 units, because no later event moves the watermark past 09:50.

The state store was read back after each batch with Spark's experimental state data source; after batch 6, for example, it held 09:20 L1 6, L2 4, L3 2 and 09:30 L3 5.

### The failure case

On arrival 04 the sink is armed to raise after it has sent its messages for the 09:20 windows. The query fails with `STREAM_FAILED` wrapping `FOREACH_BATCH_USER_FUNCTION_ERROR`. The checkpoint now holds offset entries 0 to 7 but commits 0 to 6: batch 7 was planned (watermark 09:33:00, source offset 3) and its rows delivered, but never committed. The first restart replays batch 7 with the same id and the same three rows and writes the commit; the second restart plans nothing (Spark posts one progress report numbered 8 with zero rows, writes no offset file and never calls the sink).

| Downstream stand-in | After the failure | After the replay | At the end |
|---|---|---|---|
| naive outbox (appends every message) | 7 | 10 | 12 for 9 windows |
| keyed outbox (sends a window and line key once) | 7 | 7 | 9 |

Spark processed batch 7 exactly once; the naive effect happened twice. Two further refusals are asserted for their reason: append mode without a watermark raises `STREAMING_OUTPUT_MODE.UNSUPPORTED_OPERATION` at `start()`, and restarting with one more aggregate fails with `STATE_STORE_VALUE_SCHEMA_NOT_COMPATIBLE`.

### Transfer

**Same files as a backlog.** With all five files present before one run, six micro-batches run and 09:00 L1 is emitted as 36 / 4: no batch evicted the window between files, so e011 was counted. The run showed late rows compared with the previous batch's watermark (09:07:40) while state is evicted with the current one (09:13:30); an internal Spark setting, used only to confirm this, made the backlog drop e011 again. Both outcomes are within the documented guarantee, which only protects rows within the delay.

**A 15-minute delay.** e011 counts, but each window is emitted one arrival later, 7 windows instead of 9 reach the sink, and 3 windows are still open at the end instead of 1.

**Which clock, and a checkpointed setting.** A batch read groups the same events by event time (09:00 L1 = 36) and by landing time (09:10 L1 = 48); sliding windows sum to 252 units, twice the total. A stateless stream-static join into the Parquet file sink, stopped with `stop()` and restarted, ends with 14 rows for 14 events. A restart after setting the session to 3 shuffle partitions keeps the checkpoint's 2.

### What the tests prove and do not prove

Thirteen tests prove, for Spark 4.0.4 in `local[2]` with two shuffle partitions: the watermark, input rows, state rows, removals and late drops of every micro-batch; the windows emitted and when; the checkpoint's offset, commit and file-source entries before and after a failure and a restart; the replay of exactly the uncommitted batch; the naive and keyed downstream counts; the backlog and 15-minute transfers; the refusals and their conditions. They do not prove behaviour on another Spark version or on Databricks, Kafka or other message sources, Delta Lake sinks, the RocksDB state store, stream-stream joins, clusters, or any timing. Retry and reconciliation in scheduled work are covered in [Orchestration, failure, and reconciliation](#/lesson/dbxfe-m04-l03).

### Setup, run and cleanup

Create a Python 3.12 virtual environment, `pip install -r requirements.txt` (PySpark 4.0.4, Py4J 0.10.9.9), point `JAVA_HOME` at a Java 17 or 21 JDK, then run `python run_tests.py --evidence local-evidence.json` from the lab directory. The recorded run used Python 3.12.3 and OpenJDK 21.0.10: 13 tests, 0 failures, 0 errors, 0 skips, exit 0. The runner creates one temporary directory for Spark's files, landing directories, checkpoints and the Parquet output and deletes it after stopping Spark; the starter does the same. Delete the virtual environment and the evidence file when finished. Studying this page needs no installation.
