# Lab L16 solutions

The complete reference is `solutions/project/`. This file explains it and shows
the intermediate outputs a correct run produces. Everything below was produced
by local Python; no Databricks step ran.

## Task 1 — the rules

```python
def scrap_rate(scrapped: int, inspected: int) -> Decimal | None:
    if inspected == 0:
        return None
    return (Decimal(scrapped) / Decimal(inspected)).quantize(
        RATE_PLACES, rounding=ROUND_HALF_UP
    )
```

and in `validate_record`, after the count checks:

```python
    if not problems and record["scrapped"] > record["inspected"]:
        problems.append("scrapped exceeds inspected")
```

and the alert is `rate is not None and rate > alert_threshold`.

**Why Decimal and quantize.** `round(1 / 32, 4)` is `0.0312`: 0.03125 is exact
in binary and Python's `round` sends ties to the even digit. The plant's rule
is half up, so the rate is `0.0313`. `quantize` also fixes the printed form, so
26 of 1000 is `"0.0260"` and not `"0.026"`, which matters because the summary
file is compared as text downstream.

**Why None for an idle line.** L4 inspected nothing. A rate of zero would claim
a perfect line; `None` says there is no rate, and the alert stays false.

Intermediate output for `fixtures/inspections.json` (threshold 0.0400):

| line | inspected | scrapped | scrap_rate | alert |
|---|---:|---:|---|---|
| L1 | 1000 | 26 | 0.0260 | false |
| L2 | 600 | 27 | 0.0450 | true |
| L3 | 250 | 10 | 0.0400 | false (equal is not above) |
| L4 | 0 | 0 | none | false |
| L5 | 7 | 1 | 0.1429 | true |

Rejected: record 5 (L2, 45 scrapped of 40), record 7 (L1, inspected −5),
record 8 (L3, no `inspected`).

## Task 2 — the configuration

The reviewed blocks are in `solutions/project/BUNDLE.md`. The eight findings
on the starter and the fix for each:

| rule | where | fix |
|---|---|---|
| H1 | `targets.test` | add the `test` target |
| D4 | `targets.prod.workspace.root_path` | set a fixed root path in the prod service principal's folder |
| D9 + H5 | `targets.prod.workspace.token` | delete the key; the pipeline authenticates through its environment |
| H2 | `targets.prod.git.branch` | `git: {branch: main}` |
| H3 | `targets.prod.run_as` | `run_as: {service_principal_name: ...}` |
| H6 | `targets.prod.variables.alert_threshold` | delete the override; the default applies everywhere |
| D7 | task parameter `${var.catalogue}` | `${var.catalog}` |

Two things the rules do not force but the reviewed version does: `test`
pauses the schedule with `presets.trigger_pause_status: PAUSED`, because the
pipeline starts test runs itself, and each service target's permissions give
its own service principal `CAN_MANAGE`, which the CLI recommends for the
deploying identity.

## Task 3 — resolved targets

`python bundlecheck.py solutions/project/BUNDLE.md --resolve` (abridged):

| target | --catalog | --schema | root path | needs the workspace |
|---|---|---|---|---|
| dev | cinderline_dev | quality_${workspace.current_user.short_name} | ~/.bundle/cinderline_scrap/dev | schema, root path |
| test | cinderline_test | quality | /Workspace/Users/…a001/.bundle/cinderline_scrap/test | nothing |
| prod | cinderline_prod | quality | /Workspace/Users/…b001/.bundle/cinderline_scrap/prod | nothing |

`--alert-threshold` is `0.0400` in all three. Development mode is designed to
give every developer a private copy; the copy is named after the person who
deploys, and only the workspace knows who that is. The runner shows the same
boundary from the other side: parsing `dev`'s arguments locally fails with
`--schema 'quality_${workspace.current_user.short_name}' is not a plain
lowercase identifier`.

## Task 4 — failure cases

Each mutation produces exactly the findings in `expected/bundle_findings.json`;
M07 produces two (an unknown workspace field and a credential value). M16
changes `resources/*.yml` to `resource/*.yml`. The CLI v1.17.0 source reports
an error only when an include without wildcards matches nothing; a wildcard
that matches nothing is accepted silently. The bundle would deploy with no job
at all. House rule H10 exists for exactly that reason.

## Task 5 — classification

| step | evidence it produces | who can produce it | this lab |
|---|---|---|---|
| local syntax, structure, resolve | parse result, findings list, resolved table | anyone, offline | EXECUTED |
| unit tests, entry point | test counts, a summary file | anyone, offline | EXECUTED |
| authentication | a token for an identity | a person (U2M) or the pipeline's service principal (M2M or federation) | NOT RUN |
| bundle validate | "Validation OK!" with the workspace user shown | an authenticated identity | NOT RUN |
| bundle plan / deploy | the plan; deployed resources and state | the service principal of that target | NOT RUN |
| bundle run | a run ID, a result state | the same | NOT RUN |
| integration, promotion | output checked in test; approval; prod deployment | pipeline plus reviewer | NOT RUN |

## One wrong approach, and why it fails

"Validate by parsing": a pipeline step that runs `yaml.safe_load` on
`databricks.yml` and reports success. It passes the starter, token and all:
the starter is valid YAML. It also passes M16, M13 and M10. And PyYAML's plain
`safe_load` keeps the second of two duplicate keys silently, so
`fixtures/broken_blocks.md`'s repeated `dev:` loads as a production target
without any message; this lab's loader refuses it with
`found duplicate key 'dev'` on line 7. Parsing proves the text is YAML. It says
nothing about the rules, the workspace, the identity or the job.
