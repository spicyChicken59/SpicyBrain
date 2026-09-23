### Who reports this and how

The source is the Databricks customer page "Decommissioning a Heritage Data Warehouse for a Modern Lakehouse Future", about National Australia Bank; the reporter is the vendor (vendor case study), which means the framing and figure selection are the vendor's. Search results also list a Data + AI Summit session on the same migration, presented as a customer talk, and an independent trade-press article; either could be better evidence, but the customer page is used because its snippets carry the estate counts this analysis relies on, and the other two were seen only as search-result listings. A vendor employee's social post is recorded as a second source for one figure. Publication date: not stated in the available summary. The page itself could not be opened when this analysis was written; only its search-result title and snippets were read.

### The problem

A large Australian bank had run a Teradata warehouse for more than two decades as the backbone of its data and reporting estate: thousands of daily feeds, close to a thousand use cases and more than 140 reporting suites are the reported counts. The summary describes regular batch delays and incidents that put compliance and customer commitments at risk, and support costs that crowded out new work. Decommissioning is framed as both a technical need and a business decision.

### Constraints

As far as the summary states: regulatory compliance had to be safeguarded and business processes kept running throughout (the vendor presents both as achieved), and more than 1,200 business and technical users had to be moved and re-skilled on the new platform. General context, not stated by the source: a bank's reporting suites are audited artefacts, so parity between old and new outputs has to be evidenced, not assumed. Not stated: timeline, budget, migration tooling, or which BI tools sit on top.

### Architecture as described

Per the vendor, reporting, analytics and machine-learning workloads moved onto Databricks SQL, described as a governed, real-time analytics backbone valued for speed, automation, transparency and control.

### Evidence and its limits

The vendor's claims are mostly qualitative (reliability, speed, self-service, compliance safeguarded, no interruption) plus counts of feeds, use cases, suites and users. No cost, latency or incident-rate figure appears in the summary. The only figure for the share migrated comes from the second source: a LinkedIn post by a Databricks employee whose title reads "NAB migrates 95% of workloads to Databricks SQL"; its full wording was not read, so what the 95 percent counts is unknown. A skeptical reader cannot know the migration's duration and cost, what the remaining workloads are and why they stayed, how output parity was proven for regulated reports, whether "1,200 users" means licensed or active, and whether the decommissioning is complete or scheduled.

### What transfers

Start with an inventory of feeds, use cases and report suites, because the decommission plan is that inventory with owners and dates. Make switching the old platform off the explicit goal; a migration that leaves the heritage system running has not saved anything. Budget for user skills and data literacy as a workstream, not an afterthought. In a regulated setting, keep the parallel-run evidence, since it is what lets you retire the old reports.

### Missing information

Ask for the timeline and the dual-run period; the SQL conversion approach and how parity was evidenced; the cost model before and after; what happened to the reporting tools and their semantic layers; which workloads were rebuilt rather than migrated; and what the 95 percent in the social post counts, and against what total.
