# STEP 2: Load HDB car park locations into Postgres (run once, then monthly).
# Pulls the "HDB Carpark Information" dataset from data.gov.sg,
# converts SVY21 coordinates to lat/lng, and upserts into the `carparks` table.
import os
import time

import psycopg
import requests
from pyproj import Transformer

DATASET_ID = "d_23f946fa557947f93a8043bbef41dd09"
URL = "https://data.gov.sg/api/action/datastore_search"

COLUMNS = ["car_park_no", "address", "lat", "lng", "car_park_type",
           "type_of_parking_system", "short_term_parking", "free_parking",
           "night_parking", "car_park_decks", "gantry_height", "car_park_basement"]


def fetch_carpark_info():
    records, offset, limit = [], 0, 1000
    while True:
        r = requests.get(URL, params={"resource_id": DATASET_ID,
                                      "limit": limit, "offset": offset}, timeout=30)
        r.raise_for_status()
        result = r.json()["result"]
        records.extend(result["records"])
        offset += limit
        if offset >= result["total"]:
            break
        time.sleep(1)  # be polite to the API
    return records


def to_rows(records):
    # SVY21 (Singapore's local coordinates) -> lat/lng for the map
    to_latlng = Transformer.from_crs("EPSG:3414", "EPSG:4326", always_xy=True)
    rows = []
    for rec in records:
        try:
            lng, lat = to_latlng.transform(float(rec["x_coord"]), float(rec["y_coord"]))
        except (KeyError, ValueError, TypeError):
            print(f"Skipping {rec.get('car_park_no')}: bad coordinates")
            continue
        rec = {**rec, "lat": lat, "lng": lng}
        rows.append(tuple(None if rec.get(c) is None else
                          (rec[c] if c in ("lat", "lng") else str(rec[c])) for c in COLUMNS))
    return rows


if __name__ == "__main__":
    rows = to_rows(fetch_carpark_info())
    cols = ", ".join(COLUMNS)
    placeholders = ", ".join(["%s"] * len(COLUMNS))
    updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in COLUMNS[1:])
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        with conn.cursor() as cur:
            cur.executemany(
                f"INSERT INTO carparks ({cols}) VALUES ({placeholders}) "
                f"ON CONFLICT (car_park_no) DO UPDATE SET {updates}", rows)
    print(f"Loaded {len(rows)} car parks")
    print(rows[:2])  # lat should be ~1.3, lng ~103.8
