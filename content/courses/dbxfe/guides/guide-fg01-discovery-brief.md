<!-- section:action -->

Write the brief within a day of the conversation, while attribution is still fresh. Work in this order.

1. **Name the decision before the request.** Write one sentence: who decides what, when, and with which information. If the request arrived as a product phrase, ask what would change on the day it existed.
2. **Sort every statement you heard** into reported fact, assumption and unknown. Attach each number to the person who said it and whether anyone has measured it.
3. **List the people by their stake in the decision**, not by title: who funds, who accepts the result, who operates the outcome, who can block it.
4. **Record constraints as stated**: access approval, sensitivity, permitted network paths, spending ceiling, timing, operating ownership.
5. **Rank the unknowns** by whether the answer would change the design or the decision, and assign each to the one person who can answer it.
6. **Propose one bounded next step** with a measurable criterion and named acceptors, labelled as a proposal.

Evidence to collect before you write: dated interview notes, the list of source systems and their owners, a copy of any existing report and where its numbers come from, and the approval trail for any data already shared.

Go deeper: [discovery and qualification](#/module/dbxfe-m02) for the interview method, [find the outcome behind the request](#/lesson/dbxfe-m02-l01), [define success and expose missing information](#/lesson/dbxfe-m02-l03), the [customer decision journey](#/module/dbxfe-m01) for how a brief moves an account forward, and [proofs of value](#/module/dbxfe-m10) for what the proposed next step must contain.

<!-- section:example -->

### Discovery brief: Cinderline Components (fictional), quality reporting

#### Request as received

"Real-time quality dashboards," relayed by the account team after one call with the operations director and a follow-up with the plant analyst. Nobody on the call defined "real time."

#### The decision

At the 8 a.m. meeting each plant's supervisors choose which production line to investigate first. The defect rate for the previous day differs between the analyst's workbook and the plant sheet, and the argument about which number is right often delays the choice. The decision is daily; nobody has shown that it needs continuous updates.

#### Reported facts, attributed

| Statement | Source | Measured? |
|---|---|---|
| About 20 hours a week go to reconciling the two reports | Plant analyst, self-estimate | No |
| Investigation choices happen at shift change | Operations director | No, stated from memory |
| Inspection records reach the ERP promptly; quality corrections are approved in periodic batches | DBA | Partly: batch approval confirmed, timing not |
| No source path to any cloud environment is approved | Security lead | Yes, by policy |
| Three plants; ERP on SQL Server; corrections arrive as CSV exports; sensor events held separately | Data lead | Yes, by inventory |

#### Assumptions found in the request

That hourly freshness would improve the morning choice (nobody has tested a daily trusted number first). That the workbook is the wrong report (which of the two is right is unknown; both may be). That the current team could operate a new feed (the data lead says continuous support is not staffed).

#### Stakeholders and their stake

Operations director: funds a next step only if the metric is trusted and someone maintains the feed. Quality lead: owns the metric definition and the correction policy. Data lead: can prepare approved synthetic records now; two engineers part time. Security lead: requires classification, named identities and a reviewed source-to-cloud path before any real data moves. DBA: holds the SQL Server version, topology and change-capture permission. Sponsor: has set a planning ceiling for pilot usage and labelled it unapproved.

#### Constraints

No real data until the security review completes. Synthetic samples are available now. No named operator for a failed feed. The cloud region and connectivity pattern are not agreed. Any pilot must keep the existing morning report running.

#### Unknowns, ranked by what they change

1. What is the defect-rate denominator, and what is the business-day boundary? Changes the metric and both reports. Quality lead.
2. How are corrections identified and ordered, and are historical reports restated? Changes the ingestion design. Quality lead with the DBA.
3. Which SQL Server version and topology, and is change capture permitted? Changes the source path. DBA.
4. What is the classification of inspection data and which network path is permitted? Changes whether a pilot may use real data at all. Security lead.
5. Who operates a failed feed on a Monday morning? Changes whether the sponsor will fund anything. Operations director with the data lead.

#### Proposed next step

Subject to agreement, measure one plant for five staffed days before building anything: the time from approved source availability to the report, and the number of days the two reports disagree and by how much. This is a baseline, not a benefit. The data lead validates the measurement, operations accepts whether the disagreement count matches experience, security accepts the sample scope. If daily data is sufficient for the morning decision, the alternative to compare is a reliable scheduled report, not a streaming design.

#### Conclusion

Qualified for a bounded follow-up, not for a build. The buying decision turns on a trusted metric and a named operator, and neither exists yet. Return a revised brief once the quality lead and the DBA have answered unknowns one to three.

<!-- section:template -->

### Discovery brief

#### Request as received

- The words the customer used, who said them, and through whom they reached you.

#### The decision

- One sentence: who decides what, how often, with which information, and what delays or damages that decision today.

#### Reported facts, attributed

| Statement | Source (role) | Date heard | Measured or stated? |
|---|---|---|---|
| A specific claim, quoted or closely paraphrased | The person who said it | When | "Measured by ..." or "self-estimate" |

#### Assumptions found in the request

- Each belief the request depends on that nobody has tested, with what would happen to the design if it were false.

#### Stakeholders and their stake

- One line per person: role, what they need from the outcome, and what they can block or fund.

#### Constraints

- Access approvals, sensitivity, permitted network paths, spending ceilings, dates, operating ownership; each with its status (confirmed, stated, unknown).

#### Unknowns, ranked

1. The question, what it changes (design, decision or both), who can answer it, and by when it is needed.

#### Proposed next step

- One bounded action with a population, a measurement, a threshold or an observation to collect, and the named acceptors; marked as proposed until each acceptor agrees.

#### What would stop this

- The conditions under which you would recommend not proceeding, stated before anyone has to say them.

<!-- section:limits -->

This brief records what people told you and separates it from what has been measured; it cannot make an estimate true. It establishes the decision as the customer describes it today, which may change once the metric is defined. It does not establish source feasibility, data sensitivity, network reachability or cost, each of which needs its own evidence from the DBA, the security lead and a measured baseline. A brief written from one conversation should say so, and its unknowns should outnumber its facts. Escalate when a stakeholder asks you to present a reported estimate as a result, when two people give incompatible answers to a ranked unknown, or when the decision owner cannot be identified.
