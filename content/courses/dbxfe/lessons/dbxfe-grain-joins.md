<!-- section:dbxfe-grain-joins-start -->

Use [SQL and PySpark transformation](#/lesson/dbxfe-m04-l01) to establish the one-current-inspection input grain and unit denominator. This lesson adds a second relation and follows what happens to rows. Every table is synthetic and tiny; local plan evidence is bounded to the chosen Spark configuration.

<!-- section:dbxfe-grain-joins-cardinality -->

A join returns matching row pairs. If A appears once in inspections and twice in a tags table, joining on inspection_id produces two A rows. The join does not know whether you intended enrichment, filtering, allocation or history. It performs the relation you specified. A unique key on one side protects some cardinalities, but a genuinely many-to-many relationship needs an explicit business policy rather than arbitrary deduplication.

Suppose A is 12/1 and C is 8/0. Tags are (A, urgent), (A, reviewed), (C, reviewed). A naive join produces A twice and C once: totals 32 inspected and 2 defective, rate 6.25%. The result looks plausible yet differs from the correct all-inspection total of 20/1 = 5%.

<!-- section:dbxfe-grain-joins-worked -->

~~~python
from pyspark.sql import SparkSession, functions as F
spark = SparkSession.builder.master("local[2]").appName("join-grain").getOrCreate()
inspections = spark.createDataFrame([("A",12,1),("C",8,0)],
    "inspection_id string, inspected long, defective long")
tags = spark.createDataFrame([("A","urgent"),("A","reviewed"),("C","reviewed")],
    "inspection_id string, tag string")
bad = inspections.join(tags, "inspection_id", "inner")
bad.orderBy("inspection_id", "tag").show()
# Requirement: retain inspections having at least one reviewed tag.
reviewed_keys = tags.filter(F.col("tag") == "reviewed").select("inspection_id").distinct()
good = inspections.join(reviewed_keys, "inspection_id", "left_semi")
assert bad.count() == 3
assert [tuple(r) for r in good.orderBy("inspection_id").collect()] == [
    ("A",12,1), ("C",8,0)]
good.explain(mode="formatted")
spark.stop()
~~~

A left-semi join keeps left rows that have a match without projecting matching right rows, fitting an existence requirement. Distinct makes the right-side key set explicit. If the real requirement were to attach a single current plant owner, you would instead need a verified one-row-per-plant current dimension, with a rule for resolving its history. Choosing any first owner is not a repair.

SQL for the same existence requirement is:
~~~sql
SELECT i.* FROM inspections i
WHERE EXISTS (SELECT 1 FROM tags t
              WHERE t.inspection_id = i.inspection_id AND t.tag = 'reviewed');
~~~
Register the two DataFrames as temporary views before running that SQL. Compare rows deliberately in a chosen order.

<!-- section:dbxfe-grain-joins-plans -->

Building bad or good describes work; an action such as count, show or collect requests execution. explain displays the plan and is useful for inspecting the intended operators. Spark distributes rows into partitions, subsets of data processed by tasks. A shuffle redistributes data so rows needed together for an operation can meet; exchanges in a physical plan often show this movement. A broadcast strategy may instead copy a small relation to workers. Optimizer settings, statistics and adaptive execution can change the actual strategy.

For a local exercise, inspect whether your plan shows LeftSemi, a filter on reviewed and exchange or broadcast operators. Save the actual plan rather than asserting one physical operator must appear in every environment. The logical mistake of double-counting exists regardless of which efficient physical strategy Spark chooses. A two-row local run cannot establish production skew, memory use, network cost or latency.

<!-- section:dbxfe-grain-joins-task -->

Add a second identical reviewed tag for A and a new urgent-only tag for D; inspections still contain only A and C. Predict raw tag count, naive join row count, naive inspected/defective totals, and corrected reviewed-inspection output. Then explain why applying distinct to the final aggregate does not repair the metric. Run the local plan inspection if you choose the optional bundle.

<!-- section:dbxfe-grain-joins-solution -->

There are five tag rows. A now matches three tag rows, C matches one, and D has no inspection match: the naive inner join has four rows. It sums 12 + 12 + 12 + 8 = 44 inspected and 1 + 1 + 1 + 0 = 3 defective. The reviewed-key set is still A and C, so the left-semi output remains two rows and 20/1.

Distinct on a one-row aggregate leaves the wrong 44/3 unchanged: the duplication happened before aggregation. Deduplicating full inspection output might happen to fix this sample, but can incorrectly collapse legitimate equal-valued rows if identity is omitted. Model the existence requirement directly and test grain before aggregating.

<!-- section:dbxfe-grain-joins-totals-reference -->

Write one sentence defining each relation's grain. Count each joining key on both sides. Work one key's matching pairs by hand. Decide whether the requirement is enrichment, existence or allocation. Enforce that relationship before aggregation, then compare keys/counts/totals to a literal small expectation. Finally inspect the execution plan for distribution concerns; performance work does not repair a wrong relation.

<!-- section:dbxfe-grain-joins-limits -->

An Exchange is not proof that a query is badly designed, and absence of one in a tiny optimized plan is not a scale guarantee. Row-count correctness, full-population reconciliation and performance are separate claims. The downloadable test records actual plan output; it is local Spark evidence only.

<!-- section:dbxfe-grain-joins-links -->

[Incremental identity](#/lesson/dbxfe-m04-l02) defines source revisions. [Metric foundations](#/lesson/dbxfe-m05-l01) retains the broader introductory metric exercise. Spark facts use pinned primary documentation; join arithmetic and the diagnosis recipe are original teaching.

<!-- section:dbxfe-grain-joins-foundation-sources -->

Primary documentation was read on 19 September 2026. Open Sources below for exact publishers, cloud/runtime context and limitations. Official mechanisms, original professional guidance and fictional records are distinct. These examples do not establish a Databricks execution, production performance, configured permissions or complete source coverage. The optional downloadable bundle provides setup, input files, independent expected outputs, starter tasks and complete solutions. The local acceptance run passed 30 tests with no failures or skips using Python 3.12.14, Apache Spark 4.0.4 and Java 17.0.20.1+1, including the complete displayed Python/SQL examples and changed input cases. The bundle includes exact fixture/output hashes and execution evidence. These results do not include Delta or Databricks execution; the reader itself does not execute code.

<!-- section:dbxfe-grain-joins-revisit -->

Try the explained checks, then review the linked cards. A reveal, visit or optional bridge skip does not record a pass or mastery. Mark completion only when you choose; assessment and review evidence remain separate.
