# Lab L23 tasks

Work in `starters/`. Each task names the GAP it closes and the behaviour the tests
expect. Run `python3.12 run_tests.py --starter` after each task; the tests compare
your SQL's results with the hand-derived literals in `expected/`. Before running,
write down your prediction for every result you are asked to predict.

## Task 1 — Schema rules (GAP 1 to 5, `starters/schema.sql`)

Add the missing rules so that each of the ten bad writes in
`fixtures/constraint_cases.json` is refused with the SQLSTATE and constraint name
listed in `expected/constraints.json`, and the review_item row count stays 6:

- `defect_code` only CRACK, POROSITY, DIMENSION or SURFACE (a column CHECK named by
  PostgreSQL as `review_item_defect_code_check`);
- `severity` between 1 and 4 (`review_item_severity_check`);
- a table CHECK named `review_item_state_consistent`: ready has no owner and no
  decision; claimed has an owner and no decision; decided has both;
- a partial index over ready rows in claim order (severity descending, then
  `flagged_at`, then `item_id`);
- a partial UNIQUE index named `review_item_one_open_claim` so a reviewer holds at
  most one claimed item.

Expected: the three-row batch in `atomic_batch` fails with 23514 and inserts none
of its rows, including the two valid ones.

## Task 2 — Least privilege (GAP 6, `starters/grants.sql`)

Replace the blanket grant. `qr_app` may read `plant` and `reviewer`, select,
insert and update `review_item`, and select and insert `intake_message`.
Expected: DELETE on `review_item`, UPDATE and TRUNCATE on `intake_message` fail
with 42501 "permission denied", and DROP fails with 42501 "must be owner".

## Task 3 — Idempotent intake (GAP 9 and 10, `starters/intake.sql`)

Log each `message_id` once and let an item change only for a newer `source_seq`
while its status is ready. Predict each of the ten outcomes in
`fixtures/intake_stream.json` (applied or skipped) before running. Expected:
applied, applied, applied, skipped, applied, applied, skipped, applied, applied,
skipped; 8 logged messages; the six items in `expected/intake.json`; replaying the
whole stream again changes nothing.

## Task 4 — The claim (GAP 7, `starters/claim.sql`)

Lock the chosen row in the subquery and skip rows another session holds. Expected
claim order for one reviewer who decides each item before claiming the next:
QR-0001, QR-0002, QR-0005, QR-0003, QR-0006, QR-0004, then no row.

## Task 5 — Two sessions claim at once

With session A inside an open transaction holding its claim, predict what session
B receives with your claim, with plain `FOR UPDATE`, and with `FOR UPDATE NOWAIT`
on QR-0001. Expected: QR-0002 at once; QR-0002 only after A commits (B's
`wait_event_type` reads `Lock` meanwhile); SQLSTATE 55P03.

## Task 6 — The decision (GAP 8, `starters/decide.sql`)

Make the decision succeed only for the version the form loaded, while the item
is claimed, by the reviewer who holds it. Expected sequence: R-101 claims
QR-0001 at version 3; a supervisor reassigns it to R-103 (version 4); R-101's
submit with version 3 returns no row; R-101's submit with version 4 also returns
no row; R-103's submit with version 4 returns `QR-0001|decided|rework|5`.

## Task 7 — Isolation timeline

In two psql sessions, reproduce the three sequences of test 13 and predict each
read before you run it: the Read Committed counts (6, then 5), the Repeatable
Read counts (5, then 5) and the Repeatable Read update's SQLSTATE (40001), then
the Read Committed update that succeeds on an item another reviewer has just
claimed. Write one sentence on which of the two is the dangerous result.

## Task 8 — Session state

Predict what session B sees for a temp table, an unqualified table name and an
advisory lock that session A created or took. Expected: 42P01, 42P01, `f` while A
is connected and `t` after A's connection closes. Then read `ADAPTATION.md`
section 4 and list which of your statements would still work behind a
transaction-mode pooler.

## Task 9 — Transfer

Without running anything, derive the outcomes, the final items and the claim
order for `fixtures/transfer_stream.json`, then run the suite. Expected: see
`expected/transfer.json`.

## Task 10 — Adaptation note

Using `ADAPTATION.md`, write a half-page note for moving this design to a
Lakebase branch: the role type per access path, what the pooler and scale to
zero change, the restore window you would ask for, which reference tables would
be synced tables and the freshness each screen can promise. Mark every statement
as local evidence, documentation or unknown.
