-- Lab L12 query portfolio. Executed by run_tests.py through solutions/portfolio.py on local
-- Apache Spark 4.0.4 (Spark SQL, ANSI mode on by default, session time zone America/New_York).
-- Each block starts with "-- query: <name>" and is run as one statement.
-- Views: machines, shift_output, inspections, machine_status, machine_events,
-- and latest_inspections (created from the latest_inspection query below).
-- Blocks marked "expected to fail" are executed by the tests, which assert the error class.

-- query: running_total
SELECT machine_id, day, shift, units,
       SUM(units) OVER (
         PARTITION BY machine_id
         ORDER BY day, shift
         ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_rows
FROM shift_output
ORDER BY machine_id, day, shift

-- query: running_total_default_frame
SELECT machine_id, day, shift, units,
       SUM(units) OVER (PARTITION BY machine_id ORDER BY day) AS running_range
FROM shift_output
ORDER BY machine_id, day, shift

-- query: moving_average
SELECT machine_id, day, shift, units,
       ROUND(AVG(units) OVER w, 2) AS avg3,
       COUNT(units)   OVER w AS measured,
       COUNT(*)       OVER w AS rows_in_frame,
       COUNT(*)       OVER w = 3 AS complete
FROM shift_output
WINDOW w AS (PARTITION BY machine_id ORDER BY day, shift
             ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)
ORDER BY machine_id, day, shift

-- query: range_versus_rows
SELECT day, units,
       SUM(units) OVER (ORDER BY day ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)                AS last_three_rows,
       SUM(units) OVER (ORDER BY day RANGE BETWEEN INTERVAL 2 DAYS PRECEDING AND CURRENT ROW) AS last_three_days
FROM VALUES (DATE'2026-03-01', 10), (DATE'2026-03-02', 20),
            (DATE'2026-03-05', 50), (DATE'2026-03-06', 60) AS daily(day, units)
ORDER BY day

-- query: ranking
WITH totals AS (
  SELECT machine_id, SUM(units) AS total_units
  FROM shift_output
  GROUP BY machine_id)
SELECT machine_id, total_units,
       RANK()       OVER (ORDER BY total_units DESC)             AS rnk,
       DENSE_RANK() OVER (ORDER BY total_units DESC)             AS dense_rnk,
       ROW_NUMBER() OVER (ORDER BY total_units DESC, machine_id) AS row_num
FROM totals
ORDER BY row_num

-- query: top_per_plant
WITH totals AS (
  SELECT m.plant, m.machine_id, SUM(o.units) AS total_units
  FROM machines m
  JOIN shift_output o ON o.machine_id = m.machine_id
  GROUP BY m.plant, m.machine_id),
numbered AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY plant
                               ORDER BY total_units DESC, machine_id) AS rn
  FROM totals)
SELECT plant, machine_id, total_units
FROM numbered
WHERE rn = 1
ORDER BY plant

-- query: latest_inspection
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

-- query: latest_inspection_summary
SELECT inspection_id, revision, received_at, machine_id, result, ambiguous_revision
FROM latest_inspections
ORDER BY inspection_id

-- query: dedup_counts
SELECT (SELECT COUNT(*) FROM inspections)                        AS raw_rows,
       (SELECT COUNT(*) FROM (SELECT DISTINCT * FROM inspections)) AS distinct_rows,
       (SELECT COUNT(*) FROM latest_inspections)                 AS latest_rows

-- query: down_islands
WITH keyed AS (
  SELECT machine_id, day, status,
         DATE_SUB(day, ROW_NUMBER() OVER (PARTITION BY machine_id, status
                                          ORDER BY day)) AS island_key
  FROM machine_status),
last_seen AS (
  SELECT MAX(day) AS last_observed_day FROM machine_status)
SELECT k.machine_id,
       MIN(k.day) AS island_start,
       MAX(k.day) AS island_end,
       COUNT(*)   AS days_down,
       MAX(k.day) = MAX(l.last_observed_day) AS open_at_data_end
FROM keyed k CROSS JOIN last_seen l
WHERE k.status = 'DOWN'
GROUP BY k.machine_id, k.island_key
ORDER BY k.machine_id, island_start

-- query: down_islands_naive
SELECT machine_id, MIN(day) AS first_down, MAX(day) AS last_down, COUNT(*) AS days_down
FROM machine_status
WHERE status = 'DOWN'
GROUP BY machine_id
ORDER BY machine_id

-- query: semi_down_machines
SELECT m.machine_id, m.plant
FROM machines m
LEFT SEMI JOIN machine_status s
  ON s.machine_id = m.machine_id AND s.status = 'DOWN'
ORDER BY m.machine_id

-- query: anti_no_output
SELECT m.machine_id, m.plant
FROM machines m
LEFT ANTI JOIN shift_output o ON o.machine_id = m.machine_id
ORDER BY m.machine_id

-- query: never_inspected_not_exists
SELECT m.machine_id
FROM machines m
WHERE NOT EXISTS (SELECT 1 FROM inspections i WHERE i.machine_id = m.machine_id)
ORDER BY m.machine_id

-- query: never_inspected_anti_join
SELECT m.machine_id
FROM machines m
LEFT ANTI JOIN inspections i ON i.machine_id = m.machine_id
ORDER BY m.machine_id

-- query: never_inspected_not_in
SELECT m.machine_id
FROM machines m
WHERE m.machine_id NOT IN (SELECT i.machine_id FROM inspections i)
ORDER BY m.machine_id

-- query: join_cardinality
SELECT (SELECT COUNT(*) FROM machines m
        JOIN machine_status s ON s.machine_id = m.machine_id AND s.status = 'DOWN') AS inner_join_rows,
       (SELECT COUNT(*) FROM machines m
        LEFT SEMI JOIN machine_status s ON s.machine_id = m.machine_id AND s.status = 'DOWN') AS semi_join_rows

-- query: setops_union
SELECT DISTINCT machine_id FROM shift_output
UNION
SELECT DISTINCT machine_id FROM machine_status
ORDER BY machine_id

-- query: setops_union_all
SELECT DISTINCT machine_id FROM shift_output
UNION ALL
SELECT DISTINCT machine_id FROM machine_status

-- query: setops_intersect
SELECT DISTINCT machine_id FROM shift_output
INTERSECT
SELECT DISTINCT machine_id FROM machine_status
ORDER BY machine_id

-- query: setops_except
SELECT machine_id FROM machines
EXCEPT
SELECT DISTINCT machine_id FROM shift_output
ORDER BY machine_id

-- query: setops_null_union
SELECT DISTINCT machine_id FROM inspections
UNION
SELECT DISTINCT machine_id FROM machine_status
ORDER BY machine_id NULLS FIRST

-- query: setops_null_except
SELECT DISTINCT machine_id FROM inspections
EXCEPT
SELECT machine_id FROM machines

-- query: setops_null_intersect
SELECT DISTINCT machine_id FROM inspections
INTERSECT
SELECT machine_id FROM machines
ORDER BY machine_id

-- query: setops_positional
SELECT machine_id, plant FROM machines WHERE plant = 'North'
UNION ALL
SELECT plant, machine_id FROM machines WHERE plant = 'South'

-- query: union_int_and_text
-- expected to fail under ANSI mode: CAST_INVALID_INPUT (the text branch is cast to a number);
-- with ANSI mode off the same statement returns a STRING column.
SELECT units FROM shift_output
UNION ALL
SELECT machine_id FROM machines

-- query: struct_fields
SELECT inspection_id,
       measurements.width_mm,
       measurements.weight_g,
       ROUND(measurements.weight_g / measurements.width_mm, 3) AS grams_per_mm
FROM latest_inspections
ORDER BY inspection_id

-- query: array_fields
SELECT inspection_id,
       SIZE(defect_codes)                    AS defect_count,
       ARRAY_CONTAINS(defect_codes, 'SCRATCH') AS has_scratch,
       TRY_ELEMENT_AT(defect_codes, 1)       AS first_code
FROM latest_inspections
ORDER BY inspection_id

-- query: zero_based_index
SELECT inspection_id,
       defect_codes[0]             AS first_by_bracket,
       ELEMENT_AT(defect_codes, 1) AS first_by_element_at
FROM latest_inspections
WHERE SIZE(defect_codes) > 0
ORDER BY inspection_id

-- query: element_at_all_rows
-- expected to fail under ANSI mode: INVALID_ARRAY_INDEX_IN_ELEMENT_AT (empty arrays)
SELECT inspection_id, ELEMENT_AT(defect_codes, 1) AS first_code
FROM latest_inspections
ORDER BY inspection_id

-- query: bracket_all_rows
-- expected to fail under ANSI mode: INVALID_ARRAY_INDEX (empty arrays)
SELECT inspection_id, defect_codes[0] AS first_by_bracket
FROM latest_inspections
ORDER BY inspection_id

-- query: defect_code_counts
SELECT code, COUNT(*) AS occurrences
FROM latest_inspections
LATERAL VIEW EXPLODE(defect_codes) codes AS code
GROUP BY code
ORDER BY code

-- query: explode_counts
SELECT (SELECT COUNT(*) FROM latest_inspections LATERAL VIEW EXPLODE(defect_codes) c AS code)       AS explode_rows,
       (SELECT COUNT(*) FROM latest_inspections LATERAL VIEW OUTER EXPLODE(defect_codes) c AS code) AS explode_outer_rows

-- query: try_cast_rows
SELECT inspection_id, raw_units,
       TRY_CAST(raw_units AS INT) AS units,
       SIZE(defect_codes)         AS defect_count,
       ROUND(TRY_DIVIDE(SIZE(defect_codes), TRY_CAST(raw_units AS INT)), 4) AS defects_per_unit
FROM latest_inspections
ORDER BY inspection_id

-- query: try_cast_aggregates
WITH typed AS (
  SELECT TRY_CAST(raw_units AS INT) AS units FROM latest_inspections)
SELECT SUM(units)                       AS sum_units,
       COUNT(units)                     AS measured,
       COUNT(*)                         AS rows,
       COUNT(*) - COUNT(units)          AS unparseable,
       AVG(units)                       AS avg_units,
       ROUND(AVG(COALESCE(units, 0)), 2) AS avg_with_zero_fill
FROM typed

-- query: try_cast_edge_cases
SELECT TRY_CAST(' 8 ' AS INT)         AS padded,
       TRY_CAST('12.0' AS INT)        AS decimal_text,
       TRY_CAST('3000000000' AS INT)  AS too_large,
       TRY_CAST('2026-02-30' AS DATE) AS impossible_date

-- query: strict_cast_units
-- expected to fail under ANSI mode: CAST_INVALID_INPUT ('n/a');
-- with ANSI mode off the same statement returns NULL for the unparseable values.
SELECT inspection_id, raw_units, CAST(raw_units AS INT) AS units
FROM latest_inspections
ORDER BY inspection_id

-- query: plain_division
-- expected to fail under ANSI mode: DIVIDE_BY_ZERO (I-104 has 0 units)
SELECT inspection_id, SIZE(defect_codes) / TRY_CAST(raw_units AS INT) AS defects_per_unit
FROM latest_inspections
WHERE inspection_id = 'I-104'

-- query: null_comparisons
SELECT COUNT(*) FILTER (WHERE measurements.weight_g <> 30.0)        AS not_equal_30,
       COUNT(*) FILTER (WHERE NOT (measurements.weight_g <=> 30.0)) AS not_null_safe_equal_30
FROM latest_inspections

-- query: events_local
SELECT event_id, machine_id, event_type, event_time_utc,
       DATE_FORMAT(CAST(event_time_utc AS TIMESTAMP), 'yyyy-MM-dd HH:mm XXX') AS local_wall_clock,
       HOUR(CAST(event_time_utc AS TIMESTAMP))                                AS local_hour,
       CAST(CAST(event_time_utc AS TIMESTAMP) AS DATE)                        AS local_day,
       LEFT(event_time_utc, 10)                                               AS utc_day
FROM machine_events
ORDER BY event_id

-- query: downtime_pairs
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

-- query: interval_subtraction
WITH m2 AS (
  SELECT CAST(MAX(CASE WHEN event_type = 'STOP'  THEN event_time_utc END) AS TIMESTAMP) AS stop_ts,
         CAST(MAX(CASE WHEN event_type = 'START' THEN event_time_utc END) AS TIMESTAMP) AS start_ts
  FROM machine_events
  WHERE machine_id = 'M2')
SELECT CAST(start_ts - stop_ts AS STRING)                          AS subtracted,
       TIMESTAMPDIFF(MINUTE, stop_ts, start_ts)                    AS wall_clock_minutes,
       (UNIX_TIMESTAMP(start_ts) - UNIX_TIMESTAMP(stop_ts)) DIV 60 AS elapsed_minutes
FROM m2

-- query: dst_day_hours
SELECT d AS local_day,
       TIMESTAMPDIFF(HOUR, CAST(d AS TIMESTAMP), CAST(d AS TIMESTAMP) + INTERVAL 1 DAY) AS wall_clock_hours,
       (UNIX_TIMESTAMP(CAST(d AS TIMESTAMP) + INTERVAL 1 DAY)
        - UNIX_TIMESTAMP(CAST(d AS TIMESTAMP))) DIV 3600                            AS elapsed_hours
FROM VALUES (DATE'2026-03-07'), (DATE'2026-03-08'), (DATE'2026-03-09') AS local_days(d)
ORDER BY d

-- query: day_versus_24_hours
SELECT DATE_FORMAT(ts, 'yyyy-MM-dd HH:mm XXX')                          AS start,
       DATE_FORMAT(ts + INTERVAL 1 DAY, 'yyyy-MM-dd HH:mm XXX')         AS one_day_later,
       DATE_FORMAT(TIMESTAMPADD(HOUR, 24, ts), 'yyyy-MM-dd HH:mm XXX')  AS twenty_four_hours_later
FROM (SELECT TIMESTAMP'2026-03-07 12:00:00' AS ts)

-- query: nonexistent_local_time
SELECT DATE_FORMAT(CAST('2026-03-08 02:30:00' AS TIMESTAMP), 'yyyy-MM-dd HH:mm XXX') AS resolved,
       CAST(CAST('2026-03-08 02:30:00' AS TIMESTAMP_NTZ) AS STRING)                  AS ntz_reading

-- query: fall_back_hour
WITH pair AS (
  SELECT CAST('2026-11-01T05:30:00Z' AS TIMESTAMP) AS stop_ts,
         CAST('2026-11-01T06:15:00Z' AS TIMESTAMP) AS start_ts)
SELECT DATE_FORMAT(stop_ts,  'yyyy-MM-dd HH:mm XXX')               AS stopped_local,
       DATE_FORMAT(start_ts, 'yyyy-MM-dd HH:mm XXX')               AS started_local,
       (UNIX_TIMESTAMP(start_ts) - UNIX_TIMESTAMP(stop_ts)) DIV 60 AS elapsed_minutes,
       TIMESTAMPDIFF(MINUTE, stop_ts, start_ts)                    AS wall_clock_minutes,
       DATE_FORMAT(CAST('2026-11-01 01:30:00' AS TIMESTAMP), 'yyyy-MM-dd HH:mm XXX') AS repeated_string_resolved
FROM pair

-- query: month_attribution
WITH pairs AS (
  SELECT machine_id, event_type,
         CAST(event_time_utc AS TIMESTAMP) AS at_ts,
         event_time_utc,
         LEAD(event_type) OVER w AS next_type,
         LEAD(CAST(event_time_utc AS TIMESTAMP)) OVER w AS next_ts
  FROM machine_events
  WINDOW w AS (PARTITION BY machine_id ORDER BY CAST(event_time_utc AS TIMESTAMP)))
SELECT machine_id,
       DATE_FORMAT(at_ts, 'yyyy-MM')                                     AS local_month,
       LEFT(event_time_utc, 7)                                           AS utc_month,
       SUM((UNIX_TIMESTAMP(next_ts) - UNIX_TIMESTAMP(at_ts)) DIV 60)     AS downtime_minutes
FROM pairs
WHERE machine_id = 'M3' AND event_type = 'STOP' AND next_type = 'START'
GROUP BY machine_id, local_month, utc_month

-- query: month_end_arithmetic
SELECT ADD_MONTHS(DATE'2026-01-31', 1)            AS jan31_plus_month,
       ADD_MONTHS(DATE'2026-02-28', 1)            AS feb28_plus_month,
       LAST_DAY(ADD_MONTHS(DATE'2026-02-28', 1))  AS feb28_plus_month_end,
       DATE_ADD(DATE'2026-02-28', 1)              AS feb28_plus_day,
       DATEDIFF(DATE'2026-03-01', DATE'2026-02-28') AS datediff_mar1_feb28,
       MONTHS_BETWEEN(DATE'2026-03-31', DATE'2026-02-28') AS months_between_mar31_feb28

-- query: incomplete_period
SELECT DATE_FORMAT(day, 'yyyy-MM')          AS month,
       SUM(units)                           AS units,
       COUNT(DISTINCT day)                  AS days_observed,
       DAYOFMONTH(LAST_DAY(MIN(day)))       AS days_in_month,
       MAX(day) = LAST_DAY(MAX(day))        AS reaches_month_end
FROM shift_output
GROUP BY DATE_FORMAT(day, 'yyyy-MM')
ORDER BY month

-- query: dialect_datediff
SELECT DATEDIFF(DATE'2026-03-09', DATE'2026-03-08')      AS spark_end_minus_start,
       DATEDIFF(DATE'2026-03-08', DATE'2026-03-09')      AS reversed,
       DATE_DIFF(DAY, DATE'2026-03-08', DATE'2026-03-09') AS unit_form,
       DATEDIFF(DAY, TIMESTAMP'2026-03-07 23:30:00', TIMESTAMP'2026-03-08 00:00:00') AS unit_form_on_timestamps,
       DATEDIFF(TIMESTAMP'2026-03-08 00:00:00', TIMESTAMP'2026-03-07 23:30:00')      AS two_arg_on_timestamps

-- query: dialect_dateadd
SELECT DATEADD(DAY, 1, DATE'2026-03-08') AS next_day

-- query: dialect_isnull
-- expected to fail: WRONG_NUM_ARGS.WITHOUT_SUGGESTION (Spark's isnull takes one argument)
SELECT ISNULL(NULL, 'x')

-- query: dialect_getdate
-- expected to fail: UNRESOLVED_ROUTINE (no such function in Spark SQL)
SELECT GETDATE()

-- query: dialect_trunc_number
-- expected to fail: DATATYPE_MISMATCH.UNEXPECTED_INPUT_TYPE (Spark's trunc truncates dates)
SELECT TRUNC(12.345, 1)

-- query: dialect_qualify
-- expected to fail on this local build: PARSE_SYNTAX_ERROR (QUALIFY is documented for Databricks SQL)
SELECT machine_id, units FROM shift_output QUALIFY ROW_NUMBER() OVER (ORDER BY units DESC) = 1
