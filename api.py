
import os
from pathlib import Path

import psycopg
import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from psycopg.rows import dict_row

app = FastAPI()
INDEX = Path(__file__).parent / "index.html"
ONEMAP_SEARCH = "https://www.onemap.gov.sg/api/common/elastic/search"


def db():
    return psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)


@app.get("/")
def home():
    return FileResponse(INDEX)


@app.get("/api/availability")
def availability():
    """Every car park with its live car lots, for the map."""
    with db() as conn:
        return conn.execute("""
            SELECT a.carpark_number, c.address, c.lat, c.lng,
                   a.lots_available, a.total_lots, a.update_datetime,
                   -- data quality flags
                   a.update_datetime < NOW() - INTERVAL '1 hour' AS is_stale,
                   a.lots_available > a.total_lots              AS is_invalid
            FROM current_availability a
            JOIN carparks c ON a.carpark_number = c.car_park_no
            WHERE a.lot_type = 'C' AND a.total_lots > 0
        """).fetchall()


@app.get("/api/nearby")
def nearby(lat: float = Query(ge=1.1, le=1.5),       # roughly Singapore's bounds
           lng: float = Query(ge=103.5, le=104.2),
           limit: int = Query(5, ge=1, le=20)):
    """The closest car parks with trustworthy live data, nearest first."""
    with db() as conn:
        return conn.execute("""
            SELECT c.car_park_no, c.address, c.lat, c.lng,
                   c.car_park_type, c.free_parking, c.night_parking, c.gantry_height,
                   a.lots_available, a.total_lots, a.update_datetime,
                   -- straight-line distance in metres (haversine formula)
                   ROUND(2 * 6371000 * ASIN(SQRT(
                       POWER(SIN(RADIANS(c.lat - %(lat)s) / 2), 2) +
                       COS(RADIANS(%(lat)s)) * COS(RADIANS(c.lat)) *
                       POWER(SIN(RADIANS(c.lng - %(lng)s) / 2), 2)
                   ))) AS distance_m
            FROM current_availability a
            JOIN carparks c ON a.carpark_number = c.car_park_no
            WHERE a.lot_type = 'C'
              AND a.total_lots > 0
              AND a.lots_available <= a.total_lots                    -- skip invalid readings
              AND a.update_datetime >= NOW() - INTERVAL '1 hour'      -- skip stale readings
            ORDER BY distance_m
            LIMIT %(limit)s
        """, {"lat": lat, "lng": lng, "limit": limit}).fetchall()


@app.get("/api/search")
def search(q: str = Query(min_length=2, max_length=100)):
    """Look up a place name, address or postal code with OneMap (free, no key needed)."""
    try:
        r = requests.get(ONEMAP_SEARCH, timeout=10, params={
            "searchVal": q, "returnGeom": "Y", "getAddrDetails": "Y", "pageNum": 1})
        r.raise_for_status()
        results = r.json().get("results", [])
    except (requests.RequestException, ValueError):
        raise HTTPException(status_code=502, detail="Location search is unavailable right now")

    places = []
    for res in results[:5]:
        try:
            places.append({
                "name": res["SEARCHVAL"].title(),
                "address": res.get("ADDRESS", "").title(),
                "lat": float(res["LATITUDE"]),
                "lng": float(res["LONGITUDE"]),
            })
        except (KeyError, ValueError):
            continue
    return places