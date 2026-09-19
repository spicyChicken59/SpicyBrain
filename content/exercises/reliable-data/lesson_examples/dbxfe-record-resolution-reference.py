"""Original fictional teaching policy, deliberately recomputing retained history.

This is neither a streaming engine nor a database CDC connector. No network
calls, real notifications, Delta commands, or Databricks services are used.
"""
from copy import deepcopy
from hashlib import sha256
import csv
import json

FIELDS = ("event_id", "inspection_id", "version", "inspected_units", "defective_units")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def positive_int(value):
    # bool is a Python int subclass: reject True instead of treating it as v1.
    return type(value) is int and 0 < value <= 2147483647


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def reasons(row):
    errors = []
    for key in ("event_id", "inspection_id"):
        if not nonempty(row.get(key)):
            errors.append("missing_" + key)
    if not positive_int(row.get("version")):
        errors.append("invalid_version")
    for key in ("inspected_units", "defective_units"):
        value = row.get(key)
        if value is None:
            errors.append("missing_" + key)
        elif type(value) is not int or not 0 <= value <= 2147483647:
            errors.append("invalid_" + key)
    inspected, defective = row.get("inspected_units"), row.get("defective_units")
    if type(inspected) is int and type(defective) is int and defective > inspected:
        errors.append("defective_exceeds_inspected")
    return errors


def resolve(history):
    """Return evidence, row-quality failures, reconciled state, and coverage.

    Revision numbers order one inspection, not different inspections. Delivery
    IDs identify immutable payloads; arrival position is never the tie-breaker.
    Exact repeats are audit evidence, not another business inspection.
    """
    rows = [deepcopy(row) for row in history]
    by_event, by_revision, by_key = {}, {}, {}
    quarantine = []
    for index, row in enumerate(rows):
        errors = reasons(row)
        if errors:
            quarantine.append({"raw_index": index, "row": row, "reasons": errors})
        event, key, revision = row.get("event_id"), row.get("inspection_id"), row.get("version")
        payload = {field: row.get(field) for field in FIELDS}
        if nonempty(event):
            by_event.setdefault(event, {}).setdefault(canonical(payload), []).append(index)
        if nonempty(key):
            by_key.setdefault(key, []).append((index, row, errors))
            if positive_int(revision):
                quantities = {field: row.get(field) for field in ("inspected_units", "defective_units")}
                by_revision.setdefault((key, revision), {}).setdefault(canonical(quantities), []).append(index)

    conflicts, blocked = [], set()
    for event, payloads in sorted(by_event.items()):
        if len(payloads) > 1:
            indices = sorted(index for group in payloads.values() for index in group)
            conflicts.append({"kind": "event_id", "identity": event, "raw_indices": indices})
            blocked.update(rows[index]["inspection_id"] for index in indices
                           if nonempty(rows[index].get("inspection_id")))
    for (key, revision), payloads in sorted(by_revision.items()):
        if len(payloads) > 1:
            conflicts.append({"kind": "key_version", "identity": [key, revision],
                              "raw_indices": sorted(index for group in payloads.values() for index in group)})
            blocked.add(key)

    accepted, excluded = [], []
    for key, evidence in sorted(by_key.items()):
        valid = [row for _, row, errors in evidence if not errors]
        ordered = [row for _, row, _ in evidence if positive_int(row.get("version"))]
        if not valid:
            # Baseline B never had any valid state. Its exclusion is disclosed.
            if key not in blocked:
                excluded.append(key)
            continue
        if any(not positive_int(row.get("version")) for _, row, _ in evidence):
            blocked.add(key)  # Cannot prove the current version of a known key.
        highest = max(row["version"] for row in ordered)
        latest = [(row, errors) for _, row, errors in evidence if row.get("version") == highest]
        if any(errors for _, errors in latest):
            blocked.add(key)  # Do not filter out invalid v3 then resurrect v2.
        if key in blocked:
            continue
        # Uniqueness was proved above. All remaining equal-version quantities agree.
        selected = latest[0][0]
        accepted.append({field: selected[field] for field in FIELDS[1:]})

    total = sum(row["inspected_units"] for row in accepted)
    defective = sum(row["defective_units"] for row in accepted)
    return {
        "raw_count": len(rows), "raw": rows, "accepted": accepted,
        "quarantine": quarantine, "conflicts": conflicts, "excluded_keys": excluded,
        # Provenance can conflict even when no usable inspection key is known.
        "unresolved": sorted(blocked), "publication_allowed": not conflicts and not blocked,
        "totals": {"inspected_units": total, "defective_units": defective,
                   "defect_rate": defective / total if total else None},
        "coverage": "Accepted inspections only; quarantined/excluded inputs are not complete source coverage.",
    }


def guarded_upsert(target, source):
    """Local target-update model after source resolution, not SQL MERGE execution.

    Input rows have business fields only, one row per inspection. Unknown
    absence is not deletion. Validate ambiguity before touching the target.
    A caller must separately enforce the resolver's publication_allowed gate.
    """
    state = {row["inspection_id"]: deepcopy(row) for row in target}
    if len(state) != len(target):
        raise ValueError("target is not unique at inspection grain")
    keys = [row["inspection_id"] for row in source]
    if len(set(keys)) != len(keys):
        raise ValueError("ambiguous source matches; resolve before update")
    for incoming in source:
        key = incoming["inspection_id"]
        current = state.get(key)
        if current is None or incoming["version"] > current["version"]:
            state[key] = deepcopy(incoming)
        elif incoming["version"] == current["version"] and incoming != current:
            raise ValueError("equal version disagrees with target")
        # Equal-and-identical or older source is a no-op, not an increment.
    return [state[key] for key in sorted(state)]


class LocalPipeline:
    """In-memory dependency/failure simulation, not durable orchestration.

    Boundaries: retained_raw -> resolved_state -> published_snapshot -> local_effect.
    A production design needs actual durable transactions/outbox storage and a
    recipient's idempotency agreement. A Python dictionary is not that guarantee.
    """
    def __init__(self):
        self.raw = []
        self.resolved = None
        self.published = None
        self.status = "not_published"
        self.outbox = {}

    def ingest(self, batch, fail_after=None):
        self.raw.extend(deepcopy(batch))
        self.status = "stale_previous" if self.published else "not_published"
        if fail_after == "retained_raw":
            raise RuntimeError("Injected failure after retained_raw")
        return self.recover(fail_after)

    def recover(self, fail_after=None):
        self.resolved = resolve(self.raw)
        if fail_after == "resolved_state":
            raise RuntimeError("Injected failure after resolved_state")
        if not self.resolved["publication_allowed"]:
            self.status = "stale_previous" if self.published else "blocked_no_snapshot"
            return self.resolved
        snapshot = {field: deepcopy(self.resolved[field]) for field in
                    ("accepted", "totals", "excluded_keys", "coverage")}
        snapshot_id = sha256(canonical(snapshot).encode()).hexdigest()
        self.published = {"snapshot_id": snapshot_id, **snapshot}
        self.status = "current_with_exclusions" if snapshot["excluded_keys"] else "current"
        if fail_after == "published_snapshot":
            raise RuntimeError("Injected failure after published_snapshot")
        # setdefault models a receiver keyed by snapshot ID; it sends nothing.
        self.outbox.setdefault(snapshot_id, {"kind": "local_notification", "snapshot_id": snapshot_id})
        return self.resolved


def parse_bridge(path):
    """CSV text is parsed explicitly; no truthiness shortcut turns missing into zero."""
    accepted, rejected = [], []
    with open(path, encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            text = row.get("units")
            try:
                if text is None or text.strip() == "":
                    raise ValueError("missing units")
                try:
                    units = int(text)
                except ValueError:
                    raise ValueError("malformed integer") from None
                if units < 0:
                    raise ValueError("negative units")
                accepted.append({"record_id": row["record_id"], "units": units})
            except ValueError as error:
                rejected.append({"record_id": row["record_id"], "reason": str(error)})
    return {"accepted": accepted, "rejected": rejected}
