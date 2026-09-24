### Who reports this and how

GetYourGuide's engineering article was published on 29 January 2025; it names Robert Bemmann and Houkun Zhu. The body was inspected on 24 September 2026, including Motivation and scope, PoC, Cost projection and Conducting the migration.

### The problem

The team wanted to serve Looker from its Databricks data platform and eliminate redundant warehouse copies.

### Constraints

The article identifies 750 tables, 25 Looker models and over 20,000 distinct queries requiring validation. Two internal engineers led the work with external support. Minimal disruption was an explicit objective.

### Architecture as described

Airflow loading, Delta tables and incremental Looker model migration are described. Network connectivity and SQL dialect differences required attention; the historical implementation is not a current cloud-networking prescription.

### Evidence and its limits

The authors report 20% lower costs. Their PoC compared frequently used dashboards through Looker over five runs, with mixed performance outcomes. The cost projection separates BI compute, copy-related ETL and storage. Neither the headline nor the projection establishes another organization's return or a complete accounting of migration labor.

### What transfers

Authored analysis: benchmark the user-facing report, including its query generation, rather than only the database console. Model dependencies before cutting over shared views. Keep parity checks and rollback criteria beside performance checks.

### Missing information

Request the reproducible benchmark inputs, production reconciliation results, ongoing tuning effort and full migration-cost accounting. Team size, BI tool, table count and the comparison method are stated in the article and should not be called unknown.
