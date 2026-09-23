# Lab L12 — Time-aware analytical SQL

**Execution class: R (local-executed).** The reference queries and their tests run on local
Apache Spark 4.0.4 (Spark SQL through PySpark) on one machine. Nothing here runs on Databricks;
no warehouse, cloud account, network access or paid service is involved, and "Spark SQL" in
this package always means the open-source engine executed locally.

## Purpose and outcome

A query portfolio over one fictional plant (Cinderline Components) whose answers were specified
before any query ran:

- windows with explicit frames (running total, three-row moving average), the default frame and
  tied ordering, the frame kind Spark resolved (read from the analyzed plan), and a `RANGE`
  frame of two calendar days beside a `ROWS` frame of three rows;
- ranking functions at a tie, top-per-group, and deduplication with a stated tie-breaker and a
  flag for a revision that two different rows claim;
- gaps-and-islands over daily machine status, including a gap and an island still open at the
  end of the data;
- semi and anti joins as membership questions, the `NOT IN` trap with a `NULL`, and set
  operators (`UNION`, `UNION ALL`, `INTERSECT`, `EXCEPT`) including the positional-column trap
  and a type mismatch that fails under ANSI mode;
- struct and array fields, 1-based `ELEMENT_AT` against the 0-based bracket index, `EXPLODE`
  against `LATERAL VIEW OUTER EXPLODE`, `TRY_CAST`, `TRY_DIVIDE`, null-aware arithmetic and
  aggregates;
- time zones and both 2026 daylight-saving changes in `America/New_York` (set explicitly as the
  session time zone): elapsed against wall-clock durations, timestamp subtraction, the local
  hour and day, a local time that does not exist, a local hour that occurs twice, the local
  versus UTC month, month-end arithmetic and an incomplete period;
- executed checks showing that T-SQL and Oracle expressions (`DATEDIFF` argument order and unit
  semantics, `ISNULL(x, y)`, `GETDATE()`, numeric `TRUNC`, `DATEADD`'s type, `QUALIFY`) are
  not assumed to mean the same thing in Spark SQL;
- two setting transfers: the same queries under `SET TIME ZONE 'UTC'`, and the same failing
  statements with ANSI mode switched off, where errors become silent values.

After the lab you can predict each of those results by hand, explain why the naive version of
each query is wrong, and name the session setting or dialect assumption a number depends on.

## Prerequisites

Module A3 (SQL, Python and PySpark transformations) or equivalent SQL fluency with
`GROUP BY` and joins. No Python beyond running a script.

## Package layout

```
README.md, TASKS.md, SOLUTIONS.md, DATA.md, requirements.txt
fixtures/     five synthetic JSON inputs (see DATA.md)
expected/     literal expected outputs with derivations; derive_time.py re-derives time.json
              with the standard library (never imported by the runner)
starters/     portfolio.sql with 14 blocks that have deliberate gaps; explore.py prints one query
solutions/    portfolio.sql (the executed reference, 55 named blocks) and portfolio.py (loader)
run_tests.py  unittest runner; --evidence <path> writes execution evidence;
              --portfolio <file> runs only the tests your file's queries cover
```

## Pinned environment (what was actually tested)

Python 3.12.3, OpenJDK 21.0.10, PySpark 4.0.4, Py4J 0.10.9.9, on Linux x86_64. Spark runs as
`local[2]` with the web UI and console progress bar disabled and
`spark.sql.shuffle.partitions=2`. ANSI mode is left at its Spark 4 default (`true`); the
session time zone is set to `America/New_York` by the loader. Spark's local scratch space and
warehouse directory are placed in a temporary directory that the runner deletes, so the lab
folder gains no `spark-warehouse` or `metastore_db`; the runner also writes no `__pycache__`.
Other versions were not verified here.

## Setup and run

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
# JAVA_HOME must point at a JDK 17 or 21 installation directory (not its bin folder).
.venv/bin/python run_tests.py --evidence local-evidence.json
```

The runner pins `PYSPARK_PYTHON` to the interpreter that launches it, because Spark's Python
workers must match the driver's version. Six tests deliberately execute nine statements that
must fail (a text-to-number union, `CAST` of `'n/a'`, division by zero, `ELEMENT_AT` and a
bracket index past an empty array, and four source-dialect expressions); each assertion names
the error class it expects, so a failure for a different reason is reported as a failure.

To check your own work, complete `starters/portfolio.sql` and run

```sh
.venv/bin/python run_tests.py --portfolio starters/portfolio.sql
```

Your blocks replace the reference blocks of the same name, and only the tests whose queries
your file defines are run (17 for the starter as shipped; unmodified, it passes only the
environment check). To study one query on its own:

```sh
.venv/bin/python starters/explore.py downtime_pairs
.venv/bin/python starters/explore.py running_total starters/portfolio.sql
```

## What the tests prove and do not prove

They prove that the reference SQL reproduces every literal in `expected/` on the pinned local
engine; that the wrong approaches produce the wrong numbers named in `SOLUTIONS.md`; that a
query whose values match can still carry the wrong frame, which only the analyzed plan shows;
and that altered inputs (a new tie, a filled gap) and altered settings (a UTC session, ANSI
mode off) change the answers exactly as predicted. They do not prove Databricks Runtime or
Databricks SQL behaviour, performance, or that the same SQL is correct for a different data
set. `QUALIFY` is rejected by this local parser although it is documented for Databricks SQL;
that is recorded as a difference to verify, not as a defect of either engine. Some expected
values are engine behaviour that was read off this build once and frozen rather than derived:
the error classes, the frame-kind names in the analyzed plan, the text layout of a day-time
interval, the fact that `TIMESTAMPDIFF` and timestamp subtraction use local clock readings, and
two `TRY_CAST` edge cases; `DATA.md` lists them. A change in any of them fails a test, which is
the point: it is a change to verify on the target engine.

## Cleanup

Spark keeps the views in memory and its scratch directories are deleted by the runner. The
only file the lab writes is the evidence JSON you name. Delete `.venv/` and your evidence file
when done. No tables, clusters or external effects exist.
