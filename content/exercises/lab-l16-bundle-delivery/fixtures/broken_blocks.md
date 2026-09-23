# Two deliberately broken blocks (Lab L16 syntax cases)

The first repeats a mapping key, which PyYAML's plain safe loader would accept
silently by keeping the second value. The second indents with a tab character,
which YAML forbids.

```yaml
# file: databricks.yml
bundle:
  name: cinderline_scrap
targets:
  dev:
    mode: development
  dev:
    mode: production
```

```yaml
# file: resources/scrap_job.yml
resources:
  jobs:
    scrap_summary:
      tasks:
        - task_key: summarize
          python_wheel_task:
	    package_name: cinderline_quality
```
