# Solutions

The complete reference is `solutions/pipeline.py`. This file explains the six
gaps, shows the intermediate state at each boundary, and names the wrong
approaches the tests exist to catch. Every number below is reproduced by
`run_tests.py` against a hand-written literal in `expected/`.

## The shape of the pipeline

Four tasks, each depending on the one before:

```
ingest_raw ──► resolve ──► publish_report ──► notify
   │              │               │              │ └─ after_effect  (sent, not yet marked sent)
   │              │               │              └─── before_effect (outbox entries written, nothing sent)
   │              │               └─ report stored under its business date
   │              └─ after_resolution (resolved state stored)
   └─ after_raw_retention (rows retained)
```

`Pipeline.run(run_id, business_date, landing, faults)` keeps a ledger per run
id: attempts, and for each task its status, executions, reason and detail.
A task error is either transient (retried up to the task's retry count) or
not; when it finally fails the runner writes one alert per run id, task and
reason and marks every dependent `upstream_failed`.

## GAP 1 — `next_action`

```python
def next_action(record, task):
    if record["tasks"][task]["status"] == "succeeded":
        return "reuse"
    if all(record["tasks"][upstream]["status"] == "succeeded" for upstream in DEPENDS_ON[task]):
        return "run"
    return "upstream_failed"
```

The first rule is what makes a repair a repair: re-running the same run id
does not repeat work the ledger says is done. The second is the dependency:
a task waits for *success* upstream, not for completion. A publish that ran
after a failed resolve would publish whatever the resolved area happened to
hold (mutation M2 does this, and the boundary, stale-input and conflict tests fail).

A succeeded run id is closed: `run` returns `already_succeeded` without an
attempt. That is also why a repair never re-reads new input: offered the late
correction file, `line3-2026-03-03` changes nothing, and the correction needs
a new run id.

## GAP 2 — `check_freshness`

```python
def check_freshness(landing, business_date):
    if landing.get("business_date") != business_date:
        raise StaleInput("stale_input", f"landing describes {landing.get('business_date')}, run is for {business_date}")
```

`StaleInput` is not transient, so no retry policy repeats it; the fix is a
fresh file, then a repair of the same run id.

## GAP 3 — `retain`

```python
def retain(area, row):
    event_id = row["event_id"]
    if event_id not in area:
        area[event_id] = dict(row)
        return "added"
    if canonical(area[event_id]) == canonical(row):
        return "duplicate"
    return "conflict"
```

Retention is keyed by business date and event id, not by run id, so a repair,
a retry and a second run over the same file all land on the rows already
there. After a failure after raw retention, the repair's detail is
`{"added": 0, "duplicate": 5, "conflict": 0}`: all five rows of the file
(including the in-file duplicate) were already retained.

## GAP 4 — `report_identity`

```python
def report_identity(content):
    return f"{content['report_date']}-{sha256(canonical(content).encode('utf-8')).hexdigest()[:12]}"
```

The run id is deliberately absent. The same content under `adhoc-rerun-7`
has the id `2026-03-02-bce5195c4faf`, like the scheduled run's, and a second
run over the same input reports `{"action": "unchanged"}`.

## GAP 5 — `outbox_key`

```python
def outbox_key(report, recipient, ctx):
    return f"notify:{report['report_id']}:{recipient}"
```

The key names one intent: *this report content, to this recipient*. It is the
same on every retry and repair, different for a corrected report (new
content, new id) and different per recipient.

## GAP 6 — `classify`

```python
def classify(failed_task, reason, evidence, receiver_can_answer):
    if failed_task is None:
        return "none", "none"
    if failed_task == "ingest_raw" and reason == "stale_input":
        return "stale_input", "wait_for_fresh_input_then_repair"
    if failed_task == "publish_report" and reason == "conflict":
        return "publication_gate", "new_run_after_source_correction"
    if failed_task == "ingest_raw" and evidence["raw_retained"]:
        return "after_raw_retention", "repair_same_run_id"
    if failed_task == "resolve" and evidence["resolved"]:
        return "after_resolution", "repair_same_run_id"
    if failed_task == "notify" and evidence["report_published"]:
        if not receiver_can_answer:
            return "effect_unknown", "reconcile_with_recipient_before_retry"
        if evidence["pending_already_delivered"] == 0:
            return "before_effect", "repair_same_run_id"
        return "after_effect", "repair_same_run_id"
    return "unclassified", "escalate_to_owner"
```

The two recorded reasons are business outcomes the pipeline wrote down; the
rest is read from what is actually in the store and what the receiver says it
holds. The text `injected:after_effect` is never consulted, because a real
crash does not name its boundary.

## Intermediate outputs: a failure after the effect, then its repair

After 2026-03-02 ran cleanly, `line3-2026-03-03` fails once at
`after_effect`:

```
run    {'status': 'failed', 'attempt': 1, 'tasks': {'ingest_raw': 'succeeded', 'resolve': 'succeeded',
        'publish_report': 'succeeded', 'notify': 'failed'}}
outbox notify:2026-03-02-bce5195c4faf:quality-lead        sent     m1
       notify:2026-03-02-bce5195c4faf:line-3-supervisor   sent     m2
       notify:2026-03-03-24ebcfbf4307:quality-lead        pending  None
       notify:2026-03-03-24ebcfbf4307:line-3-supervisor   pending  None
channel m1, m2 (2026-03-02), m3 quality-lead 2026-03-03
alerts  alert:line3-2026-03-03:notify:injected:after_effect → ops-on-call
diagnose {'failed_task': 'notify', 'boundary': 'after_effect', 'action': 'repair_same_run_id',
          'evidence': {'raw_retained': True, 'resolved': True, 'report_published': True,
                       'outbox_pending': 2, 'outbox_sent': 0, 'pending_already_delivered': 1}}
```

The 2026-03-03 report is published and `current`; one recipient has it; the
outbox cannot tell which, but the receiver can (`pending_already_delivered`
is 1). The repair re-runs only `notify` (executions 1/1/1/2): the pending
quality-lead entry is sent again with the same key, the channel returns `m3`
without appending (`suppressed` 1), and line-3-supervisor receives `m4`.
Four deliveries in total, two for 2026-03-03, and the recovered report equals
`expected/reports.json` field for field.

All four boundaries, in the same setup:

| Boundary | Failed task | Retained / resolved / published | Pending entries | Deliveries | 2026-03-03 view | Repair executions |
|---|---|---|---|---|---|---|
| after raw retention | `ingest_raw` | yes / no / no | 0 | 2 | `stale_previous` 2026-03-02 | 2/1/1/1 |
| after resolution | `resolve` | yes / yes / no | 0 | 2 | `stale_previous` 2026-03-02 | 1/2/1/1 |
| before the effect | `notify` | yes / yes / yes | 2 | 2 | `current` | 1/1/1/2 |
| after the effect | `notify` | yes / yes / yes | 2 (1 delivered) | 3 | `current` | 1/1/1/2 |

## The publication gate and conflicts (complete in the starter)

`resolve_rows` lists only conflicts that touch what would be published: an
event conflict whose retained row is the winning version of its key, or two
different payloads at the winning version. `publish_report` refuses when that
list is not empty. On Harbourline's 2026-03-06 the two version 1 payloads for
D1/T-91 block the report, and repairing the same run id fails again because
the stored resolution has not changed. The source's version 2 (h09), processed
by the new run id `harbour-2026-03-06-c1`, wins, the version 1 conflict no
longer touches the report, and D1/T-91 14/14 with D2/T-92 9/9 (23/23) is
published and announced once to each of the three recipients. A repair
re-uses the tasks that succeeded; only a new run re-reads new input.

## Wrong approaches, and why each fails

**Retry without a key** (`shortcuts.notify_without_key`). With one extra try
and one transient fault after the effect, the deliveries are quality-lead,
quality-lead, line-3-supervisor, and the run is green. Nothing identifies the
first send, so the retry cannot know it happened. The same shortcut with a
fault *before* the effect sends each report once, which is why it survives
casual testing: the dangerous boundary is the one after the effect.

**A fresh key per try** (`shortcuts.fresh_key_per_try`). A key that includes
the attempt or try number, or a random id generated on each call, looks like
idempotency and behaves like none: the repeat carries a key the receiver has
never seen, quality-lead is notified twice, and the first try's two entries
stay pending for ever (2 sent, 2 pending).

**A key without the report identity** (`shortcuts.coarse_key`). Keying by
date and recipient absorbs retries, but when Harbourline's correction
replaces the 2026-03-05 report the new keys equal the old ones, all three
entries are already `sent`, and nobody is told that the numbers changed
(3 deliveries where 6 are right).

**Trusting the landing slot** (`shortcuts.ingest_without_freshness`). With
yesterday's export in the 2026-03-04 slot every task is green and the
published 2026-03-04 report is 2026-03-03's rows and 50/2 totals under a new
date, announced to both recipients. The correct 2026-03-04 report is 60/4.
A green run is a statement about the tasks' success conditions, not about the
business data.

**A key alone, with a receiver that ignores it.** The outbox is correct, but
`LocalChannel(honours_keys=False)` appends every send: three deliveries after
one retry. An idempotency key protects only when the receiver deduplicates on
it or can be asked what it already holds; otherwise the runbook must
reconcile with the recipient before any retry (`effect_unknown`).

## Fourteen mutations

`python3.12 mutation_check.py` applies each of these to a temporary copy of
the package and requires at least one test to fail. When the lab was written
all fourteen were caught; these runs check the tests, and they are not part of
the recorded evidence.

| Mutation | What it breaks |
|---|---|
| M1 repair re-runs succeeded tasks | Execution counts and the retained-raw reuse |
| M2 dependents run after a failure | `upstream_failed`, the stale label, the gate |
| M3 no freshness check | The stale-input refusal |
| M4 retention overwrites | Retention counts, conflict evidence, repaired reports |
| M5 identity from rows only | Every report id |
| M6 key per try | Suppression after the effect |
| M7 gate ignores conflicts | Both conflict cases |
| M8 invalid rows take part | Every report's rows and totals |
| M9 receiver never deduplicates | The keyed retry and the repair after the effect |
| M10 no transient retry | Every retry case |
| M11 alerts not deduplicated | One alert per run, task and reason |
| M12 diagnosis trusts an unanswerable receiver | `effect_unknown` |
| M13 superseded conflicts still block | The superseding Harbourline version never publishes |
| M14 superseded event conflicts still block | A conflict on an older version blocks a newer one |
