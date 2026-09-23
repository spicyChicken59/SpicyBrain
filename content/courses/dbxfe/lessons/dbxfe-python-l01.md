<!-- section:dbxfe-python-l01-outcome -->

After this lesson you can take a CSV file and a JSON file from two fictional Cinderline plants and say, for every
record, which Python type each value arrived as, whether it becomes an accepted row with real types or a rejection
with its raw input and a named reason, and how the counts reconcile. You can read the traceback of a parser that
failed, decide what belongs in an assertion, a log line or a test, and record the interpreter and pinned packages
that make a result repeatable. Everything runs locally with CPython 3.12 and the standard library.

<!-- section:dbxfe-python-l01-start -->

Bring SQL: rows keyed by column, result sets, NULL, GROUP BY and DISTINCT. No Python is assumed; each construct is
shown before it is relied on. For a gentler first pass, the optional
[Python for a SQL-fluent learner](#/lesson/dbxfe-python-bridge) builds a first parser; this lesson does not repeat it
and goes further. The same records appear in Lab L01 (Python parsing) on the lab shelf, where every output quoted
here was executed.

<!-- section:dbxfe-python-l01-values -->

Every value has a type, and Python never casts text to a number during a comparison:

```python
>>> "12" == 12
False
>>> isinstance(True, int), type(True) is int
(True, False)
>>> 0.1 + 0.2
0.30000000000000004
```

`bool` is a subclass of `int`, so `True` passes `isinstance(value, int)` and counts as 1 in arithmetic, and a float
is a binary approximation. A dictionary maps unique keys to values: one row keyed by column. A list keeps records in order: a
result set without a schema, since nothing checks that each dictionary has the same keys or types. A tuple is an
immutable group such as a composite key; a set holds distinct hashable values, like DISTINCT:

```python
>>> len({"CL-N", "CL-S", "CL-N"})
2
>>> {"inspection_id": "CLN-001"}.get("unit_cost")    # None; square brackets would raise KeyError
```

<!-- section:dbxfe-python-l01-missing -->

A JSON record can omit a key, send `null` (Python `None`), send `""` or send `0`. A CSV row can only send text, so
its empty cell is `""`. `None`, `""` and `0` are all false in a truth test, so `if not raw.get(name)` merges four
facts and rejects a real zero. Test the key, then the value:

```python
if name not in raw or is_blank(raw[name]):   # absent or blank text: missing_
    ...
if raw[name] is None:                         # present null: null_
    ...
```

Unlike SQL's `NULL = NULL`, `None == None` is `True`, and `None < 0` raises `TypeError`.

<!-- section:dbxfe-python-l01-conversions -->

A converter returns one type or raises `ValueError`. The built-in constructors accept more than a contract wants:

| input | built-in | contract |
|---|---|---|
| `12.5` | `int` → 12 | malformed |
| `True` | `int` → 1 | malformed |
| `"1_000"` | `int` → 1000 | malformed |
| `5.1` | `Decimal` → 5.0999999999999996447… | `Decimal('5.1')` via `str()` |
| `"4,25"` | `Decimal` → `InvalidOperation` | malformed |
| `"20260903"` | `date.fromisoformat` → a date (3.11+) | malformed |

```python
def to_integer(value: object) -> int:
    if type(value) is int:
        return value
    if isinstance(value, str) and INTEGER_TEXT.match(value.strip()):
        return int(value.strip())
    raise ValueError("not an integer")
```

`def` names a function, `->` documents the result type and `raise` refuses. Costs become `Decimal` from text,
never through float arithmetic.

<!-- section:dbxfe-python-l01-files -->

Open a file in a `with` block, so it is closed even if parsing fails, and name the encoding:

```python
with open(path, encoding="utf-8", newline="") as stream:
    rows = list(csv.DictReader(stream))
```

`DictReader` returns one dictionary per row keyed by the header, and every value is a `str`: `CLN-008` arrives as
`' 15 '` and `''`. `json.load` maps `null` to `None`, `true` to `True`, `80` to int and `12.5` to float, and an unsent
key is simply absent. A wrong path raises `FileNotFoundError`; invalid JSON raises `json.JSONDecodeError`.

<!-- section:dbxfe-python-l01-contract -->

The lab's parser checks each field in contract order and keeps every record:

```python
def validate(raw, contract=CONTRACT):
    typed, reasons = {}, []
    for field in contract:
        value, reason = check_field(field, raw)
        typed[field["name"]] = value
        if reason:
            reasons.append(reason)
    if not reasons and typed["defective_units"] > typed["inspected_units"]:
        reasons.append("defective_exceeds_inspected")
    return typed, reasons
```

`parse_records` walks `enumerate(records, start=1)`, so a rejection keeps its position, raw dictionary and reasons.
`resolve_duplicates` groups with `groups.setdefault(id, []).append(record)`, a GROUP BY, and compares a set of payload
tuples: one distinct payload is an exact repeat, more is a conflict. Primary delivery: 25 received, 7 accepted, 18
rejected with 19 reasons.

<!-- section:dbxfe-python-l01-errors -->

The naive parser trusts `int()` and stops at `CLN-003` (path shortened):

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

Read upward: the exception, then the innermost frame, then its caller. The two records it had accepted died with the
frame. `except ValueError` around the one converter call turns a refusal into a reason; anything else is a bug and
should crash. An `assert` checks the code's own promise and disappears under `python -O`.

<!-- section:dbxfe-python-l01-tooling -->

```python
log = logging.getLogger("cinderline.parsing")
log.warning("rejected %s position %d: %s", source, position, ", ".join(reasons))
```

The module asks for a named logger and never configures it; `main()` calls `logging.basicConfig(...)` with
`stream=sys.stderr`, so results go to stdout and the log to stderr. Importing the module runs only its top level, and the file ends with:

```python
if __name__ == "__main__":
    raise SystemExit(main())
```

Hints such as `-> float | None` document intent; the runtime does not enforce them, so `defect_rate(120.0, 3.0)`
quietly returns 0.025.

<!-- section:dbxfe-python-l01-tests -->

A unittest test compares the code with a literal written by hand:

```python
def test_null_and_missing_are_different_reasons(self):
    self.assertEqual(rejected_at(self.result, "inspections.json", 2)["reasons"],
                     ["null_inspected_units"])
```

Lab L01 runs 36 such tests, including a deliberately failing example and an altered-input transfer. For the
environment: `python3.12 -m venv .venv`, activate it, install `name==version` pins from `requirements.txt`, often
written with `python -m pip freeze`, and record `sys.version` with every result.

<!-- section:dbxfe-python-l01-exercise -->

Plant TM-A sends nine rows under the same header:

```text
TMA-001,TM-A,2026-08-01,60,1,2.00
TMA-001,TM-A,2026-08-01,60,1,2.00
TMA-003,TM-A,2026-08-02,7,7,2.00
TMA-004,TM-A,2026-08-02,1_000,0,2.00
TMA-005,TM-A,2026-08-03,10,0,-2.00
TMA-006,TM-A,,10,0,2.00
TMA-007,TM-A,2026-08-03,10,0,abc
TMA-003,TM-A,2026-08-02,7,6,2.00
TMA-009,TM-A,2026-08-04,25,0,2.5
```

For each row write accepted, with its defect rate, or its reasons; then the order of the WARNING lines. Then set row
9's `defective_units` to `"26"` and predict again.

<!-- section:dbxfe-python-l01-solution -->

Accepted: row 1 (rate 0.016666666666666666; cost `2.00` keeps its scale) and row 9 (rate 0.0, a real rate, unlike 0
of 0). Rejected: row 2 `exact_duplicate` (row 1 kept); rows 3 and 8 `conflicting_duplicate` (7 against 6 defective);
row 4 `malformed_inspected_units`, although `int("1_000")` is 1000; row 5 `negative_unit_cost`; row 6
`missing_inspected_on`; row 7 `malformed_unit_cost`. So 9 = 2 + 7. The log lists positions 4, 5, 6, 7 while reading,
then 2, 3, 8 while resolving duplicates. With 26 defective of 25, row 9 becomes `defective_exceeds_inspected`: 1
accepted, 8 rejected. These are the lab's authored literals, and its tests pass.

<!-- section:dbxfe-python-l01-mistakes -->

- `if not value` rejects a real zero; test the key, then `is None`.
- Trusting `int()`, `Decimal()` or `date.fromisoformat()` accepts `True`, `12.5`, `"1_000"`, `"1e3"` or `"20260903"`.
- `Decimal(5.1)` keeps the binary fraction; build from text.
- `except Exception` turns code bugs into plausible data rejections.
- An input rule written as `assert` vanishes under `-O`.
- `logging.basicConfig()` inside a library hijacks its caller's logging.
- Expected results produced by the code under test prove nothing.
- A loop over 25 records is learning code; distributed tables belong to DataFrames.

<!-- section:dbxfe-python-l01-sources -->

Language and library behaviour comes from the CPython 3.12 documentation: the tutorial chapters on data structures,
input and output, modules, errors and virtual environments; the library pages for built-in functions and types, csv,
json, decimal, datetime, logging, unittest, typing and venv; the assert statement in the language reference; and
pip's repeatable-installs guidance. The contract, reason codes and records are original fiction. Every quoted output
was executed in Lab L01 with CPython 3.12.3; nothing ran on Databricks.

<!-- section:dbxfe-python-l01-related -->

[Python for a SQL-fluent learner](#/lesson/dbxfe-python-bridge) is the optional first pass.
[DataFrames, schemas, and column expressions](#/lesson/dbxfe-dataframes) moves these records into a typed,
distributed table, and [Duplicates, invalid records, and conflicts](#/lesson/dbxfe-record-resolution) extends the
duplicate rule to revisions and replays. Lab L10 (contracts and quarantine) adds manifests and cross-record rules.

<!-- section:dbxfe-python-l01-revisit -->

Explain from memory why `0`, `None`, `""` and an absent key need four different tests, then compare with the cards.
Opening or revealing an answer records nothing; mark completion only when you choose.
