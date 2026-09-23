# Data dictionary and derivations

All data is synthetic and written by hand for this lab. Cinderline
Components, plants CL-N, CL-S and TM-A, and every inspection are fiction; no
generator and no random seed are involved. Every expected value was derived by
hand, row by row, from the contract below and the documented behaviour of the
standard library, and written into `expected/*.json` before the solution was
run. No test compares the parser with a value the parser computed.

## The contract (six fields)

| field | type after parsing | required | rule |
|---|---|---|---|
| `inspection_id` | `str`, trimmed | yes | blank is missing |
| `plant_id` | `str`, trimmed | yes | blank is missing |
| `inspected_on` | `datetime.date` | yes | text `YYYY-MM-DD` that is a real calendar day |
| `inspected_units` | `int` | yes | a real `int` (not `bool`) or text of optional sign and ASCII digits; ≥ 0 |
| `defective_units` | `int` | yes | as above; ≥ 0; ≤ `inspected_units` once both are valid |
| `unit_cost` | `decimal.Decimal` | no | `int`, finite `float` via `str()`, or text `digits[.digits]` with optional sign; ≥ 0 |

Reasons are reported in field order: `missing_<field>` (key absent or blank
text), `null_<field>` (present `None`), `malformed_<field>` (conversion
refused), `negative_<field>` (under the minimum of 0), then
`defective_exceeds_inspected` (only when every field passed), then across
records `exact_duplicate` or `conflicting_duplicate`. An optional field that
is missing or null becomes `None` without a reason. `defect_rate` is
`defective / inspected`, or `None` when `inspected` is 0.

## fixtures/inspections.csv (plant CL-N, 15 rows)

| pos | id | on | insp | def | cost | derivation → outcome |
|---|---|---|---|---|---|---|
| 1 | CLN-001 | 2026-09-01 | 120 | 3 | 4.25 | valid; 3/120 = 0.025 → accepted (first of an exact pair) |
| 2 | CLN-002 | 2026-09-01 | 0 | 0 | 4.25 | valid; 0 inspected → rate None → accepted |
| 3 | CLN-003 | 2026-09-02 | twelve | 0 | 4.25 | `twelve` fails the digit pattern → malformed_inspected_units |
| 4 | CLN-004 | 2026-09-02 | (empty) | 1 | 4.25 | `""` is blank → missing_inspected_units |
| 5 | CLN-005 | 2026-09-02 | -5 | 0 | 4.25 | −5 < 0 → negative_inspected_units; cross-field not run |
| 6 | CLN-006 | 2026-09-03 | 40 | 45 | 4.25 | fields valid; 45 > 40 → defective_exceeds_inspected |
| 7 | CLN-007 | 2026/09/03 | 10 | 1 | 4.25 | slashes fail the date pattern → malformed_inspected_on |
| 8 | CLN-008 | 2026-09-03 | ` 15 ` | 2 | (empty) | trimmed to 15; optional cost None; passes alone; conflicts with 13 → conflicting_duplicate |
| 9 | CLN-009 | 2026-09-04 | 12.0 | 1 | 4.25 | `12.0` fails the digit pattern → malformed_inspected_units |
| 10 | (empty) | 2026-09-04 | 9 | 0 | 4.25 | blank id → missing_inspection_id |
| 11 | CLN-011 | 2026-09-04 | 30 | 2 | "4,25" | comma fails the decimal pattern → malformed_unit_cost |
| 12 | CLN-001 | 2026-09-01 | 120 | 3 | 4.25 | same typed payload as 1 → exact_duplicate (1 kept) |
| 13 | CLN-008 | 2026-09-03 | 16 | 2 | (empty) | payload differs from 8 (16 vs 15) → conflicting_duplicate |
| 14 | CLN-014 | 2026-09-05 | 200 | 4 | 3.90 | valid; 4/200 = 0.02; cost text `3.90` keeps its zero → accepted |
| 15 | CLN-015 | 2026-09-05 | -10 | -1 | 4.25 | two negatives, in field order; cross-field not run |

CSV: 3 accepted (1, 2, 14), 12 rejected.

## fixtures/inspections.json (plant CL-S, 10 records)

| pos | id | insp as read | other | derivation → outcome |
|---|---|---|---|---|
| 1 | CLS-001 | 80 (`int`) | def 2, cost "5.10" | valid; 2/80 = 0.025 → accepted |
| 2 | CLS-002 | `None` | | present null → null_inspected_units |
| 3 | CLS-003 | key absent | | missing_inspected_units |
| 4 | CLS-004 | "64" (`str`) | def 1 | text converts to 64; 1/64 = 0.015625 exactly → accepted |
| 5 | CLS-005 | 12.5 (`float`) | | not an `int`, not text → malformed_inspected_units |
| 6 | CLS-006 | `True` (`bool`) | | `type(True) is int` is False → malformed_inspected_units |
| 7 | CLS-007 | 0 | def 0, cost 5.1 (`float`) | valid; rate None; `Decimal(str(5.1))` prints `5.1` → accepted |
| 8 | CLS-008 | 50 | def 1, cost `None` | optional null → None, no reason; 1/50 = 0.02 → accepted |
| 9 | CLS-009 | 20 | plant "" | blank plant → missing_plant_id |
| 10 | CLS-010 | 20 | on "2026-09-31" | pattern passes, September has 30 days → malformed_inspected_on |

JSON: 4 accepted (1, 4, 7, 8), 6 rejected.

## expected/primary.json

- **Counts.** 25 raw = 15 + 10; accepted 3 + 4 = 7; rejected 12 + 6 = 18.
  Reasons: 18 records, `CLN-015` carries two, so 19; the per-reason counts are
  tallied from the two tables (for example `malformed_inspected_units` = CSV 3,
  CSV 9, JSON 5, JSON 6 = 4).
- **Order.** Rejected records are sorted by (source order, position). Accepted
  records keep processing order: CSV 1, 2, 14, then JSON 1, 4, 7, 8.
- **Rates.** 3/120, 0/0, 4/200, 2/80, 1/64, 0/0, 1/50; each quotient that is
  not `None` is the double nearest to the decimal written (0.025, 0.02,
  0.015625, which is exact in binary).
- **Log.** One warning per record rejected in `parse_records`, in reading order
  (CSV 3, 4, 5, 6, 7, 9, 10, 11, 15; JSON 2, 3, 5, 6, 9, 10: fifteen lines),
  then one per duplicate rejection in the order the accepted list is walked
  (CSV 8, 12, 13): eighteen lines, first CSV position 3, last CSV position 13.
  The shape `WARNING:cinderline.parsing:<message>` is the format the tests'
  collecting handler uses, the same shape `unittest`'s `assertLogs` prints.
- **Altered contract.** A copy of the contract with `unit_cost` required, over
  the JSON only: `CLS-008`'s null becomes `null_unit_cost`, so 3 accepted
  (1, 4, 7) and 7 rejected.
- **Script.** The same counts, printed by `solutions/parser.py` as JSON.
- **Import probe.** Importing prints nothing; the package logger and the root
  logger have 0 handlers each afterwards.
- **Assertion.** A lossy `resolve_duplicates` keeps 9 of the 10 records that
  passed field checks and rejects none, so 9 + 15 = 24 records land against
  25 raw: `AssertionError` with the module's message and exit 1; under `-O`
  the assertion is compiled away, the program prints `24 25` and exits 0.
- **Narrow and broad handlers.** With `"text"` removed from `CONVERTERS`,
  the first field of the first record raises `KeyError('text')`, which
  `except ValueError` does not catch. A handler that catches `Exception`
  turns it into `malformed_inspection_id` and `malformed_plant_id` on every
  record whose id or plant is present: 24 of each (CSV 10 has a blank id and
  JSON 9 a blank plant, which stay `missing`), so 0 accepted and 25 rejected,
  with `CLN-001` carrying exactly those two reasons.
- **Type hints.** `defect_rate(120.0, 3.0)` returns 3.0/120.0 = 0.025 although
  the hints say `int`; `defect_rate("120", "3")` reaches `"3" / "120"` and
  raises `TypeError` inside the function. The annotations literal is the dictionary
  repr CPython 3.12 prints for two `int` parameters and a `float | None`
  return, as the module's handbook quotes it; the naive parser's frame
  reports `f_lineno` 18, the same line `extract_tb` names.

### The naive parser (starters/naive_parser.py)

Line numbers were counted from the file as committed: the loop body's
`units = int(row["inspected_units"])` is line 18 and the script's
`print(parse(list(csv.DictReader(stream))))` is line 29. Walking the CSV,
rows 1 and 2 convert (`"120"`, `"0"`) and are appended; row 3 calls
`int("twelve")`, whose documented refusal is `ValueError: invalid literal for
int() with base 10: 'twelve'`. Walking the JSON, record 1 converts and record 2
calls `int(None)`: `TypeError: int() argument must be a string, a bytes-like
object or a real number, not 'NoneType'`. `CLS-003` alone reaches
`row["inspected_units"]` for an absent key: `KeyError('inspected_units')`.
`int(True)` is 1 and `int(12.5)` is 12, and neither record trips the naive
checks (1 ≥ 0, 12 ≥ 0, 0 ≤ units), so both are accepted with wrong quantities.

### The unfilled starter

Traced by hand through the starter's five gaps. On the JSON, `not
raw.get(name)` is true for `None`, an absent key and every `0`, so every record
with `defective_units` 0 collects `missing_defective_units`: `CLS-002` →
`missing_inspected_units, missing_defective_units`; `CLS-005` →
`missing_defective_units` (its `12.5` is never examined); `CLS-007` → both
missing. Accepted: `CLS-001`, `CLS-004`, `CLS-008`. On the CSV every value is a
non-empty string or `""`, so zero passes; the walk reaches row 11 and
`Decimal("4,25")` raises `InvalidOperation`, which the starter's `except
ValueError` does not catch.

## fixtures/transfer-inspections.csv (plant TM-A, 9 rows)

| pos | id | on | insp | def | cost | outcome |
|---|---|---|---|---|---|---|
| 1 | TMA-001 | 2026-08-01 | 60 | 1 | 2.00 | accepted; 1/60 = 0.016666666666666666 (nearest double); cost prints `2.00` |
| 2 | TMA-001 | 2026-08-01 | 60 | 1 | 2.00 | exact_duplicate |
| 3 | TMA-003 | 2026-08-02 | 7 | 7 | 2.00 | passes alone (7 ≤ 7); conflicts with 8 → conflicting_duplicate |
| 4 | TMA-004 | 2026-08-02 | 1_000 | 0 | 2.00 | underscore fails the digit pattern → malformed_inspected_units |
| 5 | TMA-005 | 2026-08-03 | 10 | 0 | -2.00 | converts to −2.00 < 0 → negative_unit_cost |
| 6 | TMA-006 | (empty) | 10 | 0 | 2.00 | missing_inspected_on |
| 7 | TMA-007 | 2026-08-03 | 10 | 0 | abc | malformed_unit_cost |
| 8 | TMA-003 | 2026-08-02 | 7 | 6 | 2.00 | payload differs from 3 → conflicting_duplicate |
| 9 | TMA-009 | 2026-08-04 | 25 | 0 | 2.5 | accepted; 0/25 = 0.0 (a real rate, unlike 0/0) |

`expected/transfer.json`: 2 accepted, 7 rejected, six reason kinds. The log
holds positions 4, 5, 6, 7 (field rejections while reading) and then 2, 3, 8
(duplicate rejections while walking the accepted list in order 1, 2, 3, 8,
9). **Altered:** a copy with row 9's `defective_units` set to `"26"` gives
26 > 25, so row 9 is `defective_exceeds_inspected`: 1 accepted, 8 rejected.

## expected/conversions.json and expected/policy.json

`conversions.json` states what the interpreter does, one expression per row,
written by hand from the documented behaviour of `int()`, `float()`,
`Decimal`, `date.fromisoformat`, `json`, truth-value testing and comparisons
(for example `int()` accepts surrounding whitespace and underscores between
digits and truncates a float toward zero; `bool` is a subclass of `int`;
`Decimal(float)` converts the exact binary value; `date.fromisoformat` accepts
the basic format `20260903` since 3.11; `json.dumps` refuses a `Decimal`).
The runner holds one callable per row and compares `repr()` of the result, or
`ExceptionType: message`, with the literal; the expression column and the
callable must say the same thing.

`policy.json` sets the constructor's answer beside the contract's for twenty
inputs. The policy column follows from the contract table above; the builtin
column from the same documentation. A result is printed with `str()`; a
refusal is the exception's name (`InvalidOperation` for `Decimal("4,25")`,
which is not a `ValueError`).
