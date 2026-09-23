-- Apply one intake message idempotently.
-- 1. The message_id is logged once; a redelivered message inserts nothing and stops here.
-- 2. A new item is inserted; an existing item is updated only by a NEWER source_seq and
--    only while nobody has claimed it. Older or repeated messages never overwrite newer state.
-- Returns the item row when this message changed it, and no row when it was skipped.
WITH logged AS (
    INSERT INTO qr.intake_message (message_id, item_id, source_seq)
    VALUES (:'message_id', :'item_id', :source_seq)
    ON CONFLICT (message_id) DO NOTHING
    RETURNING message_id
)
INSERT INTO qr.review_item AS r
       (item_id, plant_id, part_serial, defect_code, severity, flagged_at, source_seq)
SELECT :'item_id', :'plant_id', :'part_serial', :'defect_code',
       CAST(:severity AS smallint), CAST(:'flagged_at' AS timestamptz), :source_seq
  FROM logged
ON CONFLICT (item_id) DO UPDATE
   SET defect_code = EXCLUDED.defect_code,
       severity    = EXCLUDED.severity,
       source_seq  = EXCLUDED.source_seq,
       version     = r.version + 1
 WHERE r.source_seq < EXCLUDED.source_seq
   AND r.status = 'ready'
RETURNING r.item_id, r.version;
