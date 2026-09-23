# Workload segmentation worksheet

Place every row of `inventory.csv` in exactly one **disposition**, name the
**driver** that decides it, and write the **evidence** that placement needs
before it can be treated as agreed. All systems are fictional.

## Dispositions

| Disposition | Meaning | It is only defensible when… |
|---|---|---|
| stay | The workload remains where it runs, and nothing about it changes this quarter | no consumer needs it elsewhere, or a contract, residency rule or blackout forbids change now |
| coexist — share | The data stays owned where it is and is made available to another estate through recipient-scoped, revocable, audited sharing | the owner keeps ownership; freshness, cost, revocation and failure behaviour are stated |
| coexist — federate | The data stays where it is and is queried in place from another estate | a supported federation path exists (verify; unknown until sourced), and freshness and cost are acceptable |
| migrate — wave 1 | Moves inside this quarter, before the blackout | it retires a named risk, has an owner, a reconciliation gate, a rehearsal and a rollback |
| migrate — wave 2 | Moves next quarter | its blocker is dated (the close, the notice decision, a review) |
| retire | Switched off, not moved | evidence shows no reader (query logs, not opinion) |
| not yet | Deliberately deferred with a reconsideration condition | the condition is specific, dated and owned |

## Drivers

`latency` · `residency` · `contract` (renewal, notice, committed spend) ·
`blackout` · `dependency` (documented or disclosed) · `bi-continuity` ·
`cost` · `no-consumer` · `security-review`

## Worksheet

Copy this table into your submission and complete it. The two rows below are
worked examples of the *format*, not answers to be copied. Add the undocumented
dependencies from the disclosures as rows in `dependencies.csv` and mark them
`documented_in = disclosure`.

| system_id | disposition | driver | evidence needed before it is agreed | owner | reversible? |
|---|---|---|---|---|---|
| NB-CRM-01 (example) | stay | no-consumer | Confirm no analytics consumer other than the nightly extract into Granite | Sales operations lead | n/a |
| DEP-24 dimensions (example) | coexist — share | dependency | Name the consumer inside Vale; confirm weekly freshness is enough; define revocation and audit on both sides | Vale data lead + Data platform lead | yes — restore the weekly CSV |
| NB-ERP-01 | | | | | |
| NB-DW-01 | | | | | |
| NB-ETL-01 | | | | | |
| NB-BI-01 | | | | | |
| NB-AZ-SQL | | | | | |
| NB-AZ-LAKE | | | | | |
| NB-FIN-01 | | | | | |
| NB-MES-ASH | | | | | |
| NB-MES-COR | | | | | |
| NB-DASH-01 | | | | | |
| NB-HIST-01 | | | | | |
| NB-HR-01 | | | | | |
| GRP-MDM-01 | | | | | |
| GRP-INT-01 | | | | | |
| VC-ERP-01 | | | | | |
| VC-LH-01 | | | | | |
| VC-PIPE-01 | | | | | |
| VC-ML-01 | | | | | |
| VC-BI-01 | | | | | |
| VC-QA-01 | | | | | |
| VC-IDP-01 | | | | | |
| TR-MAINT-01 | | | | | |
| TR-GCP-01 | | | | | |
| TR-RPT-01 | | | | | |
| TR-FIN-01 | | | | | |

## Summary you must be able to give

- How many rows in each disposition, and which driver decided the most rows.
- Which wave-1 items retire a risk that exists today (name the risk).
- Which rows are "not yet", each with its reconsideration condition and date.
- Which rows depend on an *unknown* cell of the three-cloud matrix, and so
  cannot be final until it is sourced.

A segmentation that puts every row in "migrate" or every row in "stay" is
not wrong by definition, but it must survive the same evidence test row by
row.
