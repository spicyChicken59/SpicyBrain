-- Lab L23 starter intake for one message (:'message_id', :'item_id', :source_seq, ...).
-- GAP 9: log the message_id in qr.intake_message so a redelivery changes nothing.
-- GAP 10: update an existing item only for a newer source_seq and only while it is ready.
INSERT INTO qr.review_item AS r
       (item_id, plant_id, part_serial, defect_code, severity, flagged_at, source_seq)
VALUES (:'item_id', :'plant_id', :'part_serial', :'defect_code',
        CAST(:severity AS smallint), CAST(:'flagged_at' AS timestamptz), :source_seq)
ON CONFLICT (item_id) DO UPDATE
   SET defect_code = EXCLUDED.defect_code,
       severity    = EXCLUDED.severity,
       source_seq  = EXCLUDED.source_seq,
       version     = r.version + 1
RETURNING r.item_id, r.version;
