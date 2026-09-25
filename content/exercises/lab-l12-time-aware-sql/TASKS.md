# Tasks

Work in `starters/portfolio.sql`; keep the `-- query: <name>` markers and the output column
names. Predict each answer by hand from `DATA.md` before you run anything, then check with
`run_tests.py --portfolio starters/portfolio.sql`. `expected/*.json` states each answer and its
derivation; read it after your prediction, not before. Tasks marked "(reference)" have no
starter block: write the block yourself under the same name if you want the test to run
against your version.

## T1 — Running total with an explicit frame (`running_total`)

Per machine, ordered by `day, shift`, add one physical row at a time. Expected behaviour: the
`NULL` shift of M1 on 2026-03-03 adds nothing and the running value stays at 190; M1 ends at
330. The test also reads the analyzed plan and requires a `RowFrame`: the starter's version
without a frame clause returns the same eight numbers on this unique key, yet Spark resolves it
as a `RangeFrame`. Explain why equal numbers do not prove equal queries.

## T2 — The default frame and a tie (`running_total_default_frame`, reference)

Order by `day` only and omit the frame. Expected behaviour: rows that share a day share one
value (both M1 rows on 2026-03-01 read 90) and the plan shows a `RangeFrame`. Explain why.

## T3 — Three-row moving average and a two-day frame (`moving_average`, `range_versus_rows`)

Frame `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW`. Report the rounded average, the number of
measured (non-null) units in the frame, the number of rows in the frame, and whether the frame
is complete (three rows). Expected: M1's fifth row averages 50.0 over 2 measured units in a
3-row frame. Then, over four synthetic days (1, 2, 5 and 6 March with 10, 20, 50, 60 units),
put `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW` beside
`RANGE BETWEEN INTERVAL 2 DAYS PRECEDING AND CURRENT ROW`. Expected: they agree on the first two
days and differ on 5 March (80 against 50) and 6 March (130 against 110).

## T4 — Ranking at a tie (`ranking`; `top_per_plant`, reference)

Rank machines by total units. Expected: M2 and M3 tie at 225; `RANK` gives 3, 3 and skips 4;
`DENSE_RANK` gives 3, 3; `ROW_NUMBER` must be made deterministic with `machine_id`. Then the
top machine per plant: North M1, South M4.

## T5 — Latest inspection revision (`latest_inspection`)

Remove byte-identical replays, keep the highest revision per inspection with the latest
`received_at` as tie-breaker, and flag inspections whose top revision is shared by more than one
distinct row. Expected: 10 rows in, 9 after `DISTINCT`, 6 out; I-104 is flagged. Your block
also defines the `latest_inspections` view that T9 and T10 read, so finish T5 first.

## T6 — DOWN islands (`down_islands`; `down_islands_naive`, reference)

Consecutive DOWN days per machine become one island; a missing day splits an island; an island
that touches the last observed day is `open_at_data_end`. Expected: M1 has three islands (2
days, 1 day, 3 days open); M2 two one-day islands. Also note what the naive
`GROUP BY machine_id` returns.

## T7 — Membership (`semi_down_machines`, `never_inspected_not_exists`; the rest reference)

Machines with at least one DOWN day, each once (expected M1, M2; the starter's inner join
returns 8 rows); machines with no output rows (anti join: M5); machines never inspected written
with `NOT EXISTS` (M4, M5) and with `LEFT ANTI JOIN`. Then write it with `NOT IN` and explain the
empty result.

## T8 — Set operators (`setops_*`, `union_int_and_text`, reference)

Distinct machine sets from output, status, inspections and the registry: `UNION`,
`UNION ALL`, `INTERSECT`, `EXCEPT`, with and without the `NULL` machine. Then the positional
trap: a `UNION ALL` whose second branch lists the columns in the other order (expected: no
error, wrong rows). Finally `SELECT units FROM shift_output UNION ALL SELECT machine_id FROM
machines`: expected `CAST_INVALID_INPUT` under ANSI mode.

## T9 — Nested fields (`explode_counts`; `struct_fields`, `array_fields`, `zero_based_index`, `defect_code_counts`, reference)

Read `measurements.width_mm` and `measurements.weight_g`, compute grams per millimetre, count
`defect_codes`, test for `SCRATCH`, take the first code safely, and count codes across the latest
inspections with `EXPLODE`. Compare the row counts of `EXPLODE` and `LATERAL VIEW OUTER
EXPLODE` (expected 3 and 7). Put `defect_codes[0]` beside `ELEMENT_AT(defect_codes, 1)` for the
two inspections that have codes, and predict what each does on an empty array under ANSI mode.

## T10 — Safe casts and null arithmetic (`try_cast_aggregates`; `try_cast_rows`, `try_cast_edge_cases`, `null_comparisons`, reference)

`raw_units` holds `'12'`, `'n/a'`, `'1,200'`, `'8'`, `'0'`, `'5'`. Convert with `TRY_CAST`,
divide defects by units with `TRY_DIVIDE`, then aggregate. Expected: SUM 25, COUNT(units) 4,
COUNT(*) 6, 2 unparseable, AVG 6.25, zero-filled average 4.17. Predict `TRY_CAST` of `' 8 '`,
`'12.0'` and `'3000000000'` to INT and of `'2026-02-30'` to DATE. Count rows whose weight is
`<> 30.0` and rows where `NOT (weight <=> 30.0)`. The strict `CAST` and plain `/` versions are
executed as failures.

## T11 — Events in New York (`downtime_pairs`; `events_local`, `interval_subtraction`, reference)

Convert UTC instants to `America/New_York` wall clock with offset, give the local hour, the
local day and the UTC day, then pair each STOP with the next START and report elapsed minutes
beside wall-clock minutes. Expected: M2's stop reads 120 elapsed but 180 wall-clock minutes
because 02:00–03:00 did not exist. Predict what `start_ts - stop_ts` returns for M2.

## T12 — Clock changes, months and periods (`fall_back_hour`, `incomplete_period`; the rest reference)

Show that local 2026-03-08 has 24 wall-clock hours but 23 elapsed hours; that "one day later"
and "24 hours later" differ; what Spark does with the local string `2026-03-08 02:30:00` as a
`TIMESTAMP` and as a `TIMESTAMP_NTZ`; the autumn change (a synthetic stoppage from 05:30Z to
06:15Z on 1 November 2026: expected 45 elapsed minutes and a wall-clock difference of −15);
which month M3's downtime belongs to locally and in UTC; the month-end arithmetic facts; and that
March 2026 is incomplete in `shift_output`.

## T13 — Dialect checks (`dialect_datediff`; `dialect_dateadd` and the four failures, reference)

Show Spark's two-argument `DATEDIFF` argument order, the unit form `DATE_DIFF(DAY, start, end)`,
the unit form on the timestamps `2026-03-07 23:30:00` and `2026-03-08 00:00:00` (expected 0) and
the two-argument form on the same timestamps (expected 1), and what `DATEADD` returns. Then run
`ISNULL(NULL, 'x')`, `GETDATE()`, `TRUNC(12.345, 1)` and a `QUALIFY` clause and record the error
class of each.

## Transfer

1. Add `M4 2026-03-03 D 30` to `shift_output`; predict the new ranking.
2. Add `M1 2026-03-07 DOWN` to `machine_status`; predict the islands.
3. Run `downtime_pairs`, `events_local` and `interval_subtraction` after `SET TIME ZONE 'UTC'`;
   predict which minutes, hours and days change.
4. Run the five failing statements of T8–T10 after `SET spark.sql.ansi.enabled = false`; predict
   what each returns instead of an error, and say why that is worse for a report.
