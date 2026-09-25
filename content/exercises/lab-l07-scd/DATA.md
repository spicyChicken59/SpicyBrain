# Lab L07 data dictionary, source contract and derivations

All three fixtures are small, original and synthetic. They were typed by hand as
literal JSON; there is no generator and no random seed. Cinderline Components
(parts), Marlow (a fictional retailer's customers) and the suppliers named in
the snapshots are fictional. Every number in `expected/` is derived below by
hand from the fixtures and the contract; none was produced by the solution
under test.

## The source contract

A change table is only as good as the promises its source makes. The reference
implements this contract and nothing else:

| Promise | Cinderline parts | Marlow customers (transfer) | Supplier snapshots |
|---|---|---|---|
| Entity key | `part_id`, non-blank string | `customer_id`, non-blank string | `supplier_code` |
| Ordering | `seq`, a JSON integer 1..2147483647; higher is later | `seq` then `revision_no` (composite), or `seq` alone (narrow contract) | `snapshot_no` |
| Uniqueness | at most one distinct payload per (`part_id`, `seq`) | per (`customer_id`, `seq`, `revision_no`) | one row per supplier per snapshot |
| Operations | `upsert` carries every attribute; `delete` carries none | same | derived: appear or differ = upsert, disappear = delete |
| Delivery identity | `event_id`: one id is one immutable payload | same | derived ids `snap-<n>-<code>` |
| Arrival | `batch` is when a row arrived; it says nothing about order | same | — |

Attributes: `description` and `supplier_code` are non-blank strings,
`unit_cost_cents` an integer 0..2147483647; Marlow's `tier` and `postcode` are
non-blank strings; suppliers carry `name` (string) and `lead_days` (integer).

The reference's policy when the contract is broken, in the order it applies:

1. An event that fails a promise is **quarantined with every reason** and kept.
2. The same `event_id` delivered twice with identical content (the `batch`
   field aside) is **one delivery**; with different content it is a conflict.
3. Two deliveries at the same key and sequence value: identical payloads are
   **redundant evidence** (one state); different payloads are a **tie**.
4. A key with a tie, a conflict, or a quarantined event it cannot place is
   **withheld** from both tables and listed under `unresolved` with its reason.
   A key whose only events are quarantined is **excluded** and listed.
5. Type 1 (`current`): per key, the state with the highest sequence; if that
   state is a delete, the key has no current row.
6. Type 2 (`history`): per upsert state, a row with `valid_from` = its
   sequence and `valid_to` = the next state's sequence for the key (upsert or
   delete), or null; `is_current` = `valid_to` is null. Intervals are
   half-open, `[valid_from, valid_to)`. Sequences are written as lists (`[2]`
   or `[2, 1]`) so single and composite orderings read the same way.

Invariants the tests assert on every table: at most one current row per key;
per key, every closed interval ends after it starts, at most one open row and
it is the last, no overlaps. A gap between two intervals is legal only where a
delete closed a version; the tests compare the gaps with the literals.

## `fixtures/cinderline-events.json` (18 rows, arrival order)

| # | event | batch | part | seq | op | cost | supplier | note |
|---|---|---|---|---|---|---|---|---|
| 0 | e-01 | 1 | P-100 | 1 | upsert | 1250 | SUP-A | |
| 1 | e-02 | 1 | P-200 | 1 | upsert | 400 | SUP-B | |
| 2 | e-03 | 1 | P-300 | 1 | upsert | 800 | SUP-A | |
| 3 | e-04 | 1 | P-400 | 1 | upsert | 90 | SUP-D | |
| 4 | e-05 | 1 | P-500 | 1 | upsert | 150 | SUP-B | |
| 5 | e-06 | 2 | P-100 | 3 | upsert | 1310 | SUP-A | arrives before seq 2 |
| 6 | e-07 | 2 | P-200 | 2 | delete | — | — | |
| 7 | e-08 | 2 | P-300 | 2 | upsert | 830 | SUP-A | |
| 8 | e-09 | 2 | P-400 | "2" | upsert | 95 | SUP-D | seq is a string |
| 9 | e-05 | 2 | P-500 | 1 | upsert | 150 | SUP-B | identical redelivery |
| 10 | e-10 | 2 | P-600 | 1 | upsert | 2100 | SUP-C | |
| 11 | e-11 | 2 | P-600 | 2 | upsert | 2100 | SUP-D | supplier changes |
| 12 | e-12 | 2 | P-700 | 1 | modify | 60 | SUP-B | unknown op |
| 13 | e-13 | 3 | P-100 | 2 | upsert | 1290 | SUP-A | late arrival |
| 14 | e-14 | 3 | P-200 | 3 | upsert | 420 | SUP-C | returns after delete |
| 15 | e-15 | 3 | P-300 | 2 | upsert | 850 | SUP-A | ties with #7 |
| 16 | e-16 | 3 | P-500 | 1 | upsert | 150 | SUP-B | same state, new id |
| 17 | e-17 | 3 | "" | 1 | upsert | 10 | SUP-A | blank part |

Descriptions: P-100 "Bearing housing 40mm", P-200 "Gasket set", P-300 "Shaft
seal", P-400 "Retaining clip", P-500 "Spacer ring", P-600 "Cover plate", P-700
"Drain plug", and "Unknown part" on #17.

### Derivation, all three batches

- **Quarantine.** #8 `invalid_sequence` (a string is not an integer), #12
  `invalid_op`, #17 `missing_part_id`. Fifteen rows remain valid.
- **Deliveries.** `e-05` arrives at #4 and #9 with identical content, so
  `duplicate_deliveries` = e-05 at [4, 9]. Distinct deliveries count every
  arrival, quarantined ones included, minus identical repeats: 18 − 1 = **17**.
- **States.** Grouping the fourteen valid deliveries by (part, seq): P-100 at
  1, 2, 3; P-200 at 1, 2 (delete), 3; P-300 at 1, and at 2 twice with 830 and
  850 — a **tie**; P-400 at 1; P-500 at 1 twice with identical payloads (e-05,
  e-16) — **redundant evidence**; P-600 at 1, 2. Orderable states: 3 + 3 + 1 +
  1 + 1 + 2 = **11**.
- **Unresolved.** P-300 `tied_sequence` at [2], raw indices [7, 15], the two
  candidates ordered by their canonical JSON (830 before 850). P-400
  `invalid_sequence`, raw index [8]: e-09 names a key that has valid evidence
  but cannot be placed, so nobody can say whether it is the latest state.
  **Excluded**: P-700, whose only event is quarantined. #17 names no part, so
  it is quarantined and belongs to no key.
- **Type 1.** P-100 seq 3 (1310): the late seq 2 is lower and changes nothing
  current. P-200 seq 3 (420, SUP-C). P-500 seq 1. P-600 seq 2 (SUP-D). P-300
  and P-400 withheld. Four rows.
- **Type 2.** P-100: [1]→[2] 1250, [2]→[3] 1290, [3]→open 1310. P-200:
  [1]→[2] 400 (closed by the delete, which opens nothing), [3]→open 420.
  P-500: [1]→open. P-600: [1]→[2] SUP-C, [2]→open SUP-D. Eight rows; one gap,
  P-200 from [2] to [3].

### Derivation per stage

- **Through batch 1** (#0–#4): no quarantine, five states, five current rows at
  seq 1, five open history rows, no gaps. Raw 5, distinct 5.
- **Through batch 2** (#0–#12): quarantine #8 and #12; e-05 duplicate [4, 9];
  distinct 13 − 1 = 12; states: P-100 at 1 and 3, P-200 at 1 and 2 (delete),
  P-300 at 1 and 2, P-400 at 1, P-500 at 1, P-600 at 1 and 2 = **10**.
  Unresolved: P-400 only (P-300's seq 2 has one payload so far). Excluded:
  P-700. Current: P-100 seq 3, P-300 seq 2 (830), P-500, P-600 seq 2; P-200's
  latest state is its delete, so no row. History: P-100 [1]→[3] and [3]→open
  (seq 2 has not arrived), P-200 [1]→[2] only, P-300 [1]→[2] and [2]→open,
  P-500, P-600 two rows. No gap yet: P-200 has a single interval.

### What batch 3 changes (`batch3_changes`)

Comparing whole rows between the batch-2 tables and the final tables:
current loses P-300 (the tie withdraws it) and gains P-200 seq 3; history
loses P-100 [1]→[3], P-300 [1]→[2] and P-300 [2]→open, and gains P-100
[1]→[2], P-100 [2]→[3] and P-200 [3]→open. An incremental maintainer must
rewrite one closed row (P-100's first version now ends at 2), insert one row
between two existing ones, and withdraw a key it had published.

### Replay, drop filter and validator cases

- **Replay** (`replay_batch3`): #13–#17 appended again unchanged, 23 rows.
  Every replayed row is identical to its original, so distinct deliveries stay
  **17**; duplicates are e-05, e-13, e-14, e-15, e-16 (e-17 is quarantined, so
  it appears twice in quarantine, at 17 and 22, and not among the valid
  duplicates). Tables and unresolved keys are unchanged.
- **Drop filter** (`drop_filtered`): remove the three quarantined rows first,
  as a row rule that drops failures would. Fifteen rows remain; with e-09 gone,
  P-400 has one valid state and is published at seq 1 (90); P-700 vanishes
  without being excluded; the P-300 tie is still found because each of its two
  rows is valid on its own. Current: P-100, P-200, P-400, P-500, P-600.
- **Validator cases**: `true` as a sequence is a boolean, not an integer; `0`
  is not positive; a null sequence on a delete is still invalid; a blank
  description, a negative cost and a missing supplier give three reasons in
  attribute order; a well-formed delete carries no attributes and passes; an
  empty event id, a blank part and the op `insert` give three reasons, and no
  attribute check runs because the row is not an upsert.
- **Broken tables**: a second P-100 current row fails `duplicate_current_key`;
  moving P-100's first `valid_to` from [2] to [3] makes [1]→[3] overlap [2]→[3]
  (`overlap`, P-100); reopening P-600's first version leaves two open rows
  (`open_rows_per_key`, P-600). Keys are checked in sorted order, so the first
  broken key is the one reported.

### The two wrong approaches (`negative`)

- **Last arrival wins**, skipping invalid rows, walking #0 to #17: P-100 ends at
  1290 because the late seq 2 arrives after seq 3; P-200 is deleted by #6 and
  re-added by #14 (420, SUP-C); P-300 ends at 850, the later of the tied pair;
  P-400 stays at 90 because #8 is skipped silently; P-500 150; P-600 SUP-D.
- **Append per arrival**, closing the open row at each new arrival: P-100 opens
  [1], closes it at [3] when #5 arrives, opens [3], then closes that row at [2]
  when #13 arrives: a row from [3] to [2], which the interval check reports as
  `interval_order` for P-100. P-100 is the first key checked, so its row is the
  one reported (P-300 is also broken: [2]→[2]).

## `fixtures/marlow-events.json` (8 rows, the transfer case)

| # | event | batch | customer | seq | revision_no | op | tier | postcode |
|---|---|---|---|---|---|---|---|---|
| 0 | m-01 | 1 | C-1 | 1 | 1 | upsert | bronze | SW1 |
| 1 | m-02 | 1 | C-2 | 1 | 1 | upsert | silver | M1 |
| 2 | m-03 | 2 | C-1 | 2 | 1 | upsert | silver | SW1 |
| 3 | m-04 | 2 | C-1 | 2 | 2 | upsert | gold | SW1 |
| 4 | m-05 | 2 | C-2 | 2 | 1 | delete | — | — |
| 5 | m-06 | 2 | C-3 | 0 | 1 | upsert | bronze | LS1 |
| 6 | m-07 | 3 | C-2 | 3 | 1 | upsert | silver | M2 |
| 7 | m-08 | 3 | C-1 | 2 | 2 | upsert | gold | SW1 |

`revision_no` numbers corrections issued under one business change number.

- **Composite contract (`seq`, `revision_no`).** #5 has seq 0 →
  `invalid_sequence`; C-3 has nothing else → excluded. No event id repeats, so
  8 distinct deliveries. m-04 and m-08 carry the same payload at [2, 2] →
  redundant evidence. States: C-1 at [1,1], [2,1], [2,2]; C-2 at [1,1], [2,1]
  (delete), [3,1] = **6**. Current: C-1 [2,2] gold, C-2 [3,1] silver M2.
  History: C-1 [1,1]→[2,1] bronze, [2,1]→[2,2] silver, [2,2]→open gold; C-2
  [1,1]→[2,1] silver M1, [3,1]→open silver M2. One gap: C-2 from [2,1] to
  [3,1].
- **Narrow contract (`seq` alone).** The same eight rows; now C-1 at seq 2 has
  three deliveries (#2, #3, #7) with two distinct payloads, gold and silver →
  `tied_sequence`, candidates gold before silver (canonical order), and C-1 is
  withheld. States: C-1 at 1; C-2 at 1, 2, 3 = **4**; no redundant evidence
  (the identical pair sits inside the tie). Current: C-2 only. History: C-2
  [1]→[2], [3]→open; gap from [2] to [3].

## `fixtures/supplier-snapshots.json` (three full snapshots)

| Supplier | name | snapshot 1 | snapshot 2 | snapshot 3 |
|---|---|---|---|---|
| SUP-A | Ashby Metals | 5 | 5 | 5 |
| SUP-B | Brook Seals | 7 | 9 | 7 |
| SUP-C | Calder Fastenings | 10 | — | — |
| SUP-D | Dunmore Plastics | 3 | 3 | 3 |
| SUP-E | Elm Castings | — | 12 | 12 |

Values are `lead_days`. A change is derived by comparing each snapshot with the
previous one, keys in sorted order.

- **All three snapshots.** Snapshot 1: four upserts (everything is new).
  Snapshot 2: SUP-B differs (upsert 9), SUP-C missing (delete), SUP-E new
  (upsert); A and D unchanged emit nothing → 2 upserts, 1 delete. Snapshot 3:
  SUP-B differs again (upsert 7); nothing else changes → 1 upsert. Eight
  changes, eight states. Current: A seq 1, B seq 3 (7), D seq 1, E seq 2.
  History: A [1]→open; B [1]→[2] 7, [2]→[3] 9, [3]→open 7; C [1]→[2]; D
  [1]→open; E [2]→open. No gaps.
- **Snapshots 1 and 3 only.** Snapshot 3 against snapshot 1: SUP-B shows 7
  both times, so no change; SUP-C is missing (delete at 3); SUP-E is new
  (upsert at 3). History: A, B and D open from [1]; C [1]→[3]; E from [3].
  SUP-B has one version instead of three and its 9-day period is invisible; C's
  end and E's start move from snapshot 2 to snapshot 3, the first snapshot that
  could see them.
