# SG Carpark Availability

Live map and heatmap of HDB car park availability in Singapore, built on data.gov.sg open data.

**Live site:** _add your Render link here_

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
- **Idempotent loads.** Primary keys plus `ON CONFLICT` mean rerunning any step never creates duplicates.

## Known limitations

- The free Render tier sleeps after 15 minutes without visitors, so the first page load can take about a minute.
- GitHub Actions schedules can be delayed when GitHub is busy, so data may occasionally be a few minutes older than 5 minutes.

---

## Deployment guide

### 1. Create the database (Supabase)

1. Sign up at supabase.com and create a **New project**. Choose the **Southeast Asia (Singapore)** region.
2. Set a database password using **only letters and numbers** (symbols like `@ : / #` break connection strings). Save it somewhere.
3. When the project is ready, click **Connect** at the top. Copy the **Session pooler** connection string (not "Direct connection", which doesn't work from GitHub Actions or Render). It looks like:
   `postgresql://postgres.abcdefgh:[YOUR-PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres`
4. Replace `[YOUR-PASSWORD]` (including the brackets) with your password. This full string is your **DATABASE_URL**. Never put it in your code or commit it.

### 2. Put the project on GitHub

1. Create a new **public** repository on github.com, e.g. `sg-carpark-availability`. Don't add a README (you have one).
2. In a terminal inside this folder:
   ```
   git init
   git add .
   git commit -m "Car park availability pipeline"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/sg-carpark-availability.git
   git push -u origin main
   ```
3. Check that the `.github/workflows` folder appears in the repo on GitHub.

### 3. Add the database secret

Repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
- Name: `DATABASE_URL`
- Value: your connection string from step 1

### 4. Create the tables and load locations

1. Repo → **Actions** tab (click "I understand… enable them" if asked).
2. Click **Set up tables and load car park locations** → **Run workflow**.
3. Wait for the green tick. Open the run to see `Loaded 2xxx car parks`.
4. Then click **Fetch car park availability** → **Run workflow**. It should show `... readings, ... changed and added to history`.
5. In Supabase → **Table Editor**, you should see three tables with data.

From now on the fetch workflow runs every 5 minutes by itself.

### 5. Deploy the website (Render)

1. Sign up at render.com with your GitHub account.
2. **New** → **Web Service** → choose your repository.
3. Settings:
   - Runtime: **Python 3**
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn api:app --host 0.0.0.0 --port $PORT`
   - Instance type: **Free**
4. Under **Environment Variables**, add `DATABASE_URL` with the same connection string.
5. Click **Deploy**. When it says "Live", open the `https://....onrender.com` link.

### Keeping it running

- GitHub disables scheduled workflows in public repos after 60 days with no activity, so push a commit at least every month or two.
- Supabase's free tier allows 500 MB. Check usage in the Supabase dashboard every couple of weeks.

## Running locally (optional)

```
python -m pip install -r requirements.txt
$env:DATABASE_URL="your-connection-string"     # PowerShell; use export on Mac/Linux
python fetch.py
python -m uvicorn api:app --reload
```
