<!-- section:dbxfe-sharing-l01-outcome -->

After this lesson you can choose how another organization reaches Cinderline's data, or Cinderline reaches theirs, and defend the choice on six questions: movement, enforcement, cost in kind, revocation, freshness and failure. You can trace OpenSharing (the current Databricks name for the product family formerly documented as Delta Sharing) down to its request path, recognise when federation, ingestion, UniForm or a clean room fits instead, and rehearse a revocation. Nothing here creates a share, a connection or a clean room.

<!-- section:dbxfe-sharing-l01-start -->

Bring two ideas from earlier modules. A Unity Catalog object has a three-part name and a grant decides who reads it: [Unity Catalog, security and deployment](#/module/dbxfe-m06), with [design least-privilege access](#/lesson/dbxfe-m06-l02) for scoping what another party may see. A Delta table is Parquet files plus a transaction log whose versions are snapshots: [Delta tables: files, log, and snapshots](#/lesson/dbxfe-m03-l02). The sharing and federation choice field guide carries the blank six-question template; this lesson supplies the mechanism behind each answer.

<!-- section:dbxfe-sharing-l01-patterns -->

A **copy** (an export, an extract, an ingested table) puts rows into the other party's systems. After delivery only the holder's controls apply: nothing can be revoked and nothing records what was read. A **governed share** leaves the data in the provider's storage; the recipient reads it through a sharing server that checks the recipient and the share on every request. **Federation** runs a query against the other party's system in place, through a connection whose credential that party issues and can withdraw. When neither party may see the other's rows, a **clean room** shares computation and outputs instead of rows.

Ask the same six questions of each: what moves and where it lands; who authorizes each read and where; who pays in kind (storage, compute, transfer, people); how revocation works and what the other party keeps; how fresh their view is; what fails, and how visibly, when the link breaks. Governed sharing and federation are both **access-in-place**: nothing is copied until a result is saved.

<!-- section:dbxfe-sharing-l01-sharing -->

Databricks' current documentation calls its sharing product family **OpenSharing**; the historical delta-sharing documentation URL leads to the OpenSharing overview. The open protocol it implements is still specified as the **Delta Sharing Protocol**, and identifiers keep their spelling: `format("deltaSharing")` in Spark, the `delta_sharing` Python package, `shareCredentialsVersion` in the credential profile, and the `shares`, `recipients` and `providers` API resources.

A **share** lists objects from the provider's metastore (tables, views, volumes, models and others); a **recipient** represents the other organization; a grant of `SELECT` on the share connects them. The share owner must keep `SELECT` on every shared table, so a group should own it. A recipient with a Unity Catalog workspace sends a sharing identifier (`cloud:region:metastore-uuid`) and receives no token (Databricks-to-Databricks sharing); any other recipient gets an activation link that downloads a credential file once, or authenticates with OIDC federation (open sharing).

Each read is a REST call carrying the bearer token. The server answers with a list of Parquet files as short-lived HTTPS URLs, and the client downloads them directly from the provider's storage. Filters a client sends are hints, applied best effort, so restrict rows in the shared view, not in the recipient's code.

<!-- section:dbxfe-sharing-l01-lifecycle -->

A shared table is read at its latest version each time, so the recipient's view is fresh at the moment of the read. Anything the recipient saves is a copy that goes stale from then on; the protocol's table-version call lets a client check whether its cache is behind. Reading an earlier version or timestamp works only when the provider enabled history sharing for that object, which is off by default.

Revocation has three levers: remove the recipient's grant, delete the recipient, or rotate its token with zero seconds so the old one ends at once (rotation can shorten a token's life but never extend it). The next request fails. File URLs already issued keep working until their own expiry, and saved extracts stay. So revocation is proven by rehearsal: grant on synthetic rows, read, revoke, measure the time until the recipient's next read fails, and write down the tail.

<!-- section:dbxfe-sharing-l01-federation -->

Lakehouse Federation registers a **connection** in Unity Catalog (host and credential options for a source such as PostgreSQL, SQL Server, MySQL or Snowflake) and a **foreign catalog** that mirrors one database through it. An analyst's query passes two checks: Unity Catalog grants on the foreign catalog, then the source's own authorization of the connection's credential. The current overview describes the query and catalog federation paths as read-only.

**Pushdown** decides the traffic. Filters, projections and limits the connector can translate run in the source; others run in Databricks after every row has arrived. `EXPLAIN FORMATTED` shows the remote query, which is the evidence, and JDBC `fetchSize` sets rows per batch, not parallelism.

Choose **ingestion** (for example a Lakeflow Connect pipeline into Delta tables) when a dataset is queried often, needs history, or must not load the source on every query. Choose **access-in-place** when the question is occasional and needs the source's current state.

<!-- section:dbxfe-sharing-l01-formats -->

Delta Lake, Apache Iceberg and Apache Hudi tables are all Parquet files plus metadata. **UniForm** keeps a Delta table's files and additionally writes Iceberg metadata for them after each Delta commit, asynchronously, so an Iceberg reader can lag; `converted_delta_version` says which Delta version it sees. It is enabled with `delta.enableIcebergCompatV2` and `delta.universalFormat.enabledFormats = 'iceberg'`, requires column mapping, and is read-only for Iceberg clients: an external Iceberg writer can damage the Delta table.

An outside engine finds a table through a **catalog**. The Iceberg REST catalog protocol has the engine ask for configuration, load a table and optionally receive vended short-lived storage credentials. Unity Catalog vends them only after a metastore admin enables external access and the catalog owner grants `EXTERNAL USE SCHEMA`, which neither ownership nor `ALL PRIVILEGES` includes.

<!-- section:dbxfe-sharing-l01-cleanrooms -->

A clean room, per the Databricks API reference, uses the sharing layer and serverless compute so several parties can work on sensitive data without direct access to each other's data. Collaborators add tables, views, volumes or notebooks; a notebook is reviewed and run only by named collaborators; results land in an output catalog. What leaves is whatever the approved code writes, so review the outputs, not the room. Every collaborator is identified by a Unity Catalog metastore, and availability by cloud and region must be checked before one is proposed.

<!-- section:dbxfe-sharing-l01-example -->

Halvern Coatings, the fictional coating supplier in the sharing and federation choice field guide, wants line 2 coated-part defect counts by coating batch, 90 days back and then weekly. It has no Databricks workspace and works in Python notebooks.

| Question | Governed share to Halvern (chosen) |
|---|---|
| What moves | Nothing is copied by Cinderline; each read fetches the view's files; results land in Halvern's notebooks |
| Enforcement | Recipient `halvern_coatings` on share `halvern_line2_quality`, checked per request; the view `share.line2_coated_defects_by_batch` limits rows to line 2, coated parts, 90 days |
| Cost in kind | Cinderline's storage serves reads and any cross-region transfer; Halvern's compute; people to rotate the token |
| Revocation | Remove the grant and rotate with zero seconds; issued URLs run out; Halvern keeps what it saved |
| Freshness | Latest published version at each read |
| Failure | Expired token or lost owner privilege: Halvern's read fails with an error, visibly |

Conditions: open sharing with a token expiry, an IP access list and a named contact; confirm that sharing a view to an open recipient is supported for Cinderline's workspace, or share a purpose-built gold table instead; Halvern first reads a synthetic version from its own notebook. The reverse direction stays a weekly extract, as the guide records, because Halvern's DBA declined federation load.

<!-- section:dbxfe-sharing-l01-exercise -->

Choose copy, governed share, federation, ingestion or clean room for each request, with the one fact that decides it.

1. A regulator needs a signed, point-in-time extract of 2025 scrap figures.
2. Halvern wants to explore line 2 defects weekly, and Cinderline must be able to cut access.
3. Cinderline's analysts check today's MES work orders a few times a week.
4. The daily scrap dashboard needs MES work orders with three years of history.
5. Cinderline and a supplier that runs Unity Catalog want to correlate warranty returns with compound batches, and neither may see the other's rows.

<!-- section:dbxfe-sharing-l01-solution -->

1. **Copy.** The point is a fixed record the regulator keeps; withdrawal is not wanted, so write retention terms instead.
2. **Governed share** (open sharing, since Halvern has no Databricks workspace). Halvern may see the rows and access must be withdrawable; each read is fresh.
3. **Federation** through a foreign catalog. Occasional questions about the current state are access-in-place; check the remote query for the date filter.
4. **Ingestion** into Delta tables. Daily use and a three-year history need a governed copy that loads the source once per run.
5. **Clean room**, if available in both companies' clouds and regions. Neither side may see rows and both have Unity Catalog metastores; review the notebook's aggregated outputs.

A common wrong answer to request 4 is federation: it loads the MES database on every dashboard refresh and cannot reproduce last year's figures.

<!-- section:dbxfe-sharing-l01-mistakes -->

- **Treating revocation as deletion.** Removing a grant stops the next request; saved extracts and already-issued file URLs are outside it.
- **Filtering in the recipient's code.** Predicate hints are best effort; the shared view or partition specification is the boundary.
- **A person owns the share.** When that person's access goes, recipients lose the tables; make a group the owner.
- **A credential file with no expiry, sent by email.** The protocol treats a missing expiry as never expiring; set one and rotate.
- **Renaming identifiers to match the product name.** `deltaSharing`, `delta_sharing` and the API resources keep their spelling.
- **Assuming a pushed filter.** Read the remote query in `EXPLAIN FORMATTED` before blaming the source.
- **Letting an Iceberg engine write a UniForm table.** Iceberg clients may only read it.

<!-- section:dbxfe-sharing-l01-sources -->

Primary texts read in this build on 2026-09-23, in the sections this lesson relies on: the [Delta Sharing Protocol](https://github.com/delta-io/delta-sharing/blob/main/PROTOCOL.md) and its [connector README](https://github.com/delta-io/delta-sharing/blob/main/README.md); the API docstrings of the [Databricks SDK for Python 0.141.0](https://pypi.org/project/databricks-sdk/); Delta Lake's [UniForm documentation source](https://github.com/delta-io/delta/blob/master/docs/src/content/docs/delta-uniform.mdx); and the [Apache Iceberg REST Catalog API](https://github.com/apache/iceberg/blob/main/open-api/rest-catalog-open-api.yaml). Databricks pages whose titles and URLs come from this repository's earlier reviewed records, not re-read here: [What is OpenSharing?](https://docs.databricks.com/aws/en/opensharing), [Connect to external databases and catalogs](https://docs.databricks.com/aws/en/query-federation/), [Lakehouse Federation performance recommendations](https://docs.databricks.com/aws/en/query-federation/performance-recommendations) and [What is Lakeflow Connect?](https://docs.databricks.com/aws/en/ingestion/overview). SQL is shown as the author wrote it, not checked against the reference in this build; check it against the current SQL reference, and check availability by cloud, region and asset type before promising anything.

<!-- section:dbxfe-sharing-l01-related -->

[Unity Catalog, security and deployment](#/module/dbxfe-m06) for grants and least privilege; [Ingestion, records and reliable updates](#/module/dbxfe-m04) for what an ingested copy needs next; [Architecture and migration](#/module/dbxfe-m08) for recording the decision; the sharing and federation choice field guide for the blank template.

<!-- section:dbxfe-sharing-l01-revisit -->

In a week, without notes: draw the revocation timeline up to the last URL expiry; name the identifiers that never change with documentation names; explain why an Iceberg reader of a UniForm table can lag; say which of the six answers change when a partner cannot read a share.
