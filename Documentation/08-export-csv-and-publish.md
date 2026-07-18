  # 08 — Export CSV & Publish to Shopify

  **Location:** Shopify Converter → bottom section **Export to Shopify**

  ## Purpose

  Export products to Shopify-compatible CSV or publish directly to your Shopify store via API.

  ---

  ## Section A: Publish All to Shopify

  ### Prerequisites

  - Shopify configured in `.streamlit/secrets.toml`
  - App installed on store with approved scopes:
    - `read_products`, `write_products`
    - `read_inventory`, `write_inventory`, `read_locations`

  See [14-configuration-setup.md](./14-configuration-setup.md)

  ### Step-by-step

  #### Step 1: Ensure product list is not empty

  At least one product in **Product List**.

  #### Step 2: Click **Publish All to Shopify**

  Spinner: *Publishing N product(s) to Shopify...*

  #### Step 3: Check feedback banner (top of dashboard)

  | Result | Message |
  |--------|---------|
  | Success | `Shopify publish complete. Created: X, Updated: Y.` |
  | Partial | Yellow warnings for stock sync skipped |
  | Failure | Red errors with fix instructions |

  Details: [12-shopify-publish-feedback.md](./12-shopify-publish-feedback.md)

  #### Step 4: Verify in Shopify Admin

  Products created with:
  - Vendor: **at One Spot**
  - Title, description, images
  - Variants with SKU, sale price, compare-at price
  - Inventory: 50 (in stock) or 0 (out of stock)
  - Handle: `{slugified-title}-{base-sku}`

  #### What publish does per product

  | If product exists on Shopify | Action |
  |------------------------------|--------|
  | New handle | **Create** product with images |
  | Existing handle | **Update** details + add missing images + sync stock |

  ---

  ## Section B: Download Shopify CSV

  ### Step-by-step

  #### Step 1: Scroll to **Download Shopify CSV**

  #### Step 2: Review CSV Preview table

  Shows all rows that will be in the export (variants + image rows).

  #### Step 3: Click download button

  **📥 Download Shopify CSV (N products)** — downloads `.csv` file.

  #### Step 4: Import in Shopify Admin

  1. Shopify Admin → **Products** → **Import**
  2. Upload the downloaded CSV
  3. Map columns if prompted
  4. Complete import

  ### CSV includes

  - All **48 Shopify-required columns**
  - Handle, Title, Body HTML, Vendor (`at One Spot`), **Type**, Tags
  - Variant SKU, Price, Compare At Price
  - Images (multiple rows per product)
  - Inventory Qty: 50, Policy: continue
  - Status: active (in stock) or draft (out of stock)

  ---

  ## Section C: Clear All Products

  ### Step 1: Click **Clear All Products**

  ### Step 2: List empties

  `products_list` and `processed_urls` reset.  
  Does **not** affect Tracked Products in Supabase.

  ---

  ## Publish vs CSV — when to use which

  | Method | Best for |
  |--------|----------|
  | **Publish All** | Fast direct sync, recurring updates |
  | **CSV Download** | Manual review, bulk first-time import, backup |

  ## Pricing in export

  Sale and compare-at prices use adjustments from [pricing rules](./13-pricing-rules.md) or your manual edits from [Product List](./07-product-list-management.md).
