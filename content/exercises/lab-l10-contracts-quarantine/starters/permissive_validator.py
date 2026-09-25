"""DELIBERATELY WRONG. A "validator" that passes everything.

It exists so that run_tests.py can show that a validator which accepts every
row, reports no contradiction and no manifest mismatch, and always says
publish, fails the contract for a nameable reason. Never use it.
"""
from solutions.validator import defect_rate, load_contract, load_dimension, load_manifest, load_rows  # noqa: F401


def validate_rows(header, rows, contract, manifest, dimensions):
    accepted = []
    for raw in rows:
        row = {"row_number": raw["_row_number"]}
        for field in contract["fields"]:
            text = (raw.get(field["name"]) or "").strip()
            row[field["name"]] = text or None
        # Quantities are kept as text and never checked; the rate is faked as 0.0.
        accepted.append({**row, "defect_rate": 0.0})
    return {"contract_id": contract["contract_id"], "batch_id": manifest.get("batch_id"), "raw_count": len(rows),
            "accepted": accepted, "quarantine": [], "contradictions": [], "batch_failures": [], "reason_counts": {},
            "accepted_count": len(accepted), "quarantined_count": 0, "publication_allowed": True}


def validate(csv_path, plants_path, manifest_path, contract_path):
    header, rows = load_rows(csv_path)
    return validate_rows(header, rows, load_contract(contract_path), load_manifest(manifest_path),
                         {"plants": load_dimension(plants_path, "plant_id")})
