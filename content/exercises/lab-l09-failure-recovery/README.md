# Lab L09 — Failure and recovery boundaries

**Execution class: R (local-executed).** The reference pipeline and its 43
tests run on one machine with Python 3.12 and the standard library only
(`requirements.txt` pins nothing because nothing is installed). Nothing
contacts a network, nothing runs on Databricks and no message is sent.

**What this lab is not.** There is no scheduler service, no Lakeflow Jobs run,
no cluster and no durable storage. The "runner" is one short Python class
that walks four tasks in order and keeps a ledger per run id so you can see
what a task graph, a retry policy and a repair do to state. Failures are
*injected* by raising an exception at a named point, which stands in for a lost
process; a real crash can also lose memory, and this model keeps everything in
one Python object. The notification "recipient" is `LocalChannel`, which
appends a dictionary to a Python list. Nothing here shows how any product
schedules, retries, repairs or alerts; it shows the business-state reasoning
you need before trusting one that does.

## Purpose

A green run says every task met its configured success condition. It does not
say the published numbers are right, that each person was told once, or that
the input described the right day. This lab builds a small daily report
pipeline for Cinderline Components' line 3 inspections, breaks it on purpose
at each place where state is left half-written, recovers it, and compares the
recovered business state with results written by hand before any code ran.

## Outcome

After the lab you can:

- predict what remains after a failure after raw retention, after resolution,
  before the external effect and after the external effect, and name each
  boundary from the evidence it leaves;
- repair a run by re-running the same run id so that completed tasks are
  reused and the failed task and its dependents run again;
- design an outbox idempotency key that absorbs retries and repairs yet still
  announces a genuinely corrected report, and say why the receiver must honour
  the key;
- show that a run in which every task is green can publish wrong business data
  when its input is stale, and refuse that input;
- backfill a missed date from its own retained input without moving the
  current report, and write the recovery steps down as a runbook.

## Prerequisites

Python you can read (functions, dictionaries, exceptions, a class), JSON, and
the course's module *Orchestration and operations* (lesson *Orchestration,
failure, and reconciliation*). The record-resolution rules here (duplicates,
versions, invalid rows, conflicts) are a simplified version of the ingestion
module's: this lab keeps the highest *valid* version per lot, while the
ingestion module takes the highest observed version first, validates it, and
blocks publication on an unresolved conflict. Use this lab for task
boundaries, run ids, effect keys and freshness, and the ingestion module for
publication decisions.

## Files

| Path | What it holds |
|---|---|
| `fixtures/contract.json` | Line 3 contract: key `lot`, measures `inspected` and `defective`, two recipients |
| `fixtures/landing/2026-03-0{2,3,4}.json` | One export per business date: duplicates, a correction, one invalid row each |
| `fixtures/stale/2026-03-04.json` | Yesterday's export re-delivered into the 2026-03-04 slot |
| `fixtures/late/2026-03-03-correction.json` | A late version 2 for lot L-104 |
| `fixtures/late/2026-03-03-conflict.json` | Event `e07` re-sent with a different defect count |
| `fixtures/transfer/…` | Harbourline dock scans: composite key `dock` + `trailer`, three recipients, two corrections and a conflict |
| `expected/*.json` | Hand-derived literals: reports, boundary states, retries, stale input, backfill, runbook, transfer |
| `solutions/pipeline.py` | The reference pipeline, runner, local channel and diagnosis |
| `starters/pipeline.py` | The same file with six gaps marked `GAP 1` … `GAP 6` |
| `starters/shortcuts.py` | Four tempting shortcuts the tests prove wrong |
| `run_tests.py` | 43 unittest cases; `--evidence <path>` writes the evidence JSON |
| `mutation_check.py` | Fourteen deliberate mutations of the reference, each of which must turn a test red |
| `TASKS.md`, `SOLUTIONS.md`, `DATA.md`, `RUNBOOK.md` | Tasks, explained solution, data dictionary, operations runbook |

## Setup

Python 3.12 (CPython 3.12.3 was tested). No virtual environment and no
installation are needed: `requirements.txt` lists nothing.

## Run

From this directory:

```
python3.12 run_tests.py                         # the reference solution, 43 tests
python3.12 run_tests.py --evidence evidence.json
python3.12 run_tests.py --starter               # your completed starters/pipeline.py, 41 tests
python3.12 mutation_check.py                    # optional: prove the tests can fail
```

Under `--starter` the two tests that check the untouched starter's gaps are
left out of the suite (they are not skipped); the other 41 must pass.

## Cleanup

The tests keep everything in memory and write nothing unless you pass
`--evidence <path>`; delete that file when you are done. `mutation_check.py`
works in a temporary directory that Python deletes when each mutation
finishes. The runner sets `sys.dont_write_bytecode`, so no `__pycache__` is
created; if your own experiments create one, delete it.

## Limits

- One process, one Python object: no durability across a real crash, no
  concurrency between runs, no clock, no timeout.
- `LocalChannel` is a stand-in for a recipient that honours idempotency keys;
  whether a real email, chat or webhook service accepts such a key at all must
  be checked for that service.
- The freshness rule checks the business date the landing file declares; a
  file can also be late, partial or wrongly labelled in ways this does not
  detect.
- Synthetic data only. Cinderline Components, Harbourline, their lots, docks,
  trailers and recipients are fictional.
