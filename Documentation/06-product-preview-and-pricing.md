# 06 — Product Preview & Pricing

**Location:** Shopify Converter → after clicking **📥 Fetch Product Data** (Single mode only)

## Purpose

Review scraped product details and set custom price adjustments before adding to the conversion list.

## When this page appears

Only in **Single mode** after **Fetch Product Data** succeeds.  
Does **not** appear in Multiple mode or after quick **Add to List**.

## Layout (3 columns)

```
┌─────────────┬──────────────────────┬─────────────────────────┐
│  Image      │  Title, SKU,         │  Fetched Price          │
│             │  Variants, Price     │  Variant Adjustment     │
│             │                      │  Final Variant Price    │
│             │                      │  Compare At Adjustment  │
│             │                      │  Final Compare At Price │
└─────────────┴──────────────────────┴─────────────────────────┘
        [✅ Add to List]              [❌ Cancel]
```

## Step-by-step

### Step 1: Review product image (Column 1)

First product image from Markaz displayed with caption *Product Image*.

### Step 2: Review details (Column 2)

| Field | Description |
|-------|-------------|
| **Title** | Product name from Markaz |
| **SKU** | Base product code (e.g. `MZ71400000532CNCN`) |
| **Size/Color** | Detected variants if any |
| **Price** | Original Markaz price in PKR |

### Step 3: Review fetched price (Column 3, top)

Blue info box: **Fetched Price: Rs. X,XXX.XX**

### Step 4: Set Variant Price Adjustment

**Variant Price Adjustment** number input:
- Pre-filled with default from [pricing rules](./13-pricing-rules.md)
- Step: 100 PKR increments
- **Final Variant** shown below = Fetched Price + Adjustment

This becomes Shopify **Sale Price**.

### Step 5: Set Compare At Price Adjustment

**Compare At Price Adjustment** number input:
- Pre-filled with default (Variant adjustment + 1500)
- **Final Compare At** shown below

This becomes Shopify **Compare at price** (strikethrough original).

### Step 6: Add or cancel

| Button | Result |
|--------|--------|
| **✅ Add to List** | Saves product with your adjustments to list + Supabase |
| **❌ Cancel** | Clears preview, returns to URL input |

### Step 7: After Add to List

- Preview section disappears
- URL input clears (new widget key)
- Product appears in **Product List** below
- Green success message shown

## Pricing examples

| Markaz Price | Variant Adj. | Sale Price | Compare Adj. | Compare At |
|-------------|--------------|------------|--------------|------------|
| Rs. 1,500 | +500 | Rs. 2,000 | +2,000 | Rs. 3,500 |
| Rs. 3,000 | +1,500 | Rs. 4,500 | +3,000 | Rs. 6,000 |

Full rules: [13-pricing-rules.md](./13-pricing-rules.md)

## Data saved on add

```json
{
  "title": "...",
  "price": 1899,
  "variant_price_adjustment": 500,
  "compare_at_price_adjustment": 2000,
  "image_urls": [...],
  "variants": [...],
  "url": "https://www.markaz.app/..."
}
```
