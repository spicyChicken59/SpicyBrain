<!-- section:dbxfe-gcp-l01-outcome -->

After this lesson you can draw Cinderline's Google Cloud deployment as it is operated: the Databricks account and control plane on one side; Cinderline's organization, folders and projects on the other, holding the VPC, firewall rules, buckets and service accounts; and two compute planes between them. You can trace one query with a named identity at every hop, diagnose in order a refused request and a request that never arrived, and keep every capability you could not verify marked unknown. Nothing here provisions a resource.

<!-- section:dbxfe-gcp-l01-start -->

Bring the platform map: account, workspace, catalog, compute and storage as separate responsibilities. [Draw the cloud and trust boundaries](#/lesson/dbxfe-m06-l03) explains why a trust boundary changes who operates a resource, and [Cloud responsibilities and request paths](#/lesson/dbxfe-cloud-bridge) walks DNS, routing, identity and authorization on one storage request; neither is repeated here. The [AWS deployment module](#/module/dbxfe-aws) answers the same questions for AWS. This lesson adds what is specific to Google Cloud: the resource hierarchy, service accounts and bucket IAM, one regional subnet, Cloud NAT, Private Google Access, firewall rules and Private Service Connect. Nothing transfers by renaming.

<!-- section:dbxfe-gcp-l01-placement -->

Google Cloud nests resources: an organization at the root, folders beneath it, projects inside those, and VMs or buckets inside projects. IAM policies and organization policies set higher up reach the projects below, so a folder's constraint can refuse what a project owner's role allows.

A classic workspace is created in the Databricks account (console: accounts.gcp.databricks.com) and names one project, where Databricks creates its Compute Engine VMs and two workspace storage buckets, and by default a VPC. A customer-managed VPC is chosen at creation, may sit in another project named in the network configuration, and cannot be adopted by an existing workspace later. A serverless workspace is created with only a name, a region and compute mode SERVERLESS; it names no project and no network, and its compute and default storage are Databricks-managed.

| Placed in | Classic workspace | Serverless workspace |
|---|---|---|
| Databricks account | Workspace object, control plane | Workspace object, control plane |
| Cinderline's projects | VMs, workspace buckets, VPC | Nothing |
| Unity Catalog | Grants, credentials, locations | Grants, credentials, locations |

<!-- section:dbxfe-gcp-l01-identities -->

A Google service account is an identity for software, owned by the project that created it; its email is built from that project's ID, so the email names the owner. The provisioning account is Cinderline's (`dbx-provisioner@cl-admin-tools.iam.gserviceaccount.com`), an account admin in the Databricks account console, and its custom Workspace Creator role lists what creation touches: roles, service accounts, the project's IAM policy, networks and firewall rules. The workspace service account has the form db-<workspace-id>@prod-gcp-<region>.iam.gserviceaccount.com and lives in a Databricks project.

For data, a Unity Catalog storage credential on Google Cloud makes Databricks create a managed service account and return its email. Cloud Storage knows nothing about catalog grants: the bucket's administrator binds that email to roles, and Databricks' guide binds Storage Object Admin and Storage Legacy Bucket Reader. An external location pairs a gs:// path with the credential, and catalog privileges decide who may use it. With uniform bucket-level access, only bucket-level or higher IAM policies decide.

The older pattern gives a classic cluster its own Google service account for Cloud Storage and BigQuery; every workload on that cluster then reads as that account, and the catalog's grants are not the gate.

<!-- section:dbxfe-gcp-l01-network -->

A customer-managed VPC is registered as a network configuration naming the VPC's project, the VPC and one subnet in the workspace region. Compute Engine nodes take addresses from that subnet, whose netmask falls between /29 and /9 and which no other workspace or resource may share; one VPC can still host several workspaces. The pod and service ranges of the older GKE-based design are no longer supported.

Nodes open outbound connections to the secure cluster connectivity relay; without back-end PSC that needs Cloud NAT or a similar appliance. Private Google Access, set on the subnet in Databricks' examples, lets VMs without external addresses reach Google APIs such as Cloud Storage.

Firewall rules belong to the whole network: the lowest priority number decides, a deny wins a tie, and a rule without targets applies to every VM. Workspace creation may create rules; which rules Databricks requires stays unknown here until verified on the customer-managed VPC page.

<!-- section:dbxfe-gcp-l01-private -->

Back-end PSC keeps node-to-control-plane traffic private with two endpoints in your VPC, for the relay and the REST API. Each is a forwarding rule targeting a Databricks service attachment, registered in the Databricks account by project, endpoint name and region, and listed in the network configuration as dataplane_relay and rest_api. Databricks' reference template adds a private Cloud DNS zone for gcp.databricks.com, visible to the VPC, answering the workspace URL, its dp- variant and tunnel.<region>.gcp.databricks.com, and creates no Cloud NAT.

Front-end PSC puts an endpoint in a transit VPC for users reaching the web application, REST API and Databricks Connect. A workspace using any PSC scenario is created with private access settings: ACCOUNT level admits any endpoint registered in the Databricks account, ENDPOINT level only the listed ones, and public access defaults to enabled on Google Cloud. Databricks' reference architecture requires a customer-managed VPC for PSC.

<!-- section:dbxfe-gcp-l01-serverless -->

Serverless compute removes Cinderline's VPC, NAT, firewall and workspace-bucket rows; catalog grants and bucket roles stay. The open question is private access from serverless compute to Cinderline's private sources, such as a Cloud SQL instance on a private address. The Terraform provider's documentation (v1.133.0) says network connectivity configuration binding is available for AWS and Azure only; the Python SDK (v0.141.0) already models a gcp_endpoint on private endpoint rules; network policies list Google Cloud Storage as a destination type. A schema field is not availability. Until the Databricks page for Google Cloud and the account team confirm region, tier and release status in writing, the design note says unknown, and private sources stay on classic compute.

<!-- section:dbxfe-gcp-l01-differs -->

Ask each cloud the same questions and source each answer separately.

| Question | Google Cloud | AWS | Azure |
|---|---|---|---|
| What the workspace names | A project | Credential role, storage configuration | Itself an Azure resource |
| Compute network | One regional subnet | Two subnets in two zones | Two delegated subnets |
| Traffic filter | Network firewall rules | Security groups | Network security groups |
| Storage identity | Databricks-managed service account | IAM role with trust policy | Access connector identity |
| Classic private link | PSC endpoints, private zone | PrivateLink endpoints | Private endpoints |
| Public access default | Enabled | Disabled | Set on the workspace resource |
| Serverless NCC binding | Unknown until verified | Public Preview | Available |

AWS and Azure columns are contrast only, from provider documentation; their own modules own those answers. Never fill a Google Cloud cell from another column.

<!-- section:dbxfe-gcp-l01-example -->

The nightly job reads the external table quality.raw.inspections on gs://cl-quality-raw/inspections/ (synthetic records).

**Monday: a refusal.** The run fails with STORAGE_DENIED (fictional text) naming `uc-cred-quality@example-dbx-project.iam.gserviceaccount.com` and storage.objects.get. Naming the credential's account means Unity Catalog had already allowed sp-quality-nightly. DESCRIBE STORAGE CREDENTIAL confirms the email; the bucket's policy has no binding for it, because the binding went on gs://cl-quality-staging, and Policy Troubleshooter shows nothing inherited. The data platform team binds the roles on the right bucket, the job reruns as the same principal, and the evidence row records it all.

**Tuesday: a timeout.** After back-end PSC is enabled, cluster starts time out and no error names anyone. From the node subnet, tunnel.us-east4.gcp.databricks.com answers a public address: the private zone is visible to cl-vpc-staging only. With cl-vpc-dbx added, the name answers 10.20.8.5 and relay-pe shows ACCEPTED, yet starts still fail: a new block-internet rule denies all egress at priority 900, before the allow at 1000. Renumbering the allow fixes it; the row records both faults.

<!-- section:dbxfe-gcp-l01-task -->

Change the case. The serverless workspace cinderline-gcp-sls runs a SQL warehouse query on an external table in supplier Ardent Castings' bucket, gs://ardent-parts-feed, which lives in Ardent's own organization, and a lookup against Cinderline's Cloud SQL instance on a private address in cl-vpc-dbx. The first query fails at once with a storage error naming a service account; the lookup times out. Write both diagnoses in order, name the owner of each fix, and list what stays unknown. Provision nothing.

<!-- section:dbxfe-gcp-l01-solution -->

**Storage error: a refusal, so read it.** It names the credential's service account and a Google permission, so the catalog already agreed. The binding must exist on Ardent's bucket, granted by Ardent's administrator under Ardent's organization policies; Cinderline cannot grant it. Evidence: the credential's email and Ardent's bucket policy for it. Whether Ardent's policies admit an outside member is unknown until Ardent answers.

**Lookup timeout: no refusal.** The query ran on serverless compute, which uses no Cinderline subnet, NAT or firewall, so those rows are not the suspects. The question is whether serverless compute can reach a private address in cl-vpc-dbx at all on Google Cloud: the provider documentation lists NCC binding for AWS and Azure only, the SDK models Google Cloud endpoint rules, so it is unknown until verified. The lookup stays on a classic job in cl-vpc-dbx, and the open question goes to its owner, the Databricks account team.

<!-- section:dbxfe-gcp-l01-limits -->

Common mistakes: copying an AWS or Azure answer into a Google Cloud cell; reading a schema field or a Terraform example as availability; granting broad project roles to fix a bucket-level denial; opening ingress rules for an outbound problem; recreating a storage credential without re-binding its new email. This lesson does not state the required firewall rules, whether Private Google Access is mandatory, regional PSC service attachments, tier requirements or the default VM service account: each stays unknown until verified for Cinderline's region. Nothing was provisioned or tested in a cloud.

<!-- section:dbxfe-gcp-l01-sources -->

Read in full for this lesson: the Databricks Terraform provider's Google Cloud guides and resource pages (v1.133.0), the Databricks Python SDK's provisioning, catalog and settings modules (v0.141.0), Databricks' Security Reference Architecture files for Google Cloud, and Google's API discovery documents for Compute Engine, Resource Manager, IAM, Cloud Storage, Organization Policy, Policy Troubleshooter and Cloud DNS. The Databricks documentation pages for Google Cloud could not be fetched or searched from this build; they are listed for verification, and no detail rests on them alone.

<!-- section:dbxfe-gcp-l01-links -->

[Draw the cloud and trust boundaries](#/lesson/dbxfe-m06-l03) carries the trust-boundary idea. [Cloud responsibilities and request paths](#/lesson/dbxfe-cloud-bridge) is the one-request walk assumed here. [Unity Catalog names and basic access](#/lesson/dbxfe-m06-l01) owns the privilege model the denied sequence checks first. The [AWS deployment module](#/module/dbxfe-aws) and the Azure deployment module answer the same questions from their own sources; the three-cloud diagnosis lab compares them.

<!-- section:dbxfe-gcp-l01-revisit -->

Answer the checks below, then redraw Cinderline's deployment from memory: the organization, both folders, three projects, the Databricks account, both compute planes, every service account with its owning project, and the evidence you would capture at each boundary, with the unknown cells still unknown.
