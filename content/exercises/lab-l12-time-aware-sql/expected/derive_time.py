"""Independent derivation of the calendar and clock values in expected/time.json.

Standard library only: zoneinfo reads the system's IANA time zone database. This file never
imports Spark or the solution, and run_tests.py never imports this file; it is the authoring
check that DATA.md describes. Run it with any Python 3.9+ that has IANA zone data:

    python expected/derive_time.py

It recomputes each value from the fixture instants and prints OK or DIFF per value. Two things
are Spark's own and are only formatted here, not decided: the text layout of a day-time
interval (INTERVAL 'd hh:mm:ss' DAY TO SECOND) and the fact that TIMESTAMPDIFF and timestamp
subtraction work on local clock readings. Both were recorded from the pinned build, as
time.json's derivation says.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
NEW_YORK = ZoneInfo("America/New_York")
UTC = timezone.utc
EVENTS = json.loads((HERE.parent / "fixtures" / "machine_events.json").read_text(encoding="utf-8"))
EXPECTED = json.loads((HERE / "time.json").read_text(encoding="utf-8"))


def instant(text: str) -> datetime:
    """An ISO-8601 UTC string ending in Z as an aware datetime."""
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def render(moment: datetime, zone) -> str:
    """The Spark pattern 'yyyy-MM-dd HH:mm XXX': local reading plus offset, Z for zero."""
    local = moment.astimezone(zone)
    offset = int(local.utcoffset().total_seconds() // 60)
    if offset == 0:
        suffix = "Z"
    else:
        sign = "-" if offset < 0 else "+"
        suffix = f"{sign}{abs(offset) // 60:02d}:{abs(offset) % 60:02d}"
    return local.strftime("%Y-%m-%d %H:%M ") + suffix


def local_reading(moment: datetime, zone) -> datetime:
    return moment.astimezone(zone).replace(tzinfo=None)


def whole_minutes(delta: timedelta) -> int:
    seconds = delta.total_seconds()
    assert seconds % 60 == 0, "the fixtures only use whole minutes"
    return int(seconds // 60)


def interval_text(delta: timedelta) -> str:
    """A non-negative day-time interval in Spark's DAY TO SECOND text layout."""
    seconds = int(delta.total_seconds())
    days, rest = divmod(seconds, 86400)
    hours, rest = divmod(rest, 3600)
    minutes, secs = divmod(rest, 60)
    return f"INTERVAL '{days} {hours:02d}:{minutes:02d}:{secs:02d}' DAY TO SECOND"


def events(zone):
    rows = []
    for e in sorted(EVENTS, key=lambda r: r["event_id"]):
        moment = instant(e["event_time_utc"])
        local = moment.astimezone(zone)
        rows.append([e["event_id"], e["machine_id"], e["event_type"], e["event_time_utc"],
                     render(moment, zone), local.hour, local.date().isoformat(),
                     e["event_time_utc"][:10]])
    return rows


def pairs(zone):
    """Each STOP followed directly by a START on the same machine, in instant order."""
    out = []
    by_machine: dict[str, list] = {}
    for e in EVENTS:
        by_machine.setdefault(e["machine_id"], []).append(e)
    for machine in sorted(by_machine):
        seq = sorted(by_machine[machine], key=lambda r: instant(r["event_time_utc"]))
        for this, nxt in zip(seq, seq[1:]):
            if this["event_type"] == "STOP" and nxt["event_type"] == "START":
                stop, start = instant(this["event_time_utc"]), instant(nxt["event_time_utc"])
                out.append([machine, render(stop, zone), render(start, zone),
                            whole_minutes(start - stop),
                            whole_minutes(local_reading(start, zone) - local_reading(stop, zone)),
                            local_reading(stop, zone).date().isoformat()])
    return out


def interval_for_m2(zone):
    m2 = {e["event_type"]: instant(e["event_time_utc"]) for e in EVENTS if e["machine_id"] == "M2"}
    stop, start = m2["STOP"], m2["START"]
    wall = local_reading(start, zone) - local_reading(stop, zone)
    return [interval_text(wall), whole_minutes(wall), whole_minutes(start - stop)]


def dst_days():
    rows = []
    for d in (date(2026, 3, 7), date(2026, 3, 8), date(2026, 3, 9)):
        midnight = datetime(d.year, d.month, d.day, tzinfo=NEW_YORK)
        nxt = d + timedelta(days=1)
        next_midnight = datetime(nxt.year, nxt.month, nxt.day, tzinfo=NEW_YORK)
        wall_hours = int((next_midnight.replace(tzinfo=None) - midnight.replace(tzinfo=None)).total_seconds() // 3600)
        elapsed_hours = int((next_midnight.astimezone(UTC) - midnight.astimezone(UTC)).total_seconds() // 3600)
        rows.append([d.isoformat(), wall_hours, elapsed_hours])
    return rows


def day_versus_24_hours():
    start = datetime(2026, 3, 7, 12, 0, tzinfo=NEW_YORK)
    one_day_later = datetime(2026, 3, 8, 12, 0, tzinfo=NEW_YORK)      # same wall-clock time tomorrow
    plus_24_hours = (start.astimezone(UTC) + timedelta(hours=24))      # 24 elapsed hours
    return {"start": render(start, NEW_YORK), "one_day_later": render(one_day_later, NEW_YORK),
            "twenty_four_hours_later": render(plus_24_hours, NEW_YORK)}


def local_strings():
    # PEP 495: fold=0 inside a gap uses the offset before the change, i.e. the reading moves
    # forward by the gap length; inside a repeated hour it selects the earlier offset.
    gap = datetime(2026, 3, 8, 2, 30, tzinfo=NEW_YORK)
    repeated = datetime(2026, 11, 1, 1, 30, tzinfo=NEW_YORK)
    return {"resolved": render(gap.astimezone(UTC), NEW_YORK), "ntz_reading": "2026-03-08 02:30:00",
            "repeated": render(repeated.astimezone(UTC), NEW_YORK)}


def fall_back():
    stop, start = instant("2026-11-01T05:30:00Z"), instant("2026-11-01T06:15:00Z")
    return {"stopped_local": render(stop, NEW_YORK), "started_local": render(start, NEW_YORK),
            "elapsed_minutes": whole_minutes(start - stop),
            "wall_clock_minutes": whole_minutes(local_reading(start, NEW_YORK) - local_reading(stop, NEW_YORK)),
            "repeated_string_resolved": local_strings()["repeated"]}


def month_attribution():
    m3 = {e["event_type"]: e for e in EVENTS if e["machine_id"] == "M3"}
    stop = instant(m3["STOP"]["event_time_utc"])
    start = instant(m3["START"]["event_time_utc"])
    return [["M3", stop.astimezone(NEW_YORK).strftime("%Y-%m"), m3["STOP"]["event_time_utc"][:7],
             whole_minutes(start - stop)]]


def main() -> int:
    derived = {
        "events_local": events(NEW_YORK),
        "events_local_utc_session": events(UTC),
        "downtime_pairs": pairs(NEW_YORK),
        "downtime_pairs_utc_session": pairs(UTC),
        "interval_subtraction": interval_for_m2(NEW_YORK),
        "interval_subtraction_utc_session": interval_for_m2(UTC),
        "dst_day_hours": dst_days(),
        "day_versus_24_hours": day_versus_24_hours(),
        "nonexistent_local_time": {k: v for k, v in local_strings().items() if k != "repeated"},
        "fall_back_hour": fall_back(),
        "month_attribution": month_attribution(),
    }
    differences = 0
    for key, value in derived.items():
        same = EXPECTED.get(key) == value
        differences += 0 if same else 1
        print(("OK   " if same else "DIFF ") + key)
        if not same:
            print("     derived :", json.dumps(value))
            print("     expected:", json.dumps(EXPECTED.get(key)))
    print(f"{len(derived) - differences} of {len(derived)} time.json values reproduced independently")
    return 1 if differences else 0


if __name__ == "__main__":
    sys.exit(main())
