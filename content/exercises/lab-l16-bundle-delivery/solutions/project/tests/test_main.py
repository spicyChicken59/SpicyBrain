"""The entry point on a temporary directory standing in for the volume root.

This runs the job's own entry point locally. It proves the wiring from
parameters to files; it does not prove that a Databricks job can read the
real volume, which needs a workspace and was not run.
"""

import json
import tempfile
import unittest
from pathlib import Path

from cinderline_quality.main import main


class EntryPointTests(unittest.TestCase):
    def test_reads_the_export_and_writes_the_summary_under_the_volume_root(self):
        with tempfile.TemporaryDirectory(prefix="lab-l16-main-") as root:
            folder = Path(root, "cinderline_test", "quality", "exports")
            folder.mkdir(parents=True)
            records = [
                {"line_id": "L2", "inspected": 300, "scrapped": 15},
                {"line_id": "L2", "inspected": 40, "scrapped": 45},
            ]
            (folder / "inspections.json").write_text(json.dumps(records), encoding="utf-8")
            code = main([
                "--catalog", "cinderline_test", "--schema", "quality",
                "--alert-threshold", "0.0400", "--volume-root", root,
            ])
            self.assertEqual(code, 0)
            summary = json.loads((folder / "scrap_summary.json").read_text(encoding="utf-8"))
        # 15 / 300 = 0.0500, above 0.0400; the 45-of-40 record is refused.
        self.assertEqual(
            summary["rows"],
            [{"alert": True, "inspected": 300, "line_id": "L2", "scrap_rate": "0.0500", "scrapped": 15}],
        )
        self.assertEqual(summary["rejected"], [{"index": 1, "line_id": "L2", "reasons": ["scrapped exceeds inspected"]}])
        self.assertEqual(
            (summary["catalog"], summary["schema"], summary["alert_threshold"]),
            ("cinderline_test", "quality", "0.0400"),
        )


if __name__ == "__main__":
    unittest.main()
