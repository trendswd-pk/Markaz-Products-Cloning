# 03 — Shopify Converter Tab

**Location:** Dashboard → Tab **Shopify Converter**

## Purpose

Scrape Markaz product pages, adjust pricing, manage a conversion list, and export to Shopify (CSV or direct publish).

## Page sections (top to bottom)

| Section | Document |
|---------|----------|
| Import success message | Shown when sent from Tracked Products |
| Add Products | [04](./04-add-products-single-mode.md) / [05](./05-add-products-multiple-mode.md) |
| Product Preview | [06](./06-product-preview-and-pricing.md) |
| Product List | [07](./07-product-list-management.md) |
| Export to Shopify | [08](./08-export-csv-and-publish.md) |
| Empty state help | Shown when list is empty |

## Step-by-step: Overview walkthrough

### Step 1: Open Shopify Converter tab

Click **Shopify Converter** (first tab, selected by default).

### Step 2: Check for import message

If you used **Send to Converter** from Tracked Products, a green success banner appears:

> Loaded **X** product(s) with filter **{filter}**. Open the Shopify Converter tab...

Click **Dismiss** to hide it.

### Step 3: Choose add mode

Under **Add Products** heading:
- **Single** — one URL at a time, with preview option
- **Multiple** — paste many URLs (one per line), bulk add

Default mode: **Multiple**

### Step 4: Add products

See mode-specific guides:
- [04-add-products-single-mode.md](./04-add-products-single-mode.md)
- [05-add-products-multiple-mode.md](./05-add-products-multiple-mode.md)

### Step 5: Review product list

Each added product appears in **Product List (N products)** expanders.  
See [07-product-list-management.md](./07-product-list-management.md)

### Step 6: Export

Scroll to **Export to Shopify**:
- **Publish All to Shopify** — direct API publish
- **Download Shopify CSV** — manual import file

See [08-export-csv-and-publish.md](./08-export-csv-and-publish.md)

## What happens when you add a product

1. Markaz page is scraped (title, price, images, variants, SKU)
2. Default pricing rules applied — [13-pricing-rules.md](./13-pricing-rules.md)
3. Product added to session `products_list`
4. If Supabase configured → URL saved to **Tracked Products** automatically

## Empty state

When no products in list:

> 👈 Enter a product URL above and click 'Add to List' to get started!

Plus a 4-step how-to guide.
