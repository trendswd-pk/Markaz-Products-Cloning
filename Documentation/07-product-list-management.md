# 07 — Product List Management

**Location:** Shopify Converter → **Product List (N products)** section

## Purpose

View, edit pricing, and remove products in the current conversion session before CSV export or Shopify publish.

## Step-by-step: View a product

### Step 1: Scroll to Product List

Header shows count: **Product List (3 products)**

### Step 2: Click an expander

Label format: `Product 1: {Product Title}`

### Step 3: Read left column

| Field | Description |
|-------|-------------|
| Title | Product name |
| Base SKU | Markaz product code |
| Variants | Sizes/colors detected |
| Fetched Price | Original Markaz price |
| Variant Price | Sale price (with markup) |
| Compare At Price | Strikethrough price |
| URL | Source Markaz link |

### Step 4: Read right column

- Description (first 300 characters)
- Image count
- First product image thumbnail

---

## Step-by-step: Edit pricing

### Step 1: Click **✏️ Edit Prices**

Expander shows **✏️ Edit Pricing** sub-section.

### Step 2: Adjust values

Two number inputs side by side:
- **Variant Price Adjustment**
- **Compare At Price Adjustment**

Live preview shows **New Variant Price** and **New Compare At Price**.

### Step 3: Save or cancel

| Button | Action |
|--------|--------|
| **💾 Save Changes** | Updates product in list |
| **❌ Cancel** | Closes edit mode without saving |

### Step 4: Confirm

Green message: *✅ Prices updated successfully!*

---

## Step-by-step: Remove a product

### Step 1: Click **🗑️ Remove Product N**

### Step 2: Product removed from list

List re-indexes. This does **not** remove from Supabase Tracked Products.

---

## Important notes

| Topic | Detail |
|-------|--------|
| Session only | List clears when browser tab closes |
| Tracked Products | URLs remain in Supabase even after remove from list |
| Edit after publish | Re-edit prices then publish again to update Shopify |
| Order | Products listed in order added (index 0 = first) |

## Product list vs Tracked Products

| Feature | Product List | Tracked Products |
|---------|-------------|------------------|
| Storage | Browser session | Supabase database |
| Full product data | Yes (images, variants) | URL + metadata only |
| Survives refresh | Partially (session) | Yes |
| Edit pricing | Yes | No (re-fetch from Markaz) |
