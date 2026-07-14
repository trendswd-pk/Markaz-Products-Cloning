# 05 — Add Products — Multiple Mode

**Location:** Shopify Converter → **Multiple** button → text area

## Purpose

Paste many Markaz URLs at once and bulk-scrape them into the product list.

## Step-by-step

### Step 1: Switch to Multiple mode

1. Go to **Shopify Converter** section
2. Click **Multiple** button
3. Caption changes to: *Multiple products mode — paste one URL per line below.*

### Step 2: Paste URLs (one per line)

In the text area **Paste Multiple Product URLs (One per line)**:

```
https://www.markaz.app/shop/product/product-one/
https://www.markaz.app/shop/product/product-two/
https://www.markaz.app/shop/product/product-three/
```

### Step 3: Click **✅ Add to List**

Only one button is shown in Multiple mode (no Fetch preview).

### Step 4: Watch progress

- Progress bar: `Link 1 of N` → `Link N of N`
- Status caption shows current link being fetched

### Step 5: Wait for completion

Each URL takes ~5–15 seconds. A 1-second pause runs between URLs to avoid overloading Markaz.

### Step 6: Read results

Success banner example:

> ✅ **Bulk fetch complete.** Added **3** product(s) to the list (of 3 URL(s) processed).

If some failed:

> 1 URL(s) were skipped (duplicates or errors).

Yellow warnings show per-URL failures.

### Step 7: Review product list

Scroll to **Product List (N products)** — all successful products listed.

## What happens per URL

| Step | Action |
|------|--------|
| 1 | Check if URL already in `processed_urls` → skip if duplicate |
| 2 | Open Playwright browser, scrape page |
| 3 | Apply default pricing rules |
| 4 | Append to `products_list` |
| 5 | Save to Supabase Tracked Products (if configured) |

## Skipped URLs

A URL is skipped when:
- **Already added** in this session (`⚠️ Skipped (already added)`)
- **Scrape failed** (`⚠️ Skipped (failed)`)
- **Exception** during fetch (`⚠️ Skipped (error)`)

## Tips

- Start with 3–5 URLs to test before large batches
- Keep one URL per line, no commas or extra spaces
- Failed URLs can be retried individually in **Single mode**

## No preview in Multiple mode

Pricing uses automatic rules only. To customize prices per product:
1. Add in Multiple mode first
2. Then use **✏️ Edit Prices** in Product List — [07-product-list-management.md](./07-product-list-management.md)
