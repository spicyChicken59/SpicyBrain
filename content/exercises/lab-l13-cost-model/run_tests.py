#!/usr/bin/env python3
"""Lab L13 test runner (standard library only, offline).

    python3.12 run_tests.py --evidence local-evidence.json   # the reference: every test passes
    python3.12 run_tests.py --starter                          # judge starters/cost_model.py by the same literals

Every expected value lives in expected/*.json and was written by hand; the
derivation of each number is in DATA.md. Nothing here reads a live price, a
vendor rate or a discount, and one test proves the model runs with the
network disabled. --evidence writes the interpreter, versions, start and end
times, test counts and the SHA-256 of every fixture, expected, starter and
solution file and of every produced output.
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True  # keep the package free of __pycache__

import argparse
import csv
import datetime
import hashlib
import importlib
import json
import platform
import shlex
import socket
import subprocess
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = "lab-l13-cost-model"
RATE_LABEL = "hypothetical rate, not a price"
STATE = {"module": "solutions.cost_model", "script": "solutions/cost_model.py"}
OUTPUTS: dict[str, object] = {}
SUBPROCESS_COMMANDS: list[str] = []


def model():
    return importlib.import_module(STATE["module"])


def expected(name: str):
    return json.loads((HERE / "expected" / name).read_text(encoding="utf-8"))


def fixture(name: str) -> Path:
    return HERE / "fixtures" / name


def record(name: str, value):
    OUTPUTS[name] = value
    return value


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2)


def run_cli(*args: str, shown_args: tuple[str, ...] | None = None) -> subprocess.CompletedProcess:
    command = [sys.executable, "-B", STATE["script"], *args]
    shown = "python3.12 -B " + " ".join([shlex.quote(STATE["script"]), *(shlex.quote(a) if not a.startswith("<") else a
                                                                    for a in (shown_args or args))])
    if shown not in SUBPROCESS_COMMANDS:
        SUBPROCESS_COMMANDS.append(shown)
    return subprocess.run(command, cwd=HERE, capture_output=True, text=True, timeout=60)


def refusal_of(test: unittest.TestCase, call):
    m = model()
    with test.assertRaises(m.ModelRefusal) as caught:
        call()
    return {"reason": caught.exception.reason, "subject": caught.exception.subject}


class RateLabelTests(unittest.TestCase):
    def test_every_fixture_rate_is_labelled_hypothetical(self):
        seen = 0
        for name in ("worksheet.json", "transfer-worksheet.json", "alternatives.json"):
            doc = json.loads(fixture(name).read_text(encoding="utf-8"))
            rates = [d["rate"] for d in doc.get("drivers", [])] + list(doc.get("rates", {}).values())
            for rate in rates:
                seen += 1
                self.assertEqual(rate["label"], RATE_LABEL, name)
                self.assertTrue(rate["currency"].startswith("hypothetical "), name)
        self.assertEqual(seen, 13)

    def test_a_rate_labelled_as_a_price_is_refused(self):
        m = model()
        got = refusal_of(self, lambda: m.check_rate(
            {"amount": Decimal("0.50"), "currency": "hypothetical USD", "per": "DBU", "label": "list price"},
            "DBU", "hypothetical USD", "platform usage"))
        self.assertEqual(got, {"reason": "rate_not_labelled", "subject": "platform usage"})


class PeriodTests(unittest.TestCase):
    def test_periods_restated_per_month(self):
        m = model()
        spec = expected("periods.json")
        produced = []
        for case in spec["cases"]:
            value = m.to_monthly(Decimal(case["quantity"]), case["period"], "case")
            self.assertEqual(value, Decimal(case["perMonth"]), case)
            produced.append(str(value))
        record("periods", produced)

    def test_unknown_period_refused(self):
        m = model()
        got = refusal_of(self, lambda: m.to_monthly(Decimal(3), "fortnight", "operations effort"))
        self.assertEqual(got["reason"], expected("periods.json")["refused"]["fortnight"])

    def test_one_off_is_never_a_monthly_quantity(self):
        m = model()
        got = refusal_of(self, lambda: m.to_monthly(Decimal(250), "once", "migration one-off"))
        self.assertEqual(got["reason"], expected("periods.json")["refused"]["once"])


class WorksheetTests(unittest.TestCase):
    def setUp(self):
        m = model()
        self.result = m.evaluate_worksheet(m.load_json(fixture("worksheet.json")))

    def test_worksheet_matches_literals(self):
        record("worksheet", self.result)
        self.assertEqual(self.result, expected("worksheet.json"))

    def test_printed_rows_add_up_to_printed_totals(self):
        for case in ("low", "base", "high"):
            rows = sum(Decimal(row[case]) for row in self.result["recurring"].values())
            self.assertEqual(rows, Decimal(self.result["recurringTotal"][case]), case)

    def test_largest_swing_is_operations_effort_not_platform_usage(self):
        self.assertEqual(self.result["largestSwing"], "operations effort")
        self.assertGreater(Decimal(self.result["recurring"]["operations effort"]["swing"]),
                           Decimal(self.result["recurring"]["platform usage"]["swing"])
                           + Decimal(self.result["recurring"]["compute time"]["swing"]))

    def test_one_off_is_reported_apart_from_the_month(self):
        self.assertNotIn("migration one-off", self.result["recurring"])
        self.assertEqual(self.result["recurringTotal"]["base"], "1000.00")
        self.assertEqual(self.result["oneOff"]["migration one-off"]["base"], "15000.00")


class RefusalTests(unittest.TestCase):
    def test_worksheet_refusals_name_their_reason(self):
        m = model()
        cases = json.loads(fixture("refusals.json").read_text(encoding="utf-8"),
                           parse_float=Decimal, parse_int=Decimal)["worksheet"]
        wanted = expected("refusals.json")["worksheet"]
        self.assertEqual(set(cases), set(wanted))
        produced = {}
        for name, sheet in cases.items():
            produced[name] = refusal_of(self, lambda sheet=sheet: m.evaluate_worksheet(sheet))
            self.assertEqual(produced[name], wanted[name], name)
        record("worksheetRefusals", produced)


class ComparabilityTests(unittest.TestCase):
    def test_raw_sum_across_billing_units_is_refused(self):
        m = model()
        items = json.loads(fixture("refusals.json").read_text(encoding="utf-8"))["sums"]["raw sum across units"]
        got = refusal_of(self, lambda: m.sum_quantities(items))
        self.assertEqual(got, expected("refusals.json")["sums"]["raw sum across units"])

    def test_same_unit_quantities_may_be_added(self):
        m = model()
        doc = json.loads(fixture("alternatives.json").read_text(encoding="utf-8"), parse_float=Decimal)
        dbu = [d for alt in doc["alternatives"] for d in alt["drivers"] if d["unit"] == "DBU"]
        self.assertEqual(m.sum_quantities(dbu), expected("alternatives.json")["sameUnitSum"])

    def test_alternatives_compared_in_one_currency_per_month(self):
        m = model()
        result = m.compare_alternatives(m.load_json(fixture("alternatives.json")))
        record("alternatives", result)
        self.assertEqual(result, expected("alternatives.json")["comparison"])

    def test_incomparable_alternatives_are_refused(self):
        m = model()
        cases = json.loads(fixture("refusals.json").read_text(encoding="utf-8"), parse_float=Decimal)["alternatives"]
        wanted = expected("refusals.json")["alternatives"]
        self.assertEqual(set(cases), set(wanted))
        produced = {}
        for name, doc in cases.items():
            produced[name] = refusal_of(self, lambda doc=doc: m.compare_alternatives(doc))
            self.assertEqual(produced[name], wanted[name], name)
        record("alternativeRefusals", produced)


class UnitCostTests(unittest.TestCase):
    def test_unit_cost_literals(self):
        m = model()
        cases = json.loads(fixture("unit-cost.json").read_text(encoding="utf-8"))["cases"]
        wanted = expected("unit-cost.json")
        produced = {case["name"]: m.cost_per_unit(case["cost"], case["count"], case["per"]) for case in cases}
        record("unitCost", produced)
        self.assertEqual(produced, wanted)

    def test_zero_work_is_unknown_not_zero_and_not_a_crash(self):
        m = model()
        result = m.cost_per_unit("0.00", 0)
        self.assertIsNone(result["value"])
        self.assertNotEqual(result["value"], "0.00")
        self.assertEqual(result["reason"], "zero_denominator")

    def test_negative_count_is_refused(self):
        m = model()
        got = refusal_of(self, lambda: m.cost_per_unit("10.00", -1))
        self.assertEqual(got["reason"], "negative_count")


class RunTests(unittest.TestCase):
    def setUp(self):
        m = model()
        rate = m.rate_from_worksheet(m.load_json(fixture("worksheet.json")), "platform usage")
        self.result = m.summarize_runs(m.read_runs(fixture("runs.csv")), rate)

    def test_runs_match_literals(self):
        record("runs", self.result)
        self.assertEqual(self.result, expected("runs.json"))

    def test_every_row_is_used_or_refused_with_a_reason(self):
        self.assertEqual(self.result["rowsUsed"] + len(self.result["refused"]), self.result["rowsRead"])
        self.assertTrue(all(item["reason"] for item in self.result["refused"]))

    def test_single_observation_is_not_ranked(self):
        self.assertIn("xlarge", self.result["ranking"]["notRankable"])
        self.assertNotIn("xlarge", self.result["ranking"]["byMedianCost"])
        self.assertIn("single_observation", self.result["configurations"]["xlarge"]["caveats"])

    def test_unexpected_columns_are_refused(self):
        m = model()
        with tempfile.TemporaryDirectory(prefix="lab-l13-") as directory:
            path = Path(directory) / "runs.csv"
            path.write_text("run_id,configuration,work_items,units_consumed\nx1,small,1000,4.0\n", encoding="utf-8")
            got = refusal_of(self, lambda: m.read_runs(path))
        self.assertEqual(got["reason"], "unexpected_columns")


class TransferTests(unittest.TestCase):
    def test_transfer_worksheet_and_runs(self):
        m = model()
        sheet = m.load_json(fixture("transfer-worksheet.json"))
        result = {
            "worksheet": m.evaluate_worksheet(sheet),
            "runs": m.summarize_runs(m.read_runs(fixture("transfer-runs.csv")),
                                     m.rate_from_worksheet(sheet, "platform usage")),
        }
        record("transfer", result)
        self.assertEqual(result, expected("transfer.json"))

    def test_overlapping_ranges_do_not_name_a_winner(self):
        m = model()
        sheet = m.load_json(fixture("transfer-worksheet.json"))
        result = m.summarize_runs(m.read_runs(fixture("transfer-runs.csv")), m.rate_from_worksheet(sheet, "platform usage"))
        self.assertIs(result["ranking"]["cheapestSeparated"], False)


class NaiveTests(unittest.TestCase):
    """The deliberately failing example fails for the stated reasons."""

    @classmethod
    def setUpClass(cls):
        cls.naive = importlib.import_module("starters.naive_model")
        cls.sheet = json.loads(fixture("worksheet.json").read_text(encoding="utf-8"))
        cls.want = expected("naive.json")

    def test_weekly_effort_treated_as_monthly_understates_the_month(self):
        got = self.naive.naive_monthly_total(self.sheet)
        self.assertEqual(got, self.want["monthlyBaseTotal"])
        understatement = Decimal(self.want["modelBaseTotal"]) - Decimal(str(got)).quantize(Decimal("0.01"))
        self.assertEqual(str(understatement), self.want["understatement"])
        # the whole gap is the operations effort: 3 hours x 60 counted once instead of 52/12 times
        weekly = Decimal("3") * Decimal("60.00")
        self.assertEqual(understatement, weekly * 52 / 12 - weekly)
        record("naiveMonthly", got)

    def test_adding_units_gives_a_number_the_model_refuses(self):
        m = model()
        got = self.naive.naive_total_units(self.sheet)
        self.assertEqual(got, self.want["totalUnitsBase"])
        items = [{"quantity": d["quantity"]["base"], "unit": d["unit"]} for d in self.sheet["drivers"] if d["period"] != "once"]
        refused = refusal_of(self, lambda: m.sum_quantities(items))
        self.assertEqual(refused["reason"], "incomparable_units")
        record("naiveUnits", got)

    def test_unguarded_division_crashes_on_the_failed_run(self):
        with fixture("runs.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        # Caught by hand, not with assertRaises, which clears the frames' local variables:
        # the traceback itself must name the failing input, as it would for a reader.
        failure, frame_rows = None, []
        try:
            self.naive.naive_cost_per_1000(rows, 0.50)
        except ZeroDivisionError as error:
            failure = error
            trace = error.__traceback__
            while trace is not None:
                if trace.tb_frame.f_code.co_name == "naive_cost_per_1000":
                    frame_rows.append(trace.tb_frame.f_locals["row"]["run_id"])
                trace = trace.tb_next
        self.assertIsNotNone(failure, "the naive division should have raised")
        self.assertEqual(type(failure).__name__, self.want["exception"])
        self.assertEqual(frame_rows, [self.want["failsAtRun"]])
        record("naiveCrash", {"exception": type(failure).__name__, "run": frame_rows[0]})


class StarterTests(unittest.TestCase):
    """The starter's gaps are real: each task raises until it is written."""

    def test_starter_gaps_raise_with_their_task(self):
        starter = importlib.import_module("starters.cost_model")
        sheet = starter.load_json(fixture("worksheet.json"))
        calls = {
            "Task 1": lambda: starter.check_rate(sheet["drivers"][0]["rate"], "instance-hour", "hypothetical USD", "x"),
            "Task 2": lambda: starter.to_monthly(Decimal(3), "week"),
            "Task 3": lambda: starter.evaluate_worksheet(sheet),
            "Task 4": lambda: starter.sum_quantities([]),
            "Task 5": lambda: starter.cost_per_unit("1.00", 1),
            "Task 6": lambda: starter.summarize_runs([], {}),
        }
        for task, call in calls.items():
            with self.assertRaises(NotImplementedError) as caught:
                call()
            self.assertTrue(str(caught.exception).startswith(task), task)
        self.assertEqual(starter.to_monthly(Decimal(240), "month"), Decimal(240))


class ReproducibleTests(unittest.TestCase):
    def test_command_line_prints_identical_bytes_and_the_literals(self):
        commands = {
            "cliWorksheet": (["worksheet", "fixtures/worksheet.json"], expected("worksheet.json")),
            "cliRuns": (["runs", "fixtures/runs.csv", "--rates", "fixtures/worksheet.json", "--driver", "platform usage"],
                        expected("runs.json")),
            "cliCompare": (["compare", "fixtures/alternatives.json"], expected("alternatives.json")["comparison"]),
        }
        for name, (args, want) in commands.items():
            first, second = run_cli(*args), run_cli(*args)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(first.stdout, second.stdout, name)
            self.assertEqual(json.loads(first.stdout), want, name)
            record(name, first.stdout)

    def test_command_line_refusal_exits_with_status_two(self):
        case = json.loads(fixture("refusals.json").read_text(encoding="utf-8"))["worksheet"]["unknown period"]
        with tempfile.TemporaryDirectory(prefix="lab-l13-") as directory:
            path = Path(directory) / "unknown-period.json"
            path.write_text(json.dumps(case), encoding="utf-8")
            result = run_cli("worksheet", str(path), shown_args=("worksheet", "<temporary copy of the unknown-period case>"))
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(json.loads(result.stdout)["refused"],
                         expected("refusals.json")["worksheet"]["unknown period"])
        record("cliRefusal", result.stdout)


class OfflineTests(unittest.TestCase):
    def test_model_needs_no_network(self):
        m = model()

        def refuse(*args, **kwargs):
            raise AssertionError("the cost model tried to open a network connection")

        saved = socket.socket, socket.create_connection
        socket.socket, socket.create_connection = refuse, refuse
        try:
            sheet = m.load_json(fixture("worksheet.json"))
            worksheet = m.evaluate_worksheet(sheet)
            runs = m.summarize_runs(m.read_runs(fixture("runs.csv")), m.rate_from_worksheet(sheet, "platform usage"))
        finally:
            socket.socket, socket.create_connection = saved
        self.assertEqual(worksheet, expected("worksheet.json"))
        self.assertEqual(runs, expected("runs.json"))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fixture_hashes() -> dict:
    hashes = {}
    for folder in ("fixtures", "expected", "starters", "solutions"):
        for path in sorted((HERE / folder).glob("*")):
            if path.is_file() and path.suffix in {".json", ".csv", ".py"}:
                hashes[f"{folder}/{path.name}"] = sha256(path.read_bytes())
    return hashes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", help="write JSON evidence to this path")
    parser.add_argument("--starter", action="store_true", help="judge starters/cost_model.py instead of the reference")
    args = parser.parse_args()
    if args.starter:
        STATE.update(module="starters.cost_model", script="starters/cost_model.py")
    started = datetime.datetime.now(datetime.timezone.utc)
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    classes = [RateLabelTests, PeriodTests, WorksheetTests, RefusalTests, ComparabilityTests, UnitCostTests,
               RunTests, TransferTests, NaiveTests, ReproducibleTests, OfflineTests]
    if not args.starter:
        classes.append(StarterTests)
    for case in classes:
        suite.addTests(loader.loadTestsFromTestCase(case))
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
    finished = datetime.datetime.now(datetime.timezone.utc)
    status = 0 if result.wasSuccessful() and not result.skipped else 1
    summary = {
        "lab": LAB,
        "moduleUnderTest": STATE["module"],
        "tests": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "exit": status,
    }
    if args.evidence and not args.starter:
        evidence = {
            "lab": LAB,
            "executionClass": "local-executed",
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "interpreter": sys.executable,
            "inVirtualEnvironment": sys.prefix != sys.base_prefix,
            "java": "not used",
            "spark": "not used",
            "packages": {},
            "standardLibrary": ["argparse", "csv", "datetime", "decimal", "hashlib", "importlib", "json",
                                "pathlib", "platform", "shlex", "socket", "subprocess", "tempfile", "unittest"],
            "platform": platform.system() + " " + platform.release(),
            "startedAt": started.isoformat(),
            "finishedAt": finished.isoformat(),
            "durationSeconds": round((finished - started).total_seconds(), 3),
            "tests": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped),
            "exit": status,
            "moduleUnderTest": STATE["module"],
            "fixtureHashes": fixture_hashes(),
            "outputHashes": {name: sha256(value.encode("utf-8") if isinstance(value, str) else canonical(value).encode("utf-8"))
                             for name, value in sorted(OUTPUTS.items())},
            "commands": [f"{sys.executable} run_tests.py --evidence <path>"],
            "subprocessCommands": SUBPROCESS_COMMANDS,
            "notes": ("Plain CPython standard library, no packages, no network (one test runs the model with sockets "
                      "disabled). Every rate is a hypothetical rate, not a price, in hypothetical USD; no live price, "
                      "vendor rate or discount is read or implied. Expected values are hand-authored literals in "
                      "expected/*.json with derivations in DATA.md. The naive starter is asserted to understate the "
                      "month by 600.00 (weekly effort counted as monthly), to add incomparable units into 1163.0 and "
                      "to raise ZeroDivisionError on run r04; the unfilled starter is asserted to raise "
                      "NotImplementedError for each task. Run observations are synthetic, not measured; nothing runs "
                      "on Databricks or any cloud service."),
        }
        Path(args.evidence).write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
