# Add products — Category mode

**Version:** 0.1.0  
**Route:** `/` → **Shopify Converter** → **Category**  
**Who can access:** signed-in users (production UI)

> Screenshot placeholder: `./images/16-add-products-category-mode.png` (not captured yet — Category mode is production-only). Demo Mode has no Category mode.

## What this page does

Paste a Markaz category / shop page URL, choose a page range, collect product card URLs page-by-page (`?page=1`, `?page=2`, …), scrape each product, and add them to the Converter list with default pricing.

## Layout at a glance

| Area | Content |
|------|---------|
| Mode | **Category** |
| Input | **Category / Shop Page URL** |
| Pages | **From page** · **To page** (inclusive) |
| Action | **📥 Fetch Category & Add to List** |

## Steps

1. Click **Category**.
2. Paste a Markaz category or shop listing URL.
3. Set **From page** and **To page** (example: 1 → 2 fetches `?page=1` and `?page=2`).
4. Click **📥 Fetch Category & Add to List**.
5. Wait for discovery + scrape progress.
6. Confirm success: category fetch complete with an added-product count.

## Form fields

| Label | Type | Required | Notes |
|-------|------|----------|-------|
| Category / Shop Page URL | text | yes | Listing page, not a single product |
| From page | number ≥ 1 | yes | Default 1 |
| To page | number ≥ 1 | yes | Inclusive end |

## Errors & edge cases

- Invalid range or empty discovery → few or zero products added.
- Individual scrape failures are skipped; others still add.
- Large page ranges take longer (live Playwright scrape).

## Related links

- [Add products — Single](./04-add-products-single-mode.md)
- [Add products — Multiple](./05-add-products-multiple-mode.md)
- [Product list management](./07-product-list-management.md)
- [Shopify Converter tab](./03-shopify-converter-tab.md)
