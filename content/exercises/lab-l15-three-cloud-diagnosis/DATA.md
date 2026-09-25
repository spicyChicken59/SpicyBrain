# Data dictionary and derivations — Lab L15

Every file in `fixtures/` is synthetic and authored for this lab. Cinderline
Components, its people, jobs, groups, networks, addresses, account and project
identifiers, keys, buckets and every error text are fictional; addresses use
private ranges and people use the reserved `example` domain; `111122223333` is
a placeholder AWS account ID; hostnames ending in `.example` stand in for the
regional names on the current AWS pages. The Azure storage name and the
Google Cloud relay name follow the worked examples of the Azure and Google
Cloud modules. No generator and no random seed are involved: the files are the
literal inputs, and `CASES.md` shows the same content as text tables.

The three cases are drawn from the diagnostic beats of the modules AWS
deployment and network boundaries, Azure deployment and network boundaries,
and Google Cloud deployment and network boundaries: each keeps its own cloud's
objects, and no network object is shared between cases.

## Case files (`fixtures/<cloud>.json`)

| Field | Contents |
|---|---|
| `deployment`, `identities`, `requestPath` | what the case sheet shows: the deployment, who acts on each hop, and each path with the segment it walks |
| `paths` | walkable segments, each an ordered list of control IDs |
| `controls` | `id`, `name`, `layer`, `side` (`databricks` or the cloud), `type`, `owner`, `object` and the authored `config` |
| `evidence` | the evidence catalogue: `id`, the `control` it proves (`null` for `error-record`), `capture`, `where`, `doesNotProve` |
| `symptoms` | two per case, `kind` `denied` or `unreachable`, a fictional `observed` text, `context`, and the `request` the walk replays |
| `unknowns` | open questions with the reason each is unknown |

Controls per case: AWS 12 (5 on the classic control path, 2 execution, 4
serverless storage, plus the legacy instance profile), Azure 9, Google Cloud 7.
Evidence items: AWS 15, Azure 11, Google Cloud 10. Open questions: 2, 2 and 3.

## The model's rules

The evaluator walks the controls of the request's segments in order (a control
listed in two segments is checked once) and stops at the first that fails.
The classification is the layer of that control's type.

| Type | Layer | Passes when |
|---|---|---|
| `run-as` | identity | the job's configured run-as principal equals the principal the design names; it then becomes the acting principal |
| `uc-grants` | authorization | the acting principal, directly or through a group, holds USE CATALOG on the catalog, USE SCHEMA on the schema and SELECT on the table (exact securables only; no inheritance in this model) |
| `credential` | identity | always; it records which identity storage requests on this path act as |
| `allow-list` | authorization | an entry names that storage identity, the required resource and at least one of the required actions or roles (`serviceAccount:` before an email is ignored) |
| `dns` | name-resolution | the asking network is one the zone serves and the zone holds the name; the answer is then the record's private address; otherwise the answer is public, which fails a request that expects private |
| `route` | reachability | the longest matching prefix for the answered address exists and does not drop traffic |
| `filter` | reachability | allow-only (a security group): any rule matches the flow; priority (an NSG or a VPC firewall rule): among matching rules the lowest priority number decides, and at equal priority a deny wins |
| `endpoint-state` | reachability | the state is one of the listed healthy states |

An ingress filter matches the request's source address; an egress filter
matches the answered destination. Every flow uses port 443.

Where the real services are richer, and the model deliberately is not: IAM
explicit denies, conditions and cross-account rules; KMS grants; key policies
that delegate to IAM; Azure network rules and resource instance rules; Google
Cloud policies inherited from project, folder and organization, and
organization policy constraints; network ACLs; firewall policies attached
above a VPC; the hub firewall's own rules; CNAME chains; propagation delays;
and the exact ports and names each cloud's current documentation lists.

## How each key was derived (by hand)

**`expected/walks.json`.**
AWS-D: segments execution then storage-serverless. run-as: quality_nightly →
job-nightly = design, pass. uc-grants: job-nightly holds all three, pass.
storage-credential-iam-role: records cinderline-lake-cred-role. The role
policy and the bucket policy both list that role with s3:GetObject on the
prefix, pass. The key policy lists only cinderline-key-admins (no
kms:Decrypt) and cinderline-cluster-profile, fail: six steps, the sixth
failing, authorization.
AWS-U: control-classic. Zone associated with vpc-cinderline-dbx and holding
the relay name, pass (10.0.8.21). 10.0.8.21 is inside 10.0.0.0/16 → local,
pass. Compute egress allows 0.0.0.0/0, pass. Endpoint ingress admits only
10.0.16.0/20; 10.0.33.17 lies in 10.0.32.0/20, fail: four steps,
reachability.
AZ-D: execution then storage-serverless. run-as and uc-grants pass as for
AWS-D. NCC rule ESTABLISHED, pass. Connector identity recorded. No role
assignment names mi-ac-cinderline-uc, fail: five steps, authorization.
AZ-U: execution then storage-classic. run-as (quality_backfill →
sp-job-nightly) and uc-grants pass. The zone serves vnet-cinderline-hub only
and the cluster asks from vnet-cinderline-data, so the answer is public, fail:
three steps, name-resolution.
GCP-D: execution then storage. run-as: quality_nightly → ana@cinderline.example,
design sp-quality-nightly, fail: one step, identity.
GCP-U: control-classic. The zone is visible to cl-vpc-transit only; the node
asks from cl-vpc-dbx, fail: one step, name-resolution.

**`expected/answers.json`.** Classification and broken control come from the
walks above. Required evidence is `error-record` for every symptom, plus the
run-as setting for every denied symptom (every module's denied sequence
confirms the acting principal first), plus the evidence that proves the
broken control: `kms-key-policy-statements`; `relay-dns-answer` (every
unreachable sequence starts with the name from the asking network) and
`endpoint-sg-inbound`; `connector-identity` and `role-assignment-export`;
`storage-dns-answer` and `zone-vnet-links`; for GCP-D the run-as setting
itself; `relay-name-answer` and `zone-visibility`. Every open question's
status is `unknown until verified` because no source is read in this lab.

**`expected/transfer.json`.** Each scenario's changes replace whole settings
of a fresh copy of the case. T-AWS-1: 10.0.33.17 is now inside 10.0.32.0/20,
and vpce-relay is available, so every step passes. T-AWS-2: the zone serves
no network, the name answers publicly, name-resolution. T-AWS-3: the key
policy lists the credential's role with kms:Decrypt, all pass. T-AZ-1: the
name answers 10.20.2.5, the endpoint is Pending, reachability. T-AZ-2: the
endpoint is Approved; 10.20.2.5 is inside 10.20.0.0/16 (the /16 beats the /0
default); AllowVnetOutBound at 65000 is the lowest matching rule; the
identity is recorded; no data role for it, authorization. T-AZ-3: the
identity holds Storage Blob Data Contributor, all pass. T-AZ-4: the same role
with sp-job-nightly's entry gone, the serverless read passes. T-GCP-1: the
name answers 10.20.8.2, the endpoint is ACCEPTED, the matching rules are
allow at 1000, deny at 900, deny at 65000 and allow at 65535; 900 is lowest,
deny, reachability. T-GCP-2: allow at 800 is now lowest, all pass. T-GCP-3:
run-as is the design principal; sp-quality-nightly holds its three
privileges through quality-jobs; the only binding for the service account is
on cl-quality-curated, authorization. T-GCP-4: a binding on cl-quality-raw
with roles/storage.objectViewer, all pass.

**`expected/negative.json`.** Each line follows the checker's order: per
symptom in ID order, the classification, then the broken control (not in this
case, else not on the path; then expected against given), then each cited
evidence item in the order cited (not in this case, else not on the path,
else the wrong family for the key's classification), then the required items
missing in alphabetical order; then the open questions, cloud by cloud. A
source is refused for its cloud before its kind, and for its kind before its
date. The relabelled set names the AWS and Azure objects that exist only in
their own cases; the wrong-layer set cites `uc-grants` for a control-path
timeout (not on that path) and `storage-role-assignment` for AZ-U (on the
path, but after the failing name, and permission evidence for a network
failure); the off-path set cites the legacy instance profile for a serverless
read and the relay name for a catalog refusal; the starter lines are the
five blank symptoms and six blank open questions.

## Counts

Thirty tests: fourteen on the evaluator, five on the answers, six deliberate
failures, four transfers, and one starter-gap test that runs only on the
reference answers.
