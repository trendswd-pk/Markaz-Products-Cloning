# Changelog

All notable changes to this project are documented in this file.  
Documentation language: **English** throughout the `Documentation/` folder.

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
