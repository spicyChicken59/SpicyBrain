### Who reports this and how

Coinbase's Data Platform & Services Team published Part 1 on 25 January 2023. The article body was inspected on 24 September 2026, including Architecture, Performance, Unified Ingestion Framework and SOON Table Onboarding. Results are company-reported, not reproduced here.

### The problem

Operational data needed to reach analytical consumers without losing updates or deletes. The article describes unstable timestamp-based replication and losses during traffic spikes in an earlier path.

### Constraints

SOON must support CDC and non-CDC events while balancing freshness against compute expense.

### Architecture as described

Kafka, Kafka Connect and Spark feed Delta on S3. Large-table bootstrapping uses a Snowflake snapshot and overlapping Kafka offsets; Delta CDF carries changes onward to Snowflake. Small tables can start with connector snapshots.

### Evidence and its limits

The reported configurations are 15 minutes for the largest append workload, 30 minutes for the largest CDC merge workload, and one minute for some smaller tables. These are configured cadences, not measured latency percentiles or an exactly-once guarantee. The article also gives throughput examples; it does not publish a complete operating-cost or correctness study.

### What transfers

Authored analysis: make bootstrap overlap, delete handling and duplicate handling separate acceptance tests. A fast ingestion job can still produce stale or inconsistent reports. Ask the consumer which delay changes a decision before paying for a faster cadence.

### Missing information

Request measured end-to-end latency distributions, reconciliation results, ordering and replay guarantees, ongoing cost and operational ownership. The initial snapshot method is described; its production correctness evidence remains a separate question.
