"""Cinderline inspection parser: CSV and JSON records under one small contract.

Import it (``from solutions.parser import parse_delivery``) or run it as a
script from the lab directory::

    python3.12 solutions/parser.py --csv fixtures/inspections.csv --json fixtures/inspections.json

Importing runs nothing: the ``if __name__ == "__main__":`` guard at the bottom
keeps the script behaviour out of the import. The module reads no file on its
own; the caller hands it lists of records, so a test can alter a record in
memory without touching a fixture.

Reading order for a first visit: CONTRACT, the four ``to_*`` converters,
``check_field``, ``validate``, ``parse_records``, ``resolve_duplicates``,
``parse_delivery``, then ``main``.
"""
import argparse
import csv
from datetime import date
from decimal import Decimal
import json
import logging
from pathlib import Path
import re
import sys

# A logger named after the package. The module never configures handlers or
# levels; the program that runs it (main() below, or a test) decides where the
# lines go. A library that calls logging.basicConfig() hijacks its host.
log = logging.getLogger("cinderline.parsing")

INTEGER_TEXT = re.compile(r"^[+-]?[0-9]+$")
DECIMAL_TEXT = re.compile(r"^[+-]?[0-9]+(?:\.[0-9]+)?$")
ISO_DATE_TEXT = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")

# The contract: a tuple (fixed, ordered, not meant to be appended to) of small
# dictionaries, one per field, in the order reasons are reported. Every
# minimum in this contract is 0, which is why a value under it is reported as
# ``negative_<field>``.
CONTRACT: tuple[dict, ...] = (
    {"name": "inspection_id", "type": "text", "required": True},
    {"name": "plant_id", "type": "text", "required": True},
    {"name": "inspected_on", "type": "date", "required": True},
    {"name": "inspected_units", "type": "integer", "required": True, "minimum": 0},
    {"name": "defective_units", "type": "integer", "required": True, "minimum": 0},
    {"name": "unit_cost", "type": "decimal", "required": False, "minimum": 0},
)


# ---------------------------------------------------------------- conversions
# Each converter takes whatever the reader produced (a str from csv; an
# int/float/bool/str from json) and returns exactly one Python type, or raises
# ValueError. The policy is written here, not left to int(), Decimal() and
# date.fromisoformat(), which each accept more than this contract does.

def to_text(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("not text")
    return value.strip()


def to_integer(value: object) -> int:
    if type(value) is int:  # bool is a subclass of int: isinstance(True, int) is True, type(True) is int is False
        return value
    if isinstance(value, str) and INTEGER_TEXT.match(value.strip()):
        return int(value.strip())
    # int() alone would turn 12.5 into 12, True into 1 and "1_000" into 1000;
    # "12.0" and "twelve" are not integers under this contract either.
    raise ValueError("not an integer")


def to_decimal(value: object) -> Decimal:
    if isinstance(value, bool):
        raise ValueError("not a decimal")  # Decimal(True) would be Decimal('1')
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        result = Decimal(str(value))  # Decimal(5.1) exposes the binary fraction; str(5.1) is '5.1'
        if not result.is_finite():  # json.load turns a non-standard NaN or Infinity into a float
            raise ValueError("not a finite decimal")
        return result
    if isinstance(value, str) and DECIMAL_TEXT.match(value.strip()):
        return Decimal(value.strip())  # Decimal() alone would also take "1_000.50", "1e3" and "NaN"
    raise ValueError("not a decimal")  # "4,25" and "abc"


def to_date(value: object) -> date:
    if not isinstance(value, str) or not ISO_DATE_TEXT.match(value.strip()):
        raise ValueError("not an ISO date")  # "2026/09/03"; since 3.11 fromisoformat also takes "20260903"
    return date.fromisoformat(value.strip())  # raises ValueError for "2026-09-31": day is out of range for month


CONVERTERS = {"text": to_text, "integer": to_integer, "decimal": to_decimal, "date": to_date}


# ---------------------------------------------------------------- validation

def is_blank(value: object) -> bool:
    """An empty or whitespace-only string. A CSV cell that was left empty arrives as ""."""
    return isinstance(value, str) and value.strip() == ""


def check_field(field: dict, raw: dict) -> tuple[object, str | None]:
    """Return (typed value or None, reason or None) for one contract field.

    Four states are kept apart: the key is absent or the text is blank
    (missing), the key is present with None (null, which only JSON can send),
    the value cannot be converted (malformed), the value converts but is under
    the minimum (negative). Zero is a value and passes.
    """
    name = field["name"]
    if name not in raw or is_blank(raw[name]):
        return None, ("missing_" + name if field["required"] else None)
    if raw[name] is None:
        return None, ("null_" + name if field["required"] else None)
    try:
        value = CONVERTERS[field["type"]](raw[name])
    except ValueError:
        return None, "malformed_" + name
    if "minimum" in field and value < field["minimum"]:
        return value, "negative_" + name
    return value, None


def validate(raw: dict, contract: tuple[dict, ...] = CONTRACT) -> tuple[dict, list[str]]:
    """Return (typed record, reasons). An empty reasons list means accepted.

    Field rules run in contract order; the one cross-field rule runs only when
    every field passed on its own, so a record with a malformed quantity does
    not also collect a comparison it could never have passed.
    """
    typed: dict = {}
    reasons: list[str] = []
    for field in contract:
        value, reason = check_field(field, raw)
        typed[field["name"]] = value
        if reason:
            reasons.append(reason)
    if not reasons and typed["defective_units"] > typed["inspected_units"]:
        reasons.append("defective_exceeds_inspected")
    return typed, reasons


def defect_rate(inspected_units: int, defective_units: int) -> float | None:
    """Defects per inspected unit, or None when nothing was inspected (not 0.0)."""
    if inspected_units == 0:
        return None
    return defective_units / inspected_units


# ---------------------------------------------------------------- records

def parse_records(records: list[dict], source: str, contract: tuple[dict, ...] = CONTRACT) -> tuple[list[dict], list[dict]]:
    """Validate every record of one source. Nothing is dropped: each record ends
    up in exactly one of the two lists, and a rejected record keeps its raw
    input, its position (1-based) and its reasons."""
    accepted: list[dict] = []
    rejected: list[dict] = []
    for position, raw in enumerate(records, start=1):
        typed, reasons = validate(raw, contract)
        if reasons:
            rejected.append({"source": source, "position": position, "raw": raw, "reasons": reasons})
            log.warning("rejected %s position %d: %s", source, position, ", ".join(reasons))
        else:
            accepted.append({"source": source, "position": position, "raw": raw, **typed,
                             "defect_rate": defect_rate(typed["inspected_units"], typed["defective_units"])})
    return accepted, rejected


def resolve_duplicates(accepted: list[dict], contract: tuple[dict, ...] = CONTRACT) -> tuple[list[dict], list[dict]]:
    """Cross-record rule over records that passed on their own.

    Two records with the same inspection_id and the same typed payload are an
    exact duplicate: the first is kept, the repeat is rejected. Two with the
    same inspection_id and different payloads are a conflict: neither can be
    shown to be the honest one, so both are rejected.
    """
    names = [field["name"] for field in contract]
    groups: dict[str, list[dict]] = {}
    for record in accepted:
        groups.setdefault(record["inspection_id"], []).append(record)
    kept: list[dict] = []
    rejected: list[dict] = []
    for record in accepted:
        group = groups[record["inspection_id"]]
        payloads = {tuple(item[name] for name in names) for item in group}  # a set of tuples: distinct payloads
        if len(payloads) > 1:
            reason = "conflicting_duplicate"
        elif record is not group[0]:
            reason = "exact_duplicate"
        else:
            kept.append(record)
            continue
        rejected.append({"source": record["source"], "position": record["position"], "raw": record["raw"], "reasons": [reason]})
        log.warning("rejected %s position %d: %s", record["source"], record["position"], reason)
    return kept, rejected


def parse_delivery(sources: list[tuple[str, list[dict]]], contract: tuple[dict, ...] = CONTRACT) -> dict:
    """Run every source through parse_records, then the duplicate rule across
    all of them. The result carries typed accepted records (date and Decimal
    objects) and rejected records with their raw input."""
    accepted: list[dict] = []
    rejected: list[dict] = []
    for source, records in sources:
        good, bad = parse_records(records, source, contract)
        accepted.extend(good)
        rejected.extend(bad)
    accepted, duplicates = resolve_duplicates(accepted, contract)
    rejected.extend(duplicates)
    order = {source: index for index, (source, _) in enumerate(sources)}
    rejected.sort(key=lambda item: (order[item["source"]], item["position"]))
    raw_count = sum(len(records) for _, records in sources)
    # An assertion states an invariant of this code, not a rule about input.
    # python -O strips it; input rules therefore live in validate(), never here.
    assert len(accepted) + len(rejected) == raw_count, "every record is accepted or rejected exactly once"
    reason_counts: dict[str, int] = {}
    for item in rejected:
        for reason in item["reasons"]:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
    return {
        "raw_count": raw_count,
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "accepted": [{key: value for key, value in record.items() if key != "raw"} for record in accepted],
        "rejected": rejected,
        "reason_counts": dict(sorted(reason_counts.items())),
    }


def json_ready(value: object) -> object:
    """Turn dates and Decimals into strings so json.dumps can write the result.
    JSON has no date or decimal type; the text form is the honest one."""
    if isinstance(value, dict):
        return {key: json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


# ---------------------------------------------------------------- readers

def read_csv(path: Path) -> list[dict]:
    """Every value a str; an empty cell is ""; the header row supplies the keys."""
    with open(path, encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def read_json(path: Path) -> list[dict]:
    """null becomes None, numbers become int or float, true becomes True; a
    missing key is simply absent from the dictionary."""
    with open(path, encoding="utf-8") as stream:
        records = json.load(stream)
    if not isinstance(records, list):
        raise ValueError(f"{path} must hold a JSON array of records")
    return records


# ---------------------------------------------------------------- script

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Parse Cinderline inspection deliveries.")
    parser.add_argument("--csv", type=Path, action="append", default=[], help="a CSV delivery (repeatable)")
    parser.add_argument("--json", type=Path, action="append", default=[], help="a JSON delivery (repeatable)")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s", stream=sys.stderr)
    sources = [(path.name, read_csv(path)) for path in args.csv] + [(path.name, read_json(path)) for path in args.json]
    result = parse_delivery(sources)
    print(json.dumps(json_ready(result), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
