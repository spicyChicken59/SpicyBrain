"""Starter for Tasks 2-4: an intentionally flawed resolver and an intentionally naive gate.

Repair them against fixtures/ and the independently authored expected/*.json.
Do not use anything here as a solution; solutions/reference.py is the unchanged
proven resolver and is only to be read AFTER your attempt.
"""


def flawed_current(rows):
    """Three operations, each wrong under the source contract.

    1. Rows whose quantities look plausible are kept; everything else is dropped
       silently, so an invalid LATEST revision disappears and an older valid row
       becomes "current" again.
    2. The last arrival per inspection wins, so transport order decides state.
    3. Nothing compares payloads at the same event ID or key/version, so a
       conflict is never noticed.
    """
    current = {}
    for row in rows:
        inspected, defective = row.get("inspected_units"), row.get("defective_units")
        if isinstance(inspected, int) and isinstance(defective, int) and 0 <= defective <= inspected:
            current[row.get("inspection_id")] = {
                "inspection_id": row.get("inspection_id"), "version": row.get("version"),
                "inspected_units": inspected, "defective_units": defective}
    return [current[key] for key in sorted(current, key=str)]


def naive_gate(result):
    """Publishes whenever no inspection key is listed as unresolved.

    Task 4 asks you to show, with fixtures/*-unkeyed.json, why this is not the
    publication rule. A conflict can exist with no usable key to list.
    """
    return not result.get("unresolved")


def resolve(history):
    """Implement: retain every raw row; quarantine with explicit reasons; detect
    event-ID and key/version payload conflicts over ALL retained history; find the
    highest observed revision per key BEFORE dropping invalid rows; accept only
    unambiguous valid current keys; block publication while any conflict or
    unresolved key remains. Return the same keys as solutions/reference.py.
    """
    raise NotImplementedError("Replace arrival-order logic with the stated source contract")
