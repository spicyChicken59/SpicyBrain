<!-- section:action -->

An inventory is worth making only if it answers one question at the end: which slice can we move first without surprising anyone. Build it with that question in view.

1. **Set the boundary.** Name the systems, schemas, jobs, packages and reports inside scope, and the ones explicitly outside it.
2. **Card each workload.** Inputs, outputs, schedule, owner, consumers, expected availability, volume, last change date. An owner is a person who can answer questions this quarter; "the DBA team" is not an owner.
3. **Map dependencies** in both directions: upstream sources, downstream consumers, tables shared between workloads, temporary or global objects, linked servers, files dropped by other processes.
4. **Flag compatibility features:** dialect-specific constructs, stored-procedure control flow, cursors, temporary tables, collation-sensitive comparisons, local-time datetimes, incremental state kept in tables, transactional assumptions, scheduling dependencies.
5. **Classify risk** on three axes recorded separately: business criticality, technical difficulty, and unknowns. Do not multiply them into a score; a high-unknown item is a research task, not a hard item.
6. **Select the pilot** against stated criteria: bounded, representative of at least one hard feature, has a reconciliation basis, has an available owner, is a read path you can reverse.
7. **List the unknowns** with the person who can resolve each.

Evidence to collect: the inventory table, the dependency map, the compatibility flags per workload, the risk classification, the pilot criteria with the chosen and rejected candidates, and the unknowns list.

Deeper: [SQL Server and on-premises modernization](#/module/dbxfe-sqlserver) for stored-procedure decomposition and source semantics, [Warehouse and distributed-platform migrations](#/module/dbxfe-warehouse-migration) for waves and workload segmentation, and the retained lessons [Turn current state into a target design](#/lesson/dbxfe-m08-l01) and [Migrate with reconciliation and rollback](#/lesson/dbxfe-m08-l03).

<!-- section:example -->

**Fictional worked example: Cinderline's ERP reporting layer.** The SQL Server ERP feeds a nightly reporting layer of fourteen stored procedures, three package-style import jobs and twenty-two reports. The question is which slice to pilot on the platform first. The sensor historian itself is out of scope; sensor data reaches this layer only through the `sensor staging` table read by two of the procedures carded below, which stay in the inventory because one of them also reads `rpt_quality_daily` and the two share a global temp table.

### Inventory excerpt

| Workload | Inputs | Outputs | Schedule | Consumers | Owner | Volume | Last change | Compatibility flags | Criticality / difficulty / unknowns |
|---|---|---|---|---|---|---|---|---|---|
| `sp_daily_inspections` | ERP inspections; corrected CSV staging | `rpt_quality_daily` | Nightly 22:40, after the ERP extract | Plant sheet, analyst workbook, morning report | Dev (DBA), available | ~400 rows per plant per day | 2025-11 | MERGE; local temp table; `GETDATE()` local time; collation-sensitive join on inspector code; 06:00 business-day cutoff hard-coded | High / medium / medium |
| `pkg_csv_import` | Weekly approved CSV files | CSV staging | On file arrival, Fridays and ad hoc | `sp_daily_inspections` | Quality analyst | One file, tens of rows | 2024-08 | File-arrival trigger; row-count check only; no revision check | High / low / medium |
| `sp_sensor_rollup` | Sensor staging | `rpt_line_health` | Hourly | One dashboard, owner unclear | Unknown | ~50,000 rows per day | 2023-02 | Cursor loop; global temp table shared with `sp_line_summary` | Low / medium / high |
| `sp_line_summary` | `rpt_quality_daily`, sensor staging | `rpt_line_summary` | Nightly 23:30 | Operations weekly review | Operations analyst | Three rows per line per day | 2025-06 | Reads the global temp table above | Medium / low / medium |
| `rpt_morning_defect` | `rpt_quality_daily` | Morning report | Refresh 01:10 | Operations director | Operations analyst | One page | 2025-11 | Depends on the cutoff above; no independent logic | High / low / low |

Eleven further procedures, two further import jobs and twenty-one further reports are carded in the full table; four of those reports have no identified consumer and are candidates for retirement rather than migration.

### Dependency findings

Two procedures share a global temporary table, so neither can move alone without a replacement for that handoff. The business-day cutoff is applied in three places with the same literal, which means the reconciliation basis for any pilot must state the cutoff explicitly. Datetimes are local server time without an offset; the plant sheet assumes plant local time, and the two plants in a second time zone have been silently reading a shifted day. That is a finding for the quality lead before it is a migration item.

### Pilot selection

Criteria: bounded to one plant; exercises MERGE-on-corrections, which is the hard feature the rest of the layer shares; has an existing report to reconcile against; owner available; read path, so the old report keeps running. `sp_daily_inspections` for plant one meets all five; its unknowns are rated medium, not low, because three of the four listed below bear on it, and it starts only when the first two close. `sp_sensor_rollup` was rejected despite looking easy: no owner, unknown consumer, and a shared temp table. `pkg_csv_import` is not a pilot on its own but is a prerequisite because the pilot's inputs come through it; its missing revision check is logged as a dependency risk.

### Unknowns and owners

SQL Server version and edition (DBA); whether change-data capture may be enabled on the inspections table (DBA and security lead); the consumer of `rpt_line_health` (operations director); the intended time zone for the business day (quality lead). None is guessed. The pilot is conditional on the first two and starts once they close; the reconciliation plan carries the fourth as an explicit alignment rule.

### Conclusion

One pilot, one plant, one procedure, with its import job treated as a dependency and a stated cutoff. The inventory also produced a retirement list and a time-zone finding that would have surfaced mid-pilot as a "reconciliation failure" if the inventory had stopped at counting procedures.

<!-- section:template -->

### Boundary

- **In scope:** systems, schemas, jobs, packages, reports. **Out of scope:** named explicitly with the reason.

### Inventory

| Workload | Inputs | Outputs | Schedule | Consumers | Owner (a person) | Volume | Last change | Compatibility flags | Criticality | Difficulty | Unknowns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Object or job name | Tables, files, feeds | Tables, reports, files | Trigger and time | Who reads the output and for what | Someone who answers questions | Rows or bytes per run | Date | Dialect features, temp objects, time handling, state, transactions | High / medium / low | High / medium / low | High / medium / low |

### Dependency map

- **Upstream** sources per workload; **downstream** consumers; **shared objects** between workloads; **external triggers** (files, linked servers, schedules).

### Compatibility flags found

- **For each flag:** where it occurs, what could change meaning on the target, and what test would show it.

### Pilot criteria and candidates

| Criterion | Candidate A | Candidate B | Candidate C |
|---|---|---|---|
| Bounded | | | |
| Representative of a hard feature | | | |
| Reconciliation basis exists | | | |
| Owner available | | | |
| Reversible read path | | | |

- **Chosen pilot and the reasons the others were rejected.**

### Unknowns

| Unknown | Why it matters | Owner | Needed by |
|---|---|---|---|

<!-- section:limits -->

An inventory establishes what exists, who depends on it and which features will need attention; it does not establish that any translation is equivalent, and an automated conversion tool proves nothing about equivalence either. Compatibility flags are the reader's judgement from source code and documentation, not executed behaviour; the reconciliation plan is where behaviour is tested. Risk labels are separate axes deliberately, so a reader can see that a "low criticality" item is high-unknown. Ownership recorded here is proposed until the named person confirms it. Escalate when the inventory reveals a shared object nobody owns, a data-meaning defect such as a time-zone shift that affects current reports, or a source privilege that the migration would need and security has not reviewed.
