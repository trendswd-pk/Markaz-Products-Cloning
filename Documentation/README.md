# Markaz to Shopify Converter — Documentation

Step-by-step guides for every page and section in the application.  
All documentation is written in **English**.

**Recent changes:** see [CHANGELOG.md](./CHANGELOG.md).

## Quick Start

| # | Document | Description |
|---|----------|-------------|
| 00 | [Getting Started](./00-getting-started.md) | Install, run, and first login |
| 14 | [Configuration & Setup](./14-configuration-setup.md) | Supabase, Shopify, and login secrets |
| — | [Changelog](./CHANGELOG.md) | Dated feature and fix notes |

## Pages

| # | Document | UI Location |
|---|----------|-------------|
| 01 | [Login Page](./01-login-page.md) | App entry — before dashboard |
| 02 | [Dashboard Overview](./02-dashboard-overview.md) | Main screen after login |

## Shopify Converter Section

| # | Document | UI Location |
|---|----------|-------------|
| 03 | [Shopify Converter](./03-shopify-converter-tab.md) | Section radio — Converter |
| 04 | [Add Products — Single Mode](./04-add-products-single-mode.md) | Add Products → Single |
| 05 | [Add Products — Multiple Mode](./05-add-products-multiple-mode.md) | Add Products → Multiple |
| 16 | [Add Products — Category Mode](./16-add-products-category-mode.md) | Add Products → Category |
| 06 | [Product Preview & Pricing](./06-product-preview-and-pricing.md) | After "Fetch Product Data" |
| 07 | [Product List Management](./07-product-list-management.md) | Product List expanders |
| 08 | [Export CSV & Publish](./08-export-csv-and-publish.md) | Export to Shopify section |
| 13 | [Pricing Rules](./13-pricing-rules.md) | How sale/compare prices are calculated |

## Tracked Products Section

| # | Document | UI Location |
|---|----------|-------------|
| 09 | [Tracked Products](./09-tracked-products-tab.md) | Section radio — Tracked Products |
| 10 | [Tracked Products — Bulk Actions](./10-tracked-products-bulk-actions.md) | Top action buttons row |
| 11 | [Tracked Product Card](./11-tracked-product-card.md) | Each product expander + buttons |
| 12 | [Shopify Publish Feedback](./12-shopify-publish-feedback.md) | Top banner after publish |

## Demo Mode

| # | Document | UI Location |
|---|----------|-------------|
| 15 | [Demo Mode](./15-demo-mode.md) | `streamlit run demo_mode/app.py` |

## Typical Workflows

### Workflow A: Quick CSV export
1. [Login](./01-login-page.md)
2. [Single, Multiple, or Category mode](./04-add-products-single-mode.md) → Add products
3. [Download CSV](./08-export-csv-and-publish.md) → Import to Shopify manually

### Workflow B: Direct Shopify publish
1. [Login](./01-login-page.md)
2. Add products in [Converter](./03-shopify-converter-tab.md)
3. [Publish All to Shopify](./08-export-csv-and-publish.md) — Vendor: **at One Spot**

### Workflow C: Track & sync ongoing products
1. Add product in Converter (auto-saves to Supabase)
2. Open [Tracked Products](./09-tracked-products-tab.md)
3. Filter by Markaz stock and/or Shopify status; use pagination as needed
4. Use [Refresh](./10-tracked-products-bulk-actions.md) + [Sync Stock](./10-tracked-products-bulk-actions.md) or [Delete Filtered](./10-tracked-products-bulk-actions.md)

### Workflow D: Category page scrape
1. [Category mode](./16-add-products-category-mode.md) → paste category URL + From/To page
2. Collect product URLs → scrape into Product List
3. Publish or download CSV

### Workflow E: Try demo (no APIs)
1. [Run demo mode](./15-demo-mode.md) → `streamlit run demo_mode/app.py`
2. Login with `demo` / `demo123`
3. Explore [Tracked Products](./09-tracked-products-tab.md) with dummy data (simulated)
4. Paste a Markaz URL in Converter → simulated fetch → demo publish

---

**App entry point:** `app.py` (production)  
**Demo entry point:** `demo_mode/app.py` (standalone simulated UI)  
**Store vendor name:** `at One Spot`
