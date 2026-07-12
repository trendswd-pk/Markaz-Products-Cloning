# 10 — Tracked Products — Bulk Actions

**Location:** Tracked Products tab → top button row

## Buttons overview

| Button | Purpose |
|--------|---------|
| **Refresh All Status** | Re-scrape Markaz stock for all tracked URLs |
| **Refresh Shopify Status** | Fetch latest status from Shopify for all |
| **Send to Converter** | Re-fetch Markaz data → load Converter list |
| **Sync Stock** | Update Shopify inventory/status for filtered products |
| **Publish to Shopify** | Re-fetch from Markaz + publish filtered products |

---

## Refresh All Status

### Step-by-step

1. Click **Refresh All Status**
2. Progress bar: `Checking 1 of N` → `Checking N of N`
3. Each URL scraped from Markaz live
4. `stock_status` and `title` updated in Supabase
5. Success: *Stock status refreshed for all tracked products.*
6. If **Auto-sync** checkbox enabled → automatically runs **Sync Stock** for all

### Auto-sync checkbox

☑ **Auto-sync to Shopify after Refresh All Status** (default: ON)

When checked, after refresh completes, inventory is synced to Shopify for all tracked products.

---

## Refresh Shopify Status

### Step-by-step

1. Click **Refresh Shopify Status**
2. App calls Shopify API for each saved handle/product ID
3. `shopify_status_map` cache updates
4. Expander labels and details refresh on rerun

**Requires:** Shopify configured.

---

## Send to Converter

### Step-by-step

1. Apply desired **stock filter** first (e.g. only In Stock)
2. Click **Send to Converter**
3. Progress: fetching each filtered URL from Markaz
4. Products loaded into Converter `products_list`
5. Green message at top of **Shopify Converter** tab
6. Switch to Converter tab to review/edit/download

**Use case:** Re-build CSV for filtered in-stock products only.

---

## Sync Stock

### Step-by-step

1. Set stock filter (which products to sync)
2. Click **Sync Stock**
3. Spinner: *Syncing N product(s) to Shopify...*
4. For each product with a saved `shopify_handle`:
   - In stock → inventory **50**, status **active**
   - Out of stock → inventory **0**, status **draft**
5. Success/warning summary shown

**Requires:** `read_locations`, `write_inventory` scopes.

---

## Publish to Shopify

### Step-by-step

1. Set stock filter
2. Click **Publish to Shopify**
3. Phase 1: Fetch fresh data from Markaz (progress 0–50%)
4. Phase 2: Publish to Shopify API (progress 50–100%)
5. Feedback banner at dashboard top — [12-shopify-publish-feedback.md](./12-shopify-publish-feedback.md)

### Difference: Sync Stock vs Publish

| Action | Updates existing | Creates new | Re-fetches Markaz |
|--------|-----------------|-------------|-------------------|
| Sync Stock | Inventory + status only | No | No |
| Publish | Details + images | Yes | Yes |

---

## Filter interaction

All bulk actions except **Refresh All Status** and **Refresh Shopify Status** respect the current **stock filter**.

Example: Filter **In Stock** → **Publish to Shopify** only publishes in-stock filtered products.
