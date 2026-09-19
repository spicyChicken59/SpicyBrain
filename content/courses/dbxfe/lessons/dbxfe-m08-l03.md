<!-- section:why -->

A customer asks to switch reporting next Friday. Before agreeing, define how you will compare outputs, detect problems, and return to a usable state.

<!-- section:understand -->

A reversible migration changes one bounded slice while preserving a viable fallback. Inventory dependencies, define accepted behavior, rehearse the path, and keep the current system available until agreed exit criteria are met. A dual run compares old and new paths on the same population and time basis; it is useful only if their definitions are aligned.

Reconciliation checks more than row count. Compare keys, totals, time windows, duplicates, missing records, and known exceptions. A matching total can hide offsetting errors. For fictional Cinderline, compare plant/day totals and selected inspection histories, including late corrections.

A rollback plan states triggers, decision owner, steps, data consequences, and communication. “Restore the old dashboard” is insufficient if the old path stopped ingesting or users acted on a different data version. Decide how to handle changes made during the transition and how to avoid conflicting writes.

<!-- section:see -->

The schematic keeps current and target paths side by side during a bounded one-plant comparison. Reconciliation is a gate before cutover. If counts or approved metric semantics fail, the plan pauses and retains the current path.

**Fictional proposed cutover condition:** five agreed reporting days reconcile within explicitly accepted exceptions; the operating owner demonstrates alert handling and replay; security signs off access. These are authored criteria, not observed results. Rollback is triggered by an unapproved metric discrepancy or inability to serve the agreed report.

<!-- section:deeper -->

Decide whether this is read-path migration, write-path migration, or both. A reporting cutover may be simpler than transferring operational writes. Retain source and transformation version references so a discrepancy can be reproduced. Avoid destructive cleanup until the recovery window and ownership are agreed. Test restoration as an actual sequence with expected outputs; an untouched rollback document is not recovery evidence.

<!-- section:customer -->

For a delivery lead: “We propose one plant, parallel comparison, and a cutover only after agreed reconciliation and operating checks. We will keep the prior report usable during the recovery window and define who can pause or revert the switch.”

<!-- section:try -->

During a hypothetical dual run, total inspected units match but five inspection keys are missing and five unrelated keys appear instead. Decide whether to cut over, identify why the total misleads, and write the next action.

<!-- section:revisit -->

Do not cut over under a criterion requiring key-level reconciliation. Matching totals can conceal compensating errors; different populations can produce the same aggregate. Preserve both outputs and their input/version basis, assign the data engineer to trace key mapping and exclusions, and keep the existing report active. Re-run the agreed comparison after correction.

The action is proportional: the mismatch may be fixable without abandoning the target. The important habit is to preserve the gate and the fallback rather than relaxing the acceptance rule after seeing an inconvenient result.
