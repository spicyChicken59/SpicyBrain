<!-- section:dbxfe-pipelines-l01-outcome -->

After this lesson you can read a declarative pipeline as a graph of datasets and flows, say which tables are updated incrementally and which are recomputed, choose an expectation's action knowing what it does to a bad row, and derive SCD type 1 and type 2 tables from change events, including late, tied and unplaceable ones. You can also say which of these features a given Apache Spark release ships and which are Databricks Lakeflow extensions. Every table here comes from lab L07, run on local Apache Spark 4.0.4; nothing ran on Databricks.

<!-- section:dbxfe-pipelines-l01-start -->

Bring two results from the ingestion module. From [duplicates, invalid records and conflicts](#/lesson/dbxfe-record-resolution): deliveries are classified before any state is published, and nobody picks an arbitrary winner. From [version-aware updates and replay](#/lesson/dbxfe-versioned-updates): a newer version replaces an older one only under an explicit guard. This lesson does not repeat either; it asks what a pipeline declaration does with them. The streaming module's checkpoints and micro-batches explain why a streaming table reads only new input.

<!-- section:dbxfe-pipelines-l01-graph -->

A declarative pipeline is a set of dataset definitions. Each creates a **dataset** that stores rows and a **flow** that reads a source, applies the query and writes into it. A **streaming table** can take several streaming flows, one per plant; a **materialized view** always has exactly one batch flow; a temporary view lives for one run. You never order the updates: the pipeline works out which datasets each query reads, builds a **dependency graph** and runs independent branches side by side. A query that reads its own downstream result creates a cycle, and `spark-pipelines dry-run` reports it without reading or writing data. Definition code runs more than once during planning, so it only returns a DataFrame.

<!-- section:dbxfe-pipelines-l01-refresh -->

A streaming table is **incremental**: its flows keep checkpoints, so each update reads only new input and never revisits written rows. Change its query and only new rows get the new logic. In open-source Spark 4.1.0 a materialized view is truncated and rebuilt on every update, so it reflects every correction upstream; Databricks documents incremental refresh where its engine can do it. A **full refresh** (`spark-pipelines run --full-refresh part_events`) clears a table and its checkpoints and rereads the sources. It rebuilds only what they still hold: a landing zone that keeps 30 days cannot return day 1.

<!-- section:dbxfe-pipelines-l01-expectations -->

An **expectation** attaches a Boolean rule and an action to a dataset. On Databricks, warn (the default) writes a failing row and counts it, drop removes it and counts it, and fail stops the update. Not executed here:

```sql
CREATE OR REFRESH STREAMING TABLE part_events_valid (
  CONSTRAINT known_op EXPECT (op IN ('upsert', 'delete')) ON VIOLATION DROP ROW,
  CONSTRAINT has_part EXPECT (part_id IS NOT NULL AND trim(part_id) <> '') ON VIOLATION FAIL UPDATE
) AS SELECT * FROM STREAM(part_events);
```

A rule sees one row and cannot query other tables. So dropping is not neutral (drop e-09 and P-400's older price stays current), and no rule sees a tie: e-08 and e-15 are each valid; only a grouped check finds that they disagree.

<!-- section:dbxfe-pipelines-l01-scd -->

A **type 1** table keeps one row per key: the change with the highest **sequence** value, or no row if that change is a delete. A **type 2** table keeps every version with `valid_from` (its sequence) and `valid_to` (the next change's sequence, open while current); a delete closes the open row and opens none. Cinderline after three batches:

| Part | From | To | Cost | Current |
|---|---|---|---|---|
| P-100 | 1 | 2 | 1250 | no |
| P-100 | 2 | 3 | 1290 | no |
| P-100 | 3 | open | 1310 | yes |
| P-200 | 1 | 2 | 400 | no |
| P-200 | 3 | open | 420 | yes |

Per key, at most one row is open and no intervals overlap. `valid_to` is `LEAD(seq) OVER (PARTITION BY part_id ORDER BY seq)`, computed before delete rows are filtered out.

<!-- section:dbxfe-pipelines-l01-sequence -->

A **late** change: P-100's seq 2 arrives after seq 3. The current row stays, but history shortens a closed version and inserts one; an append-only history writes a row from 3 to 2. A **tie**: e-08 and e-15 give P-300 two costs at seq 2. Arrival order is not evidence, so the reference withholds P-300; Marlow's source assigns `revision_no`, so ordering by (seq, revision_no) resolves its tie. An **unplaceable** change: e-09's sequence is the string "2". It might be P-400's latest state, so the reference quarantines it and withholds P-400.

<!-- section:dbxfe-pipelines-l01-autocdc -->

On Databricks an **AUTO CDC** flow (formerly APPLY CHANGES) declares what lab L07 computes. Not executed here:

```sql
CREATE FLOW part_history_cdc AS AUTO CDC INTO part_history
FROM STREAM(part_events_valid)
KEYS (part_id)
APPLY AS DELETE WHEN op = 'delete'
SEQUENCE BY seq
COLUMNS * EXCEPT (op, seq, event_id, batch)
STORED AS SCD TYPE 2;
```

It handles out-of-order changes and names history columns `__START_AT` and `__END_AT`, but expects one distinct update per key per sequence value and no NULL sequences, so validation and tie policy stay upstream. When a source sends only full **snapshots**, comparing consecutive ones yields upserts and deletes (AUTO CDC FROM SNAPSHOT automates it). A change that reverts between snapshots is invisible: skip snapshot 2 and SUP-B's 9-day lead time never happened.

<!-- section:dbxfe-pipelines-l01-editions -->

Name the release before the feature. **Apache Spark Declarative Pipelines** ships in open-source Spark from 4.1.0: flows, streaming tables, materialized views, temporary views, sinks, `pyspark.pipelines` and `spark-pipelines`. It is absent from 4.0.4, the lab's engine, where `pyspark.pipelines` does not import. At the 4.2.0 tag the Python API adds `create_auto_cdc_flow`, which stores SCD type 1 only. Expectations, AUTO CDC type 2 and snapshot CDC are documented for **Lakeflow** pipelines on Databricks (formerly Delta Live Tables) and are absent from the open-source APIs checked. So the lab implements the semantics with DataFrame windows, and the platform version is an adaptation you verify on a workspace.

<!-- section:dbxfe-pipelines-l01-example -->

Cinderline's 18 change events arrive in three batches. The lab's reference reports:

| Evidence | Value |
|---|---|
| Raw rows / distinct deliveries | 18 / 17 (e-05 redelivered) |
| Quarantined | e-09, e-12, e-17 |
| Withheld | P-300 (tie), P-400 (unplaceable) |
| Excluded | P-700 (only a quarantined event) |
| Current | P-100 1310, P-200 420, P-500 150, P-600 SUP-D |

From batch 2 to batch 3, current loses P-300 and gains P-200; history loses three rows and gains three. Replaying batch 3 changes nothing. Dropping the quarantined rows first publishes P-400 at 90 and leaves no trace of P-700. Each is a test in lab L07, compared with literals written by hand.

<!-- section:dbxfe-pipelines-l01-exercise -->

Marlow, a fictional retailer, sends customer tier changes with `seq` and `revision_no`. C-1: seq 1 bronze; seq 2 revision 1 silver; seq 2 revision 2 gold, delivered twice under two event ids. C-2: seq 1 silver, seq 2 delete, seq 3 silver with a new postcode. C-3: one event with seq 0. Predict the current and history tables when ordering by (seq, revision_no) and when ordering by seq alone, and give the reason for every withheld or excluded customer.

<!-- section:dbxfe-pipelines-l01-solution -->

By (seq, revision_no): C-1 has three versions, bronze from (1,1) to (2,1), silver from (2,1) to (2,2) and gold from (2,2), current; the second gold delivery is redundant evidence. C-2 runs from (1,1) to its delete at (2,1) and returns at (3,1) with the new postcode. C-3 is excluded: seq 0 is not a valid sequence and it has no other event. By seq alone, C-1's deliveries at seq 2 carry two payloads, a tie, so C-1 is withheld from both tables and only C-2 is published. Same data; the contract decides.

<!-- section:dbxfe-pipelines-l01-mistakes -->

- Letting arrival order pick the current row: the late P-100 change would win with an older price.
- Appending history rows as changes arrive: a late change yields an interval that ends before it starts.
- Dropping unplaceable changes and calling the table clean: the older state is published as current.
- Filtering tied or unplaceable rows out of an incremental SCD flow's input and calling the key withheld: a key the flow already applied stays published until a table recomputed each update takes it out.
- Breaking ties by ingestion time or event id: both describe delivery, not business order.
- Fully refreshing a streaming table whose source has lost its early history.
- Promising expectations or AUTO CDC type 2 on open-source Spark without naming a release.

<!-- section:dbxfe-pipelines-l01-sources -->

Apache Spark behaviour comes from the [Spark Declarative Pipelines Programming Guide](https://spark.apache.org/docs/4.1.0/declarative-pipelines-programming-guide.html) and the pipelines source code at the v4.1.0 and v4.2.0 tags, read through their source files because the rendered site could not be fetched. Databricks behaviour comes from its [AUTO CDC](https://docs.databricks.com/aws/en/ldp/cdc), [expectations](https://docs.databricks.com/aws/en/ldp/expectations) and [pipelines overview](https://docs.databricks.com/aws/en/ldp/) pages, whose bodies could not be fetched in this build: verify argument names there. All tables come from lab L07's recorded local run; no AUTO CDC declaration was executed.

<!-- section:dbxfe-pipelines-l01-related -->

[Ingestion, records and reliable updates](#/module/dbxfe-m04) owns record resolution; this lesson assumes it. [Delta Lake: files, log and snapshots](#/module/dbxfe-delta) explains the table versions a streaming source reads. [Orchestration and operations](#/module/dbxfe-orchestration) covers what runs a pipeline and what to do when an update fails. The streaming module explains checkpoints; the data-modeling module joins facts to a type 2 dimension as of a date.

<!-- section:dbxfe-pipelines-l01-revisit -->

Come back with three questions. If e-15 had carried the same cost as e-08, what would change for P-300? If Marlow stopped sending `revision_no`, which customer would leave the tables, and why? If supplier snapshots moved from daily to weekly, which history rows would you expect to lose? Then add a fourth batch to lab L07 and write its expected rows by hand before running anything.
