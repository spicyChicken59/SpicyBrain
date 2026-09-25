"""Unit tests for the scrap-rate rules.

Synthetic records; every expected value is worked out by hand in the comments
(and in DATA.md for the larger fixtures), never by calling the code under test.
"""

import unittest
from decimal import Decimal

from cinderline_quality.scrap import scrap_rate, summarize_scrap, validate_record

THRESHOLD = Decimal("0.0400")


class ScrapRuleTests(unittest.TestCase):
    def test_line_totals_and_rates(self):
        records = [
            {"line_id": "L1", "inspected": 480, "scrapped": 12},
            {"line_id": "L1", "inspected": 520, "scrapped": 14},
            {"line_id": "L2", "inspected": 300, "scrapped": 15},
            {"line_id": "L2", "inspected": 300, "scrapped": 12},
        ]
        rows, rejected = summarize_scrap(records, THRESHOLD)
        self.assertEqual(rejected, [])
        # L1: 26 / 1000 = 0.0260, not above 0.0400. L2: 27 / 600 = 0.0450, above.
        self.assertEqual(
            rows,
            [
                {"line_id": "L1", "inspected": 1000, "scrapped": 26, "scrap_rate": "0.0260", "alert": False},
                {"line_id": "L2", "inspected": 600, "scrapped": 27, "scrap_rate": "0.0450", "alert": True},
            ],
        )

    def test_rate_rounds_half_up_to_four_places(self):
        # 1 / 32 = 0.03125 exactly: half up gives 0.0313 (half even would give 0.0312).
        self.assertEqual(scrap_rate(1, 32), Decimal("0.0313"))
        self.assertEqual(scrap_rate(1, 7), Decimal("0.1429"))  # 0.142857...
        self.assertEqual(scrap_rate(2, 3), Decimal("0.6667"))  # 0.666...
        self.assertEqual(str(scrap_rate(0, 9)), "0.0000")

    def test_line_with_nothing_inspected_has_no_rate_and_no_alert(self):
        rows, rejected = summarize_scrap([{"line_id": "L4", "inspected": 0, "scrapped": 0}], THRESHOLD)
        self.assertEqual(rejected, [])
        self.assertEqual(rows, [{"line_id": "L4", "inspected": 0, "scrapped": 0, "scrap_rate": None, "alert": False}])

    def test_rate_equal_to_threshold_is_not_an_alert(self):
        # 10 / 250 = 0.0400: the rule is "strictly greater than".
        rows, _ = summarize_scrap([{"line_id": "L3", "inspected": 250, "scrapped": 10}], THRESHOLD)
        self.assertEqual(rows[0]["scrap_rate"], "0.0400")
        self.assertFalse(rows[0]["alert"])

    def test_more_scrapped_than_inspected_is_rejected_not_counted(self):
        records = [
            {"line_id": "L2", "inspected": 300, "scrapped": 15},
            {"line_id": "L2", "inspected": 40, "scrapped": 45},
        ]
        rows, rejected = summarize_scrap(records, THRESHOLD)
        self.assertEqual(rows[0]["inspected"], 300)
        self.assertEqual(rejected, [{"index": 1, "line_id": "L2", "reasons": ["scrapped exceeds inspected"]}])

    def test_negative_boolean_and_text_counts_are_rejected(self):
        self.assertEqual(
            validate_record({"line_id": "L1", "inspected": -5, "scrapped": 0}),
            ["inspected must be a non-negative integer"],
        )
        self.assertEqual(
            validate_record({"line_id": "L2", "inspected": True, "scrapped": 2}),
            ["inspected must be a non-negative integer"],
        )
        self.assertEqual(
            validate_record({"line_id": "L2", "inspected": 200, "scrapped": "3"}),
            ["scrapped must be a non-negative integer"],
        )

    def test_missing_fields_and_blank_line_are_rejected(self):
        self.assertEqual(validate_record({"line_id": "L3", "scrapped": 3}), ["missing inspected"])
        self.assertEqual(validate_record({"inspected": 1, "scrapped": 0}), ["missing line_id"])
        self.assertEqual(
            validate_record({"line_id": " ", "inspected": 1, "scrapped": 0}),
            ["line_id must be a non-empty string"],
        )

    def test_rows_are_sorted_by_line_as_text(self):
        records = [
            {"line_id": "L9", "inspected": 1, "scrapped": 0},
            {"line_id": "L10", "inspected": 1, "scrapped": 0},
            {"line_id": "L1", "inspected": 1, "scrapped": 0},
        ]
        rows, _ = summarize_scrap(records, THRESHOLD)
        self.assertEqual([row["line_id"] for row in rows], ["L1", "L10", "L9"])


if __name__ == "__main__":
    unittest.main()
