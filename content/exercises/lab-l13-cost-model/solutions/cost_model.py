"""Reference cost model for Lab L13: a reproducible worksheet and a cost experiment.

Standard library only. Every rate this model accepts is a synthetic teaching
rate that carries the label "hypothetical rate, not a price". The model never
fetches a price, never applies a discount and never converts one currency into
another. When it cannot turn an input into a defensible number it refuses with
a stable reason code instead of guessing.

Command line (run from the lab directory):

    python3.12 solutions/cost_model.py worksheet fixtures/worksheet.json
    python3.12 solutions/cost_model.py runs fixtures/runs.csv --rates fixtures/worksheet.json --driver "platform usage"
    python3.12 solutions/cost_model.py compare fixtures/alternatives.json

Each command prints JSON with sorted keys, so two runs over the same inputs
print the same bytes. A refusal prints {"refused": ...} and exits with status 2.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
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


# ---------------------------------------------------------------- helpers
def load_json(path) -> dict:
    """Read JSON with every number as a Decimal, so 0.1 stays 0.1."""
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
    """A quantity as written: 13.6 stays '13.6', 630 stays '630'."""
    text = format(value, "f")
    return text


def median(values: list[Decimal]) -> Decimal:
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


# ---------------------------------------------------------------- task 1: labelled rates
def check_rate(rate: dict, unit: str, currency: str, subject: str) -> Decimal:
    """Return the rate amount after checking its label, currency and unit."""
    if not isinstance(rate, dict) or rate.get("label") != RATE_LABEL:
        raise ModelRefusal("rate_not_labelled", subject, "every rate must say: " + RATE_LABEL)
    if rate.get("currency") != currency:
        raise ModelRefusal("currency_mismatch", subject, f"{rate.get('currency')} is not {currency}")
    if rate.get("per") != unit:
        raise ModelRefusal("rate_unit_mismatch", subject, f"rate per {rate.get('per')} for a quantity in {unit}")
    amount = decimal_of(rate.get("amount"), subject)
    if amount < 0:
        raise ModelRefusal("negative_rate", subject)
    return amount


# ---------------------------------------------------------------- task 2: periods
def to_monthly(quantity: Decimal, period: str, subject: str = "") -> Decimal:
    """A quantity stated per period, restated per month (multiply before dividing)."""
    if period == "week":
        return quantity * 52 / 12
    if period == "month":
        return quantity
    if period == "quarter":
        return quantity / 3
    if period == "year":
        return quantity / 12
    if period == ONE_OFF:
        raise ModelRefusal("one_off_not_recurring", subject, "a one-off is reported apart, never per month")
    raise ModelRefusal("unknown_period", subject, str(period))


# ---------------------------------------------------------------- task 3: low / base / high worksheet
def check_cases(quantity: dict, subject: str) -> dict:
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


def evaluate_worksheet(sheet: dict) -> dict:
    """Monthly amounts per driver and case, the swing, the ranking and the one-off apart.

    Each driver's amount is rounded to cents once; totals are sums of the
    rounded rows, so a reader can add the printed column and get the printed total.
    """
    currency = sheet.get("currency")
    if not currency:
        raise ModelRefusal("missing_currency", "worksheet")
    if sheet.get("normalizeTo", "month") != "month":
        raise ModelRefusal("unknown_period", "normalizeTo", str(sheet.get("normalizeTo")))
    drivers = sheet.get("drivers") or []
    if not drivers:
        raise ModelRefusal("no_drivers", "worksheet")
    recurring: dict[str, dict] = {}
    one_off: dict[str, dict] = {}
    for driver in drivers:
        name = driver.get("driver", "")
        if name in recurring or name in one_off:
            raise ModelRefusal("duplicate_driver", name)
        quantity = check_cases(driver.get("quantity"), name)
        unit = driver.get("unit", "")
        rate = check_rate(driver.get("rate"), unit, currency, name)
        period = driver.get("period")
        if period == ONE_OFF:
            amounts = {case: (quantity[case] * rate).quantize(CENT, rounding=ROUND_HALF_UP) for case in CASES}
            one_off[name] = {"unit": unit, "amounts": amounts}
        else:
            amounts = {
                case: (to_monthly(quantity[case], period, name) * rate).quantize(CENT, rounding=ROUND_HALF_UP)
                for case in CASES
            }
            recurring[name] = {"unit": unit, "sourcePeriod": period, "amounts": amounts}
    months = None
    if one_off:
        raw = sheet.get("amortizeOneOffMonths")
        if raw is None:
            raise ModelRefusal("amortization_months_required", "amortizeOneOffMonths")
        months = decimal_of(raw, "amortizeOneOffMonths")
        if months == 0:
            raise ModelRefusal("zero_denominator", "amortizeOneOffMonths", "cannot spread a one-off over zero months")
        if months < 0 or months != months.to_integral_value():
            raise ModelRefusal("malformed_number", "amortizeOneOffMonths", str(raw))
    totals = {case: sum((row["amounts"][case] for row in recurring.values()), Decimal("0.00")) for case in CASES}
    swing = {name: row["amounts"]["high"] - row["amounts"]["low"] for name, row in recurring.items()}
    ranking = sorted(recurring, key=lambda name: (-swing[name], name))
    one_off_total = {case: sum((row["amounts"][case] for row in one_off.values()), Decimal("0.00")) for case in CASES}
    result = {
        "currency": currency,
        "period": "month",
        "rateLabel": RATE_LABEL,
        "recurring": {
            name: {
                "unit": row["unit"],
                "sourcePeriod": row["sourcePeriod"],
                **{case: money(row["amounts"][case]) for case in CASES},
                "swing": money(swing[name]),
            }
            for name, row in recurring.items()
        },
        "recurringTotal": {**{case: money(totals[case]) for case in CASES}, "swing": money(totals["high"] - totals["low"])},
        "swingRanking": ranking,
        "largestSwing": ranking[0] if ranking else None,
        "oneOff": {
            name: {
                "unit": row["unit"],
                **{case: money(row["amounts"][case]) for case in CASES},
                "swing": money(row["amounts"]["high"] - row["amounts"]["low"]),
                "amortizedPerMonth": {case: money(row["amounts"][case] / months) for case in CASES},
            }
            for name, row in one_off.items()
        },
        "amortizeOneOffMonths": int(months) if months is not None else None,
        "recurringYear": {case: money(totals[case] * 12) for case in CASES},
        "yearOne": {case: money(totals[case] * 12 + one_off_total[case]) for case in CASES},
    }
    return result


# ---------------------------------------------------------------- task 4: comparable units
def sum_quantities(items: list[dict]) -> dict:
    """Add raw quantities only when they share one unit; otherwise refuse."""
    units = sorted({item.get("unit") for item in items})
    if len(units) != 1:
        raise ModelRefusal("incomparable_units", " + ".join(str(unit) for unit in units),
                           "convert each quantity with its own labelled rate first")
    total = sum((decimal_of(item.get("quantity"), units[0]) for item in items), Decimal(0))
    return {"quantity": plain(total), "unit": units[0]}


def compare_alternatives(doc: dict) -> dict:
    """Two alternatives, same drivers in the same units, converted to one currency per month."""
    currency = doc.get("currency")
    rates = doc.get("rates") or {}
    alternatives = doc.get("alternatives") or []
    if len(alternatives) != 2:
        raise ModelRefusal("two_alternatives_required", "alternatives", str(len(alternatives)))
    by_driver = [{d.get("driver"): d for d in alt.get("drivers", [])} for alt in alternatives]
    if set(by_driver[0]) != set(by_driver[1]):
        missing = sorted(set(by_driver[0]) ^ set(by_driver[1]))
        raise ModelRefusal("driver_sets_differ", ", ".join(missing), "both alternatives must price the same drivers")
    for name in sorted(by_driver[0]):
        if by_driver[0][name].get("unit") != by_driver[1][name].get("unit"):
            raise ModelRefusal("driver_units_differ", name,
                               f"{by_driver[0][name].get('unit')} against {by_driver[1][name].get('unit')}")
    priced = {}
    totals = []
    for alternative, drivers in zip(alternatives, by_driver):
        rows = {}
        for name in sorted(drivers):
            item = drivers[name]
            unit = item.get("unit")
            if unit not in rates:
                raise ModelRefusal("no_rate_for_unit", unit)
            rate = check_rate({**rates[unit], "per": unit}, unit, currency, unit)
            monthly = to_monthly(decimal_of(item.get("quantity"), name), item.get("period"), name)
            rows[name] = (monthly * rate).quantize(CENT, rounding=ROUND_HALF_UP)
        total = sum(rows.values(), Decimal("0.00"))
        totals.append(total)
        priced[alternative.get("name")] = {**{name: money(value) for name, value in rows.items()}, "total": money(total)}
    names = [alternative.get("name") for alternative in alternatives]
    lower = "equal" if totals[0] == totals[1] else names[totals.index(min(totals))]
    return {
        "currency": currency,
        "period": "month",
        "rateLabel": RATE_LABEL,
        "alternatives": priced,
        "difference": money(totals[0] - totals[1]),
        "lower": lower,
    }


# ---------------------------------------------------------------- task 5: the denominator
def cost_per_unit(cost, count, per=1) -> dict:
    """Cost divided by a count of work, or no value with the reason when the count is zero."""
    cost = decimal_of(cost, "cost")
    count = decimal_of(count, "count")
    per = decimal_of(per, "per")
    if cost < 0:
        raise ModelRefusal("negative_cost", "cost")
    if count < 0:
        raise ModelRefusal("negative_count", "count")
    if count == 0:
        return {"value": None, "reason": "zero_denominator"}
    return {"value": money(cost / count * per), "reason": None}


# ---------------------------------------------------------------- task 6: runs to cost per unit of work
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
    """Cost per `per` work items for each configuration, with spread, caveats and refusals."""
    unit = rate.get("per")
    amount = check_rate(rate, unit, rate.get("currency"), unit)
    groups: dict[str, list[tuple[Decimal, Decimal]]] = {}
    spent: dict[str, Decimal] = {}
    behind: dict[str, Decimal] = {}
    notes: dict[str, set] = {}
    refused = []
    for row in rows:
        run_id = row.get("run_id", "")
        configuration = row.get("configuration", "")
        notes.setdefault(configuration, set())
        try:
            work = decimal_of(row.get("work_items"), run_id)
            duration = decimal_of(row.get("duration_seconds"), run_id)
            units = decimal_of(row.get("units_consumed"), run_id)
        except ModelRefusal:
            refused.append({"runId": run_id, "configuration": configuration, "reason": "malformed_row"})
            continue
        if row.get("unit") != unit:
            refused.append({"runId": run_id, "configuration": configuration, "reason": "unit_mismatch"})
            notes[configuration].add("unit_mismatch_refused")
            continue
        spent[configuration] = spent.get(configuration, Decimal(0)) + units
        result = cost_per_unit(units * amount, work, per)
        if result["value"] is None:
            refused.append({"runId": run_id, "configuration": configuration, "reason": result["reason"]})
            notes[configuration].add("zero_work_excluded")
            continue
        behind[configuration] = behind.get(configuration, Decimal(0)) + units
        groups.setdefault(configuration, []).append((Decimal(result["value"]), duration))
    configurations = {}
    for name in sorted(groups):
        costs = [cost for cost, _ in groups[name]]
        durations = [duration for _, duration in groups[name]]
        middle = median(costs)
        caveats = set(notes.get(name, set()))
        if len(costs) == 1:
            caveats.add("single_observation")
        elif len(costs) < rank_min:
            caveats.add("few_observations")
        spread = None
        if len(costs) > 1 and middle != 0:
            spread = str(((max(costs) - min(costs)) / middle * 100).quantize(TENTH, rounding=ROUND_HALF_UP))
        configurations[name] = {
            "runsUsed": len(costs),
            "medianDurationSeconds": plain(median(durations)),
            "costPerWork": {"min": money(min(costs)), "median": money(middle), "max": money(max(costs))},
            "spreadPercent": spread,
            "unitsSpent": plain(spent.get(name, Decimal(0))),
            "unitsBehindWork": plain(behind.get(name, Decimal(0))),
            "caveats": sorted(caveats),
        }
    rankable = sorted((name for name in configurations if configurations[name]["runsUsed"] >= rank_min),
                      key=lambda name: (Decimal(configurations[name]["costPerWork"]["median"]), name))
    separated = None
    if len(rankable) >= 2:
        first, second = configurations[rankable[0]]["costPerWork"], configurations[rankable[1]]["costPerWork"]
        separated = Decimal(first["max"]) < Decimal(second["min"])
    return {
        "basis": {"unit": unit, "rate": money(amount), "currency": rate.get("currency"),
                  "rateLabel": RATE_LABEL, "perWorkItems": per},
        "rowsRead": len(rows),
        "rowsUsed": sum(len(values) for values in groups.values()),
        "refused": refused,
        "configurations": configurations,
        "ranking": {
            "byMedianCost": rankable,
            "notRankable": sorted(name for name in configurations if name not in rankable),
            "cheapestSeparated": separated,
        },
        "caveats": ["basis_unit_only", "hypothetical_rate", "synthetic_observations"],
    }


# ---------------------------------------------------------------- command line
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lab L13 cost model (synthetic rates only)")
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
