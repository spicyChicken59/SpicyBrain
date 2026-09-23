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

Status: proposed, awaiting the DBA's confirmation of change-capture permission.

#### Decision to make

How the North plant's accepted daily defect rate will be produced for the pilot, given that corrections are approved in periodic batches, the existing SQL Server morning report must keep running, and two part-time engineers will operate whatever is chosen.

#### Constraints on every option

No real data leaves the plant network before the security review. The existing morning report is not switched off during the pilot. The metric contract, not the pipeline, defines the rate. There is no named operator yet.

#### Options

**Option A: improve the current path.** Rewrite the analyst's workbook logic as a scheduled SQL Server job that applies corrections in revision order and publishes one table both reports read. Nothing moves off the plant network. The data team already operates this environment. It cannot hold conflicting records visibly without new tables, and it does not create a path toward sensor data or shared access across plants.

**Option B: nightly extract to a governed lakehouse path.** A scheduled extract of inspections and the approved correction CSVs lands in cloud storage, a nightly job resolves revisions, quarantines conflicts and publishes the accepted rate, and the morning report reads it. Corrections approved after the extract appear the next morning. It needs the security review, a workload identity, a storage path and an operator, none of which exist today.

**Option C: change-data capture from SQL Server.** Continuous capture of inspection changes, resolved as they arrive. It answers a freshness requirement nobody has established, depends on a permission the DBA has not granted, and adds a component the team has not operated.

**Option D: nothing yet.** Measure the baseline for five days first. Costs nothing but time; produces the number every other option is judged against.

#### Assumptions

| Assumption | Option(s) | Status |
|---|---|---|
| The ERP export completes before 6:00 a.m. | B | Stated by the DBA, not measured |
| Daily freshness satisfies the 8 a.m. decision | A, B | Stated by the operations director; untested |
| Change capture is permitted on the ERP | C | Unknown |
| Two part-time engineers can operate a nightly job with a runbook | B | Stated by the data lead |
| Conflicting records are rare | A | Guessed; nobody has counted them |

#### Tradeoffs as consequences

A keeps everything local and familiar but leaves conflicts and exclusions invisible, which is the cause of today's disagreement. B makes exclusions visible and creates a governed place other plants could join, at the price of a security review, a new operating duty and next-morning corrections. C buys freshness that has not been asked for at the highest operational and permission cost. D delays everything by a week and de-risks every other choice.

#### Decision

D first, then B for the pilot, on the condition that the security review completes and an operator is named before real data moves. A remains the fallback if the review does not complete within the pilot window, because it still fixes revision ordering. C is not chosen.

#### What would reverse this

If the baseline shows corrections approved during the morning routinely change the previous day's rate, next-morning freshness is insufficient and C or an intraday extract must be re-examined. If the security review requires a connectivity pattern the team cannot operate, A becomes the decision. If the data team cannot name an operator, no option beyond D should proceed.

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
