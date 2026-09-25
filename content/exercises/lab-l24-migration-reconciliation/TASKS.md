# Lab L24 tasks

Work in `starters/migration_starter.py` (six functions raise
`NotImplementedError`) and check yourself with:

```bash
LAB_L24_SOLUTION=starters.migration_starter python run_tests.py
```

Every expected value below is also in `expected/*.json`; `DATA.md` shows how
each one was derived by hand. The legacy procedure and package are text:
read them, do not try to run them.

## Task 1 — Inventory the old job before translating it (tests 01–02)

Read `legacy/sp_daily_inspections.sql` and `legacy/pkg_csv_import.json` and
write your own inventory first: objects read and written, temporary objects,
time functions, local-time arithmetic, integer division, string comparisons
that a collation decides, NULL replacements, predicates in the ON clause of a
LEFT JOIN, the state table that makes the job incremental, and what the
transaction wraps. Then compare it with `scan_tsql()`.

Expected behaviour: 4 tables read (`erp.inspection`, `erp.inspector`,
`etl.watermark`, `dbo.rpt_quality_detail`), 3 written, one temporary table
(`#affected_days`), `GETDATE` as the only clock, one `DATEADD(HOUR, -6, ...)`
expression, one integer division, 7 string-key comparisons, the watermark as
the only state table, four statements inside the transaction, and a `MERGE`
without `WHEN NOT MATCHED BY SOURCE`. `map_package()` turns the control flow
into four tasks; the mail task runs only when at least one dependency failed.

## Task 2 — Land the extract with explicit types (tests 05–06)

`land()` is provided. Predict its schema before running it: DATETIME text
becomes `timestamp_ntz`, money becomes `decimal(12,2)`. Expected: 12 rows,
exactly one NULL (`inspector_code` on inspection 106), 11 rows as of
`2026-03-04 06:30:00.000`. The key profile must show 2 case or trailing-space
variants of `inspector_code` in P1 and one leading-space code in P2.

## Task 3 — Keys and the outer join (fill `normalize`, `assign_shift`)

Reproduce `LEFT JOIN erp.inspector AS s ON s.inspector_code =
i.inspector_code AND s.plant_code = @plant_code` under a case-insensitive
collation that ignores trailing spaces, then `ISNULL(s.shift_code,
N'UNASSIGNED')`. Expected: `qa07` and `QA07 ` join to QA07 (DAY); the NULL
code and `QA99` stay in the output as UNASSIGNED; in P2 the code ` QA21`
(leading space) does not join and stays UNASSIGNED.

## Task 4 — The business day and its clock (fill `business_day`)

`CAST(DATEADD(HOUR, -6, inspected_at) AS DATE)` ran on the New York server's
wall clock. Expected for the target rule: inspection 103 (02:10 on 3 March)
belongs to 2 March, 109 (05:59:59.997 on 4 March) to 3 March, 110 (06:00:00.000)
to 4 March, and the answer does not change when the session time zone does.
Also implement the `session` rule (an instant rendered in the session zone)
and the `plant_local` rule (06:00 in the plant's own zone) used by later tests.

## Task 5 — Aggregate with the legacy arithmetic (fill `aggregate`)

Expected report for P1 (6 rows): 2 March DAY 1/120/4/4.50/3, NIGHT
2/140/3/0.30/2; 3 March DAY 3/300/8/8.35/2, NIGHT 2/120/3/2.90/2,
UNASSIGNED 2/70/5/15.30/7; 4 March DAY 1/40/0/0.00/0 (inspections, units
inspected, units defective, rework cost, defect percentage). Money stays
`decimal`; `defect_pct` is an integer because T-SQL divides INT by INT.

## Task 6 — Reconcile, then break it on purpose (tests 08–17)

`reconcile()` is provided. Run it for the target (verdict pass) and for the
naive translation (`NAIVE`): verdict fail on every check while the report
still has six rows on both sides. Then run each of the five single flips in
`FLIPS` and predict, before looking, which checks each one fails. Expected:
`binary_keys` fails only the key checks (totals and row counts pass);
`where_filter` also fails the null count; `session_day` moves 103 and 109;
`fractional_division` fails only report keys and types; `double_amounts`
fails types, report keys and totals. Leaving out the as-of filter adds
inspection 112 and is a basis error, not a migration defect.

## Task 7 — Incremental state (fill `affected_days`)

Select rows whose `updated_at` falls in the half-open window `(since, until]`
and return the business days they touch. Expected for tonight: 2, 3 and
4 March, because inspection 101 was corrected at 16:00 on 3 March. Selecting
by `inspected_at` instead returns only 3 and 4 March and leaves 2 March
stale (4 defective in the legacy report, 3 in yours). A failure injected after
the detail write must leave the watermark at `2026-03-03 06:30:00.000` and
the tables inconsistent; the retry must converge to the legacy report. The
next window picks up inspection 112; an empty window changes nothing.

## Task 8 — Transfer and cutover (fill `cutover_gate`; tests 04, 25–28)

Run the target on plant P2 (different codes, a leading space, a plant in
America/Chicago): the legacy-compatible rules reconcile. Switch to the
intended plant-local cutover: inspections 205 and 206 move to 10 March and
every difference must be predicted by the owned entry in
`fixtures/difference_register_p2.json`; with the owner removed, nothing is
explained. Finally implement the gate: ready only after 5 consecutive clean
days since the last code change (an explained day counts only if every
exception has a named owner) and a rehearsed rollback. Expected: `as_logged`
not ready (0 of 5, EXC-07 unowned), `extended` ready, `no_rollback` not ready.
