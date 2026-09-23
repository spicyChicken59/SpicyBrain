"""Lab L11 runner: a star model and one metric contract on local Spark 4.0.4.

    python run_tests.py --evidence evidence.json   (Python 3.12 with requirements.txt installed)

Offline, one machine, local[2], UI off, two shuffle partitions, ANSI mode at its
Spark 4 default. Every output is compared with literals authored by hand in
expected/*.json (derivations in DATA.md); no expected value is produced by the
code under test. The same checks run on the baseline fixtures and on an altered
transfer set; a mutated dimension and incomplete contracts must fail for their
stated reasons.
"""
import sys

sys.dont_write_bytecode = True  # leave no __pycache__ inside the package

import argparse
import copy
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

from solutions import contract as metric_contract  # noqa: E402
from solutions.model import Model, load_rows  # noqa: E402
from solutions.session import SPARK_CONFIG, LocalSpark  # noqa: E402

LAB = "lab-l11-modeling-metrics"
EXECUTION_CLASS = "local-executed"
AVERAGE_TOLERANCE = 1e-12  # AVG adds doubles in engine order; see DATA.md
CONTRACT = load_rows(ROOT / "fixtures" / "metric_contract.json")
OUTPUTS = {}
SESSION = {}
SQL = {"path": ROOT / "solutions" / "model.sql"}  # --sql starters/model.sql tests a learner's file


def spark():
    if "local" not in SESSION:
        SESSION["local"] = LocalSpark()
        OUTPUTS["spark_version"] = SESSION["local"].spark.version
    return SESSION["local"].spark


def fraction(pair):
    return None if pair is None else pair[0] / pair[1]


def canonical(value):
    return json.dumps(value, sort_keys=True, default=str).encode("utf-8")


class ModelChecks:
    """Checks shared by the baseline and the transfer fixture sets."""

    SCENARIO = None

    @classmethod
    def setUpClass(cls):
        cls.expected = load_rows(ROOT / "expected" / ("%s.json" % cls.SCENARIO))
        cls.params = metric_contract.parameters(CONTRACT)
        cls.model = Model(spark(), ROOT / "fixtures" / cls.SCENARIO, cls.params, sql_path=SQL["path"]).register()
        cls.model.register_reports()

    def record(self, name, value):
        OUTPUTS["%s_%s" % (self.SCENARIO, name)] = value
        return value

    def assertRowsEqual(self, actual, expected, label):
        """Every field equal; a rate equals its authored fraction exactly, or is None."""
        self.assertEqual(len(actual), len(expected), label)
        for got, want in zip(actual, expected):
            plain = {k: v for k, v in want.items() if k != "rate"}
            self.assertEqual({k: got[k] for k in plain}, plain, label)
            if "rate" in want:
                if want["rate"] is None:
                    self.assertIsNone(got["rate"], (label, plain))
                else:
                    self.assertEqual(got["rate"], fraction(want["rate"]), (label, plain))

    # -- 1. grain, keys and conformed dimensions ------------------------------

    def test_01_grain_keys_and_conformed_dimensions(self):
        e, m = self.expected, self.model
        counts = {view: m.table(view).count() for view in ("silver_inspections", "fact_inspection", "quarantine")}
        self.assertEqual(counts, e["counts"])
        checks = {"duplicate_inspection_ids": m.column("check_duplicate_inspection_ids"),
                  "overlapping_versions": m.column("check_overlapping_versions"),
                  "lines_without_one_current_row": m.column("check_current_rows"),
                  "duplicate_surrogate_keys": m.column("check_duplicate_surrogate_keys")}
        self.assertEqual(checks, e["model_checks"])
        orphans = {"line": m.column("orphans_line"), "shift": m.column("orphans_shift"),
                   "date": m.column("orphans_date"), "unit": [r["inspection_id"] for r in m.rows("quarantine")]}
        self.assertEqual(orphans, e["orphans"])
        self.assertEqual(m.rows("quarantine"), e["quarantine"])
        # The point-in-time join is many-to-one: no inspection appears twice in the fact.
        self.assertEqual(m.column("fact_duplicates"), [])
        totals = m.rows("fact_totals")[0]
        self.assertEqual(totals["rows"], e["counts"]["fact_inspection"])
        self.assertEqual({k: totals[k] for k in ("inspected_pieces", "defective_pieces")}, e["fact_totals"])
        self.record("model", {"counts": counts, "checks": checks, "orphans": orphans, "totals": totals})

    # -- 2. one metric, three grains -------------------------------------------

    def test_02_three_grain_reconciliation(self):
        e, m = self.expected, self.model
        line_day, plant_day, plant_month = m.rows("line_day"), m.rows("plant_day"), m.rows("plant_month")
        self.assertRowsEqual(line_day, e["line_day"], "line_day")
        self.assertRowsEqual(plant_day, e["plant_day"], "plant_day")
        self.assertRowsEqual(plant_month, e["plant_month"], "plant_month")
        parts = ("inspections", "inspected_pieces", "defective_pieces")
        # Reconcile the additive parts across grains from the collected rows themselves.
        for row in plant_day:
            children = [r for r in line_day if r["plant_id"] == row["plant_id"] and r["business_date"] == row["business_date"]]
            self.assertTrue(children, row)
            for part in parts:
                self.assertEqual(sum(r[part] for r in children), row[part], (row, part))
        for row in plant_month:
            children = [r for r in plant_day if r["plant_id"] == row["plant_id"] and r["business_date"][:7] == row["month"]]
            for part in parts:
                self.assertEqual(sum(r[part] for r in children), row[part], (row, part))
        for part in ("inspected_pieces", "defective_pieces"):
            self.assertEqual(sum(r[part] for r in plant_month), e["fact_totals"][part], part)
        self.assertEqual(sum(r["inspections"] for r in plant_month), e["counts"]["fact_inspection"])
        # The day boundary: a night shift that crosses midnight is split by the business-day rule.
        wanted = {b["inspection_id"]: b for b in e["boundary"]}
        boundary = [r for r in m.rows("boundary") if r["inspection_id"] in wanted]
        self.assertEqual(boundary, e["boundary"])
        self.assertEqual(len({b["shift_id"] for b in boundary}), 1)
        self.assertEqual(len({b["business_date"] for b in boundary}), 2)
        self.record("grains", {"line_day": line_day, "plant_day": plant_day, "plant_month": plant_month, "boundary": boundary})

    # -- 3. rates do not add --------------------------------------------------

    def test_03_rates_do_not_add(self):
        e, m = self.expected["additivity"], self.model
        lp = e["line_to_plant"]
        row = [r for r in m.rows("average_of_line_rates")
               if r["plant_id"] == lp["plant_id"] and r["business_date"] == lp["business_date"]][0]
        self.assertAlmostEqual(row["average_of_line_rates"], lp["average_of_line_rates"], delta=AVERAGE_TOLERANCE)
        self.assertEqual(row["rated_lines"], lp["rated_lines"])
        plant = [r for r in m.rows("plant_day")
                 if r["plant_id"] == lp["plant_id"] and r["business_date"] == lp["business_date"]][0]
        self.assertEqual(plant["rate"], fraction(lp["plant_rate"]))
        self.assertGreater(abs(row["average_of_line_rates"] - plant["rate"]), 1e-6)
        dm = e["day_to_month"]
        month_avg = [r for r in m.rows("average_of_day_rates")
                     if r["plant_id"] == dm["plant_id"] and r["month"] == dm["month"]][0]
        self.assertAlmostEqual(month_avg["average_of_day_rates"], dm["average_of_day_rates"], delta=AVERAGE_TOLERANCE)
        self.assertEqual(month_avg["rated_days"], dm["rated_days"])
        month = [r for r in m.rows("plant_month") if r["plant_id"] == dm["plant_id"] and r["month"] == dm["month"]][0]
        self.assertEqual(month["rate"], fraction(dm["month_rate"]))
        self.assertGreater(abs(month_avg["average_of_day_rates"] - month["rate"]), 1e-6)
        self.record("additivity", {"line_to_plant": row, "plant_rate": plant["rate"], "day_to_month": month_avg, "month_rate": month["rate"]})

    # -- 4. an invalid denominator (deliberate failure case) --------------------

    def test_04_zero_denominator_gives_no_rate(self):
        e, m = self.expected["zero_denominator"], self.model
        with self.assertRaises(Exception) as caught:
            m.frame("naive_division_line_day").collect()
        condition = caught.exception.getCondition() if hasattr(caught.exception, "getCondition") else None
        self.assertEqual(condition, e["naive_error_condition"])
        line_day = m.rows("line_day")
        by_status = {s: [[r["business_date"], r["line_id"]] for r in line_day if r["status"] == s]
                     for s in (self.params["zero_status"], self.params["empty_status"])}
        self.assertEqual(by_status[self.params["zero_status"]], e["no_units"])
        self.assertEqual(by_status[self.params["empty_status"]], e["no_inspections"])
        for r in line_day:
            if r["status"] != "ok":
                self.assertIsNone(r["rate"], r)          # no rate, never 0 and never an error
        zero = [[r["business_date"], r["line_id"]] for r in line_day if r["rate"] == 0.0]
        self.assertEqual(zero, e["zero_rate"])          # a real zero is a value, not a missing rate
        self.record("zero_denominator", {"condition": condition, "statuses": by_status, "zero_rate": zero})

    # -- 5. a unit mismatch (deliberate failure case) ----------------------------

    def test_05_units_are_converted_before_summing(self):
        e, m = self.expected["units"], self.model
        naive = m.rows("naive_units_plant_day")
        self.assertRowsEqual(naive, e["naive_plant_day"], "naive_plant_day")
        naive_lines = [r for r in m.rows("naive_units_line_day") if r["line_id"] in e["naive_line_day_lines"]]
        self.assertRowsEqual(naive_lines, e["naive_line_day"], "naive_line_day")
        contract_rows = {(r["business_date"], r["plant_id"]): r for r in m.rows("plant_day")}
        differs, hidden = [], []
        for r in naive:
            c = contract_rows[(r["business_date"], r["plant_id"])]
            if r["rate"] != c["rate"]:
                differs.append([r["business_date"], r["plant_id"]])
            elif (r["inspected_qty"], r["defective_qty"]) != (c["inspected_pieces"], c["defective_pieces"]):
                hidden.append([r["business_date"], r["plant_id"]])
        self.assertEqual(differs, e["plant_day_rate_differs"])
        self.assertEqual(hidden, e["plant_day_sums_differ_rate_equal"])
        # Within one line and one unit a ratio is unit-free, so the line-day rate hides the
        # mismatch; it shows only where a quarantined unit was summed in anyway.
        quarantined = {(r["inspection_id"], r["line_id"]) for r in m.rows("quarantine")}
        silver = {r["inspection_id"]: r for r in m.rows("silver_dated")}
        mixed = {(silver[i]["business_date"], line) for i, line in quarantined}
        line_rates = {(r["business_date"], r["line_id"]): r["rate"] for r in m.rows("line_day")}
        for r in naive_lines:
            key = (r["business_date"], r["line_id"])
            if key in mixed:
                self.assertNotEqual(r["rate"], line_rates[key], key)
            else:
                self.assertEqual(r["rate"], line_rates[key], key)
        self.record("units", {"naive_plant_day": naive, "naive_line_day": naive_lines, "differs": differs, "hidden": hidden})

    # -- 6. a missing dimension key (deliberate failure case) ---------------------

    def test_06_missing_dimension_key_is_kept_under_the_unknown_member(self):
        e, m = self.expected["missing_key"], self.model
        self.assertEqual(m.column("orphans_line"), e["orphan_ids"])
        inner = m.rows("inner_join_totals")[0]
        self.assertEqual(inner, e["inner_join"])
        unknown = [r for r in m.rows("plant_day") if r["plant_id"] == self.params["unknown_plant_id"]]
        lost = {part: self.expected["fact_totals"][part] - inner[part] for part in ("inspected_pieces", "defective_pieces")}
        self.assertEqual(lost, {part: sum(r[part] for r in unknown) for part in lost})  # exactly the orphans
        left = m.rows("left_join_by_plant")
        self.assertEqual(left, e["left_join_by_plant"])
        null_group = [r for r in left if r["plant_id"] is None][0]
        self.assertEqual(null_group["inspected_pieces"], sum(r["inspected_pieces"] for r in unknown))
        self.record("missing_key", {"inner": inner, "left": left, "unknown_rows": unknown})

    # -- 7. a double count through a many-to-many join (deliberate failure case) --

    def test_07_history_joined_on_its_natural_key_double_counts(self):
        e, m = self.expected["many_to_many"], self.model
        rows = m.rows("history_join_rows")[0]["rows"]
        self.assertEqual(rows, e["rows"])
        by_plant, by_supervisor = m.rows("history_join_by_plant"), m.rows("history_join_by_supervisor")
        self.assertEqual(by_plant, e["by_plant"])
        self.assertEqual(by_supervisor, e["by_supervisor"])
        as_was, as_is = m.rows("supervisor_as_was"), m.rows("supervisor_as_is")
        self.assertEqual(as_was, e["as_was"])
        self.assertEqual(as_is, e["as_is"])
        facts = self.expected["counts"]["fact_inspection"]
        for reading in (as_was, as_is):                     # both readings keep every fact exactly once
            self.assertEqual(sum(r["rows"] for r in reading), facts)
            self.assertEqual(sum(r["inspected_pieces"] for r in reading), self.expected["fact_totals"]["inspected_pieces"])
        self.assertGreater(sum(r["inspected_pieces"] for r in by_supervisor), self.expected["fact_totals"]["inspected_pieces"])
        self.assertNotEqual(as_was, as_is)                  # type 2 and type 1 attribute differently
        self.record("many_to_many", {"rows": rows, "by_plant": by_plant, "by_supervisor": by_supervisor,
                                     "as_was": as_was, "as_is": as_is})

    # -- 8. a business-day versus calendar-day window (deliberate failure case) ----

    def test_08_business_day_window_is_not_a_calendar_window(self):
        e, m = self.expected["window"], self.model
        self.assertEqual(self.model.params["as_of"].isoformat(), e["as_of"])
        self.assertEqual(self.params["window_days"], e["length"])
        observed = {}
        for kind in ("business", "calendar", "weekday"):
            dates, business_days, totals = m.window(kind)
            self.assertEqual(dates, e[kind]["dates"], kind)
            self.assertRowsEqual(totals, e[kind]["rows"], kind)
            observed[kind] = {"dates": dates, "business_days": business_days, "rows": totals}
        self.assertEqual(observed["business"]["business_days"], e["length"])
        self.assertEqual(observed["calendar"]["business_days"], e["calendar"]["business_days_in_window"])
        self.assertLess(observed["calendar"]["business_days"], e["length"])
        self.assertNotEqual(observed["business"]["rows"], observed["calendar"]["rows"])
        self.record("window", observed)


class BaselineTests(ModelChecks, unittest.TestCase):
    SCENARIO = "baseline"

    def test_09_overlapping_history_is_caught_before_it_inflates_the_fact(self):
        """A deliberately broken dimension: version 101 of N1 overlaps version 102 on 2026-03-30."""
        broken_spec = self.expected["broken_history"]
        lines = copy.deepcopy(load_rows(ROOT / "fixtures" / "baseline" / "dim_line.json"))
        for line in lines:
            if line["line_sk"] == 101:
                line["valid_to"] = "2026-03-31"
        broken = Model(spark(), ROOT / "fixtures" / "baseline", self.params, overrides={"dim_line": lines},
                       sql_path=SQL["path"]).register()
        try:
            self.assertEqual(broken.column("check_overlapping_versions"), broken_spec["overlapping_versions"])
            self.assertEqual(broken.frame("fact_inspection").count(), broken_spec["fact_rows"])
            self.assertEqual(broken.column("fact_duplicates"), broken_spec["duplicated_inspection_ids"])
            totals = broken.rows("fact_totals")[0]
            self.assertEqual({k: totals[k] for k in ("inspected_pieces", "defective_pieces")}, broken_spec["fact_totals"])
            self.assertNotEqual(totals["inspected_pieces"], self.expected["fact_totals"]["inspected_pieces"])
            self.record("broken_history", {"overlaps": broken_spec["overlapping_versions"], "totals": totals})
        finally:
            self.model.register()                            # restore the clean baseline views
            self.model.register_reports()


class TransferTests(ModelChecks, unittest.TestCase):
    SCENARIO = "transfer"

    def test_09_transfer_exposes_what_the_baseline_could_not(self):
        m = self.model
        self.assertEqual([r["inspection_id"] for r in m.rows("quarantine")], ["T-10"])
        business, _, _ = m.window("business")
        weekday, _, _ = m.window("weekday")
        self.assertNotEqual(business, weekday)               # the shutdown day separates them here
        s2 = {r["business_date"]: r["supervisor"] for r in m.rows("line_day") if r["line_id"] == "S2"}
        self.assertEqual(s2["2026-04-29"], "J. Castillo")    # the day before the change
        self.assertEqual(s2["2026-04-30"], "E. Haddad")      # valid_from is inclusive, valid_to exclusive
        self.record("transfer_only", {"business": business, "weekday": weekday, "s2_supervisors": s2})


class ContractTests(unittest.TestCase):
    def test_contract_is_complete_and_drives_the_parameters(self):
        self.assertEqual(metric_contract.problems(CONTRACT), [])
        self.assertEqual(metric_contract.parameters(CONTRACT), {
            "window_days": 3, "unknown_line_sk": -1, "unknown_plant_id": "UNKNOWN",
            "zero_status": "no_units", "empty_status": "no_inspections"})
        OUTPUTS["contract_parameters"] = metric_contract.parameters(CONTRACT)

    def test_incomplete_contracts_are_refused_for_the_stated_reason(self):
        cases = []
        missing = copy.deepcopy(CONTRACT)
        del missing["denominator"]
        cases.append((missing, ["missing denominator"]))
        drift = copy.deepcopy(CONTRACT)
        drift["denominator"]["population"] = "all inspections, including quarantined ones"
        cases.append((drift, ["numerator and denominator populations differ"]))
        units = copy.deepcopy(CONTRACT)
        units["denominator"]["unit"] = "case"
        cases.append((units, ["numerator, denominator and unit disagree"]))
        zero = copy.deepcopy(CONTRACT)
        zero["empty_cases"]["rate_when_empty"] = 0
        cases.append((zero, ["an empty or zero denominator must give no rate"]))
        calendar = copy.deepcopy(CONTRACT)
        calendar["period"]["window"]["kind"] = "calendar_days"
        cases.append((calendar, ["window must be a positive whole number of business days"]))
        refused = []
        for broken, reasons in cases:
            self.assertEqual(metric_contract.problems(broken), reasons)
            with self.assertRaises(ValueError) as caught:
                metric_contract.parameters(broken)
            self.assertIn(reasons[0], str(caught.exception))
            refused.append(reasons)
        OUTPUTS["contract_refusals"] = refused


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
    parser.add_argument("--sql", type=Path, help="test this SQL file instead of solutions/model.sql")
    args = parser.parse_args()
    if args.sql:
        SQL["path"] = args.sql.resolve()
    import py4j
    import pyspark
    started = datetime.now(timezone.utc)
    clock = time.monotonic()
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite([loader.loadTestsFromTestCase(case)
                                for case in (ContractTests, BaselineTests, TransferTests)])
    try:
        result = unittest.TextTestRunner(verbosity=2).run(suite)
    finally:
        if "local" in SESSION:
            SESSION["local"].stop()
    finished = datetime.now(timezone.utc)
    exit_code = 0 if result.wasSuccessful() and result.testsRun > 0 and not result.skipped else 1
    evidence = {
        "lab": LAB, "executionClass": EXECUTION_CLASS, "runtime": "spark",
        "python": platform.python_version(), "interpreter": sys.executable, "java": java_version(),
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
        "solutionHashes": dict(file_hashes("solutions"),
                               **{"run_tests.py": sha256((ROOT / "run_tests.py").read_bytes()).hexdigest()}),
        "outputHashes": {name: sha256(canonical(value)).hexdigest() for name, value in sorted(OUTPUTS.items())},
        "commands": [" ".join([sys.executable] + sys.argv)],
        "sqlUnderTest": str(Path(SQL["path"]).relative_to(ROOT)).replace("\\", "/")
                        if Path(SQL["path"]).is_relative_to(ROOT) else str(SQL["path"]),
        "notes": ("Local Apache Spark %s on one machine (local[2], UI off, 2 shuffle partitions, session time zone UTC, "
                  "ANSI mode default); no Databricks, Delta, metric view, network or external effect. Expected literals "
                  "authored by hand in expected/*.json with derivations in DATA.md; two averages of rates are compared "
                  "within 1e-12 for the reason given there; outputHashes are SHA-256 of the canonical JSON of each "
                  "collected output." % OUTPUTS.get("spark_version", "?")),
    }
    if args.outputs:
        args.outputs.parent.mkdir(parents=True, exist_ok=True)
        args.outputs.write_text(json.dumps(OUTPUTS, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: evidence[key] for key in
                      ("lab", "python", "java", "spark", "tests", "failures", "errors", "skipped", "exit")}, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
