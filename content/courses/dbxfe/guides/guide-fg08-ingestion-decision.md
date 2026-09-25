<!-- section:action -->

Decide how records enter the platform from what the source can actually do, not from what the target could accept. Ask the source owner, then write the decision; do not write the decision and then look for a connector.

1. **Establish source capability with the owner**: can it expose changes (change capture, change tracking, a revision column), only a full snapshot, or only a periodic file? Which version, which permissions, and who grants them?
2. **State the freshness the decision needs**, with its clock, from the requirements contract; then state the freshness the source can offer. Where they differ, the gap is a business conversation, not a tooling one.
3. **Define replay**: from what position can you re-read after a failure, for how long does the source keep history, and does re-reading produce the same records? A source that cannot be re-read needs retained raw copies on arrival.
4. **Name the owners on both sides**: who operates the source export or capture, who operates the ingestion, who is called when either fails.
5. **Compare the patterns in the same terms**: full snapshot on a schedule, incremental by watermark, change capture, file drop with incremental file discovery, managed connector. For each, what it misses (deletes, late corrections), what it costs the source, and what it needs granted.
6. **Choose with conditions** and record the evidence that would change the choice.

Go deeper: [ingestion, quality and changing records](#/module/dbxfe-m04), [identity, ordering and incremental inputs](#/lesson/dbxfe-m04-l02), [Structured Streaming and recovery](#/module/dbxfe-streaming) for continuous sources, and [SQL Server modernization](#/module/dbxfe-sqlserver) for what an on-premises source can expose.

<!-- section:example -->

### Ingestion decision: Cinderline Components (fictional), North plant inspections and corrections

Status: proposed, conditional on the DBA's answers.

#### Sources

**Inspections** live in the ERP on SQL Server. Each row has an inspection identifier that persists through corrections; rows are updated in place, carry no revision and keep no visible history. The DBA confirms a nightly export already exists for the plant sheet; whether change capture or change tracking is enabled or permitted is unknown, as are the version and topology.

**Corrections** never touch the ERP. They arrive as CSV files on a file share after the quality lead's approval, on Fridays and ad hoc for urgent cases. Each row carries the inspection identifier, a source revision that supersedes lower ones, and the complete replacement quantities. The quality lead owns approval; nobody owns the file drop after that.

**Sensor events** are out of the pilot's scope.

#### Freshness needed versus offered

Needed: the accepted rate for the previous business day, available before 7:30 a.m. Offered: inspections by the existing nightly export, completing before 6:00 a.m. by the DBA's account (not measured); corrections when approved, which may be after the morning report. The gap is not technical: an urgent correction approved at 10:00 a.m. for yesterday cannot reach a 7:30 report by any pattern. Under the contract's restatement rule the day is restated on the next nightly run, and marked; the operations director has accepted that.

#### Replay

Inspections: the DBA can re-run the export for a date range, but rows are updated in place, so a re-run returns each inspection's current state, not what the failed night saw; the retained raw export is what replays a night. Corrections: an overwritten CSV is gone; the quality lead keeps no archive. Every export and correction file is copied to retained raw storage on arrival, named by arrival time, before anything reads it.

#### Owners

Source export: the DBA, who has not agreed to be called at 6:00 a.m. Correction files: unowned after approval; the quality lead's team is proposed, not agreed. Ingestion: the data team, with an operator still unnamed.

#### Patterns compared

| Pattern | What it needs granted | What it misses | Cost to the source | Fit |
|---|---|---|---|---|
| Nightly full snapshot | Read on the export or the tables | Nothing for a daily report; carries every row nightly | One nightly export, already running | Fits the pilot volume; wasteful at three plants |
| Incremental by modified-time watermark | Read plus a reliable modified-time column | Rows whose timestamp is not updated on change; deletes | Small | Needs a column nobody has validated |
| Change capture from SQL Server | Enabling capture and log access, which the DBA has not granted | The CSV corrections; changes past the capture retention; schema changes (check current documentation) | Log retention, DBA operations | Serves a freshness need nobody has established |
| File drop with incremental file discovery | Storage path and a landing convention | Files overwritten in place before discovery | None | Right for corrections; needs a drop owner |
| Managed connector to SQL Server | Change tracking or change data capture on the source tables (the same DBA permission); support for this version and network path, per current documentation | Unknown until confirmed | Depends | Not choosable until version and path are known |

#### Decision

Inspections by the existing nightly export, landed as files with retained raw copies. Corrections by file drop into a landing path with incremental discovery, retained on arrival, applied in revision order in the nightly job. Change capture is not chosen: it needs an ungranted permission, cannot carry the corrections, and answers a need nobody has established.

#### Conditions and what would change this

If the DBA measures the export finishing after 6:45 a.m., the 7:30 target is at risk. If a modified-time column is validated, the watermark replaces the full snapshot when the second plant joins. If operations shows that morning-approved corrections must appear the same morning, an intraday run over newly discovered correction files is examined. If nobody owns the correction drop, the pilot reports inspections only and says so.

<!-- section:template -->

### Ingestion decision

#### Sources

- For each source: system, owner, keys and ordering fields present, what it can expose (change capture, change tracking, revision column, snapshot, file), version and permissions, each marked confirmed or unknown.

#### Freshness needed versus offered

- The decision's requirement with its clock; what each source can offer; the gap and who owns resolving it.

#### Replay

- The position you can re-read from, how long the source keeps history, whether a re-read reproduces the same records, and what must be retained on arrival.

#### Owners

- Source-side operator, ingestion operator, escalation contact, each named or marked unowned.

#### Patterns compared

| Pattern | What it needs granted | What it misses (deletes, late corrections, overwritten files) | Cost to the source | Fit for this decision |
|---|---|---|---|---|

#### Decision

- The pattern per source, the conditions attached, and the pattern explicitly not chosen with the reason.

#### What would change this

- Observations that would switch the pattern, and the owner who would observe them.

<!-- section:limits -->

This decision records what the source owner has confirmed the source can do and chooses a pattern that fits it; it cannot establish connector support for a specific source version and network path, which needs current documentation and a test, nor the reliability of a change column nobody has validated. It does not define how records are resolved once ingested; that is the change-data contract. Owners named here have not agreed until they say so. A pattern that fits one plant's volume is not evidence for three. Escalate when the source owner will not grant a permission the chosen pattern needs, when a source cannot be re-read and no retained copy exists, or when the freshness the decision needs cannot be offered by any pattern the source supports.
