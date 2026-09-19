SELECT i.* FROM inspections i
WHERE EXISTS (SELECT 1 FROM tags t
              WHERE t.inspection_id = i.inspection_id AND t.tag = 'reviewed');
