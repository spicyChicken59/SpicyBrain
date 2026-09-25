-- Lab L23 starter claim for :'reviewer_id'.
-- GAP 7: nothing stops two workers from choosing the same row. Lock the chosen row inside
--        the subquery, and pass over rows another session is claiming instead of waiting.
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
          LIMIT 1)
   AND r.status = 'ready'
RETURNING r.item_id, r.claimed_by, r.version;
