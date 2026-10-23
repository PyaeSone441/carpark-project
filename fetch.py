# STEP 3: Pull live availability and save it to Postgres.
# GitHub Actions runs this every 5 minutes. You can also run it yourself:
#   python fetch.py
import os
from datetime import datetime, timezone, timedelta

import psycopg
import requests

SGT = timezone(timedelta(hours=8))
URL = "https://api.data.gov.sg/v1/transport/carpark-availability"


def fetch_rows():
    """EXTRACT + TRANSFORM: call the API and flatten the JSON into rows."""
    r = requests.get(URL, timeout=30)
    r.raise_for_status()
    item = r.json()["items"][0]
    fetched_at = datetime.now(SGT)

    rows, skipped = [], 0
    for cp in item["carpark_data"]:
        for info in cp["carpark_info"]:
            try:
                rows.append({
                    "carpark_number": cp["carpark_number"],
                    "lot_type": info["lot_type"],
                    "lots_available": int(info["lots_available"]),
                    "total_lots": int(info["total_lots"]),
                    "update_datetime": datetime.fromisoformat(
                        cp["update_datetime"]).replace(tzinfo=SGT),
                    "fetched_at": fetched_at,
                })
            except (KeyError, ValueError, TypeError):
                skipped += 1
    if skipped:
        print(f"Skipped {skipped} bad records")
    return rows


def save(conn, rows):
    """LOAD: overwrite the live table; add to history only when a value changed."""
    with conn.cursor() as cur:
        cur.execute("SELECT carpark_number, lot_type, lots_available FROM current_availability")
        previous = {(cp, lt): lots for cp, lt, lots in cur.fetchall()}

        changed = [r for r in rows
                   if previous.get((r["carpark_number"], r["lot_type"])) != r["lots_available"]]

        cur.executemany("""
            INSERT INTO availability_history
                (carpark_number, lot_type, lots_available, total_lots, update_datetime)
            VALUES (%(carpark_number)s, %(lot_type)s, %(lots_available)s,
                    %(total_lots)s, %(update_datetime)s)
            ON CONFLICT DO NOTHING""", changed)

        cur.executemany("""
            INSERT INTO current_availability
                (carpark_number, lot_type, lots_available, total_lots,
                 update_datetime, fetched_at)
            VALUES (%(carpark_number)s, %(lot_type)s, %(lots_available)s,
                    %(total_lots)s, %(update_datetime)s, %(fetched_at)s)
            ON CONFLICT (carpark_number, lot_type) DO UPDATE SET
                lots_available  = EXCLUDED.lots_available,
                total_lots      = EXCLUDED.total_lots,
                update_datetime = EXCLUDED.update_datetime,
                fetched_at      = EXCLUDED.fetched_at""", rows)
    return len(changed)


if __name__ == "__main__":
    rows = fetch_rows()
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        changed = save(conn, rows)
    print(f"{datetime.now(SGT):%Y-%m-%d %H:%M:%S}  {len(rows)} readings, "
          f"{changed} changed and added to history")
