"""Every academy-check warning on retained material carries its own decision."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class WarningDispositionTest(unittest.TestCase):
    def test_each_warning_has_an_individual_reasoned_disposition(self):
        coverage = json.loads((ROOT / "docs/academy/COVERAGE.json").read_text())
        dispositions = json.loads((ROOT / "docs/academy/warning-dispositions.json").read_text())
        warned = {(f["where"], f["message"]) for f in coverage["findings"] if f["level"] == "warn"}
        decided = {(i["where"], i["warning"]): i for i in dispositions["items"]}
        self.assertEqual(sorted(warned - decided.keys()), [], "warnings without a disposition")
        self.assertEqual(sorted(decided.keys() - warned), [], "dispositions for warnings that no longer occur")
        for key, item in decided.items():
            self.assertIn(item["disposition"], ("kept", "fixed"), key)
            self.assertGreater(len(item["reason"].split()), 12, key)


if __name__ == "__main__":
    unittest.main()
