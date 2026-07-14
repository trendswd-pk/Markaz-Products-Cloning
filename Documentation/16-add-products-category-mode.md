# 16 — Add Products — Category Mode

**Location:** Shopify Converter → **Category** button

## Purpose

Paste one Markaz **category / shop listing** URL (not a single product).  
The app reads product **cards** on that page, extracts each card’s product URL, then scrapes those products into the Product List.

Example category URL:

```
https://www.markaz.app/shop/…/Women's%20Unstitched/3%20Piece%20Suits
```

Page 2 style (Markaz pagination):

```
https://www.markaz.app/shop/…/3%20Piece%20Suits?page=2
```

## Step-by-step

### Step 1: Switch to Category mode

1. Open **Shopify Converter**
2. Click **Category** (next to Single / Multiple)

### Step 2: Paste category URL

Paste the main shop/category link (with or without `?page=`).

### Step 3: Choose page range

| Field | Meaning |
|-------|---------|
| **From page** | First `?page=N` to open (default `1`) |
| **To page** | Last page inclusive (default `1`) |

Examples:

- Only page 1 → From `1`, To `1`
- Pages 1 and 2 → From `1`, To `2`
- Only page 5 → From `5`, To `5`

### Step 4: Click **Fetch Category & Add to List**

1. App opens each category page with Playwright  
2. Finds all `a[href*="/shop/product/"]` product card links  
3. Deduplicates URLs  
4. Scrapes each product (same as Multiple mode)  
5. Adds successful products to the Product List + Tracked Products (Supabase)

### Step 5: Review progress

- Per-page caption: how many links found / new  
- Progress bar while each product is scraped  
- Final success count (added vs skipped)

## Card HTML used for URLs

Each product card on Markaz looks like:

```html
<a class="block w-full min-w-0"
   href="/shop/product/green-embroidered-lawn-3pcs-set-for-women/728144">
  …
</a>
```

The scraper turns relative hrefs into absolute URLs:

```
https://www.markaz.app/shop/product/green-embroidered-lawn-3pcs-set-for-women/728144
```

## Tips

- Prefer fetching **small page ranges** (1–2 pages) first — each page can have ~40–60 products.
- Already-added URLs are skipped.
- Single / Multiple modes are unchanged.

## Related code

| File | Role |
|------|------|
| `markaz_scraper.py` | `scrape_category_product_urls`, `build_category_page_url` |
| `app.py` | Category UI + `scrape_and_add_links_to_list` |
