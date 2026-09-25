"""Lab L05 acceptance runner. Local Apache Spark 4.0.4 with delta-spark 4.0.0 (open-source Delta Lake)
in local[2] mode, web UI disabled, one machine.

    python run_tests.py --evidence <path>

setUpClass builds one small Delta table through versions 0-8 (write, append, update, change-feed
property, three merges, an evolved append, OPTIMIZE) and records what Delta itself reports at every
step, including the three requests Delta must refuse (a duplicate-match MERGE, a schema-mismatched
append, a change-feed read before the feed existed) and a VACUUM retention shorter than the table's,
which the safety check refuses in DRY RUN mode. A disposable copy of version 5 receives the wrong
(unscoped) snapshot merge, and a second tiny table is declared with liquid clustering. A transfer run
repeats the whole sequence with a different correction.

Every test compares those observations with expected/snapshots.json: a plain-Python replay of the
fixtures plus literals copied from the Delta Lake 4.0.0 documentation. The solution never produces an
expected value. Nothing deletes a data file: no retention is shortened, the retention check is never
turned off, and every VACUUM here is a DRY RUN. Spark's temporary files and the tables live in a
directory the runner creates and deletes. Any failure, error or skip makes the exit status non-zero.
"""
import sys

sys.dont_write_bytecode = True  # leave no __pycache__ inside the package

import argparse  # noqa: E402
import ast  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import platform  # noqa: E402
import re  # noqa: E402
import shutil  # noqa: E402
import tempfile  # noqa: E402
import unittest  # noqa: E402
from collections import Counter  # noqa: E402
from datetime import datetime, timezone  # noqa: E402
from hashlib import sha256  # noqa: E402
from pathlib import Path  # noqa: E402

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.environ["PYSPARK_PYTHON"] = sys.executable  # workers must use this interpreter, not the system Python
os.environ["SPARK_LOCAL_IP"] = "127.0.0.1"

from expected.derive_expected import derive_all  # noqa: E402
from solutions import delta_sequence as ds  # noqa: E402

LAB = "lab-l05-delta-snapshots"
EXECUTION_CLASS = "local-executed"
EXPECTED = json.loads((ROOT / "expected/snapshots.json").read_text(encoding="utf-8"))
BASE, TRANSFER, DOC = EXPECTED["base"], EXPECTED["transfer"], EXPECTED["documented"]
RUN = {}      # observations recorded by setUpClass, asserted by the tests
OUTPUTS = {}  # the same observations, hashed into the evidence


def condition(error):
    """Delta's error class for a captured JVM error, or None when the error carries no class."""
    getter = getattr(error, "getCondition", None)
    try:
        return getter() if getter else None
    except Exception:  # noqa: BLE001 - a missing condition is itself the observation
        return None


def refused(action):
    """Run an action that Delta must refuse; return (error class, first message line), never raise."""
    try:
        action()
    except Exception as error:  # noqa: BLE001 - the refusal is the observation
        first = str(error).splitlines()[0] if str(error) else ""
        # the table's random identifier differs on every run; keep the reason, not the identifier
        first = re.sub(r"\(Table ID: [0-9a-f-]+\)", "(Table ID: <id>)", first)
        return {"condition": condition(error), "type": type(error).__name__, "message": first}
    return {"condition": None, "type": "no error", "message": "the request was accepted"}


def metrics_of(entry, keys):
    return {k: int(entry["operationMetrics"][k]) for k in keys if k in entry["operationMetrics"]}


class Quiet:
    """Silence Spark's JVM log while a refusal it logs at ERROR level is provoked on purpose."""

    def __init__(self, spark):
        self.spark = spark

    def __enter__(self):
        self.spark.sparkContext.setLogLevel("OFF")

    def __exit__(self, *exc):
        self.spark.sparkContext.setLogLevel("ERROR")


class DeltaSequenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_root = Path(tempfile.mkdtemp(prefix="lab-l05-"))
        (cls.temp_root / "local").mkdir()
        cls.spark, resolution = ds.build_session("SpicyBrain lab L05 acceptance", local_dir=cls.temp_root / "local",
                                                 warehouse_dir=cls.temp_root / "warehouse")
        spark = cls.spark
        spark.sparkContext.setLogLevel("ERROR")
        import delta
        from importlib.metadata import version as dist_version
        RUN["environment"] = {
            "spark": spark.version, "master": spark.sparkContext.master,
            "java": spark._jvm.System.getProperty("java.version"),
            "delta_spark": dist_version("delta-spark"), "delta_module": delta.__name__,
        }
        RUN["jar_resolution"] = resolution
        path = cls.path = cls.temp_root / "inspections"

        # versions 0-2: the snapshot story (write, append, update)
        ds.write_initial(spark, path)
        ds.append(spark, path, "append_c.json")
        ds.correct_inspected(spark, path, "A", ds.CORRECTION)
        RUN["after_update"] = {"data_files_on_disk": len(ds.data_files(path)),
                               "files_in_current_version": ds.detail(spark, path)["numFiles"],
                               "directory_parquet_sum": ds.directory_parquet_sum(spark, path),
                               "delta_total": ds.totals(ds.snapshot(spark, path))["total_inspected"],
                               "detail": ds.detail(spark, path)}
        # version 3: the change data feed property
        ds.enable_change_feed(spark, path)
        RUN["after_change_feed"] = {"detail": ds.detail(spark, path)}
        # version 4: incremental merge (A absent from the source)
        ds.merge_incremental(spark, path, ds.batch(spark, "incremental_day2.json"))
        # the duplicate delivery, refused
        before = ds.current_version(spark, path)
        with Quiet(spark):
            RUN["duplicate_refusal"] = refused(
                lambda: ds.merge_incremental(spark, path, ds.batch(spark, "incremental_day3.json")))
        RUN["duplicate_refusal"].update({"version_before": before, "version_after": ds.current_version(spark, path),
                                         "rows_after": ds.snapshot(spark, path)})
        day3 = ds.batch(spark, "incremental_day3.json")
        RUN["day3_source_keys"] = dict(Counter(r["inspection_id"] for r in day3.collect()))
        # version 5: the guarded fix
        deduped = ds.dedupe_latest_revision(day3)
        RUN["deduped_day3"] = sorted((r.asDict() for r in deduped.collect()), key=lambda r: r["inspection_id"])
        ds.merge_guarded(spark, path, deduped)
        # the wrong approach, on a disposable copy of version 5 only
        copy = cls.temp_root / "unscoped_copy"
        ds.copy_version(spark, path, 5, copy)
        ds.merge_unscoped_snapshot_wrong(spark, copy, ds.batch(spark, "snapshot_south.json"))
        RUN["unscoped_copy"] = {"rows": ds.snapshot(spark, copy),
                                "metrics": metrics_of(ds.history(spark, copy)[-1],
                                                      ["numTargetRowsInserted", "numTargetRowsUpdated",
                                                       "numTargetRowsDeleted", "numSourceRows"])}
        # the same day-3 delivery on a disposable copy of version 3, where D does not exist yet
        first = cls.temp_root / "first_arrival_copy"
        ds.copy_version(spark, path, 3, first)
        with Quiet(spark):
            outcome = refused(lambda: ds.merge_incremental(spark, first, ds.batch(spark, "incremental_day3.json")))
        RUN["first_arrival_copy"] = {"outcome": outcome, "rows": sorted(ds.snapshot(spark, first),
                                                                        key=lambda r: (r["inspection_id"], r["revision"])),
                                     "metrics": metrics_of(ds.history(spark, first)[-1],
                                                           ["numTargetRowsInserted", "numTargetRowsUpdated",
                                                            "numTargetRowsDeleted", "numSourceRows"])}
        # version 6: the scoped snapshot merge
        ds.merge_full_snapshot(spark, path, ds.batch(spark, "snapshot_south.json"), "South")
        # change data feed: the recorded range and a range that starts before the feed existed
        RUN["change_feed"] = ds.change_feed(spark, path, 4, 6)
        RUN["change_files"] = len(ds.change_files(path))
        with Quiet(spark):
            RUN["change_feed_refusal"] = refused(lambda: ds.change_feed(spark, path, 2, 6))
        # schema enforcement, then explicit evolution (version 7)
        before = ds.current_version(spark, path)
        with Quiet(spark):
            RUN["schema_refusal"] = refused(lambda: ds.append(spark, path, "append_f_inspector.json"))
        RUN["schema_refusal"].update({"version_before": before, "version_after": ds.current_version(spark, path),
                                      "columns_after": ds.columns(spark, path)})
        ds.append(spark, path, "append_f_inspector.json", merge_schema=True)
        RUN["evolution"] = {"columns_v6": ds.columns(spark, path, 6), "columns_v7": ds.columns(spark, path, 7)}
        # version 8: OPTIMIZE, then a second OPTIMIZE that has nothing to do
        files_before = ds.detail(spark, path)["numFiles"]
        disk_before = len(ds.data_files(path))
        first = ds.optimize(spark, path)
        version_after_first = ds.current_version(spark, path)
        second = ds.optimize(spark, path)
        RUN["optimize"] = {"files_in_current_version_before": files_before, "first": first,
                           "files_in_current_version_after": ds.detail(spark, path)["numFiles"],
                           "data_files_on_disk_before": disk_before,
                           "data_files_on_disk_after": len(ds.data_files(path)),
                           "second": second, "version_after_first": version_after_first,
                           "version_after_second": ds.current_version(spark, path)}
        # snapshots of every version, read back by time travel
        RUN["snapshots"] = {str(v): ds.snapshot(spark, path, v) for v in range(0, 9)}
        RUN["history"] = ds.history(spark, path)
        # retention: read the safety setting back, list what VACUUM would remove, provoke the refusal
        disk_before = ds.data_files(path)
        version_before = ds.current_version(spark, path)
        listed = ds.vacuum_dry_run(spark, path)
        with Quiet(spark):
            below = refused(lambda: ds.vacuum_dry_run(spark, path, DOC["retention"]["refused_retain_hours"]))
        RUN["vacuum"] = {
            "retention_check": spark.conf.get(DOC["retention"]["retention_check_setting"]),
            "dry_run_listed": [str(p).split(path.name, 1)[-1] for p in listed],
            "below_retention": below,
            "data_files_unchanged": ds.data_files(path) == disk_before,
            "version_unchanged": ds.current_version(spark, path) == version_before,
            "version_0_after": ds.snapshot(spark, path, 0),
            "history_operations_after": [h["operation"] for h in ds.history(spark, path)],
        }
        # a second, tiny table declared with liquid clustering
        RUN["clustered"] = ds.create_clustered_table(spark, cls.temp_root / "clustered")
        # the transfer: the same sequence with the altered correction, on a fresh path
        RUN["transfer"] = ds.run_sequence(spark, cls.temp_root / "transfer", EXPECTED["transfer"]["correction"])
        OUTPUTS.update(RUN)

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()
        shutil.rmtree(cls.temp_root, ignore_errors=True)

    # ---------------------------------------------------------------- the expected values
    def test_01_expected_values_are_an_independent_replay(self):
        self.assertEqual(derive_all(), EXPECTED, "expected/snapshots.json differs from a fresh plain-Python replay")
        tree = ast.parse((ROOT / "expected/derive_expected.py").read_text(encoding="utf-8"))
        imported = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import)
                    for alias in node.names}
        imported |= {node.module.split(".")[0] for node in ast.walk(tree)
                     if isinstance(node, ast.ImportFrom) and node.module}
        self.assertFalse(imported & {"pyspark", "delta", "solutions", "run_tests"},
                         f"the derivation imports {sorted(imported)}")

    # ---------------------------------------------------------------- snapshots and files
    def test_02_every_version_reads_its_own_snapshot(self):
        for v in range(0, 9):
            with self.subTest(version=v):
                rows = RUN["snapshots"][str(v)]
                self.assertEqual(rows, BASE["versions"][str(v)]["rows"])
                totals = ds.totals(rows)
                self.assertEqual(totals["total_inspected"], BASE["versions"][str(v)]["total_inspected"])
                self.assertEqual(totals["total_defective"], BASE["versions"][str(v)]["total_defective"])

    def test_03_update_rewrites_one_file_and_the_directory_overcounts(self):
        expected = BASE["update_version_2"]
        observed = RUN["after_update"]
        self.assertEqual(observed["delta_total"], BASE["versions"]["2"]["total_inspected"])  # 20
        self.assertEqual(observed["directory_parquet_sum"], BASE["directory_parquet_sum_after_version_2"])  # 30
        self.assertEqual(observed["data_files_on_disk"], expected["data_files_on_disk"])
        self.assertEqual(observed["files_in_current_version"], expected["files_in_current_version"])
        update = metrics_of(RUN["history"][2], ["numUpdatedRows", "numCopiedRows", "numRemovedFiles",
                                                "numAddedFiles"])
        self.assertEqual(update, {"numUpdatedRows": expected["rows_updated"], "numCopiedRows": expected["rows_copied"],
                                  "numRemovedFiles": expected["files_removed"],
                                  "numAddedFiles": expected["files_added"]})

    def test_04_enabling_the_change_feed_changes_protocol_not_rows(self):
        before, after = RUN["after_update"]["detail"], RUN["after_change_feed"]["detail"]
        feature = DOC["change_feed_protocol"]["table_feature"]
        self.assertNotIn(feature, before["tableFeatures"])
        self.assertIn(feature, after["tableFeatures"])
        self.assertEqual(after["properties"].get(ds.CHANGE_FEED_PROPERTY), "true")
        self.assertEqual(after["minReaderVersion"], DOC["change_feed_protocol"]["min_reader_version"])
        self.assertGreaterEqual(after["minWriterVersion"], DOC["change_feed_protocol"]["min_writer_version_at_least"])
        self.assertEqual(RUN["snapshots"]["3"], RUN["snapshots"]["2"], "a property commit must change no row")

    # ---------------------------------------------------------------- merges
    def test_05_incremental_merge_leaves_the_missing_key_alone(self):
        m = metrics_of(RUN["history"][4], ["numTargetRowsInserted", "numTargetRowsUpdated", "numTargetRowsDeleted",
                                           "numSourceRows"])
        e = BASE["merge_metrics"]["4"]
        self.assertEqual(m, {"numTargetRowsInserted": e["inserted"], "numTargetRowsUpdated": e["updated"],
                             "numTargetRowsDeleted": e["deleted"], "numSourceRows": e["source_rows"]})
        a3 = [r for r in RUN["snapshots"]["3"] if r["inspection_id"] == "A"]
        a4 = [r for r in RUN["snapshots"]["4"] if r["inspection_id"] == "A"]
        self.assertEqual(a4, a3, "A was absent from the delivery and must be untouched, not deleted")

    def test_06_duplicate_source_rows_are_refused_without_a_commit(self):
        r = RUN["duplicate_refusal"]
        self.assertEqual(r["condition"], DOC["refusals"]["duplicate_source"])
        self.assertEqual(r["version_after"], r["version_before"], "a refused MERGE must not commit")
        self.assertEqual(r["rows_after"], BASE["versions"]["4"]["rows"])
        dup = BASE["duplicate_source"]
        self.assertEqual(RUN["day3_source_keys"][dup["key"]], dup["rows"])
        self.assertEqual(len(RUN["day3_source_keys"]), dup["distinct_keys"])

    def test_07_guarded_merge_applies_only_newer_revisions(self):
        self.assertEqual(RUN["deduped_day3"], BASE["deduped_day3"])
        m = metrics_of(RUN["history"][5], ["numTargetRowsInserted", "numTargetRowsUpdated", "numTargetRowsDeleted",
                                           "numSourceRows"])
        e = BASE["merge_metrics"]["5"]
        self.assertEqual(m, {"numTargetRowsInserted": e["inserted"], "numTargetRowsUpdated": e["updated"],
                             "numTargetRowsDeleted": e["deleted"], "numSourceRows": e["source_rows"]})
        skipped = BASE["guard_skipped"]
        a5 = [r for r in RUN["snapshots"]["5"] if r["inspection_id"] == skipped["inspection_id"]][0]
        self.assertEqual(a5["revision"], skipped["target_revision"], "the stale revision-0 replay must be skipped")

    def test_08_scoped_snapshot_merge_deletes_only_inside_its_plant(self):
        entry = RUN["history"][6]
        m = metrics_of(entry, ["numTargetRowsInserted", "numTargetRowsUpdated", "numTargetRowsDeleted",
                               "numSourceRows", "numTargetRowsNotMatchedBySourceDeleted"])
        e = BASE["merge_metrics"]["6"]
        self.assertEqual(m, {"numTargetRowsInserted": e["inserted"], "numTargetRowsUpdated": e["updated"],
                             "numTargetRowsDeleted": e["deleted"], "numSourceRows": e["source_rows"],
                             "numTargetRowsNotMatchedBySourceDeleted": e["deleted"]})
        north = [r for r in RUN["snapshots"]["6"] if r["plant"] == "North"]
        self.assertEqual(north, [r for r in BASE["versions"]["5"]["rows"] if r["plant"] == "North"])

    def test_09_unscoped_delete_clause_removes_rows_it_never_saw(self):
        wrong = BASE["unscoped_snapshot_merge"]
        self.assertEqual(RUN["unscoped_copy"]["rows"], wrong["rows"])
        self.assertEqual(RUN["unscoped_copy"]["metrics"]["numTargetRowsDeleted"], wrong["metrics"]["deleted"])
        self.assertGreater(wrong["metrics"]["deleted"], BASE["merge_metrics"]["6"]["deleted"],
                           "the wrong approach must delete more than the scoped one")

    def test_19_duplicates_of_a_new_key_are_inserted_not_refused(self):
        observed, expected = RUN["first_arrival_copy"], BASE["duplicate_on_first_arrival"]
        self.assertEqual(observed["outcome"]["type"], "no error", "no target row is matched twice, so nothing is refused")
        self.assertEqual(observed["rows"], expected["rows"])
        self.assertEqual([r["inspection_id"] for r in observed["rows"]].count("D"), 2, "D must arrive twice")
        e = expected["metrics"]
        self.assertEqual(observed["metrics"], {"numTargetRowsInserted": e["inserted"], "numTargetRowsUpdated": e["updated"],
                                               "numTargetRowsDeleted": e["deleted"], "numSourceRows": e["source_rows"]})

    # ---------------------------------------------------------------- change data feed
    def test_10_change_feed_returns_row_level_changes(self):
        self.assertEqual(RUN["change_feed"], BASE["change_feed_versions_4_to_6"])
        counts = dict(sorted(Counter(c["_change_type"] for c in RUN["change_feed"]).items()))
        self.assertEqual(counts, BASE["change_feed_counts"])
        self.assertGreaterEqual(RUN["change_files"], 1, "UPDATE/DELETE/MERGE changes are stored under _change_data")

    def test_11_change_feed_before_enablement_is_refused(self):
        r = RUN["change_feed_refusal"]
        self.assertEqual(r["condition"], DOC["refusals"]["change_feed_before_enablement"])
        enabled = RUN["history"][DOC["change_feed_enabled_at_version"]]
        self.assertEqual(enabled["operation"], "SET TBLPROPERTIES")
        self.assertIn(ds.CHANGE_FEED_PROPERTY, enabled["operationParameters"].get("properties", ""))

    # ---------------------------------------------------------------- schema
    def test_12_schema_enforcement_rejects_an_unexpected_column(self):
        r = RUN["schema_refusal"]
        self.assertIn(DOC["refusals"]["schema_mismatch_text"], r["message"])
        self.assertEqual(r["version_after"], r["version_before"], "a refused append must not commit")
        self.assertEqual(r["columns_after"], BASE["schema_before_evolution"])

    def test_13_explicit_evolution_adds_a_nullable_column(self):
        self.assertEqual(RUN["evolution"]["columns_v7"], BASE["schema_after_evolution"])
        self.assertEqual(RUN["evolution"]["columns_v6"], BASE["schema_before_evolution"],
                         "time travel to version 6 must return the schema version 6 had")
        v7 = RUN["snapshots"]["7"]
        self.assertEqual(sorted(r["inspection_id"] for r in v7 if r["inspector"] is None),
                         BASE["rows_with_null_inspector_after_evolution"])
        row = BASE["row_with_inspector"]
        self.assertEqual([r["inspector"] for r in v7 if r["inspection_id"] == row["inspection_id"]], [row["inspector"]])

    # ---------------------------------------------------------------- maintenance
    def test_14_optimize_compacts_files_without_changing_rows(self):
        o, doc = RUN["optimize"], DOC["optimize"]
        self.assertGreaterEqual(o["files_in_current_version_before"], 2)
        self.assertEqual(o["first"]["numFilesAdded"], doc["files_after_compaction"])
        self.assertEqual(o["first"]["numFilesRemoved"], o["files_in_current_version_before"])
        self.assertEqual(o["files_in_current_version_after"], doc["files_after_compaction"])
        self.assertEqual(o["data_files_on_disk_after"], o["data_files_on_disk_before"] + 1,
                         "OPTIMIZE writes one file and physically deletes none")
        self.assertEqual(o["second"], {"numFilesAdded": doc["second_run_files_added"],
                                       "numFilesRemoved": doc["second_run_files_removed"]})
        self.assertEqual(o["version_after_second"], o["version_after_first"], "a no-op OPTIMIZE commits nothing")
        self.assertEqual(RUN["snapshots"]["8"], RUN["snapshots"]["7"], "compaction must not change a row")

    def test_15_vacuum_dry_run_respects_retention_and_the_safety_check(self):
        v, doc = RUN["vacuum"], DOC["retention"]
        self.assertEqual(v["retention_check"], doc["retention_check_expected_value"])
        self.assertFalse([p for p in v["dry_run_listed"] if p.endswith(".parquet")],
                         "every file is younger than the 7-day default, so no data file may be listed")
        self.assertIn(DOC["refusals"]["vacuum_retention_text"], v["below_retention"]["message"])
        self.assertTrue(v["data_files_unchanged"])
        self.assertTrue(v["version_unchanged"], "a DRY RUN commits nothing")
        self.assertEqual(v["version_0_after"], BASE["versions"]["0"]["rows"], "version 0 must still be readable")
        self.assertFalse([op for op in v["history_operations_after"] if "VACUUM" in op], "no VACUUM was committed")

    def test_16_history_names_every_commit(self):
        self.assertEqual([h["version"] for h in RUN["history"]], list(range(len(DOC["history_operations"]))))
        self.assertEqual([h["operation"] for h in RUN["history"]], DOC["history_operations"])

    def test_17_liquid_clustering_declares_its_table_features(self):
        c, doc = RUN["clustered"], DOC["clustered_table_protocol"]
        self.assertEqual(c["clusteringColumns"], doc["clustering_columns"])
        for feature in doc["table_features"]:
            self.assertIn(feature, c["tableFeatures"])
        self.assertEqual(c["minReaderVersion"], doc["min_reader_version"])
        self.assertEqual(c["minWriterVersion"], doc["min_writer_version"])

    # ---------------------------------------------------------------- transfer
    def test_18_transfer_altered_correction_moves_every_downstream_total(self):
        observed = RUN["transfer"]
        self.assertEqual(observed["directory_parquet_sum_after_version_2"],
                         TRANSFER["directory_parquet_sum_after_version_2"])
        for v in range(0, 9):
            with self.subTest(version=v):
                expected = TRANSFER["versions"][str(v)]
                self.assertEqual(observed["versions"][str(v)],
                                 {"row_count": expected["row_count"], "total_inspected": expected["total_inspected"],
                                  "total_defective": expected["total_defective"]})
        self.assertNotEqual(TRANSFER["versions"]["8"]["total_inspected"], BASE["versions"]["8"]["total_inspected"])


def hashes(patterns):
    files = sorted({p for pattern in patterns for p in ROOT.glob(pattern) if p.is_file()})
    return {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in files}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--evidence", help="write JSON evidence to this path")
    args = parser.parse_args()
    started = datetime.now(timezone.utc).isoformat()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(DeltaSequenceTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    finished = datetime.now(timezone.utc).isoformat()
    exit_status = 0 if result.wasSuccessful() and not result.skipped else 1
    if args.evidence:
        from importlib.metadata import version as dist_version
        environment = OUTPUTS.get("environment", {})
        evidence = {
            "lab": LAB,
            "executionClass": EXECUTION_CLASS,
            "runtime": "spark",
            "interpreter": sys.executable,
            "python": platform.python_version(),
            "platform": platform.platform(),
            "java": environment.get("java", "unavailable"),
            "spark": environment.get("spark", "unavailable"),
            "master": "local[2]",
            "packages": {name: dist_version(name) for name in ("pyspark", "py4j", "delta-spark",
                                                                "importlib_metadata", "zipp")},
            "deltaJarResolution": OUTPUTS.get("jar_resolution", "unavailable"),
            "sparkConfig": {"spark.ui.enabled": "false", "spark.ui.showConsoleProgress": "false",
                            "spark.driver.bindAddress": "127.0.0.1", "spark.sql.shuffle.partitions": "2",
                            "spark.databricks.delta.snapshotPartitions": "2",
                            "spark.sql.extensions": "io.delta.sql.DeltaSparkSessionExtension",
                            "spark.sql.catalog.spark_catalog": "org.apache.spark.sql.delta.catalog.DeltaCatalog",
                            "spark.local.dir": "a runner-created temporary directory, deleted after the run",
                            "spark.databricks.delta.retentionDurationCheck.enabled":
                                "never set by the lab; read back as "
                                + str(OUTPUTS.get("vacuum", {}).get("retention_check", "unavailable"))},
            "startedAt": started,
            "finishedAt": finished,
            "tests": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped),
            "exit": exit_status,
            "fixtureHashes": hashes(["fixtures/*", "expected/*"]),
            "solutionHashes": hashes(["solutions/*.py", "starters/*.py", "run_tests.py"]),
            "outputHashes": {key: sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()
                             for key, value in sorted(OUTPUTS.items())},
            "commands": ["python run_tests.py --evidence evidence.json", " ".join([sys.executable] + sys.argv)],
            "notes": ("Local Apache Spark 4.0.4 with open-source delta-spark 4.0.0 on one machine in local[2] mode, "
                      "web UI disabled. Snapshots, merge metrics, change-feed rows, schemas, protocol versions and "
                      "table features are Delta's own output, compared with a plain-Python replay and literals "
                      "copied from the Delta Lake 4.0.0 documentation. The duplicate-match MERGE, the "
                      "schema-mismatched append, the early change-feed read and the zero-hour VACUUM DRY RUN were "
                      "refused by Delta as expected. No retention was shortened, the retention check was never "
                      "turned off and no VACUUM deleted anything. Nothing ran on Databricks; no timing is reported."),
            "observations": OUTPUTS,
        }
        Path(args.evidence).write_text(json.dumps(evidence, indent=1, default=str) + "\n", encoding="utf-8")
        print(f"evidence written to {args.evidence}")
    print(f"{result.testsRun} tests, {len(result.failures)} failures, {len(result.errors)} errors, "
          f"{len(result.skipped)} skipped; exit {exit_status}")
    sys.exit(exit_status)


if __name__ == "__main__":
    main()
