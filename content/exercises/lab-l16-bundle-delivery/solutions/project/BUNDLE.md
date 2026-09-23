# Bundle configuration: Cinderline scrap summary (reviewed)

In the real repository these two files sit at the project root, beside
`pyproject.toml`: `databricks.yml` and `resources/scrap_job.yml`. The lab
download may only carry `.md .txt .json .csv .py .sql .toml` files, so each YAML
file travels here as a fenced block whose first line names its path.
`python bundlecheck.py solutions/project/BUNDLE.md --materialize <dir>` writes
the project back out with real `.yml` files if you want to try it in your own
workspace later.

This is a Declarative Automation Bundle, the configuration format formerly
named Databricks Asset Bundles; the file name `databricks.yml` and the
`databricks bundle ...` commands kept their spelling.

**Status in this lab.** Parsed with PyYAML and checked by the lab's local
structure rules: executed. `databricks bundle validate`, `plan`, `deploy` and
`run`: NOT RUN. No workspace was contacted. The hosts use the reserved
`.example` domain and the service principal IDs are placeholders; replace
them with values from your platform team.

```yaml
# file: databricks.yml
bundle:
  name: cinderline_scrap

include:
  - resources/*.yml

artifacts:
  scrap_wheel:
    type: whl
    path: .
    build: python -m build --wheel

variables:
  catalog:
    description: Unity Catalog catalog that holds this target's exports volume.
  schema:
    description: Schema inside that catalog.
  alert_threshold:
    description: Business rule. Scrap rate above which a line is flagged; the same in every target.
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
    presets:
      trigger_pause_status: PAUSED
    variables:
      catalog: cinderline_test
      schema: quality
    permissions:
      - service_principal_name: "00000000-0000-0000-0000-00000000a001"
        level: CAN_MANAGE
      - group_name: cinderline-data-eng
        level: CAN_VIEW

  prod:
    mode: production
    workspace:
      host: https://cinderline-prod.example
      root_path: /Workspace/Users/00000000-0000-0000-0000-00000000b001/.bundle/${bundle.name}/${bundle.target}
    git:
      branch: main
    run_as:
      service_principal_name: "00000000-0000-0000-0000-00000000b001"
    variables:
      catalog: cinderline_prod
      schema: quality
    permissions:
      - service_principal_name: "00000000-0000-0000-0000-00000000b001"
        level: CAN_MANAGE
      - group_name: cinderline-data-eng
        level: CAN_VIEW
      - group_name: cinderline-quality-leads
        level: CAN_RUN
```

```yaml
# file: resources/scrap_job.yml
resources:
  jobs:
    scrap_summary:
      name: cinderline-scrap-summary
      schedule:
        quartz_cron_expression: "0 30 6 * * ?"
        timezone_id: UTC
      tasks:
        - task_key: summarize
          environment_key: default
          python_wheel_task:
            package_name: cinderline_quality
            entry_point: scrap_summary
            parameters:
              - --catalog
              - ${var.catalog}
              - --schema
              - ${var.schema}
              - --alert-threshold
              - ${var.alert_threshold}
      environments:
        - environment_key: default
          spec:
            environment_version: "5"
            dependencies:
              - ../dist/*.whl
```

## What a reviewer checks in this diff

- **Targets.** `dev` is the default and uses `mode: development`, so a
  deployment is a private copy under the developer's home folder, prefixed and
  with its schedule paused. `test` and `prod` use `mode: production` with a
  fixed `workspace.root_path` in the service principal's folder, so there is
  one copy of each, whoever runs the pipeline.
- **Identity.** `test` and `prod` run as their own service principal
  (`run_as`), and the permissions name that principal with `CAN_MANAGE`.
  No token, password or client secret appears anywhere: the pipeline
  authenticates through its environment, never through this file.
- **Parameters.** Only `catalog` and `schema` differ between targets.
  `alert_threshold` is a business rule and keeps its default everywhere, so a
  test run is evidence about production behaviour.
- **Branch.** `prod` names `git.branch: main`; the CLI refuses to plan or
  deploy that target from another branch unless `--force` is given.
- **Schedule.** Development mode pauses it; `test` pauses it with a preset
  (the pipeline starts test runs itself); only `prod` runs on the 06:30 UTC
  schedule.
