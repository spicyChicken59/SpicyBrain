# Tasks

Read `fixtures/contract.json` before any code. Predict on paper; every
expected value you will be checked against was written by hand (`DATA.md`).

## 1. Sort the rules

For each rule in the contract, say whether one row is enough to check it or
whether it needs the whole delivery (and the manifest). Write two lists.
Expected behaviour: `missing_*`, `invalid_*`, `below_minimum_*`,
`unknown_plant` and `defective_exceeds_inspected` are row-level; everything
under `batch_rules` is not.

## 2. Predict the primary delivery

`fixtures/inspections.csv` has 20 data rows and `fixtures/manifest.json`
claims 21. For every row write: accepted, or the reason list in contract
order. Then write the contradictions (rule, identity, row numbers), the batch
failures and `publication_allowed`. Expected behaviour: 5 accepted, 15
quarantined, 3 contradictions, 1 batch failure, publication refused.

## 3. Fill the starter's row-level gaps (1–5)

In `starters/validator.py` implement `parse_field` and `check_row` so that:
an empty cell is `missing_<field>` for a required field and `None` otherwise
(never 0); `twelve` and `12.0` are `invalid_inspected_units`; `2026/09/06` is
`invalid_revised_at`; `-3` is `below_minimum_inspected_units`; `CL-W` is
`unknown_plant`; `7 of 5` is `defective_exceeds_inspected`; and reasons come
in contract field order followed by the cross-field rule. Run
`row_checks_only` over the primary rows: which twelve rows pass on their own?

## 4. Prove that row checks are not enough

Rows 10 and 11 both describe inspection H version 1 with different
quantities. Show that `check_row` returns `[]` for each. Do the same for the
two J rows, the two `e02` rows and the repeated `e04`. Then look for any
per-row signal that the manifest promised one more row than arrived. Write
down what a validator that only sees one row at a time can never establish.

## 5. Fill the batch gap (6)

Implement `check_batch`: keep the first of identical deliveries and
quarantine repeats as `duplicate_delivery`; quarantine every row of an event
ID that tells two stories (`event_id_conflict`); quarantine every row of a
`(inspection_id, version)` pair whose quantities differ
(`key_version_conflict`), and later rows of a pair whose quantities agree
(`redundant_key_version`); quarantine the whole inspection when a higher
version carries an earlier `revised_at` (`version_time_inversion`); report
`manifest_row_count_mismatch` and `missing_column` as batch failures. Decide,
and justify, which of these block publication. Expected behaviour: the
primary result equals `expected/primary.json` exactly, including
`defect_rate: null` for row 7.

## 6. Transfer: Tessmoor

`fixtures/transfer-inspections.csv` (12 rows, manifest agrees) breaks the
contract in seven different ways: a whitespace-only key, `12.0`, `tm-a`
instead of `TM-A`, version `2.0`, `-1` defective, `1 defective of 0
inspected`, and an exact repeat. Predict the accepted rows (five, two of them
W v1 and W v2 on the same date), the quarantine and the publication decision.
Then alter the input in memory, not the fixture: set the manifest to 13; drop
the `plant_id` column; append a row `t12` that repeats Q v1's quantities under
a new event ID. State what each alteration changes and why only two of the
three block publication.

## 7. Why the permissive validator must fail

`starters/permissive_validator.py` accepts all 20 rows, reports nothing and
says publish. Write the test that rejects it. It must not merely assert "the
result differs"; it must name the reason: which rows were wrongly accepted,
that row 6's `7 of 5` came through as text, and that the manifest mismatch
went unreported. Compare with `NegativeValidatorTests` afterwards.
