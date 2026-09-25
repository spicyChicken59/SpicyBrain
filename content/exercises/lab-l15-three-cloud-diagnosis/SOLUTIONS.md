# Solutions — Lab L15 three-cloud request-path diagnosis

The reference answers are in `solutions/answers.json`; this page explains
them. Everything below is a walk over authored tables: a diagram proves
nothing is deployed, and no cloud or Databricks service was contacted.

## The six answers at a glance

| Symptom | Looks like | Classification | Broken control | Required evidence |
|---|---|---|---|---|
| AWS-D | a refusal after the catalog agreed | authorization | `kms-key-policy` | `error-record`, `job-run-as-setting`, `kms-key-policy-statements` |
| AWS-U | a bootstrap timeout | reachability | `endpoint-security-group` | `error-record`, `relay-dns-answer`, `endpoint-sg-inbound` |
| AZ-D | a 403 from storage | authorization | `storage-role-assignment` | `error-record`, `job-run-as-setting`, `connector-identity`, `role-assignment-export` |
| AZ-U | a connect timeout | name-resolution | `private-dns-zone-link` | `error-record`, `storage-dns-answer`, `zone-vnet-links` |
| GCP-D | a catalog refusal | identity | `run-as` | `error-record`, `job-run-as-setting` |
| GCP-U | a start that stalls | name-resolution | `cloud-dns-private-zone` | `error-record`, `relay-name-answer`, `zone-visibility` |

Three of the six are network failures, and all four classifications occur.
Each "broken control" is the first control on the request's path, in the
order the case sheet lists them, whose authored configuration fails.

## AWS

**AWS-D (authorization, `kms-key-policy`).** The walk, as `diagnose.py`
prints it: `run-as` passes (quality_nightly runs as job-nightly, as
designed); `uc-grants` passes (job-nightly holds USE CATALOG, USE SCHEMA and
SELECT); `storage-credential-iam-role` records that storage requests act as
`cinderline-lake-cred-role`; `credential-role-policy` and `s3-bucket-policy`
both give that role s3:GetObject on the prefix; `kms-key-policy` fails: no
statement gives the role kms:Decrypt, and the policy does not delegate to IAM
policies. The error said so: a refusal that names KMS means S3 had already
allowed the object operation. Ana's success on legacy-interactive proves
nothing about the job, because her read acts as the instance profile's role,
which the key policy does admit (`run_tests.py` walks that legacy path and it
passes). Evidence: the error record, the job's run-as setting, and the key
policy's statements for the exact role ARN; `show-grants-output` and
`credential-role-arn` are useful and allowed. Wrong fixes: a bucket policy
wildcard, an admin role on the credential, or granting SELECT to more
principals.

**AWS-U (reachability, `endpoint-security-group`).** No service answered, so
start with the name. `route53-private-hosted-zone` passes: the zone is
associated with vpc-cinderline-dbx and answers `relay-endpoint.example` with
10.0.8.21 (vpce-relay). `vpc-route-table` passes: 10.0.0.0/16 is local.
`compute-security-group` passes: the nodes may send anything out. The
endpoints' security group fails: its only inbound rule admits 10.0.16.0/20,
the range the subnets used before Monday, and the node at 10.0.33.17 is not in
it. A security group allows only what it lists. Evidence: the error record,
the relay name's answer from an instance in subnet-compute-a, and the
endpoint group's inbound rules; flow log REJECT records at the endpoint's
interface confirm it. Wrong fixes: any grant, a new NAT route, recreating the
endpoint.

## Azure

**AZ-D (authorization, `storage-role-assignment`).** Unity Catalog agreed
(`run-as` and `uc-grants` pass) and the serverless path's NCC rule is
ESTABLISHED, so the 403 comes from the storage chain. The storage credential
acts as the access connector's managed identity, and the role assignments on
stcinderlinelake name only grp-platform-admins (Owner, a management role) and
sp-job-nightly (the attempted fix). The managed identity lost its data role
in last month's cleanup. The colleague's fix changed nothing because the job
never reads storage with its own identity: application access and storage
access are separate chains. Evidence: the error record, the run-as setting,
the connector's managed identity, and the role assignments on the account for
that identity. Wrong fixes: a storage role for sp-job-nightly or for people,
ALL PRIVILEGES on the catalog, a DNS change.

**AZ-U (name-resolution, `private-dns-zone-link`).** `run-as` and
`uc-grants` pass, then the name fails: the Private DNS zone is linked to
vnet-cinderline-hub only, so on the cluster in vnet-cinderline-data the
account name answers with its public address. With public network access
disabled and the default route sent to the hub firewall, nothing answers and
the read times out. Evidence: the error record, the storage name's answer on
the cluster itself, and the zone's virtual network links;
`endpoint-connection-state` is worth capturing now, because it is the next
fault (see the stretch). Wrong fixes: a storage role, a grant, an inbound
rule.

## Google Cloud

**GCP-D (identity, `run-as`).** The refusal is real, but it names
ana@cinderline.example, and the design says the job acts as
sp-quality-nightly. The job's settings show it runs as Ana, who created it.
The first failing control is the run-as setting, so this is identity: the
wrong principal acted. Granting Ana SELECT on `quality.raw.inspections` would
make the error disappear and hand a person the job's access. Evidence: the
error record and the job's run-as setting; `show-grants-output` read for
sp-quality-nightly confirms the design principal already holds its grants.

**GCP-U (name-resolution, `cloud-dns-private-zone`).** The first control on
the control path is the zone, and it is visible only to cl-vpc-transit, so
from the node subnet in cl-vpc-dbx the relay name answers publicly. With the
Cloud NAT removed, a public answer leads nowhere. Evidence: the error record,
the relay name's answer from a VM in dbx-nodes-use4, and the zone's
visibility networks. Capture `psc-connection-status` and
`firewall-rules-by-priority` too: `block-internet` at priority 900 is waiting
behind this fault.

## Task 4 — seven open questions, all still open

Every row's status is `unknown until verified`, with the dated source or test
that would close it: the current PrivateLink page for the relay services, the
customer-managed keys page and a written tier confirmation, the Azure
serverless networking page and a written account-team answer for the private
network gateway, the current NCC limits, the Google Cloud serverless
networking page or a written answer for serverless private connectivity, a
read-only look at a running VM's attached service account, and the
customer-managed VPC page for the firewall rules. No row moves, because this
lab read no source.

## Stretch — the eleven scenarios

| Scenario | Change | New first failure |
|---|---|---|
| T-AWS-1 | security group admits the new ranges | none: the start passes |
| T-AWS-2 | zone association removed | `route53-private-hosted-zone`, name-resolution |
| T-AWS-3 | key policy admits the credential's role | none: the read passes |
| T-AZ-1 | zone linked to the data VNet | `private-endpoint-connection`, reachability (Pending) |
| T-AZ-2 | …and the endpoint approved | `storage-role-assignment`, authorization |
| T-AZ-3 | …and the managed identity's role restored | none: the read passes |
| T-AZ-4 | role restored, sp-job-nightly's role removed | none: the serverless read passes without it |
| T-GCP-1 | zone visible to cl-vpc-dbx | `vpc-firewall-egress`, reachability (900 deny beats 1000 allow) |
| T-GCP-2 | …and the allow renumbered to 800 | none: the start passes |
| T-GCP-3 | run-as set to sp-quality-nightly | `bucket-iam-binding`, authorization (binding on cl-quality-curated) |
| T-GCP-4 | …and the binding added on cl-quality-raw | none: the read passes |

T-GCP-1 answers the stretch question: the deny at 900 was always there, but
nobody could see it while the name pointed elsewhere. Fixing one fault
exposed the next, which is why an evidence record lists every fault found,
not only the last. AZ-U shows the same thing three times over.

## One wrong approach, and why it fails

**Relabelling a diagnosis from another cloud.** The AWS answer to a timeout
reads "the private hosted zone is not associated". Copied into the Azure and
Google Cloud cases, the classification is even right (name-resolution), yet
the answer fails, because the controls it names do not exist there. The
runner prints, among others:

```text
AZ-U: brokenControl route53-private-hosted-zone is not a control of the azure case (it belongs to: aws)
GCP-U: brokenControl private-dns-zone-link is not a control of the gcp case (it belongs to: azure)
GCP-U: evidence endpoint-sg-inbound is not evidence of the gcp case (it belongs to: aws)
gcp/gcp-serverless-private-connectivity: a source about azure never settles a gcp row
```

The fix on Azure is a virtual network link on a Private DNS zone; on Google
Cloud it is the visibility list of a Cloud DNS private zone. Same question,
different object, different owner.

**A grant for a timeout.** `fixtures/negative/wrong_layer.json` answers AWS-U
with `uc-grants` and AZ-U with `storage-role-assignment`. The first is not
even on the control path. The second is a real fault in the Azure case, on
the right path, yet still wrong: the name fails before any storage
authorization is reached, and its evidence is refused as permission evidence
for a name-resolution symptom.
