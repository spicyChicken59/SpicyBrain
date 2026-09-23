<!-- section:dbxfe-azure-l01-outcome -->

After this lesson you can draw Cinderline's Azure deployment as it is operated: an Entra tenant and subscription, a workspace resource with its locked managed resource group, the control plane in the Databricks account, and two supported network patterns with different duties. You can keep storage access apart from application access, trace one query across its boundaries, and run two ordered diagnoses: one for a refused request, one for a request that never arrived. Nothing here provisions a resource; tier, region and feature availability are verified first.

<!-- section:dbxfe-azure-l01-start -->

Bring the platform map: account, workspace, catalog, compute and storage as separate responsibilities. [Draw the cloud and trust boundaries](#/lesson/dbxfe-m06-l03) explains trust boundaries and the specialist hand-off; [Cloud responsibilities and request paths](#/lesson/dbxfe-cloud-bridge) walks one request through DNS, routes and policy; [Unity Catalog names and basic access](#/lesson/dbxfe-m06-l01) owns the privilege model. The [AWS deployment and network boundaries](#/module/dbxfe-aws) module asks the same questions of AWS; this lesson answers them with Azure's own objects.

<!-- section:dbxfe-azure-l01-resources -->

Cinderline's Entra tenant trusts subscription `sub-cinderline-data`. In resource group `rg-cinderline-data` sits the workspace resource `dbw-cinderline-prod`, type `Microsoft.Databricks/workspaces`. Creating it also provisioned `rg-dbw-prod-managed`, a managed resource group holding the workspace storage account, networking components and, while clusters run, their virtual machines. A system deny assignment protects that group: a subscription Owner can read it but not change it, so tags and settings go on the workspace resource.

The control plane, including the web application, runs in the Azure Databricks account; classic compute runs in Cinderline's subscription; serverless compute runs in the Databricks account. One query crosses four paths: author (browser, Entra sign-in, workspace URL), control (classic nodes dial out on port 443 to the secure cluster connectivity relay), execution (cluster or serverless warehouse once Unity Catalog agrees) and storage (compute to an `abfss://` address).

<!-- section:dbxfe-azure-l01-identity -->

Every identity starts in Entra: analysts are users in `grp-quality-analysts`; the nightly job runs as the application service principal `sp-job-nightly`; the access connector carries a managed identity, a service principal with no application object and no secret anyone holds. The SCIM connector syncs users and groups but not nested groups or service principals; automatic identity management syncs both.

Two authorities then grant separately. Unity Catalog privileges decide what a Databricks principal may query; Azure role assignments decide what an identity may do to Azure resources, including reading blob data. Holding one says nothing about the other.

<!-- section:dbxfe-azure-l01-patterns -->

| Duty | Default managed VNet | VNet injection |
|---|---|---|
| VNet, subnets, egress | Databricks, locked group | Cinderline |
| NSG rules Databricks needs | Databricks | Databricks, via delegation |
| Routes, firewall, private endpoints, DNS | Not available | Cinderline |
| Back-end Private Link | Not available | On Premium |

An injected workspace takes two dedicated subnets, host and container, delegated to `Microsoft.Databricks/workspaces`. Each node takes one address in each; Azure reserves five per subnet, so a /26 pair caps the workspace at 59 nodes. With secure cluster connectivity nodes get no public IP and the VNet opens no inbound port.

Egress is Cinderline's in the injected pattern: a NAT gateway for stable egress IPs, or a route table sending `0.0.0.0/0` to a firewall plus service-tag routes for `AzureDatabricks`, `Storage` and `EventHub`. Azure picks the longest matching prefix. Subnets of VNets created through API versions released after 31 March 2026 are private by default, so an explicit outbound method is required.

<!-- section:dbxfe-azure-l01-storage -->

Legacy notebooks reached ADLS Gen2 with a secret in the Spark configuration: an account key (Shared Key, which opens the whole account), a SAS signed with that key, or a service principal's client secret. Storage sees the key, not the person. Disallowing Shared Key rejects keys and key-signed SAS; Entra-authorized requests continue.

Unity Catalog replaces the secret with an access connector, `ac-cinderline-uc`, whose managed identity holds a data role such as Storage Blob Data Contributor on the account:

```sql
-- storage credential cinderline_lake_cred names the connector
CREATE EXTERNAL LOCATION IF NOT EXISTS cinderline_quality
  URL 'abfss://quality@stcinderlinelake.dfs.core.windows.net/accepted'
  WITH (STORAGE CREDENTIAL cinderline_lake_cred);
GRANT READ FILES ON EXTERNAL LOCATION cinderline_quality TO `grp-quality-eng`;
```

The address reads as container `quality`, account `stcinderlinelake`, the `dfs` endpoint and path `accepted`; `abfss` is the ABFS driver over TLS. `READ FILES` controls direct path reads of files under the location, a route separate from any table's SELECT, so it goes only to the engineers who need file access, here `grp-quality-eng`; table consumers get table privileges and nothing on the location.

Every read passes two chains. Application access: an Entra-authenticated principal holds Unity Catalog privileges. Storage access: the credential's identity holds a data role and the account's network rules admit it. Analysts need no Azure role on the lake; granting one opens a path around Unity Catalog.

<!-- section:dbxfe-azure-l01-private -->

Azure Databricks has three Private Link connection types, enabled independently: front-end (users, through `databricks_ui_api` and `browser_authentication` endpoints in a transit VNet), back-end (injected clusters, through `databricks_ui_api`; Premium and VNet injection required) and outbound from serverless through the NCC. Storage takes one endpoint per sub-resource, `dfs` for `abfss` paths.

A private endpoint is a network interface with a private address that carries traffic only when Approved. Public DNS answers with a CNAME into a `privatelink` name; only a Private DNS zone linked to the asking VNet, or forwarding to a resolver that sees one, returns the private address: `privatelink.azuredatabricks.net` for workspaces, `privatelink.dfs.core.windows.net` for ADLS.

<!-- section:dbxfe-azure-l01-serverless -->

Serverless compute runs in the Databricks account, so Cinderline's routes and firewall never see it. An account admin attaches a network connectivity configuration (NCC), a regional account object, to the workspace. Without private endpoint rules, serverless reaches Azure storage through service endpoints from stable subnets Cinderline can admit in the storage network rules. A private endpoint rule makes Databricks request an endpoint; the resource owner approves it in Azure, and only then does serverless use it.

<!-- section:dbxfe-azure-l01-example -->

The nightly job runs as `sp-job-nightly` and reads `quality.accepted.inspections`, an external table under `cinderline_quality`. Error texts are fictional.

| Evidence | Case A: denied | Case B: unreachable |
|---|---|---|
| Error text | `PERMISSION_DENIED: sp-job-nightly lacks SELECT on quality.accepted.inspections` | `connect timed out: stcinderlinelake.dfs.core.windows.net:443` |
| Who answered | Unity Catalog | Nobody |
| Compute | Serverless SQL warehouse | Injected classic cluster |
| First check | `SHOW GRANTS` | Name lookup on the cluster |

Case A stops at the catalog: grant `SELECT` to `sp-job-nightly`, rerun as that principal. A 403 from `stcinderlinelake` would instead mean the catalog agreed, and the evidence lives in the connector identity's role assignments, then the network rules. Case B has no refusal to read: from the cluster the name resolved to a public address, because `privatelink.dfs.core.windows.net` was linked to the hub VNet only, and the firewall dropped the packets. Link the zone to `vnet-cinderline-data` and retest from the same subnet.

<!-- section:dbxfe-azure-l01-task -->

Cinderline moves the nightly job to a serverless SQL warehouse. `stcinderlinelake` now has public network access disabled, an NCC private endpoint rule for its `dfs` sub-resource was added the same morning, and the migration created a new access connector. The first run returns a 403 from the storage account whose (fictional) details mention network access; the second, a day later, returns a 403 whose details mention the identity's authorization. Write both diagnostic sequences in order, name the first evidence object for each step, and list what you would mark unknown. Provision nothing.

<!-- section:dbxfe-azure-l01-solution -->

First run: storage refused, but about the network, not the identity. The NCC rule's state in the account console read PENDING: the storage owner had not approved the request, so serverless had no private path, and a request arriving by a public path meets public network access disabled. Evidence: the rule state, then the owner's approval. After ESTABLISHED, allow for propagation before retesting. This is a path fault wearing a refusal; no grant fixes it.

Second run: the path now works and there was no PERMISSION_DENIED, so the catalog agreed. Read the role assignments for the new connector's managed identity on `stcinderlinelake`: none existed. Grant the narrowest data role, wait up to ten minutes, rerun as `sp-job-nightly`.

Unknown until verified: endpoint support and limits in the region, networking charges, the workspace tier. Wrong fixes: a storage role for the job, or re-enabling public access.

<!-- section:dbxfe-azure-l01-differences -->

Carry the questions across clouds, not the answers:

- The workspace is an Azure resource with a locked managed resource group, not a configuration naming a customer account's VPC and bucket.
- Classic networking uses two delegated subnets and Databricks-managed NSG rules, not a customer VPC with a security group.
- Storage identity is an access connector's managed identity holding an Azure role; no trust policy is written.
- The legacy path is a key, SAS or client secret in Spark configuration, not an instance profile.
- Private Link adds `browser_authentication` and depends on Private DNS zone links.
- Serverless egress control needs Premium on Azure where the AWS pages name Enterprise; back-end Private Link on Azure also needs Premium.

<!-- section:dbxfe-azure-l01-limits -->

Treating every 403 as a missing grant: a storage network rule refuses with a 403 too, and a Private Link validation error arrives as a permission denial. Granting analysts a storage role to fix a catalog refusal. Editing resources inside the managed resource group. Testing DNS from a laptop instead of the asking network. Assuming serverless obeys Cinderline's firewall. Reading preview, regional or tier-dependent features as available.

<!-- section:dbxfe-azure-l01-sources -->

Azure Databricks pages on Microsoft Learn were confirmed by search-result title and snippet on 23 September 2026 by this module's earlier author in the same build session; their bodies were not fetched because the sandbox blocks the documentation host. Azure platform pages were read from their Markdown sources in Microsoft's public documentation repositories, and Databricks SDK docstrings from the PyPI package. Each source record says which. Documented mechanisms, original guidance and fictional Cinderline records are labelled separately.

<!-- section:dbxfe-azure-l01-links -->

[Draw the cloud and trust boundaries](#/lesson/dbxfe-m06-l03) carries the specialist hand-off. [Design least-privilege access](#/lesson/dbxfe-m06-l02) owns narrow grants. [AWS deployment and network boundaries](#/module/dbxfe-aws) runs the same diagnosis on AWS. The identity module and the Google Cloud module answer the same questions with their own constructs.

<!-- section:dbxfe-azure-l01-revisit -->

Work the two diagnostic sequences on paper with the changed case, then review the cards. Opening a section, revealing the solution or reading the checklist records no completion; mark completion only when you choose, and keep assessment evidence separate from reading.
