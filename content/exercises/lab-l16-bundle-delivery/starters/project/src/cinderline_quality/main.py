"""Entry point of the job's python_wheel_task (console script scrap_summary).

On Databricks the bundle would pass --catalog, --schema and --alert-threshold,
and the export would sit in a Unity Catalog volume under /Volumes. That was
not run in this lab. Here the same function runs on a temporary directory
passed as --volume-root, which is all a unit test can honestly exercise.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .params import export_dir, parse_params
from .scrap import summarize_scrap

INPUT_FILE = "inspections.json"
OUTPUT_FILE = "scrap_summary.json"


def main(argv: list[str] | None = None) -> int:
    params = parse_params(sys.argv[1:] if argv is None else argv)
    folder = Path(export_dir(params))
    records = json.loads((folder / INPUT_FILE).read_text(encoding="utf-8"))
    rows, rejected = summarize_scrap(records, params.alert_threshold)
    summary = {
        "catalog": params.catalog,
        "schema": params.schema,
        "alert_threshold": str(params.alert_threshold),
        "rows": rows,
        "rejected": rejected,
    }
    (folder / OUTPUT_FILE).write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
