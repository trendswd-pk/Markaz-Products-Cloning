# 09 — Tracked Products Tab

**Location:** Dashboard → Tab **Tracked Products**

## Purpose

Persistently store Markaz product URLs, monitor stock status, view Shopify sync state, and run bulk operations.

## Page layout

```
┌─────────────────────────────────────────────────────────┐
│  Tracked Products                            [🛍️ icon]  │
│  Markaz URLs auto-save here when you add in Converter   │
│                                                         │
│  Filter: ○ All  ○ In Stock  ○ Out of Stock  ○ Unknown  │
│  ☑ Auto-sync to Shopify after Refresh All Status        │
│                                                         │
│  [Refresh All] [Refresh Shopify] [Send to Converter]    │
│  [Sync Stock]  [Publish to Shopify]                     │
│                                                         │
│  N saved URL(s)                                         │
│  Shopify: X of N found on store (Y active, Z draft)     │
│                                                         │
│  ▼ In Stock | Shopify: Active | Product Title           │
│  ▼ Out of Stock | Shopify: Draft | Product Title        │
└─────────────────────────────────────────────────────────┘
```

## Step-by-step: First visit

### Step 1: Open Tracked Products tab

Click second tab **Tracked Products**.

### Step 2: Check Supabase connection

If not configured → yellow warning and tab stops.  
Configure: [14-configuration-setup.md](./14-configuration-setup.md)

### Step 3: See saved products or empty state

**Empty:**
> No tracked products yet. Add a product in the Converter tab...

**With data:**
List of expanders with format:
`{Markaz Stock} | {Shopify Status} | {Title}`

### Step 4: Use stock filter

| Filter | Shows |
|--------|-------|
| All | Every saved URL |
| In Stock | `stock_status = in_stock` |
| Out of Stock | `stock_status = out_of_stock` |
| Unknown | `stock_status = unknown` |

### Step 5: Read Shopify summary line

Example:
> Shopify: **3** of **4** tracked product(s) found on store (2 active, 1 draft).

## How products get here

Automatically when you **Add to List** in Shopify Converter (if Supabase configured).

Saved fields:
- `markaz_url`, `title`, `stock_status`
- `shopify_handle`, `shopify_product_id` (after publish)
- `last_checked_at`, `created_at`

## Sub-pages

| Topic | Document |
|-------|----------|
| Bulk action buttons | [10-tracked-products-bulk-actions.md](./10-tracked-products-bulk-actions.md) |
| Individual product card | [11-tracked-product-card.md](./11-tracked-product-card.md) |

## Shopify icon

Green Shopify bag icon (top-right) appears when Shopify credentials are configured.
