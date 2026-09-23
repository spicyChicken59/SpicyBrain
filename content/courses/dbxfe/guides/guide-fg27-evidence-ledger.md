<!-- section:action -->

Keep one ledger for the whole engagement, from the first claim in a discovery call to the last observation in the pilot. A ledger row is a claim with what was done to test it, what was seen, where the evidence lives and what the observation cannot support.

1. **Enter claims as they are made**, attributed to their source: a stakeholder's statement, a document, a demo, a run. A claim nobody made is a hypothesis; label it so.
2. **For each claim, write the test** that would support or contradict it, in observable terms. If no test is possible within scope, record "not testable here" rather than leaving the cell blank.
3. **Record the observation** exactly: numbers with units, dates with times and zones, counts with denominators, "not run" when not run.
4. **Point at the source:** a file hash, a run log path, a snapshot id, a named person and date. A source you cannot point at is a recollection.
5. **Write the caveat:** synthetic input, single run, one reviewer, basis difference, estimated not measured.
6. **Name the unresolved gap** that stops the row from being closed, with an owner.
7. **Never overwrite a row.** A new observation is a new row that supersedes the old one by reference.

Evidence to collect: the ledger itself, with every row holding all six fields or an explicit "none", and the list of open gaps sorted by the decision they block.

Deeper: the retained lesson [Read out evidence and make a decision](#/lesson/dbxfe-m10-l03), the module [Proofs of value](#/module/dbxfe-m10) for the test matrix the ledger feeds, and [Field execution and capstone](#/module/dbxfe-m12) for the readouts and handoffs that quote it.

<!-- section:example -->

**Fictional worked example: the Cinderline quality pilot ledger, end of week two.** Nine rows are shown of the twenty-one in the full ledger. Dates and figures are fictional.

| # | Claim | Source of claim | Test | Observation | Evidence source | Caveat | Unresolved gap |
|---|---|---|---|---|---|---|---|
| 1 | The workbook and plant sheet disagree on the morning rate | Operations director, discovery call | Compare both for ten days | Disagreed on 7 of 10 days; largest gap 0.9 percentage points | Comparison sheet, dated | Old report basis was server time; re-cut not yet applied | Which of the two the meeting acted on each day |
| 2 | Corrections are approved weekly by the quality lead | Quality lead, demo session | Inspect approval records for a month | 4 approvals in 5 weeks | Approval email folder, listed by date | Reviewed by one person | Whether the skipped week means no corrections or an unrecorded approval |
| 3 | The revision rule yields 20 / 1 after the A v2 correction | Demo script | Local deterministic run on fixtures | 20 inspected / 1 defective | Run log with fixture hashes | Synthetic input; local run | None; row closed |
| 4 | Replay does not double count | Demo script | Deliver A v2 twice | Snapshot id unchanged | Same run log | Synthetic; local | Rerun on the platform pending |
| 5 | Source connectivity to the ERP is feasible | Nobody; hypothesis | Specialist review of version, topology, path | Not run | None | Not testable until inputs are supplied | Version and topology from the DBA |
| 6 | The report can be served within 60 minutes of source availability | Charter hypothesis | Pipeline timestamps over five days | 47, 52, 58, 71, 49 minutes | Pipeline log, days 6 to 10 | The 71-minute day followed a late CSV approval | Whether "source availability" starts at approval or at file arrival |
| 7 | Reconciliation effort is two to four hours a week | Data lead, estimate | Operator time log in week one | 3.5 hours logged | Operator log | One week; the operator was learning the runbook | Second week's log |
| 8 | The old path over-counts duplicate deliveries with trailing spaces | Reconciliation, day 5 | Trace five keys | Confirmed: 5 duplicates counted as distinct | Reconciliation record, day 5 | Found on one day | DBA to decide fix or documentation |
| 9 | A null revision means first version | Nobody; assumption in the resolver | Ask the quality lead | Not yet asked | None | Surfaced by the day-5 quarantine | Quality lead's answer |

### Reading the ledger

Row 3 is closed and says why. Row 4 is closed locally and open on the platform, so it appears once with the platform rerun as its gap. Row 5 is the honest shape of an untested claim: nobody made it, no test has run, and the row exists so the readout cannot omit it. Row 6 is a passing observation with a definitional gap; the 71-minute day is not a failure until the acceptor says where the clock starts, and the ledger records the observation without deciding that. Row 9 is the kind of row a ledger exists for: an assumption that lived in code until a quarantine made it visible.

### Open gaps by the decision they block

The charter's freshness criterion cannot be judged until row 6's clock is defined (operations director). The pilot cannot expand to real data until row 5 has its inputs (DBA) and a specialist review. Row 7 needs a second week before it supports the operation criterion. Row 9 blocks acceptance of the day-5 reconciliation (quality lead).

### What the ledger says at this point

Two definitional questions and one untested prerequisite block the readout. No criterion has failed; two have not been fully measured; one prerequisite has not started.

<!-- section:template -->

### Ledger

| # | Claim | Source of claim | Test | Observation | Evidence source | Caveat | Unresolved gap (owner) |
|---|---|---|---|---|---|---|---|
| Stable number, never reused | The statement, as made, in one sentence | Person and date, document, run, or "nobody; hypothesis" | What was or would be done, in observable terms, or "not testable here" | Exact values with units, dates with zones, counts with denominators, or "not run" | Hash, log path, snapshot id, record name, or "none" | Synthetic, single run, one reviewer, basis difference, estimate | What stops the row from closing, and who resolves it |

### Rules for the ledger

- **A row is never edited after another row cites it;** a new observation is a new row that names the row it supersedes.
- **Every field holds a value or an explicit "none" or "not run";** blank cells are not allowed.
- **Closed rows say why they closed.**

### Open gaps by decision

| Decision | Blocking rows | Owner | Needed by |
|---|---|---|---|

### Ledger summary for a readout

- **Counts:** claims closed with support, closed as contradicted, open with observations, open without a test, not testable here.

<!-- section:limits -->

A ledger establishes what was claimed, what was observed and where the evidence lives; it does not establish that the observations were correct, only that they can be checked by someone who follows the source column. Rows with synthetic inputs or a single run support intent and logic, not production behaviour, and the caveat column says so. A ledger is only as complete as the discipline of entering claims at the moment they are made; a claim that was never entered cannot be reported as open. Escalate when a row's observation contradicts a claim a customer has acted on, when a source cannot be produced for a closed row, or when a gap's owner has no date.
