"""Starter for Lab L13. Fill the six gaps in the order of TASKS.md.

The helpers at the top are complete. Every function marked "Task n" raises
NotImplementedError until you write it; `python3.12 run_tests.py --starter`
judges this file by the same hand-authored literals as the reference, so it
fails until every task is done. Rates must carry the label
"hypothetical rate, not a price"; never type a price you read somewhere.
"""
from __future__ import annotations

import argparse
import csv
import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

RATE_LABEL = "hypothetical rate, not a price"
CASES = ("low", "base", "high")
ONE_OFF = "once"
RECURRING_PERIODS = ("week", "month", "quarter", "year")
CENT = Decimal("0.01")
TENTH = Decimal("0.1")
RUN_COLUMNS = ["run_id", "configuration", "work_items", "duration_seconds", "units_consumed", "unit"]


class ModelRefusal(ValueError):
    """An input the model will not turn into a number, with a stable reason code."""

    def __init__(self, reason: str, subject: str = "", detail: str = ""):
        self.reason = reason
        self.subject = subject
        self.detail = detail
        super().__init__(" ".join(part for part in (reason, subject, detail) if part))

    def as_dict(self) -> dict:
        return {"reason": self.reason, "subject": self.subject}


def load_json(path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"), parse_float=Decimal, parse_int=Decimal)


def decimal_of(value, subject: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ModelRefusal("malformed_number", subject, repr(value)) from None
    if not number.is_finite():
        raise ModelRefusal("malformed_number", subject, repr(value))
    return number


def money(value: Decimal) -> str:
    return str(value.quantize(CENT, rounding=ROUND_HALF_UP))


def plain(value: Decimal) -> str:
    return format(value, "f")


def median(values: list[Decimal]) -> Decimal:
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def check_cases(quantity: dict, subject: str) -> dict:
    """Given: low, base and high as Decimals, non-negative and in order."""
    if not isinstance(quantity, dict):
        raise ModelRefusal("missing_case", subject, "quantity needs low, base and high")
    values = {}
    for case in CASES:
        if case not in quantity:
            raise ModelRefusal("missing_case", subject, case)
        value = decimal_of(quantity[case], subject)
        if value < 0:
            raise ModelRefusal("negative_quantity", subject, case)
        values[case] = value
    if not values["low"] <= values["base"] <= values["high"]:
        raise ModelRefusal("cases_out_of_order", subject, "low <= base <= high is required")
    return values


def check_rate(rate: dict, unit: str, currency: str, subject: str) -> Decimal:
    """Task 1: return the amount only if label, currency and per-unit all match.

    Refuse with rate_not_labelled, currency_mismatch, rate_unit_mismatch or
    negative_rate, in that order of checking.
    """
    raise NotImplementedError("Task 1: check the rate's label, currency and unit before using it")


def to_monthly(quantity: Decimal, period: str, subject: str = "") -> Decimal:
    """Task 2: restate a quantity per month; refuse 'once' and unknown periods."""
    if period == "month":
        return quantity
    raise NotImplementedError("Task 2: normalize week, quarter and year to month; refuse once and unknown periods")


def evaluate_worksheet(sheet: dict) -> dict:
    """Task 3: monthly amounts per driver and case, totals, swing, ranking, one-off apart."""
    raise NotImplementedError("Task 3: build the low/base/high worksheet with the one-off reported apart")


def sum_quantities(items: list[dict]) -> dict:
    """Task 4a: add raw quantities only when every item has the same unit."""
    raise NotImplementedError("Task 4: refuse a sum across different billing units")


def compare_alternatives(doc: dict) -> dict:
    """Task 4b: same drivers, same units, one currency per month, then compare."""
    raise NotImplementedError("Task 4: compare alternatives only after converting each driver with its own rate")


def cost_per_unit(cost, count, per=1) -> dict:
    """Task 5: {'value': ..., 'reason': None}, or {'value': None, 'reason': 'zero_denominator'}."""
    raise NotImplementedError("Task 5: guard the denominator; zero work is unknown, not zero and not a crash")


def read_runs(path) -> list[dict]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != RUN_COLUMNS:
            raise ModelRefusal("unexpected_columns", str(path), ",".join(reader.fieldnames or []))
        return [dict(row) for row in reader]


def rate_from_worksheet(sheet: dict, driver_name: str) -> dict:
    for driver in sheet.get("drivers", []):
        if driver.get("driver") == driver_name:
            rate = driver.get("rate") or {}
            check_rate(rate, driver.get("unit", ""), sheet.get("currency"), driver_name)
            return {**rate, "currency": sheet.get("currency")}
    raise ModelRefusal("no_rate_for_unit", driver_name)


def summarize_runs(rows: list[dict], rate: dict, per: int = 1000, rank_min: int = 3) -> dict:
    """Task 6: cost per `per` work items per configuration, with spread, caveats and refusals."""
    raise NotImplementedError("Task 6: turn run observations into cost per unit of work with caveats")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lab L13 cost model starter")
    commands = parser.add_subparsers(dest="command", required=True)
    worksheet = commands.add_parser("worksheet")
    worksheet.add_argument("path")
    runs = commands.add_parser("runs")
    runs.add_argument("path")
    runs.add_argument("--rates", required=True)
    runs.add_argument("--driver", default="platform usage")
    runs.add_argument("--per", type=int, default=1000)
    compare = commands.add_parser("compare")
    compare.add_argument("path")
    args = parser.parse_args(argv)
    try:
        if args.command == "worksheet":
            output = evaluate_worksheet(load_json(args.path))
        elif args.command == "runs":
            rate = rate_from_worksheet(load_json(args.rates), args.driver)
            output = summarize_runs(read_runs(args.path), rate, per=args.per)
        else:
            output = compare_alternatives(load_json(args.path))
    except ModelRefusal as refusal:
        print(json.dumps({"refused": refusal.as_dict()}, sort_keys=True, indent=2))
        return 2
    print(json.dumps(output, sort_keys=True, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
