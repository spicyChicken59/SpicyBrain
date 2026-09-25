-- Lab L23 starter decision for :'item_id' by :'reviewer_id' with :'decision'.
-- GAP 8: the reviewer's form was loaded at :expected_version. Refuse the write when the row
--        has moved on, when it is no longer claimed, or when someone else holds it.
UPDATE qr.review_item
   SET status     = 'decided',
       decision   = :'decision',
       decided_at = now(),
       version    = version + 1
 WHERE item_id = :'item_id'
RETURNING item_id, status, decision, version;
