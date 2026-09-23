# Tasks

Predict on paper before you run anything. Every expected value you will be
checked against was written by hand (see `DATA.md`), so a prediction that
disagrees with the file is worth investigating in both directions.

## 1. Four outputs, one baseline

Read `fixtures/cinderline-baseline.json` (five rows). Without running code,
write down: the raw count; the quarantined rows and their reasons; the
accepted current rows; the totals and unit defect rate; the excluded keys;
the unresolved keys; and the publication decision. Then explain, in one
sentence each, why *raw*, *quarantine*, *accepted* and *publication* must be
four separate outputs rather than one "clean table".

Expected behaviour: A v2 = 12/1 and C v1 = 8/0 accepted; B quarantined with two
reasons; totals 20/1, rate 0.05; excluded `["B"]`; unresolved `[]`;
publication allowed.

## 2. Repair the flawed resolver

`starters/resolver.py:flawed_current` does three things wrong. Demonstrate
each with a fixture before you fix anything:

- run it over baseline + `invalid_latest` — which A row does it report, and
  what does the reference say instead?
- run it over baseline + `version_conflict`, forwards and reversed — why do the
  two answers differ, and which one is "right"?
- what does it do with the two `cinderline-unkeyed.json` rows?

Then implement `resolve(history)` so it returns the same keys as the
reference and passes every literal in `expected/cinderline.json`. Do not read
`solutions/reference.py` until yours passes or you are stuck.

## 3. The preserved regressions

Using your resolver (or the reference), reproduce and explain each invariant:
replay (`baseline + baseline`) keeps accepted rows, totals and the published
snapshot; `late` (A v1 again under a new event ID) changes nothing; `correction`
(A v3 = 14/1) gives 22/1 once, even when ingested twice; `event_conflict` and
`version_conflict` block A across batches and under `reversed(...)`;
`invalid_latest` and `missing_order` block A rather than reviving v2. Record
the raw count, the conflict entries with their raw indices, and the pipeline
status after each.

## 4. The gate that looks right and is wrong

`starters/resolver.py:naive_gate` publishes whenever `unresolved` is empty.
Feed it the resolver's result for `cinderline-unkeyed.json` on a first run:
what does it return, what does `publication_allowed` say, and why is the
unresolved list empty even though there is a conflict? Now publish the
baseline, ingest the first unkeyed row, then the second together with A v3.
State the accepted candidate, its totals, the published totals, the status
and the local effect count. Explain why 22/1 is a candidate and not a report.

## 5. Transfer: Northgate valve seats

Open `fixtures/northgate-baseline.json`, `northgate-batches.json` and
`northgate-unkeyed.json`. Fill in `starters/northgate_predictions.py` for the
four scenarios it names (baseline, correction, blocked, invalid-only) and run
it; it compares your predictions with the authored literals without running
the resolver. Then answer:

- VS-4 reports 0 inspected / 0 defective. Is it accepted? What does it add to
  the totals, and what is the difference between a zero and a missing value?
- VS-5 arrives as v2 before its v1. What happens when v1 arrives later?
- the `invalid` batch on its own: nothing is accepted, four keys are excluded,
  and `publication_allowed` is **true**. Is that a defect in the policy, and
  what would a publisher have to check separately?

## 6. Failure boundaries on the transfer plant

Publish the Northgate baseline. Ingest the correction with
`fail_after="retained_raw"`: record raw count, status, published totals and
effect count, then `recover()` and record them again. Repeat with
`fail_after="published_snapshot"` and call `recover()` twice. Why is the
effect count 2 and not 3, and why must publication state and effect state be
different things?
