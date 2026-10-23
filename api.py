# STEP 4: Backend that serves the website and the data
#   uvicorn api:app --reload   then open http://127.0.0.1:8000/
import sqlite3

from fastapi import FastAPI
from fastapi.responses import FileResponse

app = FastAPI()


@app.get("/")
def home():
    return FileResponse("index.html")


@app.get("/api/availability")
def availability():
    conn = sqlite3.connect("carpark.db")
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT a.carpark_number, c.address, c.lat, c.lng,
               a.lots_available, a.total_lots, a.update_datetime
        FROM current_availability a
        JOIN carparks c ON a.carpark_number = c.car_park_no
        WHERE a.lot_type = 'C' AND a.total_lots > 0
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]
