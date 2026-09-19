<!-- section:why -->

A customer shares a notebook. You do not need to recognize every API immediately; you need to explain what each row means, how the transformation changes it, and how to check the result.

<!-- section:understand -->

The **grain** is what one row represents. Before inspecting code, name the input grain and intended output grain. A filter removes rows; a projection selects or derives columns; a group aggregates many rows into one row per key. A join can multiply rows if the joining keys are not unique at the intended grain.

SQL describes relational transformations. Python is a general programming language, and PySpark exposes Spark through Python APIs. A Spark DataFrame has named columns and is evaluated lazily: transformations build a plan; an action such as collecting results triggers execution. This is different from assuming every line immediately processes the entire dataset.

For fictional Cinderline, the source grain might be one inspection revision while the report grain is one plant/day. You must resolve revisions before summing units. Fluent syntax cannot rescue the wrong grain. Work through a tiny example manually and compare exact expected rows before considering performance.

<!-- section:see -->

**Synthetic input, already resolved to one accepted inspection per row:**

| plant | inspected_units | defective_units |
|---|---|---|
| North | 12 | 1 |
| North | 8 | 0 |
| South | 10 | 2 |

Illustrative SQL, not executed on Databricks:

```sql
SELECT plant,
       SUM(inspected_units) AS inspected,
       SUM(defective_units) AS defective
FROM accepted_inspections
GROUP BY plant;
```

Expected unordered output: North has inspected 20 and defective 1; South has inspected 10 and defective 2. The code changes the grain from inspection to plant. A local deterministic exercise checks this arithmetic separately from any cloud execution.

<!-- section:deeper -->

Illustrative PySpark equivalent: `df.groupBy("plant").sum("inspected_units", "defective_units")`. Inspect output names and types before a downstream join. Avoid collecting an unbounded production dataset to the driver merely to inspect it; use a bounded sample and understand that a sample does not prove full-data correctness. Databricks Runtime includes a particular Spark version, so validate exact APIs against that runtime before using a snippet in a real workspace.

<!-- section:customer -->

For an analyst: “We first make sure each accepted inspection appears once, then add inspected and defective units by plant. We will compare exact counts and totals on a small known sample before validating the full reporting population.”

<!-- section:try -->

Using the synthetic input, calculate North's defect rate as defective units divided by inspected units. Then explain why averaging two inspection-level percentages would give a different answer here.

<!-- section:revisit -->

North's rate is 1 ÷ 20 = 5%. Averaging the row percentages, (1 ÷ 12 + 0 ÷ 8) ÷ 2, gives about 4.17%. That treats each inspection as equally weighted even though the inspected-unit counts differ. The business definition decides whether units or inspections form the denominator; for this exercise it is units.

The transferable habit is to inspect grain and weighting before trusting a plausible percentage. In a notebook review, write the expected rows and the metric definition beside the transformation.
