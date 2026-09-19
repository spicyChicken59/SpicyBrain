<!-- section:dbxfe-m04-l01-foundation-start -->

[DataFrames](#/lesson/dbxfe-dataframes) introduces the typed expressions below. The input for this lesson is already resolved to one accepted current inspection per row. The five-row event baseline belongs to the later incremental lessons; summing raw deliveries here would be a different, incorrect problem. The original short three-row example remains later in this topic.

<!-- section:dbxfe-m04-l01-foundation-mechanism -->

Our accepted inspections are A at North with 12 inspected/1 defective, C at North with 8/0, and S at South with 10/2. We first check required nonnegative quantities and defects <= inspected; then project business columns; then aggregate by plant; finally divide total defects by total inspected. The grain changes only at the aggregate: one accepted inspection becomes one plant. The percentage is unit-weighted because inspected units are its denominator.

The SQL and DataFrame APIs express equivalent relational transformations here. Equivalent means the same rows and types under the tested schema and engine, not textually similar code or an unconditional performance guarantee. Sorting is used only for deterministic display/comparison; without ORDER BY, relational output order is not promised.

<!-- section:dbxfe-m04-l01-foundation-example -->

~~~python
from pyspark.sql import SparkSession, functions as F, types as T
spark = SparkSession.builder.master("local[2]").appName("weighted-metric").getOrCreate()
schema = "inspection_id string, plant string, inspected_units long, defective_units long"
df = spark.createDataFrame([
    ("A", "North", 12, 1), ("C", "North", 8, 0), ("S", "South", 10, 2)
], schema)
df.createOrReplaceTempView("accepted_inspections")
sql_result = spark.sql("""
WITH checked AS (
  SELECT inspection_id, plant, inspected_units, defective_units
  FROM accepted_inspections
  WHERE inspected_units IS NOT NULL AND defective_units IS NOT NULL
    AND inspected_units >= 0 AND defective_units >= 0
    AND defective_units <= inspected_units
), totals AS (
  SELECT plant, SUM(inspected_units) AS inspected,
         SUM(defective_units) AS defective
  FROM checked GROUP BY plant
)
SELECT plant, inspected, defective,
       CASE WHEN inspected > 0
            THEN CAST(defective AS DOUBLE) / inspected
            ELSE CAST(NULL AS DOUBLE) END AS defect_rate
FROM totals
""")
checked = df.filter(F.col("inspected_units").isNotNull()
    & F.col("defective_units").isNotNull()
    & (F.col("inspected_units") >= 0)
    & (F.col("defective_units") >= 0)
    & (F.col("defective_units") <= F.col("inspected_units")))
selected = checked.select("inspection_id", "plant", "inspected_units", "defective_units")
totals = selected.groupBy("plant").agg(
    F.sum("inspected_units").alias("inspected"),
    F.sum("defective_units").alias("defective"))
py_result = totals.select("plant", "inspected", "defective",
    F.when(F.col("inspected") > 0,
           F.col("defective").cast("double") / F.col("inspected"))
     .otherwise(F.lit(None).cast("double")).alias("defect_rate"))
expected = [("North", 20, 1, 0.05), ("South", 10, 2, 0.2)]
assert [tuple(r) for r in sql_result.orderBy("plant").collect()] == expected
assert [tuple(r) for r in py_result.orderBy("plant").collect()] == expected
assert sql_result.dtypes == py_result.dtypes == [
    ("plant", "string"), ("inspected", "bigint"),
    ("defective", "bigint"), ("defect_rate", "double")]
spark.stop()
~~~

Checked and selected contain the same three rows for this valid fixture. Totals contains North 20/1 and South 10/2. Adding the derived column yields 0.05 and 0.2; displaying these as percentages gives 5% and 20%. The literal expected list was authored from arithmetic, not calculated by the implementation being tested. In a less exactly representable floating-point case use an explicitly justified numerical tolerance rather than inventing exact equality.

<!-- section:dbxfe-m04-l01-foundation-task -->

Replace A's accepted row with its correction 14 inspected/1 defective; retain C and S. Add a Zero plant with one valid 0/0 inspection. Predict the complete plant output, including rates and types. Explain why adding A v3 alongside A v2 would be wrong even if both rows pass every quantity filter. Then compare a row-level average with the unit-weighted North metric.

<!-- section:dbxfe-m04-l01-foundation-solution -->

Sorted plants are North, South, Zero. North becomes 22 inspected/1 defective and 1/22, approximately 0.04545454545. South remains 10/2 and 0.2. Zero is 0/0 with null defect_rate by the authored denominator policy. Types remain string, bigint, bigint, double. The North output represents 22 inspected units, not two equally weighted inspections.

Keeping both A revisions changes the input grain to inspection revision and counts the same inspection twice. Validation of each row's quantities cannot fix that. Resolve to one current A first. Averaging the revised North row rates gives (1/14 + 0/8)/2 = 1/28, about 3.57%, whereas the unit rate is 1/22, about 4.55%. Neither mathematical operation is inherently illegal; only the latter matches this explicitly unit-based metric. Preserve missing/rejected coverage separately if the input was not already accepted.

<!-- section:dbxfe-m04-l01-foundation-limits -->

Local Spark tests exercise the actual interfaces on bounded fixtures. They do not test a Databricks workspace, cloud data access, production distribution or full-data coverage. Column types and explicit null handling are part of the comparison. A successful aggregate can still be wrong if its input grain was wrong.

<!-- section:dbxfe-m04-l01-foundation-links -->

[Grain, joins and execution](#/lesson/dbxfe-grain-joins) shows a plausible but corrupted result. [Incremental inputs](#/lesson/dbxfe-m04-l02) resolves multiple revisions before this transformation. The earlier lesson's introductory application sections remain below for saved links.

<!-- section:dbxfe-m04-l01-foundation-sources -->

Primary documentation was read on 19 September 2026. Open Sources below for exact publishers, cloud/runtime context and limitations. Official mechanisms, original professional guidance and fictional records are distinct. These examples do not establish a Databricks execution, production performance, configured permissions or complete source coverage. The optional downloadable bundle provides setup, input files, independent expected outputs, starter tasks and complete solutions. The local acceptance run passed 30 tests with no failures or skips using Python 3.12.14, Apache Spark 4.0.4 and Java 17.0.20.1+1, including the complete displayed Python/SQL examples and changed input cases. The bundle includes exact fixture/output hashes and execution evidence. These results do not include Delta or Databricks execution; the reader itself does not execute code.

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
