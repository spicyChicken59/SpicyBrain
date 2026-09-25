"""Independent plain-Python derivation of the batch truths in expected/windows.json.

It never imports Spark. It reads the fixture files, assigns every event to half-open
[start, end) windows by arithmetic on seconds since midnight UTC, and sums units and
events per (window start, line). The runner asserts that the hand-written literals in
windows.json equal what this script derives, so a typing slip in either one fails.

It also derives, for each watermark delay, the watermark that follows each arrival:
the largest event time read so far minus the delay. The hand-written per-batch
watermarks in sequential.json and transfer.json are checked against these values.
The micro-batch outcomes themselves (which windows each batch emits, what a late row
does) are written by hand in those files from the documented rules; see DATA.md.
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURES = HERE.parent / "fixtures"
UTC = timezone.utc


def parse(text):
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def stamp(moment):
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def manifest():
    return json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))


def arrivals():
    """[(file name, landing time, [event dicts])] in landing order."""
    out = []
    for entry in manifest()["arrivals"]:
        lines = (FIXTURES / "arrivals" / entry["file"]).read_text(encoding="utf-8").splitlines()
        out.append((entry["file"], parse(entry["landsAt"]), [json.loads(line) for line in lines if line.strip()]))
    return out


def window_starts(moment, size_minutes, slide_minutes):
    """Every window start s (a multiple of the slide since midnight) with s <= moment < s + size."""
    midnight = moment.replace(hour=0, minute=0, second=0)
    seconds = int((moment - midnight).total_seconds())
    slide, size = slide_minutes * 60, size_minutes * 60
    latest = seconds - seconds % slide
    starts = []
    start = latest
    while start > seconds - size:
        starts.append(midnight + timedelta(seconds=start))
        start -= slide
    return sorted(starts)


def windows(pairs, size_minutes, slide_minutes):
    """pairs: [(moment, event)] -> sorted rows of window_start, line, units, events."""
    groups = {}
    for moment, event in pairs:
        for start in window_starts(moment, size_minutes, slide_minutes):
            key = (stamp(start), event["line"])
            units, count = groups.get(key, (0, 0))
            groups[key] = (units + event["units"], count + 1)
    return [{"window_start": k[0], "line": k[1], "units": v[0], "events": v[1]}
            for k, v in sorted(groups.items())]


def derive():
    data = arrivals()
    events = [e for _, _, rows in data for e in rows]
    by_event_time = [(parse(e["event_time"]), e) for e in events]
    by_landing = [(landed, e) for _, landed, rows in data for e in rows]
    sliding = windows(by_event_time, 10, 5)
    return {
        "totals": {"events": len(events), "units": sum(e["units"] for e in events)},
        "eventTimeTumbling": windows(by_event_time, 10, 10),
        "processingTimeTumbling": windows(by_landing, 10, 10),
        "slidingEventTime": {
            "windowDuration": "10 minutes",
            "slideDuration": "5 minutes",
            "windowsPerEvent": 2,
            "unitsAcrossWindows": sum(r["units"] for r in sliding),
            "eventsAcrossWindows": sum(r["events"] for r in sliding),
            "rows": sliding,
        },
    }


def watermarks_after_each_arrival(delay_minutes):
    """Largest event time read so far minus the delay, after each arrival in order."""
    out, latest = [], None
    for _, _, rows in arrivals():
        for e in rows:
            moment = parse(e["event_time"])
            latest = moment if latest is None or moment > latest else latest
        out.append(stamp(latest - timedelta(minutes=delay_minutes)))
    return out


if __name__ == "__main__":
    print(json.dumps(derive(), indent=1))
    print(watermarks_after_each_arrival(5), watermarks_after_each_arrival(15))
