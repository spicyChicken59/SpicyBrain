# Tasks — predict, run, compare

Work in `starters/streaming_task.py`. Write every prediction into `PREDICTIONS`
before you run anything; the comparison is the learning. Expected behaviour is
stated so you can check yourself; how each number was derived is in `DATA.md`.

Query for every task unless told otherwise: read the landing directory with the
explicit schema `event_id STRING, line STRING, event_time TIMESTAMP, units INT`
and `maxFilesPerTrigger = 1`; `withWatermark("event_time", "5 minutes")`; group by
`window(event_time, "10 minutes")` and `line`; sum `units` as `units` and count
rows as `events`; append output mode; `foreachBatch`; an explicit checkpoint
directory; `trigger(availableNow=True)`. Session: `local[2]`, UI off,
`spark.sql.shuffle.partitions = 2`, session time zone UTC.

## Task 1 — The first file and its no-data batch (Gap 1, Gap 2)

Close Gap 1 (the watermarked window aggregation) and Gap 2 (a bounded start
with an explicit checkpoint). Land `01.json` and run once.

Expected: two micro-batches. Batch 0 reads 6 rows under the initial watermark
`1970-01-01T00:00:00Z` and keeps 4 state rows (09:00 and 09:10 windows for L1
and L2). Batch 1 reads 0 rows: availableNow ran a **no-data batch** because the
watermark moved, to `09:07:40` (09:12:40 minus 5 minutes). Nothing reaches the
sink: no window ends at or before 09:07:40. The checkpoint holds `offsets/0,1`
and `commits/0,1`.

## Task 2 — Late, but not too late

Land `02.json` and run again from the same checkpoint (a restart).

Expected: batch 2 reads **only the 4 new rows** (the file-source log assigns
`02.json` to source offset 1). `e008` happened at 09:05:00, older than the
09:07:40 watermark in force, yet it is counted because its window ends at
09:10, after the watermark. Batch 3 (no data, watermark `09:13:30`) finalizes
the 09:00 windows: L1 **27 units / 3 events**, L2 **23 / 3**. State keeps 2 rows.

## Task 3 — Too late

Land `03.json` and run.

Expected: batch 4 reports `numRowsDroppedByWatermark = 1`: `e011` (09:03:00, 9
units) belongs to the 09:00 window, which was emitted and evicted in batch 3.
The emitted L1 total stays 27, not the event-time truth of 36. Batch 5
(watermark `09:22:00`) emits the 09:10 windows: L1 21 / 2, L2 18 / 3.

## Task 4 — A failure after the effects (Gap 3, Gap 4)

Close Gap 3 so the keyed outbox stores one message per idempotency key, and
Gap 4 to list planned-but-uncommitted batches. Land `04.json` and run with the
sink armed to fail when it receives the 09:20 windows.

Expected: the query fails with `STREAM_FAILED` wrapping
`FOREACH_BATCH_USER_FUNCTION_ERROR`. Batch 6 committed; batch 7 (watermark
`09:33:00`) handed the sink L1 6 / 1, L2 4 / 1 and L3 2 / 1, the sink wrote
both outboxes, then raised. The checkpoint shows `offsets/0..7` and
`commits/0..6`: batch 7 is **planned, not committed**, and its offset entry
already records watermark `09:33:00` and source offset 3.

## Task 5 — Restart twice

Restart with no new file, then restart again.

Expected: the first restart replays **batch 7 with the same id and the same
three rows**; `commits/7` appears; the naive outbox grows from 7 to 10 messages
while the keyed outbox stays at 7. The second restart plans nothing: no new
offset file, no sink call. (Spark still posts one progress report, numbered 8,
with zero input rows.)

## Task 6 — A new file after the restart

Land `05.json` and run.

Expected: batch 8 reads only its 2 rows; batch 9 (watermark `09:41:00`) emits
the 09:30 windows, L2 3 / 1 and L3 5 / 1. At the end: 9 windows in the keyed
table, 12 naive messages (three duplicated keys, all 09:20), 9 keyed messages,
and one state row still waiting: L1's 09:40 window (8 / 1), which no later
event has closed.

## Task 7 — The same files as a backlog

Put all five files in a fresh landing directory first, then run once on a
fresh checkpoint.

Expected: 6 micro-batches, one file each plus a final no-data batch. Batch 2
now **counts `e011`** and emits L1 **36 / 4**: in the backlog nothing evicted
the 09:00 window between files, so when `e011` arrived its window was still in
state. Late rows are filtered against the previous micro-batch's watermark
(09:07:40) and state is evicted against the current one (09:13:30). Same events,
same query, different micro-batch boundaries, different emitted total.

## Task 8 — Transfer: a 15-minute delay

Repeat Tasks 1–6 on a fresh checkpoint with `withWatermark("event_time",
"15 minutes")` and no injected failure.

Expected: `e011` is counted (L1 09:00 is 36 / 4), but every window is emitted
one arrival later (09:00 at batch 5, 09:10 at batch 7, 09:20 at batch 9), only 7
windows are emitted instead of 9, and 3 state rows remain open instead of 1.

## Task 9 — Which clock?

Batch-read all five files and compare three groupings: tumbling 10-minute
windows on `event_time`; tumbling 10-minute windows on the file's landing time
(`_metadata.file_modification_time`); sliding windows of 10 minutes every 5 on
`event_time`.

Expected: event time gives 10 windows (09:00 L1 36 / 4 …); landing time gives 9
different windows (09:10 L1 **48 / 5**, because 01 and 02 both landed between
09:10 and 09:20); sliding windows give 21 rows whose units sum to **252**, twice
126, because every event falls in two windows.

## Task 10 — Stop and restart a stateless join

Join the stream to the static line table on `line` and write it with the
Parquet file sink. Use the default trigger; end each run with
`processAllAvailable()` then `stop()`. Run once with `01.json` and `02.json`,
land `03.json`, and restart.

Expected: first run commits batches 0 (6 rows) and 1 (4 rows); after `stop()`
the query is inactive and the output holds 10 rows. The restart commits batch 2
with 4 rows only; the output holds 14 rows with 14 distinct event ids (North 13,
South 1), and the sink's own log lists batches 0, 1, 2.

## Task 11 — Two refusals

(a) Remove the watermark and start in append mode. Expected: `AnalysisException`
with condition `STREAMING_OUTPUT_MODE.UNSUPPORTED_OPERATION`, raised by
`start()` before any batch is planned. (b) On a checkpoint that already holds
state, restart with one more aggregate (`max(units)`). Expected: the query fails
with `STATE_STORE_VALUE_SCHEMA_NOT_COMPATIBLE`; the checkpoint gains an offset
file for the planned batch but no commit.

## Task 12 — A setting the checkpoint keeps

Run the query once with `spark.sql.shuffle.partitions = 2` on `01.json`. Set
the session to 3, land `02.json` and restart on the same checkpoint.

Expected: the restart produces the same batches as Task 2 (batch 2 reads 4
rows, batch 3 emits 09:00 L1 27 / 3 and L2 23 / 3). Every offset file, old and
new, records `spark.sql.shuffle.partitions` as `"2"`, and the state directory
still has exactly two partition folders, `0` and `1`. A stateful query's
partitioning belongs to its checkpoint; changing it means a new checkpoint.
