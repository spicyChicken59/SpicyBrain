<!-- section:dbxfe-analytical-sql-l01-outcome -->

After this lesson you can predict what a window frame includes, rank and deduplicate at a tie, turn consecutive days into islands, ask membership questions with semi and anti joins, combine sets safely, read nested fields, convert text with `TRY_CAST`, and state which time zone and which clock a date, hour or duration depends on. Every result quoted for the Cinderline data was executed in Lab L12 on local Spark 4.0.4.

<!-- section:dbxfe-analytical-sql-l01-start -->

Bring `GROUP BY`, joins and null semantics from [DataFrames, schemas and column expressions](#/lesson/dbxfe-dataframes) and [grain and join cardinality](#/lesson/dbxfe-grain-joins). The examples use the fictional Cinderline plant: machines M1–M5, shift output for 1–4 March 2026, daily status, inspection revisions with nested fields, and stop/start instants around New York's 2026 clock changes. The engine is local Apache Spark 4.0.4, ANSI mode on, `spark.sql.session.timeZone` set explicitly to `America/New_York`; nothing here ran on Databricks.

<!-- section:dbxfe-analytical-sql-l01-frames -->

A window function computes each row from rows chosen by three clauses: `PARTITION BY` picks the group, `ORDER BY` arranges it, and the frame picks which ordered rows count. `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` adds one physical row at a time; for M1 ordered by `day, shift` it reads 50, 90, 145, 190, 190, 240, 300, 330, the NULL shift adding nothing.

Leave the frame out and write only `ORDER BY day`, and Spark uses `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`. RANGE works on the ordering value, so rows sharing a day are peers: both M1 rows for 1 March return 90. The analyzed plan names the frame Spark resolved, `RowFrame` or `RangeFrame`; the lab reads it because a running total over the unique key `day, shift` with no frame clause returns the same eight numbers while being a RangeFrame. RANGE can also take a distance: over rows on 1, 2, 5 and 6 March, `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW` sums 80 on 5 March while `RANGE BETWEEN INTERVAL 2 DAYS PRECEDING AND CURRENT ROW` sums 50, because 3 and 4 March have no rows.

A moving window is incomplete at the start of each partition and `AVG` divides by the non-null count, so report `COUNT(*) OVER w` and `COUNT(units) OVER w` beside it. At a tie, `RANK` shares and then skips (1, 2, 3, 3), `DENSE_RANK` shares without leaving a gap, and `ROW_NUMBER` needs a tie-breaker such as `machine_id`. Deduplication is the same idea: `ROW_NUMBER() OVER (PARTITION BY inspection_id ORDER BY revision DESC, CAST(received_at AS TIMESTAMP) DESC)` keeps row 1, and a `COUNT(*) OVER (PARTITION BY inspection_id, revision)` above 1 flags a revision that two different rows claim. Gaps and islands use one subtraction: `DATE_SUB(day, ROW_NUMBER() OVER (PARTITION BY machine_id, status ORDER BY day))` is constant across consecutive days and changes at a gap.

<!-- section:dbxfe-analytical-sql-l01-membership -->

A semi join asks "does a match exist?" and returns each left row at most once; an anti join keeps the left rows with no match. Neither adds columns or multiplies: joining machines to their DOWN rows returns 8 rows, the semi join returns 2. Write "never inspected" as `NOT EXISTS` or `LEFT ANTI JOIN`. `m.machine_id NOT IN (SELECT i.machine_id FROM inspections i)` returns no rows when the subquery holds one NULL: `x NOT IN (…, NULL)` is unknown for every x, and `WHERE` keeps only true.

Set operators match columns by position, never by name: `SELECT machine_id, plant … UNION ALL SELECT plant, machine_id …` runs without an error and swaps the second branch's values. `UNION`, `INTERSECT` and `EXCEPT` remove duplicates and treat NULLs as one value; `UNION ALL` keeps every row. When branch types differ, ANSI mode casts the text branch to a number and fails with `CAST_INVALID_INPUT`; with ANSI off the same statement silently returned one STRING column mixing numbers and identifiers.

<!-- section:dbxfe-analytical-sql-l01-nested -->

A struct is a column of columns: `measurements.weight_g / measurements.width_mm` is ordinary arithmetic, and a NULL field propagates to NULL. An array needs a decision. `SIZE`, `ARRAY_CONTAINS` and `TRY_ELEMENT_AT(defect_codes, 1)` describe it in place; `ELEMENT_AT` is 1-based while the bracket `defect_codes[0]` is 0-based, and under ANSI both raise past the end of an empty array. `EXPLODE` makes one row per element and drops empty arrays; `LATERAL VIEW OUTER EXPLODE` keeps them as a NULL row.

`TRY_CAST(raw_units AS INT)` returns NULL for `'n/a'` where `CAST` raises `CAST_INVALID_INPUT`; `'1,200'`, `'12.0'` and an INT overflow also become NULL, while `' 8 '` is trimmed to 8. `TRY_DIVIDE` returns NULL for a zero divisor. Then the null rules decide: `SUM`, `AVG` and `COUNT(column)` skip NULL while `COUNT(*)` does not, so `AVG(units)` is 6.25 while `AVG(COALESCE(units, 0))` is 4.17; `weight_g <> 30.0` is unknown for a NULL weight and the row is dropped, while `NOT (weight_g <=> 30.0)` keeps it.

<!-- section:dbxfe-analytical-sql-l01-time -->

A `TIMESTAMP` is an instant. The session time zone decides how it is displayed and which day, hour and month it falls in: 04:30Z is 7 March at hour 23 under `America/New_York` and 8 March at hour 4 under `UTC`. Store instants and set the zone explicitly (for example `SET TIME ZONE`); a naive local string is read in the session zone.

New York jumped from 02:00 EST to 03:00 EDT on 8 March 2026: 24 wall-clock hours, 23 elapsed. `TIMESTAMPDIFF` and timestamp subtraction read the local clock (M2's two-hour stoppage subtracts to `INTERVAL '0 03:00:00' DAY TO SECOND`); a `UNIX_TIMESTAMP` difference reads the instants. On 1 November 2026 the clock goes back: a stop at 01:30 EDT and a start at 01:15 EST are 45 elapsed minutes apart and −15 on the wall clock. The non-existent local string `2026-03-08 02:30:00` became 03:30 −04:00 as a TIMESTAMP but stayed 02:30:00 as a TIMESTAMP_NTZ. `ts + INTERVAL 1 DAY` keeps the wall-clock time; `TIMESTAMPADD(HOUR, 24, ts)` adds elapsed hours. 1 April 03:30Z is still 31 March in New York. `ADD_MONTHS` clamps but does not preserve "month end" (28 February plus one month is 28 March), and a period is complete only when the data reaches `LAST_DAY` of its month.

<!-- section:dbxfe-analytical-sql-l01-worked -->

Both queries are copied from the lab's executed `solutions/portfolio.sql`, with rows as the tests observed them.

~~~sql
SELECT machine_id, day, shift, units,
       ROUND(AVG(units) OVER w, 2) AS avg3,
       COUNT(units)   OVER w AS measured,
       COUNT(*)       OVER w AS rows_in_frame,
       COUNT(*)       OVER w = 3 AS complete
FROM shift_output
WINDOW w AS (PARTITION BY machine_id ORDER BY day, shift
             ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)
ORDER BY machine_id, day, shift
~~~

| machine_id | day | shift | units | avg3 | measured | rows_in_frame | complete |
|---|---|---|---|---|---|---|---|
| M1 | 2026-03-01 | D | 50 | 50.0 | 1 | 1 | false |
| M1 | 2026-03-01 | N | 40 | 45.0 | 2 | 2 | false |
| M1 | 2026-03-02 | D | 55 | 48.33 | 3 | 3 | true |
| M1 | 2026-03-02 | N | 45 | 46.67 | 3 | 3 | true |
| M1 | 2026-03-03 | D | NULL | 50.0 | 2 | 3 | true |

These are M1's first five rows: the NULL row's frame is (55, 45, NULL), two measured values averaging 50.0.

~~~sql
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
~~~

| machine_id | stopped_local | started_local | elapsed | wall clock | local day |
|---|---|---|---|---|---|
| M1 | 2026-03-07 23:30 -05:00 | 2026-03-08 00:00 -05:00 | 30 | 30 | 2026-03-07 |
| M2 | 2026-03-08 01:00 -05:00 | 2026-03-08 04:00 -04:00 | 120 | 180 | 2026-03-08 |
| M3 | 2026-03-31 23:30 -04:00 | 2026-04-01 00:10 -04:00 | 40 | 40 | 2026-03-31 |

M1's second pair (75 and 75) is omitted. Under a UTC session M2 reads 120 and 120, and M1's first stop moves to 8 March.

<!-- section:dbxfe-analytical-sql-l01-task -->

Predict before running. (1) Add the shift row `M4, 2026-03-03, D, 30`: give the new `RANK`, `DENSE_RANK` and `ROW_NUMBER` for all four machines. (2) Add the status row `M1, 2026-03-07, DOWN`: list M1's DOWN islands with lengths and the open flag. (3) A colleague copies `DATEDIFF(day, stop_ts, start_ts)` from a T-SQL report and writes `DATEDIFF(stop_ts, start_ts)` in Spark: what sign does the result carry, and what should be executed to check it?

<!-- section:dbxfe-analytical-sql-l01-solution -->

(1) M4 reaches 330 and ties M1: `RANK` 1, 1, 3, 3 for M1, M4, M2, M3; `DENSE_RANK` 1, 1, 2, 2; `ROW_NUMBER` with the `machine_id` tie-breaker 1, 2, 3, 4; without it nothing decides whether M1 or M4 comes first. (2) The gap closes, so 6–10 March becomes one island of five days that is open at the data end; 2–3 March stays a two-day island. (3) Spark's two-argument `DATEDIFF(end, start)` subtracts the second argument from the first, so every stoppage turns negative; the check is `DATEDIFF(DATE'2026-03-09', DATE'2026-03-08')`, which returns 1, beside its reversed call returning −1. Keeping the unit does not make it equivalent either: Spark parses `DATEDIFF(DAY, start, end)` as its unit form, which counts whole days and returned 0 for 23:30 to midnight, where T-SQL counts one day boundary crossed.

<!-- section:dbxfe-analytical-sql-l01-limits -->

A T-SQL or Oracle expression is not assumed to mean the same thing in Spark SQL; the lab executes counterexamples: `ISNULL(x, y)` fails because Spark's `isnull` takes one argument; `GETDATE()` does not exist; Oracle's numeric `TRUNC(12.345, 1)` is a date function in Spark; `DATEADD` returns a `TIMESTAMP` where T-SQL returns the type of its date argument; and `QUALIFY`, documented for Databricks SQL, is a parse error on this local Spark 4.0.4. Verify each on the target engine with a case whose answer you know.

Other executed traps: equal numbers can hide a missing frame clause; `ROW_NUMBER` without a tie-breaker is not reproducible; `NOT IN` with a NULL returns nothing; a positional `UNION` swaps columns silently; with ANSI off, errors become silent NULLs; a naive `GROUP BY` reports one six-day outage where there were three. Resolving a local time in the spring gap or the repeated autumn hour matches Databricks' Spark 3 description and was re-observed here; verify it, do not design around it.

<!-- section:dbxfe-analytical-sql-l01-sources -->

Spark, Databricks, Microsoft and Oracle documentation was checked at search level on 23 September 2026 (see Sources for context and caveats). The plant and its stakeholders are fiction; the executed outputs come from Lab L12 (51 tests, 0 failures, 0 skips, local Spark 4.0.4, Python 3.12.3, Java 21.0.10) and establish nothing about Databricks execution or performance.

<!-- section:dbxfe-analytical-sql-l01-links -->

The data modeling and metric contracts module defines the grain windows partition by. [SQL analytics and performance diagnosis](#/module/dbxfe-m05) diagnoses where a slow query's time goes: queue, execution and cache. The distributed execution module explains why a window partition is a shuffle boundary.

<!-- section:dbxfe-analytical-sql-l01-revisit -->

Try the checks, then review the cards. Opening a section, revealing a solution or reading a beat records no completion; mark the lesson complete when you choose.
