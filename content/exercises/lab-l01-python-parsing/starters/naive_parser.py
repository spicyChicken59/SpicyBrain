"""Deliberately naive parser: it trusts int() and never keeps what it drops.

Run it from the lab directory and read the traceback before SOLUTIONS.md:

    python3.12 starters/naive_parser.py

run_tests.py asserts where and why it fails: on the CSV it stops at the
int() line for CLN-003 ('twelve'); on the JSON it stops at the same line for
CLS-002 (a null); and on two JSON records it is silently wrong.
"""
import csv
from pathlib import Path


def parse(rows):
    accepted = []
    for row in rows:
        units = int(row["inspected_units"])
        defects = int(row["defective_units"])
        if units < 0 or defects < 0 or defects > units:
            continue
        accepted.append({"inspection_id": row["inspection_id"], "inspected_units": units, "defective_units": defects})
    return accepted


if __name__ == "__main__":
    path = Path(__file__).resolve().parent.parent / "fixtures" / "inspections.csv"
    with open(path, encoding="utf-8", newline="") as stream:
        print(parse(list(csv.DictReader(stream))))
