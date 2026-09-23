# Academy module authoring kit (real exemplar excerpts)

Generated from the finished new-module exemplar `dbxfe-aws` (D3). Use these shapes; do not read the full exemplar files unless a shape is unclear, and then print only the element you need with a one-line python command. Field contracts: `src/teaching-schema.ts` (teaching module) and `src/content-schema.ts` (course package, lesson). The standard is `docs/academy/AUTHORING-BRIEF.md`.

## 1. Module package `content/courses/dbxfe/modules/<moduleId>.json`

Top-level keys: `module`, `scenarios`, `sources`, `claims`, `concepts` (course-level registers used by the LESSON; teaching-module registers are separate). Shape (arrays truncated to one element):

```json
{
 "module": {
  "id": "dbxfe-aws",
  "title": "AWS deployment and network boundaries",
  "summary": "Place the account, workspace, control plane and both compute planes on AWS, trace one query across its trust boundaries, and diagnose a denied and an unreachable request in order.",
  "objectives": [
   "Draw Cinderline's AWS deployment with each resource in the account that owns it and name what differs on AWS.",
   "Trace author, control, execution and storage paths for one query on classic and on serverless compute.",
   "Run ordered diagnoses for a denied and an unreachable request and assemble a permissions and network evidence checklist."
  ],
  "prerequisiteIds": [
   "dbxfe-m03"
  ],
  "lessonFiles": [
   "lessons/dbxfe-aws-l01.json"
  ],
  "scenarioId": "dbxfe-aws-scenario"
 },
 "scenarios": [
  {
   "id": "dbxfe-aws-scenario",
   "title": "Write Cinderline's AWS deployment note for security review",
   "context": "Fictional Cinderline Components runs a classic workspace in a customer-managed VPC and is adding a serverless workspace in the same region. Sources: an SSE-KMS bucket in Cinderline's account, a supplier-owned bucket in another AWS account, and an RDS database on a private IP in Cinderline's VPC. Security requires no public egress from compute, private user access, and named evidence for every boundary. Region, tier and feature entitlement are unconfirmed.",
   "task": "Produce a one-page deployment note for the security specialist: the accounts and planes as drawn, one query's request path per plane, the storage identity and key chain for each source, the private connectivity directions required, the two diagnostic sequences the operations team will follow, and an explicit list of unknowns.",
   "requirements": [
    "Place every resource in the account that owns it and name what differs on AWS from a generic cloud picture.",
    "Give each source its identity, bucket policy and key policy chain, including the same-account rule for the supplier's role.",
    "Separate the denied-request sequence from the unreachable-request sequence, with evidence rows.",
    "Mark region, workspace type, tier, preview status and charges as unknown until verified; provision nothing."
   ],
   "model": "### Accounts and planes\nControl plane: Databricks account. Classic workspace cinderline-prod: compute in Cinderline's VPC (two private subnets, one security group, no public IPs, outbound only), workspace storage bucket and cross-account role in Cinderline's AWS account. Serverless workspace cinderline-sls: compute and default storage in the Databricks account, same region, reached through an NCC. …",
   "reasoning": "The note keeps the two accounts apart, gives each source a complete identity chain with the account that owns each policy, separates the two failure shapes so the operations team never applies a permission fix to a network fault, and turns every feature into a verification item rather than a promise.",
   "rubric": [
    {
     "id": "dbxfe-aws-scenario-rubric-1",
     "criterion": "Account and plane placement",
     "weak": "One box labelled Databricks; planes and accounts merged.",
     "partial": "Planes named but resources placed in the wrong account or Azure terms used.",
     "strong": "Every resource in its owning account, AWS constructs named, serverless drawn without a customer VPC."
    }
   ],
   "disclosures": [
    {
     "question": "Is the supplier willing to change its KMS key policy for our role?",
     "response": "Unknown; the supplier's security contact has not answered. Until they do, the supplier bucket is marked unreadable in the design."
    }
   ],
   "lessonIds": [
    "dbxfe-aws-l01"
   ],
   "claimIds": [
    "dbxfe-fact-architecture",
    "dbxfe-fact-serverless-network",
    "dbxfe-fact-classic-network",
    "dbxfe-guidance",
    "dbxfe-fiction",
    "dbxfe-aws-course-claim-workspace",
    "dbxfe-aws-course-claim-vpc",
    "dbxfe-aws-course-claim-storage",
    "dbxfe-aws-course-claim-profile",
    "dbxfe-aws-course-claim-privatelink",
    "dbxfe-aws-course-claim-keys",
    "dbxfe-aws-course-claim-egress"
   ],
   "isCapstone": false
  }
 ],
 "sources": [
  {
   "id": "dbxfe-aws-course-source-workspace",
   "title": "Create a workspace",
   "url": "https://docs.databricks.com/aws/en/admin/workspace/",
   "publisher": "Databricks",
   "type": "official documentation",
   "context": "Databricks on AWS; serverless and classic workspace types and admin roles.",
   "accessDate": "2026-09-23",
   "reviewDate": "2026-09-23",
   "caveat": "Workspace type availability and entitlement vary by account and region; no workspace is created. Search-result title and snippet confirmed 2026-09-23; page body not fetched in this build (documentation host blocked by the sandbox egress proxy)."
  }
 ],
 "claims": [
  {
   "id": "dbxfe-aws-course-claim-workspace",
   "description": "A serverless workspace is pre-configured with serverless compute and default storage in the Databricks account; a classic workspace provisions storage and compute in the customer's AWS account; account admins own workspace creation and workspace admins own in-workspace settings.",
   "kind": "documented",
   "sourceIds": [
    "dbxfe-aws-course-source-workspace"
   ],
   "context": "Workspace types on AWS; entitlement varies."
  },
  {
   "id": "dbxfe-aws-course-claim-vpc",
   "description": "A customer-managed VPC is named at workspace creation with at least two subnets and one security group; secure cluster connectivity gives nodes no public IP and opens no inbound ports; back-end and front-end PrivateLink on classic workspaces require a customer-managed VPC.",
   "kind": "documented",
   "sourceIds": [
    "dbxfe-aws-course-source-vpc"
   ],
   "context": "Classic compute plane networking on AWS."
  }
 ],
 "concepts": [
  {
   "id": "dbxfe-aws-l01-plane-concept",
   "term": "compute plane (AWS)",
   "aliases": [
    "classic compute plane",
    "serverless compute plane"
   ],
   "definition": "The network where Databricks compute runs: the customer's AWS account for classic, the Databricks account for serverless.",
   "lessonId": "dbxfe-aws-l01",
   "sectionId": "dbxfe-aws-l01-planes"
  }
 ]
}
```

## 2. Lesson `content/courses/dbxfe/lessons/<moduleId>-l01.json` (+ `.md` body)

The exemplar has 14 sections (kinds: outcome, prerequisites, mechanism, mechanism, mechanism, mechanism, mechanism, example, exercise, solution, mistakes, sources, related, revisit), 3 questions and 12 cards. Shape (truncated):

```json
{
 "id": "dbxfe-aws-l01",
 "title": "AWS deployment and network boundaries",
 "summary": "Place Cinderline's Databricks account, AWS account and two compute planes correctly, trace one query across its trust boundaries, and run ordered diagnoses for a denied and an unreachable request.",
 "contentVersion": "1.0.0",
 "teachingFormat": "flexible",
 "estimatedMinutes": 16,
 "objectives": [
  "Place the control plane, the classic compute plane and the serverless compute plane in the account that owns each, and name what differs on AWS.",
  "Trace one query across author, control, execution and storage paths and name the control at each boundary.",
  "Run an ordered diagnosis for a denied request and for an unreachable request, and assemble a permissions and network evidence checklist without provisioning anything."
 ],
 "prerequisiteIds": [],
 "tags": [
  "Governance and cloud architecture",
  "AWS",
  "VPC",
  "PrivateLink",
  "Unity Catalog",
  "KMS",
  "Substantive technical topic"
 ],
 "bodyFile": "lessons/dbxfe-aws-l01.md",
 "sections": [
  {
   "id": "dbxfe-aws-l01-outcome",
   "kind": "outcome",
   "title": "What you will be able to do",
   "conceptIds": [
    "dbxfe-aws-l01-plane-concept"
   ],
   "claimIds": [
    "dbxfe-fact-architecture",
    "dbxfe-fact-serverless-network",
    "dbxfe-fact-classic-network",
    "dbxfe-guidance",
    "dbxfe-fiction"
   ],
   "assetIds": []
  },
  {
   "id": "dbxfe-aws-l01-start",
   "kind": "prerequisites",
   "title": "Before the AWS diagram",
   "conceptIds": [
    "dbxfe-aws-l01-plane-concept"
   ],
   "claimIds": [
    "dbxfe-fact-architecture",
    "dbxfe-fact-serverless-network",
    "dbxfe-fact-classic-network",
    "dbxfe-guidance",
    "dbxfe-fiction"
   ],
   "assetIds": []
  }
 ],
 "questions": [
  {
   "id": "dbxfe-aws-l01-q1",
   "revision": "1",
   "prompt": "A serverless SQL warehouse query on the external table returns PERMISSION_DENIED: job-nightly does not have SELECT. Which boundary rejected the request?",
   "options": [
    {
     "id": "dbxfe-aws-l01-q1-a",
     "text": "The Unity Catalog privilege check for the acting principal.",
     "rationale": "The catalog names the principal and the privilege; no storage or key was consulted yet."
    },
    {
     "id": "dbxfe-aws-l01-q1-b",
     "text": "The storage credential's IAM role permissions.",
     "rationale": "A role refusal arrives from AWS as AccessDenied, and only after the catalog has agreed."
    },
    {
     "id": "dbxfe-aws-l01-q1-c",
     "text": "The subnet route table in Cinderline's VPC.",
     "rationale": "A route problem produces a timeout, and serverless compute does not use Cinderline's route tables."
    },
    {
     "id": "dbxfe-aws-l01-q1-d",
     "text": "The KMS key policy for the bucket's key.",
     "rationale": "A key refusal names KMS and comes after S3 has allowed the object read."
    }
   ],
   "correctOptionId": "dbxfe-aws-l01-q1-a",
   "conceptIds": [
    "dbxfe-aws-l01-diagnosis-concept",
    "dbxfe-aws-l01-credential-concept"
   ],
   "claimIds": [
    "dbxfe-fact-architecture",
    "dbxfe-fact-serverless-network",
    "dbxfe-fact-classic-network",
    "dbxfe-guidance",
    "dbxfe-fiction",
    "dbxfe-aws-course-claim-storage"
   ]
  }
 ],
 "cards": [
  {
   "id": "dbxfe-aws-l01-card1",
   "revision": "1",
   "prompt": "Which resources does a classic workspace place in Cinderline's own AWS account?",
   "answer": "Compute nodes in the customer VPC, the workspace storage bucket, and the IAM role Databricks assumes to launch them.",
   "explanation": "The control plane stays in the Databricks account. A classic workspace's network configuration names Cinderline's VPC, subnets and security group, its storage configuration names a bucket in Cinderline's account, and a cross-account role lets Databricks provision EC2 compute there. Those are the objects Cinderline operates and diagnoses.",
   "lessonId": "dbxfe-aws-l01",
   "sectionId": "dbxfe-aws-l01-planes",
   "conceptIds": [
    "dbxfe-aws-l01-plane-concept"
   ],
   "claimIds": [
    "dbxfe-fact-architecture",
    "dbxfe-fact-serverless-network",
    "dbxfe-fact-classic-network",
    "dbxfe-guidance",
    "dbxfe-fiction",
    "dbxfe-aws-course-claim-workspace"
   ]
  }
 ]
}
```

The `.md` body uses one marker per section id, in order, e.g.:

```md
<!-- section:dbxfe-aws-l01-outcome -->

After this lesson you can draw Cinderline's AWS deployment as it is operated: the Databricks account and control plane on one side, Cinderline's AWS account with its VPC, buckets, IAM roles and KMS keys on the other, and two compute planes that cross between them differently. You can trace one query across its trust boundaries and run two ordered diagnoses: one for a refused request, one for a request that never arrived. Nothing here provisions a resource; every feature named needs region, workspace type, tier and entitlement verified first.
<!-- section:dbxfe-aws-l01-start -->

Bring the platform map: account, workspace, catalog, compute and storage as separate responsibilities. Two retained lessons already teach the cloud-general ideas and are not repeated here. [Draw the cloud and trust boundaries](#/lesson/dbxfe-m06-l03) explains why a trust bo
…
```

## 3. Teaching module `content/teaching/dbxfe/<moduleId>.json`

Top-level keys, in order: schemaVersion, courseId, moduleId, title, summary, outcomes, startingAssumptions, lessonIds, optionalBridgeLessonIds, editorialRationale, sources, claims, concepts, visuals, questions, selfQuestions, beats, cardLinks, extensionCards, recap, appliedTask, scenarioIds. The exemplar: 13 beats, 13 visuals, 8 objective questions, 5 self-questions, 17 concepts, 11 sources, 12 claims, 12 cardLinks, 4 extension cards.

### 3a. Header

```json
{
 "schemaVersion": 1,
 "courseId": "dbxfe",
 "moduleId": "dbxfe-aws",
 "title": "AWS deployment and network boundaries",
 "summary": "Two accounts, two compute planes, one query path: who owns each boundary on AWS, and how a denied request differs from an unreachable one.",
 "outcomes": [
  "Place the control plane, classic compute plane and serverless compute plane in the account that owns each.",
  "Trace one query's author, control, execution and storage paths and name the control at every boundary.",
  "Distinguish instance profiles, Unity Catalog storage credentials and KMS key policies as three storage decisions.",
  "Run ordered diagnoses for a denied request and an unreachable request, and assemble an evidence checklist without provisioning anything."
 ],
 "startingAssumptions": [
  "The platform module separates account, workspace, catalog, compute and storage.",
  "The cloud bridge and the trust-boundary lesson have covered DNS, routing, identity and authorization in general terms."
 ],
 "lessonIds": [
  "dbxfe-aws-l01"
 ],
 "optionalBridgeLessonIds": [
  "dbxfe-cloud-bridge"
 ],
 "editorialRationale": "AWS-specific deployment teaching fails when it relabels a generic cloud picture, so the module starts by placing every resource in its owning account, follows one query across both compute planes, then treats storage identity, keys, serverless connectivity and PrivateLink as separate boundaries before two ordered diagnoses and an evidence checklist that a later lab reuses. Preview and regional features are marked as verification items throughout.",
 "scenarioIds": [
  "dbxfe-aws-scenario"
 ]
}
```

### 3b. One teaching source, claims (documented + the two conventional ones), one concept

```json
{
 "sources": [
  {
   "id": "dbxfe-aws-source-architecture",
   "title": "High-level architecture",
   "url": "https://docs.databricks.com/aws/en/getting-started/high-level-architecture",
   "publisher": "Databricks",
   "reviewedAt": "2026-09-23",
   "publishedAt": null,
   "context": "Databricks on AWS; overview of the account, the control plane and the classic and serverless compute planes.",
   "caveat": "An overview, not a network design; cloud, workspace type, region and feature availability must be verified separately for any real deployment.",
   "reviewedEvidence": "Search-result title and snippet confirmed 2026-09-23; page body not fetched in this build (documentation host blocked by the sandbox egress proxy). Passage relied on, as previously read: the control plane holds the backend services Databricks manages in the Databricks account, including the web application; classic compute resources run in the customer's AWS account (the classic compute plane); serverless compute runs in a serverless compute plane in the Databricks account, created in the same AWS region as the workspace's classic compute plane; serverless workspaces use default storage."
  }
 ],
 "claims": [
  {
   "id": "dbxfe-aws-claim-architecture",
   "description": "The control plane runs in the Databricks account; classic compute runs in the customer's AWS account; serverless compute runs in a Databricks-managed serverless compute plane in the same AWS region as the workspace's classic plane; serverless workspaces use default storage.",
   "kind": "documented",
   "sourceIds": [
    "dbxfe-aws-source-architecture"
   ],
   "context": "Databricks on AWS overview; workspace type and region must be verified."
  },
  {
   "id": "dbxfe-aws-guidance",
   "description": "Original SpicyBrain diagnostic ordering, evidence checklists and design reasoning for AWS deployments; not a Databricks or AWS runbook.",
   "kind": "guidance",
   "sourceIds": [],
   "context": "Independent curriculum; adapt to the actual account, region and security review."
  },
  {
   "id": "dbxfe-aws-fiction",
   "description": "Cinderline Components, its workspaces, buckets, roles, keys, identities, error texts and outcomes are synthetic teaching records.",
   "kind": "fictional",
   "sourceIds": [],
   "context": "No AWS or Databricks resource was created, read or tested; region names appear only as example values."
  }
 ],
 "concepts": [
  {
   "id": "dbxfe-aws-account-concept",
   "term": "Databricks account",
   "aliases": [
    "account console"
   ],
   "definition": "The Databricks-side container that holds workspaces, account-level identities and regional settings, distinct from the customer's own AWS account.",
   "example": "Cinderline's one Databricks account holds a classic workspace and a serverless workspace in the same region.",
   "sourceIds": [
    "dbxfe-aws-source-architecture",
    "dbxfe-aws-source-workspace"
   ]
  }
 ]
}
```

### 3c. One beat (with its visual) 

```json
{
 "id": "dbxfe-aws-vpc",
 "version": "1.0.0",
 "title": "Classic compute obeys the VPC you hand it",
 "outcome": "Name the VPC pieces a classic workspace needs and identify which one decides a launch failure.",
 "explanation": "A classic workspace takes a [[dbxfe-aws-vpc-concept|customer-managed VPC]] when it is created: the documentation asks for at least two subnets and at least one security group. Secure cluster connectivity means cluster nodes get no public IP address and need no open inbound port; the compute plane opens outbound connections to the control plane. So the working parts are the subnet, a route table with an outbound route, DNS resolution for the control plane names, and the security group's outbound rules. Notice in the second state that removing only the route stops the launch while DNS and the security group still look correct.",
 "lessonId": "dbxfe-aws-l01",
 "sectionId": "dbxfe-aws-l01-classic",
 "conceptIds": [
  "dbxfe-aws-vpc-concept"
 ],
 "claimIds": [
  "dbxfe-aws-claim-vpc",
  "dbxfe-aws-claim-architecture",
  "dbxfe-aws-guidance",
  "dbxfe-aws-fiction"
 ],
 "visualId": "dbxfe-aws-vpc-visual",
 "questionIds": [
  "dbxfe-aws-vpc-self"
 ],
 "handbook": {
  "markdown": "A customer-managed VPC is named in the workspace's network configuration at creation time. The documentation requires at least two subnets and at least one security group, states network ACL requirements at subnet level, and lists the DNS settings the VPC must have so that compute can resolve the control plane and AWS service names; read the current requirement list rather than this summary before designing.\n\nSecure cluster connectivity changes the shape of the diagnosis. Nodes have no public IP addresses, and the customer VPC has no open ports for Databricks to reach in. Each node dials out to the control plane's relay and keeps that connection for commands. Consequently, a launch depends on the outbound side only: a route from the subnet to a NAT gateway, or to interface endpoints if back-end PrivateLink is configured; DNS answers for the workspace and relay hostnames; security group outbound rules and network ACLs that allow the traffic.\n\nA typical failure reads as a bootstrap timeout or a cluster that never reaches running. Work outward from the node: the subnet's route table association, the NAT gateway's state and its own route through an internet gateway, the VPC's DNS attributes, the security group's outbound rules. Adding inbound rules does nothing here. What this beat does not cover: IP address exhaustion in small subnets, which surfaces as launch capacity errors rather than timeouts, and the exact port list, which the current page owns. Nothing here creates a VPC; a real design is verified by a network specialist against Cinderline's region.",
  "sourceSectionIds": [
   "dbxfe-aws-l01-classic"
  ]
 },
 "recap": "Two subnets, one security group, an outbound route and DNS; no inbound rule can rescue a launch.",
 "changeNote": "New academy beat.",
 "mediaIds": []
}
```

```json
{
 "id": "dbxfe-aws-vpc-visual",
 "kind": "nodes",
 "title": "What a classic launch needs from the VPC",
 "alt": "What a classic launch needs from the VPC. The node starts in a private subnet, resolves the control plane name, and opens an outbound connection through the subnet's route.",
 "caption": "Outbound route, DNS and security-group egress make a launch work; removing the route alone stops it while everything else still looks correct. Synthetic teaching example.",
 "textEquivalent": "Launch succeeds: The node starts in a private subnet, resolves the control plane name, and opens an outbound connection through the subnet's route. Nodes: Cluster node: No public IP; initiates outbound only. (selected); Private subnet: One of at least two subnets named at workspace creation. (selected); Route table: 0.0.0.0/0 to NAT. Outbound route through a NAT gateway. (selected); Security group: Outbound rules allow the connection; no inbound rule needed. (selected); VPC DNS: Resolves the workspace and relay hostnames. (selected); Control plane relay: Accepts the node's outbound connection. (selected). Relationships: Cluster node → Private subnet: launches in; Private subnet → Route table: uses; Cluster node → VPC DNS: resolves; Security group → Cluster node: applies to; Route table → Control plane relay: outbound.\n\nRoute removed: The default route is gone. DNS still answers and the security group still allows, yet the node times out because nothing carries its packets out. Nodes: Cluster node: Bootstrap timeout reported by the workspace. (warning); Private subnet: Unchanged. (selected); Route table: no default route. No route to the NAT gateway or an endpoint. (warning); Security group: Still allows outbound; not the cause. (selected); VPC DNS: Still resolves; not the cause. (selected); Control plane relay: Never reached. (excluded). Relationships: Cluster node → Private subnet: launches in; Private subnet → Route table: uses; Cluster node → VPC DNS: resolves; Security group → Cluster node: applies to; Route table → Control plane relay: no path.",
 "provenance": "Original SpicyBrain authored visual; synthetic values; no copied product screenshot or executed cloud result.",
 "claimIds": [
  "dbxfe-aws-claim-vpc",
  "dbxfe-aws-claim-architecture",
  "dbxfe-aws-guidance",
  "dbxfe-aws-fiction"
 ],
 "states": [
  {
   "id": "launch",
   "title": "Launch succeeds",
   "explanation": "The node starts in a private subnet, resolves the control plane name, and opens an outbound connection through the subnet's route.",
   "nodes": [
    {
     "id": "node",
     "label": "Cluster node",
     "detail": "No public IP; initiates outbound only.",
     "status": "selected"
    },
    {
     "id": "subnet",
     "label": "Private subnet",
     "detail": "One of at least two subnets named at workspace creation.",
     "status": "selected"
    },
    {
     "id": "route",
     "label": "Route table",
     "detail": "Outbound route through a NAT gateway.",
     "status": "selected",
     "value": "0.0.0.0/0 to NAT"
    },
    {
     "id": "secgroup",
     "label": "Security group",
     "detail": "Outbound rules allow the connection; no inbound rule needed.",
     "status": "selected"
    },
    {
     "id": "dns",
     "label": "VPC DNS",
     "detail": "Resolves the workspace and relay hostnames.",
     "status": "selected"
    },
    {
     "id": "control",
     "label": "Control plane relay",
     "detail": "Accepts the node's outbound connection.",
     "status": "selected"
    }
   ],
   "connections": [
    {
     "from": "node",
     "to": "subnet",
     "label": "launches in"
    },
    {
     "from": "subnet",
     "to": "route",
     "label": "uses"
    },
    {
     "from": "node",
     "to": "dns",
     "label": "resolves"
    },
    {
     "from": "secgroup",
     "to": "node",
     "label": "applies to"
    },
    {
     "from": "route",
     "to": "control",
     "label": "outbound"
    }
   ]
  },
  {
   "id": "noroute",
   "title": "Route removed",
   "explanation": "The default route is gone. DNS still answers and the security group still allows, yet the node times out because nothing carries its packets out.",
   "nodes": [
    {
     "id": "node",
     "label": "Cluster node",
     "detail": "Bootstrap timeout reported by the workspace.",
     "status": "warning"
    },
    {
     "id": "subnet",
     "label": "Private subnet",
     "detail": "Unchanged.",
     "status": "selected"
    },
    {
     "id": "route",
     "label": "Route table",
     "detail": "No route to the NAT gateway or an endpoint.",
     "status": "warning",
     "value": "no default route"
    },
    {
     "id": "secgroup",
     "label": "Security group",
     "detail": "Still allows outbound; not the cause.",
     "status": "selected"
    },
    {
     "id": "dns",
     "label": "VPC DNS",
     "detail": "Still resolves; not the cause.",
     "status": "selected"
    },
    {
     "id": "control",
     "label": "Control plane relay",
     "detail": "Never reached.",
     "status": "excluded"
    }
   ],
   "connections": [
    {
     "from": "node",
     "to": "subnet",
     "label": "launches in"
    },
    {
     "from": "subnet",
     "to": "route",
     "label": "uses"
    },
    {
     "from": "node",
     "to": "dns",
     "label": "resolves"
    },
    {
     "from": "secgroup",
     "to": "node",
     "label": "applies to"
    },
    {
     "from": "route",
     "to": "control",
     "label": "no path"
    }
   ]
  }
 ]
}
```

### 3d. Samajh on another beat

```json
{
 "text": "Socho Cinderline ne ek mall mein do dukaan li. Pehli dukaan (classic) mein godown, bijli aur staff Cinderline ka apna hai; mall sirf entrance aur billing counter chalata hai. Doosri dukaan (serverless) mall ka ready-made counter hai: staff aur storage mall ka, Cinderline sirf apna saaman aur apne rules deta hai. Dono dukaanein ek hi malik ki hain, par kaun kya chalata hai, woh alag hai.",
 "mapping": "The mall is the Databricks account and control plane; each shop is a workspace; the first shop's own stockroom and staff are the classic compute plane in Cinderline's AWS account.",
 "boundary": "A workspace is not a physical place; region, entitlement and workspace type must be verified before assuming which plane a workspace has."
}
```

### 3e. One objective question and one self-question

```json
{
 "id": "dbxfe-aws-account-question",
 "revision": "1",
 "prompt": "A Cinderline engineer says: \"Our classic notebooks execute inside Databricks' own AWS account, so our VPC rules do not apply to them.\" Which statement is accurate for a classic workspace?",
 "options": [
  {
   "id": "dbxfe-aws-account-question-a",
   "text": "Classic compute runs in Cinderline's AWS account, so its VPC, subnets, route tables and security groups apply.",
   "rationale": "Documented: the classic compute plane is the network in the customer's AWS account; only the control plane is Databricks-side."
  },
  {
   "id": "dbxfe-aws-account-question-b",
   "text": "Classic compute runs in the Databricks account and only serverless compute uses Cinderline's VPC.",
   "rationale": "Reversed: serverless compute is the plane that runs in the Databricks account, and it uses no customer VPC."
  },
  {
   "id": "dbxfe-aws-account-question-c",
   "text": "Both compute planes and the control plane all run in Cinderline's AWS account.",
   "rationale": "The control plane's backend services run in the Databricks account, never in the customer account."
  },
  {
   "id": "dbxfe-aws-account-question-d",
   "text": "Neither compute plane touches Cinderline's AWS account; only S3 buckets do.",
   "rationale": "A classic workspace provisions compute and workspace storage inside the customer's account."
  }
 ],
 "correctOptionId": "dbxfe-aws-account-question-a",
 "conceptIds": [
  "dbxfe-aws-account-concept"
 ],
 "claimIds": [
  "dbxfe-aws-claim-architecture",
  "dbxfe-aws-claim-workspace",
  "dbxfe-aws-guidance",
  "dbxfe-aws-fiction"
 ]
}
```

```json
{
 "id": "dbxfe-aws-vpc-self",
 "revision": "1",
 "prompt": "A classic cluster fails to start after a network change. A colleague proposes adding inbound rules to its security group. Explain why that will not help and what you would check instead, in order.",
 "modelAnswer": "Secure cluster connectivity means nodes have no public IP and initiate outbound connections, so inbound rules are never consulted for the launch. Check, in order: the subnet's route table has an outbound route to a NAT gateway or interface endpoint; VPC DNS resolves the control plane and relay hostnames from that subnet; the security group's outbound rules and the network ACL allow the connection; then retest a launch in the same subnet and record the result.",
 "reasoning": "The order follows the request outward from the node; each check is cheap and its result eliminates a layer. Checking NAT gateway state or the egress firewall first is an acceptable alternative when the change log points there.",
 "conceptIds": [
  "dbxfe-aws-vpc-concept"
 ],
 "claimIds": [
  "dbxfe-aws-claim-vpc",
  "dbxfe-aws-claim-architecture",
  "dbxfe-aws-guidance",
  "dbxfe-aws-fiction"
 ]
}
```

### 3f. cardLinks (every lesson card, each to the beat that teaches it), one extension card, recap, appliedTask

```json
{
 "cardLinks": [
  {
   "cardId": "dbxfe-aws-l01-card1",
   "beatId": "dbxfe-aws-account"
  },
  {
   "cardId": "dbxfe-aws-l01-card2",
   "beatId": "dbxfe-aws-serverless"
  },
  {
   "cardId": "dbxfe-aws-l01-card3",
   "beatId": "dbxfe-aws-vpc"
  }
 ],
 "extensionCards": [
  {
   "id": "dbxfe-aws-extension-egress-policy",
   "revision": "1",
   "prompt": "What can a serverless network policy deny that Cinderline's VPC firewall never sees?",
   "answer": "Outbound connections from the Databricks-managed serverless plane, such as internet, cloud storage or Databricks API destinations, which never pass through Cinderline's VPC.",
   "explanation": "A classic egress firewall inspects traffic leaving Cinderline's subnets. Serverless compute has no such subnet, so a [[dbxfe-aws-extension-egress-policy-concept|serverless network policy]] is the only place to restrict its egress: it defines allowed destinations, can deny internet, storage and Databricks API connections by default, applies at the account with per-workspace assignment, and runs enforced or in dry-run with denials or violations logged to a system table. It requires the Enterprise tier and an account admin, and it was announced as Public Preview on AWS in January 2025, so its status for Cinderline's region and products is verified, not assumed. Use dry-run first to read the log before enforcing.",
   "lessonId": "dbxfe-aws-l01",
   "sectionId": "dbxfe-aws-l01-serverless",
   "conceptIds": [
    "dbxfe-aws-extension-egress-policy-concept"
   ],
   "claimIds": [
    "dbxfe-aws-claim-egress",
    "dbxfe-aws-claim-serverless",
    "dbxfe-aws-guidance",
    "dbxfe-aws-fiction"
   ],
   "beatId": "dbxfe-aws-serverless",
   "whyItMatters": "Explains why a VPC-era egress control has no effect on serverless and names the documented replacement with its preview caveat."
  }
 ],
 "recap": {
  "title": "Two accounts, two planes, one query path",
  "markdown": "**Databricks account and control plane on one side; Cinderline's AWS account with its VPC, roles, buckets and keys on the other.** Classic compute crosses into Cinderline's VPC and obeys its subnets, routes, security groups, DNS and egress; serverless compute stays in the Databricks account and is reached through a network connectivity configuration. Storage identity is an instance profile on classic or a Unity Catalog storage credential on either, and a KMS key policy is a third door after S3 says yes. PrivateLink is three separate connections, each with its own DNS answer. A denial names its layer; a timeout names none, so each has its own ordered diagnosis. **Transfer challenge:** redraw the responsibility table for a partner-owned SSE-KMS bucket read from a serverless warehouse, marking every row that needs the partner's account and every feature whose availability is still unknown.",
  "visualId": "dbxfe-aws-responsibilities-visual"
 },
 "appliedTask": {
  "title": "Move the nightly job and keep the evidence honest",
  "prompt": "Cinderline moves the nightly job from a classic cluster with an instance profile to a serverless SQL warehouse in a new workspace in the same region. The source is an SSE-KMS bucket in a supplier's AWS account, and a lookup table lives in an RDS database on a private IP in Cinderline's VPC. List, in order, what must exist on the AWS side and the Databricks side for the job to reach both sources, which responsibilities the migration removes from Cinderline's account, and what you would mark unknown before the design review.",
  "modelAnswer": "AWS side: a supplier-account IAM role with the documented trust policy, a supplier bucket policy admitting that role for the prefix, and a supplier KMS key policy granting the role kms:Decrypt; on Cinderline's side, a VPC endpoint service in front of the RDS database and acceptance of the private endpoint connection. Databricks side: a storage credential pointing at the supplier's role ARN, an external location for the prefix, USE CATALOG, USE SCHEMA and SELECT for the job's run-as principal, a  …",
  "reasoning": "The answer follows the request path from identity through catalog, storage and key, then reachability through the NCC, keeps the two accounts distinct, and turns each feature into a verification item instead of a promise.",
  "beatIds": [
   "dbxfe-aws-unity",
   "dbxfe-aws-keys",
   "dbxfe-aws-serverless",
   "dbxfe-aws-responsibilities",
   "dbxfe-aws-evidence"
  ]
 }
}
```

## 4. Media decision `docs/academy/media-decisions/<moduleId>.json`

```json
{
 "moduleId": "dbxfe-aws",
 "date": "2026-09-23",
 "decision": "no-placement",
 "reason": "Video hosts and captions are unreachable from the build sandbox; a placement cannot be reviewed or playback-verified. The beat sequence is complete with authored visuals. Search surfaced one relevant Databricks-published talk only through an aggregator listing; its original creator URL did not surface, so no direct video URL is recorded.",
 "suggestedBeatId": "dbxfe-aws-privatelink",
 "candidates": [
  {
   "title": "Securing Databricks on AWS Using PrivateLink - Deployment and Automation",
   "creator": "Databricks (talk listed by Class Central; original YouTube URL not surfaced by search)",
   "url": "https://www.classcentral.com/course/youtube-securing-databricks-on-aws-using-private-link-134996",
   "foundVia": "web search 2026-09-23",
   "whyRelevant": "Covers front-end and back-end PrivateLink for Databricks on AWS, VPC endpoints for AWS services and workspace architecture, matching the PrivateLink beat; an aggregator listing, not the creator's page, so it is a lead for a later reviewer rather than a placement.",
   "reviewed": false
  }
 ]
}
```
