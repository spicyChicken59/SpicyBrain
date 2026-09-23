### Purpose

Lab L24 migrates one small on-premises pipeline and proves, row by row, where a translation keeps or changes its meaning. It belongs to the SQL Server and on-premises modernization module and supports the warehouse-migration module's reconciliation matrix; [Architecture and migration](#/module/dbxfe-m08) and [Ingestion, records and reliable updates](#/module/dbxfe-m04) hold the staged-migration and idempotent-pipeline background. Everything below was executed on local Apache Spark 4.0.4 (PySpark 4.0.4, Py4J 0.10.9.9, Python 3.12.3, OpenJDK 21.0.10) on one machine: 28 tests, 0 failures, 0 skips. No SQL Server, SSIS or SQL Server Agent instance was installed, started or contacted. The legacy stored procedure and the SSIS-style package outline are original teaching text that the lab reads as text; what the legacy job produced is represented by hand-authored fixtures whose numbers are derived in the package's DATA.md. Nothing ran on Databricks, and no number here is a benchmark.

### The pipeline and the fixtures

A SQL Server Agent job at 06:30 runs `pkg_csv_import`: a loop loads correction files, one Execute SQL Task applies them, another calls `dbo.sp_daily_inspections`, and a Send Mail Task fires on any failure. The procedure selects business days touched since the watermark, rebuilds `dbo.rpt_quality_detail` for those days with a LEFT JOIN to inspectors (`s.plant_code = @plant_code` in the ON clause, `ISNULL(shift, 'UNASSIGNED')`), merges `dbo.rpt_quality_daily` with `defect_pct = units_defective * 100 / units_inspected` (INT / INT) and moves the watermark, all in one transaction. The server clock is America/New_York and the collation is case-insensitive.

| Fixture | Rows | Deliberate cases |
|---|---|---|
| inspections_p1 | 12 | codes `qa07`, `QA07 `, NULL and `QA99`; 02:10 and 05:59:59.997 near the 06:00 cutoff; 101 corrected late; 112 updated after the as-of moment |
| legacy detail and report (P1) | 11 and 6 | the old path's output as of 06:30 on 4 March |
| inspections_p2 (transfer) | 6 | plant in Chicago stamped on the New York clock; ` QA21` with a leading space |
| parallel_run | 3 scenarios | verdicts for the cutover gate |

### Task 1: inventory before translating

A regular-expression scan of the procedure text, checked against a reading by hand, lists four tables read, three written, `#affected_days`, `GETDATE` as the only clock, one `DATEADD(HOUR, -6, ...)` cutoff, one integer division, seven string-key comparisons that the collation decides, two predicates in the LEFT JOIN's ON clause, `etl.watermark` as the only state table, a transaction wrapping DELETE, INSERT, MERGE and UPDATE, and a MERGE that never deletes vanished groups. The package maps to four job tasks: the loop and its data flow become one ingestion task, Success constraints become 'all succeeded' dependencies, and the three OR-joined Failure constraints become one notification task that runs when at least one dependency failed. The 06:30 schedule gains the time zone the Agent job never recorded.

### Tasks 2 to 5: the target transformation

The landed extract types `inspected_at` as `timestamp_ntz` and money as `decimal(12,2)`; exactly one value is NULL (inspection 106's code). Five explicit choices reproduce the legacy meaning: keys compared as `upper(rtrim(code))`, the plant predicate kept in the join condition, the business day as `to_date(local - INTERVAL 6 HOURS)` on the server wall clock, the rate as `(units_defective * 100) div units_inspected`, and exact decimal money. The P1 report:

| Day | Shift | Inspections | Units | Defective | Cost | Defect % |
|---|---|---|---|---|---|---|
| 2 March | DAY | 1 | 120 | 4 | 4.50 | 3 |
| 2 March | NIGHT | 2 | 140 | 3 | 0.30 | 2 |
| 3 March | DAY | 3 | 300 | 8 | 8.35 | 2 |
| 3 March | NIGHT | 2 | 120 | 3 | 2.90 | 2 |
| 3 March | UNASSIGNED | 2 | 70 | 5 | 15.30 | 7 |
| 4 March | DAY | 1 | 40 | 0 | 0.00 | 0 |

It reconciles with the legacy report on every check: row counts, keys, per-day totals, null counts and declared types. It gives the same answer under UTC, Asia/Kolkata and America/New_York sessions, because `timestamp_ntz` arithmetic ignores the session zone.

### Task 6: the failure case

The line-by-line translation compiles and returns six report rows, like the legacy job, and fails everything else: inspections 104, 105, 106 and 111 vanish (binary keys plus the filter moved to WHERE), 103 and 109 land a day late (the day taken in a UTC session puts the cutoff at 01:00 local), 3 March UNASSIGNED is missing and 4 March NIGHT is extra, the rates carry decimals (2.727272727272727 for 3 March DAY) and money prints binary noise (2.4000000000000004). One flip at a time shows which check owns which defect. Binary keys alone pass row counts and day totals, because 104 and 105 only move from DAY to UNASSIGNED within 3 March; only the keyed comparison fails. The WHERE filter also fails the null count (inspector_code 1 → 0). Fractional division fails only report values and types. DOUBLE money fails the type check and the exact totals where 0.10 + 0.20 prints 0.30000000000000004. Leaving out the as-of filter adds inspection 112 to 4 March: a basis error, not a migration defect.

### Task 7: incremental state and the retry

Tonight's window, `updated_at` in (06:30 on 3 March, 06:30 on 4 March], touches 2, 3 and 4 March, because inspection 101 was corrected at 16:00 on 3 March. Selecting by `inspected_at` touches only 3 and 4 March and leaves 2 March at 3 defective instead of 4. With a failure injected after the detail write, the watermark stays at 06:30 on 3 March and the report no longer sums the detail; the retry rebuilds the same days and converges to the legacy report. The next window picks up inspection 112 (4 March DAY becomes 2 inspections, 100 units, 2 defective, 1.25, 2 %), and an empty window changes nothing.

### Task 8: transfer and cutover

On plant P2 the same legacy-compatible rules reconcile first time. A `trim` key rule joins ` QA21` to DAY (3 → 2 on the rate, UNASSIGNED missing) while day totals stay equal; the P1 data could never show this, because P1 has no leading-space code. The intended 06:00 plant-local rule moves inspections 205 and 206 (05:25 and 05:05 in Chicago) from 11 to 10 March; every difference is predicted by an owned register entry and re-deriving the legacy report with the moves applied leaves no residue, so the verdict is 'explained'. Remove the owner and nothing is explained. The gate reads 'not ready' on the logged run (0 of 5 clean days since the code change of 11 March; exception EXC-07 has no owner), 'ready' on the extended run, and 'not ready' when rollback was never rehearsed.

### What the tests prove and do not prove

They prove that this target reproduces the hand-derived legacy outputs on these fixtures, that each of five translation defects is caught by a named check, that the retry converges, and that the register and gate apply their rules. Mutations were run during authoring: a `trim` target, a fractional target and a register that ignores owners each turned tests red. The tests do not prove equivalence on other data, that SQL Server itself would produce these fixtures, or anything about performance; the fixtures do not exercise the MERGE that never deletes, source deletes or non-ASCII collation rules.

### Setup and cleanup

Use Python 3.12 with `pyspark==4.0.4` and `py4j==0.10.9.9` installed from the package's requirements.txt and Java 17 or 21 on the path, then run `python run_tests.py --evidence evidence.json` from the lab folder. To test your own work, fill the six gaps in the starter and set `LAB_L24_SOLUTION=starters.migration_starter`. The session writes its scratch files under one temporary directory that it deletes when it stops; the runner writes no bytecode files. Delete `evidence.json` and any virtual environment you created when you are done.
