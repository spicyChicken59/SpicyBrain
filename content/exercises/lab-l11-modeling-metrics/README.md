# Lab L11 — Model it, then contract the metric

**Execution class: R (local-executed).** The reference solution and its tests
run here on one machine with Apache Spark 4.0.4 in `local[2]` mode, web UI and
console progress disabled, two shuffle partitions, session time zone UTC, ANSI
SQL mode at its Spark 4 default (on). Nothing contacts Databricks, a cluster,
Unity Catalog, a cloud account or the network after installation. No Delta
table, metric view or dashboard is created.

## Purpose and outcome

Twenty-two accepted inspections from the fictional Cinderline Components arrive
from silver with natural keys and source units. You model them as a small star
(one fact at the grain of one inspection; line, plant, shift and date
dimensions; a line dimension that keeps supervisor history as type 2 rows),
then compute one metric, `unit_defect_rate`, at three grains: line-day,
plant-day and plant-month. A metric contract (`fixtures/metric_contract.json`)
names the numerator, denominator, unit, period, window, empty-case statuses,
unknown member and owner, and drives the query parameters.

Five deliberately broken queries show what the model and the contract prevent,
and each is asserted to fail for its stated reason:

| Broken approach | What goes wrong on the baseline |
|---|---|
| Plain `SUM/SUM` division | `DIVIDE_BY_ZERO` on N2's zero-piece day under ANSI mode |
| Summing source quantities | South's plant-day rate on 27 March is 4/190 instead of 15/300 |
| Inner join to the line dimension | Inspection I-21 (line N3, not yet in the dimension) vanishes |
| Joining history on `line_id` alone | 29 rows from 22 inspections; two supervisors both claim all of N1 |
| A three-calendar-day window | On Monday 30 March it holds one business day instead of three |

The same checks then run on an altered transfer set (a new case pack, a
supervisor change on a fact's date, a plant shutdown day, an unconvertible
unit), a mutated dimension with overlapping versions must be caught, and five
incomplete contracts must be refused with named reasons. After the lab you can:

- declare the grain of a fact and a metric and test that a join preserves it;
- resolve a type 2 attribute point-in-time and explain as-was versus as-is;
- keep a missing dimension key visible through an unknown member;
- convert units before summing and prove a rate is recomputed from its parts;
- define a reporting window from a plant calendar, not from calendar days;
- write a metric contract that a machine can refuse when it is incomplete.

## Prerequisites

The data modeling and metric contracts module (grain, facts and dimensions,
slowly changing attributes, additivity, metric contracts). Lab L03's habit of
counting rows before and after a join helps. Comfortable reading SQL; the
Python only loads JSON and runs named statements.

## Files

```
README.md TASKS.md SOLUTIONS.md DATA.md requirements.txt run_tests.py
fixtures/metric_contract.json        the metric contract (drives the parameters)
fixtures/baseline/*.json             22 inspections, dimensions, calendar, units, run dates
fixtures/transfer/*.json             13 inspections with the altered cases (see DATA.md)
expected/baseline.json               authored literals for the baseline
expected/transfer.json               authored literals for the transfer set
starters/model.sql                   the model with nine marked gaps, one a review point (TASKS.md)
solutions/model.sql                  reference Spark SQL, one "-- name:" block per statement
solutions/model.py                   loads fixtures with explicit schemas, runs named statements
solutions/contract.py                validates the contract and turns it into parameters
solutions/session.py                 the local Spark session and its temporary directory
```

## Setup (tested pins)

Tested with **Python 3.12.3, Java 21.0.10 (OpenJDK), PySpark 4.0.4, Py4J
0.10.9.9** on Linux x86_64. Apache documents Java 17 and 21 for this Spark
release; only Java 21 was executed here. Set `JAVA_HOME` to the JDK directory
(not its `bin`), then:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run_tests.py --evidence local-evidence.json
```

On Windows PowerShell use `py -3.12 -m venv .venv` and
`.\.venv\Scripts\python.exe`. The PySpark wheel is large; allow disk and a few
minutes.

## Running

`run_tests.py` starts one local session and runs twenty `unittest` cases: two
contract cases (no Spark), nine baseline cases and nine transfer cases. The
baseline's ninth case mutates the line dimension on purpose; the transfer's
ninth checks what only the transfer data can show.

- `--evidence <path>` writes JSON with versions, timestamps, test counts, exit
  status, SHA-256 of every fixture, expected and solution file, and SHA-256 of
  every collected output.
- `--outputs <path>` also writes the collected rows, for reading.
- `--sql starters/model.sql` tests your own SQL file instead of the reference.
  Until every gap is filled most cases fail; that is the point of the starter.

A skipped test counts as a failure. A full run takes about two minutes here.

## Failure states

`JAVA_HOME` wrong: no Java gateway. `ModuleNotFoundError: pyspark`: the
virtual environment is not the interpreter running the tests. A case failing
with `DIVIDE_BY_ZERO` in a report means a rate is divided without a guard. A
count of 30 fact rows instead of 22 means the history join lacks its validity
window.

## Cleanup

The runner creates one temporary directory (prefix `lab-l11-`) for the Spark
warehouse and scratch space and deletes it when the session stops; it writes no
`spark-warehouse`, `metastore_db` or `__pycache__` into this folder. Delete
`.venv` and any evidence or output files you asked for when you are done.

## Limits

Local Apache Spark on toy data: the timings mean nothing and nothing here is a
benchmark. The expected values were derived by hand (DATA.md) and prove the
queries match this contract on these fixtures, not that the contract suits a
real plant. The metric view sketch in SOLUTIONS.md is a platform adaptation
written from documentation; it was **not executed** and needs a Unity
Catalog-enabled workspace, a supported runtime and your own table names.
