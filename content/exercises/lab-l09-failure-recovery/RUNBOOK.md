# Operations runbook: line 3 daily inspection report

An original runbook pattern for this lab's local pipeline, not an official
incident procedure for any product. Its decision table is
`expected/runbook.json`, and `Pipeline.diagnose(run_id)` is tested against it
row by row, so the page and the code cannot drift apart silently.

**Owner.** The line 3 data owner (fictional) owns the pipeline and this page.
The quality lead owns the business meaning of the report. Alerts go to
`ops-on-call` (a local list in this lab), one per run id, task and reason.

## Before you touch anything

1. Record the run id, its business date, the attempt number and every task's
   status, executions and reason from the run ledger.
2. Record the evidence for the date: raw retained, resolved, report
   published (and its `report_id`), outbox entries pending and sent, and how
   many pending keys the recipient already holds.
3. Record which report readers are shown for the date (`current`,
   `stale_previous` with its date, or `blocked_no_snapshot`).
4. Keep the failed run's ledger and alert. A later green repair does not erase
   them.

## Decision table

| Evidence you see | Boundary | Action | Must not |
|---|---|---|---|
| `ingest_raw` failed; raw retained; nothing resolved | after raw retention | Repair: re-run the same run id | Delete the retained rows "to start clean"; they are the evidence, and retention is idempotent |
| `resolve` failed; resolved state present; no report | after resolution | Repair: re-run the same run id | Publish the resolved state by hand; the gate has not run |
| `notify` failed; report published; entries pending; recipient holds none of them | before the effect | Repair: re-run the same run id | Republish the report; it is already current |
| `notify` failed; report published; entries pending; recipient holds some | after the effect | Repair: re-run the same run id; the keys make the repeat a lookup | Send the missing notices by hand outside the outbox |
| `notify` failed; the recipient cannot say which keys it holds | effect unknown | Reconcile with the recipient first, then mark or resend each entry deliberately | Retry blindly; it may notify twice |
| `ingest_raw` failed with `stale_input` | stale input | Wait for the correct export, then repair the same run id | Force the stale file through; every task would be green and the report wrong |
| `publish_report` failed with `conflict` | publication gate | Ask the source owner to correct the record; process it in a new run id | Pick one of the conflicting values; relabel the previous report as current for the new date |
| Every task succeeded | none | None | Treat green as proof: compare the report with the expected result anyway |

## Worked entries

**After raw retention.** Readers see 2026-03-02 labelled `stale_previous` for
2026-03-03. Four events are retained. Repair the same run id: `ingest_raw`
runs again and finds all five rows already retained (0 added, 5 duplicates),
then resolve, publish and notify run once. Prove recovery by comparing the
2026-03-03 report with the independently written 50/2 result and by counting
exactly one delivery per recipient for its `report_id`.

**After resolution.** The same view and the same repair; only `resolve`,
`publish_report` and `notify` run (executions 1/2/1/1). The retained rows are
reused, not re-read.

**Before the effect.** The 2026-03-03 report is already `current`; two outbox
entries are pending and the recipient holds neither key. Repair the same run
id; only `notify` runs and each recipient receives the report once.

**After the effect.** The report is `current`; two entries are pending;
quality-lead already received `m3`. Repair the same run id: the channel
recognizes quality-lead's key and returns `m3` without a second message;
line-3-supervisor receives `m4`. Four deliveries in total, two for the date.

**Effect unknown.** The same state against a recipient that ignores keys and
answers no lookups. Do not repair yet. Ask the recipient (or its logs) which
notices arrived, mark those entries sent with their delivery ids, then resend
only the rest. A blind retry here sends quality-lead a second copy.

**Stale input.** The 2026-03-04 slot holds an export whose own business date
is 2026-03-03. Nothing was retained; readers see 2026-03-03 as
`stale_previous`. When the correct export lands, repair the same run id: only
the failed `ingest_raw` and its dependents run, and the 60/4 report is
published.

**Publication gate (Harbourline, 2026-03-06).** Two events carry different
scan counts for dock D1, trailer T-91, version 1. Nothing is published and
readers see the corrected 2026-03-05 report as `stale_previous`. A repair of
the same run id meets the same stored conflict and fails again. When the
source sends version 2 for D1/T-91, a new run id retains it, the conflict on
version 1 no longer touches what would be published, and the 23/23 report is
published and announced once to each recipient.

## Backfill and late corrections

- A missed date is backfilled with its own run id and its own retained or
  landed input. Publishing it never moves the current report of a later date;
  its notices carry `backfill: true`.
- A run id that succeeded is closed. New input for its date is processed by a
  new run id: the report is replaced only if its content changed, the old
  version is kept in history, and recipients are told once about the new
  identity.

## After any recovery

Compare, against results written before the recovery: the report rows,
totals and exclusions; the view label for the date; one delivery per
recipient per report identity; no pending outbox entry for the current
report; one alert per failure reason. Record the comparison with the run id.
