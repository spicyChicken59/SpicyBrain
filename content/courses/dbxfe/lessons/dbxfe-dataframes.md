<!-- section:dbxfe-dataframes-start -->

Use the [Python bridge](#/lesson/dbxfe-python-bridge) if lists, imports or None are unfamiliar. SQL filtering/projection ideas help, but ordinary Python values and Spark column expressions behave differently. The local exercise targets Apache Spark 4.0.4; a Databricks Runtime bundles its own versions, so this is not a workspace compatibility claim.

<!-- section:dbxfe-dataframes-expressions -->

A DataFrame is a named, typed collection of rows on which you build a query plan. Its schema gives field names, types and nullability. It does not establish business uniqueness or validate every relationship between fields. One row below represents one received inspection revision; it is not yet one accepted current inspection.

StructType groups fields. StructField supplies a name, data type and nullable flag. StringType and LongType describe string and 64-bit integer columns; True below permits null so a missing value stays inspectable. Explicit input types make assumptions visible instead of letting a tiny sample choose types for you. A field accepting null is a structural choice, not approval to include null units in a metric.

F.col("inspected_units") returns a column expression, not one scalar unit count. Spark composes that expression across rows. Use the bitwise operators & and | with parentheses to combine column predicates; ordinary Python and/or try to evaluate local truth values. isNull/isNotNull build explicit null tests. select projects/derives columns, alias names a derived column, and cast requests conversion. Casts can fail under the chosen ANSI behavior; they are not a substitute for validation. The example below casts a known integer to double, avoiding ambiguous string conversion.

<!-- section:dbxfe-dataframes-worked -->

~~~python
from pyspark.sql import SparkSession, functions as F, types as T
spark = SparkSession.builder.master("local[2]").appName("typed-records").getOrCreate()
schema = T.StructType([
    T.StructField("inspection_id", T.StringType(), True),
    T.StructField("version", T.LongType(), True),
    T.StructField("inspected_units", T.LongType(), True),
    T.StructField("defective_units", T.LongType(), True),
])
rows = [("A", 2, 12, 1), ("C", 1, 8, 0), ("D", 1, None, 0)]
raw = spark.createDataFrame(rows, schema)
raw.printSchema()
valid = raw.filter(
    F.col("inspected_units").isNotNull()
    & F.col("defective_units").isNotNull()
    & (F.col("inspected_units") >= 0)
    & (F.col("defective_units") >= 0)
    & (F.col("defective_units") <= F.col("inspected_units")))
projected = valid.select("inspection_id",
    F.col("inspected_units").alias("inspected"),
    (F.col("inspected_units") - F.col("defective_units")).alias("nondefective"),
    F.col("inspected_units").cast("double").alias("units_as_double"))
projected.orderBy("inspection_id").show()
spark.stop()
~~~

The input schema is inspection_id:string, version:bigint, inspected_units:bigint, defective_units:bigint, all nullable. The raw rows number three. Valid contains A and C; D remains in raw as missing-quantity evidence. The projection has string, bigint, bigint, double types in that order.

| inspection_id | inspected | nondefective | units_as_double |
|---|---|---|---|
| A | 12 | 11 | 12.0 |
| C | 8 | 8 | 8.0 |

The comparison "inspected_units >= 0" yields unknown for a null value under SQL null semantics; a filter keeps only true rows. Explicit null tests make the intended reason legible. A production-quality preparation step must also report rejects and resolve identity/revisions; this isolated expression exercise intentionally does neither.

<!-- section:dbxfe-dataframes-task -->

Add E v1 with inspected 5 and defective 7, and F v1 with inspected 0 and defective 0. Predict which rows the existing valid filter keeps and the complete projected output. A teammate replaces the null test with "F.col('inspected_units') == None" and combines conditions using Python and. Explain both errors, then repair them. Optional local execution can use the downloadable bundle; study does not require installation.

<!-- section:dbxfe-dataframes-solution -->

A, C and F survive; E violates defects <= inspected and D has missing inspected units. Sorted output is A:12/11/12.0, C:8/8/8.0, F:0/0/0.0, with the same string/bigint/bigint/double field types. Zero is permitted by this quantity rule; a later defect-rate denominator of zero needs its own policy.

Use isNotNull() when selecting present units and use & between parenthesized column comparisons. "equals null" is not an is-null predicate under SQL null semantics. Python and tries to collapse expressions to a local Boolean instead of building a Spark predicate. Retain a separate rejected relation with reasons when turning this teaching projection into an accepted-state step.

<!-- section:dbxfe-dataframes-limits -->

An explicit schema does not guarantee that each inspection_id is unique. Projecting away event identity before reconciliation can remove evidence you need later. collect returns data to the driver; use only bounded synthetic inputs here. A filter that silently removes invalid rows might make a metric look correct while hiding incomplete coverage.

<!-- section:dbxfe-dataframes-links -->

[SQL and PySpark transformation](#/lesson/dbxfe-m04-l01) develops this into a multi-step weighted metric. [Identity and ordering](#/lesson/dbxfe-m04-l02) explains why structural validation alone is insufficient. Spark mechanisms come from the pinned Apache Spark docs; records and policy are original fiction.

<!-- section:dbxfe-dataframes-foundation-sources -->

Primary documentation was read on 19 September 2026. Open Sources below for exact publishers, cloud/runtime context and limitations. Official mechanisms, original professional guidance and fictional records are distinct. These examples do not establish a Databricks execution, production performance, configured permissions or complete source coverage. The optional downloadable bundle provides setup, input files, independent expected outputs, starter tasks and complete solutions. The local acceptance run passed 30 tests with no failures or skips using Python 3.12.14, Apache Spark 4.0.4 and Java 17.0.20.1+1, including the complete displayed Python/SQL examples and changed input cases. The bundle includes exact fixture/output hashes and execution evidence. These results do not include Delta or Databricks execution; the reader itself does not execute code.

<!-- section:dbxfe-dataframes-revisit -->

Try the explained checks, then review the linked cards. A reveal, visit or optional bridge skip does not record a pass or mastery. Mark completion only when you choose; assessment and review evidence remain separate.
