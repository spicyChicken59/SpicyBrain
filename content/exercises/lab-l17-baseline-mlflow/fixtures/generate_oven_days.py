"""Deterministic synthetic fixture generator for lab L17 (Cinderline Components, fictional).

Run from this directory: python generate_oven_days.py
Writes oven_days.csv: one row per oven per day, each row a 09:00 prediction opportunity,
for 8 coating ovens over 120 days. Every random draw comes from one seeded generator, so the
committed file is byte-for-byte reproducible; run_tests.py verifies that. Nothing here is a
measurement of a real oven.
"""
import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEED = 20260923
TRANSFER_SEED = 20260924  # the altered-input transfer dataset used by one test
DAYS = 120
START = date(2026, 3, 2)  # day 1, a Monday
OVENS = [  # oven id, age in years, temperature set point in degrees C
    ("O-01", 2.5, 205.0), ("O-02", 4.0, 205.0), ("O-03", 6.5, 210.0), ("O-04", 8.0, 210.0),
    ("O-05", 3.0, 200.0), ("O-06", 9.5, 215.0), ("O-07", 5.5, 205.0), ("O-08", 11.0, 215.0),
]
SERVICE_INTERVAL = 45  # scheduled service roughly every 45 days
COLUMNS = ["oven_id", "day", "date", "oven_age_years", "days_since_service", "temp_mean_c", "temp_max_c",
           "door_cycles", "humidity_pct", "fault_next_24h", "repair_minutes", "fault_code"]


def fault_probability(days_since_service, age, door_cycles):
    """Latent hazard: wear grows with days since service and age; heavy door use adds to it."""
    wear = 0.075 * days_since_service + 0.16 * age
    logit = -4.7 + wear + 0.02 * max(door_cycles - 60, 0)
    return 1.0 / (1.0 + math.exp(-logit))


def rows(seed=SEED):
    rng = random.Random(seed)
    out = []
    state = {oven: {"since": rng.randint(0, 30), "next_service": rng.randint(20, 45)} for oven, _, _ in OVENS}
    for day in range(1, DAYS + 1):
        current = START + timedelta(days=day - 1)
        season = 6.0 * math.sin(2 * math.pi * day / 120.0)
        for oven, age, setpoint in OVENS:
            s = state[oven]
            drift = 0.08 * s["since"]  # a worn oven runs hotter
            door_cycles = max(0, int(rng.gauss(58, 14)))
            p = fault_probability(s["since"], age, door_cycles)
            fault = 1 if rng.random() < p else 0
            # An oven about to fault usually ran hot in the previous 24 hours: a precursor that IS
            # observable at 09:00, unlike the repair record, which is written after the fault.
            precursor = abs(rng.gauss(5.5, 2.0)) if fault and rng.random() < 0.8 else 0.0
            temp_mean = setpoint + drift + precursor * 0.5 + rng.gauss(0.0, 1.6)
            temp_max = temp_mean + abs(rng.gauss(4.0, 2.5)) + precursor
            humidity = 44.0 + season + rng.gauss(0.0, 3.0)
            repair = rng.randint(45, 240) if fault else 0
            code = rng.choice(["F-HEAT", "F-DOOR", "F-CTRL"]) if fault else ""
            out.append({
                "oven_id": oven, "day": day, "date": current.isoformat(), "oven_age_years": f"{age:.1f}",
                "days_since_service": s["since"], "temp_mean_c": f"{temp_mean:.1f}", "temp_max_c": f"{temp_max:.1f}",
                "door_cycles": door_cycles, "humidity_pct": f"{humidity:.1f}", "fault_next_24h": fault,
                "repair_minutes": repair, "fault_code": code,
            })
            # A fault is repaired the same day, and a scheduled service also resets the counter.
            if fault or s["since"] >= s["next_service"]:
                s["since"] = 0
                s["next_service"] = SERVICE_INTERVAL + rng.randint(-8, 8)
            else:
                s["since"] += 1
    return out


def write(path, records):
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)


if __name__ == "__main__":
    write(HERE / "oven_days.csv", rows())
    print("wrote oven_days.csv")
