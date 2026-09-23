<!-- section:dbxfe-modeling-l01-outcome -->

After this lesson you can take a stream of accepted inspections and give it a shape that survives questions: a fact whose grain is written down, dimensions that describe it with keys that hold, history attributed as it was or as it is on purpose, and one metric, the unit defect rate, whose contract names its numerator, denominator, unit, period, window and owner. You can reconcile that metric at line-day, plant-day and plant-month and name the test that catches each classic failure: a double count, an empty denominator, mixed units, a dropped key and a window counted in the wrong days. Every record is a synthetic Cinderline Components example, and nothing here needs a workspace.

<!-- section:dbxfe-modeling-l01-start -->

One retained lesson carries a foundation that is not repeated here: [Grain, joins, and execution behavior](#/lesson/dbxfe-grain-joins) shows a join multiplying rows and how to count matching pairs. The metric contract is taught from scratch below, so no metric lesson is needed first; [Build a metric people can trust](#/lesson/dbxfe-m05-l01), which comes later in this track, revisits why "defect rate" needs a named numerator, denominator, time basis and owner, and is an optional short read now. The metric contract field guide gives a one-page template, and the Lab L11 walkthrough runs everything below on local Spark with hand-derived answers. You need SQL joins and GROUP BY; no Databricks workspace is required.

<!-- section:dbxfe-modeling-l01-grain -->

A medallion label says how far data has been refined: bronze keeps what arrived, silver is validated, gold is shaped for business use. It does not say what a row is. A table called `gold_quality` could hold one row per inspection, one per line and day, or both. Name tables by entity and declare the grain in one sentence: `fact_inspection` holds one row per accepted inspection.

The grain decides every other choice. A **fact** table records measured events at that grain, here pieces inspected and pieces defective. **Dimension** tables describe the events with the words people filter by: line, plant, shift and date. A **star** is one fact joined to its dimensions by keys, each join many-to-one. A table that mixes grains, such as inspection rows beside daily subtotal rows, sums silently to the wrong number, because SQL has no notion of grain.

<!-- section:dbxfe-modeling-l01-keys -->

A **conformed** dimension means the same key and the same attribute values in every fact that uses it, so a report can put inspections beside downtime for line N1 on the same business day. Two systems that code the line differently, N1 and NORTH-1, never meet, and the report shows a blank instead of an error.

A **slowly changing** attribute, such as a line's supervisor, needs a decision. Type 1 overwrites and loses history; type 2 adds a row with a new surrogate key and validity dates. Resolve the version valid on each fact's business day once, at load, into `line_sk`, and every later join on `line_sk` is many-to-one. Joining history on `line_id` alone is many-to-many: in the lab, 22 inspections become 29 rows and two supervisors both claim all of line N1.

A fact whose key has no dimension row must not disappear. An inner join drops it; a left join leaves an unnamed NULL group. Map it to an unknown member row (`line_sk = -1`) and list it.

<!-- section:dbxfe-modeling-l01-measures -->

Convert every quantity to one unit before any sum: a packing line that counts cases of 12 must become pieces first. Within one line the ratio hides the mix; at the plant it does not.

Pieces inspected and pieces defective are additive: they sum across lines, days and plants. The rate is not. Store the parts, sum them at each grain and divide once; an average of line rates weights a 100-piece line like a 200-piece line. Keep grains apart as well: a monthly target joined to daily rows repeats on every day.

A denominator of zero means no rate. Spark 4 runs in ANSI mode by default, so `SUM(defective) / SUM(inspected)` fails with `DIVIDE_BY_ZERO`; `try_divide` returns NULL, and the report shows "no units" or "no inspections", never 0%. A real zero, pieces inspected and none defective, is a value.

Periods need the same care. The contract's business day runs 00:00:00 to 23:59:59 plant local time, so a night shift that crosses midnight is split across two days. A window of three business days comes from the plant calendar in the date dimension: on a Monday, three calendar days hold one working day.

<!-- section:dbxfe-modeling-l01-contract -->

A metric contract makes the definition testable: name and grain, numerator and denominator over one population, unit and conversion, business day, month and window, empty-case statuses, unknown member, owner and version. Each clause implies a test.

On Databricks, a Unity Catalog metric view is the mechanism for defining such a measure once. Measures are aggregate expressions without a fixed grain, evaluated with `MEASURE()` at whatever fields a query selects, so a ratio is rebuilt from its parts at every grain. Its joins are many-to-one, and when a join finds several rows the first matching row is selected, so a type 2 dimension must be joined on its surrogate key. Check the current documentation for release status and runtime requirements before relying on it.

A **wide table**, with every attribute copied onto every fact row, is easy to read but freezes the joins it was built with: a supervisor correction or a new attribute means a rebuild, and nothing stops a subtotal row from slipping in. Publish one as a derived, rebuildable view of the star, with its grain stated.

<!-- section:dbxfe-modeling-l01-example -->

Twenty-two synthetic inspections, in pieces after conversion, from the Lab L11 baseline:

| Grain | Row | Inspected | Defective | Rate |
|---|---|---|---|---|
| Line-day | N1, 27 Mar (D. Varga) | 200 | 4 | 2.0% |
| Line-day | N2, 27 Mar | 100 | 5 | 5.0% |
| Plant-day | North, 27 Mar | 300 | 9 | 3.0%, not the 3.5% average |
| Plant-day | South, 27 Mar | 300 | 15 | 5.0%, not 4 / 190 in raw units |
| Line-day | N2, 31 Mar | 0 | 0 | no units, no rate |
| Plant-month | North, March | 1,000 | 22 | 2.2% |
| Plant-month | UNKNOWN, April | 50 | 2 | 4.0% (line N3) |

The parts reconcile: line-days sum to plant-days, plant-days to plant-months, and the months to 2,440 inspected and 65 defective pieces. As of Monday 30 March, three business days (26, 27 and 30 March) give North 800 / 18 = 2.25%; three calendar days give 300 / 6 = 2.0% from a single working day.

<!-- section:dbxfe-modeling-l01-exercise -->

The lab's transfer set changes the case pack to 24 pieces and adds a supervisor change on line S2 dated 30 April, a plant shutdown on Friday 1 May, an unknown line S9 and a tray inspection with no conversion. Without running anything, predict: which supervisor owns S2's inspection on 30 April; what happens to the tray inspection; which three days the business-day window covers as of Monday 4 May; and why a Monday-to-Friday rule would get that window wrong.

<!-- section:dbxfe-modeling-l01-solution -->

With `valid_from` inclusive and `valid_to` exclusive, the new version (E. Haddad) starts on 30 April, so the 30 April inspection belongs to it and the 29 April inspection to J. Castillo. The tray has no conversion: it is quarantined from both numerator and denominator and listed, never summed as pieces. The business-day window as of Monday 4 May is 29 April, 30 April and 4 May, because 1 May is a shutdown and 2 and 3 May are a weekend. A Monday-to-Friday rule would pick 30 April, 1 May and 4 May, counting the shutdown as a working day and dropping 29 April; its North total is 450 pieces instead of 550.

<!-- section:dbxfe-modeling-l01-mistakes -->

- Naming tables after layers or pipeline steps instead of entity and grain.
- Joining a type 2 dimension on its natural key; resolve the version by date or store the surrogate key.
- Letting an inner join decide which facts exist.
- Averaging rates across lines, days or plants instead of summing parts.
- Showing a zero denominator as 0% or letting it fail the report.
- Counting calendar days when the contract says business days.
- Trusting a plausible rate: the history double count moved North's rate from 2.16% to 2.13% while inflating its pieces by 80%.

<!-- section:dbxfe-modeling-l01-sources -->

Dimensional-modeling terms (grain, conformed dimensions, additive facts, type 2 rows, default dimension rows) follow the Kimball Group's published technique pages. Databricks pages describe the medallion architecture, dimensional models in the gold layer, Unity Catalog metric views and their joins, the MEASURE function and informational constraints; Apache Spark 4.0.4 pages describe JOIN, GROUP BY and ANSI mode. Titles and snippets were confirmed by search on 23 September 2026; page bodies were not fetched in this build. All Cinderline records are synthetic, and every number above comes from the local Lab L11 run, not from Databricks.

<!-- section:dbxfe-modeling-l01-related -->

[SQL analytics and performance diagnosis](#/module/dbxfe-m05) asks how fast the metric is computed; this lesson decides what it means. The business intelligence module carries the contract to a dashboard, the advanced analytical SQL module covers windows, time zones and daylight-saving days in depth, and the data contracts lab (L10) validates records before they reach this model.

<!-- section:dbxfe-modeling-l01-revisit -->

Pick one number from a report you trust. Write its grain in one sentence, trace it to the fact rows and dimension keys it came from, and name the contract clause and the test that protect it. If any step needs a guess, the contract has a gap.
