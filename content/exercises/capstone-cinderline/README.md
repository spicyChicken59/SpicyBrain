# Cinderline capstone data pack

Companion evidence for the SpicyBrain capstone *Cinderline: from first
conversation to a defensible decision* (`#/practice/dbxfe-capstone`). The
capstone's identity is unchanged; this pack was added with its 2026-09-23
revision. Everything in it is original fiction: the company, plants, people,
systems, file names, dates, quantities and money are invented for teaching.
Nothing is executed; the pack is text and tables you read, reason over and
write against. No Databricks workspace, cloud account or paid service is
needed, and no file here provisions one.

## Contents

| File | What it is | Use it for |
|---|---|---|
| `source-inventory.csv` | Nine fictional sources: systems of record, derived copies, the corrections channel, out-of-scope systems | Discovery synthesis, source semantics, the admission rule |
| `stakeholder-statements.md` | The six original disclosed statements, further remarks, and three new voices (DBA, analyst, plant controller) | Stakeholder map, acceptance roles, capacity limits, baseline figures |
| `flawed-metric.md` | The two defect-rate definitions in use today, worked figures, and why they mislead | The metric contract and the "three numbers for one day" explanation |
| `failure-timeline.md` | The night of 2–3 March: facts, hypotheses and what the contract path would have shown | Stale-versus-current evidence, incident review, operational fit |
| `quality-events.csv` | Twenty delivered rows (16 distinct events) across two plants and two business days, with delivery identity and one what-if row | Walking the publication policy, reconciliation, demo steps |
| `templates/` | Seven Markdown templates for the written deliverables | Structure your submission before revealing the model |

## Data dictionary: `quality-events.csv`

| Column | Meaning |
|---|---|
| `delivery_id` | The delivery a row arrived in (`D1`…`D8`, or `X1` for the what-if branch). The ids are not in time order and `D7` is unused; read `received_at` for order. Delivery identity is what lets a replay be recognized. |
| `received_at` | When the delivery was closed at the landing location (plant-local, fictional). The nightly extract's deliveries (D1, D8) close with the 01:10 load, whatever time their rows were extracted; the failure timeline gives the extraction times. Arrival order is not revision order. |
| `source_id` | The source from `source-inventory.csv`: `S03` is the package's extract step, the delivery channel that carries ERP records from S01 and S02 (nightly or by manual rerun); `S04` is the corrections file. |
| `channel` | `erp_nightly_extract`, `erp_manual_rerun` or `qc_corrections_csv`: the pilot's approved channels. The first two deliver ERP records; the third delivers approved revisions. The plant sheet (S05) and the workbook (S06) are refused at admission. Only admitted rows enter revision comparison, and an admitted row can still be quarantined. |
| `event_id` | Immutable identity of one delivered observation. The same `event_id` with an equal payload is one event delivered again. |
| `inspection_id` | The business key that persists through corrections. |
| `version` | The approved source revision; a higher version supersedes a lower one for the same key. Equal versions with different quantities conflict. |
| `plant`, `line` | Where the inspection happened. |
| `business_day` | The inspection's own day, which the metric is grouped by. It is not the load date. |
| `inspected_units`, `defective_units` | Quantities as delivered, including invalid ones. Negative inspected, or defective above inspected, is quarantined. |
| `branch` | `main` rows form one timeline. The single `what-if-conflict` row is applied to the verified 20/1 baseline in a separate fresh simulation, as the reliable-data bundle's `batches.json` cases are. |
| `note` | Free text for the reader; never an input to any rule. |

The first five `main` rows are, in the same order, the five-row example of the
preserved reliable-data policy: (ev1, A, 1, 10, 1), (ev1, A, 1, 10, 1),
(ev2, B, 1, −3, 1), (ev3, A, 2, 12, 1), (ev4, C, 1, 8, 0). This pack adds
plant, line, business day and delivery columns; it changes no value.

## Data dictionary: `source-inventory.csv`

`source_id` (S01–S09); `system`; `object_or_path`; `record_type`;
`owner_role` (a role, never a person); `refresh_cadence`; `business_key`;
`revision_signal` (what, if anything, orders corrections); `duplicate_behaviour`
(how duplicates arise); `approved_for_pilot` (yes, no, pending, out of scope);
`classification_status`; `known_issues`. "Derived copy" means the object is
downstream of a system of record and must not be treated as a system of
record. S03's reporting table is such a copy and is the read path the pilot
replaces; its extract step is admitted only as the delivery channel for S01
and S02 records, never as a source of revisions of its own. B's negative
quantity arrived through that extract: it is admitted as delivered and then
quarantined by validation.

## Delivery completeness (the rule this pack follows)

A nightly delivery is complete only when the package run that carries it
finishes with a completion marker; until then its rows are retained raw and
nothing from that run is published. A corrections file is a complete delivery
on its own. On 2–3 March the nightly run never completed, so North's rows in
D1 were held even though they were all present; the 11:15 manual rerun (D3)
is what completes the run. A per-plant completion marker would have let North
publish at 06:40; that is a design option to raise with the DBA, not the rule
the pack's walk uses.

## Derived states you should be able to reproduce

Accepted state per plant and business day under the preserved policy. Every
figure below was derived by hand from `quality-events.csv`; the capstone
model's technical appendix carries the same walk.

| Plant / day | After deliveries | Accepted inspections | Quarantined | Totals | Rate | Publication |
|---|---|---|---|---|---|---|
| North / 2 Mar | D1, D2 | A v2 12/1, C v1 8/0 | B (negative inspected) | 20 / 1 | 5.0% | prepared, not published: D1's run did not complete; the last verified snapshot is shown, stale, reason "incomplete delivery" |
| North / 2 Mar | + D3 (completes the run; ev-late, A v1 again) | unchanged | B | 20 / 1 | 5.0% | published, snapshot 1, `evidence_as_of` 11:15; the older revision cannot replace v2 |
| North / 2 Mar | + D4 (A v3 14/1) | A v3 14/1, C v1 8/0 | B | 22 / 1 | 4.5% | published once, snapshot 2, one effect |
| North / 2 Mar | + D5 (exact re-send of D4) | unchanged | B | 22 / 1 | 4.5% | unchanged; raw count grows; no second effect |
| North / 2 Mar, what-if | verified 20/1 baseline + X1 (ev-other, A v2 13/1) | A unresolved; only C 8/0 prepared, which is not a report | B | — | — | blocked; last verified 20/1 snapshot stays published and explicitly stale |
| East / 2 Mar | D3, D6 | E v1 20/2, F v1 15/0, G v1 9/3 | none | 44 / 5 | 11.4% | published at 11:15 (D3 completes the run); G's second delivery changes nothing |
| East / 2 Mar | + D4, D5 (F v2 15/1) | E v1 20/2, F v2 15/1, G v1 9/3 | none | 44 / 6 | 13.6% | restated once |
| North / 3 Mar | D8 | J 11/0, K 9/1, L 10/0 | none | 30 / 1 | 3.3% | published |
| East / 3 Mar | D8 | N 12/1 | M (defective exceeds inspected) | 12 / 1 | 8.3% | published with M disclosed |

Two consequences of the what-if branch are easy to miss. First, a later
approved A v3 does not clear a conflict that remains in retained history; the
conflict has to be resolved upstream, by the approving channel, before
publication resumes. Second, an empty list of unresolved keys is not by itself
permission to publish: the gate's own decision is what counts.

## Consistency with the preserved policy

This pack does not change the reliable-data publication policy and must not be
read as doing so. In that policy: the five rows give accepted A v2 12/1 and
C v1 8/0, B quarantined, totals 20/1, rate 5%; replay does not change accepted
totals; an older revision cannot replace a newer one; a valid A v3 14/1 gives
22/1 once; conflicting deliveries block publication; and a later conflict
keeps the last verified 20/1 snapshot explicitly stale. The policy is
fictional teaching policy, not a product guarantee. Where this pack adds a
source-admission step (only approved channels enter revision comparison), it
sits in front of that policy and leaves it unchanged, and so does the
delivery-completeness rule above.

## How to use the pack with the capstone

1. Read `stakeholder-statements.md` and `source-inventory.csv`; fill
   `templates/discovery-synthesis.md`.
2. Read `flawed-metric.md`; write `templates/metric-contract.md` and
   reproduce the disputed day's three figures yourself.
3. Walk `quality-events.csv` delivery by delivery; fill
   `templates/ingestion-recovery-policy.md` and check your states against the
   table above.
4. Read `failure-timeline.md`; write the stale-versus-current section and the
   operational-fit parts of `templates/migration-reconciliation-plan.md`.
5. Complete `templates/pov-charter.md`, `templates/value-model.md` and
   `templates/handoff.md`.
6. Only then open the model on the practice page and self-assess against the
   rubric.

## Fictional provenance

Authored for SpicyBrain on 2026-09-23. Cinderline Components, its plants,
people and systems do not exist. Quantities were chosen so that the worked
arithmetic is small enough to check by hand; money figures are the
hypothetical planning inputs from the capstone's own disclosures. No real
customer, organization, product telemetry or proprietary training material
was used. The synthetic data and text may be reused under this repository's
licence.

## Cleanup and limits

The pack installs nothing and writes nothing. If you copied it elsewhere,
delete that copy; keep your own written answers. The pack is not executable,
is not a lab, proves nothing about any cloud platform's behaviour, and does
not judge anyone. A submission that reproduces every table here has
practised the reasoning; it has not run a pipeline.
