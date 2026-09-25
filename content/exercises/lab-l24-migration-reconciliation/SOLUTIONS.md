# Lab L24 solutions

The complete reference is `solutions/migration.py`; this file explains each
decision, shows the intermediate outputs the tests pin, and walks through the
translation that looks right and is not. Everything here was executed on
local Apache Spark 4.0.4; the legacy procedure was only read.

## 1. The inventory comes before the translation

`scan_tsql()` reads the procedure text with regular expressions (comments
removed first). Its findings, which match a reading by hand:

| Finding | Value | Why it matters on the target |
|---|---|---|
| Reads | erp.inspection, erp.inspector, etl.watermark, dbo.rpt_quality_detail | sources and the table rebuilt in place |
| Writes | etl.watermark, dbo.rpt_quality_daily, dbo.rpt_quality_detail | three writes that one transaction made atomic |
| Temporary object | #affected_days | a session-scoped handoff that becomes a named intermediate result |
| Clock | GETDATE() | server local time, no offset stored |
| Day rule | DATEADD(HOUR, -6, i.inspected_at) | a business day computed on a wall clock |
| Arithmetic | s.units_defective * 100 / s.units_inspected | INT / INT truncates in T-SQL |
| Collation | 7 `*_code = *_code` comparisons | the collation, not the data, decides equality |
| NULL handling | ISNULL(s.shift_code, N'UNASSIGNED') and two ON predicates | the plant filter lives in ON, not WHERE |
| State | etl.watermark | incremental position, updated inside the transaction |
| Transaction | DELETE, INSERT, MERGE, UPDATE inside BEGIN/COMMIT, XACT_ABORT ON | all-or-nothing on the source |
| MERGE | no WHEN NOT MATCHED BY SOURCE | a group that disappears after a correction would stay in the report |

A regular expression cannot see dynamic SQL, synonyms, views, triggers on the
tables it names or callers of the procedure; the inventory is a starting list
that a person completes. `map_package()` turns the SSIS-style control flow
into four tasks: the Foreach Loop and the Data Flow inside it become one file
ingestion task, each Execute SQL Task becomes a task, Success constraints
become dependencies with `all_succeeded`, and the three Failure constraints
joined by logical OR become one notification task that depends on all three
with `at_least_one_failed`. The Agent schedule gains the time zone it never
recorded.

## 2. Five semantic choices, made explicitly

```python
TARGET = Rules(key_rule="collation", join_rule="on", day_rule="server_local",
               division="integer", amount_type="decimal")
```

- **Keys**: `upper(rtrim(code))` on both sides. SQL Server pads the shorter
  string with spaces before `=` compares, so trailing spaces never count,
  and the CI collation ignores case. Leading spaces do count, which is why
  `rtrim`, not `trim`, is correct.
- **Join**: the plant predicate stays in the join condition.
- **Day**: `to_date(inspected_local - INTERVAL 6 HOURS)` on a
  `timestamp_ntz` column, so no session setting can move it.
- **Division**: `(units_defective * 100) div units_inspected` returns a
  BIGINT, as INT / INT did.
- **Money**: `decimal(12,2)` in, `decimal(22,2)` after `SUM` (Spark adds ten
  digits of precision), compared exactly.

Target detail for P1 (the tests compare all eleven rows):

| id | business_day | shift | code | units | defective | cost |
|---|---|---|---|---|---|---|
| 101 | 2026-03-02 | DAY | QA07 | 120 | 4 | 4.50 |
| 103 | 2026-03-02 | NIGHT | QA11 | 60 | 1 | 0.20 |
| 104 | 2026-03-03 | DAY | qa07 | 100 | 5 | 7.25 |
| 105 | 2026-03-03 | DAY | `QA07 ` | 90 | 0 | 0.00 |
| 106 | 2026-03-03 | UNASSIGNED | NULL | 40 | 4 | 12.00 |
| 109 | 2026-03-03 | NIGHT | QA11 | 50 | 1 | 0.70 |
| 111 | 2026-03-03 | UNASSIGNED | QA99 | 30 | 1 | 3.30 |

(102, 107, 108 and 110 follow the same rules; 112 is excluded because it was
updated at 06:40, after the as-of moment.) The report is the six-row table in
TASKS.md and it reconciles with the legacy report on every check.

## 3. The wrong approach: a line-by-line translation

```python
# Compiles, runs, and returns six report rows — the same count as the legacy report.
joined = i.join(s, i.inspector_code == s.inspector_code, "left") \
          .where(s.plant_code == "P1")                        # ON predicate moved to WHERE
instant = to_timestamp(concat(inspected_at, " America/New_York"), "... VV")
day = to_date(instant - expr("INTERVAL 6 HOURS"))             # rendered in the UTC session
pct = col("units_defective") * 100 / col("units_inspected")   # Spark '/' is fractional
cost = col("rework_cost").cast("double")                       # money as DOUBLE
```

Reconciled against the legacy report it fails every check, yet
`row_counts.report` is `[6, 6]`. What each check found:

| Check | Finding | Cause |
|---|---|---|
| detail keys | 104, 105, 106, 111 missing; 103 and 109 on a later day | binary keys + WHERE filter; UTC day |
| report keys | 3 March UNASSIGNED missing, 4 March NIGHT extra, 4 groups changed | the same rows, aggregated |
| totals | 2 March 260 → 200 units, 3 March 490 → 240, 4 March 40 → 90 | rows dropped and moved |
| nulls | detail.inspector_code 1 → 0 | the NULL-key row vanished in the WHERE |
| types | rework_cost double, defect_pct double | DOUBLE money, fractional division |

Single flips show which check owns which defect. Binary keys alone move 104
and 105 from DAY to UNASSIGNED: 3 March DAY becomes 1/110/3/1.10, UNASSIGNED
becomes 4/260/10/22.55, and the day totals stay 490/16/26.55 — only the key
checks fail. A totals-only reconciliation would have accepted it. The session
flip passes when the session zone is America/New_York and fails under UTC:
the translation is right only by accident of configuration. Double money
fails only where binary floating point shows: 0.10 + 0.20 is
0.30000000000000004 and 2.20 + 0.70 is 2.9000000000000004, while 8.35 and 15.3
happen to print exactly — the type check catches the column before anyone
argues about tolerances.

## 4. Incremental state and the retry

`affected_days()` selects `updated_local > since AND updated_local <= until`
and returns the business days of those rows; `run_window()` replaces those
days in the detail, then in the report, and only then advances the
watermark. Tonight's window returns 2, 3 and 4 March: inspection 101 was
corrected (3 → 4 defective) at 16:00 on 3 March, so an old day is rebuilt.
Selecting by `inspected_at` returns 3 and 4 March only; the report keeps
2 March DAY at 3 defective and 2 %, and the reconciliation names that key.

With a failure injected after the detail write, the watermark stays at
`2026-03-03 06:30:00.000`, the report still has its two old rows, and
`consistent()` reports that the report no longer summarizes the detail. The
retry recomputes the same days from the same basis and converges to the
legacy report. On the source one transaction gave that guarantee; here it
comes from recomputing whole days and moving the watermark last.

## 5. Transfer, register and gate

On P2 the legacy-compatible rules reconcile first time. `trim` instead of
`rtrim` joins ` QA21` to the DAY shift: 10 March DAY becomes 2/350/9/7.50/2,
UNASSIGNED disappears, and the day total is unchanged — the P1 data could
never have shown this, because P1 has no leading-space code. The intended
plant-local rule moves 205 (05:25 Chicago) and 206 (05:05 Chicago) to
10 March. `explain()` accepts each move only if the register's owned entry
predicts it (field, direction and the 05:00–06:00 Chicago hour), then
re-derives the legacy report with the moves applied and requires it to equal
the new report exactly: verdict `explained`, residue empty. Remove the owner
and the same differences become unexplained. The gate counts clean days only
after the last code change: the pass on 9 March is not credit.

## What the tests prove and do not prove

They prove that this target transformation reproduces the hand-derived
legacy outputs on these fixtures, that each of the five translation defects
is caught by a named check, that the retry converges, and that the register
and gate apply their rules. They do not prove equivalence on other data,
that SQL Server would produce exactly these fixtures, or anything about
performance. The fixtures do not exercise the MERGE that never deletes (no
group disappears), deletes in the source (a timestamp watermark cannot see
them) or non-ASCII collation behaviour.
