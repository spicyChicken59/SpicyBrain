"""Deterministic synthetic fixture generator for lab L04 (Cinderline Components, fictional).

Run from this directory: python generate_inspections.py
Writes inspections.json (skewed: North 180 / South 36 / West 24 rows),
inspections_balanced.json (80 rows per plant) and plants.json. Seeds are fixed,
so the committed files are byte-for-byte reproducible; run_tests.py verifies that.
"""
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKEWED_SEED = 20260923
BALANCED_SEED = 20260924
PLANTS = [("North", "inland", "M-01"), ("South", "coastal", "M-02"), ("West", "coastal", "M-03")]


def rows_for(plant_counts, seed):
    """One synthetic inspection event per row; order is shuffled deterministically."""
    rng = random.Random(seed)
    plants = [plant for plant, count in plant_counts for _ in range(count)]
    rng.shuffle(plants)
    rows = []
    for index, plant in enumerate(plants):
        inspected = rng.randint(5, 60)
        defective = rng.randint(0, min(4, inspected))
        rows.append({"event_id": f"e{index:04d}", "plant": plant, "line": f"L{rng.randint(1, 3)}",
                     "inspected_units": inspected, "defective_units": defective})
    return rows


def skewed_rows():
    return rows_for([("North", 180), ("South", 36), ("West", 24)], SKEWED_SEED)


def balanced_rows():
    return rows_for([("North", 80), ("South", 80), ("West", 80)], BALANCED_SEED)


def plant_rows():
    return [{"plant": plant, "region": region, "manager_code": code} for plant, region, code in PLANTS]


def write(path, rows):
    path.write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    write(HERE / "inspections.json", skewed_rows())
    write(HERE / "inspections_balanced.json", balanced_rows())
    write(HERE / "plants.json", plant_rows())
    print("wrote inspections.json, inspections_balanced.json, plants.json")
