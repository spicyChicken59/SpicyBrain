<!-- section:action -->

Keep one ledger for the whole engagement, from the first claim in a discovery call to the last observation in the pilot. A ledger row is a claim with what was done to test it, what was seen, where the evidence lives and what the observation cannot support.

1. **Enter claims as they are made**, attributed to their source: a stakeholder's statement, a document, a demo, a run. A claim nobody made is a hypothesis; label it so.
2. **For each claim, write the test** that would support or contradict it, in observable terms. If no test is possible within scope, record "not testable here" rather than leaving the cell blank.
3. **Record the observation** exactly: numbers with units, dates with times and zones, counts with denominators, "not run" when not run.
4. **Point at the source:** a file hash, a run log path, a snapshot id, a named person and date. A source you cannot point at is a recollection.
5. **Write the caveat:** synthetic input, single run, one reviewer, basis difference, estimated not measured.
6. **Name the unresolved gap** that stops the row from being closed, with an owner.
7. **Never overwrite a row.** A new observation is a new row that supersedes the old one by reference.

Evidence to collect: the ledger itself, with every row holding all seven fields or an explicit "none", and the list of open gaps sorted by the decision they block.

Deeper: the retained lesson [Read out evidence and make a decision](#/lesson/dbxfe-m10-l03), the module [Proofs of value](#/module/dbxfe-m10) for the test matrix the ledger feeds, and [Field execution and capstone](#/module/dbxfe-m12) for the readouts and handoffs that quote it.

<!-- section:example -->

**Fictional worked example: the Cinderline pilot ledger at the end of day 10.** Ten of twenty-one rows are shown. Day 1 was Monday 9 March 2026; days are staffed reporting days, times are plant-one local, and everything is fictional.

| # | Claim | Source of claim | Test | Observation | Evidence source | Caveat | Unresolved gap |
|---|---|---|---|---|---|---|---|
| 1 | The workbook and plant sheet disagree on the morning rate | Mara, operations director, call of 2026-02-10 | Compare both for ten days | Disagreed on 7 of 10 days; largest gap 0.9 percentage points | `compare/rates-0211-0224.xlsx` | Old report on server time; not yet re-cut | Which one the meeting acted on each day |
| 3 | The revision rule yields 20 / 1 after the A v2 correction | Demo script, 2026-02-19 | Local run on fixtures | 20 inspected / 1 defective | `runs/local/2026-02-19T07-40.log`, fixtures sha256 `3f2a…` | Synthetic; local | None; closed |
| 4 | Replay does not double count | Demo script, 2026-02-19 | Deliver A v2 twice | Snapshot id unchanged | Same log | Synthetic; local | Platform rerun pending |
| 5 | Source connectivity to the ERP is feasible | Nobody; hypothesis | Specialist review of version, topology, path | Not run | None | Not testable without inputs | Topology (DBA) |
| 6 | Served by 07:45 and within 60 minutes of source availability | Charter criterion (freshness), 2026-02-24 | Pipeline timestamps, days 6 to 10 | Served 06:27, 06:32, 06:38, not on day 9, 06:51; 47, 52, 58 and 71 minutes after file arrival | `runs/pilot/d06-d10.log` | Day 10 waited for a 06:17 CSV approval | Does the clock start at arrival or approval? (operations director) |
| 7 | Current reconciliation effort is two to four hours a week | Leo, data lead, charter estimate | Analyst's log, current process, baseline week | 5.5 hours | `baseline/analyst-log-0306.csv` | One week, one person | None; contradicted |
| 8 | The old path counts trailing-space duplicates | Reconciliation, day 5 | Trace five keys | Confirmed: 5 counted as distinct | `recon/day05.md` | One day | Fix or document (DBA) |
| 9 | A null revision is invalid | Nobody; the resolver assumes it and quarantines such rows | Ask the quality lead | Not yet asked | None | Surfaced by the day-5 quarantine | First version or unknown? (quality lead) |
| 10 | No pilot day takes the operator over an hour | Charter criterion (operation) | Operator's daily log, days 6 to 10 | 0.5, 0.4, 0.9, 1.6, 0.4 hours | `ops/operator-log-d06-d10.csv` | Day 9: the failure in row 11. Week one logged only as a total (3.5 hours) | None; contradicted on day 9 |
| 11 | The nightly run serves each day unaided | Nobody; design assumption | Nightly runs, days 6 to 10 | 4 of 5: on day 9 the resolver failed and day 8's rate was shown at 08:00, labelled stale | `esc/day09.md`; runs `r-8814` to `r-8817` | Cause not established | The cause (integration specialist) |

### Reading the ledger

Row 4 is not edited: row 12 (day 8, not shown) records the platform replay and supersedes it. Row 5 is an untested claim nobody made, kept so the readout cannot omit it. Row 6 turns on a definition: day 10 was 71 minutes from arrival but 34 from approval, so where the clock starts decides freshness. Rows 7 and 10 closed as contradicted: a result, not a gap. Row 9 is an assumption that lived in code until a quarantine made it visible.

### Open gaps by the decision they block

Freshness waits for row 6's clock (operations director). Real data beyond the approved sample waits for row 5's inputs (DBA) and a specialist review. Acceptance of day 5 waits for row 9 (quality lead). Row 11 blocks nothing yet; a repeat would (integration specialist).

### What the ledger says at this point

One criterion failed (operation, on the failure day), one cannot be judged (freshness), one prerequisite has not started and one assumption awaits an answer.

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
