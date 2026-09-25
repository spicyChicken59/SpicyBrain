"""The deliberately failing example for Lab L13: a cost sheet written in a hurry.

Run it from the lab directory and read what it prints, then the traceback:

    python3.12 starters/naive_model.py

It makes three mistakes that real spreadsheets make, and the tests in
run_tests.py assert each one for the reason given here:

1. naive_monthly_total() multiplies every quantity by its rate as if every
   quantity were per month. Operations effort is stated per WEEK, so the
   total is too low by the weeks it forgets.
2. naive_total_units() adds DBUs, instance-hours, GB-months and hours into
   one number. The result has no unit, no currency and no meaning.
3. naive_cost_per_1000() divides by work_items with no guard. The failed run
   r04 processed zero items, so the division raises ZeroDivisionError and
   every result computed before it is lost.

Do not fix this file; the reference answer is solutions/cost_model.py.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path


def naive_monthly_total(sheet: dict) -> float:
    total = 0.0
    for driver in sheet["drivers"]:
        if driver["period"] == "once":
            continue  # the one-off silently disappears from the story
        total += float(driver["quantity"]["base"]) * float(driver["rate"]["amount"])
    return round(total, 2)


def naive_total_units(sheet: dict) -> float:
    return float(sum(float(d["quantity"]["base"]) for d in sheet["drivers"] if d["period"] != "once"))


def naive_cost_per_1000(rows: list[dict], rate_per_unit: float) -> dict:
    costs = {}
    for row in rows:
        costs[row["run_id"]] = float(row["units_consumed"]) * rate_per_unit / int(row["work_items"]) * 1000
    return costs


if __name__ == "__main__":
    here = Path(__file__).resolve().parent.parent
    sheet = json.loads((here / "fixtures" / "worksheet.json").read_text(encoding="utf-8"))
    print("naive monthly total (base):", naive_monthly_total(sheet))
    print("naive 'total units' (base):", naive_total_units(sheet))
    with (here / "fixtures" / "runs.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    print("naive cost per 1,000 items:", naive_cost_per_1000(rows, 0.50))
