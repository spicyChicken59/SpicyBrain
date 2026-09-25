-- Lab L23 starter grants for the application login role qr_app.
-- GAP 6: this is far too broad. The app must read plant and reviewer, insert and update
--        review_item, and append to intake_message; it must not delete, truncate or drop.
GRANT USAGE ON SCHEMA qr TO qr_app;
GRANT ALL ON ALL TABLES IN SCHEMA qr TO qr_app;
