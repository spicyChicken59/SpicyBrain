"""Scrap-rate rules for Cinderline inspection records.

Pure functions: no Spark, no files, no network. The same code is unit-tested
on a laptop and called by the job's entry point, so the tested rules are the
deployed rules. All records are synthetic teaching data.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
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
    if not problems and record["scrapped"] > record["inspected"]:
        problems.append("scrapped exceeds inspected")
    return problems


def scrap_rate(scrapped: int, inspected: int) -> Decimal | None:
    """Scrapped over inspected, rounded half up to four places.

    Returns None when nothing was inspected: an idle line has no rate, and
    dividing by zero is not a rate of zero.
    """
    if inspected == 0:
        return None
    return (Decimal(scrapped) / Decimal(inspected)).quantize(
        RATE_PLACES, rounding=ROUND_HALF_UP
    )


def summarize_scrap(
    records: Iterable[dict], alert_threshold: Decimal
) -> tuple[list[dict], list[dict]]:
    """Aggregate the countable records per line.

    Returns (rows, rejected). Rows are sorted by line_id as strings; scrap_rate
    is a four-decimal string or None; alert is True only when the rate is
    strictly greater than the threshold. Each rejected record keeps its
    position in the input and every reason found. A line whose records were
    all rejected has no row.
    """
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
                "alert": rate is not None and rate > alert_threshold,
            }
        )
    return rows, rejected
