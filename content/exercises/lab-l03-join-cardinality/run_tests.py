"""Lab L03 runner: join cardinality on local Spark 4.0.4.

    /home/user/labenv/spark-env/bin/python run_tests.py --evidence evidence.json

Offline, one machine, local[2], UI off, two shuffle partitions. Both the
DataFrame API and Spark SQL are held to authored literals in expected/*.json.
"""
import sys

sys.dont_write_bytecode = True  # leave no __pycache__ inside the package

import argparse
import json
import os
import platform
import re
import subprocess
import time
import unittest
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from pyspark.sql import functions as F

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from solutions import joins, sql_joins  # noqa: E402
from solutions.compare import dtypes, same_schema, schema_differences, sorted_rows  # noqa: E402
from solutions.schema import PLANT_COLUMNS, inspections_frame, plants_frame  # noqa: E402
from solutions.session import SPARK_CONFIG, local_session  # noqa: E402

LAB = "lab-l03-join-cardinality"
EXECUTION_CLASS = "local-executed"
AVERAGE_TOLERANCE = 1e-12  # AVG sums doubles in engine order; see DATA.md


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


INSPECTIONS = load("fixtures/inspections.json")
PLANTS = load("fixtures/plants.json")
PLANTS_TRANSFER = load("fixtures/plants_transfer.json")
BASELINE = load("expected/baseline.json")     # authored by hand; see DATA.md
TRANSFER = load("expected/transfer.json")
TYPES = load("expected/types.json")
OUTPUTS = {}


def canonical(value):
    return json.dumps(value, sort_keys=True, default=str).encode("utf-8")


def region_rows(frame):
    return sorted_rows(frame, F.col("region").asc_nulls_first())


class Scenario:
    """One dimension fixture with its DataFrame and SQL views."""

    def __init__(self, spark, plant_records, prefix):
        self.inspections = inspections_frame(spark, INSPECTIONS)
        self.plants = plants_frame(spark, plant_records)
        self.current = joins.current_plants_by_window(self.plants)
        self.names = sql_joins.register(spark, self.inspections, self.plants, self.current, prefix)
        self.spark = spark

    def sql(self, template):
        return sql_joins.query(self.spark, template, self.names)


class JoinCardinalityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spark = local_session()
        OUTPUTS["spark_version"] = cls.spark.version
        cls.base = Scenario(cls.spark, PLANTS, "base")

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()

    # -- diagnosis -----------------------------------------------------------

    def check_diagnosis(self, scenario, expected, label):
        self.assertEqual(dtypes(scenario.inspections), TYPES["inspection_dtypes"])
        self.assertEqual(dtypes(scenario.plants), TYPES["plant_dtypes"])
        counts = {"inspections": scenario.inspections.count(), "plant_rows": scenario.plants.count(),
                  "current_plant_rows": scenario.current.count()}
        self.assertEqual(counts, expected["counts"], label)
        self.assertEqual(joins.totals(scenario.inspections), BASELINE["fact_totals"], label)
        df_dupes = sorted_rows(joins.duplicate_keys(scenario.plants), "plant_id")
        sql_dupes = sorted_rows(scenario.sql(sql_joins.DUPLICATE_KEYS_SQL), "plant_id")
        self.assertEqual(df_dupes, expected["duplicate_keys"], label)
        self.assertEqual(sql_dupes, expected["duplicate_keys"], label)
        return {"counts": counts, "duplicate_keys": df_dupes}

    def test_fixture_grain_and_duplicate_key_diagnosis(self):
        OUTPUTS["baseline_diagnosis"] = self.check_diagnosis(self.base, BASELINE, "baseline")

    # -- the plausible wrong total (deliberate failure case) ------------------

    def check_naive(self, scenario, expected, label):
        naive = joins.naive_join(scenario.inspections, scenario.plants)
        df_totals = joins.totals(naive)
        sql_totals = scenario.sql(sql_joins.NAIVE_TOTALS_SQL).first().asDict()
        wanted = {key: expected["naive_join"][key] for key in ("row_count", "inspected", "defective")}
        self.assertEqual(df_totals, wanted, label)
        self.assertEqual(sql_totals, wanted, label)
        # It is wrong for a stated reason: rows multiplied by duplicate keys, minus unmatched facts.
        self.assertNotEqual(df_totals["inspected"], BASELINE["fact_totals"]["inspected"], label)
        self.assertEqual(df_totals["row_count"],
                         BASELINE["fact_totals"]["row_count"] + expected["naive_join"]["extra_rows_from_duplicates"]
                         - expected["naive_join"]["rows_lost_to_unknown_plant"], label)
        rate = (naive.agg(F.sum("defective_units").alias("defective"), F.sum("inspected_units").alias("inspected"))
                .select(joins.rate("defective", "inspected")).first()[0])
        self.assertEqual(rate, expected["naive_join"]["defect_rate"], label)
        regions = sorted_rows(joins.by_region(naive), "region")
        self.assertEqual(regions, expected["naive_by_region"], label)
        current_regions = {row["region"] for row in sorted_rows(scenario.current, "plant_id")}
        phantom = sorted(row["region"] for row in regions if row["region"] not in current_regions)
        self.assertEqual(phantom, expected["regions_with_no_current_plant"], label)
        return {"naive_totals": df_totals, "naive_rate": rate, "naive_by_region": regions, "phantom_regions": phantom}

    def test_naive_join_produces_a_plausible_wrong_total(self):
        OUTPUTS["baseline_naive"] = self.check_naive(self.base, BASELINE, "baseline")

    def check_non_repairs(self, scenario, expected, label):
        agg_first = joins.aggregate_then_join(scenario.inspections, scenario.plants)
        agg_totals = joins.totals(agg_first)
        self.assertEqual(agg_totals, expected["aggregate_then_join_duplicated_dimension"], label)
        self.assertEqual(agg_totals["inspected"], expected["naive_join"]["inspected"], label)
        distinct_rows = joins.naive_join(scenario.inspections, scenario.plants).distinct().count()
        self.assertEqual(distinct_rows, expected["distinct_on_naive_join"]["row_count"], label)
        return {"aggregate_then_join": agg_totals, "distinct_on_naive_join_rows": distinct_rows}

    def test_aggregate_first_and_distinct_do_not_repair_a_duplicated_dimension(self):
        OUTPUTS["baseline_non_repairs"] = self.check_non_repairs(self.base, BASELINE, "baseline")

    # -- the repair -----------------------------------------------------------

    def check_repair(self, scenario, plant_records, expected, label):
        by_window = sorted_rows(scenario.current, "plant_id")
        self.assertEqual(by_window, expected["current_plants"], label)
        self.assertEqual(dtypes(scenario.current), TYPES["plant_dtypes"], label)
        self.assertFalse(joins.has_ties(scenario.plants), label)   # precondition for max_by
        by_aggregate = sorted_rows(joins.current_plants_by_aggregate(scenario.plants).select(*PLANT_COLUMNS), "plant_id")
        self.assertEqual(by_aggregate, by_window, label)
        by_sql = sorted_rows(scenario.sql(sql_joins.CURRENT_PLANTS_SQL), "plant_id")
        by_sql_aggregate = sorted_rows(scenario.sql(sql_joins.CURRENT_PLANTS_AGGREGATE_SQL).select(*PLANT_COLUMNS), "plant_id")
        self.assertEqual(by_sql, by_window, label)
        self.assertEqual(by_sql_aggregate, by_window, label)
        self.assertTrue(same_schema(scenario.current, scenario.sql(sql_joins.CURRENT_PLANTS_SQL)),
                        schema_differences(scenario.current, scenario.sql(sql_joins.CURRENT_PLANTS_SQL)))
        # The rule is order-independent: the same versions delivered in reverse give the same current rows.
        reversed_plants = plants_frame(self.spark, list(reversed(plant_records)))
        self.assertEqual(sorted_rows(joins.current_plants_by_window(reversed_plants), "plant_id"), by_window, label)
        # dropDuplicates without a rule is recorded, never asserted: Spark promises nothing about which row survives.
        arbitrary = sorted_rows(scenario.plants.dropDuplicates(["plant_id"]), "plant_id")
        return {"current_plants": by_window, "drop_duplicates_observed_not_asserted": arbitrary}

    def test_explicit_rule_restores_the_dimension_grain(self):
        OUTPUTS["baseline_repair"] = self.check_repair(self.base, PLANTS, BASELINE, "baseline")

    def check_fixed_joins(self, scenario, expected, label):
        inner = joins.matched_join(scenario.inspections, scenario.current, "inner")
        left = joins.matched_join(scenario.inspections, scenario.current, "left")
        inner_totals, left_totals = joins.totals(inner), joins.totals(left)
        want_inner = {key: expected["fixed_inner_join"][key] for key in ("row_count", "inspected", "defective")}
        want_left = {key: expected["fixed_left_join"][key] for key in ("row_count", "inspected", "defective")}
        self.assertEqual(inner_totals, want_inner, label)
        self.assertEqual(left_totals, want_left, label)
        self.assertEqual(left_totals, BASELINE["fact_totals"], label)   # a left join loses no fact
        named = left.filter(F.col("plant_name").isNotNull()).count()
        self.assertEqual(named, expected["fixed_left_join"]["rows_with_plant_name"], label)
        self.assertEqual(left.agg(F.count("plant_name")).first()[0], named, label)
        unmatched = [r["inspection_id"] for r in sorted_rows(joins.unmatched_inspections(scenario.inspections, scenario.current), "inspection_id")]
        self.assertEqual(unmatched, expected["fixed_left_join"]["unmatched_inspection_ids"], label)
        self.assertEqual(inner_totals["row_count"] + len(unmatched), left_totals["row_count"], label)
        return {"inner": inner_totals, "left": left_totals, "rows_with_plant_name": named, "unmatched": unmatched}

    def test_fixed_inner_and_left_joins_match_derived_totals(self):
        OUTPUTS["baseline_fixed_joins"] = self.check_fixed_joins(self.base, BASELINE, "baseline")

    def check_region_report(self, scenario, expected, label):
        df_report = joins.region_report(scenario.inspections, scenario.current)
        sql_report = scenario.sql(sql_joins.REGION_REPORT_SQL)
        df_rows, sql_rows = region_rows(df_report), region_rows(sql_report)
        self.assertEqual(df_rows, expected["region_report"], label)
        self.assertEqual(sql_rows, expected["region_report"], label)
        self.assertEqual(dtypes(df_report), TYPES["region_report_dtypes"], label)
        self.assertTrue(same_schema(df_report, sql_report), schema_differences(df_report, sql_report))
        self.assertEqual(sum(r["inspections"] for r in df_rows), BASELINE["fact_totals"]["row_count"], label)
        return df_rows

    def test_region_report_sql_and_dataframe_agree_with_types(self):
        OUTPUTS["baseline_region_report"] = self.check_region_report(self.base, BASELINE, "baseline")

    # -- the left-join null-count trap ----------------------------------------

    def check_plant_counts(self, scenario, expected, label):
        df_counts = joins.plants_with_counts(scenario.current, scenario.inspections)
        sql_counts = scenario.sql(sql_joins.PLANT_COUNTS_SQL)
        df_rows, sql_rows = sorted_rows(df_counts, "plant_id"), sorted_rows(sql_counts, "plant_id")
        self.assertEqual(df_rows, expected["plants_with_counts"], label)
        self.assertEqual(sql_rows, expected["plants_with_counts"], label)
        self.assertEqual(dtypes(df_counts), TYPES["plant_counts_dtypes"], label)
        self.assertTrue(same_schema(df_counts, sql_counts), schema_differences(df_counts, sql_counts))
        empty = [r["plant_id"] for r in df_rows if r["inspection_count"] == 0]
        self.assertEqual(empty, expected["plants_without_inspections"], label)
        for row in df_rows:
            if row["plant_id"] in empty:
                self.assertEqual(row["row_count"], 1, label)          # the null row is counted by COUNT(*)
                self.assertIsNone(row["inspected_sum"], label)        # SUM over nothing is NULL
                self.assertEqual(row["inspected"], 0, label)          # COALESCE makes the policy explicit
        trap = {"count_star_total": sum(r["row_count"] for r in df_rows),
                "count_inspection_id_total": sum(r["inspection_count"] for r in df_rows)}
        self.assertEqual(trap, expected["naive_plant_count_trap"], label)
        self.assertNotEqual(trap["count_star_total"], trap["count_inspection_id_total"], label)
        return {"rows": df_rows, "trap": trap}

    def test_left_join_null_count_trap_for_plants_without_inspections(self):
        OUTPUTS["baseline_plant_counts"] = self.check_plant_counts(self.base, BASELINE, "baseline")

    # -- the weighted metric --------------------------------------------------

    def test_weighted_rate_is_not_the_average_of_rates(self):
        df_rates = joins.weighted_and_averaged(self.base.inspections)
        sql_rates = self.base.sql(sql_joins.RATES_SQL)
        self.assertEqual(dtypes(df_rates), TYPES["rates_dtypes"])
        self.assertTrue(same_schema(df_rates, sql_rates), schema_differences(df_rates, sql_rates))
        observed = {}
        for language, frame in (("dataframe", df_rates), ("sql", sql_rates)):
            rows = sorted_rows(frame, "plant_id")
            self.assertEqual([r["plant_id"] for r in rows], [r["plant_id"] for r in BASELINE["rates"]], language)
            for actual, expected in zip(rows, BASELINE["rates"]):
                self.assertEqual(actual["weighted_rate"], expected["weighted_rate"], (language, actual["plant_id"]))
                self.assertAlmostEqual(actual["average_of_rates"], expected["average_of_rates"], delta=AVERAGE_TOLERANCE,
                                       msg=(language, actual["plant_id"]))
                self.assertEqual(actual["rate_rows"], expected["rate_rows"], (language, actual["plant_id"]))
                self.assertEqual(actual["row_count"], expected["row_count"], (language, actual["plant_id"]))
            observed[language] = rows
        by_plant = {r["plant_id"]: r for r in observed["dataframe"]}
        # The two metrics disagree wherever inspections differ in size...
        for plant in ("P1", "P2", "P3", "P9"):
            self.assertNotAlmostEqual(by_plant[plant]["weighted_rate"], by_plant[plant]["average_of_rates"], delta=1e-9, msg=plant)
        # ...and P2's average silently covers 4 of 5 inspections because 0/0 is NULL under try_divide.
        self.assertEqual(by_plant["P2"]["rate_rows"], 4)
        self.assertEqual(by_plant["P2"]["row_count"], 5)
        OUTPUTS["baseline_rates"] = observed

    # -- transfer: a different duplicate pattern -------------------------------

    def test_transfer_dimension_with_a_different_duplicate_pattern(self):
        scenario = Scenario(self.spark, PLANTS_TRANSFER, "transfer")
        OUTPUTS["transfer"] = {
            "diagnosis": self.check_diagnosis(scenario, TRANSFER, "transfer"),
            "naive": self.check_naive(scenario, TRANSFER, "transfer"),
            "non_repairs": self.check_non_repairs(scenario, TRANSFER, "transfer"),
            "repair": self.check_repair(scenario, PLANTS_TRANSFER, TRANSFER, "transfer"),
            "fixed_joins": self.check_fixed_joins(scenario, TRANSFER, "transfer"),
            "region_report": self.check_region_report(scenario, TRANSFER, "transfer"),
            "plant_counts": self.check_plant_counts(scenario, TRANSFER, "transfer"),
        }
        # The symptom that helped on the baseline (a region no current plant has) is absent here.
        self.assertEqual(OUTPUTS["transfer"]["naive"]["phantom_regions"], [])
        self.assertNotEqual(OUTPUTS["transfer"]["diagnosis"]["duplicate_keys"], BASELINE["duplicate_keys"])


def file_hashes(directory, suffixes=(".json", ".csv", ".py", ".sql")):
    return {str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path.read_bytes()).hexdigest()
            for path in sorted((ROOT / directory).rglob("*")) if path.is_file() and path.suffix in suffixes}


def java_version():
    home = os.environ.get("JAVA_HOME")
    java = str(Path(home) / "bin" / ("java.exe" if os.name == "nt" else "java")) if home else "java"
    try:
        text = subprocess.run([java, "-version"], capture_output=True, text=True).stderr
    except OSError as error:
        return "unavailable: %s" % error
    match = re.search(r'version "([^"]+)"', text)
    return match.group(1) if match else text.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--evidence", type=Path, help="write evidence JSON to this path")
    parser.add_argument("--outputs", type=Path, help="also write every collected output to this JSON path")
    args = parser.parse_args()
    import py4j
    import pyspark
    started = datetime.now(timezone.utc)
    clock = time.monotonic()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(JoinCardinalityTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    finished = datetime.now(timezone.utc)
    exit_code = 0 if result.wasSuccessful() and result.testsRun > 0 and not result.skipped else 1
    evidence = {
        "lab": LAB, "executionClass": EXECUTION_CLASS,
        "python": platform.python_version(), "java": java_version(),
        "packages": {"pyspark": pyspark.__version__, "py4j": py4j.__version__},
        "spark": OUTPUTS.get("spark_version", "not started"),
        "sparkConfig": dict(SPARK_CONFIG, master="local[2]"),
        "platform": "%s %s (%s)" % (platform.system(), platform.release(), platform.machine()),
        "startedAt": started.isoformat(), "finishedAt": finished.isoformat(),
        "durationSeconds": round(time.monotonic() - clock, 3),
        "tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "skipped": len(result.skipped), "exit": exit_code,
        "fixtureHashes": file_hashes("fixtures"),
        "expectedHashes": file_hashes("expected"),
        "solutionHashes": dict(file_hashes("solutions"), **{"run_tests.py": sha256((ROOT / "run_tests.py").read_bytes()).hexdigest()}),
        "outputHashes": {name: sha256(canonical(value)).hexdigest() for name, value in sorted(OUTPUTS.items())},
        "commands": [" ".join([sys.executable] + sys.argv)],
        "notes": ("Local Apache Spark %s on one machine (local[2], UI off, 2 shuffle partitions, ANSI mode default); "
                  "no Databricks, Delta, network or external effect. Expected literals authored in DATA.md; the "
                  "average-of-rates values are compared within 1e-12 for the reason given there; outputHashes are "
                  "SHA-256 of the canonical JSON of each collected output."
                  % OUTPUTS.get("spark_version", "?")),
    }
    if args.outputs:
        args.outputs.parent.mkdir(parents=True, exist_ok=True)
        args.outputs.write_text(json.dumps(OUTPUTS, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: evidence[key] for key in ("lab", "python", "java", "spark", "tests", "failures", "errors", "skipped", "exit")}, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
