# 12 — Shopify Publish Feedback

**Location:** Dashboard top — above the section radio (after any publish action)

## Purpose

Shows results of the last Shopify publish operation from:
- **Publish All to Shopify** (Converter)
- **Publish to Shopify** (Tracked Products bulk)
- **Publish Shopify** (single product card)

## Step-by-step: Read feedback

### Step 1: Locate banner

Appears immediately below page title, above **Shopify Converter | Tracked Products** section radio.

### Step 2: Read success message (green)

```
Shopify publish complete. Created: 2, Updated: 1.
```

| Field | Meaning |
|-------|---------|
| **Created** | New products added to Shopify |
| **Updated** | Existing products refreshed |

### Step 3: Read warnings (yellow)

When publish succeeded but stock sync failed:

```
{Product Title} published, but stock/inventory was not synced. Images added: 3.

Shopify API 403: ... read_locations scope ...
Fix: Shopify Dev Dashboard → ...
```

Common cause: missing `read_locations` scope. Product and images still publish.

### Step 4: Read errors (red)

When publish completely failed:

```
Shopify publish failed for {Product Title}:

Shopify API 403: merchant approval for write_products scope.
Fix: ...
```

### Step 5: Dismiss

Click **Dismiss publish results** to hide the banner.

---

## Error types and fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `write_products` scope | App not approved to create products | Dev Dashboard → enable scope → reinstall app |
| `read_products` scope | Cannot read existing products | Same as above |
| `read_locations` scope | Cannot sync inventory | Enable scope; or ignore if only publishing |
| Product not found | Wrong handle saved | Re-publish to create fresh |
| Markaz fetch failed | URL invalid/offline | Check Markaz URL |

---

## Feedback persistence

Stored in `st.session_state.shopify_publish_feedback` until dismissed or new publish runs.

Survives section switches (Converter ↔ Tracked Products) but not browser close.

---

## After successful publish

Tracked Products automatically update:
- `shopify_handle`
- `shopify_product_id`
- `stock_status`

Click **Refresh Shopify Status** to see updated green status fields on product cards.
