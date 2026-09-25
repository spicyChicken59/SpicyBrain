# Three-cloud questions matrix (template)

The three estates run on three clouds: Northbrook's BI and landing storage on
**Azure**, Vale's lakehouse on **AWS**, Tessaly's telemetry archive on
**Google Cloud** (in an in-jurisdiction region). The same question has a
separate answer for each cloud, and the answers do not have to match.

## How to fill a cell

Every cell starts as **unknown — needs verification**. Replace it only with
one of:

- **sourced:** *<what the current primary documentation for that cloud says,
  in your words>* — *<page title, publisher, date you read it>*. Cloud-specific
  documentation only; a page about one cloud is not evidence for another.
- **customer-stated (unverified):** *<what a disclosure or the inventory says>*.
- **not applicable:** *<why the question does not arise for this estate>*.

A cell filled from memory is still **unknown**. Availability of a feature on
one cloud never implies availability on another. Preview or region-limited
capabilities are named as such. In this build the sandbox could not read
documentation pages, so the template ships with no sourced cells; sourcing
them is part of the exercise.

## The matrix

| # | Question | AWS (Vale) | Azure (Northbrook) | Google Cloud (Tessaly) | Why it matters here |
|---|---|---|---|---|---|
| 1 | Which identity provider can authenticate users and workload identities to a workspace, and can a *different* estate's directory be federated? | customer-stated (unverified): Vale's own identity provider today; no trust to Northbrook | unknown — needs verification | unknown — needs verification | Vale security will not add Northbrook groups; consolidation depends on this |
| 2 | Where is catalog **metadata** stored and processed for a workspace in a given region? | unknown — needs verification | unknown — needs verification | unknown — needs verification | Tessaly's regulator treats metadata as restricted |
| 3 | Does serverless compute process data outside the workspace's region, and can it be disabled or constrained? | unknown — needs verification | unknown — needs verification | unknown — needs verification | Residency for Tessaly; network review for Northbrook |
| 4 | What private-connectivity pattern reaches classic compute from an on-premises network, and who owns which part of it? | unknown — needs verification | unknown — needs verification | not applicable (no compute planned in Tessaly's project) | Granite extracts; Northbrook network review |
| 5 | How does a workspace authorize access to the cloud's object storage (identity, role, key)? | customer-stated (unverified): in place for Vale's account | unknown — needs verification | unknown — needs verification | No shared storage credential across clouds |
| 6 | Where are audit logs delivered, and can each estate's own security tooling consume them? | unknown — needs verification | unknown — needs verification | unknown — needs verification | Audit on both sides of every share |
| 7 | How does recipient-scoped governed sharing work across cloud boundaries: recipient identity, revocation, freshness, egress cost? | customer-stated (unverified): Vale shares to three suppliers today | unknown — needs verification | unknown — needs verification | Price list to Vale; supplier summary to Northbrook |
| 8 | Is query federation to an on-premises warehouse appliance supported, and with what freshness and cost? | unknown — needs verification | unknown — needs verification | unknown — needs verification | Whether Granite can be queried in place during coexistence |
| 9 | Which regions are available inside the Nordland jurisdiction (fictional) for a workspace, and for its metadata? | unknown — needs verification | unknown — needs verification | unknown — needs verification | Tessaly's regulator question |
| 10 | What does cross-cloud data movement cost (egress) and which side pays? | unknown — needs verification | unknown — needs verification | unknown — needs verification | Movement line in the cost worksheet |
| 11 | How is a BI service on one cloud connected to a SQL endpoint on another, and what latency has been measured? | unknown — needs verification | customer-stated (unverified): Beacon reads the Azure reporting database today | not applicable | Path A's cross-cloud read path; Rosalind's parity rule |
| 12 | What customer-managed encryption key options exist for storage and for the platform's managed services? | unknown — needs verification | unknown — needs verification | unknown — needs verification | Security review inputs |
| 13 | How are workload identities (service principals or equivalents) created, scoped and rotated? | unknown — needs verification | unknown — needs verification | unknown — needs verification | Pipeline owner design |
| 14 | What operational evidence (system tables, usage records, job events) is available to attribute cost and diagnose failures? | unknown — needs verification | unknown — needs verification | unknown — needs verification | Cost attribution and runbooks |

## Rules

- Do not fill a cell to make a path look feasible. An honest "unknown" that
  blocks a decision is a finding; list it in the open questions with an owner.
- Do not copy a cell from one column to another.
- The Google Cloud column being mostly unknown is expected: Tessaly runs an
  archive there, not an analytics platform. Say so rather than inventing
  parity.
