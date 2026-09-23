# Data dictionary and derivations

All records are original fiction about the Cinderline manufacturer. Nothing
is generated at run time; the fixtures are literal JSON hashed into the
evidence. Spark 4.0.4 runs in ANSI mode by default, so a row-level `0/0`
would raise; the average-of-rates anti-pattern therefore uses `try_divide`,
which returns NULL for a zero denominator. That NULL is part of the lesson.

## fixtures/inspections.json (20 rows: accepted current inspections)

Grain: **one accepted, current inspection**. Identity is `inspection_id`
(unique). Declared types: inspection_id string, plant_id string,
inspected_units int, defective_units int; all nullable by structure, none
null in this fixture (validation happened upstream, Lab L02).

| plant | inspections (inspected/defective) | rows | inspected | defective |
|---|---|---|---|---|
| P1 | I-01 12/1, I-02 8/0, I-03 20/3, I-12 14/2, I-18 16/0 | 5 | 70 | 6 |
| P2 | I-04 10/2, I-05 15/1, I-06 0/0, I-13 13/1, I-19 12/1 | 5 | 50 | 5 |
| P3 | I-07 9/0, I-08 18/2, I-09 4/0, I-14 7/1, I-20 11/1 | 5 | 49 | 4 |
| P4 | I-10 30/3, I-11 25/5, I-15 16/0 | 3 | 71 | 8 |
| P9 | I-16 10/1, I-17 6/0 | 2 | 16 | 1 |

Totals: 20 rows, 70 + 50 + 49 + 71 + 16 = **256** inspected,
6 + 5 + 4 + 8 + 1 = **24** defective (`fact_totals`).

## fixtures/plants.json (8 rows, duplicate keys on purpose)

Grain as delivered: **one loaded version of a plant record** — a history
that was never collapsed. Columns: plant_id, plant_name, region, manager,
valid_from (date), row_source. P1 has 2 rows (manager changed), P2 has 3
(two legacy loads, then a current row whose region moved SE → S), P3, P4
and P5 one each. P5 has no inspections; P9 has inspections but no row.
`duplicate_keys` therefore lists P1 ×2 and P2 ×3.

**The explicit rule for the current row**: the greatest `valid_from` per
plant_id, ties broken by `row_source` descending (no ties exist in either
fixture; the rule states one so it is deterministic). Current rows: P1
2026-01-01 L. Osei NE; P2 2026-02-01 M. Vidal S; P3, P4, P5 their only
row — **5 current rows**.

## fixtures/plants_transfer.json (10 rows, a different duplicate pattern)

P1 and P2 single current rows; P3 three rows (legacy NE, migration NE,
current renamed "East Yard North" in region N, 2026-03-01); P4 three rows
(current 2026-01-15 manager P. Lund); P6 Delta Plant (E) with no
inspections; P9 Ninth Site (W) now present, so nothing is unmatched.
`duplicate_keys`: P3 ×3, P4 ×3. Current rows: 6.

## Derivations for expected/baseline.json

**Naive inner join** (inspections × plants on plant_id): each P1
inspection matches 2 rows, each P2 inspection 3, P3 and P4 one, P9 none.
Rows = 5×2 + 5×3 + 5 + 3 + 0 = **33**; extra rows from duplicates =
5×(2−1) + 5×(3−1) = 15; rows lost because P9 has no row = 2; 20 + 15 − 2 =
33. Inspected = 70×2 + 50×3 + 49 + 71 = 140 + 150 + 120 = **410**;
defective = 6×2 + 5×3 + 4 + 8 = **39**; 39/410 = 0.0951219512195122
(binary64 division, as Python prints it). The number is plausible — a
9.5% rate — and wrong.

**Naive by region**: NE = P1's 10 rows (140/12) + P3's 5 (49/4) =
15 / 189 / 16; SE = P2's two SE rows × 5 = 10 / 100 / 10; S = P2's current
row × 5 = 5 / 50 / 5; W = P4 = 3 / 71 / 8. Sum 33 / 410 / 39. Region SE
appears although no *current* plant is in SE: a visible symptom, but not
one to rely on (the transfer fixture has no such symptom).

**Aggregate facts first, then join the duplicated dimension**: plant
totals are 5 rows (P1 70, P2 50, P3 49, P4 71, P9 16); joined inner to the
8-row dimension they become 2 + 3 + 1 + 1 + 0 = **7 rows** summing to the
same 410 / 39. Aggregating the fact side does not repair a duplicate on
the dimension side. **DISTINCT on the naive join** removes nothing (33
rows) because the duplicated dimension rows differ in manager, valid_from
or row_source; the duplication is in the key, not the whole row.

**Fixed joins with the 5 current rows**: inner = 20 − 2 unmatched = **18
rows**, 256 − 16 = **240** inspected, 24 − 1 = **23** defective, 23/240 =
0.09583333333333334. Left = **20 rows**, 256 / 24, 24/256 = 3/32 =
0.09375; 18 rows carry a plant_name; unmatched I-16, I-17.

**Region report** (inspections LEFT JOIN current plants, GROUP BY region,
ordered with nulls first as Spark's ascending default does): null (P9)
2 / 16 / 1, 1/16 = 0.0625; NE (P1 + P3) 10 / 119 / 10, 10/119 =
0.08403361344537816; S (P2) 5 / 50 / 5, 0.1; W (P4) 3 / 71 / 8, 8/71 =
0.11267605633802817.

**Left-join null-count trap** (current plants LEFT JOIN inspections):
P5 produces one row of nulls, so `COUNT(*)` = 1 while
`COUNT(inspection_id)` = 0 and `SUM(inspected_units)` is NULL (coalesced to
0). Totals over the five plants: COUNT(*) sums to 5+5+5+3+1 = **19**,
COUNT(inspection_id) to **18** — neither is 20, because P9's two
inspections are not reachable from the dimension side at all.

**Weighted rate versus average of rates**, per plant over the facts:

| plant | weighted = Σdef/Σinsp | row rates | average of rates | rate rows |
|---|---|---|---|---|
| P1 | 6/70 = 0.08571428571428572 | 1/12, 0, 3/20, 1/7, 0 | (1/12+3/20+1/7)/5 = 79/1050 = 0.07523809523809524 | 5 |
| P2 | 5/50 = 0.1 | 1/5, 1/15, NULL (0/0), 1/13, 1/12 | (1/5+1/15+1/13+1/12)/4 = 111/1040 = 0.10673076923076923 | 4 of 5 |
| P3 | 4/49 = 0.08163265306122448 | 0, 1/9, 0, 1/7, 1/11 | (1/9+1/7+1/11)/5 = 239/3465 = 0.06897546897546898 | 5 |
| P4 | 8/71 = 0.11267605633802817 | 1/10, 1/5, 0 | 3/10 ÷ 3 = 1/10 = 0.1 | 3 |
| P9 | 1/16 = 0.0625 | 1/10, 0 | 1/20 = 0.05 | 2 |

The exact fractions were reduced by hand, then written as the binary64
double of that fraction. The weighted rates are compared exactly (one
division of two integer sums). The averages are compared with a tolerance
of 1e-12 because Spark's AVG sums doubles in an order the engine chooses,
and floating-point addition is not associative — for P4, 0.1 + 0.2 + 0.0
is 0.30000000000000004 in binary64, so the engine may print
0.10000000000000002 for a quantity whose exact value is 0.1. P2 shows the
second trap: its 0/0 inspection is NULL under try_divide and AVG ignores
NULL, so the "average" silently covers four of five inspections.

## Derivations for expected/transfer.json

Naive join: P1 5×1, P2 5×1, P3 5×3, P4 3×3, P9 2×1 = 5 + 5 + 15 + 9 + 2 =
**36 rows**; extra = 5×2 + 3×2 = 16; lost = 0. Inspected = 70 + 50 + 147 +
213 + 16 = **496** (a first draft of this file added it to 516; the sum
was redone by hand); defective = 6 + 5 + 12 + 24 + 1 = **48**; 48/496 =
3/31 = 0.0967741935483871. By region: N = P3's current row × 5 = 5 / 49 /
4; NE = P1's 5 + P3's two old NE rows × 5 = 15 / 168 / 14; S = 5 / 50 / 5;
W = P4's three rows × 3 + P9's 2 = 11 / 229 / 25 (213 + 16, 24 + 1). Every
naive region is also a current region, so the "phantom region" symptom is
absent; only the duplicate-key check catches this pattern.

Aggregate-then-join: 1 + 1 + 3 + 3 + 1 = **9 rows**, still 496 / 48.
DISTINCT on the naive join: 36 (all dimension versions differ).

Current rows (6): P1, P2, P3 East Yard North/N/2026-03-01, P4 P. Lund/
2026-01-15, P6, P9. Fixed inner and left joins both 20 / 256 / 24
(nothing unmatched), 20 rows with a name. Region report: N 5 / 49 / 4
(4/49 = 0.08163265306122448); NE 5 / 70 / 6 (6/70); S 5 / 50 / 5; W = P4 +
P9 = 5 / 87 / 9, 9/87 = 3/29 = 0.10344827586206896. Plant counts: P6 is the
zero-inspection plant (row_count 1, inspection_count 0); COUNT(*) total
5+5+5+3+1+2 = **21** against COUNT(inspection_id) **20**. Rates are over the
unchanged facts and are not repeated.

## What the derivations do not cover

They describe these files under this contract. They say nothing about
performance, Databricks, or a dimension with ties on (plant_id,
valid_from), which the rule's tie-break handles deterministically but the
fixtures do not exercise.
