"""lab-l01-python-parsing test runner (local-executed, plain Python).

    python3.12 run_tests.py --evidence <path>   # judge solutions/parser.py and write evidence JSON
    python3.12 run_tests.py --starter           # judge your starters/parser.py by the same literals

Offline, standard library only. Every expected value is a hand-authored literal
in expected/*.json (derivations in DATA.md); no test compares the parser with a
value the parser computed. The SHA-256 of every fixture, expected, starter and
solution file, and of every produced output, goes into the evidence JSON.
"""
import argparse
from contextlib import contextmanager
import csv
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import importlib
import io
import json
import logging
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback
import unittest
from unittest import mock

sys.dont_write_bytecode = True  # keep the package free of __pycache__
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

LAB = "lab-l01-python-parsing"
FIX = ROOT / "fixtures"
EXPECTED = ROOT / "expected"
PRIMARY = json.loads((EXPECTED / "primary.json").read_text(encoding="utf-8"))
TRANSFER = json.loads((EXPECTED / "transfer.json").read_text(encoding="utf-8"))
CONVERSIONS = json.loads((EXPECTED / "conversions.json").read_text(encoding="utf-8"))
POLICY = json.loads((EXPECTED / "policy.json").read_text(encoding="utf-8"))
RESULT_KEYS = ("raw_count", "accepted_count", "rejected_count", "accepted", "rejected", "reason_counts")
LOGGER = "cinderline.parsing"
OUTPUTS: dict[str, object] = {}
SUBPROCESSES: list[str] = []
MODULE_NAME = "solutions.parser"  # --starter swaps in starters.parser


# ---------------------------------------------------------------- helpers

def load_parser():
    return importlib.import_module(MODULE_NAME)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def literal(expected):
    return {key: expected[key] for key in RESULT_KEYS}


def actual(module, result):
    return {key: module.json_ready(result[key]) for key in RESULT_KEYS}


def primary_sources(module):
    return [("inspections.csv", module.read_csv(FIX / "inspections.csv")),
            ("inspections.json", module.read_json(FIX / "inspections.json"))]


def rejected_at(result, source, position):
    return [item for item in result["rejected"] if item["source"] == source and item["position"] == position][0]


def accepted_at(result, source, position):
    return [item for item in result["accepted"] if item["source"] == source and item["position"] == position][0]


class ListHandler(logging.Handler):
    """Collects formatted log lines in the same LEVEL:logger:message shape that
    unittest's assertLogs uses."""

    def __init__(self):
        super().__init__(level=logging.DEBUG)
        self.lines: list[str] = []
        self.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))

    def emit(self, record):
        self.lines.append(self.format(record))


@contextmanager
def captured_log(name=LOGGER):
    """Attach a collecting handler for the duration of a block and remove it
    afterwards, so no test leaves a handler behind for the next one."""
    logger = logging.getLogger(name)
    handler = ListHandler()
    propagate = logger.propagate
    logger.addHandler(handler)
    logger.propagate = False
    try:
        yield handler.lines
    finally:
        logger.removeHandler(handler)
        logger.propagate = propagate


def raised_by(function, *args):
    """Call and return the exception with its traceback intact. assertRaises
    strips the traceback from the exception it stores, and these tests read
    the traceback's frames."""
    try:
        function(*args)
    except Exception as error:  # the tests inspect whatever was raised
        return error
    raise AssertionError(f"{function.__name__} raised nothing")


def innermost_frame(error):
    return [frame for frame, _ in traceback.walk_tb(error.__traceback__)][-1]


def frame_named(error, name):
    return [frame for frame, _ in traceback.walk_tb(error.__traceback__) if frame.f_code.co_name == name][-1]


def run_python(label, arguments):
    """Run the lab's interpreter in the lab directory without writing bytecode."""
    command = [sys.executable, "-B", *arguments]
    shown = [Path(sys.executable).name, "-B"] + ["<code>" if index and arguments[index - 1] == "-c" else part
                                                 for index, part in enumerate(arguments)]
    SUBPROCESSES.append(f"{label}: " + " ".join(part.replace(str(ROOT) + "/", "") for part in shown))
    return subprocess.run(command, capture_output=True, text=True, cwd=str(ROOT), check=False)


def render(function):
    """The printed form of a result, or the name of the exception it raised."""
    try:
        value = function()
    except InvalidOperation:
        return "InvalidOperation"
    except (ValueError, TypeError) as error:
        return type(error).__name__
    return str(value)


# ---------------------------------------------------------------- primary delivery

class PrimaryDeliveryTests(unittest.TestCase):
    """Fifteen CSV rows (plant CL-N) and ten JSON records (plant CL-S)."""

    @classmethod
    def setUpClass(cls):
        cls.parser = load_parser()
        with captured_log() as lines:
            cls.result = cls.parser.parse_delivery(primary_sources(cls.parser))
        cls.log_lines = list(lines)
        OUTPUTS["primary"] = cls.parser.json_ready(cls.result)
        OUTPUTS["primary_log"] = cls.log_lines

    def test_whole_result_matches_the_authored_literal(self):
        self.assertEqual(actual(self.parser, self.result), literal(PRIMARY))

    def test_counts_reconcile_and_every_record_lands_once(self):
        self.assertEqual(self.result["raw_count"], PRIMARY["raw_count"])
        self.assertEqual(self.result["accepted_count"] + self.result["rejected_count"], self.result["raw_count"])
        landed = sorted((item["source"], item["position"]) for item in self.result["accepted"] + self.result["rejected"])
        self.assertEqual(len(landed), len(set(landed)), "no record is in both lists or in one list twice")
        self.assertEqual(sum(self.result["reason_counts"].values()), sum(len(item["reasons"]) for item in PRIMARY["rejected"]))

    def test_accepted_values_carry_python_types_not_text(self):
        row = accepted_at(self.result, "inspections.csv", 1)
        self.assertIs(type(row["inspected_units"]), int)
        self.assertIs(type(row["defective_units"]), int)
        self.assertIsInstance(row["inspected_on"], date)
        self.assertIsInstance(row["unit_cost"], Decimal)
        self.assertEqual(row["unit_cost"], Decimal("4.25"))
        self.assertIsNone(accepted_at(self.result, "inspections.json", 8)["unit_cost"])
        self.assertEqual(accepted_at(self.result, "inspections.json", 4)["inspected_units"], 64)  # "64" converted, not kept as text
        self.assertEqual(str(accepted_at(self.result, "inspections.json", 7)["unit_cost"]), "5.1")  # a JSON float, via str()

    def test_null_and_missing_are_different_reasons(self):
        self.assertEqual(rejected_at(self.result, "inspections.json", 2)["reasons"], ["null_inspected_units"])
        self.assertEqual(rejected_at(self.result, "inspections.json", 3)["reasons"], ["missing_inspected_units"])
        self.assertEqual(rejected_at(self.result, "inspections.csv", 4)["reasons"], ["missing_inspected_units"])
        self.assertEqual(rejected_at(self.result, "inspections.json", 9)["reasons"], ["missing_plant_id"])
        self.assertEqual(rejected_at(self.result, "inspections.csv", 10)["reasons"], ["missing_inspection_id"])

    def test_zero_is_a_value_and_yields_no_rate(self):
        for source, position in (("inspections.csv", 2), ("inspections.json", 7)):
            row = accepted_at(self.result, source, position)
            self.assertEqual(row["inspected_units"], 0)
            self.assertIsNone(row["defect_rate"])
        self.assertIsNone(self.parser.defect_rate(0, 0))
        self.assertEqual(self.parser.defect_rate(120, 3), 0.025)

    def test_negative_values_name_the_field_and_can_stack(self):
        self.assertEqual(rejected_at(self.result, "inspections.csv", 5)["reasons"], ["negative_inspected_units"])
        self.assertEqual(rejected_at(self.result, "inspections.csv", 15)["reasons"],
                         ["negative_inspected_units", "negative_defective_units"])

    def test_malformed_values_name_the_field(self):
        self.assertEqual(rejected_at(self.result, "inspections.csv", 3)["reasons"], ["malformed_inspected_units"])  # twelve
        self.assertEqual(rejected_at(self.result, "inspections.csv", 9)["reasons"], ["malformed_inspected_units"])  # 12.0
        self.assertEqual(rejected_at(self.result, "inspections.json", 5)["reasons"], ["malformed_inspected_units"])  # 12.5
        self.assertEqual(rejected_at(self.result, "inspections.json", 6)["reasons"], ["malformed_inspected_units"])  # true
        self.assertEqual(rejected_at(self.result, "inspections.csv", 7)["reasons"], ["malformed_inspected_on"])  # 2026/09/03
        self.assertEqual(rejected_at(self.result, "inspections.json", 10)["reasons"], ["malformed_inspected_on"])  # 2026-09-31
        self.assertEqual(rejected_at(self.result, "inspections.csv", 11)["reasons"], ["malformed_unit_cost"])  # 4,25

    def test_cross_field_rule_runs_only_on_clean_records(self):
        self.assertEqual(rejected_at(self.result, "inspections.csv", 6)["reasons"], ["defective_exceeds_inspected"])
        # 0 > -5 and -1 > -10 are both true, yet neither record collects the comparison.
        self.assertNotIn("defective_exceeds_inspected", rejected_at(self.result, "inspections.csv", 5)["reasons"])
        self.assertNotIn("defective_exceeds_inspected", rejected_at(self.result, "inspections.csv", 15)["reasons"])

    def test_conflicting_duplicate_rejects_both_and_exact_duplicate_keeps_first(self):
        self.assertEqual(rejected_at(self.result, "inspections.csv", 8)["reasons"], ["conflicting_duplicate"])
        self.assertEqual(rejected_at(self.result, "inspections.csv", 13)["reasons"], ["conflicting_duplicate"])
        self.assertEqual(rejected_at(self.result, "inspections.csv", 12)["reasons"], ["exact_duplicate"])
        self.assertEqual([r["position"] for r in self.result["accepted"] if r["inspection_id"] == "CLN-001"], [1])
        self.assertEqual([r["inspection_id"] for r in self.result["accepted"] if r["inspection_id"] == "CLN-008"], [])

    def test_rejected_records_retain_raw_input_and_position(self):
        item = rejected_at(self.result, "inspections.csv", 8)
        self.assertEqual(item["raw"]["inspected_units"], " 15 ", "the raw text is kept, spaces and all")
        self.assertEqual(item["raw"]["unit_cost"], "")
        item = rejected_at(self.result, "inspections.json", 3)
        self.assertNotIn("inspected_units", item["raw"], "a missing key stays missing in the retained raw record")
        self.assertIs(rejected_at(self.result, "inspections.json", 6)["raw"]["inspected_units"], True)

    def test_every_rejection_is_logged_with_source_position_and_reasons(self):
        self.assertEqual(len(self.log_lines), PRIMARY["log_warnings"])
        self.assertEqual(self.log_lines[0], PRIMARY["first_log_line"])
        self.assertEqual(self.log_lines[-1], PRIMARY["last_log_line"])
        self.assertIn("WARNING:cinderline.parsing:rejected inspections.csv position 15: negative_inspected_units, negative_defective_units",
                      self.log_lines)

    def test_altered_contract_requiring_unit_cost_rejects_the_null(self):
        expected = PRIMARY["altered_contract_json_only"]
        altered = tuple({**field, "required": True} if field["name"] == "unit_cost" else field for field in self.parser.CONTRACT)
        with captured_log():
            result = self.parser.parse_delivery([("inspections.json", self.parser.read_json(FIX / "inspections.json"))], altered)
        self.assertEqual(result["accepted_count"], expected["accepted_count"])
        self.assertEqual(result["rejected_count"], expected["rejected_count"])
        self.assertEqual([r["inspection_id"] for r in result["accepted"]], expected["accepted_ids"])
        self.assertEqual(rejected_at(result, "inspections.json", 8)["reasons"], expected["cls_008_reasons"])
        self.assertFalse(self.parser.CONTRACT[5]["required"], "the module's own contract was not changed")
        OUTPUTS["primary_altered_contract"] = self.parser.json_ready(result)


# ---------------------------------------------------------------- transfer delivery

class TransferDeliveryTests(unittest.TestCase):
    """A third plant (TM-A) breaks the same contract in its own ways."""

    @classmethod
    def setUpClass(cls):
        cls.parser = load_parser()
        cls.rows = cls.parser.read_csv(FIX / "transfer-inspections.csv")
        with captured_log() as lines:
            cls.result = cls.parser.parse_delivery([("transfer-inspections.csv", cls.rows)])
        cls.log_lines = list(lines)
        OUTPUTS["transfer"] = cls.parser.json_ready(cls.result)
        OUTPUTS["transfer_log"] = cls.log_lines

    def test_transfer_matches_the_authored_literal(self):
        self.assertEqual(actual(self.parser, self.result), literal(TRANSFER))

    def test_transfer_breaks_the_contract_in_its_own_ways(self):
        self.assertEqual(rejected_at(self.result, "transfer-inspections.csv", 4)["reasons"], ["malformed_inspected_units"])  # 1_000
        self.assertEqual(int("1_000"), 1000, "int() alone would have accepted it")
        self.assertEqual(rejected_at(self.result, "transfer-inspections.csv", 5)["reasons"], ["negative_unit_cost"])
        self.assertEqual(rejected_at(self.result, "transfer-inspections.csv", 6)["reasons"], ["missing_inspected_on"])
        self.assertEqual(accepted_at(self.result, "transfer-inspections.csv", 9)["unit_cost"], Decimal("2.5"))
        self.assertEqual(str(accepted_at(self.result, "transfer-inspections.csv", 1)["unit_cost"]), "2.00")
        self.assertEqual(accepted_at(self.result, "transfer-inspections.csv", 9)["defect_rate"], 0.0)  # 0 of 25 is a rate; 0 of 0 is not

    def test_transfer_log_follows_processing_order_not_position_order(self):
        self.assertEqual(self.log_lines, TRANSFER["log_lines"])
        self.assertEqual([item["position"] for item in self.result["rejected"]], [2, 3, 4, 5, 6, 7, 8])

    def test_altered_defective_units_flip_an_accepted_row(self):
        expected = TRANSFER["altered_defective"]
        altered = [dict(row) for row in self.rows]  # copies: the fixture rows stay untouched
        altered[expected["altered_position"] - 1]["defective_units"] = expected["new_defective_units"]
        with captured_log():
            result = self.parser.parse_delivery([("transfer-inspections.csv", altered)])
        self.assertEqual(result["accepted_count"], expected["accepted_count"])
        self.assertEqual(result["rejected_count"], expected["rejected_count"])
        self.assertEqual([r["inspection_id"] for r in result["accepted"]], expected["accepted_ids"])
        self.assertEqual(rejected_at(result, "transfer-inspections.csv", 9)["reasons"], expected["position_9_reasons"])
        self.assertEqual(self.rows[8]["defective_units"], "0", "the original rows were not mutated")
        OUTPUTS["transfer_altered_defective"] = self.parser.json_ready(result)


# ---------------------------------------------------------------- conversions

BUILTIN_CASES = {
    'int("12")': lambda: int("12"),
    'int(" 12 ")': lambda: int(" 12 "),
    'int("12.0")': lambda: int("12.0"),
    "int(12.9)": lambda: int(12.9),
    "int(True)": lambda: int(True),
    'int("1_000")': lambda: int("1_000"),
    'int("twelve")': lambda: int("twelve"),
    "int(None)": lambda: int(None),
    'float("4,25")': lambda: float("4,25"),
    "0.1 + 0.2": lambda: 0.1 + 0.2,
    'Decimal("4.25")': lambda: Decimal("4.25"),
    "Decimal(5.1)": lambda: Decimal(5.1),
    "Decimal(str(5.1))": lambda: Decimal(str(5.1)),
    'Decimal("4,25")': lambda: Decimal("4,25"),
    'Decimal("1_000.50")': lambda: Decimal("1_000.50"),
    'str(Decimal("2.00"))': lambda: str(Decimal("2.00")),
    'date.fromisoformat("2026-09-31")': lambda: date.fromisoformat("2026-09-31"),
    'date.fromisoformat("2026/09/03")': lambda: date.fromisoformat("2026/09/03"),
    'date.fromisoformat("20260903")': lambda: date.fromisoformat("20260903"),
    'json.loads("[1, 1.0, true, null]")': lambda: json.loads("[1, 1.0, true, null]"),
    'json.dumps({"cost": Decimal("4.25")})': lambda: json.dumps({"cost": Decimal("4.25")}),
    'bool("False")': lambda: bool("False"),
    "None == None": lambda: None == None,  # noqa: E711 - the comparison itself is the lesson
    "None < 0": lambda: None < 0,
    '"12" == 12': lambda: "12" == 12,
    "type(True) is int": lambda: type(True) is int,
    "isinstance(True, int)": lambda: isinstance(True, int),
    "not 0": lambda: not 0,
    '{"a": None}.get("a") is {"a": 1}.get("b")': lambda: {"a": None}.get("a") is {"a": 1}.get("b"),
    '"inspected_units" in {"inspected_units": None}': lambda: "inspected_units" in {"inspected_units": None},
    'len({"a", "b", "a"})': lambda: len({"a", "b", "a"}),
    # the rows below are quoted by the dbxfe-python module and its lesson
    'type("12"), type(12), type(12.5), type(True), type(None)': lambda: (type("12"), type(12), type(12.5), type(True), type(None)),
    "isinstance(True, int), type(True) is int": lambda: (isinstance(True, int), type(True) is int),
    'len({"CL-N", "CL-S", "CL-N"})': lambda: len({"CL-N", "CL-S", "CL-N"}),
    'len({("CLN-008", 15), ("CLN-008", 16)})': lambda: len({("CLN-008", 15), ("CLN-008", 16)}),
    '{ {"id": 1} }': lambda: { {"id": 1} },
    '{"inspection_id": "CLN-001"}["unit_cost"]': lambda: {"inspection_id": "CLN-001"}["unit_cost"],
    '{"inspection_id": "CLN-001"}.get("unit_cost")': lambda: {"inspection_id": "CLN-001"}.get("unit_cost"),
    'bool(""), bool(0), bool(None), bool("0")': lambda: (bool(""), bool(0), bool(None), bool("0")),
    "5.1 * 100": lambda: 5.1 * 100,
    "int(5.1 * 100)": lambda: int(5.1 * 100),
    'json.loads(\'{"cost": 5.1}\', parse_float=Decimal)': lambda: json.loads('{"cost": 5.1}', parse_float=Decimal),
    'list(csv.DictReader(io.StringIO("a,b,c\\n1,2\\n")))': lambda: list(csv.DictReader(io.StringIO("a,b,c\n1,2\n"))),
}

BUILTIN_CONVERTERS = {"to_integer": int, "to_decimal": Decimal, "to_date": date.fromisoformat}


class ConversionEdgeCaseTests(unittest.TestCase):
    """expected/conversions.json states what the interpreter does; expected/policy.json
    states what the contract decides. Both tables were written by hand (DATA.md)."""

    def test_builtin_conversion_table_matches_the_authored_literals(self):
        self.assertEqual([case["expression"] for case in CONVERSIONS], list(BUILTIN_CASES), "one callable per authored row")
        observed = []
        for case in CONVERSIONS:
            try:
                text = repr(BUILTIN_CASES[case["expression"]]())
            except InvalidOperation:
                text = "InvalidOperation"
            except (ValueError, TypeError, KeyError) as error:
                text = f"{type(error).__name__}: {error}"
            observed.append({"expression": case["expression"], "result": text})
            self.assertEqual(text, case["result"], case["expression"])
        OUTPUTS["conversions"] = observed

    def test_contract_policy_refuses_what_the_constructors_accept(self):
        parser = load_parser()
        observed = []
        for case in POLICY:
            builtin = render(lambda: BUILTIN_CONVERTERS[case["converter"]](case["input"]))
            decided = render(lambda: getattr(parser, case["converter"])(case["input"]))
            observed.append({**case, "builtin": builtin, "policy": decided})
            label = f'{case["converter"]}({case["input"]!r})'
            self.assertEqual(builtin, case["builtin"], label + " builtin")
            self.assertEqual(decided, case["policy"], label + " policy")
        OUTPUTS["policy"] = observed


# ---------------------------------------------------------------- the deliberately failing example

class NaiveParserTests(unittest.TestCase):
    """The deliberately failing example must fail where and why DATA.md says."""

    def setUp(self):
        self.naive = importlib.import_module("starters.naive_parser")
        self.parser = load_parser()
        self.expected = PRIMARY["naive_parser"]

    def test_naive_parser_crashes_on_twelve_and_the_traceback_names_line_and_input(self):
        rows = self.parser.read_csv(FIX / "inspections.csv")
        error = raised_by(self.naive.parse, rows)
        self.assertEqual(type(error).__name__, self.expected["csv_error_type"])
        self.assertEqual(str(error), self.expected["csv_error_message"])
        innermost = traceback.extract_tb(error.__traceback__)[-1]
        self.assertTrue(innermost.filename.endswith("naive_parser.py"))
        self.assertEqual(innermost.name, self.expected["csv_failing_function"])
        self.assertEqual(innermost.lineno, self.expected["csv_failing_lineno"])
        self.assertEqual(innermost.line, self.expected["csv_failing_line"])
        frame = innermost_frame(error)  # the frame that raised still holds its local variables
        self.assertEqual(frame.f_lineno, self.expected["csv_failing_lineno"])
        self.assertEqual(frame.f_locals["row"]["inspection_id"], self.expected["csv_failing_inspection_id"])
        self.assertEqual([r["inspection_id"] for r in frame.f_locals["accepted"]], self.expected["csv_accepted_before_failure"])
        OUTPUTS["naive_csv"] = {"error": str(error), "lineno": innermost.lineno, "line": innermost.line,
                                "inspection_id": frame.f_locals["row"]["inspection_id"]}

    def test_naive_script_prints_the_traceback_to_stderr_and_exits_1(self):
        completed = run_python("naive script", ["starters/naive_parser.py"])
        lines = completed.stderr.replace(str(ROOT), "<lab>").splitlines()
        self.assertEqual(completed.returncode, self.expected["script_exit_code"])
        self.assertEqual(completed.stdout, "", "nothing was printed: the partial result never reached print()")
        self.assertEqual(lines[0], self.expected["script_first_line"])
        self.assertEqual([line.strip() for line in lines if line.strip().startswith("File ")], self.expected["script_frames"])
        self.assertEqual(lines[-1], self.expected["script_last_line"])
        OUTPUTS["naive_script_stderr"] = lines

    def test_naive_parser_stops_at_the_first_json_null_with_type_error(self):
        records = self.parser.read_json(FIX / "inspections.json")
        error = raised_by(self.naive.parse, records)
        self.assertEqual(type(error).__name__, self.expected["json_error_type"])
        self.assertEqual(str(error), self.expected["json_error_message"])
        self.assertEqual(innermost_frame(error).f_locals["row"]["inspection_id"], self.expected["json_failing_inspection_id"])

    def test_naive_parser_raises_key_error_on_the_record_without_the_key(self):
        record = [r for r in self.parser.read_json(FIX / "inspections.json") if r["inspection_id"] == self.expected["missing_key_inspection_id"]]
        error = raised_by(self.naive.parse, record)
        self.assertEqual(type(error).__name__, self.expected["missing_key_error_type"])
        self.assertEqual(error.args[0], self.expected["missing_key_error_key"])

    def test_naive_parser_is_silently_wrong_on_true_and_on_twelve_point_five(self):
        records = self.parser.read_json(FIX / "inspections.json")
        true_record = [r for r in records if r["inspection_id"] == "CLS-006"]
        float_record = [r for r in records if r["inspection_id"] == "CLS-005"]
        self.assertEqual(self.naive.parse(true_record)[0]["inspected_units"], self.expected["true_becomes"])
        self.assertEqual(self.naive.parse(float_record)[0]["inspected_units"], self.expected["twelve_point_five_becomes"])
        self.assertEqual(self.parser.validate(true_record[0])[1], ["malformed_inspected_units"])
        self.assertEqual(self.parser.validate(float_record[0])[1], ["malformed_inspected_units"])


# ---------------------------------------------------------------- module, logging, hints, assertions

class ModuleAndToolingTests(unittest.TestCase):
    def setUp(self):
        self.parser = load_parser()

    def test_import_has_no_side_effects_and_adds_no_handlers(self):
        expected = PRIMARY["import_probe"]
        probe = ("import logging\n"
                 f"import {MODULE_NAME}\n"
                 f"print(len(logging.getLogger('{LOGGER}').handlers), len(logging.getLogger().handlers))\n")
        completed = run_python("import probe", ["-c", probe])
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), expected["stdout"], "import printed nothing and configured no handler")
        self.assertEqual(completed.stderr, expected["stderr"])
        OUTPUTS["import_probe"] = {"stdout": completed.stdout.strip(), "stderr": completed.stderr}

    def test_script_entry_point_prints_the_same_counts(self):
        expected = PRIMARY["script"]
        completed = run_python("script", [MODULE_NAME.replace(".", "/") + ".py",
                                          "--csv", "fixtures/inspections.csv", "--json", "fixtures/inspections.json"])
        self.assertEqual(completed.returncode, 0, completed.stderr)
        printed = json.loads(completed.stdout)  # stdout carries only the result
        self.assertEqual({key: printed[key] for key in expected}, expected)
        warnings = [line for line in completed.stderr.splitlines() if line.startswith("WARNING ")]
        self.assertEqual(len(warnings), PRIMARY["log_warnings"], "stderr carries only the log")
        self.assertEqual(warnings[0], "WARNING cinderline.parsing: rejected inspections.csv position 3: malformed_inspected_units")
        OUTPUTS["script_counts"] = {key: printed[key] for key in expected}

    def test_type_hints_document_but_do_not_convert(self):
        expected = PRIMARY["type_hints"]
        hints = self.parser.defect_rate.__annotations__
        self.assertIs(hints["inspected_units"], int)
        self.assertEqual(hints["return"], float | None)
        self.assertEqual(repr(hints), expected["annotations_repr"])  # what the handbook quotes
        self.assertEqual(self.parser.defect_rate(120.0, 3.0), expected["float_inputs_rate"])  # hinted int, given float: no complaint
        error = raised_by(self.parser.defect_rate, "120", "3")  # the division fails, not the hint
        self.assertEqual(type(error).__name__, expected["text_inputs_error"])
        self.assertEqual(innermost_frame(error).f_code.co_name, "defect_rate")

    def test_a_code_bug_crashes_through_the_narrow_handler(self):
        expected = PRIMARY["broad_except"]
        with mock.patch.dict(self.parser.CONVERTERS), captured_log():
            del self.parser.CONVERTERS["text"]  # a converter lost in a refactor: a bug in the code, not bad data
            error = raised_by(self.parser.parse_delivery, primary_sources(self.parser))
        self.assertEqual(type(error).__name__, expected["narrow_error_type"])
        self.assertEqual(error.args[0], expected["narrow_error_key"])
        self.assertEqual(innermost_frame(error).f_code.co_name, "check_field")
        self.assertIn("text", self.parser.CONVERTERS, "the converter table was restored")

    def test_a_broad_handler_turns_the_same_bug_into_data_rejections(self):
        expected = PRIMARY["broad_except"]
        parser = self.parser

        def broad_check_field(field, raw):  # the wrong approach: every exception becomes a data reason
            name = field["name"]
            if name not in raw or parser.is_blank(raw[name]):
                return None, ("missing_" + name if field["required"] else None)
            if raw[name] is None:
                return None, ("null_" + name if field["required"] else None)
            try:
                value = parser.CONVERTERS[field["type"]](raw[name])
            except Exception:
                return None, "malformed_" + name
            if "minimum" in field and value < field["minimum"]:
                return value, "negative_" + name
            return value, None

        with mock.patch.dict(parser.CONVERTERS), mock.patch.object(parser, "check_field", broad_check_field), captured_log():
            del parser.CONVERTERS["text"]
            result = parser.parse_delivery(primary_sources(parser))
        self.assertEqual((result["accepted_count"], result["rejected_count"]),
                         (expected["broad_accepted_count"], expected["broad_rejected_count"]))
        self.assertEqual(rejected_at(result, "inspections.csv", 1)["reasons"], expected["broad_cln_001_reasons"])
        self.assertEqual(result["reason_counts"]["malformed_inspection_id"], expected["broad_malformed_inspection_id"])
        self.assertIn("text", parser.CONVERTERS, "the converter table was restored")
        OUTPUTS["broad_except"] = {"accepted_count": result["accepted_count"], "rejected_count": result["rejected_count"],
                                   "reason_counts": result["reason_counts"]}

    def test_assertion_guards_the_reconciliation_invariant(self):
        expected = PRIMARY["assertion"]

        def lossy(accepted, contract=None):  # a bug that silently drops the last accepted record
            return accepted[:-1], []

        with mock.patch.object(self.parser, "resolve_duplicates", lossy), captured_log():
            error = raised_by(self.parser.parse_delivery, primary_sources(self.parser))
        self.assertIsInstance(error, AssertionError)
        self.assertEqual(str(error), expected["message"])
        frame = frame_named(error, "parse_delivery")
        self.assertEqual(len(frame.f_locals["accepted"]) + len(frame.f_locals["rejected"]), expected["lossy_landed"])
        self.assertEqual(frame.f_locals["raw_count"], expected["raw_count"])

    def test_assertions_are_stripped_under_optimisation(self):
        expected = PRIMARY["assertion"]
        lossy = ("import logging\n"
                 "logging.disable(logging.CRITICAL)\n"
                 f"import {MODULE_NAME} as parser\n"
                 "parser.resolve_duplicates = lambda accepted, contract=None: (accepted[:-1], [])\n"
                 "sources = [('inspections.csv', parser.read_csv('fixtures/inspections.csv')),\n"
                 "           ('inspections.json', parser.read_json('fixtures/inspections.json'))]\n"
                 "result = parser.parse_delivery(sources)\n"
                 "print(result['accepted_count'] + result['rejected_count'], result['raw_count'])\n")
        plain = run_python("lossy plain", ["-c", lossy])
        optimised = run_python("lossy -O", ["-O", "-c", lossy])
        self.assertEqual(plain.returncode, expected["plain_exit"])
        self.assertEqual(plain.stderr.splitlines()[-1], expected["plain_last_line"])
        self.assertEqual(optimised.returncode, expected["optimised_exit"], optimised.stderr)
        self.assertEqual(optimised.stdout.strip(), expected["optimised_stdout"], "under -O the same bug reports 24 of 25 and exits 0")
        OUTPUTS["assert_under_O"] = {"plain_exit": plain.returncode, "plain_last_line": plain.stderr.splitlines()[-1],
                                     "optimised_exit": optimised.returncode, "optimised_stdout": optimised.stdout.strip()}


# ---------------------------------------------------------------- the starter's gaps are real

class StarterGapTests(unittest.TestCase):
    """Solution mode only: each of the starter's five gaps is observable, and
    the authored literals reject the unfilled starter. Excluded under --starter,
    where the learner's filled starter is judged instead."""

    @classmethod
    def setUpClass(cls):
        cls.starter = importlib.import_module("starters.parser")
        cls.expected = PRIMARY["unfilled_starter"]

    def test_gap1_int_accepts_true_fractions_and_underscores(self):
        self.assertEqual(self.starter.to_integer(True), 1)
        self.assertEqual(self.starter.to_integer(12.5), 12)
        self.assertEqual(self.starter.to_integer("1_000"), 1000)

    def test_gap2_decimal_exposes_the_binary_fraction_and_raises_the_wrong_error(self):
        self.assertEqual(self.starter.to_decimal(5.1), Decimal(5.1))
        self.assertNotEqual(self.starter.to_decimal(5.1), Decimal("5.1"))
        self.assertIsInstance(raised_by(self.starter.to_decimal, "4,25"), InvalidOperation)

    def test_gap3_zero_and_null_collapse_into_missing(self):
        field = {"name": "inspected_units", "type": "integer", "required": True, "minimum": 0}
        self.assertEqual(self.starter.check_field(field, {"inspected_units": 0}), (None, "missing_inspected_units"))
        self.assertEqual(self.starter.check_field(field, {"inspected_units": None}), (None, "missing_inspected_units"))
        self.assertEqual(self.starter.check_field(field, {"inspected_units": -5}), (-5, None))

    def test_gap4_cross_field_rule_is_absent(self):
        row = self.starter.read_csv(FIX / "inspections.csv")[5]  # CLN-006: 45 defective of 40
        self.assertEqual(row["inspection_id"], "CLN-006")
        self.assertEqual(self.starter.validate(row)[1], [])

    def test_gap5_duplicates_pass_through(self):
        rows = self.starter.read_csv(FIX / "inspections.csv")
        with captured_log():
            accepted, _ = self.starter.parse_records([rows[7], rows[12]], "inspections.csv")  # CLN-008 twice, 15 and 16
        kept, rejected = self.starter.resolve_duplicates(accepted)
        self.assertEqual((len(kept), len(rejected)), (2, 0))

    def test_the_authored_literals_reject_the_unfilled_starter(self):
        with captured_log():
            result = self.starter.parse_delivery([("inspections.json", self.starter.read_json(FIX / "inspections.json"))])
        accepted_ids = [r["inspection_id"] for r in result["accepted"]]
        self.assertEqual(accepted_ids, self.expected["json_accepted_ids"])
        self.assertNotEqual(accepted_ids, [r["inspection_id"] for r in PRIMARY["accepted"] if r["source"] == "inspections.json"])
        for key, position in (("json_cls_002_reasons", 2), ("json_cls_005_reasons", 5), ("json_cls_007_reasons", 7)):
            self.assertEqual(rejected_at(result, "inspections.json", position)["reasons"], self.expected[key])
        with captured_log():
            error = raised_by(self.starter.parse_delivery, [("inspections.csv", self.starter.read_csv(FIX / "inspections.csv"))])
        self.assertEqual(type(error).__name__, self.expected["csv_error_type"])
        frame = frame_named(error, "parse_records")
        self.assertEqual(frame.f_locals["position"], self.expected["csv_failing_position"])
        self.assertEqual(frame.f_locals["raw"]["inspection_id"], self.expected["csv_failing_inspection_id"])
        OUTPUTS["unfilled_starter"] = {"json_accepted_ids": accepted_ids, "csv_error": type(error).__name__,
                                       "csv_position": frame.f_locals["position"]}


# ---------------------------------------------------------------- runner

def main():
    global MODULE_NAME
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--starter", action="store_true", help="judge starters/parser.py instead of the solution")
    args = parser.parse_args()
    if args.starter:
        MODULE_NAME = "starters.parser"
    started_at = datetime.now(timezone.utc)
    started = time.monotonic()
    cases = [PrimaryDeliveryTests, TransferDeliveryTests, ConversionEdgeCaseTests, NaiveParserTests, ModuleAndToolingTests]
    if not args.starter:
        cases.append(StarterGapTests)
    suite = unittest.TestSuite()
    for case in cases:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    exit_code = 0 if result.wasSuccessful() else 1
    fixture_hashes = {str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path.read_bytes()).hexdigest()
                      for directory in ("fixtures", "expected", "solutions", "starters")
                      for path in sorted((ROOT / directory).iterdir()) if path.is_file()}
    output_hashes = {name: sha256(canonical(value).encode("utf-8")).hexdigest() for name, value in sorted(OUTPUTS.items())}
    command = [sys.executable, "run_tests.py"] + (["--starter"] if args.starter else []) + (["--evidence", "<path>"] if args.evidence else [])
    evidence = {
        "lab": LAB, "executionClass": "local-executed",
        "python": platform.python_version(), "implementation": platform.python_implementation(),
        "interpreter": sys.executable, "inVirtualEnvironment": sys.prefix != sys.base_prefix,
        "java": "not used", "spark": "not used",
        "packages": {},
        "standardLibrary": ["argparse", "csv", "datetime", "decimal", "hashlib", "importlib", "json", "logging",
                            "pathlib", "platform", "re", "subprocess", "traceback", "unittest"],
        "platform": platform.system() + " " + platform.release(),
        "startedAt": started_at.isoformat(), "finishedAt": datetime.now(timezone.utc).isoformat(),
        "durationSeconds": round(time.monotonic() - started, 3),
        "tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "skipped": len(result.skipped), "exit": exit_code,
        "moduleUnderTest": MODULE_NAME,
        "fixtureHashes": fixture_hashes, "outputHashes": output_hashes,
        "commands": [" ".join(command)],
        "subprocessCommands": SUBPROCESSES,
        "notes": ("Plain CPython standard library, no packages, no network. The parser reads a CSV delivery and a "
                  "JSON delivery under one contract; expected values are hand-authored literals in expected/*.json "
                  "with derivations in DATA.md, and the two conversion tables state interpreter behaviour and "
                  "contract policy separately. The naive starter is asserted to crash at the documented line on the "
                  "documented input (CSV ValueError, JSON TypeError, KeyError on a missing key) and to be silently "
                  "wrong on two JSON records; the unfilled starter is asserted to fail the literals. Nothing runs on "
                  "Databricks, Spark or any cloud service."),
    }
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: evidence[key] for key in ("lab", "python", "moduleUnderTest", "tests", "failures", "errors", "skipped", "exit")}, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
