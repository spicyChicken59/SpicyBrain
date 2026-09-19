# Reliable Data Foundations exercise bundle

Optional, original synthetic local exercises for the SpicyBrain path. Reading,
prediction, worked answers and study progress in the app need no workspace.
Start with `TASKS.md`; consult `SOLUTIONS.md` after your attempt. `starters/`
contains deliberate gaps; `solutions/` contains complete reference programs.
`fixtures/` contains inputs, and `expected/` contains independently authored
literal expected outputs. `run_tests.py` exercises the complete references.

## Reproducible local setup

Pinned teaching/test line: **Python 3.12, Java 17, PySpark 4.0.4, Py4J 0.10.9.9**.
The builder's exact patch versions and results are in the repository's
`docs/evidence/reliable-data-execution.json` and the bundle's `execution.json`.
Apache documents Python 3.9+ and Java 17/21 for this Spark release. Use Python
3.12 and Java 17 to reproduce this bundle; other versions were not locally
verified. Spark 4.0.1 was tried and rejected after the documented Windows
Python 3.12 worker defect [SPARK-53759](https://issues.apache.org/jira/browse/SPARK-53759).
Do not work around that defect by disabling tests or replacing Spark with
ordinary arithmetic. The bundle pins a maintenance release containing the fix.

Install Python 3.12 and a Java 17 JDK from their publishers or an approved local
package manager. Set JAVA_HOME to the JDK directory, not its `bin` folder.
Install dependencies in a dedicated virtual environment. Spark downloads are
large (about 434 MB compressed); allow local disk space and memory. No account,
cloud resources or paid service is needed. Internet is needed for installation,
not for the data transformations. The tests bind local Spark to loopback and
disable its web UI. They send no notifications and never upload study state.

From the extracted bundle on Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
# If java is not already configured, set this to your actual installed JDK:
$env:JAVA_HOME = 'C:\path\to\jdk-17'
.\.venv\Scripts\python.exe run_tests.py --spark --evidence local-execution.json
```

From the extracted bundle on macOS/Linux:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
# Set JAVA_HOME to your installed Java 17 JDK if java is not on PATH.
.venv/bin/python run_tests.py --spark --evidence local-execution.json
```

From the repository root/CI, after configuring Python and Java:

```sh
python -m pip install -r content/exercises/reliable-data/requirements.txt
python content/exercises/reliable-data/run_tests.py --spark --evidence docs/evidence/reliable-data-ci.json
```

For the Python-only bridge/resolution/transfer tasks, omit `--spark`; that
does **not** pass the complete Spark acceptance gate. The runner reports the
actual languages exercised, version, number of tests, errors and skipped tests.
With `--spark`, an absent dependency or failed Spark test is a failed command.

## Failure states and cleanup

If JAVA_HOME is wrong, Spark cannot start its Java gateway. If Python workers
cannot start, check the pinned release and that the current interpreter is the
virtual environment; the runner sets PYSPARK_PYTHON to that interpreter. A
Windows native-Hadoop/winutils warning can appear during startup; these tests
use local in-memory data and do not test Hadoop file permissions. A passed
run, rather than the mere absence of a warning, establishes these examples.
Memory/resource failures are failures, not a reason to skip Spark assertions.

The runner stops Spark in teardown. It creates no database tables, cloud
objects, secrets, deployments or real external effects. The only intentional
output is the evidence JSON path you choose. After exiting all local sessions,
delete only the virtual environment you created and your own local evidence
file if you no longer need them; retain source fixtures and your written
answers. Remove a separately downloaded portable JDK only if you installed it
for this exercise and no other project uses it. Normal package caches may
remain. No broad disk-cleanup command is supplied.

## Scope and source honesty

The source revision/quarantine/publication rules are **fictional teaching
policy**, not a Databricks product guarantee. Local reference logic recomputes
small retained history and stores the pipeline simulation in memory. It is
not a scalable production streaming implementation, durable orchestrator,
verified connector or exactly-once external notification system.

No Delta commands or Databricks workspace, Jobs, Unity Catalog, private network
or Free Edition exercises were executed by this bundle. Delta MERGE shown in
the course is separately marked illustrative/unexecuted and must be checked
against its target engine/runtime. Nothing here provisions an optional cloud
lab. A local pass never proves permissions, cloud behavior, scale or mastery.

`sources.json` records primary documentation, reviewed claims, versions and
limits. The original synthetic data and explanations may be reused with this
repository's license; external documentation remains with its publisher.
