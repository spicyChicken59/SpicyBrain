<!-- section:action -->

Choose compute for one workload at a time, from its pattern, and write down what you assumed. "Bigger" is not a choice; "this pattern, this concurrency, this latency tolerance, on this compute, until this evidence says otherwise" is.

1. **Describe the workload pattern**: interactive queries from people, a scheduled job, a continuous stream, model training, or a mixture. Note when it runs, for how long, and whether it is idle between runs.
2. **Estimate concurrency from observation**, not from headcount: how many queries actually overlap at the busiest minute, and what they are.
3. **State the latency the decision tolerates**, with its clock: seconds after a click, minutes after source availability, or hours overnight. Separate startup and queueing from execution.
4. **Match pattern to compute class**: job compute that starts, runs and stops for scheduled work; a SQL warehouse sized for the concurrent interactive load; serverless where startup latency and operations matter more than control, if the customer's policy permits it.
5. **List the operational limits**: who may change the configuration, quotas in the cloud account, auto-stop and scaling settings, and how usage will be attributed to this workload.
6. **Write the evidence that would change the choice** and where it will come from: query history, system usage tables, a repeated measurement.

Go deeper: [compute choices, cost and FinOps reasoning](#/module/dbxfe-finops), [balance concurrency, latency and cost](#/lesson/dbxfe-m05-l03), [workspace, storage and compute](#/lesson/dbxfe-workspace-compute), [SQL analytics and performance diagnosis](#/module/dbxfe-m05) and [platform mental models](#/module/dbxfe-m03) for what each compute class is responsible for.

<!-- section:example -->

### Compute choice: Cinderline Components (fictional), two pilot workloads

All figures are fictional observations from the five-day baseline or stated assumptions; none is a platform benchmark or a price.

#### Workload 1: the nightly resolution job

**Pattern.** A scheduled batch: read the day's extract of inspections and the correction export, resolve revisions, quarantine conflicts, write the accepted table. Runs once after the ERP export, which the DBA says completes before 6:00 a.m. (stated, not measured). Idle the rest of the day. The synthetic run processed a few thousand rows in under two minutes on a small local engine; the real volume for one plant is estimated by the data lead at tens of thousands of rows per day, not measured.

**Concurrency.** One run. A rerun after a failure must not overlap the scheduled run.

**Latency tolerance.** The accepted table must exist by 7:30 a.m.; the job may take an hour. Startup time is irrelevant at this tolerance.

**Choice.** Job compute created for the run and terminated after it, single small node class, no autoscaling, with a retry policy and a lock so a rerun waits for a running instance. Serverless job compute is the alternative if the security lead accepts its connectivity pattern; it removes the startup and node-class decisions but that is not yet permitted.

**Operational limits.** The data team owns the job definition; only the platform administrators change the compute policy. Usage is tagged to the pilot. Cloud quota for the instance family is not confirmed.

**Evidence that would change this.** A measured run over real volume longer than 40 minutes (the margin to 7:30 disappears); an export finishing later than 6:30 a.m. on any test day; a second plant joining, at which point the run either partitions by plant or grows.

#### Workload 2: the morning report

**Pattern.** Interactive, concentrated between 7:30 and 8:15 a.m. plant time, then near idle. Five saved queries on the accepted table, each returning a few hundred rows.

**Concurrency.** The baseline counted eleven distinct users on the busiest morning and at most four overlapping queries in any minute, all of them the saved dashboard queries. Headcount would have suggested thirty.

**Latency tolerance.** The operations director tolerates "a few seconds after opening the page" and would not accept a minute. The baseline measured the existing SQL Server report at 15 to 45 seconds depending on the morning; users say the variance is the annoyance.

**Choice.** One small SQL warehouse, auto-stop after the morning window, scaled for four concurrent queries with headroom for eight. Because the window is predictable, a scheduled start ten minutes before 7:30 avoids a cold start for the first user; that choice is recorded as an assumption to test. Serverless would remove the start question entirely and is the preferred alternative once policy allows it.

**Operational limits.** Analysts cannot resize the warehouse. The dashboard's refresh is scheduled once after the nightly job completes, so the morning queries hit cached results where the platform permits and are not re-executed thirty times.

**Evidence that would change this.** Queue time above five seconds in the busiest minute on more than one test day; queries other than the saved five appearing in the history, which would mean the pattern is not what was assumed; a second plant doubling the concurrent load.

#### What was not chosen and why

An always-on all-purpose cluster for both workloads: idle most of the day and shared between a batch job and interactive users, which makes the morning latency depend on the job's timing. A larger warehouse "to be safe": it buys capacity for a concurrency nobody observed and hides the cache question.

#### Conclusion

Two workloads, two compute choices, each with a written assumption and the observation that would overturn it. Neither is a cost claim; the cost worksheet takes these choices as inputs and states its own currency, period and sources.

<!-- section:template -->

### Compute choice

#### Workload

- Name; the decision it serves; the pattern (interactive, scheduled, streaming, training, mixed); when it runs and for how long; what it is between runs.

#### Concurrency

- Observed overlap at the busiest minute, from which record and which days; not headcount.

#### Latency tolerance

- The clock and the threshold the decision tolerates; startup, queueing and execution separated.

#### Choice

- The compute class and its settings (size, scaling, auto-stop, retries, policy); the alternative not taken and the condition under which it becomes preferred.

#### Operational limits

- Who may change the configuration; cloud quotas and their status; how usage is attributed; who is paged when it fails.

#### Assumptions

- Each stated or estimated figure with its source and whether it is measured.

#### Evidence that would change this

- Specific observations and where they come from (query history, usage tables, a repeated timed run).

<!-- section:limits -->

This guide produces a defensible starting choice and the evidence plan to revise it; it cannot establish the workload's real concurrency, volume or run time until they are measured, and a synthetic run says nothing about production duration. It is not a cost model: no price, discount or saving follows from a compute choice without a worksheet that states currency, period, sources and what is excluded. Availability of a compute class, and whether policy permits it, is confirmed by the customer's administrators and current documentation, not by this guide. Escalate when a stakeholder wants capacity chosen from headcount, when the security lead has not ruled on the connectivity pattern a class requires, or when the customer asks for a guaranteed latency.
