# Lab L05 — Delta snapshots, merges, schema and maintenance on a real local table

**Execution class: R (local-executed).** The reference solution and its 19 tests run here on
local Apache Spark 4.0.4 with the open-source `delta-spark` 4.0.0 package, in `local[2]` mode on
one machine. Nothing in this package runs on Databricks, nothing is a benchmark, and no data file
is ever deleted: every `VACUUM` in the lab is a `DRY RUN`, no retention is shortened and Delta's
retention safety check is never turned off.

## Purpose and outcome

You build one tiny Delta table of fictional Cinderline Components inspection results and move it
through nine committed versions: a write, an append, a correcting `UPDATE`, a table-property
commit that turns on the change data feed, three `MERGE`s with different intentions, an append
that adds a column, and `OPTIMIZE`. At each step you predict what Delta will report, then read it
back from Delta itself: the rows a version selects, `DESCRIBE HISTORY`, `DESCRIBE DETAIL`, the
change data feed and the files on disk. Four requests are refused on purpose and you read why.

After the lab you can:

- read any earlier version with `versionAsOf` and explain why a plain Parquet read of the folder
  says 30 when the table says 20;
- explain why a key that is missing from an incremental delivery must survive a `MERGE`, and why a
  complete snapshot is the only delivery whose silence means "retired";
- reproduce Delta's refusal of a source with two rows for one matched key, show that the same
  delivery is accepted (and duplicates a key) when that key is new, and fix both with a
  latest-revision de-duplication plus a revision guard that also skips a stale replay;
- scope `WHEN NOT MATCHED BY SOURCE` to what a snapshot covers, and show on a disposable copy
  how an unscoped clause deletes rows the delivery never described;
- read row-level changes (`insert`, `update_preimage`, `update_postimage`, `delete`) from the
  change data feed, and explain why a range that starts before the feed was enabled is refused;
- tell schema enforcement (an append with an unexpected column is refused) from explicit schema
  evolution (`mergeSchema` for one write), and see that time travel returns the old schema;
- show that `OPTIMIZE` rewrites files but not rows, that a second run does nothing, and that the
  replaced files stay on disk for time travel until a `VACUUM` older than the retention removes them;
- see Delta's retention safety check refuse a zero-hour `VACUUM ... DRY RUN`, and name the table
  features that the change data feed and liquid clustering add to the protocol.

## Prerequisites

The *Delta tables, commits and snapshots* module (the folder is not the table; a commit changes
the picture) and comfort reading short SQL `MERGE` statements and a few lines of Python.

## Environment (pinned, actually tested)

| Item | Version used for the recorded evidence |
|---|---|
| Python | CPython 3.12.3 |
| Java | OpenJDK 21.0.10 |
| PySpark / Py4J | 4.0.4 / 0.10.9.9 |
| delta-spark (open-source Delta Lake) | 4.0.0, with `importlib_metadata` 9.0.1 and `zipp` 4.1.0 (see `requirements.txt`) |
| Delta jars | `io.delta:delta-spark_2.13:4.0.0`, `io.delta:delta-storage:4.0.0`, `org.antlr:antlr4-runtime:4.13.1` |
| Spark master | `local[2]`, web UI and console progress bar disabled, driver bound to `127.0.0.1` |
| Small-data settings | `spark.sql.shuffle.partitions=2`, `spark.databricks.delta.snapshotPartitions=2` |

Only Java 21.0.10 was exercised. Other versions were not verified.

### Delta jars

`delta-spark` is a Python package; the engine is a set of JVM jars. `build_session()` calls
`configure_spark_with_delta_pip`, which asks Spark to resolve
`io.delta:delta-spark_2.13:4.0.0` through Ivy when the session starts: the local Maven and Ivy
caches are tried first and Maven Central only when they lack the jars, so the first run needs
network access unless a cache already holds them. Two environment variables change that without
editing code: `SPICYBRAIN_IVY_DIR` points Spark at an Ivy directory that already holds the jars,
and `LAB_DELTA_JARS` (comma-separated jar paths) bypasses Ivy entirely. The evidence file records
which method ran, the SHA-256 of each jar that was loaded, and whether identical bytes sit in the
local Maven repository (`~/.m2/repository`). For the recorded run Maven Central was rate-limiting the
build machine, so `SPICYBRAIN_IVY_DIR` named a scratch Ivy directory and Ivy resolved all three jars
from the local Maven repository (its `local-m2-cache` resolver); nothing was downloaded.

## Setup

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
# JAVA_HOME must point at a JDK directory if java is not on PATH.
```

## Run

```sh
.venv/bin/python run_tests.py --evidence /tmp/lab-l05-evidence.json   # the acceptance run
.venv/bin/python starters/delta_sequence_task.py                      # your attempt
.venv/bin/python expected/derive_expected.py                          # regenerate the expected file
```

Run everything from this directory. The runner sets `PYSPARK_PYTHON` to its own interpreter before
the session starts, so Spark's Python workers use the virtual environment rather than a system
Python. The acceptance run takes a few minutes on one machine, most of it JVM start-up and
Delta's commit protocol on a table with nine versions; that time is not a measurement of anything.

## Files

| Path | What it is |
|---|---|
| `fixtures/*.json` | six tiny synthetic deliveries, described in `DATA.md` |
| `expected/derive_expected.py` | plain-Python replay of the commit sequence plus documented literals |
| `expected/snapshots.json` | its output, committed; the tests check it equals a fresh derivation |
| `solutions/delta_sequence.py` | the reference functions |
| `starters/delta_sequence_task.py` | your starter: predictions first, five functions to complete |
| `run_tests.py` | the acceptance runner and evidence writer |
| `TASKS.md`, `SOLUTIONS.md`, `DATA.md` | the tasks, the explained solution, the data dictionary |

## Cleanup

The runner and the starter create their tables and Spark's temporary files inside one temporary
directory each (`lab-l05-*` and `lab-l05-learner-*` under the system temporary folder) and delete it
when they finish, even after a failure. If a run is killed, delete any leftover `lab-l05-*` folder
by hand. Ivy's cache (`~/.ivy2*`, or the folder named by `SPICYBRAIN_IVY_DIR`) is outside the lab and
is left alone; delete it only if you no longer need the jars. `rm -rf .venv` removes the environment.
The lab leaves no `spark-warehouse`, `metastore_db` or `__pycache__` in this folder.

## Limits (read before quoting a result)

- This is open-source Delta Lake 4.0.0 on local Spark. Databricks runs its own Delta implementation;
  defaults, error texts, which conditions count as a duplicate match, and features such as
  predictive optimization, automatic liquid clustering and some change-feed modes differ or exist
  only there. Nothing here demonstrates a Databricks behaviour.
- The table has no deletion vectors, so `UPDATE` and `MERGE` rewrite whole files (copy-on-write).
  With deletion vectors enabled the file counts would differ; the rows would not.
- File counts that depend on Spark's partitioning are asserted only as inequalities or as
  consequences of documented behaviour (compaction to one file for a tiny table), never as timings.
- The zero-hour `VACUUM` is requested only in `DRY RUN` mode and is refused before anything is
  listed. A real maintenance decision about retention belongs to the table's owners and the
  longest-running reader, not to a lab.
