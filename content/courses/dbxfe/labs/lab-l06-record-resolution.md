# Lab L06 — Record resolution: retained evidence, current state, publication

*Local-executed (R), plain Python 3.12, standard library only. Nothing to
install; nothing runs on Databricks.*

## What this lab is for

Module B3 ends with one idea that is easy to nod at and hard to keep: a
clean-looking table of "current" inspections is not evidence that the input
was valid, that the history is free of contradictions, or that the number on
it may be published. This lab makes you hold four outputs apart — **raw**
(what arrived, repeats included), **quarantine** (rows with reasons),
**accepted** (at most one valid current replacement per inspection) and the
**publication decision** — first on the five Cinderline rows the module uses
everywhere, then on a second fictional plant whose answers you predict before
you see them.

The resolver you check against is the original Cinderline reference from the
reliable-data package, copied unchanged. Its SHA-256 is
`cc4a8f46270e8f1c3e1ab4a4a24d85af3b4c9611f3983fa2656ed73f87a43510`, the test
runner asserts that hash every run, and the file imports only `copy`,
`hashlib`, `csv` and `json` — there is no Spark in it, which is why this lab
needs only `/usr/bin/python3.12`.

## The fixtures

Cinderline, `fixtures/cinderline-baseline.json` (arrival order):

| # | event_id | inspection_id | version | inspected | defective |
|---|---|---|---|---|---|
| 0 | ev1 | A | 1 | 10 | 1 |
| 1 | ev1 | A | 1 | 10 | 1 |
| 2 | ev2 | B | 1 | −3 | 1 |
| 3 | ev3 | A | 2 | 12 | 1 |
| 4 | ev4 | C | 1 | 8 | 0 |

Northgate valve seats, `fixtures/northgate-baseline.json`:

| # | event_id | inspection_id | version | inspected | defective |
|---|---|---|---|---|---|
| 0 | ng-e1 | VS-1 | 1 | 40 | 2 |
| 1 | ng-e2 | VS-2 | 1 | 25 | 0 |
| 2 | ng-e2 | VS-2 | 1 | 25 | 0 |
| 3 | ng-e3 | VS-3 | 1 | 30 | 31 |
| 4 | ng-e4 | VS-1 | 2 | 42 | 2 |
| 5 | ng-e5 | VS-4 | 1 | 0 | 0 |
| 6 | ng-e6 | VS-5 | 2 | 18 | 4 |

Each plant has a batches file with a late older revision, a valid correction,
a same-event conflicting payload, a same-key/version conflict under a new
event ID, an invalid latest revision, an unordered observation and a set of
invalid rows, plus an unkeyed-conflict file: two rows sharing one event ID,
no usable inspection ID, and different quantities. Every expected value in
`expected/` was written by hand from the contract; `DATA.md` shows the
arithmetic and the raw-index bookkeeping.

## Task 1 — one baseline, four outputs

Resolving the Cinderline rows gives raw 5; quarantine `[(2,
['invalid_inspected_units', 'defective_exceeds_inspected'])]` — B fails twice,
since −3 is out of range and 1 > −3; accepted A v2 12/1 and C v1 8/0; totals
20/1 with rate 0.05; excluded `["B"]`; unresolved `[]`; publication allowed.
The repeated ev1 is one delivery counted once; A v1 is superseded, not
rejected. The report is accepted-only with a disclosed exclusion.

## Task 2 — the flawed resolver

`starters/resolver.py` drops invalid rows, keeps the last arrival per key and
compares nothing. On baseline + an invalid A v3 it prints A **v2** 12/1 as
current: the invalid revision vanished and an older one came back. The
reference instead accepts C only and lists A as unresolved. On baseline + a
conflicting A v2 = 13/1 it answers 13/1 forwards and 10/1 when the input is
reversed — two answers for one history. The reference reports one
`key_version` conflict for `["A", 2]` either way (raw indices [3, 5]
forwards, [0, 2] reversed), and blocks A.

## Task 3 — the preserved regressions

Replay (`baseline + baseline`): raw 10, accepted rows, totals and the
published snapshot identical, still one local effect. Late A v1 under a new
event ID: nothing changes. A v3 = 14/1: A v3 and C v1, totals 22/1 (rate
0.045454545454545456), once — ingesting the correction twice leaves two
effects, not three. Event or version conflict after the baseline: accepted
C only, 8/0, unresolved `["A"]`, status `stale_previous`, the published 20/1
untouched. Invalid latest and unordered observation: the same blocked
outcome with no conflict entry. A conflict in the very first ingest:
`blocked_no_snapshot`, no report, no effect.

## Task 4 — the gate that looks right

`naive_gate` publishes whenever the unresolved list is empty. On the unkeyed
pair it returns `True` while the resolver says `publication_allowed: false`,
because the conflict is on an event ID with no key to list. After a verified
20/1 baseline, ingesting the second unkeyed row together with A v3 leaves a
perfectly plausible 22/1 **candidate** — and a blocked publication, the 20/1
snapshot labelled `stale_previous`, one effect. The candidate is diagnostic
output; it is not a report.

## Task 5 — Northgate, predicted first

`starters/northgate_predictions.py` is a prediction sheet checked against the
hand-authored literals. Baseline: VS-1 v2 42/2, VS-2 v1 25/0, VS-4 v1 0/0,
VS-5 v2 18/4, totals 85/6 (rate 0.07058823529411765), VS-3 excluded. Zero is
a value: VS-4 is accepted and adds nothing. VS-5's v1 arriving late is
retained and ignored. The correction VS-2 v2 26/1 gives 86/7. A conflicting
VS-1 v2 = 43/2 blocks VS-1 and leaves 43/4 with conflicts at [4, 7]. The
`invalid` batch alone accepts nothing, excludes VS-6…VS-9, and is
**publishable** — the gate asks whether the evidence contradicts itself, not
whether it is worth publishing; a publisher needs a separate coverage check.

## Task 6 — failure boundaries

Failing after `retained_raw` while ingesting the correction leaves raw 8,
`stale_previous`, published 85/6 and one effect; recovery recomputes from the
eight rows and publishes 86/7 with two effects. Failing after
`published_snapshot` leaves 86/7 current but one effect; two recoveries give
exactly two, because the outbox is keyed by snapshot ID.

## What the tests prove and do not prove

Twenty-four `unittest` cases (0 skipped) hold the unchanged reference to the
hand-authored literals for both plants, assert the copy's hash, and assert
that the flawed starter and the naive gate fail *for the documented reasons*
(v2 resurrected, order-dependent winner, conflict published). Three
mutations were run to show the suite can go red: one appended byte to the
reference, one wrong Northgate total, and the invalid-latest guard removed.
The tests do not prove Delta MERGE behaviour, durable orchestration,
exactly-once notification, scale, or complete source coverage; the pipeline
is a Python dictionary and its notification is an entry in it.

## Setup and cleanup

`python3.12 run_tests.py --evidence local-evidence.json` from the package
directory; `python3.12 solutions/scenarios.py` prints every scenario. The
runner writes no bytecode. Delete the evidence file when done; nothing else
is created.
