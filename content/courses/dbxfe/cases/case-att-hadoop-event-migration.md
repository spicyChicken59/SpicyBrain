> Source review remains incomplete (24 September 2026). The cited session URL redirected to the generic Summit page; no session abstract was returned. The historical search-level analysis below is provisional; it has not passed direct-source review.

### Who reports this and how

The source is the Data + AI Summit 2024 session page "AT&T's Migration of Billions of Events Processing From Hadoop". The title names the customer as the subject, so this is treated as a customer-presented conference talk; presenter names are not visible in the snippets. Search results also surface a vendor customer page and a cloud-provider customer story about a related AT&T migration, with different and larger figures; they are deliberately not used as the source record. Session date: not stated beyond the 2024 event. The page itself could not be opened when this analysis was written; only its search-result title and snippets were read.

### The problem

A telecommunications company processed billions of events on a Hadoop estate using MapReduce jobs. Per the abstract, the aims were performance, scalability and cost. General analysis: MapReduce pipelines at this scale tend to accumulate hand-written job chains whose cost is paid in cluster hours and in the people who keep them running.

### Constraints

As far as the summary states, the migration meant converting MapReduce jobs into Spark jobs that run natively on the Databricks platform, so this was a code conversion effort, not a lift of existing binaries. Event volumes in the billions imply the converted jobs had to be validated for output parity under production load (general analysis). Not stated: the number of jobs, conversion tooling, timeline, cloud, or what remained on Hadoop.

### Architecture as described

Hadoop MapReduce event-processing jobs rewritten as Spark jobs on Databricks. No further detail on ingestion, storage format, orchestration or serving appears in the available summary. General analysis: a MapReduce-to-Spark port usually changes the physical plan substantially. Spark chains narrow steps inside a stage and avoids writing each intermediate job's output to replicated HDFS, but its shuffles still write to local disk and read over the network (see "Distributed execution and reading Spark evidence" under Related modules). That is where both the savings and the new failure modes come from.

### Evidence and its limits

The reported outcome, in the abstract, is a 30 percent reduction in compute costs, together with improved performance and scalability. The measurement is the presenters' own. The figure is stated for compute costs; the summary says nothing about storage, licensing or operations costs, so the effect on total cost is unknown. Nor does it state the baseline, whether performance was quantified, or how many jobs had been converted at the time. The larger return-on-investment figures on the vendor and cloud-provider pages come from different marketing contexts and cannot be reconciled with this session from snippets alone.

### What transfers

Inventory the jobs before promising a percentage; the saving is per job, and the long tail decides the total. Measure compute per job before and after, on comparable inputs, so the comparison survives questions. Treat MapReduce-to-Spark as a rewrite with parity tests, not a translation. And plan the decommissioning: cost drops only when the old cluster is switched off, not when the new one is switched on.

### Missing information

Ask how many jobs were converted and by what method (manual, assisted, automated); how output parity was verified at billions of events; the duration of the parallel run; what the 30 percent excludes; which jobs were retired rather than ported; and what operational metrics (failures, latency, on-call load) changed.
