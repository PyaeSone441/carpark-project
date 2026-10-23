# STEP 4: Backend that serves the website and the data.
# Locally:  python -m uvicorn api:app --reload
# Render:   uvicorn api:app --host 0.0.0.0 --port $PORT
import os
from pathlib import Path

import psycopg
from fastapi import FastAPI
from fastapi.responses import FileResponse
from psycopg.rows import dict_row

app = FastAPI()
INDEX = Path(__file__).parent / "index.html"


@app.get("/")
def home():
    return FileResponse(INDEX)


@app.get("/api/availability")
def availability():
    with psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row) as conn:
        return conn.execute("""
            SELECT a.carpark_number, c.address, c.lat, c.lng,
                   a.lots_available, a.total_lots, a.update_datetime
            FROM current_availability a
            JOIN carparks c ON a.carpark_number = c.car_park_no
            WHERE a.lot_type = 'C' AND a.total_lots > 0
        """).fetchall()
