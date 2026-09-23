# Lab L11 data dictionary and derivations

Every record here is synthetic. Cinderline Components, its plants, lines,
supervisors and inspections are fictional teaching records authored by hand for
this lab; there is no generator and no random seed. Nothing was copied from a
real plant, a real schema or a Databricks workspace.

## Files

| File | Rows | Meaning |
|---|---|---|
| `fixtures/<set>/inspections.json` | 22 baseline, 13 transfer | Accepted inspections as they arrive from silver: natural keys, source units |
| `fixtures/<set>/dim_line.json` | 6 baseline, 7 transfer | Line dimension, type 2 on `supervisor`, plus the unknown member |
| `fixtures/<set>/dim_plant.json` | 3 | Plants PN (North), PS (South) and the unknown member |
| `fixtures/<set>/dim_shift.json` | 3 | Shifts A 06:00-14:00, B 14:00-22:00, C 22:00-06:00 (crosses midnight) |
| `fixtures/<set>/dim_date.json` | 12 each | Plant calendar: `is_business_day`, `month`, `note` |
| `fixtures/<set>/unit_conversion.json` | 2 each | Pieces per unit of measure |
| `fixtures/<set>/run.json` | 1 | Reporting period and the window's as-of date |
| `fixtures/metric_contract.json` | 1 | The metric contract that drives the query parameters |

### inspections.json

| Column | Type | Meaning |
|---|---|---|
| inspection_id | STRING | One accepted inspection; the fact grain |
| line_id | STRING | Natural key of the line (N1, N2, S1, S2; N3 and S9 are not in the dimension) |
| shift_id | STRING | A, B or C |
| inspected_at | TIMESTAMP_NTZ | Plant local wall-clock time of the inspection, ISO-8601 without zone |
| inspected_qty | BIGINT | Quantity inspected, in `uom` |
| defective_qty | BIGINT | Quantity found defective, in `uom` |
| uom | STRING | `piece`, `case`, or (transfer only) `tray` |

### dim_line.json

`line_sk` is the surrogate key (unique). `valid_from` is inclusive, `valid_to` is
exclusive, a NULL `valid_to` means still valid, and exactly one row per `line_id`
has `is_current = true`. Row `line_sk = -1` is the unknown member (line
`UNKNOWN`, plant `UNKNOWN`, supervisor `Unknown`).

| line_sk | line_id | plant | supervisor | valid_from | valid_to | set |
|---|---|---|---|---|---|---|
| 101 | N1 | PN | D. Varga | 2026-01-05 | 2026-03-30 | both |
| 102 | N1 | PN | P. Nair | 2026-03-30 | NULL | both |
| 103 | N2 | PN | R. Iqbal | 2026-01-05 | NULL | both |
| 104 | S1 | PS | T. Lindqvist | 2026-01-05 | NULL | both |
| 105 | S2 | PS | J. Castillo | 2026-01-05 | NULL (baseline) / 2026-04-30 (transfer) | both |
| 106 | S2 | PS | E. Haddad | 2026-04-30 | NULL | transfer |

### dim_date.json

Baseline covers 2026-03-23 to 2026-04-03; transfer covers 2026-04-27 to
2026-05-08. Weekends are not business days. The transfer calendar also marks
Friday 2026-05-01 as a plant shutdown (`is_business_day = false`).

### unit_conversion.json

Baseline: `piece` = 1, `case` = 12. Transfer: `piece` = 1, `case` = 24 (a new
case pack). `tray` has no row in either set, so a tray inspection cannot be
expressed in pieces.

### run.json

Baseline: period 2026-03-26 to 2026-04-01, window as of Monday 2026-03-30.
Transfer: period 2026-04-29 to 2026-05-04, window as of Monday 2026-05-04.

## How the expected values were derived

Every number in `expected/` was derived by hand from the tables below: convert
each inspection to pieces (quantity x pieces per unit), assign it to its
business day (the date part of the local timestamp, per the contract's
00:00:00-23:59:59 rule) and to the line version valid that day, then add. A
rate is written as the fraction `[defective, inspected]`; the tests compare
Spark's double with Python's `defective / inspected` of those two authored
integers, which is the same IEEE division. A rate is `null` when no piece was
inspected. The two averages of rates (0.035 and 0.02125 baseline, 0.03 and
0.024 transfer) are decimals computed on paper and compared within 1e-12,
because AVG adds doubles in an order the engine chooses. As an arithmetic check
only, the same numbers were re-added once in a throwaway plain-Python script
that shares no code with `solutions/`; it is not part of the package.

## Baseline derivations

### Inspections in pieces

| id | line | shift | local time | source qty | pieces inspected / defective | business day |
|---|---|---|---|---|---|---|
| I-01 | N1 | A | 03-26 08:45 | 150 / 3 piece | 150 / 3 | 03-26 |
| I-02 | S1 | A | 03-26 09:20 | 120 / 0 piece | 120 / 0 | 03-26 |
| I-03 | N2 | B | 03-26 15:10 | 50 / 0 piece | 50 / 0 | 03-26 |
| I-04 | S2 | B | 03-26 16:00 | 10 / 0 case | 120 / 0 | 03-26 |
| I-05 | S1 | A | 03-27 08:30 | 180 / 3 piece | 180 / 3 | 03-27 |
| I-06 | N1 | A | 03-27 09:15 | 120 / 3 piece | 120 / 3 | 03-27 |
| I-07 | N2 | A | 03-27 10:05 | 100 / 5 piece | 100 / 5 | 03-27 |
| I-08 | S2 | B | 03-27 15:20 | 10 / 1 case | 120 / 12 | 03-27 |
| I-09 | N1 | B | 03-27 16:40 | 80 / 1 piece | 80 / 1 | 03-27 |
| I-10 | N1 | A | 03-30 07:50 | 150 / 3 piece | 150 / 3 | 03-30 |
| I-11 | N2 | A | 03-30 09:40 | 100 / 1 piece | 100 / 1 | 03-30 |
| I-12 | S1 | B | 03-30 14:45 | 180 / 3 piece | 180 / 3 | 03-30 |
| I-13 | N1 | B | 03-30 18:10 | 50 / 2 piece | 50 / 2 | 03-30 |
| I-14 | N1 | A | 03-31 08:20 | 100 / 1 piece | 100 / 1 | 03-31 |
| I-15 | S2 | A | 03-31 09:00 | 5 / 0 case | 60 / 0 | 03-31 |
| I-16 | N2 | A | 03-31 10:30 | 0 / 0 piece | 0 / 0 | 03-31 |
| I-17 | N1 | C | 03-31 23:10 | 100 / 3 piece | 100 / 3 | 03-31 |
| I-18 | S1 | C | 03-31 23:59:59 | 60 / 3 piece | 60 / 3 | 03-31 |
| I-19 | S1 | C | 04-01 00:00:00 | 60 / 3 piece | 60 / 3 | 04-01 |
| I-20 | N1 | A | 04-01 09:30 | 250 / 5 piece | 250 / 5 | 04-01 |
| I-21 | N3 | A | 04-01 11:00 | 50 / 2 piece | 50 / 2 | 04-01 |
| I-22 | S2 | B | 04-01 17:30 | 20 / 1 case | 240 / 12 | 04-01 |

Totals: 22 inspections; inspected 150+120+50+120+180+120+100+120+80+150+100+180
+50+100+60+0+100+60+60+250+50+240 = 2,440 pieces; defective
3+0+0+0+3+3+5+12+1+3+1+3+2+1+0+0+3+3+3+5+2+12 = 65 pieces. No unit is
unconvertible, so the quarantine is empty and `fact_inspection` has 22 rows.

### Keys

N3 has no row in `dim_line`, so I-21 is the only line orphan and maps to the
unknown member. Every shift and every business day exists in its dimension.
N1's versions meet on 2026-03-30: I-01, I-06 and I-09 (before) belong to D.
Varga's version 101; I-10, I-13, I-14, I-17 and I-20 to P. Nair's version 102.
No dimension check finds a problem: no duplicate inspection, no overlapping
versions, one current row per line, unique surrogate keys.

### line_day (21 rows)

The grid is five business days (03-26, 03-27, 03-30, 03-31, 04-01) for N2, S1
and S2, plus N1 split across its two versions, plus the observed unknown-line
day. Status is `no_inspections` when a grid cell has no inspection and
`no_units` when its inspections sum to zero pieces.

| day | N1 | N2 | S1 | S2 | UNKNOWN |
|---|---|---|---|---|---|
| 03-26 | 150/3 (D. Varga) | 50/0 | 120/0 | 120/0 | |
| 03-27 | 120+80=200 / 3+1=4 (D. Varga) | 100/5 | 180/3 | 120/12 | |
| 03-30 | 150+50=200 / 3+2=5 (P. Nair) | 100/1 | 180/3 | no_inspections | |
| 03-31 | 100+100=200 / 1+3=4 | 0/0 no_units | 60/3 | 60/0 | |
| 04-01 | 250/5 | no_inspections | 60/3 | 240/12 | 50/2 |

Zero-rate rows (a real 0, not a missing rate): 03-26 N2, S1, S2 and 03-31 S2.

### plant_day (11 rows) and plant_month (5 rows)

Plant-day = sum of that plant's line-day parts:

| day | PN (N1+N2) | PS (S1+S2) | UNKNOWN |
|---|---|---|---|
| 03-26 | 150+50=200 / 3+0=3, 2 insp. | 120+120=240 / 0, 2 insp. | |
| 03-27 | 200+100=300 / 4+5=9, 3 insp. | 180+120=300 / 3+12=15, 2 insp. | |
| 03-30 | 200+100=300 / 5+1=6, 3 insp. | 180/3, 1 insp. | |
| 03-31 | 200+0=200 / 4+0=4, 3 insp. | 60+60=120 / 3+0=3, 2 insp. | |
| 04-01 | 250/5, 1 insp. | 60+240=300 / 3+12=15, 2 insp. | 50/2, 1 insp. |

Plant-month: PN March 200+300+300+200 = 1,000 / 3+9+6+4 = 22 (11 inspections);
PS March 240+300+180+120 = 840 / 0+15+3+3 = 21 (7); PN April 250/5 (1); PS
April 300/15 (2); UNKNOWN April 50/2 (1). Sum 2,440 / 65 and 22 inspections.

Boundary: I-18 (23:59:59) and I-19 (00:00:00) are both night shift C on S1, yet
fall on 03-31 (month 2026-03) and 04-01 (month 2026-04).

### Rates do not add

PN on 03-27: line rates 4/200 = 0.02 and 5/100 = 0.05, average 0.035, while the
plant rate is 9/300 = 0.03. PN in March: day rates 3/200 = 0.015, 9/300 = 0.03,
6/300 = 0.02 and 4/200 = 0.02, average 0.085/4 = 0.02125, while the month rate
is 22/1000 = 0.022.

### Zero denominator

N2 on 03-31 has one inspection with 0 pieces, so plain `SUM/SUM` meets 0/0 and
Spark's ANSI mode raises `DIVIDE_BY_ZERO`; the contract gives `no_units` and a
NULL rate. `no_inspections`: S2 on 03-30 and N2 on 04-01.

### Units (naive: source quantities summed as if all were pieces)

PS by day: 03-26 120+10 = 130 / 0; 03-27 180+10 = 190 / 3+1 = 4; 03-30 180/3;
03-31 5+60 = 65 / 0+3 = 3; 04-01 60+20 = 80 / 3+1 = 4. PN and UNKNOWN rows are
unchanged because they hold pieces only. Against the contract, the rate differs
on 03-27 (4/190 against 15/300) and 03-31 (3/65 against 3/120); on 03-26 (0
against 0) and 04-01 (4/80 = 0.05 against 15/300 = 0.05) the sums differ while
the rate happens to agree. S2's own line-day rows are unit-free ratios: 10/0,
10/1, 5/0 and 20/1 give the same rates as 120/0, 120/12, 60/0 and 240/12.

### Missing dimension key

An inner join to `dim_line` keeps 21 rows, 2,440-50 = 2,390 / 65-2 = 63 pieces.
A left join without the unknown member keeps I-21 under a NULL plant: NULL 1 row
50/2; PN 12 rows 1,250/27; PS 9 rows 1,140/36.

### Many-to-many history join (natural key only)

N1 has two versions, so its 8 inspections (1,000/21 pieces) each match twice:
16 + N2 4 + S1 5 + S2 4 = 29 rows (N3 matches nothing). By plant: PN 20 rows,
2,000+250 = 2,250 / 42+6 = 48; PS 9 rows, 1,140/36. By supervisor: D. Varga and
P. Nair each claim all 8 N1 rows (1,000/21); R. Iqbal 4 (250/6); T. Lindqvist 5
(600/12); J. Castillo 4 (540/24). As-was (type 2): D. Varga 3 rows 150+120+80 =
350 / 3+3+1 = 7; P. Nair 5 rows 150+50+100+100+250 = 650 / 3+2+1+3+5 = 14; the
others as above; Unknown 1 row 50/2. As-is (type 1, today's supervisor): P.
Nair 8 rows 1,000/21, others unchanged.

### Windows as of Monday 2026-03-30, length 3

Business days: 03-26, 03-27, 03-30. PN 200+300+300 = 800 / 3+9+6 = 18 (8
inspections); PS 240+300+180 = 720 / 0+15+3 = 18 (5). Calendar days: 03-28,
03-29, 03-30, of which one is a business day: PN 300/6 (3), PS 180/3 (1).
Weekdays (Monday to Friday) are the same three business days here because the
baseline calendar has no shutdown.

### Broken history (negative case)

Moving version 101's `valid_to` to 2026-03-31 makes it overlap version 102 on
2026-03-30, so I-10 (150/3) and I-13 (50/2) each match two versions: 24 fact
rows, 2,440+200 = 2,640 / 65+5 = 70 pieces, and the overlap check names N1.

## Transfer derivations

Changes from the baseline: a new case pack (24 pieces), a supervisor change on
S2 dated 2026-04-30, a shutdown on Friday 2026-05-01, an unknown line S9 and a
`tray` inspection with no conversion.

| id | line | shift | local time | source qty | pieces | business day |
|---|---|---|---|---|---|---|
| T-01 | N1 | A | 04-29 08:00 | 100 / 2 piece | 100 / 2 | 04-29 |
| T-02 | S1 | A | 04-29 09:00 | 80 / 2 piece | 80 / 2 | 04-29 |
| T-03 | S2 | B | 04-29 15:00 | 5 / 0 case | 120 / 0 | 04-29 |
| T-04 | S1 | C | 04-29 23:30 | 40 / 1 piece | 40 / 1 | 04-29 |
| T-05 | S1 | C | 04-30 00:30 | 40 / 1 piece | 40 / 1 | 04-30 |
| T-06 | N1 | A | 04-30 10:00 | 150 / 3 piece | 150 / 3 | 04-30 |
| T-07 | N2 | A | 04-30 11:00 | 100 / 4 piece | 100 / 4 | 04-30 |
| T-08 | S9 | A | 04-30 12:00 | 60 / 3 piece | 60 / 3 | 04-30 |
| T-09 | S2 | B | 04-30 16:00 | 10 / 1 case | 240 / 24 | 04-30 |
| T-10 | N2 | B | 04-30 17:00 | 20 / 1 tray | quarantined | 04-30 |
| T-11 | N1 | A | 05-04 08:30 | 200 / 2 piece | 200 / 2 | 05-04 |
| T-12 | S1 | A | 05-04 09:30 | 0 / 0 piece | 0 / 0 | 05-04 |
| T-13 | S2 | B | 05-04 15:45 | 5 / 0 case | 120 / 0 | 05-04 |

13 inspections, 1 quarantined (T-10, `no_unit_conversion`), 12 in the fact:
100+80+120+40+40+150+100+60+240+200+0+120 = 1,250 / 2+2+0+1+1+3+4+3+24+2+0+0 =
42 pieces. Orphans: line T-08, unit T-10.

Business days in the period: 04-29, 04-30, 05-04 (05-01 shutdown, 05-02 and
05-03 weekend). S2's version 105 (J. Castillo) covers 04-29; version 106 (E.
Haddad) starts on 04-30 inclusive, so T-09 and T-13 belong to it.

line_day (13 rows): 04-29 N1 100/2 (P. Nair), N2 no_inspections, S1 80+40 =
120 / 2+1 = 3 (2 insp.), S2 120/0 (J. Castillo); 04-30 N1 150/3, N2 100/4 (the
tray is not counted), S1 40/1, S2 240/24 (E. Haddad), UNKNOWN 60/3; 05-04 N1
200/2, N2 no_inspections, S1 0/0 no_units, S2 120/0 (E. Haddad).

plant_day (7 rows): 04-29 PN 100/2 (1), PS 120+120 = 240 / 3 (3); 04-30 PN
150+100 = 250 / 3+4 = 7 (2), PS 40+240 = 280 / 1+24 = 25 (2), UNKNOWN 60/3
(1); 05-04 PN 200/2 (1), PS 0+120 = 120 / 0 (2). plant_month (5 rows): April PN
100+250 = 350 / 2+7 = 9 (3), PS 240+280 = 520 / 3+25 = 28 (5), UNKNOWN 60/3
(1); May PN 200/2 (1), PS 120/0 (2).

Boundary: T-04 (04-29 23:30) and T-05 (04-30 00:30) are both shift C on S1 and
fall on two business days of the same month.

Rates do not add: PN on 04-30, line rates 3/150 = 0.02 and 4/100 = 0.04,
average 0.03 against the plant's 7/250 = 0.028; PN in April, day rates 0.02 and
0.028, average 0.024 against the month's 9/350.

Zero denominator: S1 on 05-04 (0/0) raises `DIVIDE_BY_ZERO` under plain
division and is `no_units` in the contract; N2 on 04-29 and 05-04 is
`no_inspections`; S2 on 04-29 and 05-04 has a real zero rate.

Units (naive): PN 04-29 100/2; PS 04-29 80+5+40 = 125 / 2+0+1 = 3; PN 04-30
150+100+20 = 270 / 3+4+1 = 8 (the tray is summed as if pieces); PS 04-30 40+10 =
50 / 1+1 = 2; UNKNOWN 04-30 60/3; PN 05-04 200/2; PS 05-04 0+5 = 5 / 0. Rate
differs on 04-29 PS, 04-30 PN and 04-30 PS; on 05-04 PS the sums differ (5
against 120) while both rates are 0. Naive line-day: S2 5/0, 10/1, 5/0 (same
rates as in pieces) and N2 on 04-30 100+20 = 120 / 4+1 = 5, which differs from
the contract's 100/4 because the tray was summed.

Missing key: inner join 11 rows (T-08 lost; T-10 is excluded by the unit join
in both queries), 1,250-60 = 1,190 / 42-3 = 39. Left join: NULL 1 row 60/3; PN
4 rows 100+150+100+200 = 550 / 2+3+4+2 = 11; PS 7 rows 80+120+40+40+240+0+120 =
640 / 2+0+1+1+24+0+0 = 28.

Many-to-many: N1's 3 inspections (450/7) and S2's 3 (480/24) each meet two
versions: 6 + N2 1 + S1 4 + 6 = 17 rows. By plant PN 7 rows 900+100 = 1,000 /
14+4 = 18; PS 10 rows 160+960 = 1,120 / 4+48 = 52. By supervisor D. Varga and
P. Nair 3 rows 450/7 each; J. Castillo and E. Haddad 3 rows 480/24 each; R.
Iqbal 1 row 100/4; T. Lindqvist 4 rows 160/4. As-was: E. Haddad 2 rows 240+120
= 360 / 24; J. Castillo 1 row 120/0; P. Nair 3 rows 450/7; R. Iqbal 1 100/4; T.
Lindqvist 4 160/4; Unknown 1 60/3. As-is: E. Haddad 3 rows 480/24, J. Castillo
absent, the rest unchanged.

Windows as of Monday 2026-05-04, length 3: business days 04-29, 04-30, 05-04:
PN 100+250+200 = 550 / 2+7+2 = 11 (4 insp.), PS 240+280+120 = 640 / 3+25+0 =
28 (7), UNKNOWN 60/3 (1). Calendar days 05-02, 05-03, 05-04 (one business day):
PN 200/2 (1), PS 120/0 (2). Weekdays ignoring the shutdown: 04-30, 05-01,
05-04: PN 250+200 = 450 / 7+2 = 9 (3 insp., 2 days), PS 280+120 = 400 / 25 (4
insp., 2 days), UNKNOWN 60/3.
