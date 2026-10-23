# STEP 2: Load HDB car park locations into the database (run once, refresh monthly)
# Pulls the "HDB Carpark Information" dataset straight from the data.gov.sg API,
# converts SVY21 coordinates to lat/lng, and saves it as the `carparks` table.
import sqlite3
import time

import pandas as pd
import requests
from pyproj import Transformer

DATASET_ID = "d_23f946fa557947f93a8043bbef41dd09"
URL = "https://data.gov.sg/api/action/datastore_search"


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
    return pd.DataFrame(records)


df = fetch_carpark_info()
df = df.drop(columns=["_id"], errors="ignore")

# Convert SVY21 (Singapore's local coordinates) to lat/lng for the map
to_latlng = Transformer.from_crs("EPSG:3414", "EPSG:4326", always_xy=True)
lng, lat = to_latlng.transform(df["x_coord"].astype(float).values,
                               df["y_coord"].astype(float).values)
df["lat"], df["lng"] = lat, lng

conn = sqlite3.connect("carpark.db")
df.to_sql("carparks", conn, if_exists="replace", index=False)
conn.close()

print(f"Loaded {len(df)} car parks")
print(df[["car_park_no", "address", "lat", "lng"]].head(3))  # lat should be ~1.3, lng ~103.8
