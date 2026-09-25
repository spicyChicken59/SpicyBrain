<!-- section:action -->

Design the application by following requests, not by choosing a database first. The storage decision falls out of what each request needs to be true when it completes.

1. **Pick the requests that matter.** List the user actions and choose the three to five that carry the business decision or the risk.
2. **Trace each request** from the browser through the application back end to authentication, then to data, model or tool, and back. At each hop name who authenticates and whose permissions apply. A request that crosses a trust boundary without a named identity is a design gap.
3. **Name the contracts.** Request and response schemas, validation rules, the error contract, and how a contract is versioned. Write the concrete example payload, not only the field list.
4. **Classify the state each request touches:** per-request (nothing survives), session (ephemeral, per user), operational records that need atomic multi-row writes and concurrent updates, derived analytical results, and caches. Only the third class needs transactions.
5. **For transactional state, write the invariants:** entities, keys, what must never be true, isolation needs, who writes concurrently, and how recovery works.
6. **Decide storage per class** and state the synchronization between operational and analytical stores with its freshness and consistency explicitly.
7. **Write local mocked contract tests** and label them: a local mock is not a deployed application.

Evidence to collect: the request traces with identities, the contract examples, the state classification table, the invariant list with a test per invariant, and the synchronization statement.

Deeper: [Databricks Apps and application architecture](#/module/dbxfe-apps) for the browser-to-data trust boundaries, [Lakebase, Postgres and operational state](#/module/dbxfe-lakebase) for transactional design and concurrency, [Identity, authorization and audit](#/module/dbxfe-identity), and the retained lesson [Cloud responsibilities and request paths](#/lesson/dbxfe-cloud-bridge).

<!-- section:example -->

**Fictional worked example: Cinderline's quality exception review application.** Quarantined inspection records (invalid quantities, conflicting revisions) currently sit in a spreadsheet. The quality lead wants reviewers to claim an item, investigate, and record a disposition; the morning dashboard should then reflect dispositions. The application is proposed on the platform's application hosting with a managed Postgres store for operational records.

### Requests that matter

1. View the quarantine queue.
2. Claim an item for review.
3. Record a disposition (accepted, corrected with new values, rejected).
4. Morning dashboard reads the resolved state.

### Request traces

*View the queue.* Browser → application back end (the reviewer's identity, forwarded by the platform) → query filtered to the reviewer's plant in the handler, until row-level enforcement is confirmed → response. No write. Same unknown and owner as the claim below; without the filter a reviewer could list other plants' quarantined records.

*Claim an item.* Browser → application back end (user authenticated by the platform's application identity flow; the reviewer's identity is passed, not the app's) → authorization check that the reviewer belongs to the item's plant → Postgres write → response. The application's own identity holds the database grant; the reviewer's identity is recorded on the row and checked in the handler. Unknown: whether row-level enforcement in the database is available under the platform's managed offering, or whether the handler is the enforcement point. The data lead owns the answer, and the design assumes handler enforcement until then.

*Record a disposition.* Same path, but the write touches two rows: the disposition record and the queue item's status. They must change together.

*Dashboard.* Analyst identity → SQL warehouse → analytical table refreshed from the operational store. No write path.

### Contracts

`ClaimRequest { inspection_key: "A-2031", revision: 2 }` → `ClaimResponse { status: "claimed", claimed_at: "2026-03-09T07:41:12Z" }` or `{ status: "conflict", claimed_by: "leo.d" }`. The reviewer is the identity the platform forwards, never a field in the body; a body that names one is rejected by the schema, and a test says so. Errors are structured, never free text, and the conflict is a normal response, not an exception. Contract version is carried in the path.

### State classification

| State | Class | Needs transactions? | Store |
|---|---|---|---|
| Queue filter selections | Session | No | Browser or session cache |
| Claims | Operational | Yes: one active claim per key and revision | Postgres |
| Dispositions | Operational, append-only | Yes: disposition and status change together | Postgres |
| Resolved-state summary for the dashboard | Derived analytical | No | Lakehouse table, refreshed hourly |
| Manual text shown beside an item | Cache | No | Application cache with expiry |

### Invariants and tests

- At most one active claim per (inspection key, revision). Test: two local connections claim the same item concurrently; exactly one succeeds, the other receives `conflict`.
- A disposition can be recorded only by the current claimant. Test: a non-claimant's write is refused.
- Dispositions are never updated; a correction appends a new disposition that supersedes the earlier one. Test: an update statement against the table is refused by grant.
- A disposition and its queue-status change commit together or not at all. Test: the transaction is made to fail after the disposition insert; a second connection sees neither change.

Isolation: read committed, with a unique partial index on active claims, which is what holds the first invariant under concurrent writers. Recovery: a failed transaction leaves the item claimed and the disposition retriable; nothing half-written is visible.

The tests ran locally against a real PostgreSQL instance, and the record says so; nothing was deployed.

### Synchronization

Dispositions reach the analytical table on an hourly schedule. The dashboard prints "dispositions as of 07:00" rather than implying live state. The quality lead accepted hourly for the morning meeting; a reviewer who needs the live queue uses the application, not the dashboard.

### Open questions

Whether dispositions must flow back to the ERP (out of scope for this design, stated so; quality lead), the application identity model on the platform (data lead), and regional availability of the managed store (security lead). Each blocks deployment, not design.

<!-- section:template -->

### Requests that matter

- **Three to five user actions**, each with the decision or risk it carries.

### Request traces

| Request | Hop | Who authenticates | Whose permissions apply | Enforcement point | Unknown? |
|---|---|---|---|---|---|
| Name | Browser → back end → auth → data/model/tool → response, one row per hop | The principal at this hop | User, application or service identity | Handler, database, platform | Name the owner of the answer |

### Contracts

- **For each request:** a concrete example request, a success response, an error response, the validation rules, and how the contract is versioned.

### State classification

| State | Class (per-request / session / operational / analytical / cache) | Needs transactions? | Store | Why |
|---|---|---|---|---|

### Invariants for operational state

- **Statement of what must never be true**, the concurrent writers who could violate it, the isolation needed, and the local test that demonstrates it.

### Synchronization

- **Direction, schedule, freshness shown to users, consistency guarantee, and what a consumer sees during a lag.**

### Local test record

- **What ran, against which engine, and the explicit statement that nothing was deployed.**

### Open questions and owners

<!-- section:limits -->

This design note establishes the request paths, contracts and invariants of an application as you intend it, and the local tests establish that the invariants hold on the engine you ran them on. It cannot establish the platform's managed-store behaviour, the application identity flow, regional availability or cost; those are read from current documentation and verified by a deployment you have not made. A local PostgreSQL run is not the managed service, and a mocked contract test is not an integration test. Escalate when a request would write to a system of record, when the enforcement point for a permission is unknown, or when the synchronization lag could change a decision that users believe is live.
