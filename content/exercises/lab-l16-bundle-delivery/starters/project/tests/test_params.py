"""Unit tests for the job parameters the bundle passes to the wheel task."""

import unittest
from decimal import Decimal
from pathlib import PurePosixPath

from cinderline_quality.params import JobParams, export_dir, parse_params, table_name

TEST_ARGS = ["--catalog", "cinderline_test", "--schema", "quality", "--alert-threshold", "0.0400"]


class ParamsTests(unittest.TestCase):
    def test_parses_the_parameters_the_bundle_passes(self):
        self.assertEqual(
            parse_params(TEST_ARGS),
            JobParams("cinderline_test", "quality", Decimal("0.0400"), "/Volumes"),
        )

    def test_identifiers_must_be_plain_lowercase(self):
        bad_catalog = ["--catalog", "Cinderline-Prod", *TEST_ARGS[2:]]
        with self.assertRaisesRegex(ValueError, "--catalog 'Cinderline-Prod' is not a plain lowercase identifier"):
            parse_params(bad_catalog)
        bad_schema = ["--catalog", "cinderline_test", "--schema", "quality; drop", "--alert-threshold", "0.0400"]
        with self.assertRaisesRegex(ValueError, "--schema"):
            parse_params(bad_schema)

    def test_threshold_is_a_number_between_zero_and_one(self):
        for value, message in [("4%", "is not a number"), ("0", "between 0 and 1"), ("1.5", "between 0 and 1")]:
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, message):
                    parse_params([*TEST_ARGS[:4], "--alert-threshold", value])

    def test_unknown_repeated_and_missing_parameters_are_refused(self):
        with self.assertRaisesRegex(ValueError, "unknown parameter '--token'"):
            parse_params([*TEST_ARGS, "--token", "x"])
        with self.assertRaisesRegex(ValueError, "given twice"):
            parse_params([*TEST_ARGS, "--catalog", "cinderline_prod"])
        with self.assertRaisesRegex(ValueError, r"missing parameter\(s\): --alert-threshold"):
            parse_params(TEST_ARGS[:4])
        with self.assertRaisesRegex(ValueError, "has no value"):
            parse_params([*TEST_ARGS[:4], "--alert-threshold"])

    def test_names_and_paths_come_from_the_parameters(self):
        params = parse_params(TEST_ARGS)
        self.assertEqual(table_name(params, "scrap_summary"), "cinderline_test.quality.scrap_summary")
        self.assertEqual(export_dir(params), PurePosixPath("/Volumes/cinderline_test/quality/exports"))
        with self.assertRaises(ValueError):
            table_name(params, "Scrap-Summary")


if __name__ == "__main__":
    unittest.main()
