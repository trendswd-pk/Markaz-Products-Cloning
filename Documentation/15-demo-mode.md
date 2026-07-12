# 15 — Demo Mode

**Location:** Separate app entry — `demo_mode/app.py`

## Purpose

Try the full UI without Supabase, Shopify API, or real credentials. Uses local storage and simulated Shopify actions.

## Run Demo Mode

```bash
streamlit run demo_mode/app.py
```

Open: **http://localhost:8501**

---

## Demo login accounts

Shown directly on the login page:

| Username | Password | Role |
|----------|----------|------|
| `demo` | `demo123` | Demo Admin |
| `viewer` | `view123` | Demo Viewer |

### Step-by-step login

1. Open demo app URL
2. See green box with credentials pre-documented
3. Enter `demo` / `demo123` (pre-filled by default)
4. Click **Sign in to Demo**
5. Dashboard loads with orange/green **Demo Mode** banner

---

## What is different in Demo Mode

| Feature | Production | Demo Mode |
|---------|-----------|-----------|
| Login | `secrets.toml` `[app_login]` | Built-in demo accounts |
| Tracked Products storage | Supabase | localStorage + JSON files |
| Shopify publish/sync | Real API | Simulated (no real calls) |
| Shopify status | Live from store | Dummy + simulated |
| Markaz scraping | Real Playwright | ✅ Still real (optional) |
| CSV export | Real | ✅ Works |
| API routes (`api/`) | Available | Not used |

---

## Storage (per user)

Each demo user gets isolated data:

| Layer | Location |
|-------|----------|
| Browser | `localStorage` key: `markaz_demo_{username}` |
| Server | `demo_mode/data/users/{username}/local_storage.json` |

Data persists between sessions per username.

---

## Dummy reference data

On **first login**, 3 sample tracked products are auto-seeded:

1. Blue Printed Cotton Lawn 2-Piece Eid Set Medium — In Stock / Active
2. Long Printed 2PC Doria Lawn Suit Blue White — In Stock / Active
3. Elegant Women's Raw Silk Shirt Set — Out of Stock / Draft

Source: `demo_mode/dummy_data.py`

---

## Demo banner

Top of dashboard after login:

> **Demo Mode** — localStorage + local JSON storage. Supabase and API routes are disabled. Shopify actions are simulated.

---

## Step-by-step: Try full workflow in demo

### Step 1: Login as `demo`

### Step 2: Open Tracked Products

See 3 dummy products with Shopify status.

### Step 3: Click **Publish Shopify** on one card

Simulated success — no real Shopify call.

### Step 4: Open Shopify Converter

Add a real Markaz URL or use existing list.

### Step 5: Download CSV

CSV export works normally with real scraped data.

### Step 6: Logout and login as `viewer`

Separate storage — empty list until viewer's first login seeds data.

---

## File structure

```
demo_mode/
├── app.py              # Entry point
├── bootstrap.py        # Patches production modules
├── demo_auth.py        # Login page with visible credentials
├── demo_store.py       # Supabase replacement
├── demo_shopify.py     # Simulated Shopify API
├── dummy_data.py       # Reference products
├── local_storage.py    # Per-user storage layer
├── static/
│   └── local_storage.js
└── README.md
```

---

## Switch to production

```bash
streamlit run app.py
```

Requires full `secrets.toml` configuration — [14-configuration-setup.md](./14-configuration-setup.md)
