from copy import deepcopy

def apply_resolved(target, source):
    next_target = deepcopy(target)
    seen = set()
    for row in source:
        key = row["inspection_id"]
        if key in seen:
            raise ValueError("source must be unique per inspection")
        seen.add(key)
        old = next_target.get(key)
        if old is None or row["version"] > old["version"]:
            next_target[key] = deepcopy(row)
        elif row["version"] == old["version"]:
            if (row["inspected_units"], row["defective_units"]) != (
                    old["inspected_units"], old["defective_units"]):
                raise ValueError("equal-version conflict")
        # An older revision is retained upstream but does not replace target.
    return next_target

target = {"A": {"inspection_id":"A", "version":2,
                 "inspected_units":12, "defective_units":1},
          "C": {"inspection_id":"C", "version":1,
                 "inspected_units":8, "defective_units":0}}
correction = [{"inspection_id":"A", "version":3,
               "inspected_units":14, "defective_units":1}]
updated = apply_resolved(target, correction)
assert updated["A"] == correction[0]
assert updated["C"] == target["C"]
assert apply_resolved(updated, correction) == updated
assert apply_resolved(updated, [target["A"]]) == updated
assert target["A"]["version"] == 2
