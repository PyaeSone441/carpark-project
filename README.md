# SG Carpark Availability

Live map and heatmap of HDB car park availability in Singapore, built on data.gov.sg open data.

## How it works

```
data.gov.sg live API ──► fetch.py (every minute) ──► carpark.db ◄── load_carparks.py ◄── HDB Carpark Info
                                                         │
                                          api.py (FastAPI) joins live data + locations
                                                         │
                                          index.html (Leaflet heatmap + markers)
```

## Run it

Open a terminal in this folder.

```bash
pip install -r requirements.txt

python db.py              # 1. create tables (once)
python load_carparks.py   # 2. load car park locations (once)
python fetch.py           # 3. save one snapshot of live availability

uvicorn api:app --reload  # 4. start the website
```

Open http://127.0.0.1:8000/ in your browser.

### Keep the map live

Open a **second** terminal in this folder and run:

```bash
python fetch.py --loop    # saves new data every 60 seconds; Ctrl+C to stop
```

The web page refreshes itself every minute.
