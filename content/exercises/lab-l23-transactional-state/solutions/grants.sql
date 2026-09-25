-- Least privilege for the application's own login role (created by the harness as qr_app).
-- The app reads reference data, inserts and updates review items, and appends to the
-- intake log. It cannot delete, truncate, alter or drop anything.
GRANT USAGE ON SCHEMA qr TO qr_app;
GRANT SELECT ON qr.plant, qr.reviewer TO qr_app;
GRANT SELECT, INSERT, UPDATE ON qr.review_item TO qr_app;
GRANT SELECT, INSERT ON qr.intake_message TO qr_app;
