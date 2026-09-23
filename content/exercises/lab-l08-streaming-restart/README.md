# Lab L08 — Streaming restart: event time, watermarks, checkpoints and idempotent effects

**Execution class: R (local-executed).** The reference solution and its thirteen
tests run here on local Apache Spark 4.0.4 in `local[2]` mode on one machine.
Nothing in this package runs on Databricks, reads from Kafka or writes to
Delta Lake, and no number in it is a timing or a benchmark.

## Purpose and outcome

Cinderline Components' press lines report how many parts they made as small
count events. A gateway drops those events into a landing directory as files,
sometimes late and out of order. You run a **real Structured Streaming query**
over that directory: Spark's file source picks up each file, a watermark on
`event_time` decides when a 10-minute window is final, the state store keeps the
windows that are still open, the checkpoint records what was planned and what
was committed, and a `foreachBatch` function hands each finished window to two
downstream stand-ins, one naive and one keyed.

The fixture files are moved into the directory **one at a time, in a controlled
order**; after each move one bounded run (`trigger(availableNow=True)`)
processes what is there and stops. Every run after the first is therefore a
restart from the same checkpoint. On the fourth arrival the sink fails on
purpose *after* its downstream effects, so you can watch the restart replay the
uncommitted micro-batch and see which outbox duplicates a notification.

After the lab you can:

- predict, for each micro-batch, the watermark Spark reports, how many rows it
  keeps in state, which windows it emits in append mode and which late row it
  drops, and check each prediction against Spark's own progress report;
- show that a row *older than the watermark* is still counted while its window
  is open, and that a row arriving after its window was finalized is dropped;
- read the checkpoint's offset log, commit log and file-source log, and explain
  a planned-but-uncommitted batch after a failure;
- show that a restart replays exactly the uncommitted batch (same id, same
  rows) and never re-reads a committed file;
- explain why a `foreachBatch` effect needs an idempotency key: the naive outbox
  ends with 12 messages for 9 windows, the keyed outbox with 9;
- show that the *same* late row is counted when the files are processed as a
  backlog, because micro-batch boundaries (processing time) decide when state
  is evicted, and attribute that difference with one internal Spark setting;
- compare event-time windows with processing-time (landing-time) windows and
  with sliding windows over the same 18 events;
- stop and restart a stateless stream-static join into the Parquet file sink
  without duplicating output rows;
- recognise two refusals for the right reason: append mode on an aggregation
  without a watermark, and a restart whose aggregation no longer matches the
  checkpointed state;
- show that a restart keeps the shuffle partition count its checkpoint recorded,
  even when the session asks for a different one.

## Prerequisites

The streaming module's lesson (micro-batches, watermarks, checkpoints, sinks) or
equivalent, typed DataFrames with column expressions, and comfort reading a few
lines of Python. SQL `GROUP BY` intuition carries over directly: a streaming
window aggregation is a grouping whose groups finish over time.

## Environment (pinned, actually tested)

| Item | Version used for the recorded evidence |
|---|---|
| Python | 3.12.3 |
| Java | OpenJDK 21.0.10 |
| PySpark / Py4J | 4.0.4 / 0.10.9.9 (see `requirements.txt`) |
| Spark master | `local[2]`, web UI and console progress bar disabled, driver bound to `127.0.0.1` |
| `spark.sql.shuffle.partitions` | 2 (also the number of state store partitions) |
| Session time zone | UTC |
| State store | the default HDFS-backed provider, read back with the experimental state data source |

The internal setting `spark.sql.streaming.statefulOperator.allowMultiple` is
changed in test 07 only, to attribute an observation; it is not a
recommendation and is restored at once. Test 13 sets
`spark.sql.shuffle.partitions` to 3 before one restart and restores 2 after it.

## Setup and run

1. Create a Python 3.12 virtual environment and `pip install -r requirements.txt`.
2. Point `JAVA_HOME` at a Java 17 or 21 JDK (the recorded run used OpenJDK 21.0.10).
3. From this directory run `python run_tests.py --evidence local-evidence.json`.

The recorded run: 13 tests, 0 failures, 0 errors, 0 skips, exit 0. The runner
sets `PYSPARK_PYTHON` to its own interpreter, creates one temporary directory
for Spark's local files, the landing directories, checkpoints and the Parquet
output, and deletes it after stopping Spark. The starter
(`python starters/streaming_task.py`) does the same with its own temporary
directory.

## Package map

| Path | What it holds |
|---|---|
| `fixtures/arrivals/01.json` … `05.json` | 18 synthetic count events in five JSON Lines files |
| `fixtures/manifest.json` | arrival order and each file's landing (processing) time |
| `fixtures/lines.json` | the static line → plant table for the stream-static join |
| `expected/*.json` | literals written by hand before the final run; derivations in `DATA.md` |
| `expected/derive_expected.py` | plain-Python re-derivation of the batch truths (no Spark) |
| `solutions/streaming_restart.py` | reference queries, sink stand-ins and checkpoint readers |
| `starters/streaming_task.py` | the learner version with four gaps |
| `TASKS.md`, `SOLUTIONS.md`, `DATA.md` | tasks with expected behaviour, explained solution, data dictionary |

## Cleanup

The runner and the starter delete their temporary directory themselves. Delete
the virtual environment and the evidence file you named when you are finished.

## Limits

One machine, tiny files, one file per micro-batch. The file source here is
replayable because the files stay in place; a message source needs its own
retention to be replayable. The downstream systems are Python lists and dicts.
Not executed: stream-stream joins, Kafka or other message sources, Delta Lake
sinks, the RocksDB state store, continuous processing, clusters and any
Databricks runtime. The late-row observation is
specific to Spark 4.0.4's behaviour here and is consistent with, but narrower
than, the documented guarantee: data later than the watermark delay *may or may
not* be counted.
