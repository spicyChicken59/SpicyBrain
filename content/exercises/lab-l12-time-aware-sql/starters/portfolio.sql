-- Lab L12 starter portfolio. Complete each block, then check it with
--     <python> run_tests.py --portfolio starters/portfolio.sql
-- which runs only the tests whose queries this file defines (the rest of the reference
-- portfolio is used for anything else a test needs). Keep the "-- query: <name>" markers and the
-- output column names exactly as given. The gaps are marked "-- fill in". Views available:
-- machines, shift_output, inspections, machine_status, machine_events, latest_inspections
-- (latest_inspections is built from YOUR latest_inspection block, so T9-T10 depend on T5).

-- query: running_total
SELECT machine_id, day, shift, units,
       SUM(units) OVER (
         PARTITION BY machine_id
         ORDER BY day, shift
         -- fill in: an explicit frame that adds one physical row at a time
       ) AS running_rows
FROM shift_output
ORDER BY machine_id, day, shift

-- query: moving_average
SELECT machine_id, day, shift, units,
       ROUND(AVG(units) OVER w, 2) AS avg3,
       -- fill in: measured = non-NULL units in the frame
       -- fill in: rows_in_frame = every row in the frame
       -- fill in: complete = the frame holds three rows
       NULL AS measured, NULL AS rows_in_frame, NULL AS complete
FROM shift_output
WINDOW w AS (PARTITION BY machine_id ORDER BY day, shift
             ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)
ORDER BY machine_id, day, shift

-- query: range_versus_rows
-- fill in: last_three_days must use a RANGE frame reaching two calendar days back,
-- not the ROWS frame copied here
SELECT day, units,
       SUM(units) OVER (ORDER BY day ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS last_three_rows,
       SUM(units) OVER (ORDER BY day ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS last_three_days
FROM VALUES (DATE'2026-03-01', 10), (DATE'2026-03-02', 20),
            (DATE'2026-03-05', 50), (DATE'2026-03-06', 60) AS daily(day, units)
ORDER BY day

-- query: ranking
WITH totals AS (
  SELECT machine_id, SUM(units) AS total_units FROM shift_output GROUP BY machine_id)
SELECT machine_id, total_units,
       -- fill in: rnk, dense_rnk and a deterministic row_num
       NULL AS rnk, NULL AS dense_rnk, NULL AS row_num
FROM totals
ORDER BY row_num

-- query: latest_inspection
-- fill in: remove byte-identical replays, then keep the highest revision per
-- inspection_id with the latest received_at as tie-breaker, and flag an
-- inspection whose top revision is shared by more than one distinct row.
SELECT * FROM inspections

-- query: down_islands
-- fill in: consecutive DOWN days per machine become one island; a missing day
-- splits an island; an island touching the last observed day is open.
SELECT machine_id, MIN(day) AS island_start, MAX(day) AS island_end,
       COUNT(*) AS days_down, FALSE AS open_at_data_end
FROM machine_status WHERE status = 'DOWN'
GROUP BY machine_id

-- query: semi_down_machines
-- fill in: keep each machine that has at least one DOWN day exactly once; this inner join
-- repeats M1 once per DOWN row
SELECT m.machine_id, m.plant
FROM machines m
JOIN machine_status s ON s.machine_id = m.machine_id AND s.status = 'DOWN'
ORDER BY m.machine_id

-- query: never_inspected_not_exists
-- fill in: machines with no inspection row, written so that a NULL machine_id
-- in inspections cannot empty the answer.
SELECT machine_id FROM machines

-- query: explode_counts
-- fill in: explode_outer_rows must keep the inspections whose defect_codes array is empty
SELECT (SELECT COUNT(*) FROM latest_inspections LATERAL VIEW EXPLODE(defect_codes) c AS code) AS explode_rows,
       (SELECT COUNT(*) FROM latest_inspections LATERAL VIEW EXPLODE(defect_codes) c AS code) AS explode_outer_rows

-- query: try_cast_aggregates
-- fill in: measured and unparseable must count converted and unconverted values, and the
-- zero-filled average must treat a NULL as 0
WITH typed AS (
  SELECT TRY_CAST(raw_units AS INT) AS units FROM latest_inspections)
SELECT SUM(units)           AS sum_units,
       COUNT(*)             AS measured,
       COUNT(*)             AS rows,
       0                    AS unparseable,
       AVG(units)           AS avg_units,
       ROUND(AVG(units), 2) AS avg_with_zero_fill
FROM typed

-- query: downtime_pairs
-- fill in: pair each STOP with the next START per machine (LEAD), then report
-- elapsed minutes (from unix_timestamp) beside wall-clock minutes (timestampdiff)
-- and the local day of the stop.
SELECT machine_id FROM machine_events

-- query: fall_back_hour
-- fill in: elapsed minutes from the two instants and wall-clock minutes from the local clock
WITH pair AS (
  SELECT CAST('2026-11-01T05:30:00Z' AS TIMESTAMP) AS stop_ts,
         CAST('2026-11-01T06:15:00Z' AS TIMESTAMP) AS start_ts)
SELECT DATE_FORMAT(stop_ts,  'yyyy-MM-dd HH:mm XXX') AS stopped_local,
       DATE_FORMAT(start_ts, 'yyyy-MM-dd HH:mm XXX') AS started_local,
       NULL                                          AS elapsed_minutes,
       NULL                                          AS wall_clock_minutes,
       DATE_FORMAT(CAST('2026-11-01 01:30:00' AS TIMESTAMP), 'yyyy-MM-dd HH:mm XXX') AS repeated_string_resolved
FROM pair

-- query: incomplete_period
-- fill in: per month, total units, distinct days observed, days in the month
-- and whether the data reaches the month end.
SELECT DATE_FORMAT(day, 'yyyy-MM') AS month, SUM(units) AS units
FROM shift_output GROUP BY 1

-- query: dialect_datediff
-- fill in: the reversed call; DATE_DIFF(DAY, start, end) on the two dates; DATEDIFF(DAY, start, end)
-- on TIMESTAMP'2026-03-07 23:30:00' and TIMESTAMP'2026-03-08 00:00:00'; and the two-argument
-- DATEDIFF(end, start) on the same two timestamps. Predict each value first (TASKS.md T13).
SELECT DATEDIFF(DATE'2026-03-09', DATE'2026-03-08') AS spark_end_minus_start,
       NULL AS reversed,
       NULL AS unit_form,
       NULL AS unit_form_on_timestamps,
       NULL AS two_arg_on_timestamps
