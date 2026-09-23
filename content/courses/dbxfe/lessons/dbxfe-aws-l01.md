<!-- section:dbxfe-aws-l01-outcome -->

After this lesson you can draw Cinderline's AWS deployment as it is operated: the Databricks account and control plane on one side, Cinderline's AWS account with its VPC, buckets, IAM roles and KMS keys on the other, and two compute planes that cross between them differently. You can trace one query across its trust boundaries and run two ordered diagnoses: one for a refused request, one for a request that never arrived. Nothing here provisions a resource; every feature named needs region, workspace type, tier and entitlement verified first.
<!-- section:dbxfe-aws-l01-start -->

Bring the platform map: account, workspace, catalog, compute and storage as separate responsibilities. Two retained lessons already teach the cloud-general ideas and are not repeated here. [Draw the cloud and trust boundaries](#/lesson/dbxfe-m06-l03) explains why a trust boundary changes who operates a resource. [Cloud responsibilities and request paths](#/lesson/dbxfe-cloud-bridge) walks DNS, routing, identity and authorization on one S3 request. This lesson adds what is specific to AWS: the customer-managed VPC, IAM roles and instance profiles, S3 bucket and KMS key policies, PrivateLink and the serverless connectivity constructs. Azure and Google Cloud have their own modules; nothing transfers by renaming.

<!-- section:dbxfe-aws-l01-planes -->

Cinderline has two accounts. The **Databricks account** holds its workspaces and the control plane (web application, jobs service, notebook and query metadata), operated by Databricks. Cinderline's **AWS account** holds its VPC, S3 buckets, IAM roles and KMS keys. A **classic workspace** provisions compute and a workspace storage bucket inside Cinderline's AWS account through a cross-account IAM role. A **serverless workspace** arrives with serverless compute and default storage in the Databricks account, same region, no VPC to hand over. Account admins create workspaces; workspace admins own identities and settings inside one.

Follow one query: an analyst runs `SELECT` on `quality.accepted.inspections`. The **author path** carries the browser to the workspace URL. The **control path** carries the command to compute: to a cluster in Cinderline's VPC through the relay the cluster dialled out to, or to a serverless warehouse over the cloud backbone. The **execution path** asks Unity Catalog for `USE CATALOG`, `USE SCHEMA` and `SELECT` before any file is read. The **storage path** reaches S3 with an identity. On classic, Cinderline's subnets, routes, security groups and DNS sit on the last two paths; on serverless, none do.

<!-- section:dbxfe-aws-l01-classic -->

A classic workspace takes a **customer-managed VPC** at creation; the documentation asks for at least two subnets and one security group and states network ACL and DNS requirements. **Secure cluster connectivity** means nodes get no public IP and need no inbound port: each node opens an outbound connection to the control plane's relay. A launch therefore depends only on the outbound side: a route from the subnet to a NAT gateway or interface endpoints, DNS answers for the workspace and relay hostnames, and outbound security group rules and network ACLs. Inbound rules change nothing.

**Egress** is where classic deployments quietly break, because every dependency is an outbound connection: the control plane, S3 (ideally via a gateway endpoint), the regional AWS services the documentation lists, any package index, any external source. The open shape routes everything to a NAT gateway; the restricted shape replaces that route with an egress firewall allowlist plus VPC endpoints. A `%pip install` that times out while S3 reads succeed is an allowlist gap, not a denial. Keep a ledger of allowlist entries with reason and verification date.

<!-- section:dbxfe-aws-l01-storage -->

On classic compute without Unity Catalog, S3 trust rides on the instance. An **instance profile** is an IAM role attached to the cluster's EC2 instances; admins create it in AWS, register it in the workspace and decide who may launch compute with it. A `GetObject` call is judged by three policies in turn: the role's policy, the bucket policy, and, for SSE-KMS objects, the KMS key policy. An `AccessDenied` naming KMS after S3 allowed the read is the key policy missing the role.

With Unity Catalog, the identity moves off the cluster. A **storage credential** wraps an IAM role that Databricks assumes; the documentation requires that role to live in the bucket's AWS account. An **external location** binds a path such as `s3://cinderline-inspections/accepted/` to a credential. A read is checked twice. First the catalog:

```sql
-- Synthetic teaching example; not executed.
GRANT USE CATALOG ON CATALOG quality TO `job-nightly`;
GRANT USE SCHEMA ON SCHEMA quality.accepted TO `job-nightly`;
GRANT SELECT ON TABLE quality.accepted.inspections TO `job-nightly`;
```

A missing grant returns `PERMISSION_DENIED` naming the principal and privilege, with no AWS call made. If all three hold, Databricks assumes the credential's role and S3 evaluates the role and bucket policies; a refusal here is an `AccessDenied` from AWS. Serverless compute has no instance to carry a role, so the credential path is its only storage path.

**Keys.** Databricks documents two customer-managed key use cases, managed services and workspace storage, on the Enterprise tier; a data bucket's own SSE-KMS key is a third matter whose policy must admit every reading identity, including the credential's role.
<!-- section:dbxfe-aws-l01-serverless -->

The serverless compute plane runs in the Databricks account and Databricks operates it, so Cinderline cannot place it in a subnet. Its lever is a **network connectivity configuration** (NCC): an account-level, regional object attached to workspaces, carrying private endpoint rules to AWS-managed services or to a VPC endpoint service Cinderline exposes in front of a resource such as an RDS database, which the AWS side must accept. Same-region S3 is reached through a Databricks-side VPC endpoint, and a bucket policy condition on `aws:VpceOrgPaths` can admit only Databricks serverless compute. Outbound restriction is separate: **serverless egress control** uses network policies that define allowed destinations and run enforced or in dry-run with logging; it requires the Enterprise tier and was announced as Public Preview on AWS in January 2025, so its status for Cinderline's region is a verification item. Name what differs from Azure rather than relabelling: no VNet injection, no managed identity; the constructs are NCCs, VPC endpoint services and IAM roles.

<!-- section:dbxfe-aws-l01-private -->

The documentation names three private connectivity types, each configured separately. **Inbound (front-end)** carries users to the workspace web application and REST APIs through a VPC interface endpoint, referenced by a private access settings object that also decides whether public access stays allowed. **Classic (back-end)** carries classic compute to the control plane's APIs and relay through interface endpoints inside the customer-managed VPC, which it requires. **Outbound (serverless)** carries the serverless plane to Cinderline's resources through NCC rules. One rule joins all three: the hostname must resolve, from the source network, to the endpoint's private address. Enabling back-end changes nothing for browsers.

<!-- section:dbxfe-aws-l01-example -->

The nightly job runs as service principal `job-nightly` on a serverless warehouse and reads `quality.accepted.inspections`, an external table under SSE-KMS. Two failures, one table.

| Evidence | Case A: denied | Case B: unreachable |
|---|---|---|
| Error text | `PERMISSION_DENIED: job-nightly lacks USE SCHEMA on quality.accepted` | Bootstrap timeout after a route change (classic cluster) |
| Service reply | Yes, from the catalog | None |
| Acting principal | `job-nightly`, not the interactive author | Not yet relevant |
| First investigation | `SHOW GRANTS` on catalog, schema and table | DNS, route table, security group outbound from the subnet |

Case A stops at the catalog: grant `USE SCHEMA` on `quality.accepted` to `job-nightly`, then rerun as that principal. An S3 `AccessDenied` instead would mean the catalog had agreed and the evidence lives in the credential's role, the bucket policy and then the key policy. Case B has no refusal to read: the subnet lost its outbound route, so DNS still answers and the security group still allows while the node never reaches the relay. Restore the route and retest from the same subnet. Neither case justifies a blanket grant or an inbound rule.

<!-- section:dbxfe-aws-l01-task -->

Cinderline moves the nightly job to a serverless warehouse in a second workspace in the same region. The source is now an SSE-KMS bucket in a supplier's AWS account, and a lookup table sits in an RDS database on a private IP in Cinderline's VPC. Security has switched the serverless egress policy to enforced. Write, in order, what must exist on the AWS side and the Databricks side for both sources, how you would tell a denial from an unreachable request here, and what you would mark unknown before the review.

<!-- section:dbxfe-aws-l01-solution -->

AWS side: a role in the supplier's account with the documented trust policy, a supplier bucket policy admitting it for the prefix, a supplier key policy granting it `kms:Decrypt`; in Cinderline's account, a VPC endpoint service in front of the RDS database and acceptance of the private endpoint connection. Databricks side: a storage credential pointing at the supplier's role ARN, an external location for the prefix, the three catalog grants for `job-nightly`, an NCC attached to the new workspace with a private endpoint rule to that endpoint service, and the egress policy reviewed against both sources.

Telling the failures apart: `PERMISSION_DENIED` is the catalog; `AccessDenied` naming S3 is the supplier's role or bucket policy; `AccessDenied` naming KMS is the supplier's key policy; a timeout to RDS is the NCC rule's state, the AWS-side acceptance, or the egress policy's log. Unknown until verified: regional availability of private endpoint rules and egress control, workspace type and tier, the supplier's consent, and networking charges. This list provisions nothing.
<!-- section:dbxfe-aws-l01-limits -->

This lesson is a schematic. It certifies no network design; no route, role, endpoint, key or workspace was created or tested. Exact subnet, DNS, network ACL and port requirements, endpoint service names, trust-policy templates and key policy principals live on the current pages and change. Serverless egress control, private endpoint rules and customer-managed keys carry tier, region or preview conditions. An admin's working interactive read proves nothing about a job's principal. An AWS diagram is not an Azure or Google Cloud diagram with new labels.

<!-- section:dbxfe-aws-l01-sources -->

The Databricks on AWS pages for the high-level architecture, workspace creation, classic and serverless networking, the customer-managed VPC, PrivateLink, Unity Catalog cloud storage, instance profiles, encryption keys and serverless egress control were confirmed by search-result title and snippet on 23 September 2026; their bodies were not fetched in this build because the sandbox blocks the documentation host, and each source record says so. Documented mechanisms, original guidance and fictional Cinderline records are labelled separately.

<!-- section:dbxfe-aws-l01-links -->

[Draw the cloud and trust boundaries](#/lesson/dbxfe-m06-l03) carries the trust-boundary idea and the specialist hand-off. [Cloud responsibilities and request paths](#/lesson/dbxfe-cloud-bridge) is the one-request DNS, route and policy walk this lesson assumes. [Unity Catalog names and access](#/lesson/dbxfe-m06-l01) owns the privilege model the denied-request sequence checks first. The Azure and Google Cloud modules answer the same questions with their own constructs.

<!-- section:dbxfe-aws-l01-revisit -->

Work the two diagnostic sequences on paper with the changed case, then review the cards. Opening a section, revealing the solution or reading the checklist records no completion; mark completion only when you choose, and keep assessment evidence separate from reading.
