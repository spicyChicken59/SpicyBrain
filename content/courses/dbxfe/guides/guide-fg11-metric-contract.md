<!-- section:action -->

Write the contract before anyone builds the table that computes the metric, and have the metric's business owner sign it. Two reports that disagree almost always compute two different metrics under one name.

1. **State the grain**: one row of the metric describes what, over what period. "Defect rate per line per business day" is a grain; "defect rate" is not.
2. **Define the numerator and the denominator separately**, each with its population, its inclusions and exclusions, and the source field it is counted from. Write which records are excluded from both and which from only one.
3. **Fix the units** of every quantity and of the result: units, pieces, batches, kilograms; a rate as a fraction or a percentage, with the precision it is reported at.
4. **Define the reporting period** with its boundary, its time zone and its clock: the source event time or the approval time. Say what happens to records whose timestamp is missing or falls on the boundary.
5. **State the restatement rule**: whether a late correction changes an already reported period, and how the change is marked.
6. **Write the tests** that would catch the classic errors: double-counting through a join, a denominator that shrinks when records are excluded, unit mixing, and a period that straddles a boundary.
7. **Name the owner and the version**, and record every change.

Go deeper: [data modeling and metric contracts](#/module/dbxfe-modeling), [build a metric people can trust](#/lesson/dbxfe-m05-l01), [SQL analytics and performance diagnosis](#/module/dbxfe-m05) for testing the computation, and [business intelligence and semantic delivery](#/module/dbxfe-bi) for how the contract reaches the dashboard.

<!-- section:example -->

### Metric contract: Cinderline Components (fictional), unit defect rate

Version 1, proposed 12 March; owner: the quality lead. The plant analyst and the operations director have reviewed the definitions; the business-day boundary is agreed, the treatment of rework is not.

#### Name and grain

`unit_defect_rate`: one value per production line per business day at the North plant. A plant-level value is the same calculation over all the plant's lines, never an average of line rates.

#### Numerator

`defective_units`: the sum of the defective-units field over accepted inspections for the line and day. Accepted means the highest valid version of each inspection under the change-data contract; quarantined, excluded and unresolved inspections are outside it, and while any inspection is unresolved no new rate is published. Units found defective and then reworked are counted as defective at inspection; whether rework changes the count is the open item.

#### Denominator

`inspected_units`: the sum of the inspected-units field over the same accepted inspections. The denominator uses exactly the population of the numerator: an inspection excluded from one is excluded from both. An inspection with zero inspected units contributes nothing to either and is not an error. A line with no accepted inspections on a day has no rate, shown as "no inspections," never as zero; one whose accepted units total zero shows "no inspected units."

#### Units and precision

Both quantities are counts of physical units as recorded at inspection. The rate is a fraction reported as a percentage to one decimal place; the underlying fraction is stored unrounded. Batch counts and weight fields in the ERP are not used.

#### Reporting period

The business day is the half-open interval from 00:00 plant local time to the next 00:00, assigned by the inspection's recorded inspection time, not by the time a correction was approved. An inspection with a missing inspection time is quarantined as unorderable in time and disclosed. No daylight-saving change falls in the pilot window; on a transition day records are assigned by local calendar date, so the day has 23 or 25 hours. The rule is untested.

#### Restatement

A correction approved after a day has been reported changes that day's rate on the next run. The restated day is marked in the report with the previous value and the date of restatement. The report never overwrites a restated value silently. Restatements older than 30 business days are applied and listed but not marked on the dashboard.

#### Why the two existing reports disagreed

On the disputed day (North, 2 March) the workbook said 7.1%, the plant sheet 10.8%, and the figure quality later agreed 5.0%: three answers to three questions. The workbook averages per-row rates by load date, and keeps a package retry's duplicate rows and the superseded revision beside its correction. The sheet sums units by inspection date over whatever was pasted, including a negative quantity typed as an adjustment. Neither rule was written down. Under this contract both read one accepted set: each delivery counted once, only the highest valid version, invalid rows quarantined and disclosed.

#### Tests

| Test | What it catches | Expected |
|---|---|---|
| Join inspections to lines and sum units | Double-counting through a one-to-many join | Sum equals the raw accepted sum |
| Exclude one inspection from the numerator only | Denominator drift | Test fails; both must exclude |
| Feed a weight field as units | Unit mixing | Test fails on the field name |
| Inspections at 23:59:59.5 and 00:00:00 | Boundary assignment | Two different days |
| Correction for a day already reported | Restatement | Rate changes; mark set |
| Line with no inspections, or only voided ones | Empty case | "no inspections" or "no inspected units", never 0 |

#### Conclusion

The contract explains the morning disagreement without blaming anyone and gives both reports one definition. One item stays open (rework) and one rule is untested (the daylight-saving day). Version 1 is proposed to the quality lead for signature with those two noted.

#### Change log

Version 1, 12 March: first proposal after the baseline interviews; not yet signed.

<!-- section:template -->

### Metric contract

#### Name, grain and owner

- The metric's name as it will appear; one row means what over what period; the business owner; the version and date.

#### Numerator

- Field, population, inclusions and exclusions, and the source of the accepted set.

#### Denominator

- Field, population, whether its population is exactly the numerator's, how zero and empty cases are shown.

#### Units and precision

- Units of each input; whether the result is a fraction or a percentage; reported precision; stored precision.

#### Reporting period

- Boundary, time zone, the timestamp that assigns a record to a period, the missing-timestamp rule, the transition-day rule.

#### Restatement

- Whether late corrections change reported periods, how a restated value is marked, and for how long.

#### Tests

| Test | What it catches (double-counting, denominator drift, unit mixing, boundary, restatement, empty case) | Expected outcome |
|---|---|---|

#### Change log

- Each version: what changed, who asked, who approved, and which reports were affected.

<!-- section:limits -->

A metric contract makes a definition unambiguous and testable; it cannot make the source fields mean what their names suggest, and it does not validate that inspections were recorded correctly at the plant. It is one metric's definition, not a data model, and it depends on the change-data contract for what "accepted" means. Tests prove the computation matches the contract, not that the contract matches what the business needs; that is the owner's signature. Open items such as rework or transition days remain open until an owner decides. Escalate when two owners claim the same metric name with different definitions, when a dashboard shows a metric no contract covers, or when a restatement rule would change a number already used in a decision.
