# Reconciliation fixture: August shipped quantity and value

All figures are fictional. Plants, shipment and revision identifiers, packaging
codes and prices are invented for this exercise; nothing here is a real
company's data.

## What the two files are

- `source-totals.csv` — the totals the current reporting paths produce for
  August 2026: Granite (`NB-DW-01`) for the two Northbrook plants and the Vale
  lakehouse (`VC-LH-01`) for Fennick. Extracted on 4 September.
- `target-totals.csv` — the same period from a *candidate* consolidated group
  table built during a trial load. Extracted on 2 September.

Both carry two metrics per plant: `shipped_quantity` and `shipped_value`.
Every row states its own `unit` and its own `as_of_utc`. Read those columns
before you compare anything.

## Your task

1. Compare the two files as a migration reconciliation would: per plant and
   per metric, not as a single group total.
2. State the size of every difference you find and its cause. There is more
   than one cause, and they interact.
3. Write the corrected consolidated totals per plant and for the group, in
   the group's declared unit.
4. Define the reconciliation gate you would apply during a parallel run so
   that the same mistakes cannot pass unnoticed.

Do the arithmetic yourself before reading the worked answer below.

## Worked answer (read after your attempt)

**The naive comparison.** Summing `value` for `shipped_quantity` in the source
file without looking at `unit` gives 48,320 + 31,175 + 9,940 = 89,435. The
target sums to 49,570 + 31,175 + 9,940 = 90,685. The difference is 1,250, which
looks like one clean cause. It is not; the naive sum has added cases to units.

**Cause one: a late revision.** The target was extracted on 2 September at
22:15 UTC. Revision `R-2026-08-117` was applied in Granite on 3 September and
reversed 1,250 units on shipment `SH-88213` at Ashcombe. The source, extracted
on 4 September, includes it (48,320); the target does not (49,570). The value
rows show the same revision as a credit of 62,500.00 USD (1,250 units at the
shipment's 50.00 USD unit price): source 2,416,000.00 against target
2,478,500.00.

**Cause two: a unit mismatch.** Fennick reports `shipped_quantity` in
`case`, and the Vale packaging master `PKG-STD-12` defines a case as 12 units.
The candidate loader copied 9,940 into a column declared in units. In the
group's unit, Fennick shipped 9,940 × 12 = 119,280 units. The target is under
by 109,340 for this plant. The value row is unaffected (506,940.00 in both
files) because value came from invoices, not from quantity × price — which is
the clue that the quantity, not the value, is wrong.

**Why the naive view misleads.** In units, the source group total is
48,320 + 31,175 + 119,280 = 198,775 and the target is 90,685: the target is
under by 108,090, which is 109,340 (unit mismatch) − 1,250 (late revision).
One error hides most of the other, and the value totals (source 4,481,690.00,
target 4,544,190.00, difference exactly 62,500.00) would tempt a reviewer to
conclude that the revision is the only problem.

**Corrected consolidated totals (units, as of 4 September):**

| plant | shipped_quantity (unit) | shipped_value (USD) |
|---|---:|---:|
| NB-ASH Ashcombe | 48,320 | 2,416,000.00 |
| NB-COR Corvane | 31,175 | 1,558,750.00 |
| VC-FEN Fennick | 119,280 | 506,940.00 |
| **Group** | **198,775** | **4,481,690.00** |

**The gate.** A parallel-run reconciliation that would have caught both:

- every row carries a declared unit, and conversion happens once, at a stated
  factor from a named master, before any total is formed;
- every total carries an as-of timestamp, and revisions applied after the
  earlier extract are listed by identifier and reconciled explicitly;
- comparison is key-level (plant and period, and shipment where available),
  never a group total; a matching group total is not a pass;
- accepted exceptions are named, owned and dated.

## Limits

This is a six-row teaching fixture, not a load test and not evidence of any
platform's behaviour. The unit price, the case size and the revision are
invented so the arithmetic is exact.
