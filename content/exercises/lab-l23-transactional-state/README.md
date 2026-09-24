# Lab L23 — Transactional state for a quality-review app

**Execution class P (platform-guide).** The SQL in this package was executed on a
**local PostgreSQL 16** server (tested: PostgreSQL 16.13, Ubuntu build) that the
test runner starts in a temporary directory and deletes afterwards. **Managed
Lakebase was not executed**: no Lakebase project, branch, token, pooler, synced
table or Databricks workspace was used. `ADAPTATION.md` is the platform guide for
moving the design to Lakebase, and every Lakebase statement in it is documentation,
not a result. SQLite is never used as a stand-in for PostgreSQL.

## Purpose and outcome

Cinderline Components (fictional) replaces a shared spreadsheet of flagged parts
with a small review app. Reviewers claim an item, inspect the part, and record a
decision; the lakehouse quality pipeline sends review requests at least once. You
design the operational state in PostgreSQL and prove, on a real server with two
real sessions, that:

- constraints refuse impossible rows, each with its own SQLSTATE, and a failed
  multi-row insert stores nothing;
- two workers claiming at the same moment receive different items
  (`FOR UPDATE SKIP LOCKED`), and you can see what plain `FOR UPDATE` and `NOWAIT`
  do instead;
- a decision made on a stale form is detected by a version column, not silently
  overwritten;
- redelivered and out-of-order intake messages change nothing (an idempotent
  upsert), while a last-write-wins upsert visibly regresses;
- Read Committed and Repeatable Read behave as documented on a two-session
  timeline, including the `40001` serialization failure;
- a least-privilege application role and a wrong password are refused, and
  session state (temp tables, `search_path`, advisory locks) belongs to one
  connection, which is what a transaction-mode pooler or scale to zero takes away.

## Prerequisites

- PostgreSQL 16 server binaries and client: `postgres`, `initdb`, `pg_ctl`, `psql`.
  On Debian or Ubuntu they live in `/usr/lib/postgresql/16/bin`; elsewhere pass
  `--pg-bin <dir>` or set `PG_BIN`. The runner refuses any other major version.
- Python 3.12, standard library only (see `requirements.txt`).
- Tested on Linux, both as root and as an ordinary user. If you run as root, an
  OS user named `postgres` must exist (initdb refuses to run as root) and
  `runuser` is used to start the server as that user. As an ordinary user nothing
  extra is needed; other Unix systems should work that way but were not tested.

## Run

```
python3.12 run_tests.py --evidence evidence.json   # judge solutions/*.sql
python3.12 run_tests.py --starter                  # judge your starters/*.sql
```

What happens: a temporary directory `lab-l23-pg-*` is created under the system
temp directory; `initdb` creates a cluster there (UTF8, C locale, SCRAM password
authentication, a random administrator password that is never written into the
package); `pg_ctl` starts the server on a free port on 127.0.0.1 with Unix sockets
disabled; `solutions/schema.sql` and `solutions/grants.sql` build a template
database; each test works in its own database cloned from that template, through
one or more long-lived `psql` processes; finally the server is stopped and the
directory deleted. A full run took under ten seconds on one machine here.

## Cleanup

Automatic, including when a test fails. If the process is killed (for example
with `kill -9`), look for a leftover `lab-l23-pg-*` directory in your temp
directory, stop its server with `pg_ctl -D <that directory>/data -m fast stop`
(as the user that owns it) and delete the directory.

## Files

| Path | What it is |
|---|---|
| `solutions/schema.sql` | reference schema: tables, constraints, the ready-queue index, the one-open-claim index |
| `solutions/grants.sql` | least-privilege grants for the application role `qr_app` |
| `solutions/claim.sql`, `decide.sql`, `intake.sql` | the three application writes, parameterised with psql variables |
| `starters/*.sql` | the same files with numbered GAPs for you to close |
| `fixtures/*.json` | synthetic reference data, the intake stream, the transfer stream, the bad writes |
| `expected/*.json` | hand-derived expected results (derivations in `DATA.md`) |
| `pglocal.py` | throwaway server lifecycle and `psql` sessions (standard library) |
| `run_tests.py` | eighteen unittest checks and the evidence writer |
| `TASKS.md`, `SOLUTIONS.md`, `DATA.md` | tasks, explained solution, data dictionary |
| `ADAPTATION.md` | the Lakebase adaptation guide and compatibility checklist |

## Limits

- Local PostgreSQL 16 proves PostgreSQL semantics only. Lakebase authentication
  (OAuth roles, one-hour tokens), its PgBouncer pooler, scale to zero, branches,
  point-in-time restore, synced tables and Lakebase CDF are described from
  documentation in `ADAPTATION.md` and are listed as not executed in the evidence.
- PgBouncer is not run. The session-state test uses two direct connections to show
  the mechanism a transaction-mode pooler exposes.
- The server uses SCRAM passwords over loopback without TLS; it is a throwaway
  test server, not a deployment pattern.
- Durations in the evidence describe this run only and are not benchmarks.
- `psql` variables (`:'name'`) stand in for driver bind parameters; the harness
  refuses variable values outside a small safe character set (letters, digits,
  space and `_ : . + -`).
