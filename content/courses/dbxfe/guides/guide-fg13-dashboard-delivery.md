<!-- section:action -->

Plan the dashboard from the action it must support, not from the tables you have. A page nobody acts on is a report, and a report nobody trusts is a dispute.

1. **Name each audience and the action** they take from the page, at what time, and what they do today instead. One page can serve two audiences only if their actions need the same numbers at the same grain.
2. **Bind every number on the page to a metric contract** by name and version. A tile without a contract is removed or labelled as unverified.
3. **Decide how freshness is communicated**: the period the numbers cover, when they were published, whether a shown period has been restated, and what the page says when it is not updated. Put it where the eye lands, not in a tooltip.
4. **Write the access matrix for the page and its underlying objects**: who sees it, who must not, and whether filters can leak rows the viewer may not read.
5. **Write the validation script before the page exists**: for a fixed input snapshot, the exact values each tile must show, the filter states to try, the empty and restated cases, and who signs.
6. **Assign ownership**: who changes a definition, who answers "is this number right," who is told when refresh fails.

Go deeper: [business intelligence and semantic delivery](#/module/dbxfe-bi), [build a metric people can trust](#/lesson/dbxfe-m05-l01), [Unity Catalog and governance](#/module/dbxfe-m06) with [design least-privilege access](#/lesson/dbxfe-m06-l02) for the access matrix, and [SQL analytics and performance](#/module/dbxfe-m05) if the page is slow at the moment it is needed.

<!-- section:example -->

### Dashboard delivery plan: Cinderline Components (fictional), North plant morning quality page

Proposed; the storyboard is a sketch reviewed with the operations director and the plant analyst, not a built page. All values in the validation script come from the five-day reconciliation sheet.

#### Audiences and actions

| Audience | Action | When | Today |
|---|---|---|---|
| Line supervisors, 8 a.m. meeting | Choose which line to investigate first | 7:45 to 8:15 a.m. | Argue over two printed reports |
| Plant analyst | Confirm the number and explain exclusions if asked | 7:30 a.m. | Reconcile the workbook against the plant sheet |
| Quality lead | See how many inspections are withheld or quarantined and open them | During the morning | Hears about problems a day later |

The supervisors and the analyst need the same numbers at the same grain, so one page serves both. The quality lead's need is a count and a link, not a second page.

#### Content, bound to contracts

Tile per line: `unit_defect_rate` version 1, previous business day, one decimal place. Beside each tile: accepted inspections, withheld (conflict), quarantined (invalid or unorderable), from the quality response plan's disclosed counts. A seven-day line per production line of the same metric. A restatement mark on any day changed since it was first shown, with the previous value on hover and in the table view. No plant-level average of line rates; the plant figure is the contract's all-lines calculation. No sensor tiles: no contract exists for them.

#### Freshness communication

Top of the page, in words: the business day covered, the publish time of the nightly run, and "restated days are marked." When the nightly run has not published by 7:30 a.m., the page shows the last published day with "not updated: see the operator note" in the same position, and the operator's note appears below it. The refresh is scheduled once after the nightly job signals completion; the morning queries read the published table and are not re-run per viewer.

#### Access

| Principal | Page | Underlying objects | Must not |
|---|---|---|---|
| `north-reporting-analysts` (supervisors and analyst) | View | SELECT on `accepted.daily_line_rate` | Read raw or quarantine rows through any filter |
| `quality-stewards` | View, plus the quarantine link | SELECT on accepted and quarantine tables | Edit the page |
| Page owner (data team) | Edit | As the service principal that publishes | Publish a tile with no contract |
| Everyone else | None | None | |

Filters are restricted to line and day; there is no free-text filter and no drill-through to raw rows, so a viewer cannot reach objects beyond the page's own grants. This is checked in the access review, not assumed here.

#### Validation script

On the retained five-day synthetic snapshot: each line tile equals the reconciliation sheet's value to one decimal (line 3, day 4: 4.8%); the counts beside each tile equal the sheet's accepted, withheld and quarantined counts (day 2: 19, 1, 1); the day-2 restatement mark appears after the day-4 correction and shows the previous value 5.3%; a line with no inspections on day 5 shows "no inspections," not 0.0%; filtering to line 3 does not change the plant figure; the page under a test analyst identity shows the tiles and refuses the quarantine link; the page under the outsider identity does not load. Signed by the plant analyst (values), the quality lead (counts and marks) and the security lead (access), with the storyboard attached.

#### Ownership

Definition changes go through the metric contract's owner and a new version, then the page. "Is this number right" goes to the plant analyst first, then the quality lead. Refresh failure notifies the operator and the analyst before 7:30 a.m.

#### Conclusion

The page supports one action, shows one contracted metric with its exclusions and its freshness in words, and has a validation script with exact expected values and three signers. Not established: the built page's behaviour, which waits on the access review, and whether supervisors act on it, which the pilot readout must observe rather than assume.

<!-- section:template -->

### Dashboard delivery plan

#### Audiences and actions

| Audience | Action taken from the page | When | What they do today |
|---|---|---|---|

#### Content, bound to contracts

- Each tile or chart: the metric contract name and version, grain, period, precision; the disclosed exclusion counts; what is deliberately absent and why.

#### Freshness communication

- Where and in which words the page states the period covered, the publish time, restatements, and the not-updated state; the refresh trigger and whether viewers re-run queries.

#### Access

| Principal | Page permission | Underlying object privileges | Must not be able to |
|---|---|---|---|

- How filters and drill-throughs are bounded so the page cannot reach beyond its grants.

#### Validation script

- The fixed snapshot; the exact expected value per tile; filter states; empty, restated and not-updated cases; identity tests; the signers and what each signs for.

#### Ownership

- Who changes definitions; who answers a correctness question; who is notified of a failed refresh and by when.

<!-- section:limits -->

This plan establishes what the page must show, to whom, and how it will be validated; it does not establish that the built page behaves that way until the script is run on it, nor that anyone will act on the numbers, which only the pilot readout can observe. The access matrix is a design until the access review executes it, and a dashboard tool's own permission model must be checked against current documentation rather than assumed. The plan depends on a metric contract and a quality response plan; a page built without them will need this one rewritten. Escalate when an audience asks for a tile with no contract, when freshness cannot be stated in words the audience accepts, or when a filter would expose rows a viewer may not read.
