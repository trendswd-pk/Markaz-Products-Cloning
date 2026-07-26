# Export CSV and publish

**Version:** 0.1.0  
**Route:** `/` → **Shopify Converter** → Export section  
**Who can access:** signed-in users

![Export / publish](./images/06-export-csv-and-publish.png)

## What this page does

From the Converter product list you can download a Shopify-ready CSV and/or push every listed product to Shopify via the Admin API (simulated in Demo Mode).

## Layout at a glance

| Area | Content |
|------|---------|
| Header | **Export to Shopify** (production) |
| Publish | **Publish All to Shopify** / **Publish All to Shopify (Demo)** |
| CSV | **Download Shopify CSV** · **📥 Download Shopify CSV** (production) |
| Preview | **CSV Preview** table (production; truncated in demo if present) |
| Clear | **Clear All Products** |

> Production CSV download UI is not in the current screenshot set — see README “Screenshots still needed”.

## Steps

1. Build a non-empty **Product List**.
2. **Download CSV (production):** open **Download Shopify CSV** → **📥 Download Shopify CSV** → file `shopify_products.csv`.
3. **Publish:** click **Publish All to Shopify** (disabled if Shopify is not configured).
4. Read created / updated counts and any warnings.
5. Optional: **Clear All Products** to empty the session list.

### Demo Mode

1. Click **Publish All to Shopify (Demo)**.
2. A demo warning explains there is no real Shopify connection.
3. Success message shows simulated Created / Updated counts.

## CSV notes

- Vendor column is **at One Spot**.
- Cost per item uses the original Markaz price.
- Full 48-column Shopify product CSV layout is generated in production.

## Errors & edge cases

- **Publish All** stays disabled when Shopify secrets are missing.
- Partial publish failures appear in [publish feedback](./12-shopify-publish-feedback.md).
- Clearing the list does not remove Tracked Products rows.

## Related links

- [Shopify publish feedback](./12-shopify-publish-feedback.md)
- [Product list management](./07-product-list-management.md)
- [Configuration setup](./14-configuration-setup.md)
- [Pricing rules](./13-pricing-rules.md)
