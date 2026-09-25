# Tasks

Read `fixtures/feature_contract.json` and `fixtures/consumers.json` before
any code, then draw the three machines on one time axis from 06:00 to 14:00
UTC: readings (observed and ingested), the five scheduled runs at :30 past
each hour from 08:30 to 12:30, and the label prediction times. Predict on
paper first; every expected value you will be checked against was written by
hand (`DATA.md`).

## 1. Assign readings to windows (GAP 1)

Windows are two hours long and closed on the right: (06:00, 08:00],
(08:00, 10:00], (10:00, 12:00]. Implement `window_end` in
`starters/features.py`. Expected behaviour: PR-02's reading observed at
exactly 10:00:00 belongs to the window ending 10:00; a reading at 09:10
belongs to the same window; a reading at 10:30 belongs to the window ending
12:00. Write down which single pandas `Series.dt` method gives this without
an `if`.

## 2. Compute one run's features (GAP 2)

Implement `compute_features(observations, run_at, contract)`: readings
ingested at or before `run_at`, windows that ended by `run_at`, one row per
(machine, window). Expected behaviour at `run_at` 10:30:

| machine | window end | temp_mean_2h | vib_max_2h | reading_count_2h | vib_count_2h | low_coverage |
|---|---|---|---|---|---|---|
| PR-01 | 08:00 | 72.0 | 2.6 | 3 | 3 | false |
| PR-01 | 10:00 | 77.0 | 3.4 | 2 | 2 | true |
| PR-02 | 08:00 | 65.5 | 1.8 | 2 | 2 | true |
| PR-02 | 10:00 | 70.0 | 1.9 | 3 | 2 | false |
| PR-03 | 10:00 | 61.0 | null | 2 | 0 | true |

Explain PR-03's `null`: which aggregation gives `null` and which would give
`0.0`, and why `0.0` would be a false measurement. Then run
`build_feature_table` (already complete) and predict how many rows the whole
schedule publishes. Expected: 6, with PR-01's 12:00 window published at 12:30
and no row at all for PR-02 or PR-03 after 10:00.

## 3. Refuse duplicate entity-time rows (GAP 3)

Implement `refuse_duplicates(frame, keys, what)`. The same helper guards
readings `(machine_id, observed_at)`, feature rows
`(machine_id, feature_time, available_at)` and labels
`(machine_id, prediction_time)`. Expected behaviour: appending a second copy
of PR-01's 10:00 window with `temp_mean_2h` 99.0 raises
`duplicate entity-time feature row: machine_id=PR-01 feature_time=2026-03-02T10:00:00+00:00 available_at=2026-03-02T10:30:00+00:00 appears 2 times`.
Then use `shortcuts.join_on_availability_unchecked` on that table twice, once
reversed: what value does PR-01's 11:00 prediction receive each time?

## 4. Join as of the prediction time (GAP 4)

Implement `point_in_time_join`: for each label row, the feature rows of the
same machine with `available_at <= prediction_time`; the newest window; of
that window, the newest version. Before running anything, fill in the
feature window each of the eleven label rows should receive, or "none".
Expected behaviour: PR-02 at 10:15 receives the 08:00 window, because the
10:00 window was not published until 10:30; PR-03 at 09:00 and at 10:20
receive nothing. Then predict which label rows `shortcuts.join_on_feature_time`
and `shortcuts.latest_row_lookup` get wrong. Expected: 2 rows and 7 rows.

## 5. One missingness rule, two paths (GAP 5 and GAP 6)

Implement `assess(prediction_time, feature_time, max_age_minutes)` and
`online_store_at(features, now)`. The failure-warning consumer allows 180
minutes, inclusive. Expected behaviour: PR-03 at 13:00 is `ok` at exactly 180
minutes; PR-03 at 13:30 is `stale` at 210; `serve_features` returns, for
every label row, exactly the fields the training set holds for it. Explain in
two sentences why a "latest row per machine" lookup is correct in
`online_store_at` and wrong in `shortcuts.latest_row_lookup`.

## 6. Find the drift in the serving port

Do not read `starters/serving_port.py` yet. Run
`assert_same_transformation(compute_features, compute_features_port, observations, run_at, contract)`
at 08:30 and at 10:30. Expected behaviour: 08:30 passes; 10:30 raises and
names two windows, PR-02 at 10:00 (four columns) and PR-03 at 10:00 (two
columns). From the differences alone, name the two drifts. Then read the port
and confirm. Why is a consistency check that only ran at 08:30 worthless as
evidence?

## 7. Rerun with the late readings

Load `observations.csv` and `late_observations.csv` together and rebuild.
Predict first: how many rows are added, with which `available_at`; which of
the eleven training rows change; what `asof_join_on_availability` (a plain
`merge_asof` on `available_at`) now returns for PR-02 at 12:45. Expected: two
new versions (PR-01 10:00 at 11:30, PR-02 08:00 at 12:30); exactly one
training row changes (PR-01 at 11:45); `merge_asof` on availability returns
PR-02's republished 08:00 window, 285 minutes old and stale, where the
point-in-time join keeps the 10:00 window. Finally run
`shortcuts.overwrite_backfill`: which contract rule refuses it, and which
three training rows would it have leaked into?

## 8. Reuse the table for a second consumer

`fixtures/labels_handover.csv` predicts at 10:00 and 12:00 with its own
policy of 90 minutes. Build its training set from the **same** feature table
without recomputing anything. Expected behaviour: five rows are `stale` at
120 minutes and PR-03 at 10:00 is `none_available`, so no row is usable;
under a 180-minute policy the five would be `ok`. Write the recommendation
you would give: is the fix a different join, a different publication time,
or a different decision time?
