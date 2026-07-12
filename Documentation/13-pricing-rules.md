# 13 — Pricing Rules

**Location:** Applied automatically across Converter, CSV export, and Shopify publish

**Source file:** `pricing_rules.py`

## Overview

Markaz price is never sold directly. The app adds a markup to create:
- **Sale Price** (Shopify `Variant Price`)
- **Compare At Price** (Shopify strikethrough price)

## Formulas

```
Sale Price     = Markaz Price + Variant Price Adjustment
Compare At     = Markaz Price + Compare At Price Adjustment
```

Adjustments are auto-calculated unless you override them manually.

---

## Default rules

### Rule 1: Markaz price **below Rs. 2,000**

| Field | Addition | Example (Markaz = Rs. 1,500) |
|-------|----------|-------------------------------|
| Variant (Sale) | **+ Rs. 500** | Rs. 2,000 |
| Compare At | **+ Rs. 2,000** | Rs. 3,500 |

*Compare = 500 + 1500 extra*

---

### Rule 2: Markaz price **Rs. 2,000 or above**

| Field | Addition | Example (Markaz = Rs. 3,000) |
|-------|----------|-------------------------------|
| Variant (Sale) | **+ Rs. 1,500** | Rs. 4,500 |
| Compare At | **+ Rs. 3,000** | Rs. 6,000 |

*Compare = 1500 + 1500 extra*

---

## Constants (in code)

```python
MARKAZ_PRICE_THRESHOLD = 2000
LOW_VARIANT_ADDITION = 500.0      # price < 2000
HIGH_VARIANT_ADDITION = 1500.0    # price >= 2000
COMPARE_AT_EXTRA = 1500.0         # added on top of variant addition
```

---

## Where rules apply

| Location | Auto-applied? | Manual override? |
|----------|--------------|------------------|
| Single mode — Fetch preview | ✅ Default pre-fill | ✅ Before add |
| Single mode — Quick Add | ✅ | ❌ (edit in list after) |
| Multiple mode — Bulk add | ✅ | ❌ (edit in list after) |
| Product List — Edit Prices | — | ✅ |
| CSV export | Uses saved adjustments | — |
| Shopify publish | Uses saved adjustments | — |
| Tracked Products → Publish | Re-fetches Markaz, applies defaults | — |

---

## Step-by-step: Change price for one product

### After adding to list

1. Open product expander in **Product List**
2. Click **✏️ Edit Prices**
3. Change **Variant Price Adjustment** and/or **Compare At Price Adjustment**
4. Click **💾 Save Changes**
5. Re-export CSV or re-publish to Shopify

### Before adding (Single mode)

1. Click **📥 Fetch Product Data**
2. Adjust numbers in preview section — [06-product-preview-and-pricing.md](./06-product-preview-and-pricing.md)
3. Click **✅ Add to List**

---

## Shopify CSV mapping

| CSV Column | Value |
|------------|-------|
| `Cost per item` | Original Markaz price |
| `Variant Price` | Markaz + variant adjustment |
| `Variant Compare At Price` | Markaz + compare adjustment |

---

## Changing rules globally

Edit `pricing_rules.py` constants and restart the app.  
All new products will use updated defaults. Existing session products keep their saved adjustments.
