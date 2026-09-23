<!-- section:dbxfe-finops-l01-outcome -->

After this lesson you can answer a sponsor's cost question as a FinOps practitioner: list the drivers in their own units and periods, choose compute from each workload's pattern, separate idle, startup and queue time, trace a failed launch to a cloud quota, attribute usage from the billable usage system table, compute unit economics with a guard and build a sensitivity table. Every rate here is a hypothetical rate, not a price.

<!-- section:dbxfe-finops-l01-start -->

Bring two earlier lessons: [Workspace, storage and compute](#/lesson/dbxfe-workspace-compute) separates compute from stored tables, and [Balance concurrency, latency and cost](#/lesson/dbxfe-m05-l03) introduced concurrency, latency and a controlled capacity experiment, which this lesson extends to money. SQL aggregation is enough for the usage queries. No workspace, billing access or paid service is needed; every figure belongs to fictional Cinderline and is synthetic.

<!-- section:dbxfe-finops-l01-drivers -->

Six drivers, each in its own unit: **compute time** (instance-hours of cloud machines), **platform usage** (DBUs; a DBU, or Databricks Unit, is a normalized unit of processing power used for measurement and pricing), **storage** (GB-months), **data movement** (GB), **operations effort** (hours per week) and a **migration one-off** (hours, once). On classic compute one running hour produces DBUs from Databricks and instance time from the cloud provider; what a serverless rate covers is read from [the current pricing page](https://www.databricks.com/product/pricing). A compute decision moves compute time and platform usage; the other four belong to other decisions and owners.

<!-- section:dbxfe-finops-l01-choose -->

| Workload pattern | Compute class | Verify first |
|---|---|---|
| Scheduled batch, idle between runs | Job compute created for each run, or serverless jobs | Startup share, serverless availability |
| People exploring in notebooks | All-purpose compute with auto-termination, or serverless notebooks | Who may create it, the idle limit |
| SQL and BI with concurrent readers | SQL warehouse: serverless, pro or classic | Type available, auto-stop minutes |
| Continuous stream | Pipeline or job compute sized for steady load | Steady usage per hour |

Lakeflow Jobs (formerly Databricks Workflows) schedules jobs; job compute terminates when its run completes, while all-purpose compute is interactive, shareable and restartable. Cinderline puts the nightly job on job compute, the morning report on one small SQL warehouse that stops after its window, and exploration on all-purpose compute under a policy. Size comes after the class.

<!-- section:dbxfe-finops-l01-time -->

**Utilization** is useful work divided by running time for one resource and period: a cluster running 08:00 to 18:00 for two busy hours is 2 ÷ 10 = 20 percent utilized. Without auto-termination an all-purpose cluster runs until stopped; a SQL warehouse stops after its auto-stop minutes, 120 by API default.

**Startup** is waited for, and often paid for, once per start: with a synthetic three-minute start, a six-minute job spends 3 ÷ 9 = 33.3 percent of its running time starting, a sixty-minute job 4.8 percent. Pools shorten starts; idle pool instances cost no DBUs, but the cloud provider bills them.

**Queue** time is arrivals beyond capacity. Query metrics record provisioning and at-capacity waits apart from execution, so a ten-second wait on a five-second query is diagnosed before anyone resizes. Size lets larger queries run; more clusters serve more concurrent ones.

<!-- section:dbxfe-finops-l01-limits -->

Classic compute launches instances in Cinderline's AWS account, so the cloud provider's quota can refuse a launch before any usage exists: a job that never started leaves a termination reason, not a usage row. AWS_RESOURCE_QUOTA_EXCEEDED means the account's limit, raised with the cloud provider or freed by stopping what holds it; AWS_INSUFFICIENT_INSTANCE_CAPACITY_FAILURE means the zone had no instances of that type, which a retry or a listed alternate node type addresses and a quota increase does not. A fallback type has its own rate.

<!-- section:dbxfe-finops-l01-attribution -->

Tags on clusters and SQL warehouses are written into every usage row they produce; serverless work takes its tags from a usage policy (formerly a budget policy). Rows keep the tags they had when the usage happened. The evidence is the billable usage system table:

```sql
SELECT custom_tags['project'] AS project,
       usage_unit,
       SUM(usage_quantity)    AS quantity
FROM system.billing.usage
WHERE usage_date BETWEEN '2026-09-01' AND '2026-09-30'
GROUP BY custom_tags['project'], usage_unit
ORDER BY quantity DESC;
```

A null project is usage nobody owns. Keep correction rows in every sum: a retraction negates an original row and a restatement carries the corrected value, so filtering to original rows overstates a corrected day. Rows arrive after the usage, so this table explains last week, not the last five minutes.

<!-- section:dbxfe-finops-l01-units -->

Unit economics divides the drivers a unit of work causes by the count of that work: the nightly job's 126 DBU × 0.50 + 36 instance-hours × 0.40 = 77.40 hypothetical USD over 30 runs is 2.58 per run. Adding 780.00 of operations effort gives a fully loaded 28.58, a different ratio that falls whenever runs rise. A month with no runs returns unknown with the reason, not 0.00 and not an error.

Sums follow the same discipline: 300 DBU + 120 instance-hours + 500 GB-month is refused, while priced with their own rates they make 150.00 + 48.00 + 10.00 = 208.00 hypothetical USD per month. Weekly effort becomes monthly by × 52 ÷ 12; a one-off stays apart.

<!-- section:dbxfe-finops-l01-sensitivity -->

**Hypothetical USD per month; every rate is a hypothetical rate, not a price.**

| Driver (low / base / high, rate) | Low | Base | High | Swing |
|---|---|---|---|---|
| Compute time (80 / 120 / 200 instance-hours at 0.40) | 32.00 | 48.00 | 80.00 | 48.00 |
| Platform usage (200 / 300 / 500 DBU at 0.50) | 100.00 | 150.00 | 250.00 | 150.00 |
| Storage (400 / 500 / 800 GB-month at 0.02) | 8.00 | 10.00 | 16.00 | 8.00 |
| Data movement (120 / 240 / 600 GB at 0.05) | 6.00 | 12.00 | 30.00 | 24.00 |
| Operations effort (1.5 / 3 / 6 hours a week at 60.00) | 390.00 | 780.00 | 1,560.00 | 1,170.00 |
| **Recurring total** | **536.00** | **1,000.00** | **1,936.00** | **1,400.00** |
| Migration one-off, kept apart (150 / 250 / 400 hours at 60.00) | 9,000.00 | 15,000.00 | 24,000.00 | 15,000.00 |

Effort swings the month more than every other driver together, so logged hours are the first measurement. The base case is the 12,000 recurring and 15,000 one-time hypothetical figures that [Make a transparent value calculation](#/lesson/dbxfe-m11-l03) assumes, now in drivers a reader can challenge.

<!-- section:dbxfe-finops-l01-governance -->

Budgets watch cumulative monthly spend, in list-price US dollars in the current API, and alert recipients at thresholds; the API also lists a block-usage action, whose scope you verify on the [budgets page](https://docs.databricks.com/aws/en/admin/account-settings/budgets) before relying on it. Dashboards and tags make usage visible and attributable. Compute policies limit what users can create, and auto-termination and auto-stop end idle compute. Give every alert an owner and an action. Nothing here guarantees a level of spend.

<!-- section:dbxfe-finops-l01-experiment -->

Lab L13's synthetic runs repeat the same 1,000 work items on each configuration, priced at 0.50 hypothetical USD per DBU:

| Configuration | Runs used | Median seconds | Cost per 1,000 items (min / median / max) | Caveat |
|---|---|---|---|---|
| small | 3 | 630 | 2.00 / 2.10 / 2.20 | a failed run's 1.0 DBU is spent with no work |
| large | 3 | 270 | 2.40 / 2.70 / 3.00 | an instance-hour row refused |
| xlarge | 1 | 200 | 4.00 | one run: not ranked |

Small is cheaper per unit of work across these runs and large is faster; with the nightly job due by 07:30, small fits unless measured production runs disagree. The runs show the method, not a benchmark.

<!-- section:dbxfe-finops-l01-exercise -->

A second plant joins in October. Its morning report adds up to eight overlapping queries, the nightly job runs once per plant, and a new analyst team asks for its own all-purpose cluster. (1) Say which worksheet drivers change and which do not. (2) Choose compute for the second nightly run and for the new team. (3) Name the evidence you would read before resizing the warehouse. (4) Write the attribution and policy changes that make October's usage owned. (5) Give the sponsor a new base month with its range, labelled hypothetical, and the one input you would measure first.

<!-- section:dbxfe-finops-l01-solution -->

(1) Compute time and platform usage rise with the second run and the extra concurrency; storage and movement rise with the new data; effort may rise and stays the widest input; the one-off is unchanged unless the plant needs its own cutover. (2) A second job compute run, or a second task in the same job, not a longer-lived cluster; the new team works under the analysts' policy with auto-termination and a required team tag. (3) Busiest-minute query timings: add a cluster only if at-capacity waiting appears, a larger size only for spilling queries. (4) Project and plant tags everywhere, a usage policy for serverless notebooks, a weekly query for untagged usage. (5) Recompute the worksheet, report base with low and high, keep the migration apart and name effort as the input to measure; every figure stays hypothetical until rates are read from current pricing.

<!-- section:dbxfe-finops-l01-mistakes -->

- **Adding unlike units.** DBU plus instance-hours plus GB-months is not a total.
- **Reading a week as a month.** Three hours a week is thirteen a month; the error here is 600.00.
- **Resizing for a queue.** Waiting at capacity needs clusters or a new arrival time, not size.
- **Trusting a budget to stop spend.** An email alert informs; policies and auto-termination act.
- **Tagging after the fact.** Rows keep their tags; allocate old rows by a stated rule.
- **Printing 0.00 for zero work.** The cost per unit is unknown, with its reason.
- **Ranking one run.** A single observation has no spread.
- **Quoting a rate from memory.** Real rates come from current pricing, dated; this lesson quotes none.

<!-- section:dbxfe-finops-l01-sources -->

Databricks: [Compute](https://docs.databricks.com/aws/en/compute/), [SQL warehouse sizing, scaling, and queuing behavior](https://docs.databricks.com/aws/en/compute/sql-warehouse/warehouse-behavior), [Billable usage system table reference](https://docs.databricks.com/aws/en/admin/system-tables/billing), [Create and monitor budgets](https://docs.databricks.com/aws/en/admin/account-settings/budgets), [Cost optimization for Databricks](https://docs.databricks.com/aws/en/lakehouse-architecture/cost-optimization/) and [Databricks pricing](https://www.databricks.com/product/pricing), with field docstrings read from the [databricks-sdk 0.141.0 package](https://pypi.org/project/databricks-sdk/0.141.0/). Documentation pages were not opened in this build; each source record states what was checked. Every rate and figure here is synthetic.

<!-- section:dbxfe-finops-l01-related -->

[SQL, analytics and performance](#/module/dbxfe-m05) diagnoses slow queries; [Make a transparent value calculation](#/lesson/dbxfe-m11-l03) turns this cost side into a value case; [platform mental models](#/module/dbxfe-m03) place classic and serverless compute. The compute choice and cost and value field guides turn this lesson into templates, and Lab L13 runs the worksheet and the experiment locally.

<!-- section:dbxfe-finops-l01-revisit -->

Return here when a cost question arrives with one number attached. Ask: which drivers, in which units and periods; which compute class fits each pattern; how much running time is idle, starting or queued; which rows carry which tags; what a unit of work costs, with a guard; and which input moves the answer most. Then read the usage rows.
