# Capstone data pack: Northbrook Holdings, enterprise coexistence and modernization

This pack supports the SpicyBrain capstone `dbxfe-capstone-coexistence`
(open it at `#/practice/dbxfe-capstone-coexistence`). It is a reading and
reasoning exercise: nothing in it executes, connects to a cloud, or needs a
workspace, and no file here is a real organization's data.

## Provenance

Every company, person, system, plant, contract, date, identifier, quantity and
monetary figure in this pack is fictional or hypothetical and was authored for
SpicyBrain. Northbrook Holdings, Vale Components, Tessaly Rail Systems, the
Nordland jurisdiction and its regulator, the Granite appliance, the Conduit job
suite, the Beacon BI service and Line Pulse do not exist. Cloud names (AWS,
Azure, Google Cloud) are used so that the three-cloud questions matrix can be
sourced from each cloud's own documentation; no product availability, price,
benchmark, discount or superiority is asserted anywhere in the pack.

## Files

| File | Purpose |
|---|---|
| `inventory.csv` | 26 systems and workloads across the three estates |
| `dependencies.csv` | 24 **documented** dependencies; the pack is intentionally incomplete (see below) |
| `workload-segmentation.md` | The disposition worksheet and the evidence test for each placement |
| `three-cloud-questions.md` | The questions matrix with every cell marked until you source it |
| `reconciliation/source-totals.csv`, `reconciliation/target-totals.csv` | Six-row totals that disagree by a specific, explainable amount |
| `reconciliation/reconciliation.md` | The task, then the worked answer (read after your attempt) |
| `cost-sensitivity.md` | Hypothetical low/base/high worksheet with currency, period, units and exclusions |
| `templates/executive-readout.md` | One-page structure for the steering group |
| `templates/technical-readout.md` | Structure for the technical readout and appendix |
| `templates/decision-record.md` | Structure for the decision record |

## Dictionary

### `inventory.csv`

| Column | Meaning |
|---|---|
| `system_id` | Stable identifier; `NB-` Northbrook, `VC-` Vale, `TR-` Tessaly, `GRP-` group-level |
| `name` | Fictional system or workload name |
| `business_unit` | Owning unit |
| `hosting` | Where it runs today (on-premises site, cloud and account, or external SaaS) |
| `category` | source system, warehouse, pipeline, BI, serving store, storage, ML job, integration, identity, master data, reporting |
| `workload_type` | transactional, batch, event stream, interactive, near-real-time, time series, weekly batch, etc. |
| `data_classification` | internal, confidential, confidential-financial, restricted-personal, restricted-residency |
| `residency_constraint` | Free text; `none` when no rule is known. Fictional jurisdiction rules only |
| `owner_role` | Role, never a person |
| `users_or_consumers` | Approximate count; **blank means unknown**, not zero |
| `refresh_or_latency_need` | Stated need; quoted text is the customer's own wording, not a requirement |
| `approx_size_gb` | Approximate; blank means unknown |
| `criticality` | high / medium as stated by the owner |
| `documented_dependency_count` | Number of rows in `dependencies.csv` naming this system as `from` or `to`; a flow that merely passes *via* a system is not counted for it |
| `notes` | Facts and known gaps |

### `dependencies.csv`

| Column | Meaning |
|---|---|
| `dependency_id` | Stable identifier |
| `from_system`, `to_system` | Direction of the data or authentication flow; an external party outside the inventory is named by description (for example `external suppliers (3)`) |
| `description` | What flows |
| `interface` | Mechanism (file drop, SFTP, ODBC, connector, governed sharing, platform) |
| `frequency` | Schedule or cadence |
| `documented_in` | Where the dependency is recorded today; use `disclosure` for ones you add |
| `owner_confirmed` | `yes` / `no`: whether an owner has confirmed the dependency still exists |
| `note` | Known gaps |

### `reconciliation/*.csv`

| Column | Meaning |
|---|---|
| `plant_code` | `NB-ASH` Ashcombe, `NB-COR` Corvane, `VC-FEN` Fennick |
| `period` | Calendar month, `YYYY-MM` |
| `metric` | `shipped_quantity` or `shipped_value` |
| `value` | The number as the system reports it |
| `unit` | **Read it.** `unit`, `case` or `USD` |
| `as_of_utc` | Extract time; totals with different as-of times are not directly comparable |
| `source_system` / `target_system` | Where the total came from |
| `note` | Revisions, conversions, basis |

## What is intentionally missing

- `dependencies.csv` holds documented dependencies only. The stakeholder
  disclosures in the capstone reveal at least one that is not here; add it
  as a row with `documented_in = disclosure`.
- Blank cells in `inventory.csv` are unknowns to record, not values to guess.
- The three-cloud matrix has no sourced cells. Sourcing them from each cloud's
  current primary documentation, or leaving them marked, is your work.
- The cost worksheet has no real prices. It never will; write "check current
  pricing" where a real figure belongs.

## How to use the pack

1. Read the capstone brief, then open the stakeholder disclosures deliberately
   and note what each one changes in the inventory, the dependencies and the
   calendar.
2. Complete `workload-segmentation.md` row by row.
3. Fill the matrix cells you can source; leave the rest marked and list them
   as open questions with owners.
4. Do the reconciliation before reading its worked answer.
5. Complete the cost worksheet as a range against the ceiling.
6. Write the three templates. Reveal the capstone's model only after your
   submission is complete, and self-assess against the rubric.

## Cleanup

The pack creates nothing: no temporary directories, environments, cloud
resources, credentials or downloads. Delete only your own working copies and
completed templates if you no longer want them. Keep the pack itself for
re-reading.

## Limits

This is educational fiction. It does not describe Databricks, any cloud
provider or any customer, and it proves nothing about performance, cost or
suitability. A completed submission is self-assessed reflection, not a
credential, a readiness score or an independent review.
