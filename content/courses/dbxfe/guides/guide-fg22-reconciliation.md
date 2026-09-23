<!-- section:action -->

Reconciliation is a comparison of two paths on one basis. Most reconciliation failures are basis failures, so fix the basis before you compare anything.

1. **Align the basis.** Same population, same time window, same business-day boundary rule and time zone, same version of corrections and the same as-of moment. Write down any difference you cannot remove; it becomes an expected difference, not a surprise.
2. **Compare keys first.** Keys only in the old path, only in the new path, and in both. For keys in both, compare field values with the null rule stated: is null equal to null, and is null equal to empty string.
3. **Then compare totals** by grain (plant and day, for example), and require every total difference to be explained by keyed differences you already listed. A matching total with keyed differences is a failure, not a pass.
4. **Count nulls per column** on both sides and list null-to-value and value-to-null changes separately.
5. **Handle time explicitly:** late arrivals, corrections after the cutoff, and rows that move between days when the boundary rule differs.
6. **State thresholds before the run:** exact for keys and integer sums, a stated tolerance for floating values and rounded rates, and accepted exceptions named with reason and owner.
7. **Record results, exceptions, unexplained residue and the decision.**

Evidence to collect: the basis statement, the key comparison counts, the field-level difference list, the totals table with explanations, the null counts, the exception register and the decision.

Deeper: [SQL Server and on-premises modernization](#/module/dbxfe-sqlserver) for source semantics that change meaning, [Warehouse and distributed-platform migrations](#/module/dbxfe-warehouse-migration) for the reconciliation matrix, and the retained lessons [Migrate with reconciliation and rollback](#/lesson/dbxfe-m08-l03) and [Orchestration, failure, and reconciliation](#/lesson/dbxfe-m04-l03).

<!-- section:example -->

**Fictional worked example: Cinderline plant one, five reporting days.** The old path is `rpt_quality_daily` from the nightly stored procedure; the new path is the `accepted_inspections` table on the platform, aggregated to plant and day. The metric is defective units divided by inspected units.

### Basis statement

Population: plant one inspections with an inspection date in the five days. Boundary: both paths use 06:00 plant local time; the old path was found to apply 06:00 server time, so for this comparison the old output was re-cut from its detail rows using plant time. That re-cut is itself recorded. Corrections: the same approved CSV batch was loaded on both sides before the comparison. As-of: both snapshots taken after the batch load, before any later delivery. Null rule: null equals null; empty string is not null and is listed as a difference.

### Key comparison

| Day | Only in old | Only in new | In both | Field differences among "both" |
|---|---|---|---|---|
| 1 | 0 | 0 | 398 | 0 |
| 2 | 0 | 0 | 405 | 0 |
| 3 | 0 | 2 | 412 | 0 |
| 4 | 0 | 0 | 396 | 7 (inspector code) |
| 5 | 5 | 5 | 401 | 0 |

### Totals and explanations

| Day | Old inspected / defective | New inspected / defective | Explained by |
|---|---|---|---|
| 1 | 398 / 16 | 398 / 16 | Equal; no keyed differences. |
| 2 | 405 / 21 | 405 / 21 | Equal; no keyed differences. |
| 3 | 412 / 19 | 414 / 19 | Two late-arriving inspections (new keys) reached the new snapshot, taken after a later delivery, but not the old job: the as-of rule was violated. Rerun needed. |
| 4 | 396 / 17 | 396 / 17 | Totals equal; seven rows have a null inspector code in old and a value in new, backfilled from the CSV. |
| 5 | 406 / 18 | 406 / 18 | Totals equal; five keys differ. Not accepted. |

Day 5 is the case the plan exists for. Totals and rate match, yet five keys are only in old and five only in new. Tracing them: the five only in old are copies from a batch delivered twice, each copy's key carrying a trailing space and no revision; the old path deduplicated on the raw key and counted them, while the new path trimmed the key and quarantined the null-revision copies. The five only in new are legitimate rows the old path loses in its collation-sensitive join on inspector code. Two defects, both in the old path, whose two groups of five happened to carry the same units, so they cancelled in the total; the totals table alone would have accepted the day.

### Nulls

Inspector code: old 7 nulls, new 0 (day 4, backfill accepted by the quality lead, Imani, on day 4 as an improvement, recorded as an exception with her name and the date). Revision: old 5 nulls (the re-delivered copies), new 0 because those rows were quarantined; whether a null revision means "first version" or "unknown" is now a question for the quality lead, not a code fix, and the answer must be written into the resolver either way.

### Thresholds (fixed in the plan before the run)

Keys exact; inspected and defective sums exact; the rate compared after rounding to two decimal places with zero tolerance because the inputs are integers. No tolerance was needed and none was invented.

### Decision

Not accepted. Day 3 is a basis error and is rerun under the as-of rule. Day 5 has three open items: the old path's trailing-space duplicates and its collation-sensitive join (DBA, fix in the old path or document both as known differences) and the null-revision meaning (quality lead). Day 4 passes with one named exception. The comparison is repeated over five clean days after the open items close; the previously passing days are not carried forward as credit.

<!-- section:template -->

### Basis statement

- **Population** (which entities, which plant or unit), **time window and boundary rule** (cutoff time and time zone on each side), **corrections version** (which batches loaded on each side), **as-of moment** (both snapshots taken after the same event), **null rule** (null equals null? empty string?), **known basis differences you could not remove.**

### Key comparison

| Grain (e.g. day) | Only in old | Only in new | In both | Field differences among "both" |
|---|---|---|---|---|
| | Count and a sample of keys | Count and a sample of keys | Count | Count per field |

### Totals

| Grain | Old measures | New measures | Difference | Explained by (keyed differences listed above) |
|---|---|---|---|---|

- **Rule:** every difference in a total must be traceable to listed keyed differences; a matching total with keyed differences is a failure.

### Nulls

| Column | Old null count | New null count | Null-to-value | Value-to-null | Meaning decided by |
|---|---|---|---|---|---|

### Time

- **Late arrivals, rows moving between days, corrections after cutoff, and the rule applied to each.**

### Thresholds (stated before the run)

- **Keys:** exact. **Integer sums:** exact. **Floating values and rates:** the tolerance and the rounding rule, with the reason. **Accepted exceptions:** each with the reason, the person who accepted it and the date.

### Results and decision

- **Pass / fail per grain, open items with owners, and whether passing days are re-run after fixes** (they should be).

<!-- section:limits -->

Reconciliation establishes that two paths agree on the population, window and rules you stated, at the moment you compared them. It cannot establish that either path is correct: two paths can share a wrong definition and reconcile perfectly, which is why the metric contract and the source semantics are checked separately. A tolerance is a decision, and it should exist only where inputs are genuinely non-integer. Exceptions accepted by a named person are evidence; exceptions accepted by the comparison script are not. Escalate when a totals match hides keyed differences, when the meaning of a null or a boundary is a business question nobody has answered, or when fixing a difference would require changing the old path that users still rely on.
