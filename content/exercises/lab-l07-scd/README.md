# Lab L07 — SCD Type 1 and Type 2 from change events

**Execution class: local-executed (R).** The reference solution and its 17
tests run on local Apache Spark 4.0.4 in `local[2]` mode on one machine. Nothing
runs on Databricks, no Delta table is written, no declarative pipeline is used
and no network service is called. The AUTO CDC adaptation in SOLUTIONS.md is
written out but **not executed**.

## Purpose and outcome

Module B5 teaches declarative pipelines and change-data processing. This lab
is its executed core: you turn a stream of entity change events into a
**current** table (SCD Type 1, one row per key) and a **history** table (SCD
Type 2, validity intervals) under an explicitly stated source contract, with
the cases that break naive designs — a late arrival, a repeated event, a tie
on the sequence value, an invalid ordering value and a delete followed by a
return. You then carry the same reasoning to a second source with a composite
sequence and to a supplier table that arrives only as full snapshots.

After the lab you can:

- derive both tables with window functions (`LEAD` for intervals,
  `ROW_NUMBER` for the current row) in the DataFrame API and in Spark SQL;
- state the invariants a Type 1 and a Type 2 table must satisfy, and test them;
- explain why a late event rewrites history but not the present, why a tie is a
  contract breach rather than a coin toss, and why dropping an unplaceable
  event publishes a stale row;
- map the reference onto a declarative AUTO CDC flow and name what the flow
  does not do for you.

## Prerequisites

Python 3.12 with the pinned `requirements.txt` installed, and a Java 17 or 21
runtime for Spark. The lab was run with Python 3.12.3, Java 21.0.10, PySpark
4.0.4 and Py4J 0.10.9.9. Module B3 (record resolution: duplicates, invalid
records, conflicts) is assumed; this lab reuses its rules rather than
re-teaching them.

## Setup

```bash
python3.12 -m venv .venv
. .venv/bin/activate            # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

## Run

```bash
python run_tests.py --evidence local-evidence.json   # 17 tests, evidence JSON with hashes
python solutions/scenarios.py                         # every intermediate output SOLUTIONS.md quotes
python starters/scd_task.py                           # the learner starter and its two flawed designs
```

The runner binds Spark to `local[2]` with the web UI off, two shuffle
partitions, the UTC session time zone and `PYSPARK_PYTHON` set to the running
interpreter. It fails if any test fails or is skipped. Expected results are
hand-authored literals in `expected/`; DATA.md derives every one.

## Package contents

| Path | What it holds |
|---|---|
| `fixtures/` | Cinderline part change events (18), Marlow customer events (8, the transfer case), supplier snapshots (3) |
| `expected/` | hand-authored literals, with `_derivation` notes |
| `solutions/scd_reference.py` | the reference: contract, validation, resolution, Type 1 and Type 2 in DataFrame API and SQL, invariant checks, snapshot comparison |
| `solutions/scenarios.py` | prints the intermediate outputs |
| `starters/scd_task.py` | predictions, two deliberately flawed designs, two functions for you to implement |
| `TASKS.md`, `SOLUTIONS.md`, `DATA.md` | tasks, explained solutions with the unexecuted platform adaptation, data dictionary and derivations |

## Cleanup

Each script creates one temporary directory for Spark's scratch files and
deletes it when Spark stops; nothing is written inside the package. Remove the
virtual environment with `rm -rf .venv` and any evidence file you asked for.

## Limits

- The reference recomputes both tables from every retained event on each
  call. A production engine maintains them incrementally; the lab shows which
  edits that requires (test 08) but does not implement incremental state.
- Tie and invalid-order handling is the reference's documented policy
  (withhold the key and say why), not any engine's built-in behaviour.
- Tens of rows on one machine: nothing here is a performance measurement.
- Spark Declarative Pipelines is not part of PySpark 4.0.4; the runner records
  that `pyspark.pipelines` is not importable in the tested environment.
