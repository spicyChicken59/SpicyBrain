# Case sheet — Lab L15 three-cloud diagnosis

Three separate fictional deployments of Cinderline Components, one per cloud. Every table here is a text
diagram of an authored case: a diagram proves nothing is deployed. Names, addresses, identifiers and error
texts are invented. Read one case at a time; the three do not share network objects, and a control of one
cloud never appears in another cloud's case. Only the Databricks-side controls `run-as` and `uc-grants`
and the evidence items `error-record`, `job-run-as-setting` and `show-grants-output` appear in all three.

## AWS case — a nightly read refused at the key, and classic clusters that stopped starting

*Fictional teaching case for Cinderline Components. Names, addresses, account and project identifiers and every error text are invented; nothing was deployed or observed. Hostnames ending in .example stand in for the regional names on the current AWS pages; 111122223333 is a placeholder account ID.*

### Deployment

| Item | Value |
|---|---|
| Workspace | cinderline-prod, on a customer-managed VPC with back-end PrivateLink; one serverless SQL warehouse and classic job clusters |
| Network | vpc-cinderline-dbx (10.0.0.0/16); compute subnets subnet-compute-a (10.0.32.0/20) and subnet-compute-b (10.0.48.0/20); interface endpoints in subnet-endpoints (10.0.8.0/24): vpce-relay 10.0.8.21 and vpce-rest 10.0.8.22 |
| Storage | S3 bucket cinderline-inspections, objects encrypted with SSE-KMS under alias/cinderline-lake |
| Unity Catalog | external location s3://cinderline-inspections/accepted/ through storage credential cinderline-lake-cred; table quality.accepted.inspections |

### Identities

| Identity | Kind | Member of | Acts |
|---|---|---|---|
| `ana@cinderline.example` | Databricks user from the identity provider | quality-analysts | In her own notebooks; never as a scheduled job |
| `job-nightly` | Databricks service principal | — | As the run-as principal of job quality_nightly |
| `arn:aws:iam::111122223333:role/cinderline-lake-cred-role` | IAM role wrapped by storage credential cinderline-lake-cred | — | On the storage path of Unity Catalog reads; Databricks assumes it |
| `arn:aws:iam::111122223333:role/cinderline-cluster-profile` | IAM role of instance profile cinderline-cluster-profile | — | On the older classic interactive cluster legacy-interactive, which has no Unity Catalog |

### Request path

| Path | Hop | Identity | Controls in order |
|---|---|---|---|
| Author | Ana's browser to the workspace web application | ana@cinderline.example after single sign-on | not examined in this case |
| Control (`control-classic`) | Classic node in subnet-compute-a to the secure cluster connectivity relay, through interface endpoint vpce-relay | None that this case examines: a timeout here names no principal | `route53-private-hosted-zone` → `vpc-route-table` → `compute-security-group` → `endpoint-security-group` → `relay-interface-endpoint` |
| Execution (`execution`) | Job quality_nightly on the serverless SQL warehouse asks Unity Catalog | The job's run-as principal | `run-as` → `uc-grants` |
| Storage (`storage-serverless`) | Serverless compute to s3://cinderline-inspections/accepted/ | The storage credential's IAM role | `storage-credential-iam-role` → `credential-role-policy` → `s3-bucket-policy` → `kms-key-policy` |
| Storage (legacy) (`storage-classic-legacy`) | Classic cluster legacy-interactive to the same prefix, outside Unity Catalog | The instance profile's IAM role | `instance-profile` → `s3-bucket-policy` → `kms-key-policy` |

### Controls and their authored configuration

| Control | Layer | Owner | Configuration |
|---|---|---|---|
| `route53-private-hosted-zone`: Route 53 private hosted zone phz-dbx-relay and the VPCs associated with it | name-resolution | Cinderline network team | Answers privately in: `vpc-cinderline-dbx`. Records: `relay-endpoint.example` → 10.0.8.21 (vpce-relay); `rest-endpoint.example` → 10.0.8.22 (vpce-rest). A VPC that is not associated with the zone gets the public answer for these names. |
| `vpc-route-table`: Route table rtb-compute on the compute subnets | reachability | Cinderline network team | Associated with `subnet-compute-a`, `subnet-compute-b`. Routes: 10.0.0.0/16 → local. No route to the internet: control traffic is meant to use the interface endpoints. |
| `compute-security-group`: Security group sg-dbx-compute on the cluster nodes (outbound rules) | reachability | Cinderline network team | Allow rules only, egress: allow 0.0.0.0/0 all ports. |
| `endpoint-security-group`: Security group sg-dbx-endpoints on vpce-relay and vpce-rest (inbound rules) | reachability | Cinderline network team | Allow rules only, ingress: allow 10.0.16.0/20 port 443 (written for the compute range used before Monday). Port 443 alone is a simplification; the ports an endpoint needs are listed on the current page. |
| `relay-interface-endpoint`: Interface endpoint vpce-relay, registered in the workspace's network configuration | reachability | Cinderline network team and the Databricks account admin | State available; healthy state: available. Registered in the network configuration. |
| `run-as`: Run-as principal in the job settings | identity | The job's owner | job `quality_nightly` runs as `job-nightly`. Set to the service principal when the job was scheduled. |
| `uc-grants`: Unity Catalog privileges of the acting principal | authorization | The owners of the catalog, schema and table | Groups: `quality-analysts`: ana@cinderline.example. Grants: `job-nightly` USE CATALOG on `quality`; `job-nightly` USE SCHEMA on `quality.accepted`; `job-nightly` SELECT on `quality.accepted.inspections`; `quality-analysts` USE CATALOG on `quality`; `quality-analysts` USE SCHEMA on `quality.accepted`; `quality-analysts` SELECT on `quality.accepted.inspections`. No other grant exists. |
| `storage-credential-iam-role`: Storage credential cinderline-lake-cred and the IAM role it wraps | identity | Metastore admin (credential) and Cinderline cloud team (role) | Storage requests on this path act as `arn:aws:iam::111122223333:role/cinderline-lake-cred-role` (credential `cinderline-lake-cred`; externalLocation `s3://cinderline-inspections/accepted/`). |
| `credential-role-policy`: Permissions policy of cinderline-lake-cred-role | authorization | Cinderline cloud team | A read needs any of s3:GetObject on `arn:aws:s3:::cinderline-inspections/accepted/*` for the path's storage identity. Entries: `arn:aws:iam::111122223333:role/cinderline-lake-cred-role`: s3:GetObject, s3:PutObject, s3:DeleteObject on `arn:aws:s3:::cinderline-inspections/accepted/*`; `arn:aws:iam::111122223333:role/cinderline-lake-cred-role`: s3:ListBucket on `arn:aws:s3:::cinderline-inspections`. |
| `s3-bucket-policy`: Bucket policy of cinderline-inspections | authorization | Cinderline cloud team | Denies every principal that is not listed below. A read needs any of s3:GetObject on `arn:aws:s3:::cinderline-inspections/accepted/*` for the path's storage identity. Entries: `arn:aws:iam::111122223333:role/cinderline-lake-cred-role`: s3:GetObject, s3:PutObject, s3:DeleteObject on `arn:aws:s3:::cinderline-inspections/accepted/*`; `arn:aws:iam::111122223333:role/cinderline-cluster-profile`: s3:GetObject on `arn:aws:s3:::cinderline-inspections/accepted/*`. |
| `kms-key-policy`: Key policy of alias/cinderline-lake | authorization | Cinderline security team (key owner) | No statement delegates to IAM policies, so only the roles listed may use the key. A read needs any of kms:Decrypt on `alias/cinderline-lake` for the path's storage identity. Entries: `arn:aws:iam::111122223333:role/cinderline-key-admins`: kms:DescribeKey, kms:EnableKeyRotation, kms:ScheduleKeyDeletion on `alias/cinderline-lake`; `arn:aws:iam::111122223333:role/cinderline-cluster-profile`: kms:Decrypt, kms:GenerateDataKey on `alias/cinderline-lake`. |
| `instance-profile`: Instance profile cinderline-cluster-profile on legacy-interactive | identity | Workspace admin (registration) and Cinderline cloud team (role) | Storage requests on this path act as `arn:aws:iam::111122223333:role/cinderline-cluster-profile` (instanceProfile `cinderline-cluster-profile`; attachedTo `Classic interactive cluster legacy-interactive, without Unity Catalog`). |

### Evidence you can collect

| Evidence | For control | Capture | Where | Does not prove |
|---|---|---|---|---|
| `error-record` | any symptom | The exact error or symptom text, its time, the run or cluster ID, and which service answered (or that none did) | The job run or cluster event log | Which layer is at fault until the service that answered, if any, has been named |
| `job-run-as-setting` | `run-as` | The job's run-as principal as its settings show it | Job settings | That the principal holds any privilege, or anything about the network |
| `show-grants-output` | `uc-grants` | SHOW GRANTS on the catalog, the schema and the table, read for the acting principal and its groups | Unity Catalog | Anything about storage permissions or reachability |
| `credential-role-arn` | `storage-credential-iam-role` | The storage credential's IAM role ARN and account, and the external location that resolved for the path | Unity Catalog storage credential and external location | That any policy admits the role on the prefix |
| `role-permissions-policy` | `credential-role-policy` | The role's permissions policy statements for the bucket and prefix | IAM role cinderline-lake-cred-role | What the bucket policy or the key policy say |
| `bucket-policy-statements` | `s3-bucket-policy` | The bucket policy's statements for the exact role ARN | Bucket cinderline-inspections | Whether the key policy lets the role decrypt |
| `kms-key-policy-statements` | `kms-key-policy` | The key policy statements and grants naming the exact role ARN, and the key's region and state | KMS key alias/cinderline-lake | Whether the network path to the key or the bucket exists |
| `instance-profile-role` | `instance-profile` | Which instance profile the cluster launched with, and its role ARN | Cluster configuration of legacy-interactive | Anything about reads that go through Unity Catalog |
| `relay-dns-answer` | `route53-private-hosted-zone` | The relay hostname's answer resolved from an instance in subnet-compute-a, with time | An instance in the compute subnet | That a route or security group admits the traffic |
| `hosted-zone-associations` | `route53-private-hosted-zone` | The private hosted zone's records and its associated VPCs | Private hosted zone phz-dbx-relay | What an instance actually received |
| `route-table-export` | `vpc-route-table` | The route table associated with the compute subnet | Route table rtb-compute | That a security group admits the flow |
| `compute-sg-outbound` | `compute-security-group` | Outbound rules of the nodes' security group | Security group sg-dbx-compute | What the endpoint's own security group admits |
| `endpoint-sg-inbound` | `endpoint-security-group` | Inbound rules of the endpoints' security group against the current compute ranges | Security group sg-dbx-endpoints | Endpoint registration or anything about permissions |
| `vpc-flow-log-rejects` | `endpoint-security-group` | VPC flow log REJECT records at the endpoint's network interface for the failure time | VPC flow logs | Which rule to change; only that packets were refused there |
| `endpoint-state-registration` | `relay-interface-endpoint` | The endpoint's state and its registration in the workspace's network configuration | VPC endpoint vpce-relay and the account console | That packets reach it |

### Symptoms

**AWS-D — The nightly job is refused after the catalog agreed** (denied). Observed (fictional text): “AccessDenied (KMS): the assumed role cinderline-lake-cred-role is not authorized to perform kms:Decrypt on alias/cinderline-lake”. The bucket's objects moved to SSE-KMS under alias/cinderline-lake last week. Ana still reads the same prefix from legacy-interactive without trouble. Unity Catalog raised no PERMISSION_DENIED.
Request: segments `execution`, `storage-serverless`; job `quality_nightly`, designPrincipal `job-nightly`, compute `serverless SQL warehouse`, table `quality.accepted.inspections`.

**AWS-U — Classic clusters stopped starting** (unreachable). Observed (fictional text): “Cluster start failed after a bootstrap timeout reaching the secure cluster connectivity relay; no service returned an error”. On Monday the compute subnets moved from 10.0.16.0/20 to 10.0.32.0/20 and 10.0.48.0/20. No job, grant or credential changed.
Request: segments `control-classic`; compute `classic job cluster`, sourceNetwork `vpc-cinderline-dbx`, sourceSubnet `subnet-compute-a`, sourceIp `10.0.33.17`, name `relay-endpoint.example`, expect `private`, port `443`.

### Open questions

| Row | Question | Why it is unknown |
|---|---|---|
| `aws-relay-endpoint-service` | The relay and REST API endpoint service names, and the ports each endpoint needs, for Cinderline's region | They are listed per region on the current PrivateLink page, which this lab does not reproduce |
| `aws-cmk-tier` | Whether Cinderline's tier and region permit customer-managed keys for managed services and workspace storage | The feature is gated by tier and its regional availability changes |

## Azure case — a 403 from storage after the catalog agreed, and a backfill that times out

*Fictional teaching case for Cinderline Components. Names, addresses, account and project identifiers and every error text are invented; nothing was deployed or observed. The managed identity's principal ID is written mi-ac-cinderline-uc for readability.*

### Deployment

| Item | Value |
|---|---|
| Workspace | dbw-cinderline, injected into vnet-cinderline-data (10.20.0.0/16): snet-dbw-host (10.20.0.0/24), snet-dbw-container (10.20.1.0/24), snet-pe (10.20.2.0/24); one serverless SQL warehouse and classic job clusters |
| Hub | vnet-cinderline-hub (10.10.0.0/16) with the hub firewall at 10.10.0.4 |
| Storage | ADLS Gen2 account stcinderlinelake with public network access disabled; private endpoint pe-lake-dfs (sub-resource dfs, 10.20.2.5) in snet-pe |
| Unity Catalog | access connector ac-cinderline-uc (Microsoft.Databricks/accessConnectors) with a system-assigned managed identity; storage credential cinderline_lake_cred; external location cinderline_quality on abfss://quality@stcinderlinelake.dfs.core.windows.net/accepted |
| Serverless | network connectivity configuration ncc-cinderline attached to the workspace, with a private endpoint rule to stcinderlinelake (dfs) |

### Identities

| Identity | Kind | Member of | Acts |
|---|---|---|---|
| `ana@cinderline.example` | Microsoft Entra user | grp-quality-analysts | In her own notebooks and queries |
| `sp-job-nightly` | Microsoft Entra application service principal, provisioned into the Databricks account | — | As the run-as principal of jobs quality_nightly and quality_backfill |
| `mi-ac-cinderline-uc` | System-assigned managed identity of access connector ac-cinderline-uc | — | On the storage path of Unity Catalog reads; it is not a Databricks principal |
| `grp-platform-admins` | Microsoft Entra group | — | Manages the storage account |

### Request path

| Path | Hop | Identity | Controls in order |
|---|---|---|---|
| Author | Ana's browser to the workspace URL after Microsoft Entra sign-in | ana@cinderline.example | not examined in this case |
| Control | Control plane to compute; classic nodes dial out to the relay | Not examined in this case | not examined in this case |
| Execution (`execution`) | Job on the serverless SQL warehouse or a classic job cluster asks Unity Catalog | The job's run-as principal | `run-as` → `uc-grants` |
| Storage (serverless) (`storage-serverless`) | Serverless compute to stcinderlinelake through the NCC's private endpoint rule | The access connector's managed identity | `ncc-private-endpoint-rule` → `access-connector-identity` → `storage-role-assignment` |
| Storage (classic) (`storage-classic`) | Classic node in snet-dbw-host to stcinderlinelake through pe-lake-dfs | The access connector's managed identity | `private-dns-zone-link` → `private-endpoint-connection` → `subnet-route-table` → `nsg-host-subnet` → `access-connector-identity` → `storage-role-assignment` |

### Controls and their authored configuration

| Control | Layer | Owner | Configuration |
|---|---|---|---|
| `run-as`: Run-as principal in the job settings | identity | The job's owner | job `quality_nightly` runs as `sp-job-nightly`; job `quality_backfill` runs as `sp-job-nightly`. Both jobs were set to the service principal when they were scheduled. |
| `uc-grants`: Unity Catalog privileges of the acting principal | authorization | The owners of the catalog, schema and table | Groups: `grp-quality-analysts`: ana@cinderline.example. Grants: `sp-job-nightly` USE CATALOG on `quality`; `sp-job-nightly` USE SCHEMA on `quality.accepted`; `sp-job-nightly` SELECT on `quality.accepted.inspections`; `grp-quality-analysts` USE CATALOG on `quality`; `grp-quality-analysts` USE SCHEMA on `quality.accepted`; `grp-quality-analysts` SELECT on `quality.accepted.inspections`. No other grant exists. |
| `ncc-private-endpoint-rule`: Private endpoint rule of network connectivity configuration ncc-cinderline to stcinderlinelake (dfs) | reachability | Databricks account admin (rule) and the storage owner (approval) | State ESTABLISHED; healthy state: ESTABLISHED. |
| `access-connector-identity`: Access connector ac-cinderline-uc and its managed identity, named by storage credential cinderline_lake_cred | identity | Metastore admin (credential) and Cinderline cloud team (connector) | Storage requests on this path act as `mi-ac-cinderline-uc` (accessConnector `ac-cinderline-uc`; storageCredential `cinderline_lake_cred`; externalLocation `abfss://quality@stcinderlinelake.dfs.core.windows.net/accepted`). |
| `storage-role-assignment`: Azure role assignments on storage account stcinderlinelake | authorization | Cinderline cloud team | A read needs any of Storage Blob Data Reader, Storage Blob Data Contributor on `stcinderlinelake` for the path's storage identity. Entries: `grp-platform-admins`: Owner on `stcinderlinelake` (A management role; it grants no data access through Entra); `sp-job-nightly`: Storage Blob Data Reader on `stcinderlinelake` (Added last week as an attempted fix). |
| `private-dns-zone-link`: Private DNS zone privatelink.dfs.core.windows.net and its virtual network links | name-resolution | Cinderline network team | Answers privately in: `vnet-cinderline-hub`. Records: `stcinderlinelake.dfs.core.windows.net` → 10.20.2.5 (pe-lake-dfs). Public DNS answers the account name with a CNAME into the privatelink zone; only a network that consults a linked zone gets the private address. |
| `private-endpoint-connection`: Private endpoint pe-lake-dfs and its connection state on stcinderlinelake | reachability | Storage owner (approval) and Cinderline network team (endpoint) | State Pending; healthy state: Approved. |
| `subnet-route-table`: Route table rt-dbw-egress on snet-dbw-host and snet-dbw-container | reachability | Cinderline network team | Associated with `snet-dbw-host`, `snet-dbw-container`. Routes: 10.20.0.0/16 → VnetLocal (system route for the VNet's address space); 0.0.0.0/0 → VirtualAppliance 10.10.0.4 (hub firewall). Service tag routes: AzureDatabricks → Internet. Other system routes are omitted; service tag routes are shown for reading and are not used by this case. |
| `nsg-host-subnet`: Network security group nsg-dbw on snet-dbw-host (outbound rules) | reachability | Cinderline network team | Priority rules, egress: AllowVnetOutBound priority 65000 allow VirtualNetwork (drawn as 10.20.0.0/16) all ports; AllowInternetOutBound priority 65001 allow Internet (drawn as 0.0.0.0/0) all ports; DenyAllOutBound priority 65500 deny 0.0.0.0/0 all ports. The default outbound rules only; rules added for an injected workspace are omitted. VirtualNetwork and Internet are Azure service tags, not address ranges; this sheet draws them as the CIDRs its walk evaluates. |

### Evidence you can collect

| Evidence | For control | Capture | Where | Does not prove |
|---|---|---|---|---|
| `error-record` | any symptom | The exact error or symptom text, its time, the run or cluster ID, and which service answered (or that none did) | The job run or cluster event log | Which layer is at fault until the service that answered, if any, has been named |
| `job-run-as-setting` | `run-as` | The job's run-as principal as its settings show it | Job settings | That the principal holds any privilege, or anything about the network |
| `show-grants-output` | `uc-grants` | SHOW GRANTS on the catalog, the schema and the table, read for the acting principal and its groups | Unity Catalog | Anything about storage permissions or reachability |
| `ncc-rule-state` | `ncc-private-endpoint-rule` | The NCC attached to the workspace and its private endpoint rule's state, with time | Account console, NCC ncc-cinderline | That the managed identity holds a data role |
| `connector-identity` | `access-connector-identity` | The storage credential's access connector resource ID and its managed identity's principal ID | Storage credential cinderline_lake_cred and access connector ac-cinderline-uc | Which roles that identity holds |
| `role-assignment-export` | `storage-role-assignment` | Role assignments on stcinderlinelake and its containers for the managed identity's principal ID, with scope | Storage account access control | Anything about network rules, DNS or catalog grants |
| `storage-dns-answer` | `private-dns-zone-link` | The storage name's answer resolved on the cluster itself, with time | A notebook on a cluster in snet-dbw-host | That the endpoint was approved |
| `zone-vnet-links` | `private-dns-zone-link` | The Private DNS zone's virtual network links | Private DNS zone privatelink.dfs.core.windows.net | What the firewall does with the traffic |
| `endpoint-connection-state` | `private-endpoint-connection` | The private endpoint connection's state on the storage account | Storage account networking | That a data role exists |
| `effective-routes` | `subnet-route-table` | The route table on snet-dbw-host, or a node network interface's effective routes | Route table rt-dbw-egress | What the NSG or firewall allow |
| `nsg-effective-rules` | `nsg-host-subnet` | The effective NSG rules for snet-dbw-host and the hub firewall log for the address and time | NSG nsg-dbw and the firewall log | Anything about permissions |

### Symptoms

**AZ-D — The nightly job gets a 403 from storage** (denied). Observed (fictional text): “HTTP 403 from storage account stcinderlinelake on a read of the accepted folder by the storage credential's identity; the error details name a missing permission, not the network. Unity Catalog raised no PERMISSION_DENIED”. A role-assignment cleanup ran on stcinderlinelake last month. Last week a colleague gave sp-job-nightly Storage Blob Data Reader on the account; the job still fails.
Request: segments `execution`, `storage-serverless`; job `quality_nightly`, designPrincipal `sp-job-nightly`, compute `serverless SQL warehouse`, table `quality.accepted.inspections`.

**AZ-U — The backfill on a classic job cluster times out** (unreachable). Observed (fictional text): “connect timed out: stcinderlinelake.dfs.core.windows.net:443 after retries; no service returned an error”. quality_backfill runs on a classic job cluster in snet-dbw-host. The storage account's public network access is disabled and pe-lake-dfs was created last week.
Request: segments `execution`, `storage-classic`; job `quality_backfill`, designPrincipal `sp-job-nightly`, compute `classic job cluster`, table `quality.accepted.inspections`, sourceNetwork `vnet-cinderline-data`, sourceSubnet `snet-dbw-host`, sourceIp `10.20.0.37`, name `stcinderlinelake.dfs.core.windows.net`, expect `private`, port `443`.

### Open questions

| Row | Question | Why it is unknown |
|---|---|---|
| `azure-private-network-gateway` | Whether the private network gateway that reaches a customer VNet from serverless is available to Cinderline's account and region | The module's sources describe it, and its availability has to be verified |
| `azure-ncc-limits` | The per-region limits on NCCs and private endpoint rules that apply to Cinderline | Limits exist per region and change; the current page was not read here |

## Google Cloud case — a refusal that names the wrong person, and a relay name that answers publicly

*Fictional teaching case for Cinderline Components. Names, addresses, account and project identifiers and every error text are invented; nothing was deployed or observed. The region us-east4 and the relay name follow the module's worked example.*

### Deployment

| Item | Value |
|---|---|
| Workspace | Classic workspace in project cl-dbx-prod (us-east4) with back-end Private Service Connect; classic job clusters |
| Network | Customer-managed VPC cl-vpc-dbx in host project cl-net-host; node subnet dbx-nodes-use4 (10.20.0.0/22); endpoint subnet dbx-psc-use4 (10.20.8.0/28) with relay-pe (10.20.8.2) and workspace-pe (10.20.8.3); users' transit network cl-vpc-transit. The Cloud NAT was removed when PSC was enabled |
| Storage | Buckets cl-quality-raw and cl-quality-curated |
| Unity Catalog | external location loc_quality_raw on gs://cl-quality-raw/inspections/ through storage credential cred_quality; table quality.raw.inspections |

### Identities

| Identity | Kind | Member of | Acts |
|---|---|---|---|
| `ana@cinderline.example` | Databricks user | quality-analysts | In her own notebooks; she created job quality_nightly |
| `sp-quality-nightly` | Databricks service principal | quality-jobs | As the run-as principal the design names for quality_nightly |
| `uc-cred-quality@example-dbx-project.iam.gserviceaccount.com` | Databricks-managed service account of storage credential cred_quality | — | On the storage path of Unity Catalog reads; Cloud Storage authorizes it by its bucket roles |
| `classic nodes` | Compute Engine VMs in dbx-nodes-use4 | — | Open the secure tunnel to the relay; their own service account is not examined here |

### Request path

| Path | Hop | Identity | Controls in order |
|---|---|---|---|
| Author | Ana's browser to the workspace URL | ana@cinderline.example; her identity does not travel with a job | not examined in this case |
| Control (`control-classic`) | Classic node in dbx-nodes-use4 to the secure cluster connectivity relay through relay-pe | None that this case examines: a timeout here names no principal | `cloud-dns-private-zone` → `psc-relay-endpoint` → `vpc-firewall-egress` |
| Execution (`execution`) | Job quality_nightly on a classic job cluster asks Unity Catalog | The job's run-as principal | `run-as` → `uc-grants` |
| Storage (`storage`) | Compute to gs://cl-quality-raw/inspections/ | The storage credential's service account | `credential-service-account` → `bucket-iam-binding` |

### Controls and their authored configuration

| Control | Layer | Owner | Configuration |
|---|---|---|---|
| `run-as`: Run-as principal in the job settings | identity | The job's owner | job `quality_nightly` runs as `ana@cinderline.example`. Ana created the job; its run-as setting was never changed from her. |
| `uc-grants`: Unity Catalog privileges of the acting principal | authorization | The owners of the catalog, schema and table | Groups: `quality-analysts`: ana@cinderline.example; `quality-jobs`: sp-quality-nightly. Grants: `quality-jobs` USE CATALOG on `quality`; `quality-jobs` USE SCHEMA on `quality.raw`; `quality-jobs` SELECT on `quality.raw.inspections`; `quality-analysts` USE CATALOG on `quality`; `quality-analysts` USE SCHEMA on `quality.accepted`; `quality-analysts` SELECT on `quality.accepted.inspections`. No other grant exists. |
| `credential-service-account`: Storage credential cred_quality and its Databricks-managed service account | identity | Metastore admin | Storage requests on this path act as `uc-cred-quality@example-dbx-project.iam.gserviceaccount.com` (credential `cred_quality`; externalLocation `loc_quality_raw on gs://cl-quality-raw/inspections/`). |
| `bucket-iam-binding`: IAM bindings on Cloud Storage buckets for the credential's service account | authorization | The buckets' administrator | A read needs any of roles/storage.objectViewer, roles/storage.objectAdmin on `cl-quality-raw` for the path's storage identity. Entries: `serviceAccount:uc-cred-quality@example-dbx-project.iam.gserviceaccount.com`: roles/storage.objectAdmin, roles/storage.legacyBucketReader on `cl-quality-curated`. |
| `cloud-dns-private-zone`: Cloud DNS private zone dbx-psc-zone (gcp.databricks.com.) and the networks it is visible to | name-resolution | Cinderline network team | Answers privately in: `cl-vpc-transit`. Records: `tunnel.us-east4.gcp.databricks.com` → 10.20.8.2 (relay-pe). A private zone answers only networks listed in its visibility; any other network gets the public answer. |
| `psc-relay-endpoint`: PSC endpoint relay-pe, registered as the network configuration's dataplane_relay | reachability | Cinderline network team and the Databricks account admin | State ACCEPTED; healthy state: ACCEPTED. |
| `vpc-firewall-egress`: Egress firewall rules of cl-vpc-dbx | reachability | Cinderline network team | Priority rules, egress: allow-psc-endpoints priority 1000 allow 10.20.8.0/28 port 443; block-internet priority 900 deny 0.0.0.0/0 all ports (Added by a colleague to stop internet traffic); deny-all-egress priority 65000 deny 0.0.0.0/0 all ports; implied allow egress priority 65535 allow 0.0.0.0/0 all ports. Firewall policies attached above the VPC are not part of this case. |

### Evidence you can collect

| Evidence | For control | Capture | Where | Does not prove |
|---|---|---|---|---|
| `error-record` | any symptom | The exact error or symptom text, its time, the run or cluster ID, and which service answered (or that none did) | The job run or cluster event log | Which layer is at fault until the service that answered, if any, has been named |
| `job-run-as-setting` | `run-as` | The job's run-as principal as its settings show it | Job settings | That the principal holds any privilege, or anything about the network |
| `show-grants-output` | `uc-grants` | SHOW GRANTS on the catalog, the schema and the table, read for the acting principal and its groups | Unity Catalog | Anything about storage permissions or reachability |
| `credential-sa-email` | `credential-service-account` | DESCRIBE STORAGE CREDENTIAL cred_quality: the service account email | Unity Catalog | Which bucket roles that email holds |
| `bucket-iam-policy` | `bucket-iam-binding` | The bucket's IAM policy, read for that email | Bucket cl-quality-raw | Policies inherited from the project, folder or organization |
| `policy-troubleshooter-result` | `bucket-iam-binding` | Policy Troubleshooter for that email, storage.objects.get and the bucket, with the inherited policies it consulted | Policy Troubleshooter | Anything about reachability |
| `relay-name-answer` | `cloud-dns-private-zone` | The relay name's answer from a VM in dbx-nodes-use4, with time | A VM or running cluster in the node subnet | That the endpoint is accepted or that a firewall rule admits the flow |
| `zone-visibility` | `cloud-dns-private-zone` | The managed zone's private visibility networks and its A records | Managed zone dbx-psc-zone | What a node actually received |
| `psc-connection-status` | `psc-relay-endpoint` | The forwarding rule's pscConnectionStatus | Forwarding rule relay-pe | That the name resolves to it |
| `firewall-rules-by-priority` | `vpc-firewall-egress` | Egress firewall rules for the node network sorted by priority, and any firewall policies attached above the VPC | VPC cl-vpc-dbx | Anything about permissions |

### Symptoms

**GCP-D — The nightly job is refused in someone else's name** (denied). Observed (fictional text): “PERMISSION_DENIED: User ana@cinderline.example does not have SELECT on table quality.raw.inspections”. Ana created quality_nightly. The design says the job acts as sp-quality-nightly, which holds its grants through the quality-jobs group.
Request: segments `execution`, `storage`; job `quality_nightly`, designPrincipal `sp-quality-nightly`, compute `classic job cluster`, table `quality.raw.inspections`.

**GCP-U — Cluster starts stall after back-end PSC was enabled** (unreachable). Observed (fictional text): “Cluster start stalled and failed; the node never opened its secure tunnel; no principal, permission or constraint appears in any error”. This week back-end Private Service Connect was enabled and the Cloud NAT removed. Zone dbx-psc-zone was created at the same time.
Request: segments `control-classic`; compute `classic job cluster`, sourceNetwork `cl-vpc-dbx`, sourceSubnet `dbx-nodes-use4`, sourceIp `10.20.1.9`, name `tunnel.us-east4.gcp.databricks.com`, expect `private`, port `443`.

### Open questions

| Row | Question | Why it is unknown |
|---|---|---|
| `gcp-serverless-private-connectivity` | Whether serverless compute can reach private resources in Cinderline's VPC on Google Cloud | The sources read for the module conflict: provider documentation lists the NCC binding for AWS and Azure only, while an SDK models a Google Cloud field; a field in a schema is not availability |
| `gcp-default-vm-service-account` | Which service account Databricks attaches to classic VMs by default, and what it may read | Not settled by the sources the module read |
| `gcp-required-firewall-rules` | The firewall rules, ports and address lists Databricks requires for a customer-managed VPC | They are on the customer-managed VPC page, which was not read for this case |
