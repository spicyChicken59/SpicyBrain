# Data dictionary and derivations

All records are original fiction about the Cinderline manufacturer. No real
plant, person, employer schema or customer data appears. Nothing is generated
at run time; the fixtures are literal JSON files hashed into the evidence.

## fixtures/inspection_events.json (26 rows: raw deliveries)

Grain of a raw row: **one delivery of one inspection event**. The same event
can be delivered more than once; a re-delivery carries an identical payload.

| column | declared type | meaning |
|---|---|---|
| event_id | string | identity of the inspection event; repeats mark re-deliveries |
| plant_id | string, nullable | the plant that reported it; null means the source did not say |
| line_id | string | production line label, informational |
| inspected_units | int, nullable | units inspected; null means not reported, never zero |
| defective_units | int, nullable | units found defective |
| inspected_on | string | ISO date text, informational only in this lab |

Deliberate content:

- Three exact re-deliveries: `ev-001`, `ev-004` and `ev-007` appear twice with
  identical payloads (file rows 15, 16 and 25).
- Nulls: `ev-008` (inspected null), `ev-009` (defective null), `ev-021` (both
  null), `ev-010` and `ev-011` (plant null).
- Invalid quantities: `ev-012` (-4 inspected), `ev-022` (-1 and -1),
  `ev-013` (9 defective of 6 inspected).
- A zero-unit inspection `ev-005` (0/0), which is valid.
- `ev-014` reports plant `P9`, which the plant dimension does not know.

## fixtures/plants.json (4 rows, unique key)

| plant_id | plant_name | region |
|---|---|---|
| P1 | North Works | NE |
| P2 | South Mill | SE |
| P3 | East Yard | NE |
| P4 | West Forge | W |

`P4` has no events in the baseline. `P9` has events but no dimension row.

## fixtures/transfer_batch.json (5 rows appended for the transfer test)

`ev-024` P4 30/3 (activates West Forge); `ev-025` P1 10/10 (defects equal
inspected, valid by the rule `defective <= inspected`); `ev-026` P3 null/0
(rejected, missing_units); `ev-016` re-delivered identically (removed by
DISTINCT); `ev-027` plant null 3/1 (rejected, missing_plant).

## Contract used for every expected number

1. **Distinct deliveries**: `SELECT DISTINCT *` over all six columns.
2. **Reason precedence** (first match wins): `missing_plant` when plant_id is
   null; `missing_units` when either quantity is null; `negative_units` when
   either quantity is below zero; `defects_exceed_inspected` when defective
   exceeds inspected. No reason means accepted.
3. **Report grain**: one row per `plant_id` that appears in accepted rows,
   LEFT JOINed to the plant dimension so an unknown plant keeps its row with
   null name and region. `inspections` = COUNT(*), `inspected` and
   `defective` = SUM, `defect_rate` = defective / inspected as a double, NULL
   when inspected is 0 (no group in these fixtures hits that branch; the
   policy is still stated).

## expected/baseline.json, derived by hand

Counts: raw 26; minus 3 re-deliveries = **23 distinct**. Rejected (from the
23): ev-008, ev-009, ev-021 missing_units (3); ev-010, ev-011 missing_plant
(2); ev-012, ev-022 negative_units (2); ev-013 defects_exceed_inspected (1)
= **8 rejected**, **15 accepted**.

Accepted rows by plant, in file order:

| plant | accepted events (inspected/defective) | inspections | inspected | defective |
|---|---|---|---|---|
| P1 | ev-001 12/1, ev-002 8/0, ev-003 20/3, ev-015 14/2, ev-016 16/0 | 5 | 70 | 6 |
| P2 | ev-004 10/2, ev-005 0/0, ev-006 15/1, ev-017 13/1, ev-018 12/1, ev-023 25/5 | 6 | 75 | 10 |
| P3 | ev-007 9/0, ev-019 18/2, ev-020 4/0 | 3 | 31 | 2 |
| P9 | ev-014 10/1 | 1 | 10 | 1 |

5 + 6 + 3 + 1 = 15 accepted; 70 + 75 + 31 + 10 = 186 inspected;
6 + 10 + 2 + 1 = 19 defective (the `grand_total` block).

Rates are the fractions reduced, then written as the IEEE-754 double that
Python prints for the same division (`n / d`), which is what Spark's DOUBLE
division also produces because both perform one correctly rounded binary64
division: P1 6/70 = 3/35 = 0.08571428571428572; P2 10/75 = 2/15 =
0.13333333333333333; P3 2/31 = 0.06451612903225806; P9 1/10 = 0.1.

Null-handling literals: the null-plant event ids among distinct deliveries
are ev-010 and ev-011 (2 rows). Known plant ids among distinct deliveries are
P1, P2, P3, P9 = **4**; counting null as a value gives **5**.

Order case: the validity filter applied to the raw 26 rows (before DISTINCT)
keeps 26 - 8 = **18** rows (the three re-deliveries are valid). In file
order the first valid row is `ev-001`; in reversed file order it is `ev-023`
(row 26, valid).

Types: the declared schema is string/string/string/int/int/string in file
order. Spark's JSON schema inference orders fields alphabetically and types
JSON integers as bigint, so the inferred dtypes are
defective_units bigint, event_id string, inspected_on string,
inspected_units bigint, line_id string, plant_id string. Report types:
COUNT(*) and SUM over int columns are bigint; the CASE/CAST rate is double.

## expected/transfer.json, derived by hand

Raw 26 + 5 = 31; re-deliveries now 4 (ev-016 joins the three) = **27
distinct**. New rejections: ev-026 missing_units, ev-027 missing_plant =
**10 rejected**; **17 accepted**. By reason: missing_units 4, missing_plant
3, negative_units 2, defects_exceed_inspected 1.

P1 gains ev-025 10/10: 6 inspections, 70 + 10 = 80 inspected, 6 + 10 = 16
defective, 16/80 = 1/5 = 0.2. P4 appears with ev-024: 1 / 30 / 3, rate 0.1.
P2, P3 and P9 are unchanged. Grand total 17 / 226 / 32 (186 + 30 + 10 = 226;
19 + 3 + 10 = 32; a first draft of this file said 22 and the suite caught it).
Null-plant ids: ev-010, ev-011, ev-027.

## What the derivations do not cover

The expected files were written from the tables above before the solution
code ran; the tests compare both implementations against them, never against
each other alone. The literals say nothing about performance, about
Databricks, or about any dataset other than these files.
