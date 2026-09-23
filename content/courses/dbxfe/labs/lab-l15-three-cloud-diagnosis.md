*Tabletop (T). Worked on paper or in a text editor; a small evaluator written
with the Python 3.12 standard library checks the answers against keys written
by hand. A diagram proves nothing is deployed: every request path here is a
text table, and nothing resolves a name, sends a packet, reads a policy or
contacts AWS, Azure, Google Cloud or Databricks.*

### What this lab is for

Each cloud module ends with the same practice: follow one query through its
author, control, execution and storage paths, then diagnose one refused and
one unreachable request in the order the request travels. The AWS module,
[AWS deployment and network boundaries](#/module/dbxfe-aws), and the modules
Azure deployment and network boundaries and Google Cloud deployment and
network boundaries each teach that sequence with their own objects. This lab
puts three fictional Cinderline Components deployments side by side, one per
cloud, so that you practise the sequence without letting one cloud's answer
leak into another. The distinction it rests on is the one drawn in
[cloud responsibilities and request paths](#/lesson/dbxfe-cloud-bridge):
identity answers who made a request, authorization whether that principal may
act, and naming and routing whether the request arrives at all.

### The four classifications

| Classification | The first failing control on the path… |
|---|---|
| identity | establishes who acts, and the wrong principal acted |
| authorization | checks a privilege, role or policy for the right principal, and it is missing |
| name resolution | answers a name, and the asking network gets the public address instead of the private one |
| reachability | routes, filters or carries the packet |

You classify by the first control that fails in path order, not by the word
in the error. A timeout is never identity or authorization, because no grant
can make a packet arrive; a refusal usually is, but a refusal from a public
front door can still be a naming fault.

### The three cases in one table

| Case | Refused symptom | Unreachable symptom |
|---|---|---|
| AWS | AWS-D: the nightly job on a serverless warehouse gets a KMS AccessDenied after the catalog agreed | AWS-U: classic clusters time out reaching the relay after the compute subnets moved |
| Azure | AZ-D: the nightly job gets a 403 from the storage account; a colleague already gave the job's service principal a storage role | AZ-U: a backfill on a classic cluster times out reaching the ADLS account behind a private endpoint |
| Google Cloud | GCP-D: PERMISSION_DENIED names Ana, who created the job, not its service principal | GCP-U: cluster starts stall after back-end Private Service Connect replaced the Cloud NAT |

Each case has its own request-path table, identities, controls with their
authored configuration, an evidence catalogue and open questions. The AWS
control path, for example, reads as a text diagram:

| Order | Control | Layer | Authored state |
|---|---|---|---|
| 1 | `route53-private-hosted-zone` | name resolution | associated with the workspace VPC; relay name → 10.0.8.21 |
| 2 | `vpc-route-table` | reachability | 10.0.0.0/16 → local |
| 3 | `compute-security-group` | reachability | outbound to anything |
| 4 | `endpoint-security-group` | reachability | inbound 443 from 10.0.16.0/20 only |
| 5 | `relay-interface-endpoint` | reachability | available, registered |

The node at 10.0.33.17 passes the first three and fails the fourth: its new
subnet is not in the endpoint group's only rule. That is AWS-U, reachability.

### Tasks 1 to 3 — classify, name the control, name the evidence

Working through the walks gives these answers:

| Symptom | Classification | Broken control | Evidence that proves it |
|---|---|---|---|
| AWS-D | authorization | `kms-key-policy` | the key policy's statements for the credential's role ARN |
| AWS-U | reachability | `endpoint-security-group` | the relay name's answer from the subnet; the endpoint group's inbound rules |
| AZ-D | authorization | `storage-role-assignment` | the connector's managed identity; its role assignments on the account |
| AZ-U | name resolution | `private-dns-zone-link` | the storage name's answer on the cluster; the zone's virtual network links |
| GCP-D | identity | `run-as` | the job's run-as setting |
| GCP-U | name resolution | `cloud-dns-private-zone` | the relay name's answer from the node subnet; the zone's visibility networks |

Every answer also cites `error-record`, and the refused ones cite the job's
run-as setting, because every module's refused-request sequence confirms the
acting principal first. Three of the six are network failures and all four
classes occur. Two teach the most. In AZ-D the colleague's fix changed
nothing: the job never reads storage with its own identity, and the access
connector's managed identity lost its data role in a cleanup. In GCP-D the
refusal is genuine but names the wrong person; granting Ana the job's access
would make the error vanish and put a scheduled job's reach in a person's
hands. The fix is the run-as setting.

### Task 4 — keep the open questions open

Each case carries open questions: the relay endpoint services and ports for
the region on AWS, the private network gateway and NCC limits on Azure, and on
Google Cloud whether serverless can reach private resources at all, which
service account classic VMs get by default, and which firewall rules are
required. Each answer stays *unknown until verified* and names the dated
source or test that would close it. A row may move only with a dated source
about the same cloud: an SDK field, a Terraform example or another cloud's
answer is refused.

### The failure cases

The relabelled answer set copies the AWS diagnosis into the other two cases.
Its classification is even right, yet the runner refuses it line by line:

```text
AZ-U: brokenControl route53-private-hosted-zone is not a control of the azure case (it belongs to: aws)
GCP-U: brokenControl private-dns-zone-link is not a control of the gcp case (it belongs to: azure)
gcp/gcp-serverless-private-connectivity: a source about azure never settles a gcp row
```

A second set proposes a catalog grant for the AWS timeout and blames the
storage role for the Azure timeout. The storage role really is missing in the
Azure case, but the name fails first, so that answer is wrong, and its role
evidence is refused as permission evidence for a network failure. A third
cites the legacy instance profile for a serverless read, a path that request
never took.

### The altered input

Eleven scenarios change one setting at a time. Linking the Azure zone to the
data network makes AZ-U fail at the Pending endpoint (reachability); approving
it exposes the missing storage role (authorization); restoring the role lets
the read pass. Making the Google Cloud zone visible to the node network turns
GCP-U from name resolution into reachability, because a deny at priority 900
now decides before the allow at 1000; renumbering the allow to 800 clears it.
Fixing one fault exposed the next, which is why an evidence record lists every
fault found.

### What the tests prove, and what they do not

Thirty tests prove that the evaluator reproduces six walks and eleven transfer
results written by hand, that the reference answers match the keys, that the
starters are incomplete, that the three wrong answer sets fail with the exact
lines in the key, that each case uses only its own cloud's vocabulary and
controls, and that every symptom's error text is marked fictional. While the
lab was written, five mutations of the evaluator (no cross-cloud check, allow
winning a priority tie, the highest priority deciding, every name answering
privately, no evidence-family check) each turned tests red; those runs are not
part of the recorded evidence. Nothing proves any cloud's behaviour: real IAM,
key policies, role assignments, inherited Google Cloud policies, network ACLs,
firewall policies and propagation delays are richer than the model, as the
package's DATA.md lists. The governance side of the same boundaries is in
[Unity Catalog, security and deployment](#/module/dbxfe-m06), and drawing them
is practised in [draw the cloud and trust boundaries](#/lesson/dbxfe-m06-l03).

### Setup and cleanup

With Python 3.12 and nothing else: `python3.12 run_tests.py` checks the
reference answers, and `python3.12 run_tests.py --answers starters` checks
yours after you edit `starters/answers.json`. `python3.12 solutions/diagnose.py
--table gcp` prints one case's request path. The runner writes only an
evidence file you name and creates no cache directory; delete that file when
you are done.
