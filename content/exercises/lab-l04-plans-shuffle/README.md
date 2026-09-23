# Lab L04 — Plans, shuffles and skew: reading local Spark evidence

**Execution class: R (local-executed).** The reference solution and its tests
run here on local Apache Spark 4.0.4 in `local[2]` mode on one machine. Nothing
in this package runs on Databricks, and no number in it is a benchmark.

## Purpose and outcome

You will build a handful of small transformations over a synthetic Cinderline
Components inspection feed, read what Spark *plans* for each one (`explain()`),
predict the expensive boundary, and then compare that prediction with what
Spark actually *ran*: partition membership, stages and tasks, and the shuffle
records each task read and wrote, all read back from Spark itself. Along the
way you change exactly one variable at a time (a broadcast hint, adaptive
execution, a salt column, the partition count) and see which evidence moves and
which does not.

After the lab you can:

- tell a narrow dependency from a wide one by reading a plan;
- predict how many `Exchange` nodes and stages a grouped sum, a sort-merge
  join and a broadcast join need, and check the prediction;
- say how many rows actually crossed each shuffle (12 partial rows for the
  grouped sum, 243 for the sort-merge join, 8 for the broadcast join);
- show that one hot key stays in one task however many partitions you ask for,
  and that a round-robin `repartition(n)` does not change that;
- split the hot key with a salt and confirm the totals do not change;
- read an adaptive plan before and after its action, say what the runtime
  changed, and explain why its broadcast build side is not a stable fact;
- watch adaptive skew-join handling split the hot partition once its size
  thresholds are scaled down to toy size, and say why it did not do so at the
  defaults;
- refuse a `collect()` that would move the whole frame into the driver.

## Prerequisites

Lab L02/L03 or the *SQL, Python and PySpark transformations* module: typed
DataFrames, column expressions, joins. Comfort reading a few lines of Python.

## Environment (pinned, actually tested)

| Item | Version used for the recorded evidence |
|---|---|
| Python | 3.12.3 |
| Java | OpenJDK 21.0.10 (`JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64` on the build machine) |
| PySpark / Py4J | 4.0.4 / 0.10.9.9 (see `requirements.txt`) |
| Spark master | `local[2]`, web UI and console progress bar disabled, driver bound to `127.0.0.1` |
| `spark.sql.shuffle.partitions` | 4 |
| Adaptive execution | off for every test except 09, 10 and 14, which switch it on deliberately |
| `spark.sql.autoBroadcastJoinThreshold` | `-1` (off) except test 10, which restores the default 10 MB |

Apache documents Java 17 or 21 for this Spark line; only Java 21.0.10 was
exercised here. Other versions were not verified.

## Setup

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
# JAVA_HOME must point at a JDK directory (not its bin folder) if java is not on PATH.
```

No account, cloud resource, network call or paid service is needed after the
install. The fixtures are already generated; `fixtures/generate_inspections.py`
regenerates them byte-for-byte from fixed seeds if you want to check.

## Run

```sh
.venv/bin/python run_tests.py --evidence local-evidence.json
```

The runner executes 14 tests, prints each name, and writes JSON evidence:
versions, start/end time, test counts (skips must be 0), exit status, SHA-256
hashes of every fixture, expected and solution file, hashes of every captured
output, and the captured plans and measurements themselves under
`observations`. The committed run is `docs/academy/labs/lab-l04-plans-shuffle.json`
in the SpicyBrain repository. A failed or skipped test is a failed run; do not
relabel it.

To work through the tasks yourself, open `TASKS.md`, fill the predictions in
`starters/execution_task.py`, then implement the functions there
(`python starters/execution_task.py` runs its small demonstration). Read
`SOLUTIONS.md` only after your attempt.

## How the runtime evidence is read

- **Jobs, stages and tasks** come from `SparkContext.statusTracker()`: each
  action runs inside its own job group, and the runner lists the stages each job
  executed, separating stages that ran from stages Spark skipped because their
  shuffle output already existed.
- **Shuffle records per stage and per task** (the *Shuffle Read* and *Shuffle
  Write* columns of the web UI's Stages tab) come from Spark's application
  status store, the store the UI renders, reached through Py4J because the UI
  is disabled. That store is an internal Spark API; the lab is pinned to Spark
  4.0.4, and on another version you should check it still exists before
  trusting the helper.
- **Partition membership** comes from `spark_partition_id()`, grouped and
  counted.
- **Wall-clock time is never evidence.** It is not recorded or asserted.

## Files

```
README.md  TASKS.md  SOLUTIONS.md  DATA.md  requirements.txt  run_tests.py
fixtures/   inspections.json (240 rows, skewed), inspections_balanced.json (240 rows, even),
            plants.json (3 rows), generate_inspections.py (seeded generator)
expected/   totals.json (plain-Python derivation, see derive_expected.py), plans.json (hand-written predictions)
starters/   execution_task.py (learner starter with gaps)
solutions/  execution_evidence.py (reference solution and measurement helpers)
```

## Failure states

- Spark cannot start its Java gateway: `JAVA_HOME` is wrong or Java is missing.
- Python workers fail with `PYTHON_VERSION_MISMATCH`: the workers started a
  different interpreter. The runner and the starter both set `PYSPARK_PYTHON`
  to the interpreter they run under; do the same in your own scripts.
- A "native-hadoop library" warning and a note that `spark.local.dir` may be
  overridden by a cluster manager are expected at startup and harmless here.
- `stage metrics ... did not settle`: the status store did not report every
  task within ten seconds. Re-run once; if it persists, the internal store API
  differs from Spark 4.0.4.
- If a partition-membership assertion fails on a different Spark version, the
  hash function that places keys may have changed. That is a real finding about
  the version, not a reason to edit the expected values.

## Cleanup

The runner creates one temporary directory (`lab-l04-…` under the system
temporary folder), points `spark.local.dir` and `spark.sql.warehouse.dir` at
it, and deletes it after stopping Spark; the evidence records
`temp_dir_removed: true`. The starter does the same with its own directory.
Nothing else is written except the evidence path you name: no tables, secrets
or external effects. Remove `.venv/` and your own evidence file when you are
done; keep the fixtures and your notes.

## Limits — read before quoting anything

- **Local Spark, one machine, 240 rows.** The stage, task and shuffle-record
  counts are exact for this configuration; they say nothing about wall-clock
  time, network cost, spill or memory at production scale.
- **Where keys land depends on Spark's hash function.** The tests assert
  properties (the hot key never splits; salting reduces the largest partition),
  and record the actual partition ids as observations rather than requirements.
- **Adaptive execution's broadcast side is a runtime outcome, not a rule.**
  With the default 10 MB threshold it converted the sort-merge join to a
  broadcast join every time, but the side it built changed between identical
  runs: in the committed evidence six runs built the right (dimension) side
  four times and the left (fact) side twice. The documented rule converts
  when the runtime statistics of *any* join side qualify, so the order in which
  the two input shuffles finish is the likely reason; the lab does not prove
  the cause. The test asserts only the switch and records the sides.
- **Skew-join splitting at default settings was not triggered, and was then
  shown at toy thresholds.** Its documented default partition threshold is
  256 MB (read back here as `268435456b`, with a factor of 5.0 over the median),
  far beyond this data. Test 14 scales the threshold and the advisory partition
  size down to 1 KB, on the record, and Spark then marked the join
  `SortMergeJoin(skew=true)` and read the hot partition with two tasks instead
  of one. That demonstrates the mechanism; it is not a recommended setting.
- **`bounded_collect` guards a teaching example.** It is not a production
  safety mechanism; it exists to make the collection risk explicit.
- Nothing here is Databricks, Photon, a SQL warehouse or a query profile; the
  performance-diagnosis module covers those with their own sources.
