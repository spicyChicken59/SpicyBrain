# Lab L13 — A reproducible cost worksheet and a controlled cost experiment

**Execution class: R (local-executed), plain Python.** Everything runs under
Python 3.12 (tested with CPython 3.12.3) and the standard library only
(`argparse`, `csv`, `datetime`, `decimal`, `hashlib`, `importlib`, `json`,
`pathlib`, `platform`, `shlex`, `socket`, `subprocess`, `tempfile`, `unittest`). No
packages, no Spark, no Java, no network, no Databricks workspace and no cloud
account.

**Every rate in this lab is a hypothetical rate, not a price.** Amounts are in
*hypothetical USD*, a labelled teaching currency. No figure here was read from
a price list, a quotation, an invoice or a billing table, and no discount is
applied. To use real rates you would read them from the current pricing page
and your own contract, date them, and change the model's labelling rule on
purpose; that is outside this lab.

## Purpose and outcome

Fictional Cinderline Components is running a one-plant quality pilot. Its
sponsor asks what the pilot costs. This lab builds the answer as a worksheet a
reader can recompute: six cost drivers, each in its own unit and period, each
with a labelled rate, turned into one currency per month with low, base and
high cases. It then turns a small file of synthetic run observations into cost
per unit of work, with the caveats that keep the number honest.

After the lab you can:

1. refuse a rate that is not labelled, is in another currency, or is priced
   per a different unit than the quantity it multiplies;
2. restate weekly, quarterly and yearly quantities per month, and keep a
   one-off (the migration) apart from the monthly figure instead of hiding it
   in it;
3. compute low, base and high monthly amounts per driver, their totals, each
   driver's swing (high minus low) and the ranking that says which input moves
   the answer most;
4. refuse to add quantities in different billing units (DBU plus
   instance-hours is not a number) and refuse to compare two alternatives
   that price different drivers or the same driver in different units;
5. divide a cost by a count of work and return *unknown* with a reason, not
   zero and not a crash, when the count is zero;
6. turn run observations (configuration, duration, units consumed, work
   items) into cost per 1,000 work items per configuration with the minimum,
   median, maximum, spread and caveats, and decline to rank a configuration
   observed once;
7. repeat all of it on an altered second worksheet and run file.

## Prerequisites

Reading a small JSON file and a CSV file, and the arithmetic of rates and
periods. The module *Compute choices, cost and FinOps reasoning* teaches every
idea used here; the Python module and Lab L01 already use `decimal`, `csv` and
`unittest`, which this lab relies on. Nothing needs to be installed beyond
Python 3.12.

## Setup and run

```sh
cd lab-l13-cost-model
python3.12 run_tests.py --evidence local-evidence.json   # 30 tests, 0 failures, 0 errors, 0 skipped, exit 0
python3.12 run_tests.py --starter                          # judge starters/cost_model.py by the same literals
python3.12 starters/naive_model.py                         # the deliberately failing example: read its traceback
python3.12 solutions/cost_model.py worksheet fixtures/worksheet.json
python3.12 solutions/cost_model.py runs fixtures/runs.csv --rates fixtures/worksheet.json --driver "platform usage"
python3.12 solutions/cost_model.py compare fixtures/alternatives.json
```

Each command prints JSON with sorted keys, so two runs over the same files
print the same bytes; a refusal prints `{"refused": {...}}` and exits with
status 2. `--evidence` writes the interpreter, versions, start and end times,
test counts and the SHA-256 of every fixture, expected, starter and solution
file and of every produced output. `--starter` fails until TASKS.md is done;
that is its purpose.

## Files

| Path | What it holds |
|---|---|
| `fixtures/worksheet.json` | The pilot's six drivers with low/base/high quantities, units, periods and labelled rates |
| `fixtures/runs.csv` | Nine synthetic run observations of the nightly job on three configurations |
| `fixtures/alternatives.json` | Always-on all-purpose cluster against job compute per run, same work |
| `fixtures/refusals.json` | Small broken inputs the model must refuse, each with a named reason |
| `fixtures/unit-cost.json` | Four cost-per-unit cases, two with a zero count |
| `fixtures/transfer-*.{json,csv}` | The altered second worksheet and run file |
| `expected/*.json` | Hand-authored literals; derivations in DATA.md |
| `starters/cost_model.py` | The API with six gaps, one per task |
| `starters/naive_model.py` | The wrong approach, kept runnable so its failures can be read |
| `solutions/cost_model.py` | The reference model and its command line |

## Cleanup

The runner writes only the evidence file you name. Two tests create a
temporary directory with Python's `tempfile` module and delete it themselves;
nothing is written inside the lab directory (`sys.dont_write_bytecode` and
`-B` keep `__pycache__` out). Delete `local-evidence.json` when you are done.

## Limits

- The rates and quantities are synthetic; the arithmetic is real. The
  worksheet says how the answer depends on its inputs, never what anything
  costs.
- Run timings are illustrations of mechanism, not benchmarks, and were not
  measured on any platform.
- One hypothetical rate per DBU is used for every configuration and both
  alternatives on purpose, so the comparisons show how *usage* moves; real
  SKUs are priced differently and must be read from current pricing.
- The experiment's basis is platform usage (DBU) only. Cloud instance charges
  for classic compute are a separate driver that this run file does not hold,
  and the output says so in its caveats.
- Nothing here is financial advice, a forecast, a saving or a quotation.
