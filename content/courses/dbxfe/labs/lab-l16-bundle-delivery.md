*Execution class P (platform-guide): the local checks ran in Python 3.12.3 with
PyYAML 6.0.3 on one machine, and every Databricks step is named and left NOT
RUN. No workspace was contacted, no token existed, and a guard in the test
runner refused network connections and subprocesses; two tests assert that
nothing tried. This page is studyable without installing anything; the package
`lab-l16-bundle-delivery` holds the files if you want to run it.*

### Purpose

The reproducible-delivery module argues that a data job should move from a
laptop to production as one reviewed commit, with environment differences in
configuration, rules proven by unit tests and every claim backed by the
evidence of its own state. This lab makes that concrete for Cinderline
Components' daily scrap-rate job (fictional). The old version was one notebook,
edited in the workspace, copied by hand between environments, with a token
pasted into it. The reviewed version is a small Python package with its own
tests plus a Declarative Automation Bundle (formerly Databricks Asset
Bundles): `databricks.yml` with `dev`, `test` and `prod` targets and a job
resource file. Because the download may not carry `.yml` files, both YAML
files travel as fenced blocks in `BUNDLE.md`, each headed `# file: <path>`.

### The project

| path | role |
|---|---|
| `src/cinderline_quality/scrap.py` | the rules: validate a record, compute a rate, summarize per line |
| `src/cinderline_quality/params.py` | parse `--catalog`, `--schema`, `--alert-threshold` and refuse unsafe values |
| `src/cinderline_quality/main.py` | thin entry point: read the export, call the rules, write the summary |
| `tests/` | 14 unit tests with hand-computed expectations |
| `pyproject.toml` | package metadata, the `scrap_summary` entry point, a pinned build backend |
| `BUNDLE.md` | `databricks.yml` and `resources/scrap_job.yml` |

### The fixture

One synthetic export day, ten records:

| # | line | inspected | scrapped | what happens |
|---|---|---:|---:|---|
| 0–1 | L1 | 480, 520 | 12, 14 | counted |
| 2–3 | L2 | 300, 300 | 15, 12 | counted |
| 4 | L3 | 250 | 10 | counted |
| 5 | L2 | 40 | 45 | rejected: scrapped exceeds inspected |
| 6 | L4 | 0 | 0 | counted, idle line |
| 7 | L1 | −5 | 0 | rejected: not a non-negative integer |
| 8 | L3 | missing | 3 | rejected: missing inspected |
| 9 | L5 | 7 | 1 | counted |

### Task 1: the rules and their tests

The starter's `scrap.py` has four gaps; the tests describe the fix. Before the
fix the package tests read 8 passed, 5 failed and 1 error. The error is L4's
division by zero; the failures come from `round()`, which sends 0.03125 to
`0.0312` (ties to even) and prints 26 of 1000 as `0.026`, from counting the
45-of-40 record, and from alerting when the rate merely equals the threshold.
After the fix, all 14 pass and the summary is:

| line | inspected | scrapped | scrap_rate | alert |
|---|---:|---:|---|---|
| L1 | 1000 | 26 | 0.0260 | no |
| L2 | 600 | 27 | 0.0450 | yes |
| L3 | 250 | 10 | 0.0400 | no: equal is not above |
| L4 | 0 | 0 | none | no |
| L5 | 7 | 1 | 0.1429 | yes |

### Task 2: review the configuration

The starter `BUNDLE.md` is valid YAML and looks nearly finished. The lab's
checker finds eight problems in it:

| rule | location | problem |
|---|---|---|
| H1 | `targets.test` | no test target |
| D4 | `targets.prod.workspace.root_path` | production mode without a fixed root path |
| D9, H5 | `targets.prod.workspace.token` | a field the bundle schema does not have, holding a credential |
| H2 | `targets.prod.git.branch` | prod can be deployed from any branch |
| H3 | `targets.prod.run_as` | the job would run as whoever deployed it |
| H6 | `targets.prod.variables.alert_threshold` | a business rule that differs from test |
| D7 | task parameter `${var.catalogue}` | a variable that was never declared |

Rules D1 to D11 restate behaviour read in the Databricks CLI v1.17.0 source;
H1 to H10 are the lab's own review policy. The reviewed version fixes all
eight; `test` also pauses its schedule with a preset because the pipeline
starts test runs itself.

### Task 3: what each target resolves to

| target | --catalog | --schema | root path | left for the workspace |
|---|---|---|---|---|
| dev | cinderline_dev | quality_${workspace.current_user.short_name} | ~/.bundle/cinderline_scrap/dev | schema, root path |
| test | cinderline_test | quality | fixed, in the test principal's folder | nothing |
| prod | cinderline_prod | quality | fixed, in the prod principal's folder | nothing |

`--alert-threshold` is `0.0400` everywhere. The runner then calls the real
entry point with `test`'s resolved arguments on a temporary folder standing in
for the volume and gets the same five rows and three rejections. It also shows
the boundary from the other side: `dev`'s arguments are refused locally,
because only the workspace knows whose name replaces
`${workspace.current_user.short_name}`.

### Task 4: the failure cases

Twenty-one mutations of the reviewed configuration each trigger exactly the
expected rule and location. Examples: deleting prod's root path fires D4;
spelling the mode `prod` fires D1; pasting a token fires D9 and H5; unpinning a
library in the job environment fires H7; `resource/*.yml` instead of
`resources/*.yml` fires H10. That last one matters: the CLI source reports an
error only for an include without wildcards that matches nothing, so a
mistyped wildcard would deploy a bundle with no job in it. Two syntax cases
show the loader's line numbers: a repeated `dev:` key on line 7 (plain
`safe_load` would silently keep the second one) and a tab on line 8.

### Task 5 and 6: classification and promotion

The runner ends with a twelve-row table:

| # | step | class | status |
|---|---|---|---|
| 1 | extract and parse the YAML blocks | local syntax check | EXECUTED |
| 2 | rules D1–D11, H1–H10 | local schema and structure check | EXECUTED |
| 3 | resolve dev, test and prod | local configuration check | EXECUTED |
| 4 | package unit tests | local unit tests | EXECUTED |
| 5 | entry point on a temporary folder | local execution of package code | EXECUTED |
| 6 | `databricks auth login`, M2M or federation | authentication | NOT RUN |
| 7 | `databricks bundle validate --strict` | authenticated validation | NOT RUN |
| 8 | `databricks bundle plan` | deployment preview | NOT RUN |
| 9 | `databricks bundle deploy` | deployment | NOT RUN |
| 10 | `databricks bundle run scrap_summary` | job run (execution) | NOT RUN |
| 11 | check the test run's output | integration test | NOT RUN |
| 12 | deploy the same commit to prod | promotion | NOT RUN |

`PROMOTION.md` turns those rows into a fourteen-gate checklist, from the
reviewed pull request to the first prod run, with the evidence each gate
requires. This run supports the unit-test, structure and resolution gates and
nothing after them.

### What the tests prove and do not prove

They prove that the rules behave as specified on synthetic records, that the
reviewed configuration satisfies every local rule and resolves to the intended
parameters, that 21 specific mistakes are each caught for the stated reason,
that the starter's gaps are the documented ones, and that none of it touched
the network. They do not prove that the configuration passes the CLI's full
validation, that the service principals exist or hold the right permissions,
that the wheel builds, that the job runs on Databricks compute or reads a real
volume, or anything about production. Each of those is a later state with its
own evidence.

### Setup and cleanup

Install Python 3.12 and `pip install -r requirements.txt` (PyYAML 6.0.3), then
run `python run_tests.py`; a full run took well under a second here. Temporary
folders are removed as each test finishes, no bytecode is written, and
`--materialize` writes only to the directory you give it.
