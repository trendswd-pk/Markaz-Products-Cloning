# Markaz to Shopify Converter

Scrape products from [Markaz](https://www.markaz.app), apply sale / compare-at markups, export a Shopify-ready CSV, and publish or sync stock to Shopify. Tracked Markaz URLs live in Supabase (or per-user JSON in Demo Mode). Store vendor name: **at One Spot**.

| | |
|---|---|
| **Version** | 0.1.0 |
| **Released** | 2026-07-26 |

**Live / demo:** run locally with `streamlit run demo_mode/app.py`  
**Demo login:** `demo` / `demo123` (or `viewer` / `view123`)

## What’s new in 0.1.0

- Tracked Products with Shopify Active / Draft / Not on Shopify status
- Category page scrape (From page → To page)
- Demo Mode without secrets or Chromium
- 14-day login session across refresh

## Documentation index

### Getting started

- [Getting started](./00-getting-started.md)
- [Version](./APP-VERSION.md)
- [Changelog](./CHANGELOG.md)
- [Configuration setup](./14-configuration-setup.md)
- [Demo mode](./15-demo-mode.md)

### Pages

- [Login](./01-login-page.md)
- [Dashboard overview](./02-dashboard-overview.md)
- [Shopify Converter tab](./03-shopify-converter-tab.md)
- [Add products — Single](./04-add-products-single-mode.md)
- [Add products — Multiple](./05-add-products-multiple-mode.md)
- [Add products — Category](./16-add-products-category-mode.md)
- [Product preview & pricing](./06-product-preview-and-pricing.md)
- [Product list management](./07-product-list-management.md)
- [Export CSV & publish](./08-export-csv-and-publish.md)
- [Tracked Products tab](./09-tracked-products-tab.md)
- [Tracked bulk actions](./10-tracked-products-bulk-actions.md)
- [Tracked product card](./11-tracked-product-card.md)
- [Shopify publish feedback](./12-shopify-publish-feedback.md)
- [Pricing rules](./13-pricing-rules.md)

## App map

```text
Login
 └── Dashboard
      ├── Shopify Converter
      │    ├── Single | Multiple | Category
      │    ├── Product preview (Single → Fetch)
      │    ├── Product list (edit prices / remove)
      │    └── Export: Download CSV | Publish All
      └── Tracked Products
           ├── Filters (Markaz stock / Shopify status)
           ├── Bulk: Refresh / Sync / Publish / Send / Delete
           └── Per-row card actions
```

## Related

Screenshots live in [`./images/`](./images/). Re-capture with `python scripts/capture_docs_screenshots.py` from the repo root.
