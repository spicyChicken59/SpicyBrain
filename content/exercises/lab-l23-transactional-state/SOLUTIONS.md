# Lab L23 solutions

Every output quoted here is what the reference files produced on local
PostgreSQL 16.13 in the recorded run (`docs/academy/labs/lab-l23-transactional-state.json`);
every expected value was first derived by hand in `DATA.md`.

## 1. Schema rules

`solutions/schema.sql` closes GAPs 1 to 5:

```sql
defect_code  text NOT NULL CHECK (defect_code IN ('CRACK', 'POROSITY', 'DIMENSION', 'SURFACE')),
severity     smallint NOT NULL CHECK (severity BETWEEN 1 AND 4),
...
CONSTRAINT review_item_state_consistent CHECK (
    (status = 'ready'   AND claimed_by IS NULL     AND decision IS NULL) OR
    (status = 'claimed' AND claimed_by IS NOT NULL AND decision IS NULL) OR
    (status = 'decided' AND claimed_by IS NOT NULL AND decision IS NOT NULL))

CREATE INDEX review_item_ready_queue
    ON qr.review_item (severity DESC, flagged_at, item_id) WHERE status = 'ready';
CREATE UNIQUE INDEX review_item_one_open_claim
    ON qr.review_item (claimed_by) WHERE status = 'claimed';
```

PostgreSQL names an unnamed column CHECK `<table>_<column>_check`, a foreign key
`<table>_<column>_fkey` and a primary key `<table>_pkey`, which is why the expected
names can be written down before running. Intermediate output of test 1:

| case | SQLSTATE | rule |
|---|---|---|
| severity out of range | 23514 | review_item_severity_check |
| missing part serial | 23502 | part_serial (not null) |
| unknown plant | 23503 | review_item_plant_id_fkey |
| duplicate item | 23505 | review_item_pkey |
| decided without a decision | 23514 | review_item_state_consistent |
| unknown defect code | 23514 | review_item_defect_code_check |
| malformed item id | 23514 | review_item_item_id_check |
| second open claim | 23505 | review_item_one_open_claim |
| unknown reviewer | 23503 | review_item_claimed_by_fkey |
| claimed without an owner | 23514 | review_item_state_consistent |

The atomic batch fails on its third row (severity 9, 23514) and the table still
holds 6 rows: one statement is one transaction, so its two valid rows vanish with
it.

## 2. Grants

`solutions/grants.sql` grants `USAGE` on the schema, `SELECT` on `plant` and
`reviewer`, `SELECT, INSERT, UPDATE` on `review_item` and `SELECT, INSERT` on
`intake_message`. `INSERT ... ON CONFLICT DO UPDATE` needs UPDATE on the target
table, and `RETURNING` needs SELECT, which is why both appear. Output of test 15:
DELETE, UPDATE and TRUNCATE are refused with `permission denied for table ...`,
DROP with `must be owner of table intake_message`, all SQLSTATE 42501.

## 3. Idempotent intake

```sql
WITH logged AS (
    INSERT INTO qr.intake_message (message_id, item_id, source_seq)
    VALUES (:'message_id', :'item_id', :source_seq)
    ON CONFLICT (message_id) DO NOTHING
    RETURNING message_id
)
INSERT INTO qr.review_item AS r
       (item_id, plant_id, part_serial, defect_code, severity, flagged_at, source_seq)
SELECT :'item_id', :'plant_id', :'part_serial', :'defect_code',
       CAST(:severity AS smallint), CAST(:'flagged_at' AS timestamptz), :source_seq
  FROM logged
ON CONFLICT (item_id) DO UPDATE
   SET defect_code = EXCLUDED.defect_code, severity = EXCLUDED.severity,
       source_seq = EXCLUDED.source_seq, version = r.version + 1
 WHERE r.source_seq < EXCLUDED.source_seq AND r.status = 'ready'
RETURNING r.item_id, r.version;
```

Why each delivery ends as it does:

| # | message | outcome | reason |
|---|---|---|---|
| 1 | M-0001 → QR-0001 seq 1 | applied, v1 | new message, new item |
| 2 | M-0002 → QR-0002 seq 1 | applied, v1 | new message, new item |
| 3 | M-0003 → QR-0003 seq 1 | applied, v1 | new message, new item |
| 4 | M-0002 again | skipped | `logged` is empty, so nothing reaches the item |
| 5 | M-0004 → QR-0004 seq 1 | applied, v1 | new message, new item |
| 6 | M-0006 → QR-0006 seq 2 | applied, v1 | the newer message arrives first and inserts |
| 7 | M-0005 → QR-0006 seq 1 | skipped | logged, but 2 < 1 is false, so DO UPDATE does nothing |
| 8 | M-0007 → QR-0005 seq 1 | applied, v1 | new message, new item |
| 9 | M-0008 → QR-0001 seq 2 | applied, v2 | newer and still ready: CRACK, severity 4 |
| 10 | M-0001 again | skipped | repeated message |

Replaying the ten deliveries returns ten skips and leaves the 8 logged messages and
six items unchanged.

**Wrong approach 1: last write wins.** An upsert without the message log and
without the sequence guard (`NAIVE_INTAKE` in `run_tests.py`, the same shape as
`starters/intake.sql`) applies every delivery. Delivery 7 turns QR-0006 back into
CRACK severity 3 at seq 1, delivery 10 turns QR-0001 back into POROSITY severity 3
at seq 1, and the redelivery of M-0002 bumps QR-0002 to version 2 although nothing
changed. Test 5 asserts exactly those three rows. It fails because "the latest
delivery" is not "the latest fact" under at-least-once delivery.

## 4. The claim

```sql
UPDATE qr.review_item AS r
   SET status = 'claimed', claimed_by = :'reviewer_id', claimed_at = now(), version = r.version + 1
 WHERE r.item_id = (SELECT q.item_id FROM qr.review_item AS q
                     WHERE q.status = 'ready'
                     ORDER BY q.severity DESC, q.flagged_at, q.item_id
                     LIMIT 1 FOR UPDATE SKIP LOCKED)
   AND r.status = 'ready'
RETURNING r.item_id, r.claimed_by, r.version;
```

Test 6 claims and decides with one reviewer: QR-0001 (claimed v3, decided v4),
then QR-0002, QR-0005, QR-0003, QR-0006, QR-0004 (each claimed v2, decided v3),
then no row. QR-0001 starts at version 2 because delivery 9 updated it.

## 5. Two sessions

- Test 7: A runs `BEGIN;` and the claim, returning `QR-0001|R-101|3`, and stays
  open. B's claim returns `QR-0002|R-102|2` at once; at that moment
  `pg_stat_activity` shows A as `idle in transaction`. After A commits, 4 items
  are ready.
- Test 8: with A still open, B's `SELECT ... FOR UPDATE NOWAIT` on QR-0001 fails
  with 55P03, `could not obtain lock on row in relation "review_item"`. A rolls
  back and QR-0001 is ready again at version 2.
- Test 9: the same claim with plain `FOR UPDATE`: B's `wait_event_type` is `Lock`
  until A commits; then B re-checks QR-0001, finds it claimed, and returns
  `QR-0002|R-102|2`. Correct, but the workers are serialized.

**Wrong approach 2: read, then update, without a lock.** A and B each run
`BEGIN; SELECT item_id ... LIMIT 1;` and both see QR-0001. A updates it for R-101
and commits; B's update (no status condition) then succeeds too, for R-102. Both
workers believe they own QR-0001; the row ends claimed by R-102 at version 4 and
A's claim is lost without an error. Test 10 asserts exactly that.

## 6. The decision

```sql
UPDATE qr.review_item
   SET status = 'decided', decision = :'decision', decided_at = now(), version = version + 1
 WHERE item_id = :'item_id' AND claimed_by = :'reviewer_id'
   AND status = 'claimed' AND version = :expected_version
RETURNING item_id, status, decision, version;
```

Test 11 output: claim `QR-0001|R-101|3`; supervisor reassignment returns version
4; R-101's submit with version 3 returns no row; R-101's submit with version 4
returns no row (R-103 owns the item); R-103's submit returns
`QR-0001|decided|rework|5`.

**Wrong approach 3: no version.** Test 12: two supervisors update QR-0003's
severity to 3 and then 1 without a version condition; both report one row and
the final severity is 1, so the first edit vanished. With `AND version = 1` on
QR-0004, the first update returns version 2 and the second returns no row.

## 7. Isolation timeline (test 13)

| Step | Read Committed | Repeatable Read |
|---|---|---|
| A reads ready count | 6 | 5 |
| B claims and commits | QR-0001 | QR-0002 |
| A reads ready count again | 5 | 5 |
| A updates the row B claimed | (not run) | 40001, could not serialize access due to concurrent update |

Then, under Read Committed, A reads QR-0005's severity (4), B (R-104) claims
QR-0005, and A's `UPDATE ... SET severity = 3` succeeds with SQLSTATE 00000: the
row is now claimed by R-104 with severity 3 and still version 2. That silent
success is the dangerous result; Repeatable Read's refusal is the safe one.

## 8. Session state (test 16)

A creates `draft_note`, sets `search_path = qr, public` and takes
`pg_try_advisory_lock(2301)` (`t`). B cannot see `draft_note` (42P01), cannot use
the unqualified `review_item` (42P01), and gets `f` for the same advisory lock.
After A's connection closes, B gets `t`. A transaction-mode pooler or a closed
idle connection separates your next transaction from all three in the same way.

## 9. Transfer (test 17)

Outcomes: applied, applied, applied, `claimed:QR-0102`, skipped (the item is
claimed), applied (QR-0101 to seq 3, v2), skipped (seq 2 < 3), skipped (repeated
M-0105), applied. Seven logged messages. The remaining ready items all have
severity 3, so the follow-up claims order by `flagged_at` and then `item_id`:
QR-0104 (06:55), QR-0101, QR-0103.
