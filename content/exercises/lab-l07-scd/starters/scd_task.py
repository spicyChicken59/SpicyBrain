"""Learner starter for lab L07. Predict first, then implement, then compare.

Two deliberately flawed functions are here so you can watch them fail against the
hand-authored literals in expected/ before you write the correct versions. The
reference in solutions/scd_reference.py is the answer key; open SOLUTIONS.md only
after your own attempt. The validation helper `reasons` is imported from the
reference because validating events is not this lab's subject (module B3 taught it).

    python starters/scd_task.py
"""
import shutil
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True  # leave no __pycache__ inside the package
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from solutions.scd_reference import CINDERLINE, build_session, load_events, reasons  # noqa: E402

# Write these down from TASKS.md before running anything.
PREDICTIONS = {
    "current_row_for_P_100_unit_cost_after_batch_3": None,   # the late seq 2 arrives after seq 3
    "history_rows_for_P_100_after_batch_3": None,            # how many validity intervals?
    "P_300_after_batch_3": None,                              # "current", "withheld" or "deleted"?
    "P_400_after_batch_2": None,                              # its second event carries seq "2" (a string)
    "P_200_open_row_after_batch_2": None,                     # a delete at seq 2: True or False?
}


def last_arrival_wins(events, contract=CINDERLINE):
    """FLAWED Type 1: drop invalid rows, then let the last arrival per key win, deletes removing the key.

    Run it over all three batches and compare P-100 and P-400 with expected/cinderline.json.
    """
    current = {}
    for event in events:
        if reasons(event, contract):
            continue  # flaw 1: an unreadable event on a known key is silently ignored
        key = event[contract.key]
        if event["op"] == "delete":
            current.pop(key, None)
        else:
            current[key] = {column: event[column] for column in contract.attributes}  # flaw 2: arrival order decides
    return current


def append_per_arrival(events, contract=CINDERLINE):
    """FLAWED Type 2: close the open row at each new arrival's sequence and open a new one.

    Run solutions.scd_reference.check_intervals over the result and read the reason it raises.
    """
    history, open_rows = [], {}
    for event in events:
        if reasons(event, contract):
            continue
        key, sequence = event[contract.key], [event[column] for column in contract.sequence]
        if key in open_rows:
            open_rows.pop(key)["valid_to"] = sequence  # flaw: assumes arrivals are in sequence order
        if event["op"] == "upsert":
            row = {contract.key: key, "valid_from": sequence, "valid_to": None,
                   **{column: event[column] for column in contract.attributes}}
            history.append(row)
            open_rows[key] = row
    return history


def current_rows_scd1(spark, events, contract=CINDERLINE):
    """Task 3: return the Type 1 table as a list of dicts matching expected/cinderline.json['current']."""
    raise NotImplementedError("validate with reasons, deduplicate, withhold ties and unorderable keys, then row_number")


def history_rows_scd2(spark, events, contract=CINDERLINE):
    """Task 4: return the Type 2 table matching expected/cinderline.json['history'] (valid_from/valid_to as lists)."""
    raise NotImplementedError("order each key by the sequence columns; lead() gives valid_to; a delete closes only")


if __name__ == "__main__":
    events = load_events("cinderline-events.json")
    print("last_arrival_wins P-100:", last_arrival_wins(events).get("P-100"))
    print("append_per_arrival rows for P-100:", [r for r in append_per_arrival(events) if r["part_id"] == "P-100"])
    scratch = tempfile.mkdtemp(prefix="lab-l07-learner-")
    spark = build_session("SpicyBrain lab L07 learner", scratch)
    try:
        print("Spark", spark.version, "local[2]; implement current_rows_scd1 and history_rows_scd2 next")
    finally:
        spark.stop()
        shutil.rmtree(scratch, ignore_errors=True)
