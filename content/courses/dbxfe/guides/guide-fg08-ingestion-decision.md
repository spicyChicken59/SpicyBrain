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

**Inspections** live in the ERP on SQL Server. Each row has an inspection identifier that persists through corrections and a source revision number. The DBA has confirmed a nightly export job already exists for the plant sheet; whether change capture or change tracking is enabled or would be permitted is unknown, as are the version and topology.

**Corrections** arrive as CSV exports after periodic approval by the quality lead, typically once a day and sometimes not for several days. Each row carries the inspection identifier, the new revision and the full replacement quantities. The quality lead owns approval; nobody owns the file drop after that.

**Sensor events** are out of the pilot's scope.

#### Freshness needed versus offered

Needed: the accepted rate for the previous business day, available before 7:30 a.m. Offered: inspections by the existing nightly export, completing before 6:00 a.m. by the DBA's account (not measured); corrections whenever approved, which may be after the morning report. The gap is not technical: a correction approved at 10:00 a.m. for yesterday cannot appear in a 7:30 report by any pattern. The requirements contract's restatement rule handles it, and the operations director has accepted that the number may be restated later in the day.

#### Replay

Inspections: the ERP retains rows indefinitely and the export can be re-run for a date range by the DBA, so a failed night can be replayed from source, at the cost of the DBA's time. Corrections: an overwritten CSV is gone; the quality lead keeps no archive. Every correction file is therefore copied to retained raw storage on arrival, named by arrival time, before anything reads it.

#### Owners

Source export: the DBA, who has not agreed to be called at 6:00 a.m. Correction files: unowned after approval; proposed owner is the quality lead's team, to be agreed. Ingestion: the data team, with an operator still unnamed.

#### Patterns compared

| Pattern | What it needs granted | What it misses | Cost to the source | Fit |
|---|---|---|---|---|
| Nightly full snapshot of the plant's inspections | Read on the export or the tables | Nothing for a daily report; carries every row every night | One export per night, already running | Fits the pilot volume; wasteful at three plants |
| Incremental by revision watermark | Read plus a reliable revision column | Rows whose revision is not updated on change; deletes | Small | Depends on a column nobody has validated |
| Change capture from SQL Server | Enabling capture, log access, a permission the DBA has not granted | Nothing, if configured; deletes appear as deletes | Log retention, DBA operations | Answers a freshness need that does not exist yet |
| File drop with incremental file discovery | Storage path and a landing convention | Files that are overwritten in place before discovery | None | The right shape for corrections; needs an owner for the drop |
| Managed connector to SQL Server | Verified support for this version and the customer's network path | Unknown until support is confirmed | Depends | Not choosable until version and path are known |

#### Decision

Inspections by the existing nightly full export for the pilot, landed as files with retained raw copies. Corrections by file drop into a landing path with incremental discovery, retained on arrival, applied by revision order in the nightly job. Change capture is not chosen: it needs a permission the DBA has not granted and answers a need nobody has established.

#### Conditions and what would change this

If the DBA measures the export finishing after 6:30 a.m., the pattern holds but the job schedule moves and the 7:30 target is at risk. If the revision column is validated as reliable, the incremental watermark replaces the full snapshot when the second plant joins. If operations shows that morning-approved corrections must appear the same morning, change capture is re-examined with the DBA. If nobody owns the correction drop, corrections are not ingested and the pilot reports inspections only, saying so.

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

This decision records what the source owner has confirmed the source can do and chooses a pattern that fits it; it cannot establish connector support for a specific source version and network path, which needs current documentation and a test, nor the reliability of a revision column nobody has validated. It does not define how records are resolved once ingested; that is the change-data contract. Owners named here have not agreed until they say so. A pattern that fits one plant's volume is not evidence for three. Escalate when the source owner will not grant a permission the chosen pattern needs, when a source cannot be re-read and no retained copy exists, or when the freshness the decision needs cannot be offered by any pattern the source supports.
