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

Version 1, proposed; owner: the quality lead. The plant analyst and the operations director have reviewed the definitions; the business-day boundary is agreed, the treatment of rework is not.

#### Name and grain

`unit_defect_rate`: one value per production line per business day at the North plant. A plant-level value is the same calculation over all the plant's lines, never an average of line rates.

#### Numerator

`defective_units`: the sum of the defective-units field over accepted inspections for the line and day. Accepted means the highest valid version of each inspection under the change-data contract, excluding quarantined and withheld inspections. Units found defective and then reworked are counted as defective at inspection; whether rework changes the count is the open item.

#### Denominator

`inspected_units`: the sum of the inspected-units field over the same accepted inspections. The denominator uses exactly the population of the numerator: an inspection excluded from one is excluded from both. An inspection with zero inspected units contributes nothing to either and is not an error. A line with no accepted inspections on a day has no rate, shown as "no inspections," never as zero.

#### Units and precision

Both quantities are counts of physical units as recorded at inspection. The rate is a fraction reported as a percentage to one decimal place; the underlying fraction is stored unrounded. Batch counts and weight fields in the ERP are not used.

#### Reporting period

The business day runs from 00:00 to 23:59:59 plant local time, assigned by the inspection's recorded inspection time, not by the time a correction was approved. An inspection with a missing inspection time is quarantined as unorderable in time and disclosed. The plant does not observe daylight-saving changes during the pilot window; the rule for the transition day is recorded as "assign by local wall-clock time; the duplicated hour belongs to the earlier day" and is untested.

#### Restatement

A correction approved after a day has been reported changes that day's rate on the next run. The restated day is marked in the report with the previous value and the date of restatement. The report never overwrites a restated value silently. Restatements older than 30 business days are applied and listed but not marked on the dashboard.

#### Why the two existing reports disagreed

The analyst's workbook used approved corrections as of the morning, so a correction approved at 10 a.m. changed yesterday's number in the workbook but not in the plant sheet, which was printed at 7. The plant sheet counted a voided inspection's original units; the workbook dropped it. Neither was wrong under its own rule; neither rule was written down. Under this contract both would be computed from the same accepted set and the plant sheet would show the restatement mark.

#### Tests

| Test | What it catches | Expected |
|---|---|---|
| Join inspections to lines and sum units | Double-counting through a one-to-many join | Sum equals the raw accepted sum |
| Exclude one inspection from the numerator only | Denominator drift | Test fails; both must exclude |
| Feed a weight field as units | Unit mixing | Test fails on the field name |
| Inspection at 23:59:59 and 00:00:00 | Boundary assignment | Two different days |
| Correction for a day already reported | Restatement | Rate changes; mark set |
| Line with no inspections | No rate | "no inspections," not 0 |

#### Conclusion

The contract explains the morning disagreement without blaming either report and gives both a shared definition. One item stays open (rework) and one rule is untested (the daylight-saving day). Version 1 is proposed to the quality lead for signature with those two noted.

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
