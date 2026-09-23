"""Starter for lab-l09-failure-recovery (Python 3.12, standard library only).

Fill the six gaps marked GAP 1 to GAP 6 (search for NotImplementedError), then run
`python run_tests.py --starter`. Everything else is complete and matches the reference.

A four-task daily report pipeline, ingest_raw -> resolve -> publish_report -> notify,
run by a tiny local runner that keeps a ledger per run id. Failures are injected
at four named boundaries; recovery re-runs the same run id, which reuses every
task that already succeeded and re-runs the failed task and its dependents.

Everything is local and in memory. The "external effect" is LocalChannel, which
appends a dictionary to a Python list: no message, email, webhook or page is ever
sent. The runner is a teaching model of task dependencies, retries and repair; it
is not Lakeflow Jobs, it has no durable storage and it survives no process crash.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys

TASKS = ("ingest_raw", "resolve", "publish_report", "notify")
DEPENDS_ON = {
    "ingest_raw": (),
    "resolve": ("ingest_raw",),
    "publish_report": ("resolve",),
    "notify": ("publish_report",),
}
BOUNDARIES = ("after_raw_retention", "after_resolution", "before_effect", "after_effect")
OPS_RECIPIENT = "ops-on-call"


# --------------------------------------------------------------------------- errors


class TaskError(RuntimeError):
    """A task stopped. `reason` is the short code the run ledger records."""

    transient = False

    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


class InjectedFailure(TaskError):
    """A deliberate crash at a named boundary (the lab's stand-in for a lost process)."""

    def __init__(self, boundary: str, transient: bool):
        super().__init__(f"injected:{boundary}")
        self.boundary = boundary
        self.transient = transient


class StaleInput(TaskError):
    """The landing file describes a different business date than the run."""


class GateRefused(TaskError):
    """The publication gate is false, so nothing is published."""


class RunIdentityError(ValueError):
    """A run id was reused for a different business date."""


# --------------------------------------------------------------------------- local stand-ins


class Faults:
    """How many times each boundary should fail. Each hit consumes one failure."""

    def __init__(self, spec: dict[str, int] | None = None, transient: bool = False):
        unknown = set(spec or {}) - set(BOUNDARIES)
        if unknown:
            raise ValueError(f"unknown boundary: {sorted(unknown)}")
        self.remaining = dict(spec or {})
        self.transient = transient

    def hit(self, boundary: str) -> None:
        if self.remaining.get(boundary, 0) > 0:
            self.remaining[boundary] -= 1
            raise InjectedFailure(boundary, self.transient)


class LocalChannel:
    """A simulated recipient system. `send` appends to `delivered`; nothing leaves the process.

    With honours_keys=True it behaves like a receiver that supports idempotency
    keys: a key it has already accepted returns the first delivery id and adds
    nothing. With honours_keys=False it ignores keys and cannot answer lookups.
    """

    def __init__(self, honours_keys: bool = True):
        self.honours_keys = honours_keys
        self.delivered: list[dict] = []
        self.suppressed = 0
        self._by_key: dict[str, str] = {}

    def send(self, recipient: str, report: dict, key: str | None = None) -> str:
        if self.honours_keys and key is not None and key in self._by_key:
            self.suppressed += 1
            return self._by_key[key]
        delivery_id = f"m{len(self.delivered) + 1}"
        self.delivered.append({
            "delivery_id": delivery_id,
            "recipient": recipient,
            "report_id": report["report_id"],
            "report_date": report["content"]["report_date"],
            "backfill": report["backfill"],
            "key": key,
        })
        if self.honours_keys and key is not None:
            self._by_key[key] = delivery_id
        return delivery_id

    def lookup(self, key: str) -> str | None:
        """Ask the receiver whether it already accepted `key` (None when it cannot say)."""
        return self._by_key.get(key) if self.honours_keys else None


class Store:
    """Every piece of state the pipeline writes, in one inspectable object."""

    def __init__(self):
        self.raw: dict[str, dict[str, dict]] = {}          # business date -> event id -> retained row
        self.raw_conflicts: dict[str, list[dict]] = {}     # business date -> event conflicts seen at retention
        self.resolved: dict[str, dict] = {}                # business date -> resolution result
        self.reports: dict[str, dict] = {}                 # business date -> published report record
        self.report_history: list[dict] = []               # report records replaced by a newer version
        self.outbox: dict[str, dict] = {}                  # idempotency key -> notification intent
        self.alerts: list[dict] = []                       # ops alerts (local list, never a real page)
        self.runs: dict[str, dict] = {}                    # run id -> run ledger


# --------------------------------------------------------------------------- helpers


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_contract(path: Path) -> dict:
    return read_json(path)


def read_landing(path: Path) -> dict:
    return read_json(path)


def is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def validate(contract: dict, row: dict) -> str | None:
    """First reason a row cannot take part in resolution, or None. Fixed order, fixed text."""
    for field in contract["key"]:
        if not isinstance(row.get(field), str) or not row.get(field):
            return f"missing key field {field}"
    if not is_int(row.get("version")) or row["version"] < 1:
        return "version must be a positive integer"
    for measure, rule in contract["measures"].items():
        value = row.get(measure)
        if not is_int(value):
            return f"{measure} must be an integer"
        if value < rule["min"]:
            return f"{measure} must be at least {rule['min']}"
        bound = rule.get("max_field")
        if bound is not None and is_int(row.get(bound)) and value > row[bound]:
            return f"{measure} must not exceed {bound}"
    return None


def key_of(contract: dict, row: dict) -> tuple:
    return tuple(row[field] for field in contract["key"])


def resolve_rows(contract: dict, retained: dict[str, dict], event_conflicts: list[dict]) -> dict:
    """Latest valid version per business key; invalid rows excluded with a reason; blocking conflicts listed.

    A conflict blocks only when it touches what would be published: the winning
    version of its key, or a retained row that cannot be placed. A later valid
    version supersedes a conflict on an older one.
    """
    excluded = []
    candidates: dict[tuple, dict[int, dict[str, dict]]] = {}
    for event_id in sorted(retained):
        row = retained[event_id]
        reason = validate(contract, row)
        if reason:
            excluded.append({"event_id": event_id, "reason": reason})
            continue
        versions = candidates.setdefault(key_of(contract, row), {})
        versions.setdefault(row["version"], {})[event_id] = row
    winning = {key: max(versions) for key, versions in candidates.items()}
    conflicts = []
    for item in event_conflicts:
        row = retained.get(item["event_id"], {})
        if validate(contract, row) or row["version"] == winning.get(key_of(contract, row)):
            conflicts.append(dict(item))
    rows = []
    for key in sorted(candidates):
        versions = candidates[key]
        latest = winning[key]
        payloads = {canonical({m: r[m] for m in contract["measures"]}) for r in versions[latest].values()}
        if len(payloads) > 1:
            conflicts.append({"key": list(key), "version": latest, "reason": "version_conflict",
                              "event_ids": sorted(versions[latest])})
        event_id = sorted(versions[latest])[0]
        row = versions[latest][event_id]
        out = {field: row[field] for field in contract["key"]}
        out.update({"version": latest, "event_id": event_id})
        out.update({measure: row[measure] for measure in contract["measures"]})
        rows.append(out)
    totals = {measure: sum(row[measure] for row in rows) for measure in contract["measures"]}
    return {"rows": rows, "totals": totals, "excluded": excluded,
            "conflicts": sorted(conflicts, key=canonical)}


def report_view(store: Store, as_of: str) -> dict:
    """What a reader may be shown for `as_of`: the date's report, an older one labelled stale, or nothing."""
    if as_of in store.reports:
        return {"status": "current", "report_date": as_of, "report_id": store.reports[as_of]["report_id"]}
    earlier = [day for day in store.reports if day < as_of]
    if earlier:
        day = max(earlier)
        return {"status": "stale_previous", "report_date": day, "report_id": store.reports[day]["report_id"]}
    return {"status": "blocked_no_snapshot", "report_date": None, "report_id": None}


# --------------------------------------------------------------------------- the six rules the starter leaves open


def next_action(record: dict, task: str) -> str:
    """'reuse' a task this run id already completed, 'run' it when its upstream succeeded, else 'upstream_failed'."""
    # Hint: a repair re-runs the same run id, so a task that already succeeded must not run again.
    raise NotImplementedError("GAP 1: return 'reuse' when this run id already completed the task, 'run' when every upstream task in DEPENDS_ON succeeded, otherwise 'upstream_failed'")


def check_freshness(landing: dict, business_date: str) -> None:
    """The landing file must describe the run's own business date."""
    # Hint: the landing file carries its own business_date; the file name proves nothing.
    raise NotImplementedError("GAP 2: raise StaleInput('stale_input', ...) unless the landing file describes the run's own business date")


def retain(area: dict[str, dict], row: dict) -> str:
    """Keep one copy per event id: 'added', 'duplicate' (same payload) or 'conflict' (different payload)."""
    # Hint: compare payloads with canonical(); never overwrite a retained row.
    raise NotImplementedError("GAP 3: keep one copy per event id and return 'added', 'duplicate' (identical payload) or 'conflict' (different payload)")


def report_identity(content: dict) -> str:
    """Derived from business content only, so the same content under any run id has the same identity."""
    # Hint: the run id must not appear in it, or a repair would mint a new report.
    raise NotImplementedError("GAP 4: derive the identity from the business content only: date, hyphen, first 12 hex of SHA-256 of canonical(content)")


def outbox_key(report: dict, recipient: str, ctx: dict) -> str:
    """One key per (report content, recipient): stable across retries, repairs and run ids."""
    # Hint: shortcuts.fresh_key_per_try and shortcuts.coarse_key show the two ways to get this wrong.
    raise NotImplementedError("GAP 5: return one key per report content and recipient that stays the same across retries and repairs")


def classify(failed_task: str | None, reason: str | None, evidence: dict, receiver_can_answer: bool) -> tuple[str, str]:
    """Name the boundary from recorded evidence (never from the injected failure's name) and the next action."""
    # Hint: expected/runbook.json lists the eight answers; never read the injected failure's name.
    raise NotImplementedError("GAP 6: name the boundary and the next action from the failed task, its recorded reason and the evidence")


# --------------------------------------------------------------------------- the four tasks


def retain_landing(pipe: "Pipeline", ctx: dict, landing: dict) -> dict:
    date = ctx["business_date"]
    area = pipe.store.raw.setdefault(date, {})
    conflicts = pipe.store.raw_conflicts.setdefault(date, [])
    counts = {"added": 0, "duplicate": 0, "conflict": 0}
    for row in landing["rows"]:
        outcome = pipe.impl.retain(area, row)
        counts[outcome] += 1
        if outcome == "conflict":
            item = {"event_id": row["event_id"], "reason": "event_conflict"}
            if item not in conflicts:
                conflicts.append(item)
    ctx["faults"].hit("after_raw_retention")
    return counts


def ingest_raw(pipe: "Pipeline", ctx: dict) -> dict:
    landing = read_landing(ctx["landing"])
    pipe.impl.check_freshness(landing, ctx["business_date"])
    return retain_landing(pipe, ctx, landing)


def resolve(pipe: "Pipeline", ctx: dict) -> dict:
    date = ctx["business_date"]
    result = resolve_rows(pipe.contract, pipe.store.raw.get(date, {}), pipe.store.raw_conflicts.get(date, []))
    pipe.store.resolved[date] = result
    ctx["faults"].hit("after_resolution")
    return {"rows": len(result["rows"]), "excluded": len(result["excluded"]), "conflicts": len(result["conflicts"])}


def publish_report(pipe: "Pipeline", ctx: dict) -> dict:
    date = ctx["business_date"]
    result = pipe.store.resolved[date]
    if result["conflicts"]:
        raise GateRefused("conflict", f"{len(result['conflicts'])} unresolved conflict(s)")
    content = {"contract": pipe.contract["name"], "report_date": date, "rows": result["rows"],
               "totals": result["totals"], "excluded": result["excluded"]}
    report_id = pipe.impl.report_identity(content)
    existing = pipe.store.reports.get(date)
    if existing is not None and existing["report_id"] == report_id:
        return {"report_id": report_id, "action": "unchanged"}
    later = [day for day in pipe.store.reports if day > date]
    record = {"report_id": report_id, "content": content, "published_by": ctx["run_id"], "backfill": bool(later)}
    if existing is not None:
        pipe.store.report_history.append(existing)
    pipe.store.reports[date] = record
    return {"report_id": report_id, "action": "replaced" if existing is not None else "published"}


def notify(pipe: "Pipeline", ctx: dict) -> dict:
    report = pipe.store.reports[ctx["business_date"]]
    keys = []
    for recipient in pipe.contract["recipients"]:
        key = pipe.key_fn(report, recipient, ctx)
        pipe.store.outbox.setdefault(key, {"key": key, "recipient": recipient, "report_id": report["report_id"],
                                           "report_date": report["content"]["report_date"],
                                           "state": "pending", "delivery_id": None})
        keys.append(key)
    ctx["faults"].hit("before_effect")
    sent = 0
    for key in keys:
        entry = pipe.store.outbox[key]
        if entry["state"] == "sent":
            continue
        delivery_id = pipe.channel.send(entry["recipient"], report, key=key)
        ctx["faults"].hit("after_effect")
        entry["state"] = "sent"
        entry["delivery_id"] = delivery_id
        sent += 1
    return {"sent": sent}


TASK_FUNCTIONS = {"ingest_raw": ingest_raw, "resolve": resolve, "publish_report": publish_report, "notify": notify}


# --------------------------------------------------------------------------- the runner


class Pipeline:
    """A local runner over one contract, one store and one channel."""

    def __init__(self, contract: dict, store: Store | None = None, channel: LocalChannel | None = None,
                 tasks: dict | None = None, retries: dict[str, int] | None = None, key_fn=None):
        self.contract = contract
        self.store = store if store is not None else Store()
        self.channel = channel if channel is not None else LocalChannel()
        self.impl = sys.modules[__name__]
        self.tasks = {**TASK_FUNCTIONS, **(tasks or {})}
        self.retries = {task: 0 for task in TASKS}
        self.retries.update(retries or {})
        self.key_fn = key_fn if key_fn is not None else outbox_key

    def run(self, run_id: str, business_date: str, landing: Path, faults: Faults | None = None) -> dict:
        record = self.store.runs.get(run_id)
        if record is None:
            record = {"run_id": run_id, "business_date": business_date, "attempts": 0, "status": "pending",
                      "tasks": {task: {"status": "not_run", "executions": 0, "reason": None, "detail": None}
                                for task in TASKS}}
            self.store.runs[run_id] = record
        elif record["business_date"] != business_date:
            raise RunIdentityError(f"run id {run_id} belongs to {record['business_date']}, not {business_date}")
        if record["status"] == "succeeded":
            return {"run_id": run_id, "status": "already_succeeded", "attempt": record["attempts"],
                    "tasks": {task: record["tasks"][task]["status"] for task in TASKS}}
        record["attempts"] += 1
        ctx = {"run_id": run_id, "business_date": business_date, "landing": Path(landing),
               "faults": faults if faults is not None else Faults(), "attempt": record["attempts"], "try": 0}
        for task in TASKS:
            state = record["tasks"][task]
            action = self.impl.next_action(record, task)
            if action == "reuse":
                continue
            if action == "upstream_failed":
                state.update(status="upstream_failed", reason=None)
                continue
            tries = 0
            while True:
                tries += 1
                ctx["try"] = tries
                state["executions"] += 1
                try:
                    detail = self.tasks[task](self, ctx)
                except TaskError as error:
                    if error.transient and tries <= self.retries[task]:
                        continue
                    state.update(status="failed", reason=error.reason, detail=error.detail or None)
                    self._alert(run_id, task, error.reason)
                    break
                state.update(status="succeeded", reason=None, detail=detail)
                break
        record["status"] = "succeeded" if all(record["tasks"][t]["status"] == "succeeded" for t in TASKS) else "failed"
        return {"run_id": run_id, "status": record["status"], "attempt": record["attempts"],
                "tasks": {task: record["tasks"][task]["status"] for task in TASKS}}

    def _alert(self, run_id: str, task: str, reason: str) -> None:
        key = f"alert:{run_id}:{task}:{reason}"
        if all(alert["key"] != key for alert in self.store.alerts):
            self.store.alerts.append({"key": key, "to": OPS_RECIPIENT, "run_id": run_id, "task": task,
                                      "reason": reason})

    def evidence(self, run_id: str) -> dict:
        """What remains for this run's business date, read from the store and the receiver."""
        date = self.store.runs[run_id]["business_date"]
        report = self.store.reports.get(date)
        entries = [entry for entry in self.store.outbox.values()
                   if report is not None and entry["report_id"] == report["report_id"]]
        pending = [entry for entry in entries if entry["state"] == "pending"]
        return {
            "raw_retained": bool(self.store.raw.get(date)),
            "resolved": date in self.store.resolved,
            "report_published": report is not None,
            "outbox_pending": len(pending),
            "outbox_sent": len(entries) - len(pending),
            "pending_already_delivered": sum(1 for entry in pending if self.channel.lookup(entry["key"])),
        }

    def diagnose(self, run_id: str) -> dict:
        record = self.store.runs[run_id]
        failed = [task for task in TASKS if record["tasks"][task]["status"] == "failed"]
        failed_task = failed[0] if failed else None
        reason = record["tasks"][failed_task]["reason"] if failed_task else None
        evidence = self.evidence(run_id)
        boundary, action = self.impl.classify(failed_task, reason, evidence, self.channel.honours_keys)
        return {"failed_task": failed_task, "boundary": boundary, "action": action, "evidence": evidence}
