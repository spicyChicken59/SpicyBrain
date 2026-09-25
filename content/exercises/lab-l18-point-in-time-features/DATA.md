# Data dictionary and derivations

All machines, readings, schedules, labels and policies are original fiction
for the fictional manufacturer Cinderline Components. The files are
hand-written; there is no generator and no seed. Every value in `expected/`
was derived by hand from the fixtures and the contract below **before** the
solution was run; the solution was then run and agreed on every field.
Nothing in `expected/` was produced by the solution. Times are UTC on
2 March 2026, written `HH:MM`.

## Fixtures

| file | grain | columns |
|---|---|---|
| `observations.csv` | one sensor reading | `machine_id`, `observed_at` (when measured), `ingested_at` (when it landed), `temp_c`, `vibration_mm_s` (empty = no value sent) |
| `late_observations.csv` | same | two readings whose `ingested_at` is long after `observed_at` |
| `labels.csv` | one prediction opportunity | `machine_id`, `prediction_time`, `event_at` (failure time, empty if none), `label_time` (when the outcome became known), `label` (1 = failed within 4 hours) |
| `labels_handover.csv` | same | second model: scrap above 2% in the two hours after a handover; `label_time` = prediction + 2 h |
| `feature_contract.json` | producer contract | entities `PR-01..PR-03`, two-hour windows (start, end], publication 30 min after each window at runs 08:30, 09:30, 10:30, 11:30, 12:30, three expected readings per window, column rules |
| `consumers.json` | consumer policies | `failure_warning`: max feature age 180 min, training cutoff 17:00; `handover_scrap`: max age 90 min |

Readings (primary), ingested two minutes after observation:

| machine | observed | temp_c | vibration |
|---|---|---|---|
| PR-01 | 06:30, 07:10, 07:50 | 70, 72, 74 | 2.0, 2.4, 2.6 |
| PR-01 | 08:30, 09:10 | 76, 78 | 3.0, 3.4 |
| PR-01 | 10:30, 11:10, 11:50 | 82, 85, 88 | 4.4, 5.1, 5.8 |
| PR-02 | 06:30, 07:50 | 65, 66 | 1.8, 1.6 |
| PR-02 | 08:30, 09:10, 10:00 | 68, 70, 72 | 1.7, empty, 1.9 |
| PR-03 | 09:10, 09:50 | 60, 62 | empty, empty |

Late readings: PR-01 09:50 (80, 3.9) ingested 11:05; PR-02 07:10 (67, 1.5)
ingested 11:40.

Labels: PR-01 fails at 14:10. Its predictions at 11:00, 11:45 and 12:45 fall
within four hours before 14:10 (label 1, `label_time` 14:10); 09:00 does not
(label 0, known at 13:00). Every other label is 0 and becomes known four
hours after its prediction time.

## Derivations

**Windows.** A reading belongs to the window whose end is its observation time
rounded up to the next even hour, unchanged if already on one: 06:30-07:50 to
08:00; 08:30, 09:10, 09:50 and PR-02's 10:00 to 10:00; 10:30-11:50 to 12:00.

**Feature table** (`expected/feature_table.json`). Each window is first
published at the first run after it ends: 08:00 at 08:30, 10:00 at 10:30,
12:00 at 12:30. Runs 09:30 and 11:30 publish nothing on the primary data
because no window's readings changed.

- PR-01 08:00: (70+72+74)/3 = 72.0; max(2.0, 2.4, 2.6) = 2.6; 3 rows, 3 values; source 07:52.
- PR-01 10:00: (76+78)/2 = 77.0; max 3.4; 2 rows so `low_coverage` true (2 < 3); source 09:12.
- PR-01 12:00: (82+85+88)/3 = 85.0; max 5.8; 3/3; source 11:52 (the 10:30 reading was ingested at 10:32, after the 10:30 run, but its window had not ended anyway).
- PR-02 08:00: (65+66)/2 = 65.5; max 1.8; 2/2, low coverage; source 07:52.
- PR-02 10:00: (68+70+72)/3 = 70.0; max(1.7, 1.9) = 1.9, the empty value skipped; 3 rows, 2 values; source 10:02.
- PR-03 10:00: (60+62)/2 = 61.0; no vibration value so max is null and the value count 0; low coverage; source 09:52.

**Training set** (`expected/training_set.json`). For each label, the feature
rows of that machine with `available_at` at or before `prediction_time`, then
the newest window. Age = prediction time minus window end, in minutes.
PR-02 at 10:15: the 10:00 window is published at 10:30, so the 08:00 window,
age 135. PR-03 at 09:00 and 10:20: no PR-03 row published yet, so
`none_available`. PR-03 at 13:00: age 180, which is not greater than 180, so
`ok`; at 13:30, 210, `stale`. `label_status` is `known` when `label_time` is at
or before 17:00; PR-03 at 13:30 is known only at 17:30. Usable rows are `ok`
and `known`: eight.

**Leaks** (`expected/leaks.json`). Event-time join: the newest window that
ended by the prediction time; wrong wherever that window was published after
it: PR-02 at 10:15 and PR-03 at 10:20 (both 10:00 windows, published 10:30).
Latest-row lookup: each machine's newest row (PR-01 12:00 at 12:30, PR-02 and
PR-03 10:00 at 10:30); wrong for every prediction before those times: seven.

**Serving** (`expected/serving.json`). The same rule evaluated at the request
time; each response equals the corresponding training row. After the late
readings, PR-01 at 11:45 reads the 11:30 version (78.0), and PR-02 at 12:45
still reads the 10:00 window: the republished 08:00 window is older.

**Drift** (`expected/drift.json`). The port assigns windows by rounding down
and adding two hours, so PR-02's 10:00:00 reading moves to a window ending
12:00 that has not closed at 10:30: PR-02 10:00 becomes (68+70)/2 = 69.0,
max(1.7, 0.0) = 1.7, two rows, low coverage. The port fills empty vibration
with 0.0: PR-03 10:00 max becomes 0.0 and the value count 2. At 08:30 neither
edge case has been ingested and the outputs agree.

**Late rerun** (`expected/late.json`). At 11:30 PR-01's 10:00 window has three
readings: (76+78+80)/3 = 78.0, max 3.9, source 11:05, a new version. At 12:30
PR-02's 08:00 window has three: (65+67+66)/3 = 66.0, max(1.8, 1.5, 1.6) = 1.8,
source 11:40. Only PR-01 at 11:45 is at or after a new version's publication
while that window is still its newest; it changes. `merge_asof` on
`available_at` picks, for PR-02 at 12:45, the row published last (08:00 at
12:30): age 12:45 minus 08:00 = 285, `stale`. The overwrite backfill stamps
every window with end + 30 min; PR-01 10:00 claims 10:30 but uses a reading
ingested at 11:05, and PR-02 08:00 claims 08:30 but uses one ingested at
11:40. Joined, the predictions at PR-01 11:00, PR-02 09:00 and PR-02 10:15
would use those readings before they arrived.

**Reuse** (`expected/reuse.json`). At 10:00 the newest published windows end
at 08:00 and at 12:00 they end at 10:00: every age is 120 minutes, over the
handover model's 90, so `stale`; PR-03 at 10:00 has no row yet. With a
180-minute policy the five would be `ok`.
