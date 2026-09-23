# Lab L01 — Python parsing under a contract

**Execution class: R (local-executed), plain Python.** Everything runs under
`/usr/bin/python3.12` (CPython 3.12.3) with the standard library only
(`argparse`, `csv`, `datetime`, `decimal`, `json`, `logging`, `pathlib`, `re`,
`traceback`, `unittest`). No packages, no Spark, no Java, no network, no
Databricks.

## Purpose and outcome

Two fictional Cinderline plants send the same inspection facts in two shapes:
plant CL-N as CSV text, plant CL-S as a JSON array. The values arrive as
whatever the reader produced — strings from `csv`, `int`/`float`/`bool`/`None`
from `json` — and some of them are wrong in ways Python will happily accept.
This lab turns both deliveries into one small typed contract and keeps every
record it refuses, with the reason, so that a count at the end can be trusted.

After the lab you can:

1. say which Python type every value arrived as: a CSV cell is always a `str`
   and an empty cell is `""`; a JSON `null` is `None`, `true` is `True`, `12.5`
   is a `float`, and a key that was never sent is simply absent;
2. convert under a written policy instead of whatever `int()`, `Decimal()` and
   `date.fromisoformat()` accept — `int(True)` is `1`, `int(12.5)` is `12`,
   `int("1_000")` is `1000`, `Decimal(5.1)` is a binary fraction — and name each
   refusal: `missing_`, `null_`, `malformed_`, `negative_`, the cross-field
   rule, an exact duplicate, a conflicting duplicate;
3. keep every record: accepted with Python types (`int`, `date`, `Decimal`), or
   rejected with its raw input, its position and its reasons, reconciled by an
   assertion that states the code's own invariant;
4. log each rejection through a named logger that the importing program
   configures, and keep the result on stdout and the log on stderr;
5. read a traceback bottom-up to the failing line and the failing input, and
   say why the naive parser's crash loses the records it had already parsed;
6. write small `unittest` tests against hand-authored literals, including a
   deliberately failing example, an altered-input transfer and a test that
   proves the starter's gaps are real.

## Prerequisites

Reading SQL and a small CSV and JSON file. The optional Python bridge lesson
for SQL-fluent learners covers dictionaries, lists and a first parser; the
module *Python for dependable data work* teaches every construct used here
before relying on it. No Python installation beyond 3.12 is needed.

## Setup and run

```sh
cd lab-l01-python-parsing
python3.12 run_tests.py --evidence local-evidence.json   # 36 tests, 0 failures, 0 errors, 0 skipped, exit 0
python3.12 run_tests.py --starter                          # judge starters/parser.py by the same literals
python3.12 starters/naive_parser.py                        # the deliberately failing example: read its traceback
python3.12 solutions/parser.py --csv fixtures/inspections.csv --json fixtures/inspections.json
python3.12 mutation_check.py                              # optional: fourteen one-line defects, each must fail a test
```

The last command prints the result as JSON on stdout and eighteen `WARNING`
lines on stderr; redirect them separately (`> result.json 2> rejects.log`) to
see that they are two streams. `--evidence` writes the interpreter, versions,
start and end times, test counts and the SHA-256 of every fixture, expected,
starter and solution file and of every produced output.

`requirements.txt` lists no packages because there are none; the interpreter
is the whole environment, so its version is recorded in the evidence. To
isolate the lab anyway:

```sh
python3.12 -m venv .venv
. .venv/bin/activate          # on Windows: .venv\Scripts\activate
python run_tests.py
deactivate
rm -rf .venv
```

That path was executed once for this package with
`python3.12 -m venv --without-pip` in a temporary directory: 36 tests passed,
and the fixture and output hashes were identical to the run outside the
environment. When a later lab needs packages, this is where `python -m pip
install -r requirements.txt` and exact `name==version` pins come in.

## Layout

```
README.md  TASKS.md  SOLUTIONS.md  DATA.md  requirements.txt  run_tests.py  mutation_check.py
fixtures/  inspections.csv           plant CL-N, 15 rows
           inspections.json          plant CL-S, 10 records
           transfer-inspections.csv  plant TM-A, 9 rows (the transfer delivery)
expected/  primary.json  transfer.json   hand-authored results (derivations in DATA.md)
           conversions.json              what the interpreter does (43 expressions)
           policy.json                   what the contract decides (20 inputs)
starters/  parser.py (five marked gaps)  naive_parser.py (deliberately wrong)
solutions/ parser.py
```

## Failure states and cleanup

A failing test prints both values. As shipped, `starters/parser.py` crashes on
the CSV with `InvalidOperation` at `CLN-011` (`"4,25"`) because `Decimal()`
does not raise `ValueError`; fill GAP 2 first and the remaining failures name
one gap each. The most common mistake after that is `if not raw.get(name)`,
which turns a JSON `0` into "missing". The runner sets
`sys.dont_write_bytecode` and starts every subprocess with `-B`, so no
`__pycache__` appears. The only file the lab writes is the evidence JSON at the
path you chose (and `result.json`/`rejects.log` if you redirected the script);
delete them when done, and remove `.venv` if you created one.

## Limits and honesty

The contract, the reason codes and the duplicate rule are an **original
fictional teaching policy**, not a Databricks, Lakeflow or Delta behaviour.
Twenty-five and nine records say nothing about scale or performance; a pure
Python loop is the right tool for learning conversions and the wrong one for a
distributed table. The tests prove that the stated rules behave as described
on these inputs with CPython 3.12.3 — `date.fromisoformat()` accepts
`"20260903"` only since 3.11, and `float | None` in an annotation needs 3.10 —
and nothing about other interpreters. Cinderline, its plants and every record
are fiction. A local pass is evidence about this code, not a measure of the
learner.
