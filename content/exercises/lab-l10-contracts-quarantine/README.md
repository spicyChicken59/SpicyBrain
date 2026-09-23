# Lab L10 — Data contracts and quarantine

**Execution class: R (local-executed), plain Python.** Everything runs under
`/usr/bin/python3.12` (CPython 3.12.3) with the standard library (`csv`,
`datetime`, `json`, `re`, `unittest`). No Spark, no Java, no packages, no
network, no Databricks.

## Purpose and outcome

A contract is a promise about data written down precisely enough that a
program can check it and a reader can name what broke. This lab gives you a
small fictional contract (`fixtures/contract.json`) for a plant inspection
feed delivered as CSV text, a delivery that breaks it in fifteen distinct
ways, a manifest that lies about how many rows were sent, and a second
plant's delivery that breaks it differently and is nevertheless publishable.

After the lab you can:

1. separate **schema** checks (required fields, types, minimums), **key**
   presence, **quantity** rules (non-negative, defects ≤ inspected, a zero
   denominator that yields `null` rather than `0.0` or a crash) and
   **referential** checks (a plant must exist in the dimension, exactly and
   case-sensitively) — each producing a named reason on the row it rejects;
2. explain why some rules are **cross-record**: uniqueness of
   `(inspection_id, version)`, uniqueness of `event_id`, a monotonic rule
   (`revised_at` may not go backwards as `version` goes forwards) and the
   manifest's row count — and show with a test that row-level checks alone
   can pass every one of those rows and cannot see the manifest at all;
3. keep three outcomes apart: rows **quarantined with reasons** (disclosed, not
   blocking), **contradictions** (blocking), and **batch failures** such as a
   manifest mismatch or a missing column (blocking); `publication_allowed`
   is true only with no contradiction and no batch failure;
4. say why a validator that "passes everything" is worse than none, and what a
   test that proves it must assert.

What leaves this validator is a set of **contract-valid rows**, not the
current state of each inspection; choosing the latest revision and blocking
on ambiguous history is Lab L06's job, downstream.

## Prerequisites

Lessons `dbxfe-m04-l02` (identity and ordering) and `dbxfe-record-resolution`
(quarantine with reasons), and reading a small CSV and JSON. Lab L01 (Python
parsing) helps but is not required.

## Setup and run

```sh
cd lab-l10-contracts-quarantine
python3.12 run_tests.py --evidence local-evidence.json
python3.12 solutions/validator.py                     # prints the primary result as JSON
python3.12 solutions/validator.py --csv fixtures/transfer-inspections.csv \
  --plants fixtures/transfer-plants.csv --manifest fixtures/transfer-manifest.json
```

`requirements.txt` lists no packages. A passed run is 19 tests, 0 failures,
0 errors, **0 skipped**, exit 0; `--evidence` writes versions, times, counts
and the SHA-256 of every fixture, expected, solution and starter file and of
every produced output. Work through `TASKS.md` first; `starters/validator.py`
has six marked gaps and `starters/permissive_validator.py` is deliberately
wrong. Open `SOLUTIONS.md` and `solutions/` after your attempt.

## Layout

```
README.md  TASKS.md  SOLUTIONS.md  DATA.md  requirements.txt  run_tests.py
fixtures/  contract.json  plants.csv  inspections.csv  manifest.json          (Cinderline delivery, 20 rows, manifest says 21)
           transfer-plants.csv  transfer-inspections.csv  transfer-manifest.json  (Tessmoor delivery, 12 rows, manifest agrees)
expected/  primary.json  transfer.json                                        (hand-authored literals; derivations in DATA.md)
starters/  validator.py (six gaps)  permissive_validator.py (deliberately wrong)
solutions/ validator.py
```

## Failure states and cleanup

A failing test prints both values. The most common mistake while filling the
starter is turning an empty cell into `0` — the tests then fail on row 15
(`missing_inspected_units`) and on the zero-denominator row. The runner sets
`sys.dont_write_bytecode`, so no `__pycache__` appears. The only file the lab
writes is the evidence JSON at the path you chose; delete it when done.

## Limits and honesty

The contract, reason codes and publication rule are an **original fictional
teaching policy**. They are not Lakeflow/DLT expectations, not a Databricks
product behaviour and not a claim about any connector. A manifest count is
one weak completeness signal, not proof that every source record arrived. The
validator is a few hundred lines of Python over twenty rows; it says nothing
about scale, performance or production operation. Plant and inspection
records are fiction. A local pass shows the stated rules behave as described
on these inputs; it is not evidence of mastery.
