-- Lab L24 legacy source, shown as TEXT ONLY.
-- Original SpicyBrain teaching procedure for the fictional Cinderline Components
-- reporting layer. It was never executed: no SQL Server, SSIS or SQL Server Agent
-- was installed, started or contacted while this lab was built or tested.
-- Settings recorded by the inventory: server clock America/New_York (local time,
-- no offset stored); database collation SQL_Latin1_General_CP1_CI_AS.

CREATE PROCEDURE dbo.sp_daily_inspections
    @plant_code NVARCHAR(10)
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @since DATETIME;
    DECLARE @until DATETIME = GETDATE();

    SELECT @since = w.last_loaded_at
      FROM etl.watermark AS w
     WHERE w.job_name = N'daily_inspections';

    -- 1. Business days touched since the last run (change time, not event time)
    SELECT DISTINCT i.plant_code,
           CAST(DATEADD(HOUR, -6, i.inspected_at) AS DATE) AS business_day
      INTO #affected_days
      FROM erp.inspection AS i
     WHERE i.plant_code = @plant_code
       AND i.updated_at > @since
       AND i.updated_at <= @until;

    BEGIN TRANSACTION;

    -- 2. Replace the detail rows of every affected day
    DELETE d
      FROM dbo.rpt_quality_detail AS d
      JOIN #affected_days AS a
        ON a.plant_code = d.plant_code
       AND a.business_day = d.business_day;

    INSERT INTO dbo.rpt_quality_detail
           (inspection_id, plant_code, business_day, shift_code, inspector_code,
            units_inspected, units_defective, rework_cost)
    SELECT i.inspection_id,
           i.plant_code,
           CAST(DATEADD(HOUR, -6, i.inspected_at) AS DATE),
           ISNULL(s.shift_code, N'UNASSIGNED'),
           i.inspector_code,
           i.units_inspected,
           i.units_defective,
           i.rework_cost
      FROM erp.inspection AS i
      JOIN #affected_days AS a
        ON a.plant_code = i.plant_code
       AND a.business_day = CAST(DATEADD(HOUR, -6, i.inspected_at) AS DATE)
      LEFT JOIN erp.inspector AS s
        ON s.inspector_code = i.inspector_code
       AND s.plant_code = @plant_code
     WHERE i.updated_at <= @until;

    -- 3. Upsert the daily report from the rebuilt detail
    MERGE dbo.rpt_quality_daily AS t
    USING (
        SELECT d.plant_code, d.business_day, d.shift_code,
               COUNT(*)               AS inspections,
               SUM(d.units_inspected) AS units_inspected,
               SUM(d.units_defective) AS units_defective,
               SUM(d.rework_cost)     AS rework_cost
          FROM dbo.rpt_quality_detail AS d
          JOIN #affected_days AS a
            ON a.plant_code = d.plant_code
           AND a.business_day = d.business_day
         GROUP BY d.plant_code, d.business_day, d.shift_code
    ) AS s
       ON t.plant_code = s.plant_code
      AND t.business_day = s.business_day
      AND t.shift_code = s.shift_code
    WHEN MATCHED THEN UPDATE SET
         inspections     = s.inspections,
         units_inspected = s.units_inspected,
         units_defective = s.units_defective,
         rework_cost     = s.rework_cost,
         defect_pct      = s.units_defective * 100 / s.units_inspected
    WHEN NOT MATCHED BY TARGET THEN INSERT
         (plant_code, business_day, shift_code, inspections, units_inspected,
          units_defective, rework_cost, defect_pct)
         VALUES (s.plant_code, s.business_day, s.shift_code, s.inspections,
                 s.units_inspected, s.units_defective, s.rework_cost,
                 s.units_defective * 100 / s.units_inspected);

    -- 4. Advance the watermark inside the same transaction
    UPDATE etl.watermark
       SET last_loaded_at = @until
     WHERE job_name = N'daily_inspections';

    COMMIT TRANSACTION;
END;
