<!-- section:dbxfe-m04-l02-foundation-start -->

[Delta snapshots](#/lesson/dbxfe-m03-l02) explains table commits, while [SQL/PySpark transformation](#/lesson/dbxfe-m04-l01) explains accepted-grain aggregation. Now decide which source records may become that accepted input. A database transaction version and a source business revision are different sequences.

<!-- section:dbxfe-m04-l02-foundation-contract -->

Each delivery has event_id, inspection_id, version, inspected_units and defective_units. event_id identifies an immutable delivered payload. inspection_id is the business key, identifying one inspection across corrections. A positive integer version orders complete replacement states for that inspection; version 3 replaces version 2, rather than adding a quantity delta. Revisions are comparable within a key only. Arrival position/time records transport observation and never breaks a revision tie. A later arrival can contain an older source revision.

Identical deliveries can repeat. Different event IDs may also describe the same key/version/payload; they are redundant business evidence, not separate inspections. The same event ID with different payloads is a conflict. The same key/version with different quantities is also a conflict even if event IDs differ. Missing identity or invalid/missing version cannot be repaired by arrival order. The resolver retains evidence and makes uncertainty visible.

This is an original teaching contract, not the contract of a verified database connector. Batch means a bounded input set. Incremental describes processing changes relative to prior progress. CDC represents source changes, with supported operations and ordering depending on the actual source/connector. A toy JSON batch proves none of those integration capabilities. Our local reference recomputes from all retained synthetic history so cross-batch conflicts remain visible; it is not a scalable production streaming design.

<!-- section:dbxfe-m04-l02-foundation-example -->

| Arrival | event_id | inspection_id | version | inspected_units | defective_units |
|---|---|---|---|---|---|
| 1 | ev1 | A | 1 | 10 | 1 |
| 2 | ev1 | A | 1 | 10 | 1 |
| 3 | ev2 | B | 1 | -3 | 1 |
| 4 | ev3 | A | 2 | 12 | 1 |
| 5 | ev4 | C | 1 | 8 | 0 |

Five deliveries contain four distinct event payloads. ev1 repeats identically; it is retained as delivery evidence but counted once during business resolution. B has impossible quantities and is quarantined. A's revision 1 is superseded by revision 2. Accepted current rows are A v2 12/1 and C v1 8/0, totaling 20/1 and a 5% unit defect rate. This accepted-only rate explicitly excludes B; it is not complete source coverage.

Add an identical ev1 tomorrow: business state stays the same. Add a new event for A v1 = 10/1 tomorrow: A v2 remains newer under the source contract. Add ev5 for A v3 = 14/1: A becomes v3, totals become 22/1. None of these cases says anything about a new inspection's actual observation time; that is a separate field if the business needs it.

<!-- section:dbxfe-m04-l02-foundation-task -->

For each arrival after the baseline, state whether it is an identical delivery, redundant business evidence, older revision, correction, conflict or unresolved ordering: ev3/A/v2/12/1 again; ev8/A/v2/12/1; ev9/A/v1/10/1; ev5/A/v3/14/1; ev5/A/v3/15/1; ev6/A/no-version/16/1. Explain why a maximum arrival timestamp cannot solve the last two cases.

<!-- section:dbxfe-m04-l02-foundation-solution -->

The repeated ev3 is an identical delivery. ev8 supplies redundant equal-version business evidence. ev9 is older than accepted v2 and cannot replace it. ev5 v3 14/1 is a valid correction. A later differing ev5 conflicts by immutable event ID and key/version; preserve both payloads and block a new current report until adjudication. A record for known A without ordering is unresolved because you cannot place it relative to v3. The last received payload is not more authoritative just because transport delivered it later.

The conservative authored policy blocks publication when identity conflicts are unresolved, including conflicts discovered across batches or on an older revision. This keeps provenance uncertainty visible instead of inventing an adjudication rule. A source owner would need to establish a separate, recorded resolution policy; the toy implementation does not silently clear such evidence.

<!-- section:dbxfe-m04-l02-foundation-limits -->

Adding 14 to the prior 12 treats a replacement state as a delta and double-counts. A timestamp watermark can indicate ingestion progress without proving business order or complete source coverage. Absence from a later incremental batch is not a deletion instruction. A source revision field deserves validation and an owner, not an assumption based on its name.

<!-- section:dbxfe-m04-l02-foundation-links -->

[Duplicates, invalid records and conflicts](#/lesson/dbxfe-record-resolution) makes the policy executable. [Version-aware updates](#/lesson/dbxfe-versioned-updates) explains a guarded target update. The preserved original introduction and assessment remain below; they are useful historical material, while this deeper contract makes exceptional cases explicit.

<!-- section:dbxfe-m04-l02-foundation-sources -->

Primary documentation was read on 19 September 2026. Open Sources below for exact publishers, cloud/runtime context and limitations. Official mechanisms, original professional guidance and fictional records are distinct. These examples do not establish a Databricks execution, production performance, configured permissions or complete source coverage. The optional downloadable bundle provides setup, input files, independent expected outputs, starter tasks and complete solutions. The bundle's execution.json records its latest local run, with no failures or skips, using Python 3.12.14, Apache Spark 4.0.4 and Java 17.0.20.1+1; it covers the displayed Python/SQL examples and changed input cases. The bundle includes exact fixture/output hashes and execution evidence. These results do not include Delta or Databricks execution; the reader itself does not execute code.

<!-- section:why -->

A feed arrives twice, and an old inspection is corrected after today's report. Learn why “incremental” is a data contract, not just a faster schedule.

<!-- section:understand -->

**Batch** processes a bounded set of records; **streaming** processes an ongoing flow. **Incremental** processing handles changes since some position rather than rebuilding all history. **Change data capture**, or CDC, represents source changes such as inserts, updates, and deletes. A timestamp filter alone may miss deletes or late corrections.

Define identity, ordering, and replay before choosing the tool. A stable business key identifies the inspection; a source revision or sequence can order its changes; an event ID can identify a repeated delivery. Arrival time is not automatically the business order. Ask what happens when two records have the same key and revision but disagree.

For fictional Cinderline, keep raw deliveries available for investigation, select the agreed latest revision, quarantine invalid records, then calculate the report. Lakeflow Connect offers ingestion options, but exact source support and privileges still need checking. Faster processing is useful only if the business needs it and the team can operate it.

<!-- section:see -->

**Synthetic correction stream; order shown is arrival order.**

| event_id | inspection_id | version | inspected | defective |
|---|---|---|---|---|
| ev1 | A | 1 | 10 | 1 |
| ev1 | A | 1 | 10 | 1 |
| ev2 | B | 1 | -3 | 1 |
| ev3 | A | 2 | 12 | 1 |
| ev4 | C | 1 | 8 | 0 |

Expected latest valid inspections: A version 2 = 12/1 and C version 1 = 8/0. B is quarantined for a negative quantity. The repeated ev1 does not create a second inspection. One older A revision is superseded. The resulting rate is 1 ÷ 20 = 5%. The diagram shows why raw retention and a replay path matter.

<!-- section:deeper -->

Delta MERGE supports insert/update/delete patterns, but it does not invent a conflict-resolution rule. Deduplicate and resolve source ordering before an upsert; ambiguous multiple matches require attention, and detailed semantics depend on runtime. A source checkpoint tracks processing position, not proof that every downstream business effect happened exactly once. Treat external notifications or writes as separate idempotency boundaries.

<!-- section:customer -->

For a data engineer: “We need an inspection key, a correction sequence, and an agreed replay rule. Then we can compare permitted CDC with scheduled extraction. The success test includes duplicates, late corrections, and invalid records—not just the happy path.”

<!-- section:try -->

Process the synthetic five-row input by hand. Name the two accepted inspections, the quarantined record, and the final totals. Explain why using the greatest arrival timestamp instead of the version number could fail on a delayed correction.

<!-- section:revisit -->

Accepted output is A at version 2 with 12 inspected and 1 defective unit, plus C at version 1 with 8 and 0. B remains available for investigation with a negative-quantity reason. The aggregate is 20 inspected and 1 defective unit. A repeated identical ev1 is redundant; the old A version is superseded, not counted again.

If an older revision arrives after a newer one, arrival ordering can overwrite the intended latest state. Use source ordering only after validating its semantics. If equal key/version records disagree, quarantine or escalate the conflict under an agreed policy; do not invent a winner.
