*Local-executed (R): Python 3.12 standard library, one machine, no network,
43 tests. There is no scheduler service, no Lakeflow Jobs run and no
Databricks workspace: a short local runner walks four tasks and keeps a ledger
per run id, failures are injected by raising an exception at a named point,
and the only "external effect" appends a dictionary to a Python list. No
message is ever sent. Everything below can be studied without installing
anything.*

### What this lab is for

[Orchestration and operations](#/module/dbxfe-orchestration) argues that a
green task is a statement about the task's success condition, not about the
business data, and that each failure boundary leaves its own kind of
evidence. This lab makes you prove both on a small daily report for
Cinderline Components' line 3 inspections. Four tasks run in order —
`ingest_raw` retains the export, `resolve` keeps the latest valid version of
each lot, `publish_report` stores the report under its business date, and
`notify` tells two recipients through an outbox — and the lab breaks the
chain on purpose at four places:

| Boundary | Where the failure is raised | What has already happened |
|---|---|---|
| after raw retention | inside `ingest_raw`, after rows are kept | raw rows retained |
| after resolution | inside `resolve`, after the result is stored | retained and resolved |
| before the effect | inside `notify`, after outbox entries are written | report published, nobody told |
| after the effect | inside `notify`, after the first send | report published, one recipient told, not recorded |

Recovery means re-running the **same run id**: the runner reuses every task
its ledger shows as succeeded and runs the failed task and its dependents
again. After every recovery the business state is compared with results
written by hand before any code ran.

### The data, briefly

| Date | Export rows | What the report should say |
|---|---|---|
| 2026-03-02 | L-101 v1 then v2 (42/2), L-102 sent twice (25/0), L-103 with −5 inspected | 2 rows, 67 inspected, 2 defective; L-103 excluded |
| 2026-03-03 | L-104 sent twice (30/1), L-105 v1 then v2 (20/1), L-106 with 13 defective of 12 | 2 rows, 50/2; L-106 excluded |
| 2026-03-04 | L-107 (36/3), L-108 v1 then v2 (24/1), L-109 with "15" as text | 2 rows, 60/4; L-109 excluded |

Three extra files cause trouble on purpose: yesterday's export re-delivered
into the 2026-03-04 slot, a late version 2 for L-104, and event `e07` re-sent
with a different defect count. A second contract, Harbourline dock scans,
has a two-field key (`dock`, `trailer`), three recipients, a correction and
a conflict. The resolution rules are the ones taught in
[duplicates, invalid records and conflicts](#/lesson/dbxfe-record-resolution).

### Task by task, with the intermediate output

**Repair (gap 1).** `next_action` returns `reuse` for a task the run id
already completed, `run` when every upstream task succeeded, and
`upstream_failed` otherwise. After a failure after resolution the ledger
reads `ingest_raw` succeeded, `resolve` failed, the other two
`upstream_failed`, and readers are shown 2026-03-02 labelled
`stale_previous`. The repair executes the tasks 1/2/1/1 times in total: the
retained rows are reused, not re-read.

**Freshness (gap 2).** The landing file declares its own business date. The
stale file in the 2026-03-04 slot says 2026-03-03, so `ingest_raw` fails with
`stale_input` before retaining anything, writes one alert and publishes
nothing. The error is not transient, so even a policy of two extra tries runs
the task once. When the right export lands, repairing the same run id
publishes 60/4.

**Idempotent retention (gap 3).** One copy per event id: `added`,
`duplicate` or `conflict`, never an overwrite. A repair after a failure after
raw retention reports 0 added and 5 duplicates — the whole file, including
its in-file duplicate, was already there.

**Identity (gap 4).** The report id is the date plus 12 hexadecimal
characters of SHA-256 over the canonical content, for example
`2026-03-02-bce5195c4faf`. The run id is not in it, so a second run over the
same input reports `unchanged` and sends nothing.

**The outbox key (gap 5).** `notify:<report_id>:<recipient>`. After a failure
after the effect, the outbox holds two pending entries while quality-lead
already has message `m3`. The repair re-sends that entry with the same key;
the local recipient recognizes it and returns `m3` without appending, and
line-3-supervisor receives `m4`: four deliveries in total, two for the date.

**Diagnosis (gap 6).** `classify` names the boundary from the evidence — raw
retained, resolved, report published, pending entries, how many of them the
recipient already holds — and from two recorded reasons, `stale_input` and
`conflict`. It never reads the injected failure's name, because a real crash
does not announce its boundary. Eight rows of `expected/runbook.json` must
match, and `RUNBOOK.md` turns them into an operations runbook with a *must
not* column.

### The failure cases

**A naive retry.** Without a key, one transient fault after the effect and
one extra try deliver quality-lead, quality-lead, line-3-supervisor, and the
run is green. With the fault *before* the effect the same code sends each
report once, which is why it survives casual testing.

**A key per try.** Adding the attempt number to the key sends the same
duplicate and leaves two entries pending for ever.

**A key without the report identity.** Keying by date and recipient absorbs
retries, but when Harbourline's correction replaces the 2026-03-05 report
nobody is told: three deliveries where six are right.

**A key the recipient ignores.** The outbox is right and the duplicate
happens anyway; the diagnosis becomes `effect_unknown`, and the runbook says
reconcile with the recipient before any retry.

**Every task green, wrong data.** Without the freshness check the stale
export publishes 2026-03-03's rows and 50/2 totals as the 2026-03-04 report
and announces it. Every task succeeded. The correct report is 60/4.

**Backfill and late input.** With 2026-03-02 and 2026-03-04 published, a
backfill of 2026-03-03 publishes with `backfill: true` and leaves 2026-03-04
current. Re-running that succeeded run id with the late correction changes
nothing; a new run id picks it up, replaces the report (the old id kept in
history) and tells both recipients once. The conflicting re-delivery of
`e07` blocks publication without undoing the report already current.

### What the tests prove and do not prove

Forty-three tests prove, for CPython 3.12.3 on one machine: the rows, totals,
exclusions and ids of every report against hand-derived literals (ids also
recomputed by a digest written independently in the test file); the ledger,
evidence, view label, delivery count and alert count after each boundary
failure and after its repair; the retry, key and recipient cases above; the
stale-input refusal; backfill, closed run ids and corrections; the
eight-row runbook; the Harbourline transfer, including a superseding version
that clears a conflict only in a new run. An optional mutation check breaks
fourteen rules one at a time and each turns the suite red; those runs are not
part of the recorded evidence.

They do not prove anything about Lakeflow Jobs, its retries, repair runs,
run-if conditions or notifications; durability across a real process crash;
concurrent runs; timeouts; or how any real email, chat or webhook service
treats an idempotency key. The freshness rule checks one declared date, not
completeness or lateness. Background on retained history and replay is in
[Orchestration, failure, and reconciliation](#/lesson/dbxfe-m04-l03) and
[Ingestion, records and reliable updates](#/module/dbxfe-m04).

### Setup, run and cleanup

Nothing to install. From the lab folder run
`python3.12 run_tests.py --evidence evidence.json`; to check your own work,
fill the six gaps in `starters/pipeline.py` and run
`python3.12 run_tests.py --starter` (41 tests; the two that inspect the
untouched starter are left out). Optionally run `python3.12 mutation_check.py`,
which works in temporary copies it deletes. Afterwards delete
`evidence.json`; the runner writes nothing else and creates no
`__pycache__`.
