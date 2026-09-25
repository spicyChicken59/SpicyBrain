# Lab L11 solutions

The reference is `solutions/model.sql`; every statement below is quoted from
it. Outputs are the baseline's, as collected by the tests (the literals are in
`expected/baseline.json`, derived by hand in DATA.md).

## 1. The fact at its grain

One row of `fact_inspection` is one accepted inspection. The line version is
resolved once, at load, into the surrogate key, so every report joins
`fact_inspection.line_sk = dim_line.line_sk`, which is many-to-one because
`line_sk` is unique in the dimension.

```sql
WITH resolved AS (
  SELECT s.*, l.line_sk
  FROM silver_dated s
  LEFT JOIN dim_line l
    ON l.line_id = s.line_id
   AND s.business_date >= l.valid_from
   AND (l.valid_to IS NULL OR s.business_date < l.valid_to)
)
SELECT r.inspection_id,
       COALESCE(r.line_sk, :unknown_line_sk) AS line_sk,
       ...
       r.inspected_qty * u.pieces_per_uom AS inspected_pieces,
       r.defective_qty * u.pieces_per_uom AS defective_pieces
FROM resolved r
JOIN unit_conversion u ON u.uom = r.uom
```

`silver_dated` adds `business_date = CAST(inspected_at AS DATE)`: the
contract's business day runs 00:00:00 to 23:59:59 plant local time and
`inspected_at` is a plant wall-clock `TIMESTAMP_NTZ`, so the date part is the
business day. That is why I-18 (23:59:59, night shift C) lands on 31 March
and I-19 (00:00:00, the same shift) on 1 April and in a different month.

Intermediate output (selected rows):

| inspection | source line | business day | line_sk | pieces |
|---|---|---|---|---|
| I-09 | N1 | 2026-03-27 | 101 (D. Varga) | 80 / 1 |
| I-10 | N1 | 2026-03-30 | 102 (P. Nair) | 150 / 3 |
| I-08 | S2 | 2026-03-27 | 105 | 120 / 12 (10 cases) |
| I-21 | N3 | 2026-04-01 | -1 (unknown member) | 50 / 2 |

Checks that run before any report: no duplicate inspection id, no overlapping
versions, one current row per line, unique surrogate keys, orphan lists per
dimension (`orphans_line` = I-21; shift, date and unit orphans empty) and no
inspection twice in the fact (22 rows, 2,440 / 65 pieces).

## 2. Line-day, plant-day, plant-month

The line-day grid is every line version valid on every business day of the
period, `UNION` every observed line-day, so a silent line shows as
`no_inspections` and no fact can fall outside the grid:

```sql
CASE WHEN f.inspections IS NULL THEN :empty_status
     WHEN f.inspected_pieces = 0 THEN :zero_status
     ELSE 'ok' END AS status,
try_divide(CAST(COALESCE(f.defective_pieces, 0) AS DOUBLE),
           COALESCE(f.inspected_pieces, 0)) AS rate
```

`plant_day` and `plant_month` sum the same two parts over all of a plant's
lines or days and divide once. Selected baseline rows:

| grain | key | inspected | defective | status | rate |
|---|---|---|---|---|---|
| line-day | 03-27 N1 (D. Varga) | 200 | 4 | ok | 0.02 |
| line-day | 03-27 N2 | 100 | 5 | ok | 0.05 |
| line-day | 03-30 S2 | 0 | 0 | no_inspections | NULL |
| line-day | 03-31 N2 | 0 | 0 | no_units | NULL |
| line-day | 04-01 UNKNOWN | 50 | 2 | ok | 0.04 |
| plant-day | 03-27 PN | 300 | 9 | ok | 0.03 |
| plant-day | 03-27 PS | 300 | 15 | ok | 0.05 |
| plant-month | 2026-03 PN | 1,000 | 22 | ok | 0.022 |
| plant-month | 2026-03 PS | 840 | 21 | ok | 0.025 |

The tests reconcile the parts from the collected rows: each plant-day equals
the sum of its line-days, each plant-month the sum of its plant-days, and the
months sum to 2,440 / 65 and 22 inspections.

**Wrong approach: averaging rates.** North's two line rates on 27 March are
0.02 and 0.05; their average is 0.035, but the plant inspected 300 pieces and
found 9 defective, 0.03. North's March day rates average 0.02125 against the
month's 22 / 1,000 = 0.022. An average of rates weights a 100-piece line like a
200-piece line; it is a different metric, and `AVG` also silently skips a NULL
rate, so the number of lines it covers changes with the data.

## 3. The five deliberate failures

| Statement | Output | Contract clause violated |
|---|---|---|
| `naive_division_line_day` | `DIVIDE_BY_ZERO` (N2, 31 March, 0/0) | An empty or zero denominator gives no rate |
| `naive_units_plant_day` | PS 27 March 190 / 4 = 0.021 against 300 / 15 = 0.05 | Both quantities in pieces before any sum |
| `inner_join_totals` | 21 rows, 2,390 / 63 against 22 rows, 2,440 / 65 | A missing dimension key is kept under the unknown member |
| `history_join_*` | 29 rows; PN 2,250 / 48; D. Varga and P. Nair each 1,000 / 21 | History is joined on its validity window |
| `window_calendar_dates` | 28, 29, 30 March: one business day; PN 300 / 6 | The window counts business days of the plant calendar |

Two details are worth noticing. On 26 March and 1 April the unit mismatch
changes South's sums (130 against 240; 80 against 300) while the rate happens
to agree, because the lines involved had equal rates; a test that compared only
rates would miss it. And the history double count barely moves North's rate
(48 / 2,250 = 0.0213 against 27 / 1,250 = 0.0216) because every N1 inspection
is doubled evenly: a plausible rate is not evidence that the totals are right.

The as-was reading (type 2, `supervisor_as_was`) gives D. Varga 350 / 7 and P.
Nair 650 / 14; the as-is reading (type 1, `supervisor_as_is`) gives P. Nair all
of N1, 1,000 / 21. Both keep every inspection exactly once; they answer
different questions, and the contract names which one a report uses.

## 4. The transfer set

The same SQL passes on `fixtures/transfer` with no edits, and that set exposes
what the baseline could not: the case pack is 24 pieces, so T-09 (10 cases)
is 240 / 24; T-10 (20 trays) has no conversion and is quarantined, not summed;
S2's new supervisor starts on 30 April, the day of T-09, and the half-open
interval assigns T-09 to E. Haddad and T-03 (29 April) to J. Castillo; the
shutdown on Friday 1 May makes the business-day window (29 April, 30 April, 4
May) differ from a Monday-to-Friday window (30 April, 1 May, 4 May).

## 5. The negative case and the contract refusals

Moving version 101's `valid_to` to 31 March makes it overlap version 102 on 30
March. `check_overlapping_versions` names N1, and without that check the fact
would silently hold 24 rows (I-10 and I-13 twice) and 2,640 / 70 pieces. The
contract validator refuses a contract with no denominator, with different
numerator and denominator populations, with mismatched units, with a zero rate
for empty cases, or with a calendar-day window, each with its named reason.

## 6. Platform adaptation (not executed)

On Databricks the same contract can become a Unity Catalog metric view over
the gold star. The sketch below was written from the metric view
documentation and was **not executed** here; the YAML version, keys and runtime
requirement must be checked against the current reference, and the table names
are placeholders.

```sql
CREATE VIEW cinderline.quality.unit_defect_rate_mv
WITH METRICS
LANGUAGE YAML
AS $$
version: 1.1
source: cinderline.quality.fact_inspection
joins:
  - name: line
    source: cinderline.quality.dim_line
    on: source.line_sk = line.line_sk
dimensions:
  - name: business_day
    expr: business_date
  - name: plant
    expr: line.plant_id
  - name: line_id
    expr: line.line_id
measures:
  - name: defective_pieces
    expr: SUM(defective_pieces)
  - name: inspected_pieces
    expr: SUM(inspected_pieces)
  - name: unit_defect_rate
    expr: try_divide(MEASURE(defective_pieces), MEASURE(inspected_pieces))
$$
```

The documentation describes measures as aggregate expressions with no fixed
level of aggregation, evaluated with `MEASURE()` at the grain of the fields a
query selects, so the ratio is recomputed from its parts at line-day, plant-day
or plant-month. It also says metric view joins are many-to-one and that, when
a join finds several rows, the first matching row is selected: joining this
dimension on `line_id` would not double count, it would silently attribute each
inspection to an arbitrary supervisor version. Join on the surrogate key.
