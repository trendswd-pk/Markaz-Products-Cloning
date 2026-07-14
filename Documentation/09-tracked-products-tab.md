# 09 — Tracked Products

**Location:** Dashboard → section **Tracked Products**

## Purpose

Persistently store Markaz product URLs, monitor stock and Shopify status, and run bulk operations.

## Page layout

```
┌─────────────────────────────────────────────────────────┐
│  Tracked Products          [🛍️] [Reload list]           │
│  Markaz URLs auto-save here when you add in Converter   │
│                                                         │
│  Markaz stock: ○ All ○ In Stock ○ Out of Stock ○ Unknown│
│  Shopify: ○ All ○ Not on Shopify ○ Active ○ Draft ○ Archived │
│  ☑ Auto-sync to Shopify after Refresh All Status        │
│                                                         │
│  [Refresh All] [Refresh Shopify] [Send to Converter]    │
│  [Sync Stock]  [Publish to Shopify] [Delete Filtered]   │
│                                                         │
│  N matching / saved · Shopify summary                   │
│  ← Prev | Page 1 of Y · showing 1–50 · 50/page | Next → │
│                                                         │
│  ▼ In Stock | Shopify: Active | Product Title           │
│  ▼ Out of Stock | Shopify: Draft | Product Title        │
└─────────────────────────────────────────────────────────┘
```

## Step-by-step: First visit

### Step 1: Open Tracked Products

Select **Tracked Products** in the top section radio.

### Step 2: Check Supabase connection

If not configured → yellow warning and section stops.  
Configure: [14-configuration-setup.md](./14-configuration-setup.md)

### Step 3: See saved products or empty state

**Empty:**
> No tracked products yet. Add a product in the Converter section...

**With data:** expanders formatted as  
`{Markaz Stock} | {Shopify Status} | {Title}`

### Step 4: Use filters

**Markaz stock**

| Filter | Shows |
|--------|-------|
| All | Every saved URL |
| In Stock | `stock_status = in_stock` |
| Out of Stock | `stock_status = out_of_stock` |
| Unknown | `stock_status = unknown` |

**Shopify status**

| Filter | Shows |
|--------|-------|
| All | Every saved URL |
| Not on Shopify | Not found on store (or no link) |
| Active | On Shopify with status `active` |
| Draft | On Shopify with status `draft` |
| Archived | On Shopify with status `archived` |

Both filters can be combined (example: In Stock + Draft).

If Shopify filter looks stale, click **Refresh Shopify Status**.

### Step 5: Pagination

- List view shows **50 products per page**
- Use **Prev** / **Next** (top and bottom)
- Changing filters resets to page **1**
- Bulk buttons still act on the **entire filtered set**, not only the current page

### Step 6: Reload list (optional)

**Reload list** forces a fresh Supabase fetch (skips session cache). Use after external DB changes.

### Step 7: Read Shopify summary line

Example:
> Shopify: **3** of **4** tracked product(s) found on store (2 active, 1 draft).

## How products get here

Automatically when you **Add to List** in Shopify Converter (if Supabase is configured).

Saved fields:
- `markaz_url`, `title`, `stock_status`
- `shopify_handle`, `shopify_product_id` (after publish)
- `last_checked_at`, `created_at`

## Performance notes

- Tracked list is **session-cached** to protect Supabase free-tier quotas
- Only the active dashboard section loads (radio, not dual tabs)
- See [CHANGELOG.md](./CHANGELOG.md)

## Sub-pages

| Topic | Document |
|-------|----------|
| Bulk action buttons | [10-tracked-products-bulk-actions.md](./10-tracked-products-bulk-actions.md) |
| Individual product card | [11-tracked-product-card.md](./11-tracked-product-card.md) |

## Shopify icon

Green Shopify bag icon appears when Shopify credentials are configured.
