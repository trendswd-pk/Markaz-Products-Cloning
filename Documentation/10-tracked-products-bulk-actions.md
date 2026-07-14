# 10 — Tracked Products — Bulk Actions

**Location:** Tracked Products → top button row

## Buttons overview

| Button | Purpose |
|--------|---------|
| **Refresh All Status** | Re-scrape Markaz stock for all tracked URLs |
| **Refresh Shopify Status** | Fetch latest status from Shopify for all |
| **Send to Converter** | Re-fetch Markaz data → load Converter list |
| **Sync Stock** | Update Shopify inventory/status for filtered products |
| **Publish to Shopify** | Re-fetch from Markaz + publish filtered products |
| **Delete Filtered** | Delete filtered products from Supabase and Shopify |

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
4. Expander labels and Shopify filters refresh on rerun

**Requires:** Shopify configured.

---

## Send to Converter

### Step-by-step

1. Apply **Markaz stock** and/or **Shopify status** filters
2. Click **Send to Converter**
3. Progress: fetching each filtered URL from Markaz
4. Products loaded into Converter `products_list`
5. Green message at top of **Shopify Converter**
6. Switch to Converter to review/edit/download

**Use case:** Rebuild CSV for a filtered subset (example: In Stock + Active).

---

## Sync Stock

### Step-by-step

1. Set filters (which products to sync)
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

1. Set filters
2. Click **Publish to Shopify**
3. Phase 1: Fetch fresh data from Markaz (progress 0–50%)
4. Phase 2: Publish to Shopify API (progress 50–100%)
5. Feedback banner at dashboard top — [12-shopify-publish-feedback.md](./12-shopify-publish-feedback.md)

Vendor on published products is **at One Spot**.

### Difference: Sync Stock vs Publish

| Action | Updates existing | Creates new | Re-fetches Markaz |
|--------|------------------|-------------|-------------------|
| Sync Stock | Inventory + status only | No | No |
| Publish | Details + images | Yes | Yes |

---

## Delete Filtered

### Step-by-step

1. Apply filters so only products you want to remove are matched
2. Click **Delete Filtered**
3. Warning shows how many products will be deleted
4. Click **Confirm Delete** (or **Cancel**)
5. For each product:
   - Delete from Shopify if linked
   - Delete from Supabase tracked list
6. Progress completes; success summary shows tracked vs Shopify delete counts

**Warning:** This is permanent. Filters define the full set — not only the current pagination page.

---

## Filter interaction

| Button | Respects Markaz + Shopify filters? |
|--------|-------------------------------------|
| Refresh All Status | No (all tracked) |
| Refresh Shopify Status | No (all tracked) |
| Send to Converter | Yes |
| Sync Stock | Yes |
| Publish to Shopify | Yes |
| Delete Filtered | Yes |

Example: Filter **In Stock** + **Draft** → **Publish to Shopify** only publishes that subset.
