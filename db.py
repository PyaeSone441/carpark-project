# STEP 1: Create the database and tables (run once; safe to rerun)
import sqlite3

conn = sqlite3.connect("carpark.db")  # creates the file if it doesn't exist

conn.executescript("""
CREATE TABLE IF NOT EXISTS current_availability (
    carpark_number   TEXT,
    lot_type         TEXT,
    lots_available   INTEGER,
    total_lots       INTEGER,
    update_datetime  TEXT,
    fetched_at       TEXT,
    PRIMARY KEY (carpark_number, lot_type)
);

CREATE TABLE IF NOT EXISTS availability_history (
    carpark_number   TEXT,
    lot_type         TEXT,
    lots_available   INTEGER,
    total_lots       INTEGER,
    update_datetime  TEXT,
    PRIMARY KEY (carpark_number, lot_type, update_datetime)
);
""")

conn.commit()
conn.close()
print("Tables created in carpark.db")
