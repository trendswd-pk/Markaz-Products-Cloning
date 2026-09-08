# Demo Mode — Markaz to Shopify Converter

Standalone offline demo for the Trends WD portfolio. Clients can try the full UI without production backends, secrets, Playwright, Supabase, or live Shopify.

**Demo is excluded from the main product deploy** (Vercel API / production Streamlit `app.py`). Deploy this folder as its **own** Streamlit Cloud (or similar) project with main file `demo_mode/app.py`.

## Run locally

From the repository root:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run demo_mode/app.py
```

Open **http://localhost:8501**. No `.env` or secrets file required.

## Demo accounts

Shown as clickable cards on the Demo Login screen:

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin@admin.com` | `admin123` |
| Editor / Staff | `demo` | `demo123` |
| Viewer | `viewer@demo.com` (or `viewer`) | `view123` |

Each account has an isolated JSON sandbox under `demo_mode/data/users/`. Seed data loads on first login. Use **Reset demo data** in the banner to restore seeds.

## `demo.json`

```json
{
  "live_demo_url": "https://demomode-for-makaz.streamlit.app/",
  "type": "web-app"
}
```

- **Do not** put passwords in `demo.json`.
- Update `live_demo_url` only when the public demo host changes.

## Branding

- Favicon: `demo_mode/public/favicon.png` (Trends WD live asset).

## Screenshots

```bash
# From repo root (writes to Documentation/images/)
python scripts/capture_docs_screenshots.py
# or
node demo_mode/capture-docs.js
```

## What is mocked

| Action | Behavior |
|--------|----------|
| Fetch Product Data | Simulated title/price from URL |
| Add to List | Converter list + per-user tracked JSON |
| Publish / Sync Shopify | Simulated + Demo Mode banner |
| Tracked Products | Professional seed rows on first login |
| Delete tracked row | Removes from demo JSON only |

## Storage keys

Per-user files: `demo_mode/data/users/{username}/local_storage.json`  
Namespace: `markaz_demo` / slug `markaz-products-cloning`.

## Production app

```bash
streamlit run app.py
```

Requires `.streamlit/secrets.toml` (login, Supabase, Shopify) and Playwright Chromium.
