### Who reports this and how

The source is a post on Coinbase's own engineering blog, "SOON (Spark cOntinuOus iNgestion) for near real-time data at Coinbase - Part 1", the first of a series (a "Part 2" on optimizations is also listed). The reporter is the customer: the post names Coinbase's Data Platform and Services team as the builders. Publication date: not stated in the available summary. Only the result title, URL and snippets were available; the page itself could not be opened when this analysis was written, so anything beyond the snippets is marked unknown below.

### The problem

Operational databases (PostgreSQL, MongoDB and DynamoDB are named) hold the freshest state but are built for transactional access. Analysts and incident responders needed the same rows in a warehouse where cross-table joins and aggregations are cheap, and with low latency: the summary ties the need to incident analysis and dashboard metrics. General analysis: this is the gap between where data is written and where it is questioned, and latency matters most when the reader is on call.

### Constraints

As far as the summary states: the solution had to replicate tables of any size in a timely way; it had to carry appends, updates and deletes rather than append-only events; the sink was Delta Lake; and SOON is said to handle latency, accuracy and reliability in a unified manner. Not stated: latency targets, volumes, cloud, team size, budget, or whether Databricks the product is involved at all (the named engine is Spark and the named table format is Delta Lake).

### Architecture as described

A home-grown framework built on Kafka, Kafka Connect and Spark that applies incremental changes to existing Delta tables and, by the same path, ingests native Kafka events. General analysis: change events are captured by connectors, buffered in Kafka, and applied by a continuously running Spark job as merge-style writes, so the target reflects deletes and updates instead of accumulating them.

### Evidence and its limits

The claim in the available summary is qualitative: SOON resolves data latency, accuracy and reliability issues in a unified manner and supports all three change types. Any measurement behind that was made by Coinbase and is not visible in the snippets; no throughput, latency or cost figure appears. A skeptical reader still cannot know the achieved end-to-end latency, the daily volume, what the previous path was and what it cost, how ordering and duplicates are handled, how the initial snapshot of a large table is taken, or whether any earlier path still serves some workloads.

### What transfers

Separate the replication problem (rows from an operational store into governed tables, with deletes) from the query problem; the first is where most reliability bugs live. Treat update and delete semantics as first-class from day one, because append-only ingestion silently produces wrong counts. Design for tables of any size by pairing a one-time backfill with an incremental stream. And read the existence of a follow-up "optimizations" post as a signal: the first working version of a continuous ingestion system usually needs a tuning round.

### Missing information

Ask for the latency objective and measured percentiles; daily change volume; the delivery guarantee (exactly-once or at-least-once with de-duplication) and how it is verified; how schema changes propagate to the Delta table; the backfill procedure for a multi-terabyte table; the run cost and on-call load; whether the framework runs on self-managed Spark or on Databricks; and which consumers depend on sub-minute freshness.
