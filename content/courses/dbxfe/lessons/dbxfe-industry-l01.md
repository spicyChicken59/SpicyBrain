<!-- section:dbxfe-industry-l01-outcome -->

After this lesson you can take a manufacturing use case from its operational source to the person who acts on it, and write the brief that decides whether it should go ahead. You fix grain, metric contracts, event identity, units, timestamps and asset hierarchies first; apply them to quality, traceability, engineering data, maintenance, demand, scheduling and documents; then transfer the patterns to retail, financial services and healthcare. Cinderline and every number here are fictional, and nothing is executed.

<!-- section:dbxfe-industry-l01-start -->

Bring the retained [Architecture and migration](#/module/dbxfe-m08) module: its target designs are where these patterns land. You should read SQL joins and aggregates comfortably and know that Unity Catalog governs tables with owners and grants. Other modules go deeper on single parts: [data modeling](#/module/dbxfe-modeling) for grain, [forecasting](#/module/dbxfe-forecasting) for demand and [retrieval](#/module/dbxfe-retrieval) for documents. This lesson is about choosing and framing the use case.

<!-- section:dbxfe-industry-l01-chain -->

Operational source → governed data → analytical or model decision → responsible human action. At Cinderline the MES records scrap, consumption and inspections, the historian records sensor readings, and the ERP holds orders and bills of materials. Governed tables declare grain, units, time basis and owner. A decision is a rule or model output with a fixed set of actions: hold, release, inspect, reorder. The chain ends with a named person who acts and records the outcome, the only data that can later show whether the use case worked. A dashboard nobody owns is a chain missing its last link.

<!-- section:dbxfe-industry-l01-contract -->

Name the grain before the metric. Three lots scrap 10 of 1,000, 20 of 200 and 8 of 800: the mean of lot rates is 4.0%, the pooled rate 38 ÷ 2,000 = 1.9%. A metric contract fixes one answer:

| Field | Scrap rate |
|---|---|
| Grain | lot × operation |
| Numerator | units with final disposition scrap |
| Denominator | units started at the operation |
| Aggregation | sum ÷ sum |
| Time basis | operation completion, site local day |
| Exclusions | engineering trial lots, reported separately |
| Owner | quality engineering lead |

<!-- section:dbxfe-industry-l01-identity -->

An event's identity is the fields naming one real occurrence: here source system, inspection id and revision. A resend repeats the identity and collapses; a correction raises the revision and keeps the old row as history; a re-inspection after rework is a new inspection. Units and time zones are data too:

| Pitfall | Symptom | Guard |
|---|---|---|
| Mixed units | 85, 85 and 185 (°F) average to 118.3 | unit column; convert once: 185 °F = 85.0 °C |
| Implied unit | bar and psi gauges share a tag | unit in the source contract |
| Local time, no zone | 01:30 twice at the autumn clock change | UTC instant plus site time zone |
| Clock drift | PLC stamps events minutes early | keep device and receive times |
| Event vs ingestion time | late batch lands tomorrow | window on event time; count late rows |
| Session time zone | one value, different displayed hours | TIMESTAMP for instants, TIMESTAMP_NTZ for wall clock |

<!-- section:dbxfe-industry-l01-hierarchy -->

| Level | Cinderline example | Key | Grain it carries |
|---|---|---|---|
| Site | Harwick plant | site_id | shifts, time zone |
| Line | Line 3 die casting | line_id | throughput per shift |
| Machine | Cell DC-07 | asset_id | cycles, downtime |
| Sensor | S-118 hydraulic pressure | sensor_id + mount period | readings |

This tree simplifies ISA-95's equipment hierarchy (enterprise, site, area, work center, work unit). Give every parent link valid-from and valid-to dates: S-118 moved from DC-07 to DC-09 on 15 June, so a reading from 10 June still rolls up to DC-07.

<!-- section:dbxfe-industry-l01-quality -->

Of 500 castings, 440 pass first inspection, 45 pass after rework and 15 are scrapped: final yield 97.0%, first-pass yield 88.0%, rework load 9.0%. If only 100 castings are X-rayed and 6 show porosity, the estimate is about 6% of castings, not 6 ÷ 500. Compare like operations with like, keep corrections as revisions, and never let a pipeline silently drop records with a missing lot id: quarantine and count them, because a dropped row changes the denominator.

<!-- section:dbxfe-industry-l01-trace -->

Traceability walks consumption edges. Forward from suspect ingot lot AL-5521: casting lots C-3301 and C-3302, assembly lots A-801 and A-802, shipment SH-77. Backward from a complaint on A-802: C-3302 and C-3303, hence both ingot lots, because A-802 mixed its inputs. Engineering data says what *should* be built: a bill of materials by revision with effectivity (PH-200 takes seal S-10 up to serial 1060, S-12 from 1061). Genealogy says what *was* built; serial 1063 consumed S-10, a deviation reported to engineering, never edited away. Unity Catalog lineage traces data, not material.

<!-- section:dbxfe-industry-l01-maintenance -->

Labels come from maintenance records: a failure-coded work order within a horizon after the prediction time. The horizon must exceed the actionable lead time (bearings take 7 days), and features may use only data available at the prediction time; teardown notes and post-failure readings leak the outcome. Split by time, evaluate at the planner's capacity, and compare with the current fixed-interval plan. An alert informs an inspection plan; it never changes the site's safety procedures.

<!-- section:dbxfe-industry-l01-planning -->

History records shipments, not demand: a week with a stock-out is censored, a lower bound. Flag it before training or judging a forecast, and measure accuracy at the planner's grain, part × distribution centre × week. Scheduling then turns demand into line time under capacity, changeover, material and maintenance constraints, and must be feasible first: when order O-3's alloy arrives a day after its due-date slot, O-3 is one day late in every feasible plan, and the planner decides whether to expedite or tell the customer.

<!-- section:dbxfe-industry-l01-documents -->

Work instructions, maintenance manuals and 8D reports are controlled documents. Every indexed chunk carries document id, revision, status, effective date, site and access group; retrieval filters to the revision in force before ranking; the answer cites it; the technician checks the controlled copy before acting. When no current revision matches, the assistant says so instead of quoting an older one.

<!-- section:dbxfe-industry-l01-transfer -->

| Question | Manufacturing | Retail | Financial services | Healthcare |
|---|---|---|---|---|
| Event identity | source, inspection id, revision | store, transaction, line; returns link to the sale | transaction id; a reversal is a new event | supply scan with item lot and location |
| Grain | lot × operation | store × SKU × day | account × day | supply item × location × day |
| Hierarchy | site → line → machine → sensor | chain → region → store → shelf | entity → business line → branch → account | organization → facility → department |
| Clock pitfall | PLC drift, clock change | trading day past midnight | posting vs value date | shifts across facilities |
| Person who acts | quality engineer, planner | replenishment planner | analyst reviewing an alert | operations or supply manager |

The pattern transfers; the stakes do not. Regulated, clinical and safety judgements belong to qualified owners, whom a brief names. This course gives no compliance, clinical or safety advice.

<!-- section:dbxfe-industry-l01-evaluate -->

| Use case | Decision owner | Data evidence | Outcome evidence | Verdict |
|---|---|---|---|---|
| Supplier-lot trace | quality engineer | 97.9% of consumption events carry a lot id | two past holds replayed | pilot |
| Scrap Pareto | shift lead | complete inspection records | descriptive | proceed |
| Spare-parts demand | parts planner | stock-outs not recorded | backtest biased low | fix data, then pilot |
| Spindle failure prediction | maintenance planner | sensors moved without dates | 6 labelled failures | not enough evidence yet |

"Not enough evidence yet" is a result when it names the missing evidence, how it will be collected and when the verdict is reviewed.

<!-- section:dbxfe-industry-l01-example -->

**Decision.** The quality engineer narrows a hold from a week's output to the lots a suspect input reached.

**Metric contract.** Hold scope: produced lots and shipments reached by a forward trace; grain lot × operation; time basis consumption time (UTC); owner quality engineering.

**Architecture.** MES consumption events → genealogy edges keyed on source and event id → trace query → hold list → engineer's decision and outcome recorded.

**Risks.** 2.1% of consumption events lack a lot id; mixed hoppers widen scope; casting-cell clock drift.

**Evaluation.** Replay two past holds; the trace must contain every lot the manual hold found.

**Conclusion.** Pilot on Line 3, with missing lot ids reported beside every trace.

<!-- section:dbxfe-industry-l01-exercise -->

Write a one-page brief for Cinderline's proposed spindle bearing early warning on its CNC line. Facts: 14 spindles; vibration sensors since January 2025; six failures in two years; failure codes on work orders only since 2025; two sensors moved between spindles without dates; replacement bearings take 7 days. Include the metric contract, the chain, risks, evaluation criteria and an honest conclusion.

<!-- section:dbxfe-industry-l01-solution -->

The decision is the maintenance planner scheduling an inspection. Contract: unplanned spindle stops per 1,000 running hours, spindle × week grain, owner maintenance lead. Label: a BRG-coded work order within 14 days of the weekly prediction time, because 7 days' lead time must fit inside it. Chain: historian → effective-dated sensor mounts → weekly score → planner → inspection finding recorded. Risks: six labels, uncoded history, undated mounts, leakage from later work orders. Evaluation: failures caught with 7 days' notice at 3 alerts a week against the fixed-interval plan. Conclusion: **not enough evidence yet**; code failures, date the mounts, review in six months.

<!-- section:dbxfe-industry-l01-mistakes -->

- Averaging lot rates and calling it the plant rate.
- Deduplicating on an id without its source system.
- Keying on local time; averaging values in mixed units.
- Joining history to today's hierarchy.
- Counting rework passes as first-pass passes.
- Tracing material with data lineage.
- Training a forecast on stock-out weeks; scheduling without material.
- Citing a superseded revision; copying tables into another industry.
- Writing "not enough evidence" without saying what would change it.

<!-- section:dbxfe-industry-l01-sources -->

Databricks' [Manufacturing Solutions](https://www.databricks.com/solutions/industries/manufacturing-industry-solutions) and retail, financial services and healthcare pages are vendor framing. [Lineage in Unity Catalog](https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-lineage), [TIMESTAMP_NTZ type](https://docs.databricks.com/aws/en/sql/language-manual/data-types/timestamp-ntz-type) and the [well-architected framework](https://docs.databricks.com/aws/en/lakehouse-architecture/well-architected) are documentation; the [ISA-95 page](https://www.isa.org/standards-and-publications/isa-standards/isa-95-standard) introduces a purchased standard. Titles were confirmed by search on 2026-09-23; page bodies were not fetched.

<!-- section:dbxfe-industry-l01-related -->

Practise the whole method in the [Cinderline capstone](#/practice/dbxfe-capstone). Models and evaluation are in [machine learning](#/module/dbxfe-m07); owners and grants in [governance](#/module/dbxfe-m06); target designs in [architecture and migration](#/module/dbxfe-m08).

<!-- section:dbxfe-industry-l01-revisit -->

Can you state the grain and denominator of a metric you use, the identity of its events, the clock and units they carry, the person who acts on it, and the evidence that would change your verdict?
