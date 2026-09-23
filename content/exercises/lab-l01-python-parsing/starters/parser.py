"""Starter: the readers and the result shape are given; five gaps are yours.

Work through TASKS.md, fill the gaps until ``python3.12 run_tests.py --starter``
passes the same literals the solution passes, and only then open
solutions/parser.py. Every gap is marked GAP n with the behaviour it must
produce. As shipped, the starter is wrong in five observable ways, and the
test suite proves each one (see StarterGapTests in run_tests.py).
"""
import argparse
import csv
from datetime import date
from decimal import Decimal, InvalidOperation
import json
import logging
from pathlib import Path
import re
import sys

log = logging.getLogger("cinderline.parsing")

INTEGER_TEXT = re.compile(r"^[+-]?[0-9]+$")
DECIMAL_TEXT = re.compile(r"^[+-]?[0-9]+(?:\.[0-9]+)?$")
ISO_DATE_TEXT = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")

CONTRACT: tuple[dict, ...] = (
    {"name": "inspection_id", "type": "text", "required": True},
    {"name": "plant_id", "type": "text", "required": True},
    {"name": "inspected_on", "type": "date", "required": True},
    {"name": "inspected_units", "type": "integer", "required": True, "minimum": 0},
    {"name": "defective_units", "type": "integer", "required": True, "minimum": 0},
    {"name": "unit_cost", "type": "decimal", "required": False, "minimum": 0},
)


def to_text(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("not text")
    return value.strip()


def to_integer(value: object) -> int:
    """GAP 1: int() is too generous. It accepts True (as 1), 12.5 (as 12) and
    "1_000" (as 1000). Under the contract only an actual int (never a bool) or
    text matching INTEGER_TEXT after trimming is an integer; "12.0" and
    "twelve" raise ValueError."""
    return int(value)


def to_decimal(value: object) -> Decimal:
    """GAP 2: Decimal() is too generous and fails the wrong way. Decimal(5.1)
    exposes the binary fraction, so a JSON float must go through str() first;
    Decimal("1_000.50"), Decimal("1e3") and Decimal("NaN") all succeed, and
    Decimal("4,25") raises InvalidOperation, which is not a ValueError. Under
    the contract: bool raises ValueError; an int converts; a float converts
    through str() and must be finite; text must match DECIMAL_TEXT after
    trimming; everything else raises ValueError."""
    return Decimal(value)


def to_date(value: object) -> date:
    if not isinstance(value, str) or not ISO_DATE_TEXT.match(value.strip()):
        raise ValueError("not an ISO date")
    return date.fromisoformat(value.strip())


CONVERTERS = {"text": to_text, "integer": to_integer, "decimal": to_decimal, "date": to_date}


def is_blank(value: object) -> bool:
    return isinstance(value, str) and value.strip() == ""


def check_field(field: dict, raw: dict) -> tuple[object, str | None]:
    """GAP 3: keep four states apart and name each one. An absent key or a
    blank string is missing_<name> (only if required); a present None is
    null_<name> (only if required); a ValueError from the converter is
    malformed_<name>; a converted value under field["minimum"] is
    negative_<name>. Zero must pass. Below, missing, null, "" and 0 are merged
    and the minimum is never checked."""
    name = field["name"]
    if not raw.get(name):  # wrong: a JSON 0 and a JSON null both land here
        return None, ("missing_" + name if field["required"] else None)
    try:
        value = CONVERTERS[field["type"]](raw[name])
    except ValueError:
        return None, "malformed_" + name
    return value, None


def validate(raw: dict, contract: tuple[dict, ...] = CONTRACT) -> tuple[dict, list[str]]:
    """GAP 4: the cross-field rule is missing. When every field passed on its
    own and defective_units > inspected_units, append
    "defective_exceeds_inspected"."""
    typed: dict = {}
    reasons: list[str] = []
    for field in contract:
        value, reason = check_field(field, raw)
        typed[field["name"]] = value
        if reason:
            reasons.append(reason)
    return typed, reasons


def defect_rate(inspected_units: int, defective_units: int) -> float | None:
    if inspected_units == 0:
        return None
    return defective_units / inspected_units


def parse_records(records: list[dict], source: str, contract: tuple[dict, ...] = CONTRACT) -> tuple[list[dict], list[dict]]:
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
    """GAP 5: group by inspection_id. Same typed payload twice: keep the first,
    reject the repeat as exact_duplicate. Different payloads under one id:
    reject every record of the group as conflicting_duplicate. Log each
    rejection the way parse_records does. Below, nothing is checked."""
    return accepted, []


def parse_delivery(sources: list[tuple[str, list[dict]]], contract: tuple[dict, ...] = CONTRACT) -> dict:
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
    if isinstance(value, dict):
        return {key: json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def read_json(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as stream:
        records = json.load(stream)
    if not isinstance(records, list):
        raise ValueError(f"{path} must hold a JSON array of records")
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Parse Cinderline inspection deliveries (starter).")
    parser.add_argument("--csv", type=Path, action="append", default=[])
    parser.add_argument("--json", type=Path, action="append", default=[])
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s", stream=sys.stderr)
    sources = [(path.name, read_csv(path)) for path in args.csv] + [(path.name, read_json(path)) for path in args.json]
    print(json.dumps(json_ready(parse_delivery(sources)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
