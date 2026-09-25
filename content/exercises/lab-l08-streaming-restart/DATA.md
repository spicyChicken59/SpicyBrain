# Data dictionary and derivations

All data is synthetic and was written by hand for this lab. Cinderline
Components, its lines, presses and plants are fictional. There is no random
generator and no seed: the fixtures are the literal files listed below.

## Fixtures

`fixtures/arrivals/NN.json` are JSON Lines files, one event per line:

| Field | Type | Meaning |
|---|---|---|
| `event_id` | string | unique id, `e001` … `e018` |
| `line` | string | press line: `L1`, `L2` or `L3` |
| `event_time` | timestamp (UTC, ISO 8601 with `Z`) | when the parts were counted at the press (event time) |
| `units` | integer | parts counted in that report |

`fixtures/manifest.json` gives the arrival order and each file's landing time.
The runner copies a file into a staging directory, sets its modification time
to `landsAt`, and renames it into the landing directory, so the landing time is
the file's processing-time arrival and the file source sees it appear whole.

| File | Lands at | Events (id line time units) |
|---|---|---|
| 01 | 09:13:00 | e001 L1 09:00:30 12 · e002 L2 09:01:10 8 · e003 L1 09:04:45 10 · e004 L2 09:08:20 9 · e005 L1 09:11:05 7 · e006 L2 09:12:40 11 |
| 02 | 09:19:00 | e007 L1 09:09:30 5 · e008 L2 09:05:00 6 · e009 L1 09:15:00 14 · e010 L2 09:18:30 4 |
| 03 | 09:28:00 | e011 L1 09:03:00 9 · e012 L2 09:14:10 3 · e013 L1 09:27:00 6 · e014 L3 09:25:00 2 |
| 04 | 09:39:00 | e015 L3 09:38:00 5 · e016 L2 09:21:00 4 |
| 05 | 09:47:00 | e017 L1 09:46:00 8 · e018 L2 09:35:00 3 |

All times are 2026-09-14 UTC. 18 events, 126 units. `fixtures/lines.json` is
the static table for the join: L1 → North (press P-210), L2 → North (P-220),
L3 → South (P-310).

## How the expected values were derived

Windows are half-open, `[start, end)`. The rule used for every hand-written
micro-batch value comes from the Spark 4.0.4 Structured Streaming guide (append
mode emits a window's final result once the watermark passes the window's end,
and then drops its state) plus two engine facts observed and then asserted:
availableNow runs a no-data batch when the last batch moved the watermark, and a
late row is compared with the previous micro-batch's watermark.

**Batch truths (`windows.json`).** Summing the table above by 10-minute window
of `event_time` and line gives the ten event-time rows (for example 09:00 L1 =
12 + 10 + 5 + 9 = 36 over e001, e003, e007, e011). Grouping by landing time
puts 01 and 02 in 09:10–09:20 (L1 12 + 10 + 7 + 5 + 14 = 48, L2 8 + 9 + 11 + 6 + 4
= 38), 03 in 09:20–09:30, 04 in 09:30–09:40 and 05 in 09:40–09:50. Sliding
windows of 10 minutes every 5 minutes place each event in exactly two windows,
so their units total 2 × 126 = 252. `expected/derive_expected.py` recomputes all
three tables in plain Python and the runner asserts equality with the literals.

**Watermarks.** The watermark after each arrival is the largest event time read
so far minus the delay. With 5 minutes: 09:12:40 → 09:07:40; 09:18:30 →
09:13:30; 09:27:00 → 09:22:00; 09:38:00 → 09:33:00; 09:46:00 → 09:41:00. With 15
minutes: 08:57:40, 09:03:30, 09:12:00, 09:23:00, 09:31:00. The first batch of a
new query reports 1970-01-01 00:00:00 (no event seen yet). A data batch uses the
watermark left by the batch before it; the no-data batch that follows uses the
new one. The derivation script recomputes both lists.

**Sequential run (`sequential.json`).** For each batch: rows in = rows of the
file read (0 for a no-data batch); state rows = open (window, line) keys after
the batch; updated = keys the batch's rows touched; evicted = keys whose window
end ≤ the batch's watermark; emitted = those evicted keys with their totals.
Worked example, batch 4: watermark 09:13:30; e011's window ends 09:10, and that
window was already evicted in batch 3, so e011 is dropped (dropped = 1); e012
updates 09:10 L2 (15 → 18); e013 and e014 open 09:20 L1 and 09:20 L3, so
updated = 3 and state = 2 + 2 = 4. The failing run's sink calls, the outbox
counts (4 → 7 → 10 → 10 → 12 naive; 4 → 7 → 7 → 7 → 9 keyed) and the checkpoint
listings follow from the same table. The emitted totals plus the dropped 9
units plus the never-emitted 8 units equal 126; the runner checks that sum.

**Backlog (`backlog.json`).** Same rule, but no no-data batch runs between
files, and a late row is judged against the previous batch's watermark: in
batch 2 that is 09:07:40, and e011's window end 09:10 is later, so e011 is
counted; eviction at 09:13:30 then emits 09:00 L1 = 36 / 4 in the same batch.
With the internal setting that judges late rows against the current watermark
(09:13:30), e011 is dropped and 09:00 L1 = 27 / 3.

**Transfer (`transfer.json`).** The 15-minute watermarks above keep every
window open one arrival longer; e011 (window end 09:10) arrives under 09:03:30
and is counted; after the last arrival 09:31:00 evicts only the 09:20 windows,
leaving 09:30 L2, 09:30 L3 and 09:40 L1 in state.

**Join (`join_restart.json`).** Files 01–03 hold 14 events: L1 7, L2 6, L3 1, so
North = 13 and South = 1; one file per micro-batch gives batches of 6, 4 and 4
rows.

**Checkpointed setting (`restart_settings.json`).** One completed run on
01.json gives offsets and commits 0 and 1, each recording two shuffle
partitions. The restart after 02.json lands is the same query on the same data
as scenario S's second run, so its batches are copied from that hand-written
derivation; the partition count stays at the recorded 2, giving state folders
`0` and `1` only.

**Refusals (`negative.json`).** Conditions and message fragments are the ones
Spark 4.0.4 defines for append mode without a watermark and for a changed
aggregation state schema; the offset and commit listings follow from one
completed run (batches 0 and 1) and one planned-but-failed batch (2).

## Provenance

Synthetic, hand-written, no personal or customer data, no real plant, press or
production figures. Timestamps are example values only.
