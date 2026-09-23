# Lab L13 tasks

Work in `starters/cost_model.py`. Each function marked *Task n* raises
`NotImplementedError` until you write it. Check your work with
`python3.12 run_tests.py --starter`; it compares your output with the same
hand-authored literals as the reference. Use `Decimal` for every quantity,
rate and amount, and round money to cents once, per driver, with
`ROUND_HALF_UP`.

## Task 1 — Accept only labelled rates (`check_rate`)

Return the rate's `amount` as a `Decimal` only if all of these hold, and
refuse (raise `ModelRefusal`) in this order otherwise:

| Check | Reason code |
|---|---|
| `label` is exactly `hypothetical rate, not a price` | `rate_not_labelled` |
| `currency` equals the worksheet's currency | `currency_mismatch` |
| `per` equals the quantity's unit | `rate_unit_mismatch` |
| the amount is not negative | `negative_rate` |

Expected behaviour: a rate labelled `list price` is refused with
`rate_not_labelled` and the driver's name as subject.

## Task 2 — Restate periods per month (`to_monthly`)

`week` → × 52 ÷ 12; `month` → unchanged; `quarter` → ÷ 3; `year` → ÷ 12.
Multiply before dividing. `once` is refused with `one_off_not_recurring`
(a one-off is reported apart); anything else with `unknown_period`.

Expected: 3 hours per week is exactly 13 hours per month; 1.5 per week is
6.5; 600 DBU per quarter is 200; 3,600 GB-month per year is 300.

## Task 3 — The low / base / high worksheet (`evaluate_worksheet`)

For every recurring driver and every case: monthly quantity × rate, rounded to
cents. Totals are sums of the rounded rows. Swing = high − low. Rank drivers
by swing, largest first. A driver whose period is `once` goes to `oneOff`,
never into the monthly total; show it spread over `amortizeOneOffMonths` for
reading only, refuse a missing value (`amortization_months_required`) or zero
(`zero_denominator`). Report `recurringYear` (total × 12) and `yearOne`
(total × 12 + the one-off).

Expected on `fixtures/worksheet.json`: base recurring 1000.00 hypothetical
USD per month; operations effort has the largest swing (1170.00); year one
in the base case is 27000.00.

## Task 4 — Refuse incomparable sums and alternatives

`sum_quantities(items)`: add raw quantities only when every item has the same
unit; otherwise refuse with `incomparable_units` and the units joined by
` + ` as subject. `compare_alternatives(doc)`: exactly two alternatives
(`two_alternatives_required`); the same driver names in both
(`driver_sets_differ`); each driver in the same unit in both
(`driver_units_differ`); a rate for every unit (`no_rate_for_unit`) that
passes Task 1; then each alternative's monthly amount per driver, its total,
the difference (first minus second) and which is lower.

Expected: 440 DBU + 880 instance-hours is refused; the always-on cluster is
572.00 and job compute per run 120.12 hypothetical USD per month.

## Task 5 — Guard the denominator (`cost_per_unit`)

Return `{"value": "<cents>", "reason": None}` for a positive count, and
`{"value": None, "reason": "zero_denominator"}` for a zero count: unknown, not
`0.00` and not an exception. Refuse a negative cost (`negative_cost`) or count
(`negative_count`). `per` scales the result (per 1,000 work items).

Expected: 77.40 over 30 runs is 2.58; 0.00 over 0 runs is unknown.

## Task 6 — Cost per unit of work from run observations (`summarize_runs`)

For each row: refuse `unit_mismatch` when its unit is not the rate's unit;
count its units as spent; compute cost per `per` work items with Task 5 and
refuse `zero_denominator` rows (their units stay counted as spent). Per
configuration report runs used, median duration, min/median/max cost, the
spread `(max − min) ÷ median × 100` to one decimal (`null` for one run), units
spent and units behind work, and caveats: `single_observation`,
`few_observations`, `zero_work_excluded`, `unit_mismatch_refused`. Rank only
configurations with at least three runs, by median cost, and say whether the
cheapest one's range is strictly below the next one's (`cheapestSeparated`).

Expected on `fixtures/runs.csv`: small 2.00 / 2.10 / 2.20 per 1,000 items,
large 2.40 / 2.70 / 3.00, xlarge observed once and not ranked; r04 and r08
refused with their reasons.

## Task 7 — Transfer

Run your model on `fixtures/transfer-worksheet.json` and
`fixtures/transfer-runs.csv` without changing code. Expected: a base month of
631.00 hypothetical USD, and a run comparison whose ranges overlap, so no
configuration is named cheaper with confidence. Write two sentences on what
changed and why the model did not need to.
