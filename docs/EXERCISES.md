# Reliable Data Foundations local exercise contract

This is the optional execution companion for the approved study-hub milestone.
The application remains a static reader with ordinary validated downloads;
it does not execute Python, SQL or downloaded code. All fixtures are original
fiction and all required teaching/prediction/solution work is readable in-app.

Source bundle: [content/exercises/reliable-data](../content/exercises/reliable-data/README.md).
Download: [reliable-data-exercises.zip](../content/downloads/reliable-data-exercises.zip).
Tasks and complete reasoning: [TASKS](../content/exercises/reliable-data/TASKS.md)
and [SOLUTIONS](../content/exercises/reliable-data/SOLUTIONS.md).

## Environment and exact execution evidence

The optional environment is pinned to Python 3.12, Java 17, PySpark 4.0.4 and
Py4J 0.10.9.9. The local run records the actual Python/JDK patch versions,
platform, command, test count, fixture/expected/program hashes, exact outputs,
schemas and captured formatted Spark plan in
[reliable-data-execution.json](evidence/reliable-data-execution.json).
CI produces its own exact-head artifact; do not relabel the Windows local run
as Linux CI, physical-device browser evidence or a Databricks execution.

The completed local suite passed **30 tests, zero failures/errors/skips** in
102.154 seconds with Python 3.12.14, Temurin Java 17.0.20.1+1 and Spark 4.0.4.
Seven exact displayed Python/SQL examples are copied with a SHA manifest and
executed, including separately asserted changed-input tasks. The final archive
also passed CRC/path checks and an extracted standalone 21-test Python smoke
run; [bundle-check evidence](evidence/reliable-data-bundle-check.json) keeps that
limited packaging check separate from the full Spark execution.

The initial Spark 4.0.1 attempt failed in Windows Python workers. Apache's
[SPARK-53759](https://issues.apache.org/jira/browse/SPARK-53759) documents the
same platform/version symptom and lists the maintenance fix. The exercise
dependency was moved to 4.0.4 and rerun; website dependencies were unaffected.
Apache's [versioned runtime documentation](https://spark.apache.org/docs/4.0.4/)
documents Python 3.9+ and Java 17/21. Source review is recorded separately in
[sources.json](../content/exercises/reliable-data/sources.json).

Reproduce from repository root after selecting Python 3.12 and Java 17:

```sh
python -m pip install -r content/exercises/reliable-data/requirements.txt
python content/exercises/reliable-data/run_tests.py --spark --evidence docs/evidence/reliable-data-ci.json
```

The command fails if required Spark cannot execute; no automatic skip/fallback
counts as success. Omitting `--spark` deliberately runs only the Python part and
records that limitation. Setup, failure diagnosis, resource needs and safe
cleanup are in the bundle README. No workspace/cloud provisioning is needed.

## What the test oracle proves

Expected fixtures are independently written literals, never calls into the
implementation under test. Ordered accepted rows and types are compared in
both Spark SQL and PySpark. Baseline intermediate distinct/valid/quarantined
relations have explicit literal rows as well as counts. The grain experiment
records incorrect join count 3 and 32/2, repaired count 2 and 20 inspected,
and an actual local physical plan under disclosed configuration.

Python tests exercise replay, late revisions, valid correction, cross-batch
event/key-version conflicts, malformed/missing/boolean values, invalid latest
revision, unknown ordering, guarded target updates and three failure boundaries.
The transfer task changes key grain, money representation and deletion contract:
composite order-line keys, integer cents and retained explicit cancellations.

| Case | Independently specified business result | Publication behavior |
|---|---|---|
| Baseline | A2 12/1; C1 8/0; total 20/1 (5%) | Current accepted-only snapshot; B quarantined/excluded |
| Exact replay or older A1 arrival | Same accepted rows and totals | Same snapshot identity; raw/audit count can grow |
| Valid A3 correction and replay | A3 14/1; C1 8/0; total 22/1 | New snapshot once; correction replay does not add it twice |
| Conflicting A event or A2 payload | A unresolved; prepared accepted C1 only | New report blocked; last verified 20/1 explicitly stale/previous |
| Invalid latest A3 or missing A ordering | A unresolved; no resurrection of A2 | Same publication block |
| Failure after retained raw/resolution | Correction retained; previous report stays 20/1 and stale | Recovery publishes independently expected 22/1 |
| Failure after publication | 22/1 published; local effect not yet recorded | Recovery records one idempotency-keyed local effect |
| Order-line transfer | O7=900 cents; O8=400; total 1300 | Cancellation tombstone retained; ambiguous current line refuses report |

The Python reference is intentionally stricter for unresolved historical
identity conflicts: it blocks associated keys pending manual adjudication.
There is no arbitrary tie-break or automatic conflict repair. Baseline B's
never-valid exclusion policy is distinct from invalid latest A's unresolved
current state. Neither policy claims complete source coverage.

## Execution boundaries

The reference reprocesses small retained history and the orchestration model is
in memory. It proves teaching examples, not durable/scalable streaming, verified
CDC connectors, exactly-once delivery or production cloud behavior. Notification
effects are local dictionaries; nothing is sent. A passed run does not prove
workspace permissions, private connectivity, Unity Catalog policy, Lakeflow Jobs,
or Databricks Runtime behavior. No Delta command was executed; course MERGE is
illustrative/unexecuted with a separately named runtime context.

## Updating the downloadable artifact

Keep code/data/text in `content/exercises/reliable-data/`, outside app logic.
Run the complete tests, then package only authored files and sanitized execution
JSON using `package_bundle.py`; it rejects cache files and writes deterministic
ZIP entries. Update the course download SHA-256 after packaging. The content
loader verifies the explicit `.zip` path/type, digest and member paths/types
before copying the archive to the built site's download directory. Archive
changes must update the declared digest; a stale digest fails validation.
