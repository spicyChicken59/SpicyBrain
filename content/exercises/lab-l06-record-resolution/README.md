# Lab L06 — Record resolution: retained evidence, current state, publication

**Execution class: R (local-executed), plain Python.** The reference resolver is
the original Cinderline resolver from the reliable-data package, copied
**byte-for-byte and unchanged** into `solutions/reference.py`:

- SHA-256 `cc4a8f46270e8f1c3e1ab4a4a24d85af3b4c9611f3983fa2656ed73f87a43510`
  (9,401 bytes), recorded in `expected/reference-hash.json`.
- `run_tests.py` asserts that hash on every run and, when the lab is run
  inside the SpicyBrain repository, byte equality with
  `content/exercises/reliable-data/solutions/reference.py` and with the three
  Cinderline fixtures copied beside it.
- The reference imports only `copy`, `hashlib`, `csv` and `json`. **It has no
  Spark dependency**, so this lab runs under the plain interpreter
  (`/usr/bin/python3.12`, CPython 3.12.3) with nothing installed.

## Purpose and outcome

You can already say what a duplicate delivery, an older revision, a
correction and a conflict are ([Identity, ordering and incremental
inputs](../../courses/dbxfe/lessons/dbxfe-m04-l02.md)). This lab makes you
prove those rules with data: first on the five-row Cinderline baseline the
course uses everywhere, then on a **second fictional plant and product line**
(Northgate, valve seats) whose expected results were authored by hand before
the resolver was run over them.

After the lab you can, for any batch history:

1. keep the four outputs apart — **raw** (what arrived, including repeats),
   **quarantine** (rows with reasons), **accepted** (at most one valid current
   replacement per key) and the **publication decision** — and say why a
   clean accepted table is not permission to publish;
2. state and test the preserved invariants: replay changes no accepted total;
   an older revision never replaces a newer one; A v3 = 14/1 turns 20/1 into
   22/1 exactly once; a conflict persists across batches and under row-order
   reversal; an unkeyed conflict blocks publication even with an empty
   unresolved-key list; a first-run conflict produces no report; a later
   conflict keeps the previous snapshot as `stale_previous`; an invalid latest
   revision never resurrects an older valid row;
3. explain why the reference's "publication allowed" answers "is there a
   contradiction?" and not "is there anything worth publishing?".

## Prerequisites

Lessons `dbxfe-m04-l02`, `dbxfe-record-resolution` and
`dbxfe-versioned-updates`. Comfortable reading small JSON files and a Python
`unittest` run. No Spark, Java, cloud account or network.

## Setup and run

```sh
cd lab-l06-record-resolution
python3.12 run_tests.py --evidence local-evidence.json
```

`requirements.txt` lists no packages: the standard library is enough. The
runner prints one line per test and a JSON summary; `--evidence` writes the
full evidence record (versions, times, counts, SHA-256 of every fixture,
expected, solution and starter file and of every produced output). A passed
run means 24 tests, 0 failures, 0 errors, **0 skipped**, exit 0.

Work through `TASKS.md` first. `starters/resolver.py` is deliberately wrong
and `starters/northgate_predictions.py` is a prediction sheet; open
`SOLUTIONS.md` and `solutions/` only after your attempt.
`solutions/scenarios.py` drives the unchanged reference through every
scenario of both plants and prints what it returned:

```sh
python3.12 solutions/scenarios.py
```

## Layout

```
README.md  TASKS.md  SOLUTIONS.md  DATA.md  requirements.txt  run_tests.py
fixtures/  cinderline-baseline.json  cinderline-batches.json  cinderline-unkeyed.json   (byte copies of the original)
           northgate-baseline.json   northgate-batches.json   northgate-unkeyed.json    (the transfer plant)
expected/  cinderline.json  northgate.json  reference-hash.json                          (hand-authored literals)
starters/  resolver.py (flawed resolver + naive gate)  northgate_predictions.py
solutions/ reference.py (unchanged original)  scenarios.py
```

## Failure states and cleanup

A failing test prints the assertion with both values. If
`test_reference_copy_hash_equals_recorded_original_hash` fails, the copy has
been edited: restore it from the original; never "fix" the hash. The runner
sets `sys.dont_write_bytecode`, so no `__pycache__` is written. The only
file the lab creates is the evidence JSON at the path you chose; delete it
when you no longer need it. Nothing else is created.

## Limits and honesty

The revision/quarantine/publication rules are a **fictional teaching policy**,
not a Databricks, Delta or connector guarantee. The `LocalPipeline` keeps
everything in Python memory and its "notification" is a dictionary entry; a
process exit loses it all. Nothing here proves durable orchestration, Delta
MERGE semantics, exactly-once delivery, scale or complete source coverage.
Northgate's rows are original fiction, like Cinderline's. A local pass is
evidence that the stated policy behaves as described on these inputs; it is
not evidence of mastery or of production readiness.
