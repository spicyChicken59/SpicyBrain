# Explained solutions

The complete resolver is `solutions/reference.py`, the original Cinderline
resolver copied byte-for-byte (SHA-256
`cc4a8f46270e8f1c3e1ab4a4a24d85af3b4c9611f3983fa2656ed73f87a43510`).
Nothing below adds policy; `solutions/scenarios.py` only drives that file
over the fixtures and reports what came back. Every intermediate output
quoted here was printed by that driver and agrees with the hand-authored
literals in `expected/`.

## Task 1 — four outputs

`resolve(cinderline-baseline)` returns:

```
raw_count 5
quarantine [(2, ['invalid_inspected_units', 'defective_exceeds_inspected'])]
accepted   [A v2 12/1, C v1 8/0]
totals     {"inspected_units": 20, "defective_units": 1, "defect_rate": 0.05}
excluded   ["B"]   unresolved []   conflicts []   publication_allowed true
```

B gets two reasons, not one: −3 is out of range **and** 1 > −3. The row is
retained in `raw` (you can point at index 2 later), listed in `quarantine`
with its reasons, absent from `accepted`, and disclosed in `excluded_keys`.
Publication is allowed because nothing contradicts anything; the report is
an accepted-only report with a disclosed exclusion, not complete coverage.
Four outputs because they answer four different questions: what arrived,
what was refused and why, what the current state is, and whether that state
may be called a report.

## Task 2 — the flawed resolver

`starters/resolver.py:flawed_current` over baseline + `invalid_latest`:

```
[{A, version 2, 12, 1}, {C, version 1, 8, 0}]       # v3 vanished, v2 "current" again
```

The reference says `accepted [C v1 8/0]`, `unresolved ["A"]`,
`publication_allowed false`: A **had** valid state and its latest revision is
unusable, so its current state cannot be proved. Filtering invalid rows first
and then picking the highest surviving version resurrects v2 and lies.

Over baseline + `version_conflict`, forwards and reversed:

```
forward  A -> {version 2, 13, 1}      # last arrival won
reversed A -> {version 1, 10, 1}      # reversing the input changed the answer
```

Two different answers for the same evidence is the failure: transport order
is not authority. The reference reports one `key_version` conflict for
`["A", 2]` in both orders (raw indices [3, 5] forwards, [0, 2] reversed),
unresolved `["A"]`, publication false. Over the unkeyed rows the starter
silently keys both rows under `None` and keeps the last.

A repaired resolver must: retain every row; validate with reasons; group by
event ID and by (key, version) over **all** retained history and compare
canonical payloads; take the highest observed revision per key *before*
dropping invalid rows; block a key whose latest revision is invalid or
unordered; exclude a key that never had valid evidence; accept the rest;
allow publication only with no conflicts and no blocked keys. That is what
`reference.py:resolve` does, group by group.

## Task 3 — the preserved regressions

| history | accepted | totals | unresolved | conflicts | raw |
|---|---|---|---|---|---|
| baseline | A v2, C v1 | 20/1 | [] | [] | 5 |
| + baseline (replay) | A v2, C v1 | 20/1 | [] | [] | 10 |
| + late A v1 | A v2, C v1 | 20/1 | [] | [] | 6 |
| + correction A v3 14/1 (×1 or ×2) | A v3, C v1 | 22/1 | [] | [] | 6 / 7 |
| + event_conflict ev3 13/1 | C v1 | 8/0 | [A] | event_id ev3 [3,5]; key_version [A,2] [3,5] | 6 |
| + version_conflict ev-other 13/1 | C v1 | 8/0 | [A] | key_version [A,2] [3,5] | 6 |
| reversed(that) | C v1 | 8/0 | [A] | key_version [A,2] [0,2] | 6 |
| + invalid_latest A v3 null | C v1 | 8/0 | [A] | [] | 6 |
| + missing_order | C v1 | 8/0 | [A] | [] | 6 |

Through `LocalPipeline`: baseline → `current_with_exclusions`, 1 effect; replay
→ raw 10, same snapshot object, 1 effect; correction → 22/1, 2 effects; the
correction again → still 2 effects; any blocked case after the baseline →
`stale_previous`, published totals still 20/1, 1 effect. The rate 1/22 prints
as 0.045454545454545456 because the literal is Python's own float for `1/22`.

## Task 4 — the naive gate

First run over `cinderline-unkeyed.json`:

```
conflicts  [{"kind": "event_id", "identity": "unkeyed", "raw_indices": [0, 1]}]
unresolved []   accepted []   publication_allowed false
status blocked_no_snapshot   published None   local_effect_count 0
naive_gate(result) -> True
```

The unresolved list is empty because both rows have `inspection_id: null`;
there is no key to list and the resolver refuses to invent one. The conflict
is real anyway: one immutable event ID, two payloads. A gate that reads only
the key list publishes a contradiction.

Cross batch: publish the baseline (20/1), ingest `[unkeyed[0]]` — one
malformed row alone is not a conflict, publication stays allowed — then
ingest `[unkeyed[1], A v3 14/1]`:

```
accepted candidate [A v3 14/1, C v1 8/0]   candidate totals 22/1
conflicts [{event_id unkeyed [5, 6]}]   unresolved []   publication_allowed false
status stale_previous   published totals 20/1   local_effect_count 1
```

22/1 is a diagnostic candidate: every accepted row is individually fine, but
the retained history contradicts itself, so the last verified 20/1 stays the
published report and is labelled stale. No second effect is recorded.

## Task 5 — Northgate

Baseline: raw 7, quarantine `[(3, ['defective_exceeds_inspected'])]`, accepted
VS-1 v2 42/2, VS-2 v1 25/0, VS-4 v1 0/0, VS-5 v2 18/4, totals 85/6, rate
0.07058823529411765, excluded `["VS-3"]`, publication allowed.

- VS-4's 0/0 is accepted: 0 is inside the range and `defective <= inspected`
  holds. It adds 0 to both sums. A *missing* value would be
  `missing_inspected_units` and quarantine; the resolver never coerces missing
  to zero, and the empty-history rate is `null`, not 0.0, for the same reason.
- VS-5 v2 first, v1 later (`late`): v1 is retained (raw 8), grouped under
  (VS-5, 1), and ignored for current state because 2 > 1. Nothing changes.
- correction VS-2 v2 26/1 → 86/7 (rate 0.08139534883720931), once, effect 2.
- event/version conflict on VS-1 (43 vs 42 at v2) → VS-1 unresolved, accepted
  VS-2/VS-4/VS-5 = 43/4, conflicts at raw indices [4, 7] ([0, 3] reversed).
- `invalid` alone: reasons `invalid_version`, `invalid_inspected_units`,
  `missing_inspection_id`, `invalid_defective_units`, `invalid_version`;
  accepted `[]`; excluded VS-6…VS-9; `publication_allowed` **true** and the
  pipeline publishes an empty snapshot as `current_with_exclusions`. That is
  the policy as written: the gate asks whether the evidence contradicts
  itself. Whether an empty accepted set is worth publishing is a separate
  check a publisher must make (a coverage floor, a minimum row count); the
  resolver deliberately does not smuggle it into the contradiction gate.

## Task 6 — failure boundaries

Failure after `retained_raw` while ingesting the correction: raw 8, status
`stale_previous`, published totals 85/6, 1 effect. `recover()` recomputes from
the eight retained rows and publishes 86/7 with 2 effects. Failure after
`published_snapshot`: the snapshot is already 86/7 and `current_with_exclusions`,
but the effect count is still 1; `recover()` twice yields exactly 2 because
the outbox is keyed by snapshot ID (`setdefault`). Publication state answers
"what is the current report"; effect state answers "which reports have been
announced"; a crash between them is exactly the case that shows they differ.

## The wrong approach, and why it fails

"Drop invalid rows, sort by arrival, keep the last row per key, publish when
the unresolved list is empty" passes the happy path and fails four ways that
the tests name: it resurrects an older valid revision when the latest is
invalid; it lets transport order pick a winner between contradictory payloads
(and gives a different winner when the batch is reversed); it never notices a
same-event contradiction; and it publishes an unkeyed conflict because there
is no key to list. `NegativeStarterTests` asserts each of those outcomes as
the reason the starter is wrong, not merely that it differs from the answer.
