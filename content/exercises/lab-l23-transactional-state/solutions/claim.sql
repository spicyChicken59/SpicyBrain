-- Claim the next ready item for :'reviewer_id' in one short transaction.
-- SKIP LOCKED: a row another session is claiming right now is passed over, not waited for.
-- Returns the claimed row, or no row when nothing is ready.
UPDATE qr.review_item AS r
   SET status     = 'claimed',
       claimed_by = :'reviewer_id',
       claimed_at = now(),
       version    = r.version + 1
 WHERE r.item_id = (
         SELECT q.item_id
           FROM qr.review_item AS q
          WHERE q.status = 'ready'
          ORDER BY q.severity DESC, q.flagged_at, q.item_id
          LIMIT 1
            FOR UPDATE SKIP LOCKED)
   AND r.status = 'ready'
RETURNING r.item_id, r.claimed_by, r.version;
