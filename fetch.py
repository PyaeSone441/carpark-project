# STEP 3: Pull live availability from the API and save it to the database
#   python fetch.py          -> runs once
#   python fetch.py --loop   -> keeps running, every 60 seconds (Ctrl+C to stop)
import sqlite3
import sys
import time
from datetime import datetime, timezone, timedelta

import requests

SGT = timezone(timedelta(hours=8))
URL = "https://api.data.gov.sg/v1/transport/carpark-availability"


def fetch_rows():
    r = requests.get(URL, timeout=30)
    r.raise_for_status()
    item = r.json()["items"][0]
    fetched_at = datetime.now(SGT).isoformat()

    rows = []
    for cp in item["carpark_data"]:
        updated = datetime.fromisoformat(cp["update_datetime"]).replace(tzinfo=SGT).isoformat()
        for info in cp["carpark_info"]:
            try:
                rows.append({
                    "carpark_number": cp["carpark_number"],
                    "lot_type": info["lot_type"],
                    "lots_available": int(info["lots_available"]),
                    "total_lots": int(info["total_lots"]),
                    "update_datetime": updated,
                    "fetched_at": fetched_at,
                })
            except (KeyError, ValueError) as e:
                print(f"Skipping bad record {cp.get('carpark_number')}: {e}")
    return rows


def save(rows):
    conn = sqlite3.connect("carpark.db")
    for r in rows:
        # live table: overwrite each car park's latest reading
        conn.execute("""INSERT OR REPLACE INTO current_availability
            VALUES (:carpark_number, :lot_type, :lots_available, :total_lots,
                    :update_datetime, :fetched_at)""", r)
        # history table: only adds a row when the reading is new
        conn.execute("""INSERT OR IGNORE INTO availability_history
            VALUES (:carpark_number, :lot_type, :lots_available, :total_lots,
                    :update_datetime)""", r)
    conn.commit()
    conn.close()


def run_once():
    rows = fetch_rows()
    save(rows)
    print(f"{datetime.now(SGT):%H:%M:%S}  Saved {len(rows)} rows")


if __name__ == "__main__":
    if "--loop" in sys.argv:
        while True:
            try:
                run_once()
            except Exception as e:  # keep looping even if one call fails
                print(f"Error: {e}")
            time.sleep(60)
    else:
        run_once()
