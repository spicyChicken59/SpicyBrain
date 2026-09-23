# Data dictionary and derivations

All five fixtures are original synthetic records for the fictional plant Cinderline
Components. They were written by hand (no generator, no seed) so that every expected number can
be derived on paper. Nothing is copied from a real system. A few queries also use literal
values written in the query itself (four synthetic days for the RANGE frame, the November
stoppage, the `TRY_CAST` edge cases and the calendar facts); those literals are listed with the
query in `solutions/portfolio.sql`.

## fixtures/machines.json — registry (5 rows)

| column | type | meaning |
|---|---|---|
| machine_id | STRING | M1..M5 |
| machine_name | STRING | Press A, Press B, Lathe, Grinder, Coater |
| plant | STRING | North (M1, M2) or South (M3, M4, M5) |

M5 has no rows anywhere else: it is the anti-join case.

## fixtures/shift_output.json — units per machine, day and shift (19 rows)

| column | type | meaning |
|---|---|---|
| machine_id | STRING | M1..M4 |
| day | DATE | 2026-03-01 .. 2026-03-04 |
| shift | STRING | D (day) or N (night); D sorts before N |
| units | INT, nullable | one NULL: M1 2026-03-03 D (count not recorded) |

Rows are deliberately not stored in (machine, day, shift) order. M2 has no night shift on
2026-03-02 (a missing row, not a NULL). Machine totals: M1 = 50+40+55+45+50+60+30 = 330;
M2 = 30+30+35+40+20+45+25 = 225; M3 = 100+125 = 225; M4 = 150+150 = 300. M2 and M3 tie by
design. `(machine_id, day, shift)` is unique, which is why a missing frame clause can hide.

## fixtures/inspections.json — inspection revisions (10 rows)

| column | type | meaning |
|---|---|---|
| inspection_id | STRING | I-100 .. I-105 |
| revision | INT | source revision number |
| received_at | STRING | UTC instant, ISO-8601 with `Z` |
| machine_id | STRING, nullable | I-105 names no machine (NULL) |
| result | STRING | PASS or FAIL |
| measurements | STRUCT<width_mm DOUBLE, weight_g DOUBLE> | either field may be NULL |
| defect_codes | ARRAY<STRING> | may be empty |
| raw_units | STRING | untyped count as received: `12`, `n/a`, `1,200`, ` 8 `, `8`, `0`, `5` |

Deliberate cases: I-100 has two revisions; I-102 revision 1 arrives twice, byte-identical (a
replay); I-103 revision 2 shares its `received_at` with revision 1; I-104 has two DIFFERENT rows
both labelled revision 1, five minutes apart (a source defect that a tie-breaker must not hide
silently); I-105 has a NULL machine (the `NOT IN` trap).

## fixtures/machine_status.json — daily status (19 rows)

| column | type | meaning |
|---|---|---|
| machine_id | STRING | M1 or M2 only |
| day | DATE | 2026-03-01 .. 2026-03-10 |
| status | STRING | UP or DOWN |

M1: 01 UP, 02 DOWN, 03 DOWN, 04 UP, 05 UP, 06 DOWN, **07 missing**, 08 DOWN, 09 DOWN, 10 DOWN.
M2: 01 DOWN, 02–04 UP, 05 DOWN, 06–10 UP. The last observed day in the table is 2026-03-10.

## fixtures/machine_events.json — stop/start events (8 rows)

| column | type | meaning |
|---|---|---|
| event_id | STRING | e1 .. e8 |
| machine_id | STRING | M1, M2, M3 |
| event_type | STRING | STOP or START |
| event_time_utc | STRING | UTC instant, ISO-8601 with `Z` |

The instants straddle the New York change from EST (UTC−05:00) to EDT (UTC−04:00) at
2026-03-08 07:00:00Z (02:00 → 03:00 local), and one pair straddles the March/April boundary in
UTC but not in New York. The autumn change (2026-11-01 06:00:00Z, 02:00 EDT → 01:00 EST) is
exercised by a synthetic pair written as literals in the `fall_back_hour` query.

## How the expected values were derived

Every file in `expected/` carries `derivation` fields. The method per file:

- **windows.json** — arithmetic on paper: running sums row by row; for the default frame, the sum
  through every row sharing the current day; moving averages as (sum of non-null units in the
  last three rows) / (count of non-null units), rounded half-up to two decimals; for
  `range_versus_rows`, the sum of the rows within two days of the current day against the sum of
  the current and two previous rows. `frame_kinds` holds Spark's own names for the two frame
  types, `RowFrame` and `RangeFrame`, as they appear in the analyzed plan (read once from this
  build and frozen).
- **ranking.json** — sort the four totals; apply the definitions of RANK (ties share, next rank
  skipped), DENSE_RANK (no skip) and ROW_NUMBER with `machine_id` as the tie-breaker.
- **dedup.json** — count rows, remove the identical pair, then keep per inspection the highest
  revision and, within it, the latest received instant; flag a top revision held by two rows.
- **islands.json** — number the DOWN days per machine 1..n and subtract the number from the
  date; equal results are one island.
- **membership.json / setops.json** — set membership by inspection of the fixtures; NULL
  handling follows the documented rules (a NULL in a `NOT IN` subquery makes the predicate
  unknown; set operators treat NULLs as one value).
- **nested.json / casts.json** — arithmetic by hand; `TRY_CAST` returns NULL for `n/a`, `1,200`
  (comma), an INT overflow and an impossible date; `TRY_DIVIDE` returns NULL for a zero or NULL
  divisor; SUM/AVG/COUNT(col) ignore NULL, COUNT(*) does not; the bracket index is 0-based and
  `ELEMENT_AT` 1-based. Two `TRY_CAST` results are recorded from this build: blanks around
  ` 8 ` are trimmed (8), and `12.0` is not accepted as an INT (NULL).
- **time.json** — an independent conversion with Python's standard-library `zoneinfo` (IANA
  data, no Spark), reproducible with `python expected/derive_time.py`, which prints OK for each
  of its 11 values: each UTC instant to `America/New_York`, the local hour and day, elapsed
  minutes as the difference of instants, wall-clock minutes as the difference of the local clock
  readings; elapsed hours of a local day as the difference of its midnight instants in UTC
  (2026-03-08 00:00 EST = 05:00Z, 2026-03-09 00:00 EDT = 04:00Z, so 23 hours). A local time in
  the spring gap moves forward by the gap and an ambiguous autumn time takes the earlier offset,
  which is both what the Databricks archive page on Spark 3 dates describes and what
  `zoneinfo`'s `fold=0` gives. Recorded from this build rather than derived: that
  `TIMESTAMPDIFF` and timestamp subtraction use local clock readings, and the text layout
  `INTERVAL 'd hh:mm:ss' DAY TO SECOND`.
- **periods.json** — calendar facts (February 2026 has 28 days) and the fixture's date range.
- **dialect.json** — the documented Spark signatures: two-argument `datediff(end, start)`
  subtracts; the unit form counts whole units between two timestamps and truncates the
  fraction (30 minutes is 0 days); the two-argument form on timestamps compares their dates.
  The error classes were read off the executed error messages once and then frozen so that a
  future engine change is detected.
- **ansi.json** — the same failing statements with ANSI mode off, derived by hand: without ANSI
  the common type of INT and STRING is STRING, an unparseable cast is NULL, division by zero is
  NULL and an index past the end of an array is NULL.
- **transfer.json** — the same methods applied to the altered inputs.

`run_tests.py` compares executed rows with these literals and never computes an expectation
from the solution; `expected/derive_time.py` is not imported by the runner.
