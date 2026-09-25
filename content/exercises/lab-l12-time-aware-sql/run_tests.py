"""Lab L12 acceptance runner: local Apache Spark 4.0.4, one machine, offline.

    <python> run_tests.py --evidence evidence.json                # every test, reference portfolio
    <python> run_tests.py --portfolio starters/portfolio.sql      # only the tests your file covers

Every expected value comes from expected/*.json, authored by hand or by the independent
standard-library derivation in expected/derive_time.py (see DATA.md) before the solution ran.
The runner never derives an expectation from the code under test. Skips are not allowed: a
missing dependency is an error, and the evidence records the skip count so that it can be
checked to be zero.
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True  # keep __pycache__ folders out of the lab package

import argparse  # noqa: E402
import copy  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import platform  # noqa: E402
import re  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
import time  # noqa: E402
import unittest  # noqa: E402
from datetime import date, datetime, timedelta, timezone  # noqa: E402
from hashlib import sha256  # noqa: E402
from pathlib import Path  # noqa: E402

# Spark's Python workers must run this interpreter; set before any session exists.
os.environ["PYSPARK_PYTHON"] = sys.executable

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from solutions.portfolio import (  # noqa: E402
    REFERENCE,
    SESSION_TIME_ZONE,
    build_session,
    load_queries,
    register_views,
    run,
)

import logging  # noqa: E402

from pyspark.logger import PySparkLogger  # noqa: E402

# The deliberate failures are asserted by error class below; stop PySpark from also printing
# each one to the console as a JSON log record.
for _logger in ("SQLQueryContextLogger", "DataFrameQueryContextLogger"):
    PySparkLogger.getLogger(_logger).setLevel(logging.CRITICAL)

EXPECTED = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "expected").glob("*.json"))}
FIXTURES = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "fixtures").glob("*.json"))}
REFERENCE_ONLY = "reference run only"
CONTEXT: dict[str, object] = {"spark": None, "queries": None}
OUTPUTS: dict[str, object] = {}


def needs(*names: str):
    """Name the portfolio queries a test checks; --portfolio runs a test only if the file defines them."""

    def mark(test):
        test.needs = set(names)
        return test

    return mark


def plain(value):
    """Spark values as JSON-comparable values: dates as ISO strings, rows as lists."""
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, timedelta):
        return value.total_seconds()
    return value


def error_class(exc: Exception) -> str | None:
    getter = getattr(exc, "getCondition", None) or getattr(exc, "getErrorClass", None)
    return getter() if getter else None


class LabCase(unittest.TestCase):
    """Shared helpers: every comparison is an executed query against an authored literal."""

    maxDiff = None

    @property
    def spark(self):
        return CONTEXT["spark"]

    @property
    def queries(self):
        return CONTEXT["queries"]

    def query(self, name: str, label: str | None = None):
        schema, rows = run(self.spark, name, self.queries)
        rows = plain(rows)
        OUTPUTS[label or name] = {"schema": schema, "rows": rows}
        return schema, rows

    def record(self, name: str, keys: list[str]) -> dict:
        """A one-row query as {column: value}, keyed by the names the expected file uses."""
        _, rows = self.query(name)
        self.assertEqual(len(rows), 1, f"{name} must return exactly one row")
        return dict(zip(keys, rows[0]))

    def expect_error(self, name: str, expected: str):
        with self.assertRaises(Exception) as caught:
            self.spark.sql(self.queries[name]).collect()
        actual = error_class(caught.exception)
        OUTPUTS["error:" + name] = {"error_class": actual}
        first_line = str(caught.exception).splitlines()[0] if str(caught.exception) else ""
        self.assertEqual(actual, expected, f"{name} failed for a different reason: {first_line}")

    def frame_kinds(self, name: str, sql: str | None = None) -> list[str]:
        """The window frame kinds Spark resolved, read from the analyzed plan."""
        df = self.spark.sql(sql if sql is not None else self.queries[name])
        plan = df._jdf.queryExecution().analyzed().toString()
        kinds = sorted(set(re.findall(r"specifiedwindowframe\((RowFrame|RangeFrame)", plan)))
        OUTPUTS["frames:" + name] = kinds
        return kinds


class PortfolioTests(LabCase):
    """The reference inputs under session zone America/New_York with ANSI mode on."""

    # ---- environment ---------------------------------------------------------------
    def test_session_is_local_ansi_new_york(self):
        self.assertEqual(self.spark.version, "4.0.4")
        self.assertEqual(self.spark.conf.get("spark.sql.session.timeZone"), SESSION_TIME_ZONE)
        self.assertEqual(self.spark.conf.get("spark.sql.ansi.enabled"), "true")
        self.assertEqual(self.spark.sparkContext.master, "local[2]")

    # ---- windows ---------------------------------------------------------------------
    @needs("running_total")
    def test_running_total_uses_an_explicit_rows_frame(self):
        _, rows = self.query("running_total")
        self.assertEqual(rows, EXPECTED["windows"]["running_total"])
        self.assertEqual(self.frame_kinds("running_total"), EXPECTED["windows"]["frame_kinds"]["running_total"])

    @needs("running_total_default_frame")
    def test_default_frame_is_range_so_peers_share_a_total(self):
        _, rows = self.query("running_total_default_frame")
        self.assertEqual(rows, EXPECTED["windows"]["running_total_default_frame"])
        m1_first_day = [r[4] for r in rows if r[0] == "M1" and r[1] == "2026-03-01"]
        self.assertEqual(m1_first_day, [90, 90], "both 1 March shifts of M1 are peers under ORDER BY day")
        self.assertEqual(self.frame_kinds("running_total_default_frame"),
                         EXPECTED["windows"]["frame_kinds"]["running_total_default_frame"])

    @needs("moving_average")
    def test_moving_average_edges_and_null(self):
        _, rows = self.query("moving_average")
        self.assertEqual(rows, EXPECTED["windows"]["moving_average"])
        self.assertEqual(self.frame_kinds("moving_average"), EXPECTED["windows"]["frame_kinds"]["moving_average"])

    @needs("range_versus_rows")
    def test_range_frame_counts_days_where_rows_frame_counts_rows(self):
        _, rows = self.query("range_versus_rows")
        self.assertEqual(rows, EXPECTED["windows"]["range_versus_rows"])
        self.assertEqual(self.frame_kinds("range_versus_rows"), EXPECTED["windows"]["frame_kinds"]["range_versus_rows"])

    @needs(REFERENCE_ONLY)
    def test_values_alone_cannot_see_a_missing_frame_clause(self):
        # The starter's running_total omits the frame. On this unique (day, shift) key its numbers
        # equal the ROWS answer, so only the resolved frame kind shows that the clause is missing.
        starter = load_queries(ROOT / "starters" / "portfolio.sql")["running_total"]
        rows = plain([list(r) for r in self.spark.sql(starter).collect()])
        OUTPUTS["starter:running_total"] = rows
        self.assertEqual(rows, EXPECTED["windows"]["running_total"])
        self.assertEqual(self.frame_kinds("starter_running_total", starter), ["RangeFrame"])
        self.assertNotEqual(["RangeFrame"], EXPECTED["windows"]["frame_kinds"]["running_total"])

    @needs("ranking")
    def test_ranking_functions_disagree_at_the_tie(self):
        self.assertEqual(self.query("ranking")[1], EXPECTED["ranking"]["ranking"])

    @needs("top_per_plant")
    def test_top_machine_per_plant(self):
        self.assertEqual(self.query("top_per_plant")[1], EXPECTED["ranking"]["top_per_plant"])

    # ---- deduplication ---------------------------------------------------------------
    @needs("latest_inspection")
    def test_latest_inspection_with_tie_breaker_and_flag(self):
        self.assertEqual(self.query("latest_inspection_summary")[1], EXPECTED["dedup"]["latest_inspection"])
        counts = self.record("dedup_counts", ["raw_rows", "distinct_rows", "latest_rows"])
        self.assertEqual(counts, EXPECTED["dedup"]["counts"])

    # ---- gaps and islands ------------------------------------------------------------
    @needs("down_islands")
    def test_down_islands_split_by_gap_and_open_at_end(self):
        self.assertEqual(self.query("down_islands")[1], EXPECTED["islands"]["down_islands"])

    @needs("down_islands_naive")
    def test_naive_group_by_merges_islands_wrongly(self):
        _, rows = self.query("down_islands_naive")
        self.assertEqual(rows, EXPECTED["islands"]["down_islands_naive"])
        self.assertNotEqual(len(rows), len(EXPECTED["islands"]["down_islands"]), "the wrong approach must differ")

    # ---- membership ------------------------------------------------------------------
    @needs("semi_down_machines")
    def test_semi_join_keeps_each_machine_once(self):
        self.assertEqual(self.query("semi_down_machines")[1], EXPECTED["membership"]["semi_down_machines"])

    @needs("anti_no_output")
    def test_anti_join_finds_the_machine_without_output(self):
        self.assertEqual(self.query("anti_no_output")[1], EXPECTED["membership"]["anti_no_output"])

    @needs("never_inspected_not_exists")
    def test_never_inspected_with_not_exists(self):
        self.assertEqual(self.query("never_inspected_not_exists")[1],
                         EXPECTED["membership"]["never_inspected_not_exists"])

    @needs("never_inspected_anti_join")
    def test_never_inspected_with_left_anti_join(self):
        self.assertEqual(self.query("never_inspected_anti_join")[1],
                         EXPECTED["membership"]["never_inspected_anti_join"])

    @needs("never_inspected_not_in")
    def test_not_in_with_a_null_returns_nothing(self):
        self.assertEqual(self.query("never_inspected_not_in")[1], EXPECTED["membership"]["never_inspected_not_in"])

    @needs("join_cardinality")
    def test_inner_join_multiplies_where_semi_join_does_not(self):
        counts = self.record("join_cardinality", ["inner_join_rows", "semi_join_rows"])
        self.assertEqual(counts, EXPECTED["membership"]["join_cardinality"])

    # ---- set operators ---------------------------------------------------------------
    @needs("setops_union", "setops_union_all", "setops_intersect", "setops_except")
    def test_set_operators(self):
        e = EXPECTED["setops"]
        self.assertEqual(self.query("setops_union")[1], e["setops_union"])
        self.assertEqual(len(self.query("setops_union_all")[1]), e["setops_union_all_count"])
        self.assertEqual(self.query("setops_intersect")[1], e["setops_intersect"])
        self.assertEqual(self.query("setops_except")[1], e["setops_except"])

    @needs("setops_null_union", "setops_null_except", "setops_null_intersect")
    def test_set_operators_treat_null_as_one_value(self):
        e = EXPECTED["setops"]
        self.assertEqual(self.query("setops_null_union")[1], e["setops_null_union"])
        self.assertEqual(self.query("setops_null_except")[1], e["setops_null_except"])
        self.assertEqual(self.query("setops_null_intersect")[1], e["setops_null_intersect"])

    @needs("setops_positional")
    def test_positional_union_swaps_columns_without_error(self):
        self.assertEqual(self.query("setops_positional")[1], EXPECTED["setops"]["setops_positional"])

    @needs("union_int_and_text")
    def test_union_of_int_and_text_fails_under_ansi(self):
        self.expect_error("union_int_and_text", EXPECTED["dialect"]["error_classes"]["cast_invalid"])

    # ---- nested fields ---------------------------------------------------------------
    @needs("struct_fields")
    def test_struct_fields_read_by_path(self):
        self.assertEqual(self.query("struct_fields")[1], EXPECTED["nested"]["struct_fields"])

    @needs("array_fields")
    def test_array_fields_described_in_place(self):
        self.assertEqual(self.query("array_fields")[1], EXPECTED["nested"]["array_fields"])

    @needs("zero_based_index")
    def test_bracket_is_zero_based_and_element_at_one_based(self):
        self.assertEqual(self.query("zero_based_index")[1], EXPECTED["nested"]["zero_based_index"])

    @needs("defect_code_counts")
    def test_explode_counts_codes_across_inspections(self):
        self.assertEqual(self.query("defect_code_counts")[1], EXPECTED["nested"]["defect_code_counts"])

    @needs("explode_counts")
    def test_explode_drops_empty_arrays_and_outer_keeps_them(self):
        e = EXPECTED["nested"]
        counts = self.record("explode_counts", ["explode_rows", "explode_outer_rows"])
        self.assertEqual(counts, {"explode_rows": e["explode_rows"], "explode_outer_rows": e["explode_outer_rows"]})

    @needs("element_at_all_rows")
    def test_element_at_past_an_empty_array_raises(self):
        self.expect_error("element_at_all_rows", EXPECTED["dialect"]["error_classes"]["element_at_out_of_bounds"])

    @needs("bracket_all_rows")
    def test_bracket_index_past_an_empty_array_raises(self):
        self.expect_error("bracket_all_rows", EXPECTED["dialect"]["error_classes"]["bracket_index"])

    # ---- casts and nulls -------------------------------------------------------------
    @needs("try_cast_rows")
    def test_try_cast_rows(self):
        self.assertEqual(self.query("try_cast_rows")[1], EXPECTED["casts"]["try_cast_rows"])

    @needs("try_cast_aggregates")
    def test_try_cast_aggregates_skip_null(self):
        keys = ["sum_units", "measured", "rows", "unparseable", "avg_units", "avg_with_zero_fill"]
        self.assertEqual(self.record("try_cast_aggregates", keys), EXPECTED["casts"]["try_cast_aggregates"])

    @needs("try_cast_edge_cases")
    def test_try_cast_edge_cases(self):
        keys = ["padded", "decimal_text", "too_large", "impossible_date"]
        self.assertEqual(self.record("try_cast_edge_cases", keys), EXPECTED["casts"]["try_cast_edge_cases"])

    @needs("null_comparisons")
    def test_null_comparison_versus_null_safe_equality(self):
        counts = self.record("null_comparisons", ["not_equal_30", "not_null_safe_equal_30"])
        self.assertEqual(counts, EXPECTED["casts"]["null_comparisons"])

    @needs("strict_cast_units")
    def test_strict_cast_raises_where_try_cast_returns_null(self):
        self.expect_error("strict_cast_units", EXPECTED["dialect"]["error_classes"]["cast_invalid"])

    @needs("plain_division")
    def test_plain_division_by_zero_raises(self):
        self.expect_error("plain_division", EXPECTED["dialect"]["error_classes"]["divide_by_zero"])

    # ---- time ------------------------------------------------------------------------
    @needs("events_local")
    def test_events_in_new_york_wall_clock(self):
        self.assertEqual(self.query("events_local")[1], EXPECTED["time"]["events_local"])

    @needs("downtime_pairs")
    def test_downtime_elapsed_versus_wall_clock(self):
        self.assertEqual(self.query("downtime_pairs")[1], EXPECTED["time"]["downtime_pairs"])

    @needs("interval_subtraction")
    def test_timestamp_subtraction_reads_the_local_clock(self):
        _, rows = self.query("interval_subtraction")
        self.assertEqual(rows, [EXPECTED["time"]["interval_subtraction"]])

    @needs("dst_day_hours")
    def test_dst_day_has_23_elapsed_hours(self):
        self.assertEqual(self.query("dst_day_hours")[1], EXPECTED["time"]["dst_day_hours"])

    @needs("day_versus_24_hours")
    def test_one_day_later_is_not_24_hours_later(self):
        keys = ["start", "one_day_later", "twenty_four_hours_later"]
        self.assertEqual(self.record("day_versus_24_hours", keys), EXPECTED["time"]["day_versus_24_hours"])

    @needs("nonexistent_local_time")
    def test_gap_string_moves_forward_but_ntz_keeps_its_reading(self):
        keys = ["resolved", "ntz_reading"]
        self.assertEqual(self.record("nonexistent_local_time", keys), EXPECTED["time"]["nonexistent_local_time"])

    @needs("fall_back_hour")
    def test_fall_back_hour_runs_the_wall_clock_backwards(self):
        keys = ["stopped_local", "started_local", "elapsed_minutes", "wall_clock_minutes", "repeated_string_resolved"]
        self.assertEqual(self.record("fall_back_hour", keys), EXPECTED["time"]["fall_back_hour"])

    @needs("month_attribution")
    def test_month_attribution_differs_by_zone(self):
        self.assertEqual(self.query("month_attribution")[1], EXPECTED["time"]["month_attribution"])

    # ---- periods ---------------------------------------------------------------------
    @needs("month_end_arithmetic")
    def test_month_end_arithmetic(self):
        keys = ["jan31_plus_month", "feb28_plus_month", "feb28_plus_month_end", "feb28_plus_day",
                "datediff_mar1_feb28", "months_between_mar31_feb28"]
        self.assertEqual(self.record("month_end_arithmetic", keys), EXPECTED["periods"]["month_end_arithmetic"])

    @needs("incomplete_period")
    def test_incomplete_period_is_reported(self):
        self.assertEqual(self.query("incomplete_period")[1], EXPECTED["periods"]["incomplete_period"])

    # ---- source dialects -------------------------------------------------------------
    @needs("dialect_datediff")
    def test_datediff_forms_are_spark_rules_not_tsql(self):
        keys = ["spark_end_minus_start", "reversed", "unit_form", "unit_form_on_timestamps", "two_arg_on_timestamps"]
        self.assertEqual(self.record("dialect_datediff", keys), EXPECTED["dialect"]["datediff"])

    @needs("dialect_dateadd")
    def test_dateadd_returns_a_timestamp(self):
        schema, _ = self.query("dialect_dateadd")
        self.assertEqual(schema, "struct<next_day:" + EXPECTED["dialect"]["dateadd_result_type"] + ">")

    @needs("dialect_isnull", "dialect_getdate", "dialect_trunc_number", "dialect_qualify")
    def test_source_dialect_expressions_are_not_spark(self):
        e = EXPECTED["dialect"]["error_classes"]
        self.expect_error("dialect_isnull", e["isnull_two_args"])
        self.expect_error("dialect_getdate", e["getdate"])
        self.expect_error("dialect_trunc_number", e["trunc_number"])
        self.expect_error("dialect_qualify", e["qualify"])


class TransferTests(LabCase):
    """The same SQL over altered inputs or an altered session setting."""

    def tearDown(self):
        # Restore the reference views and settings whatever the test did.
        self.spark.sql(f"SET TIME ZONE '{SESSION_TIME_ZONE}'")
        self.spark.sql("SET spark.sql.ansi.enabled = true")
        register_views(self.spark, queries=self.queries)

    @needs("ranking")
    def test_an_added_row_creates_a_new_tie(self):
        rows = copy.deepcopy(FIXTURES["shift_output"])
        rows.append({"machine_id": "M4", "day": "2026-03-03", "shift": "D", "units": 30})
        register_views(self.spark, {"shift_output": rows}, queries=self.queries)
        _, out = self.query("ranking", "transfer:ranking_with_new_tie")
        self.assertEqual(out, EXPECTED["transfer"]["ranking_with_new_tie"])

    @needs("down_islands")
    def test_filling_the_gap_merges_two_islands(self):
        rows = copy.deepcopy(FIXTURES["machine_status"])
        rows.append({"machine_id": "M1", "day": "2026-03-07", "status": "DOWN"})
        register_views(self.spark, {"machine_status": rows}, queries=self.queries)
        _, out = self.query("down_islands", "transfer:down_islands_gap_filled")
        self.assertEqual(out, EXPECTED["transfer"]["down_islands_gap_filled"])

    @needs("downtime_pairs", "events_local", "interval_subtraction")
    def test_a_utc_session_gives_other_days_hours_and_minutes(self):
        self.spark.sql("SET TIME ZONE 'UTC'")
        self.assertEqual(self.spark.conf.get("spark.sql.session.timeZone"), "UTC")
        t = EXPECTED["time"]
        self.assertEqual(self.query("downtime_pairs", "transfer:downtime_pairs_utc")[1], t["downtime_pairs_utc_session"])
        self.assertEqual(self.query("events_local", "transfer:events_local_utc")[1], t["events_local_utc_session"])
        self.assertEqual(self.query("interval_subtraction", "transfer:interval_subtraction_utc")[1],
                         [t["interval_subtraction_utc_session"]])

    @needs("union_int_and_text", "strict_cast_units", "plain_division", "element_at_all_rows", "bracket_all_rows")
    def test_ansi_off_turns_the_same_errors_into_silent_values(self):
        self.spark.sql("SET spark.sql.ansi.enabled = false")
        self.assertEqual(self.spark.conf.get("spark.sql.ansi.enabled"), "false")
        a = EXPECTED["ansi"]
        schema, rows = self.query("union_int_and_text", "transfer:union_int_and_text_ansi_off")
        self.assertEqual(schema, a["union_int_and_text"]["schema"])
        values = sorted((r[0] for r in rows), key=lambda v: (v is not None, v))
        self.assertEqual(values, a["union_int_and_text"]["sorted_values"])
        for name in ("strict_cast_units", "plain_division", "element_at_all_rows", "bracket_all_rows"):
            self.assertEqual(self.query(name, f"transfer:{name}_ansi_off")[1], a[name], name)


def build_suite(defined: set[str] | None):
    """Every test for the reference run; with a learner file, only the tests its queries cover."""
    loader = unittest.defaultTestLoader
    suite, selected, left_out = unittest.TestSuite(), [], []
    for case in (PortfolioTests, TransferTests):
        for name in loader.getTestCaseNames(case):
            required = getattr(getattr(case, name), "needs", set())
            if defined is None or (REFERENCE_ONLY not in required and required <= defined):
                suite.addTest(case(name))
                selected.append(f"{case.__name__}.{name}")
            else:
                left_out.append(f"{case.__name__}.{name}")
    return suite, selected, left_out


def file_hashes(directory: str, suffixes=(".json", ".sql", ".py", ".csv", ".md", ".txt")) -> dict[str, str]:
    base = ROOT / directory
    return {
        str(p.relative_to(ROOT)).replace("\\", "/"): sha256(p.read_bytes()).hexdigest()
        for p in sorted(base.rglob("*"))
        if p.is_file() and p.suffix in suffixes and "__pycache__" not in p.parts
    }


def java_version() -> str:
    java_home = os.environ.get("JAVA_HOME")
    java_bin = str(Path(java_home) / "bin" / "java") if java_home else "java"
    try:
        text = subprocess.run([java_bin, "-version"], capture_output=True, text=True).stderr
    except OSError:
        return "unknown (java not found on JAVA_HOME or PATH)"
    return next((line.split('"')[1] for line in text.splitlines() if 'version "' in line), text.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--evidence", type=Path, help="write execution evidence JSON to this path")
    parser.add_argument("--portfolio", type=Path, help="a learner portfolio file; its blocks replace the reference")
    args = parser.parse_args()

    queries = load_queries(REFERENCE)
    defined = None
    portfolio_label = "solutions/portfolio.sql"
    if args.portfolio:
        path = args.portfolio if args.portfolio.is_absolute() else Path.cwd() / args.portfolio
        learner = load_queries(path)
        queries.update(learner)
        defined = set(learner)
        portfolio_label = str(args.portfolio).replace("\\", "/")
    suite, selected, left_out = build_suite(defined)
    if defined is not None:
        print(f"{portfolio_label} defines {len(defined)} queries; {len(selected)} tests check them, "
              f"{len(left_out)} tests need queries the file does not define and are not run.")

    started_at = datetime.now(timezone.utc)
    clock = time.monotonic()
    workdir = Path(tempfile.mkdtemp(prefix="lab-l12-"))
    spark = build_session(workdir)
    spark.sparkContext.setLogLevel("OFF")
    spark_config = {key: spark.conf.get(key) for key in (
        "spark.master", "spark.ui.enabled", "spark.sql.shuffle.partitions", "spark.sql.session.timeZone",
        "spark.sql.ansi.enabled", "spark.driver.bindAddress")}
    CONTEXT.update(spark=spark, queries=queries)
    try:
        try:
            register_views(spark, queries=queries)
        except Exception as exc:  # a learner's latest_inspection that does not run
            print("latest_inspections could not be created from latest_inspection:", str(exc).splitlines()[0])
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        spark_version = spark.version
    finally:
        spark.stop()
        shutil.rmtree(workdir, ignore_errors=True)
    finished_at = datetime.now(timezone.utc)

    import py4j  # noqa: E402
    import pyspark  # noqa: E402

    exit_code = 0 if result.wasSuccessful() and not result.skipped and result.testsRun == len(selected) else 1
    outcomes = {name: "ok" for name in selected}
    for test, _ in result.failures:
        outcomes[f"{type(test).__name__}.{test._testMethodName}"] = "failure"
    for test, _ in result.errors:
        outcomes[f"{type(test).__name__}.{getattr(test, '_testMethodName', str(test))}"] = "error"
    evidence = {
        "lab": "lab-l12-time-aware-sql",
        "executionClass": "local-executed",
        "runtime": "spark",
        "interpreter": sys.executable,
        "python": platform.python_version(),
        "java": java_version(),
        "packages": {"pyspark": pyspark.__version__, "py4j": py4j.__version__},
        "spark": spark_version,
        "sparkConfig": spark_config,
        "platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "portfolio": portfolio_label,
        "startedAt": started_at.isoformat(),
        "finishedAt": finished_at.isoformat(),
        "durationSeconds": round(time.monotonic() - clock, 3),
        "tests": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "exit": exit_code,
        "testOutcomes": outcomes,
        "testsNotSelected": left_out,
        "fixtureHashes": file_hashes("fixtures"),
        "expectedHashes": file_hashes("expected"),
        "solutionHashes": {**file_hashes("solutions"),
                           "run_tests.py": sha256((ROOT / "run_tests.py").read_bytes()).hexdigest()},
        "starterHashes": file_hashes("starters"),
        "outputHashes": {name: sha256(json.dumps(value, sort_keys=True).encode("utf-8")).hexdigest()
                         for name, value in sorted(OUTPUTS.items())},
        "sparkTempDirRemoved": not workdir.exists(),
        "commands": [" ".join([sys.executable] + sys.argv)],
        "notes": (
            "Local Apache Spark 4.0.4 (Spark SQL through PySpark) on one machine: master local[2], UI disabled, "
            "2 shuffle partitions, ANSI mode at its Spark 4 default (true), session time zone America/New_York set "
            "explicitly; two transfer tests switch to SET TIME ZONE 'UTC' and to spark.sql.ansi.enabled=false and "
            "restore both. Spark's local and warehouse directories live in a temporary directory that is deleted "
            "after the run. Nothing ran on Databricks; no network, warehouse, Delta table or cloud resource was used. "
            "Expected literals were authored by hand or by the standard-library derivation in expected/derive_time.py "
            "(DATA.md), never generated by the solution; error classes, frame kinds and the interval text layout were "
            "read off this build once and frozen. outputHashes are SHA-256 of the canonical JSON of each collected "
            "output."
        ),
    }
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    summary = {k: evidence[k] for k in ("portfolio", "spark", "python", "java", "tests", "failures", "errors",
                                        "skipped", "exit", "sparkTempDirRemoved")}
    print(json.dumps(summary, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
