# Lab L12 — Time-aware analytical SQL, with every answer written down first

*Execution class R (local-executed): the reference portfolio ran on one machine with Apache
Spark 4.0.4 (Spark SQL through PySpark 4.0.4), Python 3.12.3 and Java 21.0.10, `local[2]`, UI
off, two shuffle partitions, ANSI mode at its Spark 4 default and `spark.sql.session.timeZone`
set explicitly to `America/New_York`. Nothing ran on Databricks, and the numbers are mechanism
illustrations, not benchmarks. You can study this page without installing anything; the
package `lab-l12-time-aware-sql` holds the files if you want to run them.*

## Purpose

The Advanced analytical SQL module (C2) claims that windows, membership questions, nested
fields, safe casts and time zones each have one mechanism you can predict row by row. This lab
turns that claim into 51 executed checks. Every expected value was derived before the query ran:
by hand, or for the time zone answers by an independent standard-library `zoneinfo` script that
never touches Spark. Several checks are built to go wrong on purpose, and the test asserts the
reason, not just the failure.

## The fixtures

Five small synthetic files describe the fictional Cinderline plant.

| Fixture | Rows | Deliberate cases |
|---|---|---|
| machines | 5 | M5 appears nowhere else |
| shift_output | 19 | one NULL count, one missing shift, M2 and M3 tied at 225 |
| inspections | 10 | a byte-identical replay, two different rows claiming I-104 revision 1, a NULL machine, raw counts such as `n/a` and `1,200` |
| machine_status | 19 | M1 has no row for 7 March; its last DOWN run touches the last day |
| machine_events | 8 | stops and starts around the 8 March 2026 clock change and the March/April boundary |

## Windows: the frame decides, and the plan shows which frame

The running total per machine, ordered by `day, shift` with
`ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`, reads 50, 90, 145, 190, 190, 240, 300, 330 for
M1; the NULL shift adds nothing. Order by `day` alone with no frame and both 1 March rows read
90: the default frame is `RANGE`, which includes every peer row with the same day.

The subtle case is the starter's running total, which simply omits the frame. Because
`(day, shift)` is unique per machine, it returns the same eight numbers, so a value check passes.
The test therefore also reads the analyzed plan: the reference resolves to `RowFrame`, the
starter to `RangeFrame`. Equal numbers on today's data do not make two queries equal.

The moving average reports its evidence beside the value:

| M1 row | units | avg3 | measured | rows_in_frame | complete |
|---|---|---|---|---|---|
| 03-01 D | 50 | 50.0 | 1 | 1 | false |
| 03-02 N | 45 | 46.67 | 3 | 3 | true |
| 03-03 D | NULL | 50.0 | 2 | 3 | true |

Over four synthetic days (1, 2, 5 and 6 March with 10, 20, 50, 60 units) a three-row frame and a
two-day `RANGE` frame agree until the gap: on 5 March they read 80 and 50, on 6 March 130 and
110. "The last three rows" and "the last three days" are different questions.

## Ranking, deduplication and islands

Totals 330, 300, 225, 225 give `RANK` 1, 2, 3, 3, `DENSE_RANK` 1, 2, 3, 3 and `ROW_NUMBER`
1, 2, 3, 4 once `machine_id` breaks the tie. The latest-revision query goes from 10 rows to 9
with `DISTINCT` and to 6 with `ROW_NUMBER() = 1` over
`revision DESC, CAST(received_at AS TIMESTAMP) DESC`; I-104 keeps its 08:05Z row and carries
`ambiguous_revision = true`. The islands query subtracts a row number from the day:

| M1 DOWN day | 02 | 03 | 06 | 08 | 09 | 10 |
|---|---|---|---|---|---|---|
| row number | 1 | 2 | 3 | 4 | 5 | 6 |
| island key | 03-01 | 03-01 | 03-03 | 03-04 | 03-04 | 03-04 |

Three islands result: 2–3, 6, and 8–10 flagged open at the data end. The naive `GROUP BY` reports
one six-day outage from 2 to 10 March, and a test asserts that this wrong answer is produced.

## Membership, set operators, nested fields and casts

A semi join returns M1 and M2 once each where the inner join returns 8 rows. `NOT EXISTS` and
`LEFT ANTI JOIN` both find M4 and M5 never inspected; `NOT IN` returns nothing because the
subquery holds a NULL. `UNION` gives 4 machines, `UNION ALL` 6, a NULL machine counts once, and
a second branch listing `plant, machine_id` swaps the South rows without an error.

`defect_codes[0]` and `ELEMENT_AT(defect_codes, 1)` both return SCRATCH and DENT: the bracket is
0-based, the function 1-based. `EXPLODE` returns 3 rows, `LATERAL VIEW OUTER EXPLODE` 7.
`TRY_CAST` turns `n/a` and `1,200` into NULL, so SUM is 25, `COUNT(units)` 4, `COUNT(*)` 6 and
`AVG` 6.25, while zero-filling gives 4.17. The edge cases: `' 8 '` becomes 8, while `'12.0'`,
`'3000000000'` and the date `'2026-02-30'` become NULL.

## Time: one instant, two clocks

This query, copied from the executed portfolio, pairs each stop with the next start:

```sql
WITH ordered AS (
  SELECT machine_id, event_type,
         CAST(event_time_utc AS TIMESTAMP) AS at_ts,
         LEAD(event_type) OVER w AS next_type,
         LEAD(CAST(event_time_utc AS TIMESTAMP)) OVER w AS next_ts
  FROM machine_events
  WINDOW w AS (PARTITION BY machine_id ORDER BY CAST(event_time_utc AS TIMESTAMP)))
SELECT machine_id,
       DATE_FORMAT(at_ts,   'yyyy-MM-dd HH:mm XXX') AS stopped_local,
       DATE_FORMAT(next_ts, 'yyyy-MM-dd HH:mm XXX') AS started_local,
       (UNIX_TIMESTAMP(next_ts) - UNIX_TIMESTAMP(at_ts)) DIV 60 AS elapsed_minutes,
       TIMESTAMPDIFF(MINUTE, at_ts, next_ts)                    AS wall_clock_minutes,
       CAST(at_ts AS DATE)                                      AS local_day_of_stop
FROM ordered
WHERE event_type = 'STOP' AND next_type = 'START'
ORDER BY machine_id, at_ts
```

| machine | stopped_local | started_local | elapsed | wall clock | local day |
|---|---|---|---|---|---|
| M1 | 2026-03-07 23:30 -05:00 | 2026-03-08 00:00 -05:00 | 30 | 30 | 2026-03-07 |
| M1 | 2026-03-08 00:30 -05:00 | 2026-03-08 01:45 -05:00 | 75 | 75 | 2026-03-08 |
| M2 | 2026-03-08 01:00 -05:00 | 2026-03-08 04:00 -04:00 | 120 | 180 | 2026-03-08 |
| M3 | 2026-03-31 23:30 -04:00 | 2026-04-01 00:10 -04:00 | 40 | 40 | 2026-03-31 |

M2's stoppage lasted two hours, but the clock skipped 02:00–03:00, so the wall-clock difference
is three; subtracting the two timestamps directly also gives `INTERVAL '0 03:00:00' DAY TO
SECOND`. On the autumn night the effect reverses: a synthetic stoppage from 05:30Z to 06:15Z on
1 November 2026 reads 01:30 −04:00 to 01:15 −05:00, 45 elapsed minutes and −15 on the wall
clock. Local 8 March has 23 elapsed hours; one calendar day after 7 March noon is 12:00 −04:00,
while 24 hours later is 13:00. The local string `2026-03-08 02:30:00` does not exist and becomes
03:30 −04:00 as a `TIMESTAMP`, but stays 02:30:00 as a `TIMESTAMP_NTZ`. M3's 40 minutes belong
to March in New York and April in UTC, and `ADD_MONTHS(DATE'2026-02-28', 1)` is 28 March, not a
month end. March 2026 in `shift_output` is flagged incomplete: 4 of 31 days.

## The failure cases and the dialect checks

Six tests execute nine statements that must fail and assert each error class: a union of an
INT branch with a STRING branch and `CAST(raw_units AS INT)` over `'n/a'` raise `CAST_INVALID_INPUT`; division by
zero raises `DIVIDE_BY_ZERO`; `ELEMENT_AT` and the bracket past an empty array raise
`INVALID_ARRAY_INDEX_IN_ELEMENT_AT` and `INVALID_ARRAY_INDEX`; `ISNULL(NULL, 'x')`, `GETDATE()`,
`TRUNC(12.345, 1)` and `QUALIFY` each raise their own class. `DATEDIFF` shows why a copied
expression is a hypothesis: the two-argument form subtracts its second date from its first (1,
and −1 reversed), the unit form `DATEDIFF(DAY, start, end)` keeps T-SQL's order but returns 0 for
23:30 to midnight because it counts whole days, and the two-argument form on the same two
timestamps returns 1.

## Transfer: altered inputs and altered settings

Adding `M4 2026-03-03 D 30` ties M4 with M1: `RANK` 1, 1, 3, 3 and `DENSE_RANK` 1, 1, 2, 2.
Adding `M1 2026-03-07 DOWN` merges 6–10 March into one five-day open island. After
`SET TIME ZONE 'UTC'` the same queries report 120/120 for M2, move e1 to 8 March and its hour to
4. After `SET spark.sql.ansi.enabled = false` the five statements that raised now succeed
silently: the union returns a STRING column of 24 values, the strict cast and the division
return NULL, and both indexes past an empty array return NULL.

## What the tests prove, and do not

`run_tests.py --evidence` ran 51 tests with 0 failures, 0 errors and 0 skips, hashing every
fixture, expected file, solution, starter and collected output; the evidence file records the
interpreter, Java and package versions and that Spark's temporary directories were deleted. The
tests prove that the reference SQL reproduces the authored literals on the pinned local engine,
that the named wrong approaches produce the wrong numbers, and that the altered inputs and
settings move the answers as predicted. They do not prove Databricks Runtime or Databricks SQL
behaviour (`QUALIFY` is documented there but rejected by this local parser), performance, or
correctness on another data set.

## Setup and cleanup

Create a Python 3.12 virtual environment, install `pyspark==4.0.4` and `py4j==0.10.9.9` from
`requirements.txt`, point `JAVA_HOME` at a JDK 17 or 21 directory and run
`python run_tests.py --evidence local-evidence.json`. To practise, complete
`starters/portfolio.sql` and run `python run_tests.py --portfolio starters/portfolio.sql`: it
runs the 17 tests your file's queries cover, and the unmodified starter passes only the
environment check. The runner places Spark's scratch and warehouse directories in a temporary
folder that it deletes; cleanup is removing the virtual environment and your evidence file.
