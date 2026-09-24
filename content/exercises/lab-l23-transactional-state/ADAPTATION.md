# Lakebase adaptation guide for lab L23

**Status of this guide.** Nothing here was executed on Lakebase. The statements
about Lakebase come from Databricks documentation for Databricks on AWS (Lakebase
Autoscaling). Restore and managed pooling page bodies were inspected on
2026-09-23; the historical-branching page was inspected on 2026-09-24. Other
source records retain their earlier search-level limitations. This guide was
corrected for course 4.0.1; record any platform execution separately from this
lab's historical local PostgreSQL 16 evidence.

Sources: *Lakebase Postgres* (docs.databricks.com/aws/en/oltp/), *Core concepts*,
*About authentication*, *Manage roles*, *Use connection pooling*, *Scale to
zero*, *Branches*, *Point-in-time restore*, *Serve lakehouse data with synced
tables*, *Lakehouse Sync*, *Postgres compatibility*, *Lakebase Autoscaling
limitations*, *Add a Lakebase resource to a Databricks app* and the *Lakebase
release notes*, all under docs.databricks.com/aws/en/.

## 1. What carries over unchanged

Lakebase is managed Postgres; the compatibility page lists Postgres 16 and 17
for Autoscaling on AWS. The mechanisms this lab tests are PostgreSQL semantics:
constraints and their SQLSTATEs, transactions, Read Committed and Repeatable
Read, row locks with `SKIP LOCKED` and `NOWAIT`, and `INSERT ... ON CONFLICT`.
Expect them to behave the same, and prove it by running the lab's SQL on a
branch (section 8), because a managed service can add limits of its own.

## 2. Objects and connection

A Lakebase **project** holds **branches**; each branch has a **compute** and its
own **databases** (default `databricks_postgres`) and **roles**. Connect to the
compute of the branch you want, using the connection details the project shows.
Do not copy this lab's `PGSSLMODE=disable`; use the connection settings the
project gives you.

## 3. Authentication

- **OAuth roles** are linked to a Databricks user, service principal or group and
  log in with an OAuth token. Tokens expire after one hour; expiry is checked
  only at login, so an open connection keeps working and a new one needs a fresh
  token. Fetch a token before opening connections.
- **Native Postgres password roles** log in with a password. Keep it in a secret
  store and rotate it.
- Roles are created in the Lakebase UI, with SQL through the `databricks_auth`
  extension (created in each database), or with the SDK and REST API.
- **Databricks Apps**: adding Lakebase as an app resource creates a service
  principal, a matching Postgres role and CONNECT and CREATE on the chosen
  database, and passes connection details as environment variables. Grants on
  tables the app did not create are still yours: adapt `grants.sql`, replacing
  `qr_app` with the role you use.
- There is no Postgres superuser (`databricks_superuser` takes its place). Run
  `schema.sql` as a normal owner role, not as a superuser.

## 4. Pooling

Lakebase documents a built-in PgBouncer pooler in **transaction mode**: a server
connection is lent for one transaction. Consequences for this design:

| Lab behaviour | Behind the pooler |
|---|---|
| claim, decision and intake are one transaction each | works unchanged |
| schema-qualified names (`qr.review_item`) | works unchanged |
| `SET search_path` or a temp table kept in the session | does not follow you to the next transaction |
| session advisory locks | belong to one server connection; do not use across requests |
| SQL-level `PREPARE` / `DEALLOCATE`, `LISTEN` and `NOTIFY` | documented as unsupported by the managed pooler; driver-level prepared statements are distinct; use a direct connection for pub/sub |

The pooling page states that pooling needs **native password authentication**
and is not available for OAuth roles. Choosing pooled access therefore chooses a
password role. Test 16 in this lab shows the underlying mechanism with two
direct connections; PgBouncer itself was not run.

## 5. Scale to zero

An idle compute can scale to zero. Committed rows stay; idle connections close
and their session context (temporary tables, prepared statements, advisory locks,
LISTEN and NOTIFY) is lost. The design keeps all state in committed rows, so it
survives; the application must reconnect. Measure the first-connection delay on
your own project; it is not documented here. Scale to zero can be disabled, in
which case the compute runs continuously.

## 6. Branches and recovery

- **Rehearse changes on a child branch.** A branch is a copy-on-write copy of its
  parent. Apply a migration there first, run the lab's SQL against it, then
  apply to production.
- **Restore window.** Point-in-time restore and point-in-time branching work
  within the project's restore window, documented as configurable from 2 to 30
  days with a default of 7. Set it deliberately.
- **Separate recovered state from cutover.** A historical branch lets you inspect
  missing rows. Restore creates a new root branch; the original and its existing
  connections remain unchanged. Validate and reconcile before a selective repair
  or an explicit application connection change. Newer writes still exist on the
  original; blindly switching to an older state would hide them from users.

Primary sections inspected: **Transaction mode** in
<https://docs.databricks.com/aws/en/oltp/projects/connection-pooling>;
**What happens after a restore?** and **Connections remain unchanged** in
<https://docs.databricks.com/aws/en/oltp/projects/point-in-time-restore>;
**Important considerations** in
<https://docs.databricks.com/aws/en/oltp/projects/point-in-time-branching>.

## 7. Synchronization with the lakehouse

- **Synced tables** (Unity Catalog to Lakebase) suit `plant` and `reviewer` if
  those are maintained in the lakehouse. Modes: snapshot (full copy per run),
  triggered (incremental, when run) and continuous (streamed, minimum interval
  about 15 seconds). Triggered and continuous need Change Data Feed on the
  source; a primary key is required; treat the copy as read-only. The
  foreign keys in `schema.sql` point at `qr.plant` and `qr.reviewer`: decide
  whether they reference the synced copies or local tables, and say what the app
  does when the copy lags.
- **Lakehouse Sync** (Lakebase to Unity Catalog, listed as Public Preview) writes
  row changes of Lakebase tables into Unity Catalog Delta tables as history, for
  dashboards and pipelines. A Databricks developer template refers to the feature
  as Lakebase Change Data Feed and lists requirements such as replica identity;
  confirm the current requirements on the documentation page.
- **State freshness on every screen.** A synced copy is never part of the app's
  transaction. Print its as-of time.

## 8. Running the lab's SQL on a branch (manual; not executed here)

1. Create a child branch of the project's production branch and connect to it as
   a non-superuser owner role.
2. `psql -f solutions/schema.sql` (after removing anything the compatibility page
   rules out; this schema uses no tablespace, extension or replication).
3. Create the application role your access path needs (OAuth or password), then
   run `grants.sql` with that role's name.
4. Load `fixtures/reference.json` and replay `fixtures/intake_stream.json` through
   `solutions/intake.sql` (psql `\set` each variable first, as `run_tests.py` does).
5. Repeat the two-session sequences from `SOLUTIONS.md` in two psql sessions and
   compare every result with `expected/*.json`.
6. Record the branch, region, date, Postgres version (`SHOW server_version;`) and
   access path next to the results. That record is Lakebase evidence; this lab's
   evidence file is not.

## 9. Compatibility checklist

| Area | This lab (local PostgreSQL 16.13) | Lakebase, as documented | Action before moving |
|---|---|---|---|
| Version | 16.13 | Postgres 16 or 17 on AWS | `SHOW server_version;` on the branch |
| Superuser | `lab_admin` is superuser | none; `databricks_superuser` | run DDL as an owner role |
| Authentication | SCRAM password over loopback | OAuth roles (one-hour tokens) or password roles | choose per access path |
| Pooling | none | PgBouncer, transaction mode, password roles | one transaction per unit of work |
| Idle connections | kept open | closed by scale to zero | reconnect; keep no session state |
| Tablespaces, logical replication | available | not supported | keep them out of scripts |
| Recovery | none | restore window 2 to 30 days (default 7) | set it; rehearse on a branch |
| Sync | none | synced tables; Lakehouse Sync (Public Preview) | state freshness per copy |
| Evidence | lab evidence JSON | your own branch run | never relabel one as the other |

Still unknown until measured on a project: regional availability, pricing,
performance at your load, failover time and the reconnect delay after scale to
zero.
