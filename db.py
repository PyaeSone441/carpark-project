# STEP 1: Create the tables in Postgres (Supabase). Safe to rerun.
# Needs the DATABASE_URL environment variable (your Supabase connection string).
import os

import psycopg

SCHEMA = """
CREATE TABLE IF NOT EXISTS carparks (
    car_park_no             TEXT PRIMARY KEY,
    address                 TEXT,
    lat                     DOUBLE PRECISION,
    lng                     DOUBLE PRECISION,
    car_park_type           TEXT,
    type_of_parking_system  TEXT,
    short_term_parking      TEXT,
    free_parking            TEXT,
    night_parking           TEXT,
    car_park_decks          TEXT,
    gantry_height           TEXT,
    car_park_basement       TEXT
);

CREATE TABLE IF NOT EXISTS current_availability (
    carpark_number   TEXT,
    lot_type         TEXT,
    lots_available   INTEGER,
    total_lots       INTEGER,
    update_datetime  TIMESTAMPTZ,
    fetched_at       TIMESTAMPTZ,
    PRIMARY KEY (carpark_number, lot_type)
);

CREATE TABLE IF NOT EXISTS availability_history (
    carpark_number   TEXT,
    lot_type         TEXT,
    lots_available   INTEGER,
    total_lots       INTEGER,
    update_datetime  TIMESTAMPTZ,
    PRIMARY KEY (carpark_number, lot_type, update_datetime)
);
"""

if __name__ == "__main__":
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        conn.execute(SCHEMA)
    print("Tables ready")
