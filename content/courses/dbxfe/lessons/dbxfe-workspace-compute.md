<!-- section:dbxfe-workspace-compute-start -->

You should recognize a query and the difference between a file and a process. The optional [cloud bridge](#/lesson/dbxfe-cloud-bridge) explains identity and request paths. It guides the explanation and does not lock this topic.

<!-- section:dbxfe-workspace-compute-responsibilities -->

An account is the administrative context for an organization’s Databricks resources. A workspace is an environment for collaborating on and running work. A notebook contains authored commands and results; a saved SQL query contains a query definition. Neither is the durable table itself. Compute executes the commands, while cloud storage holds durable data and table metadata. Unity Catalog controls the governed access path. A table name identifies an object; the name alone does not tell you the physical location or grant access.

Imagine submitting SELECT inspected_units FROM quality.accepted.inspections. The workspace supplies an entry point and execution context. Suitable compute plans and executes the request. The relevant identity and governance controls determine permitted table access; the table layer determines a committed view of the data files. The result returns to the client. These responsibilities interact: the diagram is a conceptual trace, not a guarantee that each permission check occurs only once or in this exact implementation order.

In the documented AWS architecture, classic compute runs in the customer's AWS account, while serverless compute runs in a Databricks-managed compute plane. Both still require appropriate identity, governed access and connectivity to the resources involved. Workspace type, region, network setup and feature availability determine the actual deployment. Serverless does not mean "no computers" or "no access responsibility"; the service manages more of the execution infrastructure.

<!-- section:dbxfe-workspace-compute-worked -->

Cinderline saves a notebook containing a query, stores a Delta table in durable object storage, and builds a Python list inside a running session. Compute then stops. The durable table is separate from that compute lifecycle, and the saved notebook definition remains a workspace artifact. The in-memory Python list is not durable state you should rely on recovering. A temporary view or cached data tied to a session is not a replacement for persisted output. Specific saved-output retention and session behavior depend on the interface; this lesson makes no blanket promise about every transient result.

| Item | Responsibility | Planning assumption after stop |
|---|---|---|
| Saved notebook commands | Workspace authoring artifact | Reopen the saved definition |
| Committed table data/log | Durable storage and table layer | Query again with suitable compute and access |
| Python list created in the session | Process memory | Reconstruct from retained input |
| Table SELECT authorization | Governance | Still verify the current principal and grants |

The recovery plan therefore starts from saved code and retained input. Restarting compute does not repair wrong data or create permissions. It supplies execution capacity for the next request.

<!-- section:dbxfe-workspace-compute-task -->

Draw a path for an analyst opening a saved SQL query, using compute to read quality.reporting.daily_rate, then viewing rows. Label the durable data location, execution responsibility and identity/authorization boundary. Draw classic and serverless alternatives using AWS labels. If the analyst cannot read the table after compute restarts, give two competing hypotheses and the evidence that distinguishes them.

<!-- section:dbxfe-workspace-compute-solution -->

Analyst identity → workspace query entry → suitable compute → governed table access → committed data in durable storage → result returned to the analyst. For classic, place the compute plane in the customer AWS account; for serverless, place it in the Databricks-managed plane. Draw storage and its access path separately. The notebook/query definition is saved authoring content, not the database's physical contents.

Hypothesis one is missing privileges for the actual analyst or job identity; inspect the denial and effective grants. Hypothesis two is failure of the required network/storage path; inspect the endpoint, connection evidence and service response. A stopped or unavailable compute resource is a third distinct possibility. Preserve the precise error and execution context instead of changing all layers at once. The storage can remain intact while a new request fails.

<!-- section:dbxfe-workspace-compute-limits -->

Calling a SQL warehouse "where all the data lives" confuses compute with durable data. Drawing every component inside one workspace box hides ownership. Moving to serverless is not proof that a chosen private endpoint is configured or a table is authorized. This original schematic uses no product screenshot and represents no tested customer environment.

<!-- section:dbxfe-workspace-compute-links -->

[Delta snapshots](#/lesson/dbxfe-m03-l02) explains which table state a reader sees. [Unity Catalog](#/lesson/dbxfe-m06-l01) explains names and basic access. Architecture claims refer to AWS primary documentation; the Cinderline request and stop/restart reasoning are teaching examples.

<!-- section:dbxfe-workspace-compute-foundation-sources -->

Primary documentation was read on 19 September 2026. Open Sources below for exact publishers, cloud/runtime context and limitations. Official mechanisms, original professional guidance and fictional records are distinct. These examples do not establish a Databricks execution, production performance, configured permissions or complete source coverage. This lesson shows no executable code. The optional downloadable bundle provides setup, input files, independent expected outputs, starter tasks and complete solutions for other lessons; its local acceptance run passed 30 tests with no failures or skips using Python 3.12.14, Apache Spark 4.0.4 and Java 17.0.20.1+1, covering the displayed examples and changed input cases of the Python bridge, DataFrame, grain-and-join and later reliable-data lessons, not this one. The bundle includes exact fixture/output hashes and execution evidence. These results do not include Delta or Databricks execution; the reader itself does not execute code.

<!-- section:dbxfe-workspace-compute-revisit -->

Try the explained checks, then review the linked cards. A reveal, visit or optional bridge skip does not record a pass or mastery. Mark completion only when you choose; assessment and review evidence remain separate.
