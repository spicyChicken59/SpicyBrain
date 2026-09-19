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
