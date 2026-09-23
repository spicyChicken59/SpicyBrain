# Lab L02 tasks

Predict before you run. Write the expected rows on paper or in a note, then
compare with `expected/*.json` only after your attempt. Opening
`SOLUTIONS.md` is not completion.

## 1. Declare the schema and count deliveries

Read `DATA.md`. Using `solutions/schema.py` (or your own `StructType`),
load `fixtures/inspection_events.json` with the declared types. State the
grain of a raw row. Predict `df.dtypes`, the raw count and the count after
`SELECT DISTINCT *` / `.distinct()`. Say why a re-delivery is removable and
why a null quantity must stay null rather than become zero.

*Expected behaviour:* dtypes are string, string, string, int, int, string
in file order; 26 raw rows; 23 distinct deliveries.

## 2. Classify every distinct delivery with a reason, both ways

Fill `REASON_SQL` in `starters/sql_pipeline.py` and `reason_column()` in
`starters/dataframe_pipeline.py` using the precedence in `DATA.md`. Produce
`rejected` (all columns plus `reason`) and `accepted` (without `reason`).
Compare the two `rejected` relations sorted by `event_id`, then compare
their `StructType`s. Predict the histogram of reasons.

*Expected behaviour:* 8 rejected rows with reasons missing_units ×3,
missing_plant ×2, negative_units ×2, defects_exceed_inspected ×1; the
`reason` column is a nullable string in both interfaces; `same_schema`
is true.

## 3. Build the plant report and compare rows AND types

Write `REPORT_SQL` and the DataFrame `report`: one row per `plant_id` in
accepted rows, LEFT JOIN to the dimension, `inspections`, `inspected`,
`defective`, and a unit-weighted `defect_rate` (NULL when inspected is 0).
Compare sorted rows against your prediction and against `expected/
baseline.json`; compare `dtypes` and the full schema between interfaces.

*Expected behaviour:* four rows P1, P2, P3, P9; P9 keeps null name and
region; counts are bigint, the rate is double; grand total 15 / 186 / 19.

## 4. Break the positional comparison (deliberate failure)

Apply the validity filter to the raw frame loaded in file order and to the
same rows loaded in reverse order. Compare the two `collect()` lists
positionally; then compare them after sorting on `event_id`. Which check
fails, and what exactly does it prove?

*Expected behaviour:* 18 valid rows in both; the positional check fails
(first rows `ev-001` versus `ev-023`); the sorted comparison passes. The
narrow filter happened to preserve input order — nothing promised it.

## 5. Two null-handling divergences, corrected

(a) SQL `WHERE plant_id IS NULL` versus DataFrame
`filter(F.col("plant_id") == None)`. Predict both counts; correct the
DataFrame; explain the SQL rule that makes `= NULL` keep nothing.
(b) SQL `COUNT(DISTINCT plant_id)` versus DataFrame
`.select("plant_id").distinct().count()`. Predict both; then apply the
contract "an unknown plant is not a plant" explicitly.

*Expected behaviour:* (a) 2 versus 0, then 2 after `isNull()`; (b) 4 versus
5, then 4 after filtering `isNotNull()` before `distinct()`.

## 6. Inferred versus declared types

Read the same file with `spark.read.json(path, multiLine=True)` and no
schema. Compare dtypes with Task 1, reorder columns, compare sorted rows,
then compare schemas. Which comparison passes and which fails?

*Expected behaviour:* inferred columns are alphabetical and integers are
bigint; sorted row values are equal; the schemas are not.

## 7. Transfer: append the batch and re-derive

Append `fixtures/transfer_batch.json`. Before running, write the new
counts, the new rejections with reasons, and the complete report including
West Forge. Then run both implementations and compare with
`expected/transfer.json`.

*Expected behaviour:* 31 raw, 27 distinct, 10 rejected, 17 accepted; P1
becomes 6 / 80 / 16 at 0.2; P4 appears as 1 / 30 / 3; grand total
17 / 226 / 32.
