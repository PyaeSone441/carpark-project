# SG Carpark Availability

Live map of HDB car park availability in Singapore, built on data.gov.sg open data.

**Live site:**(https://carpark-project-bi0v.onrender.com/)

## Architecture

```
data.gov.sg live API ──► fetch.py (GitHub Actions, every 5 min) ──► Postgres (Supabase)
HDB Carpark Info     ──► load_carparks.py (monthly)            ──►      │
                                                                          ▼
                                     api.py (FastAPI on Render) joins live data + locations
                                                                          │
                                     index.html (Leaflet heatmap + markers, refreshes every minute)
```

## Design decisions

- **The website never calls the government API directly.** One poller fills our own database, so traffic to the site doesn't hit the API rate limit, and the site still shows the last known data if the API is down.
- **Two tables for availability.** `current_availability` is overwritten each run (one row per car park and lot type) for the live map. `availability_history` keeps a record for trends.
- **Change data capture.** A reading is added to history only when the number of free lots changed, which avoids storing millions of identical rows.


## Known limitations

- The free Render tier sleeps after 15 minutes without visitors, so the first page load can take about a minute.
- GitHub Actions schedules can be delayed when GitHub is busy, so data may occasionally be a few minutes older than 5 minutes.

---
This project is deployed using supabase and render. do note that 
the website will go inactive if there are no users for 15minutes. it will rerun the website if the first user is detected and give it 1 minute for it to show the website.



```
python -m pip install -r requirements.txt
$env:DATABASE_URL="your-connection-string"     # PowerShell; use export on Mac/Linux
python fetch.py
python -m uvicorn api:app --reload
```
