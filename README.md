# Phone-First Fat Loss Coach

A complete phone-first fat-loss tracker with:
- One-tap daily logging (weight, calories, protein, workout, notes)
- Meal and thought logging
- Daily selfie upload + 30-day montage generation
- Milestone stats (consistency, predicted weight, plateau signal)
- Full data export as ZIP/JSON (portable to other app versions or LLMs)
- Streamlit analytics dashboard

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Run on phone (local Wi-Fi, no hosting required)

1. Start the app with host bound to all interfaces:
   ```bash
   ./scripts/run_phone.sh 8000
   ```
   (or `uvicorn app.main:app --host 0.0.0.0 --port 8000`)
2. Ensure laptop and phone are on the **same Wi-Fi**.
3. The script prints your LAN URL like `http://192.168.1.23:8000`.
4. Open that URL on your phone browser.
5. Tap browser menu → **Add to Home Screen** to install as an app-like icon.

If phone cannot connect:
- Check laptop firewall allows inbound `8000`
- Confirm you used `--host 0.0.0.0` (not `127.0.0.1`)
- Try another port: `./scripts/run_phone.sh 8080`

## Run on phone from anywhere (public URL)

Use any hosting option below, then open the HTTPS URL on phone and add to home screen.

## Optional Streamlit dashboard
```bash
streamlit run dashboard.py
```

## Hosting options

### Option A: Railway (fastest)
1. Push repo to GitHub.
2. Create Railway project from repo.
3. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
4. Deploy and open generated URL on phone.

### Option B: Render
1. New Web Service from GitHub repo.
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Deploy and install on home screen.

### Option C: Fly.io
1. `fly launch`
2. Set app command to uvicorn above
3. `fly deploy`

## Data ownership/export
Use `/api/export` anytime to download all logs + photos as one `fatloss_export.zip`.

## Suggested production upgrades
- Add auth (Supabase Auth/Clerk)
- Move SQLite to Postgres
- Store photos in object storage (S3/Supabase Storage)
- Add push reminders and streak engine
