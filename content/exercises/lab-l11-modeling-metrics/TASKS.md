# Lab L11 tasks

Work in `starters/model.sql`; every gap is marked `-- GAP (task n)`. Test your
file at any point with:

```sh
python run_tests.py --sql starters/model.sql
```

Numbers below are for the **baseline** fixtures; the transfer set must pass
with the same SQL and no edits. Read DATA.md first: it lists every inspection
in pieces.

## Task 1 — Build the fact at its declared grain

State the grain in one sentence before writing SQL: one row of
`fact_inspection` is one accepted inspection. Then fill the two task-1 gaps:

1. Join each inspection to the ONE version of its line valid on its business
   day: `valid_from` inclusive, `valid_to` exclusive, a NULL `valid_to` still
   valid.
2. An inspection whose line has no valid version keeps its row and takes the
   unknown member's key from the `:unknown_line_sk` parameter.

**Expected behaviour.** `fact_inspection` has 22 rows and no inspection id
appears twice. I-21 (line N3) has `line_sk = -1`. I-10 (N1 on 30 March)
resolves to version 102 (P. Nair), I-09 (N1 on 27 March) to version 101 (D.
Varga). Without the validity window you will see 30 rows; with `<=` instead of
`<` on `valid_to` you will see duplicates on 30 March.

## Task 2 — Convert before you add

Fill the task-2 gaps so both quantities are multiplied by
`unit_conversion.pieces_per_uom`. Rows in a unit with no conversion never
reach the fact; they are listed by the `quarantine` statement.

**Expected behaviour.** The fact totals 2,440 inspected and 65 defective
pieces. I-08 (10 cases, 1 defective case) becomes 120 / 12 pieces. The
quarantine is empty on the baseline and holds T-10 (20 trays) on the transfer.

## Task 3 — Line-day rows with honest empty cases

The line-day grid must contain every line version valid on every business day
of the period AND every observed line-day. Fill the three task-3 gaps: the
`UNION` of observed rows, the status (`:empty_status` when a cell has no
inspection, `:zero_status` when its inspections sum to zero pieces, otherwise
`ok`) and a rate that is NULL rather than an error or 0 when no piece was
inspected.

**Expected behaviour.** 21 rows. S2 on 30 March is `no_inspections`, N2 on 31
March is `no_units`, both with NULL rates. N2 on 26 March is `ok` with a rate
of exactly 0.0. The unknown line appears once, on 1 April, with 50 / 2. Plain
division raises `DIVIDE_BY_ZERO` because ANSI mode is on.

## Task 4 — Recompute the coarser grains from parts

Read `plant_day` and `plant_month` and justify, in a comment, why they sum
defective and inspected pieces and divide once, instead of averaging line or
day rates. No code change is required unless you find an average.

**Expected behaviour.** North on 27 March: 300 inspected, 9 defective, rate
0.03, while the average of its two line rates is 0.035. North in March: 1,000
/ 22 = 0.022, while the average of its day rates is 0.02125. Every plant-day
row equals the sum of its line-day rows, every plant-month row the sum of its
plant-day rows, and the months sum to the fact totals.

## Task 5 — A window in business days

Fill the task-5 gap so `window_business_dates` returns the last
`:window_days` business days of the plant calendar up to `:as_of`.

**Expected behaviour.** As of Monday 30 March the window is 26, 27 and 30
March: North 800 / 18, South 720 / 18. The three-calendar-day window (28, 29,
30 March) holds one business day: North 300 / 6, South 180 / 3. On the
transfer the shutdown on 1 May makes a Monday-to-Friday rule wrong as well.

## Task 6 — Explain the five deliberate failures

Run the reference once with `--outputs outputs.json` and, without code, write
two sentences for each broken statement in `solutions/model.sql`
(`naive_division_line_day`, `naive_units_plant_day`, `inner_join_totals`,
`history_join_*`, `window_calendar_dates`): what the output shows and which
contract clause it violates.

**Expected behaviour.** You can point at a specific number for each: the
error condition, 4/190 against 15/300, 2,390 against 2,440 pieces, 29 rows
from 22 inspections, one business day in a three-day window.

## Task 7 — Make the contract refusable

Open `fixtures/metric_contract.json`. Copy it, delete `denominator` and call
`solutions.contract.problems()` on the copy; then change the denominator's
population so it differs from the numerator's.

**Expected behaviour.** The first copy is refused with `missing denominator`,
the second with `numerator and denominator populations differ`, and
`parameters()` raises `ValueError` naming the reason instead of returning
parameters. Write one sentence per contract term (numerator, denominator, unit,
period, window, empty cases, unknown member, owner) saying which test would
catch its violation.
