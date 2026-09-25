# Solutions

Read this after your own attempt. The complete program is
`solutions/parser.py`; this file explains it in the order a record travels,
shows the intermediate values, and ends with three wrong approaches and why
they fail.

## 1. What the readers hand you

`read_csv` opens the file with `encoding="utf-8", newline=""` inside a `with`
block, so the file is closed even if reading fails, and `csv.DictReader` uses
the header row as the keys. Every value is a `str`; an empty cell is `""`.
`read_json` uses `json.load`, which maps `null` to `None`, `true` to `True`,
`80` to `int`, `12.5` and `5.1` to `float`, and leaves an unsent key absent.
The same logical fact therefore arrives in five shapes:

| record | `inspected_units` as read | type |
|---|---|---|
| CSV `CLN-008` | `' 15 '` | `str` |
| CSV `CLN-004` | `''` | `str` |
| JSON `CLS-002` | `None` | `NoneType` |
| JSON `CLS-003` | key absent | — |
| JSON `CLS-006` | `True` | `bool` |

Nothing in either reader knows the contract. That is the parser's job.

## 2. The converters (GAPs 1 and 2)

```python
def to_integer(value: object) -> int:
    if type(value) is int:                       # True is an int subclass; type() excludes it
        return value
    if isinstance(value, str) and INTEGER_TEXT.match(value.strip()):
        return int(value.strip())
    raise ValueError("not an integer")

def to_decimal(value: object) -> Decimal:
    if isinstance(value, bool):
        raise ValueError("not a decimal")
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        result = Decimal(str(value))              # '5.1', not 5.0999999999999996447...
        if not result.is_finite():
            raise ValueError("not a finite decimal")
        return result
    if isinstance(value, str) and DECIMAL_TEXT.match(value.strip()):
        return Decimal(value.strip())
    raise ValueError("not a decimal")
```

The regular expressions decide what text counts, not the constructors:
`int()` accepts `"1_000"` and `Decimal()` accepts `"1e3"` and `"NaN"`, and the
contract refuses all three. Every refusal is a `ValueError`, one exception type
the caller can catch. `to_date` does the same with `ISO_DATE_TEXT` before
`date.fromisoformat`, which since Python 3.11 also accepts `"20260903"`;
`"2026-09-31"` passes the pattern and is refused by the calendar ("day is out of
range for month"). `expected/policy.json` lists twenty inputs with the
constructor's answer beside the contract's.

## 3. Four states, then one cross-field rule (GAPs 3 and 4)

```python
def check_field(field, raw):
    name = field["name"]
    if name not in raw or is_blank(raw[name]):
        return None, ("missing_" + name if field["required"] else None)
    if raw[name] is None:
        return None, ("null_" + name if field["required"] else None)
    try:
        value = CONVERTERS[field["type"]](raw[name])
    except ValueError:
        return None, "malformed_" + name
    if "minimum" in field and value < field["minimum"]:
        return value, "negative_" + name
    return value, None
```

`name not in raw` asks about the key; `raw[name] is None` asks about the value;
neither asks about truthiness, so `0` reaches the converter and passes.
`validate` collects one reason per field in contract order and adds
`defective_exceeds_inspected` only when the list is still empty. Intermediate
values for four CSV rows:

| row | typed after `check_field` | reasons |
|---|---|---|
| 1 `CLN-001` | 120, 3, `Decimal('4.25')`, `date(2026, 9, 1)` | none → rate 0.025 |
| 2 `CLN-002` | 0, 0, `Decimal('4.25')` | none → rate `None` |
| 5 `CLN-005` | −5, 0 | `negative_inspected_units` only |
| 6 `CLN-006` | 40, 45 | `defective_exceeds_inspected` |

`defect_rate` returns `None` when nothing was inspected: 0 of 0 has no rate,
and `0.0` would claim a perfect plant.

## 4. Every record lands once (GAP 5 and the assertion)

`parse_records` walks `enumerate(records, start=1)` so each record keeps a
1-based position; a rejected record keeps its `raw` dictionary untouched and
is logged with `log.warning("rejected %s position %d: %s", ...)`.
`resolve_duplicates` groups with `groups.setdefault(id, []).append(record)` and
measures distinct payloads with a set of tuples — a tuple, unlike a list or a
dictionary, can be a set member:

| inspection_id | positions | distinct payloads | outcome |
|---|---|---|---|
| `CLN-001` | 1, 12 | 1 | keep 1; 12 `exact_duplicate` |
| `CLN-008` | 8, 13 | 2 (15 vs 16 units) | both `conflicting_duplicate` |

`parse_delivery` then asserts `len(accepted) + len(rejected) == raw_count`
(7 + 18 = 25). The assertion is about this code, not about the data: if a
future edit drops a record, it stops the run. `python -O` removes assertions,
which is why no input rule is written as one.

## 5. Script and module

`main()` configures logging with `logging.basicConfig(... stream=sys.stderr)`,
prints `json.dumps(json_ready(result), indent=2)` on stdout and returns 0;
`json_ready` turns `date` and `Decimal` into text because `json.dumps` refuses
both. The last two lines are the guard:

```python
if __name__ == "__main__":
    raise SystemExit(main())
```

Importing the module runs its top level — the imports, the logger, the
constants — and nothing else. The import probe in the tests confirms that it
prints nothing and that neither the package logger nor the root logger has a
handler afterwards.

## 6. Results

Primary: 25 raw, 7 accepted, 18 rejected, 19 reasons (`CLN-015` carries two),
18 warnings, first `rejected inspections.csv position 3:
malformed_inspected_units`, last `rejected inspections.csv position 13:
conflicting_duplicate`. Transfer: 9 raw, 2 accepted, 7 rejected; the altered
transfer: 1 accepted, 8 rejected. Requiring `unit_cost` in a copied contract:
the JSON delivery drops from 4 accepted to 3 and `CLS-008` is `null_unit_cost`.

## Wrong approach 1: trust `int()` (the naive parser)

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

Read it from the bottom. The last line is the exception type and its message,
which quotes the offending text. The frame above it is the innermost call —
line 18 of `parse` — with carets under the expression that raised. The top
frame is the script line that called `parse`. The input is not printed, but
the message's `'twelve'` and the loop order point to `CLN-003`, and the test
reads the frame's local `row` to prove it. Two records had been appended to
the local `accepted` list; the exception unwound the frame before `return`,
so that list — and any evidence of what was refused — is gone. On the JSON
the same line raises `TypeError` for `CLS-002`, because `int(None)` is a
type error, not a value error; a `try/except ValueError` wrapped around it
would still crash. Where it does not crash it is wrong: `int(True)` is 1 and
`int(12.5)` is 12, and both records would have been counted.

## Wrong approach 2: `except Exception`

Catching everything around the converter call looks defensive. Delete
`"text"` from `CONVERTERS` — a registration lost in a refactor — and the
solution's `except ValueError` lets `KeyError: 'text'` crash out of
`check_field`, with a traceback that names the line. A broad handler catches
the same `KeyError` and converts it into data: all 25 records rejected, every
present id and plant reported `malformed`, 24 of each, and no traceback. A bug
in the code has become a plausible-looking complaint about the plants.

## Wrong approach 3: `if not raw.get(name)`

The starter's shortcut treats every falsy value as missing. On the CSV every
cell is a non-empty string or `""`, so it looks correct. On the JSON it turns
`0` into missing: `CLS-005` is blamed for `missing_defective_units` instead of
its real problem (`12.5`), and the unfilled starter accepts only `CLS-001`,
`CLS-004` and `CLS-008` where the contract accepts four. The same bug hides in
one format and shows in the other; test both.
