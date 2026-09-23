"""Scrap-rate rules for Cinderline inspection records (STARTER: four gaps).

Pure functions: no Spark, no files, no network. The same code is unit-tested
on a laptop and called by the job's entry point, so the tested rules are the
deployed rules. All records are synthetic teaching data.

The gaps are numbered GAP 1 to GAP 4 below; TASKS.md, task 1, describes the
behaviour each one needs. Run `python run_tests.py --starter` from the lab
directory to see which package tests still fail.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Iterable

RATE_PLACES = Decimal("0.0001")
COUNT_FIELDS = ("inspected", "scrapped")


def _is_count(value: object) -> bool:
    """A count is a non-negative int; True and False are refused even though bool is an int."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def validate_record(record: dict) -> list[str]:
    """Return every reason a record cannot be counted; an empty list means it counts."""
    problems = [
        f"missing {field}" for field in ("line_id", *COUNT_FIELDS) if field not in record
    ]
    if problems:
        return problems
    line_id = record["line_id"]
    if not isinstance(line_id, str) or not line_id.strip():
        problems.append("line_id must be a non-empty string")
    for field in COUNT_FIELDS:
        if not _is_count(record[field]):
            problems.append(f"{field} must be a non-negative integer")
    # GAP 1: a record with more scrapped than inspected parts must be refused
    # with the reason "scrapped exceeds inspected" instead of being counted.
    return problems


def scrap_rate(scrapped: int, inspected: int) -> Decimal | None:
    """Scrapped over inspected, rounded half up to four places."""
    # GAP 2: a line where nothing was inspected has no rate (return None);
    # this line divides by zero.
    # GAP 3: float round() rounds half to even and drops trailing zeros, so
    # 1/32 becomes 0.0312 and 26/1000 prints as 0.026. Use Decimal division
    # and quantize(RATE_PLACES, rounding=ROUND_HALF_UP).
    return Decimal(str(round(scrapped / inspected, 4)))


def summarize_scrap(
    records: Iterable[dict], alert_threshold: Decimal
) -> tuple[list[dict], list[dict]]:
    """Aggregate the countable records per line (see the solution's docstring)."""
    totals: dict[str, list[int]] = {}
    rejected: list[dict] = []
    for index, record in enumerate(records):
        problems = validate_record(record)
        if problems:
            rejected.append(
                {"index": index, "line_id": record.get("line_id"), "reasons": problems}
            )
            continue
        counts = totals.setdefault(record["line_id"], [0, 0])
        counts[0] += record["inspected"]
        counts[1] += record["scrapped"]
    rows = []
    for line_id in sorted(totals):
        inspected, scrapped = totals[line_id]
        rate = scrap_rate(scrapped, inspected)
        rows.append(
            {
                "line_id": line_id,
                "inspected": inspected,
                "scrapped": scrapped,
                "scrap_rate": None if rate is None else str(rate),
                # GAP 4: the rule is "strictly greater than the threshold".
                "alert": rate is not None and rate >= alert_threshold,
            }
        )
    return rows, rejected
