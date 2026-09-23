"""Lab L24 acceptance runner: local Apache Spark 4.0.4 on one machine, offline.

    python run_tests.py --evidence evidence.json    # Python 3.12 with requirements.txt installed

Every expectation comes from expected/*.json, typed by hand from the tables in
DATA.md and cross-checked by expected/derive_expected.py (standard library, no
shared code). The runner never derives an expectation from the code under
test. Skips are not allowed: a missing dependency is a failure. No SQL Server,
SSIS or SQL Server Agent is installed, started or contacted: the legacy
procedure and package are read as text.
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True  # keep the package free of __pycache__

import argparse  # noqa: E402
import copy  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import platform  # noqa: E402
import subprocess  # noqa: E402
import time  # noqa: E402
import unittest  # noqa: E402
from datetime import datetime, timezone  # noqa: E402
from hashlib import sha256  # noqa: E402
from pathlib import Path  # noqa: E402

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.environ["PYSPARK_PYTHON"] = sys.executable

import importlib  # noqa: E402

from pyspark.sql import functions as F  # noqa: E402

# The reference by default; LAB_L24_SOLUTION=starters.migration_starter tests your own module.
SOLUTION = os.environ.get("LAB_L24_SOLUTION", "solutions.migration")
m = importlib.import_module(SOLUTION)

EXPECTED = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "expected").glob("*.json"))}
OUTPUTS: dict[str, object] = {}
SPARK = None


def spark():
    global SPARK
    if SPARK is None:
        SPARK = m.build_session()
        OUTPUTS["spark_version"] = SPARK.version
        OUTPUTS["ansi_enabled"] = SPARK.conf.get("spark.sql.ansi.enabled")
        OUTPUTS["session_time_zone"] = SPARK.conf.get("spark.sql.session.timeZone")
    return SPARK


P1 = m.fixture("inspections_p1.json")
P2 = m.fixture("inspections_p2.json")
CTX = m.CONTEXT


def legacy_p1():
    return m.legacy_outputs("legacy_detail_p1.json", "legacy_report_p1.json")


def legacy_p2():
    return m.legacy_outputs("legacy_detail_p2.json", "legacy_report_p2.json")


def record(name, value):
    OUTPUTS[name] = value
    return value


class TextTests(unittest.TestCase):
    """Inventory, orchestration mapping, type emulation and the cutover gate: plain Python."""

    def test_01_procedure_inventory_matches_the_hand_reading(self):
        sql = (ROOT / "legacy" / "sp_daily_inspections.sql").read_text(encoding="utf-8")
        found = record("inventory", m.scan_tsql(sql))
        self.assertEqual(found, EXPECTED["inventory"])

    def test_02_package_maps_to_a_job_plan(self):
        package = json.loads((ROOT / "legacy" / "pkg_csv_import.json").read_text(encoding="utf-8"))
        plan = record("job_plan", m.map_package(package, CTX["server_time_zone"]))
        self.assertEqual(plan, EXPECTED["job_plan"])
        # The failure path must not wait for success: it runs only when a dependency failed.
        notify = next(t for t in plan["tasks"] if t["task_key"] == "notify_on_failure")
        self.assertEqual(notify["run_if"], "at_least_one_failed")

    def test_03_datetime_rounding_emulation(self):
        rounded = {raw: m.datetime_round(raw) for raw in EXPECTED["semantics"]["datetime_round"]}
        record("datetime_round", rounded)
        self.assertEqual(rounded, EXPECTED["semantics"]["datetime_round"])

    def test_04_cutover_gate_decisions(self):
        runs = m.fixture("parallel_run.json")
        decisions = {name: m.cutover_gate(s, runs["required_clean_days"]) for name, s in runs["scenarios"].items()}
        record("cutover", decisions)
        self.assertEqual(decisions, EXPECTED["cutover"])
        # The pass on 2026-03-09 happened before the code change and is not carried forward.
        self.assertEqual(decisions["as_logged"]["clean_days"], 0)


class PipelineTests(unittest.TestCase):
    """The P1 pilot: target transformation, naive translation, reconciliation, incremental state."""

    @classmethod
    def setUpClass(cls):
        cls.spark = spark()

    def setUp(self):
        self.spark.conf.set("spark.sql.session.timeZone", m.SESSION_TIME_ZONE)

    def test_05_landing_types_and_null_counts(self):
        silver = m.land(m.source_frame(self.spark, P1))
        types = {f.name: f.dataType.simpleString() for f in silver.schema.fields}
        rows = [m.canon_row(r.asDict()) for r in silver.collect()]
        nulls = {c: sum(1 for r in rows if r[c] is None) for c in types}
        as_of_rows = silver.where(F.col("updated_local") <= F.lit(CTX["p1"]["as_of"]).cast("timestamp_ntz")).count()
        sample = next(r for r in rows if r["inspection_id"] == "109")
        got = {
            "columns": types,
            "rows": len(rows),
            "nulls": nulls,
            "as_of_rows": as_of_rows,
            "sample": {k: sample[k] for k in ("inspection_id", "inspected_local", "rework_cost")},
        }
        self.assertEqual(record("landing", got), EXPECTED["landing"])

    def test_06_key_profiles_show_which_keys_need_a_collation_rule(self):
        got = {
            "p1": {c: m.profile_keys(m.source_frame(self.spark, P1), c) for c in ("inspector_code", "plant_code")},
            "p2": {"inspector_code": m.profile_keys(m.source_frame(self.spark, P2), "inspector_code")},
        }
        self.assertEqual(record("profiles", got), EXPECTED["profiles"])

    def test_07_target_output_matches_the_literals(self):
        out = m.outputs(self.spark, P1, "P1", m.TARGET, CTX["p1"]["as_of"])
        record("target_p1", out)
        self.assertEqual(out["detail"], EXPECTED["target_p1"]["detail"])
        self.assertEqual(out["report"], EXPECTED["target_p1"]["report"])
        self.assertEqual(out["types"], EXPECTED["target_p1"]["types"])

    def test_08_target_reconciles_with_the_legacy_report(self):
        out = m.outputs(self.spark, P1, "P1", m.TARGET, CTX["p1"]["as_of"])
        result = record("reconcile_target", m.reconcile(legacy_p1(), out))
        self.assertEqual(result, EXPECTED["reconcile_p1"]["target"])

    def test_09_naive_translation_fails_on_every_check(self):
        out = m.outputs(self.spark, P1, "P1", m.NAIVE, CTX["p1"]["as_of"])
        result = record("reconcile_naive", m.reconcile(legacy_p1(), out))
        self.assertEqual(result, EXPECTED["reconcile_p1"]["naive"])
        # The report still has six rows: a row count alone would have passed.
        self.assertEqual(result["row_counts"]["report"], [6, 6])

    def test_10_spark_full_outer_join_agrees_on_membership(self):
        old = legacy_p1()
        target = m.outputs(self.spark, P1, "P1", m.TARGET, CTX["p1"]["as_of"])
        naive = m.outputs(self.spark, P1, "P1", m.NAIVE, CTX["p1"]["as_of"])
        keys = ["plant_code", "business_day", "shift_code"]
        got = {
            "target_report": m.spark_key_membership(self.spark, old["report"], target["report"], keys),
            "naive_report": m.spark_key_membership(self.spark, old["report"], naive["report"], keys),
            "naive_detail": m.spark_key_membership(self.spark, old["detail"], naive["detail"], ["inspection_id"]),
        }
        self.assertEqual(record("membership", got), EXPECTED["reconcile_p1"]["membership"])

    def flip(self, name):
        out = m.outputs(self.spark, P1, "P1", m.FLIPS[name], CTX["p1"]["as_of"])
        result = record(f"flip:{name}", m.reconcile(legacy_p1(), out))
        self.assertEqual(result, EXPECTED["flips_p1"][name])
        return result

    def test_11_binary_keys_hide_behind_matching_totals(self):
        result = self.flip("binary_keys")
        self.assertEqual((result["checks"]["totals"], result["checks"]["row_counts"]), ("pass", "pass"))
        self.assertEqual(result["verdict"], "fail")

    def test_12_where_filter_drops_rows_with_null_keys(self):
        result = self.flip("where_filter")
        self.assertIn(["detail.inspector_code", 1, 0], result["nulls"])
        self.assertEqual(result["report"]["missing"], [["P1", "2026-03-03", "UNASSIGNED"]])

    def test_13_session_zone_day_moves_rows_between_days(self):
        result = self.flip("session_day")
        moved = sorted(i for i, f, _, _ in result["detail"]["changed"] if f == "business_day")
        self.assertEqual(moved, [103, 109])

    def test_14_fractional_division_changes_only_the_rate(self):
        result = self.flip("fractional_division")
        failing = sorted(k for k, v in result["checks"].items() if v == "fail")
        self.assertEqual(failing, ["report_keys", "types"])

    def test_15_double_amounts_fail_the_type_and_exact_checks(self):
        result = self.flip("double_amounts")
        self.assertEqual(result["checks"]["types"], "fail")
        self.assertEqual(result["checks"]["detail_keys"], "pass")

    def test_16_missing_as_of_filter_is_a_basis_error(self):
        out = m.outputs(self.spark, P1, "P1", m.TARGET, as_of=None)
        result = record("reconcile_basis", m.reconcile(legacy_p1(), out))
        self.assertEqual(result, EXPECTED["reconcile_p1"]["basis_without_as_of"])
        self.assertEqual(result["detail"]["only_new"], [112])

    def test_17_session_time_zone_dependence(self):
        got = {"target": {}, "session_day": {}}
        for zone in EXPECTED["semantics"]["session_zone"]["target"]:
            self.spark.conf.set("spark.sql.session.timeZone", zone)
            out = m.outputs(self.spark, P1, "P1", m.TARGET, CTX["p1"]["as_of"])
            got["target"][zone] = m.reconcile(legacy_p1(), out)["verdict"]
        for zone in EXPECTED["semantics"]["session_zone"]["session_day"]:
            self.spark.conf.set("spark.sql.session.timeZone", zone)
            out = m.outputs(self.spark, P1, "P1", m.FLIPS["session_day"], CTX["p1"]["as_of"])
            got["session_day"][zone] = m.reconcile(legacy_p1(), out)["verdict"]
        self.assertEqual(record("session_zone", got), EXPECTED["semantics"]["session_zone"])

    def test_18_division_semantics(self):
        row = self.spark.sql("SELECT 400 / 120 AS fractional, 400 div 120 AS integral").first()
        got = {"fractional": m.canon(row.fractional), "integral": m.canon(row.integral)}
        self.assertEqual(record("division", got), EXPECTED["semantics"]["division"])

    def test_19_concat_and_not_in_null_semantics(self):
        row = self.spark.sql(
            "SELECT concat('P1', '-', CAST(NULL AS STRING)) AS c, concat_ws('', 'P1', '-', CAST(NULL AS STRING)) AS w"
        ).first()
        concat = {"concat": row.c, "concat_ws": row.w}
        outer = self.spark.sql("SELECT * FROM VALUES (1), (2) AS t(x)")
        holds = self.spark.sql("SELECT * FROM VALUES (1), (CAST(NULL AS INT)) AS h(y)")
        not_in = self.spark.sql(
            "SELECT count(*) AS n FROM VALUES (1), (2) AS t(x) WHERE x NOT IN (SELECT y FROM VALUES (1), (CAST(NULL AS INT)) AS h(y))"
        ).first().n
        anti = outer.join(holds, outer.x == holds.y, "left_anti").count()
        self.assertEqual(record("concat", concat), EXPECTED["semantics"]["concat"])
        self.assertEqual(record("not_in", {"not_in_rows": not_in, "left_anti_rows": anti}), EXPECTED["semantics"]["not_in"])

    def test_20_raw_versus_rounded_business_day(self):
        case = EXPECTED["semantics"]["raw_versus_rounded_day"]
        rounded = m.datetime_round(case["raw"])
        frame = self.spark.createDataFrame([(0, case["raw"]), (1, rounded)], "n INT, inspected_at STRING")
        frame = frame.withColumn("inspected_local", F.col("inspected_at").cast("timestamp_ntz"))
        days = [r.d.isoformat() for r in frame.orderBy("n").select(m.business_day(m.TARGET, "P1").alias("d")).collect()]
        got = {"raw": case["raw"], "raw_business_day": days[0], "rounded": rounded, "rounded_business_day": days[1]}
        self.assertEqual(record("raw_versus_rounded_day", got), case)

    def test_21_incremental_window_selects_by_change_time(self):
        w = CTX["p1"]["tonight"]
        state = m.legacy_state_before()
        days = m.run_window(self.spark, state, P1, "P1", w["since"], w["until"])
        record("tonight", {"affected_days": days, "watermark_after": state["watermark"]})
        self.assertEqual(days, EXPECTED["incremental_p1"]["tonight"]["affected_days"])
        self.assertEqual(state["watermark"], EXPECTED["incremental_p1"]["tonight"]["watermark_after"])
        result = m.reconcile(legacy_p1(), {"detail": state["detail"], "report": state["report"]})
        self.assertEqual(result["verdict"], "pass")

    def test_22_event_time_selection_misses_a_late_correction(self):
        w = CTX["p1"]["tonight"]
        state = m.legacy_state_before()
        days = m.run_window(self.spark, state, P1, "P1", w["since"], w["until"], select_by="event")
        result = m.reconcile(legacy_p1(), {"detail": state["detail"], "report": state["report"]})
        record("event_time", {"affected_days": days, "reconcile": result})
        self.assertEqual(days, EXPECTED["incremental_p1"]["event_time"]["affected_days"])
        self.assertEqual(result, EXPECTED["incremental_p1"]["event_time"]["reconcile"])

    def test_23_retry_after_a_partial_write_is_idempotent(self):
        w = CTX["p1"]["tonight"]
        state = m.legacy_state_before()
        with self.assertRaises(m.InjectedFailure) as caught:
            m.run_window(self.spark, state, P1, "P1", w["since"], w["until"], fail_after_detail=True)
        self.assertIn("report and watermark untouched", str(caught.exception))
        after_failure = {"watermark": state["watermark"], "consistent": m.consistent(state), "report_rows": len(state["report"])}
        m.run_window(self.spark, state, P1, "P1", w["since"], w["until"])
        after_retry = {"watermark": state["watermark"], "consistent": m.consistent(state)}
        record("retry", {"after_failure": after_failure, "after_retry": after_retry})
        self.assertEqual({"after_failure": after_failure, "after_retry": after_retry}, EXPECTED["incremental_p1"]["retry"])
        self.assertEqual(m.reconcile(legacy_p1(), {"detail": state["detail"], "report": state["report"]})["verdict"], "pass")

    def test_24_next_window_and_empty_window(self):
        state = m.legacy_state_before()
        tonight = CTX["p1"]["tonight"]
        m.run_window(self.spark, state, P1, "P1", tonight["since"], tonight["until"])
        nxt = CTX["p1"]["next"]
        next_days = m.run_window(self.spark, state, P1, "P1", nxt["since"], nxt["until"])
        next_report = copy.deepcopy(state["report"])
        empty = CTX["p1"]["empty"]
        empty_days = m.run_window(self.spark, state, P1, "P1", empty["since"], empty["until"])
        record("next", {"affected_days": next_days, "report": next_report, "empty_days": empty_days})
        self.assertEqual(next_days, EXPECTED["incremental_p1"]["next"]["affected_days"])
        self.assertEqual(next_report, EXPECTED["incremental_p1"]["next"]["report"])
        self.assertEqual(empty_days, EXPECTED["incremental_p1"]["empty"]["affected_days"])
        self.assertEqual(state["report"], next_report)  # an empty window changes nothing
        self.assertEqual(state["watermark"], EXPECTED["incremental_p1"]["empty"]["watermark_after"])


class TransferTests(unittest.TestCase):
    """Altered input: plant P2 in another time zone, a leading-space key and a registered rule change."""

    @classmethod
    def setUpClass(cls):
        cls.spark = spark()

    def setUp(self):
        self.spark.conf.set("spark.sql.session.timeZone", m.SESSION_TIME_ZONE)

    def run_p2(self, rules):
        return m.outputs(self.spark, P2, "P2", rules, CTX["p2"]["as_of"])

    def test_25_legacy_compatible_rules_reconcile_on_new_data(self):
        result = record("transfer_compatible", m.reconcile(legacy_p2(), self.run_p2(m.TARGET)))
        self.assertEqual(result, EXPECTED["transfer_p2"]["compatible"])

    def test_26_trim_matches_a_leading_space_the_source_kept(self):
        result = record("transfer_trim", m.reconcile(legacy_p2(), self.run_p2(m.Rules(key_rule="trim"))))
        self.assertEqual(result, EXPECTED["transfer_p2"]["trim_keys"])
        self.assertEqual(result["checks"]["totals"], "pass")

    def test_27_plant_local_rule_differences_are_all_registered(self):
        old, new = legacy_p2(), self.run_p2(m.Rules(day_rule="plant_local"))
        result = m.reconcile(old, new)
        explained = m.explain(result, old, new, P2, m.fixture("difference_register_p2.json"))
        record("transfer_plant_local", {"reconcile": result, "explain": explained})
        self.assertEqual(result, EXPECTED["transfer_p2"]["plant_local"]["reconcile"])
        self.assertEqual(explained, EXPECTED["transfer_p2"]["plant_local"]["explain"])

    def test_28_an_unowned_register_entry_explains_nothing(self):
        old, new = legacy_p2(), self.run_p2(m.Rules(day_rule="plant_local"))
        register = m.fixture("difference_register_p2.json")
        register["entries"][0]["owner"] = None
        explained = record("transfer_unowned", m.explain(m.reconcile(old, new), old, new, P2, register))
        self.assertEqual(explained, EXPECTED["transfer_p2"]["plant_local"]["explain_without_owner"])


def file_hashes(folder: str) -> dict:
    return {
        p.relative_to(ROOT).as_posix(): sha256(p.read_bytes()).hexdigest()
        for p in sorted((ROOT / folder).rglob("*"))
        if p.is_file() and "__pycache__" not in p.parts
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()
    started_at = datetime.now(timezone.utc)
    clock = time.monotonic()
    suite = unittest.TestSuite()
    for case in (TextTests, PipelineTests, TransferTests):
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    try:
        result = unittest.TextTestRunner(verbosity=2).run(suite)
    finally:
        if SPARK is not None:
            m.stop_session(SPARK)
    finished_at = datetime.now(timezone.utc)
    java_home = os.environ.get("JAVA_HOME")
    java_bin = str(Path(java_home) / "bin" / "java") if java_home else "java"
    java_text = subprocess.run([java_bin, "-version"], capture_output=True, text=True).stderr
    java_version = next((line.split('"')[1] for line in java_text.splitlines() if '"' in line), java_text.strip())
    import py4j  # noqa: E402
    import pyspark  # noqa: E402

    exit_code = 0 if result.wasSuccessful() and not result.skipped else 1
    output_hashes = {
        name: sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()
        for name, value in sorted(OUTPUTS.items())
    }
    evidence = {
        "lab": "lab-l24-migration-reconciliation",
        "executionClass": "local-executed",
        "runtime": "spark",
        "solutionModule": SOLUTION,
        "python": platform.python_version(),
        "interpreter": f"{platform.python_implementation()} {platform.python_version()} with requirements.txt installed",
        "java": java_version,
        "packages": {"pyspark": pyspark.__version__, "py4j": py4j.__version__},
        "spark": OUTPUTS.get("spark_version"),
        "sessionTimeZone": m.SESSION_TIME_ZONE,
        "ansiEnabled": OUTPUTS.get("ansi_enabled"),
        "platform": platform.system() + " " + platform.release(),
        "startedAt": started_at.isoformat(),
        "finishedAt": finished_at.isoformat(),
        "durationSeconds": round(time.monotonic() - clock, 3),
        "tests": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "exit": exit_code,
        "sourcePlatform": (
            "Not installed and not accessed: no SQL Server, SSIS or SQL Server Agent instance was installed, "
            "started or contacted. legacy/sp_daily_inspections.sql and legacy/pkg_csv_import.json were read as text."
        ),
        "fixtureHashes": file_hashes("fixtures"),
        "legacyTextHashes": file_hashes("legacy"),
        "expectedHashes": file_hashes("expected"),
        "solutionHashes": {**file_hashes("solutions"), "run_tests.py": sha256((ROOT / "run_tests.py").read_bytes()).hexdigest()},
        "outputHashes": output_hashes,
        "commands": ["python run_tests.py --evidence evidence.json"],
        "notes": (
            "Local Apache Spark 4.0.4 (PySpark) on one machine, master local[2], UI disabled, 2 shuffle partitions, "
            "ANSI mode at its Spark 4 default, session time zone UTC set explicitly (one test switches it to "
            "Asia/Kolkata and America/New_York and back). Target tables are in-memory row lists; no Delta, metastore, "
            "network, warehouse, Databricks workspace or cloud resource was used. The T-SQL procedure and the "
            "SSIS-style package were never executed; their semantics are represented by hand-authored legacy "
            "fixtures. Expected literals were typed by hand (DATA.md) and cross-checked by "
            "expected/derive_expected.py; none was generated by the solution under test."
        ),
    }
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: evidence[k] for k in ("spark", "python", "java", "tests", "failures", "errors", "skipped", "exit")}, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
