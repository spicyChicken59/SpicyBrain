<!-- section:dbxfe-operations-l01-outcome -->

After this lesson you can operate a data product. You can say which of four properties a report breaks, write objectives you can count, pick the system record that answers each incident question, keep facts apart from hypotheses on a timeline, and write a recovery plan whose data-loss window is stated before anyone runs a command. You can also say why table history is not a backup and what a managed recovery feature covers. Every figure is from a fictional Cinderline Components incident; nothing was run against a workspace.

<!-- section:dbxfe-operations-l01-start -->

Bring the orchestration picture from [Orchestration and operations](#/module/dbxfe-orchestration): jobs, tasks, retries, repair and the boundaries between raw retention, publication and external effects. [Orchestration, failure, and reconciliation](#/lesson/dbxfe-m04-l03) already showed that a green task is one piece of evidence; this lesson starts with a run that succeeded and published a wrong number. Delta versions and time travel are taught in [Delta Lake: files, log and snapshots](#/module/dbxfe-delta); here they are used for recovery.

<!-- section:dbxfe-operations-l01-properties -->

Readers depend on four properties that fail separately. **Availability**: can they read it when they need it? **Durability**: is committed data kept and recoverable? **Freshness**: is it recent and complete? **Correctness**: is it right?

On Tuesday at Cinderline, run r-7731 of the nightly job ended SUCCESS at 02:31, the Morning quality dashboard answered at 06:00 in 1.8 seconds, and every write was kept. Line 3 still showed 0.4% scrap for Monday against 3.1% recounted from raw records. Availability, durability and freshness held; correctness broke. Durability even kept the mistake: a wrong write is committed as durably as a right one.

<!-- section:dbxfe-operations-l01-objectives -->

An objective is a count: good events over valid events in a window, with the misses it allows as the error budget.

| Property | Good event | Valid events | Objective (28 days) |
|---|---|---|---|
| Freshness | All three lines in gold by 06:00 | Production days | 27 of 28 |
| Correctness | Line-day rate within 0.05 points of a raw recount | Published line-days | 83 of 84 |
| Availability | Dashboard query succeeds within 5 s | Dashboard queries 05:30 to 18:00 | 99% |
| Durability | A restore drill meets the recovery point objective (RPO) of 1 hour and recovery time objective (RTO) of 4 hours | Quarterly restore drills | Every drill |

INC-0412 is one bad line-day: it spends the whole correctness budget, so reliability work goes first.

<!-- section:dbxfe-operations-l01-evidence -->

Each record answers one question. Job run history and the system.lakeflow run timeline: how did the run end? The audit log, system.access.audit: who changed the job? Table history: what did each write do? Query history, system.query.history: who read the figure? Lineage: what depends on the table? Each has limits: runs leave the Jobs API after 60 days, most audit logs are regional, query history covers SQL warehouses and serverless compute, table history defaults to 30 days, and lineage covers queries run on Databricks.

Metrics notice and logs explain. Rows changed per run sat between 31 and 52, then jumped to 218; the task log and table history split that into 44 merge changes and 174 updates by a new cleanup step:

```sql
DESCRIBE HISTORY silver.inspections LIMIT 5;
-- 313  02:16  UPDATE  job quality-nightly  numUpdatedRows 174
-- 312  02:09  MERGE   job quality-nightly
```

No record says whether 0.4% is right; only an independent recount does.

<!-- section:dbxfe-operations-l01-ownership -->

A Unity Catalog owner holds privileges; an operational owner is paged. Cinderline's register names the on-call rota, the plant quality manager who decides whether a figure may be used, the Line 3 export team upstream, and the catalog owner group for access.

Job failure notifications cover runs ending FAILED, TIMED_OUT or with an internal error, so they could not see INC-0412. A SQL alert on a reconciliation query, published rate against raw recount, would have triggered at 02:40 and paged the rota. Give it a rearm interval, route it to the rota and link its runbook.

<!-- section:dbxfe-operations-l01-example -->

At 06:12 a quality lead reports that Line 3's 0.4% looks too good. Triage sorts by shape before cause:

| Shape | First evidence | Containment |
|---|---|---|
| Unavailable | Query history, warehouse state | Point readers to yesterday's export |
| Stale | Run history, completeness gate | Keep the stale label; hold publish |
| Wrong | Table history, recent changes, recount | Label under review; pause the writer |
| Lost | Table history, retention, backups | Stop writers; suspend VACUUM and other cleanup |

A wrong figure used at the 06:00 review makes it severity 2, declared at 06:30. The timeline keeps facts (time and source) apart from hypotheses (label and test):

| Time | Entry | Kind |
|---|---|---|
| 02:31 | Run r-7731 SUCCESS (job run history) | Fact |
| 06:35 | H1: Line 3's file was late | Hypothesis |
| 06:50 | H2: version 15's cleanup step blanked codes | Hypothesis |
| 07:05 | Landing record: Line 3 file at 01:22, 6,450 rows. H1 refuted | Fact |
| 07:40 | Cleanup step on a copy of version 312: 174 codes blanked, 3 of 3 runs. H2 confirmed | Fact |
| 07:45 | Nightly job paused by the operations lead | Fact |

<!-- section:dbxfe-operations-l01-dependency -->

H1 was wrong on Tuesday, but it had happened before. Two weeks earlier Line 3's file landed at 03:05; the 02:00 run read two files, ended SUCCESS and published a plant figure without Line 3. A file arrival trigger can wait for file activity to stop, but it cannot know a third file is due. A completeness gate compares landed files with the day's manifest, holds publication until an agreed deadline, then publishes with a visible label and pages the upstream owner.

<!-- section:dbxfe-operations-l01-recovery -->

Restoring to the last good version discards every later commit, not only the bad one.

```sql
RESTORE TABLE silver.inspections TO VERSION AS OF 312;  -- commits version 317
```

| Item | INC-0412 |
|---|---|
| Restore point | Version 312, 02:09, recount 3.1% |
| Data-loss window | Versions 313 to 316, 02:16 to 07:10 |
| Discarded | 174 bad updates, 25 corrections |
| Replayed | 25 of 25 from the correction queue (9 + 10 + 6) |
| Lost for good | None |
| Time | Declared 06:30, verified 09:40, against a 4-hour RTO |

Pause every writer and the feature stream first; afterwards rebuild the stream's output instead of reprocessing restored files.

<!-- section:dbxfe-operations-l01-backup -->

Table history is not a backup. Databricks advises against using it for long-term archival; with default retention VACUUM removes files older than 7 days, and a deleted storage location or an unavailable region takes the history with it. A backup strategy adds an independent copy in another failure domain (the deployment guide suggests deep clone for critical tables) refreshed often enough for the RPO, replayable raw files and queues, jobs and grants kept as code, and timed restore drills.

Managed promises have documented edges. Control plane high availability is described with a 15-minute RTO and 0 RPO, but customer data sits in Cinderline's own storage under Cinderline's RPO. Managed disaster recovery is gated and replicates opted-in categories up to a replication point.

<!-- section:dbxfe-operations-l01-communication -->

A runbook is a rehearsed decision path for one failure shape: trigger, containment, evidence, decision, action, verification, communication. Recovery is verified by a raw recount and matching counts, not by a command returning.

Update 2 at 08:30 read: *Impact:* Line 3's Monday scrap rate (0.4%) is wrong; Lines 1 and 2 are correct. *Do:* do not use it; the raw recount is 3.1%. *Known:* a cleanup step deployed Monday blanked 174 codes; the job is paused. *Not yet known:* whether the weekly export read Monday's data. *Next update:* 10:00.

The blameless review then turns conditions into owned, dated actions: a reconciliation gate, a test fixture with every line's codes, a deploy check on the code list, and alerts routed to the rota.

<!-- section:dbxfe-operations-l01-task -->

A supplier asks why 1,380 lots are missing from gold.supplier_lots. Twelve days ago a maintenance notebook ran a DELETE whose predicate `status LIKE 'test%'` also matched real lots with status `test-passed`, received over the 40 days before it ran. VACUUM runs nightly with default retention. Raw supplier files are kept 30 days. A nightly deep clone overwrites one copy in a second region.

Classify the failure, list two facts with their sources and one hypothesis with its test, choose a recovery approach, state what is recovered and what is lost for good, and write one prevention action.

<!-- section:dbxfe-operations-l01-solution -->

**Shape:** lost, and wrong for every report that counts lots. **Facts:** table history, kept 30 days, shows a DELETE twelve days ago with numDeletedRows 1,380, its predicate and the notebook that ran it; the landing log shows supplier files retained back 30 days. **Hypothesis:** the predicate matched `test-passed`; test by counting deleted lot IDs whose status in the raw files is `test-passed`.

**Recovery:** time travel cannot help. History still lists the version before the DELETE, but VACUUM has removed its files past the 7-day retention, and the clone was overwritten after the delete. Rebuild forward: re-insert the deleted lots from raw files. Lots received 12 to 30 days ago are in the files (610 in this exercise); lots received 30 to 52 days ago (770) are not, and are lost for good unless the supplier re-sends them. No later commit is discarded, because nothing is restored.

**Prevention:** keep dated clones rather than one overwritten copy, and alert on rows deleted per run.

<!-- section:dbxfe-operations-l01-limits -->

Common mistakes: reading SUCCESS as correct; routing alerts to a person; treating a missing lineage edge or a missing audit row as proof of absence; restoring without stating the window; calling time travel a backup; quoting "Databricks handles DR" without its scope. Limits: the queries were not executed, column names must be checked against current references, retention and regional scope vary by table, and managed disaster recovery's availability, tier and cost are verification items.

<!-- section:dbxfe-operations-l01-sources -->

The Databricks on AWS pages for system tables and their audit, jobs and query history references, job monitoring, lineage, table history, disaster recovery, the high-availability deployment phase, managed disaster recovery and reliability, and the Google SRE chapters, were confirmed by search-result title and snippet on 23 September 2026; their bodies were not fetched because the sandbox blocks the documentation host. Terraform provider, SDK and Delta Lake source files were read from their repositories. Documented behaviour, original guidance and fictional Cinderline records are labelled separately.

<!-- section:dbxfe-operations-l01-links -->

[Orchestration and operations](#/module/dbxfe-orchestration) owns retries, repair and boundaries. [Write follow-ups people can act on](#/lesson/dbxfe-m12-l02) and the Escalation packet field guide cover writing for a specialist; this lesson's update is for readers. [Unity Catalog names and basic access](#/lesson/dbxfe-m06-l01) owns privileges and ownership.

<!-- section:dbxfe-operations-l01-revisit -->

Redo the exercise with the raw files kept 60 days and see which part of the answer changes. Opening a section or revealing a solution records no completion; mark completion yourself when you choose.
