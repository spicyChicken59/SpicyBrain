# Lab L02 solutions, explained

Every number below was derived by hand in `DATA.md` before the solution ran;
`run_tests.py` holds both implementations to those literals.

## 1. Schema and deliveries

`solutions/schema.py` declares six fields; the three text fields and the
three that matter for arithmetic are all nullable so evidence of a missing
value is retained. A raw row is one delivery of one event. `SELECT DISTINCT *`
and `.distinct()` remove only identical re-deliveries (`ev-001`, `ev-004`,
`ev-007`): 26 → 23. Two deliveries of one event with *different* payloads
would be a conflict, which is a different lesson (Lab L06); these fixtures
contain none.

Intermediate: raw 26, distinct 23; dtypes `[event_id string, plant_id
string, line_id string, inspected_units int, defective_units int,
inspected_on string]` in both interfaces.

## 2. Classification

`REASON_SQL` is one `CASE` with four `WHEN`s in precedence order and no
`ELSE`, so the accepted rows carry NULL. `reason_column()` is the same
`when().when()` chain without `otherwise()`. Both yield a nullable string
column; `same_schema` holds.

Rejected (sorted): ev-008 missing_units, ev-009 missing_units, ev-010
missing_plant, ev-011 missing_plant, ev-012 negative_units, ev-013
defects_exceed_inspected, ev-021 missing_units, ev-022 negative_units.
Accepted: the other 15 distinct deliveries. `ev-005` (0/0) is accepted:
zero is a known quantity, not a missing one.

## 3. Plant report

Aggregate accepted rows by `plant_id` first (`COUNT(*)`, two `SUM`s), then
LEFT JOIN the dimension so `P9` keeps its row with null name and region.
The rate divides totals — `CAST(defective AS DOUBLE) / inspected` —
never the average of row rates; the `CASE`/`when` guard returns NULL for a
zero denominator (no group hits it here, and Spark 4 runs in ANSI mode
where an unguarded `0/0` would raise).

| plant_id | plant_name | region | inspections | inspected | defective | defect_rate |
|---|---|---|---|---|---|---|
| P1 | North Works | NE | 5 | 70 | 6 | 0.08571428571428572 |
| P2 | South Mill | SE | 6 | 75 | 10 | 0.13333333333333333 |
| P3 | East Yard | NE | 3 | 31 | 2 | 0.06451612903225806 |
| P9 | null | null | 1 | 10 | 1 | 0.1 |

Types: string ×3, bigint ×3, double. `P4` is absent because the report's
grain is "plants with accepted events"; a report of "every plant in the
dimension" would start from the dimension and LEFT JOIN the totals (Lab L03
does exactly that and shows the null-count trap it creates).

## 4. The order failure

`positional_rows(forward)` begins with `ev-001`; the same rows loaded in
reverse begin with `ev-023`. `assertEqual(f_rows, b_rows)` raises; the
sorted comparison passes; the multiset of rows is identical. What it
proves: a relation is a set of rows, and a narrow transformation over a
local collection preserved input order *by accident of implementation*.
The observed order of `.distinct()` output in the evidence
(`order_case.distinct_output_order_observed`) is neither file order nor
sorted; it is whatever the hash aggregate produced and is not asserted.

**Wrong approach and why it fails:** comparing `sql.collect() ==
df.collect()`. It passes when both plans happen to emit the same sequence
and fails on an unrelated day when one plan changes; it also proves
nothing about types. Sort on a key that is unique in that relation and
compare the schema separately.

## 5. Null handling

(a) `F.col("plant_id") == None` becomes the predicate `plant_id = NULL`,
which is *unknown* for every row; a filter keeps only *true*, so it keeps
nothing: 0 rows against SQL's 2 (`ev-010`, `ev-011`). `isNull()` is the
explicit test and gives 2. (b) `.select("plant_id").distinct().count()`
treats null as one more distinct value and returns 5; `COUNT(DISTINCT
plant_id)` ignores null and returns 4. Neither number is wrong in itself —
they answer different questions. The contract says an unknown plant is not
a plant, so the DataFrame version filters `isNotNull()` before `distinct()`
and both return 4. Choosing null-safe equality (`<=>`, `eqNullSafe`) would
be a third rule and needs a business meaning for a missing key.

## 6. Inferred versus declared

`spark.read.json(multiLine=True)` infers alphabetical columns and `bigint`
for integers: `[defective_units bigint, event_id string, inspected_on
string, inspected_units bigint, line_id string, plant_id string]`. After
reordering, sorted rows compare equal as Python values (12 == 12) while the
schema comparison reports `inspected_units type bigint versus int` and the
same for `defective_units`. Equal values do not prove equal types; a
downstream `int` column fed `bigint` can overflow a contract or fail a
union. Declare the schema you mean.

## 7. Transfer

Raw 31 (26 + 5); `ev-016` is a fourth re-delivery so distinct is 27;
`ev-026` (missing_units) and `ev-027` (missing_plant) bring rejections to
10; accepted 17. P1 gains `ev-025` 10/10 — valid because defective may
equal inspected — giving 6 / 80 / 16 = 0.2. P4 West Forge appears as
1 / 30 / 3 = 0.1. P2, P3, P9 unchanged. Grand total 17 / 226 / 32. The
first draft of the expected file said 22 defective; the runner failed on
it and the arithmetic was redone by hand (19 + 3 + 10). That is the point
of independent expected values: they catch the author too.

## What the tests prove and do not prove

Nine cases pass on local Spark 4.0.4: counts and dtypes; rejected rows,
reasons and schema; accepted rows and schema; the report's rows, types,
schema and grand total in both interfaces; the deliberate order failure;
both null divergences and their corrections; inferred-versus-declared; and
the transfer batch. They do not prove behaviour on Databricks Runtime,
performance, or correctness on rows these fixtures lack (for example a
plant whose accepted total is 0, which would exercise the NULL-rate branch
only in the transfer to a new fixture you author yourself).
