# Lab L16 tasks

Work in `starters/project/`. `python run_tests.py --starter` judges your copy;
it starts with failures on purpose and each task below removes some of them.
Nothing in any task needs a Databricks workspace, and nothing should try to
reach one.

## Task 1 — make the rules match their tests (package)

`starters/project/src/cinderline_quality/scrap.py` has four marked gaps. The
project's own tests (`starters/project/tests/`) already describe the rules;
make them pass without editing the tests.

1. A record with more scrapped than inspected parts is refused with the
   reason `scrapped exceeds inspected` and is not counted.
2. A line where nothing was inspected has no rate (`None`) and no alert; it
   must not raise.
3. Rates are `Decimal` values rounded half up to four places and printed with
   four decimals: 1 of 32 is `0.0313`, 26 of 1000 is `0.0260`.
4. An alert means the rate is strictly greater than the threshold: exactly
   `0.0400` against a threshold of `0.0400` is not an alert.

Expected: the unit-test row of the classification table reads
`14 tests: 14 passed`. Before you start it reads 8 passed, 5 failed, 1 error;
the error is the division by zero.

## Task 2 — review and correct the bundle configuration

`starters/project/BUNDLE.md` holds `databricks.yml` and
`resources/scrap_job.yml` as the pull request first proposed them. Run
`python bundlecheck.py starters/project/BUNDLE.md` and fix every finding by
editing the YAML blocks. The corrected configuration must:

- keep `dev` as the default target with `mode: development`;
- add a `test` target with `mode: production`, a fixed `workspace.root_path`,
  `run_as` a service principal, the schedule paused by preset and catalog
  `cinderline_test`;
- give `prod` a fixed `workspace.root_path`, `git.branch: main` and `run_as`
  its own service principal;
- contain no credential of any kind;
- keep `alert_threshold`, a business rule, identical in every target;
- reference only declared variables in the job's task parameters.

Expected: `bundlecheck.py` prints `[]`, and
`python bundlecheck.py starters/project/BUNDLE.md --resolve` shows three
targets whose task parameters differ only in `--catalog` and `--schema`.

## Task 3 — predict the resolved targets before you look

Without running anything, write down for `dev`, `test` and `prod`: the
`--catalog`, `--schema` and `--alert-threshold` arguments the job would
receive, the workspace root path, and which values only a workspace can
resolve. Then run `--resolve` and compare. Expected answers are in
`expected/resolved_targets.json`; explain why `dev`'s schema cannot be
resolved locally and why that is the point of `mode: development`.

## Task 4 — the failure cases

`fixtures/bundle_mutations.json` lists 21 small changes to the reviewed
configuration. For five of them of your choice, predict the rule that fires
and the location it names before reading `expected/bundle_findings.json`.
Then explain, for M16 (`resource/*.yml`), why the Databricks CLI would accept
the change without an error and what would be missing after a deployment.

## Task 5 — classify the evidence

Read the classification table printed at the end of a run. For each of the
twelve steps, state which evidence it produces (a parse result, a findings
list, a test count, a run ID, a deployment record) and who could produce it
(you on a laptop, the pipeline's service principal in a test workspace, a
reviewer). Mark which of the twelve this lab can honestly claim.

## Task 6 — promotion

Complete `PROMOTION.md` for this change as if you were the reviewer: for every
row, name the evidence you would require, and mark the rows this lab's run
supports and the rows that remain NOT RUN. Do not tick a row whose evidence
does not exist.

## Transfer

The plant adds line L6 and a new export day: `fixtures/inspections_transfer.json`
contains a tie at the fifth decimal (1 of 32), a boolean count, a text count
and a line with nothing inspected. Predict every row and every rejection, then
compare with `expected/scrap_transfer.json`.
