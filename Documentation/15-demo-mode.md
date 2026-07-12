# 15 — Demo Mode

**Location:** Separate app entry — `demo_mode/app.py`

## Purpose

Try the core workflow **without** Supabase, Shopify API, live Markaz scraping, or `secrets.toml`.  
All data is **simulated** and stored in local JSON files per demo user.

> **Important:** Demo Mode uses a **standalone lightweight UI** (`demo_mode/demo_main.py`).  
> It does **not** load the full production `app.py` (avoids Playwright/pandas instability on some systems).

## Run Demo Mode

```bash
streamlit run demo_mode/app.py
```

Open: **http://localhost:8501**

No secrets required. Chromium / Playwright is **not** needed for demo.

---

## Demo login accounts

Shown on the login page:

| Username | Password | Role |
|----------|----------|------|
| `demo` | `demo123` | Demo Admin |
| `viewer` | `view123` | Demo Viewer |

### Step-by-step login

1. Open demo app URL
2. See green box with demo credentials
3. Enter `demo` / `demo123` (pre-filled by default)
4. Click **Sign in to Demo**
5. Dashboard loads with **Demo Mode** banner at the top

---

## What is different in Demo Mode

| Feature | Production (`app.py`) | Demo Mode |
|---------|----------------------|-----------|
| Entry file | `app.py` | `demo_mode/app.py` → `demo_main.py` |
| UI | Full converter + tracked UI | Simplified standalone UI |
| Login | `secrets.toml` `[app_login]` | Built-in demo accounts |
| Tracked products | Supabase | Per-user JSON on server |
| Markaz fetch | Real Playwright scrape | **Simulated** from pasted URL |
| Shopify publish/sync | Real Admin API | **Simulated** (no real calls) |
| Shopify handles | Real store handles | `demo-` prefixed (no collision) |
| CSV export | Full pandas export | Not in simplified demo UI |
| `secrets.toml` | Required | Not required |
| Playwright / Chromium | Required | **Not used** |

---

## Architecture (why demo is separate)

```
demo_mode/app.py
    ├── activate_demo_mode()     # Patches auth only
    ├── demo_auth login page
    └── demo_main.run()          # Standalone UI (no import of app.py)
            ├── demo_scrape.py   # Simulated product from URL
            ├── demo_store.py    # JSON file storage
            └── demo_shopify.py  # Simulated publish/sync/delete
```

**Safety layer:** If production Shopify code runs while `MARKAZ_DEMO_MODE=1`, `demo_guard.py` blocks real API calls.

---

## Storage (per user)

Each demo user gets isolated server-side data:

| Layer | Location |
|-------|----------|
| Server JSON | `demo_mode/data/users/{username}/local_storage.json` |

Data persists between sessions for the same username on the same machine.

> Browser `localStorage` sync is **disabled** in demo (caused crashes on some Linux setups).  
> Server JSON is the source of truth.

---

## Simulated Markaz fetch

When you paste a Markaz URL and click **Fetch Product Data** or **Add to List**:

1. No browser opens — no network scrape
2. Title is derived from the URL slug (e.g. `blue-printed-cotton-lawn-...`)
3. Sample price: **Rs. 1,899** with default [pricing rules](./13-pricing-rules.md)
4. Sample SKU: `DEMO-...`
5. One placeholder image URL is attached

This lets you test the flow without hitting Markaz or Playwright.

---

## Dummy reference data

On **first login**, 3 sample tracked products are auto-seeded:

1. Blue Printed Cotton Lawn 2-Piece Eid Set Medium — In Stock / Active
2. Long Printed 2PC Doria Lawn Suit Blue White — In Stock / Active
3. Elegant Women's Raw Silk Shirt Set — Out of Stock / Draft

All use `demo-` prefixed Shopify handles.  
Source: `demo_mode/dummy_data.py`

---

## Demo banner

After login you will see:

> **Demo Mode** — per-user JSON storage on server.  
> Supabase, live Markaz scraping, and real Shopify are disabled. Actions are simulated only.

Every Shopify action also shows:

> **Demo Mode:** No real Shopify connection. This action was simulated only — nothing was sent to your live store.

---

## Step-by-step: Try workflow in demo

### Step 1: Login as `demo`

### Step 2: Open **Tracked Products** tab

See 3 dummy products with simulated Shopify status.

### Step 3: Click **Publish** or **Sync Stock** on a card

Yellow warning + simulated success — **no real Shopify call**.

### Step 4: Open **Shopify Converter** tab

1. Paste any Markaz product URL  
2. Click **Fetch Product Data** → preview from simulated data  
3. Click **Add to List** → product added + saved to tracked JSON  

### Step 5: Click **Publish All to Shopify (Demo)**

Simulated publish for all products in the converter list.

### Step 6: Logout and login as `viewer`

Separate per-user storage — viewer gets their own seeded data on first login.

---

## Deploy on Streamlit Cloud

**Wrong** (folder URL):
```
https://github.com/.../Markaz-Products-Cloning/tree/main/demo_mode
```

**Correct** — link to the `.py` file:
```
https://github.com/trendswd-pk/Markaz-Products-Cloning/blob/main/demo_mode/app.py
```

Or use the interactive picker:

- Repository: `trendswd-pk/Markaz-Products-Cloning`
- Branch: `main`
- Main file path: `demo_mode/app.py`

No secrets required. Login: `demo` / `demo123`

---

## File structure

```
demo_mode/
├── app.py              # Entry point (login + banner + demo_main)
├── demo_main.py        # Standalone demo UI (converter + tracked tabs)
├── bootstrap.py        # Patches auth for demo login
├── demo_auth.py        # Login page with visible credentials
├── demo_scrape.py      # Simulated Markaz fetch from URL
├── demo_markaz.py      # Simulated fetch for tracked rows
├── demo_store.py       # Supabase replacement (JSON files)
├── demo_shopify.py     # Simulated Shopify publish/sync/delete
├── demo_guard.py       # Blocks real Shopify API in demo
├── demo_ui.py          # Demo banner
├── dummy_data.py       # Reference tracked products
├── local_storage.py    # Per-user JSON storage layer
├── demo_config.py      # Demo users + storage namespace
└── data/users/         # Per-user persisted JSON (gitignored)
```

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `segmentation fault` on start | Old demo imported full `app.py` + Playwright | Use latest code; run `demo_mode/app.py` only |
| Real Shopify store updating | Ran `app.py` instead of demo, or old handles | Use `demo_mode/app.py`; handles must start with `demo-` |
| `Oh no. Error running app` on fetch | Playwright crash (production app) | Use demo mode for testing without scrape |
| Port 8501 busy | Previous Streamlit still running | `fuser -k 8501/tcp` then restart |
| Empty tracked list for `viewer` | First login seeds data | Log in once; data saves to `data/users/viewer/` |

---

## Switch to production

```bash
streamlit run app.py
```

Requires full `secrets.toml` — see [14-configuration-setup.md](./14-configuration-setup.md).

Production app includes:

- Real Markaz scraping (Playwright)
- Supabase tracked products
- Live Shopify publish/sync
- Full CSV export with pandas
- Single + Multiple add modes
- Complete tracked-products bulk actions
