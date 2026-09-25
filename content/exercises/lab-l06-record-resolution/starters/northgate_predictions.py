"""Task 5 starter: write your Northgate predictions BEFORE running the resolver.

Fill every None below from fixtures/northgate-*.json and the contract, then run
    python starters/northgate_predictions.py
It compares your predictions with expected/northgate.json (authored by hand,
derivations in DATA.md) and names each scenario as matched or not. It never
runs the resolver for you.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PREDICTIONS = {
    "baseline": {
        "accepted": None,          # list of {"inspection_id", "version", "inspected_units", "defective_units"}, sorted by key
        "totals": None,            # {"inspected_units": int, "defective_units": int, "defect_rate": float or None}
        "excluded_keys": None,     # keys that never had a valid revision
        "unresolved": None,        # keys whose current state cannot be proved
        "publication_allowed": None,
    },
    "correction": {"accepted": None, "totals": None, "excluded_keys": None, "unresolved": None, "publication_allowed": None},
    "blocked": {"accepted": None, "totals": None, "excluded_keys": None, "unresolved": None, "publication_allowed": None},
    "invalid_only": {"accepted": None, "totals": None, "excluded_keys": None, "unresolved": None, "publication_allowed": None},
}


def check():
    expected = json.loads((ROOT / "expected" / "northgate.json").read_text(encoding="utf-8"))
    outcome = {}
    for scenario, prediction in PREDICTIONS.items():
        if any(value is None for value in prediction.values()):
            outcome[scenario] = "incomplete prediction"
        elif prediction == expected[scenario]:
            outcome[scenario] = "matches the authored expectation"
        else:
            differing = sorted(field for field in prediction if prediction[field] != expected[scenario][field])
            outcome[scenario] = "differs in " + ", ".join(differing)
    return outcome


if __name__ == "__main__":
    for scenario, verdict in check().items():
        print(f"{scenario}: {verdict}")
