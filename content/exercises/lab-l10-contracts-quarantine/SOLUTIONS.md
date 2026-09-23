# Explained solutions

`solutions/validator.py` is the complete reference. `validate()` reads the
files; `validate_rows()` takes in-memory rows so a test can alter an input
without touching a fixture; `row_checks_only()` shows what a per-row
validator can see. Outputs quoted below were printed by that program and
agree with the hand-authored `expected/*.json`.

## Task 1 — row-level or batch-level

Row-level: `missing_*`, `invalid_*`, `below_minimum_*`, `unknown_plant`,
`defective_exceeds_inspected`, and the zero-denominator rate. Each can be
decided from one row plus the contract and the dimension. Batch-level:
`duplicate_delivery`, `event_id_conflict`, `key_version_conflict`,
`redundant_key_version`, `version_time_inversion`, `manifest_row_count_mismatch`,
`missing_column`. Each needs at least two rows, or the manifest, or the header.

## Task 2 / 5 — the primary delivery

```
raw_count 20   accepted_count 5   quarantined_count 15
accepted rows 1 (A v1, 0.1), 4 (C v1, 0.0), 7 (F v1, null), 18 (N v1, 0.1), 19 (N v2, 0.0967741935483871)
contradictions  event_id_conflict e02 [2, 20]; key_version_conflict [H, 1] [10, 11]; version_time_inversion J [13, 14]
batch_failures  manifest_row_count_mismatch manifest 21, delivered 20
publication_allowed false
```

Row 7's rate is `null` because `defect_rate()` divides only when
`inspected > 0`; `0.0` would claim a measured perfect batch and a division
would raise. Row 3 carries two reasons in contract order: the field rule
(`below_minimum_inspected_units`) then the cross-field rule (1 > −3). Row 16
also carries two, both field rules, in field order (version before
defective). Row 2 is quarantined although it is a perfectly formed A v2:
its event ID `e02` also arrived as row 20 describing inspection Z, so the
delivery told two stories under one immutable identity and neither can be
trusted. Rows 10 and 11 disagree on H v1 (20 vs 21 inspected): both are
quarantined and the pair is a contradiction. Row 12 repeats row 4 exactly:
row 4 stays accepted, row 12 is a disclosed duplicate. J v2 is dated before
J v1, so both J rows go, and inspection N (v1 on the 6th, v2 on the 7th)
stays.

Only contradictions and batch failures block. Fifteen quarantined rows on
their own would not: a report over the five accepted rows with fifteen
disclosed exclusions is a legitimate accepted-only report. What blocks here
is that the history contradicts itself in three places and the source
claimed a row it did not deliver.

## Task 3 — the row-level starter

`parse_field` must trim, treat empty as missing (a reason only if required),
match `^[+-]?[0-9]+$` before `int()`, compare with `minimum`, and match the
ISO shape before `date.fromisoformat`. `check_row` walks the contract fields
in order, appends each field's reason or — when the value parsed and the
field references a dimension — `unknown_<label>`, then applies
`defective_exceeds_inspected` when both quantities are integers.
`row_checks_only` over the primary rows:

```
passing [1, 2, 4, 7, 10, 11, 12, 13, 14, 18, 19, 20]   failing [3, 5, 6, 8, 9, 15, 16, 17]   sees_manifest false
```

## Task 4 — the proof

`check_row(row 10) == []` and `check_row(row 11) == []`: each H row is
individually flawless. The same holds for 13/14, 2/20 and 12. A per-row
validator therefore accepts twelve rows, seven of which the contract must
reject, and it has no input at all that mentions the manifest's 21. Row-level
checks can establish a row's shape, ranges and references; they cannot
establish uniqueness, ordering across rows, or completeness of the delivery.
`test_row_level_checks_alone_cannot_establish_uniqueness_or_completeness`
asserts exactly those facts against the literal `row_level_only` block.

## Task 5 — batch rules in order

1. **Duplicates first**, so an exact repeat is not later mistaken for a
   conflict. Compare the canonical JSON of the whole typed payload under the
   same event ID; keep the first, mark repeats.
2. **Event-ID conflicts** among the survivors: more than one distinct payload
   under one event ID → every row is a contradiction.
3. **Key/version uniqueness**: group by `(inspection_id, version)`; differing
   quantities → `key_version_conflict` on all; identical quantities under
   different events → `redundant_key_version` on the later rows only.
4. **Time inversion**: for each inspection, sort by version; if any
   `revised_at` is earlier than its predecessor's, the whole inspection is a
   contradiction — neither row can be shown to be the honest one.
5. **Manifest** against the raw row count, and **required columns** against
   the header: batch failures.

`publication_allowed = not contradictions and not failures`.

## Task 6 — Tessmoor

```
raw_count 12   accepted 1, 2, 3, 11, 12   quarantined 4, 5, 6, 7, 8, 9, 10
contradictions []   batch_failures []   publication_allowed true
```

Seven violations, one reason each, none of them a contradiction; the
manifest agrees; the delivery is publishable with seven disclosed
exclusions. Altering the manifest to 13 adds `manifest_row_count_mismatch 13
vs 12` and flips publication to false while leaving accepted and quarantine
byte-identical — completeness is orthogonal to row quality. Dropping the
`plant_id` column adds `missing_column` and, because the field is required,
every row also gets `missing_plant_id`. Appending `t12` with Q v1's exact
quantities under a new event adds `redundant_key_version` to row 13 only and
does not block: agreeing evidence is not a contradiction.

## Task 7 — the permissive validator

`starters/permissive_validator.py` returns all 20 rows as accepted (quantities
still text, rate faked as 0.0), no quarantine, no contradictions, no batch
failures, publication true. The negative test asserts the reason, not just
the difference: accepted 20 against 5; the wrongly accepted set is exactly
the 15 rows the contract quarantines; row 6 came through as `("5", "7")`;
`batch_failures` is empty although the manifest lies. A validator that never
rejects converts every downstream number into a guess while looking like a
passing gate, which is why "all green" from an unknown validator is a
question, not an answer.

## The wrong approach, and why it fails

"Loop over the rows, cast with `int()` inside `try`, drop what fails, and
publish if nothing raised." It turns `""` into a crash or a zero depending on
the day, accepts `12.0` on some paths, never sees that H v1 arrived twice
with different quantities, never sees J's version going backwards in time,
and cannot know that 21 rows were promised. It produces a clean-looking table
of twelve rows and a green light. The tests name each of those holes.
