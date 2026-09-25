# Tasks

Work in `starters/pipeline.py`. Everything except six small functions is
complete. Each gap raises `NotImplementedError("GAP n: …")` until you fill it.
Run `python3.12 run_tests.py --starter` after each task; the tests named in a
task should turn green. Write every prediction down before you run anything:
the point of the lab is to know what the state *should* be before the code
tells you what it *is*.

## Task 0 — Predict before you build

Read `fixtures/landing/2026-03-02.json` and `2026-03-03.json` and
`fixtures/contract.json`. Without running code, write down for each date: the
rows that will be published (key, version, winning event id, measures), the
totals, and each excluded event with its reason. Then compare with
`expected/reports.json` and, where you differ, find the rule in DATA.md that
you misread.

## Task 1 — The task graph and repair (GAP 1, `next_action`)

The runner asks `next_action(record, task)` before each task. Return:

- `"reuse"` when this run id's ledger already shows the task `succeeded`;
- `"run"` when every task in `DEPENDS_ON[task]` has `succeeded`;
- `"upstream_failed"` otherwise.

Expected behaviour: a clean run executes each task once; after a failure in
`resolve`, `publish_report` and `notify` are `upstream_failed`; re-running the
same run id executes `resolve`, `publish_report` and `notify` but not
`ingest_raw` (executions 1/2/1/1). Tests: `BoundaryTests`, and the repair
steps of `RetryTests` and `TransferTests`.

## Task 2 — Refuse a stale input (GAP 2, `check_freshness`)

Raise `StaleInput("stale_input", <detail>)` when the landing file's own
`business_date` differs from the run's. Do not trust the file name.

Expected behaviour: running `line3-2026-03-04` on
`fixtures/stale/2026-03-04.json` fails in `ingest_raw` with reason
`stale_input`, retains nothing for 2026-03-04, publishes nothing, sends
nothing and writes one alert; the 2026-03-04 view is `stale_previous`
showing 2026-03-03. The error is not transient, so a retry policy of two
extra tries still executes `ingest_raw` once. Tests: `StaleInputTests`,
`test_a_non_transient_error_is_not_retried`.

## Task 3 — Idempotent raw retention (GAP 3, `retain`)

Keep one copy per `event_id` in the date's area. Return `"added"` for a new
id, `"duplicate"` for an identical payload, `"conflict"` for a different
payload, and never overwrite the retained row.

Expected behaviour: 2026-03-02 reports `{"added": 4, "duplicate": 1,
"conflict": 0}`; repairing a failure after raw retention reports
`{"added": 0, "duplicate": 5, "conflict": 0}` and publishes exactly the
report a clean run would; the conflicting re-delivery of e07 is counted as
one conflict and e07 keeps defective 1. Tests: `ResolutionTests`,
`test_repair_after_raw_retention_re_retains_nothing_new`,
`test_a_conflicting_redelivery_blocks_publication_without_undoing_the_report`.

## Task 4 — A report identity from content (GAP 4, `report_identity`)

Return the business date, a hyphen and the first 12 hexadecimal characters of
SHA-256 over `canonical(content)`.

Expected behaviour: the 2026-03-02 report is `2026-03-02-bce5195c4faf` under
any run id; a second run id over the same landing file leaves the report
`unchanged` and sends nothing; the late correction produces a new id and the old one moves to
`report_history`. Tests: `test_report_identity_is_the_independent_digest_of_the_expected_content`,
`test_the_same_content_under_another_run_id_has_the_same_identity`.

## Task 5 — The outbox key (GAP 5, `outbox_key`)

Return a key that is identical for every retry and repair of one report to
one recipient, and different for a corrected report or another recipient.

Expected behaviour: one transient fault after the effect with one extra try
gives exactly two deliveries and `suppressed == 1`; a repair after the effect
gives four deliveries in total, two for 2026-03-03; the Harbourline
correction sends three new deliveries. Compare your key with the two wrong
ones in `starters/shortcuts.py` (`fresh_key_per_try`, `coarse_key`) and
predict what each would do before you read their tests.

## Task 6 — Diagnose from evidence (GAP 6, `classify`)

Given the first failed task, its recorded reason, the evidence dictionary from
`Pipeline.evidence()` and whether the receiver can answer lookups, return
`(boundary, action)`. Use the recorded reasons `stale_input` and `conflict`;
otherwise decide from the evidence alone, never from the text `injected:…`.

Expected behaviour: the eight rows of `expected/runbook.json`, including
`effect_unknown` → `reconcile_with_recipient_before_retry` when the receiver
ignores keys, because pending entries could then be either delivered or not.
Tests: `RunbookTests`.

## Task 7 — Break it on purpose

1. Plug `shortcuts.notify_without_key` into a pipeline with one extra
   `notify` try and one transient `after_effect` fault. Predict the delivery
   list, then check it: quality-lead should appear twice, and the run should
   still be green.
2. Repeat with a `before_effect` fault. Explain why the same shortcut now
   sends each report once, and why that makes it more dangerous, not less.
3. Plug in `shortcuts.ingest_without_freshness` and run 2026-03-04 on the
   stale file. Every task is green. Write two sentences for the quality lead
   saying what was published and why the green run is wrong.

## Task 8 — Backfill and correction

Run 2026-03-02 and 2026-03-04, then backfill 2026-03-03. Predict the view for
each date before and after, and the `backfill` flag. Then re-run
`line3-2026-03-03` with the late correction file and predict what changes
(nothing: a succeeded run id is not re-read). Start a new run id for the
correction instead and predict the new report, the history and the two new
deliveries. Check against `expected/backfill.json`.

## Task 9 — Transfer

Build a `Pipeline` over `fixtures/transfer/contract.json` and write your own
expected results for Harbourline before running anything: the first day after
a fault at `after_resolution` and its repair, the correction run, the
2026-03-06 conflict, a repair of that same run id, and the new run id that
processes the source's version 2 for D1/T-91. Compare with `expected/transfer.json`. Then answer: with
the key `notify:<date>:<recipient>`, who learns about the correction?

## Task 10 — Write your runbook entry

Pick one boundary and write the runbook entry you would hand to an on-call
engineer: what they will see, what to record before touching anything, the
exact recovery action, the comparison that proves recovery, and what they
must not do. `RUNBOOK.md` has one worked example per boundary to compare
against once you have written yours.
