# Tasks

Predict on paper before you run anything. Every value you will be checked
against was written by hand before the solution existed (`DATA.md` shows each
derivation), so a prediction you can defend is worth more than a green run.
Work in `starters/parser.py`; judge it with `python3.12 run_tests.py --starter`.

## 1. Say what the readers hand you

Open `fixtures/inspections.csv` and `fixtures/inspections.json`. For CSV row 8
(`CLN-008`) and JSON records 2, 3, 6 and 7, write the value and the Python type
that `read_csv` / `read_json` produce for `inspected_units` and `unit_cost`.

Expected behaviour: CSV row 8 gives `' 15 '` (`str`, spaces kept) and `''`
(`str`, an empty cell is an empty string, not `None`). JSON 2 gives `None`
for the quantity; JSON 3 has no `inspected_units` key at all; JSON 6 gives
`True` (`bool`); JSON 7 gives `0` (`int`) and `5.1` (`float`). A dictionary
is a row keyed by column name; a list of them is a result set with no schema.

## 2. Read the deliberately failing example

Run `python3.12 starters/naive_parser.py`. From the traceback alone, name the
exception type, the message, the function, the line number and its text, and
the record that failed. Then explain what happened to the two records the
function had already accepted, and predict what the same function does with
the JSON file.

Expected behaviour: `ValueError: invalid literal for int() with base 10:
'twelve'`, raised at line 18 in `parse`, `units = int(row["inspected_units"])`,
for `CLN-003`. The local list held `CLN-001` and `CLN-002`; it died with the
frame, so nothing was printed and the exit status is 1. On the JSON the same
line raises `TypeError` for `CLS-002`, a `None`. Fed only `CLS-003` it raises
`KeyError: 'inspected_units'`. Fed `CLS-006` or `CLS-005` alone it is silently
wrong: `True` becomes 1 unit, `12.5` becomes 12.

## 3. GAP 1 — an integer policy

Make `to_integer` accept only a real `int` (never a `bool`) or text that
matches `INTEGER_TEXT` after trimming. Expected behaviour (the integer rows of
`expected/policy.json`): `"12"`, `" 12 "` and `"-5"` convert; `"12.0"`,
`12.5`, `True`, `"1_000"` and `"twelve"` raise `ValueError`, although `int()`
accepts four of those five.

## 4. GAP 2 — a decimal policy

Make `to_decimal` refuse `bool`, convert an `int`, convert a `float` through
`str()` and refuse it if not finite, and accept text only when it matches
`DECIMAL_TEXT` after trimming. Expected behaviour: `"4.25"` and `"-2.00"`
convert (trailing zeros kept); `5.1` becomes `Decimal('5.1')`, not the binary
fraction; `"4,25"`, `"1_000.50"`, `"1e3"`, `"NaN"` and `True` raise
`ValueError`. Until this gap is filled the starter crashes on `CLN-011` with
`InvalidOperation`, which is not a `ValueError`.

## 5. GAP 3 — four states, four names

Rewrite `check_field` so that an absent key or blank text is `missing_<name>`,
a present `None` is `null_<name>` (both only when the field is required), a
converter's `ValueError` is `malformed_<name>`, and a converted value under the
field's minimum is `negative_<name>`. Zero must pass.

Expected behaviour: JSON 2 → `null_inspected_units`; JSON 3 and CSV 4 →
`missing_inspected_units`; JSON 7 accepted with `defect_rate` `None` (0 of 0 is
not a rate); CSV 5 → `negative_inspected_units`; CSV 15 →
`negative_inspected_units, negative_defective_units`; JSON 8, whose optional
`unit_cost` is `null`, accepted with `unit_cost` `None`.

## 6. GAP 4 — the cross-field rule

When every field passed on its own and `defective_units > inspected_units`,
add `defective_exceeds_inspected`. Expected behaviour: CSV 6 (45 of 40) gets
it; CSV 5 and CSV 15 do not, although `0 > -5` and `-1 > -10` are true,
because they already failed a field.

## 7. GAP 5 — exact and conflicting duplicates

Group the records that passed on their own by `inspection_id` (a dictionary
of lists, the Python form of `GROUP BY`). One distinct typed payload repeated:
keep the first, reject the repeat as `exact_duplicate`. More than one distinct
payload: reject every member as `conflicting_duplicate`. Log each rejection.

Expected behaviour: `CLN-001` at positions 1 and 12 → keep 1, reject 12;
`CLN-008` at 8 and 13 (15 against 16 inspected) → reject both. Totals: 25 raw,
7 accepted, 18 rejected, 19 reasons, 18 `WARNING` lines. Now
`python3.12 run_tests.py --starter` should report 30 tests, all passing.

## 8. Run it as a script and import it as a module

Run `python3.12 starters/parser.py --csv fixtures/inspections.csv --json
fixtures/inspections.json > result.json 2> rejects.log`. Then run
`python3.12 -c "import starters.parser"`. Expected behaviour: `result.json` is
one JSON document; `rejects.log` holds 18 lines that start with `WARNING
cinderline.parsing:`; the import prints nothing, because the script's work
sits under `if __name__ == "__main__":` and the module never configures
logging itself.

## 9. Transfer: a third plant, then an altered record

`fixtures/transfer-inspections.csv` (plant TM-A, 9 rows) breaks the contract
differently. Predict every outcome first. Expected behaviour: 2 accepted
(`TMA-001` at position 1, `TMA-009` with rate `0.0` and cost `2.5`) and 7
rejected: the repeat of `TMA-001` (exact), both `TMA-003` rows (7 against 6
defective, conflicting), `1_000` (malformed), `-2.00` (negative cost), a
blank date (missing) and `abc` (malformed cost). The log lists positions 4,
5, 6, 7 and then 2, 3, 8: processing order, not position order.

Then copy the rows in memory, set row 9's `defective_units` to `"26"` and
parse again. Expected behaviour: 1 accepted, 8 rejected, row 9 rejected with
`defective_exceeds_inspected`, and the original rows unchanged.

## 10. Break it on purpose

In a scratch copy, replace `resolve_duplicates` with a version that silently
drops the last accepted record, and run the delivery normally and with
`python3.12 -O`. Expected behaviour: normally, `AssertionError: every record
is accepted or rejected exactly once` and exit 1; under `-O`, the assertion is
gone, the program prints `24 25` and exits 0. Write two sentences on why an
input rule must never be written as an `assert`.

Then simulate a code bug: delete `"text"` from `CONVERTERS` for one run.
Expected behaviour: the solution's narrow `except ValueError` lets the
`KeyError: 'text'` crash out of `check_field` with a traceback; a copy of
`check_field` that catches `Exception` instead reports all 25 records as
rejected (`CLN-001` with `malformed_inspection_id, malformed_plant_id`) and
nothing crashes. Say which of the two runs you would rather be paged for.
