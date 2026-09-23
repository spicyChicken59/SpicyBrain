# DATA — lab L17 fixtures and expected values

Everything here is synthetic. Cinderline Components is a fictional manufacturer; the ovens, days,
faults, repairs and plants below were drawn by a seeded generator and describe no real equipment.

## The fixture: `fixtures/oven_days.csv`

Written by `fixtures/generate_oven_days.py` with `SEED = 20260923`: eight coating ovens at
Cinderline's (fictional) South plant, 120 days from 2026-03-02, one row per oven per day. Each row
is one **prediction opportunity at 09:00**: will this oven have a fault stop in the next 24 hours?
Every random draw comes from one `random.Random(seed)`, so the committed file is byte-for-byte
reproducible; the first test regenerates it in memory and compares SHA-256 digests.

| oven | age (years) | set point (°C) |
|---|---|---|
| O-01 | 2.5 | 205 |
| O-02 | 4.0 | 205 |
| O-03 | 6.5 | 210 |
| O-04 | 8.0 | 210 |
| O-05 | 3.0 | 200 |
| O-06 | 9.5 | 215 |
| O-07 | 5.5 | 205 |
| O-08 | 11.0 | 215 |

How a day is drawn, per oven:

1. `door_cycles` ~ Normal(58, 14), floored at 0 and truncated to an integer.
2. A latent fault probability: `logit = -4.7 + 0.075 × days_since_service + 0.16 × age + 0.02 × max(door_cycles − 60, 0)`.
   The row's label `fault_next_24h` is 1 with that probability.
3. An oven about to fault usually ran hot in the 24 hours before 09:00: with probability 0.8 a faulting
   row gets a precursor of |Normal(5.5, 2)| °C. `temp_mean_c = set point + 0.08 × days_since_service + 0.5 × precursor + Normal(0, 1.6)`,
   `temp_max_c = temp_mean_c + |Normal(4, 2.5)| + precursor`. These readings exist at 09:00.
4. `humidity_pct = 44 + 6 × sin(2π × day / 120) + Normal(0, 3)`.
5. When the row faults, `repair_minutes` ~ Uniform{45…240} and `fault_code` is one of F-HEAT, F-DOOR,
   F-CTRL; otherwise 0 and empty. **Both are written by the technician after the fault**, so they are
   post-event fields.
6. A fault is repaired the same day and a scheduled service falls due roughly every 45 ± 8 days; either
   resets `days_since_service` to 0.

`fixtures/data_dictionary.json` records, for every column, its role (identifier, time, feature,
label, post_event) and **when it becomes available** (`09:00`, `after the horizon`, `after the fault,
same day`). The leakage check reads this file, never a correlation.

### Counts

| | rows | faults | fault rate |
|---|---|---|---|
| all days 1–120 | 960 | 67 | 6.98% |
| training, days 1–84 | 672 | 49 | 7.29% |
| test, days 85–120 | 288 | 18 | 6.25% |

The test period is 36 days × 8 ovens. A random 70/30 split with seed 20260923 puts 672 rows and 48
faults in training and 288 rows and 19 faults in test, and its test rows start on day 1 while its
training rows reach day 120.

### The transfer plant

`generate_oven_days.rows(TRANSFER_SEED)` with `TRANSFER_SEED = 20260924` draws a second synthetic
plant with the same oven specification and different daily draws. It is generated in memory by the
tests and never committed: 960 rows, 60 faults; training 672 rows and 45 faults; test 288 rows and 15
faults.

## Expected values and how each was derived

No expected value is produced by `solutions/`.

### `expected/metrics.json` — written by `expected/derive_expected.py`

The derivation script is independent of the solution: it reads the CSV with the `csv` module into
numpy arrays (no pandas, no MLflow, no import from `solutions/`), splits with its own list
comprehensions and its own permutation, counts confusion cells with numpy comparisons and fits each
model with scikit-learn called directly on arrays: a `StandardScaler` fitted on the training rows
only, then `LogisticRegression(C, class_weight="balanced", max_iter=1000, random_state=seed)`. The
solution instead builds a scikit-learn `Pipeline` over a typed pandas frame inside an MLflow run. Test
2 reruns `derive()` in memory and requires it to equal the committed file, so the literals cannot
drift from the fixture.

Rates are rounded to four places. `warnings_per_day` is warnings ÷ test rows × 8 ovens, which is
warnings per test day. Precision is `null` when a predictor never warns. The baselines can be checked
by hand:

| predictor (test days 85–120) | tp | fp | fn | tn | accuracy | recall | precision | warnings/day |
|---|---|---|---|---|---|---|---|---|
| never warn | 0 | 0 | 18 | 270 | 270/288 = 0.9375 | 0/18 = 0 | null | 0 |
| temperature rule, `temp_max_c >= 220.0` | 12 | 31 | 6 | 239 | 251/288 = 0.8715 | 12/18 = 0.6667 | 12/43 = 0.2791 | 43/36 = 1.1944 |
| logistic regression, C = 1 | 15 | 53 | 3 | 217 | 232/288 = 0.8056 | 15/18 = 0.8333 | 15/68 = 0.2206 | 68/36 = 1.8889 |
| logistic regression, C = 0.01 | 17 | 74 | 1 | 196 | 213/288 = 0.7396 | 17/18 = 0.9444 | 17/91 = 0.1868 | 91/36 = 2.5278 |
| C = 1 plus `repair_minutes` (leaky) | 18 | 0 | 0 | 270 | 1.0 | 1.0 | 1.0 | 18/36 = 0.5 |

Over the random split (seed 20260923, 19 test faults): tp 14, fp 40, fn 5, tn 229, accuracy 0.8438,
recall 0.7368. The hero run trains on the six features plus `repair_minutes` over a random split whose
seed it never logs; the tests execute it with hidden seeds 11 and 12, which put 20 and 18 faults in
test and score 20 of 20 and 18 of 18. On the transfer plant the C = 1 run scores tp 9, fp 24, fn 6,
tn 249: recall 9/15 = 0.6, precision 9/33 = 0.2727, 33/36 = 0.9167 warnings a day.

### `expected/contract.json` — hand-authored

The fictional maintenance lead's requirement, written before any run: inputs are the six 09:00
features as doubles, in any order; the output is `fault_next_24h` as a long 0/1; on a time-based test
period a candidate must catch at least three of four faults (`recall_min` 0.75), one warning in five
must be real (`precision_min` 0.2), and it may add at most two ovens a day to the inspection round,
which holds two of the eight (`warnings_per_day_max` 2.0). The recall floor also sits above the
temperature rule's 0.6667 on this test period, so a candidate must beat the rule in use. The evidence
block lists what a run's record must hold before its metrics are read. Test 6 writes the solution's
contract and compares it with this literal.

### `expected/decisions.json` — hand-authored

- **Evidence reasons** follow from what each run logs. `time-split-*` runs log a time split, seed,
  training and evaluation datasets, the feature list and a signature. `random-split-seeded` logs
  `split=random`, hence `split_not_time_based`. `time-split-leaky` records `repair_minutes` in its
  feature list, whose dictionary role is `post_event`, and its signature has a seventh input the
  contract does not name, hence `post_event_feature:repair_minutes` and
  `unexpected_input:repair_minutes`. The hero logs only `model`, so it has no split, seed, training
  dataset, feature list or signature: five reasons. Reason lists are sorted.
- **Threshold reasons** compare `metrics.json` with the contract: C = 1 passes all three
  (0.8333 ≥ 0.75, 0.2206 ≥ 0.2, 1.8889 ≤ 2.0); C = 0.01 fails precision (0.1868) and the cap (2.5278);
  the transfer run fails recall (0.6).
- **The accuracy ranking** is `metrics.json`'s accuracy for the seven runs logged before anything else,
  highest first, ties broken by run name: the two leaks at 1.0, then never-warn at 0.9375.
- **Comparisons**: C = 1 against C = 0.01 differs in `C` only and trains on the same rows; against the
  leaky run, in `features` only (the logged dataset holds every column, so the rows are the same);
  against the random split, in `split`, `train_fraction` and `train_through_day`, on different rows;
  against the hero, in eight parameters, and the hero logged no dataset.
- **Reproduction refusals**: the hero's record lacks every parameter a rerun needs and its training
  dataset. The `environment_copy` case is a record built by the tests with the clean run's parameters
  and dataset but `scikit_learn=1.8.0`, which the installed 1.9.1 must refuse.
- **Drift cases**: renaming `humidity_pct` removes a required input and adds an unknown one; sending
  `door_cycles` as int64 changes its type from double to long; adding `repair_minutes` adds an unknown
  input; naming the output `prediction` breaks the output clause; reversing the column order is not
  drift, because columns are matched by name.
- **MLflow's own enforcement** (MLflow 3.16.1, pyfunc): the documented rule is that a missing required
  input raises and that only lossless type conversions are made. The message fragments are those this
  version prints: `Model is missing inputs ['humidity_pct']` and
  `Can not safely convert int64 to float64`. An extra input is logged as `These inputs will be ignored`
  and does not raise, which is why the contract checks unexpected inputs itself.
- **Registry**: one registration gives version 1 with alias `candidate`; a second registration gives
  version 2 and moving the alias leaves version 1 with no alias; moving it back is the rollback.

## Hashes

`run_tests.py --evidence <path>` writes the SHA-256 of every file under `fixtures/`, `expected/`,
`starters/` and `solutions/`, of `run_tests.py` and `requirements.txt`, and of a canonical JSON form of
each produced output (metrics, decisions, rankings, drift reasons, registry states). Run IDs and
timestamps are random and are kept out of the hashed outputs.
