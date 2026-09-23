<!-- section:dbxfe-delivery-l01-outcome -->

After this lesson you can move a change to Cinderline's scrap-rate job to production as one reviewed commit, naming at each step the delivery state reached and its evidence. You can lay out a tested package and a bundle with dev, test and prod targets, choose between the CLI, the SDK and raw REST, keep credentials out of code, and write a promotion checklist. Nothing here deploys anything.

<!-- section:dbxfe-delivery-l01-start -->

From [Platform, workspace and compute](#/module/dbxfe-m03): workspace, catalog, compute and storage as separate responsibilities. From [Python for dependable data work](#/module/dbxfe-python): testable functions with inputs and outputs. From [Identity, authorization and audit](#/module/dbxfe-identity), optional prior reading in the governance track: users, groups and service principals. In brief, a user is a person's identity, a group is a named set of identities that permissions are granted to, and a service principal is an identity for automation rather than a person. Commands and keys are spelled as in Databricks CLI v1.17.0 and the Databricks SDK for Python v0.141.0; the rename from Databricks Asset Bundles to Declarative Automation Bundles changed neither.

<!-- section:dbxfe-delivery-l01-states -->

A change passes through five states, each proven only by its own evidence.

| state | what exists | evidence |
|---|---|---|
| local source | a commit whose unit tests pass | commit SHA, test counts |
| validation | the bundle resolved for one target by an authenticated CLI | the `databricks bundle validate` summary naming host and user |
| reviewed artifact | an approved diff and plan | pull-request approval, the reviewed plan |
| deployment | resources created or updated in a workspace | deploy log, deployment state |
| execution | a job run | run ID and result state |

A green unit test says nothing about a missing root path; a clean validate uploads nothing; a successful deploy ends with a job that has never run. Lab L16 executes only the local state and prints every later step as NOT RUN. A status sentence names its state: "tests pass at 7f3c; validated for test; not deployed".

<!-- section:dbxfe-delivery-l01-git -->

Work starts on a branch cut from `main`, so prod keeps its code while `feature/scrap-rounding` collects the fix. A pull request shows the diff, runs the required checks and records reviews; merging moves `main` to a reviewed, tested commit. Review `databricks.yml` like code: `catalog: cinderline_prod` in the test target passes every unit test and points test at production data. Databricks Git folders are a Git client for the same repository inside the workspace; people explore there, while the pipeline deploys from its own checkout. A target can be tied to a branch:

```yaml
targets:
  prod:
    git:
      branch: main
```

Then `databricks bundle plan` and `deploy` for prod stop with "not on the right Git branch" from any other branch unless `--force` is given, which belongs in no pipeline.

<!-- section:dbxfe-delivery-l01-code -->

The old notebook mixed reading, rate rules, writing and a pasted token. The package separates them by what each part needs to run:

```text
src/cinderline_quality/scrap.py    pure rules: records in, rows out
src/cinderline_quality/params.py   parses the job's arguments
src/cinderline_quality/main.py     entry point: read, call, write
tests/                             14 unit tests, answers worked by hand
pyproject.toml                     metadata, entry point, pinned backend
```

A unit test feeds one function records whose answer was computed independently: 1 scrapped of 32 inspected is exactly 0.03125, which the plant's half-up rule makes `0.0313` while Python's `round()` gives `0.0312`; an idle line has no rate rather than zero; a rate exactly at the threshold is not an alert. An integration test is a later state: the deployed job run in test and its output checked.

Pin what the build resolves: `pyyaml==6.0.3`, `build==1.6.1`, `setuptools==84.0.0`, the CLI version, and `databricks-sdk==0.141.0` if used. The CLI follows semantic versioning from v1.0.0, but Beta commands may change in a minor release. Upgrade in a pull request of its own.

<!-- section:dbxfe-delivery-l01-config -->

Catalog, schema and host legitimately differ between environments; the alert threshold is a business rule and must not. Declare variables once and assign them per target:

```yaml
variables:
  catalog:
    description: Exports catalog.
  schema:
    description: Schema in that catalog.
  alert_threshold:
    description: Business rule.
    default: "0.0400"
targets:
  dev:
    mode: development
    default: true
    workspace:
      host: https://cinderline-dev.example
    variables:
      catalog: cinderline_dev
      schema: quality_${workspace.current_user.short_name}
  test:
    mode: production
    workspace:
      host: https://cinderline-test.example
      root_path: /Workspace/Users/00000000-0000-0000-0000-00000000a001/.bundle/${bundle.name}/${bundle.target}
    run_as:
      service_principal_name: "00000000-0000-0000-0000-00000000a001"
    variables:
      catalog: cinderline_test
      schema: quality
```

A value resolves from `--var`, then `BUNDLE_VAR_<name>`, then the target's overrides file, the target's value and the default; with none, validation fails. Development mode makes a private copy: a `[dev <short name>]` prefix, paused schedules, a root path in the deployer's home folder. Production mode requires an explicit `workspace.root_path` so one copy exists (only a recommendation when every job sets `run_as` or a service principal deploys). Cinderline's test target uses production mode too.

<!-- section:dbxfe-delivery-l01-bundle -->

A Declarative Automation Bundle declares the project in `databricks.yml`: `bundle.name`, `include: [resources/*.yml]`, `artifacts` (the wheel), `variables` and `targets`. The job lives in an included file:

```yaml
resources:
  jobs:
    scrap_summary:
      name: cinderline-scrap-summary
      tasks:
        - task_key: summarize
          environment_key: default
          python_wheel_task:
            package_name: cinderline_quality
            entry_point: scrap_summary
            parameters: [--catalog, "${var.catalog}", --schema, "${var.schema}", --alert-threshold, "${var.alert_threshold}"]
```

Four commands, four states. `databricks bundle validate --strict --target test` authenticates, asks the workspace for the current user and applies the schema and mode rules; its summary names host and user before `Validation OK!`, and `--strict` turns warnings such as `unknown field: token` into failures. `databricks bundle plan --target test` lists create, update, recreate and delete actions and changes nothing. `databricks bundle deploy --target test` takes a lock, uploads the wheel and files, applies the plan and records state; deleting or recreating a schema, pipeline or volume needs approval. `databricks bundle run scrap_summary --target test` starts the job and waits for a result state: the only execution evidence. A wildcard include matching nothing is accepted silently, so `resource/*.yml` deploys a bundle without its job.

<!-- section:dbxfe-delivery-l01-interfaces -->

Every client ends in one HTTP request: starting a run is `POST /api/2.2/jobs/run-now` with the job ID and the caller's access token. The Databricks SDK for Python wraps it as `w.jobs.run_now(job_id=...)` with typed arguments, the default authentication chain, safe retries and a waiter; it is labelled Beta, so pin it. The Databricks CLI wraps the same APIs for people and pipelines and adds profiles and bundles: `databricks bundle run` calls run-now, and `databricks api post /api/2.2/jobs/run-now --json '{"job_id": 123}'` sends a raw request with the CLI's authentication. Raw REST suits a language without an SDK; you then own authentication, retries and waiting.

<!-- section:dbxfe-delivery-l01-auth -->

People use OAuth user-to-machine: `databricks auth login --host https://cinderline-dev.example` opens a browser and saves a profile the CLI and SDKs use. Pipelines authenticate as a service principal, identified by an application ID: through OAuth machine-to-machine, with `DATABRICKS_CLIENT_ID` and `DATABRICKS_CLIENT_SECRET` injected by the CI secret store, or through workload identity federation, which exchanges the CI platform's own token and stores no Databricks secret. The pipeline's identity deploys; the job runs as its `run_as` principal. No credential lives in code or configuration: the bundle's workspace section has no token field. A committed token is readable by everyone with the repository; revoke and rotate it, because history keeps it.

<!-- section:dbxfe-delivery-l01-cicd -->

Continuous integration checks every proposed change; continuous delivery moves only merged commits, the same commit, through every environment.

```text
on pull request   (test principal)  unit tests; local checks; validate --strict --target test
on merge to main  (test principal)  deploy --target test; run scrap_summary --target test; output check
on approval       (prod principal)  plan --target prod, reviewed; deploy --target prod
```

Every step records the commit SHA, `databricks --version` and its identity; a failing gate stops the line. Promotion deploys the same reviewed commit to prod with prod's configuration, and each checklist row names its own evidence: approval, test counts at that SHA, validate summary, reviewed plan, test run ID and output check, a prod deploy log with the same SHA. Rollback redeploys the previous commit; `databricks bundle destroy` removes every deployed resource and is not a rollback.

<!-- section:dbxfe-delivery-l01-example -->

Cinderline's first release, synthetic. Commit `7f3c` rounds half up and adds a `test` target. Pull request: 14 of 14 tests, 0 structure findings, and `validate --strict --target test` prints `Validation OK!` for the test principal. A reviewer asks to remove the prod override `alert_threshold: "0.0500"`: a business rule, not configuration. Merge: deploy to test, run `scrap_summary`; run `4471` ends `SUCCESS` and its five rows match the expected rows. Approval: a second person reads `bundle plan --target prod` (one job to create). Prod: the deploy log carries `7f3c`.

<!-- section:dbxfe-delivery-l01-task -->

A pull request proposes the configuration below, and the job's parameters reference `${var.catalogue}`. Review it: list every finding with the rule it breaks, and mark which findings a local check catches, which only `databricks bundle validate` reports authoritatively, and which no tool reports at all. Then write the three pipeline stages this change must pass, with the identity of each.

```yaml
targets:
  dev:
    mode: development
    default: true
  prod:
    mode: production
    workspace:
      host: https://cinderline-prod.example
      token: dapi-0000-example
    variables:
      catalog: cinderline_prod
      schema: quality
      alert_threshold: "0.0500"
```

<!-- section:dbxfe-delivery-l01-solution -->

No `test` target, so nothing separates a merge from prod: a house rule a local checker enforces. `prod` lacks `workspace.root_path`, which production mode requires unless every job sets `run_as` or a service principal deploys: a local check sees the gap; validate reports it authoritatively. `workspace.token` is an unknown key and a credential in a file: validate warns `unknown field: token`, so `--strict` is needed, and the leak is a review finding. No `run_as` and no `git.branch`: house rules. `alert_threshold` overridden in prod means test no longer predicts prod: no tool reports it; a reviewer does. `${var.catalogue}` is undeclared: a local checker catches it, and validate reports "reference does not exist". Stages: pull request (tests, local checks, validate for test, as the test principal); merge (deploy, run and check test, same principal); approval, then prod deploy of the same commit as the prod principal.

<!-- section:dbxfe-delivery-l01-limits -->

Common mistakes: parsing YAML and calling it validated; reading a deploy as a run; expected test values copied from the code's output; a business rule overridden per target; version ranges; a personal token in CI; `--force` or a blanket `--auto-approve` in a script. Limits: one CLI release and one SDK release were read, and later releases can differ; federation's account-side setup is not covered; nothing ran on Databricks.

<!-- section:dbxfe-delivery-l01-sources -->

The documentation host is blocked in this build. Primary references were read in full on 23 September 2026 from Databricks-authored repositories at pinned, hash-checked tags: Databricks CLI v1.17.0 and the Databricks SDK for Python v0.141.0 (commands, phases, modes, variables, authentication types, Jobs and workspace APIs, acceptance-test output). Documentation pages cited beside them were confirmed by search title and URL only.

<!-- section:dbxfe-delivery-l01-links -->

[Platform, workspace and compute](#/module/dbxfe-m03) owns the workspace and catalog a target names. [Identity, authorization and audit](#/module/dbxfe-identity) owns service principals and secret scopes. [Orchestration and operations](#/module/dbxfe-orchestration) owns jobs, tasks and schedules once deployed. The streaming and pipelines modules deploy through the same bundle mechanism. Lab L16 is this lesson's practice.

<!-- section:dbxfe-delivery-l01-revisit -->

Work the exercise before reading the solution and check each finding against its rule. A day later, redraw the five states from memory with one piece of evidence each. Revealing the solution records no completion; mark it yourself.
