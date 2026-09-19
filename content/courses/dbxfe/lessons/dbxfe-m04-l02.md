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
