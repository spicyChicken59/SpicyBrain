# Lab package brief

The lab shelf is 24 packages under `content/exercises/<lab-id>/`, each zipped
by the integrator into `content/downloads/<lab-id>.zip` and indexed in
`course.json` (`labs[]`, with a Markdown walkthrough under
`content/courses/dbxfe/labs/<lab-id>.md`). The original reliable-data
package stays untouched; L06 reuses its resolver as an unchanged reference
by copying `content/exercises/reliable-data/solutions/reference.py`
byte-for-byte and adding a separate transfer fixture.

Execution classes (from `academy.json`; the class is fixed per package):

- **R (local-executed)**: the reference solution and its tests are executed
  here in a pinned CPU environment. A failing R lab is a delivery blocker, not
  a reason to relabel it.
- **T (tabletop)**: complete authored exercise whose engine/platform is not
  executed (L14 governance review, L15 three-cloud diagnosis); the local
  script only evaluates the authored policy/diagnosis table.
- **P (platform-guide)**: complete platform adaptation with target execution
  explicitly unclaimed (L16 bundle delivery, L23 transactional state); local
  static checks (YAML/JSON structure, SQL syntax on real PostgreSQL 16 for L23)
  are labelled separately.

## Package layout (every lab)

```
content/exercises/<lab-id>/
  README.md          # purpose, outcome, environment class, prerequisites, setup, run, cleanup, limits
  TASKS.md           # starter tasks with explicit expected behaviour (no solutions)
  SOLUTIONS.md       # complete explained solution, intermediate outputs, one wrong approach and why it fails
  DATA.md            # data dictionary for fixtures / generator, seed, provenance (synthetic)
  requirements.txt   # pinned dependencies actually tested (exact versions)
  fixtures/          # original synthetic inputs (.json/.csv) or a deterministic generator (.py, seed)
  expected/          # independently authored literal expected outputs (never produced by the solution)
  starters/          # learner starters with deliberate gaps
  solutions/         # complete reference programs
  run_tests.py       # unittest runner; --evidence <path> writes JSON evidence (see below)
```

Only `.md .txt .json .csv .py .sql .toml` members are allowed in the ZIP
(YAML/Terraform/notebook examples go in fenced blocks inside a `.md`). No
member over the archive bounds (20 MB compressed, 50 MB expanded, 200
members). No symlinks, no absolute paths, no `__pycache__`, no `.venv`.

## Tests (R labs)

`run_tests.py` must: run offline; bind Spark to `local[2]` with the UI
disabled and `spark.sql.shuffle.partitions` small; compare against
`expected/*.json` literals; include at least one negative/failure case and
one altered-input transfer test; hash every fixture and produced output
(SHA-256) into the evidence JSON; record Python/Java/Spark/library versions,
start/end time, test counts, skips (must be 0) and exit status. Evidence
shape:

```json
{ "lab": "lab-l04-plans-shuffle", "executionClass": "local-executed",
  "python": "3.12.3", "java": "21.0.10", "packages": {"pyspark": "4.0.4"},
  "startedAt": "…", "finishedAt": "…", "tests": 9, "failures": 0, "errors": 0, "skipped": 0,
  "exit": 0, "fixtureHashes": {"fixtures/events.json": "…"}, "outputHashes": {"…": "…"},
  "commands": ["python run_tests.py --evidence evidence.json"], "notes": "…" }
```

Never make a test pass by comparing the solution with an expected value
computed by the same code; expected literals are authored by hand or by an
independent calculation described in `DATA.md`. Deliberately broken cases
must fail for the expected reason (assert the reason).

## Environments available here

- Spark labs: `/home/user/labenv/spark-env/bin/python` (Python 3.12.3,
  PySpark 4.0.4, Py4J 0.10.9.9, delta-spark 4.0.0, pandas 3.0.6, pyarrow
  25.0.1; Java 21.0.10 at `/usr/lib/jvm/java-21-openjdk-amd64`). Delta labs
  configure `spark.jars.packages` only if network allows; prefer
  `delta-spark`'s `configure_spark_with_delta_pip` and record what happened.
- ML labs: `/home/user/labenv/ml-env/bin/python` (mlflow 3.16.1,
  scikit-learn 1.9.1, pandas 3.0.6, numpy 2.5.3, scipy 1.18.1). MLflow runs use
  a local file store inside a temporary directory, never a server.
- PostgreSQL 16 server binaries are installed (`/usr/lib/postgresql/16`); L23
  may `initdb` into a temporary directory, start on a loopback port, run SQL,
  stop and delete. Label it "local PostgreSQL 16", never "Lakebase".
- Plain-Python labs: `/usr/bin/python3.12` with the standard library.

Pin exactly the versions you tested in `requirements.txt` and README.

## Honesty rules

- Say what was executed: "local Spark 4.0.4 on one machine", never "on
  Databricks". Delta means open-source delta-spark. MLflow means open-source
  MLflow with a file store. PostgreSQL means the local server.
- Toy timings are illustrations of mechanism; never call them benchmarks.
- Notifications and external effects are local stubs that append to a list.
- Every number in `expected/` has a stated derivation.
- No real credentials, tokens, hostnames, customer data or employer schemas.
- Cleanup instructions remove every temporary directory the lab creates.

## Definition of done for a lab task

1. Package files complete per layout; README states the execution class.
2. `python run_tests.py --evidence <scratch>/evidence.json` passes with zero
   skips in the named environment; the evidence JSON is copied to
   `docs/academy/labs/<lab-id>.json`.
3. The walkthrough `content/courses/dbxfe/labs/<lab-id>.md` (≥600 words)
   lets a reader study the lab without installing anything: purpose, the
   fixture in a small table, each task with its intermediate output, the
   failure case, what the tests prove and do not prove, and setup/cleanup.
4. A one-paragraph report of what was run, versions, and any limitation.
