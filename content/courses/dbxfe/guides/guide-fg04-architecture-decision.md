<!-- section:action -->

Write the decision record when there are at least two options you could defend, and before the customer has heard you prefer one. A record with one option is a proposal, not a decision.

1. **State the requirement the decision serves** by reference to the requirements contract, and the constraints that bind every option equally: access policy, team capacity, existing reports that must keep running.
2. **Describe each option in the same terms**: what moves, who operates it, what changes for the people who use today's report, what it costs in effort, and what it cannot do. Include the option of changing nothing yet.
3. **List the assumptions each option depends on** and mark each as measured, stated or guessed.
4. **Write the tradeoffs as consequences**, not adjectives: "corrections apply the next morning, not within the hour," not "less real-time."
5. **Choose, and say what evidence would reverse the choice.** A decision you cannot describe reversing is one you have not examined.
6. **Record what stays open** and who owns closing it.

Evidence to collect: the current-state drawing with owners, the source capabilities the DBA has confirmed, the security lead's written constraints, the data team's stated capacity, and any measured baseline.

Go deeper: [architecture reasoning and migration decisions](#/module/dbxfe-m08), [turn current state into a target design](#/lesson/dbxfe-m08-l01), [defend tradeoffs and alternatives](#/lesson/dbxfe-m08-l02), [competition, coexistence and business value](#/module/dbxfe-m11) for a fair comparison, and [warehouse and platform migrations](#/module/dbxfe-warehouse-migration) for staged coexistence.

<!-- section:example -->

### Architecture decision record: Cinderline Components (fictional), daily quality report

Status: proposed, 16 March; the operations director decides; B waits on the security review and a named operator.

#### Decision to make

How the pilot produces the North plant's accepted daily defect rate under requirements contract version 0.2.

#### Constraints on every option

No real data leaves the plant network before the security review. The existing SQL Server morning report keeps running. The metric contract, not the pipeline, defines the rate. Two part-time engineers operate whatever is chosen, and there is no named operator yet.

#### Options

| Option | What moves | Who operates it | Change for report users | Effort (guessed) | What it cannot do |
|---|---|---|---|---|---|
| A: improve the current path | Nothing leaves the plant; the workbook logic becomes a scheduled SQL Server job applying corrections in revision order | The data team, as today | Both reports read one table | Low: existing tools | Show conflicts without new tables; open a path to sensor data or other plants |
| B: nightly extract to a governed lakehouse path | Inspections and the approved correction CSVs land in cloud storage; a nightly job resolves revisions, quarantines conflicts and publishes the accepted rate | Unnamed; an operator must exist first | The morning report reads the accepted rate; corrections approved after the extract appear the next morning | High: security review, workload identity, storage path, the job | Run before the review completes |
| C: change-data capture from SQL Server | Inspection changes, continuously | Data team and DBA; a component nobody here has run | Numbers fresher than the meeting needs | Highest: B's prerequisites plus a change request in a DBA window | Carry corrections, which arrive as CSV files and never pass through the ERP; start without the DBA's permission |
| D: nothing yet | Nothing; five days of baseline measurement | The data lead | None; today's two reports continue | Five staffed days | Fix anything; it only measures |

#### Assumptions

| Assumption | Option(s) | Status, and when recorded |
|---|---|---|
| The ERP export completes before 6:00 a.m. | B | Stated by the DBA, 12 March; not measured |
| Daily freshness satisfies the 8 a.m. decision | A, B | Stated by the operations director, 4 March; untested |
| Change capture is permitted on the ERP | C | Unknown; asked of the DBA, 12 March |
| Two part-time engineers can operate a nightly job with a runbook | B | Stated by the data lead, 5 March |
| Conflicting records are rare | A | Guessed, 16 March; nobody has counted them |
| Hidden conflicts and exclusions caused today's disagreement | A, B | Guessed, 16 March; D measures it |

#### Tradeoffs as consequences

A keeps everything local and familiar, but conflicts and exclusions stay invisible, so its one number cannot show why it differs from the old reports; whether they caused today's disagreement is unmeasured. B makes exclusions visible and creates a governed place other plants could join, at the price of a security review, a new operating duty and next-morning corrections. C buys freshness nobody has asked for at the highest operational and permission cost. D delays everything by a week and de-risks every other choice.

#### Decision

D first, then B for the pilot, provided the security review completes and an operator is named before real data moves. A remains the fallback if the review does not complete within the pilot window, because it still fixes revision ordering. C is not chosen.

#### What would reverse this

If the baseline shows morning-approved corrections routinely change the previous day's rate, next-morning freshness is insufficient and an intraday run over new correction files must be examined; C would not help. If the security review requires a connectivity pattern the team cannot operate, A becomes the decision. If the data team cannot name an operator, no option beyond D should proceed.

#### Open

Change-capture permission (DBA). Business-day boundary (quality lead). Operator (data lead with operations). Cloud region and connectivity pattern (security lead).

<!-- section:template -->

### Architecture decision record

#### Status and date

- Proposed, accepted, superseded; the date; who decides.

#### Decision to make

- The requirement served, by reference; the constraints that apply to every option.

#### Options

- For each option, in the same terms: what moves and where, who operates it, what changes for the people using today's path, effort, what it cannot do. Always include "change nothing yet."

#### Assumptions

| Assumption | Option(s) it supports | Status (measured, stated by whom, guessed) |
|---|---|---|

#### Tradeoffs as consequences

- One sentence per option stating what the customer gains and gives up, in observable terms.

#### Decision

- The option chosen, the conditions attached, and the fallback if a condition fails.

#### What would reverse this

- Specific observations that would change the decision and which option they would point to.

#### Open questions

- Each unresolved item with its owner and the decision it blocks.

<!-- section:limits -->

A decision record makes a choice defensible and reversible; it cannot make an assumption true or a capability exist. Options are compared on what you know at the date recorded, so a record without dates and assumption status is unreadable later. It does not establish cost, which needs its own worksheet with currency, period and sources; nor security acceptance, which needs a review; nor migration safety, which needs reconciliation and a rollback rehearsal. The reversal criteria are the record's main value, so a decision whose reversal you cannot describe should not be presented as final. Escalate when a sponsor asks for the record without the alternative, when an assumption marked "guessed" is load-bearing for the chosen option, or when the operator is unnamed at the point of commitment.
