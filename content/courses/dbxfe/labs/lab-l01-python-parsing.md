# Lab L01 — Python parsing under a contract

*Local-executed (R), plain CPython 3.12.3, standard library only. Nothing to
install; nothing runs on Databricks, Spark or any cloud service.*

## What this lab is for

Before a Spark job, a notebook or a dashboard, somebody's Python reads a file.
This lab is that moment done carefully. Two fictional Cinderline plants send
the same inspection facts in two shapes — plant CL-N as fifteen CSV rows,
plant CL-S as a JSON array of ten records — and a third plant, TM-A, sends a
transfer delivery that breaks the same rules differently. You turn every
record into typed Python values under one small contract, or refuse it with a
named reason and keep its raw input, so that `7 accepted + 18 rejected = 25
received` is a checkable sentence rather than a hope.

## The contract, briefly

Six fields. `inspection_id` and `plant_id` are required text; `inspected_on`
is a real calendar date written `YYYY-MM-DD`; `inspected_units` and
`defective_units` are integers of at least 0; `unit_cost` is an optional
non-negative `Decimal`. Reasons come in field order — `missing_` (key absent
or blank), `null_` (a present `None`), `malformed_` (conversion refused),
`negative_` — then `defective_exceeds_inspected` when every field passed,
then `exact_duplicate` or `conflicting_duplicate` across records. The defect
rate is `defective / inspected`, or `None` when nothing was inspected.

## The deliveries and what happens to each record

| source | pos | what arrives | outcome |
|---|---|---|---|
| CSV | 1 | CLN-001, 120 / 3, cost 4.25 | accepted, rate 0.025 |
| CSV | 2 | CLN-002, 0 / 0 | accepted, rate `None` |
| CSV | 3 | `twelve` units | malformed_inspected_units |
| CSV | 4 | empty units cell | missing_inspected_units |
| CSV | 5 | −5 units | negative_inspected_units |
| CSV | 6 | 45 defective of 40 | defective_exceeds_inspected |
| CSV | 7 | date `2026/09/03` | malformed_inspected_on |
| CSV | 8, 13 | CLN-008 twice: ` 15 ` and 16 units | conflicting_duplicate (both) |
| CSV | 9 | `12.0` units | malformed_inspected_units |
| CSV | 10 | empty id | missing_inspection_id |
| CSV | 11 | cost `"4,25"` | malformed_unit_cost |
| CSV | 12 | CLN-001 repeated exactly | exact_duplicate (1 kept) |
| CSV | 14 | CLN-014, 200 / 4, cost 3.90 | accepted, rate 0.02 |
| CSV | 15 | −10 / −1 | two negatives |
| JSON | 1, 4 | 80 / 2; `"64"` / 1 | accepted (0.025; 0.015625) |
| JSON | 2 | units `null` | null_inspected_units |
| JSON | 3 | units key absent | missing_inspected_units |
| JSON | 5, 6 | `12.5`; `true` | malformed_inspected_units |
| JSON | 7 | 0 / 0, cost `5.1` (a float) | accepted, rate `None`, cost `5.1` |
| JSON | 8 | 50 / 1, cost `null` (optional) | accepted, cost `None` |
| JSON | 9 | plant `""` | missing_plant_id |
| JSON | 10 | date `2026-09-31` | malformed_inspected_on |

Every value in `expected/primary.json` was derived by hand from this table
before the solution was run; the lab's `DATA.md` shows each derivation.

## Task 1 — what the readers hand you

`csv.DictReader` returns one dictionary per row, keyed by the header, and
every value is a `str`: CSV row 8 gives `' 15 '` with its spaces and `''` for
the empty cost. `json.load` returns typed values: `None` for `null`, `True`
for `true`, `12.5` and `5.1` as floats, `"64"` as text, and nothing at all
for a key that was never sent. A dictionary is a row keyed by column; a list
of dictionaries is a result set without a schema. Nothing in either reader
knows the contract.

## Task 2 — the deliberately failing example

The naive parser trusts `int()`. Run on the CSV, it prints this to stderr and
exits with status 1 (path shortened):

```text
Traceback (most recent call last):
  File ".../starters/naive_parser.py", line 29, in <module>
    print(parse(list(csv.DictReader(stream))))
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File ".../starters/naive_parser.py", line 18, in parse
    units = int(row["inspected_units"])
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^
ValueError: invalid literal for int() with base 10: 'twelve'
```

Read it from the bottom: the exception and the text it choked on; the
innermost frame (line 18 in `parse`, carets under the failing expression);
the outer frame that called it. The input is not printed, but `'twelve'`
points at row 3, `CLN-003`, and the test reads the frame's local `row` to
prove it. The two records already appended to the local list were lost when
the exception unwound the frame, so nothing was printed at all. On the JSON
the same line raises `TypeError` for `CLS-002`, because `int(None)` is a type
error; where it does not crash it is wrong: `True` becomes 1 unit and `12.5`
becomes 12.

## Tasks 3 and 4 — conversion policies

| input | the constructor says | the contract says |
|---|---|---|
| `"1_000"` | `int` → 1000 | malformed |
| `12.5` | `int` → 12 | malformed |
| `True` | `int` → 1; `Decimal` → 1 | malformed |
| `5.1` (float) | `Decimal` → 5.0999999999999996447286321199499070644378662109375 | `Decimal('5.1')` via `str()` |
| `"4,25"` | `Decimal` → InvalidOperation | malformed (a `ValueError`) |
| `"1e3"`, `"NaN"` | `Decimal` → 1E+3, NaN | malformed |
| `"20260903"` | `date.fromisoformat` → 2026-09-03 (3.11+) | malformed |
| `"2026-09-31"` | ValueError: day is out of range for month | malformed |

A regular expression decides what text counts; the constructor only converts
text that already passed. Every refusal becomes one exception type,
`ValueError`, which the field check catches.

## Tasks 5 to 7 — four states, one cross-field rule, duplicates

`check_field` asks `name not in raw` (the key), then `raw[name] is None` (the
value), never "is it falsy", so a zero reaches the converter and passes.
`validate` adds `defective_exceeds_inspected` only when no field failed —
`CLN-005` (0 of −5) and `CLN-015` (−1 of −10) would satisfy the comparison
and do not collect it. Duplicates are found with a dictionary of lists keyed
by `inspection_id` and a set of payload tuples: `CLN-001` has one distinct
payload (keep position 1, reject 12); `CLN-008` has two (reject both).

## Tasks 8 and 9 — script, module, transfer

Run as a script, the solution prints one JSON document on stdout and eighteen
lines such as `WARNING cinderline.parsing: rejected inspections.csv position
3: malformed_inspected_units` on stderr. Imported, it prints nothing and adds
no logging handler: the work sits under `if __name__ == "__main__":`.

The TM-A delivery (9 rows) yields 2 accepted and 7 rejected: an exact repeat,
a conflicting pair (7 against 6 defective), `1_000`, a cost of `-2.00`, a
blank date and a cost of `abc`. The log lists positions 4, 5, 6, 7 and then
2, 3, 8 — processing order, not position order. Changing row 9's defective
units to 26 in a copy flips it to `defective_exceeds_inspected`: 1 accepted,
8 rejected, and the original rows are untouched.

## Task 10 — an assertion is not a validation

`parse_delivery` ends with `assert len(accepted) + len(rejected) ==
raw_count`. A deliberately lossy duplicate step that drops one record fails it
with `AssertionError: every record is accepted or rejected exactly once` and
exit status 1. Under `python -O` the assertion is compiled away: the same
program prints `24 25` and exits 0. Invariants of your own code may be
asserted; rules about input may not.

The same run shows why the field check catches only `ValueError`. With one
converter removed from `CONVERTERS` — a bug in the code — the narrow handler
lets `KeyError: 'text'` crash with a traceback; a copy that catches
`Exception` reports all 25 records as rejected with `malformed` ids and plants
and never crashes, turning a code defect into a complaint about the plants.

## What the tests prove and do not prove

The final run executed 36 `unittest` tests with 0 failures, 0 errors and 0
skipped under `/usr/bin/python3.12` (CPython 3.12.3); the evidence records the
SHA-256 of every fixture, expected, starter and solution file and of every
produced output. Six tests prove the starter's five gaps are real and that the
literals reject it; fourteen deliberate mutations of the solution were each
caught by the tests named for that defect, and `python mutation_check.py` in the
package re-runs all fourteen against temporary copies. A single extra run inside
a fresh `python3.12 -m venv --without-pip` environment produced identical
hashes; that run is not the recorded evidence file. The
tests do not prove anything about scale, other interpreters (the date and
annotation behaviour needs 3.11 and 3.10), real plant data, or Databricks.

## Setup and cleanup

From the unzipped package: `python3.12 run_tests.py --evidence
local-evidence.json`, `python3.12 run_tests.py --starter`, `python3.12
starters/naive_parser.py`. The runner writes no bytecode; the only file
created is the evidence JSON you named. Delete it, and any `.venv`,
`result.json` or `rejects.log` you made, when done.
