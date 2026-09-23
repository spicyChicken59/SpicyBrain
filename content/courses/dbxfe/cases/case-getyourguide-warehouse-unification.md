### Who reports this and how

The source is a post on "Inside GetYourGuide", the company's own engineering and careers blog, titled "From Snowflake to Databricks: Our cost-effective journey to a unified data warehouse". The reporter is the customer's engineering team (customer-authored). Publication date: not stated in the available summary. Search results also list a Databricks customer page and a Data + AI Summit session about the same company; neither is used as the source record here. The page body was not fetched in this build (egress blocked), so this analysis rests on the result title and snippets.

### The problem

The team ran a separate cloud warehouse for analytics and BI alongside its processing platform and wanted a single place where data is processed, modelled and served. The stated aims, per the snippets, were unifying the warehouse, improving business-intelligence capability, tuning SQL query performance and cutting cost. General analysis: two engines means two copies of the important tables, two security models, and a team that pays twice for the same question.

### Constraints

As far as the summary states, the migration ran as a proof of concept followed by an incremental rollout, and the notable engineering friction was SQL syntax differences between the two systems, which implies existing queries, views and reports had to be rewritten and re-validated. BI consumers presumably needed continuity throughout (general analysis; not stated). Not stated: data volume, number of dashboards or models, team size, timeline, or which BI tool sits on top.

### Architecture as described

Data processing centralised on the Databricks platform with the warehouse layer served from it. The related vendor page's title refers to Databricks SQL serverless, but the blog snippet itself does not name the compute type, so that detail is unconfirmed here. One snippet attached to the result mentions that serverless SQL compute runs in the vendor's account with its own IP range, which suggests network allow-listing was part of the work; treat that as a hint, not a documented step.

### Evidence and its limits

The headline figure, reported by GetYourGuide, is a 20 percent reduction in operational costs. It is the reporter's own accounting; no baseline, period or cost definition is visible in the summary, so a reader cannot tell whether it covers licences, compute, storage, engineering time, or all of them, nor whether one-off migration effort was netted out. The vendor page cites separate performance figures; they are not adopted here. Query-latency, concurrency and dashboard-freshness outcomes are not stated.

### What transfers

Run a proof of concept on the queries that matter to finance and marketing before deciding, then move workloads incrementally so each cut-over has a rollback. Budget the real effort in dialect translation and result parity testing, not in infrastructure. Define "operational cost" before the migration so the after-figure means something. Unifying processing and serving pays mostly by removing copies and the reconciliation around them.

### Missing information

Ask which SQL constructs broke and how parity was proven; whether a transformation tool such as dbt was in the path; how long the two systems ran in parallel and who owned the final switch; concurrency and latency targets for dashboards; the cost breakdown behind the 20 percent; and what was deliberately left behind.
