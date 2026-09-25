# Lab L03 solutions, explained

Every number below was derived by hand in `DATA.md` before the code ran.
`run_tests.py` holds the DataFrame API and Spark SQL to those literals; a
wrong literal, a removed dedup and a `COUNT(*)` in place of
`COUNT(inspection_id)` were each tried on a scratch copy and failed in
exactly the tests that name them.

## 1. Grain and the duplicate-key check

`inspections`: one accepted, current inspection per row, key
`inspection_id`. `plants` as delivered: one *loaded version* of a plant
record per row, so `plant_id` is not a key. `groupBy("plant_id").count()
filter > 1` / `GROUP BY ... HAVING COUNT(*) > 1` reports P1 ×2, P2 ×3.
That check costs one aggregate and should precede every join to a
dimension whose uniqueness has not been proved.

## 2. The plausible wrong total

Each P1 inspection meets two versions, each P2 inspection three, P9 meets
none: 5×2 + 5×3 + 5 + 3 = **33 rows**, 410 inspected, 39 defective,
0.0951219512195122. Both APIs return the same wrong number — equivalence
between interfaces proves nothing about the relation you asked for. By
region: NE 15 / 189 / 16, SE 10 / 100 / 10, S 5 / 50 / 5, W 3 / 71 / 8.
SE is a region no current plant has; the test derives that "phantom"
list from the current dimension and asserts `["SE"]`.

## 3. Non-repairs

Aggregating inspections to plant grain first gives five totals; joined to
the eight-row dimension they become 7 rows that still sum to 410. The
duplicate is on the dimension side, so collapsing the fact side cannot
touch it. `.distinct()` on the naive join keeps all 33 rows because each
joined row carries a different manager, date or source. Distinct removes
identical rows; the problem is a repeated key, not a repeated row.

**Wrong approach and why it fails:** `plants.dropDuplicates(["plant_id"])`.
It does fix the row count (5 rows), which is why it is tempting. On this
run it kept P1's 2024 row (R. Ahmed) and P2's 2023 SE row — the oldest
versions — and on the transfer fixture P3's legacy NE row and P4's 2024
row. Spark promises nothing about which duplicate survives, so the
evidence records this observation and no test asserts it. A repair must
say *which* row is current.

## 4. Repair with an explicit rule

`ROW_NUMBER() OVER (PARTITION BY plant_id ORDER BY valid_from DESC,
row_source DESC) = 1` picks the latest version with a stated tie-break.
The aggregate form — `max_by(attribute, valid_from)` for each attribute
and `MAX(valid_from)` — gives the same five rows here, but `max_by` has no
tie-break, so `has_ties()` is checked first (false for both fixtures).
The window and aggregate forms, in DataFrame and SQL, all produce:

| plant_id | plant_name | region | manager | valid_from |
|---|---|---|---|---|
| P1 | North Works | NE | L. Osei | 2026-01-01 |
| P2 | South Mill | S | M. Vidal | 2026-02-01 |
| P3 | East Yard | NE | K. Ito | 2025-01-01 |
| P4 | West Forge | W | A. Costa | 2025-01-01 |
| P5 | Harbour Plant | W | J. Novak | 2025-01-01 |

The same eight rows delivered in reverse order give the same five: the
rule, not arrival order, decides. Re-joined: inner 18 rows 240 / 23
(P9's two inspections dropped), left 20 rows 256 / 24 with 18 named rows
and I-16, I-17 unmatched via `left_anti`. `inner + unmatched = left` is
asserted as an identity. Which join is right depends on the report:
"inspections at known plants" is the inner join; "all inspections, plant
unknown where unknown" is the left join. Neither is a data-quality fix.

## 5. Region report

Inspections LEFT JOIN current plants, GROUP BY region, ordered with nulls
first (Spark's ascending default, made explicit with `asc_nulls_first`):

| region | inspections | inspected | defective | defect_rate |
|---|---|---|---|---|
| null | 2 | 16 | 1 | 0.0625 |
| NE | 10 | 119 | 10 | 0.08403361344537816 |
| S | 5 | 50 | 5 | 0.1 |
| W | 3 | 71 | 8 | 0.11267605633802817 |

Rows sum to 20. Types string, bigint ×3, double; the SQL `CASE` and the
DataFrame `when` give the same nullable double and the schemas are equal.

## 6. The left-join null-count trap

Current plants LEFT JOIN inspections yields one all-null inspection row
for P5. `COUNT(*)` counts it (1); `COUNT(inspection_id)` does not (0);
`SUM(inspected_units)` over no values is NULL, which `COALESCE(..., 0)`
turns into an explicit policy. Column totals: COUNT(*) 19 versus
COUNT(inspection_id) 18. Both differ from the 20 facts because P9 is not
in the dimension: a dimension-driven report cannot see facts the
dimension lacks. Say which side drives the report and count the other
side's key, never `*`.

## 7. Weighted versus average of rates

| plant | weighted | average of rates | rate rows / rows |
|---|---|---|---|
| P1 | 0.08571428571428572 | 0.07523809523809524 | 5 / 5 |
| P2 | 0.1 | 0.10673076923076923 | 4 / 5 |
| P3 | 0.08163265306122448 | 0.06897546897546898 | 5 / 5 |
| P4 | 0.11267605633802817 | 0.1 (engine printed 0.10000000000000002) | 3 / 3 |
| P9 | 0.0625 | 0.05 | 2 / 2 |

The weighted rate divides two integer sums once and is compared exactly.
The average sums doubles in engine order — P4's 0.1 + 0.2 + 0.0 is
0.30000000000000004 in binary64 — so it is compared within 1e-12, a
tolerance justified in `DATA.md` rather than invented. P2's I-06 is 0/0:
`try_divide` returns NULL (ANSI mode would otherwise raise), AVG ignores
NULL, and the "average" quietly describes four of five inspections. The
weighted rate has no such gap. Both metrics are arithmetic; only one is
the unit-based defect rate the module defines.

## 8. Transfer

Duplicate keys P3 ×3, P4 ×3. Naive: 5 + 5 + 15 + 9 + 2 = 36 rows, 496 /
48, 0.0967741935483871; aggregate-first 9 rows still 496; distinct 36. No
phantom region — every naive region is also a current one — so the
symptom that helped in Task 2 is absent, and the test asserts that it is.
Current rows 6 (P3 renamed East Yard North in N; P4 under P. Lund; P6;
P9). Inner and left joins both 20 rows 256 / 24, nothing unmatched.
Region: N 5 / 49 / 4, NE 5 / 70 / 6, S 5 / 50 / 5, W 5 / 87 / 9. P6 is the
empty plant: COUNT(*) 21 versus COUNT(inspection_id) 20.

## What the tests prove and do not prove

Nine cases, zero skips, on local Spark 4.0.4: diagnosis; the wrong total
and its arithmetic reason; the two non-repairs; the rule-based repair in
four forms plus order-independence; fixed joins and the inner + unmatched
= left identity; the region report in both APIs with schema equality; the
null-count trap; the weighted metric; and every check again on the
transfer dimension. Not proved: Databricks Runtime behaviour, scale,
performance, the business correctness of "latest valid_from", or
behaviour on ties, which the tie-break handles but no fixture exercises.
