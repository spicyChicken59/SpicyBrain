# Lab L24 data

All files are original synthetic teaching data for the fictional Cinderline
Components. They were written by hand; there is no generator and no seed.
No row comes from a real system, and SQL Server was never run to produce the
legacy files: they record what the procedure text does under the documented
behaviour of its data types and operators, derived below.

## Fixtures

| File | Rows | Meaning |
|---|---|---|
| `run_context.json` | — | server clock America/New_York (no offset stored), 06:00 cutoff, source collation `SQL_Latin1_General_CP1_CI_AS`, as-of moments and watermark windows |
| `plants.json` | 2 | P1 in America/New_York, P2 in America/Chicago |
| `inspectors.json` | 4 | P1: QA07 DAY, QA11 NIGHT; P2: QA21 DAY, QA22 NIGHT |
| `inspections_p1.json` | 12 | extract of `erp.inspection` for P1 taken after 06:40 on 4 March |
| `legacy_state_before_p1.json` | 3 + 2 | detail, report and watermark left by the run of 3 March 06:30 |
| `legacy_detail_p1.json` | 11 | `dbo.rpt_quality_detail` after the run of 4 March 06:30 |
| `legacy_report_p1.json` | 6 | `dbo.rpt_quality_daily` after the same run |
| `inspections_p2.json` | 6 | transfer extract for P2 (times on the New York server clock) |
| `legacy_detail_p2.json`, `legacy_report_p2.json` | 6, 5 | legacy outputs for P2 |
| `difference_register_p2.json` | 1 | the owned expected difference for the plant-local rule |
| `parallel_run.json` | 3 scenarios | daily reconciliation verdicts for the cutover gate |

Columns of an inspection: `inspection_id` (INT), `plant_code`, `lot_id`,
`inspector_code` (NVARCHAR as stored, may be NULL or padded), `inspected_at`
and `updated_at` (DATETIME text, milliseconds already on the .000/.003/.007
grid), `units_inspected`, `units_defective` (INT), `rework_cost`
(DECIMAL(12,2) as text, so no float ever touches it).

## P1 derivation (target rules = legacy behaviour)

Business day = date of (local time − 6 h) on the server clock. Shift = the
inspector matched case-insensitively with trailing spaces ignored, else
UNASSIGNED. Rows updated after 06:30 on 4 March (112) are outside the basis.

| id | local time | day | code → shift | units / def / cost |
|---|---|---|---|---|
| 101 | 03-02 07:15 | 03-02 | QA07 → DAY | 120 / 4 / 4.50 |
| 102 | 03-02 22:40 | 03-02 | QA11 → NIGHT | 80 / 2 / 0.10 |
| 103 | 03-03 02:10 | 03-02 | QA11 → NIGHT | 60 / 1 / 0.20 |
| 104 | 03-03 08:05 | 03-03 | qa07 → DAY | 100 / 5 / 7.25 |
| 105 | 03-03 09:30 | 03-03 | `QA07 ` → DAY | 90 / 0 / 0.00 |
| 106 | 03-03 11:45 | 03-03 | NULL → UNASSIGNED | 40 / 4 / 12.00 |
| 107 | 03-03 13:00 | 03-03 | QA07 → DAY | 110 / 3 / 1.10 |
| 108 | 03-03 23:20 | 03-03 | QA11 → NIGHT | 70 / 2 / 2.20 |
| 109 | 03-04 05:59:59.997 | 03-03 | QA11 → NIGHT | 50 / 1 / 0.70 |
| 110 | 03-04 06:00:00.000 | 03-04 | QA07 → DAY | 40 / 0 / 0.00 |
| 111 | 03-03 15:00 | 03-03 | QA99 → UNASSIGNED | 30 / 1 / 3.30 |

Report (defect % = defective × 100 DIV units, truncated): 03-02 DAY 1 / 120
/ 4 / 4.50 / 400÷120 = 3; 03-02 NIGHT 2 / 140 / 3 / 0.30 / 300÷140 = 2; 03-03
DAY 3 / 300 / 8 / 8.35 / 800÷300 = 2; 03-03 NIGHT 2 / 120 / 3 / 2.90 /
300÷120 = 2; 03-03 UNASSIGNED 2 / 70 / 5 / 15.30 / 500÷70 = 7; 03-04 DAY 1 /
40 / 0 / 0.00 / 0. Day totals: 03-02 260 / 7 / 4.80; 03-03 490 / 16 / 26.55;
03-04 40 / 0 / 0.00. Spark types: counts and integer sums BIGINT, money
`decimal(22,2)` after SUM of `decimal(12,2)`.

## Flip derivations

- **binary_keys**: `qa07` and `QA07 ` do not equal QA07 → UNASSIGNED. 03-03
  DAY = 107 only: 1 / 110 / 3 / 1.10 / 300÷110 = 2. 03-03 UNASSIGNED = 104,
  105, 106, 111: 4 / 260 / 10 / 22.55 / 1000÷260 = 3. Day totals unchanged.
- **where_filter**: `s.plant_code = 'P1'` in WHERE removes rows with no
  match (106 NULL, 111 QA99): UNASSIGNED missing; 03-03 totals 420 / 11 /
  11.25; NULL codes 1 → 0; detail 11 → 9 rows, report 6 → 5.
- **session_day** (UTC session): New York is UTC−5 before 8 March, so the
  cutoff falls at 01:00 local. 103 (02:10 → 07:10Z) moves to 03-03; 109
  (05:59:59.997 → 10:59:59.997Z) moves to 03-04 NIGHT (extra key). 03-02
  NIGHT 1 / 80 / 2 / 0.10 / 2; 03-03 NIGHT 2 / 130 / 3 / 2.40 / 2. Under an
  America/New_York session the same code matches the legacy output.
- **fractional_division**: 400/120 = 3.3333333333333335, 300/140 =
  2.142857142857143, 800/300 = 2.6666666666666665, 300/120 = 2.5, 500/70 =
  7.142857142857143 (IEEE doubles); 0/40 = 0.0 equals 0.
- **double_amounts**: sums in binary floating point print 0.30000000000000004
  (0.1 + 0.2) and 2.9000000000000004 (2.2 + 0.7); 4.5, 8.35, 15.3 and 0.0
  print exactly. Totals compare the printed values as decimals: 4.5 +
  0.30000000000000004 = 4.80000000000000004; 8.35 + 2.9000000000000004 +
  15.3 = 26.5500000000000004.
- **naive** (all five): kept rows 101, 102, 103, 107, 108, 109, 110; report
  03-02 DAY 120 / 4 / 4.5 / 3.3333333333333335, 03-02 NIGHT 80 / 2 / 0.1 /
  2.5, 03-03 DAY 110 / 3 / 1.1 / 2.727272727272727, 03-03 NIGHT 130 / 3 /
  2.4000000000000004 / 2.3076923076923075, 04 DAY 40 / 0 / 0.0 / 0.0, 04
  NIGHT 50 / 1 / 0.7 / 2.0: six rows, like the legacy report.
- **no as-of filter**: 112 (06:40, 60 / 2 / 1.25) joins 03-04 DAY: 2 / 100 /
  2 / 1.25 / 2.

## Incremental derivation

Tonight's window is (03-03 06:30, 03-04 06:30]. Updated inside it: 101
(16:00, the correction), 104–111 → days 03-02, 03-03, 03-04. By event time
(`inspected_at` > 03-03 06:30): 104–111 → 03-03 and 03-04 only, so 03-02 keeps
the first version of 101: DAY 120 / 3 / 4.50 / 300÷120 = 2, one defective
fewer on the day. Next window (03-04 06:30, 03-05 06:30]: 112 → 03-04 DAY
2 / 100 / 2 / 1.25 / 200÷100 = 2. The window after that selects nothing.

## Transfer derivation (P2)

New York and Chicago are both on daylight time after 8 March 2026 and one
hour apart. Legacy days use the New York clock: 201 03-10 DAY; 202 ` QA21`
(leading space, no match) 03-10 UNASSIGNED; 203 `qa22  ` 03-10 NIGHT; 204
05:45 → 03-10 NIGHT; 205 06:25 → 03-11 NIGHT; 206 06:05 → 03-11 DAY. Report:
03-10 DAY 1 / 200 / 6 / 5.40 / 3; NIGHT 2 / 220 / 6 / 4.50 / 2; UNASSIGNED 1
/ 150 / 3 / 2.10 / 2; 03-11 DAY 1 / 90 / 0 / 0.00 / 0; NIGHT 1 / 80 / 1 /
0.35 / 1. With `trim`, 202 joins DAY: 03-10 DAY 2 / 350 / 9 / 7.50 / 900÷350 =
2. Plant-local days: 205 is 05:25 and 206 is 05:05 in Chicago, both before
06:00, so both move to 03-10: DAY 2 / 290 / 6 / 5.40 / 2, NIGHT 3 / 300 / 7 /
4.85 / 2; both 03-11 keys disappear.

## Type emulation

`datetime_round()` moves fractional seconds to the nearest 1/300-second tick
(halves rounded up) and prints it to the millisecond, which reproduces the
.000/.003/.007 increments described for DATETIME: .999 → next second .000;
.995–.998 → .997; .992–.994 → .993; .990–.991 → .990; .001 → .000; .002 →
.003; .005 → .007. A raw value of 05:59:59.999 therefore belongs to 3 March
while its DATETIME form, 06:00:00.000, belongs to 4 March.

## Cutover scenarios

`as_logged`: the last code change is 11 March; 11, 12 (owned exception) and
13 March qualify, 16 March has EXC-07 with no owner, so the run of clean days
restarts at 0. `extended`: five qualifying days from 11 to 17 March and a
rehearsed rollback → ready. `no_rollback`: five clean days, rollback not
rehearsed → not ready.

## Independent cross-check

`expected/derive_expected.py` recomputes the P1, P2, flip, incremental,
rounding and gate literals with the standard library (zoneinfo, Decimal,
floor division) and shares no code with the solution. It agreed with every
literal before the Spark solution was first run.
