# Metric contract (template)

Fictional exercise. One contract per metric. Every field must be testable
against `quality-events.csv`; if you cannot write the test, the field is not
finished.

## Identity

- Metric name: [e.g. plant/day unit defect rate]
- Owner (role): [who accepts a change to this contract]
- Consumers: [board, meeting, workbook to be retired]
- Contract version and date: [ ]

## Definition

| Field | Your contract | Test against the pack |
|---|---|---|
| Grain | [one accepted inspection at its highest valid approved revision] | North 2 Mar resolves A to v2, then v3 |
| Measure | [total defective units / total inspected units] | 1/20 = 5.0%; never a mean of per-row rates |
| Denominator | [accepted inspections only] | B excluded; its count disclosed |
| Exclusions and disclosure | [what is quarantined, and how the count is shown beside the figure] | M on East 3 Mar |
| Time boundary | [business day of the inspection; plant-local; midnight or shift] | correction for the 2nd counts against the 2nd |
| Restatement | [an approved higher revision restates its business day; how readers learn of it] | A v3 moves 5.0% to 4.5% once |
| Freshness | [per plant: newest delivery included; pending deliveries] | East "no delivery for 2 March" at 07:30 |
| Staleness | [when publication is blocked, the last verified snapshot stays visible and is labelled stale with a reason] | what-if branch: 20/1 stale |
| Identity of what a reader saw | [snapshot id, evidence-as-of time] | two readers can name the version they used |

## The disputed day, reconciled

| Definition | Rows used | Figure | Why it differs |
|---|---|---|---|
| Workbook (mean of rates) | | | |
| Plant sheet (sums over pasted rows) | | | |
| This contract | | | |

## Tests the contract must pass

- [ ] Exact re-delivery changes no accepted total.
- [ ] An older revision cannot replace a newer one.
- [ ] A valid later revision restates once, however many times its file is sent.
- [ ] Equal revision, different quantities: publication blocked; last verified snapshot visible and stale.
- [ ] Invalid quantities are quarantined and disclosed, never silently dropped.
- [ ] Load date never replaces business day.

## Open questions for the quality lead

1.
2.
