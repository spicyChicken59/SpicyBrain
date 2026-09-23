"""lab-l10-contracts-quarantine test runner (local-executed, plain Python).

    python run_tests.py --evidence <path>

Offline, standard library only. Every expected value is a hand-authored literal
in expected/*.json (derivations in DATA.md); no test compares the validator
with a value the validator computed. Fixture and output SHA-256 go into the
evidence JSON.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import platform
import sys
import time
import unittest

sys.dont_write_bytecode = True  # keep the package free of __pycache__
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from solutions.validator import (check_row, defect_rate, load_contract, load_dimension, load_manifest,  # noqa: E402
                                 load_rows, row_checks_only, validate, validate_rows)
from starters import permissive_validator  # noqa: E402

LAB = "lab-l10-contracts-quarantine"
FIX = ROOT / "fixtures"
PRIMARY = json.loads((ROOT / "expected" / "primary.json").read_text(encoding="utf-8"))
TRANSFER = json.loads((ROOT / "expected" / "transfer.json").read_text(encoding="utf-8"))
RESULT_KEYS = ("contract_id", "batch_id", "raw_count", "accepted", "quarantine", "contradictions", "batch_failures",
               "reason_counts", "accepted_count", "quarantined_count", "publication_allowed")
OUTPUTS = {}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def literal(expected):
    return {key: expected[key] for key in RESULT_KEYS}


def actual(result):
    return {key: result[key] for key in RESULT_KEYS}


def inputs(prefix=""):
    contract = load_contract(FIX / "contract.json")
    header, rows = load_rows(FIX / (prefix + "inspections.csv"))
    manifest = load_manifest(FIX / (prefix + "manifest.json"))
    dimensions = {"plants": load_dimension(FIX / (prefix + "plants.csv"), "plant_id")}
    return contract, header, rows, manifest, dimensions


def reasons_of(result, number):
    return [item["reasons"] for item in result["quarantine"] if item["row_number"] == number][0]


class PrimaryContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = validate(FIX / "inspections.csv", FIX / "plants.csv", FIX / "manifest.json", FIX / "contract.json")
        OUTPUTS["primary"] = cls.result

    def test_whole_result_matches_the_authored_literal(self):
        self.assertEqual(actual(self.result), literal(PRIMARY))

    def test_accepted_rows_are_typed_and_carry_rates(self):
        self.assertEqual(self.result["accepted"], PRIMARY["accepted"])
        for row in self.result["accepted"]:
            self.assertIs(type(row["version"]), int)
            self.assertIs(type(row["inspected_units"]), int)
            self.assertIs(type(row["defective_units"]), int)

    def test_every_quarantined_row_names_its_reasons(self):
        self.assertEqual(self.result["quarantine"], PRIMARY["quarantine"])
        self.assertEqual(self.result["reason_counts"], PRIMARY["reason_counts"])
        self.assertEqual(sum(self.result["reason_counts"].values()), sum(len(item["reasons"]) for item in PRIMARY["quarantine"]))
        self.assertEqual(self.result["accepted_count"] + self.result["quarantined_count"], self.result["raw_count"])

    def test_contradictions_and_manifest_block_publication(self):
        self.assertEqual(self.result["contradictions"], PRIMARY["contradictions"])
        self.assertEqual(self.result["batch_failures"], PRIMARY["batch_failures"])
        self.assertFalse(self.result["publication_allowed"])
        self.assertEqual(self.result["batch_failures"][0]["manifest_rows"] - self.result["batch_failures"][0]["delivered_rows"], 1)

    def test_zero_denominator_yields_null_rate_not_zero_and_not_an_error(self):
        row = [item for item in self.result["accepted"] if item["row_number"] == 7][0]
        self.assertEqual(row["inspected_units"], 0)
        self.assertIsNone(row["defect_rate"])
        self.assertIsNone(defect_rate({"inspected_units": 0, "defective_units": 0}))
        self.assertEqual(defect_rate({"inspected_units": 10, "defective_units": 1}), 0.1)
        OUTPUTS["zero_denominator_row"] = row

    def test_reasons_follow_contract_field_order_then_cross_field_rule(self):
        self.assertEqual(reasons_of(self.result, 3), ["below_minimum_inspected_units", "defective_exceeds_inspected"])
        self.assertEqual(reasons_of(self.result, 16), ["below_minimum_version", "below_minimum_defective_units"])
        self.assertEqual(reasons_of(self.result, 6), ["defective_exceeds_inspected"])

    def test_type_rules_reject_words_float_text_and_slashed_dates(self):
        self.assertEqual(reasons_of(self.result, 5), ["invalid_inspected_units"])
        self.assertEqual(reasons_of(self.result, 17), ["invalid_revised_at"])
        self.assertEqual(reasons_of(self.result, 15), ["missing_inspected_units"])
        self.assertEqual(reasons_of(self.result, 8), ["missing_inspection_id"])

    def test_reference_check_is_exact(self):
        self.assertEqual(reasons_of(self.result, 9), ["unknown_plant"])

    def test_duplicate_kept_once_and_key_version_conflict_quarantines_both(self):
        self.assertEqual(reasons_of(self.result, 12), ["duplicate_delivery"])
        self.assertIn(4, [row["row_number"] for row in self.result["accepted"]])
        self.assertEqual(reasons_of(self.result, 10), ["key_version_conflict"])
        self.assertEqual(reasons_of(self.result, 11), ["key_version_conflict"])
        self.assertEqual(reasons_of(self.result, 2), ["event_id_conflict"])
        self.assertEqual(reasons_of(self.result, 20), ["event_id_conflict"])

    def test_version_time_inversion_quarantines_the_whole_inspection(self):
        self.assertEqual(reasons_of(self.result, 13), ["version_time_inversion"])
        self.assertEqual(reasons_of(self.result, 14), ["version_time_inversion"])
        self.assertIn({"rule": "version_time_inversion", "identity": "J", "row_numbers": [13, 14]}, self.result["contradictions"])
        self.assertEqual([row["inspection_id"] for row in self.result["accepted"] if row["inspection_id"] == "N"], ["N", "N"])

    def test_row_level_checks_alone_cannot_establish_uniqueness_or_completeness(self):
        contract, header, rows, manifest, dimensions = inputs()
        alone = row_checks_only(rows, contract, dimensions)
        expected = PRIMARY["row_level_only"]
        self.assertEqual({k: alone[k] for k in ("passing_row_numbers", "failing_row_numbers", "sees_manifest")},
                         {k: expected[k] for k in ("passing_row_numbers", "failing_row_numbers", "sees_manifest")})
        for number in (10, 11, 12, 13, 14, 2, 20):  # each passes on its own ...
            self.assertIn(number, alone["passing_row_numbers"])
            self.assertIn(number, [item["row_number"] for item in self.result["quarantine"]])  # ... and fails with the batch
        for number in (10, 11):
            _, reasons = check_row(rows[number - 1], contract, dimensions)
            self.assertEqual(reasons, [], "row %d is individually clean" % number)
        # No per-row signal exists for a manifest that promises more rows than were delivered.
        self.assertFalse(alone["sees_manifest"])
        self.assertEqual(len(alone["passing_row_numbers"]) + len(alone["failing_row_numbers"]), len(rows))
        self.assertNotEqual(manifest["delivered_rows"], len(rows))
        OUTPUTS["row_level_only"] = alone

    def test_reason_counts_survive_row_order_reversal(self):
        contract, header, rows, manifest, dimensions = inputs()
        reversed_rows = [{**row, "_row_number": index} for index, row in enumerate(reversed(rows), start=1)]
        result = validate_rows(header, reversed_rows, contract, manifest, dimensions)
        self.assertEqual(result["reason_counts"], PRIMARY["reason_counts"])
        self.assertEqual(sorted(row["event_id"] for row in result["accepted"]), sorted(row["event_id"] for row in PRIMARY["accepted"]))
        self.assertFalse(result["publication_allowed"])


class TransferTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = validate(FIX / "transfer-inspections.csv", FIX / "transfer-plants.csv",
                              FIX / "transfer-manifest.json", FIX / "contract.json")
        OUTPUTS["transfer"] = cls.result

    def test_transfer_is_publishable_with_disclosed_quarantine(self):
        self.assertEqual(actual(self.result), literal(TRANSFER))
        self.assertTrue(self.result["publication_allowed"])
        self.assertEqual(self.result["quarantined_count"], 7)

    def test_transfer_violations_are_the_different_ones(self):
        self.assertEqual(reasons_of(self.result, 5), ["missing_inspection_id"])  # whitespace-only key
        self.assertEqual(reasons_of(self.result, 6), ["invalid_inspected_units"])  # 12.0
        self.assertEqual(reasons_of(self.result, 7), ["unknown_plant"])  # tm-a is not TM-A
        self.assertEqual(reasons_of(self.result, 8), ["invalid_version"])  # 2.0
        self.assertEqual(reasons_of(self.result, 9), ["below_minimum_defective_units"])
        self.assertEqual(reasons_of(self.result, 10), ["defective_exceeds_inspected"])  # 1 of 0
        self.assertIsNone([row for row in self.result["accepted"] if row["row_number"] == 11][0]["defect_rate"])
        self.assertEqual([row["revised_at"] for row in self.result["accepted"] if row["inspection_id"] == "W"], ["2026-08-04", "2026-08-04"])

    def test_altered_manifest_blocks_the_same_rows(self):
        contract, header, rows, manifest, dimensions = inputs("transfer-")
        altered = {**manifest, "delivered_rows": TRANSFER["altered_manifest"]["delivered_rows"]}
        result = validate_rows(header, rows, contract, altered, dimensions)
        self.assertEqual(result["batch_failures"], TRANSFER["altered_manifest"]["batch_failures"])
        self.assertEqual(result["publication_allowed"], TRANSFER["altered_manifest"]["publication_allowed"])
        self.assertEqual(result["accepted"], TRANSFER["accepted"])
        self.assertEqual(result["quarantine"], TRANSFER["quarantine"])
        OUTPUTS["transfer_altered_manifest"] = result

    def test_dropped_required_column_is_a_batch_failure(self):
        contract, header, rows, manifest, dimensions = inputs("transfer-")
        column = TRANSFER["altered_header"]["dropped_column"]
        stripped = [{key: value for key, value in row.items() if key != column} for row in rows]
        result = validate_rows([name for name in header if name != column], stripped, contract, manifest, dimensions)
        self.assertIn({"rule": TRANSFER["altered_header"]["batch_failure_rule"], "column": column}, result["batch_failures"])
        self.assertEqual(result["publication_allowed"], TRANSFER["altered_header"]["publication_allowed"])
        self.assertEqual(result["accepted"], [])
        for item in result["quarantine"]:
            self.assertIn(TRANSFER["altered_header"]["every_row_reason"], item["reasons"])
        OUTPUTS["transfer_altered_header"] = result

    def test_redundant_equal_payload_under_new_event_is_disclosed_not_blocking(self):
        contract, header, rows, manifest, dimensions = inputs("transfer-")
        extra = TRANSFER["redundant_pair"]
        rows = rows + [{"_row_number": extra["row_number"], **extra["appended"]}]
        result = validate_rows(header, rows, contract, {**manifest, "delivered_rows": len(rows)}, dimensions)
        self.assertEqual(reasons_of(result, extra["row_number"]), extra["reasons"])
        self.assertEqual(result["publication_allowed"], extra["publication_allowed"])
        self.assertEqual(result["contradictions"], [])
        self.assertEqual([row["row_number"] for row in result["accepted"]], [row["row_number"] for row in TRANSFER["accepted"]])
        OUTPUTS["transfer_redundant"] = result

    def test_transfer_reason_counts_survive_row_order_reversal(self):
        contract, header, rows, manifest, dimensions = inputs("transfer-")
        reversed_rows = [{**row, "_row_number": index} for index, row in enumerate(reversed(rows), start=1)]
        result = validate_rows(header, reversed_rows, contract, manifest, dimensions)
        self.assertEqual(result["reason_counts"], TRANSFER["reason_counts"])
        self.assertTrue(result["publication_allowed"])


class NegativeValidatorTests(unittest.TestCase):
    """The deliberately wrong validator must fail for the documented reason."""

    def test_permissive_validator_fails_for_the_expected_reason(self):
        result = permissive_validator.validate(FIX / "inspections.csv", FIX / "plants.csv", FIX / "manifest.json", FIX / "contract.json")
        expected = PRIMARY["permissive_validator"]
        self.assertEqual({"accepted_count": result["accepted_count"], "quarantined_count": result["quarantined_count"],
                          "publication_allowed": result["publication_allowed"]},
                         {k: expected[k] for k in ("accepted_count", "quarantined_count", "publication_allowed")})
        accepted_numbers = [row["row_number"] for row in result["accepted"]]
        wrongly = sorted(set(accepted_numbers) - {row["row_number"] for row in PRIMARY["accepted"]})
        self.assertEqual(wrongly, expected["wrongly_accepted_row_numbers"])
        six = [row for row in result["accepted"] if row["row_number"] == 6][0]
        self.assertEqual((six["inspected_units"], six["defective_units"]), ("5", "7"), "7 defective of 5 inspected was accepted, as text")
        self.assertEqual(result["batch_failures"], [], "the manifest mismatch went unreported")
        self.assertNotEqual(actual(result), literal(PRIMARY))
        OUTPUTS["negative_permissive"] = {"accepted_count": result["accepted_count"], "wrongly_accepted": wrongly}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()
    started_at = datetime.now(timezone.utc)
    started = time.monotonic()
    suite = unittest.TestSuite()
    for case in (PrimaryContractTests, TransferTests, NegativeValidatorTests):
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    exit_code = 0 if result.wasSuccessful() else 1
    fixture_hashes = {str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path.read_bytes()).hexdigest()
                      for directory in ("fixtures", "expected", "solutions", "starters")
                      for path in sorted((ROOT / directory).iterdir()) if path.is_file()}
    output_hashes = {name: sha256(canonical(value).encode("utf-8")).hexdigest() for name, value in sorted(OUTPUTS.items())}
    evidence = {
        "lab": LAB, "executionClass": "local-executed",
        "python": platform.python_version(), "interpreter": sys.executable, "java": "not used", "spark": "not used",
        "packages": {}, "platform": platform.system() + " " + platform.release(),
        "startedAt": started_at.isoformat(), "finishedAt": datetime.now(timezone.utc).isoformat(),
        "durationSeconds": round(time.monotonic() - started, 3),
        "tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "skipped": len(result.skipped), "exit": exit_code,
        "fixtureHashes": fixture_hashes, "outputHashes": output_hashes,
        "commands": [f"{Path(sys.executable).name} run_tests.py --evidence <path>"],
        "notes": ("Plain Python standard library; the contract validator reads CSV text and JSON. Expected values are "
                  "hand-authored literals in expected/*.json with derivations in DATA.md. The permissive starter is "
                  "asserted to fail for its documented reason. No network, no Databricks, no Delta, nothing sent."),
    }
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: evidence[key] for key in ("lab", "python", "tests", "failures", "errors", "skipped", "exit")}, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
