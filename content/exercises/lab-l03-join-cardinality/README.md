# Lab L03 — Join cardinality: the total that multiplied

**Execution class: R (local-executed).** The reference solution and its
tests run here on one machine with Apache Spark 4.0.4 in `local[2]` mode,
web UI disabled, two shuffle partitions, ANSI SQL mode at its Spark 4
default. Nothing contacts Databricks, a cluster, a cloud account or the
network after installation.

## Purpose and outcome

Twenty accepted Cinderline inspections are joined to a plant dimension that
was delivered as uncollapsed history: the key `plant_id` repeats. The naive
inner join returns 33 rows and 410 inspected units — a plausible 9.5% defect
rate that is simply wrong (the facts total 256 / 24). You diagnose it (row
counts before and after, a duplicate-key check), repair it with an explicit
rule (latest `valid_from` per plant, by window or by `max_by` aggregate),
show why two tempting non-repairs do nothing, and then test the whole
sequence on a **different** dimension with a different duplicate pattern.
Two further traps are built in: a per-plant "average of rates" that
disagrees with the unit-weighted rate and silently drops a 0/0 inspection,
and a LEFT JOIN whose `COUNT(*)` reports one inspection for a plant that has
none. After the lab you can:

- name the grain of both sides of a join and predict its row count;
- run a duplicate-key check before trusting any joined total;
- write a deterministic current-row rule and prove it order-independent;
- explain `COUNT(*)` versus `COUNT(column)` on a left join, and why
  sum-then-divide is the metric while average-of-rates is a different one.

## Prerequisites

Module A3 (`dbxfe-transformations`), especially the grain and join beats,
and Lab L02's habit of comparing sorted rows and schemas. Comfortable
reading Python.

## Files

```
README.md TASKS.md SOLUTIONS.md DATA.md requirements.txt run_tests.py
fixtures/inspections.json       20 accepted inspections (see DATA.md)
fixtures/plants.json            8 dimension rows, keys P1 x2 and P2 x3
fixtures/plants_transfer.json   10 rows, keys P3 x3 and P4 x3, P9 present, P6 empty
expected/baseline.json          authored literals for plants.json
expected/transfer.json          authored literals for plants_transfer.json
expected/types.json             dtypes of inputs and every report
starters/                       joins.py, sql_joins.py with TODO gaps
solutions/                      session.py, schema.py, joins.py, sql_joins.py, compare.py
```

## Setup (tested pins)

Tested with **Python 3.12.3, Java 21.0.10 (OpenJDK), PySpark 4.0.4, Py4J
0.10.9.9** on Linux x86_64. Apache documents Java 17 and 21 for this Spark
release; only Java 21 was executed here. Set `JAVA_HOME` to the JDK
directory (not its `bin`), then:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run_tests.py --evidence local-evidence.json
```

On Windows PowerShell use `py -3.12 -m venv .venv` and
`.\.venv\Scripts\python.exe`. The PySpark wheel is large; allow disk and a
few minutes.

## Running

`run_tests.py` starts one local session and runs nine `unittest` cases:
seven over the baseline dimension, one over the weighted metric, and one
transfer case that re-runs every check over `plants_transfer.json`. Both
the DataFrame API and Spark SQL are held to the literals in `expected/`.
`--evidence <path>` writes JSON with versions, timestamps, test counts,
exit status, SHA-256 of every fixture, expected and solution file, and
SHA-256 of every collected output; `--outputs <path>` also writes the
collected rows. Skipped tests count as failure.

## Failure states

`JAVA_HOME` wrong → no Java gateway. Worker start errors → make sure the
virtual environment's interpreter runs the script (the runner sets
`PYSPARK_PYTHON` to itself). A `DIVIDE_BY_ZERO` error means a row-level
rate was written without `try_divide` or a guard: Spark 4 is in ANSI mode
by default, and the starter's `RATES_SQL` is left that way on purpose.

## Cleanup

The runner stops Spark in `tearDownClass`, writes no bytecode, creates no
tables or external effects. Delete `.venv/` and any evidence file you no
longer need; keep the fixtures and your predictions.

## Limits

Local Spark 4.0.4 over 20 facts and 8 or 10 dimension rows. A pass proves
that the naive, non-repair and repaired relations produce the authored rows
and types on these fixtures in this engine version, in both interfaces.
It proves nothing about Databricks Runtime, cluster behaviour, performance
or a real dimension's semantics: whether "latest valid_from" is the right
current-row rule is a business decision the fixtures merely assume. The
`dropDuplicates` result is recorded in the evidence and never asserted,
because Spark promises nothing about which duplicate survives. Timings are
illustrations, not benchmarks. All records are fiction.
