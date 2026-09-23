"""Lab L02 runner: SQL and DataFrame equivalence on local Spark 4.0.4.

    /home/user/labenv/spark-env/bin/python run_tests.py --evidence evidence.json

Runs offline on one machine with local[2], the Spark UI disabled and two
shuffle partitions. Compares both implementations against authored literals
in expected/*.json. --evidence writes the JSON described in the lab brief.
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

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from solutions.compare import dtypes, positional_rows, same_schema, schema_differences, sorted_rows  # noqa: E402
from solutions.dataframe_pipeline import (dataframe_stages, known_plant_count as df_known_plant_count,  # noqa: E402
                                          known_plant_count_wrong, null_plant_events, null_plant_events_wrong,
                                          reason_column)
from solutions.schema import EVENT_COLUMNS, events_frame, plants_frame  # noqa: E402
from solutions.session import SPARK_CONFIG, local_session  # noqa: E402
from solutions.sql_pipeline import known_plant_count as sql_known_plant_count, null_plant_event_ids, sql_stages  # noqa: E402

LAB = "lab-l02-sql-pyspark-equivalence"
EXECUTION_CLASS = "local-executed"


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


EVENTS = load("fixtures/inspection_events.json")
PLANTS = load("fixtures/plants.json")
TRANSFER = load("fixtures/transfer_batch.json")
BASELINE = load("expected/baseline.json")   # authored by hand; see DATA.md
TRANSFER_EXPECTED = load("expected/transfer.json")
TYPES = load("expected/types.json")
OUTPUTS = {}


def canonical(value):
    return json.dumps(value, sort_keys=True, default=str).encode("utf-8")


def summarise(report_rows):
    return {"inspections": sum(r["inspections"] for r in report_rows),
            "inspected": sum(r["inspected"] for r in report_rows),
            "defective": sum(r["defective"] for r in report_rows)}


class EquivalenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spark = local_session()
        OUTPUTS["spark_version"] = cls.spark.version
        cls.events = events_frame(cls.spark, EVENTS)
        cls.plants = plants_frame(cls.spark, PLANTS)
        cls.sql = sql_stages(cls.spark, cls.events, cls.plants, prefix="base")
        cls.df = dataframe_stages(cls.events, cls.plants)

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()

    def both(self, stage):
        return (("sql", self.sql[stage]), ("dataframe", self.df[stage]))

    def test_declared_schema_and_delivery_counts(self):
        self.assertEqual(dtypes(self.events), TYPES["declared_event_dtypes"])
        self.assertEqual(dtypes(self.plants), TYPES["plant_dtypes"])
        counts = {}
        for language, distinct in self.both("distinct"):
            counts[language] = {"raw": self.events.count(), "distinct": distinct.count(),
                                "rejected": (self.sql if language == "sql" else self.df)["rejected"].count(),
                                "accepted": (self.sql if language == "sql" else self.df)["accepted"].count()}
            self.assertEqual(counts[language], BASELINE["counts"], language)
        self.assertTrue(same_schema(self.sql["distinct"], self.df["distinct"]), schema_differences(self.sql["distinct"], self.df["distinct"]))
        OUTPUTS["baseline_counts"] = counts

    def test_sql_and_dataframe_reject_the_same_rows_with_the_same_reasons(self):
        observed = {}
        for language, rejected in self.both("rejected"):
            rows = sorted_rows(rejected, "event_id")
            self.assertEqual([{"event_id": r["event_id"], "reason": r["reason"]} for r in rows], BASELINE["rejected"], language)
            histogram = {}
            for row in rows:
                histogram[row["reason"]] = histogram.get(row["reason"], 0) + 1
            self.assertEqual(histogram, BASELINE["rejected_by_reason"], language)
            self.assertEqual(dtypes(rejected), TYPES["rejected_dtypes"], language)
            observed[language] = rows
        self.assertTrue(same_schema(self.sql["rejected"], self.df["rejected"]), schema_differences(self.sql["rejected"], self.df["rejected"]))
        self.assertEqual(observed["sql"], observed["dataframe"])
        OUTPUTS["baseline_rejected"] = observed["sql"]

    def test_sql_and_dataframe_accept_the_same_rows_and_schema(self):
        observed = {}
        for language, accepted in self.both("accepted"):
            rows = sorted_rows(accepted, "event_id")
            self.assertEqual([r["event_id"] for r in rows], BASELINE["accepted_event_ids"], language)
            self.assertEqual(dtypes(accepted), TYPES["declared_event_dtypes"], language)
            observed[language] = rows
        self.assertTrue(same_schema(self.sql["accepted"], self.df["accepted"]), schema_differences(self.sql["accepted"], self.df["accepted"]))
        self.assertEqual(observed["sql"], observed["dataframe"])
        OUTPUTS["baseline_accepted"] = observed["sql"]

    def test_plant_report_rows_and_types_match_in_both_apis(self):
        observed = {}
        for language, report in self.both("report"):
            rows = sorted_rows(report, "plant_id")
            self.assertEqual(rows, BASELINE["report"], language)
            self.assertEqual(dtypes(report), TYPES["report_dtypes"], language)
            self.assertEqual(summarise(rows), BASELINE["grand_total"], language)
            observed[language] = {"rows": rows, "dtypes": dtypes(report)}
        self.assertTrue(same_schema(self.sql["report"], self.df["report"]), schema_differences(self.sql["report"], self.df["report"]))
        # The unknown plant P9 is kept with a null name: the left join is part of the contract.
        p9 = [r for r in observed["sql"]["rows"] if r["plant_id"] == "P9"][0]
        self.assertIsNone(p9["plant_name"])
        self.assertEqual(p9["inspected"], 10)
        OUTPUTS["baseline_report"] = observed

    def test_positional_comparison_breaks_when_input_order_differs(self):
        # Deliberate failure case: the same rows delivered in reverse order.
        forward = self.events.filter(reason_column().isNull())
        backward = events_frame(self.spark, list(reversed(EVENTS))).filter(reason_column().isNull())
        f_rows, b_rows = positional_rows(forward), positional_rows(backward)
        self.assertEqual(len(f_rows), BASELINE["order_case"]["valid_before_dedup"])
        self.assertEqual(len(b_rows), BASELINE["order_case"]["valid_before_dedup"])
        self.assertEqual(f_rows[0]["event_id"], BASELINE["order_case"]["first_valid_event_forward"])
        self.assertEqual(b_rows[0]["event_id"], BASELINE["order_case"]["first_valid_event_reversed"])
        with self.assertRaises(AssertionError) as naive:
            self.assertEqual(f_rows, b_rows)  # the check a learner writes first
        self.assertIn("ev-001", str(naive.exception))
        # Same multiset of rows: the relation is equal, the sequence is not.
        self.assertEqual(sorted(canonical(r) for r in f_rows), sorted(canonical(r) for r in b_rows))
        self.assertEqual(sorted_rows(forward, "event_id", "inspected_on"), sorted_rows(backward, "event_id", "inspected_on"))
        OUTPUTS["order_case"] = {"forward_first": f_rows[0]["event_id"], "backward_first": b_rows[0]["event_id"],
                                 "rows": len(f_rows), "positional_equal": f_rows == b_rows,
                                 "distinct_output_order_observed": [r["event_id"] for r in positional_rows(self.df["distinct"])]}

    def test_equals_none_is_not_is_null_until_corrected(self):
        sql_ids = null_plant_event_ids(self.spark, self.sql["views"])
        self.assertEqual(sql_ids, BASELINE["null_plant_event_ids"])
        wrong = null_plant_events_wrong(self.df["distinct"]).count()
        self.assertEqual(wrong, 0)                      # "= NULL" is unknown for every row
        self.assertNotEqual(wrong, len(sql_ids))        # the two APIs disagree until corrected
        corrected = [r["event_id"] for r in sorted_rows(null_plant_events(self.df["distinct"]), "event_id")]
        self.assertEqual(corrected, sql_ids)
        OUTPUTS["null_handling_is_null"] = {"sql_is_null": sql_ids, "dataframe_equals_none_rows": wrong, "dataframe_is_null": corrected}

    def test_distinct_count_includes_unknown_plant_until_the_contract_is_applied(self):
        sql_count = sql_known_plant_count(self.spark, self.sql["views"])
        wrong = known_plant_count_wrong(self.df["distinct"])
        self.assertEqual(sql_count, BASELINE["distinct_plant_ids_known"])
        self.assertEqual(wrong, BASELINE["distinct_plant_ids_including_unknown"])
        self.assertNotEqual(sql_count, wrong)
        self.assertEqual(df_known_plant_count(self.df["distinct"]), sql_count)
        OUTPUTS["null_handling_distinct_count"] = {"sql_count_distinct": sql_count, "dataframe_distinct_count": wrong,
                                                   "dataframe_with_contract": df_known_plant_count(self.df["distinct"])}

    def test_inferred_schema_differs_while_rows_look_equal(self):
        inferred = self.spark.read.json(str(ROOT / "fixtures/inspection_events.json"), multiLine=True)
        self.assertEqual(dtypes(inferred), TYPES["inferred_event_dtypes"])
        self.assertNotEqual(dtypes(inferred), dtypes(self.events))
        aligned = inferred.select(*EVENT_COLUMNS)
        self.assertFalse(same_schema(aligned, self.events))
        self.assertEqual(sorted_rows(aligned, "event_id", "plant_id"), sorted_rows(self.events, "event_id", "plant_id"))
        OUTPUTS["inferred_versus_declared"] = {"inferred": dtypes(inferred), "declared": dtypes(self.events),
                                               "differences_after_reorder": schema_differences(aligned, self.events)}

    def test_transfer_batch_changes_the_report_as_derived(self):
        events = events_frame(self.spark, EVENTS + TRANSFER)
        sql = sql_stages(self.spark, events, self.plants, prefix="transfer")
        df = dataframe_stages(events, self.plants)
        observed = {}
        for language, stages in (("sql", sql), ("dataframe", df)):
            counts = {"raw": events.count(), "distinct": stages["distinct"].count(),
                      "rejected": stages["rejected"].count(), "accepted": stages["accepted"].count()}
            self.assertEqual(counts, TRANSFER_EXPECTED["counts"], language)
            rejected = sorted_rows(stages["rejected"], "event_id")
            histogram = {}
            for row in rejected:
                histogram[row["reason"]] = histogram.get(row["reason"], 0) + 1
            self.assertEqual(histogram, TRANSFER_EXPECTED["rejected_by_reason"], language)
            new = [{"event_id": r["event_id"], "reason": r["reason"]} for r in rejected if r["event_id"] >= "ev-024"]
            self.assertEqual(new, TRANSFER_EXPECTED["new_rejected"], language)
            report = sorted_rows(stages["report"], "plant_id")
            self.assertEqual(report, TRANSFER_EXPECTED["report"], language)
            self.assertEqual(dtypes(stages["report"]), TYPES["report_dtypes"], language)
            self.assertEqual(summarise(report), TRANSFER_EXPECTED["grand_total"], language)
            observed[language] = {"counts": counts, "report": report}
        self.assertTrue(same_schema(sql["report"], df["report"]), schema_differences(sql["report"], df["report"]))
        self.assertEqual(null_plant_event_ids(self.spark, sql["views"]), TRANSFER_EXPECTED["null_plant_event_ids"])
        self.assertEqual([r["event_id"] for r in sorted_rows(null_plant_events(df["distinct"]), "event_id")],
                         TRANSFER_EXPECTED["null_plant_event_ids"])
        OUTPUTS["transfer"] = observed


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
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(EquivalenceTests)
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
        "notes": ("Local Apache Spark %s on one machine (local[2], UI off, 2 shuffle partitions); "
                  "no Databricks, Delta, network or external effect. Expected literals authored in DATA.md; "
                  "outputHashes are SHA-256 of the canonical JSON of each collected output."
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
