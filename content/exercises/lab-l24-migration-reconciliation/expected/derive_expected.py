"""Independent cross-check for Lab L24's expected literals (standard library only).

The runner never imports this file and never computes an expectation. The
literals in expected/*.json were written by hand from the derivation tables in
DATA.md; this script re-derives the numeric outputs with plain Python
(zoneinfo, Decimal, integer floor division), sharing no code with
solutions/migration.py, and prints every difference it finds between its own
answers and the committed literals. Run it with any Python 3.11+ interpreter:

    python expected/derive_expected.py

It exits 0 when every literal it can derive agrees, 1 otherwise. Inventory,
job-plan and profile literals are read from the text by hand and are not
re-derived here.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from fractions import Fraction
from math import floor
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
UTC = ZoneInfo("UTC")


def load(path):
    return json.loads((LAB / path).read_text(encoding="utf-8"))


CTX = load("fixtures/run_context.json")
SERVER = CTX["server_time_zone"]
CUT = CTX["business_day_cutoff_hours"]
PLANTS = {p["plant_code"]: p["plant_time_zone"] for p in load("fixtures/plants.json")}
INSPECTORS = load("fixtures/inspectors.json")


def text(v):
    if v is None:
        return None
    if isinstance(v, float):
        return repr(v)
    return str(v)


def day_of(row, rule, session_zone="UTC"):
    local = datetime.fromisoformat(row["inspected_at"])
    if rule == "server_local":
        return (local - timedelta(hours=CUT)).date()
    aware = local.replace(tzinfo=ZoneInfo(SERVER))
    if rule == "plant_local":
        plant = aware.astimezone(ZoneInfo(PLANTS[row["plant_code"]])).replace(tzinfo=None)
        return (plant - timedelta(hours=CUT)).date()
    if rule == "session":
        shown = aware.astimezone(ZoneInfo(session_zone)).replace(tzinfo=None)
        return (shown - timedelta(hours=CUT)).date()
    raise ValueError(rule)


def key_form(code, rule):
    if code is None:
        return None
    if rule == "collation":
        return code.rstrip(" ").upper()
    if rule == "trim":
        return code.strip(" ").upper()
    return code


def shift_for(row, plant, rules):
    matches = [
        s for s in INSPECTORS
        if row["inspector_code"] is not None
        and key_form(s["inspector_code"], rules["key"]) == key_form(row["inspector_code"], rules["key"])
    ]
    if rules["join"] == "on":
        matches = [s for s in matches if s["plant_code"] == plant]
        return [matches[0]["shift_code"] if matches else "UNASSIGNED"]
    kept = [s for s in matches if s["plant_code"] == plant]  # WHERE after a LEFT JOIN
    return [s["shift_code"] for s in kept]  # empty list: the row disappears


def derive(rows, plant, rules, as_of=None, days=None, session_zone="UTC"):
    detail = []
    for r in rows:
        if r["plant_code"] != plant:
            continue
        if as_of and datetime.fromisoformat(r["updated_at"]) > datetime.fromisoformat(as_of):
            continue
        d = day_of(r, rules["day"], session_zone).isoformat()
        if days is not None and d not in days:
            continue
        for shift in shift_for(r, plant, rules):
            amount = Decimal(r["rework_cost"]) if rules["amount"] == "decimal" else float(r["rework_cost"])
            detail.append({
                "inspection_id": r["inspection_id"], "plant_code": plant, "business_day": d,
                "shift_code": shift, "inspector_code": r["inspector_code"],
                "units_inspected": r["units_inspected"], "units_defective": r["units_defective"],
                "rework_cost": amount,
            })
    groups = {}
    for x in detail:
        k = (x["plant_code"], x["business_day"], x["shift_code"])
        g = groups.setdefault(k, [0, 0, 0, None])
        g[0] += 1
        g[1] += x["units_inspected"]
        g[2] += x["units_defective"]
        g[3] = x["rework_cost"] if g[3] is None else g[3] + x["rework_cost"]
    report = []
    for (p, d, s), (n, ui, ud, cost) in sorted(groups.items()):
        pct = ud * 100 // ui if rules["division"] == "integer" else ud * 100 / ui
        report.append({"plant_code": p, "business_day": d, "shift_code": s, "inspections": n,
                       "units_inspected": ui, "units_defective": ud, "rework_cost": cost, "defect_pct": pct})
    detail = [{k: text(v) for k, v in x.items()} for x in sorted(detail, key=lambda x: x["inspection_id"])]
    report = [{k: text(v) for k, v in x.items()} for x in report]
    types = []
    if rules["amount"] == "double":
        types += [["detail.rework_cost", "decimal(*,2)", "double"], ["report.rework_cost", "decimal(*,2)", "double"]]
    if rules["division"] == "fractional":
        types.append(["report.defect_pct", "integral", "double"])
    return {"detail": detail, "report": report, "type_mismatches": sorted(types)}


def legacy(detail_file, report_file):
    return {
        "detail": [{k: text(v) for k, v in r.items()} for r in sorted(load(detail_file), key=lambda r: r["inspection_id"])],
        "report": [{k: text(v) for k, v in r.items()} for r in load(report_file)],
        "type_mismatches": [],
    }


NUM = {"inspection_id", "units_inspected", "units_defective", "rework_cost", "inspections", "defect_pct"}
D_FIELDS = ["business_day", "shift_code", "inspector_code", "units_inspected", "units_defective", "rework_cost"]
R_FIELDS = ["inspections", "units_inspected", "units_defective", "rework_cost", "defect_pct"]
D_COLS = ["inspection_id", "plant_code", "business_day", "shift_code", "inspector_code", "units_inspected", "units_defective", "rework_cost"]
R_COLS = ["plant_code", "business_day", "shift_code", "inspections", "units_inspected", "units_defective", "rework_cost", "defect_pct"]


def equal(f, a, b):
    if a is None or b is None:
        return a is None and b is None
    return Decimal(a) == Decimal(b) if f in NUM else a == b


def compare(old, new):
    od = {int(r["inspection_id"]): r for r in old["detail"]}
    nd = {int(r["inspection_id"]): r for r in new["detail"]}
    d_changed = [[i, f, od[i][f], nd[i][f]] for i in sorted(set(od) & set(nd)) for f in D_FIELDS if not equal(f, od[i][f], nd[i][f])]
    rk = lambda r: (r["plant_code"], r["business_day"], r["shift_code"])  # noqa: E731
    orp = {rk(r): r for r in old["report"]}
    nrp = {rk(r): r for r in new["report"]}
    r_changed = [[*k, f, orp[k][f], nrp[k][f]] for k in sorted(set(orp) & set(nrp)) for f in R_FIELDS if not equal(f, orp[k][f], nrp[k][f])]
    totals = []
    def sums(rep):
        out = {}
        for r in rep:
            t = out.setdefault((r["plant_code"], r["business_day"]), {f: Decimal(0) for f in ["units_inspected", "units_defective", "rework_cost"]})
            for f in t:
                t[f] += Decimal(r[f])
        return out
    so, sn = sums(old["report"]), sums(new["report"])
    for k in sorted(set(so) | set(sn)):
        for f in ["units_inspected", "units_defective", "rework_cost"]:
            a, b = so.get(k, {}).get(f, Decimal(0)), sn.get(k, {}).get(f, Decimal(0))
            if a != b:
                totals.append([k[0], k[1], f, str(a), str(b)])
    nulls = []
    for table, cols in (("detail", D_COLS), ("report", R_COLS)):
        for c in cols:
            a = sum(1 for r in old[table] if r[c] is None)
            b = sum(1 for r in new[table] if r[c] is None)
            if a != b:
                nulls.append([f"{table}.{c}", a, b])
    result = {
        "row_counts": {"detail": [len(old["detail"]), len(new["detail"])], "report": [len(old["report"]), len(new["report"])]},
        "detail": {"only_old": sorted(set(od) - set(nd)), "only_new": sorted(set(nd) - set(od)), "changed": d_changed},
        "report": {"missing": [list(k) for k in sorted(set(orp) - set(nrp))], "extra": [list(k) for k in sorted(set(nrp) - set(orp))], "changed": r_changed},
        "totals": totals,
        "nulls": sorted(nulls),
        "types": new["type_mismatches"],
    }
    checks = {
        "row_counts": "pass" if all(a == b for a, b in result["row_counts"].values()) else "fail",
        "detail_keys": "pass" if not any(result["detail"].values()) else "fail",
        "report_keys": "pass" if not any(result["report"].values()) else "fail",
        "totals": "pass" if not totals else "fail",
        "nulls": "pass" if not nulls else "fail",
        "types": "pass" if not result["types"] else "fail",
    }
    return {"verdict": "pass" if set(checks.values()) == {"pass"} else "fail", "checks": checks, **result}


TARGET = {"key": "collation", "join": "on", "day": "server_local", "division": "integer", "amount": "decimal"}
NAIVE = {"key": "binary", "join": "where", "day": "session", "division": "fractional", "amount": "double"}
FLIPS = {
    "binary_keys": dict(TARGET, key="binary"),
    "where_filter": dict(TARGET, join="where"),
    "session_day": dict(TARGET, day="session"),
    "fractional_division": dict(TARGET, division="fractional"),
    "double_amounts": dict(TARGET, amount="double"),
}


def datetime_round(value):
    whole, _, frac = value.partition(".")
    seconds = Fraction(int(frac.ljust(6, "0")[:6]), 1_000_000)
    ticks = floor(seconds * 300 + Fraction(1, 2))
    millis = floor(Fraction(ticks * 1000, 300) + Fraction(1, 2))
    return (datetime.fromisoformat(whole) + timedelta(milliseconds=millis)).isoformat(sep=" ", timespec="milliseconds")


def gate(scenario, need):
    days = scenario["days"]
    since = 0
    for i, d in enumerate(days):
        if d["code_change"]:
            since = i
    run, blocker = 0, None
    for d in days[since:]:
        ok = d["verdict"] == "pass" or (d["verdict"] == "explained" and len(d["exceptions"]) > 0 and all(e["owner"] for e in d["exceptions"]))
        run, blocker = (run + 1, blocker) if ok else (0, d)
    reasons = []
    if run < need:
        reasons.append(f"{run} of {need} consecutive clean days since the code change of {days[since]['business_day']}")
        if blocker is not None:
            if blocker["verdict"] == "explained":
                ids = ", ".join(e["id"] for e in blocker["exceptions"] if not e["owner"])
                reasons.append(f"{blocker['business_day']}: exception {ids} has no named owner")
            else:
                reasons.append(f"{blocker['business_day']}: unexplained differences")
    if not scenario["rollback_rehearsed"]:
        reasons.append("rollback to the legacy path has not been rehearsed")
    return {"decision": "not ready" if reasons else "ready", "clean_days": run, "reasons": reasons}


def main():
    problems = []

    def check(label, derived, committed):
        if derived != committed:
            problems.append(label)
            print("DIFFERS:", label)
            print("  derived  :", json.dumps(derived)[:600])
            print("  committed:", json.dumps(committed)[:600])

    p1 = load("fixtures/inspections_p1.json")
    p2 = load("fixtures/inspections_p2.json")
    as_of = CTX["p1"]["as_of"]
    old1 = legacy("fixtures/legacy_detail_p1.json", "fixtures/legacy_report_p1.json")
    old2 = legacy("fixtures/legacy_detail_p2.json", "fixtures/legacy_report_p2.json")
    target1 = derive(p1, "P1", TARGET, as_of)
    check("target P1 equals the legacy fixtures", compare(old1, target1)["verdict"], "pass")
    committed = load("expected/target_p1.json")
    check("target_p1 detail", target1["detail"], committed["detail"])
    check("target_p1 report", target1["report"], committed["report"])
    rec = load("expected/reconcile_p1.json")
    check("reconcile target", compare(old1, target1), rec["target"])
    check("reconcile naive", compare(old1, derive(p1, "P1", NAIVE, as_of)), rec["naive"])
    check("reconcile basis", compare(old1, derive(p1, "P1", TARGET, None)), rec["basis_without_as_of"])
    flips = load("expected/flips_p1.json")
    for name, rules in FLIPS.items():
        check(f"flip {name}", compare(old1, derive(p1, "P1", rules, as_of)), flips[name])

    sem = load("expected/semantics.json")
    for raw, shown in sem["datetime_round"].items():
        check(f"datetime_round {raw}", datetime_round(raw), shown)
    sz = sem["session_zone"]
    for zone, verdict in sz["target"].items():
        check(f"target under {zone}", compare(old1, derive(p1, "P1", TARGET, as_of, session_zone=zone))["verdict"], verdict)
    for zone, verdict in sz["session_day"].items():
        check(f"session_day under {zone}", compare(old1, derive(p1, "P1", FLIPS["session_day"], as_of, session_zone=zone))["verdict"], verdict)

    inc = load("expected/incremental_p1.json")
    def affected(since, until, by):
        out = set()
        for r in p1:
            moment = r["updated_at"] if by == "change" else r["inspected_at"]
            if datetime.fromisoformat(moment) > datetime.fromisoformat(since) and datetime.fromisoformat(r["updated_at"]) <= datetime.fromisoformat(until):
                out.add(("P1", day_of(r, "server_local").isoformat()))
        return [list(x) for x in sorted(out)]
    tonight = CTX["p1"]["tonight"]
    check("tonight affected days", affected(tonight["since"], tonight["until"], "change"), inc["tonight"]["affected_days"])
    ev_days = affected(tonight["since"], tonight["until"], "event")
    check("event-time affected days", ev_days, inc["event_time"]["affected_days"])
    before = load("fixtures/legacy_state_before_p1.json")
    touched = {d for _, d in ev_days}
    kept_detail = [{k: text(v) for k, v in r.items()} for r in before["detail"] if r["business_day"] not in touched]
    kept_report = [{k: text(v) for k, v in r.items()} for r in before["report"] if r["business_day"] not in touched]
    fresh = derive(p1, "P1", TARGET, tonight["until"], days=touched)
    state = {
        "detail": sorted(kept_detail + fresh["detail"], key=lambda r: int(r["inspection_id"])),
        "report": sorted(kept_report + fresh["report"], key=lambda r: (r["plant_code"], r["business_day"], r["shift_code"])),
        "type_mismatches": [],
    }
    check("event-time reconcile", compare(old1, state), inc["event_time"]["reconcile"])
    nxt = CTX["p1"]["next"]
    next_days = affected(nxt["since"], nxt["until"], "change")
    check("next-window affected days", next_days, inc["next"]["affected_days"])
    later = derive(p1, "P1", TARGET, nxt["until"], days={d for _, d in next_days})
    report_next = [r for r in old1["report"] if r["business_day"] not in {d for _, d in next_days}] + later["report"]
    report_next.sort(key=lambda r: (r["plant_code"], r["business_day"], r["shift_code"]))
    check("next-window report", report_next, inc["next"]["report"])
    empty = CTX["p1"]["empty"]
    check("empty-window affected days", affected(empty["since"], empty["until"], "change"), inc["empty"]["affected_days"])

    tr = load("expected/transfer_p2.json")
    check("transfer compatible", compare(old2, derive(p2, "P2", TARGET, CTX["p2"]["as_of"])), tr["compatible"])
    check("transfer trim", compare(old2, derive(p2, "P2", dict(TARGET, key="trim"), CTX["p2"]["as_of"])), tr["trim_keys"])
    check("transfer plant-local", compare(old2, derive(p2, "P2", dict(TARGET, day="plant_local"), CTX["p2"]["as_of"])), tr["plant_local"]["reconcile"])

    runs = load("fixtures/parallel_run.json")
    cut = load("expected/cutover.json")
    for name, scenario in runs["scenarios"].items():
        check(f"cutover {name}", gate(scenario, runs["required_clean_days"]), cut[name])

    print("derived literals agree" if not problems else f"{len(problems)} literal(s) differ")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
