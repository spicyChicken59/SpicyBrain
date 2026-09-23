<!-- section:dbxfe-sqlserver-l01-outcome -->

After this lesson you can take a small SQL Server pipeline apart before translating a line of it: inventory its stored procedure, SSIS-style package and SQL Server Agent schedule, decompose the procedure into target steps, and name the source semantics that decide its results: collation, NULL handling, the clock behind the business day, integer division, exact decimals, identity columns, triggers, transactions and the watermark. You can show why a translation that compiles is not a migration, reconcile old and new paths on one basis, and plan coexistence, cutover and rollback on evidence. Nothing here runs SQL Server; Lab L24 runs local Spark only.

<!-- section:dbxfe-sqlserver-l01-start -->

Bring SQL joins, grouping and three-valued NULL logic, and a first reading of PySpark DataFrames. [Architecture and migration](#/module/dbxfe-m08) teaches staged, reversible migration and decision records, including [Migrate with reconciliation and rollback](#/lesson/dbxfe-m08-l03). [Ingestion, records and reliable updates](#/module/dbxfe-m04) teaches incremental inputs and idempotent recovery in [Identity, ordering, and incremental inputs](#/lesson/dbxfe-m04-l02) and [Orchestration, failure, and reconciliation](#/lesson/dbxfe-m04-l03). This lesson applies both to one SQL Server source; the Migration inventory and Reconciliation plan field guides hold the templates.

<!-- section:dbxfe-sqlserver-l01-pipeline -->

Fictional Cinderline Components builds its morning quality report on premises. The chain, as the inventory found it:

| Step | Legacy object | What it promises |
|---|---|---|
| 06:30 daily | SQL Server Agent job `nightly_quality` | runs on the server clock |
| Load files | Foreach Loop + Data Flow Task | every correction CSV is staged first |
| Apply | Execute SQL Task | staged rows reach `erp.inspection` |
| Build | `dbo.sp_daily_inspections` | each inspection counted once, on its business day |
| Alert | Send Mail Task on Failure | the owner hears about any failed step |

The procedure's core lines, shown as text and never executed:

```sql
SELECT DISTINCT i.plant_code, CAST(DATEADD(HOUR, -6, i.inspected_at) AS DATE) AS business_day
  INTO #affected_days
  FROM erp.inspection AS i
 WHERE i.updated_at > @since AND i.updated_at <= @until;
-- LEFT JOIN erp.inspector AS s ON s.inspector_code = i.inspector_code AND s.plant_code = @plant_code
-- defect_pct = s.units_defective * 100 / s.units_inspected
```

The inventory also records what no object list shows: the server clock (America/New_York, no offset stored), the collation (`SQL_Latin1_General_CP1_CI_AS`) and `etl.watermark`, which the procedure updates inside its transaction.

<!-- section:dbxfe-sqlserver-l01-decompose -->

A stored procedure mixes selection, rules, writes and state. Decompose it into steps that each have one input, one output and one test:

| Procedure step | Target step | Test that proves it |
|---|---|---|
| `#affected_days` from the watermark window | select changed rows, return affected days | tonight returns 2, 3 and 4 March |
| DELETE and INSERT detail | rebuild whole affected days | detail keyed by inspection matches |
| MERGE report | aggregate with the legacy arithmetic | report reconciles on keys, totals, types |
| UPDATE watermark | move the watermark after both writes | a retry after a partial write converges |

The package maps the same way: the loop and its data flow become one ingestion task, each Execute SQL Task a task, Success constraints dependencies that run when all succeeded, and the three Failure constraints joined by OR one notification task that runs when at least one dependency failed. The Agent schedule becomes a schedule trigger that names its time zone.

<!-- section:dbxfe-sqlserver-l01-semantics -->

Some behaviour lives in the source tables, not the procedure. An identity column assigns `inspection_id` on insert; values are unique but may have gaps, on SQL Server and on a Delta identity column alike, so never reconcile on the sequence. A trigger keeps `updated_at` current; any write path that skips it hides a change from the watermark. The procedure's writes sit in one transaction with `XACT_ABORT ON`: detail, report and watermark change together or not at all. On the target each table commits on its own, so the design recomputes whole days and moves the watermark last; multi-statement transactions exist for Unity Catalog managed tables but were in Public Preview when read. `#affected_days` is a temporary object that dies with the procedure; a `##global` table read by another session is hidden coupling that must become a named, owned table.

<!-- section:dbxfe-sqlserver-l01-types -->

Each data type and comparison carries a rule the target must choose deliberately:

- **DATETIME** is local, has no offset and rounds to .000, .003 or .007 seconds. Land it as `TIMESTAMP_NTZ` and compute the business day on a named clock; a raw `05:59:59.999` lands on 3 March as `TIMESTAMP_NTZ` but on 4 March once DATETIME rounds it to 06:00:00.000.
- **INT / INT truncates** in T-SQL: 800 / 300 is 2. Spark's `/` returns 2.6666666666666665; `div` returns 2.
- **DECIMAL(12,2)** stays exact; the same money as DOUBLE prints 0.30000000000000004 for 0.10 + 0.20.
- **Collation**: SQL Server pads trailing spaces before `=`, and CI_AS ignores case, so `qa07` and `QA07 ` join to QA07 while ` QA07` does not. `upper(rtrim(code))` reproduces that; `trim` does not.
- **NULL**: a filter on the joined table moved from ON to WHERE turns a LEFT JOIN into an inner join; T-SQL `CONCAT` treats NULL as empty, Spark's `concat` returns NULL.
- **Time**: the TIMEZONE default is UTC, so a correct instant rendered in a UTC session moves a 06:00 New York cutoff to 01:00.

<!-- section:dbxfe-sqlserver-l01-incremental -->

The watermark is state. Select rows whose `updated_at` falls in the half-open window (since, until], record `until` at the start of the run, and rebuild every business day those rows touch. Selecting by `inspected_at` misses late corrections: inspection 101, inspected on 2 March and corrected at 16:00 on 3 March, is found by change time and lost by event time. A timestamp watermark cannot see deletes at all. SQL Server change tracking records which rows changed, deletes included, and change data capture records the changed data from the log; the Lakeflow Connect SQL Server connector ingests with either and recommends change tracking for tables with a primary key. Enabling either needs the DBA and security lead, so record it as an unknown until they agree.

<!-- section:dbxfe-sqlserver-l01-example -->

Lab L24 ran a line-by-line translation of the procedure beside the target on local Spark 4.0.4 against the same synthetic extract:

| Check | Line-by-line translation | Target |
|---|---|---|
| Report rows | 6 = 6 | 6 = 6 |
| Keys | 3 March UNASSIGNED missing, 4 March NIGHT extra, 4 groups changed | none |
| Day totals | all three days differ | equal |
| Nulls | inspector_code 1 → 0 | equal |
| Types | money and rate DOUBLE | decimal money, integer rate |

Flipping one choice at a time shows which check owns which defect. Binary keys alone pass row counts and day totals, because 104 and 105 only move from DAY to UNASSIGNED on the same day; only the keyed comparison fails. That is the case the rule "keys before totals" exists for.

<!-- section:dbxfe-sqlserver-l01-cutover -->

Coexistence keeps the legacy job serving users while the new job runs after it on the same as-of moment, writes to its own tables and reconciles every night. The gate is evidence: five consecutive clean days after the last code change, every explained difference owned by a named person, and a rehearsed rollback. A code change restarts the count; days that passed before it are not credit. Cutover moves consumers report by report; the legacy schedule stays in place until the rollback window closes, and only then is the old path decommissioned and its outputs archived.

<!-- section:dbxfe-sqlserver-l01-exercise -->

Plant P2 is in America/Chicago but its rows are stamped on the New York server. Its extract has ` QA21` (leading space), `qa22  `, and rows at 06:05 and 06:25 New York time on 11 March. Predict: (1) which shift ` QA21` gets under the legacy rule and under a `trim` key rule; (2) which business day the 06:05 and 06:25 rows get under the legacy rule and under a 06:00 plant-local rule; (3) what the reconciliation must show before the plant-local rule can be accepted.

<!-- section:dbxfe-sqlserver-l01-solution -->

(1) Legacy: UNASSIGNED, because a leading space is significant; with `trim` it joins QA21 and moves to DAY, which the keyed comparison catches while day totals stay equal. (2) Legacy: 11 March, because 06:05 and 06:25 are after 06:00 on the server clock; plant-local: 10 March, because they are 05:05 and 05:25 in Chicago. (3) Exactly those two rows move one day earlier, each predicted by a register entry with a named owner, and re-deriving the legacy report with the moves applied equals the new report with no residue. Remove the owner and nothing is explained.

<!-- section:dbxfe-sqlserver-l01-mistakes -->

- Treating a clean compile, a converter's zero-error report or equal row counts as equivalence.
- Reconciling totals before keys, which hides rows that moved between groups.
- Using `trim` for a collation that only ignores trailing spaces.
- Moving a joined-table filter from ON to WHERE and losing unmatched rows.
- Computing a business day from a session default instead of a named clock.
- Selecting incremental rows by event time, or moving the watermark before the writes commit.
- Fixing a legacy quirk silently during migration; reproduce it, reconcile, then change it with an owner.
- Claiming SQL Server behaviour was observed when only the documentation and a local emulation were used.

<!-- section:dbxfe-sqlserver-l01-sources -->

- [Transact-SQL reference](https://learn.microsoft.com/en-us/sql/t-sql/language-reference), [SQL Server Integration Services](https://learn.microsoft.com/en-us/sql/integration-services/sql-server-integration-services), [string comparison](https://learn.microsoft.com/en-us/sql/t-sql/language-elements/string-comparison-assignment), [datetime](https://learn.microsoft.com/en-us/sql/t-sql/data-types/datetime-transact-sql), [division](https://learn.microsoft.com/en-us/sql/t-sql/language-elements/divide-transact-sql) and [track data changes](https://learn.microsoft.com/en-us/sql/relational-databases/track-changes/track-data-changes-sql-server) (Microsoft).
- [SQL Server ingestion setup](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/sql-server), [Lakeflow Jobs](https://docs.databricks.com/aws/en/jobs/) and [migration](https://docs.databricks.com/aws/en/migration) (Databricks); [NULL semantics](https://spark.apache.org/docs/latest/sql-ref-null-semantics.html) (Apache Spark).

Titles and addresses were confirmed by search on 23 September 2026; the pages were not fetched in this build. Feature status, versions and defaults change: verify them for the actual source and workspace.

<!-- section:dbxfe-sqlserver-l01-related -->

Continue with [Architecture and migration](#/module/dbxfe-m08) for decision records and staged plans, and [Ingestion, records and reliable updates](#/module/dbxfe-m04) for idempotent pipelines. The warehouse-migration module extends this to migration waves across whole platforms. Lab L24, migration reconciliation, is the executable version of this lesson: inventory, target transformation, five single-choice flips, incremental retry, a transfer plant and the cutover gate.

<!-- section:dbxfe-sqlserver-l01-revisit -->

Without notes: list the five semantic choices the P1 target makes and the check that catches each wrong one; explain why a timestamp watermark cannot see a delete; and state the three conditions of the cutover gate.
