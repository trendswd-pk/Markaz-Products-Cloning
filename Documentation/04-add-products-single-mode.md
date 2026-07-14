# 04 — Add Products — Single Mode

**Location:** Shopify Converter → **Single** button → URL input area

## Purpose

Add one Markaz product at a time. Optionally preview and adjust pricing before adding to the list.

## Step-by-step

### Step 1: Switch to Single mode

1. Go to **Shopify Converter** section
2. Click **Single** button (next to "Add Products" heading)
3. Caption changes to: *Single product mode — enter one URL below.*

### Step 2: Paste product URL

In the **Product URL** field, paste a Markaz link:

```
https://www.markaz.app/shop/product/your-product-name/
```

**Tip:** Press **Enter** to trigger **Add to List** (keyboard shortcut enabled).

### Step 3: Choose an action

Two buttons appear:

| Button | Action |
|--------|--------|
| **✅ Add to List** | Scrape immediately and add with default pricing |
| **📥 Fetch Product Data** | Scrape and show preview first (no add yet) |

---

## Path A: Quick Add (Add to List)

### Step A1: Click **✅ Add to List**

Spinner shows: *Fetching and adding product to list...*

### Step A2: Wait for scrape (5–15 seconds)

Playwright opens Markaz page headlessly and extracts data.

### Step A3: Success message

Green banner example:

> Product **Blue Printed Cotton Lawn...** has been added to your list with default pricing rules. Saved to Supabase tracked products.

### Step A4: Product appears in list

Scroll down to **Product List** section.

---

## Path B: Preview First (Fetch Product Data)

### Step B1: Click **📥 Fetch Product Data**

### Step B2: Review preview section

Three columns appear:
- **Image** | **Details** (title, SKU, variants, price) | **Pricing inputs**

Full guide: [06-product-preview-and-pricing.md](./06-product-preview-and-pricing.md)

### Step B3: Adjust pricing (optional)

Change **Variant Price Adjustment** and **Compare At Price Adjustment**.

### Step B4: Click **✅ Add to List** in preview

Or **❌ Cancel** to discard preview.

---

## Duplicate protection

If the same URL was already added in this session:
- URL is in `processed_urls`
- You may see a skip warning in bulk; in single mode a re-add may still attempt scrape

## Common errors

| Error | Cause | Fix |
|-------|-------|-----|
| Failed to scrape | Invalid URL or page not found | Check Markaz URL in browser |
| Please enter at least one product URL | Empty input | Paste a valid URL |
| Supabase save failed | DB not configured | Add Supabase secrets (optional) |

## Valid Markaz URL format

```
https://www.markaz.app/shop/product/{product-slug}/
```

Old `shop.markaz.app/explore` URLs are **not supported**.
