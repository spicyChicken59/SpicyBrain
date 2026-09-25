<!-- section:dbxfe-m06-l01-foundation-start -->

[Workspace, storage and compute](#/lesson/dbxfe-workspace-compute) explains the request entry and execution responsibilities. The optional [cloud bridge](#/lesson/dbxfe-cloud-bridge) separates permission from connectivity. This package teaches basic governed table reads in the AWS documentation context, using Privilege Model 1.0; it is not an enterprise administration lab.

<!-- section:dbxfe-m06-l01-foundation-mechanism -->

A Unity Catalog metastore is a top-level governance container. A workspace uses an assigned metastore context; workspaces and metastores are different objects. Within that hierarchy, catalog.schema.object names the data asset: quality.reporting.daily_rate means catalog quality, schema reporting, object daily_rate. A schema here is an organizational namespace; "DataFrame schema" later means a set of fields/types, a different use of the word.

A managed table delegates storage lifecycle management to Unity Catalog as well as governing access. An external table can still have governed table access while storage lifecycle remains externally managed. In either case, people still own data meaning, source quality and intended permission policy. Direct file access outside the intended governed route needs separate review.

For a basic table reader, check USE CATALOG on the parent catalog, USE SCHEMA on the parent schema, and SELECT on the table, including any effective inherited grants. These table requirements are not the whole execution checklist: the principal also needs the relevant workspace/compute access, supported execution context and available data path. Avoid claiming every denial has the same cause.

<!-- section:dbxfe-m06-l01-foundation-example -->

Assume the workspace can use the relevant catalog, execution is available, storage connectivity is functioning, no additional policy blocks the query, and the table exists. These assumptions isolate the basic privilege example. Group membership/effective grants below are fictional.

| Principal | USE CATALOG quality | USE SCHEMA reporting | SELECT daily_rate | Basic table-read result |
|---|---|---|---|---|
| analyst-ava | Yes | Yes | Yes | Allowed under stated assumptions |
| analyst-ben | Yes | No | Yes | Denied: missing schema usage |
| pipeline-job | Yes | Yes | No | Denied: missing table SELECT |

Granting Ben SELECT again will not supply missing USE SCHEMA. Granting the pipeline author's human user SELECT will not change the pipeline-job principal. Diagnose the exact attempted name and actual identity before altering scope.

The following is illustrative administrator SQL for an already authorized, scoped change, not a command run in this course:
~~~sql
GRANT USE CATALOG ON CATALOG quality TO quality_readers;
GRANT USE SCHEMA ON SCHEMA quality.reporting TO quality_readers;
GRANT SELECT ON TABLE quality.reporting.daily_rate TO quality_readers;
~~~
Do not execute grants merely to follow a reading exercise. An owner with authority must verify the real principal, grant inheritance and intended access. The example intentionally avoids ALL PRIVILEGES and preview fine-grained write grants.

<!-- section:dbxfe-m06-l01-foundation-task -->

Ben successfully connects to the compute service and receives a specific USE SCHEMA denial for quality.reporting. An administrator can query the table. The reporting schema also contains sensitive objects that Ben should not read. Identify the missing basic grant, explain why broad schema SELECT is unnecessary, and specify a consumer test and a denied-action test after an authorized correction.

<!-- section:dbxfe-m06-l01-foundation-solution -->

Under the matrix assumptions, Ben needs USE SCHEMA on quality.reporting while retaining existing catalog usage and SELECT on only the intended daily_rate table. USE SCHEMA allows namespace usage; it does not itself grant read access to every table. Broad SELECT on the schema would expand access to its current/future tables and is unnecessary for the stated request.

Retest the exact daily_rate SELECT as Ben in the intended workspace/compute context. Also attempt to read a designated out-of-scope table as Ben and expect denial, without exposing its actual data. The administrator's success can help establish object existence and some functioning path, but does not prove Ben's effective grants. Record the actual identity, object, outcome and assumptions; do not report the local worksheet as a tested cloud configuration.

<!-- section:dbxfe-m06-l01-access-reference -->

1. Preserve exact error, time, object and operation.
2. Confirm actual executing principal; interactive author and scheduled job can differ.
3. For a named table privilege denial, inspect effective SELECT and parent usage, bindings and relevant policies.
4. For DNS, timeout or endpoint errors, inspect the request path; adding table grants does not create a route.
5. Make the smallest authorized correction and test permitted plus denied behavior in the consumer context.

<!-- section:dbxfe-m06-l01-foundation-limits -->

Discovering an object in a catalog is not permission to read its data. External does not mean ungoverned. Managed does not mean the organization no longer owns retention or quality decisions. Do not infer full lineage coverage or compliance from a catalog entry. The original governance worksheet and application material remain below.

<!-- section:dbxfe-m06-l01-foundation-links -->

[Design least-privilege access](#/lesson/dbxfe-m06-l02) retains the applied stakeholder exercise. [Cloud trust boundaries](#/lesson/dbxfe-m06-l03) retains introductory deployment framing, without claiming this path teaches advanced security. Official object/privilege mechanisms and fictional grants are labeled separately.

<!-- section:dbxfe-m06-l01-foundation-sources -->

Primary documentation was read on 19 September 2026. Open Sources below for exact publishers, cloud/runtime context and limitations. Official mechanisms, original professional guidance and fictional records are distinct. Nothing in this lesson was executed. The three GRANT statements are illustrative platform SQL: they cannot run on local Spark, were not run in a Databricks workspace, and are not part of the optional Reliable Data Foundations bundle offered with this path, whose local tests cover the path's Python and Spark lessons, not this one. These examples do not establish configured permissions, a Databricks execution or complete source coverage. To practise this lesson's access matrix, work the tabletop governance review lab: a small local evaluator checks your answers against authored keys, which is not Unity Catalog enforcement. The reader itself does not execute code.

<!-- section:why -->

A customer asks where to put a table and who owns it. A useful answer distinguishes organizational naming, permissions, and responsibility for the underlying data.

<!-- section:understand -->

Unity Catalog provides a governance layer for data and AI assets in Databricks. Key assets use a three-part name such as `quality.accepted.inspections`: catalog, schema, and object. A name helps locate an asset; it is not itself an access grant.

Managed and external tables differ in storage-lifecycle responsibility. Do not translate “external” into “ungoverned,” or “managed” into “no customer responsibility.” The organization still chooses appropriate ownership, classification, access, and operating procedures. Exact behavior depends on object type and supported operations.

For fictional Cinderline, separate raw inspection input from accepted reporting data so responsibilities are clear. The quality team may own the metric definition, while a platform group owns technical operations. Record both. A technical table owner is not automatically the person who can approve a new defect definition.

<!-- section:see -->

**Fictional naming and ownership worksheet.**

| Asset | Meaning | Decisions to confirm |
|---|---|---|
| quality.raw.inspection_events | Received deliveries | Retention, sensitivity, producer |
| quality.accepted.inspections | Resolved valid inspection state | Correction rule and technical owner |
| quality.reporting.daily_rate | Agreed daily metric | Definition owner and consumer access |

The names are illustrative, not required conventions. The worksheet teaches that each object needs both a technical responsibility and a business meaning.

<!-- section:deeper -->

A metastore, workspace, catalog, and schema are different concepts. Before prescribing a hierarchy, understand regional boundaries, workspace attachment, isolation requirements, and administrative ownership. Lineage and audit information are useful, but coverage depends on supported paths and operations. Do not promise that any arbitrary external transformation is automatically captured or that governance configuration alone establishes regulatory compliance.

<!-- section:customer -->

For a data-governance lead: “We can organize the raw, accepted, and reporting assets so ownership and access are explicit. We will distinguish the technical object owner from the person who approves the metric, and verify the governance coverage for the actual tools in the path.”

<!-- section:try -->

The fictional analyst says, “It is an external table, so Unity Catalog cannot govern it.” Correct the misconception without promising that every possible access path is governed. Name the configuration you would inspect.

<!-- section:revisit -->

Explain that external assets can be governed while the storage lifecycle remains externally managed. Inspect how the table is registered, which storage location and credentials are involved, which identities have object privileges, and whether any direct storage access bypasses the intended path. Ask the platform/security owner to validate that configuration.

The key is to separate object governance from file ownership and every possible access route. A catalog entry alone is not evidence that all alternate paths are closed.
