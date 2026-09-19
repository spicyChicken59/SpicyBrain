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
