# Changelog

All notable changes to this project are documented in this file.  
Documentation language: **English** throughout the `Documentation/` folder.

---

## 2026-07-16

### Supabase — fewer API calls (RPC + session cache)
- Added PostgreSQL RPC functions in `supabase/03_rpc_functions.sql`:
  - `list_tracked_products_rpc` — one call to load all rows
  - `upsert_tracked_product_rpc` — one call per save (no update-then-insert round trip)
  - `batch_upsert_tracked_products_rpc` — one call after **Refresh All**
  - `batch_update_shopify_metadata_rpc` — one call after bulk Shopify sync
  - `delete_tracked_products_rpc` — one call for bulk delete
- Python auto-detects RPC; falls back to table REST API if SQL not run yet.
- Tracked list stays in `session_state` and is **patched in place** after add/update/delete (no automatic refetch).
- **Reload list** is the only manual full refetch.
- Tracked Products shows how many full Supabase fetches happened this session.

**Note:** Browser Network tab URLs like `markazapp.streamlit.app/api/v2/app/status` are Streamlit Cloud heartbeats — not Supabase. Supabase calls run server-side.

---

## 2026-07-15

### Shopify publish timeouts
- Raised Shopify API read timeout from 30s to **120s** (connect 15s).
- Create product **without** embedding all images in one request; attach images afterward (avoids slow Shopify remote-image fetch timing out the whole create).
- If the HTTP response times out but the product already exists by handle, treat publish as **success** (recovered) instead of a false failure.
- Image uploads continue on individual failures instead of aborting the whole product.

### Product overview description formatting
- Markaz product overview now uses `<dt>` / `<dd>` highlight cards (label and value stacked).
- Scraper joins each card into a single bullet line, e.g. `• Fabric: Lawn` (no split title/value rows).
- **Brand** / Specifications block is omitted from the Shopify description.
- Fallback still cleans legacy plain `inner_text` if structured HTML parse fails.

---

## 2026-07-14

### Vendor name
- CSV export and Shopify API publish now set **Vendor** to `at One Spot` (previously `Markaz`).

### Category mode (Shopify Converter)
- New **Category** add mode next to Single / Multiple.
- Paste a Markaz category/shop page URL and choose a page range (`?page=N`).
- App collects product card URLs (`a[href*="/shop/product/"]`), then scrapes and adds them to the Product List.
- Improved category scraping: deep scroll, HTML/`__NEXT_DATA__` fallback, unique by product ID (dedupes duplicate cards on the same page).
- Guide: [16-add-products-category-mode.md](./16-add-products-category-mode.md)

### Tracked Products — filters
- Added **Filter by Shopify status**: All / Not on Shopify / Active / Draft / Archived.
- Markaz stock filter renamed label to **Filter by Markaz stock**.
- Stock + Shopify filters can be combined.
- Bulk actions use the combined filtered set.

### Tracked Products — bulk delete
- Added **Delete Filtered** button.
- Confirmation step before permanent delete.
- Deletes matched products from **Supabase** and **Shopify** (when linked).
- Supabase bulk delete uses a single batched API call.

### Tracked Products — pagination
- Product expanders paginated at **50 rows per page**.
- Prev / Next controls at top and bottom.
- Filter changes reset to page 1.
- Bulk actions still apply to the **full filtered list**, not only the current page.

### Performance / Supabase quota
- Replaced `st.tabs` with a section **radio** (`Shopify Converter` | `Tracked Products`) so only the active section runs (tabs previously executed both bodies every rerun and flooded Supabase).
- Session cache for tracked product list (`load_tracked_rows`); use **Reload list** to force refresh.
- Shared Supabase client (no reconnect on every call).
- Upsert no longer does SELECT-then-UPDATE; uses update-then-insert.
- Publish writes stock + Shopify metadata in **one** upsert (not two).
- Shopify status map remains session-cached.

### Login persistence
- Browser refresh no longer forces re-login.
- After Sign in, a signed HMAC token is stored in the URL query (`?auth=...`).
- Token verified on load; valid for **14 days**.
- Logout clears session and token.
- Guide: [01-login-page.md](./01-login-page.md)

### Demo Mode
- Standalone UI (`demo_mode/demo_main.py`) — does not import heavy production `app.py`.
- Simulated Markaz scrape and Shopify actions; no Playwright required for demo.
- Real Shopify API blocked when `MARKAZ_DEMO_MODE=1`.
- Guide: [15-demo-mode.md](./15-demo-mode.md)

---

## Earlier (session summary)

### Markaz scraper
- Support for `markaz.app` product pages, JSON-LD, gallery images.
- Image URL normalization (`static.markaz.app` → public CDN) for Shopify imports.
- Stock status extraction: `in_stock` / `out_of_stock` / `unknown`.

### Shopify integration
- Client-credentials OAuth, publish/update products, image sync, inventory sync.
- Delete tracked product from Shopify when removing from Tracked list.
- Pricing rules: Markaz &lt; 2000 → +500 / +2000; ≥ 2000 → +1500 / +3000 (sale / compare).

### Supabase
- `tracked_products` table, RLS, service_role usage from Streamlit secrets.
- Auto-save on successful Add to List.

### Auth
- Login via `[app_login]` in `.streamlit/secrets.toml` (not Streamlit-reserved `[auth]`).
