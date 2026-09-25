# Lab L16 — Bundle delivery for a small data project

**Execution class P (platform-guide).** This package runs a real set of local
checks and names every Databricks step it does not run. Executed here: YAML
parsing, the lab's structure rules for the bundle configuration, variable
resolution per target, the project's unit tests and its entry point on a
temporary directory, all in Python 3.12 with PyYAML 6.0.3. **Not executed:**
authentication to a workspace, `databricks bundle validate`, `plan`, `deploy`
and `run`, any job run, integration check or promotion. No workspace was
contacted; a guard in the runner refuses network connections and subprocesses
and the tests assert that nothing tried.

## Purpose and outcome

Cinderline Components (fictional) computes a daily scrap rate per production
line. The logic lived in one notebook, edited in the workspace, copied by hand
between environments, with a token pasted into it. This lab is the reviewed
replacement: a small Python package with its own unit tests and a Declarative
Automation Bundle (formerly Databricks Asset Bundles) that deploys the same
code to `dev`, `test` and `prod` with different parameters. After the lab you
can:

- lay out a project as `src/` package, `tests/`, `pyproject.toml` and bundle
  configuration, and keep environment differences in configuration;
- read a `databricks.yml` with targets, modes, variables, `run_as`,
  `git.branch` and permissions, and predict what each target resolves to;
- tell a local syntax or structure check apart from authenticated validation,
  deployment and a job run, and say which evidence each one produces;
- review a pull request's configuration against a promotion checklist.

## Prerequisites

- Python 3.12 and `pip install -r requirements.txt` (PyYAML 6.0.3 only).
- No Databricks account, CLI, SDK or network access is needed or used.

## Run

```
python run_tests.py                            # judge solutions/ (16 checks)
python run_tests.py --evidence evidence.json   # also write the evidence record
python run_tests.py --starter                  # judge your work in starters/
python bundlecheck.py solutions/project/BUNDLE.md             # findings (none)
python bundlecheck.py solutions/project/BUNDLE.md --resolve   # resolved targets
python bundlecheck.py solutions/project/BUNDLE.md --materialize /some/new/dir
```

To run only the project's own tests, from `solutions/project`:
`PYTHONPATH=src python -m unittest discover -s tests -t tests`.

`run_tests.py` prints a classification table at the end: five local steps
marked EXECUTED with their evidence, seven platform steps marked NOT RUN. A
full run took well under a second on one machine here.

## Cleanup

Every temporary directory the runner creates (`lab-l16-volume-*`,
`lab-l16-project-*`, `lab-l16-main-*` in the system temp directory) is removed
when its test finishes, including on failure. The runner writes no bytecode and
deletes any `__pycache__` it finds in the package. `--materialize` writes only
where you tell it to; delete that directory yourself.

## Files

| Path | What it is |
|---|---|
| `solutions/project/` | the reviewed project: `src/cinderline_quality/` (rules, parameters, entry point), `tests/`, `pyproject.toml`, `requirements-ci.txt`, `BUNDLE.md` |
| `solutions/project/BUNDLE.md` | `databricks.yml` and `resources/scrap_job.yml` as fenced YAML blocks (the download may not contain `.yml` files) |
| `starters/project/` | the same project as first proposed: four gaps in `scrap.py`, eight problems in `BUNDLE.md` |
| `bundlecheck.py` | the lab's local checker: block extraction, strict parsing, rules D1–D11 and H1–H10, resolution, materialization |
| `run_tests.py` | sixteen checks, the network guard, the classification table and the evidence writer |
| `fixtures/` | synthetic inspection exports, 21 configuration mutations, two broken YAML blocks |
| `expected/` | hand-derived expected results (derivations in `DATA.md`) |
| `TASKS.md`, `SOLUTIONS.md`, `DATA.md`, `PROMOTION.md` | tasks, explained solution, data dictionary, promotion checklist |

## Limits

- The structure rules are a small, local subset. Rules D1–D11 restate
  behaviour read in the Databricks CLI v1.17.0 source; they are not the CLI and
  cannot replace `databricks bundle validate`, which authenticates, asks the
  workspace who the current user is and applies the full schema. Rules H1–H10
  are this lab's own review policy, stricter than the CLI in places.
- The entry point ran against a temporary folder, not a Unity Catalog volume.
- `requirements-ci.txt` pins build tools the pipeline would use; they were
  confirmed to exist on PyPI but were not installed or run.
- Hosts use the reserved `.example` domain and the service principal IDs are
  placeholders. Nothing here is a real workspace, identity or credential.
