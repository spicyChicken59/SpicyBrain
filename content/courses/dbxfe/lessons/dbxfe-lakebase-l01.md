<!-- section:dbxfe-lakebase-l01-outcome -->

After this lesson you can say why an application's operational state belongs in a transactional database rather than in the tables your pipelines scan, and design that state for Cinderline's quality-review app: a schema whose constraints refuse impossible rows, a work queue two reviewers can claim from at once, a decision that detects a stale form, and an intake that survives redelivery. You can place Lakebase, Databricks' managed Postgres, in that design: how the app connects and authenticates, what a pooler and scale to zero take away, how branches and point-in-time restore support change and recovery, and what freshness a synced copy can honestly promise. The SQL ran on local PostgreSQL 16 in lab L23; nothing here ran on Lakebase.

<!-- section:dbxfe-lakebase-l01-start -->

Bring SQL fluency (keys, `UPDATE ... WHERE`, joins) and the platform map from [Platform, workspace and compute](#/module/dbxfe-m03). [Delta Lake: files, log and snapshots](#/module/dbxfe-delta) gives table-level commits for analytical tables; this lesson is about row-level transactions with many concurrent writers. The module *Databricks Apps and application architecture* covers the browser-to-back-end path; here you design what that app stores. OLTP (online transaction processing) means many short reads and writes of a few rows by key; OLAP (online analytical processing) means scans and aggregates over many rows.

<!-- section:dbxfe-lakebase-l01-workloads -->

A reviewer clicking *Claim* is a transactional request: it changes one row, must answer in milliseconds and competes with other reviewers doing the same. The morning defect dashboard is analytical: it scans a day of inspections and tolerates data minutes old. On one engine each hurts the other: dashboard scans compete with claims, or every click waits on a warehouse that has no row locks to offer.

Lakebase is Databricks' fully managed Postgres for the transactional side. In the current Autoscaling version a **project** holds **branches** (isolated database environments sharing storage with their parent), a **compute** per branch that autoscales and can scale to zero when idle, and the **databases** and **roles** on each branch (default database `databricks_postgres`). The documentation lists Postgres 16 and 17 on AWS and describes Lakebase as generally available, with some features, such as Lakehouse Sync, marked Public Preview; check the release notes before promising one.

<!-- section:dbxfe-lakebase-l01-model -->

Model operational state as relational rows and write the rules as constraints, so no handler can store an impossible row. The app has `plant`, `reviewer`, `review_item` and `intake_message`. A review item's status is a small state machine (`ready`, `claimed`, `decided`) and one table constraint ties it to the columns: ready has no owner, claimed has an owner and no decision, decided has both. A partial unique index on `claimed_by WHERE status = 'claimed'` stops a reviewer holding two open items, and a `version` column counts changes.

The state lives in committed rows, not in server memory or an open transaction. A claim commits in milliseconds; the reviewer inspects the part for minutes with no transaction open; the decision is a second short transaction. App servers can restart or lose their connection in between and nothing is lost.

<!-- section:dbxfe-lakebase-l01-transactions -->

A transaction makes several statements one all-or-nothing change whose intermediate states other sessions never see. The isolation level decides which *committed* changes a statement sees. PostgreSQL's default, Read Committed, gives each statement a fresh snapshot, so two reads in one transaction can differ. Repeatable Read keeps the snapshot of the transaction's first statement; updating a row that another transaction changed and committed since then fails with SQLSTATE `40001`, and the code must retry the whole transaction. Serializable also prevents the anomalies Repeatable Read allows, with the same retry duty.

In lab L23, under Read Committed session A counted 6 ready items, B claimed one and committed, and A's second count was 5. Under Repeatable Read A counted 5 twice around B's commit, then its update of the row B had claimed failed with `40001`.

<!-- section:dbxfe-lakebase-l01-concurrency -->

**Claim with a lock that skips.** `FOR UPDATE SKIP LOCKED` in the claim's subquery locks the chosen row and passes over rows another session holds. In the lab, A held QR-0001 in an open transaction and B's claim returned QR-0002 at once; with plain `FOR UPDATE` B waited on a lock until A committed, and with `NOWAIT` it failed with `55P03`.

**Detect a stale write with a version.** The decision updates `WHERE ... AND version = <the version the form loaded>`. Zero rows means someone changed the row: reload and show what changed.

**Make redelivery harmless.** Intake logs each `message_id` with `ON CONFLICT DO NOTHING` and updates the item only for a newer `source_seq` while it is ready. Replaying all ten lab deliveries changed nothing; a last-write-wins upsert let a late, older message undo a newer one.

<!-- section:dbxfe-lakebase-l01-connections -->

Every Postgres connection is a server process, so connection count is a capacity limit. Lakebase documents a built-in PgBouncer pooler in transaction mode: a server connection is lent to a client for one transaction, then returned. Session state does not follow you: `SET search_path`, temporary tables, SQL-level `PREPARE` and `LISTEN` break, while driver-level prepared statements work. Keep each unit of work in one transaction and schema-qualify names. Scale to zero also closes idle connections, taking temp tables and advisory locks with them.

A connection authenticates as an OAuth role tied to a Databricks identity (user, service principal or group), with tokens that expire after one hour and are checked only at login, or as a native Postgres password role; the pooling page says pooling needs password authentication. Privileges remain Postgres `GRANT`s: give the app role only what it uses.

<!-- section:dbxfe-lakebase-l01-recovery -->

A **branch** is an isolated copy-on-write environment created from a parent; it shares unchanged storage. Run a schema migration on a child branch before production. **Point-in-time restore** returns a branch to a moment inside the project's restore window (documented as 2 to 30 days, 7 by default), and a **point-in-time branch** lets you query the past without touching production. Choose by the question: a restore rewinds legitimate later writes too; a past-state branch lets you copy back only what was lost.

<!-- section:dbxfe-lakebase-l01-sync -->

Synchronization copies data between the two sides; it never makes them one transaction. **Synced tables** copy a Unity Catalog table into Lakebase Postgres in snapshot, triggered or continuous mode. Triggered and continuous need Change Data Feed on the source, a primary key is required, and the app treats the copy as read-only. **Lakehouse Sync**, documented as Public Preview, captures Lakebase row changes into Unity Catalog Delta tables as history.

| Path | Freshness you can promise | Consistency |
|---|---|---|
| Synced table, snapshot or triggered | As of the last run | Asynchronous copy |
| Synced table, continuous | Seconds behind | Asynchronous copy |
| Lakehouse Sync to Delta | Behind the source | History rows |
| `review_item` read in a transaction | Current | Transactional |

A screen that joins the app's claims with a synced roster mixes two moments; show the roster's as-of time.

<!-- section:dbxfe-lakebase-l01-example -->

The claim is one statement and one short transaction:

```sql
UPDATE qr.review_item AS r
   SET status = 'claimed', claimed_by = :'reviewer_id',
       claimed_at = now(), version = r.version + 1
 WHERE r.item_id = (
         SELECT q.item_id FROM qr.review_item AS q
          WHERE q.status = 'ready'
          ORDER BY q.severity DESC, q.flagged_at, q.item_id
          LIMIT 1 FOR UPDATE SKIP LOCKED)
   AND r.status = 'ready'
RETURNING r.item_id, r.claimed_by, r.version;
```

The decision carries the version the form loaded:

```sql
UPDATE qr.review_item
   SET status = 'decided', decision = :'decision',
       decided_at = now(), version = version + 1
 WHERE item_id = :'item_id' AND claimed_by = :'reviewer_id'
   AND status = 'claimed' AND version = :expected_version
RETURNING item_id, status, decision, version;
```

In the lab, R-101 claimed QR-0001 at version 3, a supervisor reassigned it to R-103 (version 4), and R-101's submit with version 3 updated no row; R-103 then decided *rework* at version 5. These are local PostgreSQL 16.13 results on synthetic records.

<!-- section:dbxfe-lakebase-l01-exercise -->

A second producer, the supplier portal, starts sending review requests with its own message numbering. Redesign intake so that a redelivered portal message changes nothing, and portal and pipeline messages for the same part never overwrite each other's newer state. Write the changed keys and the upsert's conflict rule, one sentence the dashboard shows about the synced reviewer roster, and which statements still work behind a transaction-mode pooler.

<!-- section:dbxfe-lakebase-l01-solution -->

Key the log by source and message, `PRIMARY KEY (source, message_id)`, because two producers can reuse each other's numbers. Give each source its own sequence on the item (`pipeline_seq`, `portal_seq`), or move per-source facts into a child table keyed by `(item_id, source)`, so each source competes only with itself; `DO UPDATE ... WHERE` compares the incoming sequence with that source's stored one and still requires `status = 'ready'`. The dashboard says: "Reviewer roster as of 06:40 (synced table, triggered daily); claims and decisions are live." Every statement is one transaction with schema-qualified names, so all of them work behind the pooler; a session advisory lock or a temp table held across requests would not.

<!-- section:dbxfe-lakebase-l01-mistakes -->

- **A transaction held open while a person decides.** Locks stay held, a server connection is pinned, and a disconnect rolls the claim back. Commit the claim; check the version on the decision.
- **Read, then update, with no lock or condition.** Two workers read the same ready row and both "claim" it; in the lab the second silently replaced the first.
- **Last write wins on intake.** A late, older message overwrote newer state.
- **A synced table treated as current or writable.** It lags its source and is read-only.
- **A local run called Lakebase.** The lab proves PostgreSQL semantics; tokens, pooling, branches and sync are verified on the platform.

<!-- section:dbxfe-lakebase-l01-sources -->

Databricks on AWS documentation: Lakebase Postgres, Core concepts, About authentication, Use connection pooling, Scale to zero, Branches, Point-in-time restore, Serve lakehouse data with synced tables, Lakehouse Sync, Postgres compatibility and the Lakebase release notes. PostgreSQL 16 documentation: Transactions, Transaction Isolation, Explicit Locking, SELECT and INSERT. Reviewed at search level on 2026-09-23; page bodies were not fetched in this build.

<!-- section:dbxfe-lakebase-l01-related -->

Lab L23, *Transactional state for a quality-review app*, runs every statement here on a throwaway local PostgreSQL 16 server and adds a Lakebase adaptation guide. *Databricks Apps and application architecture* puts this database behind an application's identity and request path. For migration staging and rollback, revisit [Architecture and migration](#/module/dbxfe-m08).

<!-- section:dbxfe-lakebase-l01-revisit -->

Revisit whenever you design an app that writes: name each piece of state, the constraint that guards it, the transaction that changes it, the concurrency pattern that protects it, and the freshness of every copy it reads.
