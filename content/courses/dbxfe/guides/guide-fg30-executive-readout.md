<!-- section:action -->

An executive readout gives a decision-maker what they need to decide, on one page, in an order that puts the decision first and the evidence within reach.

1. **Lead with the decision requested**, in one sentence, and the recommendation in the next. A reader who stops here should know what you are asking.
2. **State what was tested,** on what population, in what environment, for how long, and what was not tested. Two or three sentences.
3. **Give the evidence** as a short table: each criterion with its status (pass, fail, not tested, blocked), the observation, and where the evidence lives. Do not combine statuses into a score.
4. **Translate to business meaning:** what the result changes about the morning decision, the operating burden, or the risk. Say what it does not change.
5. **Report cost on its actual basis:** incurred versus projected, measured versus hypothetical.
6. **Name the risks and open questions** that could change the recommendation, with owners.
7. **Propose the next step** with a date or a decision condition, and what the reader is being asked to approve or not approve.
8. **Attach the ledger** and the readout's own limits.

Evidence to collect: the criteria table with sources, the incurred-cost record, the ledger reference, and the recommendation with its reversal conditions.

Deeper: the retained lessons [Assemble the customer engagement](#/lesson/dbxfe-m12-l03) and [Read out evidence and make a decision](#/lesson/dbxfe-m10-l03), the module [Field execution and capstone](#/module/dbxfe-m12), and [Proofs of value](#/module/dbxfe-m10) for the mixed-result readout and the cost basis.

<!-- section:example -->

**Fictional worked example: Cinderline plant-one quality pilot, readout to the sponsor.** All names, figures and dates are fictional.

### Decision requested

Approve a second five-day run on plant-one real data after the two open items below close, or retain the current path. Recommendation: approve the second run, conditional; do not approve expansion to other plants yet.

### What was tested

One plant, approved fields only, five staffed reporting days (days 6 to 10) on the platform workspace the data lead provisioned, with the current report re-cut to the same plant-time boundary for comparison. Synthetic edge cases (duplicate batch, late correction, invalid quantity, injected failure) were delivered deliberately. Not tested: the other two plants, sensor data, any write to the ERP, and performance beyond the pilot's volume.

### Evidence

| Criterion | Status | Observation | Evidence |
|---|---|---|---|
| Correctness | Pass with one named exception | Key-level and total reconciliation on all five days; inspector-code backfill accepted by the quality lead | Reconciliation records, days 6 to 10 |
| Freshness | Not yet judged | 47, 52, 58, 71, 49 minutes; the 71-minute day followed a late CSV approval | Pipeline log; ledger row 6 |
| Replay | Pass | Duplicate delivery left the snapshot unchanged; correction produced one new snapshot | Snapshot ids in the run log |
| Recovery | Pass, one failure mode | Injected failure recovered in 14 minutes against a 30-minute target | Rehearsal record, day 8 |
| Operation | Not yet judged | 3.5 hours in week one by one operator learning the runbook; no backup | Operator log; ledger row 7 |
| Source path review | Blocked | Specialist review not started; version and topology not supplied | Ledger row 5 |

### Business meaning

For the 08:00 meeting, the pilot shows that one accepted-inspection path can produce a rate both the quality lead and the operations director accept, with corrections applied once and visible. It does not yet show that the rate arrives on time by a definition the operations director has set, because "source availability" has not been defined; on four of five days it arrived within the hour by either definition. It does not change the operating burden question: one operator without a backup is not an operating model.

### Cost on its basis

Incurred: hypothetical platform usage of 410 currency units against the 1,500 planning figure, and 3.5 operator hours. Projected: the illustrative annual model, hypothetical inputs only, which is negative in year one at base and positive in the recurring year above about 5.6 released hours per week. No saving has been observed.

### Risks and open questions

Freshness clock definition (operations director); operator backup (data lead); the source path review (security lead and specialist), which blocks any run on real data beyond the approved sample; a third analyst workbook of unknown ownership that reads the old table (operations analyst).

### Next step

If the freshness definition and the operator backup are settled by the review date, run five more days on the same basis and re-read this table with a second column. Expansion to a second plant is not on the table until the source path review closes and the operation criterion is judged. The reader is asked to approve the second run's planning figure of a hypothetical 1,500 currency units; nothing else.

### Not claimed

Production readiness, savings, performance at scale, and any result on plants two and three. The ledger with twenty-one rows is attached.

<!-- section:template -->

### Decision requested and recommendation

- **The decision in one sentence; the recommendation in one sentence, with "conditional on" where true.**

### What was tested and not tested

- **Population, environment, duration, deliberate edge cases; the explicit exclusions.**

### Evidence

| Criterion | Status (pass / fail / not tested / blocked / not yet judged) | Observation with units | Evidence location |
|---|---|---|---|

### Business meaning

- **What the result changes about the decision it serves; what it does not change; the operating question stated plainly.**

### Cost on its basis

- **Incurred (measured, with currency and period) separated from projected (hypothetical or quoted, dated).**

### Risks and open questions

| Item | Effect on the recommendation | Owner | Needed by |
|---|---|---|---|

### Next step

- **The action, its date or condition, and exactly what the reader is asked to approve.**

### Not claimed

- **One line each for the claims a reader might infer and should not.**

<!-- section:limits -->

A readout establishes what was observed against agreed criteria on the tested scope, and it puts a recommendation beside that evidence; it does not make the recommendation true, and it cannot upgrade a blocked or untested criterion into a pass by omission. A criterion that is "not yet judged" because its definition is open is reported as such, not as a near-pass. Costs incurred are facts; projected costs are the model's, with the model's labels. A readout that names no reversal condition is advocacy. Escalate rather than send when a stakeholder asks for a single readiness number, when an evidence location cannot be produced, or when the recommendation would commit spending or scope that no named person has approved.
