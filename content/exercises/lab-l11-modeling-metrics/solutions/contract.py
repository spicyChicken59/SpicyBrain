"""Validate the metric contract and turn it into query parameters.

A contract is only useful if an incomplete one is refused before anyone builds
the table. problems() returns every reason a contract is not usable; an empty
list means it is complete enough to drive model.sql.
"""

REQUIRED = ("metric", "version", "owner", "grain", "numerator", "denominator", "same_population",
            "unit", "period", "empty_cases", "unknown_member", "tests")


def problems(contract):
    found = []
    for key in REQUIRED:
        value = contract.get(key)
        if value is None or value == "" or value == [] or value == {}:
            found.append("missing %s" % key)
    if found:
        return found
    numerator, denominator = contract["numerator"], contract["denominator"]
    if contract["same_population"] is not True or numerator.get("population") != denominator.get("population"):
        found.append("numerator and denominator populations differ")
    quantity = contract["unit"].get("quantity")
    if not quantity or numerator.get("unit") != quantity or denominator.get("unit") != quantity:
        found.append("numerator, denominator and unit disagree")
    window = contract["period"].get("window") or {}
    length = window.get("length")
    if window.get("kind") != "business_days" or not isinstance(length, int) or isinstance(length, bool) or length < 1:
        found.append("window must be a positive whole number of business days")
    if not contract["period"].get("day"):
        found.append("business day boundary is not stated")
    empty = contract["empty_cases"]
    if empty.get("rate_when_empty") is not None:
        found.append("an empty or zero denominator must give no rate")
    if not empty.get("zero_denominator_status") or not empty.get("no_rows_status"):
        found.append("empty-case statuses are not named")
    unknown = contract["unknown_member"]
    if not isinstance(unknown.get("line_sk"), int) or not unknown.get("plant_id"):
        found.append("unknown member is not defined")
    return found


def parameters(contract):
    """Named parameters for model.sql; refuses an unusable contract."""
    issues = problems(contract)
    if issues:
        raise ValueError("metric contract refused: " + "; ".join(issues))
    return {
        "window_days": contract["period"]["window"]["length"],
        "unknown_line_sk": contract["unknown_member"]["line_sk"],
        "unknown_plant_id": contract["unknown_member"]["plant_id"],
        "zero_status": contract["empty_cases"]["zero_denominator_status"],
        "empty_status": contract["empty_cases"]["no_rows_status"],
    }
