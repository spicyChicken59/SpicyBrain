# Solutions — explained

The complete reference is `solutions/streaming_restart.py`; `run_tests.py`
drives it and compares every result with `expected/*.json`. The intermediate
outputs below are the ones the recorded run produced (local Spark 4.0.4,
`local[2]`, two shuffle partitions, UTC).

## Gap 1 — the watermarked window aggregation

```python
def line_windows(events, delay="5 minutes", window="10 minutes"):
    return (events.withWatermark("event_time", delay)
            .groupBy(F.window("event_time", window), "line")
            .agg(F.sum("units").alias("units"), F.count("*").alias("events")))
```

The watermark is declared on the same column the window uses and before the
aggregation. That is what lets append mode emit a window once, when it is
final, and lets the engine drop that window's state afterwards.

## Gap 2 — a bounded start with an explicit checkpoint

```python
query = (frame.writeStream.outputMode("append")
         .option("checkpointLocation", str(checkpoint))
         .foreachBatch(sink)
         .trigger(availableNow=True)
         .start())
if not query.awaitTermination(300):
    query.stop()
    raise TimeoutError("availableNow run did not terminate within the bound")
```

`availableNow` processes everything present when the run starts, in as many
micro-batches as `maxFilesPerTrigger` requires, runs a no-data batch if the last
batch moved the watermark, and stops by itself. The timeout is a safety bound,
not a wait: no test ever reaches it, and nothing sleeps.

## Gap 3 — an idempotency key

```python
key = f"{row['window_start']}|{row['line']}"
if key not in self.sent_keys:
    self.sent_keys.add(key)
    self.keyed.append(message)
```

The key must be identical when the same micro-batch is replayed. The window
start and the line identify the business fact (one finished window of one
line), so a replay finds the key and writes nothing. The batch id would also be
stable across a replay, but a batch-level ledger only works when the effect and
the ledger entry are recorded atomically; here the sink fails *between* sending
and finishing, which is exactly the case a batch-level ledger written last
would miss.

## Gap 4 — planned but not committed

```python
logs = checkpoint_logs(checkpoint)
return sorted(set(logs["offsets"]) - set(logs["commits"]))
```

After the injected failure this returns `[7]`.

## The run, micro-batch by micro-batch (scenario S, 5-minute delay)

| Run | Batch | Rows in | Watermark used | State rows after | Evicted | Dropped late | Emitted (units / events) |
|---|---|---|---|---|---|---|---|
| 01 lands | 0 | 6 | 1970-01-01 00:00:00 | 4 | 0 | 0 | — |
| | 1 | 0 | 09:07:40 | 4 | 0 | 0 | — |
| 02 lands (restart) | 2 | 4 | 09:07:40 | 4 | 0 | 0 | — |
| | 3 | 0 | 09:13:30 | 2 | 2 | 0 | 09:00 L1 27/3, L2 23/3 |
| 03 lands (restart) | 4 | 4 | 09:13:30 | 4 | 0 | **1** | — |
| | 5 | 0 | 09:22:00 | 2 | 2 | 0 | 09:10 L1 21/2, L2 18/3 |
| 04 lands (restart) | 6 | 2 | 09:22:00 | 4 | 0 | 0 | — |
| | 7 | 0 | 09:33:00 | *failed after the sink wrote* | | | (09:20 L1 6/1, L2 4/1, L3 2/1 delivered, then the error) |
| restart | 7 (replay) | 0 | 09:33:00 | 1 | 3 | 0 | 09:20 L1 6/1, L2 4/1, L3 2/1 **again** |
| restart | — | — | — | — | — | — | nothing planned |
| 05 lands (restart) | 8 | 2 | 09:33:00 | 3 | 0 | 0 | — |
| | 9 | 0 | 09:41:00 | 1 | 2 | 0 | 09:30 L2 3/1, L3 5/1 |

State read back with the state data source after batch 6 (before the failing
batch): 09:20 L1 6/1, 09:20 L2 4/1, 09:20 L3 2/1, 09:30 L3 5/1. After batch 9:
09:40 L1 8/1 only. That last window is never emitted in this lab: no later event
moves the watermark past 09:50.

Checkpoint after the failure: `offsets/0` … `offsets/7`, `commits/0` …
`commits/6`. `offsets/7` records `batchWatermarkMs` for 09:33:00 and file-source
offset 3; `commits/6` already records `nextBatchWatermarkMs` 09:33:00. The
restart reads both, replays batch 7 with the same plan, and writes `commits/7`.
The file-source log maps source offsets 0–4 to `01.json` … `05.json`, one each.

Downstream at the end: sink calls for batches 0, 1, 2, 3, 4, 5, 6, 7, 7, 8, 9;
the keyed table holds 9 windows; the naive outbox 12 messages (the three 09:20
windows twice); the keyed outbox 9.

## What the backlog run shows

With all five files present before one run, batches 0–5 read files 01–05 and
then run one no-data batch. Batch 2 reads `03.json` with watermark 09:13:30 and
**emits 09:00 L1 as 36 / 4**: `e011` was counted. Two observations explain it.
The 09:00 window was still in state (no batch had run with a watermark past
09:10 yet), and in Spark 4.0.4 a stateful operator drops late rows against the
*previous* micro-batch's watermark (09:07:40) while it evicts state against the
current one (09:13:30). Test 07 confirms the attribution: with the internal
setting `spark.sql.streaming.statefulOperator.allowMultiple=false`, which makes
both use the current watermark, the same batch drops `e011` and emits 27 / 3.
The documented guarantee covers both outcomes: rows within the delay are never
dropped; rows later than the delay may or may not be counted.

## Transfer: 15 minutes

Watermarks after each arrival become 08:57:40, 09:03:30, 09:12:00, 09:23:00 and
09:31:00. `e011` arrives while the 09:00 window is still open (09:03:30 <
09:10), so L1 09:00 is 36 / 4; windows are emitted one arrival later; 7 windows
are emitted and 3 stay in state (09:30 L2, 09:30 L3, 09:40 L1).

## A setting the checkpoint keeps (test 13)

The first run records `"spark.sql.shuffle.partitions":"2"` in the settings map
of `offsets/0` and `offsets/1`. After the session is set to 3, the restart
reads that map back and runs with 2: `offsets/2` and `offsets/3` also record
`"2"`, the state directory keeps only partitions `0` and `1`, and the batches
match scenario S's second run exactly. With warnings visible, Spark also logs
that it is updating the session value from 3 to 2. State is partitioned by
this number, so the checkpoint, not the session, owns it.

## One wrong approach, and why it fails

**Append-to-list notifications in `foreachBatch`, trusting the checkpoint for
exactly-once.** The checkpoint makes Spark's *processing* exactly-once: batch 7
was planned once, replayed once, committed once, and no file was read twice. It
says nothing about what the sink function did before it raised. The naive
outbox therefore received the three 09:20 messages twice (12 messages for 9
windows). The file sink in Task 10 is exactly-once because Spark's own sink log
records which batch's files are committed; `foreachBatch` is only as strong as
the function you write, which is why the keyed outbox checks its key first.

A second wrong approach: **removing the watermark to "keep every late row".**
Append mode refuses the query outright (Task 11a); in update or complete mode
the state would grow without bound.

## What the other outputs were

- Batch comparison (Task 9): event time 10 windows; landing time 9 windows
  (09:10 L1 48/5, 09:10 L2 38/5, 09:20 L1 15/2, 09:20 L2 3/1, 09:20 L3 2/1,
  09:30 L2 4/1, 09:30 L3 5/1, 09:40 L1 8/1, 09:40 L2 3/1); sliding 21 rows,
  252 units.
- Stream-static join (Task 10): batches 0 (6 rows) and 1 (4 rows), stop,
  inactive, 10 output rows; restart: batch 2 (4 rows), 14 rows, 14 distinct
  ids; sink log 0, 1, 2.
- Refusals (Task 11): `STREAMING_OUTPUT_MODE.UNSUPPORTED_OPERATION` from
  `start()`; `STATE_STORE_VALUE_SCHEMA_NOT_COMPATIBLE` after the restart, with
  `offsets/0..2` and `commits/0..1` left behind.
