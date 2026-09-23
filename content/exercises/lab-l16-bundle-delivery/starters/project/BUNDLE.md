# Bundle configuration: Cinderline scrap summary (STARTER, as opened in the pull request)

This is the configuration as a colleague first proposed it. It parses, and a
quick read suggests it is nearly done; the lab's local rules find eight
problems in it. TASKS.md, task 2, lists what the reviewed version must do;
the gaps are marked `GAP` in comments where a line is missing or wrong.

In the real repository these two files sit at the project root, beside
`pyproject.toml`. The lab download cannot carry `.yml` files, so each travels
here as a fenced block whose first line names its path.

**Status in this lab.** Parsed and structure-checked locally. Never validated
with `databricks bundle validate`, deployed or run.

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

  # GAP: there is no test target.

  prod:
    mode: production
    workspace:
      host: https://cinderline-prod.example
      token: PASTE-A-TOKEN-HERE   # GAP: a credential in configuration
      # GAP: no root_path, so every identity that deploys gets its own copy
    # GAP: no git.branch, so prod can be deployed from any branch
    # GAP: no run_as, so the job runs as whoever deployed it
    variables:
      catalog: cinderline_prod
      schema: quality
      alert_threshold: "0.0500"   # GAP: a business rule that differs from test
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
              - ${var.catalogue}   # GAP: not a declared variable
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
