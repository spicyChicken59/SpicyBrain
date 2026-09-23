*Execution class P (platform-guide): the SQL ran on a local PostgreSQL 16.13
server that the test runner started in a temporary directory on one machine,
listening on 127.0.0.1 only, and deleted afterwards; two `psql` processes were
two real database sessions. Managed Lakebase was not executed: no Lakebase
project, branch, OAuth token, pooler, synced table or Databricks workspace was
used, and SQLite was not used as a stand-in. This page is studyable without
installing anything; the package `lab-l23-transactional-state` holds the files
if you want to run it.*

### Purpose

The Lakebase module argues that an application's operational state belongs in a
transactional database, guarded by constraints, changed by short transactions and
protected by the right concurrency pattern. This lab makes each of those claims
observable. Cinderline's quality-review app keeps flagged parts in
`qr.review_item`; reviewers claim an item, inspect the part and record a decision;
the lakehouse quality pipeline sends review requests at least once. Eighteen tests
check the reference SQL against results that were derived by hand before it ran,
three of them demonstrating a wrong approach failing for the stated reason. A
Lakebase adaptation guide, `ADAPTATION.md`, carries the design to the platform as
documentation, clearly separated from what ran.

### The fixture

Ten deliveries arrive in this order (all synthetic, 14 September 2026, UTC):

| # | message | item | seq | defect, severity | note |
|---|---|---|---|---|---|
| 1 | M-0001 | QR-0001 | 1 | POROSITY 3 | |
| 2 | M-0002 | QR-0002 | 1 | CRACK 4 | |
| 3 | M-0003 | QR-0003 | 1 | DIMENSION 2 | |
| 4 | M-0002 | QR-0002 | 1 | CRACK 4 | redelivery |
| 5 | M-0004 | QR-0004 | 1 | SURFACE 1 | |
| 6 | M-0006 | QR-0006 | 2 | POROSITY 2 | newer message first |
| 7 | M-0005 | QR-0006 | 1 | CRACK 3 | older message, late |
| 8 | M-0007 | QR-0005 | 1 | CRACK 4 | |
| 9 | M-0008 | QR-0001 | 2 | CRACK 4 | reclassified |
| 10 | M-0001 | QR-0001 | 1 | POROSITY 3 | redelivery |

Four reviewers (R-101 to R-104) and three plants (P1 to P3) are reference data.

### Task 1: constraints

The schema writes the state machine as a table CHECK: ready has no owner and no
decision, claimed has an owner and no decision, decided has both. A partial
unique index allows one open claim per reviewer. Ten bad writes are each refused
with their own SQLSTATE: severity 7 gives 23514 on `review_item_severity_check`;
a missing part serial gives 23502; plant P9 gives 23503; a duplicate QR-0001 gives
23505 on the primary key; a decided row without a decision gives 23514 on
`review_item_state_consistent`; a second open claim for R-101 gives 23505 on
`review_item_one_open_claim`. A three-row INSERT whose third row has severity 9
stores none of the three rows.

### Task 2: idempotent intake

The intake statement logs each `message_id` with `ON CONFLICT DO NOTHING` and
lets an item change only for a newer `source_seq` while it is ready. Intermediate
output, one word per delivery: applied, applied, applied, skipped, applied,
applied, skipped, applied, applied, skipped. Eight messages are logged. QR-0001
ends as CRACK severity 4 at seq 2, version 2; QR-0006 stays POROSITY severity 2 at
seq 2. Replaying all ten deliveries returns ten skips and changes nothing.

**The failure case.** A last-write-wins upsert applies every delivery. Delivery 7
turns QR-0006 back into CRACK severity 3 at seq 1, and delivery 10 turns QR-0001
back into POROSITY severity 3 at seq 1: stale messages overwrote newer facts.

### Task 3: the work queue with two sessions

The claim is one UPDATE whose subquery picks the most urgent ready row with
`FOR UPDATE SKIP LOCKED`. One reviewer claiming and deciding in turn gets
QR-0001, QR-0002, QR-0005, QR-0003, QR-0006, QR-0004, then no row.

With session A holding its claim on QR-0001 in an open transaction:

| Session B runs | B receives |
|---|---|
| the claim with SKIP LOCKED | QR-0002 at once, while A is still `idle in transaction` |
| the claim with plain FOR UPDATE | nothing until A commits (`wait_event_type` = `Lock`), then QR-0002 |
| `SELECT ... FOR UPDATE NOWAIT` on QR-0001 | SQLSTATE 55P03, could not obtain lock on row |

**The failure case.** Read, then update, with no lock and no status condition:
both sessions read QR-0001, both updates succeed, and the row ends claimed by
R-102 at version 4. Session A believes it owns an item it lost, and no error was
raised.

### Task 4: the version check

R-101 claims QR-0001 at version 3. A supervisor reassigns it to R-103 with
`WHERE version = 3`, making version 4. R-101's decision with version 3 updates no
row, and so does R-101's decision with version 4 because R-103 now holds the
item; R-103's decision returns `QR-0001 | decided | rework | 5`. Without a version,
two supervisors editing QR-0003 both report one row updated and the first edit
disappears.

### Task 5: isolation on a timeline

| Step | Read Committed | Repeatable Read |
|---|---|---|
| A counts ready items | 6 | 5 |
| B claims and commits | QR-0001 | QR-0002 |
| A counts again | 5 | 5 |
| A updates the row B claimed | | 40001, could not serialize access |

A third sequence shows the dangerous case: under Read Committed, A's update of
QR-0005's severity succeeds after R-104 has claimed it, silently changing work in
progress.

### Task 6: identity and session state

The application role `qr_app` can do its job but DELETE, UPDATE of the intake log,
TRUNCATE and DROP each fail with 42501; a wrong password fails at login (psql exit
status 2). A temp table, a `search_path` and an advisory lock taken by session A
are invisible or unavailable to session B (42P01, 42P01, `f`), and the lock frees
only when A's connection closes. That is what a transaction-mode pooler or a
closed idle connection takes away, which is why every write here is one
transaction with schema-qualified names.

### Transfer

A second stream adds a claim in the middle, a newer message for the claimed item
(skipped), an out-of-order message, a redelivery and a three-way severity tie. The
hand-derived order of the follow-up claims, QR-0104, QR-0101, QR-0103, matched.

### What the tests prove and do not prove

They prove that this SQL behaves as described on PostgreSQL 16.13, with real
concurrent sessions and real error codes. They do not prove anything about
Lakebase: OAuth tokens, the managed PgBouncer pooler, scale to zero, branches,
point-in-time restore, synced tables, Lakehouse Sync, performance or failover were
not executed and are listed as such in the evidence file. The run time (under ten seconds here)
describes one run, not a benchmark.

### Setup and cleanup

Needs PostgreSQL 16 server binaries (`postgres`, `initdb`, `pg_ctl`, `psql`) and
Python 3.12 with the standard library. Run `python3.12 run_tests.py --evidence
evidence.json`; run `python3.12 run_tests.py --starter` to judge your own SQL.
When run as root, the cluster is owned by the `postgres` OS user because initdb
refuses root. The runner deletes its `lab-l23-pg-*` temporary directory after the
run, even when a test fails; if the process is killed, stop the leftover server
with `pg_ctl -D <directory>/data -m fast stop` and delete the directory.
