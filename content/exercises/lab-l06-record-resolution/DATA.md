# Data dictionary and derivations

All records are original fiction. There is no generator and no random seed:
every fixture is a hand-written JSON list, and every value in `expected/` was
derived by hand from the source contract below **before** the reference was
run. The reference was then executed over the fixtures once, in scratch, and
agreed with every literal; nothing in `expected/` was produced by the resolver.

## Row contract (both plants, unchanged from the original package)

| field | type | rule |
|---|---|---|
| `event_id` | non-blank string | identifies one immutable delivered payload |
| `inspection_id` | non-blank string | business key; revisions are comparable within one key only |
| `version` | integer 1…2147483647 (not bool) | orders complete replacement states within a key |
| `inspected_units` | integer 0…2147483647 | missing → `missing_…`; wrong type or out of range → `invalid_…` |
| `defective_units` | integer 0…2147483647 | as above; `defective > inspected` → `defective_exceeds_inspected` |

Reasons are appended in that field order, then the cross-field check. A row
with any reason is quarantined but still retained in `raw`. Identical payloads
under one event ID are deliveries of one event; different payloads under one
event ID are an `event_id` conflict; equal `(key, version)` with different
quantities is a `key_version` conflict. A key whose only evidence is invalid
is **excluded** (disclosed); a key with earlier valid evidence whose latest
revision is invalid or unordered is **unresolved** (blocks). Publication is
allowed only when there are no conflicts and no unresolved keys. Totals are
sums over accepted rows; the rate is `defective / inspected` or `null` when
inspected is 0.

## Cinderline fixtures (byte copies of the original package)

`cinderline-baseline.json` (raw index: row):

| idx | event_id | inspection_id | version | inspected | defective | outcome |
|---|---|---|---|---|---|---|
| 0 | ev1 | A | 1 | 10 | 1 | valid, superseded |
| 1 | ev1 | A | 1 | 10 | 1 | identical delivery of idx 0 |
| 2 | ev2 | B | 1 | -3 | 1 | `invalid_inspected_units`, `defective_exceeds_inspected` (1 > -3) |
| 3 | ev3 | A | 2 | 12 | 1 | valid, current |
| 4 | ev4 | C | 1 | 8 | 0 | valid, current |

Derivations: accepted A v2 12/1, C v1 8/0 (sorted by key); totals 12+8 = 20,
1+0 = 1; rate 1/20 = 0.05; excluded `["B"]` (never valid); unresolved `[]`.
Batches (`cinderline-batches.json`): `late` = A v1 10/1 under ev-late (older,
no change, raw 6); `correction` = ev5 A v3 14/1 → A v3, C v1, totals 14+8 = 22,
1+0 = 1, rate 1/22 = 0.045454545454545456 (Python `1/22`); `event_conflict` =
ev3 again with 13/1 → event conflict `ev3` at raw indices [3, 5] **and**
key/version conflict `["A", 2]` at [3, 5]; `version_conflict` = ev-other A v2
13/1 → key/version conflict at [3, 5] only; reversed history of six rows puts
those two rows at indices 5→0 and 3→2, hence [0, 2]; `invalid_latest` = A v3
with null inspected → reason `missing_inspected_units`, A unresolved, no
conflict; `missing_order` = A with no version → `invalid_version`, A
unresolved. Every blocked case accepts C only: totals 8/0, rate 0/8 = 0.0.
`cinderline-unkeyed.json`: two rows, event `unkeyed`, null key, 2 vs 3
inspected → event conflict at [0, 1] on a first run; after the 5-row baseline
and one row per batch they sit at raw indices 5 and 6.

Pipeline literals: baseline publishes once (effect count 1,
`current_with_exclusions` because B is excluded); replay raw 10, same snapshot,
still 1 effect; correction raw 6, effect 2; its replay raw 7, effect still 2;
a conflict or invalid latest after the baseline → `stale_previous`, raw 6,
effect 1; a first-run conflict → `blocked_no_snapshot`, `published` null,
0 effects; failure after `retained_raw` while ingesting the correction leaves
raw 6, `stale_previous`, 1 effect; recovery publishes 22/1 with 2 effects.

## Northgate fixtures (the transfer plant: valve-seat line, keys `VS-n`)

`northgate-baseline.json`:

| idx | event_id | inspection_id | version | inspected | defective | outcome |
|---|---|---|---|---|---|---|
| 0 | ng-e1 | VS-1 | 1 | 40 | 2 | valid, superseded by idx 4 |
| 1 | ng-e2 | VS-2 | 1 | 25 | 0 | valid, current |
| 2 | ng-e2 | VS-2 | 1 | 25 | 0 | identical delivery of idx 1 |
| 3 | ng-e3 | VS-3 | 1 | 30 | 31 | `defective_exceeds_inspected`; VS-3 excluded |
| 4 | ng-e4 | VS-1 | 2 | 42 | 2 | valid, current |
| 5 | ng-e5 | VS-4 | 1 | 0 | 0 | valid: zero is a value, not missing |
| 6 | ng-e6 | VS-5 | 2 | 18 | 4 | valid, current (v1 has not arrived) |

Baseline derivation: accepted VS-1 v2 42/2, VS-2 v1 25/0, VS-4 v1 0/0,
VS-5 v2 18/4 (sorted by key string); inspected 42+25+0+18 = **85**, defective
2+0+0+4 = **6**; rate 6/85 = 0.07058823529411765 (Python `6/85` typed in an
interpreter, not the resolver); excluded `["VS-3"]`; unresolved `[]`;
publication allowed; quarantine one row at raw index 3; raw count 7.

`northgate-batches.json`:

| batch | row | derivation |
|---|---|---|
| `late` | ng-late VS-5 v1 17/4 | older than accepted v2: baseline unchanged, raw 8 |
| `correction` | ng-e7 VS-2 v2 26/1 | VS-2 → v2; inspected 42+26+0+18 = **86**, defective 2+1+0+4 = **7**; rate 7/86 = 0.08139534883720931; ingesting it twice gives the same accepted rows (raw 9) |
| `event_conflict` | ng-e4 VS-1 v2 **43**/2 | same event ID as idx 4, different payload → `event_id` conflict `ng-e4` at [4, 7] and `key_version` conflict `["VS-1", 2]` at [4, 7]; VS-1 unresolved |
| `version_conflict` | ng-e8 VS-1 v2 43/2 | new event ID, same key/version, different quantities → `key_version` conflict at [4, 7] only; reversed eight-row history puts them at [0, 3] |
| `invalid_latest` | ng-e9 VS-1 v3 null/2 | `missing_inspected_units` at raw index 7; VS-1 has earlier valid evidence → unresolved, not excluded; no conflict |
| `missing_order` | ng-e10 VS-1 (no version) 44/2 | `invalid_version` at index 7; unordered observation on a known key → VS-1 unresolved |
| `invalid` | five rows, keys VS-6…VS-9 and a blank | reasons in order: `invalid_version` ("2" is a string), `invalid_inspected_units` (3.5 is a float), `missing_inspection_id` (two spaces), `invalid_defective_units` (-1), `invalid_version` (`true` is a bool) |

Every VS-1-blocked case accepts VS-2, VS-4, VS-5: inspected 25+0+18 = **43**,
defective 0+0+4 = **4**, rate 4/43 = 0.09302325581395349, excluded `["VS-3"]`,
unresolved `["VS-1"]`, publication false. The `invalid` batch alone accepts
nothing: totals 0/0, rate `null`; VS-6, VS-7, VS-8 and VS-9 never had a valid
revision so all four are excluded; the blank-key row has no key to exclude;
no conflict and no unresolved key → `publication_allowed` **true** (the gate
checks contradiction, not emptiness), and the pipeline publishes an empty
snapshot with status `current_with_exclusions` and one effect.

`northgate-unkeyed.json`: event `ng-unkeyed`, null keys, 5 vs 6 inspected.
First run: conflict at [0, 1], nothing accepted, unresolved `[]`,
`blocked_no_snapshot`, no effect. Cross batch: after the 7-row baseline,
`[unkeyed[0]]` lands at index 7 and `[unkeyed[1], correction]` at 8 and 9, so
the conflict is at [7, 8]; the candidate is the correction state 86/7; the
published snapshot stays 85/6, `stale_previous`, one effect.

Pipeline literals: baseline effect 1, raw 7; replay raw 14; late raw 8;
correction raw 8, effect 2; correction replay raw 9, effect 2; conflict or
invalid latest after baseline → `stale_previous`, raw 8, effect 1; first-run
conflict → `blocked_no_snapshot`; failure after `retained_raw` → raw 8,
`stale_previous`, effect 1, then recovery → `current_with_exclusions`, effect
2; failure after `published_snapshot` → status already
`current_with_exclusions`, effect still 1, and two recoveries give exactly 2.

## Reference hash

`expected/reference-hash.json` records SHA-256
`cc4a8f46270e8f1c3e1ab4a4a24d85af3b4c9611f3983fa2656ed73f87a43510` and
9,401 bytes for `solutions/reference.py`, computed with `sha256sum` over the
original `content/exercises/reliable-data/solutions/reference.py` on
2026-09-23. The Cinderline fixture copies are byte-identical to the originals
(`fixtures/baseline.json`, `fixtures/batches.json`,
`fixtures/unkeyed-conflict.json`) and are checked against them when the
originals are present.
