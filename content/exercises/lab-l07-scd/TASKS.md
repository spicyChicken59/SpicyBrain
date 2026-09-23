# Lab L07 tasks

Work in `starters/scd_task.py`. Each task says what correct behaviour looks
like; the literals to compare with are in `expected/`, and DATA.md explains how
every one was derived. Do not open SOLUTIONS.md until you have tried.

## Task 1 — Predict before you run anything

Read `fixtures/cinderline-events.json` and the source contract in DATA.md, then
fill in `PREDICTIONS` at the top of the starter:

1. P-100's unit cost in the current table after all three batches. Its seq 2
   event arrives in batch 3, after seq 3 arrived in batch 2.
2. How many validity intervals P-100 has in the history table after batch 3.
3. Whether P-300 is current, withheld or deleted after batch 3 (look at e-08
   and e-15).
4. What happens to P-400 after batch 2, whose second event says `"seq": "2"`.
5. Whether P-200 has an open history row after batch 2 (its seq 2 is a delete).

Expected behaviour: each prediction names a value and a reason taken from the
contract, never from arrival order.

## Task 2 — Watch two plausible designs fail

Run `python starters/scd_task.py`. It calls two deliberately flawed functions.

- `last_arrival_wins` builds a current table by letting the last valid arrival
  per key win. Compare its P-100, P-300 and P-400 with
  `expected/cinderline.json` → `current`. Expected behaviour: P-100 shows the
  older 1290, and P-300 and P-400 appear although the contract cannot resolve
  them. Write one sentence per key saying which promise the function ignored.
- `append_per_arrival` builds a history by closing the open row at each new
  arrival. Pass its result to `solutions.scd_reference.check_intervals`.
  Expected behaviour: a `ScdContractError` whose `reason` is `interval_order`
  for P-100, on a row that runs from [3] to [2]. Explain which arrival produced
  that row.

## Task 3 — Type 1 with a window

Implement `current_rows_scd1(spark, events, contract)`. Use `resolve()` from the
reference for validation, deduplication, ties and unplaceable events (module B3
covered those), then compute the current table in Spark: one row per resolved
key, the state with the highest sequence, no row when that state is a delete.
Return a list of dictionaries shaped like `expected/cinderline.json` →
`current`, sorted by key, with the sequence as a list (`[3]`).

Expected behaviour: through batch 1, five rows at `[1]`; through batch 2, four
rows (P-200 deleted, P-400 withheld); through batch 3, the four rows in
`current`.

## Task 4 — Type 2 with a window

Implement `history_rows_scd2(spark, events, contract)`: per upsert state, a
row with `valid_from` = its sequence, `valid_to` = the next state's sequence
for that key (whether that state is an upsert or a delete) or null, and
`is_current` true only when `valid_to` is null.

Expected behaviour: the rows in `expected/cinderline.json` → `history` after
batch 3, and the `stages` rows after batches 1 and 2. A delete closes a row and
opens none, so P-200 shows a gap from [2] to [3]. Hint: decide where the
filter that removes delete rows goes relative to the window.

## Task 5 — Check the invariants, then break them on purpose

Run `check_current_unique` on your current table and `check_intervals` on your
history. Expected behaviour: both pass, and `check_intervals` returns exactly the
`gaps` literal. Then build three broken tables by hand — a second P-100 current
row, P-100's first interval stretched to end at [3], P-600's first version
reopened — and confirm each fails with `duplicate_current_key`, `overlap` and
`open_rows_per_key` respectively. Write down why passing these checks is not
the same as being correct (hint: run them on `last_arrival_wins`).

## Task 6 — Transfer: another source, another contract

Run your two functions on `fixtures/marlow-events.json` with
`MARLOW_COMPOSITE` (ordered by `seq`, then `revision_no`) and with
`MARLOW_SINGLE` (ordered by `seq` alone). Predict first. Expected behaviour:
under the composite contract C-1 has three versions and m-08 is redundant
evidence; under the single contract C-1 is withheld as `tied_sequence` with two
candidates, and only C-2 is published. Both results are in
`expected/marlow.json`.

## Task 7 — Snapshots instead of events

Call `snapshot_changes` on `fixtures/supplier-snapshots.json` and feed the
derived changes to your functions with `SUPPLIERS`. Expected behaviour: eight
changes, SUP-B with three versions (7, 9, 7 days). Then drop snapshot 2 and
repeat. Expected behaviour: SUP-B has one version and SUP-C's delete moves to
snapshot 3. Explain in two sentences what a snapshot cadence can never show.

## Task 8 — Adapt it on paper (not executed)

Without running anything, write the Databricks AUTO CDC declaration that would
maintain Marlow's history table: which columns are the keys, what the sequence
expression is, which condition marks a delete, which columns are excluded, and
which SCD type is stored. Then list two things the reference does that the
declaration does not do for you, and say where in your pipeline they would go.
Compare with section 9 of SOLUTIONS.md afterwards.

## Run the checks

```bash
python run_tests.py --evidence local-evidence.json
```

Seventeen tests should pass with no skips. The runner compares the reference,
not your starter, with the literals; to test your own functions, call them from
a scratch script and compare with the same files.
