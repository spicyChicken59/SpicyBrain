<!-- section:dbxfe-warehouse-migration-l01-outcome -->

After this lesson you can assess an analytics estate before moving any of it: inventory it by readers rather than objects, give each workload one disposition, find and bridge the dependencies a wave boundary cuts, and profile legacy, Hadoop and cloud source platforms in their own vendors' words. You can separate silent dialect and engine differences from loud ones, prove results, performance and permissions separately, and sequence waves through pilot, parallel run, cutover and rollback. Everything at Cinderline here is fictional, and nothing is executed.

<!-- section:dbxfe-warehouse-migration-l01-start -->

Bring the retained [Architecture and migration](#/module/dbxfe-m08) module: target designs in [Turn current state into a target design](#/lesson/dbxfe-m08-l01), and basis alignment, cutover and recovery after a switch in [Migrate with reconciliation and rollback](#/lesson/dbxfe-m08-l03). The SQL Server module takes one procedure apart; this lesson works at the scale of an estate. The Migration inventory, Reconciliation plan and Cutover and rollback plan field guides hold the templates, and the enterprise coexistence capstone is where you practise the whole method.

<!-- section:dbxfe-warehouse-migration-l01-inventory -->

Cinderline's analytics run on three estates: Basalt, a fictional on-premises warehouse appliance with its own dialect; an Apache Hadoop sensor cluster; and Pellworth Castings, an acquired business on Amazon Redshift. Joining Basalt's catalog to 90 days of query history (synthetic figures) changes the size of the job:

| Basalt tables | Count | Meaning |
|---|---|---|
| Read by people or reports | 610 | Work with consumers |
| Read only by scripts | 410 | Moves with its producers |
| No reader | 220 | Retire once owners confirm |

Twelve procedures that build table names at run time and three desktop extracts become named gaps. Each workload then gets one disposition (stay, coexist by sharing or federation, migrate in a wave, retire, or not yet), one driver and the evidence that would make it agreed.

<!-- section:dbxfe-warehouse-migration-l01-dependencies -->

Draw jobs, tables and reports as a graph and colour wave 1. Two edges cross its boundary: the plant dashboards (wave 1) read line_health, which a Spark 2.4 job writes into Basalt until wave 2, and Basalt's finance marts read scrap cost from the quality mart that wave 1 moves. Each cut edge gets a bridge: a forward federated read or nightly copy of line_health until wave 2, and a backward sync-back into Basalt for finance until the finance marts move. Both bridges carry an owner, a freshness target and an end date.

<!-- section:dbxfe-warehouse-migration-l01-platforms -->

Profile each source in its own vendor's current words before mapping it. In this build each vendor page's title and search snippet were confirmed, Microsoft's Fabric source and AWS's archived Redshift guides were read in full, and Snowflake and BigQuery detail beyond their snippets is marked as previously read.

| Question | Legacy appliance | Hadoop and Spark | Cloud warehouse |
|---|---|---|---|
| Storage | Appliance disks | HDFS blocks; Parquet, ORC | Per vendor profile |
| Metadata | Appliance catalog | Hive metastore | Per vendor profile |
| Engine, dialect | Vendor SQL | Spark and Hive versions | Per vendor profile |
| Security | Grants, security views | Path permissions, ACLs | Per vendor profile |

A Hadoop estate moves on four tracks: files to object storage, metastore tables into Unity Catalog, jobs onto a current Spark runtime, and path permissions into table grants. Spark's migration guide shows why the engine is its own track: since 3.0 a new calendar changes dates before 1582 and inserts follow ANSI store assignment; since 4.0 ANSI mode is on by default.

<!-- section:dbxfe-warehouse-migration-l01-dialect -->

Classify every difference as loud at compile, loud at run time, or silent. The silent ones matter most:

```sql
-- Basalt (fictional): 7 / 2 = 3; 5 / 0 = NULL; NULLs sort last
-- Spark 4.0: / is floating point (3.5); ANSI mode raises on 5 / 0;
-- ascending sorts put NULLs first unless NULLS LAST is written
SELECT plant,
       CASE WHEN inspected = 0 THEN NULL          -- div also raises on 0 under ANSI
            ELSE defects * 100 div inspected END AS pct_truncated
FROM quality_day
ORDER BY reject_code ASC NULLS LAST;
```

Conversion tools such as Lakebridge (a Databricks Labs project whose release 0.15.2 is classified Beta, provided as-is without formal support, with experimental reconcile commands) size the work and fix the loud differences. A conversion rate is a syntax measure. Results, performance and permissions are three separate equivalences, each with its own test: keyed reconciliation, a replay of recorded queries, and a persona outcome matrix.

<!-- section:dbxfe-warehouse-migration-l01-security -->

Map security by intent. Write, for each persona and object, what the source allows; translate; then run the same queries as each persona on both paths. Basalt's view-based plant filter becomes a row filter, masked supplier prices a column mask, and per-table grants stay per table, because a Unity Catalog schema grant also reaches future tables. Redshift's row-level security, masking policies and role inheritance, and HDFS path permissions, are mapped the same way.

Choose data movement per dataset: copy and load incrementally (survives a source outage, lags it), federate (read-only, fails with its source), share (the owner stays the writer and can revoke future access), or re-derive from upstream. For reports, move the meaning, not only the connection: measures, rules in source views, refresh schedule and identity. Cinderline's dashboard differed on 3 of 30 days until the 06:00 cutoff and test-lot exclusion moved out of Basalt's view into one governed definition.

<!-- section:dbxfe-warehouse-migration-l01-validation -->

Set each workload's risk class before the first comparison, by the consequence of a wrong number:

| Check | Class 1: money | Class 2: operational | Class 3: exploratory |
|---|---|---|---|
| Keys | Every key | Every key | Every key |
| Fields | All | Reported | Key fields |
| Parallel run | Full close cycle | 5 clean days | 2 clean runs |
| Sign-off | Business and control | Business owner | Data owner |

Every class writes the basis first, and tolerances exist only when stated before the run.

<!-- section:dbxfe-warehouse-migration-l01-sequence -->

Order waves by dependencies and fixed blackouts: foundations (identity, catalog, network, reconciliation harness), the plant-quality pilot, the sensor cluster, finance after the year-end close, then decommissioning. During coexistence each dataset has one writer: Basalt writes the quality mart until cutover and the lakehouse afterwards, with a read-only sync-back to Basalt for finance until wave 3. Each step ends in a test: the pilot in keyed and persona checks for one plant; the parallel run in five consecutive clean days, restarted by any fix; cutover in written entry conditions; rollback in rehearsed triggers; cleanup only after the recovery window and the owners' acceptance.

<!-- section:dbxfe-warehouse-migration-l01-example -->

**Cinderline's assessment (fictional).**

- **Dispositions:** plant-quality mart, migrate in wave 1 as the pilot; sensor jobs, wave 2; finance close marts, not yet (reconsidered 15 February); Pellworth, coexist by federation after its security review; 220 unread tables, retire; supplier extract, stay by contract.
- **Bridges:** line_health read forward until wave 2; a sync-back to Basalt for finance until wave 3.
- **Profile unknowns:** Pellworth's export path, node type and policy list (Pellworth's leads); federation connector support (Cinderline's data lead).
- **Risks:** integer division, NULL ordering and a business-day function in Basalt SQL; a TINYINT insert that Spark 2.4 wrapped silently.
- **Equivalence:** 33 of 38 pilot scripts equal on keyed results; two dashboards over the 10-second p95 target; one widened grant fixed.
- **Wave 1:** class 2, day 3 of 5 clean; rollback rehearsed in 20 minutes against a 30-minute target.

The steering group's 'everything by the renewal date' is answered with what the evidence supports: one wave proven, two planned, one deliberately waiting.

<!-- section:dbxfe-warehouse-migration-l01-exercise -->

Harrowmere, a second fictional plant group, runs supplier analytics on Snowflake (60 tables, 12 dashboards) and a Hadoop cluster whose Spark 3.1 jobs write ORC files, some holding 0001-01-01 as an 'unknown date' placeholder. Its finance team reads a Snowflake view every morning. Write a one-page assessment: dispositions with drivers, the cut dependencies, the Snowflake profile cells you can source and those you cannot, the engine and dialect risks, the persona tests, the risk classes and wave 1's exit test.

<!-- section:dbxfe-warehouse-migration-l01-solution -->

A strong answer:

- Inventories Snowflake and Hadoop by readers first and names the gaps.
- Gives the Snowflake supplier analytics one disposition and one driver; coexistence by federation or sharing is defensible once its connector and security review are verified.
- Bridges the finance view whenever its producer moves in a different wave from it.
- Fills Snowflake cells only from Snowflake's own current pages; its role model and export path stay unknown, with owners, until read.
- Flags the move from Spark 3.1 to a current runtime, where the engine risk is ANSI mode on by default since 4.0. No 1582 calendar rebase is expected for files Spark 3.1 wrote, because the calendar changed at 3.0; the 0001-01-01 placeholders need a before-and-after comparison only if the inventory finds files written by Spark 2.x or Hive.
- Writes persona tests for Snowflake roles before mapping them.
- Sets finance as class 1 and supplier analytics as class 2, and makes wave 1's exit test countable.

<!-- section:dbxfe-warehouse-migration-l01-mistakes -->

- Sizing by catalog counts, then migrating 220 tables nobody reads.
- One disposition for a whole platform.
- Waves by size, with cut dependencies found on cutover day.
- A comparison cell filled from memory or from a competitor's slide.
- Reporting a conversion rate as progress.
- Translating GRANT statements and calling access 'the same'.
- Repointing a report and leaving its rules in the old view.
- Choosing reconciliation depth after the results.
- Editing the new copy during a parallel run.
- A cutover date with no exit test, or deleting the old path before the recovery window ends.

<!-- section:dbxfe-warehouse-migration-l01-sources -->

Every vendor page cited had its title and search snippet confirmed on 2026-09-23; no page body could be fetched from the build sandbox. Microsoft's Fabric overview (page source, March 2026), AWS's Redshift welcome, architecture and database-security pages (details from AWS's archived source, out of date since June 2023), the Apache Hadoop HDFS design and permissions guides, and Spark's migration guide, ANSI compliance, ORDER BY and built-in function texts were also read from their published sources, Spark at the v4.0.4 tag. Lakebridge 0.15.2 was read from its PyPI metadata and wheel. Snowflake's and BigQuery's pages are cited from their snippets, earlier readings marked. Databricks federation, sharing, privilege, mask, lineage and ingestion records are reused from earlier reviews. Every Cinderline figure is synthetic, nothing was executed, and no vendor is ranked.

<!-- section:dbxfe-warehouse-migration-l01-related -->

[Architecture and migration](#/module/dbxfe-m08) for decision records and recovery after a switch, and [AWS deployment and network boundaries](#/module/dbxfe-aws) for the network path a federated read travels. The SQL Server module decomposes one procedure; the sharing and federation module compares copy, share and federation in depth; the identity module owns account-level identity; the operations module owns recovery validation.

<!-- section:dbxfe-warehouse-migration-l01-revisit -->

Answer without notes: which evidence retires a table, which edge needs a bridge, what a conversion rate proves, which class the plant-quality mart has, and what the first rollback trigger is. Then try the three questions below.
