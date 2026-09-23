### Who reports this and how

The source is the Databricks customer page "Decommissioning a Heritage Data Warehouse for a Modern Lakehouse Future", about National Australia Bank; the reporter is the vendor (vendor case study), which means the framing and figure selection are the vendor's. Search results also list a Data + AI Summit session on the same migration, presented as a customer talk, and an independent trade-press article; both would be better evidence and neither was fetched. Publication date: not stated in the available summary. The page body was not fetched in this build (egress blocked).

### The problem

A large Australian bank had run a Teradata warehouse for more than two decades as the backbone of its data and reporting estate: thousands of daily feeds, close to a thousand use cases and more than 140 reporting suites are the reported counts. The summary describes regular batch delays and incidents that put compliance and customer commitments at risk, and support costs that crowded out new work. Decommissioning is framed as both a technical need and a business decision.

### Constraints

As far as the summary states: regulatory compliance had to be safeguarded throughout, business processes could not be interrupted, and more than 1,200 business and technical users had to be moved and re-skilled on the new platform. General context, not stated by the source: a bank's reporting suites are audited artefacts, so parity between old and new outputs has to be evidenced, not assumed. Not stated: timeline, budget, migration tooling, or which BI tools sit on top.

### Architecture as described

Reporting, analytics and machine-learning workloads moved onto Databricks SQL, described as a governed, real-time analytics backbone valued for speed, automation, transparency and control. One search summary attributes a figure of 95 percent of critical workloads migrated to a vendor social post; another summary mentions 456 migrated use cases without a traceable origin. Both are flagged as reported and unverified here.

### Evidence and its limits

The vendor's claims are mostly qualitative (reliability, speed, self-service) plus counts of feeds, use cases, suites and users. No cost, latency or incident-rate figure appears in the summary. A skeptical reader cannot know the migration's duration and cost, what the remaining workloads are and why they stayed, how output parity was proven for regulated reports, whether "1,200 users" means licensed or active, and whether the decommissioning is complete or scheduled.

### What transfers

Start with an inventory of feeds, use cases and report suites, because the decommission plan is that inventory with owners and dates. Make switching the old platform off the explicit goal; a migration that leaves the heritage system running has not saved anything. Budget for user skills and data literacy as a workstream, not an afterthought. In a regulated setting, keep the parallel-run evidence, since it is what lets you retire the old reports.

### Missing information

Ask for the timeline and the dual-run period; the SQL conversion approach and how parity was evidenced; the cost model before and after; what happened to the reporting tools and their semantic layers; which workloads were rebuilt rather than migrated; and the origin of the 95 percent and 456 figures.
