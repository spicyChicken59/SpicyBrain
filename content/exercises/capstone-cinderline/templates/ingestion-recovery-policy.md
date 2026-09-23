# Ingestion, publication and recovery policy (template)

Fictional exercise. This policy must not contradict the preserved
reliable-data publication policy; it may add stages in front of it. Walk
`quality-events.csv` delivery by delivery and record the state after each.

## Stages

| Stage | Rule you propose | What is retained | Who owns a failure here |
|---|---|---|---|
| 0 Source admission | [only approved channels enter revision comparison; how a delivery is identified] | | |
| 1 Retain raw | [every row, with delivery identity, never deleted] | | |
| 2 Validate / quarantine | [negative or null quantities; defective above inspected; missing key; unusable version] | | |
| 3 Resolve identity and revision | [same event id + equal payload = one delivery; higher revision supersedes; equal revision + different quantities = conflict; arrival order is not authority] | | |
| 4 Publication gate | [all conflict counts zero and no blocked key; read the gate's own decision, not an empty list] | | |
| 5 Publish snapshot | [snapshot id, evidence-as-of, per-plant freshness, stale label with reason] | | |
| 6 External effects | [once per snapshot identity; pending effect recorded separately from publication] | | |

## State walk

| Delivery | Rows | Accepted state after | Quarantine | Publication | Effect count | Your note |
|---|---|---|---|---|---|---|
| D1 + D2 | | | | | | |
| D3 | | | | | | |
| D4 | | | | | | |
| D5 | | | | | | |
| X1 on the verified 20/1 baseline (fresh simulation) | | | | | | |
| D6, D8 (East and 3 March) | | | | | | |

## Failure boundaries and recovery

| Failure after | Visible state | Recovery action | Who | Proof it worked |
|---|---|---|---|---|
| raw retention | previous snapshot explicitly stale | recompute from retained rows; publish once | | |
| resolution | | | | |
| publication, before the effect | correct report, pending effect | record the effect once against the snapshot id | | |
| an operator's manual rerun | | | | |

## What this policy refuses to do

- Adjudicate a conflict automatically: [where it is resolved instead]
- Treat absence from a later delivery as a deletion
- Delete raw rows to "fix" a number
- Publish partial coverage as a complete report

## Alert routing within the disclosed capacity

- Who reads an alert at 06:30, and what they can do without the DBA:
- What waits for a Tuesday or Thursday window:
- What the board says meanwhile:
