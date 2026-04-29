-- =============================================================
-- Migration V1: Role enum type
-- =============================================================
-- Why an enum?
--   Postgres enums are stored as integers internally (fast),
--   enforce a closed set of values at the DB level (no "typo"
--   roles sneaking in), and read as human-friendly strings in
--   queries.  Adding a new role later is a single ALTER TYPE.
-- =============================================================

CREATE TYPE public.app_role AS ENUM (
    'customer',    -- default role for anyone who signs up
    'organizer',   -- elevated: can create/manage events (or whatever your domain needs)
    'admin'        -- full platform access
);
