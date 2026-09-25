# Lab L13 solutions

The complete reference is `solutions/cost_model.py`. This page explains each
task with the intermediate output it produces. All amounts are hypothetical
USD; every rate is a hypothetical rate, not a price.

## Task 1 — Labelled rates

`check_rate` checks the label first, because an unlabelled number is the most
dangerous input a cost model can receive: it looks like a price. Then the
currency (the model never converts), then the unit the rate is priced per.
The platform-usage rate is `0.50` hypothetical USD per DBU; a copy labelled
`list price` is refused as `rate_not_labelled: platform usage`, and a copy
priced per instance-hour as `rate_unit_mismatch`.

## Task 2 — Periods

```text
3 hours per week      × 52 ÷ 12 = 13 hours per month
1.5 hours per week    × 52 ÷ 12 = 6.5 hours per month
600 DBU per quarter   ÷ 3       = 200 DBU per month
3,600 GB-month a year ÷ 12      = 300 GB-month per month
```

Multiplying before dividing keeps these exact in `Decimal`. `once` is refused
here on purpose: the migration is not a monthly quantity, and the worksheet
reports it separately.

## Task 3 — The worksheet

| Driver | Unit, period | Low | Base | High | Swing |
|---|---|---|---|---|---|
| compute time | instance-hour, month | 32.00 | 48.00 | 80.00 | 48.00 |
| platform usage | DBU, month | 100.00 | 150.00 | 250.00 | 150.00 |
| storage | GB-month, month | 8.00 | 10.00 | 16.00 | 8.00 |
| data movement | GB, month | 6.00 | 12.00 | 30.00 | 24.00 |
| operations effort | hour, week | 390.00 | 780.00 | 1560.00 | 1170.00 |
| **recurring total per month** | | **536.00** | **1000.00** | **1936.00** | **1400.00** |
| migration one-off (apart) | hour, once | 9000.00 | 15000.00 | 24000.00 | 15000.00 |

The ranking by swing is operations effort, platform usage, compute time, data
movement, storage. The sponsor's uncertainty is about people's hours, not
DBUs: the effort swing (1170.00) is more than five times the compute and
platform swings together (198.00). Year one is `total × 12 + one-off`:
15432.00 / 27000.00 / 47232.00. The base case reproduces the 12,000 recurring
and 15,000 one-time hypothetical figures that the course's value calculation
uses, now broken into drivers a reader can challenge one at a time.

## Task 4 — Comparable units and alternatives

`sum_quantities([440 DBU, 880 instance-hour])` is refused as
`incomparable_units: DBU + instance-hour`. The two DBU quantities alone add
to 532.4 DBU, which is allowed. The priced comparison:

| Alternative | platform usage | compute time | total per month |
|---|---|---|---|
| always-on all-purpose cluster (440 DBU, 880 instance-hours) | 220.00 | 352.00 | 572.00 |
| job compute per run (92.4 DBU, 184.8 instance-hours) | 46.20 | 73.92 | 120.12 |

The difference is 451.88 hypothetical USD per month, and it comes entirely
from usage: 220 billed cluster-hours against 46.2 for the same two hours of
daily work. The rate per DBU is the same hypothetical number for both on
purpose, so this says nothing about which SKU is cheaper. Leaving out the
compute-time driver for one alternative is refused (`driver_sets_differ`), as
is pricing one driver in different units (`driver_units_differ`).

## Task 5 — The denominator

`cost_per_unit("77.40", 30)` is `2.58` per run. A month with no runs returns
`{"value": null, "reason": "zero_denominator"}`: the honest answer is
*unknown*, which is different from both `0.00` (free) and a crash (which
loses every other result). `857.40` over 30 runs is `28.58`, the fully loaded
figure that includes 780.00 of operations effort; it answers a different
question and falls by itself if the run count rises, so it is labelled apart.

## Task 6 — Runs to cost per unit of work

```text
row  configuration  work  units  unit           cost per 1,000 items (0.50 per DBU)
r01  small          1000  4.0    DBU            2.00
r02  small          1000  4.4    DBU            2.20
r03  small          1000  4.2    DBU            2.10
r04  small             0  1.0    DBU            refused: zero_denominator (1.0 DBU spent, no work)
r05  large          1000  4.8    DBU            2.40
r06  large          1000  6.0    DBU            3.00
r07  large          1000  5.4    DBU            2.70
r08  large          1000  0.3    instance-hour  refused: unit_mismatch
r09  xlarge         1000  8.0    DBU            4.00
```

| Configuration | Runs | Median seconds | Min / median / max | Spread | Caveats |
|---|---|---|---|---|---|
| small | 3 | 630 | 2.00 / 2.10 / 2.20 | 9.5 % | zero_work_excluded |
| large | 3 | 270 | 2.40 / 2.70 / 3.00 | 22.2 % | unit_mismatch_refused |
| xlarge | 1 | 200 | 4.00 / 4.00 / 4.00 | none | single_observation |

Large finishes in less than half the time and costs more per unit of work;
small's whole range sits below large's, so the cheaper ordering holds across
these observations (`cheapestSeparated: true`). xlarge is not ranked: one run
has no spread. Small spent 13.6 DBU but only 12.6 of them sit behind work;
the failed run's 1.0 DBU is real spend with nothing to divide it by.

## Task 7 — Transfer

The second worksheet states platform usage per quarter and storage per year,
has no compute-time driver and spreads its one-off over six months; the base
month is 631.00 and effort again has the largest swing (780.00). On the
transfer runs size-s (2.60 / 3.00 / 3.60) and size-m (3.00 / 3.20 / 3.40)
overlap, so `cheapestSeparated` is `false`: three runs each cannot say which
is cheaper, although size-m is faster. Nothing in the code changed, because
every input carries its own unit, period and label.

## One wrong approach and why it fails

`starters/naive_model.py` is the spreadsheet written in a hurry. It prints a
base month of **400.0**, not 1000.00: it multiplies 3 hours of weekly effort by
the hourly rate as if it were monthly, losing 600.00. It prints a "total" of
**1163.0 units** by adding 120 instance-hours, 300 DBU, 500 GB-month, 240 GB
and 3 hours, a number with no unit, currency or meaning that the model
refuses. Then it divides by `work_items` with no guard and stops with
`ZeroDivisionError` on row r04; the traceback's frame for
`naive_cost_per_1000` holds `row["run_id"] == "r04"`, and the three costs it
had already computed are lost with it. The tests assert all three reasons.
