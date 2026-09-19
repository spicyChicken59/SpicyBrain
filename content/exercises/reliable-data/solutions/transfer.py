"""Different contract: composite order-line keys, cents, explicit cancellation."""
import json


def reconcile_orders(events):
    grouped = {}
    for event in events:
        key = (event["order_id"], event["line_id"])
        for field in ("revision", "quantity", "unit_cents"):
            if type(event[field]) is not int or event[field] < (1 if field == "revision" else 0):
                raise ValueError("invalid " + field)
        if event["operation"] not in ("upsert", "cancel"):
            raise ValueError("unknown operation")
        if event["operation"] == "cancel" and event["quantity"] != 0:
            raise ValueError("cancellation must carry zero quantity")
        grouped.setdefault(key, {}).setdefault(event["revision"], set()).add(
            json.dumps(event, sort_keys=True))
    current = []
    for revisions in grouped.values():
        latest = revisions[max(revisions)]
        if len(latest) != 1:
            raise ValueError("ambiguous current line")
        current.append(json.loads(next(iter(latest))))
    totals, cancelled = {}, []
    for row in current:
        if row["operation"] == "cancel":
            cancelled.append([row["order_id"], row["line_id"]])
        else:
            totals[row["order_id"]] = totals.get(row["order_id"], 0) + row["quantity"] * row["unit_cents"]
    return {"order_cents": dict(sorted(totals.items())), "total_cents": sum(totals.values()),
            "current_line_count": len(current), "active_line_count": len(current) - len(cancelled),
            "cancelled_keys": sorted(cancelled)}
