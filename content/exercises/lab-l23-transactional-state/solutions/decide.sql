-- Record a decision only if the row is still exactly what the reviewer loaded:
-- same version, still claimed, still claimed by this reviewer.
-- No row returned means a conflict: reload, show what changed, let the person decide again.
UPDATE qr.review_item
   SET status     = 'decided',
       decision   = :'decision',
       decided_at = now(),
       version    = version + 1
 WHERE item_id    = :'item_id'
   AND claimed_by = :'reviewer_id'
   AND status     = 'claimed'
   AND version    = :expected_version
RETURNING item_id, status, decision, version;
