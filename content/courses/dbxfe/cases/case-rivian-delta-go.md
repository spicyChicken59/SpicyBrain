### Who reports this and how

The source is a post on the Delta Lake project blog at delta.io, titled "Rivian expands the Delta Lake ecosystem with Delta-Go". Search results also surface the public repository github.com/rivian/delta-go, which corroborates that the connector is real and open source. Authorship is not visible from the snippets: the post may be written by Rivian engineers on the community blog or by project maintainers describing Rivian's contribution, so this analysis labels the reporter as joint. Publication date: not stated in the available summary. The page body was not fetched in this build (egress blocked); only the title, URL and snippets were read.

### The problem

Rivian, an electric-vehicle manufacturer, ingests packet captures (PCAP data taken from vehicle network interfaces) from a reported fleet of more than 80,000 connected vehicles, at a reported rate of 9.8 million records per second. Per the source, the earlier design wrote the same data twice, once as Parquet and once as Delta, and kept 20 Spark workers running continuously just to land it. The cost of that always-on landing path, and the duplication itself, are the stated motivations.

### Constraints

As far as the summary states: the ingestion service is written in Go and needed to write Delta tables directly rather than through Spark; Spark jobs and the Go service write to the same tables, so concurrent commits had to be made safe; ingestion is event-driven from queue notifications; and the service runs on Kubernetes. AWS services (SQS, DynamoDB) are named, which implies object storage without native put-if-absent at the time. Not stated: retention, schema, downstream readers, latency targets.

### Architecture as described

A Go application on Kubernetes consumes SQS notifications and writes directly into Delta tables through Delta-Go, reportedly reaching about 10 commits per second on the table. A DynamoDB-backed log store coordinates commits so that simultaneous writes from Spark and Delta-Go do not race each other. General analysis: this is the standard multi-writer pattern for Delta on S3, where an external lock or conditional-write service stands in for the atomic rename other stores provide.

### Evidence and its limits

Figures reported by the source: 80,000+ vehicles, 9.8 million records per second, roughly 10 commits per second, removal of 20 continuously running Spark workers, and an estimated saving of about 500 dollars per day. All are the reporter's own estimates or measurements; none is reproduced here. A skeptical reader cannot tell whether the dollar figure is a full before-and-after cost or only the removed workers; what 10 commits per second does to file counts and compaction cost; end-to-end latency; how correctness of the Go writer was validated against Spark; and the maintenance burden of a custom connector as the Delta protocol evolves.

### What transfers

Two writers on one Delta table need a coordination mechanism, and on S3 that is an explicit design decision, not a default. Commit frequency is a trade-off: fast commits give fresh tables and many small files, so a compaction schedule belongs in the design. Writing data once, in one format, removes a whole class of reconciliation work. Polyglot writers are viable, but you then own protocol compatibility (reader and writer versions, newer table features) for as long as the connector lives.

### Missing information

Ask about typical file sizes and the OPTIMIZE cadence; which Delta protocol features the connector supports and refuses; how failed or partial commits are retried; who reads the tables and at what freshness; whether the 500-dollar estimate includes DynamoDB, SQS and Kubernetes costs; and who maintains the connector today.
