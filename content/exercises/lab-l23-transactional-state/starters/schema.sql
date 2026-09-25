-- Lab L23 starter schema. It creates the right tables and columns, so the harness can run,
-- but several rules are left to you. Each GAP names the rule the tests expect.

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

CREATE TABLE qr.review_item (
    item_id      text PRIMARY KEY CHECK (item_id ~ '^QR-[0-9]{4}$'),
    plant_id     text NOT NULL REFERENCES qr.plant (plant_id),
    part_serial  text NOT NULL,
    defect_code  text NOT NULL,          -- GAP 1: allow only CRACK, POROSITY, DIMENSION, SURFACE
    severity     smallint NOT NULL,      -- GAP 2: severity must be between 1 and 4
    flagged_at   timestamptz NOT NULL,
    source_seq   integer NOT NULL CHECK (source_seq >= 1),
    status       text NOT NULL DEFAULT 'ready' CHECK (status IN ('ready', 'claimed', 'decided')),
    claimed_by   text REFERENCES qr.reviewer (reviewer_id),
    claimed_at   timestamptz,
    decision     text CHECK (decision IN ('accept', 'rework', 'scrap')),
    decided_at   timestamptz,
    version      integer NOT NULL DEFAULT 1 CHECK (version >= 1)
    -- GAP 3: a table constraint named review_item_state_consistent that ties status to
    --        claimed_by and decision (ready: neither; claimed: owner, no decision;
    --        decided: owner and decision).
);

-- GAP 4: a partial index over ready rows in claim order (severity DESC, flagged_at, item_id).
-- GAP 5: a partial UNIQUE index named review_item_one_open_claim so that a reviewer
--        holds at most one claimed item at a time.

CREATE TABLE qr.intake_message (
    message_id   text PRIMARY KEY,
    item_id      text NOT NULL,
    source_seq   integer NOT NULL CHECK (source_seq >= 1),
    received_at  timestamptz NOT NULL DEFAULT clock_timestamp()
);
