# Lab L03 tasks

Predict on paper first. `DATA.md` states the grain of each relation and
the current-row rule; `expected/*.json` is for checking after your attempt.

## 1. Grain and the duplicate-key check

Load both fixtures with the declared schemas. Write one sentence for the
grain of `inspections` and one for `plants` as delivered. Count rows on
both sides, then implement `duplicate_keys` (DataFrame) and
`DUPLICATE_KEYS_SQL`: plant ids that occur more than once, with their row
counts.

*Expected behaviour:* 20 inspections, 8 plant rows, duplicate keys P1 ×2
and P2 ×3; facts total 256 inspected, 24 defective.

## 2. Produce the plausible wrong total (deliberate failure)

Inner-join inspections to plants on `plant_id` and total it. Before
running, predict the row count from the multiplicities in Task 1 and the
one plant that has no dimension row. Group the naive join by region and
look for a region no current plant belongs to.

*Expected behaviour:* 33 rows, 410 inspected, 39 defective, rate
0.0951219512195122 — 20 + 15 extra − 2 unmatched. Region SE appears with
100 inspected although P2 is currently in S.

## 3. Two non-repairs

(a) Aggregate inspections to plant grain *first*, then join the raw
dimension. (b) Apply `.distinct()` to the naive join. Predict each row
count and total, then explain why neither changes 410.

*Expected behaviour:* (a) 7 rows, still 410 / 39; (b) 33 rows — the
duplicated versions differ in manager, date or source, so nothing is
removed.

## 4. Repair with an explicit rule

Implement `current_plants_by_window` (ROW_NUMBER over plant_id ordered by
valid_from desc, row_source desc; keep rank 1) and
`current_plants_by_aggregate` (`max_by` per attribute, guarded by
`has_ties`). Write `CURRENT_PLANTS_SQL`. Show both produce the same five
rows, that SQL agrees, and that reversing the input order changes nothing.
Then re-join: inner and left. Report unmatched inspections with a
`left_anti` join.

*Expected behaviour:* current rows P1 (L. Osei, NE), P2 (M. Vidal, S), P3,
P4, P5; inner join 18 rows 240 / 23; left join 20 rows 256 / 24 with 18
named rows; unmatched I-16, I-17.

## 5. The region report, both ways

Left-join inspections to the current dimension, group by region, add the
guarded unit-weighted `defect_rate`. Compare DataFrame and SQL rows sorted
with nulls first, then dtypes and the schema object.

*Expected behaviour:* null 2 / 16 / 1 (0.0625); NE 10 / 119 / 10; S 5 /
50 / 5; W 3 / 71 / 8. Types string, bigint, bigint, bigint, double.

## 6. The left-join null-count trap

Start from the current dimension and LEFT JOIN inspections. Per plant,
compute `COUNT(*)`, `COUNT(inspection_id)`, `SUM(inspected_units)` and a
`COALESCE`d `inspected`. Which plant shows the difference, and what does
its SUM return?

*Expected behaviour:* P5 has row_count 1, inspection_count 0,
inspected_sum NULL, inspected 0. Totals: COUNT(*) 19, COUNT(inspection_id)
18 — and neither is 20, because P9's inspections are unreachable from the
dimension side.

## 7. Weighted rate versus average of rates

Per plant over the facts alone: `weighted_rate` = Σ defective / Σ
inspected; `average_of_rates` = AVG of per-row `try_divide` rates;
`rate_rows` = COUNT of those rates; `row_count` = COUNT(*). Predict which
plants disagree and why P2's average covers four rows.

*Expected behaviour:* P1 0.0857 vs 0.0752; P2 0.1 vs 0.1067 with
rate_rows 4 of 5 (I-06 is 0/0 → NULL → ignored by AVG); P3 0.0816 vs
0.0690; P4 0.1127 vs 0.1; P9 0.0625 vs 0.05.

## 8. Transfer: a different duplicate pattern

Swap in `fixtures/plants_transfer.json` (P3 ×3 with a rename and a region
change, P4 ×3, P9 now present, P6 with no inspections). Redo Tasks 1–6 on
paper before running. Note which symptom from Task 2 is now absent.

*Expected behaviour:* naive 36 rows, 496 / 48; no phantom region; current
rows 6; inner and left both 20 rows 256 / 24; nothing unmatched; P6 is the
empty plant; region W becomes P4 + P9 = 5 / 87 / 9.
