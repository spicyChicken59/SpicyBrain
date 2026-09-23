"""Independent derivation of expected literals for lab L04, in plain Python only.

This script never imports PySpark and never calls the reference solution. It
reads the committed fixtures, computes the literals with ordinary loops and
dictionaries, and writes totals.json. The derivations are described in DATA.md.
run_tests.py re-runs derive() in memory and asserts the committed file matches,
so the expected values cannot silently drift from the fixtures.

One premise is stated rather than computed: SparkContext.parallelize(rows, 4)
cuts a list into four contiguous, equal slices in list order. The input-slice
literals below follow from that premise, and run_tests.py checks the premise
itself against the partition membership Spark reports.
"""
import json
import zlib
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURES = HERE.parent / "fixtures"
SALTS = 4
INPUT_PARTITIONS = 4


def load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def salt_of(event_id):
    # Spark's crc32() is the standard CRC-32 of the UTF-8 bytes; zlib.crc32 computes the same value.
    return zlib.crc32(event_id.encode("utf-8")) % SALTS


def slices_of(rows, parts=INPUT_PARTITIONS):
    """Contiguous equal slices in list order: slice i holds positions [i*n/parts, (i+1)*n/parts)."""
    n = len(rows)
    return [rows[(i * n) // parts:((i + 1) * n) // parts] for i in range(parts)]


def derive_dataset(rows, plants):
    region_of = {p["plant"]: p["region"] for p in plants}
    per_plant = defaultdict(lambda: {"rows": 0, "inspected": 0, "defective": 0})
    per_region = defaultdict(lambda: {"rows": 0, "inspected": 0})
    per_group = defaultdict(int)
    defective_rows = 0
    for row in rows:
        p = per_plant[row["plant"]]
        p["rows"] += 1
        p["inspected"] += row["inspected_units"]
        p["defective"] += row["defective_units"]
        r = per_region[region_of[row["plant"]]]
        r["rows"] += 1
        r["inspected"] += row["inspected_units"]
        per_group[(row["plant"], salt_of(row["event_id"]))] += 1
        if row["defective_units"] > 0:
            defective_rows += 1
    plant_totals = [{"plant": k, **v} for k, v in sorted(per_plant.items())]
    hot = max(plant_totals, key=lambda t: t["rows"])
    hot_lines = defaultdict(int)
    for row in rows:
        if row["plant"] == hot["plant"]:
            hot_lines[row["line"]] += 1
    input_slices = []
    for index, part in enumerate(slices_of(rows)):
        mix = defaultdict(int)
        for row in part:
            mix[row["plant"]] += 1
        input_slices.append({"partition": index, "rows": len(part), "plants": dict(sorted(mix.items())),
                             "defective_rows": sum(1 for row in part if row["defective_units"] > 0),
                             "regions": sorted({region_of[row["plant"]] for row in part})})
    dimension_rows = sum(1 for p in plants if p["plant"] is not None)
    return {
        "row_count": len(rows),
        "defective_rows": defective_rows,
        "plant_totals": plant_totals,
        "region_totals": [{"region": k, **v} for k, v in sorted(per_region.items())],
        "hot_plant": hot["plant"],
        "hot_plant_rows": hot["rows"],
        "hot_share": round(hot["rows"] / len(rows), 4),
        "hot_plant_line_counts": [{"line": k, "count": v} for k, v in sorted(hot_lines.items())],
        "salts": SALTS,
        "salted_groups": [{"plant": p, "salt": s, "rows": n} for (p, s), n in sorted(per_group.items())],
        "max_salted_group_rows": max(per_group.values()),
        "input_slices": input_slices,
        # A partial aggregate writes one row per key present in each input partition.
        "grouped_partial_rows": sum(len(s["plants"]) for s in input_slices),
        "regional_partial_rows": sum(len(s["regions"]) for s in input_slices),
        # A sort-merge join shuffles every fact row and every dimension row with a non-null key.
        "dimension_rows": dimension_rows,
        "join_shuffle_read_rows": len(rows) + dimension_rows,
    }


def derive():
    plants = load("plants.json")
    return {"skewed": derive_dataset(load("inspections.json"), plants),
            "balanced": derive_dataset(load("inspections_balanced.json"), plants)}


if __name__ == "__main__":
    (HERE / "totals.json").write_text(json.dumps(derive(), indent=1) + "\n", encoding="utf-8")
    print("wrote totals.json")
