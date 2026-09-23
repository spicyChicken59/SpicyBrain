# Lab L03 — Join cardinality: the total that multiplied

*Execution class R (local-executed): the reference solution ran on one
machine with Apache Spark 4.0.4, Python 3.12.3 and Java 21.0.10, `local[2]`,
UI off, two shuffle partitions, ANSI SQL mode at its Spark 4 default. No
Databricks workspace was involved. This page is studyable without
installing anything; the package `lab-l03-join-cardinality` holds the
files if you want to run it.*

## Purpose

Module A3's join beat says a join returns matching row pairs and does not
know what you meant. This lab lets you watch that produce a number a
manager would believe. Twenty accepted inspections are joined to a plant
dimension delivered as uncollapsed history — the key repeats — and the
total comes out at 410 inspected units instead of 256. You diagnose it
with counts and a duplicate-key check, repair it with an explicit
current-row rule, see two tempting non-repairs do nothing, then run the
same sequence on a second dimension with a different duplicate pattern.
Two more traps ride along: a per-plant average of rates that silently
drops a 0/0 inspection, and a LEFT JOIN whose `COUNT(*)` gives an empty
plant one inspection. Every expected number was derived by hand in
`DATA.md` before the code ran.

## The fixtures

Inspections (grain: one accepted current inspection; `inspection_id` unique):

| plant | inspections (inspected/defective) | rows | inspected | defective |
|---|---|---|---|---|
| P1 | I-01 12/1, I-02 8/0, I-03 20/3, I-12 14/2, I-18 16/0 | 5 | 70 | 6 |
| P2 | I-04 10/2, I-05 15/1, I-06 0/0, I-13 13/1, I-19 12/1 | 5 | 50 | 5 |
| P3 | I-07 9/0, I-08 18/2, I-09 4/0, I-14 7/1, I-20 11/1 | 5 | 49 | 4 |
| P4 | I-10 30/3, I-11 25/5, I-15 16/0 | 3 | 71 | 8 |
| P9 | I-16 10/1, I-17 6/0 | 2 | 16 | 1 |

Facts total 20 rows, 256 inspected, 24 defective. The plant dimension
(grain as delivered: one loaded *version* of a plant record):

| plant_id | plant_name | region | manager | valid_from | row_source |
|---|---|---|---|---|---|
| P1 | North Works | NE | R. Ahmed | 2024-01-01 | legacy-load |
| P1 | North Works | NE | L. Osei | 2026-01-01 | current-load |
| P2 | South Mill | SE | T. Brand | 2023-06-01 | legacy-load |
| P2 | South Mill | SE | T. Brand | 2025-03-01 | migration |
| P2 | South Mill | S | M. Vidal | 2026-02-01 | current-load |
| P3 | East Yard | NE | K. Ito | 2025-01-01 | current-load |
| P4 | West Forge | W | A. Costa | 2025-01-01 | current-load |
| P5 | Harbour Plant | W | J. Novak | 2025-01-01 | current-load |

P5 has no inspections; P9 has inspections and no row. The current-row rule
is stated, not guessed: the greatest `valid_from` per plant, ties broken by
`row_source` descending.

## Task 1 — grain and the duplicate-key check

Twenty facts, eight dimension rows. `GROUP BY plant_id HAVING COUNT(*) > 1`
returns **P1 ×2, P2 ×3** in both APIs. This one aggregate is the whole
diagnosis; everything after it is confirmation.

## Task 2 — the plausible wrong total (the failure case)

The inner join multiplies each P1 inspection by two versions and each P2
inspection by three, and drops P9: 5×2 + 5×3 + 5 + 3 = **33 rows**, **410
inspected, 39 defective, rate 0.0951**. The test asserts the wrong number
*and its reason*: 20 facts + 15 extra rows − 2 unmatched = 33. Both
interfaces return the same wrong total, which is the quiet lesson: SQL and
DataFrame agreeing proves the code is consistent, not that the relation is
the one you meant. Grouped by region the naive join shows NE 15 / 189 / 16,
SE 10 / 100 / 10, S 5 / 50 / 5, W 3 / 71 / 8 — and no current plant is in
SE. That phantom region is a symptom worth noticing and not relying on: the
transfer fixture has none.

## Task 3 — two non-repairs

Aggregating the facts to plant grain *first* and then joining the raw
dimension gives 7 rows that still sum to 410: the duplication is on the
dimension side, so collapsing the fact side cannot reach it. Applying
`distinct()` to the naive join leaves all 33 rows, because every joined row
differs in manager, date or source. Distinct removes identical rows; the
problem is a repeated key.

## Task 4 — the repair

`ROW_NUMBER() OVER (PARTITION BY plant_id ORDER BY valid_from DESC,
row_source DESC) = 1` keeps one version per plant. The aggregate form —
`max_by(attribute, valid_from)` per column — gives the same result once a
`has_ties` check has passed (it has no tie-break of its own). Window and
aggregate, DataFrame and SQL, all produce five rows: P1 L. Osei NE, P2
M. Vidal S, P3, P4, P5. Delivering the eight rows in reverse order changes
nothing; `dropDuplicates(["plant_id"])`, by contrast, kept the *oldest*
rows on this run (P1's 2024 record, P2's 2023 SE record), which the
evidence records and no test asserts, because Spark promises nothing about
which duplicate survives. Re-joined to the five current rows: inner
**18 rows, 240 / 23**; left **20 rows, 256 / 24**, 18 with a plant name,
I-16 and I-17 unmatched by `left_anti`, and `inner + unmatched = left` as an
identity. Which join is the report is a grain decision, not a repair.

## Task 5 — the region report in both APIs

| region | inspections | inspected | defective | defect_rate |
|---|---|---|---|---|
| null | 2 | 16 | 1 | 0.0625 |
| NE | 10 | 119 | 10 | 0.08403361344537816 |
| S | 5 | 50 | 5 | 0.1 |
| W | 3 | 71 | 8 | 0.11267605633802817 |

Sorted with nulls first, rows sum to 20; types string, bigint, bigint,
bigint, double; the SQL and DataFrame schemas are equal objects.

## Task 6 — the left-join null-count trap

Start from the current dimension and LEFT JOIN inspections. P5 produces one
row of nulls: `COUNT(*)` says 1, `COUNT(inspection_id)` says 0,
`SUM(inspected_units)` is NULL and `COALESCE(..., 0)` makes the zero an
explicit policy. Column totals are 19 by `COUNT(*)` and 18 by
`COUNT(inspection_id)` — neither is 20, because a dimension-driven report
cannot see P9's inspections at all. Count the other side's key; never `*`.

## Task 7 — weighted rate versus average of rates

Per plant over the facts: P1 6/70 = 0.0857 weighted against 0.0752 for the
mean of five row rates; P2 0.1 against 0.1067; P3 0.0816 against 0.0690;
P4 0.1127 against 0.1; P9 0.0625 against 0.05. Two mechanisms hide inside
the averages. P2's I-06 is 0/0: Spark 4's ANSI mode would raise on a plain
division, `try_divide` returns NULL instead, and `AVG` ignores NULL, so the
"average" quietly covers four of five inspections (`rate_rows` 4, `rows`
5). And P4's exact 1/10 printed as 0.10000000000000002 because 0.1 + 0.2 +
0.0 is not 0.3 in binary64 — so the averages are compared within 1e-12, a
tolerance justified in `DATA.md`, while the weighted rates (one division of
two integer sums) are compared exactly.

## Task 8 — transfer: a different duplicate pattern

`plants_transfer.json` has P3 ×3 (a rename to East Yard North and a move to
region N), P4 ×3, P9 present, P6 empty. Naive join: 5 + 5 + 15 + 9 + 2 =
**36 rows, 496 / 48**; aggregate-first 9 rows, still 496; distinct 36; no
phantom region, so only the duplicate-key check catches it. Six current
rows; inner and left joins both 20 rows 256 / 24 with nothing unmatched;
region W becomes P4 + P9 = 5 / 87 / 9; P6 is the empty plant with
`COUNT(*)` 21 against `COUNT(inspection_id)` 20. The author's first sum for
the naive total was 516; redoing it by hand gave 496, and the test would
have refused the wrong one.

## What the tests prove, and do not

Nine cases, zero skips, exit 0 on the pinned environment; three mutants on
a scratch copy — a wrong literal, the dedup removed, `COUNT(*)` in place of
`COUNT(inspection_id)` — each failed in exactly the tests that name its
rule. The evidence JSON carries versions, timestamps, SHA-256 of every
fixture, expected and solution file and of every collected output. Not
proved: Databricks Runtime behaviour, scale or performance; whether "latest
valid_from" is the right business rule (the fixtures assume it); behaviour
on ties, which the tie-break handles but no fixture exercises.

## Setup and cleanup

Install Python 3.12 and a JDK (Java 21.0.10 was used), set `JAVA_HOME`,
create a virtual environment, `pip install -r requirements.txt` (PySpark
4.0.4, Py4J 0.10.9.9), then run
`python run_tests.py --evidence local-evidence.json`. The runner stops
Spark itself, writes no bytecode and creates nothing but the evidence file
you name; cleanup is deleting `.venv/` and that file.
