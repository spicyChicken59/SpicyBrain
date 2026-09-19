<!-- section:dbxfe-m03-l02-foundation-start -->

Bring the distinction between storage and compute from [Workspace, storage and compute](#/lesson/dbxfe-workspace-compute). This deeper package retains the original responsibility explanation and its links below. A Delta table is more than a folder of independently readable data files: the table protocol tells a reader which committed state is visible.

<!-- section:dbxfe-m03-l02-foundation-mechanism -->

Delta combines data files with a transaction log. The log records committed changes used to reconstruct a table snapshot. A reader of a particular committed version uses that version's logical state, not every data file it happens to find in a directory. New writes can create new physical files and retire old ones from the current table without immediately erasing all old bytes. That distinction supports coherent reads while the table changes.

The following timeline is intentionally schematic. It uses invented filenames and simplified add/remove actions; it is not an actual transaction log format, full protocol implementation, or instruction to edit files. Modern features may represent some changes differently, including deletion vectors. Use supported table APIs rather than manually changing a real log, deleting files, or reducing retention because this picture looks simple.

<!-- section:dbxfe-m03-l02-foundation-example -->

At table version 0, file f0 contains A v1 = 10/1 and file f1 contains C v1 = 8/0. The visible rows total 18 inspected and 1 defective. A correction writes file f2 containing A v2 = 12/1. A successful commit creates version 1 whose logical changes retire f0 and add f2. File f1 remains active.

| Table snapshot | Active files in this schematic | Visible business rows | Total |
|---|---|---|---|
| Version 0 | f0, f1 | A v1 10/1; C v1 8/0 | 18/1 |
| Version 1 | f1, f2 | A v2 12/1; C v1 8/0 | 20/1 |

f0 may still physically exist because retention and cleanup are separate from logically retiring it. Reading every file as plain Parquet could count A twice: 10 + 12 + 8 = 30 inspected and 1 + 1 + 0 = 2 defective. It bypasses the snapshot meaning. Reading version 1 through the table layer returns only its logical rows. If writing f2 succeeds but the transaction never commits, the uncommitted file does not alone make a new table snapshot.

There are two versions here with different meanings. Table version 1 identifies a committed table state. A's business revision 2 identifies a source correction under Cinderline's contract. A table commit can contain many business keys/revisions; those numbers must not be compared as if they were the same sequence.

<!-- section:dbxfe-m03-l02-foundation-task -->

Starting at table version 1, a proposed commit retires f2 and adds f3 containing A v3 = 14/1. C remains in f1. Predict the table rows/totals after a successful commit, and after writing f3 but failing before commit. Explain why "the schema accepted an integer 1400" does not establish that 1400 inspected units are correct for the source inspection.

<!-- section:dbxfe-m03-l02-foundation-solution -->

A committed version 2 contains A v3 = 14/1 and C v1 = 8/0, totaling 22 inspected and 1 defective. If f3 is only written and no commit is accepted, readers of the last committed snapshot still see A v2 and C, totaling 20/1. The failed write needs supported recovery/cleanup procedures; this lesson authorizes no manual file deletion.

Schema checks establish compatibility with specified structural requirements, such as field types. The integer 1400 can satisfy the type yet reflect a wrong unit, wrong inspection or erroneous correction. Reconciliation against the source contract and business validations addresses that problem. A successful transaction preserves the chosen change atomically at the table boundary; it does not verify that every business assertion in the payload is true.

<!-- section:dbxfe-m03-l02-foundation-limits -->

Reader and writer protocol/features govern what clients must support. Before enabling a feature, identify every reader/writer and verify its documented compatibility. A current Databricks page does not certify an arbitrary external client. Historical reads depend on retained data/log and configured retention; do not promise unlimited time travel. Nothing here executes Delta, benchmarks concurrency or demonstrates Databricks transaction behavior. The original responsibility-model sections remain useful context below.

<!-- section:dbxfe-m03-l02-foundation-links -->

[Incremental identity and ordering](#/lesson/dbxfe-m04-l02) adds business revisions. [Version-aware updates](#/lesson/dbxfe-versioned-updates) applies resolved source state to a target. Sources distinguish the documented table mechanism from this original schematic.

<!-- section:dbxfe-m03-l02-foundation-sources -->

Primary documentation was read on 19 September 2026. Open Sources below for exact publishers, cloud/runtime context and limitations. Official mechanisms, original professional guidance and fictional records are distinct. These examples do not establish a Databricks execution, production performance, configured permissions or complete source coverage. The optional downloadable bundle provides setup, input files, independent expected outputs, starter tasks and complete solutions. The local acceptance run passed 30 tests with no failures or skips using Python 3.12.14, Apache Spark 4.0.4 and Java 17.0.20.1+1, including the complete displayed Python/SQL examples and changed input cases. The bundle includes exact fixture/output hashes and execution evidence. These results do not include Delta or Databricks execution; the reader itself does not execute code.

<!-- section:why -->

A customer sees data files in a bucket and asks why a table format or governance layer is needed. Explain the responsibilities separately so the diagram does not imply that one box solves every problem.

<!-- section:understand -->

**Storage** holds bytes. **Compute** performs work on them. A **table format** supplies rules and metadata for treating files as a changing table. **Governance** controls and records permitted use. A usable analytical system needs those responsibilities to cooperate.

Delta Lake extends Parquet files with a transaction log. That supports table-level transactional behavior; it does not make a wrong inspection count correct. Spark SQL and DataFrame APIs provide ways to express structured transformations. They are interfaces to computation, not substitutes for the data's meaning.

In fictional Cinderline, two teams may write quality updates while analysts query a stable table view. The design still needs a key for each inspection, a correction rule, and an agreed unit of measure. Putting ambiguous input into a transactional table preserves ambiguity more reliably; it does not remove it.

<!-- section:see -->

Read the schematic by responsibility. The source record `inspection A, version 2, accepted_units 12` is stored as data. The table layer determines which committed version a reader sees. Compute applies the correction and aggregation rules. Governance determines which principal may perform the operation.

**Counterexample:** a quantity of 12 entered in the wrong unit can pass schema validation and a transaction commit. Business validation must catch that mismatch. This is why “ACID” should never be explained as “all of your data becomes correct.”

<!-- section:deeper -->

A table feature can impose reader/writer protocol requirements. Before enabling or migrating a feature, inventory the clients that must continue reading and writing. The documented compatibility page is the starting check; do not assume every external engine supports every table feature. Transactions also do not make external side effects, such as sending a message or charging an account, automatically idempotent. Design those boundaries explicitly.

<!-- section:customer -->

For a technical architect: “The bucket stores the files, the table format coordinates table changes, compute transforms and queries the data, and governance controls access. We still need to agree the inspection key, correction rule, and permitted clients.”

<!-- section:try -->

Classify these fictional issues by the primary responsibility: a bucket policy denies access; two source rows conflict about inspection A; a query needs more processing capacity; an external reader cannot support an enabled table feature. Explain why the second issue needs business rules.

<!-- section:revisit -->

The bucket policy is a storage-access/identity configuration issue; conflicting inspection rows require source semantics and a correction rule; processing capacity is compute; unsupported table features are client/protocol compatibility. Real incidents can span several layers, so use these as starting hypotheses rather than exclusive categories.

For conflicting rows, ask which field establishes identity and which sequence establishes the intended correction. Selecting the latest arrival time is unjustified if a network delay reordered the events. Validate the rule with the source owner before writing an upsert.
