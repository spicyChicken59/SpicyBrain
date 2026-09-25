*Local-executed (R), plain Python 3.12, standard library only. Nothing to
install; nothing runs on Databricks.*

### What this lab is for

Modules B3 and C1 both lean on one habit: before a number is trusted, the
rows behind it have to be admitted under a written contract, and every row
that is refused has to say why. This lab gives you that contract in a file
(`fixtures/contract.json`), a twenty-row delivery from the fictional
Cinderline plants that breaks it in fifteen distinct ways, a manifest that
promises twenty-one rows, and a second delivery from the fictional Tessmoor
plants that breaks the contract differently and is nevertheless publishable.
The point is not the CSV parsing. The point is the line between what one row
can prove about itself and what only the whole delivery can prove.

### The contract, briefly

Eight fields. `event_id` identifies one delivery and must be unique;
`plant_id` must exist exactly in the plant dimension; `inspection_id` is the
business key; `version` is an integer of at least 1; `revised_at` is an ISO
date; `inspected_units` and `defective_units` are integers of at least 0,
with `defective <= inspected`; `note` is optional. Text is trimmed and an
empty cell is *missing*, never zero. Then four rules that need more than one
row: `(inspection_id, version)` must be unique; `event_id` must tell one
story; within an inspection `revised_at` may not go backwards as `version`
goes forwards; and the manifest's `delivered_rows` must equal what arrived.
Rows fail with reasons into quarantine; contradictions and batch failures
block publication; plain quarantine is disclosed and does not.

### The primary delivery

| row | event | plant | key | ver | date | insp | def | outcome |
|---|---|---|---|---|---|---|---|---|
| 1 | e01 | CL-N | A | 1 | 09-01 | 10 | 1 | accepted, rate 0.1 |
| 2 | e02 | CL-N | A | 2 | 09-03 | 12 | 1 | event_id_conflict (with 20) |
| 3 | e03 | CL-N | B | 1 | 09-01 | −3 | 1 | below_minimum, defective_exceeds |
| 4 | e04 | CL-S | C | 1 | 09-02 | 8 | 0 | accepted, 0.0 |
| 5 | e05 | CL-S | D | 1 | 09-02 | twelve | 0 | invalid_inspected_units |
| 6 | e06 | CL-S | E | 1 | 09-02 | 5 | 7 | defective_exceeds_inspected |
| 7 | e07 | CL-N | F | 1 | 09-04 | 0 | 0 | accepted, rate null |
| 8 | e08 | CL-N | — | 1 | 09-04 | 9 | 0 | missing_inspection_id |
| 9 | e09 | CL-W | G | 1 | 09-04 | 6 | 1 | unknown_plant |
| 10 | e10 | CL-S | H | 1 | 09-05 | 20 | 2 | key_version_conflict |
| 11 | e11 | CL-S | H | 1 | 09-05 | 21 | 2 | key_version_conflict |
| 12 | e04 | CL-S | C | 1 | 09-02 | 8 | 0 | duplicate_delivery |
| 13 | e13 | CL-N | J | 1 | 09-06 | 15 | 1 | version_time_inversion |
| 14 | e14 | CL-N | J | 2 | 09-05 | 16 | 1 | version_time_inversion |
| 15 | e15 | CL-S | K | 1 | 09-06 | — | 0 | missing_inspected_units |
| 16 | e16 | CL-S | L | 0 | 09-06 | 4 | −1 | below_minimum ×2 |
| 17 | e17 | CL-S | M | 1 | 2026/09/06 | 4 | 0 | invalid_revised_at |
| 18 | e18 | CL-S | N | 1 | 09-06 | 30 | 3 | accepted, 0.1 |
| 19 | e19 | CL-S | N | 2 | 09-07 | 31 | 3 | accepted, 0.0967741935483871 |
| 20 | e02 | CL-N | Z | 1 | 09-03 | 12 | 1 | event_id_conflict (with 2) |

Every value in `expected/primary.json` was written by hand from that table
(`DATA.md` shows each derivation) before the validator existed.

### Task 1 — which rules need the whole delivery

Row-level: missing, invalid, below-minimum, unknown plant, defects over
inspected, and the zero-denominator rate. Batch-level: duplicates, event
conflicts, key/version uniqueness, time inversion, the manifest, the header.

### Task 2 — predict, then run

The validator reports raw 20, accepted 5 (rows 1, 4, 7, 18, 19), quarantined
15, three contradictions (`e02` at rows 2 and 20; H v1 at 10 and 11; J at 13
and 14), one batch failure (manifest 21 against 20) and `publication_allowed:
false`. Row 7's rate is `null`, not `0.0`: nothing was inspected, so no rate
was measured. Row 3 carries two reasons in contract order, the field rule
before the cross-field rule.

### Task 3 — the row-level starter

`starters/validator.py` has six marked gaps. Filling the first five gives
`parse_field` and `check_row`; `row_checks_only` then reports twelve passing
rows — 1, 2, 4, 7, 10, 11, 12, 13, 14, 18, 19, 20 — and eight failing.

### Task 4 — the proof that row checks are not enough

`check_row` returns `[]` for row 10 and for row 11. Both H rows are
individually flawless; only side by side do they contradict. The same holds
for the two J rows, the two `e02` rows and the repeated `e04`. And no row
carries anything about the manifest, so a per-row validator can never learn
that a row is missing. The test asserts precisely that: the twelve pass
alone, seven of them are quarantined by the batch, and `sees_manifest` is
false by construction.

### Task 5 — the batch gap

Duplicates are removed first so a repeat is not mistaken for a conflict;
then event-ID conflicts; then `(inspection_id, version)` uniqueness, where
differing quantities contradict and agreeing quantities are merely
redundant; then the time inversion, which quarantines the whole inspection
because neither row can be shown honest; then the manifest and the header.
Only contradictions and batch failures block.

### Task 6 — Tessmoor, and three alterations

Twelve rows, manifest agrees: accepted 1, 2, 3, 11, 12 (W v1 and v2 share a
date, which is allowed), seven quarantined for seven different reasons — a
whitespace-only key, `12.0`, `tm-a`, version `2.0`, `-1` defective, one
defective of zero inspected, an exact repeat — no contradiction, publishable.
The tests then alter the input in memory: manifest 13 adds a batch failure
and blocks while every row stays the same; dropping `plant_id` is a
`missing_column` failure; appending `t12` with Q v1's quantities under a new
event is `redundant_key_version` and does not block.

### Task 7 — the validator that passes everything

`starters/permissive_validator.py` accepts all twenty rows as text and says
publish. The negative test does not stop at "different": it asserts the
fifteen wrongly accepted rows by number, that row 6's seven-of-five came
through, and that the manifest mismatch went unreported. A gate that cannot
say no is not a gate.

### What the tests prove and do not prove

Nineteen `unittest` cases, zero skipped, hold the validator to the
hand-authored literals for both deliveries, prove the row-level limitation,
run three altered-input transfer cases, check that reason counts survive
reversing the rows, and reject the permissive validator for its documented
reason. Four mutants were run to show the suite can go red: the manifest
check removed, the zero-denominator rate faked as 0.0, the inversion rule
removed, and a wrong literal. The tests do not prove that a manifest count is
sufficient completeness evidence, that these reason codes match any product's
expectations feature, or anything about scale.

### Setup and cleanup

`python3.12 run_tests.py --evidence local-evidence.json` in the package
directory; `python3.12 solutions/validator.py` prints the primary result and
accepts `--csv --plants --manifest` for the transfer files. No bytecode is
written; delete the evidence file when you are done.
