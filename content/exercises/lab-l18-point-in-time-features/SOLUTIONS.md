# Explained solutions

`solutions/features.py` is the complete reference. Outputs quoted below were
printed by it (pandas 3.0.6, numpy 2.5.3) and agree with the hand-authored
`expected/*.json`. Times are UTC on 2 March 2026 and shortened to `HH:MM`.

## Task 1 — windows closed on the right

```python
def window_end(observed_at, window_hours):
    return observed_at.dt.ceil(pd.Timedelta(hours=window_hours))
```

`ceil` leaves a timestamp already on the grid where it is (10:00 stays
10:00) and moves every other one up to the next grid point (09:10 becomes
10:00, 10:30 becomes 12:00). That is exactly the (start, end] convention. The
tempting alternative, `floor(...) + 2h`, is the [start, end) convention and
moves the 10:00:00 reading into the next window; Task 6 shows what that does.

## Task 2 — one run's features

```python
grouped = known.groupby(["machine_id", "feature_time"], as_index=False).agg(
    temp_mean_2h=("temp_c", "mean"),
    vib_max_2h=("vibration_mm_s", "max"),      # skips missing values
    reading_count_2h=("temp_c", "size"),        # rows
    vib_count_2h=("vibration_mm_s", "count"),  # non-missing values
    source_max_ingested_at=("ingested_at", "max"),
)
```

`max` skips missing values, so a window whose vibration values are all
missing yields `null`; `count` counts non-missing values and `size` counts
rows. PR-03's window therefore reads `vib_max_2h` null and `vib_count_2h` 0
next to `reading_count_2h` 2: two readings arrived, neither carried a
vibration value. Filling with 0.0 would claim the sensor measured no
vibration at all, which nobody observed. `source_max_ingested_at` is lineage:
the latest arrival time among the readings used, needed in Task 7.

The replay publishes a (machine, window) row at the first run after the
window closes and again only when the readings behind it change. Primary
result, six rows:

```
PR-01 08:00 @08:30  72.0  2.6  3/3  low=False   PR-02 08:00 @08:30  65.5  1.8  2/2  low=True
PR-01 10:00 @10:30  77.0  3.4  2/2  low=True    PR-02 10:00 @10:30  70.0  1.9  3/2  low=False
PR-01 12:00 @12:30  85.0  5.8  3/3  low=False   PR-03 10:00 @10:30  61.0  null 2/0  low=True
```

(`3/2` is `reading_count_2h/vib_count_2h`.) PR-02 has no row after 10:00
because its gateway sent nothing; an absent row is the honest record of
that, not a row of zeros.

## Task 3 — duplicates

```python
def refuse_duplicates(frame, keys, what):
    duplicated = frame[frame.duplicated(keys, keep=False)]
    if not duplicated.empty:
        first = duplicated.sort_values(keys, kind="stable").iloc[0]
        identity = " ".join(f"{key}={plain(first[key])}" for key in keys)
        count = int((frame[keys] == first[keys]).all(axis=1).sum())
        raise DuplicateEntityTimeError(f"duplicate entity-time {what}: {identity} appears {count} times")
```

Without the check, `join_on_availability_unchecked` gives PR-01's 11:00
prediction `99.0` with the copy appended last and `77.0` when the rows are
reversed: the value a model trains on would depend on how files happened to
be written.
Refusing is the only safe choice; the producer must resolve the duplicate.

## Task 4 — the point-in-time join

```python
candidates = left.merge(features, on="machine_id", how="inner")
candidates = candidates[candidates["available_at"] <= candidates["prediction_time"]]
chosen = (candidates.sort_values(["label_row", "feature_time", "available_at"], kind="stable")
          .groupby("label_row", as_index=False).tail(1))
```

Result for the eleven label rows (window used, publication, age, status):

```
PR-01 09:00 -> 08:00 @08:30  60 ok      PR-02 09:00 -> 08:00 @08:30  60 ok
PR-01 11:00 -> 10:00 @10:30  60 ok      PR-02 10:15 -> 08:00 @08:30 135 ok
PR-01 11:45 -> 10:00 @10:30 105 ok      PR-02 12:45 -> 10:00 @10:30 165 ok
PR-01 12:45 -> 12:00 @12:30  45 ok      PR-03 09:00 -> none             none_available
PR-03 10:20 -> none   none_available    PR-03 13:00 -> 10:00 @10:30 180 ok
PR-03 13:30 -> 10:00 @10:30 210 stale
```

The guard then refuses both shortcuts, naming the rows:

```
event-time -> 2 row(s) use future information: PR-02 at 10:15 (published_after_prediction); PR-03 at 10:20 (published_after_prediction)
latest-row -> 7 row(s) use future information: PR-01 at 09:00, 11:00, 11:45; PR-02 at 09:00, 10:15; PR-03 at 09:00, 10:20
```

**Wrong approach 1, the event-time join.** `merge_asof(..., left_on="prediction_time", right_on="feature_time")`
picks the newest window that had *ended* by the prediction time. The window
ending 10:00 ended before 10:15 but did not exist until 10:30, so PR-02 at
10:15 trains on 70.0 instead of 65.5, and PR-03 at 10:20 trains on a value
where the honest answer is "none yet". Nothing crashes, and offline scores
improve for exactly the rows a live model will never have.

**Wrong approach 2, the latest-row lookup.** "The machine's current value"
is right at serving time, when now is the prediction time. Applied to
history it hands the 09:00 prediction the 12:00 window.

## Task 5 — one rule, two paths

```python
def assess(prediction_time, feature_time, max_age_minutes):
    if feature_time is None or pd.isna(feature_time):
        return None, "none_available"
    age = int((prediction_time - feature_time) / pd.Timedelta(minutes=1))
    return age, "stale" if age > max_age_minutes else "ok"
```

`online_store_at` keeps, per machine, the newest window published by `now`
and of it the newest version, and `serve_features` applies the same `assess`.
The test calls it at all eleven label times, before and after the late
readings, and requires every field to equal the training row. The online
lookup is correct because at serving time "latest published" and "published
by the prediction time" are the same set of rows.

## Task 6 — the drifted port

```
10:30 -> [PR-02 10:00: temp_mean_2h 70.0 vs 69.0, vib_max_2h 1.9 vs 1.7, reading_count_2h 3 vs 2, low_coverage false vs true;
          PR-03 10:00: vib_max_2h null vs 0.0, vib_count_2h 0 vs 2]
08:30 -> no difference
```

Drift one is the window convention: the port uses `floor + 2h`, so PR-02's
10:00:00 reading leaves the 10:00 window (count 3 to 2, mean 70.0 to 69.0,
max 1.9 to 1.7). Drift two is `fillna(0.0)`: PR-03's missing vibration becomes
a measured zero and `count` now counts it. At 08:30 no boundary reading and
no missing vibration value had been ingested, so the same broken port agreed.
A consistency check proves agreement only on the inputs it saw; keep edge
cases in the check's input, and better still import the one transformation.

## Task 7 — late readings

Two versions are appended and nothing published is rewritten:

```
PR-01 10:00 @11:30  78.0  3.9  3/3  source 11:05   (09:50 reading ingested 11:05)
PR-02 08:00 @12:30  66.0  1.8  3/3  source 11:40   (07:10 reading ingested 11:40)
```

Only PR-01 at 11:45 changes (77.0 at 10:30 becomes 78.0 at 11:30); PR-01 at
11:00 keeps 77.0 because at 11:00 the late reading had not arrived. That is
point-in-time correctness: each row sees what existed then.

**Wrong approach 3, `merge_asof` on `available_at` alone.** It returns the
most recently *published* row. At 12:45 that is PR-02's republished 08:00
window (published 12:30), 285 minutes old and `stale`, where the
point-in-time join keeps the 10:00 window at 165 minutes. No future
information is involved, so the guard is silent; only a comparison with the
explicit rule catches it. On the primary fixture the two joins agree, which
is why a test on clean data alone would not have found it. A last-write-wins
online store keyed by machine alone has the same defect.

**Wrong approach 4, the overwrite backfill.** Recomputing every window once
from everything and stamping nominal publication times folds the late
readings into rows that claim to have existed before them. The contract's
lineage rule refuses the table:

```
2 row(s) claim readings ingested after they were published:
PR-01 window 10:00 published 10:30 uses a reading ingested 11:05;
PR-02 window 08:00 published 08:30 uses a reading ingested 11:40
```

Had it been joined unchecked, three rows would have trained on future data
(PR-01 at 11:00, PR-02 at 09:00 and 10:15). Without `source_max_ingested_at`
nothing could detect this afterwards.

## Task 8 — reuse

The handover model reads the same six rows. At 10:00 and 12:00 the freshest
published window is always two hours old, so under its 90-minute policy five
rows are `stale` and PR-03 at 10:00 is `none_available`: zero usable rows.
The join is right; the cadence does not fit this decision time. Options, in
order of cost: move the decision after a publication (at 10:35 the 10:00
window is 35 minutes old); shift the window grid so a window closes and is
published just before each handover (windows ending 09:30, published at
10:00, are 30 minutes old at 10:00); or compute the value at request time
from raw readings. Publishing sooner alone cannot help, because a decision
made at the instant a window closes can never see that window. Loosening the
consumer's policy to 180 minutes would make the rows `ok` only by accepting
older information, which is a decision for the model owner, not a join fix.
