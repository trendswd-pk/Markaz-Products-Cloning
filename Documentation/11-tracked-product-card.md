# 11 — Tracked Product Card

**Location:** Tracked Products → each product expander (current pagination page)

## Expander label format

```
{Markaz Stock Status} | {Shopify Status} | {Product Title}
```

Examples:
- `In Stock | Shopify: Active | Blue Printed Cotton Lawn...`
- `Out of Stock | Shopify: Draft | Elegant Women's Raw Silk...`
- `In Stock | Not on Shopify | New Product Title`

## Step-by-step: View product details

### Step 1: Click expander to open

### Step 2: Read Markaz section

| Field | Description |
|-------|-------------|
| **Markaz Stock Status** | `In Stock` / `Out of Stock` / `Unknown` |
| **Markaz URL** | Original product link (clickable) |
| **Last Checked (Markaz)** | When stock was last scraped |
| **Saved At** | When URL was first added to Supabase |

### Step 3: Read Shopify section (green fields)

| Field | Color | Description |
|-------|-------|-------------|
| **Shopify Status** | 🟢 Green | Active/Draft/Not on Shopify + image count + inventory |
| **Shopify Product ID** | 🟢 Green | Numeric Shopify product ID |
| **Shopify Handle** | White | URL slug on Shopify |
| **Published on Shopify** | White | First publish timestamp |
| **Last Updated on Shopify** | White | Last modification on Shopify |
| **Open in Shopify** | Link | Direct admin URL |

### Step 4: Handle edge cases

**Handle saved but not on Shopify:**
> Handle is saved locally but product was not found on Shopify.

---

## Card action buttons (5 buttons)

```
[Refresh Status] [Shopify Status] [Sync Stock] [Publish Shopify] [Delete]
```

### Refresh Status

1. Click **Refresh Status**
2. Re-scrapes Markaz page for this URL only
3. Updates `stock_status`, `title`, `last_checked_at` in Supabase
4. Success: *Markaz status updated.*

---

### Shopify Status

1. Click **Shopify Status**
2. Fetches live status from Shopify API for this product only
3. Updates cached `shopify_status_map`
4. Success: *Shopify status refreshed.*

**Requires:** Shopify configured + saved handle.

---

### Sync Stock

1. Click **Sync Stock**
2. Syncs inventory for this one product on Shopify
3. In stock → qty 50, active | Out of stock → qty 0, draft
4. Shows sync summary (success or warning)

---

### Publish Shopify

1. Click **Publish Shopify**
2. Fetches fresh Markaz data for this URL
3. Creates or **updates** the product on Shopify (matched by handle)
4. On update, pushes: title, description, vendor, tags, Type, Variant Grams **750**, prices/SKUs, images + variant images, Age group, Target gender, and stock when scopes allow
5. Updates `shopify_handle` and `shopify_product_id` in Supabase
6. Publish feedback shown at dashboard top

---

### Delete

1. Click **Delete**
2. **Phase 1:** Deletes product from Shopify (if linked)
3. **Phase 2:** Removes row from Supabase tracked list
4. Card disappears from list

| Result message | Meaning |
|----------------|---------|
| Removed from tracked list and deleted from Shopify | Full delete success |
| Removed from tracked list. No Shopify product was linked | Only Supabase row removed |
| Removed from tracked list, but Shopify delete failed | Supabase removed, Shopify error shown |

---

## Per-card vs bulk actions

| Action | Card button | Bulk button |
|--------|------------|-------------|
| Refresh Markaz | ✅ This product | ✅ All products |
| Shopify status | ✅ This product | ✅ All products |
| Sync stock | ✅ This product | ✅ Filtered products |
| Publish | ✅ This product | ✅ Filtered products |
| Delete | ✅ This product | ❌ Not available in bulk |
