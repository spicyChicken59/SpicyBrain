# Lab L02 — SQL and PySpark equivalence on typed inspection events

**Execution class: R (local-executed).** The reference solution and its
tests run here on one machine with Apache Spark 4.0.4 in `local[2]` mode,
web UI disabled, two shuffle partitions. Nothing in this package contacts
Databricks, a cluster, a cloud account or the network after installation.

## Purpose and outcome

The same synthetic dataset — 26 delivered Cinderline inspection events with
re-deliveries, nulls, invalid quantities and a four-row plant dimension — is
transformed twice: once with Spark SQL, once with the PySpark DataFrame API.
You compare the two results **deliberately**: rows after an explicit sort,
and the schema (names, types, nullability, column order) as a separate
check. Two cases are built to disagree until corrected — one where relying
on implicit row order breaks, one where SQL and DataFrame code differ in
null handling — so that "equivalent" becomes something you can prove rather
than assume. After the lab you can:

- declare a schema and say what each nullable field means;
- write one staged transformation in both interfaces and compare each stage
  against independently authored expected rows *and* types;
- explain why `collect()` order is not a contract and why `== None` and
  `.distinct().count()` are not the null tests they look like;
- re-derive the report by hand when the input changes (the transfer batch).

## Prerequisites

Module A3 (`dbxfe-transformations`): grain, typed columns, null semantics,
the unit-weighted rate. Comfortable reading Python; no Spark installation
knowledge is assumed beyond this README.

## Files

```
README.md TASKS.md SOLUTIONS.md DATA.md requirements.txt run_tests.py
fixtures/inspection_events.json   26 raw deliveries (see DATA.md)
fixtures/plants.json              plant dimension, unique key
fixtures/transfer_batch.json      5 rows appended by the transfer task
expected/baseline.json            authored literals for the baseline
expected/transfer.json            authored literals after the transfer batch
expected/types.json               declared, inferred and report dtypes
starters/                         sql_pipeline.py, dataframe_pipeline.py, compare.py with TODO gaps
solutions/                        session.py, schema.py, sql_pipeline.py, dataframe_pipeline.py, compare.py
```

## Setup (tested pins)

Tested with **Python 3.12.3, Java 21.0.10 (OpenJDK), PySpark 4.0.4, Py4J
0.10.9.9** on Linux x86_64. Apache documents Java 17 and 21 for this Spark
release; only Java 21 was executed here. Install Python 3.12 and a JDK, set
`JAVA_HOME` to the JDK directory (not its `bin`), then:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run_tests.py --evidence local-evidence.json
```

On Windows PowerShell use `py -3.12 -m venv .venv` and
`.\.venv\Scripts\python.exe` in place of `.venv/bin/python`. The PySpark
wheel is large (hundreds of MB); allow disk space and a few minutes.

## Running

`run_tests.py` starts one local session, runs nine `unittest` cases against
the complete `solutions/`, and prints a summary. `--evidence <path>` writes
JSON with Python/Java/Spark versions, start and end time, counts of tests,
failures, errors and skips, the exit status, SHA-256 of every fixture,
expected and solution file, and SHA-256 of every collected output.
`--outputs <path>` additionally writes the collected rows themselves.
Skipped tests count as failure (`exit` 1). To test your own attempt, point
the imports at `starters/` after filling the TODOs, or copy your files over
`solutions/` in a scratch copy of the package.

## Failure states

`JAVA_HOME` wrong → Spark cannot start its Java gateway. Python worker
errors → check that the interpreter running `run_tests.py` is the virtual
environment (the runner sets `PYSPARK_PYTHON` to itself). A native-Hadoop
warning on Windows is harmless here: the data is in memory. A memory or
resource failure is a failure, not a reason to skip.

## Cleanup

The runner stops Spark in `tearDownClass`, writes no bytecode
(`sys.dont_write_bytecode`), creates no tables, files or external effects.
The only outputs are the evidence/outputs paths you pass. To clean up,
delete `.venv/` and any evidence file you no longer need; keep the fixtures
and your written predictions.

## Limits

This is local Spark 4.0.4 on 26 rows. A pass proves that both
implementations produce the authored rows and types on these fixtures in
this engine version. It proves nothing about Databricks Runtime behaviour,
cluster execution, performance, full-population coverage or the correctness
of a transformation over data these fixtures do not contain. Timings in the
evidence are wall-clock illustrations, not benchmarks. All records are
fiction; the validation contract is authored teaching policy.
