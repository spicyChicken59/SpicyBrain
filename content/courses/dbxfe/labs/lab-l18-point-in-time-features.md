# Lab L18 — Point-in-time features

*Local-executed (R), pandas 3.0.6 and numpy 2.5.3 on Python 3.12. Nothing
runs on Databricks; everything below can be studied without installing
anything.*

## What this lab is for

A model is trained on rows that pretend to be past moments: "at 10:15, here
is what we knew about press PR-02, and here is what happened next". If any
feature in that row was not actually known at 10:15, the offline score
measures a model that can never exist. The features module teaches the
mechanism; this lab makes you build it and prove it with tests. You get
fifteen sensor readings from three fictional Cinderline presses, a feature
job that publishes two-hour window aggregates thirty minutes after each
window closes, eleven labelled prediction times, two readings that arrive
late, and a second model that wants to reuse the same features.

## The data, briefly

Readings carry two times: when they were measured (`observed_at`) and when
they landed (`ingested_at`, normally two minutes later). Windows are
(start, end]: a reading at exactly 10:00 belongs to the window ending 10:00.

| machine | readings (observed) | what is special |
|---|---|---|
| PR-01 | 06:30-07:50, 08:30, 09:10, 10:30-11:50 | its 09:50 reading arrives at 11:05 (late file) |
| PR-02 | 06:30, 07:50, 08:30, 09:10, 10:00 | 09:10 has no vibration value; 10:00:00 sits on a boundary; nothing after 10:00; its 07:10 reading arrives at 11:40 (late file) |
| PR-03 | 09:10, 09:50 | commissioned at 09:00; no vibration value at all |

The job runs at 08:30, 09:30, 10:30, 11:30 and 12:30. Each feature row
carries `feature_time` (the window's end), `available_at` (the run that
published it) and `source_max_ingested_at` (the latest arrival it used).

## Task by task, with the intermediate output

**Windows and one run (gaps 1 and 2).** `window_end` rounds each observation
time up to the even hour. At the 10:30 run the job publishes five rows,
including PR-02's 10:00 window (70.0 °C mean, max vibration 1.9, three
readings but two vibration values) and PR-03's (61.0 °C, vibration `null`,
zero values, low coverage). `max` skips missing values; `count` counts values
and `size` counts rows. That difference is how the table says "two readings,
no vibration measured" instead of inventing 0.0.

**The published table.** Six rows over the whole schedule:

| machine | window | published | temp | vib max | rows/values |
|---|---|---|---|---|---|
| PR-01 | 08:00 | 08:30 | 72.0 | 2.6 | 3/3 |
| PR-01 | 10:00 | 10:30 | 77.0 | 3.4 | 2/2 |
| PR-01 | 12:00 | 12:30 | 85.0 | 5.8 | 3/3 |
| PR-02 | 08:00 | 08:30 | 65.5 | 1.8 | 2/2 |
| PR-02 | 10:00 | 10:30 | 70.0 | 1.9 | 3/2 |
| PR-03 | 10:00 | 10:30 | 61.0 | null | 2/0 |

**Duplicates (gap 3).** One entity at one time key is one row. A second copy
of PR-01's 10:00 window with 99.0 is refused with the key named; left in, the
11:00 prediction would get 77.0 or 99.0 depending on storage order.

**The point-in-time join (gap 4).** For each label: rows of the same machine
published at or before the prediction time, the newest window, then its
newest version. PR-02 at 10:15 gets the 08:00 window (65.5, 135 minutes
old), because the 10:00 window did not exist until 10:30. PR-03 at 09:00 and
10:20 get nothing: `none_available`.

**One missingness rule (gaps 5 and 6).** The failure model allows 180
minutes, inclusive. PR-03 at 13:00 is exactly 180 minutes old and `ok`; at
13:30 it is 210 and `stale`. The online lookup, "each machine's newest
published row at the request time", runs the same `assess` function, and a
test calls it at all eleven label times and requires every field to equal
the training row. Eight rows are usable (feature `ok` and label known by the
17:00 cutoff).

## The failure cases, and why each fails

- **Joining on the time a row describes.** `merge_asof` on `feature_time`
  gives PR-02 at 10:15 and PR-03 at 10:20 the 10:00 windows, published at
  10:30. The guard refuses both rows by name.
- **"The current value" for history.** A latest-row lookup is right when
  serving and wrong for seven of the eleven training rows.
- **A drifted serving port.** A re-implementation that buckets readings with
  `floor + 2h` and fills missing vibration with 0.0 agrees with the training
  code at 08:30 and disagrees at 10:30 on exactly two windows: PR-02's mean
  drops from 70.0 to 69.0 because the boundary reading moved, and PR-03's
  missing vibration becomes 0.0. A consistency check proves agreement only on
  inputs that contain the edge cases.
- **`merge_asof` on availability alone.** Correct on the primary data, wrong
  after the late readings: at 12:45 it returns PR-02's republished 08:00
  window (285 minutes old, stale) instead of the 10:00 window.
- **The overwrite backfill.** Recomputing history in one pass with nominal
  publication times hides the late readings in rows that claim earlier
  availability. The lineage rule (`source_max_ingested_at` never after
  `available_at`) refuses the table; unchecked, three predictions would have
  used readings before they arrived.

## The late rerun: what changes

Two versions are appended and nothing is rewritten: PR-01's 10:00 window at
11:30 (78.0, three readings) and PR-02's 08:00 window at 12:30 (66.0). Exactly
one training row changes, PR-01 at 11:45, which now sees 78.0. PR-01 at
11:00 still sees 77.0 because the late reading landed at 11:05.

## Reuse by a second model

A handover model predicting at 10:00 and 12:00 reads the same table without
recomputing it. Every usable row is 120 minutes old against its 90-minute
policy, so nothing is usable. The finding is a schedule mismatch, not a join
bug: decide after a publication (at 10:35 the 10:00 window is 35 minutes
old) or shift the window grid so a window closes and is published just
before each handover. Publishing sooner alone cannot help a decision made at
the instant a window closes.

## What the tests prove, and what they do not

The 25 tests show that the stated rules produce the hand-authored rows,
that each wrong approach fails for the reason named, and that the six
starter gaps are marked. They do not show that these features predict
failure (no model is trained), anything about scale or streaming, clock skew
between systems, or how a Databricks feature table, Feature View or online
store behaves; the module names those capabilities and their caveats.

## Setup and cleanup

```sh
cd lab-l18-point-in-time-features
pip install -r requirements.txt           # pandas 3.0.6, numpy 2.5.3
python run_tests.py --evidence local-evidence.json
python solutions/features.py --late
```

A passed run is 25 tests, 0 failures, 0 errors, 0 skipped. The runner writes
no bytecode; delete the evidence file and any virtual environment you
created when done. Revisit the prediction-time lesson in
[Machine learning fundamentals](#/module/dbxfe-m07) if the label timeline is
unfamiliar.
