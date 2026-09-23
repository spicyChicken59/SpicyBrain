# Lab L13 — A reproducible cost worksheet and a controlled cost experiment

*Local-executed (R), plain CPython 3.12.3, standard library only. Nothing to
install; nothing runs on Databricks or any cloud service. Every rate is a
hypothetical rate, not a price, in hypothetical USD.*

## What this lab is for

A sponsor's question, "what will the pilot cost?", sounds like it wants one
number. This lab builds the answer the way the module *Compute choices, cost
and FinOps reasoning* teaches it: as a worksheet a reader can recompute. Six
cost drivers each keep their own unit and period and carry a labelled rate;
the model restates them per month in one currency, runs low, base and high
cases, keeps the one-off migration apart, and says which input moves the
answer most. A second part turns a file of synthetic run observations into
cost per unit of work, and refuses the rows that cannot honestly be divided.
The model refuses rather than guesses: every refusal has a named reason.

## The worksheet

| Driver | Unit | Period | Low | Base | High | Rate (hypothetical rate, not a price) |
|---|---|---|---|---|---|---|
| compute time | instance-hour | month | 80 | 120 | 200 | 0.40 per instance-hour |
| platform usage | DBU | month | 200 | 300 | 500 | 0.50 per DBU |
| storage | GB-month | month | 400 | 500 | 800 | 0.02 per GB-month |
| data movement | GB | month | 120 | 240 | 600 | 0.05 per GB |
| operations effort | hour | week | 1.5 | 3 | 6 | 60.00 per hour |
| migration one-off | hour | once | 150 | 250 | 400 | 60.00 per hour |

**Tasks 1 and 2 — labels and periods.** A rate is used only if its label says
it is hypothetical, its currency matches the sheet, and it is priced per the
quantity's unit. Weekly effort becomes monthly by × 52 ÷ 12, so 3 hours a
week is exactly 13 hours a month; `once` is never restated per month.

**Task 3 — the cases.** The intermediate output, per month in hypothetical USD:

| Driver | Low | Base | High | Swing |
|---|---|---|---|---|
| compute time | 32.00 | 48.00 | 80.00 | 48.00 |
| platform usage | 100.00 | 150.00 | 250.00 | 150.00 |
| storage | 8.00 | 10.00 | 16.00 | 8.00 |
| data movement | 6.00 | 12.00 | 30.00 | 24.00 |
| operations effort | 390.00 | 780.00 | 1560.00 | 1170.00 |
| recurring total | 536.00 | 1000.00 | 1936.00 | 1400.00 |

The migration is reported apart: 9000.00 / 15000.00 / 24000.00, shown as
750.00 / 1250.00 / 2000.00 a month over twelve months for reading only. The
largest swing is operations effort, more than five times the compute and
platform swings together: the uncertainty worth measuring first is people's
hours. The base case reproduces the 12,000 recurring and 15,000 one-time
figures used by [the transparent value calculation](#/lesson/dbxfe-m11-l03),
now broken into drivers that can be challenged one at a time.

**Task 4 — comparable units.** Adding 440 DBU and 880 instance-hours is
refused (`incomparable_units`). Priced with their own rates, the same two
hours of daily work cost 572.00 a month on an always-on all-purpose cluster
and 120.12 on job compute per run, a difference of 451.88 that comes entirely
from billed hours, because one hypothetical DBU rate is used for both on
purpose. Dropping a driver from one alternative is refused too
(`driver_sets_differ`): a comparison that prices less is not cheaper.

**Task 5 — the denominator.** 77.40 over 30 runs is 2.58 per run. A month
with no runs returns *unknown* with the reason `zero_denominator`, never
`0.00` and never a crash.

## The experiment

| run | configuration | work items | seconds | units | unit |
|---|---|---|---|---|---|
| r01–r03 | small | 1000 each | 600, 660, 630 | 4.0, 4.4, 4.2 | DBU |
| r04 | small | 0 | 120 | 1.0 | DBU |
| r05–r07 | large | 1000 each | 240, 300, 270 | 4.8, 6.0, 5.4 | DBU |
| r08 | large | 1000 | 255 | 0.3 | instance-hour |
| r09 | xlarge | 1000 | 200 | 8.0 | DBU |

**Task 6 — cost per 1,000 work items at 0.50 per DBU.** Small: 2.00 / 2.10 /
2.20 (spread 9.5 %, median 630 s). Large: 2.40 / 2.70 / 3.00 (spread 22.2 %,
median 270 s). xlarge: 4.00 once, not ranked (`single_observation`). r04 is
refused because it did no work, yet its 1.0 DBU still counts as spent; r08 is
refused because instance-hours are outside the DBU basis. Small's whole range
sits below large's, so across these observations it is cheaper per unit of
work while large is faster; which one to run depends on the latency the
nightly job must meet, a question the balance of concurrency, latency and
cost in [the SQL performance lesson](#/lesson/dbxfe-m05-l03) also asks.

**Task 7 — transfer.** A second worksheet states usage per quarter and
storage per year and has no compute-time driver: its base month is 631.00,
and effort again swings most (780.00). Its run file has overlapping ranges
(size-s 2.60 to 3.60, size-m 3.00 to 3.40), so the model declines to name a
cheaper configuration.

## The failure case

`starters/naive_model.py` prints a base month of 400.0 (weekly effort counted
as monthly, 600.00 short), a "total" of 1163.0 units (five units added into
nothing), and then stops with `ZeroDivisionError` on r04, losing the three
costs it had already computed. The tests assert each reason, including the
failing row read from the traceback.

## What the tests prove, and what they do not

Thirty tests compare the model with hand-authored literals, prove every
fixture rate is labelled hypothetical, show the refusals by reason, run the
command line twice for identical bytes and once with the network disabled,
and assert the naive and starter failures. They prove the arithmetic and the
refusals are right for these inputs. They do not prove any price, any saving,
any real run time or which product is cheaper: the inputs are synthetic.

## Setup and cleanup

Run `python3.12 run_tests.py --evidence local-evidence.json` from the lab
directory (30 tests, 0 skipped). Nothing is written inside the lab directory;
two tests use a temporary directory that deletes itself. Remove
`local-evidence.json` afterwards.
