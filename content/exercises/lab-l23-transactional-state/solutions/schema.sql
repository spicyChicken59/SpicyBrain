-- Lab L23 reference schema: operational state for Cinderline's quality-review app.
-- Tested on local PostgreSQL 16.13. Run once, as the database owner, on an empty database.
-- Every rule the application relies on is a constraint the database enforces,
-- so a bug in one request handler cannot write an impossible row.

CREATE SCHEMA qr;

CREATE TABLE qr.plant (
    plant_id    text PRIMARY KEY CHECK (plant_id ~ '^P[0-9]$'),
    plant_name  text NOT NULL
);

CREATE TABLE qr.reviewer (
    reviewer_id  text PRIMARY KEY CHECK (reviewer_id ~ '^R-[0-9]{3}$'),
    display_name text NOT NULL CHECK (length(display_name) > 0),
    plant_id     text NOT NULL REFERENCES qr.plant (plant_id),
    active       boolean NOT NULL DEFAULT true
);

-- One row per part awaiting (or finished with) a human quality review.
CREATE TABLE qr.review_item (
    item_id      text PRIMARY KEY CHECK (item_id ~ '^QR-[0-9]{4}$'),
    plant_id     text NOT NULL REFERENCES qr.plant (plant_id),
    part_serial  text NOT NULL,
    defect_code  text NOT NULL CHECK (defect_code IN ('CRACK', 'POROSITY', 'DIMENSION', 'SURFACE')),
    severity     smallint NOT NULL CHECK (severity BETWEEN 1 AND 4),
    flagged_at   timestamptz NOT NULL,
    source_seq   integer NOT NULL CHECK (source_seq >= 1),
    status       text NOT NULL DEFAULT 'ready' CHECK (status IN ('ready', 'claimed', 'decided')),
    claimed_by   text REFERENCES qr.reviewer (reviewer_id),
    claimed_at   timestamptz,
    decision     text CHECK (decision IN ('accept', 'rework', 'scrap')),
    decided_at   timestamptz,
    version      integer NOT NULL DEFAULT 1 CHECK (version >= 1),
    -- The state machine as data: which columns must be filled in which status.
    CONSTRAINT review_item_state_consistent CHECK (
        (status = 'ready'   AND claimed_by IS NULL     AND decision IS NULL) OR
        (status = 'claimed' AND claimed_by IS NOT NULL AND decision IS NULL) OR
        (status = 'decided' AND claimed_by IS NOT NULL AND decision IS NOT NULL))
);

-- The work queue: only ready rows, stored in claim order.
CREATE INDEX review_item_ready_queue
    ON qr.review_item (severity DESC, flagged_at, item_id)
    WHERE status = 'ready';

-- A reviewer holds at most one open claim at a time.
CREATE UNIQUE INDEX review_item_one_open_claim
    ON qr.review_item (claimed_by)
    WHERE status = 'claimed';

-- Append-only log of intake messages; the producer's message_id is the idempotency key.
CREATE TABLE qr.intake_message (
    message_id   text PRIMARY KEY,
    item_id      text NOT NULL,
    source_seq   integer NOT NULL CHECK (source_seq >= 1),
    received_at  timestamptz NOT NULL DEFAULT clock_timestamp()
);
