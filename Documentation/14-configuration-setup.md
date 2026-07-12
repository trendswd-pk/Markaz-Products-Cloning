# 14 — Configuration & Setup

## Secrets file

All credentials go in `.streamlit/secrets.toml` (gitignored).

Copy from example:
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

---

## [app_login] — App login (required)

```toml
[app_login]
username = "admin"
password = "your_strong_password"
```

| Field | Purpose |
|-------|---------|
| `username` | Login username |
| `password` | Login password |

> Use `[app_login]` not `[auth]` — Streamlit reserves `[auth]`.

See [01-login-page.md](./01-login-page.md)

---

## [supabase] — Tracked Products database

```toml
[supabase]
url = "https://YOUR_PROJECT.supabase.co"
key = "YOUR_SERVICE_ROLE_KEY"
```

| Field | Purpose |
|-------|---------|
| `url` | Supabase project URL |
| `key` | Service role key (server-side only) |

### Setup steps

1. Create project at [supabase.com](https://supabase.com)
2. SQL Editor → run `supabase/01_fresh_install.sql`
3. Copy URL + service_role key from Project Settings → API
4. Paste into `secrets.toml`
5. Restart app

**Without Supabase:** Tracked Products tab shows warning. Converter still works.

---

## [shopify] — Direct Shopify integration

```toml
[shopify]
store_url = "your-store.myshopify.com"
client_id = "your_dev_dashboard_client_id"
client_secret = "shpss_your_dev_dashboard_client_secret"
api_version = "2026-07"
```

### Setup steps

1. [Shopify Dev Dashboard](https://dev.shopify.com/dashboard) → Create app
2. **Configuration** → enable Admin API scopes:
   - `read_products`, `write_products`
   - `read_inventory`, `write_inventory`
   - `read_locations`
3. Save and release app version
4. Install app on your store → approve permissions
5. Copy Client ID + Client Secret to `secrets.toml`
6. Restart app

**Without Shopify:** Publish/Sync buttons disabled. CSV export still works.

### Verify connection

```bash
python check_shopify.py
```

---

## Environment variables (alternative)

| Variable | Replaces |
|----------|----------|
| `APP_USERNAME` | `[app_login].username` |
| `APP_PASSWORD` | `[app_login].password` |
| `SUPABASE_URL` | `[supabase].url` |
| `SUPABASE_KEY` | `[supabase].key` |
| `SHOPIFY_STORE_URL` | `[shopify].store_url` |
| `SHOPIFY_CLIENT_ID` | `[shopify].client_id` |
| `SHOPIFY_CLIENT_SECRET` | `[shopify].client_secret` |

---

## Streamlit config

File: `.streamlit/config.toml`

```toml
[server]
port = 8501
headless = true
```

---

## Vercel API (optional)

Separate serverless scraper at `api/index.py`:

```
GET https://your-app.vercel.app?url=MARKAZ_PRODUCT_URL
```

Not used by Streamlit UI. Returns JSON product data.

---

## Checklist: Full production setup

- [ ] `playwright install chromium`
- [ ] `[app_login]` configured
- [ ] `[supabase]` configured + SQL migration run
- [ ] `[shopify]` configured + scopes approved on store
- [ ] `python check_shopify.py` passes
- [ ] `python check_supabase.py` passes
- [ ] Test login → add product → Tracked Products shows URL
- [ ] Test Publish to Shopify on one product
