"""Data-contract validator: rows fail with reasons into quarantine, batch rules block publication.

Original fictional teaching policy over CSV text. Standard library only; no
network, no database, no Databricks. `validate()` reads files; `validate_rows()`
takes in-memory rows so tests can alter an input without touching a fixture.
"""
import csv
from datetime import date
import json
from pathlib import Path
import re

INTEGER_TEXT = re.compile(r"^[+-]?[0-9]+$")
ISO_DATE_TEXT = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
QUANTITIES = ("inspected_units", "defective_units")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def load_contract(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_manifest(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_dimension(path, field):
    """Exact, case-sensitive identifiers from a dimension CSV. 'tm-a' is not 'TM-A'."""
    with open(path, encoding="utf-8", newline="") as stream:
        return {row[field].strip() for row in csv.DictReader(stream) if row.get(field, "").strip()}


def load_rows(path):
    """Return (header, rows). Each row is the raw text plus a 1-based data row number."""
    with open(path, encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        header = list(reader.fieldnames or [])
        rows = [{"_row_number": number, **row} for number, row in enumerate(reader, start=1)]
    return header, rows


def parse_field(field, text):
    """Return (typed value, reason or None). Empty after trimming is missing, never zero."""
    name = field["name"]
    text = "" if text is None else str(text).strip()
    if text == "":
        return None, ("missing_" + name if field.get("required") else None)
    kind = field["type"]
    if kind == "string":
        return text, None
    if kind == "integer":
        if not INTEGER_TEXT.match(text):
            return None, "invalid_" + name
        value = int(text)
        minimum = field.get("minimum")
        if minimum is not None and value < minimum:
            return value, "below_minimum_" + name
        return value, None
    if kind == "date":
        if not ISO_DATE_TEXT.match(text):
            return None, "invalid_" + name
        try:
            date.fromisoformat(text)
        except ValueError:
            return None, "invalid_" + name
        return text, None
    raise ValueError("unsupported contract type " + kind)


def check_row(raw, contract, dimensions):
    """Row-level checks only: schema, key presence, quantity rules, reference. Returns (typed, reasons)."""
    typed, reasons = {"row_number": raw["_row_number"]}, []
    for field in contract["fields"]:
        value, reason = parse_field(field, raw.get(field["name"]))
        typed[field["name"]] = value
        if reason:
            reasons.append(reason)
        elif value is not None and field.get("references"):
            reference = field["references"]
            if value not in dimensions.get(reference["dimension"], set()):
                reasons.append("unknown_" + reference["label"])
    inspected, defective = typed.get("inspected_units"), typed.get("defective_units")
    if isinstance(inspected, int) and isinstance(defective, int) and defective > inspected:
        reasons.append("defective_exceeds_inspected")
    return typed, reasons


def defect_rate(row):
    """None when the denominator is zero: not 0.0, not an exception."""
    inspected, defective = row["inspected_units"], row["defective_units"]
    return defective / inspected if inspected > 0 else None


def payload_of(row, contract):
    return {field["name"]: row[field["name"]] for field in contract["fields"]}


def quantities_of(row):
    return {name: row[name] for name in QUANTITIES}


def check_batch(clean, contract, manifest, header, raw_count):
    """Cross-record rules over rows that passed row checks. Returns (reasons by row, contradictions, failures)."""
    reasons, contradictions, failures = {row["row_number"]: [] for row in clean}, [], []

    # 1. Exact repeats of one delivery: keep the first, quarantine the rest (disclosed, not blocking).
    first_payload, survivors = {}, []
    for row in clean:
        payload = canonical(payload_of(row, contract))
        seen = first_payload.get(row["event_id"])
        if seen is not None and seen == payload:
            reasons[row["row_number"]].append("duplicate_delivery")
            continue
        first_payload.setdefault(row["event_id"], payload)
        survivors.append(row)

    # 2. One event ID telling two different stories: every such row is a contradiction.
    by_event = {}
    for row in survivors:
        by_event.setdefault(row["event_id"], []).append(row)
    conflicted = set()
    for event, rows in sorted(by_event.items()):
        if len({canonical(payload_of(row, contract)) for row in rows}) > 1:
            numbers = sorted(row["row_number"] for row in rows)
            contradictions.append({"rule": "event_id_conflict", "identity": event, "row_numbers": numbers})
            conflicted.update(numbers)
    survivors = [row for row in survivors if row["row_number"] not in conflicted]

    # 3. Uniqueness of (inspection_id, version): differing quantities contradict; identical ones are redundant.
    by_key = {}
    for row in survivors:
        by_key.setdefault((row["inspection_id"], row["version"]), []).append(row)
    keyed = set()
    for (key, version), rows in sorted(by_key.items()):
        if len(rows) < 2:
            continue
        if len({canonical(quantities_of(row)) for row in rows}) > 1:
            numbers = sorted(row["row_number"] for row in rows)
            contradictions.append({"rule": "key_version_conflict", "identity": [key, version], "row_numbers": numbers})
            keyed.update(numbers)
        else:
            for row in sorted(rows, key=lambda item: item["row_number"])[1:]:
                reasons[row["row_number"]].append("redundant_key_version")
                keyed.add(row["row_number"])
    survivors = [row for row in survivors if row["row_number"] not in keyed]

    # 4. Monotonic rule: within one inspection, revised_at must not decrease as version increases.
    by_inspection = {}
    for row in survivors:
        by_inspection.setdefault(row["inspection_id"], []).append(row)
    for key, rows in sorted(by_inspection.items()):
        ordered = sorted(rows, key=lambda item: item["version"])
        if any(later["revised_at"] < earlier["revised_at"] for earlier, later in zip(ordered, ordered[1:])):
            numbers = sorted(row["row_number"] for row in rows)
            contradictions.append({"rule": "version_time_inversion", "identity": key, "row_numbers": numbers})

    for item in contradictions:
        for number in item["row_numbers"]:
            reasons[number].append(item["rule"])

    # 5. Source completeness: the manifest's claim against the rows actually delivered.
    if manifest.get("delivered_rows") != raw_count:
        failures.append({"rule": "manifest_row_count_mismatch", "manifest_rows": manifest.get("delivered_rows"),
                         "delivered_rows": raw_count})
    # 6. Schema at batch level: a required column that is absent altogether.
    for field in contract["fields"]:
        if field.get("required") and field["name"] not in header:
            failures.append({"rule": "missing_column", "column": field["name"]})
    return reasons, contradictions, failures


def validate_rows(header, rows, contract, manifest, dimensions):
    typed_rows, quarantine, clean = [], [], []
    for raw in rows:
        typed, reasons = check_row(raw, contract, dimensions)
        typed_rows.append(typed)
        if reasons:
            quarantine.append({"row_number": typed["row_number"], "event_id": typed["event_id"], "reasons": reasons})
        else:
            clean.append(typed)
    batch_reasons, contradictions, failures = check_batch(clean, contract, manifest, header, len(rows))
    accepted = []
    for row in clean:
        reasons = batch_reasons[row["row_number"]]
        if reasons:
            quarantine.append({"row_number": row["row_number"], "event_id": row["event_id"], "reasons": reasons})
        else:
            accepted.append({**row, "defect_rate": defect_rate(row)})
    quarantine.sort(key=lambda item: item["row_number"])
    counts = {}
    for item in quarantine:
        for reason in item["reasons"]:
            counts[reason] = counts.get(reason, 0) + 1
    return {
        "contract_id": contract["contract_id"], "batch_id": manifest.get("batch_id"), "raw_count": len(rows),
        "accepted": accepted, "quarantine": quarantine, "contradictions": contradictions, "batch_failures": failures,
        "reason_counts": dict(sorted(counts.items())), "accepted_count": len(accepted), "quarantined_count": len(quarantine),
        "publication_allowed": not contradictions and not failures,
    }


def row_checks_only(rows, contract, dimensions):
    """What a per-row validator can see on its own. It has no view of other rows or of the manifest."""
    passing, failing = [], []
    for raw in rows:
        typed, reasons = check_row(raw, contract, dimensions)
        (failing if reasons else passing).append(typed["row_number"])
    return {"passing_row_numbers": passing, "failing_row_numbers": failing, "sees_manifest": False}


def validate(csv_path, plants_path, manifest_path, contract_path):
    contract = load_contract(contract_path)
    header, rows = load_rows(csv_path)
    dimensions = {"plants": load_dimension(plants_path, "plant_id")}
    return validate_rows(header, rows, contract, load_manifest(manifest_path), dimensions)


def main(argv=None):
    import argparse
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Validate an inspection CSV against the contract.")
    parser.add_argument("--csv", default=str(root / "fixtures" / "inspections.csv"))
    parser.add_argument("--plants", default=str(root / "fixtures" / "plants.csv"))
    parser.add_argument("--manifest", default=str(root / "fixtures" / "manifest.json"))
    parser.add_argument("--contract", default=str(root / "fixtures" / "contract.json"))
    args = parser.parse_args(argv)
    print(json.dumps(validate(args.csv, args.plants, args.manifest, args.contract), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
