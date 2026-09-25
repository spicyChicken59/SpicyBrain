*Execution class R (local-executed): the reference solution ran on one
machine with Apache Spark 4.0.4, Python 3.12.3 and Java 21.0.10, `local[2]`,
UI off, two shuffle partitions, session time zone UTC, ANSI SQL mode at its
Spark 4 default. No Databricks workspace, Unity Catalog object or metric view
was involved. This page is studyable without installing anything; the package
`lab-l11-modeling-metrics` holds the files if you want to run it.*

### Purpose

The data modeling module argues that a metric is only as good as the model
under it. This lab makes the argument with one synthetic dataset. Twenty-two
accepted Cinderline inspections arrive from silver with natural keys and
source units. You build a small star (one fact at the grain of one inspection;
line, plant, shift and date dimensions; supervisor history kept as type 2
rows), compute `unit_defect_rate` at line-day, plant-day and plant-month, and
let a metric contract drive the query parameters. Five deliberately broken
queries then show what the model and the contract prevent, each asserted to
fail for its stated reason. Every expected number was derived by hand before
the code ran.

### The fixtures

The baseline covers Thursday 26 March to Wednesday 1 April 2026; the weekend
of 28 and 29 March is not a business day. Quantities are shown in pieces after
conversion (line S2 records cases of 12).

| Line | Plant | Supervisor (type 2) | Inspections | Inspected | Defective |
|---|---|---|---|---|---|
| N1 | North | D. Varga to 29 Mar, P. Nair from 30 Mar | 8 | 1,000 | 21 |
| N2 | North | R. Iqbal | 4 (one of 0 pieces) | 250 | 6 |
| S1 | South | T. Lindqvist | 5 | 600 | 12 |
| S2 | South | J. Castillo | 4 (in cases) | 540 | 24 |
| N3 | not in the dimension | none | 1 | 50 | 2 |

Totals: 22 inspections, 2,440 inspected and 65 defective pieces. Two night-shift
inspections on S1 sit on either side of midnight: I-18 at 23:59:59 on 31 March
and I-19 at 00:00:00 on 1 April.

The metric contract (`fixtures/metric_contract.json`) states: one value per
line per business day; defective pieces over inspected pieces of the same
accepted inspections; pieces as the unit, with no conversion meaning
quarantine; a business day of 00:00:00 to 23:59:59 plant local time; a window
of the last three business days of the plant calendar; `no_inspections` and
`no_units` for empty cases, with no rate; line_sk -1 for unknown lines; the
quality lead as owner.

### Task 1 — the fact at its grain

The fact resolves each inspection to the line version valid on its business
day, once, at load (`valid_from` inclusive, `valid_to` exclusive), maps a line
with no valid version to the unknown member, and converts both quantities to
pieces. Intermediate output: 22 fact rows, no inspection twice, I-09 on
version 101 (D. Varga), I-10 on version 102 (P. Nair), I-21 on line_sk -1,
I-08 as 120 / 12 pieces. The model checks find no duplicate inspection, no
overlapping versions and one current row per line; the only orphan is I-21.

### Task 2 — one metric at three grains

The line-day grid lists every line version on every business day plus every
observed line-day, so silent days appear. Selected rows:

| Grain | Row | Inspected / defective | Status | Rate |
|---|---|---|---|---|
| Line-day | N1, 27 Mar | 200 / 4 | ok | 2.0% |
| Line-day | S2, 30 Mar | 0 / 0 | no_inspections | none |
| Line-day | N2, 31 Mar | 0 / 0 | no_units | none |
| Plant-day | North, 27 Mar | 300 / 9 | ok | 3.0% |
| Plant-month | North, March | 1,000 / 22 | ok | 2.2% |
| Plant-month | South, March | 840 / 21 | ok | 2.5% |
| Plant-month | UNKNOWN, April | 50 / 2 | ok | 4.0% |

The tests reconcile the collected rows: every plant-day equals the sum of its
line-days, every plant-month the sum of its plant-days, and the months sum to
2,440 / 65. Averaging instead gives North 3.5% on 27 March (against 3.0%) and
2.125% for March (against 2.2%).

### Task 3 — the five failures

| Broken query | Output | What it violates |
|---|---|---|
| Plain `SUM / SUM` | `DIVIDE_BY_ZERO` on N2's 31 March | An empty denominator gives no rate |
| Source quantities summed | South, 27 March: 190 / 4 = 2.1% against 300 / 15 = 5.0% | Convert before summing |
| Inner join to the line dimension | 21 rows, 2,390 / 63 against 22 rows, 2,440 / 65 | Missing keys stay visible |
| History joined on `line_id` | 29 rows; North 2,250 / 48; D. Varga and P. Nair each 1,000 / 21 | Join history on its validity window |
| Three calendar days as of Monday 30 March | one business day: North 300 / 6 = 2.0% against 800 / 18 = 2.25% | Count business days |

Two details make the tests strict. On 26 March and 1 April the unit mistake
changes South's sums while its rate happens to agree, so the test compares
parts, not only rates. And the history double count barely moves North's rate
(2.13% against 2.16%) while inflating its pieces by 80%, so the test counts
rows and pieces.

### Task 4 — the transfer set and the negative cases

The same SQL runs unchanged on an altered set: a 24-piece case, a supervisor
change on S2 dated 30 April (the day of inspection T-09, which must go to the
new supervisor), a shutdown on Friday 1 May, an unknown line S9 and a tray
inspection with no conversion (quarantined, never summed). As of Monday 4 May
the business window is 29 April, 30 April and 4 May; a Monday-to-Friday rule
would take 1 May instead of 29 April. A mutated line dimension whose versions
overlap is caught by the overlap check before it can inflate the fact to 24
rows, and five incomplete contracts are refused with named reasons.

### What the tests prove, and do not

They prove that this Spark SQL, on these fixtures, matches hand-derived
literals at every grain and that each broken approach fails for its stated
reason; the starter file fails 18 of the 20 cases until its gaps are filled.
They do not prove the contract suits a real plant, say anything about
performance (toy data, no benchmark), or exercise Databricks: the metric view
sketch in the solutions is an unexecuted platform adaptation.

### Setup and cleanup

Use Python 3.12 with the package's `requirements.txt` installed (PySpark 4.0.4,
Py4J 0.10.9.9) and a Java 17 or 21 runtime, then run `python run_tests.py
--evidence local-evidence.json`; `--sql starters/model.sql` tests your own
file. The runner creates one temporary directory for Spark and deletes it when
the session stops; delete the virtual environment and any evidence file when
done.
