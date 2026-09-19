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
