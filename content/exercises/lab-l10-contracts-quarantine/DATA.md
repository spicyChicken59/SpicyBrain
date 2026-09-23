# Data dictionary and derivations

All plants, inspections and events are original fiction; the files are
hand-written and there is no generator or seed. Every number in `expected/`
was derived by hand from `fixtures/contract.json` and the CSV rows below
**before** the validator was run; the validator was then run once in scratch
and agreed on every field. Nothing in `expected/` was produced by the
validator.

## Contract (`fixtures/contract.json`, `inspection-feed-v1`)

| field | type | required | rule |
|---|---|---|---|
| `event_id` | string | yes | unique per delivery; repeat + same payload = `duplicate_delivery`; repeat + different payload = `event_id_conflict` |
| `plant_id` | string | yes | must exist exactly (case-sensitive) in the plants dimension, else `unknown_plant` |
| `inspection_id` | string | yes | business key; blank after trimming = `missing_inspection_id` |
| `version` | integer | yes | minimum 1; `2.0` is `invalid_version`, `0` is `below_minimum_version` |
| `revised_at` | date | yes | `YYYY-MM-DD`; `2026/09/06` is `invalid_revised_at` |
| `inspected_units` | integer | yes | minimum 0; `twelve`, `12.0` invalid; empty = `missing_inspected_units` |
| `defective_units` | integer | yes | minimum 0 |
| `note` | string | no | empty becomes `null` |

Cross-field: `defective_units <= inspected_units` when both parsed, else
`defective_exceeds_inspected`. Reasons are appended in contract field order
(missing → invalid → below minimum → unknown reference), then the cross-field
rule; batch reasons come after. `defect_rate` = `defective / inspected` for an
accepted row, `null` when `inspected == 0`. Batch rules run over rows that
passed every row check, in this order: duplicate deliveries, event-ID
conflicts, key/version uniqueness, time inversion, manifest, columns.
`publication_allowed` = no contradictions and no batch failures.

## Primary delivery (`inspections.csv`, plants `CL-N`, `CL-S`; manifest claims 21)

| row | event | plant | key | ver | revised_at | insp | def | outcome |
|---|---|---|---|---|---|---|---|---|
| 1 | e01 | CL-N | A | 1 | 2026-09-01 | 10 | 1 | accepted, rate 1/10 = 0.1 |
| 2 | e02 | CL-N | A | 2 | 2026-09-03 | 12 | 1 | `event_id_conflict` with row 20 |
| 3 | e03 | CL-N | B | 1 | 2026-09-01 | −3 | 1 | `below_minimum_inspected_units`, `defective_exceeds_inspected` (1 > −3) |
| 4 | e04 | CL-S | C | 1 | 2026-09-02 | 8 | 0 | accepted, rate 0/8 = 0.0 |
| 5 | e05 | CL-S | D | 1 | 2026-09-02 | twelve | 0 | `invalid_inspected_units` |
| 6 | e06 | CL-S | E | 1 | 2026-09-02 | 5 | 7 | `defective_exceeds_inspected` |
| 7 | e07 | CL-N | F | 1 | 2026-09-04 | 0 | 0 | accepted, rate `null` (zero denominator) |
| 8 | e08 | CL-N | (blank) | 1 | 2026-09-04 | 9 | 0 | `missing_inspection_id` |
| 9 | e09 | CL-W | G | 1 | 2026-09-04 | 6 | 1 | `unknown_plant` |
| 10 | e10 | CL-S | H | 1 | 2026-09-05 | 20 | 2 | `key_version_conflict` with row 11 |
| 11 | e11 | CL-S | H | 1 | 2026-09-05 | 21 | 2 | `key_version_conflict` with row 10 |
| 12 | e04 | CL-S | C | 1 | 2026-09-02 | 8 | 0 | identical to row 4: `duplicate_delivery` |
| 13 | e13 | CL-N | J | 1 | 2026-09-06 | 15 | 1 | `version_time_inversion` (v2 is dated earlier) |
| 14 | e14 | CL-N | J | 2 | 2026-09-05 | 16 | 1 | `version_time_inversion` |
| 15 | e15 | CL-S | K | 1 | 2026-09-06 | (empty) | 0 | `missing_inspected_units` |
| 16 | e16 | CL-S | L | 0 | 2026-09-06 | 4 | −1 | `below_minimum_version`, `below_minimum_defective_units` |
| 17 | e17 | CL-S | M | 1 | 2026/09/06 | 4 | 0 | `invalid_revised_at` |
| 18 | e18 | CL-S | N | 1 | 2026-09-06 | 30 | 3 | accepted, note `resampled`, rate 3/30 = 0.1 |
| 19 | e19 | CL-S | N | 2 | 2026-09-07 | 31 | 3 | accepted, rate 3/31 = 0.0967741935483871 |
| 20 | e02 | CL-N | Z | 1 | 2026-09-03 | 12 | 1 | `event_id_conflict` with row 2 (same event, different story) |

Derived: raw 20; accepted rows 1, 4, 7, 18, 19 → **5**; quarantined **15**;
5 + 15 = 20. Reason counts: two rows carry two reasons (3 and 16), so 17
reasons over 15 rows: `below_minimum_defective_units` 1,
`below_minimum_inspected_units` 1, `below_minimum_version` 1,
`defective_exceeds_inspected` 2 (rows 3, 6), `duplicate_delivery` 1,
`event_id_conflict` 2, `invalid_inspected_units` 1, `invalid_revised_at` 1,
`key_version_conflict` 2, `missing_inspected_units` 1, `missing_inspection_id`
1, `unknown_plant` 1, `version_time_inversion` 2 — sum 17. Contradictions in
rule order: `event_id_conflict` e02 [2, 20]; `key_version_conflict` [H, 1]
[10, 11]; `version_time_inversion` J [13, 14]. Batch failure:
`manifest_row_count_mismatch` 21 vs 20. Publication false. Rates are Python's
own floats typed into an interpreter (`3/31`), not read from the validator.

Row-level only: rows failing a row check are 3, 5, 6, 8, 9, 15, 16, 17
(eight); the other twelve — 1, 2, 4, 7, 10, 11, 12, 13, 14, 18, 19, 20 —
pass on their own. Seven of those twelve (2, 10, 11, 12, 13, 14, 20) are
quarantined only by batch rules. No row carries any information about the
manifest, so `sees_manifest` is false by construction.

Permissive validator: it accepts all 20 (quarantine 0, publication true).
Wrongly accepted = the 15 rows the contract quarantines. Row 6 comes through
with `inspected_units "5"`, `defective_units "7"` as text.

## Transfer delivery (`transfer-inspections.csv`, plants `TM-A`, `TM-B`; manifest 12)

| row | event | plant | key | ver | revised_at | insp | def | outcome |
|---|---|---|---|---|---|---|---|---|
| 1 | t01 | TM-A | P | 1 | 2026-08-01 | 50 | 2 | accepted, 2/50 = 0.04 |
| 2 | t02 | TM-A | P | 2 | 2026-08-04 | 52 | 2 | accepted, 2/52 = 0.038461538461538464 |
| 3 | t03 | TM-B | Q | 1 | 2026-08-02 | 40 | 0 | accepted, 0.0 |
| 4 | t03 | TM-B | Q | 1 | 2026-08-02 | 40 | 0 | `duplicate_delivery` |
| 5 | t04 | TM-B | (spaces) | 1 | 2026-08-02 | 12 | 1 | `missing_inspection_id` |
| 6 | t05 | TM-B | R | 1 | 2026-08-03 | 12.0 | 1 | `invalid_inspected_units` |
| 7 | t06 | tm-a | S | 1 | 2026-08-03 | 9 | 0 | `unknown_plant` (case) |
| 8 | t07 | TM-A | T | 2.0 | 2026-08-03 | 9 | 0 | `invalid_version` |
| 9 | t08 | TM-A | U | 1 | 2026-08-03 | 9 | −1 | `below_minimum_defective_units` |
| 10 | t09 | TM-A | V | 1 | 2026-08-04 | 0 | 1 | `defective_exceeds_inspected` |
| 11 | t10 | TM-B | W | 1 | 2026-08-04 | 0 | 0 | accepted, rate `null` |
| 12 | t11 | TM-B | W | 2 | 2026-08-04 | 3 | 0 | accepted, 0.0 (equal dates are not an inversion) |

Derived: raw 12; accepted 1, 2, 3, 11, 12 → 5; quarantined 7; seven reasons,
one each; no contradiction; manifest 12 = 12; publication **true**. Altered
in memory by the tests: manifest 13 → `manifest_row_count_mismatch` 13 vs 12,
publication false, rows unchanged; `plant_id` column dropped → batch failure
`missing_column`, every row `missing_plant_id`, nothing accepted; appended
row 13 `t12` = Q v1 40/0 under a new event → `redundant_key_version`,
disclosed, still publishable (manifest raised to 13 for that case so only the
redundancy is under test).
