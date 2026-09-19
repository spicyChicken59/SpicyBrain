"""Run from any directory. --spark is mandatory for the complete acceptance gate."""
import argparse
from contextlib import redirect_stdout
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from solutions.reference import LocalPipeline, guarded_upsert, parse_bridge, resolve
from solutions.transfer import reconcile_orders


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


BASE = load("fixtures/baseline.json")
BATCHES = load("fixtures/batches.json")
EXPECTED = load("expected/business.json")  # Authored literals; never built by resolve().
OUTPUTS = {}


def business(result):
    return {key: result[key] for key in ("accepted", "totals", "excluded_keys", "unresolved", "publication_allowed")}


class ReferenceTests(unittest.TestCase):
    def test_displayed_python_examples_and_current_source_match(self):
        manifest = load("lesson_examples/manifest.json")
        course = ROOT.parents[1] / "courses" / "dbxfe" / "lessons"
        for entry in manifest:
            path = ROOT / "lesson_examples" / entry["file"]
            snippet = path.read_text(encoding="utf-8")
            self.assertEqual(sha256(path.read_bytes()).hexdigest(), entry["sha256"])
            if course.is_dir():
                body = (course / (entry["lesson_id"] + ".md")).read_text(encoding="utf-8")
                language = entry["language"]
                displayed = re.findall(r"~~~" + language + r"\n(.*?)\n~~~", body, re.DOTALL)[0] + "\n"
                self.assertEqual(snippet, displayed, "Displayed example changed; sync and rerun")
            if entry["lesson_id"] in ("dbxfe-python-bridge", "dbxfe-versioned-updates", "dbxfe-m04-l03"):
                previous = Path.cwd()
                try:
                    os.chdir(ROOT)
                    exec(compile(snippet, entry["file"], "exec"), {"__name__": "__main__"})
                finally:
                    os.chdir(previous)
        OUTPUTS["displayed_example_manifest"] = manifest

    def test_baseline_exact_rows_and_coverage(self):
        result = resolve(BASE)
        self.assertEqual(business(result), EXPECTED["baseline"])
        self.assertEqual(len(result["quarantine"]), 1)
        self.assertEqual(result["quarantine"][0]["row"]["inspection_id"], "B")
        self.assertEqual(result["raw_count"], 5)
        OUTPUTS["python_baseline"] = result

    def test_replay_business_invariant_raw_audit_grows(self):
        pipe = LocalPipeline()
        pipe.ingest(BASE)
        snapshot = deepcopy(pipe.published)
        pipe.ingest(BASE)
        self.assertEqual(pipe.published, snapshot)
        self.assertEqual(pipe.resolved["raw_count"], 10)
        self.assertEqual(len(pipe.outbox), 1)

    def test_late_older_revision(self):
        self.assertEqual(business(resolve(BASE + BATCHES["late"])), EXPECTED["baseline"])

    def test_correction_and_correction_replay(self):
        for copies in (1, 2):
            result = resolve(BASE + BATCHES["correction"] * copies)
            self.assertEqual(business(result), EXPECTED["correction"])
        OUTPUTS["python_correction"] = result

    def test_cross_batch_event_id_conflict(self):
        pipe = LocalPipeline()
        pipe.ingest(BASE)
        pipe.ingest(BATCHES["event_conflict"])
        self.assertEqual(business(pipe.resolved), EXPECTED["blocked"])
        self.assertIn("event_id", [item["kind"] for item in pipe.resolved["conflicts"]])
        self.assertEqual(pipe.status, "stale_previous")
        self.assertEqual(pipe.published["totals"], EXPECTED["baseline"]["totals"])
        OUTPUTS["event_conflict"] = {"resolved": pipe.resolved, "status": pipe.status, "previous": pipe.published}

    def test_cross_batch_business_revision_conflict(self):
        pipe = LocalPipeline()
        pipe.ingest(BASE)
        pipe.ingest(BATCHES["version_conflict"])
        self.assertEqual(business(pipe.resolved), EXPECTED["blocked"])
        self.assertEqual(pipe.resolved["conflicts"][0]["kind"], "key_version")

    def test_row_order_never_breaks_conflict_tie(self):
        rows = BASE + BATCHES["version_conflict"]
        self.assertEqual(business(resolve(list(reversed(rows)))), EXPECTED["blocked"])

    def test_invalid_latest_never_resurrects_old_valid(self):
        pipe = LocalPipeline()
        pipe.ingest(BASE)
        pipe.ingest(BATCHES["invalid_latest"])
        self.assertEqual(business(pipe.resolved), EXPECTED["blocked"])
        self.assertEqual(pipe.status, "stale_previous")
        OUTPUTS["invalid_latest"] = {"resolved": pipe.resolved, "status": pipe.status, "previous": pipe.published}

    def test_unknown_order_on_known_key_blocks(self):
        self.assertEqual(business(resolve(BASE + BATCHES["missing_order"])), EXPECTED["blocked"])

    def test_explicit_invalid_outcomes_no_coercion(self):
        result = resolve(BATCHES["invalid"])
        self.assertEqual([row["reasons"][0] for row in result["quarantine"]], [
            "missing_inspection_id", "invalid_version", "missing_inspected_units",
            "defective_exceeds_inspected", "invalid_version", "invalid_version"])
        self.assertEqual(result["accepted"], [])
        self.assertIsNone(result["totals"]["defect_rate"])
        OUTPUTS["invalid_inputs"] = result

    def test_failure_after_raw_retained_then_recovery(self):
        pipe = LocalPipeline()
        pipe.ingest(BASE)
        with self.assertRaisesRegex(RuntimeError, "retained_raw"):
            pipe.ingest(BATCHES["correction"], fail_after="retained_raw")
        self.assertEqual(len(pipe.raw), 6)
        self.assertEqual(pipe.status, "stale_previous")
        self.assertEqual(pipe.published["totals"], EXPECTED["baseline"]["totals"])
        pipe.recover()
        self.assertEqual(business(pipe.resolved), EXPECTED["correction"])
        self.assertEqual(len(pipe.outbox), 2)
        OUTPUTS["recovered"] = {"resolved": pipe.resolved, "status": pipe.status, "published": pipe.published,
                                "local_notification_count": len(pipe.outbox)}

    def test_failure_after_resolution_does_not_publish(self):
        pipe = LocalPipeline()
        pipe.ingest(BASE)
        with self.assertRaisesRegex(RuntimeError, "resolved_state"):
            pipe.ingest(BATCHES["correction"], fail_after="resolved_state")
        self.assertEqual(pipe.status, "stale_previous")
        self.assertEqual(pipe.published["totals"], EXPECTED["baseline"]["totals"])
        pipe.recover()
        self.assertEqual(pipe.published["totals"], EXPECTED["correction"]["totals"])

    def test_external_effect_recovery_is_local_and_idempotent(self):
        pipe = LocalPipeline()
        pipe.ingest(BASE)
        with self.assertRaisesRegex(RuntimeError, "published_snapshot"):
            pipe.ingest(BATCHES["correction"], fail_after="published_snapshot")
        self.assertEqual(len(pipe.outbox), 1)
        pipe.recover()
        pipe.recover()
        self.assertEqual(len(pipe.outbox), 2)

    def test_first_run_conflict_has_no_previous_report(self):
        pipe = LocalPipeline()
        pipe.ingest(BASE + BATCHES["version_conflict"])
        self.assertEqual(pipe.status, "blocked_no_snapshot")
        self.assertIsNone(pipe.published)
        self.assertEqual(pipe.outbox, {})

    def test_bridge_parses_missing_malformed_zero_and_negative(self):
        result = parse_bridge(ROOT / "fixtures/python_bridge.csv")
        self.assertEqual(result, {"accepted": [{"record_id": "p1", "units": 7}, {"record_id": "p5", "units": 0}],
             "rejected": [{"record_id": "p2", "reason": "missing units"},
                          {"record_id": "p3", "reason": "malformed integer"},
                          {"record_id": "p4", "reason": "negative units"}]})
        OUTPUTS["python_bridge"] = result

    def test_transfer_composite_key_cancellation_replay_and_late(self):
        rows = load("fixtures/orders.json")
        expected = load("expected/orders.json")
        self.assertEqual(reconcile_orders(rows), expected)
        self.assertEqual(reconcile_orders(rows + rows), expected)
        self.assertEqual(reconcile_orders(list(reversed(rows))), expected)
        self.assertEqual(reconcile_orders(rows + [rows[0]]), expected)
        OUTPUTS["orders"] = reconcile_orders(rows)

    def test_transfer_ambiguous_latest_blocks(self):
        rows = load("fixtures/orders.json")
        conflicting = {**rows[2], "quantity": 4}
        with self.assertRaisesRegex(ValueError, "ambiguous current line"):
            reconcile_orders(rows + [conflicting])

    def test_target_insert_update_older_replay_and_absence(self):
        target = EXPECTED["baseline"]["accepted"]
        correction = [EXPECTED["correction"]["accepted"][0]]
        updated = guarded_upsert(target, correction)
        self.assertEqual(updated, EXPECTED["correction"]["accepted"])
        self.assertEqual(guarded_upsert(updated, correction), EXPECTED["correction"]["accepted"])
        self.assertEqual(guarded_upsert(updated, target), EXPECTED["correction"]["accepted"])
        self.assertEqual(guarded_upsert([], target), EXPECTED["baseline"]["accepted"])
        OUTPUTS["target_update"] = updated

    def test_target_equal_revision_disagreement_is_not_ignored(self):
        target = EXPECTED["baseline"]["accepted"]
        before = deepcopy(target)
        with self.assertRaisesRegex(ValueError, "equal version"):
            guarded_upsert(target, [{**target[0], "inspected_units": 13}])
        self.assertEqual(target, before)

    def test_target_ambiguous_source_is_rejected_before_mutation(self):
        target = EXPECTED["baseline"]["accepted"]
        with self.assertRaisesRegex(ValueError, "ambiguous source"):
            guarded_upsert(target, [target[0], target[0]])


class SparkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from pyspark.sql import SparkSession
        from solutions.spark_transform import SCHEMA
        os.environ["PYSPARK_PYTHON"] = sys.executable
        os.environ["SPARK_LOCAL_IP"] = "127.0.0.1"
        cls.spark = (SparkSession.builder.master("local[2]").appName("SpicyBrain reliable data local exercise")
                     .config("spark.ui.enabled", "false").config("spark.driver.bindAddress", "127.0.0.1")
                     .config("spark.sql.shuffle.partitions", "2").config("spark.sql.adaptive.enabled", "false")
                     .config("spark.sql.autoBroadcastJoinThreshold", "-1").getOrCreate())
        cls.spark.sparkContext.setLogLevel("ERROR")
        cls.schema = SCHEMA
        OUTPUTS["spark_version"] = cls.spark.version

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()

    def frame(self, rows):
        # These tiny fixtures are reused by many independent actions. Cache only
        # test input, not expected results; no production performance claim.
        frame = self.spark.createDataFrame(rows, self.schema).cache()
        frame.count()
        return frame

    def rows(self, frame):
        return [row.asDict() for row in frame.orderBy("inspection_id").collect()]

    def test_baseline_and_changed_input_sql_pyspark_exact_rows_types(self):
        from solutions.spark_transform import pyspark_transform, sql_transform
        for name, rows in (("baseline", BASE), ("correction", BASE + BATCHES["correction"])):
            raw = self.frame(rows)
            py = pyspark_transform(raw)
            sql = sql_transform(raw, self.spark)
            for language, stages in (("pyspark", py), ("sql", sql)):
                stages["accepted"].cache()
                actual_rows = self.rows(stages["accepted"])
                actual_totals = stages["totals"].first().asDict()
                self.assertEqual(actual_rows, EXPECTED[name]["accepted"])
                self.assertEqual(actual_totals, EXPECTED[name]["totals"])
                self.assertEqual([list(item) for item in stages["accepted"].dtypes], EXPECTED["types"])
                self.assertEqual([list(item) for item in stages["totals"].dtypes], EXPECTED["totals_types"])
                OUTPUTS[f"{language}_{name}"] = {"rows": actual_rows, "totals": actual_totals,
                                                   "types": stages["accepted"].dtypes,
                                                   "totals_types": stages["totals"].dtypes}
            if name == "baseline":
                intermediate = {}
                for stage in ("distinct", "valid", "quarantine"):
                    intermediate[stage] = [row.asDict() for row in py[stage].orderBy("event_id").collect()]
                self.assertEqual(intermediate, load("expected/intermediate.json"))
                OUTPUTS["spark_intermediate_rows"] = intermediate
                counts = {"raw_count": raw.count(), "distinct_delivery_rows": py["distinct"].count(),
                          "quarantine_rows": py["quarantine"].count(), "valid_revision_rows": py["valid"].count(),
                          "accepted_rows": py["accepted"].count()}
                self.assertEqual(counts, EXPECTED["baseline_intermediate"])
                OUTPUTS["spark_intermediate"] = counts
            self.spark.catalog.clearCache()

    def test_spark_replay_older_arrival_and_conflicts(self):
        from solutions.spark_transform import pyspark_transform, sql_transform
        for name, extra, expected in (
            ("replay", BASE, "baseline"), ("late", BATCHES["late"], "baseline"),
            ("event_conflict", BATCHES["event_conflict"], "blocked"),
            ("version_conflict", BATCHES["version_conflict"], "blocked"),
            ("invalid_latest", BATCHES["invalid_latest"], "blocked"),
            ("missing_order", BATCHES["missing_order"], "blocked")):
            raw = self.frame(BASE + extra)
            stages = pyspark_transform(raw)
            stages["accepted"].cache()
            actual = self.rows(stages["accepted"])
            self.assertEqual(actual, EXPECTED[expected]["accepted"])
            self.assertEqual([row["inspection_id"] for row in stages["unresolved"].orderBy("inspection_id").collect()],
                             EXPECTED[expected]["unresolved"])
            sql_rows = self.rows(sql_transform(raw, self.spark)["accepted"])
            self.assertEqual(sql_rows, EXPECTED[expected]["accepted"])
            OUTPUTS["spark_" + name] = actual
            self.spark.catalog.clearCache()

    def test_join_grain_and_actual_plan(self):
        from solutions.spark_transform import join_experiment, pyspark_transform
        from pyspark.sql import functions as F
        accepted = pyspark_transform(self.frame(BASE))["accepted"].cache()
        accepted.count()
        flawed, corrected = join_experiment(self.spark, accepted)
        actual = {"flawed_count": flawed.count(),
                  "flawed_inspected_units": flawed.agg(F.sum("inspected_units")).first()[0],
                  "flawed_defective_units": flawed.agg(F.sum("defective_units")).first()[0],
                  "correct_count": corrected.count(),
                  "correct_inspected_units": corrected.agg(F.sum("inspected_units")).first()[0]}
        self.assertEqual(actual, EXPECTED["join"])
        stream = io.StringIO()
        with redirect_stdout(stream):
            corrected.explain(mode="formatted")
        plan = stream.getvalue()
        self.assertIn("Join", plan)
        self.assertIn("Exchange", plan)
        OUTPUTS["join"] = actual
        OUTPUTS["actual_local_plan"] = plan
        self.spark.catalog.clearCache()

    def test_explicit_schema_null_and_safe_cast(self):
        row = self.spark.sql("SELECT try_cast('twelve' AS INT) AS malformed, try_cast('12' AS INT) AS valid").first()
        self.assertIsNone(row.malformed)
        self.assertEqual(row.valid, 12)
        frame = self.frame([{"event_id": "null", "inspection_id": "N", "version": 1,
                            "inspected_units": None, "defective_units": 0}])
        self.assertEqual(frame.filter("inspected_units = NULL").count(), 0)
        self.assertEqual(frame.filter("inspected_units IS NULL").count(), 1)
        OUTPUTS["null_cast"] = {"malformed": row.malformed, "valid": row.valid}


class DisplayedSparkTests(unittest.TestCase):
    def setUp(self):
        from pyspark.sql import SparkSession
        os.environ["PYSPARK_PYTHON"] = sys.executable
        os.environ["SPARK_LOCAL_IP"] = "127.0.0.1"
        self.spark = (SparkSession.builder.master("local[2]").appName("SpicyBrain displayed examples")
                      .config("spark.ui.enabled", "false").config("spark.sql.shuffle.partitions", "2")
                      .config("spark.driver.bindAddress", "127.0.0.1").getOrCreate())
        self.spark.sparkContext.setLogLevel("ERROR")

    def tearDown(self):
        self.spark.stop()

    def execute_displayed(self, lesson):
        path = ROOT / "lesson_examples" / (lesson + ".py")
        stream, namespace = io.StringIO(), {"__name__": "__main__"}
        with redirect_stdout(stream):
            exec(compile(path.read_text(encoding="utf-8"), path.name, "exec"), namespace)
        OUTPUTS["displayed_" + lesson] = {"sha256": sha256(path.read_bytes()).hexdigest(),
                                           "stdout": stream.getvalue(), "completed": True}
        return stream.getvalue(), namespace

    def test_typed_displayed_dataframe(self):
        output, namespace = self.execute_displayed("dbxfe-dataframes")
        cells = [[cell.strip() for cell in line.split("|")[1:-1]] for line in output.splitlines() if line.startswith("|")]
        self.assertEqual(cells, [["inspection_id", "inspected", "nondefective", "units_as_double"],
                                  ["A", "12", "11", "12.0"], ["C", "8", "8", "8.0"]])
        self.assertEqual(namespace["projected"].dtypes, [("inspection_id", "string"), ("inspected", "bigint"),
                                                        ("nondefective", "bigint"), ("units_as_double", "double")])

    def test_weighted_displayed_sql_and_pyspark(self):
        self.execute_displayed("dbxfe-m04-l01")  # Exact displayed assertions compare independently authored rows/types.

    def test_join_displayed_python(self):
        output, _ = self.execute_displayed("dbxfe-grain-joins")
        self.assertIn("LeftSemi", output)

    def test_join_displayed_sql(self):
        inspections = self.spark.createDataFrame([("A", 12, 1), ("C", 8, 0)],
                                                 "inspection_id string, inspected long, defective long")
        tags = self.spark.createDataFrame([("A", "urgent"), ("A", "reviewed"), ("C", "reviewed")],
                                          "inspection_id string, tag string")
        inspections.createOrReplaceTempView("inspections")
        tags.createOrReplaceTempView("tags")
        query = (ROOT / "lesson_examples/dbxfe-grain-joins.sql").read_text()
        rows = [tuple(row) for row in self.spark.sql(query).orderBy("inspection_id").collect()]
        self.assertEqual(rows, [("A", 12, 1), ("C", 8, 0)])
        OUTPUTS["displayed_join_sql"] = rows

    def test_changed_typed_weighted_and_join_tasks(self):
        from pyspark.sql import functions as F
        typed = self.spark.createDataFrame([("A", 12, 1), ("C", 8, 0), ("D", None, 0), ("E", 5, 7), ("F", 0, 0)],
                                           "inspection_id string, inspected_units long, defective_units long")
        valid = typed.filter("inspected_units IS NOT NULL AND defective_units IS NOT NULL AND inspected_units >= 0 AND defective_units >= 0 AND defective_units <= inspected_units")
        projection = valid.select("inspection_id", F.col("inspected_units").alias("inspected"),
                                  (F.col("inspected_units") - F.col("defective_units")).alias("nondefective"),
                                  F.col("inspected_units").cast("double").alias("units_as_double"))
        rows = [tuple(row) for row in projection.orderBy("inspection_id").collect()]
        self.assertEqual(rows, [("A", 12, 11, 12.0), ("C", 8, 8, 8.0), ("F", 0, 0, 0.0)])
        changed = self.spark.createDataFrame([("A", "North", 14, 1), ("C", "North", 8, 0), ("S", "South", 10, 2), ("Z", "Zero", 0, 0)],
                                             "inspection_id string, plant string, inspected_units long, defective_units long")
        changed.createOrReplaceTempView("accepted_inspections")
        code = (ROOT / "lesson_examples/dbxfe-m04-l01.py").read_text()
        # Execute the exact displayed SQL against the changed independent fixture.
        query = re.search(r'sql_result = spark.sql\("""(.*?)"""\)', code, re.DOTALL).group(1)
        sql_rows = [tuple(row) for row in self.spark.sql(query).orderBy("plant").collect()]
        totals = changed.groupBy("plant").agg(F.sum("inspected_units").alias("inspected"), F.sum("defective_units").alias("defective"))
        py = totals.withColumn("defect_rate", F.when(F.col("inspected") > 0, F.col("defective").cast("double") / F.col("inspected")))
        expected = [("North", 22, 1, 0.045454545454545456), ("South", 10, 2, 0.2), ("Zero", 0, 0, None)]
        self.assertEqual(sql_rows, expected)
        self.assertEqual([tuple(row) for row in py.orderBy("plant").collect()], expected)
        inspections = self.spark.createDataFrame([("A", 12, 1), ("C", 8, 0)], "inspection_id string, inspected long, defective long")
        tags = self.spark.createDataFrame([("A", "urgent"), ("A", "reviewed"), ("C", "reviewed"), ("A", "reviewed"), ("D", "urgent")],
                                          "inspection_id string, tag string")
        bad = inspections.join(tags, "inspection_id")
        self.assertEqual(tags.count(), 5)
        self.assertEqual(bad.count(), 4)
        self.assertEqual(tuple(bad.agg(F.sum("inspected"), F.sum("defective")).first()), (44, 3))
        good = inspections.join(tags.filter("tag = 'reviewed'").select("inspection_id").distinct(), "inspection_id", "left_semi")
        self.assertEqual([tuple(row) for row in good.orderBy("inspection_id").collect()], [("A", 12, 1), ("C", 8, 0)])
        OUTPUTS["displayed_changed_tasks"] = {"typed_rows": rows, "weighted": sql_rows, "flawed_join": [4, 44, 3], "correct_join": [["A", 12, 1], ["C", 8, 0]]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--spark", action="store_true")
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()
    program_hashes = {name: sha256((ROOT / name).read_bytes()).hexdigest() for name in ("run_tests.py", "requirements.txt")}
    input_hashes = {str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path.read_bytes()).hexdigest()
                   for directory in ("fixtures", "expected", "solutions", "lesson_examples")
                   for path in sorted((ROOT / directory).rglob("*"))
                   if path.is_file() and path.suffix in (".json", ".csv", ".py", ".sql")}
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ReferenceTests)
    if args.spark:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(SparkTests))
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(DisplayedSparkTests))
    started = time.monotonic()
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    java_path = str(Path(os.environ["JAVA_HOME"]) / "bin" / ("java.exe" if os.name == "nt" else "java")) if os.environ.get("JAVA_HOME") else "java"
    java_version = subprocess.run([java_path, "-version"], capture_output=True, text=True).stderr.strip() if args.spark else "not used"
    evidence = {
        "executed_at_utc": datetime.now(timezone.utc).isoformat(), "execution_kind": "local Python and Spark SQL/PySpark" if args.spark else "local Python only",
        "databricks_executed": False, "delta_executed": False, "external_notifications_sent": False,
        "python": platform.python_version(), "java": java_version, "spark": OUTPUTS.get("spark_version", "not executed"),
        "platform": platform.system() + " " + platform.release(),
        "command": "python content/exercises/reliable-data/run_tests.py" + (" --spark" if args.spark else ""),
        "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "skipped": len(result.skipped), "successful": result.wasSuccessful(), "duration_seconds": round(time.monotonic() - started, 3),
        "program_sha256": program_hashes,
        "input_sha256": input_hashes,
        "outputs": OUTPUTS,
    }
    evidence["outputs_sha256"] = sha256(json.dumps(OUTPUTS, sort_keys=True).encode()).hexdigest()
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: evidence[key] for key in ("execution_kind", "python", "spark", "tests_run", "failures", "errors", "skipped", "successful", "outputs_sha256")}, indent=2))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
