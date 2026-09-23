# Lab L23 data

All data is synthetic and was written by hand for fictional Cinderline Components.
No real plant, person, part, message or system is represented. There is no random
generator and no seed: every fixture is a static JSON file, and every expected
value below was derived by hand from these fixtures and PostgreSQL's documented
rules before the SQL ran. No expected value was produced by the solution.

## Fixtures

### `fixtures/reference.json`

| Field | Type | Meaning |
|---|---|---|
| `plants[].plant_id` | text `P<digit>` | plant key: P1 North Works, P2 South Mill, P3 East Yard |
| `plants[].plant_name` | text | display name |
| `reviewers[].reviewer_id` | text `R-<3 digits>` | R-101, R-102, R-103, R-104 |
| `reviewers[].display_name` | text | fictional initials and surname |
| `reviewers[].plant_id` | text | home plant |
| `reviewers[].active` | boolean | all true |

### `fixtures/intake_stream.json` — ten deliveries in arrival order

| Field | Type | Meaning |
|---|---|---|
| `message_id` | text | the producer's idempotency key |
| `item_id` | text `QR-<4 digits>` | the review item the message is about |
| `source_seq` | integer ≥ 1 | the producer's per-item sequence; higher is newer |
| `plant_id`, `part_serial` | text | the flagged part |
| `defect_code` | text | CRACK, POROSITY, DIMENSION or SURFACE |
| `severity` | integer 1–4 | 4 is most urgent |
| `flagged_at` | ISO-8601 UTC | when the pipeline flagged the part; the queue's tie-breaker |

| # | message | item | seq | defect | sev | flagged_at (2026-09-14, UTC) |
|---|---|---|---|---|---|---|
| 1 | M-0001 | QR-0001 | 1 | POROSITY | 3 | 06:10 |
| 2 | M-0002 | QR-0002 | 1 | CRACK | 4 | 06:20 |
| 3 | M-0003 | QR-0003 | 1 | DIMENSION | 2 | 06:05 |
| 4 | M-0002 | QR-0002 | 1 | CRACK | 4 | 06:20 (redelivery) |
| 5 | M-0004 | QR-0004 | 1 | SURFACE | 1 | 06:30 |
| 6 | M-0006 | QR-0006 | 2 | POROSITY | 2 | 06:15 |
| 7 | M-0005 | QR-0006 | 1 | CRACK | 3 | 06:15 (older, late) |
| 8 | M-0007 | QR-0005 | 1 | CRACK | 4 | 06:25 |
| 9 | M-0008 | QR-0001 | 2 | CRACK | 4 | 06:10 (reclassified) |
| 10 | M-0001 | QR-0001 | 1 | POROSITY | 3 | 06:10 (redelivery) |

### `fixtures/transfer_stream.json` — altered input

Nine steps on 2026-09-15: three new items, a claim by R-102 in the middle, a newer
message for the item R-102 now holds, an update, an older message, a redelivery,
and a fourth item flagged five minutes earlier than the others. Every remaining
item ends at severity 3, so ordering falls to `flagged_at` and `item_id`.
`follow_up_claims` lists three reviewers who each claim once afterwards.

### `fixtures/constraint_cases.json`

Ten statements, each breaking exactly one rule, plus a three-row INSERT whose third
row has severity 9. They run as `qr_app` after the primary stream and after R-101
has claimed QR-0001.

## Derivations of `expected/`

**`server.json`.** Major version 16 is the requirement; `read committed` is
PostgreSQL's documented default isolation; `127.0.0.1` is what the runner passes
as `listen_addresses`; `scram-sha-256` is PostgreSQL 16's default
`password_encryption`.

**`constraints.json`.** Names follow PostgreSQL's naming of unnamed constraints:
column CHECK `review_item_<column>_check`, foreign key `review_item_<column>_fkey`,
primary key `review_item_pkey`; named ones keep their names
(`review_item_state_consistent`, `review_item_one_open_claim`). SQLSTATEs:
23514 check, 23502 not null (the message names the column, `part_serial`), 23503
foreign key, 23505 unique. Case 8 is a unique violation because R-101 already
holds QR-0001. Rows stay at 6. The batch fails at row 3 (23514) and, being one
statement, stores neither valid row: rows before 6, after 6, visible 0.

**`intake.json`.** Walk the stream with two rules: a message_id seen before is
skipped; an item changes only if the incoming seq is greater than the stored seq
and the item is ready. Deliveries 1, 2, 3, 5 insert new items at version 1.
Delivery 4 repeats M-0002: skipped. Delivery 6 inserts QR-0006 with seq 2.
Delivery 7 is a new message (logged) but seq 1 < 2: skipped. Delivery 8 inserts
QR-0005. Delivery 9: seq 2 > 1 and QR-0001 is ready, so it becomes CRACK 4, seq
2, version 2. Delivery 10 repeats M-0001: skipped. Distinct message IDs: M-0001
to M-0008, so 8 logged messages. A replay repeats every message ID: ten skips.

**`naive.json`.** Apply every delivery with last write wins and `version + 1` on
every conflict: QR-0002 conflicts once (delivery 4) → version 2; QR-0006 is
inserted by delivery 6 and overwritten by delivery 7 → CRACK 3 seq 1 version 2;
QR-0001 is inserted by 1, overwritten by 9 (version 2) and by 10 → POROSITY 3 seq 1
version 3.

**`queue.json`.** Order ready items by severity descending, then `flagged_at`,
then `item_id`: severity 4 are QR-0001 (06:10), QR-0002 (06:20), QR-0005 (06:25);
severity 2 are QR-0003 (06:05), QR-0006 (06:15); severity 1 is QR-0004. A claim adds
1 to the version and a decision adds 1 more: QR-0001 goes 2 → 3 → 4, the others
1 → 2 → 3. With nothing ready, the claim returns no row.

**`concurrency.json`.** Skip locked: A takes the first item, QR-0001, at 2 + 1 = 3;
B skips it and takes QR-0002 at 1 + 1 = 2; A is `idle in transaction` while it
waits for its COMMIT; after both, 6 − 2 = 4 ready. NOWAIT: 55P03 with PostgreSQL's
message for an unlockable row; after ROLLBACK QR-0001 is ready at version 2 again.
Blocking: B waits on A's row lock, so its `wait_event_type` is `Lock`; after A
commits, QR-0001 is no longer ready and B takes QR-0002 at version 2. Unlocked:
both read QR-0001; A's update makes version 3, B's update makes version 4 and
owner R-102.

**`optimistic.json`.** The claim takes QR-0001 from 2 to 3; the supervisor's
`WHERE version = 3` update makes 4 and sets R-103; R-101's submit with 3 matches no
row; R-101's submit with 4 fails the owner condition; R-103's submit with 4 makes
version 5, decided, rework. Last write wins on QR-0003 (severity 2, version 1):
3 then 1, both one row, final 1, version untouched at 1. Guarded on QR-0004
(version 1): first update → version 2 with severity 3; second, still asking for
version 1, matches no row.

**`isolation.json`.** Read Committed: 6 ready, B claims the first (QR-0001), then
5. Repeatable Read (after that claim): 5, B claims the next (QR-0002), still 5 from
the snapshot, and an update of QR-0002 changed after the snapshot fails with 40001.
Read Committed update: QR-0005 severity 4; R-104 claims the next ready item,
QR-0005 (version 2); A's update succeeds (00000) and leaves severity 3, owner
R-104, version 2.

**`security.json`.** A wrong password fails authentication, so `psql` exits with
status 2 and prints PostgreSQL's message for failed password authentication; the
right password logs in as `qr_app`. The four refused statements follow from the
grants in `solutions/grants.sql`; nothing is deleted, so 6 items and 8 messages
remain.

**`session.json`.** Temporary tables and `search_path` are per session, so B sees
neither (42P01, undefined table); a session advisory lock is held by A's session,
so B's try returns `f` until A's connection ends and `t` afterwards.

**`transfer.json`.** Steps 1 to 3 insert QR-0101 (severity 2), QR-0102 and
QR-0103 (severity 3, both 07:00). Step 4: R-102 claims the most urgent, which is the
severity-3 tie broken by item_id, QR-0102 (version 2). Step 5: QR-0102 is claimed,
so the newer message is logged but skipped. Step 6: QR-0101 seq 3 > 1 and ready →
severity 3, seq 3, version 2. Step 7: seq 2 < 3, skipped. Step 8: repeated M-0105,
skipped. Step 9 inserts QR-0104 at 06:55. Messages M-0101 to M-0107: 7. Follow-up
claims: all severity 3, so QR-0104 (06:55) first, then the 07:00 tie by item_id:
QR-0101, QR-0103.
