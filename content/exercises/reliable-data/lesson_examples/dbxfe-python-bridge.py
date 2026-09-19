import json
import csv
from io import StringIO

def units(value):
    if type(value) is int:
        result = value
    elif isinstance(value, str) and value.strip().isdigit():
        result = int(value.strip())
    else:
        raise ValueError("quantity must be an integer")
    if result < 0:
        raise ValueError("quantity must be nonnegative")
    return result

def parse(rows):
    accepted, rejected = [], []
    for index, row in enumerate(rows):
        try:
            key = row.get("inspection_id")
            if not isinstance(key, str) or not key.strip():
                raise ValueError("inspection_id is required")
            if "inspected_units" not in row:
                raise ValueError("inspected_units is missing")
            count = units(row["inspected_units"])
            accepted.append({"inspection_id": key.strip(),
                             "inspected_units": count})
        except ValueError as error:
            rejected.append({"index": index, "raw": row,
                             "reason": str(error)})
    return accepted, rejected

rows = json.loads('[{"inspection_id":"A","inspected_units":"12"},'
                  '{"inspection_id":"B","inspected_units":null},'
                  '{"inspection_id":"C"}]')
accepted, rejected = parse(rows)
assert accepted == [{"inspection_id": "A", "inspected_units": 12}]
assert [r["reason"] for r in rejected] == [
    "quantity must be an integer", "inspected_units is missing"]
csv_rows = list(csv.DictReader(StringIO(
    "inspection_id,inspected_units\nD,8\nE,eight\n")))
assert parse(csv_rows)[0] == [{"inspection_id": "D", "inspected_units": 8}]
