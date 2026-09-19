<!-- section:why -->

You are asked to sketch an architecture after a short call. A list of logos is insufficient. You need the path from source to decision, including identities, timing, and who fixes failures.

<!-- section:understand -->

A current-state inventory describes what happens today. Trace one important data product backward: the report, the transformation, the ingestion path, and the originating event. For each step ask about volume, frequency, keys, schema changes, access, sensitivity, failure handling, and owner.

Keep facts, reports, and assumptions separate. “SQL Server holds inspection records” may be confirmed. “CDC is permitted” is still an assumption until the source owner and security team validate it. A platform offering a database connector does not establish support for this version, topology, or network path.

Fictional Cinderline combines SQL Server inspection records with emailed quality CSV files. A late CSV correction can change yesterday's total after the report is published. Before drawing a streaming solution, discover whether corrections carry a stable inspection key and change sequence. The challenge may be interpretation and reconciliation, not raw transport speed.

<!-- section:see -->

**Fictional inventory excerpt.**

| Flow | Known | Unknown with owner |
|---|---|---|
| ERP inspections → nightly extract | SQL Server; batch file | Source version and CDC permissions: DBA |
| Quality CSV → analyst workbook | Manual corrections occur | Stable record key: quality lead |
| Sensor events → maintenance store | Separate event feed | Retention and event-time meaning: plant engineer |
| Workbook → morning meeting | Daily distribution | Accepted metric and cut-off: supervisor |

The useful output is the rightmost column. Each gap can change the target design.

<!-- section:deeper -->

Lakeflow Connect includes ingestion options, but its overview is only a starting point for connector selection. Inspect the specific connector's supported source version, initial-load behavior, CDC prerequisites, identity requirements, and limitations before making an implementation claim. Also ask whether the customer permits the required privileges. Support and permission are distinct. In this course we leave the exact Cinderline connector choice conditional because those inputs are deliberately incomplete.

<!-- section:customer -->

For a data lead: “Let us trace one inspection from the ERP to the meeting. I want to understand corrections, keys, and failure ownership as well as volume. Then we can compare a permitted incremental path with a simpler scheduled extract.”

<!-- section:try -->

A fictional architecture note says, “SQL Server to cloud in real time.” Rewrite it as a current-state statement plus four prioritized unknowns. Include one unknown that could make scheduled batch a better choice.

<!-- section:revisit -->

A better note: “Inspection records originate in SQL Server and currently reach a nightly file. We still need the DBA to confirm version/topology and allowed access, the quality lead to explain correction ordering, security to identify a permitted path, and operations to confirm the decision freshness required. If the only action occurs at the daily meeting, a reliable scheduled feed may meet the need with less operating complexity.”

This does not reject streaming. It delays a choice until the constraints make it defensible. Preserve who supplied each fact so later corrections can be traced.
