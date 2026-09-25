# Lab L13 data dictionary and derivations

**Provenance.** Every file under `fixtures/` was written by hand for this lab.
Cinderline Components, its pilot, its workloads, quantities, run
observations and rates are synthetic teaching records. No row was measured on
any platform, and no rate was read from a price list, quotation, invoice or
billing table. Every rate carries the label `hypothetical rate, not a price`
and every amount is in `hypothetical USD`. There is no generator and no seed:
the files are the data.

**How the expected values were produced.** Every literal in `expected/` was
calculated by hand from the fixtures with the rules below, then written into
the JSON; none was produced by running `solutions/cost_model.py`. The rules:
money is rounded to cents once per driver and case with half-up rounding;
totals are sums of those rounded rows; a week is 52 ÷ 12 of a month; spread
is `(max − min) ÷ median × 100` rounded half-up to one decimal.

## fixtures/worksheet.json

| Field | Meaning |
|---|---|
| `currency` | the one currency every rate must use; here `hypothetical USD` |
| `normalizeTo` | the period results are restated in; only `month` is supported |
| `amortizeOneOffMonths` | months a one-off is spread over for reading only (12) |
| `drivers[].driver` | the cost driver's name |
| `drivers[].unit` | the billing or effort unit the quantity is counted in |
| `drivers[].period` | `week`, `month`, `quarter`, `year`, or `once` for a one-off |
| `drivers[].quantity` | `low`, `base` and `high` quantities per period |
| `drivers[].rate` | `amount`, `currency`, `per` (unit) and `label` |
| `drivers[].source`, `owner` | provenance label and the person who owns the uncertainty |

Derivation of `expected/worksheet.json`:

| Driver | Quantity per period | Per month | × rate | Low / base / high (per month) |
|---|---|---|---|---|
| compute time | 80 / 120 / 200 instance-hours per month | same | × 0.40 | 32.00 / 48.00 / 80.00 |
| platform usage | 200 / 300 / 500 DBU per month | same | × 0.50 | 100.00 / 150.00 / 250.00 |
| storage | 400 / 500 / 800 GB-month per month | same | × 0.02 | 8.00 / 10.00 / 16.00 |
| data movement | 120 / 240 / 600 GB per month | same | × 0.05 | 6.00 / 12.00 / 30.00 |
| operations effort | 1.5 / 3 / 6 hours per week | × 52 ÷ 12 = 6.5 / 13 / 26 hours | × 60.00 | 390.00 / 780.00 / 1560.00 |

- Totals: 32 + 100 + 8 + 6 + 390 = **536.00**; 48 + 150 + 10 + 12 + 780 =
  **1000.00**; 80 + 250 + 16 + 30 + 1560 = **1936.00**; swing 1936 − 536 =
  **1400.00**.
- Swings: 48.00, 150.00, 8.00, 24.00, 1170.00, so the ranking is operations
  effort, platform usage, compute time, data movement, storage.
- One-off: 150 / 250 / 400 hours × 60.00 = **9000.00 / 15000.00 / 24000.00**,
  swing 15000.00; ÷ 12 months = 750.00 / 1250.00 / 2000.00.
- Recurring year: × 12 = 6432.00 / 12000.00 / 23232.00. Year one: plus the
  one-off = 15432.00 / 27000.00 / 47232.00.

## fixtures/runs.csv

| Column | Meaning |
|---|---|
| `run_id` | the run's identifier |
| `configuration` | the candidate compute configuration: `small`, `large`, `xlarge` |
| `work_items` | work items processed (1,000 per run; 0 for a failed run) |
| `duration_seconds` | wall-clock seconds, an illustration of mechanism, not a benchmark |
| `units_consumed` | usage recorded for the run |
| `unit` | the unit of `units_consumed`: `DBU`, or `instance-hour` in the one pasted-in row |

Derivation of `expected/runs.json` (rate 0.50 per DBU from the worksheet's
platform-usage driver; cost per 1,000 items = units × 0.50 ÷ items × 1,000):

- small: r01 4.0 → 2.00, r02 4.4 → 2.20, r03 4.2 → 2.10; min 2.00, median
  2.10, max 2.20; spread 0.20 ÷ 2.10 × 100 = 9.52 → **9.5**; durations 600,
  630, 660 → median **630**. r04 has 0 work items: refused
  `zero_denominator`; units spent 4.0 + 4.4 + 4.2 + 1.0 = **13.6**, behind
  work **12.6**.
- large: r05 4.8 → 2.40, r06 6.0 → 3.00, r07 5.4 → 2.70; min 2.40, median
  2.70, max 3.00; spread 0.60 ÷ 2.70 × 100 = 22.22 → **22.2**; durations 240,
  270, 300 → **270**. r08 is in instance-hours: refused `unit_mismatch` and
  not counted in DBU; units spent and behind work 4.8 + 6.0 + 5.4 = **16.2**.
- xlarge: r09 8.0 → 4.00 once; spread **null**; not ranked.
- Rows read 9, used 7, refused 2. Ranking by median: small (2.10), large
  (2.70); small's maximum 2.20 is below large's minimum 2.40, so
  `cheapestSeparated` is **true**.

## fixtures/alternatives.json

Same two hours of daily work over 22 working days, with a synthetic
consumption of 2 DBU and 4 instance-hours per cluster-hour.

- Always-on: billed 10 hours a day × 22 = 220 cluster-hours → **440 DBU,
  880 instance-hours**; 440 × 0.50 = 220.00, 880 × 0.40 = 352.00, total
  **572.00**.
- Job compute per run: 2 runs a day × (60 + 3) minutes = 2.1 hours × 22 =
  46.2 cluster-hours → **92.4 DBU, 184.8 instance-hours**; 92.4 × 0.50 =
  46.20, 184.8 × 0.40 = 73.92, total **120.12**.
- Difference 572.00 − 120.12 = **451.88**; lower: job compute per run.
- Same-unit sum of the two DBU quantities: 440 + 92.4 = **532.4 DBU**.

## fixtures/refusals.json

Each case differs from a valid input in one field, and its expected reason in
`expected/refusals.json` names that field's rule: an unlabelled rate
(`label: list price`), a storage rate in `hypothetical EUR`, a `fortnight`
period, a data-movement low of 300 above its base of 240, a compute-time low
of −10, a platform-usage rate priced per instance-hour, a one-off spread over
0 months, a raw sum of DBU and instance-hours, an alternative missing its
compute-time driver, one pricing platform usage in instance-hours, and an
instance-hour rate in `hypothetical EUR`.

## fixtures/unit-cost.json

- 77.40 over 30 runs = **2.58**. The 77.40 is the nightly job's month:
  126 DBU × 0.50 = 63.00 plus 36 instance-hours × 0.40 = 14.40.
- 857.40 over 30 runs = **28.58**: the same plus 780.00 of operations effort.
- 0.00 over 0 runs and 0.50 over 0 work items: **null, zero_denominator**.

## Transfer: fixtures/transfer-worksheet.json and fixtures/transfer-runs.csv

- platform usage 450 / 600 / 900 DBU per quarter ÷ 3 = 150 / 200 / 300 × 0.50
  = **75.00 / 100.00 / 150.00**, swing 75.00.
- storage 2,400 / 3,600 / 6,000 GB-month per year ÷ 12 = 200 / 300 / 500 ×
  0.02 = **4.00 / 6.00 / 10.00**, swing 6.00.
- data movement 50 / 100 / 200 GB × 0.05 = **2.50 / 5.00 / 10.00**, swing 7.50.
- operations effort 1 / 2 / 4 hours per week × 52 ÷ 12 × 60.00 =
  **260.00 / 520.00 / 1040.00**, swing 780.00.
- Totals 341.50 / 631.00 / 1210.00, swing 868.50; ranking operations effort,
  platform usage, data movement, storage.
- One-off 40 / 80 / 120 hours × 60.00 = 2400.00 / 4800.00 / 7200.00, ÷ 6 =
  400.00 / 800.00 / 1200.00. Recurring year 4098.00 / 7572.00 / 14520.00;
  year one 6498.00 / 12372.00 / 21720.00.
- Runs, 250 queries each (cost per 1,000 = units × 0.50 ÷ 250 × 1,000 =
  units × 2): size-s 1.5, 1.3, 1.8 → 3.00, 2.60, 3.60 (median 3.00, spread
  1.00 ÷ 3.00 = 33.3, durations median 410, units 4.6); size-m 1.7, 1.6, 1.5
  → 3.40, 3.20, 3.00 (median 3.20, spread 0.40 ÷ 3.20 = 12.5, durations
  median 220), t07 0 queries refused, units spent 5.2, behind work 4.8.
  size-s's maximum 3.60 is not below size-m's minimum 3.00, so
  `cheapestSeparated` is **false**.

## expected/naive.json

The naive base month: 48 + 150 + 10 + 12 + 3 × 60 = **400.0** (weekly effort
counted once instead of 52 ÷ 12 times); the model's 1000.00 − 400.00 =
**600.00** = 780.00 − 180.00. The naive "units": 120 + 300 + 500 + 240 + 3 =
**1163.0**. The naive division fails at the first zero-work row, **r04**, with
`ZeroDivisionError`.
