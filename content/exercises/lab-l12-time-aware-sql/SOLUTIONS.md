# Solutions, intermediate outputs and the wrong approaches

The complete reference is `solutions/portfolio.sql` (55 named blocks); `solutions/portfolio.py`
loads the fixtures with explicit schemas, sets the session time zone to `America/New_York` and
runs each named block. Every output below is a row the tests observed on local Apache Spark
4.0.4 and matches `expected/*.json`. SQL quoted here is copied from the reference file.

## T1–T3 Windows

```sql
SUM(units) OVER (
  PARTITION BY machine_id
  ORDER BY day, shift
  ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_rows
```

M1: 50, 90, 145, 190, **190** (the NULL shift adds nothing), 240, 300, 330. The analyzed plan
names the frame `RowFrame`. **Wrong approach that passes a value check:** the starter's block
without a frame clause returns the same eight numbers, because `(day, shift)` is unique per
machine, but Spark resolves it as the default `RangeFrame`; the day a second row shares a key,
its totals change. The test `test_values_alone_cannot_see_a_missing_frame_clause` runs exactly
that block and asserts both facts.

Default frame (`ORDER BY day` only): `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`, and
RANGE includes every peer row with the same ordering value, so both M1 rows of 2026-03-01 read
90 and both of 2026-03-04 read 330. **Wrong approach:** treating the default as "one row at a
time"; it only looks that way when the ordering key is unique.

Moving average (`ROWS BETWEEN 2 PRECEDING AND CURRENT ROW`), M1:

| row | units | avg3 | measured | rows_in_frame | complete |
|---|---|---|---|---|---|
| 03-01 D | 50 | 50.0 | 1 | 1 | false |
| 03-01 N | 40 | 45.0 | 2 | 2 | false |
| 03-02 D | 55 | 48.33 | 3 | 3 | true |
| 03-02 N | 45 | 46.67 | 3 | 3 | true |
| 03-03 D | NULL | 50.0 | 2 | 3 | true |
| 03-03 N | 50 | 47.5 | 2 | 3 | true |
| 03-04 D | 60 | 55.0 | 2 | 3 | true |
| 03-04 N | 30 | 46.67 | 3 | 3 | true |

`AVG` divides by the count of non-null values, so a NULL inside a complete frame still yields a
two-value average; `COUNT(*)` and `COUNT(units)` make that visible. **Wrong approach:**
`SUM(units) / 3`, which silently under-reports the frames containing the NULL and the two
incomplete frames at the start.

Rows against days (`range_versus_rows`, four synthetic days):

| day | units | last_three_rows (ROWS 2 PRECEDING) | last_three_days (RANGE INTERVAL 2 DAYS) |
|---|---|---|---|
| 2026-03-01 | 10 | 10 | 10 |
| 2026-03-02 | 20 | 30 | 30 |
| 2026-03-05 | 50 | 80 | 50 |
| 2026-03-06 | 60 | 130 | 110 |

On 5 March the ROWS frame reaches back to 1 and 2 March because it counts rows; the RANGE frame
covers 3–5 March, of which only 5 March has a row. **Wrong approach:** calling a three-row
frame "the last three days" over a calendar with gaps.

## T4 Ranking

| machine | total | RANK | DENSE_RANK | ROW_NUMBER |
|---|---|---|---|---|
| M1 | 330 | 1 | 1 | 1 |
| M4 | 300 | 2 | 2 | 2 |
| M2 | 225 | 3 | 3 | 3 |
| M3 | 225 | 3 | 3 | 4 |

Top per plant: North M1 (330), South M4 (300). **Wrong approach:**
`ROW_NUMBER() OVER (ORDER BY total_units DESC)` without `machine_id`; nothing in the query
decides whether M2 or M3 receives 3, so the answer may differ between runs.

## T5 Latest inspection

```sql
WITH distinct_rows AS (
  SELECT DISTINCT * FROM inspections),
numbered AS (
  SELECT *,
         ROW_NUMBER() OVER (PARTITION BY inspection_id
                            ORDER BY revision DESC,
                                     CAST(received_at AS TIMESTAMP) DESC) AS rn,
         COUNT(*) OVER (PARTITION BY inspection_id, revision) AS rows_at_revision
  FROM distinct_rows)
SELECT inspection_id, revision, received_at, machine_id, result,
       measurements, defect_codes, raw_units,
       rows_at_revision > 1 AS ambiguous_revision
FROM numbered
WHERE rn = 1
```

Counts 10 → 9 → 6. I-104 keeps the 08:05Z PASS row and is flagged `ambiguous_revision = true`.
**Wrong approaches:** `SELECT DISTINCT` alone (keeps both revisions of I-100 and both I-104 rows:
9 rows, not 6); `ORDER BY revision DESC` alone (I-104's choice is left to the engine and nothing
reports it).

## T6 DOWN islands

```sql
DATE_SUB(day, ROW_NUMBER() OVER (PARTITION BY machine_id, status
                                 ORDER BY day)) AS island_key
```

M1 DOWN days 02, 03, 06, 08, 09, 10 get keys 03-01, 03-01, 03-03, 03-04, 03-04, 03-04 →
islands 02–03 (2 days), 06 (1), 08–10 (3, open at data end). M2: 01 (1), 05 (1).
**Wrong approach:** `GROUP BY machine_id` over the DOWN rows returns M1 02–10 with 6 days as if
it were one outage; the test asserts that answer is produced and differs.

## T7 Membership

Semi join (at least one DOWN day): M1, M2. Anti join (no output rows): M5. Never inspected:
`NOT EXISTS` and `LEFT ANTI JOIN` both return M4, M5; `NOT IN (SELECT machine_id FROM
inspections)` returns **no rows** because the subquery contains a NULL and `x NOT IN (…, NULL)`
is never true. Inner join to DOWN rows returns 8 rows (M1 six, M2 two) where the semi join
returns 2: a join multiplies, a semi join only asks.

## T8 Set operators

`UNION` 4 rows (M1..M4); `UNION ALL` 6 rows; `INTERSECT` M1, M2; registry `EXCEPT` output = M5;
inspections `UNION` status = NULL, M1, M2, M3 (one NULL); inspections `EXCEPT` registry = NULL;
inspections `INTERSECT` registry = M1, M2, M3. Positional trap:

| machine_id | plant |
|---|---|
| M1 | North |
| M2 | North |
| South | M3 |
| South | M4 |
| South | M5 |

No error is raised; columns are matched by position, never by name. When the types differ
(`units` INT with `machine_id` STRING) ANSI mode casts the text branch to a number (BIGINT on
this build) and the statement fails with `CAST_INVALID_INPUT`. With ANSI mode off (transfer 4)
the same statement succeeds and returns one STRING column of 24 values, the numbers turned into
text: no error, and a column that no longer means anything.

## T9 Nested fields

`measurements.width_mm` and `.weight_g` are ordinary column paths; `grams_per_mm` is NULL for
I-101 because its weight is NULL. `SIZE`, `ARRAY_CONTAINS` and `TRY_ELEMENT_AT(defect_codes, 1)`
give I-100 1/true/SCRATCH, I-102 2/true/DENT, the rest 0/false/NULL. `defect_codes[0]` and
`ELEMENT_AT(defect_codes, 1)` both return SCRATCH and DENT for the two inspections with codes:
the bracket is 0-based and `ELEMENT_AT` 1-based. `EXPLODE` yields 3 rows (SCRATCH 2, DENT 1);
`LATERAL VIEW OUTER EXPLODE` yields 7 (four NULL-code rows kept). **Failure cases:** on the empty
arrays `ELEMENT_AT(defect_codes, 1)` raises `INVALID_ARRAY_INDEX_IN_ELEMENT_AT` and
`defect_codes[0]` raises `INVALID_ARRAY_INDEX` under ANSI mode; with ANSI off both return NULL.

## T10 Safe casts and null arithmetic

| inspection | raw_units | units | defects | defects_per_unit |
|---|---|---|---|---|
| I-100 | 12 | 12 | 1 | 0.0833 |
| I-101 | n/a | NULL | 0 | NULL |
| I-102 | 1,200 | NULL | 2 | NULL |
| I-103 | 8 | 8 | 0 | 0.0 |
| I-104 | 0 | 0 | 0 | NULL |
| I-105 | 5 | 5 | 0 | 0.0 |

Aggregates: SUM 25, COUNT(units) 4, COUNT(*) 6, unparseable 2, AVG 6.25,
AVG(COALESCE(units, 0)) 4.17. Edge cases: `TRY_CAST(' 8 ' AS INT)` = 8 (blanks trimmed),
`TRY_CAST('12.0' AS INT)` = NULL, `TRY_CAST('3000000000' AS INT)` = NULL (overflow),
`TRY_CAST('2026-02-30' AS DATE)` = NULL. `weight_g <> 30.0` counts 4 rows;
`NOT (weight_g <=> 30.0)` counts 5. **Failure cases:** `CAST(raw_units AS INT)` raises
`CAST_INVALID_INPUT`; `SIZE(defect_codes) / TRY_CAST(raw_units AS INT)` for I-104 raises
`DIVIDE_BY_ZERO`. With ANSI off, the strict cast returns NULL for 'n/a' and '1,200' and the
division returns NULL, silently.

## T11–T12 Time

| event | UTC | New York | local hour | local day | UTC day |
|---|---|---|---|---|---|
| e1 | 2026-03-08T04:30Z | 2026-03-07 23:30 −05:00 | 23 | 03-07 | 03-08 |
| e5 | 2026-03-08T06:00Z | 2026-03-08 01:00 −05:00 | 1 | 03-08 | 03-08 |
| e6 | 2026-03-08T08:00Z | 2026-03-08 04:00 −04:00 | 4 | 03-08 | 03-08 |
| e7 | 2026-04-01T03:30Z | 2026-03-31 23:30 −04:00 | 23 | 03-31 | 04-01 |

Downtime pairs (elapsed / wall-clock minutes): M1 30/30 on 03-07, M1 75/75, **M2 120/180**,
M3 40/40 on 03-31. `TIMESTAMPDIFF` and timestamp subtraction read the local clock (M2's
`start_ts - stop_ts` is `INTERVAL '0 03:00:00' DAY TO SECOND`); `UNIX_TIMESTAMP` differences
read the instant (120). The local day 2026-03-08 is 24 wall-clock hours and 23 elapsed hours;
`ts + INTERVAL 1 DAY` lands on 03-08 12:00 −04:00 while `TIMESTAMPADD(HOUR, 24, ts)` lands on
13:00. The local string `2026-03-08 02:30:00` resolves to 03:30 −04:00 as a `TIMESTAMP`; as a
`TIMESTAMP_NTZ` it stays `2026-03-08 02:30:00`.

Autumn change (`fall_back_hour`): the stoppage from 05:30Z to 06:15Z renders as
2026-11-01 01:30 −04:00 → 2026-11-01 01:15 −05:00; 45 elapsed minutes, and `TIMESTAMPDIFF`
reports **−15** because the second reading is earlier on the wall clock. The ambiguous local
string `2026-11-01 01:30:00` resolves to the earlier offset, −04:00. **Wrong approach:**
computing stoppages from local clock readings, which inflates the March stoppage by an hour and
makes the November one negative.

M3's 40 minutes belong to 2026-03 locally and 2026-04 in UTC. Under a UTC session (transfer 3)
the same `downtime_pairs` query reports 120/120 for M2 and moves e1 to 03-08, `events_local`
reports UTC hours (e1 at 4), and the M2 subtraction becomes two hours.

Month ends: `ADD_MONTHS(DATE'2026-01-31', 1)` = 2026-02-28; `ADD_MONTHS(DATE'2026-02-28', 1)` =
2026-03-28 (not a month end); `LAST_DAY(...)` = 2026-03-31; `DATE_ADD(DATE'2026-02-28', 1)` =
2026-03-01; `MONTHS_BETWEEN(DATE'2026-03-31', DATE'2026-02-28')` = 1.0. March 2026 in
`shift_output`: 1080 units over 4 of 31 days, `reaches_month_end = false`.

## T13 Dialect

`DATEDIFF(DATE'2026-03-09', DATE'2026-03-08')` = 1 and the reversed call = −1 (T-SQL lists start
first). `DATE_DIFF(DAY, DATE'2026-03-08', DATE'2026-03-09')` = 1. On the timestamps
2026-03-07 23:30:00 and 2026-03-08 00:00:00 the unit form `DATEDIFF(DAY, start, end)` returns
**0** (whole days, fraction truncated) while the two-argument form returns **1** (both values
cast to dates first); T-SQL's documented `DATEDIFF(day, …)` counts day boundaries crossed, so
the same text copied from T-SQL can change its answer. `DATEADD(DAY, 1, DATE)` returns a
TIMESTAMP. `ISNULL(NULL, 'x')` → `WRONG_NUM_ARGS.WITHOUT_SUGGESTION`; `GETDATE()` →
`UNRESOLVED_ROUTINE`; `TRUNC(12.345, 1)` → `DATATYPE_MISMATCH.UNEXPECTED_INPUT_TYPE`;
`QUALIFY` → `PARSE_SYNTAX_ERROR` in this local Spark build (documented for Databricks SQL, so
verify on the target engine rather than assume either way).
