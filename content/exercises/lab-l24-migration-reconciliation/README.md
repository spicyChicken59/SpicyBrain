# Lab L24 — Migration reconciliation for a small on-premises pipeline

**Execution class: local-executed (R).** The reference solution and its 28 tests
were executed on local Apache Spark 4.0.4 (PySpark 4.0.4, Py4J 0.10.9.9,
Python 3.12.3, OpenJDK 21.0.10) on one machine. Nothing ran on Databricks.

**No source platform was used.** No SQL Server, SQL Server Integration
Services (SSIS) or SQL Server Agent instance was installed, started or
contacted. The legacy stored procedure (`legacy/sp_daily_inspections.sql`) and
the SSIS-style package outline (`legacy/pkg_csv_import.json`) are original
teaching text, read by the lab as text. What the legacy job produced is
represented by hand-authored fixtures (`fixtures/legacy_*.json`) whose every
number is derived in `DATA.md`.

## Purpose

A procedure that converts line by line into PySpark can compile, run and still
mean something else. This lab migrates one fictional Cinderline Components
nightly report and proves, row by row, where a translation keeps or changes
the legacy meaning: collation-sensitive keys, a filter on the outer side of a
LEFT JOIN, the clock the business day is computed on, integer division, exact
decimal money, the as-of basis, and the watermark that makes the job
incremental.

## Outcome

After the lab you can:

1. Build a dependency and semantics inventory from procedure text and map an
   SSIS-style control flow onto job tasks with dependencies and run-if
   conditions.
2. Write a target transformation whose five semantic choices reproduce the
   legacy behaviour, and show which reconciliation check catches each wrong
   choice.
3. Reconcile two paths on one basis: row counts, keyed differences (missing,
   extra, changed), per-day totals with exact decimals, null counts and
   declared types.
4. Run an incremental window, prove that a retry after a partial write is
   idempotent, and explain why selecting by event time misses a late
   correction.
5. Classify differences against a register of expected, owned changes and
   decide whether a parallel run is ready for cutover.

## Prerequisites

SQL joins, grouping and NULL rules; a first reading of PySpark DataFrames;
the business-day idea (a day that starts at 06:00 local time).

## Setup

```bash
python3.12 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt      # pyspark==4.0.4, py4j==0.10.9.9
java -version                        # Java 17 or 21 must be on PATH (21.0.10 was used)
```

No network access is needed after installation.

## Run

```bash
python run_tests.py --evidence evidence.json
```

The runner starts one Spark session (`local[2]`, UI disabled, two shuffle
partitions, session time zone UTC set explicitly), runs 28 tests, stops the
session and writes evidence: versions, start and finish times, test counts,
skips (must be zero) and SHA-256 hashes of every fixture, legacy text,
expected literal, solution file and produced output.

To test your own work instead of the reference, fill the gaps in
`starters/migration_starter.py` and run:

```bash
LAB_L24_SOLUTION=starters.migration_starter python run_tests.py
```

`python expected/derive_expected.py` re-derives the numeric literals with the
standard library only and reports any disagreement; the runner never calls it.

## Cleanup

The session writes its scratch files (Spark local directory and warehouse
path) under one temporary directory created with `tempfile.mkdtemp(prefix=
"lab-l24-")` and removes it when the session stops. The runner disables
bytecode files, so no `__pycache__` appears. Delete `evidence.json` and any
`.venv` you created when you are done.

## Limits

- Local Spark on one machine; timings are not benchmarks.
- The legacy semantics come from the procedure text and the documented
  behaviour of SQL Server data types and operators, represented in
  hand-authored fixtures; they are not observations of a running server.
- Target tables are in-memory lists of rows standing in for platform tables:
  no Delta, metastore, workspace, job or pipeline was created.
- Collation is emulated for ASCII codes with `upper(rtrim(...))`; accents,
  non-ASCII case rules and other collations are out of scope.
- The job plan is a mapping, not a deployed job; run-if names follow the
  documented conditions and were not validated against a live service.
- All organizations, people, codes and numbers are fictional.
