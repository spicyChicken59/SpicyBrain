-- Lab L11 reference model: a small star for Cinderline inspections (fictional)
-- and one metric, unit_defect_rate, at three grains. Spark SQL 4.0.4.
--
-- Views registered by solutions/model.py before these statements run:
--   silver_inspections  one row per accepted inspection (natural keys, source units)
--   dim_line            type 2 on supervisor: line_sk surrogate key, valid_from
--                       inclusive, valid_to exclusive (NULL = open), unknown member -1
--   dim_plant, dim_shift, dim_date (plant calendar), unit_conversion
-- Named parameters (from fixtures/metric_contract.json and fixtures/*/run.json):
--   :period_start :period_end :as_of :window_days :unknown_line_sk
--   :unknown_plant_id :zero_status :empty_status
-- Each statement starts with a "-- name:" line; model.py splits on it.

-- name: silver_dated
-- The contract's business day: 00:00:00-23:59:59 plant local time by the
-- recorded inspection time. inspected_at is TIMESTAMP_NTZ plant wall clock.
SELECT i.*, CAST(i.inspected_at AS DATE) AS business_date
FROM silver_inspections i

-- name: check_duplicate_inspection_ids
SELECT inspection_id
FROM silver_inspections
GROUP BY inspection_id
HAVING COUNT(*) > 1
ORDER BY inspection_id

-- name: check_overlapping_versions
SELECT DISTINCT a.line_id
FROM dim_line a
JOIN dim_line b
  ON a.line_id = b.line_id
 AND a.line_sk < b.line_sk
 AND a.valid_from < COALESCE(b.valid_to, DATE'9999-12-31')
 AND b.valid_from < COALESCE(a.valid_to, DATE'9999-12-31')
ORDER BY a.line_id

-- name: check_current_rows
SELECT line_id
FROM dim_line
GROUP BY line_id
HAVING SUM(CASE WHEN is_current THEN 1 ELSE 0 END) <> 1
ORDER BY line_id

-- name: check_duplicate_surrogate_keys
SELECT line_sk
FROM dim_line
GROUP BY line_sk
HAVING COUNT(*) > 1
ORDER BY line_sk

-- name: orphans_line
SELECT s.inspection_id
FROM silver_dated s
LEFT ANTI JOIN dim_line l
  ON l.line_id = s.line_id
 AND s.business_date >= l.valid_from
 AND (l.valid_to IS NULL OR s.business_date < l.valid_to)
ORDER BY s.inspection_id

-- name: orphans_shift
SELECT s.inspection_id
FROM silver_dated s
LEFT ANTI JOIN dim_shift d ON d.shift_id = s.shift_id
ORDER BY s.inspection_id

-- name: orphans_date
SELECT s.inspection_id
FROM silver_dated s
LEFT ANTI JOIN dim_date d ON d.date = s.business_date
ORDER BY s.inspection_id

-- name: quarantine
-- A unit with no conversion cannot be expressed in pieces: it leaves BOTH the
-- numerator and the denominator and is listed, never summed.
SELECT s.inspection_id, s.line_id, s.uom, s.inspected_qty, s.defective_qty,
       'no_unit_conversion' AS reason
FROM silver_dated s
LEFT ANTI JOIN unit_conversion u ON u.uom = s.uom
ORDER BY s.inspection_id

-- name: fact_inspection
-- The gold fact at its declared grain: one row per accepted inspection. The
-- line version valid on the business day is resolved ONCE, here, into line_sk
-- (point-in-time), so every later join to dim_line is many-to-one. A line with
-- no valid version maps to the unknown member instead of disappearing.
WITH resolved AS (
  SELECT s.*, l.line_sk
  FROM silver_dated s
  LEFT JOIN dim_line l
    ON l.line_id = s.line_id
   AND s.business_date >= l.valid_from
   AND (l.valid_to IS NULL OR s.business_date < l.valid_to)
)
SELECT r.inspection_id,
       COALESCE(r.line_sk, :unknown_line_sk) AS line_sk,
       r.line_id AS source_line_id,
       r.shift_id,
       r.inspected_at,
       r.business_date,
       r.inspected_qty * u.pieces_per_uom AS inspected_pieces,
       r.defective_qty * u.pieces_per_uom AS defective_pieces,
       r.uom AS source_uom
FROM resolved r
JOIN unit_conversion u ON u.uom = r.uom

-- name: fact_duplicates
SELECT inspection_id
FROM fact_inspection
GROUP BY inspection_id
HAVING COUNT(*) > 1
ORDER BY inspection_id

-- name: fact_totals
SELECT COUNT(*) AS rows,
       SUM(inspected_pieces) AS inspected_pieces,
       SUM(defective_pieces) AS defective_pieces
FROM fact_inspection

-- name: line_day
-- Grid = every line version valid on every business day of the period (so a
-- silent line is visible as no_inspections) UNION every observed line-day (so
-- no fact can fall outside the grid). Sum the additive parts, then divide.
WITH days AS (
  SELECT date AS business_date
  FROM dim_date
  WHERE is_business_day AND date BETWEEN :period_start AND :period_end
),
facts AS (
  SELECT line_sk, business_date, COUNT(*) AS inspections,
         SUM(inspected_pieces) AS inspected_pieces,
         SUM(defective_pieces) AS defective_pieces
  FROM fact_inspection
  WHERE business_date BETWEEN :period_start AND :period_end
  GROUP BY line_sk, business_date
),
grid AS (
  SELECT l.line_sk, d.business_date
  FROM dim_line l
  JOIN days d
    ON d.business_date >= l.valid_from
   AND (l.valid_to IS NULL OR d.business_date < l.valid_to)
  WHERE l.line_sk <> :unknown_line_sk
  UNION
  SELECT line_sk, business_date FROM facts
)
SELECT g.business_date, l.line_id, l.plant_id, l.supervisor,
       COALESCE(f.inspections, 0) AS inspections,
       COALESCE(f.inspected_pieces, 0) AS inspected_pieces,
       COALESCE(f.defective_pieces, 0) AS defective_pieces,
       CASE WHEN f.inspections IS NULL THEN :empty_status
            WHEN f.inspected_pieces = 0 THEN :zero_status
            ELSE 'ok' END AS status,
       try_divide(CAST(COALESCE(f.defective_pieces, 0) AS DOUBLE),
                  COALESCE(f.inspected_pieces, 0)) AS rate
FROM grid g
JOIN dim_line l ON l.line_sk = g.line_sk
LEFT JOIN facts f ON f.line_sk = g.line_sk AND f.business_date = g.business_date
ORDER BY g.business_date, l.line_id

-- name: plant_day
-- The same calculation over all of a plant's lines: recomputed from summed
-- parts, never an average of line rates.
WITH days AS (
  SELECT date AS business_date
  FROM dim_date
  WHERE is_business_day AND date BETWEEN :period_start AND :period_end
),
facts AS (
  SELECT l.plant_id, f.business_date, COUNT(*) AS inspections,
         SUM(f.inspected_pieces) AS inspected_pieces,
         SUM(f.defective_pieces) AS defective_pieces
  FROM fact_inspection f
  JOIN dim_line l ON l.line_sk = f.line_sk
  WHERE f.business_date BETWEEN :period_start AND :period_end
  GROUP BY l.plant_id, f.business_date
),
grid AS (
  SELECT p.plant_id, d.business_date
  FROM dim_plant p CROSS JOIN days d
  WHERE p.plant_id <> :unknown_plant_id
  UNION
  SELECT plant_id, business_date FROM facts
)
SELECT g.business_date, g.plant_id,
       COALESCE(f.inspections, 0) AS inspections,
       COALESCE(f.inspected_pieces, 0) AS inspected_pieces,
       COALESCE(f.defective_pieces, 0) AS defective_pieces,
       CASE WHEN f.inspections IS NULL THEN :empty_status
            WHEN f.inspected_pieces = 0 THEN :zero_status
            ELSE 'ok' END AS status,
       try_divide(CAST(COALESCE(f.defective_pieces, 0) AS DOUBLE),
                  COALESCE(f.inspected_pieces, 0)) AS rate
FROM grid g
LEFT JOIN facts f ON f.plant_id = g.plant_id AND f.business_date = g.business_date
ORDER BY g.business_date, g.plant_id

-- name: plant_month
WITH months AS (
  SELECT DISTINCT date_format(date, 'yyyy-MM') AS month
  FROM dim_date
  WHERE is_business_day AND date BETWEEN :period_start AND :period_end
),
facts AS (
  SELECT l.plant_id, date_format(f.business_date, 'yyyy-MM') AS month,
         COUNT(*) AS inspections,
         SUM(f.inspected_pieces) AS inspected_pieces,
         SUM(f.defective_pieces) AS defective_pieces
  FROM fact_inspection f
  JOIN dim_line l ON l.line_sk = f.line_sk
  WHERE f.business_date BETWEEN :period_start AND :period_end
  GROUP BY l.plant_id, date_format(f.business_date, 'yyyy-MM')
),
grid AS (
  SELECT p.plant_id, m.month
  FROM dim_plant p CROSS JOIN months m
  WHERE p.plant_id <> :unknown_plant_id
  UNION
  SELECT plant_id, month FROM facts
)
SELECT g.month, g.plant_id,
       COALESCE(f.inspections, 0) AS inspections,
       COALESCE(f.inspected_pieces, 0) AS inspected_pieces,
       COALESCE(f.defective_pieces, 0) AS defective_pieces,
       CASE WHEN f.inspections IS NULL THEN :empty_status
            WHEN f.inspected_pieces = 0 THEN :zero_status
            ELSE 'ok' END AS status,
       try_divide(CAST(COALESCE(f.defective_pieces, 0) AS DOUBLE),
                  COALESCE(f.inspected_pieces, 0)) AS rate
FROM grid g
LEFT JOIN facts f ON f.plant_id = g.plant_id AND f.month = g.month
ORDER BY g.month, g.plant_id

-- name: average_of_line_rates
-- A DIFFERENT metric, kept only to show that rates do not add. AVG skips NULL.
SELECT plant_id, business_date,
       AVG(rate) AS average_of_line_rates,
       COUNT(rate) AS rated_lines
FROM report_line_day
GROUP BY plant_id, business_date
ORDER BY business_date, plant_id

-- name: average_of_day_rates
SELECT plant_id, date_format(business_date, 'yyyy-MM') AS month,
       AVG(rate) AS average_of_day_rates,
       COUNT(rate) AS rated_days
FROM report_plant_day
GROUP BY plant_id, date_format(business_date, 'yyyy-MM')
ORDER BY month, plant_id

-- name: naive_division_line_day
-- Deliberately wrong: plain division. Under ANSI mode (the Spark 4 default) a
-- line-day whose inspected pieces sum to 0 raises DIVIDE_BY_ZERO.
SELECT l.line_id, f.business_date,
       SUM(f.defective_pieces) / SUM(f.inspected_pieces) AS rate
FROM fact_inspection f
JOIN dim_line l ON l.line_sk = f.line_sk
GROUP BY l.line_id, f.business_date

-- name: naive_units_plant_day
-- Deliberately wrong: source quantities summed as if every uom were a piece.
SELECT COALESCE(l.plant_id, :unknown_plant_id) AS plant_id, s.business_date,
       SUM(s.inspected_qty) AS inspected_qty,
       SUM(s.defective_qty) AS defective_qty,
       try_divide(CAST(SUM(s.defective_qty) AS DOUBLE), SUM(s.inspected_qty)) AS rate
FROM silver_dated s
LEFT JOIN dim_line l
  ON l.line_id = s.line_id
 AND s.business_date >= l.valid_from
 AND (l.valid_to IS NULL OR s.business_date < l.valid_to)
GROUP BY COALESCE(l.plant_id, :unknown_plant_id), s.business_date
ORDER BY s.business_date, plant_id

-- name: naive_units_line_day
SELECT s.business_date, s.line_id,
       SUM(s.inspected_qty) AS inspected_qty,
       SUM(s.defective_qty) AS defective_qty,
       try_divide(CAST(SUM(s.defective_qty) AS DOUBLE), SUM(s.inspected_qty)) AS rate
FROM silver_dated s
GROUP BY s.business_date, s.line_id
ORDER BY s.business_date, s.line_id

-- name: inner_join_totals
-- Deliberately wrong for a report: an inner join to the dimension silently
-- drops every inspection whose line has no valid dimension row.
SELECT COUNT(*) AS rows,
       SUM(s.inspected_qty * u.pieces_per_uom) AS inspected_pieces,
       SUM(s.defective_qty * u.pieces_per_uom) AS defective_pieces
FROM silver_dated s
JOIN dim_line l
  ON l.line_id = s.line_id
 AND s.business_date >= l.valid_from
 AND (l.valid_to IS NULL OR s.business_date < l.valid_to)
JOIN unit_conversion u ON u.uom = s.uom

-- name: left_join_by_plant
-- A left join keeps the fact but leaves a NULL plant: the group exists, it is
-- just unnamed. The contract replaces that NULL with the unknown member.
SELECT l.plant_id,
       COUNT(*) AS rows,
       SUM(s.inspected_qty * u.pieces_per_uom) AS inspected_pieces,
       SUM(s.defective_qty * u.pieces_per_uom) AS defective_pieces
FROM silver_dated s
LEFT JOIN dim_line l
  ON l.line_id = s.line_id
 AND s.business_date >= l.valid_from
 AND (l.valid_to IS NULL OR s.business_date < l.valid_to)
JOIN unit_conversion u ON u.uom = s.uom
GROUP BY l.plant_id
ORDER BY l.plant_id NULLS FIRST

-- name: history_join_rows
-- Deliberately wrong: the natural key alone. line_id repeats in a type 2
-- dimension, so each fact meets every version of its line: many-to-many.
SELECT COUNT(*) AS rows
FROM silver_dated s
JOIN dim_line l ON l.line_id = s.line_id
JOIN unit_conversion u ON u.uom = s.uom

-- name: history_join_by_plant
SELECT l.plant_id,
       COUNT(*) AS rows,
       SUM(s.inspected_qty * u.pieces_per_uom) AS inspected_pieces,
       SUM(s.defective_qty * u.pieces_per_uom) AS defective_pieces
FROM silver_dated s
JOIN dim_line l ON l.line_id = s.line_id
JOIN unit_conversion u ON u.uom = s.uom
GROUP BY l.plant_id
ORDER BY l.plant_id

-- name: history_join_by_supervisor
SELECT l.supervisor,
       COUNT(*) AS rows,
       SUM(s.inspected_qty * u.pieces_per_uom) AS inspected_pieces,
       SUM(s.defective_qty * u.pieces_per_uom) AS defective_pieces
FROM silver_dated s
JOIN dim_line l ON l.line_id = s.line_id
JOIN unit_conversion u ON u.uom = s.uom
GROUP BY l.supervisor
ORDER BY l.supervisor

-- name: supervisor_as_was
-- Type 2 reading: the supervisor on the inspection's business day.
SELECT l.supervisor,
       COUNT(*) AS rows,
       SUM(f.inspected_pieces) AS inspected_pieces,
       SUM(f.defective_pieces) AS defective_pieces
FROM fact_inspection f
JOIN dim_line l ON l.line_sk = f.line_sk
GROUP BY l.supervisor
ORDER BY l.supervisor

-- name: supervisor_as_is
-- Type 1 reading of the same history: today's supervisor for every inspection.
SELECT c.supervisor,
       COUNT(*) AS rows,
       SUM(f.inspected_pieces) AS inspected_pieces,
       SUM(f.defective_pieces) AS defective_pieces
FROM fact_inspection f
JOIN dim_line l ON l.line_sk = f.line_sk
JOIN dim_line c ON c.line_id = l.line_id AND c.is_current
GROUP BY c.supervisor
ORDER BY c.supervisor

-- name: window_business_dates
-- The contract's window: the last :window_days BUSINESS days of the plant
-- calendar up to and including :as_of.
SELECT date
FROM (
  SELECT date, ROW_NUMBER() OVER (ORDER BY date DESC) AS position
  FROM dim_date
  WHERE is_business_day AND date <= :as_of
)
WHERE position <= :window_days
ORDER BY date

-- name: window_calendar_dates
-- Deliberately wrong: the last :window_days calendar days.
SELECT date
FROM dim_date
WHERE date BETWEEN date_sub(:as_of, :window_days - 1) AND :as_of
ORDER BY date

-- name: window_weekday_dates
-- Deliberately wrong: Monday to Friday, ignoring the plant calendar's shutdowns.
SELECT date
FROM (
  SELECT date, ROW_NUMBER() OVER (ORDER BY date DESC) AS position
  FROM dim_date
  WHERE dayofweek(date) NOT IN (1, 7) AND date <= :as_of
)
WHERE position <= :window_days
ORDER BY date

-- name: window_business_day_count
SELECT COUNT(*) AS business_days
FROM window_dates w
JOIN dim_date d ON d.date = w.date AND d.is_business_day

-- name: window_totals
-- Reads the temporary view window_dates registered from one of the three
-- window statements above; every real plant appears, observed or not.
WITH facts AS (
  SELECT l.plant_id,
         COUNT(DISTINCT f.business_date) AS days_with_data,
         COUNT(*) AS inspections,
         SUM(f.inspected_pieces) AS inspected_pieces,
         SUM(f.defective_pieces) AS defective_pieces
  FROM fact_inspection f
  JOIN dim_line l ON l.line_sk = f.line_sk
  WHERE f.business_date IN (SELECT date FROM window_dates)
  GROUP BY l.plant_id
),
grid AS (
  SELECT plant_id FROM dim_plant WHERE plant_id <> :unknown_plant_id
  UNION
  SELECT plant_id FROM facts
)
SELECT g.plant_id,
       COALESCE(f.days_with_data, 0) AS days_with_data,
       COALESCE(f.inspections, 0) AS inspections,
       COALESCE(f.inspected_pieces, 0) AS inspected_pieces,
       COALESCE(f.defective_pieces, 0) AS defective_pieces,
       CASE WHEN f.inspections IS NULL THEN :empty_status
            WHEN f.inspected_pieces = 0 THEN :zero_status
            ELSE 'ok' END AS status,
       try_divide(CAST(COALESCE(f.defective_pieces, 0) AS DOUBLE),
                  COALESCE(f.inspected_pieces, 0)) AS rate
FROM grid g
LEFT JOIN facts f ON f.plant_id = g.plant_id
ORDER BY g.plant_id

-- name: boundary
SELECT inspection_id, shift_id, business_date,
       date_format(business_date, 'yyyy-MM') AS month
FROM fact_inspection
ORDER BY inspection_id
