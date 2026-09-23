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

**Fictional worked example: Cinderline plant-one quality pilot, readout to the sponsor on day 10.** All names, figures and dates are fictional.

### Decision requested

Approve a second five-day run, days 11 to 15, inside the same approved sample, or retain the current path. Recommendation: approve it once the freshness clock is defined (operations director), a backup operator is named (data lead) and the security lead confirms in writing that her approval covers those days; do not approve expansion to other plants.

### What was tested

Plant one, days 6 to 10, on the platform workspace, against the current report re-cut to the same plant-time boundary. Real data ran only as the approved sample: plant-one approved fields exported nightly to the workspace, a route the security lead approved in writing before day 1 after a specialist review of that route; no live source path has been reviewed. Synthetic edge cases (duplicate batch, late correction, invalid quantity, injected failure) were delivered on purpose. Not tested: plants two and three, sensor data, ERP writes, performance beyond pilot volume.

### Evidence

| Criterion | Status | Observation | Evidence |
|---|---|---|---|
| Correctness | Pass with one named exception | Key-level and total reconciliation on all five days; inspector-code backfill accepted as an exception | Reconciliation records, days 6 to 10 |
| Freshness | Not yet judged | Served by 07:45 on 4 of 5 days; 47, 52, 58 and 71 minutes after file arrival, day 10's 71 being 34 after a late approval | Pipeline log; ledger row 6 |
| Replay | Pass | Duplicate delivery left the snapshot unchanged; correction produced one new snapshot | Snapshot ids in the run log |
| Recovery | Pass, one failure mode | Injected failure recovered in 14 minutes against a 30-minute target | Rehearsal record, day 8 |
| Day-9 failure | Open | Resolver failed; day 8's rate shown, labelled stale; cause not established | Escalation packet, day 9; ledger row 11 |
| Operation | Fail on one day | 0.5, 0.4, 0.9, 1.6, 0.4 hours on days 6 to 10; day 9, the failure, passed the one-hour ceiling | Operator log; ledger row 10 |
| Source path review | Blocked | Live source path: specialist review not started; topology not supplied | Ledger row 5 |

### Business meaning

For the 08:00 meeting: one accepted-inspection path produced a rate the quality lead accepts, with corrections applied once and visible, and it failed safely on day 9, showing a day-old rate labelled stale rather than a wrong one. Freshness cannot be judged until the operations director defines when the clock starts; recorded latencies were 47 to 71 minutes. The operating burden is not settled: the failure cost 1.6 operator hours, and one operator without a backup is not an operating model.

### Cost on its basis

Incurred, as measured in this fictional pilot, days 1 to 10: $410 of platform usage against the hypothetical $1,500 planning ceiling, and 7.3 operator hours (3.5 in week one while learning, 3.8 on days 6 to 10). Projected: the illustrative annual model, hypothetical inputs only, negative in year one at base and positive in the recurring year above about 5.6 released hours per week. No saving has been observed.

### Risks and open questions

Freshness clock definition (operations director); operator backup (data lead); the day-9 failure's cause (integration specialist); the live source path review (security lead and specialist), which blocks real data beyond the approved sample; a third analyst workbook of unknown ownership that reads the old table (operations analyst).

### Next step

If the three conditions are met by the review at 16:00 on day 10, run days 11 to 15 on the same basis and re-read this table with a second column; if not, the run starts the day after they are. A second plant waits for the live source path review and a met operation criterion. The reader is asked to approve the second run and its usage, expected within the ceiling's remaining $1,090; nothing else.

### Not claimed

Production readiness, savings, performance at scale, or any result on plants two and three. The twenty-one-row ledger is attached.

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
